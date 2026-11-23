"""T-030 / CR-014: preserve source data, reject mismatches, roll back complete imports."""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mysql_restored_fortune as importer


def source_row(spec, index, key):
    item = dict.fromkeys(spec.columns, 0)
    item.update(zip(spec.natural_key, key, strict=True))
    item.update(idx=index, gend_ref=bool(item['gend_ref']), contents='검증용 한글 본문 𠀀', starPoint=3)
    return item


def complete_source(spec):
    if spec.source == 'TB_yearLuck':
        keys = itertools.product(range(10), range(2), range(2001, 2051), range(1, 8))
    else:
        keys = ((gan, sex, act_gan, act_ji)
                for gan, sex, act_gan, act_ji in itertools.product(range(10), range(2), range(10), range(12))
                if act_gan % 2 == act_ji % 2)
    return [source_row(spec, index, key) for index, key in enumerate(keys, 1)]


def synthetic_snapshots():
    result = []
    for spec in importer.SPECS:
        key = (0, 0, 2001, 1) if spec.source == 'TB_yearLuck' else (0, 0, 0, 0)
        raw = source_row(spec, 1, key)
        raw['gend_ref'] = int(raw['gend_ref'])
        rows = [tuple(raw[column] for column in spec.columns)]
        metadata = {'source_table': spec.source, 'source_sha256': spec.source_sha256,
                    'data_sha256': importer.data_digest(rows), 'row_count': len(rows),
                    'mapping_status': 'unverified', 'quality': importer.data_quality(spec, rows)}
        result.append((spec, rows, metadata))
    return result


class FakeConnection:
    def __init__(self):
        self.rows = {spec.target: [] for spec in importer.SPECS}
        self.metadata = []
        self.events = []
        self.transaction = None
        self.closed = False
        self.commits = self.rollbacks = 0
        self.database = 'woonari'
        self.lock_result = 1
        self.engine = 'InnoDB'
        self.trigger_count = 0
        self.bad_columns = self.bad_collation = self.bad_index = False
        self.fail_table = None
        self.corrupt_readback = self.inserted = False

    def cursor(self):
        return FakeCursor(self)

    def autocommit(self, enabled):
        self.events.append(('autocommit', enabled))

    def begin(self):
        self.events.append(('begin', None))
        self.transaction = copy.deepcopy((self.rows, self.metadata))

    def commit(self):
        self.events.append(('commit', None))
        self.commits += 1
        self.transaction = None

    def rollback(self):
        self.rollbacks += 1
        if self.transaction:
            self.rows, self.metadata = self.transaction
            self.transaction = None

    def close(self):
        self.closed = True


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.result = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, args=None):
        c = self.connection
        c.events.append((sql, args))
        self.result = []
        if sql == 'SELECT DATABASE()':
            self.result = [(c.database,)]
        elif 'GET_LOCK' in sql:
            self.result = [(c.lock_result,)]
        elif 'RELEASE_LOCK' in sql:
            self.result = [(1,)]
        elif sql.startswith(('CREATE TABLE', 'SET TRANSACTION')):
            pass
        elif 'information_schema.TABLES' in sql:
            self.result = [(c.engine,)]
        elif 'information_schema.COLUMNS' in sql:
            spec = next((spec for spec in importer.SPECS if spec.target == args[1]), None)
            columns = spec.columns if spec else importer.METADATA_COLUMNS
            for column in columns:
                kind = ('longtext' if column in {'contents', 'payload'} else
                        'varchar' if column == 'source_table' else
                        'char' if column.endswith('sha256') else 'int')
                length = 32 if kind == 'varchar' else 64 if kind == 'char' else None
                collation = None if kind == 'int' else 'utf8mb4_bin'
                if c.bad_collation and collation:
                    collation = 'utf8mb4_general_ci'
                self.result.append((column, kind, 'NO', '', length, collation))
            if c.bad_columns:
                self.result = self.result[:-1]
        elif 'information_schema.STATISTICS' in sql:
            spec = next((spec for spec in importer.SPECS if spec.target == args[1]), None)
            self.result = [('PRIMARY', 0, 1, 'idx' if spec else 'source_table')]
            if spec:
                self.result += [('source_lookup', 0, index, column)
                                for index, column in enumerate(spec.natural_key, 1)]
            if c.bad_index:
                self.result.append(('unexpected_unique', 0, 1, 'contents'))
        elif 'information_schema.TRIGGERS' in sql:
            self.result = [(c.trigger_count,)]
        elif sql.startswith('SELECT') and importer.METADATA_TABLE in sql:
            self.result = list(c.metadata)
        elif sql.startswith('INSERT') and importer.METADATA_TABLE in sql:
            c.metadata.append(tuple(args))
        elif sql.startswith('SELECT'):
            spec = next(spec for spec in importer.SPECS if f'`{spec.target}`' in sql)
            self.result = list(c.rows[spec.target])
            if c.corrupt_readback and self.result:
                changed = list(self.result[0])
                changed[spec.columns.index('contents')] = 'modified'
                self.result = [tuple(changed), *self.result[1:]]
        else:
            raise AssertionError('Unexpected query')
        return len(self.result)

    def executemany(self, sql, values):
        c = self.connection
        c.events.append((sql, list(values)))
        spec = next(spec for spec in importer.SPECS if f'`{spec.target}`' in sql)
        c.rows[spec.target].extend(values)
        c.inserted = True
        if spec.target == c.fail_table:
            raise RuntimeError('private values must never escape')

    def fetchone(self):
        return self.result[0] if self.result else None

    def fetchall(self):
        return self.result


class SourceValidationTests(unittest.TestCase):
    def test_invalid_fields_types_values_and_duplicates_are_rejected(self):
        source = complete_source(importer.YEAR)
        corruptions = [lambda rows: rows.pop(), lambda rows: rows.append(dict(rows[0])),
                       lambda rows: rows[0].update(customer_email='excluded'),
                       lambda rows: rows[0].update(starPoint=None),
                       lambda rows: rows[0].update(gan_ref=True),
                       lambda rows: rows[0].update(gend_ref=0),
                       lambda rows: rows[0].update(score1=256),
                       lambda rows: rows[0].update(contents=1),
                       lambda rows: rows[0].update(year_act=2051)]
        for number, corrupt in enumerate(corruptions):
            with self.subTest(corruption=number):
                rows = [dict(row) for row in source]
                corrupt(rows)
                with self.assertRaises(ValueError):
                    importer.validate_rows(importer.YEAR, rows)

    def test_wrong_month_pair_does_not_satisfy_full_coverage(self):
        rows = complete_source(importer.MONTH)
        rows[0]['ji_act'] = 1
        with self.assertRaises(ValueError):
            importer.validate_rows(importer.MONTH, rows)

    def test_structural_coverage_does_not_make_placeholder_years_populated(self):
        source = complete_source(importer.YEAR)
        for row in source:
            if row['year_act'] >= 2021:
                row.update(contents='', starPoint=1)
        rows = importer.validate_rows(importer.YEAR, source)
        quality = importer.data_quality(importer.YEAR, rows)
        self.assertEqual(quality['populated_years'], list(range(2001, 2021)))
        self.assertEqual(quality['placeholder_years'], list(range(2021, 2051)))
        self.assertEqual(quality['year_counts'][26],
                         {'year': 2027, 'row_count': 140, 'populated': 0, 'placeholder': 140})
        self.assertFalse(quality['ready_for_personal_selection'])

    def test_hash_failure_prevents_even_obtaining_database_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exports = root / '.local/woonari/restore/exports'
            exports.mkdir(parents=True)
            (exports / 'TB_yearLuck.json').write_text('[]')
            with patch.object(importer, 'ROOT', root), \
                    patch.object(importer, 'connect_mysql') as connect, \
                    self.assertRaises(importer.DatabaseCheckError):
                importer.import_mysql(exports)
            connect.assert_not_called()

    def test_complete_snapshot_hashes_provenance_and_json_duplicate_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exports = root / '.local/woonari/restore/exports'
            exports.mkdir(parents=True)
            specs = []
            for spec in importer.SPECS:
                raw = json.dumps(complete_source(spec), ensure_ascii=False).encode()
                (exports / f'{spec.source}.json').write_bytes(raw)
                specs.append(replace(spec, source_sha256=hashlib.sha256(raw).hexdigest()))
            with patch.object(importer, 'ROOT', root), patch.object(importer, 'SPECS', specs):
                snapshots = importer.local_snapshots(exports)
            self.assertEqual([len(rows) for _, rows, _ in snapshots], [7000, 1200])
            self.assertTrue(all(meta['mapping_status'] == 'unverified' for _, _, meta in snapshots))
            with self.assertRaises(ValueError):
                importer._unique_object([('contents', 'a'), ('contents', 'b')])


class ImportTransactionTests(unittest.TestCase):
    def setUp(self):
        self.snapshots = synthetic_snapshots()

    def run_import(self, connection):
        with patch.object(importer, 'local_snapshots', return_value=self.snapshots), \
                patch.object(importer, 'connect_mysql', return_value=connection):
            return importer.import_mysql(Path('unused'))

    def test_both_tables_commit_together_with_unicode_and_ddl_before_transaction(self):
        c = FakeConnection()
        report = self.run_import(c)
        self.assertEqual([item['status'] for item in report['tables']], ['imported', 'imported'])
        self.assertEqual(c.commits, 1)
        self.assertEqual(len(c.metadata), 2)
        self.assertTrue(c.closed)
        for spec, rows, _meta in self.snapshots:
            self.assertEqual(c.rows[spec.target], rows)
        sqls = [sql for sql, _args in c.events]
        begin = sqls.index('begin')
        self.assertTrue(all(i < begin for i, sql in enumerate(sqls) if sql.startswith('CREATE')))
        self.assertTrue(all(i > begin for i, sql in enumerate(sqls) if sql.startswith('INSERT')))
        self.assertFalse(any(word in sql for sql in sqls for word in ('DROP ', 'DELETE ', 'TRUNCATE ', 'UPDATE `', 'REPLACE ')))

    def test_idempotent_rerun_checks_data_and_provenance_without_inserts(self):
        c = FakeConnection()
        self.run_import(c)
        c.events = []
        report = self.run_import(c)
        self.assertEqual([item['status'] for item in report['tables']], ['already_present'] * 2)
        self.assertFalse(any(sql.startswith('INSERT') for sql, _args in c.events))

    def test_changed_existing_text_is_never_overwritten(self):
        c = FakeConnection()
        self.run_import(c)
        old = list(c.rows[importer.YEAR.target][0])
        old[importer.YEAR.columns.index('contents')] = 'existing different data'
        c.rows[importer.YEAR.target][0] = tuple(old)
        before = copy.deepcopy(c.rows)
        with self.assertRaisesRegex(importer.DatabaseCheckError, '기존 데이터를 보존'):
            self.run_import(c)
        self.assertEqual(c.rows, before)

    def test_provenance_mismatch_is_never_rewritten(self):
        c = FakeConnection()
        self.run_import(c)
        previous = list(c.metadata[0])
        previous[4] = json.dumps({'mapping_status': 'wrong'})
        c.metadata[0] = tuple(previous)
        before = copy.deepcopy(c.metadata)
        with self.assertRaisesRegex(importer.DatabaseCheckError, '출처 정보'):
            self.run_import(c)
        self.assertEqual(c.metadata, before)

    def test_second_table_failure_rolls_back_first_table_and_metadata(self):
        c = FakeConnection()
        c.fail_table = importer.MONTH.target
        with self.assertRaises(importer.DatabaseCheckError) as caught:
            self.run_import(c)
        self.assertNotIn('private', str(caught.exception))
        self.assertEqual(c.rows, {spec.target: [] for spec in importer.SPECS})
        self.assertEqual(c.metadata, [])
        self.assertEqual(c.commits, 0)
        self.assertEqual(c.rollbacks, 1)

    def test_text_readback_changes_roll_back_all_inserts(self):
        c = FakeConnection()
        c.corrupt_readback = True
        with self.assertRaisesRegex(importer.DatabaseCheckError, '전체 적재를 취소'):
            self.run_import(c)
        self.assertEqual(c.rows[importer.YEAR.target], [])

    def test_schema_engine_collation_index_and_trigger_guards(self):
        for field, value in [('engine', 'MyISAM'), ('bad_columns', True), ('bad_collation', True),
                             ('bad_index', True), ('trigger_count', 1)]:
            with self.subTest(field=field):
                c = FakeConnection()
                setattr(c, field, value)
                with self.assertRaises(importer.DatabaseCheckError):
                    self.run_import(c)
                self.assertFalse(c.inserted)

    def test_wrong_database_and_lock_fail_before_any_ddl(self):
        for field, value in [('database', 'different_project'), ('lock_result', 0)]:
            with self.subTest(field=field):
                c = FakeConnection()
                setattr(c, field, value)
                with self.assertRaises(importer.DatabaseCheckError):
                    self.run_import(c)
                self.assertFalse(any(sql.startswith('CREATE') for sql, _args in c.events))


if __name__ == '__main__':
    unittest.main()

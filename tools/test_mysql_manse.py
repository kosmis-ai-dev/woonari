"""T-017 / CR-009: preserve MySQL data across import failures and reruns."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mysql_manse as importer

ROWS = [
    (1, 1900, 1, 1, 1899, 12, 1, 0, 0, 0, 0, 5, 11, 2, 0, 0, 0, "1900-01-01"),
    (2, 1900, 1, 2, 1899, 12, 1, 0, 0, 0, 0, 5, 11, 2, 0, 1, 1, "1900-01-02"),
]
METADATA = {
    "source_sha256": "a" * 64, "data_sha256": importer.data_digest(ROWS), "row_count": 2,
    "format": "fixture.tb_manse.v1", "schema_version": 1, "min_solar_date": "1900-01-01",
    "max_solar_date": "1900-01-02", "annotations": ["원본 중복 날짜 보존"],
}
PROVENANCE = {key: METADATA[key] for key in importer.PROVENANCE_COLUMNS}
REMOTE_METADATA = (*PROVENANCE.values(), json.dumps(METADATA, ensure_ascii=False))


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.results = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, statement, values=None):
        connection = self.connection
        connection.events.append((statement, values))
        self.results = []
        if statement.startswith("SELECT GET_LOCK"):
            self.results = [(connection.lock_available,)]
        elif statement.startswith("SELECT RELEASE_LOCK"):
            connection.released = True
        elif statement.startswith("CREATE"):
            connection.ddl_created = True
        elif statement.startswith("SELECT ENGINE"):
            self.results = [(connection.engine,)]
        elif "information_schema.COLUMNS" in statement:
            table = values[1]
            names = importer.COLUMNS if table == importer.TABLE else importer.METADATA_COLUMNS
            types = (("int",) * 17 + ("date",) if table == importer.TABLE
                     else ("char", "char", "int", "longtext"))
            self.results = [(name, kind, "NO", "") for name, kind in zip(names, types, strict=True)]
            if connection.schema_mismatch and table == importer.TABLE:
                self.results[7] = ("different_column", "int", "NO", "")
        elif "information_schema.STATISTICS" in statement:
            self.results = [("PRIMARY", 0, 1, "idx")]
            self.results += [("solar", 0, index, column)
                             for index, column in enumerate(importer.SOLAR_COLUMNS, start=1)]
            self.results += [("lunar", int(not connection.unique_lunar), index, column)
                             for index, column in enumerate(importer.LUNAR_COLUMNS, start=1)]
        elif "information_schema.TRIGGERS" in statement:
            self.results = [(connection.trigger_count,)]
        elif statement.startswith("SELECT") and "ORDER BY `idx`" in statement:
            self.results = sorted(connection.rows, key=lambda row: row[0])
            if connection.corrupt_readback and connection.inserted:
                self.results = [(*self.results[0][:-1], "2000-01-01"), *self.results[1:]]
        elif statement.startswith("SELECT") and importer.METADATA_TABLE in statement:
            self.results = list(connection.metadata)
        elif statement.startswith("INSERT") and importer.METADATA_TABLE in statement:
            if connection.fail_metadata:
                raise RuntimeError("private connection detail must never escape")
            connection.metadata.append(tuple(values))
        elif statement.startswith("SET TRANSACTION"):
            pass
        else:
            raise AssertionError("Unexpected query")
        return len(self.results)

    def executemany(self, statement, values):
        self.connection.events.append((statement, list(values)))
        self.connection.rows.extend(values)
        self.connection.inserted = True
        if self.connection.fail_insert:
            raise RuntimeError("private connection detail must never escape")
        return len(values)

    def fetchone(self):
        return self.results[0] if self.results else None

    def fetchall(self):
        return self.results


class FakeConnection:
    def __init__(self, rows=None, metadata=None):
        self.rows = list(rows or [])
        self.metadata = list(metadata or [])
        self.events = []
        self.snapshot = None
        self.closed = False
        self.released = False
        self.ddl_created = False
        self.inserted = False
        self.commits = 0
        self.rollbacks = 0
        self.engine = "InnoDB"
        self.lock_available = 1
        self.schema_mismatch = False
        self.unique_lunar = False
        self.trigger_count = 0
        self.fail_insert = False
        self.fail_metadata = False
        self.corrupt_readback = False

    def cursor(self):
        return FakeCursor(self)

    def autocommit(self, enabled):
        self.events.append(("autocommit", enabled))

    def begin(self):
        self.events.append(("begin", None))
        self.snapshot = (copy.deepcopy(self.rows), list(self.metadata))

    def commit(self):
        self.events.append(("commit", None))
        self.commits += 1
        self.snapshot = None

    def rollback(self):
        self.rollbacks += 1
        if self.snapshot is not None:
            self.rows, self.metadata = self.snapshot
            self.snapshot = None

    def close(self):
        self.closed = True


class MysqlManseTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = patch.object(importer, "_local_snapshot", return_value=(ROWS, METADATA))
        self.snapshot.start()
        self.addCleanup(self.snapshot.stop)

    def run_import(self, connection, database="woonari"):
        with patch.object(importer, "connect_mysql", return_value=connection) as connect:
            result = importer.import_mysql(database)
        connect.assert_called_once_with(select_database=False)
        return result

    def test_import_creates_database_and_commits_rows_and_metadata_together(self):
        connection = FakeConnection()
        report = self.run_import(connection)
        self.assertEqual(report, {"database": "woonari", "table": "tb_manse", **PROVENANCE, "status": "imported"})
        self.assertEqual(connection.rows, ROWS)
        self.assertEqual(connection.metadata[0][:3], REMOTE_METADATA[:3])
        self.assertEqual(json.loads(connection.metadata[0][3]), METADATA)
        self.assertNotIn("annotations", report)
        self.assertEqual(connection.commits, 1)
        self.assertEqual(connection.rollbacks, 0)
        self.assertTrue(connection.closed and connection.released)
        statements = [statement for statement, _ in connection.events]
        begin = statements.index("begin")
        self.assertTrue(all(index < begin for index, statement in enumerate(statements)
                            if statement.startswith("CREATE")))
        self.assertTrue(all(index > begin for index, statement in enumerate(statements)
                            if statement.startswith("INSERT")))
        self.assertIn("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE", statements)
        self.assertFalse(any(word in statement.upper() for statement in statements
                             for word in ("TRUNCATE ", "DROP ", "INSERT IGNORE", "REPLACE INTO")))

    def test_duplicate_lunar_keys_are_preserved(self):
        connection = FakeConnection()
        self.run_import(connection)
        lunar = [tuple(record[4:8]) for record in connection.rows]
        self.assertEqual(lunar[0], lunar[1])
        ddl = next(statement for statement, _ in connection.events
                   if statement.startswith("CREATE TABLE") and "`tb_manse`" in statement)
        self.assertIn("KEY `manse_lunar_lookup`", ddl)
        self.assertNotIn("UNIQUE KEY `manse_lunar_lookup`", ddl)

    def test_repeat_import_verifies_existing_data_without_writing_it(self):
        connection = FakeConnection()
        self.run_import(connection)
        connection.events = []
        report = self.run_import(connection)
        self.assertEqual(report["status"], "already_present")
        self.assertEqual(connection.rows, ROWS)
        self.assertFalse(any(statement.startswith("INSERT") for statement, _ in connection.events))

    def test_matching_existing_date_objects_are_hashed_as_iso_dates(self):
        rows = [(*row[:-1], date.fromisoformat(row[-1])) for row in ROWS]
        metadata = [REMOTE_METADATA]
        connection = FakeConnection(rows, metadata)
        self.assertEqual(self.run_import(connection)["status"], "already_present")

    def test_matching_existing_data_can_receive_missing_provenance(self):
        connection = FakeConnection(ROWS)
        self.assertEqual(self.run_import(connection)["status"], "already_present")
        data_inserts = [statement for statement, _ in connection.events
                        if statement.startswith("INSERT") and "`tb_manse`" in statement]
        self.assertEqual(data_inserts, [])
        self.assertEqual(len(connection.metadata), 1)

    def test_nonempty_mismatching_table_is_never_overwritten(self):
        old_rows = [(*ROWS[0][:-1], "1900-01-03")]
        connection = FakeConnection(old_rows)
        with self.assertRaisesRegex(importer.DatabaseCheckError, "기존 데이터를 보존"):
            self.run_import(connection)
        self.assertEqual(connection.rows, old_rows)
        self.assertFalse(connection.inserted)
        self.assertEqual(connection.commits, 0)
        self.assertTrue(connection.closed)

    def test_mismatching_metadata_is_never_overwritten(self):
        metadata = [("b" * 64, METADATA["data_sha256"], 2, REMOTE_METADATA[3])]
        connection = FakeConnection(ROWS, metadata)
        with self.assertRaisesRegex(importer.DatabaseCheckError, "출처 정보가 다릅니다"):
            self.run_import(connection)
        self.assertEqual(connection.metadata, metadata)
        self.assertFalse(connection.inserted)

    def test_matching_hashes_with_different_payload_are_not_reused(self):
        changed = {**METADATA, "annotations": ["different source annotation"]}
        metadata = [(*REMOTE_METADATA[:3], json.dumps(changed))]
        connection = FakeConnection(ROWS, metadata)
        with self.assertRaisesRegex(importer.DatabaseCheckError, "출처 정보가 다릅니다"):
            self.run_import(connection)
        self.assertEqual(connection.metadata, metadata)
        self.assertFalse(connection.inserted)

    def test_equivalent_payload_json_format_is_reused_without_rewriting(self):
        payload = json.dumps(METADATA, ensure_ascii=True, indent=2, sort_keys=True)
        connection = FakeConnection(ROWS, [(*REMOTE_METADATA[:3], payload)])
        self.assertEqual(self.run_import(connection)["status"], "already_present")
        self.assertEqual(connection.metadata[0][3], payload)
        self.assertFalse(any(statement.startswith("INSERT") for statement, _ in connection.events))

    def test_insert_failure_rolls_back_all_rows_and_keeps_only_empty_ddl(self):
        connection = FakeConnection()
        connection.fail_insert = True
        with self.assertRaisesRegex(importer.DatabaseCheckError, "적재 또는 데이터 검증") as caught:
            self.run_import(connection)
        self.assertNotIn("private connection", str(caught.exception))
        self.assertEqual(connection.rows, [])
        self.assertEqual(connection.metadata, [])
        self.assertEqual(connection.rollbacks, 1)
        self.assertTrue(connection.ddl_created and connection.closed and connection.released)

    def test_metadata_failure_rolls_back_data_and_allows_retry(self):
        connection = FakeConnection()
        connection.fail_metadata = True
        with self.assertRaises(importer.DatabaseCheckError):
            self.run_import(connection)
        self.assertEqual(connection.rows, [])
        connection.fail_metadata = False
        self.assertEqual(self.run_import(connection)["status"], "imported")
        self.assertEqual(connection.rows, ROWS)

    def test_failed_readback_digest_rolls_back_all_inserts(self):
        connection = FakeConnection()
        connection.corrupt_readback = True
        with self.assertRaisesRegex(importer.DatabaseCheckError, "전체 적재를 취소"):
            self.run_import(connection)
        self.assertEqual(connection.rows, [])
        self.assertEqual(connection.metadata, [])
        self.assertEqual(connection.commits, 0)

    def test_other_import_lock_prevents_ddl_and_inserts(self):
        connection = FakeConnection()
        connection.lock_available = 0
        with self.assertRaisesRegex(importer.DatabaseCheckError, "다른 만세력 적재"):
            self.run_import(connection)
        self.assertFalse(connection.ddl_created or connection.inserted or connection.released)
        self.assertTrue(connection.closed)

    def test_schema_engine_index_or_trigger_mismatch_prevents_writes(self):
        for key, value in (("engine", "MyISAM"), ("schema_mismatch", True),
                           ("unique_lunar", True), ("trigger_count", 1)):
            connection = FakeConnection(ROWS)
            setattr(connection, key, value)
            with self.subTest(key=key), self.assertRaises(importer.DatabaseCheckError):
                self.run_import(connection)
            self.assertEqual(connection.rows, ROWS)
            self.assertFalse(connection.inserted)
            self.assertTrue(connection.closed)

    def test_invalid_database_name_is_rejected_before_connecting(self):
        for name in ("", "bad-name", "db`; DROP TABLE data;--", "x" * 65, "1database"):
            with self.subTest(name=name), patch.object(importer, "connect_mysql") as connect, \
                    self.assertRaises(importer.DatabaseCheckError):
                importer.import_mysql(name)
            connect.assert_not_called()

    def test_valid_explicit_database_is_quoted_and_metadata_is_parameterized(self):
        connection = FakeConnection()
        self.assertEqual(self.run_import(connection, "OwnDatabase_2")["database"], "OwnDatabase_2")
        self.assertIn(("CREATE DATABASE IF NOT EXISTS `OwnDatabase_2` CHARACTER SET utf8mb4", None),
                      connection.events)
        metadata_insert = next((statement, params) for statement, params in connection.events
                               if statement.startswith("INSERT") and importer.METADATA_TABLE in statement)
        self.assertNotIn(METADATA["source_sha256"], metadata_insert[0])
        self.assertEqual(metadata_insert[1][0], METADATA["source_sha256"])

    def test_local_hash_mismatch_prevents_any_network_connection(self):
        self.snapshot.stop()
        store = Mock()
        store.metadata.return_value = {**METADATA, "data_sha256": "0" * 64}
        store.iter_records.return_value = iter(ROWS)
        with patch.object(importer, "ManseStore", return_value=store), \
                patch.object(importer, "connect_mysql") as connect, \
                self.assertRaisesRegex(importer.DatabaseCheckError, "로컬 만세력 DB"):
            importer.import_mysql()
        connect.assert_not_called()

    def test_local_snapshot_keeps_complete_metadata_for_remote_reader(self):
        self.snapshot.stop()
        store = Mock()
        store.metadata.return_value = METADATA
        store.iter_records.return_value = iter(ROWS)
        with patch.object(importer, "ManseStore", return_value=store):
            rows, metadata = importer._local_snapshot()
        self.assertEqual(rows, ROWS)
        self.assertEqual(metadata, METADATA)
        self.assertEqual(metadata["annotations"], ["원본 중복 날짜 보존"])


if __name__ == "__main__":
    unittest.main()

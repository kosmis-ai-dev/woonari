"""CR-015 / T-033: source fidelity, table isolation, atomicity and idempotence."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import asdict, replace
from datetime import date, datetime, timedelta
from decimal import Decimal

import mysql_fortune_archive as archive
import pytest


def column(name, kind="int", *, nullable=False, precision=10, scale=0, length=4):
    return archive.ColumnSpec(name, kind, length, precision, scale, nullable)


def sample_tables():
    return [
        ("tbPreLife", [column("num"), column("content", "text", nullable=True, length=16)],
         [{"num": 1, "content": "검증용 한글 𠀀  "}, {"num": 2, "content": None}], ["num"]),
        ("TB_BirthLuck", [column("num", nullable=True)], [], []),
    ]


def write_registry(tmp_path, monkeypatch, tables=None):
    directory = tmp_path / "restore/exports"
    directory.mkdir(parents=True)
    entries = []
    for source, columns, values, primary_key in tables or sample_tables():
        target = archive.target_name(source)
        raw = json.dumps(values, ensure_ascii=False).encode("utf-8")
        entry = {
            "source_table": source, "target_table": target, "file": target + ".json",
            "source_sha256": hashlib.sha256(raw).hexdigest(), "row_count": len(values),
            "columns": [asdict(c) for c in columns], "primary_key": primary_key,
        }
        path = directory / entry["file"]
        path.write_bytes(raw)
        _rows, entry["data_sha256"] = archive.inspect_export(entry, path)
        entries.append(entry)
    registry = {
        "format": archive.FORMAT, "source_backup": "dbkosmis_20251106.bak", "tables": entries,
        "excluded_tables": [{"name": "TB_member", "reason": "personal_records"}],
    }
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2))
    monkeypatch.setattr(archive, "REGISTRY", registry_path)
    monkeypatch.setattr(archive, "PRIVATE_ROOT", tmp_path / "restore")
    return directory, registry


def test_export_preserves_unicode_trailing_space_null_and_empty_tables(tmp_path, monkeypatch):
    directory, _registry = write_registry(tmp_path, monkeypatch)
    snapshots = archive.local_snapshots(directory)
    assert snapshots[0].rows == [(1, "검증용 한글 𠀀  "), (2, None)]
    assert snapshots[1].rows == []
    assert snapshots[0].metadata["mapping_status"] == "unverified"
    assert snapshots[0].metadata["registry_sha256"] == hashlib.sha256(
        archive.REGISTRY.read_bytes()).hexdigest()
    assert "not an ASP query order" in snapshots[0].metadata["ordinal_semantics"]


@pytest.mark.parametrize(("spec", "raw", "canonical"), [
    (column("a", "bit", precision=1, length=1), True, 1),
    (column("a", "numeric", precision=38, scale=8), "123456789012345678901234567890.12345678",
     "123456789012345678901234567890.12345678"),
    (column("a", "datetime", precision=23, scale=3), "2001-01-02T03:04:05.003",
     "2001-01-02T03:04:05.003000"),
    (column("a", "date"), "1900-01-01", "1900-01-01"),
    (column("a", "time", scale=6), "03:04:05.123456", "03:04:05.123456"),
    (column("a", "float", precision=53, length=8), "1.2345678901234567", 1.2345678901234567),
    (column("a", "varbinary"), "0x00AbFF", "0x00abff"),
])
def test_lossless_normalization(spec, raw, canonical):
    assert archive.normalize(spec, raw, source=True) == canonical


def test_mysql_native_date_decimal_binary_and_time_values_normalize_identically():
    assert archive.normalize(column("a", "date"), date(1900, 1, 1), source=False) == "1900-01-01"
    assert archive.normalize(column("a", "datetime"), datetime(2001, 1, 2), source=False) == (
        "2001-01-02T00:00:00.000000")
    assert archive.normalize(column("a", "numeric", precision=10, scale=2),
                             Decimal("12.30"), source=False) == "12.30"
    assert archive.normalize(column("a", "varbinary"), b"\x00\xab", source=False) == "0x00ab"
    assert archive.normalize(column("a", "time", scale=6),
                             timedelta(hours=3, microseconds=1), source=False) == "03:00:00.000001"


@pytest.mark.parametrize(("spec", "raw"), [
    (column("a"), True), (column("a"), 2**31),
    (column("a", "tinyint"), -1), (column("a", "bit"), 1),
    (column("a"), None), (column("a", "text"), b"not Unicode"),
    (column("a", "numeric", precision=4, scale=2), "1.234"),
    (column("a", "numeric", precision=4, scale=2), "100.00"),
    (column("a", "float", precision=53), "NaN"),
    (column("a", "datetime"), "2001-01-01T00:00:00+09:00"),
    (column("a", "varbinary"), "0xA"),
])
def test_invalid_or_lossy_values_are_rejected(spec, raw):
    with pytest.raises((ValueError, ArithmeticError)):
        archive.normalize(spec, raw, source=True)


def test_duplicate_original_primary_key_rejected_but_unkeyed_duplicates_preserved(tmp_path, monkeypatch):
    directory, registry = write_registry(tmp_path, monkeypatch)
    spec = archive.table_spec(registry["tables"][0])
    with pytest.raises(ValueError, match="duplicate"):
        archive.validate_rows(spec, [{"num": 1, "content": "a"}, {"num": 1, "content": "b"}])
    unkeyed = replace(spec, primary_key=())
    assert archive.validate_rows(unkeyed, [{"num": 1, "content": "a"}] * 2) == [(1, "a")] * 2
    assert directory.is_dir()


@pytest.mark.parametrize("corruption", ["member_table", "sql_target", "column_injection", "file_hash",
                                       "data_hash", "unexpected_field", "symlink", "outside"])
def test_untrusted_sources_rejected_before_credentials(tmp_path, monkeypatch, corruption):
    directory, registry = write_registry(tmp_path, monkeypatch)
    entry = registry["tables"][0]
    path = directory / entry["file"]
    if corruption == "member_table":
        entry["source_table"] = "TB_member"
    elif corruption == "sql_target":
        entry["target_table"] = "tb_manse"
    elif corruption == "column_injection":
        entry["columns"][0]["name"] = "num`; DROP TABLE member"
    elif corruption == "file_hash":
        path.write_text("[]")
    elif corruption == "data_hash":
        entry["data_sha256"] = "b" * 64
    elif corruption == "unexpected_field":
        values = json.loads(path.read_text())
        values[0]["unexpected"] = "not permitted"
        raw = json.dumps(values).encode()
        path.write_bytes(raw)
        entry["source_sha256"] = hashlib.sha256(raw).hexdigest()
    elif corruption == "symlink":
        original = directory / "other.json"
        path.rename(original)
        path.symlink_to(original)
    else:
        directory = tmp_path
    archive.REGISTRY.write_text(json.dumps(registry))
    monkeypatch.setattr(archive, "connect_mysql", lambda: pytest.fail("must validate before credentials"))
    with pytest.raises(archive.DatabaseCheckError):
        archive.import_mysql(directory)


class Connection:
    def __init__(self, snapshots):
        self.snapshots = snapshots
        self.by_target = {s.spec.target_table: s for s in snapshots}
        self.rows = {target: [] for target in self.by_target}
        self.metadata = []
        self.events = []
        self.transaction = None
        self.closed = False
        self.commits = self.rollbacks = 0
        self.database = "woonari"
        self.engine = "InnoDB"
        self.lock = 1
        self.triggers = 0
        self.bad_schema = self.bad_index = self.corrupt_readback = False
        self.fail_target = None

    def cursor(self):
        return Cursor(self)

    def autocommit(self, enabled):
        self.events.append(("autocommit", enabled))

    def begin(self):
        self.events.append(("begin", None))
        self.transaction = copy.deepcopy((self.rows, self.metadata))

    def commit(self):
        self.commits += 1
        self.events.append(("commit", None))
        self.transaction = None

    def rollback(self):
        self.rollbacks += 1
        if self.transaction is not None:
            self.rows, self.metadata = self.transaction
            self.transaction = None

    def close(self):
        self.closed = True


def schema_rows(connection):
    rows = []
    for target, snapshot in connection.by_target.items():
        for c in (column(archive.ORDINAL, "bigint", precision=19, length=8), *snapshot.spec.columns):
            mysql = c.mysql_type
            kind = mysql.split()[0].split("(")[0].lower()
            rows.append((target, c.name, kind, "YES" if c.nullable else "NO", "", mysql.lower(),
                         "utf8mb4_bin" if c.sql_type in archive.TEXT_TYPES else None,
                         c.precision, c.scale, 6 if kind in {"datetime", "time"} else None, None))
    for name, kind, length in [("source_table", "varchar", 128), ("source_sha256", "char", 64),
                               ("data_sha256", "char", 64), ("row_count", "bigint", None),
                               ("payload", "longtext", None)]:
        rows.append((archive.METADATA_TABLE, name, kind, "NO", "", kind,
                     None if kind == "bigint" else "utf8mb4_bin", 19, 0, None, length))
    return rows


class Cursor:
    def __init__(self, connection):
        self.connection = connection
        self.result = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def execute(self, sql, parameters=()):
        c = self.connection
        c.events.append((sql, parameters))
        self.result = []
        if sql == "SELECT DATABASE()":
            self.result = [(c.database,)]
        elif "GET_LOCK" in sql:
            self.result = [(c.lock,)]
        elif "RELEASE_LOCK" in sql:
            self.result = [(1,)]
        elif sql.startswith(("CREATE TABLE", "SET TRANSACTION")):
            pass
        elif "information_schema.TABLES" in sql:
            self.result = [(name, c.engine) for name in (*c.by_target, archive.METADATA_TABLE)]
        elif "information_schema.COLUMNS" in sql:
            self.result = schema_rows(c)
            if c.bad_schema:
                row = self.result[0]
                self.result[0] = (*row[:3], "YES", *row[4:])
        elif "information_schema.STATISTICS" in sql:
            self.result = [(name, "PRIMARY", 0, 1, archive.ORDINAL) for name in c.by_target]
            self.result.append((archive.METADATA_TABLE, "PRIMARY", 0, 1, "source_table"))
            if c.bad_index:
                self.result.pop()
        elif "information_schema.TRIGGERS" in sql:
            self.result = [(c.triggers,)]
        elif archive.METADATA_TABLE in sql:
            if sql.startswith("INSERT"):
                c.metadata.append(tuple(parameters))
            else:
                self.result = copy.deepcopy(c.metadata)
        else:
            table = re.search(r"FROM `woonari`\.`([^`]+)`", sql)
            if not table:
                raise AssertionError(sql)
            self.result = copy.deepcopy(c.rows[table[1]])
            if c.corrupt_readback and self.result:
                self.result[0] = (999, *self.result[0][1:])

    def executemany(self, sql, values):
        c = self.connection
        target = re.search(r"INSERT INTO `woonari`\.`([^`]+)`", sql)[1]
        if target == c.fail_target:
            raise RuntimeError("private simulated driver detail")
        c.events.append(("executemany", target))
        c.rows[target].extend(tuple(row) for row in values)

    def fetchone(self):
        return self.result[0]

    def fetchall(self):
        return self.result


def prepared_connection(tmp_path, monkeypatch, tables=None):
    directory, _registry = write_registry(tmp_path, monkeypatch, tables)
    snapshots = archive.local_snapshots(directory)
    connection = Connection(snapshots)
    monkeypatch.setattr(archive, "connect_mysql", lambda: connection)
    return directory, connection


def test_atomic_copy_empty_schema_and_idempotent_reexecution(tmp_path, monkeypatch):
    directory, c = prepared_connection(tmp_path, monkeypatch)
    result = archive.import_mysql(directory)
    assert [t["status"] for t in result["tables"]] == ["imported", "empty_schema_preserved"]
    assert result["row_count"] == 2 and result["table_count"] == 2
    assert not result["personal_data_imported"]
    before = copy.deepcopy((c.rows, c.metadata))
    again = archive.import_mysql(directory)
    assert all(t["status"] == "already_present" for t in again["tables"])
    assert (c.rows, c.metadata) == before
    assert c.commits == 2 and c.closed
    begin = next(i for i, event in enumerate(c.events) if event[0] == "begin")
    assert all(i < begin for i, event in enumerate(c.events[:begin])
               if event[0].startswith("CREATE TABLE"))
    assert not any(event[0].startswith(("UPDATE", "DELETE", "DROP", "TRUNCATE")) for event in c.events)


@pytest.mark.parametrize("failure", ["wrong_db", "lock", "engine", "schema", "index", "trigger"])
def test_schema_or_isolation_failure_never_inserts(tmp_path, monkeypatch, failure):
    directory, c = prepared_connection(tmp_path, monkeypatch)
    if failure == "wrong_db":
        c.database = "another_project"
    elif failure == "lock":
        c.lock = 0
    elif failure == "engine":
        c.engine = "MyISAM"
    elif failure == "schema":
        c.bad_schema = True
    elif failure == "index":
        c.bad_index = True
    else:
        c.triggers = 1
    with pytest.raises(archive.DatabaseCheckError):
        archive.import_mysql(directory)
    assert c.commits == 0 and not c.metadata and all(not rows for rows in c.rows.values())
    assert c.closed


def test_later_table_failure_rolls_back_earlier_rows_and_metadata(tmp_path, monkeypatch):
    tables = sample_tables()
    tables[1] = ("TB_BirthLuck", [column("num")], [{"num": 1}], ["num"])
    directory, c = prepared_connection(tmp_path, monkeypatch, tables)
    c.fail_target = c.snapshots[1].spec.target_table
    with pytest.raises(archive.DatabaseCheckError) as error:
        archive.import_mysql(directory)
    assert "private simulated driver detail" not in str(error.value)
    assert c.commits == 0 and c.rollbacks == 1
    assert not c.metadata and all(not rows for rows in c.rows.values())


def test_readback_corruption_rolls_back_all_data(tmp_path, monkeypatch):
    directory, c = prepared_connection(tmp_path, monkeypatch)
    c.corrupt_readback = True
    with pytest.raises(archive.DatabaseCheckError):
        archive.import_mysql(directory)
    assert c.commits == 0 and not c.metadata and all(not rows for rows in c.rows.values())


def test_existing_different_rows_are_never_overwritten(tmp_path, monkeypatch):
    directory, c = prepared_connection(tmp_path, monkeypatch)
    target = c.snapshots[0].spec.target_table
    c.rows[target] = [(1, 9, "existing data")]
    before = copy.deepcopy(c.rows)
    with pytest.raises(archive.DatabaseCheckError):
        archive.import_mysql(directory)
    assert c.rows == before and c.commits == 0


def test_modified_existing_provenance_is_not_adopted(tmp_path, monkeypatch):
    directory, c = prepared_connection(tmp_path, monkeypatch)
    archive.import_mysql(directory)
    row = c.metadata[0]
    c.metadata[0] = (row[0], "f" * 64, *row[2:])
    before = copy.deepcopy((c.rows, c.metadata))
    with pytest.raises(archive.DatabaseCheckError):
        archive.import_mysql(directory)
    assert (c.rows, c.metadata) == before


def test_dynamic_parameters_preserve_binary_and_all_precision(tmp_path, monkeypatch):
    tables = [("tbPreLife", [column("num"), column("when", "datetime"),
                               column("amount", "numeric", precision=18, scale=4),
                               column("binary", "varbinary"), column("valid", "bit")],
               [{"num": 1, "when": "2001-01-02T03:04:05.003", "amount": "123.4500",
                 "binary": "0x00ff", "valid": True}], ["num"])]
    directory, c = prepared_connection(tmp_path, monkeypatch, tables)
    archive.import_mysql(directory)
    row = next(iter(c.rows.values()))[0]
    assert row == (1, 1, "2001-01-02T03:04:05.003000", "123.4500", b"\x00\xff", 1)

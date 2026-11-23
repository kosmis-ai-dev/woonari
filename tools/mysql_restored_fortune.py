"""T-030 / CR-014: preserve allowlisted restored fortune tables in MySQL.

This stages source rows only. It does not assign meanings to the restored keys
or make them usable as personal fortune decisions.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools"))

from isolated_db import DatabaseCheckError, connect_mysql

DATABASE = "woonari"
METADATA_TABLE = "woonari_legacy_fortune_metadata"
METADATA_COLUMNS = ("source_table", "source_sha256", "data_sha256", "row_count", "payload")
COMMON_END = ("contents", *[f"idx_bujeok{i}" for i in range(1, 6)],
              "starPoint", *[f"score{i}" for i in range(1, 12)])
YEAR_COLUMNS = ("idx", "gan_ref", "gend_ref", "year_act", "chapter", *COMMON_END)
MONTH_COLUMNS = ("idx", "gan_ref", "gend_ref", "gan_act", "ji_act", *COMMON_END)
BATCH_SIZE = 100
LOCK_NAME = "woonari_cr014_restored_fortune"


@dataclass(frozen=True)
class TableSpec:
    source: str
    target: str
    columns: tuple[str, ...]
    natural_key: tuple[str, ...]
    source_sha256: str


YEAR = TableSpec(
    "TB_yearLuck", "woonari_legacy_year_luck", YEAR_COLUMNS,
    ("gan_ref", "gend_ref", "year_act", "chapter"),
    "869a1074b7c8e55c4fdd5ff45401317297ce2d10330e5fbeab7ee0a0d3c9e4b7",
)
MONTH = TableSpec(
    "TB_yearLuck_mon", "woonari_legacy_year_luck_month", MONTH_COLUMNS,
    ("gan_ref", "gend_ref", "gan_act", "ji_act"),
    "f427c8bb5d34da799f9b1c51f55863e9851e7f5db78b08a3b3edc8e8976e49d5",
)
SPECS = (YEAR, MONTH)


def data_digest(rows: list[tuple]) -> str:
    encoded = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def data_quality(spec: TableSpec, rows: list[tuple]) -> dict:
    """Separate structural coverage from populated source judgement data."""
    indexes = {name: index for index, name in enumerate(spec.columns)}
    content_index = indexes["contents"]
    score_indexes = [indexes[f"score{i}"] for i in range(1, 12)]

    def placeholder(row: tuple) -> bool:
        return (not row[content_index].strip() and row[indexes["starPoint"]] == 1
                and all(row[index] == 0 for index in score_indexes))

    result = {
        "blank_content_rows": sum(not row[content_index].strip() for row in rows),
        "placeholder_rows": sum(placeholder(row) for row in rows),
        "placeholder_definition": "blank_contents_and_starPoint_1_and_all_scores_0",
        "ready_for_personal_selection": False,
    }
    if spec.source == "TB_yearLuck":
        years = {}
        for row in rows:
            group = years.setdefault(row[indexes["year_act"]], {"row_count": 0, "populated": 0,
                                                              "placeholder": 0})
            group["row_count"] += 1
            group["populated"] += bool(row[content_index].strip())
            group["placeholder"] += placeholder(row)
        result.update({
            "populated_years": sorted(year for year, group in years.items()
                                      if group["populated"] == group["row_count"]),
            "placeholder_years": sorted(year for year, group in years.items()
                                        if group["placeholder"] == group["row_count"]),
            "year_counts": [{"year": year, **counts} for year, counts in sorted(years.items())],
        })
    return result


def _unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate field")
        result[key] = value
    return result


def validate_rows(spec: TableSpec, values: object) -> list[tuple]:
    """Validate raw storage types and full source coverage, without key semantics."""
    if not isinstance(values, list) or not values:
        raise ValueError("empty source")
    rows, ids, keys = [], set(), set()
    for item in values:
        if not isinstance(item, dict) or set(item) != set(spec.columns):
            raise ValueError("unexpected fields")
        normalized = {}
        for name in spec.columns:
            value = item[name]
            if name == "contents":
                if not isinstance(value, str) or len(value.encode("utf-8")) > 1_000_000:
                    raise ValueError("invalid text")
            elif name == "gend_ref":
                if type(value) is not bool:
                    raise ValueError("invalid source bit")
                value = int(value)
            else:
                if type(value) is not int:
                    raise ValueError("invalid source integer")
                limits = ((1, 2_147_483_647) if name == "idx" else
                          (0, 2_147_483_647) if name.startswith("idx_bujeok") else
                          (2001, 2050) if name == "year_act" else
                          (1, 7) if name == "chapter" else
                          (1, 5) if name == "starPoint" else
                          (0, 255) if name.startswith("score") else
                          (0, 11) if name == "ji_act" else (0, 9))
                if not limits[0] <= value <= limits[1]:
                    raise ValueError("integer out of range")
            normalized[name] = value
        key = tuple(normalized[name] for name in spec.natural_key)
        if normalized["idx"] in ids or key in keys:
            raise ValueError("duplicate key")
        ids.add(normalized["idx"])
        keys.add(key)
        rows.append(tuple(normalized[name] for name in spec.columns))
    if spec.source == "TB_yearLuck":
        expected = set(itertools.product(range(10), range(2), range(2001, 2051), range(1, 8)))
    else:
        pairs = {(gan, ji) for gan in range(10) for ji in range(12) if gan % 2 == ji % 2}
        expected = {(gan, gender, act_gan, act_ji)
                    for gan, gender in itertools.product(range(10), range(2))
                    for act_gan, act_ji in pairs}
    if keys != expected:
        raise ValueError("incomplete source coverage")
    return sorted(rows, key=lambda row: row[0])


def local_snapshots(directory: Path) -> list[tuple[TableSpec, list[tuple], dict]]:
    try:
        root = ROOT / ".local/woonari/restore"
        directory = Path(directory)
        directory.resolve(strict=True).relative_to(root.resolve(strict=True))
        result = []
        for spec in SPECS:
            path = directory / f"{spec.source}.json"
            if path.is_symlink() or not path.is_file():
                raise ValueError("not a regular export")
            raw = path.read_bytes()
            if not spec.source_sha256 or hashlib.sha256(raw).hexdigest() != spec.source_sha256:
                raise ValueError("source digest mismatch")
            values = json.loads(raw, object_pairs_hook=_unique_object)
            rows = validate_rows(spec, values)
            metadata = {
                "format": "woonari.restored-fortune.v1", "source_table": spec.source,
                "source_sha256": spec.source_sha256, "data_sha256": data_digest(rows),
                "row_count": len(rows), "mapping_status": "unverified",
                "source_backup": "dbkosmis_20251106.bak",
                "excluded_columns": ["date_write", "date_edit"],
                "columns": list(spec.columns), "natural_key": list(spec.natural_key),
                "quality": data_quality(spec, rows),
            }
            result.append((spec, rows, metadata))
        return result
    except Exception:  # noqa: BLE001 - never expose source text or private paths
        raise DatabaseCheckError("복원 판정 자료의 출처 해시·열·형식·전체 키 범위를 검증하지 못했습니다.") from None


def _quoted(columns: tuple[str, ...]) -> str:
    return ", ".join(f"`{name}`" for name in columns)


def _create_tables(cursor) -> None:
    # DDL commits implicitly: create only new, explicitly named staging tables.
    for spec in SPECS:
        columns = ", ".join(
            f"`{name}` LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL"
            if name == "contents" else f"`{name}` INT NOT NULL"
            for name in spec.columns
        )
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS `{DATABASE}`.`{spec.target}` ({columns}, "
            f"PRIMARY KEY (`idx`), UNIQUE KEY `source_lookup` ({_quoted(spec.natural_key)})) "
            "ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin"
        )
    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS `{DATABASE}`.`{METADATA_TABLE}` ("
        "`source_table` VARCHAR(32) NOT NULL, `source_sha256` CHAR(64) NOT NULL, "
        "`data_sha256` CHAR(64) NOT NULL, `row_count` INT NOT NULL, "
        "`payload` LONGTEXT NOT NULL, PRIMARY KEY (`source_table`)) "
        "ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin"
    )


def _verify_schema(cursor) -> None:
    for spec in (*SPECS, None):
        table = spec.target if spec else METADATA_TABLE
        expected = spec.columns if spec else METADATA_COLUMNS
        cursor.execute(
            "SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s",
            (DATABASE, table),
        )
        if cursor.fetchone() != ("InnoDB",):
            raise DatabaseCheckError("복원 판정표 적재 대상에 InnoDB 엔진이 필요합니다.")
        cursor.execute(
            "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, EXTRA, CHARACTER_MAXIMUM_LENGTH, "
            "COLLATION_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s "
            "ORDER BY ORDINAL_POSITION", (DATABASE, table),
        )
        actual = cursor.fetchall()
        types = (tuple("longtext" if name == "contents" else "int" for name in expected)
                 if spec else ("varchar", "char", "char", "int", "longtext"))
        if (tuple(row[0] for row in actual) != expected
                or tuple(row[1] for row in actual) != types
                or any(row[2] != "NO" or row[3] for row in actual)
                or any(row[5] != "utf8mb4_bin" for row in actual if row[1] != "int")
                or (not spec and tuple(row[4] for row in actual[:3]) != (32, 64, 64))):
            raise DatabaseCheckError("기존 복원 판정표의 열·문자열 형식이 다릅니다. 기존 데이터를 보존합니다.")
        cursor.execute(
            "SELECT INDEX_NAME, NON_UNIQUE, SEQ_IN_INDEX, COLUMN_NAME FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY INDEX_NAME, SEQ_IN_INDEX",
            (DATABASE, table),
        )
        indexes = {}
        for name, non_unique, _position, column in cursor.fetchall():
            indexes.setdefault((name, non_unique), []).append(column)
        desired = ({("PRIMARY", 0): ["idx"], ("source_lookup", 0): list(spec.natural_key)}
                   if spec else {("PRIMARY", 0): ["source_table"]})
        if indexes != desired:
            raise DatabaseCheckError("복원 판정표의 원본 유일 키 구성이 다릅니다.")
    targets = tuple(spec.target for spec in SPECS) + (METADATA_TABLE,)
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE EVENT_OBJECT_SCHEMA=%s "
        "AND EVENT_OBJECT_TABLE IN (%s, %s, %s)", (DATABASE, *targets),
    )
    if cursor.fetchone() != (0,):
        raise DatabaseCheckError("트리거가 있는 복원 판정표는 자동 적재하지 않습니다.")


def _remote_rows(cursor, spec: TableSpec) -> list[tuple]:
    cursor.execute(
        f"SELECT {_quoted(spec.columns)} FROM `{DATABASE}`.`{spec.target}` ORDER BY `idx` FOR UPDATE"
    )
    rows = [tuple(row) for row in cursor.fetchall()]
    for row in rows:
        if (len(row) != len(spec.columns)
                or any((not isinstance(value, str) if name == "contents" else type(value) is not int)
                       for name, value in zip(spec.columns, row, strict=True))):
            raise DatabaseCheckError("MySQL 복원 판정 자료의 열 형식이 다릅니다.")
    return rows


def _copy_data(cursor, snapshots: list[tuple[TableSpec, list[tuple], dict]]) -> list[dict]:
    cursor.execute(
        f"SELECT {_quoted(METADATA_COLUMNS)} FROM `{DATABASE}`.`{METADATA_TABLE}` FOR UPDATE"
    )
    existing_metadata = {row[0]: tuple(row) for row in cursor.fetchall()}
    if set(existing_metadata) - {spec.source for spec in SPECS}:
        raise DatabaseCheckError("복원 판정표에 알 수 없는 출처 정보가 있어 적재를 중단했습니다.")
    reports = []
    for spec, rows, metadata in snapshots:
        remote = _remote_rows(cursor, spec)
        payload = json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        expected_meta = (spec.source, metadata["source_sha256"], metadata["data_sha256"],
                         metadata["row_count"], payload)
        previous_meta = existing_metadata.get(spec.source)
        if previous_meta:
            try:
                matched = (previous_meta[:4] == expected_meta[:4]
                           and len(previous_meta) == 5 and json.loads(previous_meta[4]) == metadata)
            except (ValueError, TypeError, RecursionError):
                matched = False
            if not matched:
                raise DatabaseCheckError("기존 복원 판정표 출처 정보가 다릅니다. 기존 데이터를 보존합니다.")
        if remote:
            if remote != rows or data_digest(remote) != metadata["data_sha256"]:
                raise DatabaseCheckError("기존 복원 판정 데이터가 다릅니다. 기존 데이터를 보존합니다.")
            status = "already_present"
        else:
            if previous_meta:
                raise DatabaseCheckError("복원 판정표 행과 출처 정보가 일치하지 않습니다.")
            statement = (f"INSERT INTO `{DATABASE}`.`{spec.target}` ({_quoted(spec.columns)}) "
                         f"VALUES ({', '.join('%s' for _ in spec.columns)})")
            for offset in range(0, len(rows), BATCH_SIZE):
                cursor.executemany(statement, rows[offset:offset + BATCH_SIZE])
            copied = _remote_rows(cursor, spec)
            if copied != rows or data_digest(copied) != metadata["data_sha256"]:
                raise DatabaseCheckError("적재 후 원본 데이터 해시가 달라 전체 적재를 취소했습니다.")
            status = "imported"
        if not previous_meta:
            cursor.execute(
                f"INSERT INTO `{DATABASE}`.`{METADATA_TABLE}` ({_quoted(METADATA_COLUMNS)}) "
                "VALUES (%s, %s, %s, %s, %s)", expected_meta,
            )
        reports.append({"source_table": spec.source, "table": spec.target, "status": status,
                        "row_count": len(rows), "data_sha256": metadata["data_sha256"],
                        "source_sha256": spec.source_sha256, "mapping_status": "unverified"})
    return reports


def import_mysql(directory: Path) -> dict:
    snapshots = local_snapshots(directory)  # Validate everything before obtaining credentials.
    connection = connect_mysql()
    locked = False
    try:
        connection.autocommit(True)
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            if cursor.fetchone() != (DATABASE,):
                raise DatabaseCheckError("복원 판정 자료는 woonari 데이터베이스에만 적재합니다.")
            cursor.execute("SELECT GET_LOCK(%s, 2)", (LOCK_NAME,))
            if cursor.fetchone() != (1,):
                raise DatabaseCheckError("다른 복원 판정 자료 적재가 진행 중입니다.")
            locked = True
            _create_tables(cursor)
            _verify_schema(cursor)
        connection.autocommit(False)
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        connection.begin()
        with connection.cursor() as cursor:
            tables = _copy_data(cursor, snapshots)
        connection.commit()
        return {"database": DATABASE, "tables": tables, "runtime_enabled": False}
    except DatabaseCheckError:
        with suppress(Exception):
            connection.rollback()
        raise
    except Exception:  # noqa: BLE001 - driver errors may contain source and connection details
        with suppress(Exception):
            connection.rollback()
        raise DatabaseCheckError("MySQL 복원 판정표 적재 또는 검증에 실패했습니다.") from None
    finally:
        if locked:
            with suppress(Exception), connection.cursor() as cursor:
                cursor.execute("SELECT RELEASE_LOCK(%s)", (LOCK_NAME,))
        with suppress(Exception):
            connection.close()


def main(args: list[str]) -> int:
    parser = argparse.ArgumentParser(description="검증한 복원 판정표를 woonari의 별도 표에 보존합니다.")
    parser.add_argument("source_directory", type=Path)
    options = parser.parse_args(args)
    try:
        report = import_mysql(options.source_directory)
    except DatabaseCheckError as error:
        print(f"Woonari 복원 판정표: {error}", file=sys.stderr)
        return 1
    except Exception:  # noqa: BLE001 - never emit arbitrary errors or source contents
        print("Woonari 복원 판정표: 적재 도구 실행에 실패했습니다.", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""T-017 / CR-009: copy validated local tb_manse data into the project MySQL."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from contextlib import suppress
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "python_api"))

from app.manse_store import COLUMNS, ManseStore, data_digest
from isolated_db import DatabaseCheckError, connect_mysql

TABLE = "tb_manse"
METADATA_TABLE = "woonari_manse_metadata"
PROVENANCE_COLUMNS = ("source_sha256", "data_sha256", "row_count")
METADATA_COLUMNS = (*PROVENANCE_COLUMNS, "payload")
SELECT_COLUMNS = ", ".join(f"`{column}`" for column in COLUMNS)
SOLAR_COLUMNS = ("s_year", "s_mon", "s_day")
LUNAR_COLUMNS = ("l_year", "l_mon", "l_day", "leafMon_YN")
BATCH_SIZE = 500


def _database_name(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", value):
        raise DatabaseCheckError("MySQL DB 이름은 영문자로 시작하는 영문·숫자·밑줄 1~64자여야 합니다.")
    return value


def _local_snapshot() -> tuple[list[tuple], dict]:
    try:
        store = ManseStore()
        metadata = store.metadata()
        rows = list(store.iter_records())
        valid = (
            type(metadata["row_count"]) is int
            and metadata["row_count"] == len(rows)
            and len(rows) > 0
            and all(isinstance(metadata[key], str) and re.fullmatch(r"[a-f0-9]{64}", metadata[key])
                    for key in ("source_sha256", "data_sha256"))
            and data_digest(rows) == metadata["data_sha256"]
        )
        if not valid:
            raise ValueError("invalid local snapshot")
        json.dumps(metadata, ensure_ascii=False)
        return rows, metadata
    except Exception:  # noqa: BLE001 - local DB errors must not expose SQL or private paths
        raise DatabaseCheckError("로컬 만세력 DB의 원본 정보·행 수·데이터 해시를 확인하지 못했습니다.") from None


def _create_tables(cursor, database: str) -> None:
    # MySQL DDL commits implicitly, so all DDL precedes the data transaction.
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4")
    integer_columns = ", ".join(f"`{column}` INT NOT NULL" for column in COLUMNS[:-1])
    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS `{database}`.`{TABLE}` ("
        f"{integer_columns}, `sDate` DATE NOT NULL, PRIMARY KEY (`idx`), "
        "UNIQUE KEY `manse_solar_lookup` (`s_year`, `s_mon`, `s_day`), "
        "KEY `manse_lunar_lookup` (`l_year`, `l_mon`, `l_day`, `leafMon_YN`)"
        ") ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4"
    )
    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS `{database}`.`{METADATA_TABLE}` ("
        "`source_sha256` CHAR(64) NOT NULL, `data_sha256` CHAR(64) NOT NULL, "
        "`row_count` INT NOT NULL, `payload` LONGTEXT NOT NULL, PRIMARY KEY (`source_sha256`)"
        ") ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4"
    )


def _verify_schema(cursor, database: str) -> None:
    for table, columns in ((TABLE, COLUMNS), (METADATA_TABLE, METADATA_COLUMNS)):
        cursor.execute(
            "SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s",
            (database, table),
        )
        engine = cursor.fetchone()
        if not engine or str(engine[0]).casefold() != "innodb":
            raise DatabaseCheckError("만세력 적재 대상 테이블에 InnoDB 엔진이 필요합니다.")
        cursor.execute(
            "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, EXTRA FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION",
            (database, table),
        )
        schema = cursor.fetchall()
        expected_types = (("int",) * 17 + ("date",) if table == TABLE
                          else ("char", "char", "int", "longtext"))
        if (tuple(row[0] for row in schema) != columns
                or tuple(str(row[1]).lower() for row in schema) != expected_types
                or any(row[2] != "NO" or row[3] for row in schema)):
            raise DatabaseCheckError("기존 MySQL 만세력 테이블의 열 구성이 가져오기 형식과 다릅니다.")
    cursor.execute(
        "SELECT INDEX_NAME, NON_UNIQUE, SEQ_IN_INDEX, COLUMN_NAME FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s ORDER BY INDEX_NAME, SEQ_IN_INDEX",
        (database, TABLE),
    )
    indexes = {}
    for name, non_unique, _position, column in cursor.fetchall():
        indexes.setdefault((name, non_unique), []).append(column)
    unique = {tuple(columns) for (_name, non_unique), columns in indexes.items() if non_unique == 0}
    ordinary = {tuple(columns) for (_name, non_unique), columns in indexes.items() if non_unique == 1}
    if (tuple(indexes.get(("PRIMARY", 0), [])) != ("idx",)
            or unique != {("idx",), SOLAR_COLUMNS} or LUNAR_COLUMNS not in ordinary):
        raise DatabaseCheckError("양력 유일 키와 중복을 허용하는 음력 조회 인덱스가 필요합니다.")
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE EVENT_OBJECT_SCHEMA = %s "
        "AND EVENT_OBJECT_TABLE IN (%s, %s)",
        (database, TABLE, METADATA_TABLE),
    )
    if cursor.fetchone() != (0,):
        raise DatabaseCheckError("기존 트리거가 있는 만세력 테이블은 자동 적재할 수 없습니다.")


def _remote_rows(cursor, database: str) -> list[tuple]:
    cursor.execute(
        f"SELECT {SELECT_COLUMNS} FROM `{database}`.`{TABLE}` ORDER BY `idx` FOR UPDATE"
    )
    rows = []
    for record in cursor.fetchall():
        values = tuple(record)
        if len(values) != len(COLUMNS) or any(type(value) is not int for value in values[:-1]):
            raise DatabaseCheckError("MySQL 만세력 데이터 형식을 확인하지 못했습니다.")
        day = values[-1]
        if isinstance(day, date) and not isinstance(day, datetime):
            day = day.isoformat()
        if not isinstance(day, str):
            raise DatabaseCheckError("MySQL 만세력 날짜 형식을 확인하지 못했습니다.")
        rows.append((*values[:-1], day))
    return rows


def _matches(rows: list[tuple], metadata: dict) -> bool:
    return len(rows) == metadata["row_count"] and data_digest(rows) == metadata["data_sha256"]


def _copy_data(cursor, database: str, rows: list[tuple], metadata: dict) -> str:
    existing = _remote_rows(cursor, database)
    cursor.execute(
        f"SELECT `source_sha256`, `data_sha256`, `row_count`, `payload` "
        f"FROM `{database}`.`{METADATA_TABLE}` FOR UPDATE"
    )
    existing_metadata = cursor.fetchall()
    provenance = tuple(metadata[column] for column in PROVENANCE_COLUMNS)
    payload = json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    expected_metadata = (*provenance, payload)
    if existing_metadata:
        try:
            same_metadata = (
                len(existing_metadata) == 1
                and tuple(existing_metadata[0][:3]) == provenance
                and len(existing_metadata[0]) == len(METADATA_COLUMNS)
                and json.loads(existing_metadata[0][3]) == metadata
            )
        except (ValueError, TypeError, RecursionError):
            same_metadata = False
        if not same_metadata:
            raise DatabaseCheckError("기존 MySQL 만세력 출처 정보가 다릅니다. 기존 데이터를 보존하고 중단했습니다.")
    if existing:
        if not _matches(existing, metadata):
            raise DatabaseCheckError("기존 MySQL 만세력 데이터가 다릅니다. 기존 데이터를 보존하고 중단했습니다.")
        status = "already_present"
    else:
        if existing_metadata:
            raise DatabaseCheckError("MySQL 만세력 행과 출처 정보가 일치하지 않습니다. 적재를 중단했습니다.")
        placeholders = ", ".join("%s" for _ in COLUMNS)
        statement = (
            f"INSERT INTO `{database}`.`{TABLE}` ({SELECT_COLUMNS}) VALUES ({placeholders})"
        )
        for offset in range(0, len(rows), BATCH_SIZE):
            cursor.executemany(statement, rows[offset:offset + BATCH_SIZE])
        if not _matches(_remote_rows(cursor, database), metadata):
            raise DatabaseCheckError("적재 후 만세력 행 수 또는 데이터 해시가 달라 전체 적재를 취소했습니다.")
        status = "imported"
    if not existing_metadata:
        cursor.execute(
            f"INSERT INTO `{database}`.`{METADATA_TABLE}` "
            "(`source_sha256`, `data_sha256`, `row_count`, `payload`) VALUES (%s, %s, %s, %s)",
            expected_metadata,
        )
    return status


def import_mysql(database: str = "woonari") -> dict:
    database = _database_name(database)
    rows, metadata = _local_snapshot()
    connection = connect_mysql(select_database=False)
    lock_name = "woonari_manse_" + hashlib.sha256(database.encode("ascii")).hexdigest()[:48]
    locked = False
    try:
        connection.autocommit(True)
        with connection.cursor() as cursor:
            cursor.execute("SELECT GET_LOCK(%s, 2)", (lock_name,))
            if cursor.fetchone() != (1,):
                raise DatabaseCheckError("다른 만세력 적재 작업이 진행 중입니다. 완료 후 다시 실행해 주세요.")
            locked = True
            _create_tables(cursor, database)
            _verify_schema(cursor, database)
        connection.autocommit(False)
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        connection.begin()
        with connection.cursor() as cursor:
            status = _copy_data(cursor, database, rows, metadata)
        connection.commit()
        return {"database": database, "table": TABLE, "status": status,
                **{key: metadata[key] for key in PROVENANCE_COLUMNS}}
    except DatabaseCheckError:
        with suppress(Exception):
            connection.rollback()
        raise
    except Exception:  # noqa: BLE001 - driver messages can contain connection values
        with suppress(Exception):
            connection.rollback()
        raise DatabaseCheckError("MySQL 만세력 적재 또는 데이터 검증에 실패했습니다.") from None
    finally:
        if locked:
            with suppress(Exception), connection.cursor() as cursor:
                cursor.execute("SELECT RELEASE_LOCK(%s)", (lock_name,))
        with suppress(Exception):
            connection.close()


def main(args: list[str]) -> int:
    parser = argparse.ArgumentParser(description="검증한 로컬 만세력 DB를 MySQL에 적재합니다.")
    parser.add_argument("--database", default="woonari")
    options = parser.parse_args(args)
    try:
        report = import_mysql(options.database)
    except DatabaseCheckError as error:
        print(f"Woonari 만세력: {error}", file=sys.stderr)
        return 1
    except Exception:  # noqa: BLE001 - CLI never exposes arbitrary exception details
        print("Woonari 만세력: MySQL 적재 도구 실행에 실패했습니다.", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

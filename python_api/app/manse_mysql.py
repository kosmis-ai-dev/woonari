"""T-017: query the explicitly configured MySQL copy of original tb_manse."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager, suppress
from datetime import date, datetime
from typing import Any

from app.manse_store import (
    COLUMNS,
    FORMAT_NAME,
    KST,
    SCHEMA_VERSION,
    TERM_NAMES,
    ManseDataError,
    term_datetime,
)

SELECT_COLUMNS = ", ".join(f"`{column}`" for column in COLUMNS)
UNAVAILABLE = "MySQL 원본 만세력 데이터를 읽을 수 없습니다."


def _normalize_record(row) -> dict:
    try:
        if isinstance(row, Mapping):
            result = {column: row[column] for column in COLUMNS}
        else:
            if len(row) != len(COLUMNS):
                raise ValueError
            result = dict(zip(COLUMNS, row))
        for column in COLUMNS[:-1]:
            value = result[column]
            if type(value) is not int:
                raise ValueError
        stored_date = result["sDate"]
        if isinstance(stored_date, datetime):
            if stored_date.time() != datetime.min.time():
                raise ValueError
            stored_date = stored_date.date()
        if isinstance(stored_date, str):
            stored_date = date.fromisoformat(stored_date)
        if type(stored_date) is not date:
            raise ValueError
        if stored_date != date(result["s_year"], result["s_mon"], result["s_day"]):
            raise ValueError
        result["sDate"] = stored_date.isoformat()
        return result
    except (KeyError, ValueError, TypeError, OverflowError):
        raise ManseDataError("manse_unavailable", UNAVAILABLE) from None


def _metadata(row) -> dict:
    try:
        if isinstance(row, Mapping):
            source, digest, count, payload = (
                row["source_sha256"], row["data_sha256"], row["row_count"], row["payload"],
            )
        else:
            source, digest, count, payload = row
        metadata = json.loads(payload)
        if (
            not isinstance(metadata, dict)
            or metadata["format"] != FORMAT_NAME
            or metadata["schema_version"] != SCHEMA_VERSION
            or type(count) is not int
            or count < 1
            or metadata["row_count"] != count
            or metadata["source_sha256"] != source
            or metadata["data_sha256"] != digest
            or not isinstance(source, str)
            or not isinstance(digest, str)
            or re.fullmatch(r"[a-f0-9]{64}", source) is None
            or re.fullmatch(r"[a-f0-9]{64}", digest) is None
        ):
            raise ValueError
        first = date.fromisoformat(metadata["min_date"])
        last = date.fromisoformat(metadata["max_date"])
        if first > last or (last - first).days + 1 != count:
            raise ValueError
        return metadata
    except (KeyError, ValueError, TypeError, OverflowError, RecursionError):
        raise ManseDataError("manse_unavailable", "MySQL 만세력 출처 정보가 올바르지 않습니다.") from None


class MySQLManseStore:
    backend = "mysql"

    def __init__(self, connector: Callable[[], Any]):
        self.connector = connector

    @contextmanager
    def _connection(self):
        connection = None
        try:
            connection = self.connector()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT source_sha256, data_sha256, row_count, payload "
                    "FROM woonari_manse_metadata LIMIT 2"
                )
                rows = cursor.fetchall()
            if len(rows) != 1:
                raise ManseDataError("manse_unavailable", "MySQL 만세력 출처 정보가 올바르지 않습니다.")
            yield connection, _metadata(rows[0])
        except ManseDataError:
            raise
        except Exception:  # noqa: BLE001 - driver exceptions can contain credentials or endpoints
            raise ManseDataError("manse_unavailable", UNAVAILABLE) from None
        finally:
            if connection is not None:
                with suppress(Exception):
                    connection.close()

    def metadata(self) -> dict:
        with self._connection() as (_, metadata):
            return metadata

    def solar_record(self, day: date) -> dict:
        if not isinstance(day, date) or isinstance(day, datetime):
            raise ManseDataError("date_not_found", "양력 날짜를 확인해 주세요.")
        with self._connection() as (connection, _):
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT {SELECT_COLUMNS} FROM tb_manse "
                    "WHERE s_year = %s AND s_mon = %s AND s_day = %s LIMIT 2",
                    (day.year, day.month, day.day),
                )
                rows = cursor.fetchall()
        if len(rows) > 1:
            raise ManseDataError("manse_unavailable", "MySQL 만세력의 양력 날짜가 중복되어 있습니다.")
        if not rows:
            raise ManseDataError("date_not_found", "해당 양력 날짜의 원본 만세력 자료가 없습니다.")
        return _normalize_record(rows[0])

    def lunar_record(self, year: int, month: int, day: int, leap: bool | int) -> dict:
        if (
            any(type(value) is not int for value in (year, month, day))
            or not 1 <= month <= 12
            or not 1 <= day <= 30
            or type(leap) not in (bool, int)
            or leap not in (0, 1)
        ):
            raise ManseDataError("invalid_lunar_date", "음력 날짜와 윤달 여부를 확인해 주세요.")
        with self._connection() as (connection, _):
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT {SELECT_COLUMNS} FROM tb_manse "
                    "WHERE l_year = %s AND l_mon = %s AND l_day = %s AND leafMon_YN = %s LIMIT 2",
                    (year, month, day, int(leap)),
                )
                rows = cursor.fetchall()
        if len(rows) > 1:
            raise ManseDataError(
                "ambiguous_lunar_date", "원본 만세력에 같은 음력 날짜가 중복되어 양력 날짜를 확정할 수 없습니다."
            )
        if not rows:
            raise ManseDataError("invalid_lunar_date", "해당 음력 날짜의 원본 만세력 자료가 없습니다.")
        return _normalize_record(rows[0])

    def lunar_candidates(self, year: int, month: int, day: int) -> list[dict]:
        """Query unfiltered original rows so corrected leap flags can be matched."""
        if (
            any(type(value) is not int for value in (year, month, day))
            or not 1 <= month <= 12
            or not 1 <= day <= 30
        ):
            raise ManseDataError("invalid_lunar_date", "음력 날짜를 확인해 주세요.")
        with self._connection() as (connection, _):
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT {SELECT_COLUMNS} FROM tb_manse "
                    "WHERE l_year = %s AND l_mon = %s AND l_day = %s ORDER BY sDate",
                    (year, month, day),
                )
                rows = cursor.fetchall()
        return [_normalize_record(row) for row in rows]

    def solar_terms(self, moment: datetime) -> tuple[dict | None, dict | None]:
        if not isinstance(moment, datetime) or moment.tzinfo is None or moment.utcoffset() is None:
            raise ManseDataError("invalid_datetime", "절기 조회 시각에 시간대가 필요합니다.")
        try:
            current = moment.astimezone(KST).replace(second=0, microsecond=0)
        except (ValueError, OverflowError):
            raise ManseDataError("invalid_datetime", "절기 조회 시각을 확인해 주세요.") from None
        with self._connection() as (connection, metadata):
            first_year = date.fromisoformat(metadata["min_date"]).year
            last_year = date.fromisoformat(metadata["max_date"]).year
            year = min(max(current.year, first_year), last_year)
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT {SELECT_COLUMNS} FROM tb_manse "
                    "WHERE s_year BETWEEN %s AND %s AND MOD(div_name, 2) = 1 ORDER BY sDate LIMIT 100",
                    (max(first_year, year - 1), min(last_year, year + 1)),
                )
                rows = cursor.fetchall()
        terms = []
        for row in rows:
            record = _normalize_record(row)
            code = record["div_name"]
            if not 1 <= code <= 24 or code % 2 != 1:
                raise ManseDataError("manse_unavailable", UNAVAILABLE)
            record["name"] = TERM_NAMES[code]
            record["at"] = term_datetime(record).isoformat()
            terms.append(record)
        terms.sort(key=term_datetime)
        previous, following = None, None
        for record in terms:
            if term_datetime(record) <= current:
                previous = record
            else:
                following = record
                break
        return previous, following

    def iter_records(self) -> Iterator[tuple]:
        with self._connection() as (connection, _):
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT {SELECT_COLUMNS} FROM tb_manse ORDER BY idx")
                while True:
                    rows = cursor.fetchmany(1000)
                    if not rows:
                        break
                    for row in rows:
                        record = _normalize_record(row)
                        yield tuple(record[column] for column in COLUMNS)

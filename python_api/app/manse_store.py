"""T-017: read the original, imported tb_manse records without recalculation."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

KST = timezone(timedelta(hours=9))
DEFAULT_DATABASE = Path(__file__).resolve().parent / "data/manse.sqlite3"
APPLICATION_ID = 0x574D4E53
SCHEMA_VERSION = 1
FORMAT_NAME = "woonari.tb_manse.v1"
COLUMNS = (
    "idx", "s_year", "s_mon", "s_day", "l_year", "l_mon", "l_day", "leafMon_YN",
    "div_hour", "div_min", "div_name", "y_gan", "y_ji", "m_gan", "m_ji",
    "d_gan", "d_ji", "sDate",
)
TERM_NAMES = (
    "", "立春", "雨水", "驚蟄", "春分", "清明", "穀雨", "立夏", "小滿",
    "芒種", "夏至", "小暑", "大暑", "立秋", "處暑", "白露", "秋分",
    "寒露", "霜降", "立冬", "小雪", "大雪", "冬至", "小寒", "大寒",
)
SELECT_COLUMNS = ", ".join(f'"{column}"' for column in COLUMNS)
SQLITE_TABLE_DDL = """CREATE TABLE tb_manse (
    idx INTEGER PRIMARY KEY,
    s_year INTEGER NOT NULL,
    s_mon INTEGER NOT NULL,
    s_day INTEGER NOT NULL,
    l_year INTEGER NOT NULL,
    l_mon INTEGER NOT NULL,
    l_day INTEGER NOT NULL,
    leafMon_YN INTEGER NOT NULL CHECK (leafMon_YN IN (0, 1)),
    div_hour INTEGER NOT NULL CHECK (div_hour BETWEEN 0 AND 24),
    div_min INTEGER NOT NULL CHECK (div_min BETWEEN 0 AND 59),
    div_name INTEGER NOT NULL CHECK (div_name BETWEEN 0 AND 24),
    y_gan INTEGER NOT NULL CHECK (y_gan BETWEEN 0 AND 9),
    y_ji INTEGER NOT NULL CHECK (y_ji BETWEEN 0 AND 11),
    m_gan INTEGER NOT NULL CHECK (m_gan BETWEEN 0 AND 9),
    m_ji INTEGER NOT NULL CHECK (m_ji BETWEEN 0 AND 11),
    d_gan INTEGER NOT NULL CHECK (d_gan BETWEEN 0 AND 9),
    d_ji INTEGER NOT NULL CHECK (d_ji BETWEEN 0 AND 11),
    sDate TEXT NOT NULL UNIQUE,
    UNIQUE (s_year, s_mon, s_day)
)"""
SQLITE_INDEX_DDL = (
    "CREATE INDEX manse_lunar_lookup ON tb_manse(l_year, l_mon, l_day, leafMon_YN)",
    "CREATE INDEX manse_division_lookup ON tb_manse(div_name, sDate)",
)
SQLITE_TERMS_DDL = """CREATE TABLE manse_terms (
    idx INTEGER PRIMARY KEY REFERENCES tb_manse(idx),
    term_at TEXT NOT NULL UNIQUE
)"""
SQLITE_METADATA_DDL = """CREATE TABLE manse_metadata (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    payload TEXT NOT NULL
)"""
INSERT_SQL = (
    f"INSERT INTO tb_manse ({SELECT_COLUMNS}) VALUES ({', '.join('?' for _ in COLUMNS)})"
)


class ManseDataError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def data_digest(rows: Iterable[tuple]) -> str:
    """Hash exact column values in idx order, independently of the DB engine."""
    digest = hashlib.sha256()
    for row in rows:
        encoded = json.dumps(list(row), ensure_ascii=False, separators=(",", ":"))
        digest.update(encoded.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


record_digest = data_digest


def term_datetime(record: dict) -> datetime:
    try:
        day = date(record["s_year"], record["s_mon"], record["s_day"])
        return datetime.combine(day, datetime.min.time(), KST) + timedelta(
            hours=record["div_hour"], minutes=record["div_min"]
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        raise ManseDataError("manse_unavailable", "만세력 절기 자료를 읽을 수 없습니다.") from None


class ManseStore:
    backend = "sqlite"

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path is not None else DEFAULT_DATABASE

    @contextmanager
    def _connection(self):
        connection = None
        try:
            if not self.path.is_file():
                raise ManseDataError("manse_unavailable", "원본 만세력 데이터가 설치되어 있지 않습니다.")
            uri = self.path.resolve().as_uri() + "?mode=ro"
            connection = sqlite3.connect(uri, uri=True, timeout=3)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA query_only = ON")
            application_id = connection.execute("PRAGMA application_id").fetchone()[0]
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if application_id != APPLICATION_ID or version != SCHEMA_VERSION:
                raise ManseDataError("manse_unavailable", "지원하는 원본 만세력 데이터 형식이 아닙니다.")
            yield connection
        except ManseDataError:
            raise
        except (sqlite3.Error, OSError, ValueError, TypeError):
            raise ManseDataError("manse_unavailable", "원본 만세력 데이터를 읽을 수 없습니다.") from None
        finally:
            if connection is not None:
                connection.close()

    def metadata(self) -> dict:
        with self._connection() as connection:
            result = connection.execute("SELECT payload FROM manse_metadata WHERE id = 1").fetchone()
            if result is None:
                raise ManseDataError("manse_unavailable", "원본 만세력 출처 정보가 없습니다.")
            try:
                metadata = json.loads(result[0])
                valid = (
                    metadata["format"] == FORMAT_NAME
                    and metadata["schema_version"] == SCHEMA_VERSION
                    and type(metadata["row_count"]) is int
                    and metadata["row_count"] > 0
                )
            except (ValueError, KeyError, TypeError, RecursionError):
                valid = False
            if not valid:
                raise ManseDataError("manse_unavailable", "원본 만세력 출처 정보가 올바르지 않습니다.")
            return metadata

    def solar_record(self, day: date) -> dict:
        if not isinstance(day, date) or isinstance(day, datetime):
            raise ManseDataError("date_not_found", "양력 날짜를 확인해 주세요.")
        with self._connection() as connection:
            row = connection.execute(
                f"SELECT {SELECT_COLUMNS} FROM tb_manse WHERE sDate = ?", (day.isoformat(),)
            ).fetchone()
        if row is None:
            raise ManseDataError("date_not_found", "해당 양력 날짜의 원본 만세력 자료가 없습니다.")
        return dict(row)

    def lunar_record(self, year: int, month: int, day: int, leap: bool | int) -> dict:
        integers = (year, month, day)
        if (
            any(type(value) is not int for value in integers)
            or not 1 <= month <= 12
            or not 1 <= day <= 30
            or type(leap) not in (bool, int)
            or leap not in (0, 1)
        ):
            raise ManseDataError("invalid_lunar_date", "음력 날짜와 윤달 여부를 확인해 주세요.")
        with self._connection() as connection:
            rows = connection.execute(
                f"SELECT {SELECT_COLUMNS} FROM tb_manse "
                "WHERE l_year = ? AND l_mon = ? AND l_day = ? AND leafMon_YN = ? LIMIT 2",
                (year, month, day, int(leap)),
            ).fetchall()
        if len(rows) > 1:
            raise ManseDataError(
                "ambiguous_lunar_date", "원본 만세력에 같은 음력 날짜가 중복되어 양력 날짜를 확정할 수 없습니다."
            )
        if not rows:
            raise ManseDataError("invalid_lunar_date", "해당 음력 날짜의 원본 만세력 자료가 없습니다.")
        return dict(rows[0])

    def lunar_candidates(self, year: int, month: int, day: int) -> list[dict]:
        """Return every original candidate before a verified leap correction."""
        if (
            any(type(value) is not int for value in (year, month, day))
            or not 1 <= month <= 12
            or not 1 <= day <= 30
        ):
            raise ManseDataError("invalid_lunar_date", "음력 날짜를 확인해 주세요.")
        with self._connection() as connection:
            rows = connection.execute(
                f"SELECT {SELECT_COLUMNS} FROM tb_manse "
                "WHERE l_year = ? AND l_mon = ? AND l_day = ? ORDER BY sDate",
                (year, month, day),
            ).fetchall()
        return [dict(row) for row in rows]

    def solar_terms(self, moment: datetime) -> tuple[dict | None, dict | None]:
        if not isinstance(moment, datetime) or moment.tzinfo is None or moment.utcoffset() is None:
            raise ManseDataError("invalid_datetime", "절기 조회 시각에 시간대가 필요합니다.")
        try:
            current = moment.astimezone(KST).replace(second=0, microsecond=0).isoformat()
        except (ValueError, OverflowError):
            raise ManseDataError("invalid_datetime", "절기 조회 시각을 확인해 주세요.") from None
        select = ", ".join(f't."{column}"' for column in COLUMNS)
        with self._connection() as connection:
            previous = connection.execute(
                f"SELECT {select} FROM tb_manse t JOIN manse_terms m ON m.idx = t.idx "
                "WHERE m.term_at <= ? ORDER BY m.term_at DESC LIMIT 1", (current,),
            ).fetchone()
            following = connection.execute(
                f"SELECT {select} FROM tb_manse t JOIN manse_terms m ON m.idx = t.idx "
                "WHERE m.term_at > ? ORDER BY m.term_at ASC LIMIT 1", (current,),
            ).fetchone()

        def describe(row):
            if row is None:
                return None
            record = dict(row)
            try:
                record["name"] = TERM_NAMES[record["div_name"]]
                record["at"] = term_datetime(record).isoformat()
            except (IndexError, KeyError, TypeError):
                raise ManseDataError("manse_unavailable", "만세력 절기 자료를 읽을 수 없습니다.") from None
            return record

        return describe(previous), describe(following)

    def iter_records(self) -> Iterator[tuple]:
        with self._connection() as connection:
            cursor = connection.execute(f"SELECT {SELECT_COLUMNS} FROM tb_manse ORDER BY idx")
            for row in cursor:
                yield tuple(row)


_store_provider: Callable[[], Any] = ManseStore


def configure_manse_store(provider: Callable[[], Any] | None) -> None:
    """Configure the process's explicitly selected database provider."""
    global _store_provider
    if provider is not None and not callable(provider):
        raise TypeError("A callable ManseStore provider is required.")
    _store_provider = provider if provider is not None else ManseStore


def get_manse_store():
    # Keep raw providers available to import/export tools; only application
    # lookups receive the explicitly versioned correction layer.
    from app.manse_corrections import CorrectedManseStore

    store = _store_provider()
    return store if isinstance(store, CorrectedManseStore) else CorrectedManseStore(store)

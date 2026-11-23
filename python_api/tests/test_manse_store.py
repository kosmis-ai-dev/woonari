"""T-017: original-date lookups, minute boundaries and DB failures."""

import json
import sqlite3
from datetime import date, datetime, timedelta, timezone

import pytest

from app.manse_store import (
    APPLICATION_ID,
    COLUMNS,
    FORMAT_NAME,
    INSERT_SQL,
    KST,
    SCHEMA_VERSION,
    SQLITE_INDEX_DDL,
    SQLITE_METADATA_DDL,
    SQLITE_TABLE_DDL,
    SQLITE_TERMS_DDL,
    ManseDataError,
    ManseStore,
    term_datetime,
)


@pytest.fixture
def calendar_database(tmp_path):
    path = tmp_path / "calendar.sqlite3"
    rows = [
        (1, 2024, 1, 1, 2023, 11, 20, 0, 24, 0, 23, 9, 3, 0, 0, 0, 0, "2024-01-01"),
        (2, 2024, 1, 2, 2023, 11, 20, 0, 12, 30, 24, 9, 3, 0, 0, 1, 1, "2024-01-02"),
        (3, 2024, 1, 3, 2023, 11, 21, 1, 10, 15, 1, 9, 3, 1, 1, 2, 2, "2024-01-03"),
    ]
    with sqlite3.connect(path) as connection:
        connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.execute(SQLITE_TABLE_DDL)
        connection.execute(SQLITE_METADATA_DDL)
        connection.execute(SQLITE_TERMS_DDL)
        for statement in SQLITE_INDEX_DDL:
            connection.execute(statement)
        connection.executemany(INSERT_SQL, rows)
        for row in rows:
            if row[10] % 2:
                moment = term_datetime(dict(zip(COLUMNS, row)))
                connection.execute("INSERT INTO manse_terms VALUES (?, ?)", (row[0], moment.isoformat()))
        metadata = {"format": FORMAT_NAME, "schema_version": SCHEMA_VERSION, "row_count": 3}
        connection.execute("INSERT INTO manse_metadata VALUES (1, ?)", (json.dumps(metadata),))
    return path


def test_solar_record_returns_exact_original_columns(calendar_database):
    record = ManseStore(calendar_database).solar_record(date(2024, 1, 1))
    assert tuple(record) == COLUMNS
    assert record["div_hour"] == 24
    assert record["sDate"] == "2024-01-01"


def test_duplicate_lunar_key_is_explicitly_ambiguous(calendar_database):
    with pytest.raises(ManseDataError) as error:
        ManseStore(calendar_database).lunar_record(2023, 11, 20, False)
    assert error.value.code == "ambiguous_lunar_date"


def test_lunar_lookup_respects_original_leap_flag(calendar_database):
    store = ManseStore(calendar_database)
    assert store.lunar_record(2023, 11, 21, True)["sDate"] == "2024-01-03"
    with pytest.raises(ManseDataError) as error:
        store.lunar_record(2023, 11, 21, False)
    assert error.value.code == "invalid_lunar_date"


def test_lunar_candidates_preserve_all_raw_variants_before_filtering(calendar_database):
    with sqlite3.connect(calendar_database) as connection:
        extra = (4, 2024, 1, 4, 2023, 11, 20, 1, 0, 0, 0, 9, 3, 0, 0, 3, 3, "2024-01-04")
        connection.execute(INSERT_SQL, extra)

    rows = ManseStore(calendar_database).lunar_candidates(2023, 11, 20)

    assert [row["sDate"] for row in rows] == ["2024-01-01", "2024-01-02", "2024-01-04"]
    assert [row["leafMon_YN"] for row in rows] == [0, 0, 1]
    assert all(tuple(row) == COLUMNS for row in rows)
    assert ManseStore(calendar_database).lunar_candidates(2023, 12, 1) == []


@pytest.mark.parametrize("values", [(True, 1, 1), (2023, 0, 20), (2023, 11, 31)])
def test_invalid_lunar_candidates_are_rejected_before_db_access(tmp_path, values):
    with pytest.raises(ManseDataError) as error:
        ManseStore(tmp_path / "missing.sqlite3").lunar_candidates(*values)
    assert error.value.code == "invalid_lunar_date"


def test_jie_boundaries_are_minute_inclusive_and_normalize_original_24h(calendar_database):
    store = ManseStore(calendar_database)
    before = datetime(2024, 1, 1, 23, 59, tzinfo=KST)
    at = before + timedelta(minutes=1)
    assert store.solar_terms(before)[0] is None
    previous, following = store.solar_terms(at)
    assert previous["idx"] == 1
    assert previous["at"] == "2024-01-02T00:00:00+09:00"
    assert previous["div_hour"] == 24
    assert following["idx"] == 3  # Even-numbered 中氣 is not a Jie boundary.
    assert previous["name"] == "小寒"
    same_minute = at + timedelta(seconds=59)
    assert store.solar_terms(same_minute) == (previous, following)
    assert store.solar_terms(at.astimezone(timezone.utc)) == (previous, following)


def test_last_term_and_missing_solar_date_have_clear_boundaries(calendar_database):
    store = ManseStore(calendar_database)
    assert store.solar_terms(datetime(2024, 1, 3, 10, 15, tzinfo=KST))[1] is None
    with pytest.raises(ManseDataError) as error:
        store.solar_record(date(2023, 12, 31))
    assert error.value.code == "date_not_found"
    with pytest.raises(ManseDataError) as error:
        store.solar_terms(datetime(2024, 1, 1))
    assert error.value.code == "invalid_datetime"


@pytest.mark.parametrize("contents", [b"not a sqlite database", b""])
def test_corrupt_database_has_safe_error(tmp_path, contents):
    path = tmp_path / "invalid.sqlite3"
    path.write_bytes(contents)
    with pytest.raises(ManseDataError) as error:
        ManseStore(path).solar_record(date(2024, 1, 1))
    assert error.value.code == "manse_unavailable"
    assert "sqlite" not in str(error.value)


def test_newer_database_version_is_rejected(calendar_database):
    with sqlite3.connect(calendar_database) as connection:
        connection.execute("PRAGMA user_version = 999")
    with pytest.raises(ManseDataError) as error:
        ManseStore(calendar_database).metadata()
    assert error.value.code == "manse_unavailable"


def test_lookups_reopen_database_after_atomic_replacement(calendar_database):
    store = ManseStore(calendar_database)
    assert store.solar_record(date(2024, 1, 1))["d_gan"] == 0
    replacement = calendar_database.with_name("replacement.sqlite3")
    replacement.write_bytes(calendar_database.read_bytes())
    with sqlite3.connect(replacement) as connection:
        connection.execute("UPDATE tb_manse SET d_gan = 8 WHERE idx = 1")
    replacement.replace(calendar_database)
    assert store.solar_record(date(2024, 1, 1))["d_gan"] == 8

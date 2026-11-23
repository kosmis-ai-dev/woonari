"""Remote original data queries use explicit connections and preserve failure boundaries."""

import json
from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from app.manse_mysql import MySQLManseStore
from app.manse_store import (
    FORMAT_NAME,
    KST,
    SCHEMA_VERSION,
    ManseDataError,
    ManseStore,
    configure_manse_store,
    get_manse_store,
)


def raw_record(idx=1, day=1, lunar_day=20, division=23, hour=24, minute=0):
    return (
        idx, 2024, 1, day, 2023, 11, lunar_day, 0, hour, minute, division,
        9, 3, 0, 0, 0, 0, date(2024, 1, day),
    )


def metadata_row():
    metadata = {
        "format": FORMAT_NAME, "schema_version": SCHEMA_VERSION, "row_count": 3,
        "min_date": "2024-01-01", "max_date": "2024-01-03",
        "source_sha256": "a" * 64, "data_sha256": "b" * 64,
    }
    return (metadata["source_sha256"], metadata["data_sha256"], 3, json.dumps(metadata))


def fake_store(rows):
    cursor = MagicMock()
    cursor.fetchall.side_effect = [[metadata_row()], rows]
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    connector = MagicMock(return_value=connection)
    return MySQLManseStore(connector), connection, cursor, connector


def test_mysql_lookup_normalizes_date_parameterizes_values_and_closes():
    store, connection, cursor, connector = fake_store([raw_record()])

    row = store.solar_record(date(2024, 1, 1))

    assert row["sDate"] == "2024-01-01"
    assert row["div_hour"] == 24
    sql, arguments = cursor.execute.call_args.args
    assert "s_year = %s AND s_mon = %s AND s_day = %s" in sql
    assert arguments == (2024, 1, 1)
    connector.assert_called_once_with()
    connection.close.assert_called_once_with()


def test_mysql_lunar_ambiguity_matches_original_store_contract():
    store, connection, cursor, _ = fake_store([raw_record(), raw_record(idx=2, day=2)])
    with pytest.raises(ManseDataError) as error:
        store.lunar_record(2023, 11, 20, False)
    assert error.value.code == "ambiguous_lunar_date"
    assert cursor.execute.call_args.args[1] == (2023, 11, 20, 0)
    connection.close.assert_called_once_with()


def test_mysql_lunar_candidates_include_every_raw_leap_variant_and_close():
    first = raw_record()
    leap = list(raw_record(idx=2, day=2))
    leap[7] = 1
    store, connection, cursor, _ = fake_store([first, tuple(leap), raw_record(idx=3, day=3)])

    rows = store.lunar_candidates(2023, 11, 20)

    assert [row["leafMon_YN"] for row in rows] == [0, 1, 0]
    assert [row["sDate"] for row in rows] == ["2024-01-01", "2024-01-02", "2024-01-03"]
    sql, arguments = cursor.execute.call_args.args
    assert arguments == (2023, 11, 20)
    assert "AND leafMon_YN =" not in sql
    assert "LIMIT" not in sql
    connection.close.assert_called_once_with()


def test_mysql_lunar_candidates_mask_query_failure_and_close():
    store, connection, cursor, _ = fake_store([])
    cursor.fetchall.side_effect = [[metadata_row()], RuntimeError("private-driver-detail")]

    with pytest.raises(ManseDataError) as error:
        store.lunar_candidates(2023, 11, 20)

    assert error.value.code == "manse_unavailable"
    assert "private" not in str(error.value)
    connection.close.assert_called_once_with()


@pytest.mark.parametrize("values", [(True, 1, 1), (2023, 0, 20), (2023, 11, 31)])
def test_mysql_invalid_lunar_candidates_never_connect(values):
    store, _, _, connector = fake_store([])
    with pytest.raises(ManseDataError) as error:
        store.lunar_candidates(*values)
    assert error.value.code == "invalid_lunar_date"
    connector.assert_not_called()


def test_mysql_jie_window_is_inclusive_and_preserves_original_24h():
    store, connection, cursor, _ = fake_store([
        raw_record(), raw_record(idx=3, day=3, division=1, hour=10, minute=15),
    ])

    previous, following = store.solar_terms(datetime(2024, 1, 2, tzinfo=KST))

    assert previous["at"] == "2024-01-02T00:00:00+09:00"
    assert previous["name"] == "小寒"
    assert previous["div_hour"] == 24
    assert following["idx"] == 3
    assert "MOD(div_name, 2) = 1" in cursor.execute.call_args.args[0]
    assert cursor.execute.call_args.args[1] == (2024, 2024)
    connection.close.assert_called_once_with()


def test_remote_failure_is_safe_and_never_falls_back_to_sqlite(monkeypatch):
    def connector():
        raise RuntimeError("private-password @ private-db-host")

    fallback = MagicMock()
    monkeypatch.setattr(ManseStore, "solar_record", fallback)
    store = MySQLManseStore(connector)
    with pytest.raises(ManseDataError) as error:
        store.solar_record(date(2024, 1, 1))
    assert error.value.code == "manse_unavailable"
    assert "private" not in str(error.value)
    fallback.assert_not_called()


def test_remote_metadata_version_mismatch_is_safe_and_closes():
    store, connection, cursor, _ = fake_store([])
    invalid = list(metadata_row())
    payload = json.loads(invalid[3])
    payload["schema_version"] = 999
    invalid[3] = json.dumps(payload)
    cursor.fetchall.side_effect = [[invalid]]

    with pytest.raises(ManseDataError) as error:
        store.metadata()

    assert error.value.code == "manse_unavailable"
    connection.close.assert_called_once_with()


def test_store_provider_selection_is_explicit_and_resettable():
    provider = MagicMock(return_value=ManseStore())
    try:
        configure_manse_store(provider)
        selected = get_manse_store()
        assert selected.raw_store is provider.return_value
        assert selected.backend == "sqlite"
        assert isinstance(ManseStore(), ManseStore)
        configure_manse_store(lambda: selected)
        assert get_manse_store() is selected
    finally:
        configure_manse_store(None)
    assert isinstance(get_manse_store().raw_store, ManseStore)


def test_mysql_iter_records_preserves_ordered_digest_contract_and_closes():
    store, connection, cursor, _ = fake_store([])
    cursor.fetchall.side_effect = [[metadata_row()]]
    cursor.fetchmany.side_effect = [[raw_record()], []]

    records = list(store.iter_records())

    assert records[0][-1] == "2024-01-01"
    assert "ORDER BY idx" in cursor.execute.call_args.args[0]
    connection.close.assert_called_once_with()

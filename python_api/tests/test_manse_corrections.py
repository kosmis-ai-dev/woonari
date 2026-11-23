"""CR-010: reviewed leap flags restore lunar input without modifying the source."""

from collections import Counter
from datetime import date

import pytest

from app.manse_corrections import (
    CORRECTION_COUNT,
    CORRECTION_VERSION,
    DATA_SHA256,
    CorrectedManseStore,
    apply_correction,
)
from app.manse_store import COLUMNS, ManseDataError, ManseStore, data_digest

CORRECTED_DATES = [
    ("2017-06-23", (2017, 5, 29), False),
    ("2017-07-22", (2017, 5, 29), True),
    ("2020-05-22", (2020, 4, 30), False),
    ("2020-06-20", (2020, 4, 29), True),
    ("2023-03-21", (2023, 2, 30), False),
    ("2023-04-19", (2023, 2, 29), True),
    ("2025-07-24", (2025, 6, 30), False),
    ("2025-08-22", (2025, 6, 29), True),
    ("2028-06-22", (2028, 5, 30), False),
    ("2028-07-21", (2028, 5, 29), True),
]


@pytest.mark.parametrize("solar,lunar,leap", CORRECTED_DATES)
def test_reviewed_dates_convert_both_ways_and_leave_raw_values_unchanged(solar, lunar, leap):
    raw = ManseStore()
    store = CorrectedManseStore(raw)
    target = date.fromisoformat(solar)
    original = raw.solar_record(target)

    forward = store.solar_record(target)
    reverse = store.lunar_record(*lunar, leap)

    assert forward == reverse
    assert forward["sDate"] == solar
    assert forward["leafMon_YN"] == int(leap)
    assert original["leafMon_YN"] == int(not leap)
    assert {key for key in original if original[key] != forward[key]} == {"leafMon_YN"}
    assert raw.solar_record(target) == original
    assert store.backend == raw.backend


@pytest.mark.parametrize(
    "lunar,ordinary_solar,leap_solar",
    [
        ((2020, 4, 29), "2020-05-21", "2020-06-20"),
        ((2023, 2, 29), "2023-03-20", "2023-04-19"),
        ((2025, 6, 29), "2025-07-23", "2025-08-22"),
        ((2028, 5, 29), "2028-06-21", "2028-07-21"),
    ],
)
def test_formerly_ambiguous_ordinary_and_leap_dates_have_distinct_results(
    lunar, ordinary_solar, leap_solar,
):
    store = CorrectedManseStore(ManseStore())
    assert store.lunar_record(*lunar, False)["sDate"] == ordinary_solar
    assert store.lunar_record(*lunar, True)["sDate"] == leap_solar


@pytest.mark.parametrize("year,month", [(2020, 4), (2023, 2), (2025, 6), (2028, 5)])
def test_thirtieth_day_is_only_in_the_ordinary_month(year, month):
    store = CorrectedManseStore(ManseStore())
    assert store.lunar_record(year, month, 30, False)["leafMon_YN"] == 0
    with pytest.raises(ManseDataError) as caught:
        store.lunar_record(year, month, 30, True)
    assert caught.value.code == "invalid_lunar_date"


def test_all_source_records_keep_their_hash_and_have_a_consistent_corrected_lunar_sequence():
    raw = ManseStore()
    store = CorrectedManseStore(raw)
    metadata = raw.metadata()
    records = list(store.iter_records())
    assert len(records) == 73414
    assert data_digest(records) == metadata["data_sha256"] == DATA_SHA256
    assert store.metadata() == metadata
    corrected = [apply_correction(dict(zip(COLUMNS, row)), metadata) for row in records]
    changed = [row for row, original in zip(corrected, records)
               if tuple(row[column] for column in COLUMNS) != original]
    assert len(changed) == CORRECTION_COUNT == 10
    assert CORRECTION_VERSION == "lunar-leap-flags-v1"
    keys = Counter((row["l_year"], row["l_mon"], row["l_day"], row["leafMon_YN"])
                   for row in corrected)
    assert max(keys.values()) == 1
    ordered = sorted(corrected, key=lambda row: row["sDate"])
    for previous, current in zip(ordered, ordered[1:]):
        py, pm, pd, pl = (previous[key] for key in ("l_year", "l_mon", "l_day", "leafMon_YN"))
        cy, cm, cd, cl = (current[key] for key in ("l_year", "l_mon", "l_day", "leafMon_YN"))
        if cd != 1:
            assert (cy, cm, cl, cd) == (py, pm, pl, pd + 1)
        else:
            assert pd in (29, 30)
            next_year, next_month = (py + 1, 1) if pm == 12 else (py, pm + 1)
            assert (
                (pl == 0 and (cy, cm, cl) == (py, pm, 1))
                or (cy, cm, cl) == (next_year, next_month, 0)
            )
    assert data_digest(raw.iter_records()) == DATA_SHA256


@pytest.mark.parametrize("field,value", [
    ("source_sha256", "a" * 64), ("data_sha256", "b" * 64), ("row_count", 10),
])
def test_known_corrections_fail_closed_for_a_different_source(monkeypatch, field, value):
    raw = ManseStore()
    metadata = raw.metadata() | {field: value}
    monkeypatch.setattr(raw, "metadata", lambda: metadata)
    store = CorrectedManseStore(raw)
    for call in (
        lambda: store.solar_record(date(2023, 4, 19)),
        lambda: store.lunar_record(2023, 2, 29, True),
    ):
        with pytest.raises(ManseDataError) as caught:
            call()
        assert caught.value.code == "manse_unavailable"
        assert value not in str(caught.value) if isinstance(value, str) else True


@pytest.mark.parametrize("field,value", [
    ("idx", 1), ("s_day", 18), ("l_day", 28), ("leafMon_YN", 1),
])
def test_a_changed_original_row_is_never_silently_repaired(field, value):
    raw = ManseStore()
    original = raw.solar_record(date(2023, 4, 19)) | {field: value}
    with pytest.raises(ManseDataError) as caught:
        apply_correction(original, raw.metadata())
    assert caught.value.code == "manse_unavailable"
    assert original[field] == value


def test_unreviewed_ambiguity_is_still_rejected(monkeypatch):
    raw = ManseStore()

    def unreviewed(*args):
        raise ManseDataError("ambiguous_lunar_date", "검증되지 않은 음력 날짜 중복")

    monkeypatch.setattr(raw, "lunar_record", unreviewed)
    with pytest.raises(ManseDataError) as caught:
        CorrectedManseStore(raw).lunar_record(2024, 1, 1, False)
    assert caught.value.code == "ambiguous_lunar_date"


def test_additional_candidates_are_not_resolved_by_arbitrary_order(monkeypatch):
    raw = ManseStore()
    original = raw.lunar_candidates(2023, 2, 29)
    duplicate = original[0] | {"idx": 1, "sDate": "2023-03-19"}
    monkeypatch.setattr(raw, "lunar_candidates", lambda *args: [*original, duplicate])
    with pytest.raises(ManseDataError) as caught:
        CorrectedManseStore(raw).lunar_record(2023, 2, 29, False)
    assert caught.value.code == "ambiguous_lunar_date"


def test_missing_expected_correction_candidate_is_a_data_error(monkeypatch):
    raw = ManseStore()
    ordinary = raw.solar_record(date(2023, 3, 20))
    monkeypatch.setattr(raw, "lunar_candidates", lambda *args: [ordinary])
    with pytest.raises(ManseDataError) as caught:
        CorrectedManseStore(raw).lunar_record(2023, 2, 29, True)
    assert caught.value.code == "manse_unavailable"

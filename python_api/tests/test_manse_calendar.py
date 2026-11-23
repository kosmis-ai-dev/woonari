"""CR-009 / T-018: fixtures from the supplied tb_manse and original ASP boundaries."""

from datetime import date, datetime, timezone

import pytest

from app import calendar
from app.calendar import calculate_saju, day_ganji, ganji_from_row, period_pillars, solar_birth
from app.errors import DomainError
from app.manse_store import ManseStore
from app.models import Birth
from app.rules import GANJI


def birth(**changes):
    return Birth(
        **(
            {"year": 2005, "month": 12, "day": 6, "hour": 12, "minute": 0, "gender": "male"}
            | changes
        )
    )


@pytest.mark.parametrize("index", range(60))
def test_zero_based_gan_ji_columns_map_to_original_asp_array(index):
    row = {"d_gan": index % 10, "d_ji": index % 12}
    assert ganji_from_row(row, "d") == GANJI[index]


def test_source_lunar_date_is_preserved_instead_of_library_recalculation():
    # The supplied row differs from the previous independent Korean calendar.
    result = calculate_saju(birth(year=1903, month=10, day=20))
    assert result.lunar_birth == {"year": 1903, "month": 8, "day": 30, "leap_month": False}
    lunar = birth(year=1903, month=8, day=30, calendar="lunar")
    assert solar_birth(lunar).date() == date(1903, 10, 20)


@pytest.mark.parametrize(
    "year,month,day,hour,minute,expected_year,expected_month",
    [
        (2024, 2, 4, 16, 59, "癸卯", "乙丑"),
        (2024, 2, 4, 17, 0, "甲辰", "丙寅"),
        (2024, 2, 4, 17, 1, "甲辰", "丙寅"),
        (2026, 2, 4, 4, 37, "乙巳", "己丑"),
        (2026, 2, 4, 4, 38, "丙午", "庚寅"),
        (1984, 2, 5, 0, 19, "癸亥", "乙丑"),
        (1984, 2, 5, 0, 20, "甲子", "丙寅"),
        (2023, 12, 7, 18, 10, "癸卯", "癸亥"),
        (2023, 12, 7, 18, 11, "癸卯", "甲子")
    ]
)
def test_source_solar_term_minutes_and_sixty_pillar_wrap(
    year, month, day, hour, minute, expected_year, expected_month
):
    result = calculate_saju(birth(year=year, month=month, day=day, hour=hour, minute=minute))
    assert result.pillars["year"].hanja == expected_year
    assert result.pillars["month"].hanja == expected_month


def test_period_pillars_respect_source_boundary_and_convert_aware_time_to_kst():
    before = period_pillars(datetime(2024, 2, 4, 7, 59, tzinfo=timezone.utc))
    at = period_pillars(datetime(2024, 2, 4, 8, 0, tzinfo=timezone.utc))
    assert before == {"year": "癸卯", "month": "乙丑", "day": "戊戌"}
    assert at == {"year": "甲辰", "month": "丙寅", "day": "戊戌"}
    assert period_pillars(datetime(2024, 2, 4, 17, 0)) == at


@pytest.mark.parametrize(
    "profile,hour,minute,expected_day,expected_hour",
    [
        ("today_inline", 0, 29, "癸亥", "甲子"),
        ("today_inline", 0, 30, "甲子", "甲子"),
        ("today_inline", 1, 29, "甲子", "甲子"),
        ("today_inline", 1, 30, "甲子", "乙丑"),
        ("today_inline", 23, 29, "甲子", "乙亥"),
        ("today_inline", 23, 30, "甲子", "甲子"),
        ("dotong", 0, 29, "癸亥", "甲子"),
        ("dotong", 0, 30, "甲子", "甲子"),
        ("dotong", 23, 29, "甲子", "乙亥"),
        ("dotong", 23, 30, "甲子", "丙子")
    ]
)
def test_hour_is_computed_before_day_correction_and_profiles_remain_distinct(
    profile, hour, minute, expected_day, expected_hour
):
    result = calculate_saju(birth(hour=hour, minute=minute), profile)
    assert result.pillars["day"].hanja == expected_day
    assert result.pillars["hour"].hanja == expected_hour


@pytest.mark.parametrize(
    "year,month,day,leap,expected",
    [
        (2017, 5, 29, False, date(2017, 6, 23)),
        (2017, 5, 29, True, date(2017, 7, 22)),
        (2020, 4, 29, False, date(2020, 5, 21)),
        (2020, 4, 30, False, date(2020, 5, 22)),
        (2020, 4, 29, True, date(2020, 6, 20)),
        (2023, 2, 29, False, date(2023, 3, 20)),
        (2023, 2, 30, False, date(2023, 3, 21)),
        (2023, 2, 29, True, date(2023, 4, 19)),
        (2025, 6, 29, False, date(2025, 7, 23)),
        (2025, 6, 30, False, date(2025, 7, 24)),
        (2025, 6, 29, True, date(2025, 8, 22)),
        (2028, 5, 29, False, date(2028, 6, 21)),
        (2028, 5, 30, False, date(2028, 6, 22)),
        (2028, 5, 29, True, date(2028, 7, 21)),
    ],
)
def test_approved_corrections_distinguish_regular_and_leap_dates(year, month, day, leap, expected):
    lunar = birth(year=year, month=month, day=day, calendar="lunar", leap_month=leap)
    assert solar_birth(lunar).date() == expected
    solar = birth(year=expected.year, month=expected.month, day=expected.day)
    assert calculate_saju(lunar) == calculate_saju(solar)
    assert calculate_saju(solar).lunar_birth["leap_month"] is leap


@pytest.mark.parametrize("year,month", [(2020, 4), (2023, 2), (2025, 6), (2028, 5)])
def test_correction_does_not_create_a_nonexistent_leap_thirtieth_day(year, month):
    with pytest.raises(DomainError) as caught:
        solar_birth(birth(year=year, month=month, day=30, calendar="lunar", leap_month=True))
    assert caught.value.code == "invalid_lunar_date"


def test_invalid_leap_date_is_not_resolved_to_a_regular_month():
    with pytest.raises(DomainError) as caught:
        solar_birth(birth(year=2024, month=2, day=1, calendar="lunar", leap_month=True))
    assert caught.value.code == "invalid_lunar_date"


def test_valid_leap_month_uses_source_row_and_preserves_solar_lunar_equivalence():
    lunar = birth(year=2023, month=2, day=1, calendar="lunar", leap_month=True)
    solar = birth(year=2023, month=3, day=22)
    assert calculate_saju(lunar) == calculate_saju(solar)
    assert calculate_saju(lunar).lunar_birth["leap_month"] is True


def test_original_wrong_division_code_is_preserved_without_silent_correction():
    # 1945-06-06 is supplied as division 8, not the expected odd division 9.
    source_day = calculate_saju(birth(year=1945, month=6, day=6, hour=23, minute=59))
    following = calculate_saju(birth(year=1945, month=6, day=7))
    assert source_day.pillars["month"].hanja == "辛巳"
    assert following.pillars["month"].hanja == "壬午"


def test_first_db_date_does_not_require_a_missing_previous_term_or_day_row():
    result = calculate_saju(birth(year=1900, month=1, day=1, hour=0, minute=0))
    assert result.pillars["day"].hanja == "癸酉"
    assert result.solar_term_window["previous"] is None
    assert result.solar_term_window["next"]["name"] == "小寒"


def test_source_term_window_and_policy_expose_db_provenance():
    result = calculate_saju(birth(year=2024, month=2, day=4, hour=17, minute=0))
    assert result.solar_term_window["previous"] == {
        "name": "立春", "at": "2024-02-04T17:00:00+09:00"
    }
    assert result.policy.version == "asp-manse-db-v4"
    assert result.policy.lunar_correction_version == "lunar-leap-flags-v1"
    assert "tb_manse" in result.policy.lunar_calendar
    assert "tb_manse" in result.policy.solar_terms
    assert result.major_luck["available"] is False


def test_missing_db_is_explicit_and_never_uses_an_independent_calendar(monkeypatch, tmp_path):
    monkeypatch.setattr(calendar, "get_manse_store", lambda: ManseStore(tmp_path / "missing.sqlite3"))
    with pytest.raises(DomainError) as caught:
        calculate_saju(birth())
    assert caught.value.code == "manse_unavailable"
    assert caught.value.status == 503


def test_day_lookup_does_not_keep_stale_values_after_db_replacement(monkeypatch):
    rows = iter([{"d_gan": 0, "d_ji": 0}, {"d_gan": 1, "d_ji": 1}])

    class ReimportedStore:
        def solar_record(self, value):
            return next(rows)

    monkeypatch.setattr(calendar, "get_manse_store", ReimportedStore)
    assert day_ganji(date(2005, 12, 6)) == "甲子"
    assert day_ganji(date(2005, 12, 6)) == "乙丑"


def test_larger_db_does_not_implicitly_expand_the_public_api_range():
    with pytest.raises(DomainError) as caught:
        day_ganji(date(2051, 1, 1))
    assert caught.value.code == "date_out_of_range"

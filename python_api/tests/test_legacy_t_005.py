"""CR-001/T-005: literal ASP predicates, not replacement fortune formulas."""

from datetime import date

import pytest

from app.calendar import calculate_saju
from app.errors import DomainError
from app.legacy_periods import YEAR_COLUMNS, _month_index_after_division, decide_period
from app.models import FortuneRequest


def request(target="2024-02-04", gender="male"):
    return FortuneRequest(
        birth={"year": 1990, "month": 5, "day": 17, "hour": 14, "minute": 30, "gender": gender},
        target_date=target,
        include_ai=False,
    )


def decide(kind, value):
    return decide_period(kind, value, calculate_saju(value.birth))


def test_monthly_preserves_source_keys_and_female_nyeo_value():
    result = decide("monthly", request(gender="female"))
    selector = result["selectors"][0]
    assert result["source"] == "old/unse/monthluck/main_end.asp"
    assert selector == {
        "id": "monthly-content",
        "table": "monthfor",
        "where": {"memno": 1, "yukgap_no": 2, "sex": "녀"},
        "columns": ["contents"],
        "purpose": "월간 운세 본문 조회를 AI 작성으로 교체",
    }
    assert "samples" not in result["facts"]


def test_odd_division_day_increments_without_time_of_day_comparison():
    # Source div_name=1 (입춘). Stored prior month 乙丑 -> 丙寅 for the
    # whole target date, despite the source DB's 2024 입춘 being at 17:00 KST.
    result = decide("monthly", request())
    facts = result["facts"]
    assert facts["replacement_manse"]["div_name"] == 1
    assert facts["month_pillar_before_asp_adjustment"] == 1
    assert facts["odd_division_increment_applied"] is True
    assert facts["selected_month_pillar"] == "丙寅"
    assert result["period_start"] == date(2024, 2, 4)
    assert result["period_end"] == date(2024, 3, 5)
    assert facts["replacement_manse"]["replacement_disp_day"] == "2024020420240305"


def test_before_division_uses_previous_month_and_term_display_boundaries():
    result = decide("monthly", request("2024-02-03"))
    assert result["facts"]["selected_month_pillar"] == "乙丑"
    assert result["facts"]["replacement_manse"]["div_name"] == 0
    assert result["period_start"] == date(2024, 1, 6)
    assert result["period_end"] == date(2024, 2, 4)
    assert result["facts"]["calendar_replacement"]["limitation"]


def test_even_division_does_not_increment_month():
    result = decide("monthly", request("2024-02-19"))
    assert result["facts"]["replacement_manse"]["div_name"] == 2
    assert result["facts"]["odd_division_increment_applied"] is False
    assert result["facts"]["selected_month_pillar"] == "丙寅"


def test_source_month_wrap_is_preserved():
    assert _month_index_after_division(59, 1) == 0
    assert _month_index_after_division(59, 2) == 59
    assert _month_index_after_division(59, 0) == 59
    assert _month_index_after_division(58, 23) == 59


@pytest.mark.parametrize("target", ["1900-01-06", "2024-01-01", "2050-12-31"])
def test_month_period_crosses_years_without_clipping_or_civil_month_substitution(target):
    value = request(target)
    if target.startswith("1900"):
        value.birth = value.birth.model_copy(update={"year": 1900, "month": 1, "day": 1})
    result = decide("monthly", value)
    assert result["period_start"] <= value.target_date < result["period_end"]
    assert result["facts"]["original_calendar_lookup"]["where"] == {
        "syear": value.target_date.year,
        "smonth": value.target_date.month,
        "sday": value.target_date.day,
    }


def test_monthly_requires_previous_boundary_in_the_supplied_database():
    value = request("1900-01-01")
    value.birth = value.birth.model_copy(update={"year": 1900, "month": 1, "day": 1})
    with pytest.raises(DomainError) as error:
        decide("monthly", value)
    assert error.value.code == "calendar_boundary_unavailable"


def test_source_1945_division_code_is_preserved_in_monthly_selection():
    value = request("1945-06-06")
    value.birth = value.birth.model_copy(update={"year": 1940})
    result = decide("monthly", value)
    assert result["facts"]["replacement_manse"]["div_name"] == 8
    assert result["facts"]["odd_division_increment_applied"] is False
    assert result["facts"]["selected_month_pillar"] == "辛巳"
    assert result["period_start"] == date(1945, 5, 6)
    assert result["period_end"] == date(1945, 7, 7)


@pytest.mark.parametrize(
    "year,expected",
    [
        (2001, "辛巳"),
        (2002, "壬午"),
        (2003, "癸未"),
        (2004, "甲申"),
        (2005, "乙酉"),
        (2006, "丙戌"),
        (2007, "丁亥"),
        (2008, "戊子"),
        (2009, "己丑"),
        (2010, "庚寅"),
        (2011, "辛卯"),
        (2012, "壬辰"),
        (2013, "癸巳"),
        (2014, "甲午"),
    ],
)
def test_all_literal_year_code_branches(year, expected):
    # January is intentionally before LiChun: this source uses code, not
    # an astronomical year-pillar query for target_date.
    result = decide("yearly", request(f"{year}-01-01", gender="female"))
    assert result["selectors"][0]["where"] == {
        "memno": 1,
        "sex": "녀",
        "year_pillar": expected,
    }
    assert result["facts"]["source_default_code_if_empty"] == "2013"
    assert result["facts"]["query_order_by"] == ["num ASC"]
    assert result["selectors"][0]["columns"] == YEAR_COLUMNS
    assert result["period_start"] == date(year, 1, 1)
    assert result["period_end"] == date(year, 12, 31)


def test_yearly_does_not_invent_db_supplied_branch_values_or_scores():
    result = decide("yearly", request("2014-06-01"))
    assert result["unresolved"]
    assert result["facts"]["db_supplied_values"]["section"] is None
    assert result["facts"]["db_supplied_values"]["star_cnt"] is None
    assert result["facts"]["db_supplied_values"]["mark11"] is None
    assert all(
        not condition["resolved"] for condition in result["facts"]["row_rendering_conditions"]
    )
    assert "scores" not in result["facts"]


@pytest.mark.parametrize("year", [1900, 2000, 2015, 2026, 2050])
def test_yearly_rejects_undefined_source_years_instead_of_extrapolating(year):
    with pytest.raises(DomainError) as error:
        decide("yearly", request(f"{year}-11-02"))
    assert error.value.code == "legacy_year_unsupported"
    assert error.value.status == 422


def test_unknown_period_kind_is_rejected():
    with pytest.raises(DomainError) as error:
        decide("daily", request())
    assert error.value.code == "legacy_period_unsupported"

from datetime import date

import pytest

from app.calendar import calculate_saju, day_ganji, solar_birth
from app.errors import DomainError
from app.models import Birth


def birth(**kwargs):
    return Birth(
        **(
            {"year": 2005, "month": 12, "day": 23, "hour": 8, "minute": 37, "gender": "male"}
            | kwargs
        )
    )


def test_known_four_pillars():
    # 6tail/lunar-python official EightCharTest: 2005-12-23 08:37.
    result = calculate_saju(birth())
    assert [p.hanja for p in result.pillars.values()] == ["乙酉", "戊子", "辛巳", "壬辰"]
    assert sum(result.elements.values()) == 8


def test_korean_lunar_new_year_and_leap_month():
    # Korean New Year 2024, and Korean leap second month in 2023.
    assert solar_birth(birth(year=2024, month=1, day=1, calendar="lunar")).date() == date(
        2024, 2, 10
    )
    leap = birth(year=2023, month=2, day=1, calendar="lunar", leap_month=True)
    assert solar_birth(leap).date() == date(2023, 3, 22)
    assert calculate_saju(leap).lunar_birth["leap_month"] is True


def test_invalid_leap_month_is_not_silently_regular():
    with pytest.raises(DomainError, match="윤달"):
        solar_birth(birth(year=2024, month=2, day=1, calendar="lunar", leap_month=True))


def test_legacy_day_boundary_and_uncorrected_time_stem():
    before = calculate_saju(birth(hour=0, minute=29))
    after = calculate_saju(birth(hour=0, minute=30))
    assert before.pillars["day"].hanja == day_ganji(date(2005, 12, 22))
    assert after.pillars["day"].hanja == "辛巳"
    assert before.pillars["hour"].hanja == after.pillars["hour"].hanja == "戊子"


@pytest.mark.parametrize(
    "hour,minute,branch", [(1, 29, "子"), (1, 30, "丑"), (23, 29, "亥"), (23, 30, "子")]
)
def test_hour_boundaries(hour, minute, branch):
    result = calculate_saju(birth(hour=hour, minute=minute))
    assert result.pillars["hour"].branch == branch
    assert result.pillars["day"].hanja == "辛巳"


def test_ipchun_changes_year_and_month_at_korean_instant():
    # User-supplied tb_manse records 2024 입춘 at 17:00 KST.
    before = calculate_saju(birth(year=2024, month=2, day=4, hour=16, minute=59))
    after = calculate_saju(birth(year=2024, month=2, day=4, hour=17, minute=0))
    assert before.pillars["year"].hanja == "癸卯"
    assert after.pillars["year"].hanja == "甲辰"
    assert before.pillars["month"].hanja == "乙丑"
    assert after.pillars["month"].hanja == "丙寅"


def test_minimum_date_before_0030_wraps_without_external_lookup():
    result = calculate_saju(birth(year=1900, month=1, day=1, hour=0, minute=0))
    assert len(result.pillars["day"].hanja) == 2
    assert result.major_luck["available"] is False


def test_solar_and_lunar_birth_produce_identical_results():
    solar = birth(year=2023, month=3, day=22)
    lunar = birth(year=2023, month=2, day=1, calendar="lunar", leap_month=True)
    assert calculate_saju(solar) == calculate_saju(lunar)


def test_commercial_profiles_preserve_different_yajasi_stems():
    before = birth(hour=23, minute=29)
    at = birth(hour=23, minute=30)
    assert (
        calculate_saju(before, "dotong").pillars == calculate_saju(before, "today_inline").pillars
    )
    inline, dotong = calculate_saju(at, "today_inline"), calculate_saju(at, "dotong")
    assert inline.pillars["day"] == dotong.pillars["day"]
    assert inline.pillars["hour"].hanja == "戊子"
    assert dotong.pillars["hour"].hanja == "庚子"


def test_ipchun_transitions_at_original_minute_not_engine_second():
    at = birth(year=2024, month=2, day=4, hour=17, minute=0)
    assert calculate_saju(at).pillars["year"].hanja == "甲辰"

"""CR-012/T-024 source fixtures; these tests run without the ASP archive."""

import math
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app import ported_remaining as port
from app.calendar import calculate_saju
from app.errors import DomainError
from app.models import Birth
from app.service_models import ServiceRequest

BIRTH = Birth(year=1974, month=3, day=2, hour=8, minute=30, gender="male")
PARTNER = Birth(year=1977, month=7, day=9, hour=12, gender="female")


@pytest.fixture(scope="module")
def natal():
    return calculate_saju(BIRTH, "dotong")


@pytest.fixture(scope="module")
def partner():
    return calculate_saju(PARTNER, "dotong")


def request(parameters=None, *, birth=BIRTH, target=date(2026, 11, 18), pair=PARTNER):
    return ServiceRequest(birth=birth, partner=pair, target_date=target,
                          parameters=parameters or {}, include_ai=False)


@pytest.mark.parametrize("service_id,count,ready", [
    ("ddiluck", 12, True), ("adultluck-timesexbioluck", 12, True),
    ("counselluck", 0, False), ("fivegiluck", 1, False),
    ("lottoluck", 1, True), ("loverluck", 6, True), ("meetluck", 1, True),
    ("perluck", 14, True), ("sinsalluck", 1, False),
    ("studentluck", 3, True), ("sweetluck", 4, True),
])
def test_all_remaining_services_have_explicit_output_or_missing_source(service_id, count, ready, natal, partner):
    result = port.decide(service_id, request(port.SERVICES[service_id]["example_parameters"]), natal, partner)
    assert result["source"].endswith("main_end.asp")
    assert len(result["selectors"]) == count
    assert all(row["columns"] == list(row["topics"]) for row in result["selectors"])
    assert bool(result["unresolved"]) is not ready
    assert port.SERVICES[service_id]["ready"] is ready
    assert "adviceluck" not in port.SERVICES


def test_ddiluck_preserves_year_branch_specific_order_and_polarity(natal):
    result = port.decide("ddiluck", request(), natal, None)
    rows = result["facts"]["ordered_zodiac_relations"]
    assert [row["branch"] for row in rows] == list("寅午戌亥卯未辰巳申酉丑子")
    assert [row["favorable"] for row in rows] == [True] * 6 + [False] * 6
    assert all(row["meaning_anchor"] for row in rows)
    assert len(port._DATA["ddiluck"]["order"]) == 12
    assert len(port._DATA["ddiluck"]["anchors"]) == 24


@pytest.mark.parametrize("elapsed,code", [(0, "2"), (7, "2"), (21, "1"), (28, "1")])
def test_time_biorhythm_uses_source_truncated_pi_and_28_day_sign(elapsed, code):
    target = date(1974, 3, 2) + timedelta(days=elapsed)
    result = port.decide("adultluck-timesexbioluck", request(target=target), None, None)
    assert result["facts"]["rhythm"] == math.sin(elapsed / 28 * 2 * 3.141592)
    assert result["facts"]["sign_key"] == code
    assert [row["where"] for row in result["selectors"]] == [
        {"menu": "", "sex": "", "keyno": int(code + hour)}
        for hour in ("06", "08", "10", "12", "14", "16", "18", "20", "22", "00", "02", "04")
    ]
    assert all(row["table"] == "tbSexLove_Content" for row in result["selectors"])


@pytest.mark.parametrize("stem,branch,label", [
    ("甲", "辰", "재성"), ("乙", "未", "재성"), ("丙", "戌", "식상"),
    ("戊", "申", "식상"), ("庚", "子", "식상"), ("壬", "寅", "식상"),
])
def test_meeting_uses_its_own_branch_order_and_numeric_gender(stem, branch, label):
    saju = SimpleNamespace(day_master=stem, pillars={"day": SimpleNamespace(branch=branch)})
    female = BIRTH.model_copy(update={"gender": "female"})
    result = port.decide("meetluck", request(birth=female), saju, None)
    assert result["selectors"][0]["where"] == {"Name": label, "Gender": "2"}


def test_student_uses_original_memno_digit_and_continues_after_age_alert(natal):
    female = BIRTH.model_copy(update={"gender": "female"})
    result = port.decide("studentluck", request(birth=female, target=date(2035, 3, 2)), natal, None)
    assert result["facts"]["legacy_age"] == 61
    assert result["facts"]["source_over_60_alert"] is True
    assert [row["where"] for row in result["selectors"]] == [{"ilgan": 1, "sex": 2}] * 3
    assert [row["table"] for row in result["selectors"]] == ["Exam_Unse", "Gender_Unse", "School_Unse"]


def test_lover_uses_solar_month_and_gender_specific_last_table():
    female = BIRTH.model_copy(update={"gender": "female"})
    solar = port.decide("loverluck", request(birth=female), None, None)
    lunar = Birth(year=1974, month=2, day=9, hour=8, minute=30, calendar="lunar", gender="female")
    same = port.decide("loverluck", request(birth=lunar), None, None)
    assert solar["selectors"] == same["selectors"]
    assert [row["where"] for row in solar["selectors"]] == [{"Num": 0}] * 6
    assert solar["selectors"][-1]["table"] == "love_mylover_woman"


def test_sweet_preserves_four_pillar_keys_and_gender_column(natal):
    female = BIRTH.model_copy(update={"gender": "female"})
    result = port.decide("sweetluck", request(birth=female), natal, None)
    assert [row["where"] for row in result["selectors"]] == [
        {"yukgap": value, "daygan": "壬"} for value in ("甲寅", "丙寅", "壬寅", "甲辰")
    ]
    assert all(row["columns"] == ["loveWoman"] for row in result["selectors"])
    assert result["facts"]["relationship_element"] == "토"


def test_counsel_returns_source_weights_and_shared_scale_without_inventing_major_luck(natal, partner):
    result = port.decide("counselluck", request(), natal, partner)
    profile = result["facts"]["profiles"]["birth"]
    assert profile["weighted_five_ki"] == {"목": 220, "화": 45, "토": 10, "금": 0, "수": 60}
    largest = max(value for p in result["facts"]["profiles"].values() for value in p["weighted_five_ki"].values())
    assert result["facts"]["shared_graph_divisor"] == max(1, largest / 100)
    assert result["facts"]["major_luck"]["available"] is False
    assert "num·disp_day" in result["unresolved"][0]


def test_fivegi_retains_direction_and_marks_missing_boundaries_as_calculation(natal):
    result = port.decide("fivegiluck", request(), natal, None)
    assert result["facts"]["major_luck_direction"] == "+"
    assert result["facts"]["major_luck"]["available"] is False
    assert result["selectors"][0]["columns"] == ["num", "month_pillar", "disp_day"]
    assert result["selectors"][0]["narrative"] is False


def test_lottery_seed_replays_original_37_retained_array_draw_procedure(natal):
    result = port.decide("lottoluck", request({"seed": 20261118}), natal, None)
    assert result == port.decide("lottoluck", request({"seed": 20261118}), natal, None)
    facts = result["facts"]
    assert (facts["strength_points"], facts["selected_yongsin"], facts["selected_element"]) == (0, "편인", "금")
    assert facts["generated_sample_count"] == 37
    assert facts["source_positions"] == [4, 5, 9, 13, 36]
    assert facts["selected_combinations"] == [
        [7, 9, 26, 37, 41, 42], [3, 14, 17, 19, 27, 33], [3, 5, 9, 13, 25, 44],
        [2, 13, 16, 27, 33, 38], [6, 8, 10, 22, 34, 45],
    ]
    assert facts["explanation_index"] == 5


@pytest.mark.parametrize("seed", [True, -1, 2**32, "123", 1.5])
def test_lottery_rejects_non_integer_or_out_of_range_seeds(seed, natal):
    with pytest.raises(DomainError, match="seed"):
        port.decide("lottoluck", request({"seed": seed}), natal, None)


def test_total_luck_uses_lunar_steps_empty_temp3_and_all_fourteen_outputs(natal):
    result = port.decide("perluck", request(), natal, None)
    keys = {row["id"]: row["where"] for row in result["selectors"]}
    assert result["facts"]["Temp3_uses_empty_zero"] is True
    assert [keys[f"total-{i}"]["title"] for i in range(1, 7)] == ["寅", "월천간", "천액성", "천수행", "생교", "지살"]
    assert keys["result7"] == {"section": "result7", "case": "empty"}
    assert keys["result11"] == {"title": {"in": ["각목", "우토", "목상"]}}
    assert keys["result12"] == {"title": {"in": ["시횡"]}}
    assert keys["result13"] == {"title": {"in": ["해년"]}}
    assert keys["total-8"] == {"part": "금전 및 행운", "title": "해왕성"}
    assert keys["total-14"] == {"title": "3"}


def test_total_luck_fails_closed_when_original_lunar_relookup_has_multiple_rows(natal, monkeypatch):
    fake = SimpleNamespace(raw_store=SimpleNamespace(lunar_candidates=lambda *args: [{}, {}]))
    monkeypatch.setattr(port, "get_manse_store", lambda: fake)
    result = port.decide("perluck", request(), natal, None)
    assert "윤달 조건 없이" in result["unresolved"][0]


@pytest.mark.parametrize("name,a,b,match,code", [
    ("Chung", "子", "午", "충 ", 98), ("Chung", "午", "子", "충 ", 104),
    ("GoGwa_m2f", "辛", "亥", "고과법 ", 16), ("GoGwa_f2m", "辛", "亥", "", 0),
    ("SamJae2_m2f", "巳", "申", "혼삼재2 ", 0),
    ("WolJi", "寅", "丙午", "월덕 천마 ", 61),
    ("ILGan", "戊", "巳", "일덕 일록 은사 일의 천도 ", 73),
    ("ILJi", "寅", "亥", "지파 시살 ", 77),
    ("JiSal", "子", "酉", "복덕 금신 ", 89),
])
def test_sinsal_direction_and_last_assigned_checknum_are_preserved(name, a, b, match, code):
    assert port._gp_rule(name, a, b) == {"match": match, "content_id": code}


def test_sinsal_has_all_23_frozen_helpers_and_no_implicit_cookie_repair(natal, partner):
    tables = port._DATA["sinsalluck"]["tables"]
    assert len(tables) == 23
    assert sum(map(len, tables.values())) == 963
    result = port.decide("sinsalluck", request(), natal, partner)
    assert result["facts"]["gp_func_count"] == 3
    assert result["facts"]["matched_sections"]["male_year"] == "고과살 냉담운 혼삼재2"
    assert result["facts"]["matched_sections"]["year_conflicts"] == "해"
    assert "이전 요청" in result["unresolved"][0]
    empty_cookie = port.decide("sinsalluck", request({"legacy_gpcheck": []}), natal, partner)
    assert "배열 길이를 초과" in empty_cookie["unresolved"][0]


def test_sinsal_explicit_old_cookie_preserves_prior_ids_not_new_matches(natal, partner):
    # Source Gp_ContentCheck checks |code|; last code has no trailing delimiter.
    result = port.decide("sinsalluck", request({"legacy_gpcheck": [98, 99, 100]}), natal, partner)
    assert result["unresolved"] == []
    assert [row["where"]["num"] for row in result["selectors"][1:]] == [98, 99, 100]
    assert result["facts"]["gp_func_count"] == 3


@pytest.mark.parametrize("value", ["|98|", [0], [True], [999], [98] * 65])
def test_sinsal_cookie_is_a_bounded_whitelisted_numeric_array(value, natal, partner):
    with pytest.raises(DomainError):
        port.decide("sinsalluck", request({"legacy_gpcheck": value}), natal, partner)


def test_unrecognized_parameters_never_become_freeform_ai_instructions(natal):
    with pytest.raises(DomainError):
        port.decide("ddiluck", request({"prompt": "invent a result"}), natal, None)

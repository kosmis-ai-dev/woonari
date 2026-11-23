"""CR-012: direct-service fixtures from active ASP branches, including safe input handling."""

import json
from datetime import date
from types import SimpleNamespace

import pytest

from app.calendar import calculate_saju
from app.errors import DomainError
from app.models import Birth
from app.ported_direct import SERVICES, decide
from tools.source_inventory import load_snapshot

SOURCE_FILES = load_snapshot()["files"]
BIRTH = Birth(year=1974, month=3, day=2, hour=8, minute=30, gender="male")


def request(parameters=None, *, birth=BIRTH, target=date(2026, 11, 18)):
    return SimpleNamespace(birth=birth, partner=None, target_date=target,
                           parameters=parameters or {}, include_ai=False)


def run(service_id, value):
    saju = calculate_saju(value.birth, "dotong") if SERVICES[service_id]["uses_saju"] else None
    return decide(service_id, value, saju, None)


@pytest.mark.parametrize("service_id,count", [
    ("analysisluck", 4), ("businessluck", 4), ("birthluck", 7), ("bloodluck", 7),
    ("carluck", 3), ("hpluck", 6), ("juminluck", 1), ("jusoluck", 4), ("preluck", 6),
    ("correctyouluck", 18), ("flowerluck", 7), ("jewelryluck", 4), ("coinluck", 3),
    ("starluck", 7), ("adultluck-starcoupleluck", 3), ("hanjaluck", 2), ("adviceluck", 1),
])
def test_all_direct_examples_have_real_sources_and_explicit_output_contracts(service_id, count):
    result = run(service_id, request(SERVICES[service_id]["example_parameters"]))
    assert result["source"] in SOURCE_FILES
    assert sum(len(selector["columns"]) for selector in result["selectors"]) == count
    assert all(selector["columns"] == list(selector["topics"]) for selector in result["selectors"])
    assert bool(result["unresolved"]) is not SERVICES[service_id]["ready"]


def test_love_analysis_preserves_the_source_social_mod144_typo():
    result = run("analysisluck", request())
    # ASP1385/1399: (1974-1900)%12=2; 11-2+3=12, ordinary %12=0, social %144=12.
    assert [(item["table"], item["where"], item["columns"]) for item in result["selectors"]] == [
        ("love_mind", {"Num": 0}, ["Content"]),
        ("love_lifestyle", {"Num": 0}, ["Content"]),
        ("love_social", {"Num": 12}, ["Content"]),
        ("love_hobby", {"Num": 0}, ["Content"]),
    ]


def test_business_output_order_matches_the_page_instead_of_table_array_order():
    result = run("businessluck", request())
    assert [item["table"] for item in result["selectors"]] == [
        "life_personality", "life_aptitude", "life_advice", "life_basic",
    ]
    assert all(item["where"] == {"Num": 0} for item in result["selectors"])


@pytest.mark.parametrize("service_id,parameters,pillar,code,kind,count", [
    # 1234%60=34 -> 丁酉, then SipKyuk(丁, 壬)=6. Not digit-sum 10.
    ("carluck", {"mycar1": "1234"}, "丁酉", "6", "carnum", 3),
    # 010+0000+0000=10 -> 癸酉, SipKyuk(癸, 壬)=2.
    ("hpluck", {"myHp1": "010", "myHp2": "0000", "myHp3": "0000"}, "癸酉", "2", "Hp", 6),
    # addr+addr2 has the numeric groups 12,34,5. Source concatenates without a separator.
    ("jusoluck", {"zipcode": "000000", "addr": "테스트12길3", "addr2": "4층5호"}, "甲寅", "3", "juso", 4),
    ("carluck", {"mycar1": "0000"}, "癸亥", "2", "carnum", 3),
])
def test_number_formulas_and_sipkyuk_argument_direction(service_id, parameters, pillar, code, kind, count):
    result = run(service_id, request(parameters))
    assert result["facts"]["number_pillar"] == pillar
    assert result["facts"]["sipkyuk_code"] == code
    assert result["facts"]["sipkyuk_ten_god"] == {"6": "정재", "2": "겁재", "3": "식신"}[code]
    assert result["selectors"][0]["where"] == {"unse": kind, "sipkyuk_code": code}
    assert result["selectors"][0]["columns"] == [f"desc{i}" for i in range(1, count + 1)]


@pytest.mark.parametrize("first,second,code", [
    ("999999", "6000000", "60"), ("999999", "7000000", "3"),
    ("999999", "9999999", "3"), ("000000", "0000000", "0"),
])
def test_resident_digit_sum_uses_constant_three_after_sixty(first, second, code):
    result = run("juminluck", request({"myJumin1": first, "myJumin2": second}, birth=None))
    assert result["selectors"][0]["where"] == {"code": code}
    assert result["selectors"][0]["columns"] == ["desc1"]
    assert first + second not in json.dumps(result, ensure_ascii=False)


@pytest.mark.parametrize("parameters", [{}, {"gender": "", "blood": ""}])
def test_blood_source_defaults_need_no_birth_or_saju(parameters):
    result = run("bloodluck", request(parameters, birth=None))
    assert result["selectors"][0]["where"] == {"gender": "남", "blood": "AB"}
    assert list(result["selectors"][0]["topics"].values()) == [
        "특징", "기본성격", "사회성", "인간성", "가치관", "감정", "업무성",
    ]


def test_preluck_uses_raw_year_index_and_lunar_date_keys():
    result = run("preluck", request())
    assert [selector["where"] for selector in result["selectors"]] == [
        {"div_flag": 1, "div_date": 51}, {"div_flag": 2, "div_date": 2},
        {"div_flag": 3, "div_date": 9},
    ]
    assert result["selectors"][0]["columns"] == ["content", "character", "parent", "child"]


def test_preluck_does_not_replace_the_raw_calendar_year_with_the_after_ipchun_year():
    birthday = Birth(year=2024, month=2, day=4, hour=18, minute=0, gender="male")
    assert calculate_saju(birthday, "dotong").pillars["year"].hanja == "甲辰"
    result = run("preluck", request(birth=birthday))
    assert result["selectors"][0]["where"] == {"div_flag": 1, "div_date": 40}  # Raw 癸卯=39.


def test_cabala_harmony_has_nine_ordered_partner_numbers_and_eighteen_topics():
    result = run("correctyouluck", request())
    assert result["facts"]["birth_number"] == 8  # 19740302 -> 26 -> 8.
    assert [selector["where"] for selector in result["selectors"]] == [
        {"menu": "cabala_harmony", "keyno": key} for key in range(81, 90)
    ]
    assert all(selector["columns"] == ["content1", "content2"] for selector in result["selectors"])
    assert result["unresolved"] == []


def test_lunar_conversion_reuses_the_verified_calendar_correction():
    lunar = Birth(year=2023, month=2, day=29, hour=8, minute=30, gender="male",
                  calendar="lunar", leap_month=True)
    result = run("birthluck", request(birth=lunar))
    assert result["selectors"][0]["where"] == {"month": 4, "day": 19}
    assert result["selectors"][0]["columns"] == ["unse"]
    assert any(item["table"] == "wiki_person" and item["narrative"] is False
               for item in result["selectors"])


def test_missing_fact_tables_do_not_become_ai_predictions():
    for service_id, table in [("flowerluck", "flowerluck"), ("jewelryluck", "stoneluck"),
                              ("starluck", "tbStarLuck"), ("coinluck", "tbsaju_juyuk")]:
        result = run(service_id, request(SERVICES[service_id]["example_parameters"]))
        assert result["unresolved"]
        assert any(selector["table"] == table and selector.get("role") == "calculation"
                   and selector["narrative"] is False for selector in result["selectors"])


def test_hanja_reports_the_unassigned_source_return_instead_of_inventing_a_keyword():
    result = run("hanjaluck", request())
    assert result["facts"]["code_prefix"] == "M_01"
    assert result["selectors"][0]["where"] == {"code": None}
    assert len(result["unresolved"]) == 2


def test_advice_preserves_the_source_shift_and_unhandled_year_overflow():
    result = run("adviceluck", request(target=date(2023, 1, 1)))
    assert result["facts"]["source_calendar_date"] == "2023-01-11"
    assert result["facts"]["day_shift_applied"] is True
    assert result["unresolved"]  # Original disp_day and unhandled 59+1 are not invented.


@pytest.mark.parametrize("service_id,parameters", [
    ("carluck", {"mycar1": "9876"}),
    ("hpluck", {"myHp1": "010", "myHp2": "4321", "myHp3": "9876"}),
    ("jusoluck", {"zipcode": "123456", "addr": "비공개12번지", "addr2": "34호"}),
    ("juminluck", {"myJumin1": "999999", "myJumin2": "7000000"}),
])
def test_sensitive_input_values_are_absent_from_decision_output(service_id, parameters):
    result = run(service_id, request(parameters))
    encoded = json.dumps(result, ensure_ascii=False)
    for value in parameters.values():
        assert value not in encoded


@pytest.mark.parametrize("service_id,parameters", [
    ("carluck", {"mycar1": "private-input"}),
    ("carluck", {"mycar1": "1234", "unexpected": "private-input"}),
    ("hpluck", {"myHp1": "010", "myHp2": 1234, "myHp3": "1234"}),
    ("jusoluck", {"zipcode": "12345", "addr": "private-input", "addr2": ""}),
    ("jusoluck", {"zipcode": "000000", "addr": "private-input1000000", "addr2": ""}),
    ("juminluck", {"myJumin1": "private-input", "myJumin2": "0000000"}),
    ("bloodluck", {"blood": "private-input"}),
    ("coinluck", {"bt": "total", **{f"yut{i}": "0" for i in range(6)}}),
    ("coinluck", {"bt": "money", **{f"yut{i}": "2" for i in range(6)}}),
    ("starluck", {"gender": "남", "bloodtype": "A", "startdate": "private-input"}),
])
def test_invalid_parameters_raise_safe_errors_without_echoing_input(service_id, parameters):
    with pytest.raises(DomainError) as caught:
        run(service_id, request(parameters))
    assert caught.value.code == "invalid_service_parameters"
    assert caught.value.status == 422
    assert "private-input" not in caught.value.message


def test_birthless_services_are_explicit_and_unknown_service_is_not_fabricated():
    assert SERVICES["bloodluck"]["requires_birth"] is False
    assert SERVICES["coinluck"]["uses_saju"] is False
    with pytest.raises(DomainError) as caught:
        decide("numluck", request(), None, None)
    assert caught.value.status == 404
    with pytest.raises(DomainError) as caught:
        decide("analysisluck", request(birth=None), None, None)
    assert caught.value.code == "service_birth_required"

"""CR-012/T-024: actual source arithmetic and honest external-data boundaries."""

import hashlib
import json
from datetime import datetime

import pytest

from app.errors import DomainError
from app.models import Birth
from app.ported_interlife_dependencies import SERVICES, TABLES, _animal, decide
from app.service_models import ServiceRequest
from tools.source_inventory import load_snapshot


def request(parameters=None, *, birth=None):
    return ServiceRequest(birth=birth or Birth(year=1974, month=3, day=2, hour=8, minute=30, gender="female"),
                          target_date="2026-11-18", parameters=parameters or {}, include_ai=False)


def test_all_seven_services_are_calculated_partials_with_specific_required_materials():
    assert len(SERVICES) == 7
    assert all(not item["ready"] and item["required_source_fields"] for item in SERVICES.values())
    assert not any(item["uses_saju"] for item in SERVICES.values())


def test_static_calculation_tables_have_pinned_content_and_original_source_hashes():
    canonical = json.dumps(TABLES, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == "02654783c0a314fc2f8b2dca2e4dad0ecd076864e01948703bd9326b2bb56b47"
    inventory = load_snapshot()["files"]
    assert len(TABLES["s058_ordered_groups"]) == 12
    assert sum(len(group["codes"]) for group in TABLES["s058_ordered_groups"]) == 720
    assert len(TABLES["j045_jumc_transforms"]) == 12
    for source in TABLES["sources"]:
        assert inventory[source["path"]]["sha256"] == source["sha256"]


def test_resident_number_source_bug_is_preserved_without_collecting_an_identifier():
    result = decide("interlife-free-4", request())
    assert result["facts"]["source_globals"]["dd"] == list("庚辛壬癸甲乙丙丁戊己庚辛")
    assert result["facts"]["post_error_empty_unmyung_fallback_candidate"] == 10
    assert result["facts"]["resident_number_read_by_leaf"] is False
    assert result["selectors"][0]["where"] == {"DB_express": None}
    assert "생일 합으로 고치지 않습니다" in result["unresolved"][0]


def test_biorhythm_default_does_not_substitute_an_ordinal_for_the_missing_original_serial():
    result = decide("interlife-free-8", request({"server_time": "1974-03-03T12:00:00"}))
    assert result["facts"]["independent_calendar_day_difference"] == 1
    assert result["facts"]["original_total_days"] is None
    assert result["facts"]["calendar_ordinal_used_as_original_num"] is False
    assert result["facts"]["source_february_graph_days"] == 28
    assert result["selectors"][0]["where"] == {"DB_express": None}


@pytest.mark.parametrize("days,phases,key", [(0, [1, 1, 1], "1"), (1, [2, 2, 2], "14"), (17, [3, 3, 1], "25"), (70, [2, 1, 2], "11")])
def test_biorhythm_original_day_number_difference_and_27_class_selector(days, phases, key):
    result = decide("interlife-free-8", request({"day_numbers": {"from_num": 1000, "see_num": 1000 + days, "to_num": 1050}}))
    assert result["facts"]["original_total_days"] == days
    assert result["facts"]["day_numbers"] is None
    assert result["facts"]["source_day_numbers_supplied"] is True
    assert result["facts"]["original_total_life_days"] == 50
    assert result["facts"]["original_phase_classes"] == phases
    assert result["selectors"][0]["where"] == {"DB_express": key}
    assert result["unresolved"]  # User-supplied investigation values are not certified source data.
    if days == 1:
        assert result["facts"]["source_scores"]["physical"] == [0, 26, 51]
        assert result["facts"]["source_scores"]["emotion"] == [0, 22, 43]
        assert result["facts"]["source_scores"]["mental"] == [0, 18, 37]


def test_negative_biorhythm_mod_does_not_wrap_into_an_invented_positive_phase():
    result = decide("interlife-free-8", request({"day_numbers": {"from_num": 1000, "see_num": 999, "to_num": 999}}))
    assert result["facts"]["original_phase_classes"] == [None, None, None]
    assert result["facts"]["original_ment_num"] is None


def test_tarot_uses_server_clock_and_forced_male_with_original_arithmetic(monkeypatch):
    monkeypatch.setattr("app.ported_interlife_dependencies.randbelow", lambda n: n - 1)
    fields = {"my_year_e": "寅", "Xyeargi": 3, "Xdaygan": 9, "todaygan": 3, "yong_code": 2,
              "my_year_h_org": "A", "my_year_e_org": "11", "my_month_e_org": "12"}
    result = decide("interlife-theme-2", request({"server_time": "2026-11-18T12:34:00", "intSuja_cookie": 21,
                                                "tele_cookie": "1234", "source_fields": fields}))
    assert result["facts"]["birth_input_ignored"] is True
    assert result["facts"]["original_forced_server_male_profile"] is True
    assert result["facts"]["f019"]["classification_column"] == "DB_express"
    assert result["facts"]["raw_server_datetime_sum_mod5"] == 1
    assert result["facts"]["trigrams"] == {"under": 8, "over": 8}
    assert result["facts"]["original_unassigned_T039_graph_draw"] == 8
    selectors = {row["id"]: row for row in result["selectors"]}
    assert selectors["tarot"]["where"] == {"DB_express": "21"}
    assert selectors["year-animal"]["where"] == {"DB_express": "3"}
    assert selectors["surname"]["where"] == {"DB_num": "1"}
    assert selectors["place"]["where"] == {"DB_num": "1"}
    assert selectors["season"]["where"] == {"DB_express": "01"}
    assert result["unresolved"] and "1234" not in str(result)


def test_coin_service_new_choices_override_previous_cookie_and_draws_stay_independent(monkeypatch):
    monkeypatch.setattr("app.ported_interlife_dependencies.randbelow", lambda n: n - 1)
    result = decide("interlife-theme-3", request({"server_time": "2026-11-18T12:00:00", "coins": [1, 2, 1, 2],
                                                "intSuja_num": "unused-invalid-cookie", "tele_cookie": "1234"}))
    assert result["facts"]["coin_key"] == "1212"
    assert result["facts"]["independent_draws"] == {"J047": 8, "J048": 8}
    assert result["selectors"][0]["where"] == {"DB_express": "1212"}
    assert result["unresolved"]


def test_janimal_preserves_empty_zero_column_and_literal_animal_lookup():
    result = _animal(datetime(1974, 3, 2))
    assert result == {"year_code": 74, "table_column": 0, "source_empty_column_zero": True,
                      "animal_code": 2, "keyword": "너구리"}
    assert len(TABLES["janimal_months"]) == 12
    assert len(TABLES["janimal_animals"]) == 60


def test_birthstone_uses_raw_input_month_but_solar_date_for_janimal(monkeypatch):
    monkeypatch.setattr("app.ported_interlife_dependencies.solar_birth", lambda b: datetime(1974, 3, 2))
    birthday = Birth(year=1974, month=2, day=9, hour=8, calendar="lunar", gender="female")
    result = decide("interlife-theme-4", request({"tele_cookie": "1234"}, birth=birthday))
    assert result["selectors"][0]["where"] == {"DB_express": "2"}
    assert result["selectors"][2]["where"] == {"DB_express": {"operator": "sql_like", "pattern": "%너구리%"}}
    assert result["facts"]["f019"]["classification_column"] == "DB_express_1"


def test_jum2_preserves_irregular_life_table_and_actual_numeric_dependencies(monkeypatch):
    monkeypatch.setattr("app.ported_interlife.randbelow", lambda n: 0)
    fields = {"todaygan": 3, "todaygi": 12, "Xyeargi": 12, "Xyeargan": 1, "Tmonth": 1, "Xdaygan": 9}
    result = decide("interlife-jum-2", request({"source_fields": fields}))
    assert TABLES["towoonsung"][2][11] == 12  # Preserve source gan_2 last value, not the regular life-stage table.
    assert result["facts"]["available_source_life_stage_code"] == 12
    assert result["facts"]["available_source_dang12"] == 1
    assert "birth-number" not in {row["id"] for row in result["selectors"]}
    numeric = [row for row in result["selectors"] if row["id"].endswith("-score")]
    assert len(numeric) == 5
    assert all(row["columns"] == ["DB_numerical"] and row["role"] == "calculation" for row in numeric)
    assert result["unresolved"]


def test_yukim_preserves_unpadded_time_comparison_and_biased_mod_draw(monkeypatch):
    limits = []

    def draw(n):
        limits.append(n)
        return n - 1

    monkeypatch.setattr("app.ported_interlife_dependencies.randbelow", draw)
    result = decide("interlife-yukim-1", request({"server_time": "2026-11-18T01:05:00", "what": "16",
                                                "source_fields": {"woljang": "子", "lday_h": "甲"}}))
    assert limits == [238722]
    assert result["facts"]["original_unpadded_hhmm"] == "15"
    assert result["facts"]["time_branch"] == "未"
    assert result["facts"]["visit_na"] == 5
    assert result["facts"]["adjusted_time_branch"] == "卯"
    assert result["facts"]["chenban_05"] == "卯"
    assert result["selectors"][0]["where"] == {"DB_express_1": "卯", "DB_express": "甲"}
    assert result["selectors"][0]["columns"] == ["DB_data_16"]
    assert result["unresolved"]  # Optional typed values never bypass verification.


def test_default_yukim_never_guesses_a_month_general(monkeypatch):
    monkeypatch.setattr("app.ported_interlife_dependencies.randbelow", lambda n: 0)
    result = decide("interlife-yukim-1", request({"server_time": "2026-11-18T09:05:00"}))
    assert result["facts"]["time_branch"] == "子"  # '95' >= '2331' in the source string comparison.
    assert result["facts"]["chenban_05"] is None
    assert result["selectors"][0]["key_unresolved"] is True


@pytest.mark.parametrize("service,parameters", [
    ("interlife-free-4", {"jumin": "private-resident-value"}),
    ("interlife-free-8", {"day_numbers": {"from_num": True, "see_num": 1, "to_num": 2}}),
    ("interlife-theme-2", {"intSuja_cookie": 22}),
    ("interlife-theme-3", {"coins": [1, 2, 3, 4]}),
    ("interlife-jum-2", {"source_fields": {"Xyeargi": 0}}),
    ("interlife-yukim-1", {"source_fields": {"woljang": "estimate"}}),
    ("interlife-yukim-1", {"source_fields": {"lday_h": "甲乙"}}),
    ("interlife-yukim-1", {"what": "17"}),
])
def test_invalid_parameters_are_safe_business_errors(service, parameters):
    with pytest.raises(DomainError) as caught:
        decide(service, request(parameters))
    assert caught.value.status == 422
    assert "private-resident-value" not in str(caught.value)

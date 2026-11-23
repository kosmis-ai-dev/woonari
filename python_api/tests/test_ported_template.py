"""CR-012: source matrix fixtures and active-template field/key contracts."""

import json
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.calendar import calculate_saju, solar_birth
from app.errors import DomainError
from app.models import Birth
from app.ported_direct import SERVICES as DIRECT_SERVICES
from app.ported_template import (
    HAN,
    HIDDEN_STEMS,
    SERVICES,
    UN12_JAPAN,
    _love_harmony,
    _zokan_month,
    basic_profile,
    decide,
)
from app.rules import BRANCHES, STEMS
from tools.source_inventory import load_snapshot

SOURCE_FIXTURE = json.loads((Path(__file__).parent / "fixtures/template_source_rules.json").read_text("utf-8"))
SOURCE_FILES = load_snapshot()["files"]
SELF = Birth(year=1974, month=3, day=2, hour=8, minute=30, gender="male")
OTHER = Birth(year=2005, month=12, day=23, hour=8, minute=37, gender="female")


def request(*, birth=SELF, partner=OTHER, target=date(2026, 11, 18), parameters=None):
    return SimpleNamespace(birth=birth, partner=partner, target_date=target, parameters=parameters or {})


def run(service_id, value=None):
    value = value or request()
    spec = SERVICES[service_id]
    mine = calculate_saju(value.birth, "dotong") if spec["uses_saju"] else None
    yours = calculate_saju(value.partner, "dotong") if spec["uses_saju"] and spec["requires_partner"] else None
    return decide(service_id, value, mine, yours)


def test_static_matrices_and_pillar_indexes_match_the_original_asp_definitions():
    assert SOURCE_FIXTURE["schema_version"] == 1
    for path, metadata in SOURCE_FIXTURE["sources"].items():
        assert SOURCE_FILES[path]["sha256"] == metadata["sha256"]
    rules = SOURCE_FIXTURE["rules"]
    for name, actual in (("HanTbl", HAN), ("Un12Tbl_Japan", UN12_JAPAN)):
        rows = rules[name]
        assert len(rows) == 10
        assert tuple(tuple(row) for row in rows) == actual
    for name, expected in (("KAN_Text", STEMS), ("SI_Text", BRANCHES)):
        assert "".join(rules[name]) == expected
    assert tuple(rules["tmpZOKAN"]) == HIDDEN_STEMS
    assert rules["pillar_headings"] == ["時", "日", "月", "年"]


def test_zokan_date_map_matches_every_valid_day_in_the_source_ranges():
    ranges = SOURCE_FIXTURE["rules"]["ZOKAN3_ranges"]
    assert len(ranges) == 13
    current = date(2000, 1, 1)
    while current.year == 2000:
        day = current.strftime("%m%d")
        expected = [entry["stem"] for entry in ranges if entry["start"] <= day <= entry["end"]]
        assert len(expected) == 1
        assert _zokan_month(current.month, current.day) == expected[0]
        current += timedelta(days=1)


def test_basic_profile_has_only_the_source_defined_six_fields_in_hour_day_month_year_order():
    profile = basic_profile(calculate_saju(SELF, "dotong"), solar_birth(SELF).date())
    assert profile == {
        "order": ["hour", "day", "month", "year"],
        "KAN": [1, 9, 3, 1], "SI": [5, 3, 3, 3], "ZOKAN": [5, 1, 1, 1],
        "UN12": [8, 9, 3, 6], "TUHEN": [1, 9, 3, 1], "TUHEN2": [5, 1, 1, 1],
    }
    assert "DAEUN" not in profile and "SEUN" not in profile


@pytest.mark.parametrize("service_id,table,menu,keys", [
    ("humanorganizationmanagement", "tbSajuMaster_mobile1", "bizhostility", [109, 203, 403, 503]),
    ("ourgrowthluck", "tbSajuMaster_mobile1", "marrycheck", [106, 109, 305, 4052]),
    ("adultluck-affairorloveluck", "tbWedding_Content", "immorality", [204, 410, 610]),
    ("adultluck-prohibitionsexluck", "tbSajuMaster_mobile1", "sexcheck", [0, 109, 209, 303]),
    ("adultluck-lovertechniqueluck", "tbSexLove_Content", "", [601, 408, 801]),
    ("adultluck-loverwishluck", "tbSexLove_Content", "", [309, 701, 508]),
])
def test_source_active_branches_have_exact_table_menu_and_key_fixtures(service_id, table, menu, keys):
    result = run(service_id)
    assert result["unresolved"] == []
    assert [selector["where"]["keyno"] for selector in result["selectors"]] == keys
    assert all(selector["table"] == table and selector["where"]["menu"] == menu
               for selector in result["selectors"])
    assert result["facts"]["source_limits"]
    assert result["source"] in SOURCE_FILES


@pytest.mark.parametrize("service_id,keys", [
    ("adultluck-affairorloveluck", [104, 310, 510]),
    ("ourgrowthluck", [106, 109, 305, 4051]),
])
def test_source_gender_suffixes_are_preserved(service_id, keys):
    value = request(birth=SELF.model_copy(update={"gender": "female"}))
    result = run(service_id, value)
    assert [selector["where"]["keyno"] for selector in result["selectors"]] == keys


def test_sexlove_uses_the_source_opposite_gender_even_if_partner_input_gender_is_same():
    value = request(partner=OTHER.model_copy(update={"gender": "male"}))
    result = run("adultluck-lovertechniqueluck", value)
    assert [selector["where"]["sex"] for selector in result["selectors"]] == ["1", "2", "1"]
    female = run("adultluck-lovertechniqueluck", request(birth=SELF.model_copy(update={"gender": "female"})))
    assert [selector["where"]["sex"] for selector in female["selectors"]] == ["2", "1", "2"]


def test_masterman_has_three_resolved_basic_keys_and_three_unresolved_planet_keys():
    result = run("mastermanrelations")
    basic = [selector for selector in result["selectors"] if selector["table"] == "tbSajuMaster_mobile1"]
    assert [selector["where"] for selector in basic] == [
        {"menu": "bizmanpower", "keyno": 401}, {"menu": "bizmanpower", "keyno": 203},
        {"menu": "bizmanpower", "keyno": 306},
    ]
    assert len(result["unresolved"]) == 3
    assert any(selector["table"] == "tbSavianAstro_Planet_1" for selector in result["selectors"])


@pytest.mark.parametrize("service_id,unresolved_count", [
    ("mastermanrelations", 3), ("socialmyhonor", 4), ("wedupluck", 4),
    ("adultluck-bedroommatchingluck", 3),
])
def test_planet_classifications_never_become_arbitrary_ready_predictions(service_id, unresolved_count):
    result = run(service_id)
    assert SERVICES[service_id]["ready"] is False
    assert len(result["unresolved"]) == unresolved_count
    dependencies = [selector for selector in result["selectors"] if selector.get("role") == "calculation"]
    assert dependencies and all(selector["narrative"] is False for selector in dependencies)
    assert all(selector["where"] == {"fdDate": {"lt": None}} for selector in dependencies)
    assert "1974-03-02" not in json.dumps(result)


def test_women_mymarry_preserves_its_actual_array_offsets_in_dependency_diagnostics():
    result = run("adultluck-bedroommatchingluck")
    tables = {selector["table"] for selector in result["selectors"]
              if selector["id"].startswith("women_mymarry-planet-")}
    assert tables == {f"tbSavianAstro_Planet_{number}" for number in (2, 3, 5, 6)}


def test_women_loveharmony_is_asymmetric_in_the_original_remainder_comparison():
    earlier = Birth(year=2000, month=1, day=1, hour=12, gender="male")
    later = earlier.model_copy(update={"day": 2})
    value = request(birth=earlier, partner=later, target=date(2000, 1, 11))
    assert _love_harmony(value) == 11
    reverse = request(birth=later, partner=earlier, target=date(2000, 1, 11))
    assert _love_harmony(reverse) == 2
    partial = run("adultluck-bedroommatchingluck", value)
    assert partial["selectors"][0]["where"] == {"keyno": 11}


@pytest.mark.parametrize("target", [date(2000, 1, 24), date(2000, 1, 25)])
def test_women_loveharmony_keeps_cint_bankers_rounding(target):
    birthday = Birth(year=2000, month=1, day=1, hour=12, gender="male")
    assert _love_harmony(request(birth=birthday, partner=birthday, target=target)) == 13


def test_only_the_ten_assigned_templates_are_registered_without_direct_service_duplicates():
    assert len(SERVICES) == 10
    assert len([item for item in SERVICES.values() if item["ready"]]) == 6
    assert not set(SERVICES).intersection(DIRECT_SERVICES)
    assert "adultluck-timesexbioluck" not in SERVICES


def test_bad_profile_or_additional_parameters_do_not_silently_change_the_contract():
    with pytest.raises(DomainError) as caught:
        basic_profile(calculate_saju(SELF, "today_inline"), solar_birth(SELF).date())
    assert caught.value.code == "service_saju_required"
    with pytest.raises(DomainError) as caught:
        run("humanorganizationmanagement", request(parameters={"private-value": "must-not-echo"}))
    assert caught.value.code == "invalid_service_parameters"
    assert "must-not-echo" not in caught.value.message

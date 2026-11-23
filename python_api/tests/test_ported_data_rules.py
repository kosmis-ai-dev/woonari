"""CR-012/T-024: independently chosen row fixtures for actual ASP comparisons."""

from copy import deepcopy

import pytest

from app.errors import DomainError
from app.manse_corrections import CorrectedManseStore
from app.manse_store import ManseStore
from app.models import Birth
from app.ported_data_rules import FLAGS, SERVICES, _directions, calendar_icons, decide, score_day
from app.service_models import ServiceRequest


@pytest.fixture(autouse=True)
def calendar(monkeypatch):
    store = CorrectedManseStore(ManseStore())
    monkeypatch.setattr("app.calendar.get_manse_store", lambda: store)
    monkeypatch.setattr("app.ported_data_rules.get_manse_store", lambda: store)


def request(parameters=None, *, partner=True):
    return ServiceRequest(birth=Birth(year=1974, month=3, day=2, hour=8, minute=30, gender="male"),
                          partner=Birth(year=2005, month=12, day=23, hour=8, minute=37, gender="female") if partner else None,
                          target_date="2026-11-18", parameters=parameters or {}, include_ai=False)


def flags(**changes):
    return {**dict.fromkeys(FLAGS, False), **changes}


def test_four_registered_rules_are_partial_with_specific_missing_materials():
    assert set(SERVICES) == {"calendarluck", "marriageluck", "moveluck", "mindluck"}
    assert all(not spec["ready"] and spec["required_source_fields"] for spec in SERVICES.values())


def test_calendar_condition_preserves_not_equal_clause_and_combines_rows8_and9():
    rules = [{"change": "乙", "chungan": "甲", "jiji": "午"} for _ in range(11)]
    rules[0] = {"change": "乙", "chungan": "丙", "jiji": "子"}
    rules[1] = {"change": "乙", "chungan": "甲", "jiji": "子"}
    rules[8] = {"change": "甲", "chungan": "甲", "jiji": "子"}
    assert calendar_icons("甲子", rules) == [1, 8]


def test_calendar_uses_actual_daily_pillars_and_fails_closed_without_rules():
    result = decide("calendarluck", request({"year": 2000, "month": 2, "do_num": 7}))
    assert len(result["facts"]["monthly_calendar"]) == 29
    assert all(day["icons"] is None for day in result["facts"]["monthly_calendar"])
    assert result["selectors"][0]["where"] == {"do_num": 7, "sex": "남"}
    assert result["selectors"][0]["role"] == "calculation" and result["unresolved"]


@pytest.mark.parametrize("values,good,score,mark,icons", [
    ({}, False, 50, "■", []),
    ({"yellow_black": True, "hap_chunduk": True, "hap_wolduk": True}, True, 100, "▲", ["대길", "황도", "천덕합", "월덕합"]),
    ({"yellow_black": True, "hap_chunduk": True, "hap_wolduk": True, "sal_chun": True}, True, 49, "▼", []),
    ({"sipak_il": True, "sipak_daepae": True}, True, 30, "▼", []),
    ({"hap_chunduk": True, "hap_wolduk": True}, True, 81, "▲", []),
])
def test_chosen_day_score_order_replaces_positive_points_on_harm(values, good, score, mark, icons):
    result = score_day(flags(**values), good)
    assert result["score"] == score
    assert result["mark"] == mark
    assert result["icons"] == icons


def test_marriage_lunar_age_moduli_and_february_before_lichun_shift():
    rows = {"luck_days": [{"male": 2, "female": 3, "luckDay": "未"}, {"male": 3, "female": 4, "luckDay": "亥"}],
            "chosen_days": [{"day": 1, **flags(yellow_black=True)}, {"day": 5, **flags()}]}
    result = decide("marriageluck", request({"year": 2024, "month": 2, "source_rows": rows}))
    assert result["facts"]["source_ages"] == [51, 20]
    assert result["facts"]["source_age_mod8"] == [3, 4]
    assert result["facts"]["lichun_day"] == 4
    before, after = result["facts"]["monthly_calendar"][0], result["facts"]["monthly_calendar"][4]
    assert before["day_pillar"] == "乙未" and before["before_lichun_age_shift"] == 1
    assert before["role_daegil"] == [True, True] and before["original_scoring"]["score"] == 82
    assert after["day_pillar"] == "己亥" and after["before_lichun_age_shift"] == 0
    assert after["original_scoring"]["score"] == 81
    assert result["facts"]["monthly_calendar"][1]["original_scoring"] is None
    assert result["unresolved"]  # Even complete investigation fixtures cannot authorize AI.


def test_january_age_year_and_missing_partner_are_explicit():
    result = decide("marriageluck", request({"year": 2024, "month": 1}))
    assert result["facts"]["age_year"] == 2023
    assert result["facts"]["source_ages"] == [50, 19]
    with pytest.raises(DomainError) as caught:
        decide("marriageluck", request(partner=False))
    assert caught.value.code == "missing_partner"


def test_month_guidance_uses_fixed_10am_for_the_source_year_branch():
    req = request({"year": 2026, "month": 6})
    req.birth = Birth(year=2024, month=2, day=4, hour=18, minute=0, gender="male")
    result = decide("marriageluck", req)
    # At 18:00 dotong is 甲辰; source CalcSaju(...10,0) is still 癸卯.
    role = result["facts"]["month_guidance"]["roles"][0]
    assert role["birth_year_branch_at_source_10am"] == "卯"
    assert role["base_good_months"] == [1, 6]
    assert role["current_month_class"] == "중계"


def location_rows(male, female):
    return [{"gender": gender, "cont_idx": i, **{f"age_{age}": direction for age in range(9)}}
            for gender, directions in enumerate((male, female)) for i, direction in enumerate(directions)]


def test_moving_couple_direction_order_and_male_only_no_match_fallback():
    rows = location_rows(["동", "서", "남", "북"], ["북", "동", "서", "남"])
    result = _directions(rows, [51, 20], None)
    assert result["source_display_pairs"] == [
        {"male_index": 0, "female_recordset_index": 5, "direction": "동"},
        {"male_index": 1, "female_recordset_index": 6, "direction": "서"},
        {"male_index": 2, "female_recordset_index": 7, "direction": "남"},
        {"male_index": 3, "female_recordset_index": 4, "direction": "북"},
    ]
    unmatched = _directions(location_rows(["동", "서", "남", "북"], ["동북", "동남", "서북", "서남"]), [51, 20], None)
    assert unmatched["source_display_path"] == "male_only_fallback"


def test_moving_direction_duplicate_matches_preserve_source_array_fault_instead_of_repair():
    result = _directions(location_rows(["동"] * 4, ["동"] * 4), [51, 20], None)
    assert result["source_array_overflow"] is True
    assert result["source_display_pairs"] is None


def test_moving_single_gender_keys_and_typed_directions_remain_untrusted():
    rows = location_rows(["동", "서", "남", "북"], [])
    result = decide("moveluck", request({"year": 2024, "month": 1, "source_rows": {"locations": rows}}, partner=False))
    assert result["facts"]["source_ages"] == [50]
    assert result["facts"]["source_age_mod9"] == [5]
    selector = next(row for row in result["selectors"] if row["id"] == "directions")
    assert selector["where"] == {"luck": 0, "gender": 0}
    assert selector["columns"] == ["gender", "age_5", "content", "cont_idx"]
    assert len(result["facts"]["direction_results"]["directions"]) == 4
    assert result["unresolved"]


def test_mindluck_uses_same_sorted_index_and_ignores_loaded_jump_and_score_ranges():
    params = {"mental_id": 17, "answer_index": 1, "source_rows": {
        "questions": [{"content_num": 9}, {"content_num": 2}],
        "members": [{"content_num": 9, "member_num": 20, "jump_position": 888}, {"content_num": 9, "member_num": 10, "jump_position": 999}],
        "results": [{"result_num": 9, "start_point": 100, "end_point": 200}, {"result_num": 4, "start_point": -20, "end_point": -10}],
    }}
    result = decide("mindluck", request(params))
    assert result["facts"]["first_recordset_content_num"] == 9
    assert result["facts"]["visible_member_numbers"] == [10, 20]
    assert result["facts"]["selected_result_num"] == 9
    assert result["facts"]["jump_position_used"] is False
    assert result["facts"]["score_range_used"] is False
    assert result["selectors"][-1]["where"] == {"mental_id": 17, "result_num": 9}
    assert result["unresolved"]


@pytest.mark.parametrize("service,params", [
    ("calendarluck", {"do_num": True}),
    ("calendarluck", {"source_rows": {"cal_rules": [{"unsecode": [], "change": "甲", "chungan": "甲", "jiji": "子"}] * 11}}),
    ("marriageluck", {"source_rows": {"chosen_days": [{"day": [], **flags()}]}}),
    ("marriageluck", {"source_rows": {"chosen_days": [{"day": 1, **flags(yellow_black=1)}]}}),
    ("moveluck", {"mode": []}),
    ("mindluck", {"mental_id": 1, "answer_index": 4}),
    ("mindluck", {"mental_id": 1, "source_rows": {"questions": [{"content_num": 1, "private_name": "secret-input"}]}}),
])
def test_bad_typed_rows_fail_as_safe_422_errors(service, params):
    with pytest.raises(DomainError) as caught:
        decide(service, request(deepcopy(params)))
    assert caught.value.status == 422
    assert "secret-input" not in str(caught.value)

"""CR-012: source fixtures for number arrays, retained quirks and clock bounds."""

from datetime import datetime

import pytest

from app import ported_interlife_extra as extra
from app.errors import DomainError
from app.models import Birth
from app.service_models import ServiceRequest

BIRTH = Birth(year=1974, month=3, day=2, hour=8, minute=30, gender="male")
CLOCK = "2026-11-18T15:20:00+09:00"


def request(parameters=None, *, birth=BIRTH):
    return ServiceRequest(birth=birth, target_date="2026-11-18", parameters=parameters or {}, include_ai=False)


def test_static_arrays_keep_original_lengths_including_unused_61st_entry():
    arrays = extra._DATA["lotto"]
    assert len(arrays["lottoNum"]) == 45
    assert set(arrays["lottoNum"]) == set(range(1, 46))
    assert len(arrays["heng_day_su"]) == 61
    assert all(len(arrays[name]) == 60 for name in ("gabja", "year_su", "month_su", "day_su", "hour_su", "heng_year_su", "heng_month_su", "heng_hour_su"))
    assert len(arrays["juyek_data"]) == len(arrays["juyek_title"]) == 64
    assert set(map(len, arrays["juyek_data"])) == {6}
    assert len(extra._DATA["S058"]) == 720
    assert len(extra._DATA["combination_filters"]) == 29


def test_theme_ports_five_real_outputs_and_keeps_calendar_candidates_unresolved():
    result = extra.decide("interlife-theme-15", request({"server_datetime": CLOCK}))
    facts = result["facts"]
    assert facts["candidate_product"] == 624
    assert facts["candidate_positions"] == {"nam": 84, "nam2": 39, "nam3": 129, "nam4": 174}
    rows = result["selectors"]
    assert [row["table"] for row in rows] == ["S118", "S082", "S090", "S091", "S058"]
    assert rows[0]["where"] == {"DB_express": "2"}
    assert [row["candidate_where"]["DB_express"] for row in rows[1:]] == ["9", "JSH10", "HH10", "01"]
    assert all(row["where"] == {"DB_express": None} for row in rows[1:])
    assert rows[1]["columns"] == ["DB_data"]  # Original overrides male/female column.
    assert rows[-1]["columns"] == ["DB_title", "DB_data"]
    assert result["unresolved"] and "대응이 미검증" in result["unresolved"][0]


def test_lotto_pure_formula_preserves_12_numbers_first_unused_replacement_and_hexagram():
    result = extra.decide("interlife-lotto-1", request({"server_datetime": CLOCK}))
    facts = result["facts"]["candidate_number_calculation"]
    assert facts["natal_sums"] == [784, 120, 353, 674]
    assert facts["natal_total"] == 1931
    assert facts["current_sums"] == [247, 945, 789, 957]
    assert facts["current_total"] == 2938
    assert facts["current_heng_total"] == 2555
    assert facts["numbers"] == [11, 22, 30, 36, 37, 39, 20, 8, 40, 18, 42, 44]
    assert facts["ggum_no"] == 0
    assert facts["hexagram"] == {"source_index": 11, "lines": "111000", "title": "천지비"}
    assert len(set(facts["numbers"])) == 12
    assert result["selectors"][0]["candidate_where"] == {"DB_express": "0906"}
    assert result["unresolved"]


def test_requested_draw_date_does_not_change_original_initial_number_calculation():
    base = extra.decide("interlife-lotto-1", request({"server_datetime": CLOCK}))
    changed = extra.decide("interlife-lotto-1", request({"server_datetime": CLOCK, "draw_date": "2030-01-01"}))
    assert base["facts"]["candidate_number_calculation"] == changed["facts"]["candidate_number_calculation"]
    assert changed["facts"]["draw_date_changes_initial_numbers"] is False


@pytest.mark.parametrize("hour,minute,cutoff,slot", [
    (1, 29, 130, 0), (1, 30, 130, 1), (23, 29, 130, 11), (23, 30, 130, 0),
    (1, 30, 131, 0), (1, 31, 131, 1), (23, 30, 131, 11), (23, 31, 131, 0),
])
def test_birth_and_server_hour_boundaries_differ_by_one_minute(hour, minute, cutoff, slot):
    _, actual = extra._hour("甲", hour, minute, cutoff=cutoff)
    assert actual == slot


def test_source_midnight_day_fix_does_not_reuse_dotong_behavior():
    midnight = extra._calendar_candidate(datetime.fromisoformat("1974-03-02T00:00:00+09:00"), birth=True)
    before = extra._calendar_candidate(datetime.fromisoformat("1974-03-02T00:29:00+09:00"), birth=True)
    after = extra._calendar_candidate(datetime.fromisoformat("1974-03-02T00:30:00+09:00"), birth=True)
    assert midnight["day"] == after["day"] == "壬寅"
    assert before["day"] == "辛丑"


@pytest.mark.parametrize("size,count", [(7, 7), (8, 28), (9, 84), (10, 210)])
def test_combination_mode_ports_all_six_number_groups_and_the_extra_empty_row(size, count):
    result = extra.decide("interlife-lotto-1", request({"mode": "combine", "select_num": list(range(1, size + 1))}, birth=None))
    facts = result["facts"]
    assert result["calculation_only"] is True
    assert result["unresolved"] == []
    assert result["selectors"] == []
    assert facts["generated_combination_count"] == facts["valid_display_combination_count"] == count
    assert len(facts["display_rows"]) == count + 1
    assert facts["display_rows"][-1] == {"numbers": [], "odd_even": "", "decade_counts": [0] * 5}


def test_combination_filters_preserve_original_odd_even_labels_and_blank_row():
    result = extra.decide("interlife-lotto-1", request({"mode": "combine", "select_num": list(range(1, 8)), "want2": True}))
    facts = result["facts"]
    assert facts["valid_display_combination_count"] == 4
    assert {row["odd_even"] for row in facts["display_rows"]} == {"홀3짝3", ""}
    cluster = extra.decide("interlife-lotto-1", request({"mode": "combine", "select_num": list(range(1, 8)), "want11": True}))
    assert cluster["facts"]["valid_display_combination_count"] == 0
    assert len(cluster["facts"]["display_rows"]) == 1  # Empty source row passes this predicate.


def test_combination_undefined_all_four_filters_and_show_all_precedence():
    params = {"mode": "combine", "select_num": list(range(1, 8)), **dict.fromkeys(("want1", "want2", "want3", "want4"), True)}
    result = extra.decide("interlife-lotto-1", request(params))
    assert result["facts"]["source_filter_branch_defined"] is False
    assert result["facts"]["display_rows"] == []
    override = extra.decide("interlife-lotto-1", request({**params, "want0": True}))
    assert override["facts"]["valid_display_combination_count"] == 7


@pytest.mark.parametrize("parameters", [
    {"mode": []}, {"server_datetime": "private fixture"}, {"server_datetime": "2026-11-18"},
    {"draw_date": "20261118"}, {"mode": "combine", "select_num": [1] * 7},
    {"mode": "combine", "select_num": [True, 2, 3, 4, 5, 6, 7]},
    {"mode": "combine", "select_num": list(range(1, 8)), "want1": "yes"},
    {"mode": "combine", "select_num": list(range(1, 8)), "draw_date": "2026-11-18"},
    {"prompt": "private fixture"},
])
def test_invalid_inputs_are_safe_domain_errors(parameters):
    with pytest.raises(DomainError) as caught:
        extra.decide("interlife-lotto-1", request(parameters))
    assert caught.value.code == "invalid_service_parameters"
    assert "private fixture" not in caught.value.message


def test_combination_public_route_marks_calculation_only_and_never_calls_ai():
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    class NoAI:
        async def interpret(self, analysis):
            pytest.fail("Original combination mode has no AI narrative")

        async def close(self):
            pass

    application = create_app(Settings(_env_file=None, api_key=None), interpreter_factory=lambda _: NoAI())
    payload = {"birth": BIRTH.model_dump(mode="json"), "target_date": "2026-11-18", "include_ai": False,
               "parameters": {"mode": "combine", "select_num": list(range(1, 8))}}
    with TestClient(application) as client:
        response = client.post("/v1/un/interlife-lotto-1", json=payload)
        assert response.status_code == 200
        assert response.json()["result"]["service_id"] == "interlife-lotto-1"
        assert response.json()["result"]["calculations"]
        assert "analysis" not in response.json()
        blocked = client.post("/v1/un/interlife-lotto-1", json={**payload, "include_ai": True})
        assert blocked.status_code == 422
        assert blocked.json()["error"]["code"] == "ai_not_applicable"

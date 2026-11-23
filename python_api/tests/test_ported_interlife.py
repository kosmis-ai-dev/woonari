"""T-024 source leaf contracts, source quirks and approved calendar adaptation."""

from copy import deepcopy

import pytest

from app.errors import DomainError
from app.manse_corrections import CorrectedManseStore
from app.manse_store import ManseStore
from app.models import Birth
from app.ported_interlife import FACE_EXAMPLE, SERVICES, decide
from app.service_models import ServiceRequest


@pytest.fixture
def birth():
    return Birth(year=1974, month=3, day=2, hour=8, minute=30, gender="male")


@pytest.fixture
def calendar_store(monkeypatch):
    # Calendar adapter verification always uses the bundled original SQLite rows.
    store = CorrectedManseStore(ManseStore())
    monkeypatch.setattr("app.calendar.get_manse_store", lambda: store)
    return store


def request_for(parameters=None, birth=None):
    return ServiceRequest(
        birth=birth,
        target_date="2026-11-18",
        parameters=parameters or {},
        include_ai=False
    )


def test_registration_separates_ready_narratives_calculations_and_blocked_search():
    assert len(SERVICES) == 12
    assert {key for key, item in SERVICES.items() if item.get("calculation_only")} == {
        "interlife-free-12", "interlife-manse-2"
    }
    assert {key for key, item in SERVICES.items() if not item["ready"]} == {
        "interlife-free-5", "interlife-free-7", "interlife-free-13", "interlife-free-14", "interlife-jum-16"
    }
    assert all(not item["uses_saju"] for item in SERVICES.values())


def test_twelve_animal_output_is_not_a_personal_saju_lookup():
    result = decide("interlife-free-1", request_for({"server_date": "2026-11-18"}))
    assert [item["where"]["DB_express"] for item in result["selectors"]] == [
        "111811", "111812", "111801", "111802", "111803", "111804",
        "111805", "111806", "111807", "111808", "111809", "111810"
    ]
    assert [item["purpose"] for item in result["selectors"]] == [
        "쥐띠", "소띠", "범띠", "토끼띠", "용띠", "뱀띠",
        "말띠", "양띠", "원숭이띠", "닭띠", "개띠", "돼지띠"
    ]
    assert result["facts"]["all_twelve_animals"] is True
    assert result["facts"]["personal_birth_used"] is False
    assert result["unresolved"] == []


@pytest.mark.parametrize(
    "month,day,name,serial",
    [
        (1, 20, "염소자리", 12), (1, 21, "물병자리", 1),
        (2, 19, "물병자리", 1), (2, 20, "물고기자리", 2),
        (3, 20, "물고기자리", 2), (3, 21, "양자리", 3),
        (4, 20, "양자리", 3), (4, 21, "황소자리", 4),
        (5, 21, "황소자리", 4), (5, 22, "쌍둥이자리", 5),
        (6, 21, "쌍둥이자리", 5), (6, 22, "게자리", 6),
        (7, 23, "게자리", 6), (7, 24, "사자자리", 7),
        (8, 23, "사자자리", 7), (8, 24, "처녀자리", 8),
        (9, 23, "처녀자리", 8), (9, 24, "천칭자리", 9),
        (10, 23, "천칭자리", 9), (10, 24, "전갈자리", 10),
        (11, 22, "전갈자리", 10), (11, 23, "사수자리", 11),
        (12, 23, "사수자리", 11), (12, 24, "염소자리", 12)
    ]
)
def test_interlife_zodiac_uses_its_own_source_boundary_table(birth, month, day, name, serial):
    birthday = birth.model_copy(update={"month": month, "day": day})
    result = decide("interlife-free-2", request_for(birth=birthday))
    selector = result["selectors"][0]
    assert selector["table"] == "F013"
    assert selector["where"] == {"DB_express": name}
    assert selector["columns"] == ["DB_data_m"]
    assert result["facts"]["zodiac"] == {"name": name, "source_serial_no": serial}


def test_lunar_zodiac_requires_explicit_raw_request_month_profile(birth):
    lunar = birth.model_copy(update={"calendar": "lunar", "gender": "female"})
    with pytest.raises(DomainError) as caught:
        decide("interlife-free-2", request_for(birth=lunar))
    assert caught.value.code == "interlife_raw_lunar_zodiac"
    result = decide(
        "interlife-free-2",
        request_for({"source_profile": "asp_original_unconverted"}, lunar)
    )
    assert result["selectors"][0]["where"] == {"DB_express": "물고기자리"}
    assert result["selectors"][0]["columns"] == ["DB_data_w"]
    assert result["facts"]["calendar_action"] == "explicit_original_unconverted_lunar_digits"


@pytest.mark.parametrize("value,expected", [("blood_01", "A"), ("blood_02", "B"), ("blood_03", "O"), ("blood_04", "AB"), ("ab", "AB")])
def test_source_blood_codes_and_common_then_gender_text_order(value, expected):
    result = decide("interlife-free-3", request_for({"sex": "여", "blood": value}))
    selector = result["selectors"][0]
    assert selector["where"] == {"DB_express": expected}
    assert selector["columns"] == ["DB_data", "DB_data_w"]
    assert selector["role"] == "narrative"
    assert result["unresolved"] == []


def test_blood_pair_keeps_original_male_female_column_direction():
    first = decide("interlife-free-6", request_for({"bloodm": "bloodm_03", "bloodw": "bloodw_02"}))
    second = decide("interlife-free-6", request_for({"bloodm": "B", "bloodw": "O"}))
    assert first["selectors"][0]["where"] == {"DB_express": "O", "DB_express_1": "B"}
    assert second["selectors"][0]["where"] == {"DB_express": "B", "DB_express_1": "O"}


def face_request(sex="남", **overrides):
    face = deepcopy(FACE_EXAMPLE)
    face.update(overrides)
    return request_for({"sex": sex, "face": face})


def test_face_final_print_order_and_nineteen_source_texts_are_preserved():
    result = decide("interlife-faceface", face_request())
    selectors = result["selectors"]
    assert [item["id"] for item in selectors] == [
        "data_1", "data_2", "data_3", "data_4_1", "data_4_2", "data_4_3", "data_4_4",
        "data_4_5", "data_5_1", "data_5_2", "data_8", "data_7", "data_9", "data_10",
        "data_10_1", "data_12", "data_6_1", "data_6_2", "data_11"
    ]
    assert all(item["table"] == "T063" and item["columns"] == ["DB_data_m"] for item in selectors)
    assert result["facts"]["printed_items"] == 19
    assert "직업" in result["facts"]["unused_source_queries"]
    assert result["unresolved"] == []
    assert result["facts"]["shared_saju_preamble_used"] is False


@pytest.mark.parametrize(
    "shape,wrinkle,key",
    [
        ("이마참자형", "이마주름살한개", "이마참자형||이마발애형&&이마주름살복잡||이마주름살한개"),
        ("이마M자형", "이마주름살복잡", "이마M자형||이마둥근형||이마네모형&&이마주름살복잡||이마주름살한개"),
        ("이마발애형", "이마주름살활형", "이마참자형||이마발애형&&이마주름살세개||이마주름살기러기||이마주름살활형||이마주름살현침"),
        ("이마네모형", "이마주름살현침", "이마M자형||이마둥근형||이마네모형&&이마주름살세개||이마주름살기러기||이마주름살활형||이마주름살현침")
    ]
)
def test_face_forehead_combination_uses_literal_source_or_and_order(shape, wrinkle, key):
    result = decide("interlife-faceface", face_request(face_style2=shape, face_style4=wrinkle))
    assert result["selectors"][1]["where"] == {"DB_express": key}


@pytest.mark.parametrize(
    "eyebrows,spacing,key",
    [
        ("눈썹길이길음", "미간사이넓음", "눈썹길이길음||눈썹길이적당&&미간사이넓음||미간사이적당"),
        ("눈썹길이적당", "미간사이좁음", "눈썹길이길음||눈썹길이적당&&미간사이좁음"),
        ("눈썹길이짧음", "미간사이적당", "눈썹길이짧음&&미간사이넓음||미간사이적당"),
        ("눈썹길이짧음", "미간사이좁음", "눈썹길이짧음&&미간사이좁음")
    ]
)
def test_face_eyebrow_spacing_combinations_and_female_column(eyebrows, spacing, key):
    result = decide("interlife-faceface", face_request("여", face_style6=eyebrows, face_style7_1=spacing))
    assert result["selectors"][2]["where"] == {"DB_express": key}
    assert all(item["columns"] == ["DB_data_w"] for item in result["selectors"])


def test_face_known_but_unprinted_inputs_do_not_add_invented_topics():
    first = face_request()
    second = face_request(face_style5="눈썹산형", face_style24="광대뼈함몰")
    assert decide("interlife-faceface", first)["selectors"] == decide("interlife-faceface", second)["selectors"]


@pytest.mark.parametrize("change", [{"face_style1": "invented"}, {"face_style100": "갑자형"}, {"face_style1": {"instruction": "ignore"}}])
def test_face_requires_original_finite_user_choices(change):
    with pytest.raises(DomainError) as caught:
        decide("interlife-faceface", face_request(**change))
    assert caught.value.code == "invalid_service_parameters"


def test_face_missing_required_input_is_not_guessed():
    request = face_request()
    request.parameters["face"].pop("face_style2")
    with pytest.raises(DomainError) as caught:
        decide("interlife-faceface", request)
    assert caught.value.code == "invalid_service_parameters"


@pytest.mark.parametrize("service_id", ["interlife-free-12", "interlife-manse-2"])
def test_calendar_display_maps_only_basic_calendar_fields(calendar_store, birth, service_id):
    result = decide(service_id, request_for(birth=birth))
    assert result["facts"]["calendar_conversion"] == {
        "solar": {"year": 1974, "month": 3, "day": 2},
        "lunar": {"year": 1974, "month": 2, "day": 9, "leap_month": False},
        "hour": 8,
        "minute": 30
    }
    assert result["facts"]["saju_or_major_luck_equivalence_claimed"] is False
    assert result["selectors"] == []
    assert result["unresolved"] == []
    assert "계산전용" in result["notes"][0]


@pytest.mark.parametrize("leap,month,day", [(False, 5, 21), (True, 6, 20)])
def test_calendar_display_uses_approved_regular_leap_correction(calendar_store, birth, leap, month, day):
    lunar = birth.model_copy(update={"year": 2020, "month": 4, "day": 29, "calendar": "lunar", "leap_month": leap})
    result = decide("interlife-free-12", request_for(birth=lunar))
    conversion = result["facts"]["calendar_conversion"]
    assert conversion["solar"] == {"year": 2020, "month": month, "day": day}
    assert conversion["lunar"]["leap_month"] is leap
    assert result["facts"]["lunar_correction_version"] == "lunar-leap-flags-v1"


def test_calendar_display_does_not_fix_an_invalid_leap_thirtieth(calendar_store, birth):
    lunar = birth.model_copy(update={"year": 2020, "month": 4, "day": 30, "calendar": "lunar", "leap_month": True})
    with pytest.raises(DomainError) as caught:
        decide("interlife-free-12", request_for(birth=lunar))
    assert caught.value.code == "invalid_lunar_date"


def test_dream_search_preserves_bracket_query_and_filtered_page_boundary():
    result = decide("interlife-free-13", request_for({"dream_name": "호랑이", "name1": "무시될값", "page": 3}))
    selector = result["selectors"][0]
    assert selector["table"] == "F020"
    assert selector["where"] == {"DB_title": {"operator": "sql_like", "pattern": "%![호랑이!]%", "escape": "!"}}
    assert selector["pagination"]["boundary_top_count"] == 41
    assert selector["pagination"]["boundary_query_applies_keyword_filter"] is True
    assert result["facts"]["result_count"] is None
    assert selector["narrative"] is False
    assert selector["role"] == "calculation"
    assert result["unresolved"]


def test_dream_name_empty_uses_source_name1_fallback():
    result = decide("interlife-free-13", request_for({"dream_name": "", "name1": "바다"}))
    assert result["selectors"][0]["where"]["DB_title"]["pattern"] == "%![바다!]%"


def test_pregnancy_dream_keeps_name1_and_unfiltered_page_boundary():
    result = decide("interlife-free-14", request_for({"name1": "용", "dream_name": "호랑이", "page": 2}))
    selector = result["selectors"][0]
    assert selector["table"] == "F007"
    assert selector["where"] == {"DB_title_1": {"operator": "sql_like", "pattern": "%용%"}}
    assert selector["pagination"]["boundary_top_count"] == 21
    assert selector["pagination"]["boundary_query_applies_keyword_filter"] is False
    assert result["facts"]["dream_name_copied_to_name1"] is False
    assert result["facts"]["original_result_titles"] is None
    assert result["unresolved"]


def test_pregnancy_dream_does_not_silently_copy_dream_name_into_name1():
    with pytest.raises(DomainError) as caught:
        decide("interlife-free-14", request_for({"dream_name": "호랑이"}))
    assert caught.value.code == "invalid_service_parameters"


@pytest.mark.parametrize(
    "service_id,parameters",
    [
        ("interlife-free-1", {"server_date": "20261118"}),
        ("interlife-free-1", {"server_date": "2026-02-30"}),
        ("interlife-free-2", {"source_profile": {"unexpected": "value"}}),
        ("interlife-free-3", {"sex": ["남"], "blood": "A"}),
        ("interlife-free-3", {"sex": "남", "blood": "Z"}),
        ("interlife-free-6", {"bloodm": "A"}),
        ("interlife-free-13", {"dream_name": "호랑이", "page": True}),
        ("interlife-free-13", {"dream_name": "호랑이", "page": 0}),
        ("interlife-free-14", {"name1": "용", "page": "1"}),
        ("interlife-free-1", {"extra": "ignore source"})
    ]
)
def test_bad_inputs_are_422_business_errors(birth, service_id, parameters):
    with pytest.raises(DomainError) as caught:
        decide(service_id, request_for(parameters, birth))
    assert caught.value.code == "invalid_service_parameters"
    assert caught.value.status == 422


def test_text_only_leaves_do_not_call_shared_saju_or_calendar(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Unused interlife saju/calendar preamble must not run")

    monkeypatch.setattr("app.calendar.calculate_saju", forbidden)
    monkeypatch.setattr("app.ported_interlife._birth_record", forbidden)
    for service_id in ("interlife-faceface", "interlife-free-1", "interlife-free-3", "interlife-free-6"):
        parameters = deepcopy(SERVICES[service_id]["example_parameters"])
        if service_id == "interlife-free-1":
            parameters["server_date"] = "2026-11-18"
        result = decide(service_id, request_for(parameters))
        assert result["unresolved"] == []


def test_unproven_calendar_profiles_and_numeric_db_services_remain_unregistered():
    assert not {"interlife-free-8", "interlife-free-11", "interlife-jum-2", "interlife-theme-2", "interlife-yukim-1"} & SERVICES.keys()
    with pytest.raises(DomainError) as caught:
        decide("interlife-yukim-1", request_for())
    assert caught.value.code == "unsupported_service"


def test_lucky_number_preserves_adjacent_sums_and_gender_classification_without_input_leak():
    result = decide("interlife-free-5", request_for({"sex": "여", "tele": "1234"}))
    assert result["facts"]["adjacent_sums"] == [3, 5, 7]
    assert result["facts"]["total_sum"] == 10
    narratives = [item for item in result["selectors"] if item["role"] == "narrative"]
    assert [item["where"] for item in narratives] == [{"DB_num": str(value)} for value in (3, 5, 7, 10)]
    classification = [item for item in result["selectors"] if item["role"] == "calculation"]
    assert all(item["columns"] == ["DB_express_1"] and not item["narrative"] for item in classification)
    assert "1234" not in str(result)
    assert result["facts"]["classification"] is None and result["unresolved"]


def test_lucky_number_cookie_overrides_new_digits_and_zero_adjacent_rows_are_omitted():
    result = decide("interlife-free-5", request_for({"sex": "남", "tele": "9876", "tele_cookie": "0000"}))
    assert result["facts"]["selection_mode"] == "tele_cookie"
    assert result["facts"]["adjacent_sums"] == [0, 0, 0]
    assert [item["id"] for item in result["selectors"]] == ["total", "total-classification"]
    assert result["selectors"][0]["where"] == {"DB_num": "0"}
    assert result["selectors"][1]["columns"] == ["DB_express"]


def test_lucky_number_blank_source_draws_only_digits_zero_through_eight(monkeypatch):
    limits = []

    def draw(limit):
        limits.append(limit)
        return limit - 1

    monkeypatch.setattr("app.ported_interlife.randbelow", draw)
    result = decide("interlife-free-5", request_for({"sex": "남"}))
    assert limits == [9, 9, 9, 9]
    assert result["facts"]["adjacent_sums"] == [16, 16, 16]
    assert result["facts"]["total_sum"] == 32
    assert "8888" not in str(result)


def test_housing_keeps_real_raw_month_branch_separate_from_unverified_source_key(birth, calendar_store):
    result = decide("interlife-free-7", request_for(birth=birth))
    assert result["facts"]["available_tb_manse_month_branch"] == "寅"
    assert result["facts"]["available_tb_manse_month_branch_code"] == 1
    assert result["facts"]["source_month_e"] is None
    assert result["facts"]["available_basic_calendar_is_original_month_e"] is False
    assert result["selectors"][0]["where"] == {"DB_express": None}
    assert result["selectors"][0]["key_unresolved"] is True and result["unresolved"]


def test_hexagrams_preserve_raw_birthday_mod65_independent_lines_and_source_score_draw_order(birth, monkeypatch):
    values = iter((0, 2, 4))
    monkeypatch.setattr("app.ported_interlife.randbelow", lambda limit: next(values))
    parameters = {"rd": 6, "sticks": [0, 1, 2, 0, 1, 2], "sticks_z": [1] * 6, "sticks_zz": [2] * 6}
    result = decide("interlife-jum-16", request_for(parameters, birth))
    assert result["facts"]["source_birth_date_mod65"] == 52
    assert result["facts"]["source_birth_date_variant"] == "form_strings"
    assert result["facts"]["highlighted_line"] == 6
    assert result["facts"]["hexagram_keys"] == {"past": "222222", "current": "212212", "future": "111111"}
    assert result["facts"]["random_graph_scores"] == {"past": 4, "current": 6, "future": 8}
    assert [item["id"] for item in result["selectors"]] == ["birth-number", "past-name", "past", "current-name", "current", "future-name", "future"]
    assert result["selectors"][0]["where"] == {"DB_express": "52"}
    assert all(item["columns"] == [f"DB_data_{index}" for index in range(1, 9)]
               for item in result["selectors"] if item["id"] in {"past", "current", "future"})
    assert result["facts"]["hexagram_names"] is None and result["unresolved"]


def test_hexagram_missing_lines_and_highlight_use_independent_original_ranges(birth, monkeypatch):
    calls = []

    def draw(limit):
        calls.append(limit)
        return limit - 1

    monkeypatch.setattr("app.ported_interlife.randbelow", draw)
    result = decide("interlife-jum-16", request_for(birth=birth))
    assert calls == [6] + [2] * 18 + [5] * 3
    assert result["facts"]["highlighted_line"] == 6
    assert set(result["facts"]["hexagram_keys"].values()) == {"222222"}
    assert set(result["facts"]["random_graph_scores"].values()) == {8}


@pytest.mark.parametrize("source,key,variant", [
    ({"year": "1974", "month": "03", "day": "02"}, 52, "form_strings"),
    ({"year": "1974", "month": "3", "day": "02"}, 52, "form_strings"),
    ({"year": "1974", "month": "3", "day": "2"}, 7, "form_strings"),
    ({"year": 1974, "month": 3, "day": 2}, 29, "leap_byref_numeric"),
])
def test_j015_preserves_form_string_addition_padding_and_leap_byref_numeric_state(birth, source, key, variant):
    result = decide("interlife-jum-16", request_for({"source_request_date": source}, birth))
    assert result["facts"]["source_birth_date_mod65"] == key
    assert result["facts"]["source_birth_date_variant"] == variant
    assert result["selectors"][0]["where"] == {"DB_express": str(key)}
    assert source not in result["facts"].values()
    assert result["unresolved"]


@pytest.mark.parametrize("service,parameters", [
    ("interlife-free-5", {"sex": "남", "tele": "private-phone-value"}),
    ("interlife-free-5", {"sex": "남", "tele": 1234}),
    ("interlife-jum-16", {"rd": True}),
    ("interlife-jum-16", {"sticks": [1, 2]}),
    ("interlife-jum-16", {"sticks": [True, 1, 1, 1, 1, 1]}),
    ("interlife-jum-16", {"source_request_date": {"year": 1974, "month": "03", "day": "02"}}),
])
def test_partial_service_parameters_fail_safely_without_echo(birth, service, parameters):
    with pytest.raises(DomainError) as caught:
        decide(service, request_for(parameters, birth))
    assert caught.value.status == 422
    assert "private-phone-value" not in str(caught.value)

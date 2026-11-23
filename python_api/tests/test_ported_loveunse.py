"""T-024 source arithmetic fixtures; no live ASP, DB or AI is called."""

from datetime import date

import pytest

from app.errors import DomainError
from app.models import Birth
from app.ported_loveunse import SERVICES, decide, lunar_to_solar, vb_mod
from app.service_models import ServiceRequest


@pytest.fixture
def birth():
    return Birth(year=1974, month=3, day=2, hour=8, minute=30, gender="male")


@pytest.fixture
def partner():
    return Birth(year=1981, month=7, day=14, hour=10, gender="female")


def request_for(birth=None, partner=None, parameters=None, target="2026-11-18"):
    return ServiceRequest(
        birth=birth,
        partner=partner,
        target_date=date.fromisoformat(target),
        parameters=parameters or {},
        include_ai=False
    )


# Independent source fixtures for A=438, D=149, pair total=391.
# Weekly uses source week 3; server-date fixtures use Monday November 16.
@pytest.mark.parametrize(
    "suffix,table,code,count",
    [
        ("lotto", "hm_lotto", "lotto001", 3),
        ("eroticwoto", "hm_eroticman", "sssmto007", 5),
        ("sexwoman", "hm_sexman", "sssm007", 3),
        ("horse", "hm_horse", "ho-race001", 3),
        ("birth-flower", "hm_birth_flower", "datefl0302", 3),
        ("blood-blood", "hm_blood_blood", "bloodkh-A-B", 6),
        ("flower", "hm_flower", "flower011", 3),
        ("game", "hm_game", "game011", 3),
        ("jugan-unse", "hm_jugan_unse", "w008", 2),
        ("prince-date", "hm_prince_date", "wdate0019", 3),
        ("prince-love-today", "hm_prince_love_today", "wlove011", 5),
        ("prince-today", "hm_prince_today", "Wto047", 4),
        ("princess-date", "hm_princess_date", "kdatew0019", 3),
        ("princess-love-today", "hm_princess_love_today", "kglove011", 5),
        ("princess-today", "hm_princess_today", "kto047", 5),
        ("star-un", "hm_star_un", "stara012", 5),
        ("firstdate", "hm_firstdate", "fdate031", 6),
        ("firstsex", "hm_firstsex", "fsex007", 5),
        ("gostop", "hm_gostop", "gostop011", 3),
        ("gunghap", "hm_gunghap", "mw031", 1),
        ("leisure", "hm_leisure", "leisure011", 4),
        ("life-all", "hm_life_all", "sa018", 6),
        ("sok-gonghap", "hm_sok_gonghap", "lovekh007", 4),
        ("star-blood", "hm_star_blood", "star1221", 4),
        ("today-date-unse", "hm_today_date_unse_man", "datem0000", 3),
        ("yupgi-dosa", "hm_yupgi_dosa", "today011", 6)
    ]
)
def test_all_active_cases_preserve_source_selectors(birth, partner, suffix, table, code, count):
    service_id = "loveunse-" + suffix
    metadata = SERVICES[service_id]
    parameters = dict(metadata["example_parameters"])
    if suffix in {"lotto", "horse"}:
        parameters["server_date"] = "2026-11-18"
    result = decide(service_id, request_for(birth, partner, parameters))
    selector = result["selectors"][0]
    assert selector["table"] == table
    assert selector["where"] == {"code": code}
    assert selector["columns"] == [f"content{i}" for i in range(1, count + 1)]
    assert selector["role"] == "narrative"
    assert selector["narrative"] is True
    assert result["unresolved"] == []
    assert result["facts"]["selector_is_score"] is False
    assert metadata["uses_saju"] is False
    assert metadata["ready"] is True


def test_menu_only_love_today_is_not_aliased(birth):
    assert len(SERVICES) == 26
    with pytest.raises(DomainError) as caught:
        decide("loveunse-love-today", request_for(birth))
    assert caught.value.code == "unsupported_service"


def test_blood_pair_has_no_birth_requirement_and_preserves_order():
    first = decide(
        "loveunse-blood-blood",
        request_for(parameters={"user1_blood": "ab", "user2_blood": "o"})
    )
    second = decide(
        "loveunse-blood-blood",
        request_for(parameters={"user1_blood": "o", "user2_blood": "ab"})
    )
    assert first["selectors"][0]["where"]["code"] == "bloodkh-AB-O"
    assert second["selectors"][0]["where"]["code"] == "bloodkh-O-AB"
    assert SERVICES["loveunse-blood-blood"]["requires_birth"] is False


@pytest.mark.parametrize("service_id,error", [("loveunse-game", "birth_required"), ("loveunse-firstdate", "partner_required")])
def test_required_people_are_checked(birth, service_id, error):
    request = request_for(birth if error == "partner_required" else None)
    with pytest.raises(DomainError) as caught:
        decide(service_id, request)
    assert caught.value.code == error


def test_ui_gender_codes_both_use_else_in_original_pair_helper(birth, partner):
    ui_male = decide("loveunse-firstdate", request_for(birth, partner))
    ui_female = decide(
        "loveunse-firstdate",
        request_for(birth.model_copy(update={"gender": "female"}), partner)
    )
    legacy_zero = decide(
        "loveunse-firstdate", request_for(birth, partner, {"legacy_sex": 0})
    )
    assert ui_male["selectors"] == ui_female["selectors"]
    assert legacy_zero["selectors"][0]["where"]["code"] == "fdate019"


def test_princess_date_partner_assignment_replaces_self_total(birth, partner):
    result = decide("loveunse-princess-date", request_for(birth, partner))
    different_self = birth.model_copy(update={"year": 1999, "hour": 22, "day": 10})
    other = decide("loveunse-princess-date", request_for(different_self, partner))
    assert result["selectors"] == other["selectors"]
    assert "partner_replaces_self_total" in result["facts"]["source_assignment_rule"]
    assert result["selectors"][0]["where"]["code"] == "kdatew0019"


@pytest.mark.parametrize("suffix,table,prefix", [("eroticwoto", "hm_eroticwoto", "ssswto"), ("sexwoman", "hm_sexwoman", "sssw")])
def test_female_adult_branch_keeps_table_and_forces_helper_gender_nine(birth, suffix, table, prefix):
    result = decide(
        "loveunse-" + suffix,
        request_for(birth.model_copy(update={"gender": "female"}))
    )
    assert result["selectors"][0]["table"] == table
    assert result["selectors"][0]["where"]["code"] == prefix + "007"
    assert result["facts"]["helper_sex_code"] == 9


@pytest.mark.parametrize(
    "month,day,number,name",
    [
        (3, 20, "012", "물고기"), (3, 21, "001", "양"),
        (4, 19, "001", "양"), (4, 20, "002", "황소"),
        (5, 20, "002", "황소"), (5, 21, "003", "쌍둥이"),
        (6, 21, "003", "쌍둥이"), (6, 22, "004", "게"),
        (7, 22, "004", "게"), (7, 23, "005", "사자"),
        (8, 22, "005", "사자"), (8, 23, "006", "처녀"),
        (9, 22, "006", "처녀"), (9, 23, "007", "천평"),
        (10, 23, "007", "천평"), (10, 24, "008", "전갈"),
        (11, 22, "008", "전갈"), (11, 23, "009", "궁수"),
        (12, 21, "009", "궁수"), (12, 22, "010", "염소"),
        (1, 19, "010", "염소"), (1, 20, "011", "물병"),
        (2, 18, "011", "물병"), (2, 19, "012", "물고기")
    ]
)
def test_source_zodiac_boundaries(birth, month, day, number, name):
    birthday = birth.model_copy(update={"month": month, "day": day})
    result = decide("loveunse-star-un", request_for(birthday))
    assert result["selectors"][0]["where"]["code"] == "stara" + number
    assert result["facts"]["zodiac"]["name"] == name


def test_source_star_blood_exception_changes_key_but_not_zodiac(birth):
    birthday = birth.model_copy(update={"month": 6, "day": 22, "gender": "female"})
    result = decide("loveunse-star-blood", request_for(birthday, parameters={"user_blood": "O"}))
    assert result["selectors"][0]["where"]["code"] == "star0714"
    assert result["facts"]["zodiac"] == {"number": 4, "name": "게"}
    assert "source_code_remap" in result["facts"]


@pytest.mark.parametrize(
    "lunar,solar",
    [
        ((1900, 1, 1), date(1900, 1, 31)),
        ((1974, 3, 2), date(1974, 3, 25)),
        ((2025, 8, 1), date(2025, 9, 22)),
        ((2043, 1, 1), date(2043, 2, 10))
    ]
)
def test_original_regular_lunar_array_known_dates(lunar, solar):
    assert lunar_to_solar(*lunar) == solar


def test_connected_calendar_argument_uses_original_lunar_conversion(birth):
    lunar = birth.model_copy(update={"calendar": "lunar"})
    solar = birth.model_copy(update={"month": 3, "day": 25})
    result = decide("loveunse-life-all", request_for(lunar))
    reference = decide("loveunse-life-all", request_for(solar))
    assert result["selectors"] == reference["selectors"]
    assert result["selectors"][0]["where"]["code"] == "sa041"
    assert result["facts"]["self_profile"]["calendar_action"] == "original_lun2sol_regular_month_array"


def test_missing_calendar_argument_rejects_lunar_until_reproduction_is_explicit(birth):
    lunar = birth.model_copy(update={"calendar": "lunar"})
    with pytest.raises(DomainError) as caught:
        decide("loveunse-birth-flower", request_for(lunar))
    assert caught.value.code == "loveunse_calendar_argument_unassigned"
    result = decide(
        "loveunse-birth-flower",
        request_for(lunar, parameters={"source_profile": "asp_original_unconverted"})
    )
    assert result["selectors"][0]["where"]["code"] == "datefl0302"
    assert result["facts"]["self_profile"]["calendar_action"] == "explicit_original_unconverted_lunar_digits"


@pytest.mark.parametrize(
    "changes,error",
    [
        ({"calendar": "lunar", "leap_month": True}, "unsupported_loveunse_leap_month"),
        ({"calendar": "lunar", "year": 2044}, "loveunse_lunar_year_out_of_range"),
        ({"calendar": "lunar", "day": 31}, "invalid_loveunse_lunar_date")
    ]
)
def test_source_calendar_limits_do_not_silently_fall_back(birth, changes, error):
    with pytest.raises(DomainError) as caught:
        decide("loveunse-life-all", request_for(birth.model_copy(update=changes)))
    assert caught.value.code == error
    assert caught.value.status == 422


def test_server_monday_day_retains_requested_year_and_month(birth):
    result = decide(
        "loveunse-lotto",
        request_for(birth, parameters={"server_date": "2027-01-01"}, target="2027-01-01")
    )
    # A438 + requested year27 + requested month3 + server Monday day28*5 =608.
    assert result["selectors"][0]["where"]["code"] == "lotto008"
    assert result["facts"]["server_week"]["monday"] == "2026-12-28"
    assert result["facts"]["server_week"]["target_year_month_retained"] is True


def test_horse_unassigned_day_oo_preserves_ignored_sat_option(birth):
    plain = decide("loveunse-horse", request_for(birth, parameters={"server_date": "2026-11-18"}))
    sat = decide(
        "loveunse-horse",
        request_for(birth, parameters={"server_date": "2026-11-18", "option_name": "sat"})
    )
    assert plain["selectors"] == sat["selectors"]
    assert sat["facts"]["source_day_oo"] == "VB_Empty_as_zero"


@pytest.mark.parametrize("target,week,code", [("2026-11-07", 1, "w034"), ("2026-11-08", 2, "w003"), ("2026-05-02", 1, "w016"), ("2026-05-03", 2, "w021")])
def test_week_number_counts_source_sunday_boundaries(birth, target, week, code):
    result = decide("loveunse-jugan-unse", request_for(birth, target=target))
    assert result["facts"]["source_week_number"] == week
    assert result["selectors"][0]["where"]["code"] == code


def test_negative_modulo_and_zero_padding_preserve_vb_sign():
    early = Birth(year=1900, month=1, day=1, hour=0, gender="male")
    request = request_for(early, parameters={"legacy_sex": 0}, target="1900-01-01")
    game = decide("loveunse-game", request)
    princess = decide("loveunse-princess-love-today", request)
    assert vb_mod(-88, 12) == -4
    assert game["selectors"][0]["where"]["code"] == "game00-4"
    assert princess["selectors"][0]["where"]["code"] == "kglove004"


def test_minute_is_not_added_to_source_hour_arithmetic(birth):
    first = decide("loveunse-game", request_for(birth.model_copy(update={"minute": 0})))
    second = decide("loveunse-game", request_for(birth.model_copy(update={"minute": 59})))
    assert first["selectors"] == second["selectors"]
    assert first["facts"]["self_profile"]["minute_used"] is False


@pytest.mark.parametrize(
    "service_id,parameters",
    [
        ("loveunse-game", {"legacy_sex": True}),
        ("loveunse-game", {"legacy_sex": "1"}),
        ("loveunse-game", {"unexpected": "ignore original"}),
        ("loveunse-game", {"source_profile": "unknown"}),
        ("loveunse-life-all", {"source_profile": "asp_original_unconverted"}),
        ("loveunse-lotto", {"server_date": "not-a-date"}),
        ("loveunse-star-blood", {"user_blood": "Z"})
    ]
)
def test_invalid_extra_inputs_are_explicit_business_errors(birth, service_id, parameters):
    with pytest.raises(DomainError) as caught:
        decide(service_id, request_for(birth, parameters=parameters))
    assert caught.value.code == "invalid_service_parameters"


def test_no_saju_or_narrative_database_is_needed_for_arithmetic(birth, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("This source helper does not use saju or DB")

    monkeypatch.setattr("app.calendar.calculate_saju", forbidden)
    monkeypatch.setattr("app.calendar.get_manse_store", forbidden)
    result = decide("loveunse-life-all", request_for(birth))
    assert result["selectors"][0]["where"]["code"] == "sa018"
    assert "birth" not in result["facts"]
    assert "name" not in result["facts"]

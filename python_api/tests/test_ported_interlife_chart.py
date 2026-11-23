"""Portable native-profile fixtures frozen from the audited source contracts."""

import json
from datetime import date, datetime, timedelta

import pytest

from app.errors import DomainError
from app.models import Birth
from app.ported_interlife_chart import (
    BRANCHES,
    DATA,
    SourceCurrentRecord,
    SourceYearTerms,
    SourceZiweiBirth,
    SourceZiweiLeaf,
    build_source_globals,
    bundled_source_terms,
    calculate_native,
    decide,
    native_birth,
    native_source_callbacks,
    source_day_hour,
    source_gapja_number,
    source_lunar_to_solar,
    source_major_luck,
    source_natal,
    source_solar_to_lunar,
    source_star_key,
    source_ten_god,
    source_term_lookup,
    source_ziwei_placement,
)
from app.ported_interlife_display import _rules as display_rules
from app.ported_ziwei import (
    EMPTY,
    SUPPORTED_BUILTINS,
    FunctionResult,
    Missing,
    compile_predicates,
    execute,
)
from app.ported_ziwei import _program as ziwei_rules
from app.service_models import ServiceRequest

ROWS = {"birth": {"no": "19740302", "number": 27000, "day_h": "I", "day_e": "01", "jeolip": ""},
        "selected": {"number": 27000, "year_h": "A", "year_e": "01", "month_h": "C", "month_e": "01"}}
CURRENT = {"no": "20261118", "umdate": "20261010", "umyear_h": "丙", "umyear_e": "午"}
ZIWEI_BIRTH = {"year_h": "甲", "year_e": "寅", "lunar_year": 1974, "lunar_month": "02", "lunar_day": "09"}


@pytest.fixture
def birth():
    return Birth(year=1974, month=3, day=2, hour=8, minute=30, gender="male")


@pytest.fixture
def native(birth):
    return calculate_native(
        birth, source_solunar=2, terms_by_year=bundled_source_terms(2029), reference_year=2026
    )


def test_frozen_source_tables_preserve_actual_ranges_and_counts():
    assert DATA["version"] == "interlife-chart-source-v1"
    assert len(DATA["term_rows"]) == 3600
    assert len(DATA["source_lunar_table"]) == 170
    assert len(DATA["source_leap_dates"]) == 3207
    assert len(DATA["source_malformed_leap_rows"]) == 40
    assert len(DATA["find_yong"]["decision_matrix"]) == 25 * 126
    assert len(DATA["ziwei_ming_body"]) == 12
    assert len(DATA["ziwei_jami_positions"]) == 5
    assert all(len(source["sha256"]) == 64 and source["lines"] > 0 for source in DATA["sources"])


def test_two_digit_dates_require_source_policy_instead_of_prefix_year_repair():
    unambiguous = bundled_source_terms(None)
    assert set(unambiguous) == set(range(1901, 1930))
    assert set(bundled_source_terms(2029)) == set(range(1901, 2050))
    assert bundled_source_terms(2029)[1974][2] == datetime(1974, 2, 4, 14)
    assert bundled_source_terms(2029)[2030][2].year == 1930
    assert bundled_source_terms(2049)[1945][2].year == 2045
    assert 2050 not in bundled_source_terms(2099)


@pytest.mark.parametrize(
    "clock,day,hour,shift,advanced",
    [
        ((23, 29), "壬寅", "辛亥", 0, False),
        ((23, 30), "癸卯", "壬子", 0, True),
        ((0, 0), "壬寅", "庚子", -1, True),
        ((0, 29), "壬寅", "庚子", -1, True),
        ((0, 30), "壬寅", "庚子", 0, False),
        ((1, 29), "壬寅", "庚子", 0, False),
        ((1, 30), "壬寅", "辛丑", 0, False)
    ]
)
def test_native_clock_day_boundaries_are_distinct_from_dotong(clock, day, hour, shift, advanced):
    result = source_day_hour(datetime(1974, 3, 2, *clock))
    assert result["pillars"]["day"]["hanja"] == day
    assert result["pillars"]["hour"]["hanja"] == hour
    assert result["corrected_date_shift_days"] == shift
    assert result["late_zi_advance"] is advanced
    assert "corrected_datetime" not in result


def test_all_1440_hour_branches_match_the_independent_buffer_clock_intervals():
    # sajuyowha:201-219 uses civil HHMM intervals while f_Saju shifts by30min.
    # This proves this one field's equivalence; it does not equate both profiles.
    for minute in range(24 * 60):
        hour, part = divmod(minute, 60)
        hhmm = hour * 100 + part
        if hhmm < 130 or hhmm >= 2330:
            expected = "子"
        else:
            expected = BRANCHES[(minute - 90) // 120 + 1]
        assert source_day_hour(datetime(1974, 3, 2, hour, part))["pillars"]["hour"]["branch"] == expected


def test_year_uses_shifted_clock_but_month_uses_civil_clock_at_lichun():
    terms = bundled_source_terms(2029)
    instant = terms[1974][2]
    at = source_natal(instant, terms)
    after = source_natal(instant + timedelta(minutes=30), terms)
    assert at["pillars"]["year"]["hanja"] == "癸丑"
    assert at["pillars"]["month"]["branch"] == "寅"
    assert after["pillars"]["year"]["hanja"] == "甲寅"
    assert at["month_comparison"].startswith("unshifted_birth")


def test_full_native_sample_preserves_raw_arrays_and_yongsin_order_bug(native):
    assert native["active_native_algorithm_complete"] is True
    assert [native["natal"]["pillars"][key]["hanja"] for key in ("year", "month", "day", "hour")] == ["甲寅", "丙寅", "壬寅", "甲辰"]
    assert native["yongsin"]["paljayuk"] == ["食神", "食神", "偏財", "食神", "食神", "食神", "偏官"]
    assert native["yongsin"]["counts_in_bi_sh_ja_kw"] == [0, 0, 3, 1, 1]
    assert native["yongsin"]["return_value"] == "土-金-水-木-火|2-1-5-4-3|01|09|07"
    values = native["source_variables"]
    assert values["hansin"] == "土" and values["han_code"] == "2"
    assert values["yongsin"] == "火" and values["yong_code"] == "3"
    assert values["gongmang"] == "辰巳"
    assert (values["dae1gan"], values["dae1gi"]) == ("丁", "卯")
    assert (values["dae8gan"], values["dae8gi"]) == ("甲", "戌")
    assert "byear" not in values
    assert [error["line"] for error in native["source_state_errors"]] == [334, 335, 336]


def test_all_220_ten_gods_match_independent_literal_f029_tables():
    labels = {"비견": "比肩", "겁재": "劫財", "식신": "食神", "상관": "傷官", "편재": "偏財", "정재": "正財", "편관": "偏官", "정관": "正官", "편인": "偏印", "정인": "正印"}
    tables = DATA["f029_ten_god_arrays"]
    for pairs, values, branch in (
        ("ilgan_chengan", "ilgan_chengan_sipsin", False),
        ("ilgan_jiji", "ilgan_jiji_sipsin", True)
    ):
        for pair, value in zip(tables[pairs], tables[values]):
            assert source_ten_god(pair[1], pair[0], branch) == labels[value]


def test_find_yong_matrix_covers_all_source_shapes_and_possible_five_slot_counts():
    actual_shapes = set()
    for key, values in DATA["find_yong"]["decision_matrix"].items():
        shape, *counts = map(int, key.split("|"))
        actual_shapes.add(shape)
        assert sum(counts) == 5
        assert len(values) == 2 and all(1 <= value <= 5 for value in values)
    assert actual_shapes == set(range(1, 26))


def test_all_saju_made_hour_elements_match_frozen_independent_source_branches(birth):
    # These 120 pairs were frozen by evaluating the original 157..309 branch
    # program with each day stem / Hangul hour, independently of native math.
    checked = set()
    for offset in range(10):
        for branch in range(12):
            person = birth.model_copy(update={"day": birth.day + offset, "hour": branch * 2, "minute": 30})
            native = calculate_native(person, source_solunar=2, terms_by_year=bundled_source_terms(2029), reference_year=2026)
            values = native["source_variables"]
            expected = DATA["saju_made_hour_element_rows"][values["daygan"]][branch]
            assert [values["Xtimegan_oh"], values["Xtimegi_oh"]] == expected
            checked.add((values["daygan"], branch))
    assert len(checked) == 120


def test_major_luck_uses_ole_date_components_and_source_return_order(native):
    major = native["major_luck"]
    assert major["direction"] == "forward"
    assert major["boundary"] == "1974-03-06T08:07:00"
    assert major["ole_date_day_component"] == 2
    assert major["ole_date_half_hour_component"] == 11.5
    assert major["source_daeunsu"] == 1
    assert [pair["start_number"] for pair in major["pairs"]] == [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]
    assert [pair["hanja"] for pair in major["returned_first_eight"]] == ["丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉", "甲戌"]


def test_female_major_luck_reverses_original_month_pillar(native):
    result = source_major_luck(datetime(1974, 3, 2, 8, 30), "female", native["natal"], bundled_source_terms(2029), 2026)
    assert result["direction"] == "backward"
    assert result["pairs"][0]["hanja"] == "乙丑"


def test_source_last_term_equality_error_is_not_silently_repaired():
    terms = bundled_source_terms(2029)
    value = terms[1974][-1]
    with pytest.raises(DomainError) as caught:
        source_major_luck(value, "male", source_natal(value, terms), terms)
    assert caught.value.code == "source_last_term_equality_unverified"


def test_century_mismatch_is_kept_and_negative_major_interval_is_blocked():
    terms = bundled_source_terms(2029)
    value = datetime(2030, 3, 2, 8, 30)
    natal = source_natal(value, terms)
    assert natal["term_date_year_matches_array_key"] is False
    assert natal["month_scan_exit_index"] == 25
    with pytest.raises(DomainError) as caught:
        source_major_luck(value, "male", natal, terms)
    assert caught.value.code == "source_term_century_order_unverified"


def test_original_solar_lunar_conversion_is_not_replaced_by_tb_manse():
    assert source_solar_to_lunar(date(1903, 10, 20)) == {"year": 1903, "month": 9, "day": 1, "leap_month": False}
    assert source_solar_to_lunar(date(1974, 3, 2)) == {"year": 1974, "month": 2, "day": 9, "leap_month": False}
    assert source_lunar_to_solar(1974, 2, 9)["solar_date"] == date(1974, 3, 2)


def test_source_december_last_day_raw_zero_is_normalized_as_dateserial():
    result = source_lunar_to_solar(1974, 11, 18)
    assert (result["raw_year"], result["raw_month"], result["raw_day"]) == (1975, 1, 0)
    assert result["source_day_zero_normalized"] is True
    assert result["solar_date"] == date(1974, 12, 31)


def test_native_lunar_and_solar_inputs_have_same_pillars_under_explicit_binding(birth, native):
    lunar = birth.model_copy(update={"month": 2, "day": 9, "calendar": "lunar"})
    result = calculate_native(lunar, source_solunar=1, terms_by_year=bundled_source_terms(2029), reference_year=2026)
    assert result["natal"]["pillars"] == native["natal"]["pillars"]
    assert result["source_variables"]["byear"] == "1974"
    assert result["source_state_errors"] == []


@pytest.mark.parametrize("binding", [True, "2", 0, 4, 1])
def test_native_calendar_binding_is_explicit_and_matches_public_birth(birth, binding):
    with pytest.raises(DomainError):
        native_birth(birth, binding)


def test_malformed_original_leap_row_is_reported_without_inserting_separator():
    lunar = Birth(year=1984, month=10, day=10, hour=8, gender="male", calendar="lunar", leap_month=True)
    with pytest.raises(DomainError) as caught:
        native_birth(lunar, 3)
    assert caught.value.code == "source_leap_record_malformed"


def test_native_leap_lookup_preserves_raw_form_padding_instead_of_fixing_it():
    lunar = Birth(year=1900, month=8, day=1, hour=8, gender="male", calendar="lunar", leap_month=True)
    original, _ = native_birth(lunar, 3, {"year": "1900", "month": "8", "day": "1"})
    assert original.date() == date(1900, 9, 24)
    with pytest.raises(DomainError) as caught:
        native_birth(lunar, 3, {"year": "1900", "month": "08", "day": "01"})
    assert caught.value.code == "source_leap_request_padding_unmatched"
    # Omitting raw tokens is an explicit integer-argument calculation profile.
    assert native_birth(lunar, 3)[0] == original


@pytest.mark.parametrize("tokens", [
    {"year": 1974, "month": 3, "day": 3},
    {"year": 1974, "month": True, "day": 2},
    {"year": "1974", "month": "003", "day": "02"},
    {"year": "1974", "month": "03", "day": "private-value"}
])
def test_native_raw_tokens_are_typed_and_bound_to_the_public_birth(birth, tokens):
    with pytest.raises(DomainError) as caught:
        native_birth(birth, 2, tokens)
    assert "private-value" not in str(caught.value)


def test_native_raw_token_profile_does_not_publish_raw_birth_values(birth):
    result = calculate_native(birth, source_solunar=2, terms_by_year=bundled_source_terms(2029), reference_year=2026,
                              source_native_request_date={"year": "1974", "month": "03", "day": "02"})
    assert result["source_native_input_variant"] == "explicit_source_tokens"
    assert "source_native_request_date" not in result


def test_unmatched_leap_source_investigation_reproduces_ordinary_lunar_fallback():
    lunar = Birth(year=1903, month=5, day=1, hour=8, gender="male", calendar="lunar", leap_month=True)
    instant, effective = native_birth(lunar, 3, {"year": "1903", "month": "05", "day": "01"}, "original_regular_fallback")
    assert instant.date() == date(1903, 5, 27)
    assert native_birth(lunar, 3)[0].date() == date(1903, 6, 25)
    assert effective["requested_leap_month"] is True
    assert effective["leap_month"] is False
    assert effective["source_leap_lookup_matched"] is False
    assert effective["source_effective_calendar"] == "original_regular_lunar_fallback"


def test_malformed_leap_line_also_takes_original_no_match_fallback_in_investigation():
    lunar = Birth(year=1984, month=10, day=10, hour=8, gender="male", calendar="lunar", leap_month=True)
    instant, effective = native_birth(lunar, 3, source_leap_mismatch_policy="original_regular_fallback")
    assert instant.date() == date(1984, 11, 2)
    assert effective["source_lookup_reason"] == "source_leap_record_malformed"


def test_complete_native_fallback_math_retains_binding_warning_for_ai():
    lunar = Birth(year=1903, month=5, day=1, hour=8, gender="male", calendar="lunar", leap_month=True)
    result = calculate_native(lunar, source_solunar=3, terms_by_year=bundled_source_terms(None), reference_year=2026,
                              source_native_request_date={"year": "1903", "month": "05", "day": "01"},
                              source_leap_mismatch_policy="original_regular_fallback")
    assert result["active_native_algorithm_complete"] is True
    assert result["source_effective_calendar"] == "original_regular_lunar_fallback"
    assert result["source_unresolved_bindings"] == ["source_leap_lookup_unmatched_regular_fallback"]
    assert result["source_state_errors"][0]["reason_code"] == "source_leap_request_padding_unmatched"
    assert result["source_variables"]["byear"] == "1903"


@pytest.mark.parametrize("policy", [None, True, [], "auto_fix"])
def test_native_leap_mismatch_policy_never_accepts_implicit_auto_fix(birth, policy):
    with pytest.raises(DomainError) as caught:
        native_birth(birth, 2, source_leap_mismatch_policy=policy)
    assert caught.value.code == "invalid_service_parameters"


def test_native_private_callback_returns_exact_five_slot_solosaju_contract():
    messages = []
    functions = native_source_callbacks(terms_by_year=bundled_source_terms(2029), reference_year=2026, diagnostics=messages)
    output = functions["b_saju_click"]("1", 1, "1974", "03", "02", "08", "30", "")
    assert isinstance(output, FunctionResult)
    assert output.value[0].split("|") == list("甲寅丙寅壬寅甲辰丁卯戊辰己巳庚午辛未壬申癸酉甲戌")
    assert output.value[1:3] == ["1", "土-金-水-木-火|2-1-5-4-3|01|09|07"]
    assert output.value[3] == "1974년 3월 2일 辰시 (土요일)"
    assert output.value[4] == "1974년 2월 9일 08시 30분 "
    assert output.byref == {} and output.writes == {}
    assert messages == []


def test_native_callback_leap_success_mutates_only_three_original_date_arguments():
    functions = native_source_callbacks(terms_by_year=bundled_source_terms(None), reference_year=2026)
    program = compile_predicates([(1, 'y="1903":m="5":d="1":h="08":n="30"'),
                                  (2, 'result=b_saju_click("1",3,y,m,d,h,n,"")')])
    result = execute(program, {}, functions=functions)
    assert (result["variables"]["y"], result["variables"]["m"], result["variables"]["d"]) == (1903, 6, 25)
    assert (result["variables"]["h"], result["variables"]["n"]) == ("08", "30")
    assert all(type(result["variables"][name]) is int for name in ("y", "m", "d"))
    assert len(result["variables"]["result"]) == 5
    assert result["source_errors"] == []


def test_native_callback_padding_fallback_preserves_form_strings_and_diagnostic():
    messages = []
    functions = native_source_callbacks(terms_by_year=bundled_source_terms(None), reference_year=2026, diagnostics=messages)
    program = compile_predicates([(1, 'y="1903":m="05":d="01"'),
                                  (2, 'result=b_saju_click("1",3,y,m,d,"08","30","")')])
    result = execute(program, {}, functions=functions)
    assert (result["variables"]["y"], result["variables"]["m"], result["variables"]["d"]) == ("1903", "05", "01")
    assert result["variables"]["result"][3].startswith("1903년 5월 27일")
    assert messages == [{"source": "old/unse/interlife/UNSE_DATA/solve/f_Saju.asp", "code": "source_leap_lookup_unmatched_regular_fallback", "category": "source_binding"}]
    assert "1903" not in json.dumps(messages)


def test_original_empty_sun_value_deterministically_takes_regular_lunar_path():
    messages = []
    functions = native_source_callbacks(terms_by_year=bundled_source_terms(2029), reference_year=2026, diagnostics=messages)
    output = functions["b_saju_click"]("1", EMPTY, "1974", "03", "02", "08", "30", "")
    assert isinstance(output, FunctionResult)
    assert output.value[3].startswith("1974년 3월 25일")
    assert output.value[4] == "1974년 3월 2일 08시 30분 "
    assert output.byref == {}
    assert messages[0]["code"] == "source_calendar_binding_empty_regular_fallback"


def test_term_callbacks_preserve_all_boundary_indices_and_source_empty_quirk():
    terms = bundled_source_terms(2029)
    for number, instant in enumerate(terms[1974], 1):
        index = source_term_lookup("fi_pre_div24", instant, terms)
        previous = source_term_lookup("f_pre_div24", instant, terms)
        following = source_term_lookup("f_next_div24", instant, terms)
        if number == 24:
            assert index is EMPTY and previous is EMPTY
            assert following == terms[1974][0]
        else:
            assert index == number and previous == instant
            assert following == terms[1974][number]
    early = datetime(1974, 1, 1)
    assert source_term_lookup("fi_pre_div24", early, terms) == 24
    assert source_term_lookup("f_pre_div24", early, terms) == terms[1973][-1]
    assert source_term_lookup("f_next_div24", early, terms) == terms[1974][0]
    assert source_term_lookup("f_next_div24", terms[1974][-1] + timedelta(minutes=1), terms) == terms[1975][0]


def test_native_callbacks_report_missing_policies_without_raw_input_values():
    messages = []
    functions = native_source_callbacks(terms_by_year={}, reference_year=2026, diagnostics=messages)
    assert isinstance(functions["b_saju_click"]("1", 1, "1974", "03", "02", "08", "30", ""), Missing)
    assert isinstance(functions["f_pre_div24"]("1974-03-02"), Missing)
    assert isinstance(functions["f_pre_div24"]("03/02/1974"), Missing)
    assert {entry["code"] for entry in messages} == {"source_terms_required", "source_date_interpretation_required"}
    assert "1974" not in json.dumps(messages)


def test_explicit_current_calendar_record_validates_source_field_meanings():
    row = SourceCurrentRecord(no="20261118", umdate="20261010", umyear_h="丙", umyear_e="午")
    assert row.umyear_h == "丙"
    with pytest.raises(ValueError):
        SourceCurrentRecord(no="20261118", umdate="20261340", umyear_h="丙", umyear_e="午")
    with pytest.raises(ValueError):
        SourceCurrentRecord(no="20261118", umdate="20261010", umyear_h="甲", umyear_e="丑")


def test_typed_terms_validate_number_order_and_fixed_korean_time():
    dates = bundled_source_terms(2029)[1974]
    rows = [{"number": number, "at": value.isoformat()} for number, value in enumerate(dates, 1)]
    assert SourceYearTerms(year=1974, terms=rows).terms[2].at == datetime(1974, 2, 4, 14)
    with pytest.raises(ValueError):
        SourceYearTerms(year=1974, terms=list(reversed(rows)))
    with pytest.raises(ValueError):
        SourceYearTerms(year=1974, terms=[{**row, "at": row["at"] + "Z"} for row in rows])


def test_frozen_ziwei_early_source_tables_preserve_exact_principal_star_fixture():
    birth = SourceZiweiBirth(year_h="甲", year_e="寅", lunar_year=1974, lunar_month="02", lunar_day="09")
    result = source_ziwei_placement(birth, "辰")
    assert result["life_palace_position"] == 10
    assert result["body_palace_position"] == 6
    assert result["myung_guk"] == "火6局"
    assert len(result["principal_stars"]) == 14
    assert result["principal_stars"]["jami"] == {"position": 11, "label": "자미"}
    assert result["principal_stars"]["cheanbu"] == {"position": 3, "label": "천부"}
    assert result["principal_stars"]["pagun"] == {"position": 1, "label": "파군"}


@pytest.mark.parametrize("raw,expected", [("자미", "자미"), ("자미천상", "자미천상"), ("자미천상문곡", "자미천상문곡"), ("자미천상기문곡권", "자미천상기문"), ("자미기천상문곡권", "상문곡권"), ("자미천상문곡문창천기문곡", "자미천상문곡")])
def test_j017_to_j030_source_string_compression(raw, expected):
    assert SourceZiweiLeaf(palace="寅", stars=raw).stars == raw
    assert source_star_key(raw) == expected


def test_original_three_chene_queries_are_kept_as_distinct_tables():
    by_table = {row["table"]: row for row in DATA["ziwei_text_leaves"]}
    assert [by_table[table]["stars_field"] for table in ("J020", "J021", "J022")] == ["chene"] * 3
    assert set(by_table) == {f"J{number:03d}" for number in range(17, 31)}


def test_pure_native_math_never_calls_manse_store(birth, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("The native source profile uses its own frozen DAT")

    monkeypatch.setattr("app.calendar.get_manse_store", forbidden)
    result = calculate_native(birth, source_solunar=2, terms_by_year=bundled_source_terms(2029), reference_year=2026)
    assert result["active_native_algorithm_complete"]


def test_source_gapja_number_preserves_all_sixty_one_based_pairs():
    for index in range(60):
        assert source_gapja_number(index % 10 + 1, index % 12 + 1) == index + 1
    with pytest.raises(DomainError):
        source_gapja_number(1, 2)


def _request(birth, parameters=None):
    return ServiceRequest(birth=birth, target_date=date(2026, 11, 18), include_ai=False,
                          parameters={"server_date": "2026-11-18", **(parameters or {})})


@pytest.mark.parametrize("service_id", ["interlife-free-11", "interlife-manse-1"])
def test_display_default_reports_real_missing_rows_and_source_faults(birth, service_id):
    result = decide(service_id, _request(birth))
    display = result["facts"]["display"]
    assert display["algorithm_complete"] is True
    assert display["native_profile_substituted_for_original_rows"] is False
    assert any("source_birth_rows.selected.year_h" in value for value in result["unresolved"])
    assert any(value.startswith("source_unassigned_state:") for value in result["unresolved"])
    assert any(value.startswith("source_syntax_anomaly:") for value in result["unresolved"])
    assert "algorithm_port_incomplete" not in json.dumps(result)
    assert result["selectors"] == []


@pytest.mark.parametrize("service_id", ["interlife-free-11", "interlife-manse-1"])
def test_complete_display_predicates_export_source_pillars_and_hidden_stems(birth, service_id):
    result = decide(service_id, _request(birth, {
        "source_birth_rows": ROWS, "source_current_record": CURRENT,
        "source_state": {"my_age": 53, **{f"daeun{index}_no": index * 10 for index in range(1, 11)}}
    }))
    display = result["facts"]["display"]
    assert display["missing_fields"] == {}
    assert display["source_pillars"]["day"] == {"h": "壬", "e": "寅", "h_org": "I", "e_org": "01"}
    assert display["source_pillars"]["hour"] == {"h": "甲", "e": "辰", "h_org": "A", "e_org": "03"}
    assert display["hidden_stems"]["day"] == {"stem1": "무", "stem2": "병", "stem3": "갑"}
    assert display["hidden_stems"]["hour"] == {"stem1": "을", "stem2": "계", "stem3": "무"}
    assert len(display["display_fields"]) == 82
    assert len(display["major_pillars"]) == 10
    assert display["unassigned_source_inputs"] == []
    assert {value.split(":", 1)[0] for value in result["unresolved"]} == {"source_syntax_anomaly", "provided_source_records_unverified"}
    serialized = json.dumps(result["facts"], ensure_ascii=False)
    assert all(private not in serialized for private in ("19740302", "1974-03-02", "08:30", "member_hour_min", "source_birth_rows"))


def test_full_ziwei_calculation_builds_fourteen_original_leaf_selectors(birth):
    result = decide("interlife-jum-1", _request(birth, {
        "source_ziwei_birth": ZIWEI_BIRTH, "source_current_record": CURRENT
    }))
    assert result["facts"]["ziwei"]["algorithm_complete"] is True
    assert result["facts"]["ziwei"]["missing_fields"] == {}
    assert len(result["facts"]["ziwei"]["slots"]) == 12
    expected = [
        ("J017", "거문천동", "丑"), ("J018", "천량태양", "酉"), ("J019", "자미", "子"),
        ("J020", "태음", "巳"), ("J021", "태음", "巳"), ("J022", "태음", "巳"),
        ("J023", "천량태양", "卯"), ("J024", "칠살", "戌"), ("J025", "거문천동", "未"),
        ("J026", "천상무곡", "申"), ("J027", "파군", "寅"), ("J028", "탐랑", "午"),
        ("J029", "천기", "亥"), ("J030", "염정천부", "辰")
    ]
    assert [(row["table"], row["where"]["DB_express_1"], row["where"]["DB_express"]) for row in result["selectors"]] == expected
    assert all(row["columns"] == ["DB_data"] for row in result["selectors"])
    assert [value.split(":", 1)[0] for value in result["unresolved"]] == ["provided_source_records_unverified"]
    serialized = json.dumps(result["facts"], ensure_ascii=False)
    assert all(private not in serialized for private in ("19740302", "1974-03-02", "08:30", "variables", "lunar_year", "lunar_month", "lunar_day"))


def test_ziwei_default_preserves_available_hour_without_inventing_year_fields(birth):
    result = decide("interlife-jum-1", _request(birth))
    assert result["facts"]["source_hour_branch"] == "辰"
    assert result["selectors"] == []
    assert len(result["unresolved"]) == 1
    assert result["unresolved"][0].startswith("source_ziwei_birth_required:")


def test_source_record_dates_and_ziwei_conflicts_are_validated(birth):
    with pytest.raises(DomainError) as current:
        decide("interlife-jum-1", _request(birth, {"source_current_record": {**CURRENT, "no": "20261117"}}))
    assert current.value.code == "source_record_date_mismatch"
    with pytest.raises(DomainError) as conflict:
        decide("interlife-jum-1", _request(birth, {
            "source_birth_rows": ROWS, "source_ziwei_birth": {**ZIWEI_BIRTH, "year_h": "丙"}
        }))
    assert conflict.value.code == "source_record_conflict"


def test_ziwei_annual_input_requires_an_actual_selected_year(birth):
    with pytest.raises(DomainError) as caught:
        decide("interlife-jum-1", _request(birth, {
            "source_ziwei_birth": ZIWEI_BIRTH, "source_annual_record": {"umdate": "20261111", "umyear_e": "午"}
        }))
    assert caught.value.code == "invalid_service_parameters"


def test_display_does_not_require_unused_lunar_current_date_but_ziwei_does(birth):
    current = {key: value for key, value in CURRENT.items() if key != "umdate"}
    display = decide("interlife-free-11", _request(birth, {"source_current_record": current}))
    assert display["facts"]["display"]["algorithm_complete"] is True
    with pytest.raises(DomainError) as caught:
        decide("interlife-jum-1", _request(birth, {"source_current_record": current, "source_ziwei_birth": ZIWEI_BIRTH}))
    assert caught.value.code == "invalid_source_record"


def test_shared_source_globals_keep_independent_native_and_row_profiles(birth):
    result = build_source_globals(
        birth=birth, source_solunar=2, terms_by_year=bundled_source_terms(2029),
        source_birth_rows=ROWS, source_current_record=CURRENT, server_date=date(2026, 11, 18)
    )
    values = result["variables"]
    assert (values["daygan"], values["xdaygan"], values["yong_code"]) == ("壬", 9, "3")
    assert (values["my_day_h"], values["my_day_h_org"]) == ("壬", "I")
    assert result["missing_fields"] == {}
    assert result["f029_executed"] is False
    assert "i" not in values and "k" not in values
    assert "byear" not in values and "my_number" not in values
    assert result["dotong_substitution"] is False
    serialized = json.dumps(values, ensure_ascii=False)
    assert all(private not in serialized for private in ("19740302", "1974-03-02", "08:30", "source_birth_", "member_hour_min"))


def test_shared_source_globals_do_not_alias_raw_rows_into_missing_native_profile(birth):
    result = build_source_globals(birth=birth, source_birth_rows=ROWS, server_date=date(2026, 11, 18))
    assert result["variables"]["my_year_h"] == "甲"
    assert isinstance(result["variables"]["yeargan"], Missing)
    assert result["missing_fields"]["yeargan"] == ["native.source_solunar"]
    assert result["variables"]["sex_2"] == "1"


def test_shared_source_globals_preserve_actual_row_missing_despite_complete_native(birth):
    result = build_source_globals(birth=birth, source_solunar=2,
                                  terms_by_year=bundled_source_terms(2029), server_date=date(2026, 11, 18))
    assert result["variables"]["yeargan"] == "甲"
    assert isinstance(result["variables"]["my_year_h"], Missing)
    assert "source_birth_rows.selected.year_h" in result["missing_fields"]["my_year_h"]


def test_shared_native_globals_use_available_unambiguous_four_digit_source_terms():
    person = Birth(year=1903, month=3, day=2, hour=8, gender="male")
    result = build_source_globals(birth=person, source_solunar=2, server_date=date(2026, 11, 18))
    assert result["variables"]["yeargan"] == "癸"
    assert not isinstance(result["variables"]["daygan"], Missing)
    assert isinstance(result["variables"]["my_year_h"], Missing)


def test_shared_source_globals_need_binding_for_explicit_native_terms(birth):
    with pytest.raises(DomainError) as caught:
        build_source_globals(birth=birth, terms_by_year=bundled_source_terms(2029))
    assert caught.value.code == "source_calendar_binding_required"


def test_complete_display_and_ziwei_programs_have_no_unbound_hidden_callbacks():
    # Merely executing Missing-valued inputs can hide a call before lookup.
    # Inspect every frozen call regardless of branch reachability or arguments.
    def bindings(node, calls, assigned):
        if not isinstance(node, list):
            return
        if len(node) > 2 and node[0] == "call":
            calls.add(node[1])
        if len(node) > 2 and node[0] == "redim":
            assigned.add(node[2])
        if len(node) > 3 and node[0] == "set" and isinstance(node[3], list):
            expression = node[3]
            if len(expression) > 1 and expression[0] == "call" and expression[1] in {"split", "array"}:
                assigned.add(node[2])
        for child in node:
            bindings(child, calls, assigned)

    programs = [ziwei_rules()["program"], *display_rules()["programs"].values()]
    seen = set()
    for program in programs:
        calls, arrays = set(), set()
        bindings(program, calls, arrays)
        assert calls - arrays <= SUPPORTED_BUILTINS
        seen |= calls - arrays
    assert seen == {"int", "mid", "rs", "split", "len", "request", "array", "date", "replace", "year"}

"""Source-table and execution fixtures without opening original ASP files."""

import json
import random
from datetime import datetime
from pathlib import Path

import pytest

from app.ported_interlife_chart import SourceZiweiBirth, source_ziwei_placement
from app.ported_ziwei import (
    EMPTY,
    FunctionResult,
    Missing,
    SourceProcedure,
    SourceRecordset,
    _program,
    calculate_ziwei,
    compile_predicates,
    execute,
)
from app.rules import BRANCHES, GANJI
from tools.source_inventory import load_snapshot

BIRTH = {"year_h": "甲", "year_e": "寅", "lunar_year": 1974, "lunar_month": "02", "lunar_day": "09"}
CURRENT = {"no": "20261118", "umdate": "20261010", "umyear_e": "午"}


def test_frozen_predicates_keep_original_provenance_and_exact_internal_literals_without_asp():
    rules = _program()
    assert rules["source_sha256"] == load_snapshot()["files"][rules["source"]]["sha256"]
    assert rules["source_lines"] == 18144
    assert "<img" in json.dumps(rules, ensure_ascii=False)
    assert "@display" not in json.dumps(rules, ensure_ascii=False)
    assert "<%" not in json.dumps(rules, ensure_ascii=False)
    assert rules["annual_record_read_line"] == 9594
    assert not bool(EMPTY)


@pytest.mark.parametrize("number", list(range(0, 60, 3)))
def test_full_predicates_preserve_independently_frozen_initial_placement_tables(number):
    birth = SourceZiweiBirth(year_h=GANJI[number][0], year_e=GANJI[number][1], lunar_year=1900 + number,
                            lunar_month=f"{number % 12 + 1:02d}", lunar_day=f"{number % 30 + 1:02d}")
    hour = BRANCHES[number % 12]
    expected = source_ziwei_placement(birth, hour)
    actual = calculate_ziwei(birth=birth.model_dump(), hour_branch=hour, gender="male", current=CURRENT)
    assert actual["algorithm_complete"] is True
    variables = actual["variables"]
    assert variables["myung_guk"] == expected["myung_guk"]
    for name, star in expected["principal_stars"].items():
        placements = [position for position in range(1, 13) if variables.get(f"{name}_{position:02d}")]
        assert placements == [star["position"]]
        assert variables[f"{name}_{star['position']:02d}"] == star["label"]


def test_star_grading_four_transformations_and_auxiliaries_are_source_calculations():
    result = calculate_ziwei(birth=BIRTH, hour_branch="辰", gender="male", current=CURRENT)
    values = result["variables"]
    assert values["jami_my_11"] == "평"
    assert [values[name] for name in ("s_yeamjung_03", "s_pagun_01", "s_mugok_07", "s_taeyang_08")] == ["1", "2", "3", "4"]
    assert values["cheangue_12"] == "천괴" and values["cheanwol_06"] == "천월"
    assert values["jabo_04"] == "좌보" and values["upil_08"] == "우필"
    assert values["munchang_my_05"] == "함" and values["mungok_my_07"] == "평"
    assert values["yangum"] == "양남"
    # Source uses yangum in 博士 placement before assigning it at line 6287.
    assert not any(name.startswith("bosa_") for name in values)


def test_decadal_ranges_current_palace_and_source_faults_are_preserved():
    result = calculate_ziwei(birth=BIRTH, hour_branch="辰", gender="male", current=CURRENT)
    values = result["variables"]
    assert values["current_age"] == 53
    assert values["daehan_10"] == "6~15"
    assert values["daehan_02"] == "46~55"
    assert values["daehan_07"] == "96~"
    # Split returns soft strings; current_age is a soft numeric Variant. Original
    # VBScript orders every string above every number, so this range never hits.
    assert values.get("current_daehan") is None
    assert values["s4j_nokjon_05"] == " 녹존"  # Literal '' comparison coerces Boolean to text.
    assert result["source_errors"] == []
    assert result["missing_fields"] == {}


def test_selected_annual_record_uses_source_palace_stem_instead_of_solar_year_stem():
    result = calculate_ziwei(birth=BIRTH, hour_branch="辰", gender="male", current=CURRENT,
                             selected_year=2026, annual={"umdate": "20261111", "umyear_e": "午"})
    values = result["variables"]
    assert values["you_umyear_h"] == "庚"  # Natal palace 庚午, not current-year 丙午.
    assert values["you_umyear_e"] == "午"
    assert [values[name] for name in ("y_taeyang_08", "y_mugok_07", "y_taeum_04", "y_chendong_06")] == ["1", "2", "3", "4"]


def test_borrowing_and_final_order_use_original_sequential_assignments():
    result = calculate_ziwei(birth=BIRTH, hour_branch="辰", gender="male", current=CURRENT)
    leaves = result["final_leaves"]
    assert len(leaves) == 24
    assert leaves["result_myunggung"] == "亥"
    assert leaves["result_14jusung_myung"] == "천기"
    assert leaves["result_14jusung_bubu"] == leaves["result_14jusung_guanrok"] == "천량태양"
    assert leaves["result_14jusung_jaebaek"] == leaves["result_14jusung_bokduk"] == "거문천동"
    assert result["variables"]["mujung_bokduk"].startswith("본궁에 정성이 없어")
    assert all("@display" not in str(value) and ".gif" not in str(value) for value in result["variables"].values())
    assert "<img" not in json.dumps(result, ensure_ascii=False)
    assert "<font" not in json.dumps(result, ensure_ascii=False)


def test_missing_current_or_annual_record_propagates_without_fabricating_values():
    current_missing = calculate_ziwei(birth=BIRTH, hour_branch="辰", gender="male")
    assert current_missing["variables"]["current_age"] is None
    assert "current.umdate" in current_missing["missing_fields"]["current_age"]
    assert current_missing["final_leaves"]["result_14jusung_myung"] == "천기"
    annual_missing = calculate_ziwei(birth=BIRTH, hour_branch="辰", gender="male", current=CURRENT, selected_year=2026)
    assert annual_missing["variables"]["you_umyear_h"] is None
    assert "annual.umyear_e" in annual_missing["missing_fields"]["you_umyear_h"]


def test_if_colons_and_resume_next_keep_statement_order_and_previous_values():
    program = compile_predicates([(1, 'If 1 = 1 Then a=1 : b=2 Else a=9'),
                                  (2, 'x=7'), (3, 'x=Int("bad")'), (4, 'If a=1 Then'),
                                  (5, 'If b=2 Then x=x+1 Else x=0'), (6, 'End If')])
    result = execute(program, {}, on_error_resume_next=True)
    assert result["variables"] == {"a": 1, "b": 2, "x": 8}
    assert result["source_errors"] == [{"line": 3, "code": "ValueError"}]


def test_vb_empty_boolean_minus_one_bitwise_not_and_truncated_mod():
    result = execute(compile_predicates([(1, 'a=0'), (2, 'If missing Then a=99'),
        (3, 'b=Not missing'), (4, 'c=(1=1)+2'), (5, 'd=Not 1'), (6, 'e=1 And 2'),
        (7, 'f=-5 Mod 3'), (8, 'g=2 Or 4'), (9, 'h="x" & missing')]), {})
    assert result["variables"] == {"a": 0, "b": -1, "c": 1, "d": -2, "e": 0, "f": -2, "g": 6, "h": "x"}


def test_unknown_original_fields_taint_conditional_results_instead_of_false_defaults():
    result = execute(compile_predicates([(1, 'If raw > 0 Then star="자미" Else star="천부"')]),
                     {"raw": Missing(frozenset({"source.raw"}))})
    assert result["variables"]["star"] is None
    assert result["missing"]["star"] == ["source.raw"]


def test_no_asp_files_are_opened_when_running_frozen_calculation(monkeypatch):
    original = Path.open

    def guarded(path, *args, **kwargs):
        assert path.suffix.lower() != ".asp"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    assert calculate_ziwei(birth=BIRTH, hour_branch="辰", gender="male")["algorithm_complete"] is True


def test_vb_comparison_literal_rules_match_microsoft_engine_examples():
    # https://learn.microsoft.com/en-us/archive/blogs/ericlippert/typing-hard-can-trip-you-up
    program = compile_predicates([(1, 'a="1"'), (2, 'b=1'), (3, 'x1=("1"=1)'),
        (4, 'x2=("1"=b)'), (5, 'x3=(a=1)'), (6, 'x4=(a=b)'),
        (7, 's="True"'), (8, 't=True'), (9, 'y1=("True"=True)'),
        (10, 'y2=("True"=t)'), (11, 'y3=(s=True)'), (12, 'y4=(s=t)'),
        (13, 'z1=(True=-1)'), (14, 'z2=(True<False)'), (15, 'z3=(True=False)')])
    values = execute(program, {})["variables"]
    assert [values[f"x{i}"] for i in range(1, 5)] == [True, True, True, False]
    assert [values[f"y{i}"] for i in range(1, 5)] == [True, True, False, False]
    assert [values[f"z{i}"] for i in range(1, 4)] == [True, True, False]


def test_trusted_use_observer_preserves_source_literal_hardness_without_hardening_function_results():
    program = compile_predicates([(1, 'negative="-1"'), (2, 'number="1"'),
        (3, 'untracked=(negative=-1)'), (4, 'tracked=(negative=__use("calculation",-1))'),
        (5, 'Select Case 1'), (6, 'Case number : baseline=7'), (7, 'End Select'),
        (8, 'Select Case __use("calculation",1)'), (9, 'Case number : observed=7'),
        (10, 'End Select'), (11, 'expression_stays_soft=(number=__use("calculation",0+1))'),
        (12, 'function_stays_soft=(number=__use("calculation",actual_function()))'),
        (13, 'boolean="True"'), (14, 'boolean_stays_soft=(boolean=__use("calculation",True))')])
    result = execute(program, {}, functions={"__use": lambda _role, value: value, "actual_function": lambda: 1})
    values = result["variables"]
    assert values["untracked"] is values["tracked"] is True
    assert values["baseline"] == values["observed"] == 7
    assert values["expression_stays_soft"] is False and values["function_stays_soft"] is False
    assert values["boolean_stays_soft"] is False and result["source_errors"] == []


def test_select_case_keeps_selected_variable_soft_and_supports_inline_and_ranges():
    lines = [(1, 'selected=1'), (2, 'casevar="1"'), (3, 'Select Case selected'),
        (4, 'Case casevar : answer=9'), (5, 'Case "1" : answer=2'), (6, 'Case Else : answer=3'),
        (7, 'End Select'), (8, 'Select Case 5'), (9, 'Case 1 To 3 : span=1'),
        (10, 'Case Is > 4 : span=2'), (11, 'End Select'), (12, 'parts=Split("a,b",",")(1)')]
    values = execute(compile_predicates(lines), {})["variables"]
    assert values["answer"] == 2 and values["span"] == 2 and values["parts"] == "b"


def test_dim_inside_loop_declares_without_resetting_the_variable_each_iteration():
    values = execute(compile_predicates([(1, 'For i=1 To 3'), (2, 'Dim total'),
        (3, 'total=total+1'), (4, 'Next')]), {})["variables"]
    assert values["total"] == 3 and values["i"] == 4


def test_alias_operators_and_optional_inline_end_if_are_source_supported_syntax():
    values = execute(compile_predicates([(1, 'If 1 =< 2 Then a=1 Else a=2 End If'),
        (2, 'If 2 => 1 Then b=1 End If'), (3, 'If 1 >< 1 Then End If')]), {})["variables"]
    assert values == {"a": 1, "b": 1}


def test_vb_mod_and_integer_division_have_distinct_arithmetic_precedence():
    values = execute(compile_predicates([(1, 'a=9 Mod 4 * 2'), (2, 'b=9 \\ 2 * 2'),
        (3, 'c=-2*3+10'), (4, 'd=Not 1=1 And True')]), {})["variables"]
    assert values == {"a": 1, "b": 2, "c": 4, "d": False}


def test_vb_numeric_and_date_string_conversion_preserves_original_lookup_keys():
    values = execute(compile_predicates([(1, 'key=3/3 & "A"'), (2, 'zero=CStr(-0/1)'),
        (3, 'fraction=CStr(1/8)'), (4, 'scientific=Int("1e2")'),
        (5, 'today=Replace(Date(),"-","")'), (6, 'same="" & Date')]),
        {"__clock__": datetime(2026, 11, 18, 8, 30)})["variables"]
    assert values == {"key": "1A", "zero": "0", "fraction": "0.125", "scientific": 100,
                      "today": "20261118", "same": "2026-11-18"}


def test_vb_null_stays_distinct_from_empty_and_missing_in_supplied_database_rows():
    result = execute(compile_predicates([(1, 'a=rs("nullable")+1'),
        (2, 'b=(rs("nullable")=0)'), (3, 'If rs("nullable") Then wrong=1 Else right=1'),
        (4, 'c=rs("nullable") & "A"'), (5, 'd=Null And False'), (6, 'e=Null Or True'),
        (7, 'f=Not Null'), (8, 'g=unknown+1'), (9, 'h=rs("absent")+1')]),
        {"__rs__": {"nullable": None}, "__rs_source__": "typed.rows"})
    assert {k: result["variables"][k] for k in "abcf"} == {k: None for k in "abcf"} | {"c": "A"}
    assert result["variables"]["right"] == 1 and "wrong" not in result["variables"]
    assert result["variables"]["d"] is False and result["variables"]["e"] is True
    assert result["variables"]["g"] == 1
    assert result["missing"]["h"] == ["typed.rows.absent"]
    assert "a" not in result["missing"] and result["source_errors"] == []
    converted = execute(compile_predicates([(1, 'On Error Resume Next'), (2, 'a=3'),
        (3, 'a=CInt(Null)'), (4, 'b=CDate(Null)'), (5, 'c=CStr(Null)')]), {})
    assert converted["variables"] == {"a": 3}
    assert [error["line"] for error in converted["source_errors"]] == [3, 4, 5]


def test_source_procedure_preserves_global_state_default_byref_and_local_return_scope():
    callback = SourceProcedure(("a",), compile_predicates([(1, 'a=a+1'), (2, 'i=i+1'),
        (3, 'localtemp=99'), (4, 'If a<5 Then helper=a')]),
        local_names=frozenset({"localtemp"}), source_writes=("i",))
    result = execute(compile_predicates([(1, 'n=1'), (2, 'first=helper(n)'),
        (3, 'n=6'), (4, 'second=helper(n)'), (5, 'arr=Array(4)'),
        (6, 'third=helper(arr(0))'), (7, 'fourth=helper((n))'), (8, 'fifth=helper(2+1)')]),
        {"i": 0}, functions={"helper": callback})
    values = result["variables"]
    assert values["first"] == 2 and values["n"] == 7 and values["arr"] == [5]
    assert values["second"] is None and values["third"] is None  # Function return is Empty anew.
    assert values["fourth"] is None and values["fifth"] == 4 and values["i"] == 5
    assert "localtemp" not in values and "a" not in values and "helper" not in values
    assert result["source_errors"] == []


def test_callback_argument_writes_and_unknown_branch_taint_are_applied_to_caller_references():
    def helper(value):
        return FunctionResult(value=2, writes={"vvv": 3}, argument_writes={0: 7})

    result = execute(compile_predicates([(1, 'arr=Array(1)'), (2, 'x=helper(arr(0))'),
        (3, 'If raw Then Call helper(arr(0))'), (4, 'y=arr(0)')]),
        {"raw": Missing(frozenset({"source.condition"}))}, functions={"helper": helper},
        function_writes={"helper": ("vvv",)}, function_argument_writes={"helper": (0,)})
    assert result["variables"]["x"] == 2
    assert result["missing"]["vvv"] == result["missing"]["y"] == ["source.condition"]
    unknown_index = execute(compile_predicates([(1, 'arr=Array(1)'),
        (2, 'If raw Then Call helper(arr(index))'), (3, 'y=arr(0)')]),
        {"raw": Missing(frozenset({"source.condition"})), "index": Missing(frozenset({"source.index"}))},
        functions={"helper": helper}, function_argument_writes={"helper": (0,)})
    assert unknown_index["missing"]["y"] == ["source.condition", "source.index"]
    assert unknown_index["source_errors"] == []


def test_recordsets_require_explicit_order_transpose_getrows_and_preserve_cursor_state():
    rows = SourceRecordset([{"id": 10, "value": "A"}, {"id": 20, "value": None}],
                          columns=("id", "value"), source="provided", record_count=2)
    result = execute(compile_predicates([(1, 'before=rs.BOF Or rs.EOF'), (2, 'n=rs.RecordCount'),
        (3, 'first=rs("ID")'), (4, 'data=rs.GetRows'), (5, 'last=data(1,1)'),
        (6, 'ended=rs.EOF'), (7, 'Call rs.MoveFirst'), (8, 'reset=rs(0)'),
        (9, 'rs.Close')]), {"__rs__": rows})
    assert result["variables"] == {"before": False, "n": 2, "first": 10,
        "data": [[10, 20], ["A", None]], "last": None, "ended": True, "reset": 10}
    assert rows.closed and result["source_errors"] == []
    unknown = execute(compile_predicates([(1, 'data=rs.GetRows'), (2, 'count=other.RecordCount')]),
        {"__rs__": SourceRecordset([{"x": 1}], source="rows"),
         "other": SourceRecordset([], source="other")})
    assert unknown["missing"]["data"] == ["rows.ADO_field_order"]
    assert unknown["missing"]["count"] == ["other.ADO_record_count"]


def test_source_date_numeric_string_and_array_builtins_are_portable_and_locale_explicit():
    result = execute(compile_predicates([(1, 'nextmonth=DateAdd("m",1,CDate("2024-01-31"))'),
        (2, 'boundary=DateDiff("d","2024-01-31 23:59:59","2024-02-01")'),
        (3, 'week=Weekday("2026-11-22")'), (4, 'hours=Hour("2026-11-18 08:30")'),
        (5, 'minutes=Minute("2026-11-18 08:30")'), (6, 'n=UBound(Array("a","b"))'),
        (7, 'search=InStr(2,"aBaB","ab",1)'), (8, 'numeric=IsNumeric("1e2")'),
        (9, 'locale=CDate("01/02/26")'), (10, 'ansi=Chr(176)')]), {})
    values = result["variables"]
    assert values["nextmonth"] == "2024-02-29T00:00:00"
    assert {k: values[k] for k in ("boundary", "week", "hours", "minutes", "n", "search", "numeric")} == {
        "boundary": 1, "week": 1, "hours": 8, "minutes": 30, "n": 1, "search": 3, "numeric": True}
    assert result["missing"]["locale"] == ["VBScript.date_order"]
    assert result["missing"]["ansi"] == ["VBScript.ANSI_codepage"]
    assert result["source_errors"] == []


def test_erase_resets_dynamic_arrays_and_randomize_uses_request_local_generator():
    result = execute(compile_predicates([(1, 'a=Array(1)'), (2, 'Erase a'),
        (3, 'Randomize 7'), (4, 'x=Rnd'), (5, 'same=Rnd(0)'),
        (6, 'Randomize 7'), (7, 'again=Rnd()')]), {}, rng=random.Random(99))
    assert result["variables"] == {"a": None, "x": random.Random(7).random(),
        "same": random.Random(7).random(), "again": random.Random(7).random()}
    assert result["source_errors"] == []
    helper = SourceProcedure((), compile_predicates([(1, 'helper=Rnd')]))
    returned = execute(compile_predicates([(1, 'first=helper()'), (2, 'same=Rnd(0)')]), {},
        functions={"helper": helper}, rng=random.Random(7))
    assert returned["variables"] == {"first": random.Random(7).random(), "same": random.Random(7).random()}


def test_redim_preserve_retains_values_when_growing_and_truncates_when_shrinking():
    result = execute(compile_predicates([(1, 'ReDim a(1)'), (2, 'a(0)="first"'),
        (3, 'a(1)="second"'), (4, 'ReDim Preserve a(3)'), (5, 'grown=UBound(a)'),
        (6, 'a(3)="last"'), (7, 'ReDim Preserve a(0)'), (8, 'ReDim b(2)'),
        (9, 'b(0)="independent"')]), {}, retain_state=True)
    assert result["variables"]["a"] == ["first"] and result["variables"]["grown"] == 3
    assert result["variables"]["b"] == ["independent", None, None]
    assert result["source_errors"] == []


def test_for_next_increments_mutated_actual_control_and_captures_bounds_once():
    result = execute(compile_predicates([(1, 'bound=6'), (2, 'stepvalue=1'),
        (3, 'For i=1 To bound Step stepvalue'), (4, 'seen=seen & i'),
        (5, 'i=i+1'), (6, 'bound=0'), (7, 'stepvalue=9'), (8, 'Next')]), {})
    assert result["variables"]["seen"] == "135"
    assert result["variables"]["i"] == 7 and result["source_errors"] == []
    missing = execute(compile_predicates([(1, 'For i=1 To 5'), (2, 'seen=seen+1'),
        (3, 'i=raw'), (4, 'Next')]), {"raw": Missing(frozenset({"source.control"}))})
    assert missing["missing"]["i"] == missing["missing"]["seen"] == ["source.control"]
    assert missing["source_errors"] == []


def test_source_procedures_do_not_inherit_callers_resume_next_and_keep_prior_byref_writes():
    helper = SourceProcedure(("n",), compile_predicates([(10, 'n=n+1'), (11, 'global_value=3'),
        (12, 'bad=1/0'), (13, 'global_value=99'), (14, 'helper=7')]), source_writes=("global_value",))
    result = execute(compile_predicates([(1, 'On Error Resume Next'), (2, 'n=1'), (3, 'x=5'),
        (4, 'x=helper(n)'), (5, 'continued=1')]), {}, functions={"helper": helper}, on_error_resume_next=False)
    assert result["variables"] == {"n": 2, "x": 5, "global_value": 3, "continued": 1}
    assert result["source_errors"] == [{"line": 12, "code": "ZeroDivisionError"}]
    assert not result.get("aborted")


def test_procedure_local_on_error_resumes_then_goto_zero_disables_it():
    helper = SourceProcedure((), compile_predicates([(10, 'On Error Resume Next'),
        (11, 'bad=1/0'), (12, 'helper=7')]))
    result = execute(compile_predicates([(1, 'x=helper()'), (2, 'done=1')]), {},
        functions={"helper": helper}, on_error_resume_next=False)
    assert result["variables"] == {"x": 7, "done": 1}
    assert result["source_errors"] == [{"line": 11, "code": "ZeroDivisionError"}]
    disabled = execute(compile_predicates([(1, 'On Error Resume Next'), (2, 'bad=1/0'),
        (3, 'On Error GoTo 0'), (4, 'bad=1/0'), (5, 'should_not_run=1')]), {}, on_error_resume_next=False)
    assert "should_not_run" not in disabled["variables"] and disabled["aborted"] is True
    assert [error["line"] for error in disabled["source_errors"]] == [2, 4]


def test_known_procedure_runs_independent_calculations_even_with_missing_arguments():
    helper = SourceProcedure(("unused",), compile_predicates([(10, 'helper=3')]))
    result = execute(compile_predicates([(1, 'x=helper(raw)')]),
        {"raw": Missing(frozenset({"provided.field"}))}, functions={"helper": helper})
    assert result["variables"]["x"] == 3 and "x" not in result["missing"]
    assert result["source_errors"] == []


def test_trusted_callback_missing_observation_and_readonly_live_context_hooks():
    observations = []

    def observer(*args, source_context):
        observations.append((args, source_context["counter"]))

    def query(name, missing, *, source_context):
        with pytest.raises(TypeError):
            source_context["counter"] = 99
        with pytest.raises(TypeError):
            source_context["array_values"][0] = 99
        return FunctionResult(missing, {"out": source_context["counter"]})

    query.source_observer = observer
    query.source_accepts_missing = True
    query.source_context = True
    result = execute(compile_predicates([(1, 'counter=1'), (2, 'counter=counter+1'),
        (3, 'x=query("DB_table",raw)')]),
        {"raw": Missing(frozenset({"provided.field"})), "array_values": [1]}, functions={"query": query})
    assert result["variables"]["out"] == 2 and result["variables"]["counter"] == 2
    assert result["missing"]["x"] == ["provided.field"]
    assert observations[0][1] == 2 and isinstance(observations[0][0][1], Missing)
    assert result["source_errors"] == []
    query.source_context_keys = ("counter", "array_values")
    filtered = execute(compile_predicates([(1, 'x=query("DB_table",raw)')]),
        {"raw": Missing(frozenset({"provided.field"})), "counter": 4, "array_values": [1],
         "private_unused": "excluded"}, functions={"query": query})
    assert filtered["variables"]["out"] == 4 and filtered["source_errors"] == []


def test_exit_for_accepts_large_initial_distance_but_only_runs_until_source_exit():
    result = execute(compile_predicates([(1, 'For i=27000 To 1 Step -1'),
        (2, 'count=count+1'), (3, 'If count=3 Then Exit For'), (4, 'Next'),
        (5, 'after=1')]), {})
    assert result["variables"] == {"i": 26998, "count": 3, "after": 1}
    assert result["source_errors"] == []
    helper = SourceProcedure((), compile_predicates([(10, 'helper=2'),
        (11, 'Exit Function'), (12, 'helper=99')]))
    exited = execute(compile_predicates([(1, 'x=helper()')]), {}, functions={"helper": helper})
    assert exited["variables"] == {"x": 2}


def test_unknown_exit_for_stays_inside_its_loop_and_independent_later_work_continues():
    result = execute(compile_predicates([(1, 'For i=raw To 1 Step -1'),
        (2, 'loopvalue=3'), (3, 'If raw Then Exit For'), (4, 'Next'),
        (5, 'independent=7')]), {"raw": Missing(frozenset({"source.bound"}))}, retain_state=True)
    assert result["variables"]["independent"] == 7
    assert result["missing"]["loopvalue"] == ["source.bound"]
    assert "__pending_exit__" not in result["state"] and result["source_errors"] == []
    conditional = execute(compile_predicates([(1, 'If raw Then'), (2, 'For i=1 To 3'),
        (3, 'loopvalue=3'), (4, 'Exit For'), (5, 'Next'), (6, 'End If'),
        (7, 'independent=7')]), {"raw": Missing(frozenset({"source.condition"}))}, retain_state=True)
    assert conditional["variables"]["independent"] == 7
    assert "__pending_exit__" not in conditional["state"] and conditional["source_errors"] == []


def test_source_halt_stops_entire_call_chain_without_assigning_an_unreturned_value():
    def halt():
        return FunctionResult(EMPTY, {"__source_halted__": True})

    helper = SourceProcedure((), compile_predicates([(10, 'flag=3'), (11, 'Call halt()'),
        (12, 'flag=99'), (13, 'helper=8')]), source_writes=("flag",))
    result = execute(compile_predicates([(1, 'x=5'), (2, 'x=helper()'),
        (3, 'should_not_run=1')]), {}, functions={"helper": helper, "halt": halt}, retain_state=True)
    assert result["variables"] == {"x": 5, "flag": 3}
    assert result["state"]["__source_halted__"] is True and result["source_errors"] == []


def test_source_time_and_datepart_use_explicit_server_clock_without_inventing_time():
    program = compile_predicates([(1, 'h=Hour(Time)'), (2, 'm=Minute(Time())'),
        (3, 'weekday=DatePart("w",Date)'), (4, 'dayofyear=DatePart("y",Date())')])
    result = execute(program, {"__clock__": datetime(2026, 11, 18, 8, 30)})
    assert result["variables"] == {"h": 8, "m": 30, "weekday": 4, "dayofyear": 322}
    date_only = execute(program, {"__clock__": datetime(2026, 11, 18).date()})
    assert date_only["missing"]["h"] == date_only["missing"]["m"] == ["source_clock.time"]


def test_multidimensional_assignment_and_inline_elseif_keep_source_control_flow():
    result = execute(compile_predicates([(1, 'PO(0,1)=7'), (2, 'hour_var="00"'),
        (3, 'If hour_var="01" Then'), (4, 'time_str="one"'),
        (5, 'ElseIf hour_var="00" Then time_str="zero"'), (6, 'Else'),
        (7, 'time_str="other"'), (8, 'End If'), (9, 'answer=PO(0,1)')]),
        {"po": [[EMPTY, EMPTY], [EMPTY, EMPTY]]})
    assert result["variables"]["po"] == [[None, 7], [None, None]]
    assert result["variables"]["time_str"] == "zero" and result["variables"]["answer"] == 7
    assert result["source_errors"] == []

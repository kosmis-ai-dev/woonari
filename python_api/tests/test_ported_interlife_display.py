"""Portable full F029/source-row display fixtures and original loop quirks."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from app.errors import DomainError
from app.ported_interlife_display import (
    SourceBirthRows,
    _rules,
    process_display,
    process_source_profile,
)
from app.ported_ziwei import EMPTY, compile_predicates, execute
from tools.source_inventory import load_snapshot

BIRTH = datetime.fromisoformat("1974-03-02T08:30+09:00")
ROWS = {"birth": {"no": "19740302", "number": 27000, "day_h": "I", "day_e": "01", "jeolip": ""},
        "selected": {"number": 27000, "year_h": "A", "year_e": "01", "month_h": "C", "month_e": "01"}}
CURRENT = {"no": "20261118", "umyear_h": "丙", "umyear_e": "午"}


def test_full_frozen_program_has_source_provenance_and_separates_invalid_source_comments():
    rules = _rules()
    inventory = load_snapshot()["files"]
    for path, metadata in rules["sources"].items():
        assert metadata["sha256"] == inventory[path]["sha256"]
    assert [entry["line"] for entry in rules["anomalies"]] == [3919, 4170]
    assert all(entry["code"] == "non_vb_comment_syntax" for entry in rules["anomalies"])
    assert "<img" in json.dumps(rules, ensure_ascii=False)  # Internal literal semantics stay exact.
    assert "@display" not in json.dumps(rules, ensure_ascii=False)
    assert len(rules["display_names"]) == 82


def test_raw_calendar_rows_are_transformed_by_original_code_not_native_saju():
    result = process_display(birth_datetime=BIRTH, source_birth_rows=ROWS, source_current_record=CURRENT)
    values = result["variables"]
    assert {name: values[name] for name in ("my_year_h", "my_year_e", "my_month_h", "my_month_e", "my_day_h", "my_day_e", "my_hour_h", "my_hour_e")} == {
        "my_year_h": "甲", "my_year_e": "寅", "my_month_h": "丙", "my_month_e": "寅",
        "my_day_h": "壬", "my_day_e": "寅", "my_hour_h": "甲", "my_hour_e": "辰",
    }
    assert result["algorithm_complete"] is True
    assert result["native_profile_substituted_for_original_rows"] is False
    assert result["source_errors"] == []
    assert result["source_pillars"]["year"] == {"h": "甲", "e": "寅", "h_org": "A", "e_org": "01"}
    assert result["hidden_stems"]["year"] == {"stem1": "무", "stem2": "병", "stem3": "갑"}
    assert values["i"] == 119 and values["j"] == 11 and values["k"] == 97
    assert result["display_fields"]["td_y1"] == 2024
    assert result["display_fields"]["td_y10"] == 2033
    assert result["display_fields"]["td_unsung1"] == "관대"
    assert result["display_fields"]["td_unsung10"] == "양"


def test_unassigned_outer_ages_are_preserved_as_source_input_defects():
    result = process_display(birth_datetime=BIRTH, source_birth_rows=ROWS, source_current_record=CURRENT)
    assert set(result["unassigned_source_inputs"]) == {"my_age", *(f"daeun{i}_no" for i in range(1, 11))}
    assert result["display_fields"]["td1_my_age"] == -2  # Original unassigned my_age=Empty.
    assert result["display_fields"]["td10_my_age"] == 7
    provided = process_display(birth_datetime=BIRTH, source_birth_rows=ROWS, source_current_record=CURRENT,
        native_result={"my_age": 53, **{f"daeun{i}_no": 6 + 10 * (i - 1) for i in range(1, 11)}})
    assert provided["unassigned_source_inputs"] == []
    assert provided["display_fields"]["td1_my_age"] == 51
    assert provided["display_fields"]["td10_my_age"] == 60


@pytest.mark.parametrize("minute,number", [(19, 26999), (20, 27000)])
def test_original_february_cutoff_uses_supplied_previous_number_not_idx_or_date_arithmetic(minute, number):
    value = datetime.fromisoformat(f"2026-02-04T04:{minute}+09:00")
    rows = {"birth": {"no": "20260204", "number": 27000, "day_h": "I", "day_e": "01", "jeolip": "0420"},
            "selected": {**ROWS["selected"], "number": number}}
    result = process_display(birth_datetime=value, source_birth_rows=rows, source_current_record=CURRENT)
    assert result["variables"]["my_number"] == number
    rows["selected"]["number"] = number + 1
    with pytest.raises(DomainError) as caught:
        process_display(birth_datetime=value, source_birth_rows=rows, source_current_record=CURRENT)
    assert caught.value.code == "invalid_source_record"


def test_loop_ends_missing_last_match_and_stale_k_follow_original_vb():
    source = [(1, 'ReDim values(2)'), (2, 'values(0)="A"'), (3, 'values(1)="B"'), (4, 'values(2)="C"'),
              (5, 'k=1'), (6, 'For i=0 To 1'), (7, 'If values(i)="C" Then k=i'), (8, 'Next'),
              (9, 'answer=values(k)')]
    result = execute(compile_predicates(source), {}, retain_state=True)
    assert result["variables"]["i"] == 2
    assert result["variables"]["k"] == 1
    assert result["variables"]["answer"] == "B"
    assert result["state"]["values"] == ["A", "B", "C"]
    redim = execute(compile_predicates([(1, 'ReDim x(2)')]), {}, retain_state=True)
    assert redim["variables"]["x"] == [None, None, None]
    assert redim["state"]["x"] == [EMPTY] * 3


def test_missing_actual_source_rows_propagate_as_missing_not_algorithm_unimplemented():
    result = process_display(birth_datetime=BIRTH)
    assert result["algorithm_complete"] is True
    assert result["variables"]["my_day_h"] is None
    assert result["missing_fields"]
    assert result["source_pillars"]["year"]["h"] is None
    assert "source_birth_rows.selected.year_h" in result["missing_fields"]["my_year_h"]
    assert result["source_errors"] == []
    partial_current = process_display(birth_datetime=BIRTH, source_birth_rows=ROWS,
                                     source_current_record={"no": "20261118", "umyear_e": "午"})
    assert "source_current_record.umyear_h" in partial_current["missing_fields"]["umyear_h"]


def test_raw_birth_timestamp_names_and_arbitrary_native_fields_never_enter_outputs():
    result = process_display(birth_datetime=BIRTH, source_birth_rows=ROWS, source_current_record=CURRENT,
                             native_result={"user_name": "PRIVATE-NAME", "birth_datetime": BIRTH.isoformat(), "unused": "PRIVATE-FIELD"})
    encoded = json.dumps(result, ensure_ascii=False)
    assert all(value not in encoded for value in ("PRIVATE-NAME", "PRIVATE-FIELD", BIRTH.isoformat(), "19740302"))


@pytest.mark.parametrize("rows", [
    {**ROWS, "birth": {**ROWS["birth"], "day_h": "壬"}},
    {**ROWS, "birth": {**ROWS["birth"], "number": True}},
    {**ROWS, "birth": {**ROWS["birth"], "jeolip": "2460"}},
    {**ROWS, "birth": {**ROWS["birth"], "no": "19740303"}},
])
def test_invalid_original_rows_are_422_errors(rows):
    with pytest.raises(DomainError) as caught:
        process_display(birth_datetime=BIRTH, source_birth_rows=rows)
    assert caught.value.status == 422


def test_no_asp_files_are_opened_and_typed_rows_are_accepted(monkeypatch):
    original = Path.open

    def guarded(path, *args, **kwargs):
        assert path.suffix.lower() != ".asp"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    assert process_display(birth_datetime=BIRTH, source_birth_rows=SourceBirthRows(**ROWS))["algorithm_complete"] is True


def test_internal_source_profile_keeps_original_native_types_without_running_f029():
    result = process_source_profile(birth_datetime=BIRTH, source_birth_rows=ROWS,
                                    source_current_record=CURRENT, native_result={"i": 7, "k": 8})
    assert result["state"]["my_year_h"] == "甲"
    assert result["state"]["i"] == 7 and result["state"]["k"] == 8
    assert "td_y1" not in result["state"]
    assert "source_birth_day_h" in result["state"]  # Internal only; caller must filter.


def test_semantic_element_markup_is_kept_for_original_later_classification_but_never_public():
    profile = process_source_profile(birth_datetime=BIRTH, source_birth_rows=ROWS)
    assert profile["state"]["my_oheng_day_h"] == "<font color=red><b>+</b></font>수"
    # G004/G005/G006/G007:6-21 strip the original tags before selecting 五行.
    original_selection = compile_predicates([(6, 'element=Replace(my_oheng_day_h,"<font color=blue>","")'),
        (7, 'element=Replace(element,"<font color=red>","")'), (8, 'element=Replace(element,"<b>-</b>","")'),
        (9, 'element=Replace(element,"<b>+</b>","")'), (10, 'element=Replace(element,"</font>","")'),
        (12, 'Select Case element'), (13, 'Case "목" : serial=1'), (14, 'Case "화" : serial=2'),
        (15, 'Case "토" : serial=3'), (16, 'Case "금" : serial=4'), (17, 'Case "수" : serial=5'),
        (18, 'Case Else : serial=1'), (19, 'End Select'), (21, 'serial=serial*16')])
    result = execute(original_selection, profile["state"])
    assert result["variables"]["element"] == "수" and result["variables"]["serial"] == 80
    public = process_display(birth_datetime=BIRTH, source_birth_rows=ROWS)
    assert not any(name.startswith("my_oheng_") for name in public["variables"])
    assert "<font" not in json.dumps(public, ensure_ascii=False)
    assert "<img" not in json.dumps(public, ensure_ascii=False)

import json
from pathlib import Path

import pytest

from tools.extract_rule_fixture import parse_vb_string_array


def test_vb_doubled_quote_is_one_string_not_two_array_cells():
    assert parse_vb_string_array('"편인","인수""비견","겁재"') == ["편인", '인수"비견', "겁재"]


def test_vb_empty_strings_and_whitespace():
    assert parse_vb_string_array(' "", "a" , "b""c" ') == ["", "a", 'b"c']


def test_vb_line_continuation_is_static_not_code_execution():
    assert parse_vb_string_array('"a", _\n "b"') == ["a", "b"]


@pytest.mark.parametrize(
    "expression", ['"a" & "b"', '"a", code()', '"a",', "unterminated", '"a" "b"']
)
def test_unsupported_or_invalid_expressions_are_rejected(expression):
    with pytest.raises(ValueError):
        parse_vb_string_array(expression)


def test_source_snapshot_preserves_the_observable_sin_chen_literal():
    snapshot = json.loads((Path(__file__).parent / "fixtures" / "legacy_ten_gods.json").read_text())
    assert snapshot["branches"]["辛"]["辰"] == '인수"비견'
    assert snapshot["branches"]["辛"]["丑"] == "편인"
    assert snapshot["stems"]["辛"]["戊"] == "인수"
    assert (
        sum(len(mapping) for group in ("stems", "branches") for mapping in snapshot[group].values())
        == 220
    )

"""T-024: independent known-row fixtures for source helpers and their caller.

Only source-derived Python data is opened. Synthetic rows exercise post-query
formatting, numeric selection and default ByRef changes without a database.
"""

import re
from pathlib import Path

import pytest

from app.ported_interlife_leaves import _data, _program
from app.ported_ziwei import (
    EMPTY,
    FunctionResult,
    SourceProcedure,
    SourceRecordset,
    compile_predicates,
    execute,
)
from tools.source_inventory import load_snapshot


@pytest.fixture(autouse=True)
def no_original_source_reads(monkeypatch):
    original = Path.open

    def guarded(path, *args, **kwargs):
        assert path.suffix.lower() not in {".asp", ".dat"}
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)


def _fixture(name):
    data = _data()
    candidates = [(identifier, procedure) for identifier, procedure in data["procedures"].items()
                  if procedure["name"] == name]
    assert len(candidates) == 1
    identifier, definition = candidates[0]
    route = next(route for service in data["services"].values() for route in service["routes"]
                 if route.get("bindings", {}).get(name) == identifier)
    source = definition["source"]
    assert data["sources"][source]["sha256"] == load_snapshot()["files"][source]["sha256"]
    globals_ = set(route["globals"]) | {"__rs__", "__rs_source__"}
    locals_ = set(definition.get("explicit_locals", ())) | (set(definition["assigned"]) - globals_)
    writes = tuple(set(definition["assigned"]) - locals_ - set(definition["arguments"]) - {name})
    procedure = SourceProcedure(tuple(definition["arguments"]), _program(data, definition),
                                frozenset(locals_), frozenset(definition["by_value"]), writes)
    queries = []

    def query(query_id, sql):
        recordset = SourceRecordset([{"DB_data": "FIRST\nSECOND", "DB_numerical": 37}],
                                   columns=("DB_data", "DB_numerical"), record_count=1,
                                   source=query_id)
        queries.append((sql, recordset))
        return FunctionResult(EMPTY, {"__rs__": recordset, "__rs_source__": query_id})

    query.source_writes = ("__rs__", "__rs_source__")
    functions = {name: procedure, "__query": query, "__use": lambda _role, value: value,
                 "__connect": lambda: EMPTY, "__disconnect": lambda: EMPTY}
    environment = {key: EMPTY for key in set(definition["assigned"]) & globals_}
    environment.update({"__rs__": EMPTY, "__rs_source__": "synthetic_known_row"})
    return data, route, functions, environment, queries


def _selected_code(sql, column="DB_express"):
    match = re.search(rf"\b{column}\s*=\s*['\"]?(\d+)", sql, re.I)
    assert match
    return int(match[1])


@pytest.mark.parametrize("input_code,expected_code", [(0, 1), (24, 1), (26, 2)])
def test_original_dang_helper_normalizes_byref_then_reads_and_formats_the_known_row(input_code, expected_code):
    _, _, functions, environment, queries = _fixture("f_dang4_6_db")
    environment["code"] = input_code
    result = execute(compile_predicates([(1, 'result=f_dang4_6_db("S007",code)')]),
                     environment, functions=functions)
    # Original rules: 0->1; values above 12 use Mod 12, with zero->1.
    assert result["variables"]["code"] == expected_code
    assert len(queries) == 1 and _selected_code(queries[0][0]) == expected_code
    returned = result["variables"]["result"]
    assert returned == "FIRST<BR>SECOND|37"
    assert "\n" not in returned and queries[0][1].closed is True
    assert result["source_errors"] == []


@pytest.mark.parametrize("table,expected_code", [("S008", 1), ("S009", 10)])
def test_original_woonday_helper_uses_table_specific_modulus_and_returns_both_row_fields(table, expected_code):
    _, _, functions, environment, queries = _fixture("f_woonday")
    environment.update({"code": "8.9", "xyeargi": 2, "table": table})
    result = execute(compile_predicates([(1, 'result=f_woonday(table,code)')]),
                     environment, functions=functions)
    # Int(8.9)+2=10; S008 uses Mod 10 then 0->1, other tables Mod 12.
    assert result["variables"]["code"] == expected_code
    assert len(queries) == 1 and _selected_code(queries[0][0], "DB_num") == expected_code
    assert re.search(rf"\bfrom\s+{table}\b", queries[0][0], re.I)
    returned = result["variables"]["result"]
    assert returned == "FIRST\nSECOND|37"
    assert queries[0][1].closed is True and result["source_errors"] == []


@pytest.mark.parametrize("year_branch,expected_image_code", [(10, "1"), (2, "2")])
def test_actual_s008_caller_splits_numeric_field_and_consumes_mutated_image_classification(year_branch, expected_image_code):
    data, route, functions, environment, queries = _fixture("f_woonday")
    source = "old/unse/interlife/UNSE_DATA/solve/S/S008.asp"
    assert data["sources"][source]["sha256"] == load_snapshot()["files"][source]["sha256"]
    # This is the frozen original caller, not a rewritten equivalent fixture.
    route = data["services"]["interlife-saju-17"]["routes"][0]
    caller = [node for node in _program(data, route)
              if data["locations"].get(str(node[1]), {}).get("path") == source]
    assert caller
    environment.update({"xdaygan": 7, "xtodaygan": 3, "xyeargi": year_branch})
    result = execute(caller, environment, functions=functions)
    values = result["variables"]
    # Caller P=(7+3) Mod 10 -> 10; helper mutates P using this year's branch.
    # The caller then splits both DB fields and uses the changed P for its image.
    assert values["p"] == int(expected_image_code)
    assert values["tb_s008"] == "FIRST\nSECOND"
    assert values["tb_s008_numerical"] == "37"
    assert values["s008_img_var"] == expected_image_code
    assert len(queries) == 1 and _selected_code(queries[0][0], "DB_num") == int(expected_image_code)
    assert result["source_errors"] == []

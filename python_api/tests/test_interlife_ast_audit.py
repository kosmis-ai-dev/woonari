"""T-024: portable static coverage audit, including unreachable source branches.

Only the frozen Python data artifact is read. Missing-valued arguments cannot
hide unsupported callbacks, operators or statements from this inspection.
Array types require an actual construction/declaration, alias or typed return;
assigning a scalar to an identifier never makes calls to that name valid.
"""

from __future__ import annotations

import json

from app.ported_ziwei import (
    SUPPORTED_BINARY_OPERATORS,
    SUPPORTED_BUILTINS,
    SUPPORTED_EXPRESSIONS,
    SUPPORTED_RECORDSET_MEMBERS,
    SUPPORTED_STATEMENTS,
    SUPPORTED_UNARY_OPERATORS,
    compile_predicates,
)

RUNTIME_CALLBACKS = frozenset({
    "__connect", "__disconnect", "__query", "__emit", "__halt", "__dim_array",
    "__native_calendar_constants", "__presentation_path", "__use", "__phase", "cookie", "server_variable", "dive",
    "b_saju_click", "f_pre_div24", "f_next_div24", "fi_pre_div24",
})
NATIVE_ARRAY_RETURNS = {"b_saju_click": 1}
CALLBACK_ARRAY_WRITES = {"__native_calendar_constants": {"sixty": 1, "chungan": 1, "gigi": 1}}
SOURCE_FAULT_PATH = "old/unse/interlife/UNSE_DATA/solve/saju_made.asp"
SOURCE_FAULT_SHA256 = "4f17c338728760dc7abb77474fa0ccb73f5b3291ee55817b9cb26838e41fd7c4"


def _program(data, scope):
    if data.get("schema_version", 1) >= 3:
        from app.ported_interlife_leaves import _program as expand_program

        return expand_program(data, scope)
    if "program_refs" in scope:
        return [data["nodes"][reference] for reference in scope["program_refs"]]
    return scope["program"]


def _scan(program):
    """Inspect AST syntax without evaluating any source literal or expression."""
    info = {"calls": [], "sets": [], "array_seeds": {}, "assigned": set(), "errors": []}

    def issue(code, name, line):
        info["errors"].append({"code": code, "name": str(name), "line": line})

    def expression(node, line):
        if not isinstance(node, list) or not node or not isinstance(node[0], str):
            issue("malformed_expression", "AST", line)
            return
        kind = node[0]
        if kind not in SUPPORTED_EXPRESSIONS:
            issue("unsupported_expression", kind, line)
            return
        if kind in {"literal", "value", "variable"}:
            return
        if kind == "group":
            expression(node[1], line)
        elif kind == "unary":
            if node[1] not in SUPPORTED_UNARY_OPERATORS:
                issue("unsupported_unary_operator", node[1], line)
            expression(node[2], line)
        elif kind == "binary":
            if node[1] not in SUPPORTED_BINARY_OPERATORS:
                issue("unsupported_binary_operator", node[1], line)
            expression(node[2], line)
            expression(node[3], line)
        elif kind == "call":
            if not isinstance(node[1], str):
                issue("malformed_expression_call", node[1], line)
                return
            info["calls"].append((node[1], node[2], line))
            for name, depth in CALLBACK_ARRAY_WRITES.get(node[1], {}).items():
                info["array_seeds"][name] = depth
            for argument in node[2]:
                expression(argument, line)
            if node[1] == "__dim_array" and node[2] and node[2][0][0] == "literal":
                name = node[2][0][1]
                info["array_seeds"][name] = max(1, len(node[2]) - 1)
                info["assigned"].add(name)
        elif kind == "index":
            expression(node[1], line)
            for index in node[2]:
                expression(index, line)
        elif kind == "member":
            if node[2] not in SUPPORTED_RECORDSET_MEMBERS:
                issue("unsupported_member", node[2], line)
            expression(node[1], line)
            for argument in node[3]:
                expression(argument, line)

    def statements(nodes):
        for node in nodes:
            if not isinstance(node, list) or len(node) < 2 or not isinstance(node[0], str):
                issue("malformed_statement", "AST", None)
                continue
            kind, line = node[:2]
            if kind not in SUPPORTED_STATEMENTS:
                issue("unsupported_statement", kind, line)
                continue
            if kind == "set":
                info["sets"].append(node)
                info["assigned"].add(node[2])
                expression(node[3], line)
                if node[4] is not None:
                    expression(node[4], line)
            elif kind in {"dim", "erase"}:
                info["assigned"].add(node[2])
            elif kind == "redim":
                info["array_seeds"][node[2]] = 1
                info["assigned"].add(node[2])
                expression(node[3], line)
            elif kind == "if":
                expression(node[2], line)
                statements(node[3])
                statements(node[4])
            elif kind == "for":
                info["assigned"].add(node[2])
                for value in node[3:6]:
                    expression(value, line)
                statements(node[6])
            elif kind == "call":
                # Statement call has integer line; expression call has a name.
                expression(node[2], line)
            elif kind == "randomize":
                if node[2] is not None:
                    expression(node[2], line)
            elif kind == "select_case":
                expression(node[2], line)
                for tests, body in node[3]:
                    for test in tests:
                        if test[0] == "compare":
                            if test[1] not in {"=", "<>", "<", ">", "<=", ">="}:
                                issue("unsupported_case_operator", test[1], line)
                            expression(test[2], line)
                        elif test[0] == "equal":
                            expression(test[1], line)
                        elif test[0] == "range":
                            expression(test[1], line)
                            expression(test[2], line)
                        else:
                            issue("unsupported_case_test", test[0], line)
                    statements(body)
                statements(node[4])
            elif kind == "exit" and node[2] not in {"for", "function", "sub"}:
                issue("unsupported_exit", node[2], line)
            elif kind == "on_error" and type(node[2]) is not bool:
                issue("unsupported_error_policy", "AST", line)
            # `select` is a static record descriptor, not executable SQL.

    statements(program)
    return info


def audit_route(data, route):
    """Resolve all transitive calls under this route's actual procedure binding."""
    bindings = route.get("bindings", {})
    scopes = {"@route": {**route, "name": "@route", "arguments": [], "by_value": []}}
    pending = ["@route"]
    scans, errors = {}, []
    while pending:
        identifier = pending.pop()
        if identifier in scans:
            continue
        scope = scopes[identifier]
        scans[identifier] = _scan(_program(data, scope))
        for name, _, line in scans[identifier]["calls"]:
            if name in bindings:
                target = bindings[name]
                if target not in data["procedures"]:
                    errors.append({"scope": identifier, "line": line, "name": name, "code": "missing_procedure_binding"})
                else:
                    scopes[target] = data["procedures"][target]
                    pending.append(target)

    for name, identifier in bindings.items():
        if identifier not in scopes:
            continue
        procedure = scopes[identifier]
        if procedure["name"] != name:
            errors.append({"scope": identifier, "line": None, "name": name, "code": "procedure_name_mismatch"})
        if "source" in procedure and "includes" in route and procedure["source"] not in route["includes"]:
            errors.append({"scope": identifier, "line": None, "name": name, "code": "procedure_outside_active_includes"})
        arguments = procedure.get("arguments", ())
        if len(set(arguments)) != len(arguments) or any(type(index) is not int or not 0 <= index < len(arguments) for index in procedure.get("by_value", ())):
            errors.append({"scope": identifier, "line": None, "name": name, "code": "procedure_scope_metadata"})

    global_names = set(route.get("globals", scans["@route"]["assigned"]))
    for name, _, _ in scans["@route"]["calls"]:
        global_names.update(CALLBACK_ARRAY_WRITES.get(name, ()))
    local_names = {key: set(scope.get("explicit_locals", ())) | set(scope.get("arguments", ())) |
                  {scope["name"]} | (scans[key]["assigned"] - global_names) if key != "@route" else set()
                  for key, scope in scopes.items()}
    ranks = {key: dict(scan["array_seeds"]) for key, scan in scans.items()}
    globals_rank = {}

    def raise_rank(scope_id, name, rank):
        if rank <= ranks[scope_id].get(name, 0):
            return False
        ranks[scope_id][name] = rank
        return True

    def rank(node, scope_id):
        kind = node[0]
        if kind == "variable":
            return ranks[scope_id].get(node[1], 0)
        if kind == "group":
            return rank(node[1], scope_id)
        if kind == "member" and node[2] == "getrows":
            return 2
        if kind == "call":
            name = node[1]
            if name == "__use" and len(node[2]) == 2:
                return rank(node[2][1], scope_id)  # Verified observer returns this value unchanged.
            if name in {"array", "split"}:
                return 1
            if name in NATIVE_ARRAY_RETURNS:
                return NATIVE_ARRAY_RETURNS[name]
            if name in bindings and bindings[name] in ranks:
                return ranks[bindings[name]].get(scopes[bindings[name]]["name"], 0)
            return max(0, ranks[scope_id].get(name, 0) - len(node[2]))
        if kind == "index":
            return max(0, rank(node[1], scope_id) - len(node[2]))
        return 0

    changed = True
    while changed:
        changed = False
        for key, scan in scans.items():
            for name, depth in globals_rank.items():
                if name not in local_names[key]:
                    changed |= raise_rank(key, name, depth)
            for node in scan["sets"]:
                if node[4] is None:
                    changed |= raise_rank(key, node[2], rank(node[3], key))
            for name, depth in list(ranks[key].items()):
                if name in global_names and name not in local_names[key] and depth > globals_rank.get(name, 0):
                    globals_rank[name] = depth
                    changed = True
            for name, arguments, _ in scan["calls"]:
                target = bindings.get(name)
                if target not in scopes:
                    continue
                procedure = scopes[target]
                for index, (parameter, argument) in enumerate(zip(procedure.get("arguments", ()), arguments)):
                    changed |= raise_rank(target, parameter, rank(argument, key))
                    if index not in procedure.get("by_value", ()) and argument[0] == "variable":
                        changed |= raise_rank(key, argument[1], ranks[target].get(parameter, 0))

    unknown = []
    for key, scan in scans.items():
        errors.extend({"scope": key, **error} for error in scan["errors"])
        for name, arguments, line in scan["calls"]:
            if name not in SUPPORTED_BUILTINS | RUNTIME_CALLBACKS and name not in bindings and ranks[key].get(name, 0) == 0:
                unknown.append({"scope": key, "line": line, "name": name, "code": "unbound_call_or_unproven_array"})
            target = bindings.get(name)
            if target in scopes and len(arguments) != len(scopes[target].get("arguments", ())):
                errors.append({"scope": key, "line": line, "name": name, "code": "procedure_argument_count"})
    return {"unknown_calls": unknown, "unsupported": errors, "scopes": sorted(scans),
            "arrays": {key: sorted(values) for key, values in ranks.items()}}


def audit_artifact(data):
    report = {"unknown_calls": [], "unsupported": [], "source_faults": [], "routes": 0, "procedures": set()}
    for service_id, service in data["services"].items():
        for route in service["routes"]:
            result = audit_route(data, route)
            report["routes"] += 1
            report["procedures"].update(set(result["scopes"]) - {"@route"})
            for field in ("unknown_calls", "unsupported"):
                for issue in result[field]:
                    location = data.get("locations", {}).get(str(issue["line"]), {})
                    known_fault = (field == "unknown_calls" and issue["name"] == "buf" and
                                   location.get("path") == SOURCE_FAULT_PATH and location.get("line") in {334, 335, 336} and
                                   data.get("sources", {}).get(SOURCE_FAULT_PATH, {}).get("sha256") == SOURCE_FAULT_SHA256)
                    output = "source_faults" if known_fault else field
                    report[output].append({"service_id": service_id, "route": route.get("source"), **issue})
    report["procedures"] = sorted(report["procedures"])
    return report


def _fixture(program, procedures=None, bindings=None):
    return {"services": {"fixture": {"routes": [{"source": "fixture", "program": program, "bindings": bindings or {}}]}},
            "procedures": procedures or {}}


def test_statement_call_and_missing_argument_cannot_hide_unbound_expression_call():
    data = _fixture(compile_predicates([(1, "Call unknown_callback(unavailable_row)")]))
    report = audit_artifact(data)
    assert [entry["name"] for entry in report["unknown_calls"]] == ["unknown_callback"]
    assert report["unsupported"] == []


def test_scalar_assignment_is_not_evidence_that_a_name_is_an_array():
    data = _fixture(compile_predicates([(1, "madeup=3"), (2, "answer=madeup(0)")]))
    assert [entry["name"] for entry in audit_artifact(data)["unknown_calls"]] == ["madeup"]


def test_arrays_propagate_through_aliases_native_returns_and_ado_getrows():
    program = compile_predicates([(1, 'a=Split("a,b",","):alias=a'),
                                  (2, 'solo=b_saju_click(1,1,1974,3,2,8,30,"")'),
                                  (3, "rows=rs.GetRows():r=rows(0,0):s=solo(0):t=alias(1)")])
    report = audit_artifact(_fixture(program))
    assert report["unknown_calls"] == [] and report["unsupported"] == []


def test_known_native_constant_callback_writes_actual_global_arrays():
    procedure = {"name": "helper", "arguments": [], "by_value": [],
                 "program": compile_predicates([(3, "helper=chungan(0)")])}
    data = _fixture(compile_predicates([(1, "Call __native_calendar_constants()"), (2, "answer=helper()")]),
                    {"p": procedure}, {"helper": "p"})
    assert audit_artifact(data)["unknown_calls"] == []


def test_calculation_observer_preserves_the_underlying_array_type():
    data = _fixture(compile_predicates([(1, 'a=__use("calculation",Split("a,b",",")):answer=a(0)')]))
    assert audit_artifact(data)["unknown_calls"] == []


def test_original_buf_fault_is_exactly_pinned_and_not_a_generic_callback_allowance():
    data = _fixture(compile_predicates([(1, "byear=buf(3)")]))
    data.update(locations={"1": {"path": SOURCE_FAULT_PATH, "line": 334}},
                sources={SOURCE_FAULT_PATH: {"sha256": SOURCE_FAULT_SHA256}})
    report = audit_artifact(data)
    assert report["unknown_calls"] == [] and len(report["source_faults"]) == 1
    data["locations"]["1"]["line"] = 333
    assert len(audit_artifact(data)["unknown_calls"]) == 1


def test_array_arguments_and_returns_are_resolved_transitively():
    procedure = {"name": "passthrough", "arguments": ["argument"], "by_value": [],
                 "program": compile_predicates([(3, "passthrough=argument")])}
    data = _fixture(compile_predicates([(1, 'a=Split("a,b",","):got=passthrough(a):result=got(0)')]),
                    {"p": procedure}, {"passthrough": "p"})
    report = audit_artifact(data)
    assert report["unknown_calls"] == [] and report["procedures"] == ["p"]


def test_byref_array_construction_propagates_but_explicit_local_shadows_global_array():
    procedure = {"name": "initialize", "arguments": ["argument"], "by_value": [],
                 "program": compile_predicates([(3, "ReDim argument(3)")])}
    data = _fixture(compile_predicates([(1, "Call initialize(a)"), (2, "answer=a(0)")]),
                    {"p": procedure}, {"initialize": "p"})
    assert audit_artifact(data)["unknown_calls"] == []
    procedure = {"name": "helper", "arguments": [], "by_value": [], "explicit_locals": ["a"],
                 "program": compile_predicates([(3, "helper=a(0)")])}
    data = _fixture(compile_predicates([(1, 'a=Split("a,b",","):answer=helper()')]), {"p": procedure}, {"helper": "p"})
    assert [entry["name"] for entry in audit_artifact(data)["unknown_calls"]] == ["a"]


def test_unsupported_operators_members_and_statements_are_visible_without_execution():
    data = _fixture([["set", 1, "answer", ["binary", "xor", ["literal", 1], ["literal", 2]], None],
                     ["call", 2, ["member", ["variable", "rs"], "execute", []]], ["invented", 3]])
    codes = {item["code"] for item in audit_artifact(data)["unsupported"]}
    assert codes == {"unsupported_binary_operator", "unsupported_member", "unsupported_statement"}


def test_frozen_all_interlife_routes_and_transitive_procedures_have_supported_bindings():
    from app.ported_interlife_leaves import _data

    data = _data()
    assert len(data["services"]) == 74
    report = audit_artifact(data)
    assert report["routes"] >= 74
    assert report["procedures"]
    assert report["unsupported"] == []
    assert report["unknown_calls"] == []


def _source_request(**parameters):
    from app.service_models import ServiceRequest

    return ServiceRequest(
        birth={"year": 1974, "month": 3, "day": 2, "hour": 8, "minute": 30, "gender": "male"},
        target_date="2026-11-18", include_ai=False,
        parameters={"server_time": "2026-11-18T12:34:56", "source_solunar": 2,
                    "source_two_digit_year_max": 2029, **parameters},
    )


def test_header_layout_profile_preserves_its_six_original_random_draws():
    from app.ported_interlife_leaves import _run

    class CountingRng:
        def __init__(self):
            self.draws = 0

        def random(self):
            self.draws += 1
            return 0.25

        def seed(self, value):
            pass

    without_result, with_result = CountingRng(), CountingRng()
    first = _run("interlife-saju-10", _source_request(source_path_contains_result=False), rng=without_result)
    second = _run("interlife-saju-10", _source_request(source_path_contains_result=True), rng=with_result)
    assert without_result.draws == 8 and with_result.draws == 2
    assert sum(item["body"] for item in first["projections"]) == sum(item["body"] for item in second["projections"])


def test_supplied_actual_query_row_stays_untrusted_and_private():
    from app.ported_interlife_leaves import _run, decide

    identifier = "old/unse/interlife/UNSE_DATA/solve/T/T042.asp:38"
    request = _source_request(source_queries={identifier: [{
        "rows": [{"DB_data": "PRIVATE_PROSE_SENTINEL"}], "columns": ["DB_data"], "record_count": 1,
    }]})
    private = _run("interlife-jum-13", request)
    assert any(query["id"] == identifier and query["response_supplied"] for query in private["queries"])
    result = decide("interlife-jum-13", request)
    assert "source_rows_unverified" in result["unresolved"]
    assert result["facts"]["source_rows_trusted"] is False
    public = json.dumps(result, ensure_ascii=False)
    assert all(value not in public for value in ("PRIVATE_PROSE_SENTINEL", "19740302", "1974-03-02", "08:30"))


def test_query_projection_never_exposes_name_identifier_or_date_literals():
    from app.ported_interlife_leaves import _safe_where

    projected = _safe_where("SELECT DB_data FROM S010 WHERE name='甲乙' AND member_id=12345 AND no='19740302' AND DB_num=12", "S010")
    assert projected["DB_num"] == "12"
    assert all(projected[key] == {"private_or_unverified_key": True} for key in ("name", "member_id", "no"))
    assert _safe_where("SELECT DB_data FROM N011 WHERE DB_express=12", "N011")["DB_express"] == {"private_or_unverified_key": True}

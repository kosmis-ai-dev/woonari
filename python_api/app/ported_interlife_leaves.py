"""CR-012/T-024: frozen, request-local execution of the remaining ASP leaves.

The VM receives application-owned AST only. Queries are descriptors which read
explicit investigation records; no SQL, connection, ASP interpreter or COM runs.
Investigation records never establish production data provenance or AI readiness.
"""

from __future__ import annotations

import copy
import json
import math
import random
import re
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError

from app.calendar import solar_birth
from app.errors import DomainError
from app.ported_interlife import KST
from app.ported_interlife_chart import (
    SourceYearTerms,
    bundled_source_terms,
    native_birth,
    native_source_callbacks,
)
from app.ported_ziwei import (
    EMPTY,
    FunctionResult,
    Missing,
    SourceProcedure,
    SourceRecordset,
    execute,
)
from app.rules import BRANCHES, STEMS

DATA_PATH = Path(__file__).with_name("data") / "interlife_leaves_rules.json"


@lru_cache(maxsize=1)
def _data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _node(reference):
    return [_node(value['node']) if isinstance(value, dict) and set(value) == {'node'} else value
            for value in _data()['nodes'][reference]]


def _program(data, item):
    if data is _data():
        return [_node(reference) for reference in item['program_refs']]
    cache = {}
    def expand(reference):
        if reference not in cache:
            cache[reference] = [expand(value['node']) if isinstance(value, dict) and set(value) == {'node'} else value
                                for value in data['nodes'][reference]]
        return cache[reference]
    return [expand(reference) for reference in item['program_refs']]


HELP = {
    "server_time": "선택: 원본 Now/Date의 ISO 한국시간. target_date나 생일을 서버시각으로 대신하지 않습니다.",
    "source_solunar": "선택: saju_made 진입 전 원본값 2=양력,1=평달음력,3=윤달음력. 실제 원본 입력과 대조한 값만 사용합니다.",
    "source_two_digit_year_max": "선택: 원본 CDate의 두 자리 연도 해석 상한(1900~2099). 추정하지 않습니다.",
    "source_terms": "선택: 원본 gDIV 연도키·24절기의 명시적인 4자리 ISO 시각. source_two_digit_year_max와 함께 쓰지 않습니다.",
    "source_request_date": "선택: 원본 Form year/month/day 숫자 문자열 또는 윤달 ByRef 변환 후 정수. 원문은 응답·AI에 포함하지 않습니다.",
    "source_queries": "선택: 원본 query ID별 순서가 확정된 응답 목록. rows/columns/record_count만 받으며 조사용 입력은 실제 DB로 인증되지 않습니다.",
    'source_path_contains_result': '선택: 원본 MapPath의 result 포함 여부만 비교하는 명시적 배치 프로필(bool). 기본 false는 제공 소스의 unse 경로 배치이며 IIS 실제 경로를 조회하지 않습니다.',
    'source_form': '선택: 원본 Request에 명시된 추가 문자열 입력의 조사용 객체. birth/partner/성별·달력 키 중복은 거부하며 원문은 응답·AI에 보내지 않습니다. 이름·획수 서비스는 source_form_fields 안내를 따르세요.',
    'source_route': '선택: 동일 서비스의 원본 단계 파일명. source_routes 안내의 정확한 파일명만 허용하며 기본은 첫 원본 진입점입니다.',
}


def _walk(value):
    if isinstance(value, list):
        if value and isinstance(value[0], str):
            yield value
        for item in value:
            yield from _walk(item)


PROTECTED_FORM = frozenset({'sex', 'my_solnuar', 'youn', 'your_youn', 'your_solunar',
                            'request_year', 'request_month', 'request_day', 'request_hour', 'request_min',
                            'your_year', 'your_month', 'your_day', 'your_hour', 'your_min'})


@lru_cache(maxsize=None)
def _form_fields(service_id, source_route=None):
    data = _data()
    routes = data['services'][service_id]['routes']
    route = next((item for item in routes if Path(item['source']).name == source_route), routes[0])
    if 'request_fields' in route:
        return frozenset(route['request_fields']) - PROTECTED_FORM
    fields = set()
    for item in [route, *(data['procedures'][identifier] for identifier in route['bindings'].values())]:
        for node in _walk(_program(data, item)):
            if len(node) > 2 and node[:2] == ['call', 'request'] and node[2] and node[2][0][0] == 'literal' and isinstance(node[2][0][1], str):
                fields.add(node[2][0][1].lower())
    return frozenset(fields - PROTECTED_FORM)


SERVICES = {
    identifier: {
        "name": item["name"], "original_name": item["name"],
        "requires_birth": True, "requires_partner": identifier.startswith("interlife-gunghap-"),
        "uses_saju": False, "ready": False, "example_parameters": {}, "parameter_help": dict(HELP),
        "source": item["routes"][0]["source"],
        "required_source_fields": ["실제 출력·조회 조건까지 도달하는 원본 필드(계산 결과의 required_source_fields 참조)",
                                   "원본 query 응답의 행 순서·ADO 커서 메타데이터와 실제 데이터 검증"],
        "source_limits": ["공통 include와 본문·후속 DB 분기를 Python AST로 실행합니다. 수동 입력 행은 조사용이며 AI 승인 자료가 아닙니다.",
                          "원본 CDate 세기·달력 입력과 DB 분류/점수의 미확정 항목을 AI가 추정하지 않습니다."],
    }
    for identifier, item in _data()["services"].items()
}
for identifier, spec in SERVICES.items():
    routes = _data()['services'][identifier]['routes']
    spec['source_routes'] = [Path(item['source']).name for item in routes]
    spec['source_form_fields_by_route'] = {Path(item['source']).name: sorted(_form_fields(identifier, Path(item['source']).name)) for item in routes}
    fields = sorted(set().union(*spec['source_form_fields_by_route'].values()))
    spec['source_form_fields'] = fields
    spec['parameter_help']['source_form'] += ' 허용 원본 키: ' + ', '.join(fields)


def _invalid():
    return DomainError("invalid_service_parameters", "원본 계산 조사 입력의 항목·형식·범위를 확인해 주세요.")


class _UnavailableRecordset(SourceRecordset):
    def __init__(self, source, context=frozenset()):
        super().__init__([], source=source)
        self.missing_context = context

    def field(self, key):
        suffix = str(key).lower() if isinstance(key, (str, int)) else "field"
        return Missing(self.missing_context | frozenset({self.source + "." + suffix}))

    def member(self, name, arguments):
        return Missing(self.missing_context | frozenset({self.source + ".ADO_" + name.lower()}))


def _clock(parameters):
    raw = parameters.get("server_time")
    if raw is None:
        return datetime.now(KST).replace(tzinfo=None)
    try:
        if not isinstance(raw, str) or "T" not in raw:
            raise ValueError
        value = datetime.fromisoformat(raw)
        if value.tzinfo is not None:
            if value.utcoffset() != KST.utcoffset(value):
                raise ValueError
            value = value.replace(tzinfo=None)
        if not 1901 <= value.year <= 2049:
            raise ValueError
        return value
    except ValueError:
        raise _invalid() from None


def _terms(parameters):
    if "source_terms" in parameters and "source_two_digit_year_max" in parameters:
        raise _invalid()
    if "source_terms" in parameters:
        rows = parameters["source_terms"]
        if not isinstance(rows, list) or not 1 <= len(rows) <= 3:
            raise _invalid()
        try:
            parsed = [SourceYearTerms.model_validate(row) for row in rows]
        except (ValidationError, TypeError, ValueError):
            raise _invalid() from None
        if len({row.year for row in parsed}) != len(parsed):
            raise _invalid()
        return {row.year: [term.at for term in row.terms] for row in parsed}
    pivot = parameters.get("source_two_digit_year_max")
    if pivot is not None and (type(pivot) is not int or not 1900 <= pivot <= 2099):
        raise _invalid()
    return bundled_source_terms(pivot)


def _records(raw, allowed):
    if raw is None:
        return {}
    if not isinstance(raw, dict) or len(raw) > 500 or set(raw) - allowed:
        raise _invalid()
    result = {}
    for identifier, responses in raw.items():
        if not isinstance(responses, list) or len(responses) > 200:
            raise _invalid()
        result[identifier] = []
        for response in responses:
            if not isinstance(response, dict) or set(response) - {"rows", "columns", "record_count"}:
                raise _invalid()
            rows, columns, count = response.get("rows"), response.get("columns"), response.get("record_count")
            if not isinstance(rows, list) or len(rows) > 1000:
                raise _invalid()
            for row in rows:
                if not isinstance(row, dict) or len(row) > 100:
                    raise _invalid()
                for key, value in row.items():
                    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", key) or not (
                        value is None or type(value) in {str, bool, int, float}
                    ) or isinstance(value, str) and len(value) > 5000 or isinstance(value, float) and not math.isfinite(value):
                        raise _invalid()
            if columns is not None and (not isinstance(columns, list) or len(columns) > 100 or
                                        any(not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name) for name in columns)):
                raise _invalid()
            if count is not None and (type(count) is not int or not -1 <= count <= 100000):
                raise _invalid()
            result[identifier].append({"rows": copy.deepcopy(rows), "columns": tuple(columns) if columns is not None else None,
                                       "record_count": count})
    return result


def _private_request(request, parameters):
    birth = request.birth
    values = {"sex": "남" if birth.gender == "male" else "여", "my_solnuar": "solar" if birth.calendar == "solar" else "lunar",
              "youn": "1" if birth.leap_month else "0", "request_year": str(birth.year),
              "request_month": f"{birth.month:02}", "request_day": f"{birth.day:02}",
              "request_hour": f"{birth.hour:02}", "request_min": f"{birth.minute:02}"}
    if request.partner:
        other = request.partner
        values.update({"your_solunar": "solar" if other.calendar == "solar" else "lunar", "your_youn": "1" if other.leap_month else "0",
                       "your_year": str(other.year), "your_month": f"{other.month:02}", "your_day": f"{other.day:02}",
                       "your_hour": f"{other.hour:02}", "your_min": f"{other.minute:02}"})
    raw_date = parameters.get("source_request_date")
    if raw_date is not None:
        if not isinstance(raw_date, dict) or set(raw_date) != {"year", "month", "day"}:
            raise _invalid()
        fields = [raw_date[key] for key in ("year", "month", "day")]
        if not (all(type(item) is int for item in fields) or all(isinstance(item, str) and re.fullmatch(r"[0-9]{1,4}", item) for item in fields)):
            raise _invalid()
        if [int(value) for value in fields] != [birth.year, birth.month, birth.day]:
            raise _invalid()
        values.update(zip(("request_year", "request_month", "request_day"), fields))
    return values


def _fields(value):
    return set(value.fields) if isinstance(value, Missing) else set()


def _run(service_id, request, *, rng=None):
    """Internal execution result; its private state must never be API evidence."""
    data = _data()
    if request.birth is None or set(request.parameters) - set(HELP):
        raise _invalid()
    parameters = request.parameters
    if 'source_path_contains_result' in parameters and type(parameters['source_path_contains_result']) is not bool:
        raise _invalid()
    clock, terms = _clock(parameters), _terms(parameters)
    binding = parameters.get("source_solunar")
    if binding is not None and (type(binding) is not int or binding not in {1, 2, 3}):
        raise _invalid()
    item = data['services'][service_id]
    selected = parameters.get('source_route')
    allowed_routes = {Path(route['source']).name: route for route in item['routes']}
    if selected is not None and (not isinstance(selected, str) or selected not in allowed_routes):
        raise _invalid()
    route = allowed_routes[selected] if selected is not None else item['routes'][0]
    records = _records(parameters.get("source_queries"), set(data["queries"]))
    request_values = _private_request(request, parameters)
    raw_form = parameters.get('source_form', {})
    if not isinstance(raw_form, dict) or set(raw_form) - _form_fields(service_id, selected):
        raise _invalid()
    for key, value in raw_form.items():
        if not isinstance(value, str) or len(value) > 100 or any(ord(char) < 32 for char in value):
            raise _invalid()
        request_values[key] = value
    queries, projections, halts, native_limits, positions = [], [], [], [], {}
    consumed = set()
    body_consumed = set()
    body_phase = False
    functions = {}

    def connect():
        return EMPTY

    def query(identifier, sql, *, source_context):
        ordinal = positions.get(identifier, 0)
        positions[identifier] = ordinal + 1
        prototype = data["queries"][identifier]
        table_match = re.search(r"\bfrom\s+([a-z_][a-z_0-9]*)", sql, re.I) if isinstance(sql, str) else None
        table = table_match[1] if table_match else prototype.get("table", "source_query")
        table_value = source_context.get(prototype.get('table_variable'))
        if isinstance(table_value, str) and re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', table_value):
            table = table_value
        selected = re.search(r'\bselect\s+(.*?)\s+from\b', sql, re.I) if isinstance(sql, str) else None
        columns = [name.strip() for name in selected[1].split(',')] if selected else []
        source = identifier + '#' + str(ordinal)
        responses = records.get(identifier, [])
        response = responses[ordinal] if ordinal < len(responses) and isinstance(sql, str) else None
        record = SourceRecordset(source=source, **response) if response is not None else _UnavailableRecordset(source, frozenset(_fields(sql)))
        queries.append({"id": identifier, "table": table, "where_dependencies": sorted(_fields(sql)),
                        "sql": sql, "response_supplied": response is not None, "ordinal": ordinal,
                        "body": body_phase, 'columns': columns, 'field_source': source})
        return FunctionResult(EMPTY, {"__rs__": record, "__rs_source__": source})

    query.source_writes = ("__rs__", "__rs_source__")
    query.source_accepts_missing = True
    query.source_context = True
    query.source_context_keys = tuple({item['table_variable'] for item in data['queries'].values() if item.get('table_variable')})

    def emit(identifier, value):
        projections.append({"id": identifier, "dependencies": sorted(_fields(value)),
                            "number": value if type(value) in {int, float} and math.isfinite(value) else None,
                            "body": body_phase})
        return EMPTY

    emit.source_observer = True
    emit.source_accepts_missing = True

    def use(kind, value):
        consumed.update(_fields(value))
        if body_phase:
            body_consumed.update(_fields(value))
        return value

    use.source_observer = True
    use.source_accepts_missing = True

    def phase(value):
        nonlocal body_phase
        body_phase = value is True
        return EMPTY

    def halt(identifier):
        halts.append(identifier)
        return FunctionResult(EMPTY, {"__source_halted__": True})

    halt.source_writes = ("__source_halted__",)

    def dim_array(name, *bounds):
        def allocate(remaining):
            size = int(remaining[0])
            if not 0 <= size <= 1000:
                raise ValueError("Source array size")
            return [allocate(remaining[1:]) if len(remaining) > 1 else EMPTY for _ in range(size + 1)]
        return FunctionResult(EMPTY, {name: allocate(bounds)})

    dim_array.source_writes = tuple(data["declared_arrays"])

    def native_calendar_constants():
        return FunctionResult(EMPTY, {"sixty": [STEMS[i % 10] + BRANCHES[i % 12] for i in range(60)],
                                      "chungan": list(STEMS), "gigi": list(BRANCHES)})

    native_calendar_constants.source_writes = ("sixty", "chungan", "gigi")

    functions.update({"__connect": connect, "__disconnect": connect, "__query": query, "__emit": emit, '__use': use, '__phase': phase, "__halt": halt,
                      "__dim_array": dim_array, "__native_calendar_constants": native_calendar_constants,
                      "cookie": lambda *args: '', '__presentation_path': lambda *args: 'source_result' if parameters.get('source_path_contains_result', False) else 'source_layout',
                      "server_variable": lambda *args: Missing(frozenset({"source_server_variable"})), "dive": lambda *args: EMPTY})
    functions.update(native_source_callbacks(terms_by_year=terms, reference_year=clock.year, diagnostics=native_limits))
    global_names = set(route.get("globals", route["assigned"])) | {"__rs__", "__rs_source__"}
    for name, identifier in route.get("bindings", {}).items():
        procedure = data["procedures"][identifier]
        local_names = set(procedure.get("explicit_locals", [])) | (set(procedure["assigned"]) - global_names)
        writes = tuple(set(procedure["assigned"]) - local_names - set(procedure["arguments"]) - {name})
        functions[name] = SourceProcedure(tuple(procedure["arguments"]), _program(data, procedure), frozenset(local_names),
                                          frozenset(procedure["by_value"]), writes)
    environment = {name: EMPTY for name in global_names}
    environment.update({"__clock__": clock, "__request__": request_values,
                        "solunar": binding if binding is not None else EMPTY,
                        "__source_halted__": False, '__body_phase__': False})
    result = execute(_program(data, route), environment, functions=functions, rng=rng or random.Random(), retain_state=True,
                     on_error_resume_next=False)
    return {"state": result["state"], "source_errors": result["source_errors"], "queries": queries,
            "projections": projections, "halts": halts, "native_limits": native_limits,
            "records_supplied": bool(records), "route": route["source"], 'aborted': result.get('aborted', False),
            'consumed_fields': consumed, 'body_consumed_fields': body_consumed}


def _safe_where(sql, table):
    """Expose only small classification codes; never raw birth/name/number keys."""
    if not isinstance(sql, str):
        return None
    match = re.search(r"\bwhere\s+(.*?)(?:\border\s+by\b|$)", sql, re.I)
    if not match:
        return {}
    fields = {}
    for column, quoted, numeric in re.findall(r"\b([A-Za-z_][A-Za-z_0-9]*)\s*(?:=|like)\s*(?:'([^']*)'|(-?\d+(?:\.\d+)?))", match[1], re.I):
        value = quoted if quoted else numeric
        safe = bool(re.fullmatch(r'DB_(?:express(?:_\d+)?|num(?:ber)?)', column, re.I) and
                    not table.upper().startswith('N') and
                    re.fullmatch(r"[0-9]{1,3}|[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]{1,4}", value))
        fields[column] = value if safe else {"private_or_unverified_key": True}
    return fields or {"source_expression": "computed; private values suppressed"}


def source_birth_dates(service_id, request):
    """Use the explicitly selected native date profile before engine validation."""
    if request.birth is None:
        return []
    binding = request.parameters.get('source_solunar')
    if binding is None:
        dates = [solar_birth(request.birth).date()]
    else:
        private = _private_request(request, request.parameters)
        tokens = {key: private['request_' + key] for key in ('year', 'month', 'day')}
        dates = [native_birth(request.birth, binding, tokens, 'original_regular_fallback')[0].date()]
    if request.partner is not None:
        dates.append(solar_birth(request.partner).date())
    return dates


def decide(service_id, request, saju=None, partner=None):
    result = _run(service_id, request)
    material = set(result['body_consumed_fields'])
    projected = set()
    for projection in result["projections"]:
        if projection['body']:
            projected.update(projection["dependencies"])
    query_map = {query['field_source']: query for query in result['queries']}
    prose = set()
    for field in projected:
        source, _, column = field.rpartition('.')
        query = query_map.get(source)
        if query and field not in result['consumed_fields'] and re.fullmatch(r'db_data(?:_\d+)?', column, re.I) and not (
            query['table'].upper().startswith('N') or query['table'].upper() in {'S008', 'S009'}
        ):
            prose.add(field)
        else:
            material.add(field)
    selectors = []
    for query in result["queries"]:
        # Calendar lookups feed the calculation, never narrative AI prompts.
        if not query['body'] or query["table"].lower() in {"mansedata", "lunartosolar"}:
            continue
        prefix = query['field_source'] + '.'
        factual_columns = sorted({field[len(prefix):] for field in material if field.startswith(prefix)})
        prose_columns = sorted({field[len(prefix):] for field in prose if field.startswith(prefix)})
        if factual_columns or prose_columns:
            material.update(query["where_dependencies"])
        where = _safe_where(query["sql"], query['table'])
        for role, columns in [('calculation', factual_columns), ('narrative', prose_columns)]:
            if columns:
                selectors.append({'id': query['field_source'] + ':' + role, 'table': query['table'], 'where': where,
                                  'columns': columns, 'purpose': '원본의 계산·조건 소비 필드' if role == 'calculation' else '계산 후 본문에만 표시되는 원문을 AI로 대체합니다.',
                                  'role': role, 'narrative': role == 'narrative'})
    if result["records_supplied"]:
        material.add("source_rows_unverified")
    if request.parameters.get('source_form'):
        material.add('source_form_unverified')
    if result['halts']:
        material.add('source_control_flow_halted_at_recorded_location')
    material.update(_fields(result['state'].get('__source_halted__')))
    if result['aborted']:
        material.add('source_execution_aborted_at_recorded_fault')
    def describe(field):
        source, _, column = field.rpartition('.')
        query = query_map.get(source)
        if query:
            metadata = _data()['queries'][query['id']]
            return f"{query['table']}.{column} [{metadata['path']}:{metadata['line']}; 호출 {query['ordinal'] + 1}]"
        return field
    error_counts = Counter((row['line'], row['code']) for row in result['source_errors'])
    errors = [{"source": _data()["locations"].get(str(line)), "code": code, 'count': count}
              for (line, code), count in error_counts.items()]
    return {"source": result["route"], "facts": {"source_profile": "interlife-frozen-shared-ast-v1",
            "source_algorithm_complete": True, "sql_executed": False, "source_rows_trusted": False,
            "source_rows_supplied": result["records_supplied"], "output_projection_count": len(result["projections"]),
            'presentation_scope': '공통 헤더의 수식·전역 대입·RNG는 배치 프로필에 따라 원본 순서로 실행하며 헤더 HTML만 API 본문에서 제외합니다.',
            'source_path_profile': 'contains_result' if request.parameters.get('source_path_contains_result', False) else 'provided_unse_layout_without_result',
            "numeric_output_count": sum(row['body'] and row['number'] is not None for row in result['projections']),
            "required_source_fields": sorted(describe(field) for field in material), "source_errors": errors,
            'narrative_only_fields': sorted(describe(field) for field in prose),
            'native_diagnostics': result['native_limits'],
            "control_flow_halted": bool(result["halts"]), "raw_private_inputs_returned": False},
            "selectors": selectors, "unresolved": sorted(describe(field) for field in material)}

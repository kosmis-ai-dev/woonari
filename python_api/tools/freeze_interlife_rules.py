"""CR-012/T-024: compile supplied interlife calculations into a frozen Python VM AST.

Development tool only: --freeze requires the original source. Connection files
are metadata-only boundaries and are never read, copied, compiled or executed.
Normal API execution reads the frozen JSON and never needs original ASP files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ported_ziwei import compile_predicates
from tools.source_inventory import ROOT, load_snapshot

DESTINATION = ROOT / "python_api/app/data/interlife_leaves_rules.json"
BASELINE = ROOT / ".local/woonari/analysis/cr012/dependency_audit.json"
SSI = re.compile(r'<!--\s*#include\s+(?:virtual|file)\s*=\s*["\x27]?([^"\x27\s>]+)[^>]*-->', re.I)
TOKENS = re.compile(r'<!--\s*#include\s+(?:virtual|file)\s*=\s*["\x27]?([^"\x27\s>]+)[^>]*-->|<%(?!@)(=?)(.*?)%>', re.I | re.S)
PROCEDURE = re.compile(r'^(?:(?:public|private)\s+)?(function|sub)\s+(\w+)\s*\((.*?)\)\s*$', re.I)
NATIVE_FILES = {}
PROFILE_FILES = {
    "old/unse/interlife/UNSE_DATA/solve/f_Saju.asp",
}
NATIVE_PROCEDURES = {
    "b_saju_click", "f_pre_div24", "f_next_div24", "fi_pre_div24",
}


def uncomment(code):
    result, quoted, index = "", False, 0
    while index < len(code):
        char = code[index]
        if char == '"':
            if quoted and index + 1 < len(code) and code[index + 1] == '"':
                result += '""'
                index += 2
                continue
            quoted = not quoted
        if char == "'" and not quoted:
            break
        result += char
        index += 1
    return result.strip()


def commas(code):
    return re.split(r",\s*(?![^()]*\))", code)


def replace_writes(code, identifier):
    """Split inline Else/colon at statement level, preserving quoted HTML."""
    cursor = 0
    while True:
        match = re.search(r'\bresponse\.write\s+', code[cursor:], re.I)
        if match is None:
            return code
        begin, start = cursor + match.start(), cursor + match.end()
        position, depth, quoted = start, 0, False
        while position < len(code):
            char = code[position]
            if char == '"':
                if quoted and position + 1 < len(code) and code[position + 1] == '"':
                    position += 2
                    continue
                quoted = not quoted
            if not quoted:
                depth += (char == '(') - (char == ')')
                if depth == 0 and (char == ':' or re.match(r'\b(?:else|end\s+if)\b', code[position:], re.I)):
                    break
            position += 1
        replacement = f'Call __emit("{identifier}", {code[start:position].strip()})'
        code = code[:begin] + replacement + ' ' + code[position:]
        cursor = begin + len(replacement)


def walk(node):
    if isinstance(node, list):
        if node and isinstance(node[0], str):
            yield node
        for child in node:
            yield from walk(child)


def names(program):
    assigned, arrays, calls = set(), set(), set()
    for node in walk(program):
        if node[0] == "set":
            assigned.add(node[2])
            value = node[3]
            while value[:2] == ['call', '__use']:
                value = value[2][1]
            if node[4] is not None or value[:2] in (["call", "split"], ["call", "array"], ['call', 'b_saju_click']) or value[0] == 'member' and value[2] == 'getrows':
                arrays.add(node[2])
        elif node[0] == "redim":
            assigned.add(node[2])
            arrays.add(node[2])
        elif node[0] == "for":
            assigned.add(node[2])
        elif node[0] == 'dim':
            assigned.add(node[2])
        elif node[0] == "call" and isinstance(node[1], str):
            calls.add(node[1])
            if node[1] == '__dim_array' and isinstance(node[2], list) and node[2] and node[2][0][0] == 'literal':
                arrays.add(node[2][0][1])
                assigned.add(node[2][0][1])
    return {"assigned": sorted(assigned), "arrays": sorted(arrays), "calls": sorted(calls)}


def observe(program):
    """Value-preserving observers distinguish prose from classification use."""
    parsing = {'int', 'cint', 'abs', 'round', 'sgn', 'isnumeric', 'ubound', 'lbound', 'instr',
               'mid', 'left', 'right', 'len', 'split', 'replace', 'cdate', 'year', 'month', 'day',
               'hour', 'minute', 'weekday', 'dateadd', 'datediff', 'datepart'}
    def used(value):
        return ['call', '__use', [['literal', 'calculation'], value]]
    def expression(value):
        if not isinstance(value, list) or not value:
            return value
        kind = value[0]
        if kind == 'binary':
            result = [kind, value[1], expression(value[2]), expression(value[3])]
            return result if value[1] == '&' else used(result)
        if kind == 'unary':
            return used([kind, value[1], expression(value[2])])
        if kind == 'group':
            return [kind, expression(value[1])]
        if kind == 'call':
            result = [kind, value[1], [expression(arg) for arg in value[2]]]
            newline = (value[2][1] in (['literal', '\n'], ['literal', '\r'], ['literal', '\r\n']) or
                       value[2][1] in (['call', 'chr', [['literal', 10]]], ['call', 'chr', [['literal', 13]]])) if len(value[2]) == 3 else False
            formatting = (value[1] == 'replace' and newline and value[2][2][0] == 'literal' and
                          isinstance(value[2][2][1], str) and value[2][2][1].lower() in {'<br>', '<br/>', '<br />'})
            return used(result) if value[1] in parsing and not formatting else result
        if kind == 'member':
            return [kind, expression(value[1]), value[2], [expression(arg) for arg in value[3]]]
        if kind == 'index':
            return used([kind, expression(value[1]), [expression(arg) for arg in value[2]]])
        return value
    result = []
    for node in program:
        value = list(node)
        if node[0] == 'set':
            value[3] = expression(node[3])
            value[4] = used(expression(node[4])) if node[4] is not None else None
        elif node[0] == 'call':
            value[2] = expression(node[2])
        elif node[0] == 'if':
            value[2], value[3], value[4] = used(expression(node[2])), observe(node[3]), observe(node[4])
        elif node[0] == 'for':
            value[3:6] = [used(expression(part)) for part in node[3:6]]
            value[6] = observe(node[6])
        elif node[0] == 'select_case':
            value[2] = used(expression(node[2]))
            value[3] = [[tests, observe(body)] for tests, body in node[3]]
            value[4] = observe(node[4])
        elif node[0] == 'redim':
            value[3] = used(expression(node[3]))
        result.append(value)
    return result


class Freezer:
    def __init__(self):
        self.inventory = load_snapshot()["files"]
        self.paths = {name.lower(): name for name in self.inventory if name.lower().endswith(('.asp', '.js'))}
        self.locations, self.location_ids = {}, {}
        self.sources, self.procedures, self.definitions = {}, {}, {}
        self.queries, self.outputs, self.omissions = {}, {}, []
        self.connection_declarations = {}
        self.declared_arrays = set()
        self.explicit_declarations = {}
        self.route_sources = set()
        self.code_lines, self.procedure_boundaries, self.route_definitions = {}, set(), []
        self.next_location = 1

    def location(self, path, line):
        key = (path, line)
        if key not in self.location_ids:
            number = self.next_location
            self.next_location += 1
            self.location_ids[key] = number
            self.locations[str(number)] = {"path": path, "line": line}
        return self.location_ids[key]

    def resolve(self, parent, include):
        part = include.replace("\\", "/").lstrip("/")
        candidates = [part, "old/" + part]
        if "unse_data/" in part.lower():
            index = part.lower().index("unse_data/")
            candidates.insert(0, "old/unse/interlife/" + part[index:])
        candidates.append((Path(parent).parent / part).as_posix())
        return next((self.paths[item.lower()] for item in candidates if item.lower() in self.paths), None)

    def read(self, path):
        if path not in self.sources:
            self.sources[path] = {**self.inventory[path], "connection_body_excluded": "db_connect" in path.lower()}
        if "db_connect" in path.lower():
            raise ValueError("Legacy connection bodies must not be read")
        raw = (ROOT / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != self.inventory[path]["sha256"]:
            raise ValueError("Original source changed after provenance was frozen")
        return raw.decode("cp949")

    def lines(self, path, source, offset):
        rows, buffer, start = [], "", offset
        for number, raw in enumerate(source.splitlines(), offset):
            code = uncomment(raw)
            if not code:
                continue
            if not buffer:
                start = number
            buffer += (" " if buffer else "") + (code[:-1].rstrip() if code.endswith("_") else code)
            if not code.endswith("_"):
                rows.extend(self.prepare(path, start, buffer))
                buffer = ""
        if buffer:
            raise ValueError("Unclosed source continuation")
        return rows

    def prepare(self, path, line, code):
        number = self.location(path, line)
        self.code_lines[number] = {'sha256': hashlib.sha256(code.encode('utf-8')).hexdigest(),
                                   'structural': bool(re.match(r'^(?:end\s+(?:if|select|function|sub)|else\b|next\b|case\b)', code, re.I))}
        if path.endswith('/N/N005.asp') and line == 8:
            # Implicit procedure call syntax, not an assignment. Primary parser
            # grammar: Wine vbscript/parser.y SimpleStatement SubFirstArgOp.
            code = re.sub(r'Then\s+Int\(malun_no\)\s*-\s*80\s*$',
                          'Then Call Int((malun_no) - 80)', code, flags=re.I)
            self.omissions.append({'location': number, 'reason': 'equivalent implicit-call normalization; discarded result, original malun_no unchanged',
                                   'grammar': 'https://raw.githubusercontent.com/wine-mirror/wine/master/dlls/vbscript/parser.y#L218-L230'})
        code = re.sub(r"\brequest\.cookies\s*\(", "cookie(", code, flags=re.I)
        code = re.sub(r"\brequest\.form\s*\(", "request(", code, flags=re.I)
        code = re.sub(r"\brequest\.servervariables\s*\(", "server_variable(", code, flags=re.I)
        if path.endswith(('/solve/ohang.asp', '/solve/yukhyo.asp')):
            code = re.sub(r'\bServer\.MapPath\s*\(', '__presentation_path(', code, flags=re.I)
        if re.match(r"^(?:call\s+)?f_db_connect\s*\(", code, re.I):
            return [(number, "Call __connect()")]
        match = re.match(r"^set\s+rs\s*=\s*ldb\.execute\((.*)\)\s*$", code, re.I)
        if match:
            identifier = path + ":" + str(line)
            temporary = "__sql_" + str(number)
            table = re.search(r'\bfrom\s+([a-z_][a-z_0-9]*)', match[1], re.I)
            variable = re.search(r'\bfrom\s*"\s*&\s*([a-z_][a-z_0-9]*)', match[1], re.I)
            self.queries[identifier] = {"path": path, "line": line, "temporary": temporary,
                                        "table": table[1] if table else Path(path).stem,
                                        'table_variable': variable[1].lower() if variable else None}
            return [(number, f"{temporary} = {match[1]}"), (number, f'Call __query("{identifier}", {temporary})')]
        if re.match(r"^set\s+rs\s*=\s*nothing\b", code, re.I):
            return [(number, "__rs__ = null")]
        if re.match(r"^ldb\.close\b|^set\s+ldb\s*=\s*nothing\b", code, re.I):
            return [(number, "Call __disconnect()")]
        if re.match(r"^response\.cookies\s*\(", code, re.I):
            self.omissions.append({"location": number, "reason": "response cookie transport excluded; request cookie is explicit input, no request-local mutation"})
            return []
        if re.match(r"^response\.end\b", code, re.I):
            return [(number, f'Call __halt("{number}")')]
        if re.match(r"^response\.redirect\b", code, re.I):
            return [(number, f'Call __halt("{number}")')]
        if re.match(r"^(?:re)?dim\s+", code, re.I):
            declaration, *tail = code.split(":", 1)
            body = re.sub(r"^(?:re)?dim\s+", "", declaration, flags=re.I)
            if re.match(r'^dim\b', code, re.I):
                self.explicit_declarations.setdefault(number, set()).update(re.match(r'\w+', item.strip())[0].lower() for item in commas(body))
            rows = []
            for item in commas(body):
                array = re.fullmatch(r'(\w+)\s*\((.*)\)', item.strip())
                if array:
                    self.declared_arrays.add(array[1].lower())
                if array and ',' in array[2]:
                    rows.append((number, f'Call __dim_array("{array[1].lower()}", {array[2]})'))
                else:
                    rows.append((number, ("ReDim " if "(" in item else "Dim ") + item))
            if tail:
                rows.extend(self.prepare(path, line, tail[0].strip()))
            return rows
        if re.search(r"\bresponse\.write\s+", code, re.I):
            identifier = path + ":" + str(line)
            self.outputs[identifier] = {"path": path, "line": line, "kind": "write"}
            code = replace_writes(code, identifier)
        if re.match(r"^call\s+s_graph\s*\(", code, re.I):
            self.outputs[path + ":" + str(line)] = {"path": path, "line": line, "kind": "graph"}
        if re.fullmatch(r'\w+\s*\(.*\)', code) and not re.match(r'^(?:if|elseif|for)\b|^\w+\s*\([^)]*\)\s*=', code, re.I):
            code = 'Call ' + code
        return [(number, code)]

    def flatten(self, path, stack=(), *, library_only=False):
        self.route_sources.add(path)
        if path in stack:
            raise ValueError("Cyclic source includes require explicit review")
        if "db_connect" in path.lower():
            self.sources.setdefault(path, {**self.inventory[path], "connection_body_excluded": True})
            # Only Dim declarations are extracted; authentication expressions,
            # literals and connection bodies are never retained or compiled.
            if path not in self.connection_declarations:
                declarations = []
                for number, raw in enumerate((ROOT / path).read_bytes().decode('cp949').splitlines(), 1):
                    if re.match(r'^\s*Dim\s+', raw, re.I):
                        declaration = uncomment(raw).split(':', 1)[0]
                        if not re.fullmatch(r'[A-Za-z_0-9,() \t]+', declaration):
                            raise ValueError('Connection declaration must contain identifiers and array bounds only')
                        declarations.extend(self.prepare(path, number, declaration))
                self.connection_declarations[path] = declarations
            return self.connection_declarations[path] + [(self.location(path, 1), "Call __connect()")]
        text = self.read(path)
        if path.endswith('.js'):
            self.omissions.append({'location': self.location(path, 1), 'reason': 'client tooltip CSS/visibility only; no server ASP block or fortune arithmetic'})
            return []
        result, procedure = [], None
        for token in TOKENS.finditer(text):
            if token[1] is not None:
                included = self.resolve(path, token[1])
                if included is not None:
                    if not library_only and re.search(r'/common/include_bottom[^/]*\.asp$', included, re.I):
                        result.extend([(self.location(path, text[:token.start()].count('\n') + 1), '__body_phase__ = False'),
                                       (self.location(path, text[:token.start()].count('\n') + 1), 'Call __phase(False)')])
                    result.extend(self.flatten(included, (*stack, path), library_only=library_only or path in NATIVE_FILES or path in PROFILE_FILES))
                    if not library_only and re.search(r'/common/include_top[^/]*\.asp$', included, re.I):
                        result.append((self.location(path, text[:token.start()].count('\n') + 1), '__body_phase__ = True'))
                        result.append((self.location(path, text[:token.start()].count('\n') + 1), 'Call __phase(True)'))
                else:
                    self.omissions.append({"location": self.location(path, text[:token.start()].count("\n") + 1), "reason": "external static presentation include", "include": token[1]})
                continue
            offset = text[:token.start(3)].count("\n") + 1
            if token[2] == '=':
                expression = uncomment(token[3])
                identifier = path + ':' + str(offset)
                self.outputs[identifier] = {'path': path, 'line': offset, 'kind': 'expression'}
                block_rows = [(self.location(path, offset), f'Call __emit("{identifier}", {expression})')]
            else:
                block_rows = self.lines(path, token[3], offset)
            for location, code in block_rows:
                declaration = PROCEDURE.match(code)
                if declaration:
                    self.procedure_boundaries.add(location)
                    if procedure is not None:
                        raise ValueError("Nested source procedure definition")
                    parameters, by_value = [], []
                    for index, argument in enumerate(commas(declaration[3])):
                        if not argument.strip():
                            continue
                        if argument.lower().strip().startswith("byval "):
                            by_value.append(index)
                        parameters.append(re.sub(r"^(?:byval|byref)\s+", "", argument.strip(), flags=re.I).lower())
                    procedure = {"name": declaration[2].lower(), "arguments": parameters, "by_value": by_value,
                                 "lines": [], "source": path, "definition_location": location}
                elif re.match(r"^end\s+(?:function|sub)\b", code, re.I):
                    self.procedure_boundaries.add(location)
                    if procedure is None:
                        raise ValueError("Unmatched source procedure end")
                    identifier = path + "::" + procedure["name"]
                    self.procedures[identifier] = procedure
                    self.definitions.setdefault(procedure["name"], []).append(identifier)
                    self.route_definitions.append(identifier)
                    procedure = None
                elif procedure is not None:
                    procedure["lines"].append((location, code))
                elif not library_only and path not in NATIVE_FILES and path not in PROFILE_FILES:
                    result.append((location, code))
        if procedure is not None:
            raise ValueError("Unclosed source procedure")
        if not library_only and path in NATIVE_FILES:
            result.append((self.location(path, 1), f"Call {NATIVE_FILES[path]}()"))
        elif not library_only and path in PROFILE_FILES:
            native = {"common/requestBuffer.asp": "__request_buffer", "solve/setting_var.asp": "__setting_var", "solve/f_Saju.asp": "__native_calendar_constants"}
            name = next(value for key, value in native.items() if path.endswith(key))
            result.append((self.location(path, 1), f"Call {name}()"))
        return result

    def freeze(self, definitions):
        services = {}
        for definition in definitions:
            paths = definition["entrypoints"]
            routes = []
            for path in paths:
                self.route_sources = set()
                self.route_definitions = []
                lines = self.flatten(path)
                try:
                    program = observe(compile_predicates(lines))
                except ValueError as error:
                    trace = error.__traceback__
                    while trace and trace.tb_frame.f_code.co_name != 'compile_predicates':
                        trace = trace.tb_next
                    failed = trace.tb_frame.f_locals.get('number') if trace else None
                    detail = [(self.locations[str(number)], code) for number, code in lines if number == failed]
                    raise ValueError(f'{path}: {error}; source={detail}') from error
                duplicates = sorted({identifier for identifier in self.route_definitions if self.route_definitions.count(identifier) > 1})
                routes.append({"source": path, "program": program, "includes": sorted(self.route_sources),
                               'duplicate_procedure_definitions': duplicates, **names(program)})
            services[definition["id"]] = {"name": definition["original_name"], "routes": routes}
        # Only recursively required procedures are compiled. Native replacements
        # name the separately tested, exact source-calculation adapters.
        needed = {name for item in services.values() for route in item["routes"] for name in route["calls"]}
        compiled = {}
        while needed:
            name = needed.pop()
            if name in NATIVE_PROCEDURES:
                continue
            for identifier in self.definitions.get(name, []):
                if identifier in compiled:
                    continue
                raw = self.procedures[identifier]
                program = observe(compile_predicates(raw["lines"]))
                compiled[identifier] = {key: value for key, value in raw.items() if key != "lines"}
                compiled[identifier].update(program=program, **names(program))
                declarations = set().union(*(self.explicit_declarations.get(number, set()) for number, _ in raw['lines']))
                if 'rs' in declarations:
                    declarations.update({'__rs__', '__rs_source__'})
                compiled[identifier]['explicit_locals'] = sorted(declarations)
                needed.update(compiled[identifier]["calls"])
        for item in services.values():
            for route in item['routes']:
                bindings, pending = {}, set(route['calls'])
                while pending:
                    name = pending.pop()
                    if name in bindings or name in NATIVE_PROCEDURES:
                        continue
                    available = [key for key, value in compiled.items() if value['name'] == name and value['source'] in route['includes']]
                    if available:
                        bindings[name] = available[-1]
                        pending.update(compiled[available[-1]]['calls'])
                route['bindings'] = bindings
                route['globals'] = route['assigned']
                route['request_fields'] = sorted({node[2][0][1].lower()
                    for item in [route, *(compiled[key] for key in bindings.values())]
                    for node in walk(item['program']) if len(node) > 2 and node[:2] == ['call', 'request'] and node[2]
                    and node[2][0][0] == 'literal' and isinstance(node[2][0][1], str)})
        active = {node[1] for item in [*(route for service in services.values() for route in service['routes']), *compiled.values()]
                  for node in walk(item['program']) if len(node) > 1 and type(node[1]) is int and node[0] not in {'literal', 'value'}}
        unused = {number for identifier, procedure in self.procedures.items() if identifier not in compiled
                  for number, _ in procedure['lines']}
        excluded = {item['location'] for item in self.omissions if item['reason'].startswith('response cookie')}
        coverage = {}
        for number, entry in self.code_lines.items():
            path = self.locations[str(number)]['path']
            category = ('compiled' if number in active else 'native_f_saju_delegate' if path.endswith('/solve/f_Saju.asp') else
                        'structural_or_procedure_boundary' if entry['structural'] or number in self.procedure_boundaries else
                        'unused_procedure' if number in unused else 'cookie_transport' if number in excluded else 'unaccounted')
            coverage[str(number)] = {'category': category, 'sha256': entry['sha256']}
        unaccounted = [self.locations[number] for number, entry in coverage.items() if entry['category'] == 'unaccounted']
        if unaccounted:
            raise ValueError(f'Unaccounted active source statements: {unaccounted[:20]}')
        nodes, node_keys = [], {}
        def pack(value):
            if not isinstance(value, list):
                return value
            encoded = [pack(child) for child in value]
            key = json.dumps(encoded, ensure_ascii=False, separators=(',', ':'))
            if key not in node_keys:
                node_keys[key] = len(nodes)
                nodes.append(encoded)
            return {'node': node_keys[key]}
        for item in [*(route for service in services.values() for route in service['routes']), *compiled.values()]:
            item['program_refs'] = [pack(node)['node'] for node in item.pop('program')]
        return {"schema_version": 3, "change": "CR-012/T-024", "services": services, "procedures": compiled, 'nodes': nodes,
                "native_procedures": sorted(NATIVE_PROCEDURES), "sources": self.sources, "locations": self.locations,
                "queries": self.queries, "outputs": self.outputs, "omissions": self.omissions,
                "declared_arrays": sorted(self.declared_arrays), 'source_statement_coverage': coverage,
                'delegations': {'f_Saju': {'module': 'app.ported_interlife_chart', 'callbacks': sorted(NATIVE_PROCEDURES),
                                          'proof': 'tested native calendar/date/major-luck/yongsin adapter; no ASP or file loader at runtime'},
                                'connections': 'Only Dim symbol/array declarations and no-I/O boundary are retained; authentication bodies excluded'}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true")
    options = parser.parse_args()
    if not options.freeze:
        data = json.loads(DESTINATION.read_text(encoding="utf-8"))
        print(json.dumps({"services": len(data["services"]), "source_files": len(data["sources"])}))
        return
    baseline = json.loads(BASELINE.read_text())
    identifiers = baseline["groups"]["interlife_noncalendar_DB_rules"]["ids"]
    catalog = json.loads((ROOT / "python_api/app/data/legacy_services.json").read_text())["items"]
    definitions = [item for item in catalog if item["id"] in identifiers]
    data = Freezer().freeze(definitions)
    temporary = DESTINATION.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary.replace(DESTINATION)
    print(json.dumps({"services": len(data["services"]), "source_files": len(data["sources"]), "procedures": len(data["procedures"])}))


if __name__ == "__main__":
    main()

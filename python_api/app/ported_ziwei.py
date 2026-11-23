"""CR-012/T-024: constrained source predicates and the complete Ziwei calculation.

Only a frozen data AST runs. No eval, filesystem source lookup, SQL, COM, or
caller-supplied executable expressions are used by calculate_ziwei.
"""

from __future__ import annotations

import json
import math
import random
import re
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType

from app.errors import DomainError
from app.rules import BRANCHES, STEMS

SOURCE = "old/unse/interlife/UNSE_DATA/solve/S_J017_J030_sol.asp"
_TOKEN = re.compile(r'\s*("(?:[^"]|"")*"|\d+(?:\.\d+)?|[A-Za-z_][A-Za-z_0-9]*|<>|<=|>=|=<|=>|><|[=<>+*/\\&(),:.\-])')
_PRECEDENCE = {"or": 1, "and": 2, "=": 3, "<>": 3, "<": 3, ">": 3, "<=": 3, ">=": 3, "&": 4, "+": 5, "-": 5, "mod": 6, "\\": 7, "*": 8, "/": 8}
SUPPORTED_STATEMENTS = frozenset({"set", "dim", "if", "redim", "erase", "randomize", "select", "call", "select_case", "for", "exit", "on_error"})
SUPPORTED_EXPRESSIONS = frozenset({"literal", "value", "variable", "group", "unary", "binary", "call", "index", "member"})
SUPPORTED_UNARY_OPERATORS = frozenset({"not", "+", "-"})
SUPPORTED_BINARY_OPERATORS = frozenset(_PRECEDENCE)
SUPPORTED_OPERATORS = SUPPORTED_UNARY_OPERATORS | SUPPORTED_BINARY_OPERATORS
SUPPORTED_BUILTINS = frozenset({"rs", "request", "int", "abs", "round", "sgn", "isnumeric", "ubound", "lbound",
    "lcase", "ucase", "trim", "ltrim", "rtrim", "instr", "chr", "rnd", "cint", "cstr", "mid", "left", "right",
    "len", "split", "replace", "array", "date", "now", "time", "cdate", "year", "month", "day", "hour", "minute", "weekday", "dateadd", "datediff", "datepart"})
SUPPORTED_RECORDSET_MEMBERS = frozenset({"eof", "bof", "recordcount", "getrows", "movenext", "moveprevious", "movefirst", "movelast", "close"})


def _tokens(text):
    values, position = [], 0
    while text[position:].strip():
        match = _TOKEN.match(text, position)
        if match is None:
            raise ValueError("Unsupported source token")
        value = match[1]
        value = {"=<": "<=", "=>": ">=", "><": "<>"}.get(value, value)
        values.append(value if value.startswith('"') else value.lower())
        position = match.end()
    return values


class _Parser:
    def __init__(self, tokens):
        self.tokens, self.position = tokens, 0

    def pop(self):
        value = self.tokens[self.position]
        self.position += 1
        return value

    def peek(self):
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def expression(self, minimum=0):
        token = self.pop()
        if token in ("-", "+", "not"):
            left = ["unary", token, self.expression(3 if token == "not" else 9)]
        elif token == "(":
            left = ["group", self.expression()]
            if self.pop() != ")":
                raise ValueError("Unclosed source expression")
        elif token.startswith('"'):
            left = ["literal", token[1:-1].replace('""', '"')]
        elif re.fullmatch(r"\d+(?:\.\d+)?", token):
            left = ["literal", float(token) if "." in token else int(token)]
        elif re.fullmatch(r"[a-z_][a-z_0-9]*", token):
            if token in ("true", "false"):
                left = ["literal", token == "true"]
            elif token == "null":
                left = ["literal", None]
            elif token == "empty":
                left = ["variable", "__empty__"]
            elif self.peek() == "(":
                self.pop()
                arguments = []
                if self.peek() != ")":
                    while True:
                        arguments.append(self.expression())
                        if self.peek() != ",":
                            break
                        self.pop()
                if self.pop() != ")":
                    raise ValueError("Unclosed source call")
                left = ["call", token, arguments]
            else:
                left = ["variable", token]
        else:
            raise ValueError("Unsupported source expression")
        while self.peek() in ("(", "."):
            member = None
            if self.pop() == ".":
                member = self.pop()
                if not re.fullmatch(r"[a-z_][a-z_0-9]*", member):
                    raise ValueError("Invalid source recordset member")
                if self.peek() != "(":
                    left = ["member", left, member, []]
                    continue
                self.pop()
            indexes = []
            if self.peek() != ")":
                while True:
                    indexes.append(self.expression())
                    if self.peek() != ",":
                        break
                    self.pop()
            if self.pop() != ")":
                raise ValueError("Unclosed source postfix index")
            left = ["member", left, member, indexes] if member else ["index", left, indexes]
        while self.peek() in _PRECEDENCE and _PRECEDENCE[self.peek()] >= minimum:
            operator = self.pop()
            left = ["binary", operator, left, self.expression(_PRECEDENCE[operator] + 1)]
        return left

    def inline(self, line, stop_at_else=False):
        result = []
        while self.peek() is not None and not (stop_at_else and self.peek() == "else"):
            if self.tokens[self.position:self.position + 2] == ["end", "if"]:
                self.position += 2
                break
            if self.peek() == ":":
                self.pop()
                continue
            if self.peek() == "exit":
                self.pop()
                kind = self.pop()
                if kind not in {"for", "function", "sub"}:
                    raise ValueError("Unsupported source Exit")
                result.append(["exit", line, kind])
                continue
            if self.peek() == "on":
                if self.tokens[self.position:self.position + 4] == ["on", "error", "resume", "next"]:
                    self.position += 4
                    result.append(["on_error", line, True])
                elif self.tokens[self.position:self.position + 4] == ["on", "error", "goto", "0"]:
                    self.position += 4
                    result.append(["on_error", line, False])
                else:
                    raise ValueError("Unsupported source error policy")
                continue
            if self.peek() == "erase":
                self.pop()
                while True:
                    name = self.pop()
                    if not re.fullmatch(r"[a-z_][a-z_0-9]*", name):
                        raise ValueError("Invalid source Erase target")
                    result.append(["erase", line, name])
                    if self.peek() != ",":
                        break
                    self.pop()
                continue
            if self.peek() == "randomize":
                self.pop()
                result.append(["randomize", line, None if self.peek() in {None, ":", "else", "end"} else self.expression()])
                continue
            if self.peek() == "call":
                self.pop()
                value = self.expression()
                if value[0] not in {"call", "member"}:
                    raise ValueError("Invalid source inline Call")
                result.append(["call", line, value])
                continue
            if self.position + 1 < len(self.tokens) and self.tokens[self.position + 1] == ".":
                result.append(["call", line, self.expression()])
                continue
            if self.peek() == "if":
                self.pop()
                condition = self.expression()
                if self.pop() != "then":
                    raise ValueError("Expected source Then")
                yes = self.inline(line, True)
                no = []
                if self.peek() == "else":
                    self.pop()
                    no = self.inline(line, stop_at_else)
                result.append(["if", line, condition, yes, no])
            else:
                target = self.pop()
                if not re.fullmatch(r"[a-z_][a-z_0-9]*", target):
                    raise ValueError("Invalid source assignment target")
                index = None
                multiple_indexes = False
                if self.peek() == "(":
                    self.pop()
                    indexes = [self.expression()]
                    while self.peek() == ",":
                        self.pop()
                        indexes.append(self.expression())
                    multiple_indexes = len(indexes) > 1
                    index = ["call", "array", indexes] if multiple_indexes else indexes[0]
                    if self.pop() != ")":
                        raise ValueError("Invalid source array target")
                if self.pop() != "=":
                    raise ValueError("Expected source assignment")
                assignment = ["set", line, target, self.expression(), index]
                result.append(assignment + [True] if multiple_indexes else assignment)
        return result


def compile_predicates(lines) -> list:
    """Development-only strict If/assignment compiler, also reusable by F029.

    Input is (one-based source line, code) pairs already excluding IO statements.
    Unsupported syntax fails instead of executing code or silently omitting it.
    """
    program, stack = [], []
    current = program
    for number, code in lines:
        parser = _Parser(_tokens(code))
        tokens = parser.tokens
        if not tokens:
            continue
        if tokens[:2] == ["end", "if"]:
            if not stack or stack[-1][1][0] != "if":
                raise ValueError("Unmatched source End If")
            current = stack.pop()[0]
        elif tokens[:2] == ["select", "case"]:
            parser.pop()
            parser.pop()
            selected = parser.expression()
            if parser.peek() is not None:
                raise ValueError("Unconsumed source Select Case")
            selection = ["select_case", number, selected, [], []]
            current.append(selection)
            stack.append((current, selection))
            current = selection[4]
        elif tokens[:2] == ["end", "select"]:
            if not stack or stack[-1][1][0] != "select_case":
                raise ValueError("Unmatched source End Select")
            current = stack.pop()[0]
        elif tokens[0] == "case":
            if not stack or stack[-1][1][0] != "select_case":
                raise ValueError("Unmatched source Case")
            parser.pop()
            selection = stack[-1][1]
            if parser.peek() == "else":
                parser.pop()
                current = selection[4]
            else:
                tests = []
                while parser.peek() is not None:
                    if parser.peek() == "is":
                        parser.pop()
                        operator = parser.pop()
                        if operator not in {"=", "<>", "<", ">", "<=", ">="}:
                            raise ValueError("Invalid source Case Is")
                        tests.append(["compare", operator, parser.expression()])
                    else:
                        value = parser.expression()
                        if parser.peek() == "to":
                            parser.pop()
                            tests.append(["range", value, parser.expression()])
                        else:
                            tests.append(["equal", value])
                    if parser.peek() != ",":
                        break
                    parser.pop()
                body = []
                selection[3].append([tests, body])
                current = body
            if parser.peek() == ":":
                current.extend(parser.inline(number))
            if parser.peek() is not None:
                raise ValueError("Unconsumed source Case")
        elif tokens[0] == "for":
            parser.pop()
            variable = parser.pop()
            if parser.pop() != "=":
                raise ValueError("Invalid source For")
            start = parser.expression()
            if parser.pop() != "to":
                raise ValueError("Invalid source For bound")
            end = parser.expression()
            step = ["literal", 1]
            if parser.peek() == "step":
                parser.pop()
                step = parser.expression()
            if parser.peek() is not None:
                raise ValueError("Unconsumed source For")
            loop = ["for", number, variable, start, end, step, []]
            current.append(loop)
            stack.append((current, loop))
            current = loop[6]
        elif tokens[0] == "next":
            if not stack or stack[-1][1][0] != "for":
                raise ValueError("Unmatched source Next")
            current = stack.pop()[0]
        elif tokens[0] == "redim":
            parser.pop()
            preserve = parser.peek() == "preserve"
            if preserve:
                parser.pop()
            name = parser.pop()
            if parser.pop() != "(":
                raise ValueError("Invalid source ReDim")
            size = parser.expression()
            if parser.pop() != ")" or parser.peek() is not None:
                raise ValueError("Invalid source ReDim bound")
            current.append(["redim", number, name, size, True] if preserve else ["redim", number, name, size])
        elif tokens[0] == "dim":
            for name in tokens[1:]:
                if name != ",":
                    current.append(["dim", number, name])
        elif tokens[0] == "call":
            parser.pop()
            call = parser.expression()
            if call[0] not in {"call", "member"} or parser.peek() is not None:
                raise ValueError("Invalid source Call")
            current.append(["call", number, call])
        elif tokens == ["else"]:
            current = stack[-1][1][4]
        elif tokens[0] == "elseif":
            parser.pop()
            condition = parser.expression()
            if parser.pop() != "then":
                raise ValueError("Invalid multiline ElseIf")
            branch = ["if", number, condition, [], []]
            stack[-1][1][4].append(branch)
            parent, _ = stack[-1]
            stack[-1] = (parent, branch)
            current = branch[3]
            if parser.peek() is not None:
                current.extend(parser.inline(number))
        elif tokens[0] == "if" and tokens[-1] == "then":
            parser.pop()
            condition = parser.expression()
            if parser.pop() != "then" or parser.peek() is not None:
                raise ValueError("Invalid multiline If")
            branch = ["if", number, condition, [], []]
            current.append(branch)
            stack.append((current, branch))
            current = branch[3]
        else:
            current.extend(parser.inline(number))
            if parser.peek() is not None:
                raise ValueError("Unconsumed source statement")
    if stack:
        raise ValueError("Unclosed source If")
    return program


@dataclass(frozen=True)
class Missing:
    fields: frozenset[str]


@dataclass(frozen=True)
class FunctionResult:
    value: object
    writes: dict
    byref: dict = field(default_factory=dict)
    argument_writes: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SourceProcedure:
    arguments: tuple
    program: list
    local_names: frozenset = frozenset()
    by_value: frozenset = frozenset()
    source_writes: tuple = ()
    on_error_resume_next: bool = False


class _ExitFor(Exception):
    pass


class _ExitProcedure(Exception):
    pass


class _AbortSource(Exception):
    pass


class _ProcedureFailure(Exception):
    pass


class _HaltSource(Exception):
    pass


@dataclass
class SourceRecordset:
    """Provided rows with explicit field order; no provider or DB connection.

    ADO cursor-dependent RecordCount/ordinal columns are unknown unless the
    caller supplies that metadata. GetRows is field-major, as documented by ADO.
    """

    rows: list[dict]
    columns: tuple | None = None
    source: str = "source_row"
    position: int = 0
    record_count: int | None = None
    closed: bool = False

    def field(self, key):
        if self.closed or not 0 <= self.position < len(self.rows):
            raise IndexError("No current source record")
        if type(key) in {int, float}:
            if self.columns is None:
                return Missing(frozenset({self.source + ".ADO_field_order"}))
            if int(key) < 0:
                raise IndexError
            key = self.columns[int(key)]
        lower = str(key).lower()
        values = {str(name).lower(): value for name, value in self.rows[self.position].items()}
        return values.get(lower, Missing(frozenset({self.source + "." + lower})))

    def member(self, name, arguments):
        if self.closed:
            raise ValueError("Source recordset is closed")
        if name == "eof":
            return self.position >= len(self.rows)
        if name == "bof":
            return not self.rows or self.position < 0
        if name == "recordcount":
            return self.record_count if self.record_count is not None else Missing(frozenset({self.source + ".ADO_record_count"}))
        if name == "getrows":
            if self.position < 0 or self.position >= len(self.rows):
                raise IndexError("No current source record")
            count = len(self.rows) - self.position if not arguments or arguments[0] == -1 else int(_number(arguments[0]))
            if count < 0:
                raise ValueError("Invalid source GetRows count")
            if len(arguments) > 1:
                return Missing(frozenset({self.source + ".ADO_bookmark_configuration"}))
            stop = min(len(self.rows), self.position + count)
            if self.columns is None:
                self.position = stop
                return Missing(frozenset({self.source + ".ADO_field_order"}))
            output = []
            start = self.position
            for column in self.columns:
                values = []
                for index in range(start, stop):
                    self.position = index
                    values.append(self.field(column))
                output.append(values)
            self.position = stop
            return output
        if name in {"movenext", "moveprevious", "movefirst", "movelast"}:
            if not self.rows or name == "movenext" and self.position >= len(self.rows) or name == "moveprevious" and self.position < 0:
                raise IndexError("No source record to move")
            self.position = self.position + 1 if name == "movenext" else self.position - 1 if name == "moveprevious" else 0 if name == "movefirst" else len(self.rows) - 1
            return EMPTY
        if name == "close":
            self.closed = True
            return EMPTY
        return Missing(frozenset({self.source + ".ADO_" + name}))


class _Empty:
    def __bool__(self):
        return False


EMPTY = _Empty()


def _number(value):
    if value is EMPTY:
        return 0
    if isinstance(value, bool):
        return -int(value)
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, (datetime, date)):
        moment = value if isinstance(value, datetime) else datetime.combine(value, datetime.min.time())
        return (moment.replace(tzinfo=None) - datetime(1899, 12, 30)).total_seconds() / 86400
    return float(value) if any(char in str(value).lower() for char in ".e") else int(value)


def _string(value):
    if value is EMPTY or value is None:
        return ""
    if isinstance(value, float):
        return "0" if value == 0 else format(value, ".15g")
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def contains_presentation(value):
    """Keep exact internal literals while excluding markup from public evidence."""
    if isinstance(value, str):
        return "@display" in value or ".gif" in value or bool(re.search(r"</?[A-Za-z][A-Za-z0-9]*(?:\s|/?>|$)", value))
    if isinstance(value, (list, tuple)):
        return any(contains_presentation(item) for item in value)
    if isinstance(value, dict):
        return any(contains_presentation(item) for item in value.values())
    return False


def _boolean(value):
    if value is EMPTY or value is None:
        return False
    if isinstance(value, str):
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        return bool(_number(value))
    return bool(value)


def _date_value(value, environment):
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if value is EMPTY or type(value) in {int, float, bool}:
        number = _number(value)
        return datetime(1899, 12, 30) + timedelta(days=math.trunc(number), seconds=abs(number - math.trunc(number)) * 86400)
    text = str(value).strip()
    iso = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})(?:[ T](\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?", text)
    if iso:
        parts = [int(item) if item is not None else 0 for item in iso.groups()]
        return datetime(*parts)
    ordered = re.fullmatch(r"(\d{1,2})[-/](\d{1,2})[-/](\d{2}|\d{4})", text)
    if ordered:
        order = environment.get("__date_order__")
        if order not in {"mdy", "dmy"}:
            return Missing(frozenset({"VBScript.date_order"}))
        first, second, year = map(int, ordered.groups())
        if year < 100:
            pivot = environment.get("__two_digit_year_max__")
            if type(pivot) is not int:
                return Missing(frozenset({"VBScript.TwoDigitYearMax"}))
            year += (pivot // 100 - int(year > pivot % 100)) * 100
        return datetime(year, first if order == "mdy" else second, second if order == "mdy" else first)
    raise ValueError("Unsupported source date value")


def _date_add(interval, number, value):
    number = round(_number(number))
    if interval in {"yyyy", "q", "m"}:
        months = number * (12 if interval == "yyyy" else 3 if interval == "q" else 1)
        year, month = divmod(value.year * 12 + value.month - 1 + months, 12)
        if not 100 <= year <= 9999:
            raise ValueError("Source date out of range")
        return value.replace(year=year, month=month + 1, day=min(value.day, monthrange(year, month + 1)[1]))
    units = {"y": 86400, "d": 86400, "w": 86400, "ww": 604800, "h": 3600, "n": 60, "s": 1}
    return value + timedelta(seconds=number * units[interval])


def _date_diff(interval, first, second, week_start=1):
    if interval == "yyyy":
        return second.year - first.year
    if interval in {"m", "q"}:
        divisor = 3 if interval == "q" else 1
        return (second.year * 12 + second.month - 1) // divisor - (first.year * 12 + first.month - 1) // divisor
    if interval == "w":
        return math.trunc((second.date() - first.date()).days / 7)
    if interval == "ww":
        offset = (week_start + 5) % 7
        return ((second.date().toordinal() - 1 - offset) // 7 - (first.date().toordinal() - 1 - offset) // 7)
    units = {"y": 86400, "d": 86400, "h": 3600, "n": 60, "s": 1}
    origin = datetime(1899, 12, 30)
    return math.floor((second - origin).total_seconds() / units[interval]) - math.floor((first - origin).total_seconds() / units[interval])


def _missing(values):
    fields = frozenset(field for value in values if isinstance(value, Missing) for field in value.fields)
    return Missing(fields) if fields else None


def _hard(node):
    # VBScript hard types direct literals, except Boolean literals (a shipped
    # engine bug). Operators and function return values remain soft Variants.
    # __use is trusted instrumentation inserted by the freezer, not an original
    # VB function call. Its identity observer must preserve the source operand.
    if node[0] == "call" and node[1] == "__use" and len(node[2]) == 2:
        return _hard(node[2][1])
    if node[0] == "literal":
        return not isinstance(node[1], bool)
    if node[0] == "value":
        return node[2]
    if node[0] == "group":
        return _hard(node[1])
    return node[0] == "unary" and node[1] in {"+", "-"} and node[2][0] == "literal" and type(node[2][1]) in {int, float}


def _comparison(operator, left, right, left_hard, right_hard):
    if left is None or right is None:
        return None
    if left is EMPTY or right is EMPTY:
        left, right = (_string(left), _string(right)) if isinstance(left, str) or isinstance(right, str) else (_number(left), _number(right))
    elif isinstance(left, str) != isinstance(right, str):
        string_left = isinstance(left, str)
        string_hard = left_hard if string_left else right_hard
        number_hard = right_hard if string_left else left_hard
        if number_hard:
            left, right = _number(left), _number(right)
        elif string_hard:
            left, right = _string(left), _string(right)
        else:
            # A soft numeric Variant always sorts before a soft string Variant,
            # even when the string contains a perfectly valid numeric value.
            left, right = (1, 0) if string_left else (0, 1)
    elif not isinstance(left, str):
        left, right = _number(left), _number(right)
    return {"=": lambda: left == right, "<>": lambda: left != right, "<": lambda: left < right,
            ">": lambda: left > right, "<=": lambda: left <= right, ">=": lambda: left >= right}[operator]()


def execute(program: list, variables: dict, *, records: dict | None = None, functions: dict | None = None,
            function_writes: dict | None = None, function_argument_writes: dict | None = None,
            rng=None, retain_state=False, on_error_resume_next=False) -> dict:
    """Execute frozen AST with explicit scope-local VB error directives.

    Global and procedure scopes both start with error handling disabled; a
    source On Error statement or explicit caller policy changes only that scope.
    """
    environment = {key.lower(): value for key, value in variables.items()}
    errors = []
    resume_next = bool(on_error_resume_next)
    reads = set()
    callbacks = {key.lower(): function for key, function in (functions or {}).items()}
    generator = rng or environment.get("__rng__") or random.Random()
    environment["__rng__"] = generator
    writes = {name.lower(): tuple(key.lower() for key in fields) for name, fields in (function_writes or {}).items()}
    for name, callback in callbacks.items():
        writes.setdefault(name, tuple(key.lower() for key in getattr(callback, "source_writes", ())))
    argument_writes = {name.lower(): tuple(indexes) for name, indexes in (function_argument_writes or {}).items()}
    for name, callback in callbacks.items():
        default = tuple(i for i in range(len(callback.arguments)) if i not in callback.by_value) if isinstance(callback, SourceProcedure) else ()
        argument_writes.setdefault(name, tuple(getattr(callback, "source_argument_writes", default)))

    def taint_calls(node, missing):
        if not isinstance(node, list) or not node:
            return
        if node[0] == "call":
            for key in writes.get(node[1], ()):
                environment[key] = missing
            for index in argument_writes.get(node[1], ()):
                if index < len(node[2]):
                    assign_reference(node[2][index], missing)
        if node[0] == "member" and node[2] in {"getrows", "movenext", "moveprevious", "movefirst", "movelast", "close"}:
            target = node[1]
            key = "__rs__" if target == ["variable", "rs"] else target[1] if target[0] == "variable" else None
            if key is not None:
                environment[key] = missing
        for child in node:
            if isinstance(child, list):
                taint_calls(child, missing)

    def assign_reference(node, value):
        if node[0] == "variable":
            environment[node[1]] = value
        elif node[0] == "call" and node[1] in environment and isinstance(environment[node[1]], list):
            target = environment[node[1]]
            index_values = [expression(item) for item in node[2]]
            missing = _missing([value, *index_values]) if any(isinstance(item, Missing) for item in index_values) else None
            if missing:
                environment[node[1]] = missing
                return
            indexes = [int(_number(item)) for item in index_values]
            for index in indexes[:-1]:
                target = target[index]
            target[indexes[-1]] = value

    def readonly(value):
        if isinstance(value, dict):
            return MappingProxyType({key: readonly(item) for key, item in value.items()})
        if isinstance(value, (list, tuple)):
            return tuple(readonly(item) for item in value)
        return value

    def expression(node):
        kind = node[0]
        if kind in ("literal", "value"):
            return node[1]
        if kind == "group":
            return expression(node[1])
        if kind == "variable":
            reads.add(node[1])
            if node[1] in ("now", "date", "time") and node[1] not in environment:
                clock = environment.get("__clock__", Missing(frozenset({"source_clock"})))
                if node[1] == "time" and isinstance(clock, datetime):
                    return datetime(1899, 12, 30, clock.hour, clock.minute, clock.second)
                if node[1] == "time" and isinstance(clock, date):
                    return Missing(frozenset({"source_clock.time"}))
                return clock.date() if node[1] == "date" and isinstance(clock, datetime) else clock
            if node[1] == "rs":
                return environment.get("__rs__", Missing(frozenset({"source_row"})))
            if node[1] == "rnd":
                if isinstance(environment.get("__random_state_missing__"), Missing):
                    return environment["__random_state_missing__"]
                value = generator.random()
                environment["__last_rnd__"] = value
                return value
            return environment.get(node[1], EMPTY)
        if kind == "unary":
            value = expression(node[2])
            if isinstance(value, Missing) or value is None:
                return value
            if node[1] == "not":
                return not value if isinstance(value, bool) else ~round(_number(value))
            return -_number(value) if node[1] == "-" else _number(value)
        if kind == "index":
            value = expression(node[1])
            indexes = [expression(index) for index in node[2]]
            missing = _missing([value, *indexes])
            if missing:
                return missing
            for index in indexes:
                index = int(_number(index))
                if index < 0:
                    raise IndexError
                value = value[index]
            return value
        if kind == "member":
            target = expression(node[1])
            arguments = [expression(argument) for argument in node[3]]
            missing = _missing([target, *arguments])
            if missing:
                return missing
            if isinstance(target, dict):
                target = SourceRecordset([target], source=environment.get("__rs_source__", "source_row"))
                if node[1] == ["variable", "rs"]:
                    environment["__rs__"] = target
            if not isinstance(target, SourceRecordset):
                raise TypeError("Source recordset required")
            return target.member(node[2], arguments)
        if kind == "call":
            name, arguments = node[1], [expression(argument) for argument in node[2]]
            callback = callbacks.get(name)
            observer = getattr(callback, "source_observer", None)
            context = {}
            if getattr(callback, "source_context", False):
                keys = getattr(callback, "source_context_keys", None)
                snapshot = environment if keys is None else {key.lower(): environment[key.lower()] for key in keys if key.lower() in environment}
                context = {"source_context": readonly(snapshot)}
            if callable(observer):
                observer(*arguments, **context)
            missing = _missing(arguments)
            if missing and not (isinstance(callback, SourceProcedure) or getattr(callback, "source_accepts_missing", False) or observer is True):
                for key in writes.get(name, ()):
                    environment[key] = missing
                for index in argument_writes.get(name, ()):
                    if index < len(node[2]):
                        assign_reference(node[2][index], missing)
                return missing
            if name not in callbacks and isinstance(environment.get(name), Missing):
                return environment[name]
            if name in callbacks:
                # Callbacks are trusted application implementations of original
                # pure helpers; request parameters never supply Python callables.
                callback = callbacks[name]
                if isinstance(callback, SourceProcedure):
                    local_names = {item.lower() for item in callback.local_names} | {item.lower() for item in callback.arguments} | {name}
                    for global_name in callback.source_writes:
                        environment.setdefault(global_name.lower(), EMPTY)
                    frame = dict(environment)
                    frame.pop("__pending_exit__", None)
                    for local_name in local_names:
                        frame[local_name] = EMPTY
                    if len(arguments) != len(callback.arguments):
                        raise ValueError("Source procedure argument count mismatch")
                    for index, (parameter, argument) in enumerate(zip(callback.arguments, arguments)):
                        # Array arguments passed ByVal receive a Variant array copy.
                        reference = node[2][index]
                        is_reference = reference[0] == "variable" or reference[0] == "call" and reference[1] in environment and isinstance(environment[reference[1]], list)
                        if (index in callback.by_value or not is_reference) and isinstance(argument, list):
                            def clone(value):
                                return [clone(item) for item in value] if isinstance(value, list) else value
                            argument = clone(argument)
                        frame[parameter.lower()] = argument
                    returned = execute(callback.program, frame, records=records, functions=callbacks,
                                       function_writes=writes, function_argument_writes=argument_writes,
                                       rng=generator, retain_state=True, on_error_resume_next=callback.on_error_resume_next)
                    errors.extend(returned["source_errors"])
                    state = returned["state"]
                    environment.update({key: value for key, value in state.items() if key not in local_names and key in environment})
                    for intrinsic in ("__last_rnd__", "__random_state_missing__"):
                        if intrinsic in state:
                            environment[intrinsic] = state[intrinsic]
                        else:
                            environment.pop(intrinsic, None)
                    for index, parameter in enumerate(callback.arguments):
                        if index not in callback.by_value:
                            assign_reference(node[2][index], state[parameter.lower()])
                    if state.get("__source_halted__") is True:
                        environment["__source_halted__"] = True
                        raise _HaltSource
                    if returned.get("aborted"):
                        raise _ProcedureFailure
                    return state.get(name, EMPTY)
                value = callback(*arguments, **context)
                if isinstance(value, FunctionResult):
                    environment.update({key.lower(): item for key, item in value.writes.items()})
                    for index, item in (value.byref | value.argument_writes).items():
                        assign_reference(node[2][index], item)
                    if environment.get("__source_halted__") is True:
                        raise _HaltSource
                    return value.value
                return value
            if name in environment and isinstance(environment[name], (list, tuple)):
                value = environment[name]
                for index in arguments:
                    index = int(_number(index))
                    if index < 0:
                        raise IndexError
                    value = value[index]
                return value
            if name == "rs":
                row = environment.get("__rs__", {})
                if isinstance(row, Missing):
                    return row
                if isinstance(row, SourceRecordset):
                    return row.field(arguments[0])
                if isinstance(row, dict):
                    source = environment.get("__rs_source__", "source_row")
                    return SourceRecordset([row], source=source).field(arguments[0])
                raise TypeError("Source recordset required")
            if name == "request":
                return environment.get("__request__", {}).get(_string(arguments[0]).lower(), "")
            if name in {"cint", "cdate", "cstr"} and arguments and arguments[0] is None:
                raise ValueError("Invalid use of Null")
            if any(item is None for item in arguments) and name not in {"array", "isnumeric", "cstr", "date", "now"}:
                return None
            if name == "int":
                return math.floor(_number(arguments[0]))
            if name in {"abs", "round", "sgn"}:
                number = _number(arguments[0])
                return abs(number) if name == "abs" else (number > 0) - (number < 0) if name == "sgn" else round(number, int(_number(arguments[1])) if len(arguments) > 1 else 0)
            if name == "isnumeric":
                try:
                    return arguments[0] is not None and not isinstance(arguments[0], (date, datetime, bool)) and math.isfinite(_number(arguments[0]))
                except (ValueError, TypeError):
                    return False
            if name in {"ubound", "lbound"}:
                value = arguments[0]
                dimension = int(_number(arguments[1])) if len(arguments) > 1 else 1
                for _ in range(dimension - 1):
                    value = value[0]
                if not isinstance(value, (list, tuple)) or dimension < 1:
                    raise TypeError("Source array required")
                return len(value) - 1 if name == "ubound" else 0
            if name in {"lcase", "ucase", "trim", "ltrim", "rtrim"}:
                value = _string(arguments[0])
                return {"lcase": str.lower, "ucase": str.upper, "trim": str.strip, "ltrim": str.lstrip, "rtrim": str.rstrip}[name](value)
            if name == "instr":
                start = int(_number(arguments[0])) if len(arguments) >= 3 else 1
                haystack, needle = map(_string, arguments[1:3] if len(arguments) >= 3 else arguments[:2])
                if start < 1:
                    raise ValueError("Invalid source InStr start")
                if len(arguments) > 3 and _number(arguments[3]) == 1:
                    haystack, needle = haystack.lower(), needle.lower()
                found = haystack.find(needle, start - 1)
                return found + 1 if found >= 0 else 0
            if name == "chr":
                number = int(_number(arguments[0]))
                if 0 <= number < 128:
                    return chr(number)
                codepage = environment.get("__ansi_codepage__")
                if codepage not in {"cp949", "cp1252"}:
                    return Missing(frozenset({"VBScript.ANSI_codepage"}))
                encoded = (number & 65535).to_bytes(2 if number > 255 or number < 0 else 1, "big")
                return encoded.decode(codepage)
            if name == "rnd":
                if isinstance(environment.get("__random_state_missing__"), Missing):
                    return environment["__random_state_missing__"]
                if arguments and _number(arguments[0]) == 0 and "__last_rnd__" in environment:
                    return environment["__last_rnd__"]
                if arguments and _number(arguments[0]) < 0:
                    generator.seed(_number(arguments[0]))
                value = generator.random()
                environment["__last_rnd__"] = value
                return value
            if name == "cint":
                value = round(_number(arguments[0]))
                if not -32768 <= value <= 32767:
                    raise OverflowError
                return value
            if name == "cstr":
                if arguments[0] is None:
                    raise ValueError("Invalid use of Null")
                return _string(arguments[0])
            if name == "mid":
                start = int(_number(arguments[1])) - 1
                return _string(arguments[0])[start:] if len(arguments) == 2 else _string(arguments[0])[start:start + int(_number(arguments[2]))]
            if name == "left":
                return _string(arguments[0])[:int(_number(arguments[1]))]
            if name == "right":
                return _string(arguments[0])[-int(_number(arguments[1])):] if _number(arguments[1]) else ""
            if name == "len":
                return len(_string(arguments[0]))
            if name == "split":
                return _string(arguments[0]).split(_string(arguments[1]))
            if name == "replace":
                return _string(arguments[0]).replace(_string(arguments[1]), _string(arguments[2]))
            if name == "array":
                return arguments
            if name in ("date", "now", "time"):
                clock = environment.get("__clock__", Missing(frozenset({"source_clock"})))
                if name == "time" and isinstance(clock, datetime):
                    return datetime(1899, 12, 30, clock.hour, clock.minute, clock.second)
                if name == "time" and isinstance(clock, date):
                    return Missing(frozenset({"source_clock.time"}))
                return clock.date() if name == "date" and isinstance(clock, datetime) else clock
            if name in {"cdate", "year", "month", "day", "hour", "minute", "weekday", "dateadd", "datediff", "datepart"}:
                date_args = arguments[2:3] if name == "dateadd" else arguments[1:3] if name == "datediff" else arguments[1:2] if name == "datepart" else arguments[:1]
                dates = [_date_value(value, environment) for value in date_args]
                absent = _missing(dates)
                if absent:
                    return absent
                if name == "cdate":
                    return dates[0]
                if name in {"year", "month", "day", "hour", "minute"}:
                    return getattr(dates[0], name)
                if name == "datepart":
                    interval = _string(arguments[0]).lower()
                    if interval in {"yyyy", "m", "d", "h", "n", "s"}:
                        return getattr(dates[0], {"yyyy": "year", "m": "month", "d": "day", "h": "hour", "n": "minute", "s": "second"}[interval])
                    if interval == "q":
                        return (dates[0].month - 1) // 3 + 1
                    if interval == "y":
                        return dates[0].timetuple().tm_yday
                    first_day = int(_number(arguments[2])) if len(arguments) > 2 else 1
                    if first_day == 0:
                        return Missing(frozenset({"VBScript.system_first_day_of_week"}))
                    if not 1 <= first_day <= 7:
                        raise ValueError("Invalid source first day of week")
                    offset = (first_day + 5) % 7
                    if interval == "w":
                        return (dates[0].weekday() - offset) % 7 + 1
                    if interval == "ww":
                        first_week = int(_number(arguments[3])) if len(arguments) > 3 else 1
                        if first_week == 0:
                            return Missing(frozenset({"VBScript.system_first_week_of_year"}))
                        if first_week not in {1, 2, 3}:
                            raise ValueError("Invalid source first week of year")
                        january = dates[0].replace(month=1, day=1)
                        shift = (january.weekday() - offset) % 7
                        start = january.toordinal() - shift
                        if first_week == 2 and shift > 3 or first_week == 3 and shift > 0:
                            start += 7
                        if dates[0].toordinal() < start:
                            previous = january.replace(year=january.year - 1)
                            previous_shift = (previous.weekday() - offset) % 7
                            start = previous.toordinal() - previous_shift
                            if first_week == 2 and previous_shift > 3 or first_week == 3 and previous_shift > 0:
                                start += 7
                        return (dates[0].toordinal() - start) // 7 + 1
                    raise ValueError("Unsupported source DatePart interval")
                if name == "weekday":
                    first_day = int(_number(arguments[1])) if len(arguments) > 1 else 1
                    if first_day == 0:
                        return Missing(frozenset({"VBScript.system_first_day_of_week"}))
                    if not 1 <= first_day <= 7:
                        raise ValueError("Invalid source first day of week")
                    return (dates[0].weekday() - (first_day + 5) % 7) % 7 + 1
                if name == "dateadd":
                    return _date_add(_string(arguments[0]).lower(), arguments[1], dates[0])
                first_day = int(_number(arguments[3])) if len(arguments) > 3 else 1
                return _date_diff(_string(arguments[0]).lower(), dates[0], dates[1], first_day)
            raise ValueError("Unsupported frozen source function")
        if kind != "binary":
            raise ValueError("Unsupported frozen AST node")
        operator, left, right = node[1], expression(node[2]), expression(node[3])
        missing = _missing((left, right))
        if missing:
            return missing
        if operator == "&":
            return None if left is None and right is None else _string(left) + _string(right)
        if left is None or right is None:
            other = right if left is None else left
            if operator == "and" and other is not None and _number(other) == 0:
                return False if isinstance(other, bool) else 0
            if operator == "or" and other is not None and _number(other) == -1:
                return True if isinstance(other, bool) else -1
            return None
        if operator in ("and", "or"):
            first, second = round(_number(left)), round(_number(right))
            combined = first & second if operator == "and" else first | second
            return bool(combined) if isinstance(left, bool) and isinstance(right, bool) else combined
        if operator in ("=", "<>", "<", ">", "<=", ">="):
            return _comparison(operator, left, right, _hard(node[2]), _hard(node[3]))
        if operator == "+" and isinstance(left, str) and isinstance(right, str):
            return left + right
        left, right = _number(left), _number(right)
        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            return left / right
        if operator == "\\":
            return math.trunc(round(left) / round(right))
        if operator == "mod":
            return round(left) - math.trunc(round(left) / round(right)) * round(right)
        raise ValueError("Unsupported frozen source operator")

    def mark_missing(statements, missing):
        for statement in statements:
            taint_calls(statement, missing)
            if statement[0] == "set":
                environment[statement[2]] = missing
            elif statement[0] == "if":
                mark_missing(statement[3], missing)
                mark_missing(statement[4], missing)
            elif statement[0] == "for":
                environment[statement[2]] = missing
                previous_exit = environment.get("__pending_exit__")
                mark_missing(statement[6], missing)
                pending = environment.get("__pending_exit__")
                if pending and pending[0] == "for":
                    if previous_exit is None:
                        environment.pop("__pending_exit__", None)
                    else:
                        environment["__pending_exit__"] = previous_exit
            elif statement[0] in {"redim", "erase"}:
                environment[statement[2]] = missing
            elif statement[0] == "select":
                environment["__rs__"] = missing
                environment["__rs_source__"] = statement[2]
            elif statement[0] == "randomize":
                environment["__random_state_missing__"] = missing
            elif statement[0] == "exit":
                environment["__pending_exit__"] = (statement[2], missing)
            elif statement[0] == "select_case":
                for _, body in statement[3]:
                    mark_missing(body, missing)
                mark_missing(statement[4], missing)

    def run(statements):
        nonlocal resume_next
        for position, statement in enumerate(statements):
            if environment.get("__source_halted__") is True:
                return
            if "__pending_exit__" in environment:
                mark_missing(statements[position:], environment["__pending_exit__"][1])
                return
            try:
                if statement[0] == "on_error":
                    resume_next = bool(statement[2])
                elif statement[0] == "exit":
                    if statement[2] == "for":
                        raise _ExitFor
                    raise _ExitProcedure
                elif statement[0] == "set":
                    value = expression(statement[3])
                    if statement[4] is None:
                        environment[statement[2]] = value
                    else:
                        if isinstance(environment.get(statement[2]), Missing):
                            continue
                        index_value = expression(statement[4])
                        if isinstance(index_value, Missing):
                            environment[statement[2]] = index_value
                            continue
                        indexes = index_value if len(statement) > 5 and statement[5] else [index_value]
                        target = environment[statement[2]]
                        for offset, item in enumerate(indexes):
                            index = int(_number(item))
                            if index < 0:
                                raise IndexError
                            if offset == len(indexes) - 1:
                                target[index] = value
                            else:
                                target = target[index]
                elif statement[0] == "dim":
                    environment.setdefault(statement[2], EMPTY)
                elif statement[0] == "erase":
                    environment[statement[2]] = EMPTY
                elif statement[0] == "randomize":
                    seed = expression(statement[2]) if statement[2] is not None else None
                    if isinstance(seed, Missing):
                        environment["__random_state_missing__"] = seed
                    else:
                        generator.seed(_number(seed) if seed is not None else None)
                        environment.pop("__last_rnd__", None)
                        environment.pop("__random_state_missing__", None)
                elif statement[0] == "if":
                    condition = expression(statement[2])
                    if isinstance(condition, Missing):
                        mark_missing(statement[3] + statement[4], condition)
                    else:
                        run(statement[3] if _boolean(condition) else statement[4])
                elif statement[0] == "redim":
                    bound = expression(statement[3])
                    if isinstance(bound, Missing):
                        environment[statement[2]] = bound
                        continue
                    size = int(_number(bound))
                    if not 0 <= size <= 10000:
                        raise ValueError("Source array bound exceeds supported scope")
                    values = [EMPTY] * (size + 1)
                    if len(statement) > 4 and statement[4]:
                        previous = environment.get(statement[2], EMPTY)
                        if isinstance(previous, Missing):
                            environment[statement[2]] = previous
                            continue
                        if previous is not EMPTY:
                            if not isinstance(previous, list):
                                raise TypeError("Source array required for Preserve")
                            values[:min(len(previous), len(values))] = previous[:len(values)]
                    environment[statement[2]] = values
                elif statement[0] == "select":
                    # A frozen descriptor selects a supplied, validated row.
                    # This is a dictionary lookup; SQL is never executed.
                    name = statement[2]
                    environment["__rs_source__"] = name
                    environment["__rs__"] = (records or {}).get(name, Missing(frozenset({name})))
                elif statement[0] == "call":
                    expression(statement[2])
                elif statement[0] == "select_case":
                    selected = expression(statement[2])
                    if isinstance(selected, Missing):
                        mark_missing([statement], selected)
                        continue
                    matched = False
                    for tests, body in statement[3]:
                        selected_node = ["value", selected, _hard(statement[2])]
                        for test in tests:
                            if test[0] == "equal":
                                predicate = ["binary", "=", selected_node, test[1]]
                            elif test[0] == "compare":
                                predicate = ["binary", test[1], selected_node, test[2]]
                            else:
                                predicate = ["binary", "and", ["binary", ">=", selected_node, test[1]],
                                             ["binary", "<=", selected_node, test[2]]]
                            condition = expression(predicate)
                            if isinstance(condition, Missing):
                                mark_missing([statement], condition)
                                matched = True
                                break
                            if _boolean(condition):
                                run(body)
                                matched = True
                                break
                        if matched:
                            break
                    if not matched:
                        run(statement[4])
                elif statement[0] == "for":
                    first, last, step = [expression(node) for node in statement[3:6]]
                    missing = _missing((first, last, step))
                    if missing:
                        environment[statement[2]] = missing
                        mark_missing(statement[6], missing)
                        pending = environment.get("__pending_exit__")
                        if pending and pending[0] == "for":
                            environment.pop("__pending_exit__", None)
                        continue
                    first, last, step = _number(first), _number(last), _number(step)
                    if step == 0:
                        raise ValueError("Source loop bound exceeds supported scope")
                    index = first
                    iterations = 0
                    while index <= last if step > 0 else index >= last:
                        iterations += 1
                        if iterations > 10001:
                            raise ValueError("Source loop exceeds supported iteration scope")
                        environment[statement[2]] = index
                        try:
                            run(statement[6])
                        except _ExitFor:
                            index = environment[statement[2]]
                            break
                        if environment.get("__source_halted__") is True:
                            index = environment[statement[2]]
                            break
                        pending = environment.get("__pending_exit__")
                        if pending and pending[0] == "for":
                            environment.pop("__pending_exit__")
                            mark_missing(statement[6], pending[1])
                            environment.pop("__pending_exit__", None)
                            index = pending[1]
                            break
                        if pending:
                            environment[statement[2]] = pending[1]
                            mark_missing(statement[6], pending[1])
                            return
                        control = environment[statement[2]]
                        if isinstance(control, Missing):
                            mark_missing(statement[6], control)
                            index = control
                            break
                        index = _number(control) + step
                    environment[statement[2]] = index
                else:
                    raise ValueError("Unsupported frozen statement")
            except _ProcedureFailure:
                if not resume_next:
                    raise _AbortSource from None
            except (ValueError, TypeError, IndexError, KeyError, OverflowError, ZeroDivisionError) as error:
                errors.append({"line": statement[1], "code": type(error).__name__})
                if not resume_next:
                    raise _AbortSource from None
    aborted = False
    try:
        run(program)
    except _AbortSource:
        aborted = True
    except _ExitProcedure:
        pass
    except _HaltSource:
        pass
    except _ExitFor:
        errors.append({"line": 0, "code": "InvalidExitFor"})
        aborted = True
    missing = {key: sorted(value.fields) for key, value in environment.items() if isinstance(value, Missing)
               and (key in reads or key not in variables)}
    def clean_value(value):
        if value is EMPTY or isinstance(value, Missing):
            return None
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, SourceRecordset):
            return {"recordset": value.source, "closed": value.closed}
        if isinstance(value, (list, tuple)):
            return [clean_value(item) for item in value]
        if isinstance(value, dict):
            return {key: clean_value(item) for key, item in value.items()}
        return value

    clean = {key: clean_value(value) for key, value in environment.items() if not key.startswith("__")}
    result = {"variables": clean, "missing": missing, "source_errors": errors}
    if aborted:
        result["aborted"] = True
    if retain_state:
        result["state"] = environment
    return result


@lru_cache(maxsize=1)
def _program():
    return json.loads((Path(__file__).parent / "data/ported_ziwei_rules.json").read_text("utf-8"))


def calculate_ziwei(*, birth: dict, hour_branch: str, gender: str, current: dict | None = None,
                    annual: dict | None = None, selected_year: int | None = None, source_mm: str | None = None) -> dict:
    """Run source calculations from validated original calendar records only."""
    if not isinstance(hour_branch, str) or hour_branch not in BRANCHES or len(hour_branch) != 1 or gender not in {"male", "female"}:
        raise DomainError("invalid_source_record", "자미두수 원본 시지·성별을 확인하세요.")
    if not isinstance(birth, dict) or birth.get("year_h") not in set(STEMS) or birth.get("year_e") not in set(BRANCHES):
        raise DomainError("invalid_source_record", "자미두수 원본 연간지를 확인하세요.")
    if (STEMS.index(birth["year_h"]) % 2 != BRANCHES.index(birth["year_e"]) % 2
        or type(birth.get("lunar_year")) is not int or not 1881 <= birth["lunar_year"] <= 2050
        or birth.get("lunar_month") not in {f"{i:02d}" for i in range(1, 13)}
        or birth.get("lunar_day") not in {f"{i:02d}" for i in range(1, 31)}):
        raise DomainError("invalid_source_record", "자미두수 원본 음력년·두 자리 월일·연간지 음양을 확인하세요.")
    if selected_year is not None and (type(selected_year) is not int or not 1881 <= selected_year <= 2050):
        raise DomainError("invalid_source_record", "선택 유년은 1881~2050 정수 연도입니다.")
    if source_mm is not None:
        allowed = re.escape(STEMS + BRANCHES)
        if not isinstance(source_mm, str) or not re.fullmatch(rf"\d{{4}}[{allowed}0-9 _~-]{{0,12}}", source_mm) or not 1881 <= int(source_mm[:4]) <= 2050:
            raise DomainError("invalid_source_record", "source_mm은 원본 연도·간지 선택 문자열이어야 합니다.")
        mm_year = int(source_mm[:4])
        if selected_year is not None and selected_year != mm_year:
            raise DomainError("invalid_source_record", "source_mm 연도와 selected_year가 일치해야 합니다.")
    else:
        mm_year = selected_year
    if annual is not None and (mm_year is None or annual.get("umdate") != f"{max(1929, mm_year)}1111" or annual.get("umyear_e") not in set(BRANCHES)):
        raise DomainError("invalid_source_record", "선택 유년의 원본 음력11월11일 행을 확인하세요.")
    variables = {
        "my_year_h": birth["year_h"], "my_year_e": birth["year_e"],
        "lunar_year": birth["lunar_year"], "lunar_month": birth["lunar_month"], "lunar_day": birth["lunar_day"],
        "my_hour_e": hour_branch, "sex": "남" if gender == "male" else "여", "choice2": "", "choice4": "",
        "yangdate": current["no"] if current else Missing(frozenset({"current.no"})),
        "umdate": current["umdate"] if current else Missing(frozenset({"current.umdate"})),
        "umyear_e": current["umyear_e"] if current else Missing(frozenset({"current.umyear_e"})),
        "mm": source_mm if source_mm is not None else str(selected_year) if selected_year is not None else "",
        "annual_umyear_e": annual["umyear_e"] if annual else Missing(frozenset({"annual.umyear_e"})),
        "__rs_source__": "jamidata_02",
    }
    result = execute(_program()["program"], variables)
    presentation = re.compile(r"_disp$|^(?:ary|temp_i|bgcolor)\d*$|^(?:width|height|img_back)$")
    values = {key: value for key, value in result["variables"].items() if not presentation.search(key)
              and not contains_presentation(value)}
    leaves = {key: value for key, value in values.items() if key.startswith("result_14jusung_") or re.fullmatch(r"result_\w+gung", key)}
    slots = {}
    for index, branch in enumerate("寅卯辰巳午未申酉戌亥子丑", 1):
        suffix = f"_{index:02d}"
        slots[branch] = {key[:-3]: value for key, value in values.items() if key.endswith(suffix) and value not in ("", None)
                         and not key.endswith("_disp") and not key.startswith(("bgcolor", "age_"))}
    return {"source": SOURCE, "source_sha256": _program()["source_sha256"],
            "algorithm_complete": True, "slots": slots, "final_leaves": leaves,
            "variables": values, "missing_fields": result["missing"], "source_errors": result["source_errors"],
            "notes": ["原本 On Error Resume Next의 실패 대입은 직전 값을 유지하며 line/code로 기록합니다.",
                      "HTML·이미지 장식은 계산에서 제외하고, 실제 원본 DB의 미제공 값은 미확정 상태로 전파합니다."]}

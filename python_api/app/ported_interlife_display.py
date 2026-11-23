"""CR-012/T-024: full saj u jowha/F029 pure display calculations over source rows."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

from pydantic import Field, StrictInt, StrictStr, model_validator

from app.calendar import KST
from app.errors import DomainError
from app.models import Model
from app.ported_ziwei import Missing, contains_presentation, execute
from app.rules import BRANCHES, STEMS

ROOT = "old/unse/interlife/UNSE_DATA/"


class SourceBirthDayRow(Model):
    no: StrictStr
    number: StrictInt = Field(ge=0)
    day_h: StrictStr
    day_e: StrictStr
    jeolip: StrictStr | StrictInt

    @model_validator(mode="after")
    def validate_row(self):
        if not re.fullmatch(r"\d{8}", self.no):
            raise ValueError("no는 원본 YYYYMMDD 양력 날짜입니다.")
        date(int(self.no[:4]), int(self.no[4:6]), int(self.no[6:]))
        if self.day_h not in set("ABCDEFGHIJ") or self.day_e not in {f"{i:02d}" for i in range(1, 13)}:
            raise ValueError("원본 day_h는 A~J, day_e는 01寅~12丑 코드입니다.")
        value = str(self.jeolip)
        if value not in {"", "0"} and (not re.fullmatch(r"\d{4}", value) or not 0 <= int(value[:2]) <= 23 or not 0 <= int(value[2:]) <= 59):
            raise ValueError("jeolip은 원본 빈 값·0 또는 네 자리 HHMM입니다.")
        return self


class SourceYearMonthRow(Model):
    number: StrictInt = Field(ge=0)
    year_h: StrictStr
    year_e: StrictStr
    month_h: StrictStr
    month_e: StrictStr

    @model_validator(mode="after")
    def validate_codes(self):
        if any(value not in set("ABCDEFGHIJ") for value in (self.year_h, self.month_h)):
            raise ValueError("원본 year_h/month_h는 A~J 코드입니다.")
        if any(value not in {f"{i:02d}" for i in range(1, 13)} for value in (self.year_e, self.month_e)):
            raise ValueError("원본 year_e/month_e는 01寅~12丑 코드입니다.")
        return self


class SourceBirthRows(Model):
    birth: SourceBirthDayRow
    selected: SourceYearMonthRow | None = None


@lru_cache(maxsize=1)
def _rules():
    return json.loads((Path(__file__).parent / "data/ported_interlife_display.json").read_text("utf-8"))


def _assigned(program):
    result = set()
    for node in program:
        if not isinstance(node, list) or not node:
            continue
        if isinstance(node[0], str) and node[0] in {"set", "redim", "for"}:
            result.add(node[2])
        result.update(_assigned(node))
    return result


def _invalid():
    raise DomainError("invalid_source_record", "원본 출생일 행·선택 번호 행·현재 행의 형식과 날짜 대응을 확인하세요.")


def _process(*, birth_datetime: datetime, source_birth_rows=None, source_current_record=None,
             native_result: dict | None = None, profile_only=False) -> dict:
    """Calculate all source blocks; do not substitute another native chart.

    Source row ``number`` remains the original supplied number. It is never
    synthesized from idx or elapsed days. The 2월 previous-number check is run
    by the original predicates before validating the supplied selected row.
    """
    if not isinstance(birth_datetime, datetime) or birth_datetime.tzinfo is None:
        _invalid()
    value = birth_datetime.astimezone(KST)
    if isinstance(source_birth_rows, SourceBirthRows):
        rows = source_birth_rows
    elif source_birth_rows is None:
        rows = None
    else:
        try:
            rows = SourceBirthRows.model_validate(source_birth_rows)
        except ValueError:
            _invalid()
    if rows and rows.birth.no != value.strftime("%Y%m%d"):
        _invalid()
    if source_current_record is not None:
        if hasattr(source_current_record, "model_dump"):
            source_current_record = source_current_record.model_dump()
        try:
            current_no = source_current_record["no"]
            if not isinstance(current_no, str) or not re.fullmatch(r"\d{8}", current_no):
                _invalid()
            clock = date(int(current_no[:4]), int(current_no[4:6]), int(current_no[6:]))
            if (source_current_record.get("umyear_h") is not None and source_current_record.get("umyear_h") not in set(STEMS)) or source_current_record.get("umyear_e") not in set(BRANCHES):
                _invalid()
        except (KeyError, TypeError, ValueError):
            _invalid()
    else:
        clock = Missing(frozenset({"source_current_record.no"}))
    variables = dict(native_result or {})
    variables.update({"solar_year": f"{value.year:04d}", "solar_month": f"{value.month:02d}",
                      "solar_day": f"{value.day:02d}", "request_hour": f"{value.hour:02d}",
                      "request_min": f"{value.minute:02d}", "__clock__": clock})
    for field in ("number", "day_h", "day_e", "jeolip"):
        variables["source_birth_" + field] = getattr(rows.birth, field) if rows else Missing(frozenset({"source_birth_rows.birth." + field}))
    for field in ("year_h", "year_e", "month_h", "month_e"):
        variables["source_selected_" + field] = getattr(rows.selected, field) if rows and rows.selected else Missing(frozenset({"source_birth_rows.selected." + field}))
    for field in ("umyear_h", "umyear_e"):
        variables["source_current_" + field] = source_current_record[field] if source_current_record and source_current_record.get(field) else Missing(frozenset({"source_current_record." + field}))
    rules = _rules()
    natal = execute(rules["programs"]["solve/sajujowha.asp"], variables, retain_state=True)
    if rows and rows.selected and natal["variables"].get("my_number") != rows.selected.number:
        _invalid()
    if profile_only:
        return natal
    display = execute(rules["programs"]["solve/F/F029.asp"], natal["state"], retain_state=False)
    private = {"solar_year", "solar_month", "solar_day", "request_hour", "request_min", "my_ymd_jeolip", "member_hour_min"}
    exports = set().union(*(_assigned(program) for program in rules["programs"].values())) | {"my_age"} | {f"daeun{i}_no" for i in range(1, 11)}
    outputs = {name: item for name, item in display["variables"].items() if name in exports and name not in private
               and not name.startswith(("source_", "__", "my_oheng_")) and not name.endswith(("_hh", "_ee"))
               and not contains_presentation(item)}
    missing = {}
    for stage in (natal, display):
        for key, fields in stage["missing"].items():
            if key not in private and not key.startswith(("source_", "__")):
                missing[key] = sorted(set(missing.get(key, ())) | set(fields))
    source_pillars = {pillar: {field: outputs.get(f"my_{pillar}_{field}")
                               for field in ("h", "e", "h_org", "e_org")}
                      for pillar in ("year", "month", "day", "hour")}
    hidden_stems = {pillar: {f"stem{index}": outputs.get(f"jijanggan_{pillar}{index}0")
                              for index in (1, 2, 3)}
                     for pillar in ("year", "month", "day", "hour")}
    major_pillars = {str(index): {"stem": outputs.get(f"td{index}_daeun_check"),
                                 "branch": outputs.get(f"td{index}_daeun_check_jiji")}
                     for index in range(1, 11)}
    native_keys = {key.lower() for key in (native_result or {})}
    unassigned = [name for name in rules["source_unassigned_names"]
                  if (name == "my_age" or re.fullmatch(r"daeun\d+_no", name)) and name not in native_keys]
    errors = [{"source": ROOT + "solve/sajujowha.asp", **error} for error in natal["source_errors"]]
    errors.extend({"source": ROOT + "solve/F/F029.asp", **error} for error in display["source_errors"])
    return {"algorithm_complete": True, "source_profile": "original-sajujowha-f029-predicates-v1",
            "sources": rules["sources"], "variables": outputs,
            "source_pillars": source_pillars, "hidden_stems": hidden_stems,
            "major_pillars": major_pillars,
            "display_fields": {name: outputs.get(name) for name in rules["display_names"] if name not in private},
            "missing_fields": missing, "source_errors": errors,
            "source_syntax_anomalies": rules["anomalies"], "unassigned_source_inputs": unassigned,
            "native_profile_substituted_for_original_rows": False,
            "notes": ["F029 자체의 모든 For/배열·십신·지장간·운성·대운 표시 분기를 실행하며 원본 k 상태와 마지막 인덱스 누락을 보존합니다.",
                      "미제공 원본 행은 Missing, 원본 // 문법 행과 미할당 입력은 별도 원본 결함으로 구분합니다."]}


def process_display(*, birth_datetime: datetime, source_birth_rows=None, source_current_record=None,
                    native_result: dict | None = None) -> dict:
    """Public display evidence; private birth/clock inputs are never returned."""
    return _process(birth_datetime=birth_datetime, source_birth_rows=source_birth_rows,
                    source_current_record=source_current_record, native_result=native_result)


def process_source_profile(*, birth_datetime: datetime, source_birth_rows=None, source_current_record=None,
                           native_result: dict | None = None) -> dict:
    """Internal native VM state immediately after saj u jowha, before F029.

    This result deliberately retains Missing/Empty and private runtime inputs.
    It must be filtered by the source-profile builder and must never be sent
    directly to an API response, AI request, logs, or persisted user evidence.
    """
    return _process(birth_datetime=birth_datetime, source_birth_rows=source_birth_rows,
                    source_current_record=source_current_record, native_result=native_result,
                    profile_only=True)

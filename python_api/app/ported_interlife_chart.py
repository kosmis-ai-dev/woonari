"""T-024: interlife f_Saju and Ziwei source profiles, with honest partial output.

Only checked-in static tables are loaded. No ASP/DLL is executed. Native,
display-chart and Ziwei predicates are complete implementations of the known
calculations; absent source rows and original source faults remain explicit.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, StrictInt, StrictStr, ValidationError, field_validator, model_validator

from app.calendar import KST, solar_birth
from app.errors import DomainError
from app.models import Birth, Model, SajuResult
from app.ported_interlife_display import SourceBirthRows, process_display, process_source_profile
from app.ported_ziwei import EMPTY, FunctionResult, Missing, calculate_ziwei
from app.service_models import ServiceRequest

DATA = json.loads((Path(__file__).parent / "data/ported_interlife_chart.json").read_text())
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
PALACE_BRANCHES = "寅卯辰巳午未申酉戌亥子丑"
SOURCE = "old/unse/interlife/UNSE_DATA/solve/f_Saju.asp"
ZIWEI_SOURCE = "old/unse/interlife/UNSE_DATA/solve/S_J017_J030_sol.asp"


def _local(value: datetime) -> datetime:
    if value.tzinfo is not None:
        if value.utcoffset() != timedelta(hours=9):
            raise DomainError("invalid_source_record", "원본 절기·생시 레코드는 고정 한국시간 UTC+09:00이어야 합니다.")
        return value.replace(tzinfo=None)
    return value


class SourceTerm(Model):
    number: Annotated[int, Field(strict=True, ge=1, le=24)]
    at: datetime

    @field_validator("at", mode="before")
    @classmethod
    def iso_source_datetime(cls, value):
        if not isinstance(value, datetime) and (
            not isinstance(value, str) or not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:\+09:00)?", value
            )
        ):
            raise ValueError("원본 시각은 4자리 연도의 ISO datetime이어야 합니다.")
        return value

    @field_validator("at")
    @classmethod
    def local_time(cls, value):
        return _local(value)


class SourceYearTerms(Model):
    # This is the source gDIV array's year key, not an inferred date year.
    year: Annotated[int, Field(strict=True, ge=1901, le=2049)]
    terms: Annotated[list[SourceTerm], Field(min_length=24, max_length=24)]

    @model_validator(mode="after")
    def validate_terms(self):
        if [term.number for term in self.terms] != list(range(1, 25)):
            raise ValueError("원본 절기는 1=小寒, 3=立春, ... 24 순서로 24개여야 합니다.")
        dates = [term.at for term in self.terms]
        if any(first >= second for first, second in zip(dates, dates[1:])):
            raise ValueError("원본 절기 날짜는 엄격히 증가해야 합니다.")
        if len({value.year for value in dates}) != 1:
            raise ValueError("한 gDIV 연도 행의 실제 날짜 연도는 같아야 합니다.")
        if any(term.at.month != (term.number + 1) // 2 for term in self.terms):
            raise ValueError("원본 절기 번호는 각 월의 두 절기 순서여야 합니다.")
        return self


class SourceCurrentRecord(Model):
    no: StrictStr
    umdate: StrictStr | None = None
    umyear_e: StrictStr
    umyear_h: StrictStr | None = None

    @field_validator("no")
    @classmethod
    def solar_no(cls, value):
        if not re.fullmatch(r"\d{8}", value):
            raise ValueError("no는 원본 YYYYMMDD 양력 날짜입니다.")
        date(int(value[:4]), int(value[4:6]), int(value[6:]))
        return value

    @field_validator("umdate")
    @classmethod
    def lunar_no(cls, value):
        if value is None:
            return value
        if not re.fullmatch(r"\d{8}", value) or not 1 <= int(value[4:6]) <= 12 or not 1 <= int(value[6:]) <= 30:
            raise ValueError("umdate는 원본 YYYYMMDD 음력 날짜입니다.")
        return value

    @field_validator("umyear_e")
    @classmethod
    def branch(cls, value):
        if value not in BRANCHES or len(value) != 1:
            raise ValueError("umyear_e는 원본 한자 지지 한 글자여야 합니다.")
        return value

    @field_validator("umyear_h")
    @classmethod
    def stem(cls, value):
        if value is not None and (value not in STEMS or len(value) != 1):
            raise ValueError("umyear_h는 원본 한자 천간 한 글자여야 합니다.")
        return value

    @model_validator(mode="after")
    def parity(self):
        if self.umyear_h and STEMS.index(self.umyear_h) % 2 != BRANCHES.index(self.umyear_e) % 2:
            raise ValueError("원본 연간지의 천간·지지 음양이 일치하지 않습니다.")
        return self


class SourceZiweiBirth(Model):
    year_h: StrictStr
    year_e: StrictStr
    lunar_year: Annotated[int, Field(strict=True, ge=1881, le=2050)]
    lunar_month: StrictStr
    lunar_day: StrictStr

    @model_validator(mode="after")
    def validate_birth(self):
        if len(self.year_h) != 1 or self.year_h not in STEMS or len(self.year_e) != 1 or self.year_e not in BRANCHES:
            raise ValueError("year_h/year_e는 원본 한자 천간·지지입니다.")
        if STEMS.index(self.year_h) % 2 != BRANCHES.index(self.year_e) % 2:
            raise ValueError("원본 연간지 음양이 일치하지 않습니다.")
        if self.lunar_month not in {f"{number:02d}" for number in range(1, 13)}:
            raise ValueError("lunar_month는 원본과 같은 01~12 두 자리 문자열입니다.")
        if self.lunar_day not in {f"{number:02d}" for number in range(1, 31)}:
            raise ValueError("lunar_day는 원본과 같은 01~30 두 자리 문자열입니다.")
        return self


class SourceZiweiLeaf(Model):
    palace: StrictStr
    stars: Annotated[StrictStr, Field(min_length=2, max_length=12)]

    @model_validator(mode="after")
    def validate_leaf(self):
        if len(self.palace) != 1 or self.palace not in BRANCHES:
            raise ValueError("palace는 원본 result_*gung 한자 지지입니다.")
        if len(self.stars) not in {2, 4, 6, 8, 12} or not self.stars.isalpha():
            raise ValueError("stars는 원본 helper가 처리하는 2/4/6/8/12글자 별 표기입니다.")
        return self


class SourceDisplayState(Model):
    my_age: Annotated[int, Field(strict=True, ge=0, le=200)] | None = None
    daeun1_no: Annotated[int, Field(strict=True, ge=0, le=200)] | None = None
    daeun2_no: Annotated[int, Field(strict=True, ge=0, le=200)] | None = None
    daeun3_no: Annotated[int, Field(strict=True, ge=0, le=200)] | None = None
    daeun4_no: Annotated[int, Field(strict=True, ge=0, le=200)] | None = None
    daeun5_no: Annotated[int, Field(strict=True, ge=0, le=200)] | None = None
    daeun6_no: Annotated[int, Field(strict=True, ge=0, le=200)] | None = None
    daeun7_no: Annotated[int, Field(strict=True, ge=0, le=200)] | None = None
    daeun8_no: Annotated[int, Field(strict=True, ge=0, le=200)] | None = None
    daeun9_no: Annotated[int, Field(strict=True, ge=0, le=200)] | None = None
    daeun10_no: Annotated[int, Field(strict=True, ge=0, le=200)] | None = None


class SourceNativeRequestDate(Model):
    year: StrictInt | StrictStr
    month: StrictInt | StrictStr
    day: StrictInt | StrictStr

    @model_validator(mode="after")
    def numeric_source_tokens(self):
        for name, minimum, maximum, width in (("year", 1881, 2050, 4), ("month", 1, 12, 2), ("day", 1, 31, 2)):
            item = getattr(self, name)
            if isinstance(item, str) and not re.fullmatch(rf"[0-9]{{1,{width}}}", item):
                raise ValueError("원본 날짜 토큰은 허용 길이의 숫자 문자열 또는 정수여야 합니다.")
            if not minimum <= int(item) <= maximum:
                raise ValueError("원본 날짜 토큰의 범위를 확인하세요.")
        return self


class SourceAnnualRecord(Model):
    umdate: Annotated[StrictStr, Field(pattern=r"^\d{4}1111$")]
    umyear_e: StrictStr

    @field_validator("umyear_e")
    @classmethod
    def branch(cls, value):
        if len(value) != 1 or value not in BRANCHES:
            raise ValueError("유년 행의 umyear_e는 원본 한자 지지입니다.")
        return value


_HELP = {
    "source_solunar": "선택: 원본 saju_made swap 전 달력 코드 1=평달 음력,2=양력,3=윤달. 원본의 solunar 할당이 확인되지 않았으므로 전체 native 실행 시 명시하며 Birth의 달력과 일치해야 합니다.",
    "source_two_digit_year_max": "선택: 원본 CDate 서버의 TwoDigitYearMax(예: 2029)를 명시합니다. 보관 div24.dat의 두 자리 연도를 prefix 연도로 조용히 바꾸지 않습니다.",
    "source_terms": "선택: [{year:원본 gDIV 배열 연도키, terms:[{number:1,at:4자리 ISO 한국시간}, ...24]}]. 원본 1=小寒,3=立春이며 출생 연도와 필요한 전/후년 행을 제공합니다. pivot 입력과 동시 사용하지 않습니다.",
    "source_native_request_date": "선택: b_saju_Click 호출 직전 {year,month,day}의 실제 정수/숫자문자열 토큰. Birth의 숫자 날짜와 일치해야 합니다. 생략하면 정수 인자 프로필이며, 윤달 파일의 문자열 키 비교에서 앞자리0을 임의 제거하지 않습니다.",
    "source_leap_mismatch_policy": "선택: reject(기본) 또는 original_regular_fallback(조사용). Sun_Value=3의 원본 YunDat 키가 일치하지 않으면 원본은 평달 gf_Lun2Sun으로 진행합니다. 조사 모드는 그 값을 계산하지만 요청 윤달과 다른 실행이므로 검증 경고/AI 차단을 유지합니다.",
    "source_current_record": "선택: 원본 mansedata 현재 행 {no:YYYYMMDD,umdate:YYYYMMDD,umyear_h:한자천간,umyear_e:한자지지}. umyear 필드를 제공 tb_manse에서 추측하지 않습니다.",
    "source_birth_rows": "선택: 원본 조회행 {birth:{no,number,day_h:A~J,day_e:01寅~12丑,jeolip},selected:{number,year_h/e,month_h/e}}. 선택 번호는 2월 절입 분기에 따라 원본 number 또는 number-1이어야 합니다. idx를 쓰지 않습니다.",
    "source_state": "선택: 원본 외부 상태 {my_age,daeun1_no,...daeun10_no}. 미할당 값을 출생 나이/대운 수로 조용히 채우지 않습니다.",
    "server_date": "선택: 원본 Date()를 재현할 YYYY-MM-DD. 생략하면 한국시간 오늘이며 source_current_record.no와 일치해야 합니다."
}
_LIMITS = [
    "원본 f_Saju의 30분 보정·보정시각 연주/보정전 월주 비교·23시 익일 일주를 별도 구현합니다. dotong을 대입하지 않습니다.",
    "div24.dat은 보관되어 있지만 두 자리 CDate 해석 및 2050년 loader 중단을 확인해야 합니다.",
    "f_Saju/find_yong/saju_made·F029/sajujowha·자미 순수 분기는 Python/정적 자료로 준비했으며 실제 원본 행·입력 상태·서버 달력 설정의 검증과 구분합니다."
]
SERVICES = {}
for _sid in ("interlife-free-11", "interlife-manse-1", "interlife-jum-1"):
    _help = dict(_HELP)
    if _sid == "interlife-jum-1":
        _help = {key: _help[key] for key in ("source_current_record", "source_birth_rows", "server_date")}
        _help.update({
            "source_ziwei_birth": "선택: 원본 입력 배열 {year_h,year_e,lunar_year,lunar_month:두자리,lunar_day:두자리}. 음력 월·일과 연간지를 임의 합성하지 않습니다.",
            "source_selected_year": "선택: 유년 조회 연도(1881~2050). 원본의 1929 이전 clamp를 보존합니다.",
            "source_mm": "선택: 원본 대한/유년 선택값 mm의 문자열. 4자리 연도와 원본 코드 조합을 그대로 재현합니다. source_selected_year를 함께 주면 연도가 일치해야 합니다.",
            "source_annual_record": "선택: 선택 유년의 원본 mansedata 행 {umdate:YYYY1111,umyear_e:한자지지}. 선택하지 않은 유년의 자료는 요구하지 않습니다."
        })
    SERVICES[_sid] = {
        "name": "자미두수" if _sid.endswith("jum-1") else "사주명식",
        "requires_birth": True,
        "requires_partner": False,
        "uses_saju": False,
        "example_parameters": {},
        "parameter_help": _help,
        "ready": False,
        "algorithm_complete": True,
        "calculation_only": _sid != "interlife-jum-1",
        "source_limits": (["자미의 주성·등급·사화·보조성·대한·유년·차성안궁·최종 별/궁과 14개 원본 selector의 모든 알려진 분기를 구현했습니다.",
                           "실제 원본 연간지·음력 월일·현재 행을 다른 명식으로 대체하지 않습니다. 조건부 유년 행과 제목 분류는 실제 도달 경로에만 요구합니다.",
                           "typed 요청 행은 계산 검증용이며 신뢰된 서버 자료 연결 전에는 최종 AI를 허용하지 않습니다."] if _sid == "interlife-jum-1" else _LIMITS + [
                               "F029는 원본 명식 표시 계산전용입니다. 원본 // 문법 이상과 미할당 외부 나이·대운 상태는 DB 누락과 구분합니다."]),
        "required_source_fields": (["source_ziwei_birth.{year_h,year_e,lunar_year,lunar_month,lunar_day} 또는 원본 출생 선택 행의 연간지/기본 음력 날짜",
                                    "source_current_record.{no,umdate,umyear_h?,umyear_e}"] if _sid == "interlife-jum-1" else [
                                        "source_birth_rows.birth.{no,number,day_h,day_e,jeolip}",
                                        "source_birth_rows.selected.{number,year_h,year_e,month_h,month_e}",
                                        "source_current_record.{no,umyear_h,umyear_e}",
                                        "source_state.{my_age,daeun1_no..daeun10_no}; 원본에 할당문 없는 외부 입력"]),
        "conditional_source_fields": (["선택 유년의 source_annual_record.{umdate:YYYY1111,umyear_e}", "실제 도달한 jamidata_02.gung/*_title 분류"] if _sid == "interlife-jum-1" else [
                                          "선택적 native 비교만 source_solunar + 검증한 CDate pivot 또는 source_terms"]),
        "source_scope_truth": "원본에 존재하는 활성 순수 계산과 후처리 분기는 모두 Python/정적 자료로 구현했습니다. 기본 source_required는 실제 자료·원본 실행 상태·신뢰 조건이며 미이식 코드나 알고리즘 길이를 뜻하지 않습니다.",
        "source": ZIWEI_SOURCE if _sid.endswith("jum-1") else "old/unse/interlife/UNSE_DATA/solve/F/F029.asp"
    }


def _one_based(value: int, count: int) -> int:
    return (value - 1) % count + 1


def _pillar(stem: int, branch: int) -> dict:
    return {"stem_index": stem, "branch_index": branch, "stem": STEMS[stem - 1], "branch": BRANCHES[branch - 1], "hanja": STEMS[stem - 1] + BRANCHES[branch - 1]}


def source_gapja_number(stem: int, branch: int) -> int:
    """f_Cal_GapJa60:841-856, with source signed Mod and one-based output."""
    if not 1 <= stem <= 10 or not 1 <= branch <= 12 or stem % 2 != branch % 2:
        raise DomainError("invalid_source_record", "원본 간지의 1-based 천간·지지 코드와 음양을 확인해 주세요.")
    compared = branch + 10 if stem >= branch else branch
    number = 10 - (compared - stem)
    remainder = number % 10 if number >= 0 else -(abs(number) % 10)
    return remainder * 6 + branch


def source_day_hour(solar_datetime: datetime) -> dict:
    """f_Saju:3096-3179. Clock shift and Zi-hour day change are source rules."""
    value = _local(solar_datetime)
    corrected = value - timedelta(minutes=30)
    days = (corrected.date() - date(1901, 1, 1)).days
    stem, branch = _one_based(days + 6, 10), _one_based(days + 4, 12)
    hour_branch = (corrected.hour + 1) // 2 + 1
    late_zi = corrected.hour == 23
    if late_zi:
        stem, branch = _one_based(stem + 1, 10), _one_based(branch + 1, 12)
        hour_branch = 1
    hour_stem = _one_based((stem % 5) * 2 + 8 + hour_branch, 10)
    return {
        "profile": "interlife-b_saju-source-v1",
        "source": SOURCE + ":3096-3179",
        "time_correction_minutes": -30,
        "corrected_date_shift_days": (corrected.date() - value.date()).days,
        "corrected_hour": corrected.hour,
        "corrected_minute": corrected.minute,
        "late_zi_advance": late_zi,
        "pillars": {"day": _pillar(stem, branch), "hour": _pillar(hour_stem, hour_branch)}
    }


def source_natal(solar_datetime: datetime, terms_by_year: dict[int, list[datetime]]) -> dict:
    """f_Saju:3103-3130 compares year at shifted time, month at civil time."""
    value = _local(solar_datetime)
    result = source_day_hour(value)
    corrected = value - timedelta(minutes=30)
    terms = terms_by_year.get(corrected.year)
    if terms is None:
        raise DomainError("source_terms_required", "보정시각 연도의 원본 gDIV 24절기 행이 필요합니다.")
    if len(terms) != 24 or any(not isinstance(term, datetime) for term in terms):
        raise DomainError("invalid_source_record", "gDIV는 원본 순서의 datetime 24개여야 합니다.")
    terms = [_local(term) for term in terms]
    if any(first >= second for first, second in zip(terms, terms[1:])):
        raise DomainError("invalid_source_record", "원본 절기 24개의 시각 순서를 확인해 주세요.")
    year = corrected.year - int(corrected < terms[2])
    year_stem = _one_based(year - 1900 + 7, 10)
    year_branch = _one_based(year - 1900 + 1, 12)
    count = next((index for index, term in enumerate(terms, 1) if term > value), 25)
    month_branch = _one_based(count // 2 + 1, 12)
    offset = 8 if month_branch not in {1, 2} else 0
    month_stem = _one_based((year_stem % 5) * 2 + offset + month_branch, 10)
    result["pillars"].update(year=_pillar(year_stem, year_branch), month=_pillar(month_stem, month_branch))
    result["saju_one_based_indices"] = {name: source_gapja_number(pillar["stem_index"], pillar["branch_index"]) for name, pillar in result["pillars"].items()}
    result.update({"source_term_year_key": corrected.year, "year_comparison": "corrected_datetime vs term3", "month_comparison": "unshifted_birth vs corrected-year gDIV array", "month_scan_exit_index": count, "term_date_year_matches_array_key": all(term.year == corrected.year for term in terms)})
    return result


@lru_cache(maxsize=8)
def bundled_source_terms(two_digit_year_max: int | None) -> dict[int, list[datetime]]:
    """Decode source CDate only with an explicit century policy, never prefix repair."""
    result: dict[int, list[datetime]] = {}
    ambiguous_years = set()
    for year, number, text in DATA["term_rows"]:
        if not 1881 < year < 2050:
            break  # init_gDIV_Load:72-74 exits at the first invalid year.
        match = re.fullmatch(r"(\d{2}|\d{4})-(\d{2})-(\d{2})(?:\s+(오전|오후)\s+(\d{1,2}):(\d{2}):(\d{2}))?", text)
        if match is None:
            raise DomainError("source_term_format_unverified", "보관 절기의 원본 CDate 문자열 형식을 확인해야 합니다.")
        yy, mm, dd, meridiem, hh, minute, second = match.groups()
        if len(yy) == 2:
            if two_digit_year_max is None:
                ambiguous_years.add(year)
                continue
            date_year = two_digit_year_max // 100 * 100 + int(yy)
            if date_year > two_digit_year_max:
                date_year -= 100
        else:
            date_year = int(yy)
        hour = int(hh or 0)
        if meridiem:
            hour = hour % 12 + (12 if meridiem == "오후" else 0)
        parsed = datetime(date_year, int(mm), int(dd), hour, int(minute or 0), int(second or 0))
        result.setdefault(year, []).append(parsed)
    return {year: rows for year, rows in result.items() if year not in ambiguous_years and len(rows) == 24}


def source_major_luck(solar_datetime: datetime, gender: str, natal: dict, terms_by_year: dict[int, list[datetime]], reference_year: int | None = None) -> dict:
    """Port ten source major-luck pairs and its OLE-date start-number arithmetic."""
    value = _local(solar_datetime)
    year = value.year
    terms = terms_by_year.get(year)
    if terms is None:
        raise DomainError("source_terms_required", "대운에 쓰는 보정 전 출생연도 gDIV 행이 필요합니다.")
    if value == terms[-1]:
        raise DomainError("source_last_term_equality_unverified", "원본 fi_Pre_Div24는 마지막 절기와 정확히 같은 시각에 반환값이 미할당됩니다. 원본 실행 대조가 필요합니다.")
    previous_index = 24 if value < terms[0] else max(index for index, term in enumerate(terms, 1) if term <= value)
    odd = previous_index - int(previous_index % 2 == 0)
    sex = 1 if gender == "male" else 2
    forward = natal["pillars"]["year"]["stem_index"] % 2 == sex % 2
    if odd == 23:
        term_year = year if value < terms[0] else year + 1
        if not forward:
            term_year = year if value > terms[22] else year - 1
        term_number = 1 if forward else 23
    else:
        term_year, term_number = year, odd + 2 if forward else odd
    if term_year not in terms_by_year:
        raise DomainError("source_terms_required", "대운 경계에 필요한 원본 인접연도 gDIV 행이 없습니다.")
    boundary = terms_by_year[term_year][term_number - 1]
    duration = boundary - value if forward else value - boundary
    if duration.total_seconds() < 0:
        raise DomainError("source_term_century_order_unverified", "명시한 원본 CDate 연도 해석으로 절기·생시 순서가 역전됩니다. 원본 서버 결과 대조가 필요합니다.")
    # VB Year/Day/Hour(Double date difference) use the OLE epoch 1899-12-30.
    ole = datetime(1899, 12, 30) + duration
    days = 0 if ole.year <= 1899 else ole.day
    hours = ole.hour / 2
    start = round((days * 12 + hours + 18) / 36 + 0.000001)
    month = natal["pillars"]["month"]
    step = 1 if forward else -1
    pairs = [
        {"sequence": number, "start_number": start + (number - 1) * 10, **_pillar(_one_based(month["stem_index"] + step * number, 10), _one_based(month["branch_index"] + step * number, 12))}
        for number in range(1, 11)
    ]
    hour_gap = boundary.replace(minute=0, second=0, microsecond=0) - value.replace(minute=0, second=0, microsecond=0)
    date_diff_hours = hour_gap.days * 24 + hour_gap.seconds // 3600
    if not forward:
        date_diff_hours = -date_diff_hours
    highlight = 0
    if reference_year is not None:
        age = reference_year - value.year + 1
        for number in range(10, 0, -1):
            began = start + (number - 1) * 10
            if began < age and age - began <= 10:
                highlight = (number - 8) * -1
                break
    return {"source": SOURCE + ":3203-3264,3395-3488", "direction": "forward" if forward else "backward", "boundary": boundary.isoformat(), "boundary_term_number": term_number, "boundary_array_year": term_year, "elapsed_days": duration.total_seconds() / 86400, "ole_date_day_component": days, "ole_date_half_hour_component": hours, "source_daeunsu": start, "source_day2_hours_over_72": date_diff_hours / 72, "source_highlight_number": highlight, "pairs": pairs, "returned_first_eight": pairs[:8]}


def source_ziwei_placement(birth: SourceZiweiBirth, hour_branch: str) -> dict:
    """Literal source tables through the fourteen principal-star placements."""
    if hour_branch not in BRANCHES or len(hour_branch) != 1:
        raise DomainError("invalid_source_record", "자미 원본 시지는 한자 지지여야 합니다.")
    slots = DATA["ziwei_ming_body"][hour_branch][birth.lunar_month]
    palaces = dict(DATA["ziwei_palace_ganji"][birth.year_h])
    life = str(slots["life"])
    names = dict(DATA["ziwei_palace_names"][life])
    names[life] = "命"
    group = DATA["ziwei_napum"][palaces[life]]
    jami = DATA["ziwei_jami_positions"][group][birth.lunar_day]
    cheanbu = DATA["ziwei_cheanbu_positions"][jami - 1]
    stars = {"jami": {"position": jami, "label": "자미"}, "cheanbu": {"position": cheanbu, "label": "천부"}}
    stars.update(deepcopy_dict(DATA["ziwei_star_positions"]["jami"][str(jami)]))
    stars.update(deepcopy_dict(DATA["ziwei_star_positions"]["cheanbu"][str(cheanbu)]))
    return {"source": ZIWEI_SOURCE + ":268-2246", "source_inputs": "explicit original year_h/e and padded lunar month/day", "life_palace_position": slots["life"], "body_palace_position": slots["body"], "palace_ganji": palaces, "palace_names": names, "myung_guk": group, "principal_stars": stars, "star_grading_and_transformations_applied": False}


def deepcopy_dict(value: dict) -> dict:
    return {key: dict(item) for key, item in value.items()}


def source_star_key(stars: str) -> str:
    """J017..J030 literal Mid/Len dispatch, including repeated chene bindings."""
    if len(stars) in {2, 4, 6}:
        return stars
    if len(stars) == 12:
        return stars[:6]
    if len(stars) == 8:
        return stars[:6] if stars[4] in "과록기권" else stars[4:10]
    return ""  # Unhandled source Len leaves re_14jusung_* at VB Empty.


def source_solar_to_lunar(value: date) -> dict:
    """gf_Sun2Lun:735-830, including its explicit DT(0..162) range."""
    rows = [DATA["source_lunar_table"][str(year)] for year in range(1881, 2044)]
    totals = [sum(28 + int(code) if int(code) <= 2 else 26 + int(code) for code in row if code != "0") for row in rows]
    remaining = value.toordinal() - date(1881, 1, 30).toordinal() + 1
    if remaining < 1:
        raise DomainError("source_lunar_calendar_range", "원본 gf_Sun2Lun의 시작일 이전입니다.")
    index = 0
    while index < len(rows) and remaining > totals[index]:
        remaining -= totals[index]
        index += 1
    if index == len(rows):
        raise DomainError("source_lunar_calendar_range", "원본 gf_Sun2Lun은 DT 1881~2043년만 계산합니다. 이후 날짜의 원본 반환은 검증해야 합니다.")
    month = 0
    for code in rows[index]:
        number = int(code)
        if number == 0:
            break
        if number <= 2:
            month += 1
        length = number + (28 if number <= 2 else 26)
        if remaining <= length:
            return {"year": index + 1881, "month": month, "day": remaining, "leap_month": number > 2}
        remaining -= length
    raise DomainError("source_lunar_calendar_unverified", "원본 음력 월별 일수의 경계를 확인해야 합니다.")


def source_lunar_to_solar(year: int, month: int, day: int) -> dict:
    """gf_Lun2Sun:607-720. Preserve DateSerial normalization of source day=0."""
    if str(year) not in DATA["source_lunar_table"] or not 1 <= month <= 12:
        raise DomainError("source_lunar_calendar_range", "원본 suntolun.dat의 1881~2050년 월 범위를 확인해 주세요.")
    total = 0
    for previous in range(1881, year):
        row = DATA["source_lunar_table"][str(previous)]
        total += sum(int(code) for code in row) + (336 if row[12] == "0" else 362)
    row = DATA["source_lunar_table"][str(year)]
    target, position = month - 1, -1
    while True:
        position += 1
        if position >= len(row) or row[position] == "0":
            raise DomainError("source_lunar_calendar_unverified", "원본 음력 월 배열의 경계를 확인해야 합니다.")
        number = int(row[position])
        if number > 2:
            total += 26 + number
            target += 1
        elif position == target:
            if not 1 <= day <= 28 + number:
                raise DomainError("invalid_source_lunar_date", "원본 평달 배열에 없는 음력 날짜입니다.")
            break
        else:
            total += 28 + number
    total += day + 29
    solar_year = 1881
    while True:
        leap = solar_year % 400 == 0 or solar_year % 100 != 0 and solar_year % 4 == 0
        length = 366 if leap else 365
        if total < length:  # Source uses <, not <=.
            break
        total -= length
        solar_year += 1
    lengths = [31, length - 337, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    solar_month = 1
    while total > lengths[solar_month - 1]:
        total -= lengths[solar_month - 1]
        solar_month += 1
    normalized = date(solar_year, solar_month, 1) + timedelta(days=total - 1)
    return {"solar_date": normalized, "raw_year": solar_year, "raw_month": solar_month, "raw_day": total, "source_day_zero_normalized": total == 0}


def native_birth(birth: Birth, source_solunar: int, source_native_request_date: SourceNativeRequestDate | dict | None = None,
                 source_leap_mismatch_policy: str = "reject") -> tuple[datetime, dict]:
    """saju_made:8-20 input codes: 2->native solar, 1->lunar, 3->YunDat."""
    if type(source_solunar) is not int or source_solunar not in {1, 2, 3}:
        raise DomainError("invalid_service_parameters", "source_solunar는 원본 swap 전 코드 1(평달 음력), 2(양력), 3(윤달)입니다.")
    expected = 2 if birth.calendar == "solar" else 3 if birth.leap_month else 1
    if source_solunar != expected:
        raise DomainError("source_calendar_binding_mismatch", "Birth의 양력·음력·윤달과 명시한 원본 source_solunar가 다릅니다.")
    if not isinstance(source_leap_mismatch_policy, str) or source_leap_mismatch_policy not in {"reject", "original_regular_fallback"}:
        raise DomainError("invalid_service_parameters", "source_leap_mismatch_policy는 reject 또는 original_regular_fallback입니다.")
    tokens = _validated(SourceNativeRequestDate, source_native_request_date) if source_native_request_date is not None else None
    if tokens and (int(tokens.year), int(tokens.month), int(tokens.day)) != (birth.year, birth.month, birth.day):
        raise DomainError("source_record_date_mismatch", "원본 native 호출 토큰의 숫자 날짜와 Birth가 다릅니다.")
    if source_solunar == 2:
        solar = date(birth.year, birth.month, birth.day)
        lunar = source_solar_to_lunar(solar)
    elif source_solunar == 3:
        canonical = f"{birth.year}/{birth.month}/{birth.day}"
        key = "/".join(str(getattr(tokens, part)) for part in ("year", "month", "day")) if tokens else canonical
        reason = None
        if key != canonical and key not in DATA["source_leap_dates"] and (
            canonical in DATA["source_leap_dates"] or any(row.get("input_key") == canonical for row in DATA["source_malformed_leap_rows"])
        ):
            reason = ("source_leap_request_padding_unmatched", "원본 윤달 조회는 문자열 키를 정확히 비교합니다. 호출 토큰의 앞자리0 때문에 파일 키가 일치하지 않으며 자동 정규화하지 않습니다.")
        elif any(row.get("input_key") == key for row in DATA["source_malformed_leap_rows"]):
            reason = ("source_leap_record_malformed", "원본 YunDat.dat의 이 날짜 행에 구분자 오류가 있어 임의 복구하지 않습니다.")
        raw = DATA["source_leap_dates"].get(key)
        if raw is None and reason is None:
            reason = ("source_leap_record_missing", "원본 YunDat.dat에서 이 윤달 날짜의 행을 확인할 수 없습니다.")
        if reason:
            if source_leap_mismatch_policy == "reject":
                raise DomainError(*reason)
            # Source 2914 never sets Opt_Cal_Sun_Value when the raw key does
            # not match. Its Empty state takes 3018..3036's ordinary path.
            # gf_Lun2Sun's fourth argument is output weekday, not leap mode.
            solar = source_lunar_to_solar(birth.year, birth.month, birth.day)["solar_date"]
            lunar = {"year": birth.year, "month": birth.month, "day": birth.day, "leap_month": False,
                     "source_effective_calendar": "original_regular_lunar_fallback", "source_leap_lookup_matched": False,
                     "source_lookup_reason": reason[0], "requested_leap_month": True}
        else:
            year, month, day = map(int, raw.split("/"))
            solar = date(year, month, day)
            lunar = source_solar_to_lunar(solar)
    else:
        conversion = source_lunar_to_solar(birth.year, birth.month, birth.day)
        solar = conversion["solar_date"]
        lunar = {"year": birth.year, "month": birth.month, "day": birth.day, "leap_month": False}
    return datetime(solar.year, solar.month, solar.day, birth.hour, birth.minute), lunar


def source_birth_dates(service_id: str, request: ServiceRequest) -> list[date]:
    """Use native source conversion only when its otherwise-unbound code is explicit."""
    if request.birth is None:
        return []
    binding = request.parameters.get("source_solunar")
    if binding is None:
        if request.birth.calendar == "solar":
            return [date(request.birth.year, request.birth.month, request.birth.day)]
        return [solar_birth(request.birth).date()]
    return [native_birth(request.birth, binding, request.parameters.get("source_native_request_date"),
                         request.parameters.get("source_leap_mismatch_policy", "reject"))[0].date()]


def source_buffer_hour_branch(hour: int, minute: int) -> str:
    """sajujowha:201-219, independent of the native year/month/day profile."""
    hhmm = hour * 100 + minute
    if hhmm < 130 or hhmm >= 2330:
        return "子"
    return BRANCHES[(hour * 60 + minute - 90) // 120 + 1]


def source_ten_god(target: str, day_stem: str, branch: bool = False) -> str:
    """F_re_yukchin's exact polarity/representative-stem mapping."""
    other = "癸己甲乙戊丙丁己庚辛戊壬"[BRANCHES.index(target)] if branch else target
    own_index, other_index = STEMS.index(day_stem), STEMS.index(other)
    same = own_index % 2 == other_index % 2
    relation = (other_index // 2 - own_index // 2) % 5
    labels = {
        0: ("比肩", "劫財"), 1: ("食神", "傷官"), 2: ("偏財", "正財"),
        3: ("偏官", "正官"), 4: ("偏印", "正印")
    }
    return labels[relation][0 if same else 1]


def source_find_yong(natal: dict) -> dict:
    """All find_yong decisions: frozen 25*126 Y/H matrix and source-order loops."""
    pillars = natal["pillars"]
    day = pillars["day"]["stem"]
    ordered = [
        source_ten_god(pillars["year"]["stem"], day),
        source_ten_god(pillars["year"]["branch"], day, True),
        source_ten_god(pillars["month"]["stem"], day),
        source_ten_god(pillars["month"]["branch"], day, True),
        source_ten_god(pillars["day"]["branch"], day, True),
        source_ten_god(pillars["hour"]["stem"], day),
        source_ten_god(pillars["hour"]["branch"], day, True)
    ]
    groups = ("偏印正印", "比肩劫財", "食神傷官", "偏財正財", "偏官正官")
    def group(god):
        return next(index for index, names in enumerate(groups) if god in names)
    counted = [ordered[index] for index in (0, 1, 2, 5, 6)]
    counts = [sum(group(god) == index for god in counted) for index in range(5)]
    shape = group(ordered[3]) * 5 + group(ordered[4]) + 1
    key = "|".join(map(str, (shape, *counts)))
    favorable, supporting = DATA["find_yong"]["decision_matrix"][key]
    hostile = (favorable + 2) % 5 + 1
    opposing = (supporting + 2) % 5 + 1
    neutral = 15 - favorable - supporting - hostile - opposing
    relative = [neutral, opposing, hostile, supporting, favorable]
    absolute = ["木火土金水"[(STEMS.index(day) // 2 + index - 1) % 5] for index in relative]
    # The loop overwrites only when a condition fires; a late opposite god does
    # not clear a previously assigned code. Counting just final totals is wrong.
    matching, opposite = {1: ("比肩", "劫財"), 2: ("食神", "傷官"), 3: ("正財", "偏財"), 4: ("正官", "偏官"), 5: ("正印", "偏印")}[favorable]
    first_code = {1: "01", 2: "03", 3: "06", 4: "08", 5: "10"}[favorable]
    other_code = {1: "02", 2: "04", 3: "05", 4: "07", 5: "09"}[favorable]
    cnt, kcnt, ten_code = 0, 0, ""
    for index in (0, 2, 5, 1, 3, 4, 6):
        cnt += ordered[index] == matching
        kcnt += ordered[index] == opposite
        if cnt in {1, 2} and kcnt == 0:
            ten_code = first_code
        if cnt not in {0, 1, 2}:
            ten_code = other_code
    ten_code = ten_code or "01"
    stem_code = DATA["find_yong"]["yong_chungan"][str(STEMS.index(day) + 1)][ten_code]
    life_code = DATA["find_yong"]["woonsung"][str(STEMS.index(day))][BRANCHES.index(pillars["day"]["branch"])]
    element_codes = [str("木火土金水".index(element) + 1) for element in absolute]
    # Original return order is yong/hee/kee/goo/han while saju_made names it in
    # reverse order; preserve both instead of silently relabeling those values.
    returned_codes = list(reversed(element_codes))
    returned = "-".join(absolute) + "|" + "-".join(returned_codes) + "|" + ten_code + "|" + stem_code + "|" + life_code
    return {"source": SOURCE + ":904-2751", "paljayuk": ordered, "counts_in_bi_sh_ja_kw": counts, "hyung": shape, "Y": favorable, "H": supporting, "elements_han_goo_kee_hee_yong": absolute, "returned_element_codes": returned_codes, "yong_to_sibsin": ten_code, "yong_chungan": stem_code, "woon12_daygi": life_code, "return_value": returned}


def source_saju_made(natal: dict, major: dict, yong: dict, lunar: dict, source_solunar: int) -> dict:
    """All selector variables from saju_made, including code-order quirks."""
    values = {"moks": str(major["source_daeunsu"]), "solunar": {1: 2, 2: 1, 3: 3}[source_solunar]}
    branch_elements = (5, 3, 1, 1, 3, 2, 2, 3, 4, 4, 3, 5)
    for name, source_name in (("year", "year"), ("month", "month"), ("day", "day"), ("hour", "time")):
        pillar = natal["pillars"][name]
        values[source_name + "gan"] = pillar["stem"]
        values[source_name + "gi"] = pillar["branch"]
        values["X" + source_name + "gan"] = pillar["stem_index"]
        values["X" + source_name + "gi"] = pillar["branch_index"]
        values["X" + source_name + "gan_oh"] = str((pillar["stem_index"] + 1) // 2)
        values["X" + source_name + "gi_oh"] = str(branch_elements[pillar["branch_index"] - 1])
    for index, pair in enumerate(major["returned_first_eight"], 1):
        values[f"dae{index}gan"], values[f"dae{index}gi"] = pair["stem"], pair["branch"]
    values["sSajuArr"] = [part for name in ("year", "month", "day", "hour") for part in (natal["pillars"][name]["stem"], natal["pillars"][name]["branch"])]
    values["sSajuArr"] += [part for pair in major["returned_first_eight"] for part in (pair["stem"], pair["branch"])]
    values["yYongs"] = yong["return_value"].split("|")
    names = ("hansin", "goosin", "keesin", "heesin", "yongsin")
    values.update(zip(names, yong["elements_han_goo_kee_hee_yong"]))
    values.update(zip(("han_code", "goo_code", "kee_code", "hee_code", "yong_code"), yong["returned_element_codes"]))
    for name in ("yong_to_sibsin", "yong_chungan", "woon12_daygi"):
        values[name] = yong[name]
    day_index = next(number for number in range(60) if number % 10 == natal["pillars"]["day"]["stem_index"] - 1 and number % 12 == natal["pillars"]["day"]["branch_index"] - 1)
    values["gongmang"] = ("戌亥", "申酉", "午未", "辰巳", "寅卯", "子丑")[day_index // 10]
    values["ilgan_baeyeul"], values["ilgi_baeyeul"] = natal["pillars"]["day"]["stem_index"] - 1, natal["pillars"]["day"]["branch_index"] - 1
    values["sigi"] = "자축인묘진사오미신유술해"[natal["pillars"]["hour"]["branch_index"] - 1]
    values["ilgan"] = values["daygan"]
    # The solar branch references unassigned buf(3..5). Keep these absent and
    # report the source-state error; do not populate them from another calendar.
    if source_solunar != 2:
        values.update(byear=str(lunar["year"]), bmonth=str(lunar["month"]), bday=str(lunar["day"]))
    return values


def calculate_native(birth: Birth, *, source_solunar: int, terms_by_year: dict[int, list[datetime]], reference_year: int,
                     source_native_request_date: SourceNativeRequestDate | dict | None = None,
                     source_leap_mismatch_policy: str = "reject") -> dict:
    """Complete active b_saju calculation and saju_made selector variables."""
    solar, lunar = native_birth(birth, source_solunar, source_native_request_date, source_leap_mismatch_policy)
    natal = source_natal(solar, terms_by_year)
    major = source_major_luck(solar, birth.gender, natal, terms_by_year, reference_year)
    yong = source_find_yong(natal)
    values = source_saju_made(natal, major, yong, lunar, source_solunar)
    values["sex_2"] = "1" if birth.gender == "male" else "2"
    # f_Saju:3270-3384 uses OR in every range test, so the first arm always wins.
    ruling = (9, 10, 5, 1, 2, 5, 3, 4, 5, 7, 8, 5)[natal["pillars"]["month"]["branch_index"] - 1]
    errors = []
    bindings = []
    if lunar.get("source_leap_lookup_matched") is False:
        bindings.append("source_leap_lookup_unmatched_regular_fallback")
        errors.append({"source": SOURCE, "line": 2914, "code": bindings[0], "reason_code": lunar["source_lookup_reason"]})
    if source_solunar == 2:
        errors += [{"source": "saju_made.asp", "line": line, "code": "unassigned_buf_array", "field": field} for line, field in ((334, "byear"), (335, "bmonth"), (336, "bday"))]
    return {
        "natal": natal,
        "major_luck": major,
        "yongsin": yong,
        "source_variables": values,
        "source_ruling_stem": {"index": ruling, "stem": STEMS[ruling - 1], "source_or_range_preserved": True},
        "source_state_errors": errors,
        "source_unresolved_bindings": bindings,
        "source_effective_calendar": lunar.get("source_effective_calendar", "solar" if source_solunar == 2 else "matched_leap_lunar" if source_solunar == 3 else "regular_lunar"),
        "source_calendar_adapter": "explicit saju_made solunar + original suntolun/YunDat; original gDIV century interpretation",
        "source_native_input_variant": "explicit_source_tokens" if source_native_request_date is not None else "typed_integer_arguments",
        "active_native_algorithm_complete": True
    }


def _source_date(value) -> datetime:
    if isinstance(value, datetime):
        return _local(value)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        found = re.fullmatch(r"\s*(\d{4})[-/](\d{1,2})[-/](\d{1,2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?\s*", value)
        if found:
            return datetime(*(int(part or 0) for part in found.groups()))
    raise DomainError("source_date_interpretation_required", "원본 절기 함수의 CDate 인수 해석을 확인해야 합니다.")


def source_term_lookup(function: str, value, terms_by_year: dict[int, list[datetime]]):
    """Exact f_Pre/f_Next/fi_Pre, including the last-term Empty return."""
    instant = _source_date(value)

    def terms(year):
        rows = terms_by_year.get(year)
        if rows is None or len(rows) != 24:
            raise DomainError("source_terms_required", "원본 절기 함수가 읽는 gDIV 연도 행이 필요합니다.")
        return rows

    rows = terms(instant.year)
    if instant < rows[0]:
        index = 24
    elif instant == rows[-1]:
        index = EMPTY
    else:
        index = max(number for number, term in enumerate(rows, 1) if term <= instant)
    if function == "fi_pre_div24":
        return index
    if function == "f_pre_div24":
        return terms(instant.year - 1)[23] if instant < rows[0] else EMPTY if index is EMPTY else rows[index - 1]
    if function == "f_next_div24":
        if index is EMPTY:
            return rows[0]  # Empty = hard literal0; source takes its first arm.
        if index == 24:
            return terms(instant.year + 1)[0] if instant > rows[23] else rows[0]
        return rows[index]
    raise DomainError("invalid_service_parameters", "지원하지 않는 원본 절기 함수입니다.")


def native_source_callbacks(*, terms_by_year: dict[int, list[datetime]], reference_year: int,
                            diagnostics: list | None = None) -> dict:
    """Private VM callbacks for native source bodies, with original ByRef types.

    SoloSaju includes source date display strings solely for the caller's original
    saju_made parser. Never serialize these return arrays or the VM environment
    into public/AI evidence. Diagnostics contain codes only, never raw inputs.
    The source Sun_Value is AFTER saju_made's 1/2 swap.
    """
    messages = diagnostics if diagnostics is not None else []

    def unresolved(code, category="source_policy"):
        entry = {"source": SOURCE, "code": code, "category": category}
        if entry not in messages:
            messages.append(entry)
        return Missing(frozenset({category + "." + code}))

    def integer(value):
        if value is EMPTY:
            return 0
        if isinstance(value, bool):
            return -int(value)
        if type(value) is int:
            return value
        if isinstance(value, str) and re.fullmatch(r"[+-]?[0-9]+", value.strip()):
            return int(value)
        raise ValueError("Source CInt argument required")

    def b_saju_click(man, sun, year, month, day, hour, minute, unused):
        male, calendar = integer(man), integer(sun)
        mode = 2 if calendar == 1 else 3 if calendar == 3 else 1
        try:
            birth = Birth(year=integer(year), month=integer(month), day=integer(day),
                          hour=integer(hour), minute=integer(minute), gender="male" if male == 1 else "female",
                          calendar="solar" if mode == 2 else "lunar", leap_month=mode == 3)
            tokens = {"year": year, "month": month, "day": day}
            native = calculate_native(birth, source_solunar=mode, terms_by_year=terms_by_year, reference_year=reference_year,
                                      source_native_request_date=tokens, source_leap_mismatch_policy="original_regular_fallback")
            solar, lunar = native_birth(birth, mode, tokens, "original_regular_fallback")
        except DomainError as error:
            category = "source_runtime_fault" if error.code in {"source_last_term_equality_unverified", "source_term_century_order_unverified"} else "source_policy"
            return unresolved(error.code, category)
        except (ValidationError, ValueError, TypeError):
            return unresolved("native_source_argument_contract_required")
        if calendar not in {1, 2, 3}:
            unresolved("source_calendar_binding_empty_regular_fallback", "source_binding")
        for code in native["source_unresolved_bindings"]:
            unresolved(code, "source_binding")
        values = native["source_variables"]
        weekday = "月火水木金土日"[solar.weekday()]
        solar_text = f"{solar.year}년 {solar.month}월 {solar.day}일 {native['natal']['pillars']['hour']['branch']}시 ({weekday}요일)"
        lunar_text = f"{lunar['year']}년 {lunar['month']}월 {lunar['day']}일 {hour}시 {minute}분 "
        result = ["|".join(values["sSajuArr"]), values["moks"], native["yongsin"]["return_value"], solar_text, lunar_text]
        changed = {2: solar.year, 3: solar.month, 4: solar.day} if calendar == 3 and not native["source_unresolved_bindings"] else {}
        return FunctionResult(value=result, writes={}, byref=changed)

    result = {"b_saju_click": b_saju_click}
    for name in ("f_pre_div24", "f_next_div24", "fi_pre_div24"):
        def lookup(value, function=name):
            try:
                return source_term_lookup(function, value, terms_by_year)
            except DomainError as error:
                return unresolved(error.code)
        result[name] = lookup
    return result


def _validated(model, value):
    try:
        return model.model_validate(value)
    except (ValidationError, ValueError, TypeError):
        raise DomainError("invalid_source_record", "명시한 원본 레코드의 필드·형식·순서를 확인해 주세요.") from None


def build_source_globals(
    *, birth: Birth, source_solunar: int | None = None,
    terms_by_year: dict[int, list[datetime]] | None = None,
    source_birth_rows: SourceBirthRows | dict | None = None,
    source_current_record: SourceCurrentRecord | dict | None = None,
    source_state: SourceDisplayState | dict | None = None,
    source_native_request_date: SourceNativeRequestDate | dict | None = None,
    source_leap_mismatch_policy: str = "reject",
    server_date: date | None = None
) -> dict:
    """Internal calculation globals before the leaf/common helper programs.

    Native f_Saju and row-based sajuyowha remain independent source profiles.
    Only an explicit native calendar binding enables the former. Missing source
    data remains ``Missing`` rather than a pillar from another implementation.
    The returned variables are private VM input, not public/AI evidence. Raw
    birth date/time, record identities and calendar-conversion dates are omitted.
    F029 is deliberately not executed here, so its loop state cannot alter a
    subsequent leaf's original i/j/k variables.
    """
    clock = server_date or datetime.now(KST).date()
    rows = _validated(SourceBirthRows, source_birth_rows) if source_birth_rows is not None else None
    current = _validated(SourceCurrentRecord, source_current_record) if source_current_record is not None else None
    state = _validated(SourceDisplayState, source_state).model_dump(exclude_none=True) if source_state is not None else {}
    if current and current.no != clock.strftime("%Y%m%d"):
        raise DomainError("source_record_date_mismatch", "원본 현재 mansedata.no가 명시한 server_date와 다릅니다.")
    values = {"chungan": list(STEMS), "gigi": list(BRANCHES),
              "sex": "남" if birth.gender == "male" else "여",
              "sex_2": "1" if birth.gender == "male" else "2"}
    native_names = {"moks", "solunar", "ssajuarr", "yyongs", "hansin", "goosin", "keesin", "heesin", "yongsin",
                    "han_code", "goo_code", "kee_code", "hee_code", "yong_code", "yong_to_sibsin", "yong_chungan",
                    "woon12_daygi", "gongmang", "ilgan_baeyeul", "ilgi_baeyeul", "sigi", "ilgan"}
    native_names |= {prefix + kind + suffix for prefix in ("", "x")
                     for kind in ("yeargan", "yeargi", "monthgan", "monthgi", "daygan", "daygi", "timegan", "timegi")
                     for suffix in (("", "_oh") if prefix else ("",))}
    native_names |= {f"dae{index}{part}" for index in range(1, 9) for part in ("gan", "gi")}
    missing_policy = "native.source_solunar" if source_solunar is None else "native.source_terms"
    values.update({name: Missing(frozenset({missing_policy})) for name in native_names})
    errors = []
    bindings = []
    if source_solunar is not None:
        try:
            native_terms = bundled_source_terms(None) if terms_by_year is None else terms_by_year
            native = calculate_native(birth, source_solunar=source_solunar, terms_by_year=native_terms, reference_year=clock.year,
                                      source_native_request_date=source_native_request_date, source_leap_mismatch_policy=source_leap_mismatch_policy)
            values.update({key.lower(): item for key, item in native["source_variables"].items()})
            errors.extend(native["source_state_errors"])
            bindings.extend(native["source_unresolved_bindings"])
        except DomainError as exc:
            errors.append({"source": SOURCE, "code": exc.code})
            values.update({name: Missing(frozenset({"native." + exc.code})) for name in native_names})
    elif terms_by_year is not None:
        raise DomainError("source_calendar_binding_required", "원본 native 절기에는 source_solunar가 필요합니다.")
    values.update(state)
    birthday = datetime(birth.year, birth.month, birth.day, birth.hour, birth.minute, tzinfo=KST) if birth.calendar == "solar" else solar_birth(birth)
    profile = process_source_profile(birth_datetime=birthday, source_birth_rows=rows,
                                     source_current_record=current, native_result=values)
    private = {"solar_year", "solar_month", "solar_day", "request_year", "request_month", "request_day", "request_hour", "request_min",
               "selected_month", "my_ymd_jeolip", "member_hour_min", "my_number", "my_jeolip", "solosaju", "byear", "bmonth", "bday", "bb", "bbarr"}
    filtered = {name: item for name, item in profile["state"].items()
                if name not in private and not name.startswith(("source_", "__")) and not name.endswith(("_hh", "_ee"))
                and not (isinstance(item, str) and ("@display" in item or ".gif" in item))}
    missing = {name: sorted(item.fields) for name, item in filtered.items() if isinstance(item, Missing)}
    errors.extend({"source": "old/unse/interlife/UNSE_DATA/solve/sajujowha.asp", **error} for error in profile["source_errors"])
    return {"source_profile": "original-native-and-sajujowha-globals-v1", "variables": filtered,
            "missing_fields": missing, "source_errors": errors, "unresolved_bindings": bindings, "f029_executed": False,
            "dotong_substitution": False, "contains_private_birth_inputs": False}


def _parameters(request: ServiceRequest, service_id: str):
    parameters = request.parameters
    if set(parameters) - set(SERVICES[service_id]["parameter_help"]):
        raise DomainError("invalid_service_parameters", "지원하지 않는 원본 차트 parameters 항목입니다.")
    if "source_terms" in parameters and "source_two_digit_year_max" in parameters:
        raise DomainError("invalid_service_parameters", "source_terms와 source_two_digit_year_max 중 한 경로만 사용해 주세요.")
    if "source_terms" in parameters:
        rows = parameters["source_terms"]
        if not isinstance(rows, list) or not 1 <= len(rows) <= 3:
            raise DomainError("invalid_source_record", "source_terms는 출생연도 및 필요한 인접연도 1~3개 레코드 목록입니다.")
        parsed = [_validated(SourceYearTerms, row) for row in rows]
        if len({row.year for row in parsed}) != len(parsed):
            raise DomainError("invalid_source_record", "원본 gDIV 연도키가 중복되었습니다.")
        terms = {row.year: [term.at for term in row.terms] for row in parsed}
    else:
        pivot = parameters.get("source_two_digit_year_max")
        if pivot is not None and (type(pivot) is not int or not 1900 <= pivot <= 2099):
            raise DomainError("invalid_service_parameters", "source_two_digit_year_max는 검증한 원본 서버 설정의 1900~2099 정수여야 합니다.")
        terms = bundled_source_terms(pivot)
    server = parameters.get("server_date")
    if server is None:
        server_date = datetime.now(KST).date()
    else:
        if not isinstance(server, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", server):
            raise DomainError("invalid_service_parameters", "server_date는 YYYY-MM-DD 날짜입니다.")
        try:
            server_date = date.fromisoformat(server)
        except ValueError:
            raise DomainError("invalid_service_parameters", "server_date가 유효한 날짜가 아닙니다.") from None
    record = _validated(SourceCurrentRecord, parameters["source_current_record"]) if "source_current_record" in parameters else None
    if record and record.no != server_date.strftime("%Y%m%d"):
        raise DomainError("source_record_date_mismatch", "원본 현재 mansedata.no가 명시한 server_date와 다릅니다.")
    return parameters, terms, server_date, record


def decide(service_id: str, request: ServiceRequest, saju: SajuResult | None = None, partner: SajuResult | None = None) -> dict:
    if service_id not in SERVICES:
        raise DomainError("unsupported_service", "이식 대상 차트 서비스가 아닙니다.")
    if request.birth is None:
        raise DomainError("birth_required", "이 원본 차트에는 birth가 필요합니다.")
    parameters, terms, server_date, current = _parameters(request, service_id)
    if request.birth.calendar == "solar":
        birth_date = datetime(request.birth.year, request.birth.month, request.birth.day, request.birth.hour, request.birth.minute, tzinfo=KST)
    else:
        birth_date = solar_birth(request.birth)
    facts = {"source_profile": "interlife-complete-source-predicates-v1", "basic_solar_conversion": "solar input directly; lunar buffer uses approved corrected tb_manse", "source_current_date": server_date.isoformat(), "original_source_present": True, "dotong_substitution": False}
    unresolved = []
    selectors = []
    native_values = {}
    binding = parameters.get("source_solunar")
    if binding is not None:
        try:
            native = calculate_native(request.birth, source_solunar=binding, terms_by_year=terms, reference_year=server_date.year,
                                      source_native_request_date=parameters.get("source_native_request_date"),
                                      source_leap_mismatch_policy=parameters.get("source_leap_mismatch_policy", "reject"))
            native_values = native["source_variables"]
            facts["native_comparison"] = {key: value for key, value in native.items() if key != "source_variables"}
            unresolved.extend("source_calendar_binding_unverified: " + code for code in native["source_unresolved_bindings"])
        except DomainError as exc:
            unresolved.append(exc.code + ": " + exc.message)
    elif any(key in parameters for key in ("source_terms", "source_two_digit_year_max", "source_native_request_date", "source_leap_mismatch_policy")):
        raise DomainError("source_calendar_binding_required", "native 비교 계산에는 원본 source_solunar를 명시해야 합니다.")

    rows = _validated(SourceBirthRows, parameters["source_birth_rows"]) if "source_birth_rows" in parameters else None
    state = _validated(SourceDisplayState, parameters["source_state"]).model_dump(exclude_none=True) if "source_state" in parameters else {}
    display = None
    if service_id != "interlife-jum-1" or rows is not None:
        display = process_display(
            birth_datetime=birth_date,
            source_birth_rows=rows,
            source_current_record=current,
            native_result={**native_values, **state}
        )
    if service_id != "interlife-jum-1":
        facts["display"] = {key: display[key] for key in ("algorithm_complete", "source_profile", "source_pillars", "hidden_stems", "major_pillars", "display_fields", "missing_fields", "source_errors", "source_syntax_anomalies", "unassigned_source_inputs", "native_profile_substituted_for_original_rows")}
        missing = sorted({field for fields in display["missing_fields"].values() for field in fields})
        unresolved += ["source_row_required: " + field for field in missing]
        if display["unassigned_source_inputs"]:
            unresolved.append("source_unassigned_state: 원본 외부 입력이 미할당입니다: " + ", ".join(display["unassigned_source_inputs"]))
        if display["source_syntax_anomalies"]:
            unresolved.append("source_syntax_anomaly: 원본 VB 블록의 // 주석형 행을 계산식과 구분해 보존했습니다. 원본 배포의 주석 처리 상태를 확인해야 합니다.")
    else:
        original_birth = None
        if "source_ziwei_birth" in parameters:
            original_birth = _validated(SourceZiweiBirth, parameters["source_ziwei_birth"])
        elif rows and rows.selected:
            # Only the basic lunar date is replaced by the approved table. The
            # year stem/branch come from actual source row predicates, never a
            # substituted native or dotong pillar.
            from app.calendar import _birth_record

            _, calendar_row = _birth_record(request.birth)
            variables = display["variables"]
            original_birth = _validated(SourceZiweiBirth, {
                "year_h": variables["my_year_h"], "year_e": variables["my_year_e"],
                "lunar_year": int(calendar_row["l_year"]),
                "lunar_month": f"{int(calendar_row['l_mon']):02d}",
                "lunar_day": f"{int(calendar_row['l_day']):02d}"
            })
        hour = source_buffer_hour_branch(request.birth.hour, request.birth.minute)
        facts["source_hour_branch"] = hour
        if original_birth:
            if current and current.umdate is None:
                raise DomainError("invalid_source_record", "자미 현재 행은 나이·대운 계산에 읽는 원본 음력 umdate가 필요합니다.")
            if rows and rows.selected:
                values = display["variables"]
                if values.get("my_year_h") != original_birth.year_h or values.get("my_year_e") != original_birth.year_e:
                    raise DomainError("source_record_conflict", "자미 입력의 원본 연간지와 출생 선택 행이 다릅니다.")
            selected = parameters.get("source_selected_year")
            if selected is not None and (type(selected) is not int or not 1881 <= selected <= 2050):
                raise DomainError("invalid_service_parameters", "source_selected_year는 원본 범위의 정수 연도입니다.")
            annual = _validated(SourceAnnualRecord, parameters["source_annual_record"]) if "source_annual_record" in parameters else None
            if annual and selected is None and "source_mm" not in parameters:
                raise DomainError("invalid_service_parameters", "유년 원본 행에는 source_selected_year 또는 source_mm 선택값이 필요합니다.")
            result = calculate_ziwei(
                birth=original_birth.model_dump(), hour_branch=hour,
                gender=request.birth.gender, current=current.model_dump() if current else None,
                annual=annual.model_dump() if annual else None,
                selected_year=selected, source_mm=parameters.get("source_mm")
            )
            facts["ziwei"] = {key: result[key] for key in ("algorithm_complete", "slots", "final_leaves", "missing_fields", "source_errors")}
            missing = sorted({field for fields in result["missing_fields"].values() for field in fields})
            unresolved += ["source_row_required: " + field for field in missing]
            final = result["final_leaves"]
            for leaf in DATA["ziwei_text_leaves"]:
                raw_stars = final.get("result_14jusung_" + leaf["stars_field"])
                palace = final.get("result_" + leaf["palace_field"])
                if raw_stars is None or palace is None:
                    unresolved.append("source_leaf_key_required: " + leaf["table"])
                    continue
                key = source_star_key(raw_stars)
                selectors.append({"id": leaf["table"], "table": leaf["table"], "where": {"DB_express_1": key, "DB_express": palace}, "columns": ["DB_data"], "purpose": "원본 주성 표기와 궁의 해석", "source": f"old/unse/interlife/UNSE_DATA/solve/J/{leaf['table']}.asp:{leaf['source_line']}"})
                if key == "":
                    unresolved.append("source_unassigned_star_key: " + leaf["table"] + "의 원본 Len 분기에 없는 별 표기 길이입니다.")
            if any("jamidata_02." in field or "source_row." in field for field in missing):
                unresolved.append("jamidata_02_title_mapping_required: 실제 도달한 원본 *_title 분류가 미제공입니다. AI가 출력 열을 정하는 사실 분류를 만들지 않습니다.")
        else:
            unresolved.append("source_ziwei_birth_required: 원본 연간지와 음력 월일 또는 실제 출생일·선택 번호 행이 필요합니다.")

    if any(key in parameters for key in ("source_current_record", "source_birth_rows", "source_state", "source_ziwei_birth", "source_annual_record")):
        unresolved.append("provided_source_records_unverified: 요청에 직접 넣은 원본 행·상태는 계산 검증용입니다. 신뢰된 서버 판정 데이터 연결 전에는 AI 생성을 허용하지 않습니다.")
    return {"source": SERVICES[service_id]["source"], "facts": facts, "selectors": selectors, "unresolved": list(dict.fromkeys(unresolved)), "notes": ["보관된 native·표시 차트·자미의 순수 계산 분기를 모두 Python/정적 자료로 준비했습니다. 실제 원본 행·서버 입력 상태·문법 차이를 별도로 진단하며 임의 판정을 만들지 않습니다."]}

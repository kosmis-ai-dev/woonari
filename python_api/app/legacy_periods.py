"""CR-001 / T-005: monthly/yearly ASP decisions and original content selectors.

Only the basic ``manse`` calendar rows are replaced.  This module does not
calculate substitute fortunes, read narrative rows, or invent DB-supplied scores.
"""

from datetime import date, datetime, time

from app.calendar import KST, _raise_store_error, ganji_from_row
from app.errors import DomainError
from app.manse_store import ManseDataError, get_manse_store, term_datetime
from app.models import FortuneRequest, SajuResult
from app.rules import GANJI

MONTHLY_SOURCE = "old/unse/monthluck/main_end.asp"
YEARLY_SOURCE = "old/unse/2014yearluck/main_end.asp"

# This is the source Select Case table, not a general year-pillar formula.
YEAR_CODES = {
    2001: "辛巳",
    2002: "壬午",
    2003: "癸未",
    2004: "甲申",
    2005: "乙酉",
    2006: "丙戌",
    2007: "丁亥",
    2008: "戊子",
    2009: "己丑",
    2010: "庚寅",
    2011: "辛卯",
    2012: "壬辰",
    2013: "癸巳",
    2014: "甲午",
}

# Source CalcSaju defines 立春=1, with month changes on odd division numbers.
DIVISION_NAMES = (
    "立春",
    "雨水",
    "惊蛰",
    "春分",
    "清明",
    "谷雨",
    "立夏",
    "小满",
    "芒种",
    "夏至",
    "小暑",
    "大暑",
    "立秋",
    "处暑",
    "白露",
    "秋分",
    "寒露",
    "霜降",
    "立冬",
    "小雪",
    "大雪",
    "冬至",
    "小寒",
    "大寒",
)
DIVISIONS = {name: index for index, name in enumerate(DIVISION_NAMES, 1)}
TERM_ALIASES = {
    "DA_XUE": "大雪",
    "DONG_ZHI": "冬至",
    "XIAO_HAN": "小寒",
    "DA_HAN": "大寒",
    "LI_CHUN": "立春",
    "YU_SHUI": "雨水",
    "JING_ZHE": "惊蛰",
}

YEAR_COLUMNS = [
    "memno",
    "section",
    "sex",
    "content",
    "sol1",
    "sol2",
    "sol3",
    "sol4",
    "sol5",
    "star_cnt",
    "solar",
    *[f"mark{i}" for i in range(1, 12)],
]
YEAR_DB_DECISION_FIELDS = ["section", "star_cnt", "solar", *[f"mark{i}" for i in range(1, 12)]]


def _month_index_after_division(month_index: int, division: int) -> int:
    """ASP monthluck lines 64–71: increment on the entire odd-division date."""
    if division % 2 != 0:
        return 0 if month_index == 59 else month_index + 1
    return month_index


def _monthly_calendar_row(target: date) -> dict:
    try:
        store = get_manse_store()
        raw = store.solar_record(target)
        previous, following = store.solar_terms(datetime.combine(target, time.max, tzinfo=KST))
    except ManseDataError as exc:
        _raise_store_error(exc)
    if previous is None or following is None:
        raise DomainError(
            "calendar_boundary_unavailable",
            "제공된 만세력 DB에 월간 표시 범위를 정할 이전·다음 절입 자료가 없습니다.",
        )
    division = raw["div_name"]
    start = datetime.fromisoformat(previous["at"]).date()
    end = datetime.fromisoformat(following["at"]).date()
    return {
        "month_pillar": GANJI.index(ganji_from_row(raw, "m")),
        "div_name": division,
        "division_name": DIVISION_NAMES[division - 1] if division else None,
        "division_at": term_datetime(raw).isoformat() if division else None,
        "period_start": start,
        "period_end": end,
        "replacement_disp_day": start.strftime("%Y%m%d") + end.strftime("%Y%m%d"),
        "previous_jie": {key: previous[key] for key in ("name", "at")},
        "next_jie": {key: following[key] for key in ("name", "at")},
    }


def _selection_identity(request: FortuneRequest, saju: SajuResult) -> tuple[int, str]:
    # Both source pages use Left(CalcMemNo(...), 1). Female DB value is "녀".
    memno = int(saju.legacy_memno[0])
    sex = "녀" if request.birth.gender == "female" else "남"
    return memno, sex


def _monthly(request: FortuneRequest, saju: SajuResult) -> dict:
    row = _monthly_calendar_row(request.target_date)
    memno, sex = _selection_identity(request, saju)
    selected_month = _month_index_after_division(row["month_pillar"], row["div_name"])
    where = {"memno": memno, "yukgap_no": selected_month, "sex": sex}
    start, end = row["period_start"], row["period_end"]
    facts = {
        "legacy_memno_first_digit": memno,
        "legacy_sex": sex,
        "target_date_replaces_server_Date": request.target_date.isoformat(),
        "original_calendar_lookup": {
            "table": "manse",
            "where": {
                "syear": request.target_date.year,
                "smonth": request.target_date.month,
                "sday": request.target_date.day,
            },
            "columns": ["month_pillar", "div_name", "disp_day"],
        },
        "replacement_manse": {
            key: value for key, value in row.items() if key not in {"period_start", "period_end"}
        },
        "month_pillar_before_asp_adjustment": row["month_pillar"],
        "odd_division_increment_applied": row["div_name"] % 2 != 0,
        "selected_yukgap_no": selected_month,
        "selected_month_pillar": GANJI[selected_month],
        "text_selection_keys": where,
        "display_period": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "asp_display": f"{start:%m}월{start:%d}일 ~ {end:%m}월{end:%d}일",
            "end_semantics": "DB-derived next division date is displayed as the end boundary; do not subtract a day",
        },
        "calendar_replacement": {
            "status": "source_tb_manse_database",
            "basis": "script.sql tb_manse raw month/division; monthluck:47-71; lifeluck:501-509 disp_day parsing",
            "limitation": "제공 tb_manse에는 disp_day가 없습니다. DB 절입 날짜로 생성한 replacement_disp_day와 기존 manse.disp_day의 완전 동일성은 미검증입니다.",
        },
    }
    return {
        "source": MONTHLY_SOURCE,
        "facts": facts,
        "selectors": [
            {
                "id": "monthly-content",
                "table": "monthfor",
                "where": where,
                "columns": ["contents"],
                "purpose": "월간 운세 본문 조회를 AI 작성으로 교체",
            }
        ],
        "unresolved": [],
        "period_start": start,
        "period_end": end,
    }


def _yearly(request: FortuneRequest, saju: SajuResult) -> dict:
    code = request.target_date.year
    if code not in YEAR_CODES:
        raise DomainError(
            "legacy_year_unsupported",
            "원본 2014yearluck의 code 분기는 2001~2014년만 정의되어 있습니다. "
            "복원된 새 연간 표의 2021~2050년은 미작성 초기 행이며 기존 키와의 매핑도 필요합니다. "
            "GET /v1/restored-data에서 확인하세요.",
        )
    memno, sex = _selection_identity(request, saju)
    where = {"memno": memno, "sex": sex, "year_pillar": YEAR_CODES[code]}
    return {
        "source": YEARLY_SOURCE,
        "facts": {
            "code": str(code),
            "source_default_code_if_empty": "2013",
            "supported_source_codes": list(YEAR_CODES),
            "selected_year_pillar": YEAR_CODES[code],
            "text_selection_keys": where,
            "query_order_by": ["num ASC"],
            "source_rule": "Select Case CStr(code); not birth-year or target-day LiChun calculation",
            "db_supplied_decision_fields": YEAR_DB_DECISION_FIELDS,
            "db_supplied_values": {field: None for field in YEAR_DB_DECISION_FIELDS},
            "row_rendering_conditions": [
                {
                    "expression": "section <> 0",
                    "effect": "star_cnt개의 별을 표시",
                    "resolved": False,
                },
                {
                    "expression": "section < 20",
                    "effect": "해당 DB 행의 solar 기간을 표시",
                    "resolved": False,
                },
                {
                    "expression": "section = 0 And sol1 <> ''",
                    "effect": "첫 번째 본문/부적 표시 분기",
                    "resolved": False,
                },
                {
                    "expression": "section < 20 And CStr(code) > '2003'",
                    "effect": "mark1~mark11 그래프 표시",
                    "resolved": False,
                },
            ],
            "row_order_ui": {
                "index_starts_at": 1,
                "monthly_row_condition": "row index > 7",
                "monthly_title_index": "row index - 7",
                "known_tab_labels": [
                    "사업운",
                    "재물운",
                    "애정운",
                    "건강운",
                    "여행운",
                    "시험직장운",
                    "1월2월운",
                    "3월4월운",
                    "5월6월운",
                    "7월8월운",
                    "9월10월운",
                    "11월12월운",
                ],
                "limitation": "실제 행 수·순서·section 대응은 yearfortune 레코드 없이는 확정할 수 없습니다.",
            },
            "period_semantics": "code 연도의 API 조회 범위입니다. 원본 개별 행의 solar 표시 구간은 미확보입니다.",
        },
        "selectors": [
            {
                "id": "yearly-sections",
                "table": "yearfortune",
                "where": where,
                "columns": YEAR_COLUMNS.copy(),
                "purpose": "원본 num순 연간/항목별/월별 본문 조회 키 보존; content만 AI로 작성 가능",
            }
        ],
        "unresolved": [
            "yearfortune의 section/num 행 구성과 star_cnt/solar/mark1~mark11은 원본 DB 값입니다. ASP에는 산출식이 없으므로 생성하지 않았습니다.",
            "행별 sol1~sol5(부적) 선택도 원본 DB 값이며 본문 content와 별개입니다. AI가 원본 판정처럼 보완할 수 없습니다.",
            "백업의 구 yearfortune del은 0행입니다. 새 TB_yearLuck은 다른 키 구조이며 사주·성별·항목 매핑이 미검증입니다. GET /v1/restored-data에서 복원 자료 상태를 확인하세요.",
        ],
        "period_start": date(code, 1, 1),
        "period_end": date(code, 12, 31),
    }


def decide_period(kind: str, request: FortuneRequest, saju: SajuResult) -> dict:
    """Return exact source predicates and source-dependent unresolved fields.

    ``target_date.year`` maps to the yearly page's explicit ``code`` input. A
    missing ``code`` fallback is recorded, but target_date is mandatory in this API.
    """
    if kind == "monthly":
        return _monthly(request, saju)
    if kind == "yearly":
        return _yearly(request, saju)
    raise DomainError("legacy_period_unsupported", "월간 또는 연간 운세만 처리할 수 있습니다.")

"""CR-012/T-024: source arithmetic for theme15 and the two-stage lotto page.

The original mansedata profile is not asserted equivalent to tb_manse. Candidate
calendar-dependent results are distinct from final selectors; pure combination
mode needs neither that profile nor an AI interpretation.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path
from typing import TYPE_CHECKING

from app.calendar import ganji_from_row, solar_birth
from app.errors import DomainError
from app.manse_store import ManseDataError, get_manse_store
from app.models import SajuResult
from app.ported_interlife import _zodiac
from app.rules import BRANCHES, GANJI, STEMS

if TYPE_CHECKING:
    from app.service_models import ServiceRequest

ROOT = "old/unse/interlife/UNSE_DATA/"
KST = timezone(timedelta(hours=9))
_DATA = json.loads((Path(__file__).parent / "data/ported_interlife_extra_rules.json").read_text("utf-8"))
_BRANCH_CODES = "寅卯辰巳午未申酉戌亥子丑"
_LIMIT = "원본 mansedata의 A~J·01~12 간지/number/jeolip와 tb_manse 원시 간지·절입 필드의 대응이 미검증입니다. 기본 달력 후보와 원본 산술을 제공하며 원본 최종 판정으로 확정하지 않습니다."

SERVICES = {
    "interlife-theme-15": {
        "name": "재테크비법", "requires_birth": True, "requires_partner": False,
        "uses_saju": False, "ready": False, "example_parameters": {},
        "parameter_help": {"server_datetime": "원본 Date/Now 재현용 한국시간 ISO 날짜시각. 생략하면 한국시간 현재입니다. target_date와 별개입니다."},
        "source_limits": [_LIMIT],
    },
    "interlife-lotto-1": {
        "name": "로또번호un·번호 조합", "requires_birth": True, "requires_partner": False,
        "uses_saju": False, "ready": False, "example_parameters": {},
        "parameter_help": {
            "mode": "generate(기본): 원본 12개 번호 산술 후보. combine: 선택 번호를 6개씩 조합하는 계산 전용 모드.",
            "server_datetime": "원본 Now 재현용 한국시간 ISO 날짜시각. 번호는 날짜·시·분과 출생 간지에 따라 결정되며 난수가 아닙니다.",
            "draw_date": "원본 cyear/cmonth/cday에 해당하는 추첨일. 최초 번호 계산은 이 값을 읽기 전에 현재 날짜로 고정하며 별도 표시용입니다.",
            "select_num": "combine 모드의 중복 없는 1~45 정수 배열, 7~10개. 입력 순서대로 조합합니다.",
            "want1": "combine: 홀1짝5/홀5짝1 제외 여부(bool).",
            "want2": "combine: 홀2짝4/홀4짝2 제외 여부(bool).",
            "want3": "combine: 홀3짝3 제외 여부(bool).",
            "want4": "combine: 홀6/짝6 제외 여부(bool).",
            "want0": "combine: 다른 필터보다 우선하는 전체 표시(bool).",
            "want11": "combine: 같은 십단위에 세 개 이상인 조합 제외(bool).",
        },
        "source_limits": [_LIMIT, "원본은 모든 홀짝 제외 옵션을 동시에 켠 분기를 정의하지 않으며 마지막 빈 행을 한 번 더 순회합니다."],
    },
}


def _invalid(message="이 서비스의 parameters 형식과 허용 범위를 확인하세요."):
    raise DomainError("invalid_service_parameters", message)


def _clock(parameters):
    value = parameters.get("server_datetime")
    if value is None:
        return datetime.now(KST)
    if not isinstance(value, str) or "T" not in value:
        _invalid("server_datetime은 날짜와 시각을 포함한 ISO 문자열이어야 합니다.")
    try:
        clock = datetime.fromisoformat(value)
    except ValueError:
        _invalid("server_datetime을 유효한 ISO 날짜시각으로 입력하세요.")
    clock = clock.replace(tzinfo=KST) if clock.tzinfo is None else clock.astimezone(KST)
    if not 1900 <= clock.year <= 2050:
        _invalid("server_datetime 지원 연도는 1900~2050년입니다.")
    return clock


def _raw(day):
    try:
        return get_manse_store().solar_record(day)
    except ManseDataError as error:
        raise DomainError(error.code, "기본 만세력 날짜 자료를 확인할 수 없습니다.", 503) from None


def _code(pillar):
    return chr(65 + STEMS.index(pillar[0])) + f"{_BRANCH_CODES.index(pillar[1]) + 1:02d}"


def _hour(stem, hour, minute, *, cutoff):
    number = hour * 100 + minute
    if number < cutoff or number >= 2200 + cutoff:
        slot = 0
    else:
        slot = (number // 100 * 60 + number % 100 - (cutoff // 100 * 60 + cutoff % 100)) // 120 + 1
    table = ("aa", "bb", "cc", "dd", "ee")[STEMS.index(stem) % 5]
    return _DATA["lotto"][table][slot] + BRANCHES[slot], slot


def _calendar_candidate(value, *, birth=False, draw=False):
    """Apply visible source branches to explicitly unverified basic raw rows."""
    row = _raw(value.date())
    year_month = row
    boundary = False
    # Source only performs this previous-number lookup in February. The raw row
    # mapping itself remains unverified; neither idx nor num is fabricated.
    if (birth or draw) and value.month == 2 and row.get("div_name") and row.get("div_hour") is not None:
        term = int(row["div_hour"]) * 100 + int(row.get("div_min") or 0)
        compared = value.hour * 100 + value.minute if birth else int(str(value.hour) + str(value.minute))
        if term > compared:
            year_month = _raw(value.date() - timedelta(days=1))
            boundary = True
    year, month = ganji_from_row(year_month, "y"), ganji_from_row(year_month, "m")
    day = ganji_from_row(row, "d")
    hhmm = value.hour * 100 + value.minute
    if birth:
        # sajujowha:68 rewrites exact midnight to 2400, so only 00:01..00:29
        # take the previous-day branch; the impossible 2000000 guard is retained.
        if 0 < hhmm < 30:
            day = GANJI[(GANJI.index(day) - 1) % 60]
        hour, slot = _hour(day[0], value.hour, value.minute, cutoff=130)
    elif draw:
        if hhmm < 131 or hhmm >= 2331:
            day = GANJI[(GANJI.index(day) + 1) % 60]
        hour, slot = _hour(day[0], value.hour, value.minute, cutoff=131)
    else:
        hour, slot = _hour(day[0], value.hour, value.minute, cutoff=131)
    return {"year": year, "month": month, "day": day, "hour": hour,
            "hour_slot": slot, "february_previous_row_candidate": boundary,
            "original_mansedata_verified": False}


def _selector(identifier, table, where, columns, topic, *, candidate=None):
    result = {"id": identifier, "table": table, "where": where, "columns": columns,
              "purpose": topic, "topics": dict.fromkeys(columns, topic)}
    if candidate is not None:
        result.update(key_unresolved=True, candidate_where=candidate)
    return result


def _theme(request, clock):
    natal = _calendar_candidate(solar_birth(request.birth), birth=True)
    today = ganji_from_row(_raw(clock.date()), "d")
    table = _DATA["theme"]
    first, second = table["gabja_01"].index(natal["day"]), table["gabja_02"].index(today)
    product = (first + 1) * (second + 1)
    positions = {"nam": product % 180, "nam2": (product + 135) % 180,
                 "nam3": (product + 45) % 180, "nam4": (product + 90) % 180}
    sign_name, serial = _zodiac(request.birth.month, request.birth.day)
    s058_key = _code(natal["year"]) + f"{_BRANCH_CODES.index(natal['month'][1]) + 1:02d}"
    s058 = _DATA["S058"][s058_key]
    candidates = {
        "S082": str(STEMS.index(natal["day"][0]) + 1),
        "S090": table["data_array"][positions["nam"]],
        "S091": table["data_array"][positions["nam4"]], "S058": s058,
    }
    selectors = [_selector("S118", "S118", {"DB_express": str(serial)}, ["DB_data"], "태어난 별자리의 조언")]
    for name, columns, topic in (("S082", ["DB_data"], "일간 성향"), ("S090", ["DB_data"], "오늘의 흐름"),
                                  ("S091", ["DB_data"], "오늘의 조언"), ("S058", ["DB_title", "DB_data"], "적성")):
        selectors.append(_selector(name, name, {"DB_express": None}, columns, topic, candidate={"DB_express": candidates[name]}))
    return {"source": ROOT + "unse/theme/theme_15.asp", "selectors": selectors,
            "facts": {"calendar_candidate": natal, "source_date": clock.date().isoformat(),
                      "source_zodiac": {"name": sign_name, "serial_no": serial, "raw_input_month_day_used": True},
                      "candidate_today_pillar": today, "candidate_product": product, "candidate_positions": positions,
                      "source_s082_column_override": "성별 선택 후 DB_data로 강제 재할당",
                      "original_calendar_equivalence_claimed": False}, "unresolved": [_LIMIT]}


def _source_numbers(natal, current, *, age, calendar_total, female):
    """Pure source arrays and duplicate replacement; no randomness involved."""
    rules = _DATA["lotto"]
    natal_values, current_values, current_heng = [], [], []
    for name in ("year", "month", "day", "hour"):
        index = rules["gabja"].index(_code(natal[name]))
        natal_values.append(rules[name + "_su"][index])
        index = rules["gabja"].index(_code(current[name]))
        current_values.append(rules[name + "_su"][index])
        current_heng.append(rules["heng_" + name + "_su"][index])
    natal_total = sum(natal_values)
    current_total, heng_total = sum(current_values) + 60 * female, sum(current_heng) + 60 * female
    base = age + calendar_total
    # ggum_no is never assigned by this page/requestBuffer: Empty contributes 0.
    raw = [base + value + natal_total + current_total for value in natal_values]
    raw.extend([base + natal_total + current_total] * 2)
    raw.extend(base + current_values[i] + current_total for i in (2, 3))
    raw.extend(base + current_values[i] + heng_total for i in (0, 1, 2, 3))
    chosen = []
    for value in raw:
        candidate = value % 45 or 45
        if candidate in chosen:
            candidate = next(number for number in rules["lottoNum"] if number not in chosen)
        chosen.append(candidate)
    hexagram_index = natal_total % 64
    return {"numbers": chosen, "natal_sums": natal_values, "natal_total": natal_total,
            "current_sums": current_values, "current_total": current_total, "current_heng_total": heng_total,
            "ggum_no": 0, "hexagram": {"source_index": hexagram_index,
                "lines": rules["juyek_data"][hexagram_index], "title": rules["juyek_title"][hexagram_index]},
            "randomness": "none; 원본 배열과 Mod45·순서상 첫 미사용 대체번호로 결정"}


def _generate(request, clock):
    value = solar_birth(request.birth)
    natal = _calendar_candidate(value, birth=True)
    current = _calendar_candidate(clock)
    draw = request.parameters.get("draw_date")
    parsed_draw = clock.date()
    if draw is not None:
        if not isinstance(draw, str):
            _invalid("draw_date는 YYYY-MM-DD 문자열이어야 합니다.")
        try:
            parsed_draw = date.fromisoformat(draw)
        except ValueError:
            _invalid("draw_date가 유효한 날짜가 아닙니다.")
        if parsed_draw.isoformat() != draw or not 1900 <= parsed_draw.year <= 2050:
            _invalid("draw_date 지원 범위와 YYYY-MM-DD 형식을 확인하세요.")
    candidate = _source_numbers(natal, current, age=clock.year - value.year + 1,
                                calendar_total=clock.year + clock.month + clock.day + clock.hour + clock.minute,
                                female=request.birth.gender == "female")
    display_clock = clock.replace(year=parsed_draw.year, month=parsed_draw.month, day=parsed_draw.day)
    draw_candidate = _calendar_candidate(display_clock, draw=True)
    draw_spirits = {}
    for name in ("year", "month", "day", "hour"):
        draw_spirits[name] = {
            part: _DATA["draw_six_spirits"][f"c_{name}_{part}"].get(natal["day"][0] + "|" + draw_candidate[name][index])
            for part, index in (("h", 0), ("e", 1))
        }
    day_stem_code = f"{STEMS.index(natal['day'][0]) + 1:02d}"
    hour_code = f"{_BRANCH_CODES.index(current['hour'][1]) + 1:02d}"
    return {"source": ROOT + "unse/lotto/lotto_1.asp",
            "facts": {"mode": "generate", "calendar_candidate": natal, "current_calendar_candidate": current,
                      "candidate_number_calculation": candidate, "server_datetime": clock.isoformat(timespec="minutes"),
                      "requested_draw_date": draw, "draw_date_changes_initial_numbers": False,
                      "display_calendar_candidate": draw_candidate, "display_six_spirits_candidate": draw_spirits,
                      "initial_draw_date_rule": "cyear/cmonth/cday는 최초 Empty 분기에서 Now 값으로 채워지며 원본 요청값은 번호 생성 후 sajujowha2에서 읽음",
                      "source_heng_day_array_length": len(_DATA["lotto"]["heng_day_su"]),
                      "source_heng_day_last_entry_used": False, "original_calendar_equivalence_claimed": False,
                      "draw_display_scope": "사주조화2 표시용 별도 DB 객체 상태·달력 프로필은 미검증; 완전 동일 출력 주장 없음"},
            "selectors": [_selector("S042", "S042", {"DB_express": None}, ["DB_data"], "현재 시간과 일간에 따른 조언",
                                    candidate={"DB_express": day_stem_code + hour_code})],
            "unresolved": [_LIMIT]}


def _combine(parameters):
    selected = parameters.get("select_num")
    if not isinstance(selected, list) or not 7 <= len(selected) <= 10 or any(type(x) is not int or not 1 <= x <= 45 for x in selected) or len(set(selected)) != len(selected):
        _invalid("select_num은 중복 없는1~45 정수 7~10개의 배열이어야 합니다.")
    flags = {key: parameters.get(key, False) for key in ("want1", "want2", "want3", "want4", "want0", "want11")}
    if any(type(value) is not bool for value in flags.values()):
        _invalid("want 필터는 true/false로 입력하세요.")
    key = "".join("1" if flags[name] else "0" for name in flags)
    show_all = flags["want0"] or not any(flags.values())
    recipe = _DATA["combination_filters"].get(key)
    rows = []
    for numbers in combinations(selected, 6):
        odd = sum(number % 2 for number in numbers)
        label = "홀6" if odd == 6 else "짝6" if odd == 0 else f"홀{odd}짝{6 - odd}"
        decades = [sum(lo <= number <= hi for number in numbers) for lo, hi in ((1, 9), (10, 19), (20, 29), (30, 39), (40, 49))]
        rows.append({"numbers": list(numbers), "odd_even": label, "decade_counts": decades})
    count = len(rows)
    # Original loops through select_i+1; preserve its final empty display row.
    rows.append({"numbers": [], "odd_even": "", "decade_counts": [0] * 5})
    if show_all:
        output = rows
    elif recipe is None:
        output = []
    else:
        output = [row for row in rows if row["odd_even"] not in recipe["excluded_labels"]
                  and (recipe["max_per_decade_exclusive"] is None or max(row["decade_counts"]) < recipe["max_per_decade_exclusive"])]
    return {"source": ROOT + "unse/lotto/lotto_1.asp:1931-2665", "selectors": [], "unresolved": [],
            "calculation_only": True, "facts": {"mode": "combine", "source_input_count": len(selected),
                "generated_combination_count": count, "source_extra_empty_row": True,
                "source_filter_branch_defined": bool(show_all or recipe), "filter_flags": flags,
                "display_rows": output, "valid_display_combination_count": sum(bool(row["numbers"]) for row in output),
                "source_order_preserved": True, "calendar_used": False, "randomness": "none"}}


def decide(service_id: str, request: ServiceRequest, saju: SajuResult | None = None,
           partner: SajuResult | None = None) -> dict:
    if service_id not in SERVICES:
        raise DomainError("unsupported_service", "지원하지 않는 interlife 추가 서비스입니다.", 404)
    if set(request.parameters) - set(SERVICES[service_id]["parameter_help"]):
        _invalid()
    if service_id == "interlife-lotto-1":
        mode = request.parameters.get("mode", "generate")
        if not isinstance(mode, str) or mode not in {"generate", "combine"}:
            _invalid("mode는 generate 또는 combine입니다.")
        if mode == "combine":
            if set(request.parameters) - {"mode", "select_num", "want1", "want2", "want3", "want4", "want0", "want11"}:
                _invalid("combine에는 select_num과 want 필터만 사용합니다.")
            return _combine(request.parameters)
        if set(request.parameters) - {"mode", "server_datetime", "draw_date"}:
            _invalid("generate에는 server_datetime과 draw_date만 사용합니다.")
    if request.birth is None:
        raise DomainError("birth_required", "이 서비스에는 birth 생년월일시가 필요합니다.")
    clock = _clock(request.parameters)
    if solar_birth(request.birth).date() > clock.date():
        raise DomainError("target_before_birth", "원본 서버 기준일은 출생일 이후여야 합니다.")
    return _theme(request, clock) if service_id == "interlife-theme-15" else _generate(request, clock)

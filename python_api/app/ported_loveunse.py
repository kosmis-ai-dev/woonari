"""CR-012 / T-024: pure arithmetic and text selectors from loveunse ASP.

No SQL, COM, saju package or narrative table is executed.  The source's UI
gender codes, unassigned calendar arguments, partial server dates and assignment
quirks are explicit execution rules.  Opaque selector codes are not scores.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import TYPE_CHECKING

from app.errors import DomainError
from app.models import Birth, SajuResult

if TYPE_CHECKING:
    from app.service_models import ServiceRequest


SOURCE = "old/unse/loveunse/main_end.asp"
HELPER = "function/loveunse.asp"
PROFILE = "loveunse-asp-ui-v1"
KST = timezone(timedelta(hours=9))

# kk(y - 1841), loveunse.asp:725-949, preserved as twelve month codes per year.
# 1/2 = 29/30 days; 3/4/5/6 include a following leap month: 58/59/59/60.
# The actual 203 rows cover 1841..2043; the source comment says 2041.
LUNAR_MONTH_CODES = """124112121221
221211212121
222121412121
221212121212
121221212121
212152122121
211212122212
121121212221
212321212122
212112112212
221211212152
212211212112
212212121212
121212521212
112122122121
211212122212
121152121222
121121122122
212112112122
216112112122
122121212112
212122122312
122121221212
112121221221
211241221221
211211221222
121121121222
122321121221
222112112121
222121211521
221221212112
121221212212
112124212212
112121212221
211211212221
221151212212
221121121212
221212112121
224212112121
212212212112
121212522121
121212122122
112112122212
211232122122
211211212122
212121121212
221521121212
212212112121
212212121212
152122121212
121212122122
112115221222
112112121222
121211212122
212151212121
222121121212
122121212121
215221212121
212121221212
121121252212
121121212221
212112121222
121232112212
221211211221
221221121212
122412121212
121212212121
211221212212
151212122212
121121212221
212115122122
212112112212
221211211212
221251212112
212212121212
121212212121
232122122121
211212122212
121121522122
121121122122
212112112122
212232112122
122121212112
212122121211
212521221212
112121221221
211212122122
151211221222
121121121222
122115121221
222112112121
222121211212
122161212112
121221221212
112121221221
214121212221
211211212221
221121412212
221121121212
221212112121
221224112121
212212212112
121212212212
112412122122
112112122212
211211212212
251211212122
212121121212
221212321212
212212112121
212212121212
121242121212
121122122122
112112122122
214112121222
121211212122
212121152122
122121121212
122121212121
212125212121
212121221212
121121221221
212321212221
212112121222
121211211221
225211211221
221221121212
122121521212
121212212121
211221212212
121152122212
121121212221
212112112221
221512112212
221211211212
221212152112
212212121211
221212212121
211216122121
211212122122
121121122122
212321122122
212112112122
212211211522
122121211212
122122121211
212215221212
112121221221
211212122122
121151212222
121121121222
122112112122
125212112121
222121211212
122122152112
121221212212
112121221221
211232212221
211211212221
221121121221
222321121212
221212112121
221221211212
152212122112
121212212212
112121522122
112112122212
211211212212
221151212122
212121121212
212212112121
216212112121
212212121212
121212125212
121121222122
112112122122
211232121222
121211212122
212121121212
212521121212
122121212121
212122121212
152121221212
121121221221
212115212221
212112121222
121211211222
122151211221
221221121122
121221212121
215212212121
211212212212
121121522212
121121212221
212112112212
221214112122
221211211212
221212121121
221252121211
212212212121
211212212212
151212122212
121121122122""".split()
MONTH_TOTALS = {1: 29, 2: 30, 3: 58, 4: 59, 5: 59, 6: 60}

# id suffix, name, helper, source line, query prefix, output column count.
_BRANCHES = (
    ("lotto", "이번주 로또un", "lotto_unse", 77, "lotto", 3),
    ("eroticwoto", "오늘의 섹스un", "game_unse", 86, "ssswto", 5),
    ("sexwoman", "오늘의 섹스감도", "game_unse", 106, "sssw", 3),
    ("horse", "오늘의 경마un", "horse_unse", 122, "ho-race", 3),
    ("birth_flower", "탄생화un", "birth_flower", 130, "datefl", 3),
    ("blood_blood", "혈액형 궁합", "blood_pair", 138, "bloodkh-", 6),
    ("flower", "플라워un", "flower", 149, "flower", 3),
    ("game", "오늘의 게임un", "game_unse", 157, "game", 3),
    ("jugan_unse", "주간un", "jugan_unse", 165, "w", 2),
    ("prince_date", "왕자의 오늘 데이트", "princess_date", 172, "wdate", 3),
    ("prince_love_today", "왕자의 오늘 사랑", "princess_love", 180, "wlove", 5),
    ("prince_today", "왕자의 오늘un", "princess_nolmal", 190, "Wto", 4),
    ("princess_date", "공주의 오늘 데이트", "princess_date", 199, "kdatew", 3),
    ("princess_love_today", "공주의 오늘 사랑", "princess_love", 207, "kglove", 5),
    ("princess_today", "공주의 오늘un", "princess_nolmal", 217, "kto", 5),
    ("star_un", "별자리un", "star_unse", 227, "stara", 5),
    ("firstdate", "첫 데이트 궁합", "gunghab", 237, "fdate", 6),
    ("firstsex", "첫 섹스 만족도", "deepsex", 248, "fsex", 5),
    ("gostop", "오늘의 고스톱un", "game_unse", 258, "gostop", 3),
    ("gunghap", "궁합", "gunghab", 266, "mw", 1),
    ("leisure", "오늘의 레저un", "yupgi1_unse", 272, "leisure", 4),
    ("life_all", "평생사주", "life_all", 281, "sa", 6),
    ("sok_gonghap", "속궁합", "deepsex", 292, "lovekh", 4),
    ("star_blood", "별자리와 혈액형 심리", "star_blood", 301, "star", 4),
    ("today_date_unse", "오늘의 데이트un", "date_unse", 310, "date", 3),
    ("yupgi_dosa", "오늘의 엽기un", "yupgi1_unse", 318, "today", 6)
)
_PAIRED = {
    "prince_date", "princess_date", "firstdate", "firstsex", "gunghap",
    "sok_gonghap", "today_date_unse"
}
_UNASSIGNED_CALENDAR = {
    "lotto", "birth_flower", "flower", "game", "jugan_unse", "prince_date",
    "prince_love_today", "prince_today", "princess_date", "princess_love_today",
    "princess_today", "star_un", "firstdate", "yupgi_dosa"
}


def _metadata(branch: tuple) -> dict:
    suffix, name, helper, line, prefix, count = branch
    example: dict = {}
    help_text: dict = {}
    if suffix == "blood_blood":
        example = {"user1_blood": "A", "user2_blood": "B"}
        help_text = {
            "user1_blood": "첫 번째 혈액형: A, B, O, AB. 원본 남자 칸입니다.",
            "user2_blood": "두 번째 혈액형: A, B, O, AB. 원본 여자 칸이며 순서를 보존합니다."
        }
    else:
        help_text["legacy_sex"] = "선택: 원본 입력 코드 0/1/2. 기본 male=1, female=2이며 0은 원본 helper 재현용입니다."
    if suffix in _PAIRED:
        help_text["partner_legacy_sex"] = "선택: 상대 원본 입력 코드 0/1/2. 기본 male=1, female=2입니다."
    if suffix == "star_blood":
        example["user_blood"] = "A"
        help_text["user_blood"] = "본인 혈액형: A, B, O, AB. 원본 helper의 성별·별자리 결합 코드를 계산합니다."
    if suffix in {"lotto", "horse"}:
        help_text["server_date"] = "선택: 원본 Date()를 재현할 YYYY-MM-DD. 생략하면 한국시간 오늘이며, 이 날짜의 주 월요일 '일'만 계산에 사용합니다."
    if suffix == "horse":
        help_text["option_name"] = "원본 입력값을 기록합니다. 원본 horse 분기의 day_oo는 미할당 Empty=0이므로 sat 입력도 계산을 바꾸지 않습니다."
    if suffix in _UNASSIGNED_CALENDAR:
        help_text["source_profile"] = "기본 asp_ui: 음력 요청은 원본 달력인자 미할당 때문에 422. asp_original_unconverted를 명시하면 음력 숫자를 변환 없이 쓰던 원본 동작만 재현합니다."
    return {
        "name": name,
        "requires_birth": suffix != "blood_blood",
        "requires_partner": suffix in _PAIRED,
        "uses_saju": False,
        "example_parameters": example,
        "parameter_help": help_text,
        "ready": True,
        "source": f"{SOURCE}:{line}",
        "source_profile": PROFILE,
        "source_limits": [
            "원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.",
            "선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.",
            "음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.",
            "명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다."
        ],
        "_branch": suffix,
        "_helper": helper,
        "_prefix": prefix,
        "_count": count
    }


SERVICES = {
    "loveunse-" + branch[0].replace("_", "-"): _metadata(branch)
    for branch in _BRANCHES
}


def vb_mod(number: int, divisor: int) -> int:
    """VB integer Mod truncates toward zero; Python % instead floors negatives."""
    quotient = abs(number) // abs(divisor)
    if (number < 0) != (divisor < 0):
        quotient = -quotient
    return number - quotient * divisor


def _padded(number: int, width: int = 3) -> str:
    # Source concatenates zeros before the sign (e.g. -2 -> '00-2').
    if number < 10:
        return "0" * (width - 1) + str(number)
    if number < 100:
        return "0" * (width - 2) + str(number)
    if width == 4 and 101 <= number < 1000:
        return "0" + str(number)
    return str(number)


def lunar_to_solar(year: int, month: int, day: int) -> date:
    """Original lun2sol:722-1057, regular month only (source leapyes=0)."""
    if not 1841 <= year < 1841 + len(LUNAR_MONTH_CODES):
        raise DomainError(
            "loveunse_lunar_year_out_of_range",
            "이 원본 loveunse 음력 변환 배열은 1841~2043년만 지원합니다. 양력으로 입력해 주세요."
        )
    codes = LUNAR_MONTH_CODES[year - 1841]
    code = int(codes[month - 1])
    regular_days = 29 if code in {1, 3, 4} else 30
    if not 1 <= day <= regular_days:
        raise DomainError(
            "invalid_loveunse_lunar_date",
            "원본 loveunse 달력 배열에 없는 평달 날짜입니다. 양력 또는 원본 날짜를 확인해 주세요."
        )
    total = sum(
        MONTH_TOTALS[int(value)]
        for row in LUNAR_MONTH_CODES[: year - 1841]
        for value in row
    )
    total += sum(MONTH_TOTALS[int(value)] for value in codes[: month - 1])
    # Source td = prior days + lunar day + 22; January 1 has td=1.
    return date(1841, 1, 1) + timedelta(days=total + day + 21)


def _sex(birth: Birth, parameters: dict, parameter: str) -> int:
    value = parameters.get(parameter, 1 if birth.gender == "male" else 2)
    if type(value) is not int or value not in {0, 1, 2}:
        raise DomainError("invalid_service_parameters", f"{parameter}는 숫자 0, 1, 2 중 하나여야 합니다.")
    return value


def _birth_parts(birth: Birth, suffix: str, parameters: dict, side: str) -> tuple[tuple, dict]:
    profile = parameters.get("source_profile", "asp_ui")
    if not isinstance(profile, str) or profile not in {"asp_ui", "asp_original_unconverted"}:
        raise DomainError("invalid_service_parameters", "지원하는 source_profile은 asp_ui 또는 asp_original_unconverted입니다.")
    unassigned = suffix in _UNASSIGNED_CALENDAR
    if profile == "asp_original_unconverted" and not unassigned:
        raise DomainError("invalid_service_parameters", "이 분기는 원본 달력 인자를 전달하므로 미변환 프로필을 적용할 수 없습니다.")
    y, m, d = birth.year, birth.month, birth.day
    calendar_action = "solar_input"
    if birth.calendar == "lunar":
        if unassigned:
            if profile != "asp_original_unconverted":
                raise DomainError(
                    "loveunse_calendar_argument_unassigned",
                    "이 ASP 분기는 음력 변환 인자가 미할당입니다. 양력으로 입력하거나 source_profile=asp_original_unconverted로 원본 미변환 동작을 명시해 주세요."
                )
            calendar_action = "explicit_original_unconverted_lunar_digits"
        else:
            if birth.leap_month:
                raise DomainError(
                    "unsupported_loveunse_leap_month",
                    "이 원본 loveunse 변환 함수는 leapyes=0으로 고정되어 윤달을 지원하지 않습니다. 양력으로 입력해 주세요."
                )
            converted = lunar_to_solar(y, m, d)
            y, m, d = converted.year, converted.month, converted.day
            calendar_action = "original_lun2sol_regular_month_array"
    parameter = "legacy_sex" if side == "self" else "partner_legacy_sex"
    sex = _sex(birth, parameters, parameter)
    return (y % 100, m, d, birth.hour, sex), {
        "calendar_action": calendar_action,
        "calendar_argument": "unassigned_VB_Empty" if unassigned else "user_calendar",
        "source_sex_code": sex,
        "minute_used": False
    }


def source_birth_dates(service_id: str, request: ServiceRequest) -> list[date]:
    """Validate used births with this service's original calendar, never tb_manse.

    An explicit unconverted profile preserves arithmetic digits after validation;
    it does not make an impossible lunar date or a future birth valid.
    """
    metadata = SERVICES[service_id]
    suffix = metadata["_branch"]
    people = []
    if metadata["requires_birth"]:
        people.append((request.birth, "self"))
    if metadata["requires_partner"]:
        people.append((request.partner, "partner"))
    result = []
    for birth, side in people:
        if birth is None:
            raise DomainError("birth_required" if side == "self" else "partner_required", "해당 서비스의 생년월일 입력이 필요합니다.")
        # Keep asp_ui's missing calendar-argument error before any conversion.
        _birth_parts(birth, suffix, request.parameters, side)
        if birth.calendar == "lunar":
            if birth.leap_month:
                raise DomainError("unsupported_loveunse_leap_month", "이 원본 loveunse 날짜 검증은 평달만 지원합니다. 윤달은 양력으로 입력해 주세요.")
            result.append(lunar_to_solar(birth.year, birth.month, birth.day))
        else:
            result.append(date(birth.year, birth.month, birth.day))
    return result


def _base(parts: tuple) -> int:
    yy, month, day, hour, sex = parts
    return 5 * yy + 3 * month + day + 7 * hour + sex


def _pair_base(parts: tuple, date_only: bool = False, princess: bool = False) -> int:
    yy, month, day, hour, sex = parts
    female_formula = sex == 2 if princess else sex == 0
    if female_formula:
        return 5 * yy + 3 * month + day + (0 if date_only else 7 * hour)
    if date_only:
        return 7 * yy + 5 * month + 3 * day
    return yy + 3 * month + 5 * day + 7 * hour


def _zodiac(month: int, day: int) -> tuple[int, str]:
    mmdd = 100 * month + day
    for start, stop, number, label in (
        (321, 420, 1, "양"), (420, 521, 2, "황소"), (521, 622, 3, "쌍둥이"),
        (622, 723, 4, "게"), (723, 823, 5, "사자"), (823, 923, 6, "처녀"),
        (923, 1024, 7, "천평"), (1024, 1123, 8, "전갈"), (1123, 1222, 9, "궁수"),
        (120, 219, 11, "물병"), (219, 321, 12, "물고기")
    ):
        if start <= mmdd < stop:
            return number, label
    return 10, "염소"


def _blood(parameters: dict, key: str) -> str:
    value = parameters.get(key)
    if not isinstance(value, str) or value.upper() not in {"A", "B", "O", "AB"}:
        raise DomainError("invalid_service_parameters", f"{key}에 A, B, O, AB 중 하나를 입력해 주세요.")
    return value.upper()


def _server_date(parameters: dict) -> date:
    value = parameters.get("server_date")
    if value is None:
        return datetime.now(KST).date()
    if not isinstance(value, str):
        raise DomainError("invalid_service_parameters", "server_date는 YYYY-MM-DD 문자열이어야 합니다.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DomainError("invalid_service_parameters", "server_date는 유효한 YYYY-MM-DD 날짜여야 합니다.") from exc


def decide(
    service_id: str,
    request: ServiceRequest,
    saju: SajuResult | None = None,
    partner: SajuResult | None = None
) -> dict:
    """Return source facts and ordered narrative selectors, without AI/DB work."""
    if service_id not in SERVICES:
        raise DomainError("unsupported_service", "이 모듈에 이식되지 않은 loveunse 서비스입니다.")
    metadata = SERVICES[service_id]
    suffix = metadata["_branch"]
    parameters = request.parameters
    unknown = set(parameters) - set(metadata["parameter_help"])
    if unknown:
        raise DomainError("invalid_service_parameters", "이 loveunse 분기에서 지원하지 않는 parameters 항목이 있습니다.")
    if metadata["requires_birth"] and request.birth is None:
        raise DomainError("birth_required", "이 서비스에는 birth가 필요합니다.")
    if metadata["requires_partner"] and request.partner is None:
        raise DomainError("partner_required", "이 서비스에는 partner가 필요합니다.")

    facts = {
        "source_profile": PROFILE,
        "helper": metadata["_helper"],
        "selector_is_score": False,
        "interpretation_limit": "선택키는 문구 분류입니다. 키에서 길흉·점수·확률을 추정하지 않습니다.",
        "output_order": "content1부터 원본 필드 순서",
        "heading_source": "원본 항목 제목은 이미지 자산이며 텍스트 제목을 임의 복원하지 않습니다."
    }
    target = request.target_date
    target_term = (target.year - 2000) + 3 * target.month + 5 * target.day
    prefix = metadata["_prefix"]
    table = "hm_" + suffix

    if suffix == "blood_blood":
        first = _blood(parameters, "user1_blood")
        second = _blood(parameters, "user2_blood")
        number = first + "-" + second
        facts["ordered_blood_types"] = [first, second]
    else:
        parts, profile_facts = _birth_parts(request.birth, suffix, parameters, "self")
        facts["self_profile"] = profile_facts
        if suffix in {"eroticwoto", "sexwoman"}:
            # main_end:49-56 forces helper sex=9 after using UI sex for table.
            if parts[4] == 1:
                table = "hm_" + ("eroticman" if suffix == "eroticwoto" else "sexman")
                prefix = "sssmto" if suffix == "eroticwoto" else "sssm"
            parts = (*parts[:4], 9)
            facts["helper_sex_code"] = 9
        base = _base(parts)
        facts["weighted_birth_total"] = base

        if suffix in {"lotto", "horse"}:
            server_day = _server_date(parameters)
            monday = server_day - timedelta(days=server_day.weekday())
            mixed_term = target.year - 2000 + 3 * target.month + 5 * monday.day
            number = _padded(vb_mod(base + mixed_term, 12))
            facts["server_week"] = {
                "date": server_day.isoformat(),
                "monday": monday.isoformat(),
                "used_monday_day": monday.day,
                "target_year_month_retained": True,
                "default_clock": "UTC+09:00"
            }
            if suffix == "horse":
                facts["source_day_oo"] = "VB_Empty_as_zero"
                facts["option_name_effect"] = "none_in_original_horse_branch"
        elif suffix == "birth_flower":
            number = f"{parts[1]:02d}{parts[2]:02d}"
        elif suffix in {"star_un", "star_blood"}:
            zodiac_number, zodiac_name = _zodiac(parts[1], parts[2])
            facts["zodiac"] = {"number": zodiac_number, "name": zodiac_name}
            if suffix == "star_un":
                number = f"{zodiac_number:03d}"
            else:
                blood = _blood(parameters, "user_blood")
                sex_digit = "1" if parts[4] == 2 else "2"
                blood_digit = {"A": "1", "O": "2", "B": "3", "AB": "4"}[blood]
                number = f"{zodiac_number:02d}" + sex_digit + blood_digit
                if number == "0412":
                    number = "0714"
                    facts["source_code_remap"] = "0412 -> 0714 (helper:289)"
                facts["blood_type"] = blood
        elif suffix in _PAIRED:
            other, other_facts = _birth_parts(request.partner, suffix, parameters, "partner")
            facts["partner_profile"] = other_facts
            if suffix in {"prince_date", "princess_date"}:
                value = _pair_base(other, date_only=True, princess=True) + target_term
                number = _padded(vb_mod(value, 30), 4)
                facts["source_assignment_rule"] = "partner_replaces_self_total (helper:565-568)"
            elif suffix == "today_date_unse":
                value = _pair_base(parts, date_only=True) + _pair_base(other, date_only=True)
                number = _padded(vb_mod(value + target_term, 12), 4)
                is_male = parts[4] == 1
                table += "_man" if is_male else "_woman"
                prefix += "m" if is_male else "w"
            else:
                value = _pair_base(parts) + _pair_base(other)
                modulus = 60 if suffix in {"firstdate", "gunghap"} else 12
                number = _padded(vb_mod(value, modulus))
                facts["original_gender_condition"] = "sex == 0, else (UI codes 1 and 2 both take else)"
        elif suffix == "life_all":
            number = _padded(vb_mod(base, 60))
        elif suffix == "jugan_unse":
            first = target.replace(day=1)
            sunday_offset = (first.weekday() + 1) % 7
            week = (target.day - 1 + sunday_offset) // 7 + 1
            value = base + target.year - 2000 + 3 * target.month + 5 * week
            number = _padded(vb_mod(value, 36))
            facts["source_week_number"] = week
        else:
            value = base + target_term
            if suffix in {"prince_love_today", "princess_love_today"}:
                value = abs(value)  # Replace(number, "-", ""), helper:600.
            modulus = 72 if suffix == "flower" else 12
            if suffix in {"prince_today", "princess_today"}:
                modulus = 60
            number = _padded(vb_mod(value, modulus))

    facts["selector_number"] = number
    selector = {
        "id": service_id + ":content",
        "table": table,
        "where": {"code": prefix + number},
        "columns": [f"content{i}" for i in range(1, metadata["_count"] + 1)],
        "purpose": "원본 순서의 문구 항목만 AI로 작성합니다. 선택키는 점수나 확률로 해석하지 않습니다.",
        "role": "narrative",
        "narrative": True
    }
    return {
        "source": metadata["source"] + "; " + HELPER,
        "facts": facts,
        "selectors": [selector],
        "unresolved": []
    }

"""CR-021 / T-041: errors that describe the user's action, not implementation."""

import re

from app.errors import DomainError

_PRIVATE = re.compile(r"asp|\.asp|legacy|source_|원본|이식|미할당|재현|VB_|COM\b|DLL\b", re.IGNORECASE)
_MESSAGES = {
    "loveunse_calendar_argument_unassigned": "이 콘텐츠의 음력 생일은 양력으로 입력하거나 birth_profile=as_entered를 선택하세요. as_entered는 입력한 월·일 숫자를 그대로 사용합니다.",
    "interlife_raw_lunar_zodiac": "별자리는 양력 생일로 계산합니다. 입력한 월·일 숫자를 그대로 사용하려면 birth_profile=as_entered를 선택하세요.",
    "unsupported_loveunse_leap_month": "이 콘텐츠는 음력 윤달을 지원하지 않습니다. 양력 생일로 입력하세요.",
    "loveunse_lunar_year_out_of_range": "이 콘텐츠의 음력 변환은 1841~2043년을 지원합니다. 양력 생일로 입력하세요.",
    "invalid_loveunse_lunar_date": "존재하지 않는 음력 날짜입니다. 생일을 확인하거나 양력으로 입력하세요."
}


def public_error(error: DomainError) -> tuple[int, dict]:
    status, code, message = error.status, error.code, error.message
    if code.startswith("legacy_"):
        status, code, message = 503, "result_unavailable", "현재 이 요청의 결과를 제공할 수 없습니다."
    elif code in _MESSAGES:
        message = _MESSAGES[code]
    elif _PRIVATE.search(code) or _PRIVATE.search(message):
        if status == 503:
            code, message = "result_unavailable", "현재 이 요청의 결과를 제공할 수 없습니다."
        else:
            if _PRIVATE.search(code):
                code = "invalid_service_parameters" if status == 422 else "request_failed"
            message = "입력값의 이름·형식·허용 범위를 확인하세요." if status == 422 else "요청 결과를 생성하지 못했습니다."
    return status, {"error": {"code": code, "message": message}}

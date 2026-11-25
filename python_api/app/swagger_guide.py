"""CR-002 / T-009: Korean Swagger labels, examples, and execution guide."""

from copy import deepcopy

from app.fortunes import SOURCE_SERVICE_NAMES
from app.models import FortuneKind
from app.service_offerings import (
    CALCULATION_TAG,
    DIAGNOSTIC_TAG,
    OTHER_TAG,
    SERVICE_TAG,
    service_offering_description,
)

READY_TAG = SERVICE_TAG
WAITING_TAG = DIAGNOSTIC_TAG
WAITING_KINDS = {FortuneKind.compatibility}
MANSE_GUIDE = (
    "생년월일시의 지원 범위는 1900~2050년입니다. "
    "음력은 일반 달과 윤달을 구분하여 입력하세요. 존재하지 않는 음력 날짜는 422 invalid_lunar_date, "
    "양력 날짜를 하나로 확정할 수 없는 경우는 422 ambiguous_lunar_date로 응답합니다."
)

TAGS = [
    {
        "name": SERVICE_TAG,
        "description": "개인 사주·연도·생일에 따른 운세 본문을 제공하는 대표 API입니다. "
        "같은 운세의 대표 API만 모았습니다. 첫 번째 AI 본문 생성 예시를 실행하고 응답 content에서 결과 글을 확인하세요. "
        "현재 결과를 제공할 수 있는 항목만 표시합니다. "
        "개별 설명의 양력·상대방 입력 등 조건을 확인하세요.",
    },
    {"name": "시작 안내", "description": "un별 한글 이름과 호출 경로를 확인합니다."},
    {
        "name": "사주 계산",
        "description": "un 해석 전에 사주팔자와 음양력 변환을 확인할 수 있습니다. " + MANSE_GUIDE,
    },
    {
        "name": OTHER_TAG,
        "description": "오락·일반 조언형 콘텐츠와 다른 호출 경로입니다. 개별 설명의 해석 범위를 확인하세요.",
    },
    {
        "name": CALCULATION_TAG,
        "description": "음양력 변환 등 계산 결과만 제공하는 도구입니다. 운세 본문을 생성하지 않습니다.",
    },
    {
        "name": "공통 호출",
        "description": "API 코드로 운세 종류를 선택하는 공통 호출 경로입니다.",
    },
    {"name": "서버 상태", "description": "로컬 서버와 AI 설정 여부를 확인합니다. 키 값은 표시하지 않습니다."},
]

GUIDES = {
    FortuneKind.daily: "조회 날짜의 **오늘·어제·내일 un과 당일 8항목 점수**를 제공합니다. `target_date`를 바꾸면 그 날짜를 기준으로 계산합니다.",
    FortuneKind.weekly: "조회 날짜가 속한 **일요일~토요일 한 주**를 해석합니다. 날짜별 점수·별점과 주간 총평을 제공합니다.",
    FortuneKind.monthly: "조회 날짜가 속한 **절기 기준 월간 un**을 해석합니다. 월간 기간은 절입 날짜를 기준으로 합니다. 1900-01-01~01-05는 월간 경계 자료가 없어 422 calendar_boundary_unavailable로 응답합니다.",
    FortuneKind.lifetime: "사주·십격·당사주에 따른 **평생 사주 13개 해석 항목**을 제공합니다. 성향·사회생활·생애 흐름·재물 등의 주제를 다룹니다.",
    FortuneKind.wealth: "년·월·일·시주에 따른 **초년·장년·중년·말년 재물운 4개 항목**을 해석합니다.",
    FortuneKind.love: "**인연의 시기·성격·직업·만날 장소·사랑 스타일**의 5개 항목을 해석합니다. 생년월일시와 성별을 입력합니다.",
    FortuneKind.biorhythm: "출생일부터 조회 날짜까지의 일수로 **신체 23일·감성 28일·지성 33일 주기**를 계산하고 해석합니다. 실제 건강 상태나 사고 확률을 측정하는 값은 아닙니다.",
    FortuneKind.yearly: "**사주 기반 AI 연간 해석입니다.** 개인 사주와 대상 연도 간지·십성 관계를 근거로 AI가 본문을 작성합니다. 기본 예시는 `target_date=2027-01-01`이며 1900~2050년을 지원합니다. **별점·점수·부적은 제공하지 않습니다.** 양력 연도 전체를 안내하며 대표 간지는 입춘 이후 7월 1일 기준입니다.",
    FortuneKind.compatibility: "본인 `birth`와 상대방 `partner`의 생년월일시를 모두 입력합니다. 현재 필요한 궁합 분류 자료가 준비되지 않아 **최종 궁합 본문은 제공하지 않습니다.** AI 해석 요청은 503으로 응답합니다.",
}

BASE_BIRTH = {
    "year": 1990,
    "month": 5,
    "day": 17,
    "hour": 14,
    "minute": 30,
    "calendar": "solar",
    "leap_month": False,
    "gender": "male",
}


def fortune_examples(kind: FortuneKind) -> dict:
    body = {"birth": deepcopy(BASE_BIRTH), "target_date": "2026-11-02", "include_ai": False}
    if kind == FortuneKind.yearly:
        body["target_date"] = "2027-01-01"
    if kind == FortuneKind.compatibility:
        body["partner"] = {**BASE_BIRTH, "year": 1992, "gender": "female"}
    name = "연간 un · 사주 기반 AI 해석" if kind == FortuneKind.yearly else SOURCE_SERVICE_NAMES[kind].replace("운세", "un")
    waiting = kind in WAITING_KINDS
    calculation = {
        "calculation_only": {
            "summary": f"{name} · {'현재 미지원' if waiting else '계산만 확인'} (AI 연결 불필요)",
            "description": "생년월일시와 조회 날짜를 수정한 뒤 Execute를 누르세요. "
            + (
                "현재 최종 운세를 제공하지 않아 503 result_unavailable로 응답합니다."
                if waiting
                else "AI를 호출하지 않습니다. result에서 계산 결과를 확인합니다."
            ),
            "value": body,
        }
    }
    if waiting:
        return calculation
    return {
        "with_ai": {
            "summary": f"{name} · 실제 AI un 내용 받기 (추천 · AI 연결 설정 필요)",
            "description": "응답 content가 실제 해석 본문이며 interpretation.sections는 항목별 해석, result는 계산 결과입니다. "
            "AI 연결이 준비되지 않은 서버는 503 ai_not_configured로 응답합니다.",
            "value": {**deepcopy(body), "include_ai": True},
        },
        **calculation,
    }


def fortune_description(kind: FortuneKind) -> str:
    guide = GUIDES[kind] + "\n\n" + MANSE_GUIDE
    execution = (
        """
### 실행 방법
현재 최종 운세를 제공하지 않아 503 result_unavailable로 응답합니다.
"""
        if kind in WAITING_KINDS
        else """
### 실제 un 내용 받기
1. **Try it out → Examples**에서 첫 번째 **실제 AI un 내용 받기**를 선택합니다. `include_ai: true`입니다.
2. `birth`의 생년월일시·성별과 `target_date`를 수정하고 **Execute**를 누릅니다.
3. **Response body → content**에서 요약·항목별 해석·조언이 이어진 본문을 읽습니다.

AI 연결이 준비되지 않은 서버는 `503 ai_not_configured`로 응답합니다. 계산 결과만 확인할 때는 두 번째 **계산만 확인** 예시를 선택하세요. 이 경우 `include_ai: false`이며 AI 문장을 생성하지 않습니다.
"""
    )
    selected_guide = service_offering_description(f"/v1/fortunes/{kind.value}")
    return (selected_guide + "\n\n" if selected_guide else "") + guide + "\n" + execution + """
### 응답에서 볼 항목
- `content`: 실제 AI가 작성한 un 본문. 요약·항목별 해석·조언을 한 문자열로 제공합니다.
- `interpretation`: 요약·항목별 해석·실천 조언으로 나눈 결과
- `interpretation.sections`: topic과 text로 나눈 항목별 해석
- `result`: 사주·점수·주기 등 해당 운세의 계산 결과
- `result.saju.pillars`: 계산한 사주팔자 (`hangul`은 한글 간지)

계산만 요청하면 운세 본문 없이 `result`를 제공합니다.
`calendar`: `solar`=양력, `lunar`=음력. `gender`: `male`=남성, `female`=여성.
윤달은 음력에서만 `leap_month: true`로 지정합니다. 출생·조회 날짜의 지원 범위는 1900~2050년입니다.
"""


def generic_examples() -> dict:
    return {
        kind.value: {
            **fortune_examples(kind)["calculation_only"],
            "description": f"위 kind 경로 매개변수에서 {kind.value}를 직접 선택하세요. "
            "이 공통 경로의 예시는 include_ai=false 계산 전용입니다. AI 본문은 include_ai=true로 요청하거나 위의 개별 un 예시를 사용하세요. Examples 선택만으로 kind 값이 자동 변경되지는 않습니다.",
        }
        for kind in FortuneKind if kind not in WAITING_KINDS
    }


SAJU_EXAMPLES = {
    "solar": {
        "summary": "양력 생일로 사주 계산",
        "description": "생년월일시의 절입·일주·시주 경계를 적용하여 사주팔자를 계산합니다.",
        "value": {"birth": deepcopy(BASE_BIRTH), "calculation_profile": "dotong"},
    },
    "lunar_leap": {
        "summary": "음력·윤달 생일로 사주 계산",
        "description": "음력 날짜의 후보 행을 조회한 뒤 검증된 교정표를 적용하고 윤달 여부를 구분합니다. 존재하지 않는 윤달 날짜는 거절합니다.",
        "value": {
            "birth": {
                **BASE_BIRTH,
                "year": 2023,
                "month": 2,
                "day": 1,
                "calendar": "lunar",
                "leap_month": True,
            },
            "calculation_profile": "dotong",
        },
    },
    "corrected_lunar_leap": {
        "summary": "윤달 표시 교정 확인 · 2023년 윤2월 29일",
        "description": "음력 윤2월 29일의 양력은 2023-04-19이며 일반 2월 29일은 2023-03-20입니다.",
        "value": {
            "birth": {
                **BASE_BIRTH,
                "year": 2023,
                "month": 2,
                "day": 29,
                "calendar": "lunar",
                "leap_month": True,
            },
            "calculation_profile": "dotong",
        },
    },
}

ERROR_RESPONSES = {
    401: {"description": "API_KEY가 설정된 서버에서 X-API-Key가 없거나 올바르지 않습니다."},
    429: {"description": "Woonari의 한국시간 일일 AI 호출 시도 한도에 도달했습니다. 다음 날 00:00 이후 다시 요청하세요. 계산만 확인하려면 include_ai=false를 사용하세요."},
    422: {
        "description": "입력 오류, 확정할 수 없는 음력 날짜 또는 월간 절입 경계 자료가 없는 경우입니다.",
        "content": {
            "application/json": {
                "examples": {
                    "ambiguous_lunar_date": {
                        "summary": "음력 날짜 중복",
                        "value": {
                            "error": {
                                "code": "ambiguous_lunar_date",
                                "message": "양력 날짜를 확정할 수 없습니다. 양력 생년월일로 입력해 주세요."
                            }
                        }
                    },
                    "calendar_boundary_unavailable": {
                        "summary": "월간 표시 범위의 이전·다음 절입 부재",
                        "value": {
                            "error": {
                                "code": "calendar_boundary_unavailable",
                                "message": "선택한 날짜의 월간 기간을 계산할 수 없습니다. 다른 조회 날짜를 입력해 주세요."
                            }
                        }
                    }
                }
            }
        }
    },
    502: {"description": "AI 응답을 처리하지 못했습니다."},
    503: {
        "description": "현재 계산 또는 AI 연결을 사용할 수 없거나 해당 결과를 지원하지 않는 경우입니다.",
        "content": {
            "application/json": {
                "examples": {
                    "manse_unavailable": {
                        "summary": "사주 계산을 일시적으로 사용할 수 없음",
                        "value": {
                            "error": {
                                "code": "manse_unavailable",
                                "message": "현재 사주 계산을 사용할 수 없습니다. 잠시 후 다시 요청해 주세요."
                            }
                        }
                    },
                    "ai_not_configured": {
                        "summary": "AI 연결 준비 필요",
                        "value": {
                            "error": {
                                "code": "ai_not_configured",
                                "message": "현재 AI 해석을 사용할 수 없습니다. 잠시 후 다시 요청해 주세요.",
                            }
                        },
                    },
                    "result_unavailable": {
                        "summary": "현재 결과를 제공하지 않는 항목",
                        "value": {
                            "error": {
                                "code": "result_unavailable",
                                "message": "현재 이 운세의 결과를 제공할 수 없습니다.",
                            }
                        },
                    },
                }
            }
        },
    },
    504: {"description": "AI 응답 대기 시간이 초과되었습니다."},
}

_ROWS = "\n".join(
    f"| {'연간 un' if k == FortuneKind.yearly else SOURCE_SERVICE_NAMES[k].replace('운세', 'un')} | {k.value} |"
    for k in FortuneKind if k not in WAITING_KINDS
)
DESCRIPTION = (
    """## un API 사용 안내

**서비스 운세 · AI 본문 제공** 그룹에서 원하는 운세를 펼치세요.
**GET /v1/un-services**에서 운세 이름·호출 경로·필요한 입력을 확인할 수 있습니다.

1. **Try it out → Examples**에서 첫 번째 **실제 AI un 내용 받기** 예시를 선택합니다. `include_ai: true`입니다.
2. 생년월일시 `birth`와 조회 기준일 `target_date`를 수정합니다. 두 사람의 정보가 필요한 항목은 `partner`도 입력합니다.
3. **Execute**를 누른 뒤 `content`에서 운세 본문을 읽습니다. `interpretation.sections`는 주제·본문으로 나눈 해석이며 `result`는 계산 결과입니다.

두 번째 **계산만 확인** 예시는 `include_ai: false`입니다. AI 본문 없이 `result`를 제공합니다.
`/v1/saju`는 사주팔자·음양력 변환 계산용입니다.

## 기본 운세

| 한글 이름 | API 코드 |
|---|---|
"""
    + _ROWS
    + """

연간 un은 **2027년 포함 1900~2050년**을 지원합니다. 개인 사주와 대상 연도를 해석하며 별점·점수·부적은 제공하지 않습니다.

## 입력과 호출 제한

`calendar`: `solar`=양력, `lunar`=음력. `gender`: `male`=남성, `female`=여성.
윤달은 음력에서만 `leap_month: true`로 지정합니다. 생년월일과 조회 날짜의 지원 범위는 **1900~2050년**입니다.
존재하지 않는 음력 날짜는 `422 invalid_lunar_date`, 날짜를 확정할 수 없으면 `422 ambiguous_lunar_date`입니다.
1900-01-01~01-05는 월간 기간을 계산할 수 없어 `422 calendar_boundary_unavailable`로 응답합니다.

**GET /v1/ai-usage**에서 AI 일일 사용량을 확인합니다. 한국시간 자정 기준 최대 100회이며 전송 후 오류도 차감합니다. 계산 요청은 차감하지 않습니다.
API 키를 설정한 서버에서만 `X-API-Key` 헤더를 입력합니다.
현재 지원하지 않는 결과는 `503 result_unavailable`, AI 연결이 준비되지 않은 경우는 `503 ai_not_configured`로 응답합니다.
"""
)

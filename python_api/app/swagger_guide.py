"""CR-002 / T-009: Korean Swagger labels, examples, and execution guide."""

from copy import deepcopy

from app.fortunes import CATALOG, SOURCE_SERVICE_NAMES
from app.legacy_catalog import CATALOG_TAGS
from app.models import FortuneKind
from app.restored_fortune import BACKUP_FINDING

READY_TAG = "un 테스트 · AI 해석 가능 8종"
WAITING_TAG = "un 테스트 · 원본 자료 대기 1종"
WAITING_KINDS = {FortuneKind.compatibility}
MANSE_GUIDE = (
    "사주·음양력·절입은 제공된 script.sql의 tb_manse 73,414행을 기준으로 조회합니다. "
    "공식 ./woonari 실행은 적재된 MySQL woonari.tb_manse를 사용하며 조회 실패 시 다른 달력으로 자동 대체하지 않습니다. "
    "데이터는 1900~2100년을 보존하고 공개 API 범위는 기존 1900~2050년을 유지합니다. "
    "윤달 표시 오류 10행은 검증된 lunar-leap-flags-v1 교정표를 적용해 일반 달·윤달을 정상 구분합니다. 교정 후에도 남는 중복은 422 ambiguous_lunar_date로 거부합니다."
)

TAGS = [
    {"name": "시작 안내", "description": "un별 한글 이름과 현재 테스트 가능 상태를 확인합니다."},
    {
        "name": "사주 계산",
        "description": "un 해석 전에 사주팔자와 음양력 변환을 확인할 수 있습니다. " + MANSE_GUIDE,
    },
    {
        "name": READY_TAG,
        "description": "첫 예시 include_ai=true로 실제 AI un 본문(content)을 생성합니다. 선택한 AI 제공자의 전용 인증·모델 설정이 필요하며, 두 번째 계산 전용 예시는 AI 호출 없이 근거만 확인합니다.",
    },
    {
        "name": WAITING_TAG,
        "description": "조회키와 미확보 의존성만 확인합니다. 정상적인 최종 un·AI 해석은 아직 생성할 수 없습니다.",
    },
    {
        "name": "공통 호출",
        "description": "기존 통합 경로입니다. 처음에는 위의 한글 un별 항목을 사용하세요.",
    },
    *[
        {
            "name": tag,
            "description": "ASP 원본의 실제 이름·출처·현재 문제·해결 자료를 개별 조회합니다. GET 성공은 상태 조회이며 계산 실행이 아닙니다."
            + (" 하위 서비스는 각각 별도 항목으로 표시합니다." if status == "reference" else ""),
        }
        for status, tag in CATALOG_TAGS.items()
    ],
    {"name": "서버 상태", "description": "로컬 서버와 AI 설정 여부를 확인합니다. 키 값은 표시하지 않습니다."},
]

GUIDES = {
    FortuneKind.daily: "조회 날짜의 **오늘·어제·내일 un 선택키와 8항목 점수**를 계산합니다. `target_date`를 바꾸면 그 날짜를 기준으로 계산합니다.",
    FortuneKind.weekly: "조회 날짜가 속한 **일요일~토요일 한 주**를 계산합니다. 날짜별 점수·별점과 주간 총평의 원본 분기를 확인할 수 있습니다.",
    FortuneKind.monthly: "조회 날짜가 속한 **절기 기준 월간 un**의 선택키를 계산합니다. 기간은 제공 DB의 절입 날짜를 기준으로 표시하며, 기존 manse.disp_day와의 동일성은 미검증입니다. 이전 절입이 DB에 없는 1900-01-01~01-05는 422 calendar_boundary_unavailable입니다.",
    FortuneKind.lifetime: "사주·십격·당사주에 따른 **평생 사주 13개 해석 항목**을 확인합니다. 성향·사회적 un·생애 구간·재물 관련 원본 선택키를 제공합니다.",
    FortuneKind.wealth: "년·월·일·시주에 따른 **초년·장년·중년·말년 재물운 4개 항목**을 계산합니다. 당일 재물 점수를 재활용하는 방식이 아닙니다.",
    FortuneKind.love: "**인연의 시기·성격·직업·만날 장소·사랑 스타일**의 5개 원본 출력 항목을 선택합니다. 생년월일시와 성별을 바꾸어 비교할 수 있습니다.",
    FortuneKind.biorhythm: "출생일부터 조회 날짜까지의 일수로 **신체 23일·감성 28일·지성 33일 주기**와 원본 27가지 멘트 분류를 계산합니다. 실제 건강 상태나 사고 확률을 측정하는 값은 아닙니다.",
    FortuneKind.yearly: "**사주 기반 AI 연간 해석입니다.** 기존 만세력·ASP 사주 계산과 대상 연도 간지·십성 관계를 근거로 AI가 본문을 작성합니다. 기본 예시는 `target_date=2027-01-01`이며 1900~2050년을 지원합니다. **운세 DB 본문·별점·점수·부적은 사용하지 않습니다.** `analysis.scores`는 빈 배열이고 연간 근거의 별점·점수는 null입니다. 양력 연도 전체 안내이며 대표 간지는 입춘 이후 7월 1일의 만세력 계산값입니다. 기존 연간 DB 결과 재현이나 월별 확정 예측을 뜻하지 않습니다.",
    FortuneKind.compatibility: "**진단 전용입니다.** 본인 `birth`와 상대방 `partner`의 생년월일시를 모두 입력합니다. tb_manse의 음양력·간지와 별개인 tbAisyo의 원본 27숙 분류 데이터가 없어 최종 궁합은 생성하지 않습니다. 기본 예시는 필요한 분류 조회키와 `unresolved_dependencies`를 확인하는 용도이며, AI 해석 요청은 503으로 차단됩니다.",
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
            "summary": f"{name} · {'조회키 진단만' if waiting else '계산 전용 · 근거 확인'} (AI 연결 불필요)",
            "description": "생년월일시와 조회 날짜를 수정한 뒤 Execute를 누르세요. "
            + (
                "최종 un는 미제공이며 원본 의존성을 확인합니다. content와 interpretation은 null입니다."
                if waiting
                else "AI를 호출하지 않습니다. analysis에 계산 근거만 표시되며 content와 interpretation은 null입니다."
            ),
            "value": body,
        }
    }
    if waiting:
        return calculation
    return {
        "with_ai": {
            "summary": f"{name} · 실제 AI un 내용 받기 (추천 · AI 연결 설정 필요)",
            "description": "전용 .local/woonari/api.env에서 AI_PROVIDER와 선택한 제공자의 모델·인증 설정을 확인하고 재시작하세요. 현재 연결 대상은 Amazon Bedrock의 Claude이며 명시한 전용 IAM 또는 AI 전용 장기 키를 사용합니다. "
            "응답 content가 실제 해석 본문입니다. 미설정 시 503 ai_not_configured이며 /health의 ai_missing_settings에서 필요한 항목을 확인합니다.",
            "value": {**deepcopy(body), "include_ai": True},
        },
        **calculation,
    }


def fortune_description(kind: FortuneKind) -> str:
    guide = (
        f"**원본 서비스명:** {SOURCE_SERVICE_NAMES[kind].replace('운세', 'un')}  \n"
        f"**원본 결과 파일:** `{CATALOG[kind][1]}`\n\n" + GUIDES[kind]
        + "\n\n**만세력 데이터:** " + MANSE_GUIDE
    )
    if kind == FortuneKind.lifetime:
        guide += "\n\n원본 `loveunse`의 메뉴명 '평생사주'와 구분합니다. 현재 API는 `lifeluck`의 평생 un 로직입니다."
    if kind == FortuneKind.yearly:
        guide += "\n\n**과거 ASP 결과 재현 자료의 별도 진단:** " + BACKUP_FINDING + " 현재 사주 기반 연간 AI 해석은 이 자료 대기와 무관하게 실행합니다."
    execution = (
        """
### 실행 방법
1. **Try it out**을 누르고 **Examples → 조회키 진단만**을 선택합니다.
2. `birth`와 `target_date`를 수정하고 **Execute**를 누릅니다.
3. `analysis.unresolved_dependencies`에서 필요한 원본 판정 자료를 확인합니다.

진단 전용 요청은 `include_ai: false`입니다. 최종 un 본문은 아직 생성하지 않습니다.
"""
        if kind in WAITING_KINDS
        else """
### 실제 un 내용 받기
1. 서버의 전용 `.local/woonari/api.env`에 선택한 AI 제공자의 설정을 입력하고 재시작합니다. Bedrock Claude는 `AI_PROVIDER=bedrock`, `BEDROCK_MODEL_ID`, `BEDROCK_REGION`을 사용합니다. 인증은 명시한 `BEDROCK_AUTH_MODE`에 따라 전용 IAM 프로필 또는 AI 전용 장기 키를 사용합니다.
2. **서버 상태 → GET /health**에서 `ai_configured: true`인지 확인합니다. `ai_missing_settings`에 이름이 나오면 해당 설정이 필요합니다.
3. **Try it out → Examples**에서 첫 번째 **실제 AI un 내용 받기**를 선택합니다. `include_ai: true`입니다.
4. `birth`의 생년월일시·성별과 `target_date`를 수정하고 **Execute**를 누릅니다.
5. **Response body → content**에서 요약·항목별 해석·조언이 이어진 본문을 읽습니다.

선택한 AI 제공자의 설정이 없으면 `503 ai_not_configured`입니다. 계산 근거만 점검할 때는 두 번째 **계산 전용 · 근거 확인** 예시를 선택하세요. 이 경우 `include_ai: false`이며 AI 문장을 생성하지 않습니다.
"""
    )
    return guide + "\n" + execution + """
### 응답에서 볼 항목
- `content`: 실제 AI가 작성한 un 본문. 요약·항목별 해석·조언을 한 문자열로 제공합니다.
- `interpretation`: 요약·항목·근거 참조·조언으로 나눈 구조화된 AI 해석
- `analysis`: ASP 규칙에 따른 사주·점수·판정·문구 선택키 등 계산 근거
- `analysis.saju.pillars`: 계산한 사주팔자 (`hangul`은 한글 간지)
- `analysis.ready_for_ai`: 원본 판정과 출력항목이 준비됐는지 여부. AI 키 설정 여부와는 별개입니다.
- `analysis.unresolved_dependencies`: 원본 자료가 필요한 항목

계산 전용·진단 요청에서는 `content`와 `interpretation`이 **null이 정상**입니다.
`calendar`: `solar`=양력, `lunar`=음력. `gender`: `male`=남성, `female`=여성.
윤달은 음력에서만 `leap_month: true`로 지정합니다. 출생·조회 날짜의 지원 범위는 1900~2050년입니다.
"""


def generic_examples() -> dict:
    return {
        kind.value: {
            **fortune_examples(kind)["calculation_only"],
            "description": f"위 kind 경로 매개변수에서 {kind.value}를 직접 선택하세요. "
            "이 공통 경로의 예시는 include_ai=false 계산·진단 전용입니다. 실제 AI 본문은 준비된 8종에서 include_ai=true로 요청하거나 위의 개별 un 예시를 사용하세요. Examples 선택만으로 kind 값이 자동 변경되지는 않습니다.",
        }
        for kind in FortuneKind
    }


SAJU_EXAMPLES = {
    "solar": {
        "summary": "양력 생일로 사주 계산",
        "description": "제공된 만세력 DB 행과 ASP 절입·일주·시주 경계로 계산합니다. 독립 달력으로 재계산하지 않습니다.",
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
        "description": "원본의 윤달 표시 오류를 검증된 교정표로 처리합니다. 응답 양력은 2023-04-19이며 일반 2월 29일은 2023-03-20입니다.",
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
        "description": "입력 오류·교정 후 미해결 음력키 중복·월간 절입 경계 부재. 연간 un의 2001~2014년 밖 요청도 해당합니다.",
        "content": {
            "application/json": {
                "examples": {
                    "ambiguous_lunar_date": {
                        "summary": "검증된 교정 후에도 남는 음력 날짜 중복",
                        "value": {
                            "error": {
                                "code": "ambiguous_lunar_date",
                                "message": "검증된 교정표 적용 후에도 같은 음력·윤달 날짜가 중복되어 양력 날짜를 확정할 수 없습니다. 원본 데이터를 확인해 주세요."
                            }
                        }
                    },
                    "calendar_boundary_unavailable": {
                        "summary": "월간 표시 범위의 이전·다음 절입 부재",
                        "value": {
                            "error": {
                                "code": "calendar_boundary_unavailable",
                                "message": "제공된 만세력 DB에 월간 표시 범위를 정할 이전·다음 절입 자료가 없습니다."
                            }
                        }
                    }
                }
            }
        }
    },
    502: {"description": "AI 제공자 오류 또는 원본 출력 계약에 맞지 않는 AI 응답입니다."},
    503: {
        "description": "만세력 DB 조회 불가, AI 설정·호출 권한·AWS 계정 검증 대기 또는 별도 원본 판정 자료 미확보입니다.",
        "content": {
            "application/json": {
                "examples": {
                    "manse_unavailable": {
                        "summary": "선택한 만세력 DB 조회 불가 · 자동 대체 없음",
                        "value": {
                            "error": {
                                "code": "manse_unavailable",
                                "message": "만세력 DB를 사용할 수 없습니다. 제공된 원본 데이터의 DB 구축 상태를 확인해 주세요."
                            }
                        }
                    },
                    "ai_not_configured": {
                        "summary": "선택한 AI 제공자 설정 미완료",
                        "value": {
                            "error": {
                                "code": "ai_not_configured",
                                "message": "선택한 AI 제공자의 전용 설정이 필요합니다. /health의 ai_missing_settings를 확인하세요.",
                            }
                        },
                    },
                    "bedrock_not_configured": {
                        "summary": "Bedrock 전용 모델·리전·호출 연결 미설정",
                        "value": {"error": {
                            "code": "bedrock_not_configured",
                            "message": "Woonari 전용 Bedrock 모델·리전과 AWS 호출 연결이 필요합니다. ./woonari start로 실행하세요.",
                        }},
                    },
                    "bedrock_account_verification": {
                        "summary": "AWS 계정 검증 진행 중 · Claude 실제 생성 대기",
                        "value": {"error": {
                            "code": "bedrock_account_verification",
                            "message": "AWS 계정 검증이 진행 중이어서 Bedrock 호출이 거부되었습니다. AWS 검증 완료 후 다시 실행하세요.",
                        }},
                    },
                    "bedrock_use_case_required": {
                        "summary": "Anthropic 사용 목적 양식 제출 필요",
                        "value": {"error": {
                            "code": "bedrock_use_case_required",
                            "message": "AWS Bedrock의 Anthropic 사용 목적 양식을 제출해야 Claude를 호출할 수 있습니다.",
                        }},
                    },
                    "legacy_dependency_unavailable": {
                        "summary": "원본 판정 자료 미확보",
                        "value": {
                            "error": {
                                "code": "legacy_dependency_unavailable",
                                "message": "원본 판정 의존성이 필요합니다. include_ai=false로 선택키와 unresolved_dependencies를 확인하세요.",
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
    f"| {SOURCE_SERVICE_NAMES[k].replace('운세', 'un')} | {k.value} | {'조회키 진단만 가능' if k in WAITING_KINDS else 'AI 본문 생성 가능 · 설정 필요'} |"
    for k in FortuneKind
)
DESCRIPTION = (
    """## Python 전체 실행 안내

**GET /v1/un-services**에서 현재 실행 경로와 추가 입력을 확인합니다.
**Python 추가 전환 · 계산 가능**의 한글 이름을 펼쳐 **POST /v1/un/{id}** 예시를 실행하세요.
자료 진단 항목은 `include_ai=false`로 실행해 `analysis.unresolved_dependencies`와 필요한 원본 자료를 확인합니다.
달력 계산 전용 항목에는 AI 해석을 요청하지 않습니다. ASP 파일·IIS 없이 Python 코드만으로 실행·개발합니다.

Bedrock Claude는 전용 IAM 또는 명시한 AI 전용 계정의 장기 키로 연결합니다. `BEDROCK_AUTH_MODE=api_key`는 전용 `ai/bedrock.env`의 키와 `BEDROCK_ACCOUNT_ID`를 검증합니다.
**GET /v1/ai-usage**에서 일일 사용량을 확인합니다. Woonari의 AI 모델 전송은 한국시간 자정 기준 최대 100회이며 전송 후 오류도 차감합니다. 계산 요청은 차감하지 않습니다.
`ai_configured=true`는 필수 설정 존재를 뜻하며 실제 접근 권한은 개별 AI 요청으로 확인합니다.

## 기존 10종에서 실제 un 내용 받기

**un 테스트 · AI 해석 가능 8종**에서 원하는 한글 un 이름을 펼치세요.
1. 전용 `.local/woonari/api.env`에 선택한 AI 제공자의 설정을 입력하고 `./woonari stop` / `./woonari start`로 재시작합니다. 현재 연결 대상은 **Amazon Bedrock의 Claude**입니다. `AI_PROVIDER=bedrock`, `BEDROCK_MODEL_ID`, `BEDROCK_REGION`과 `BEDROCK_AUTH_MODE`를 사용합니다. 장기 키 모드는 `BEDROCK_ACCOUNT_ID`와 전용 키 파일을 확인합니다.
2. **서버 상태 → GET /health**에서 `ai_configured: true`를 확인합니다. `ai_missing_settings`에는 누락된 설정 이름만 표시합니다.
3. **Try it out → Examples → 첫 번째 실제 AI un 내용 받기 → Execute**로 실행합니다. `include_ai: true`입니다.
4. 응답의 **`content`**에서 실제 해석 본문을 읽습니다. `interpretation`은 같은 해석의 구조화된 값이며 `analysis`는 계산 근거입니다.

`analysis.ready_for_ai`는 원본 판정과 출력항목이 준비됐는지를 뜻하며 제공자 설정 상태와는 별개입니다.
선택한 AI 제공자의 설정 미완료 시 `503 ai_not_configured`입니다. **두 번째 계산 전용 예시**는 `include_ai=false`로 AI 호출 없이 근거를 점검합니다. 이때 `content: null`, `interpretation: null`은 정상입니다.
`/health`는 설정 입력 상태를 보여줍니다. 모델 호출 권한과 실제 생성 성공은 POST 결과로 확인합니다.
`/v1/saju`는 사주팔자 계산용이며 un 해석 문장을 생성하지 않습니다.

## 기본 Python 9종

| 한글 이름 | API 코드 | 현재 상태 |
|---|---|---|
"""
    + _ROWS
    + """

**궁합은 조회키 진단 전용**이며 첫 예시는 `include_ai=false`입니다. 연간 un은 사주 기반 AI 해석으로 2027년을 지원합니다. DLL 계산이 필요했던 직업운 등11종과 관련 메뉴 진단4개는 CR-019로 제거했습니다.

## ASP 전체 항목과 문제 확인

**시작 안내 → GET /v1/asp-services**에서 원본 전체 목록을 조회합니다.
아래 **ASP 전체** 태그에서는 실제 한글 이름별 **현재 상태·문제 원인·해결 자료·원본 파일/줄**을 볼 수 있습니다.
하위 서비스, 과거 연도판, 묶음 및 보조 코드를 구분합니다. **전체 항목이 Python으로 이식된 상태는 아닙니다.**
상태 조회 GET의 200은 조회 성공이며 실제 un 생성은 POST로 실행합니다.
`ready`는 계산·해석 계약 준비, `calculation_only`는 계산 전용, `source_required`는 원본·판정 자료 또는 계산 프로필 검증이 필요하다는 뜻입니다. 미구현 항목은 `issues`에 구체적인 의존성과 미전환 범위를 표시합니다.
AI는 ASP가 확정한 판정과 출력항목을 문장으로 작성합니다. 만세력·분류·점수 데이터의 미확보 판정을 대신 만들지 않습니다.

## 사주·만세력 데이터

사용자 제공 `script.sql`의 `tb_manse` **73,414행**을 사용합니다. 공식 `./woonari` 실행은 적재된 **MySQL woonari.tb_manse**를 조회합니다.
독립 만세력 패키지로 원본 값을 대체하지 않으며 선택한 DB 조회가 실패하면 `503 manse_unavailable`입니다.
원본 데이터는 **1900~2100년**, 공개 API 지원 범위는 기존 **1900~2050년**입니다.
원본에 남아 있는 음력 중복 4건을 포함해 윤달 표시 오류 10행은 **`lunar-leap-flags-v1` 교정표**로 해결합니다. 일반 달·윤달을 구분해 입력할 수 있으며 원본 행과 해시는 보존합니다. 교정 후 미해결 중복만 `422 ambiguous_lunar_date`입니다. 존재하지 않는 윤달 30일은 `422 invalid_lunar_date`입니다. 월간 표시 범위의 이전 절입이 없는 1900-01-01~01-05는 `422 calendar_boundary_unavailable`입니다.
이 DB는 음양력·간지·절입 자료입니다. 과거 연간 `yearfortune`, 궁합 `tbAisyo`와 일부 interlife의 별도 판정 자료는 포함하지 않습니다. 연간 AI 본문은 별도 운세 DB 없이 실행하며 DLL 의존 운세는 서비스에서 제거했습니다. interlife는 항목별 이식·필요 자료 상태를 확인하세요.

생년월일시는 `birth`, 조회 기준일은 `target_date`입니다. 양력/음력과 성별 코드는 각 항목과 **Schemas**에 설명합니다.
API_KEY를 설정한 서버에서만 `X-API-Key` 헤더를 입력합니다. 로컬 기본 설정에서는 비워둡니다.
"""
)

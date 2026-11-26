# un FastAPI

생년월일시와 조회 날짜로 사주·운세를 계산하고, AI가 계산 결과에 맞는 한국어 본문을 작성합니다. API 응답에는 운세 본문과 결과 데이터만 제공합니다.

## 실행

Python 3.11 이상을 사용합니다. 준비된 작업 환경에서는 저장소 루트에서 실행합니다.

```sh
./woonari start
./woonari status
./woonari stop
```

새 환경에서는 의존성과 프로젝트 전용 설정을 준비합니다.

```sh
python3 -m venv python_api/.venv
python_api/.venv/bin/python -m pip install -r python_api/requirements.lock
./woonari init
./woonari start
```

- Swagger: <http://127.0.0.1:9090/docs>
- 프로젝트 보드: <http://127.0.0.1:18101/>
- 운세 목록과 입력 안내: `GET /v1/un-services`
- 기본 운세 목록: `GET /v1/fortunes`
- 운세 실행: `POST /v1/un/{id}` 또는 `POST /v1/fortunes/{kind}`
- 사주팔자·음양력 계산: `POST /v1/saju`
- AI 일일 사용량: `GET /v1/ai-usage`
- 서버 상태: `GET /health`

목록과 Swagger에는 현재 결과를 제공할 수 있는 항목만 표시합니다. 미지원 항목은 `503 result_unavailable`로 응답합니다.

## Swagger에서 운세 결과 보기

상단 **서비스 운세 · AI 본문 제공** 그룹에는 선별한 운세의 대표 경로를 모았습니다. [17종과 입력 조건](../docs/service-offerings.md)을 확인하세요. 현재 필요한 자료가 준비된 항목만 표시하므로 실행 환경에 따라 목록이 줄어들 수 있습니다.

1. 원하는 운세를 펼치고 **Try it out**을 누릅니다.
2. 첫 번째 **실제 AI un 내용 받기** 예시를 선택합니다. `include_ai: true`입니다.
3. `birth`와 `target_date`를 수정하고 **Execute**를 누릅니다. 두 사람의 정보가 필요한 항목에는 `partner`도 입력합니다.
4. 응답의 `content`에서 운세 본문을 읽습니다.

두 번째 **계산만 확인** 예시는 `include_ai: false`입니다. AI를 호출하지 않고 `result`만 제공합니다. 공통 `/v1/fortunes/{kind}` 경로에서는 Examples를 바꿔도 `kind`가 자동 변경되지 않으므로 코드도 직접 선택합니다.

## 응답

AI 본문을 요청하면 다음 값을 제공합니다.

| 필드 | 내용 |
|---|---|
| `content` | 요약·항목별 해석·조언을 연결한 운세 본문 |
| `interpretation.summary` | 해석 요약 |
| `interpretation.sections` | `topic`, `text`로 나눈 항목별 해석 |
| `interpretation.practical_advice` | 실천 조언 |
| `result` | 운세 종류·조회 기간·사주·점수·항목별 계산 결과 |

`include_ai: false` 요청에는 본문 없이 `result`만 제공합니다. `/v1/saju`는 `solar_birth`, `lunar_birth`, `pillars`, `day_master`, `elements`, `solar_term_window`를 반환합니다.

응답에는 출처 파일·개발 상태·이식 정보·조회 조건·내부 검증 계약을 포함하지 않습니다. 계산 및 본문 검증은 서버 내부에서 수행합니다.

## 입력 예시

```json
{
  "birth": {
    "year": 1990, "month": 5, "day": 17,
    "hour": 14, "minute": 30,
    "calendar": "solar", "leap_month": false,
    "gender": "male"
  },
  "target_date": "2027-01-01",
  "include_ai": true
}
```

`birth`의 년월일·시간·성별은 필수이며 분은 기본 0입니다. 한국시간을 사용하며 `calendar`는 `solar`=양력, `lunar`=음력, `gender`는 `male`=남성, `female`=여성입니다. 음력 윤달만 `leap_month: true`로 지정합니다. 시간을 모른다고 임의 시각으로 보정하지 않습니다.

입력 및 변환된 양력 날짜의 지원 범위는 **1900-01-01~2050-12-31**이며 `target_date`는 출생일 이후여야 합니다. 존재하지 않는 날짜·윤달은 거절합니다. 양력 날짜를 확정할 수 없는 음력 요청은 `422 ambiguous_lunar_date`입니다. 1900-01-01~01-05는 월간 기간을 계산할 수 없어 `422 calendar_boundary_unavailable`로 응답합니다.

사주 계산만 필요하면 다음과 같이 요청합니다.

```json
{
  "birth": {
    "year": 1990, "month": 5, "day": 17,
    "hour": 23, "minute": 30, "gender": "male"
  },
  "calculation_profile": "dotong"
}
```

`calculation_profile`의 기본값은 `dotong`이며 `today_inline`도 선택할 수 있습니다. 두 기준은 23:30 이후 시주의 일간 적용 방식이 다릅니다. 운세 API는 항목별 기준을 자동 적용합니다. 역사적 표준시·DST·출생지별 진태양시 보정과 해외 출생은 지원하지 않습니다.

## 연간 un

`POST /v1/fortunes/yearly`는 **2027년 포함 1900~2050년**의 연간 본문을 생성합니다. 개인 사주와 대상 연도의 간지·십성 관계를 바탕으로 양력 연도 전체를 해석합니다. 별점·점수·부적은 제공하지 않습니다.

## AI 설정과 호출 한도

공식 실행기는 이 프로젝트의 `.local/woonari/api.env`만 읽습니다. 다른 프로젝트의 키나 터미널에 상속된 설정을 사용하지 않습니다. 현재 연결 대상은 Amazon Bedrock의 Claude입니다.

```dotenv
AI_PROVIDER=bedrock
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-6
BEDROCK_REGION=ap-northeast-2
BEDROCK_AUTH_MODE=api_key
AI_DAILY_CALL_LIMIT=100
AI_TIMEOUT_SECONDS=45
AI_MAX_CONCURRENCY=4
```

모델과 리전은 실제 사용할 값으로 설정합니다. 장기 키는 `.local/woonari/ai/bedrock.env`에만 저장하며, `api.env`의 `BEDROCK_ACCOUNT_ID`에 승인된 AI 계정을 지정합니다. DB·Secrets Manager 계정과 AI 계정은 분리합니다. 전용 `iam` 모드도 지원하며 다른 인증·계정으로 자동 전환하지 않습니다. 자세한 절차는 [독립 환경 안내](../docs/isolated-environment.md)를 따릅니다.

설정 후 `./woonari stop` / `./woonari start`로 재시작합니다. `/health`의 설정 상태는 실제 모델 호출 성공과 다르며 POST 결과로 생성 여부를 확인합니다. AI 연결이 준비되지 않은 경우는 `503 ai_not_configured`, 모델 응답을 처리하지 못하면 `502`, 응답 대기 시간 초과는 `504`입니다.

AI 모델 전송 시도는 **한국시간 하루 최대 100회**입니다. 모든 경로가 같은 영속 사용량 기록을 공유하며 재시작·동시 요청·조회 날짜 변경으로 초기화되지 않습니다. 전송 후 오류도 차감합니다. `GET /v1/ai-usage`에서 사용·잔여·다음 초기화 시각을 확인할 수 있습니다. 한도 초과는 `429`이며 계산 요청·입력 오류·전송 전 차단은 차감하지 않습니다. 사용량 DB를 삭제하지 마세요.

OpenAI도 전용 `AI_PROVIDER=openai`, `OPENAI_API_KEY`, `OPENAI_MODEL`로 선택할 수 있습니다. 키는 채팅·명령 인자·소스에 기록하지 않습니다.

## 개발과 검증

공개 응답 스키마와 변환은 `app/public_models.py`, `app/public_results.py`, `app/public_catalog.py`, `app/public_errors.py`에서 관리합니다. 내부 계산·본문 검증 모델은 공개 응답과 분리되어 있습니다.

```sh
python_api/.venv/bin/python -m pytest -q python_api/tests tools
python_api/.venv/bin/ruff check python_api/app python_api/tests python_api/tools tools
node .project/_tools/project-dashboard.mjs check
```

내부 규칙·출처 관리 절차는 [Python 전용 작업 안내](../docs/python-only.md)와 [계산 규칙 관리](docs/source-rules.md)를 따릅니다. 설정·인증·키·로그·개인 입력·사용량 기록은 배포하지 않습니다.

## 소셜 로그인

카카오·구글·네이버 로그인 API를 Swagger의 **소셜 로그인 · 카카오·구글·네이버** 그룹에서 확인합니다. 로그인 시작·콜백·신규회원 생성·Bearer 토큰·내정보·갱신·로그아웃을 제공합니다. `./woonari auth init|status`로 전용 앱 설정을 준비하고 `./woonari db init-auth`로 신규 인증 표를 생성합니다. 실제 로그인은 앱 키 설정 후 확인합니다. [설정과 호출 가이드](../docs/social-login.md)

**회원 사주 정보** 그룹의 `GET/PUT/PATCH /v1/auth/me/birth`로 본인의 생년월일·태어난 시/분·성별·양력/음력·윤달 정보를 관리합니다. Bearer 인증이 필요하며 PUT은 최초 저장·전체 교체, PATCH는 저장값의 일부 수정입니다. [입력 예시와 검증 규칙](../docs/social-login.md#회원-사주-정보-저장수정)을 참고하세요.

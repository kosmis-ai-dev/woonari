# un FastAPI

상용 ASP의 계산·분류·문구 선택키를 Python으로 옮기고, 원본에서 결과 문구를 읽던 부분을 AI 작성으로 교체합니다. 처리 흐름은 **입력 → 원본 규칙에 따른 사주·un 판정 → 출력항목 확정 → AI 문장 작성**입니다. AI가 계산이나 조건 분기를 대신하지 않습니다.

원본 MSSQL의 문구는 사용하지 않습니다. 기본 만세력은 사용자 제공 `script.sql`의 `tb_manse` DB에서 조회하며, 그 밖의 DB에 들어 있는 판정은 임의 알고리즘으로 채우지 않습니다. 필요한 판정 의존성이 없으면 계산 근거와 미확보 항목을 반환하고 AI 생성을 막습니다.

## 실행

Python 3.11 이상을 사용합니다. 현재 작업 환경에는 `.venv`와 의존성이 설치되어 있습니다.

```bash
cd /Users/kosmis/work/kosmis/un
./woonari init
./woonari start
```

새 환경에서는 다음과 같이 설치합니다.

```bash
python3 -m venv python_api/.venv
python_api/.venv/bin/python -m pip install -r python_api/requirements.lock
```

- 문서: <http://127.0.0.1:9090/docs>
- 상태: `GET /health`
- 전체 Python 실행 목록: `GET /v1/un-services`
- 항목별 실행: `POST /v1/un/{id}` (한글 이름·추가 입력·예시 제공)
- 기본 Python 9종: `GET /v1/fortunes`
- ASP 전체 원본 목록·문제·해결 자료: `GET /v1/asp-services`
- 원본별 진단: `GET /v1/asp-services/{목록의 id}` (각 항목이 Swagger에 개별 표시됨)
- 사주 계산: `POST /v1/saju`
- un 판정·해석: `POST /v1/fortunes/{kind}`

공식 실행기는 `.local/woonari/api.env`만 읽습니다. 다른 프로젝트의 환경변수·기존 `.env`·원본 사이트 접속정보는 사용하지 않습니다. [독립 환경 안내](../docs/isolated-environment.md)를 참고하세요. 전용 보드는 http://127.0.0.1:18101/ 이며 종료는 루트의 `./woonari stop`입니다.

## 추가 전환 서비스와 Python 전용 개발

현재 공식 MySQL 실행 기준 해석 준비 **65개**, 달력 계산 전용 **2개**, 부분 계산 **108개**로 Python 실행 경로는 **175개**입니다. 활성 목록 **291개**는 준비65·계산전용2·자료필요199·묶음/보조17·과거판8로 구성됩니다. DLL 의존11종과 실행없는 관련 메뉴 진단4개를 제거했습니다. 추가 Python 핸들러166개와 기본9종을 구분하며, 원본/자료가 필요한 미구현91개를 완료된 운세로 세지 않습니다.

Swagger **Python 추가 전환 · 계산 가능**에서 한글 이름을 선택하고 예시를 실행하세요. `parameters`에는 서비스별 추가 입력을 넣습니다. 원본 자료 진단 항목은 `include_ai=false`로 실행합니다. [전체 상태](docs/legacy_services.md) · [Python 전용 작업 안내](../docs/python-only.md)

ASP는 활성 작업 폴더에서 분리해 비공개 보관합니다. Python API·회귀 테스트에는 ASP 파일이 필요하지 않습니다. 외부 만세력 계산 패키지의 실행 의존성도 제거했으며 제공 DB·원본 정적표·Python 계산을 사용합니다. 기본 9종 경로도 그대로 사용할 수 있습니다.

## Swagger에서 실제 un 내용 받기

[Swagger 문서](http://127.0.0.1:9090/docs)의 **un 테스트 · AI 해석 가능 8종**에서 오늘의 un·이번주 un·이달의 un·연간 un·평생un·명품 평생재물운·러브 어드바이스·바이오리듬 중 원하는 항목을 펼치세요.

1. 아래 **AI 연결과 출력 계약** 절차로 `.local/woonari/api.env`의 제공자·모델·인증 설정을 완료하고 `./woonari stop` / `./woonari start`로 재시작합니다. 현재 연결 대상은 Amazon Bedrock의 Claude입니다.
2. **서버 상태 → GET /health**에서 `ai_configured: true`를 확인합니다. `ai_missing_settings`에는 필요한 설정 이름만 표시합니다. 모델 호출 권한과 실제 생성 성공은 다음 POST로 확인합니다.
3. **Try it out → Examples**에서 첫 번째 **실제 AI un 내용 받기**를 선택합니다. `include_ai: true`입니다.
4. `birth`의 생년월일시·성별, `target_date`의 조회 날짜를 수정하고 **Execute**를 누릅니다.
5. **Response body → `content`**에서 요약·항목별 해석·조언이 이어진 un 본문을 읽습니다. `interpretation`은 같은 해석의 구조화된 값이며 `analysis`는 계산 근거입니다.

선택한 제공자의 설정이 없으면 `503 ai_not_configured`입니다. 계산 근거만 검증하려면 두 번째 **계산 전용 · 근거 확인** 예시를 선택하세요. `include_ai: false`이면 AI를 호출하지 않으며 `content`와 `interpretation`이 null입니다.

각 un는 `/v1/fortunes/daily`처럼 고정 경로로 표시됩니다. 기존 공통 `/v1/fortunes/{kind}`의 Examples는 계산·진단 전용입니다. 실제 AI 본문을 받으려면 준비된 8종에서 `include_ai: true`로 변경하거나 개별 un 예시를 사용하세요. 공통 경로에서는 Examples를 바꿔도 `kind`가 자동으로 바뀌지 않으므로 해당 코드도 직접 선택해야 합니다.

**un 테스트 · 원본 자료 대기 1종**은 궁합의 조회키 진단용입니다. 연간 un은 별도 사주 기반 AI 해석으로 2027년을 포함해 실행합니다. 별점·점수·부적은 생성하지 않습니다.

## ASP 전체 이름·문제 확인

Swagger **시작 안내 → GET /v1/asp-services → Try it out → Execute**로 전체 목록을 확인합니다. 아래 **ASP 전체** 태그에는 개별 항목이 한글 이름으로 표시됩니다. 생년월일 입력 없이 원본 이름·다른 메뉴명·원본 파일/줄·현재 상태·문제 원인·해결 순서·필요 자료를 조회할 수 있습니다.

- `issues[].reason`: 문제가 생기는 이유
- `issues[].effect`: 현재 계산/판정에 미치는 영향
- `issues[].resolution`: 구현 또는 자료 복구 순서
- `issues[].required_materials`: 필요한 원본 데이터/소스/대조 결과
- `issues[].certainty`: 확인된 사실과 추가 검토 대상을 구분
- `test_path`: 현재 계산 POST가 있는 항목에만 표시

GET의 200은 **상태 조회 성공**입니다. 미이식 항목의 계산이나 최종 해석 성공을 뜻하지 않습니다. 폴더·입력 단계 수를 서비스 수로 세지 않고 하위 서비스/과거판/묶음/보조 코드를 구분합니다. 같은 이름이어도 다른 엔진·메뉴 경로이면 동일한 계산으로 간주하지 않습니다. XML 메뉴 IM1~IM90 전체의 연결 상태도 `menu_map`으로 추적합니다. JS 실행 매핑은 앞의 67개만 있으며, IM68~IM90은 이름만 선언되어 실행 연결을 별도로 확인해야 합니다.

현재 `lifetime`은 `lifeluck`의 **평생un**이며, 메뉴상 **평생사주**로 표기된 `loveunse`와 별개입니다. `love`는 **러브 어드바이스**, `compatibility`는 **숙명의 궁합**, `yearly`는 **2014 도통비결** 원본입니다. `운세`라는 표시 문구는 `un`으로 바꾸되 `original_name`에는 식별을 위한 실제 원본 이름을 보관합니다.

원본 DB의 문구 조회는 AI로 교체할 수 있습니다. 판정 코드·별점·택일 플래그·점수 구간·날짜 분류·DLL 내부 계산은 문구와 구분해 다룹니다. 원본 DB 미접속이라는 이유만으로 모든 미이식 항목에 DB가 필요하다고 판단하지 않습니다. 전체 조사표는 [legacy_services.md](docs/legacy_services.md), 실제 API 데이터는 [legacy_services.json](app/data/legacy_services.json)입니다.

## 계산 근거만 별도로 확인

```bash
curl -s http://127.0.0.1:9090/v1/fortunes/daily \
  -H 'Content-Type: application/json' \
  --data-binary @examples/daily.json
```

```json
{
  "birth": {
    "year": 1990, "month": 5, "day": 17,
    "hour": 14, "minute": 30,
    "calendar": "solar", "leap_month": false,
    "gender": "male"
  },
  "target_date": "2026-11-02",
  "include_ai": false
}
```

`birth`의 년월일·시간·성별은 필수이며 분은 기본 0입니다. `calendar`는 `solar`/`lunar`, `gender`는 `male`/`female`입니다. 시간을 모르면 임의 시각으로 자동 보정하지 않습니다.

음력은 `calendar: "lunar"`, 윤달이면 `leap_month: true`를 지정합니다. 존재하지 않는 날짜·윤달은 거절합니다. 공개 API의 입력 및 변환된 양력 범위는 1900-01-01~2050-12-31입니다. DB에는 1900~2100년 원본 73,414행을 보존합니다. 검증된 윤달 표시 오류 10행은 `lunar-leap-flags-v1` 교정표로 처리합니다. 교정 후 남는 음력키 중복만 `422 ambiguous_lunar_date`로 거절합니다. `target_date`는 출생일 이후여야 합니다. **연간 un도 1900~2050년을 지원**하며 별도의 운세 DB 없이 사주·연도 근거로 AI가 해석합니다.

사주만 필요하면 `/v1/saju`에 다음처럼 요청합니다.

```json
{
  "birth": {
    "year": 1990, "month": 5, "day": 17,
    "hour": 23, "minute": 30, "gender": "male"
  },
  "calculation_profile": "dotong"
}
```

`calculation_profile`은 `dotong`이 기본이며 `today_inline`도 선택할 수 있습니다. un 엔드포인트에서는 해당 ASP가 사용하는 프로필을 자동 적용합니다.

기본 9종 API에서는 궁합에 같은 구조의 `partner`가 필수이며 다른 종류에는 받지 않습니다. 추가 전환 `/v1/un/{id}`의 입력은 개별 Swagger를 따릅니다.

## un별 준비 상태

다음8종은 해석 계약이 준비돼 있습니다. 연간은 사주 기반 AI 해석이고 나머지는 제공 만세력 DB를 기준으로 원본의 판정·문구 선택키를 확정합니다. 여기서 준비 완료는 실제 AI 호출 검증 완료나 원본 DB/DLL 실행 결과와의 완전 동일성을 뜻하지 않습니다.

| kind | 보존한 판정·출력 |
|---|---|
| daily | 원본 8항목 점수와 `dayfortune(memno,num)`의 어제·오늘·내일 문구 선택키 |
| weekly | 일요일~토요일 원본 점수·별점·주간 등급, 총평 `weekDesc` |
| yearly | 기존 사주·연도 관계를 근거로 운세 DB 없이 AI 본문 생성. 별점·점수·부적 미제공 |
| monthly | 절기 월주·도깨비번호 첫 자리·성별로 `monthfor` 본문 선택 |
| lifetime | 십격·당사주·일주 분류에 따른 원본 실제 출력 13항목 |
| wealth | 년·월·일·시주와 일간으로 `Moneyluck.Money` 초년·장년·중년·말년 4항목 선택 |
| love | 도깨비번호 앞 3자리·성별로 `tbLoveLuck`의 원본 5항목 선택 |
| biorhythm | 원본 23/28/33일 주기·상태·27가지 멘트 분류 |

아래 궁합은 원본의 조회·호출 분기를 보존했지만 판정 의존성이 미확보되어 `ready_for_ai: false`입니다.

| kind | 보존한 부분 | 현재 필요한 원본 판정 의존성 |
|---|---|---|
| compatibility | 원본 4개 출력항목, 방향성 있는 `AisyoTbl` 전체 표와 후속 문구 선택 공식 | 두 양력 출생일 → `tbAisyo.aisyo` 분류코드. 단순 육합·충으로 대체하지 않습니다. |

궁합도 `include_ai: false`이면 확인 가능한 선택키·미확보 항목을 볼 수 있습니다. `include_ai: true`이면 `503 legacy_dependency_unavailable`로 중단합니다.

상세 근거: [월간·연간](docs/legacy_periods.md), [평생·재물](docs/legacy_life_wealth.md), [연애·궁합](docs/legacy_relationships.md). 기존 [legacy_inventory.json](docs/legacy_inventory.json)은 68개 폴더의 정규식 기반 기초 조사입니다. 실제 서비스 이름·하위 항목·메뉴의 누락된 연결·구체적 해결 자료는 새 [전체 조사표](docs/legacy_services.md)를 기준으로 확인하세요.

## 원본 계산 정책

- 음양력·윤달·년월일 간지·절입 시각은 제공된 `tb_manse` 행을 사용합니다. 공식 실행기는 전용 시크릿으로 MySQL `woonari` DB를 조회합니다. 오프라인 개발용 SQLite 스냅샷도 같은 원본을 보존합니다. 두 저장소 모두 승인된 10행의 윤달 표시 교정표를 조회 시 적용하며 원본 데이터 해시는 유지합니다. 패키지 계산으로 자동 대체하지 않습니다. [DB 구축·데이터 특이점](docs/manse_database.md)을 참고하세요.
- 절입 시각의 **해당 분부터** 새 년주·월주를 적용합니다. 원본의 `div_hour/div_minute` 비교를 따르며, 절입 초 때문에 다음 분으로 전환을 미루지 않습니다.
- 일주는 00:00~00:29에 전날, 00:30부터 당일입니다. 시주의 천간을 계산한 후 일주를 보정하는 원본 순서를 지킵니다.
- `dotong` 프로필은 `dotong_function.asp`처럼 **23:30부터 다음날 일간으로 자시**를 계산합니다. `today_inline`은 오늘·주간 인라인 함수 및 `dokebi.asp`처럼 **23:30에도 당일 일간**을 사용합니다. 01:30부터 2시간 단위 시각 경계는 공통입니다.
- 오늘·주간·월간은 `today_inline`, 나머지 un는 `dotong`을 적용합니다. `/v1/saju`에서는 프로필을 명시할 수 있습니다.
- 주간 `tempChk`는 원본처럼 한 주의 반복문 안에서 누적됩니다. 날짜별로 임의 초기화하지 않으며, 요청 간에는 상태를 공유하지 않습니다. 원본 별점 비교식의 구간도 그대로 적용합니다.
- 일일·주간 `compareZone8`의 VB 문자열 `인수"비견`처럼 특이한 값도 원본 판정 경로에 보존합니다. 이를 정상 십성 값으로 조용히 고치거나 다른 helper 프로필에 적용하지 않습니다.
- 월간은 절기 날짜 기준으로 월주를 바꾸며, 해당 날짜의 절입 시각을 따로 비교하지 않는 원본 분기를 보존합니다. 표시 범위도 양력 1일~말일이 아닌 절입 날짜~다음 절입 날짜입니다. 원본 `disp_day`와 대체 생성한 범위의 동일성은 미검증입니다.
- `saju.elements`는 8자 단순 개수입니다. 평생·재물의 근거에는 원본 `twelveChart/KiK`에 따른 가중 오기, 공망, 합형충파해, 신살 등을 별도로 제공합니다.
- 원본에 대응하지 않는 공통 라이브러리 대운은 제거했습니다. `major_luck.available=false`이며 임의로 대운을 채우지 않습니다.
- 역사적 표준시·DST·출생지별 진태양시 보정은 하지 않습니다. 해외 출생은 현재 지원하지 않습니다.

제공된 `tb_manse` 데이터와 적재 DB의 전체 행·해시를 검증했습니다. 기존 `manse`의 `disp_day` 및 ASP 서버의 실제 실행 결과와 완전 동일성은 미검증입니다. `1945-06-06`의 절기번호 8 등 원본 특이값은 그대로 보존합니다.

## AI 연결과 출력 계약

프로젝트 루트 `/Users/kosmis/work/kosmis/un`에서 관리합니다. 공식 실행기는 **이 프로젝트의 `.local/woonari/api.env`만** 읽습니다. 다른 프로젝트의 키나 터미널에 상속된 AI 설정을 사용하지 않습니다. 비밀값은 전용 파일에 직접 입력하고 채팅·명령 인자·소스에 기록하지 않습니다.

현재 선택한 제공자는 **Amazon Bedrock의 Claude**입니다. `.local/woonari/api.env`에서 제공자·모델·리전·인증 모드를 설정합니다. 사용자가 승인한 AI 전용 계정의 장기 키 모드를 사용하며 DB·Secrets Manager용 AWS 계정은 유지합니다.

```dotenv
AI_PROVIDER=bedrock
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-6
BEDROCK_REGION=ap-northeast-2
BEDROCK_MAX_TOKENS=8192
AI_TIMEOUT_SECONDS=45
AI_MAX_CONCURRENCY=4
API_KEY=
```

위 모델 ID와 리전은 실제 사용할 값으로 설정합니다. `BEDROCK_AUTH_MODE=api_key`일 때 `BEDROCK_ACCOUNT_ID`에 확인된 AI 계정 ID를 넣고, 키는 `.local/woonari/ai/bedrock.env`의 `AWS_BEARER_TOKEN_BEDROCK` 한 항목에만 저장합니다(권한600). 해당 키로 조회한 추론 프로필 계정·리전·ID를 대조합니다. `iam` 모드를 명시하면 기존 `.local/woonari/aws/`의 전용 `woonari` 프로필을 사용합니다. 어느 모드도 다른 인증·계정으로 자동 전환하지 않습니다. [독립 환경 안내](../docs/isolated-environment.md)

`AI_DAILY_CALL_LIMIT=100`은 한국시간 자정 기준 Woonari의 모델 전송 시도를 최대100회로 제한합니다. 모든 경로와 제공자가 영속 기록을 공유하므로 서버 재시작·동시 요청·조회 날짜 변경으로 초기화되지 않습니다. `GET /v1/ai-usage`로 사용·잔여·다음 초기화 시각을 확인합니다. 전송 후 오류도 차감하며, 초과는429입니다. 계산만 하는 요청·입력 오류·자료 부족·전송 전 키 검증 실패는 차감하지 않습니다. 상태 기록을 삭제하지 마세요.

AI는 Python의 사주·점수·선택키·출력항목을 입력받아 **요약, 항목별 해석, 실천 조언**을 작성합니다. 원본 DB 문구의 복원이나 미확보 판정 생성은 하지 않습니다. 연간 un은 별도의 승인된 AI 해석 모드이며 사주 원국과 대상 연도 관계를 전달합니다. 2027년 요청도 실제 본문 생성이 가능하고 실제 전송마다 같은 일일 한도를 사용합니다. 계산 전용 요청은 차감하지 않습니다.

설정 후 `./woonari stop` / `./woonari start`로 재시작하고 `/health`의 `ai_configured`, `ai_missing_settings`를 확인하세요. 준비된 8종의 첫 **실제 AI un 내용 받기** 예시로 POST를 실행하면 `content`에 실제 생성 문장이 반환됩니다. 설정 상태와 모델 호출 권한은 구분하며 실제 호출 성공은 POST 결과로 확인합니다. 키·모델 등 선택한 제공자의 설정이 없으면 `503 ai_not_configured`, 원본 판정 의존성이 없으면 먼저 `503 legacy_dependency_unavailable`입니다.

OpenAI 연결도 선택할 수 있습니다. 이 경우 `AI_PROVIDER=openai`와 전용 `OPENAI_API_KEY`, `OPENAI_MODEL`을 설정합니다. 모델은 Responses API와 structured outputs를 지원하는 모델 ID를 사용합니다. 실제 호출 여부는 선택한 제공자의 전용 설정과 POST 응답으로 확인하며 모의 전송 테스트를 외부 서비스 호출 검증으로 간주하지 않습니다.

응답 `analysis`의 주요 필드는 다음과 같습니다.

- `source_file`: 기준 ASP 파일
- `selectors`: 원본 조회 테이블·조건·열·목적. 계산용 조회는 `role: "calculation"`, `narrative: false`로 구분합니다.
- `evidence`: Python이 확정한 계산·분류·조회키 근거
- `narrative_contract`: AI가 작성할 원본 출력항목의 `id/topic/output_field/evidence_ids/constraints`
- `unresolved_dependencies`: 문구 외 원본 판정 중 미확보 의존성
- `ready_for_ai`: 원본 분기와 작성할 출력항목이 확정됐는지 여부

AI는 계약의 각 `id`를 `sections[].target_id`로 **정확히 한 번씩** 반환해야 합니다. 추가·누락·중복 항목, 변경된 제목, 계약에서 요구한 근거 ID 누락, 존재하지 않는 근거 참조는 오류로 거절합니다. 응답의 `content`는 검증된 AI 요약·항목별 해석·조언을 한 본문으로 연결한 값입니다. `interpretation`에는 구조화된 해석을, `analysis`에는 판정·점수 등 계산 근거를 반환합니다.

이 검사는 출력항목과 근거 참조의 일치를 확인하는 것이며 자연어 내용 전체의 의미적 정확성을 증명하지는 않습니다. 원본의 불투명한 코드만으로 구체적 직업·시기·성격을 원본 판정처럼 단정하도록 하지 않습니다. 원본 DB 문구를 복원했다고 주장하지도 않습니다.

이름·원시 출생 타임스탬프·회원식별자는 AI에 전송하지 않습니다. 계산된 사주와 확정된 근거만 전달합니다. OpenAI 경로에서는 `store=false`를 사용합니다.

## 응답·인증·오류

AI 생성이 성공하면 응답 첫 항목 `content`에서 자연어 un 본문을 읽을 수 있습니다. 계산 전용·진단 요청이면 `content`, `interpretation`, `ai_provider`, `ai_model`은 null입니다. `scores`는 해당 ASP가 계산한 항목에만 있습니다. `raw`는 원본 값이며 `direction=caution`은 높을수록 주의 필요도가 높습니다. `favorable`는 높은 쪽을 유리한 방향으로 정규화한 값입니다. AI는 수치·별점·분류를 생성하지 않습니다.

`API_KEY`를 설정하면 `/v1/*`에 `X-API-Key`가 필요합니다. `/health`, `/docs`, `/openapi.json`은 공개이며 기본 실행은 localhost에 바인딩합니다.

오류는 `{"error":{"code":"...","message":"..."}}` 형식입니다. 입력 오류422, 인증401, 원본 판정 의존성·AI 설정·한도503, AI 오류·출력 계약 불일치502, 시간초과504를 사용합니다. 미확보 원본 판단이나 AI 실패를 새 un로 대체하지 않습니다.

## 검증

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/python -m compileall -q app
```

출처별 야자시·절입 분 경계, 한국 음력·윤달, 조견표와 원본 점수, 주간 누적 동작, 월간·연간 분기, 평생·재물·연애 선택키, 직업·궁합의 미확보 의존성 차단, AI 출력 계약·오류, 실제 SDK 모의 전송, 인증을 검사합니다. 이는 원본 DB/DLL 실행 결과와의 전체 동일성 검증은 아닙니다.

원본 정적 조사 자료는 아래 명령으로 출력합니다. ASP가 없는 작업본에서는 고정된 출처·규칙 자료를 사용하며 그 사실을 명시합니다. 일반 API 실행에는 조사 도구가 필요하지 않습니다.

```bash
.venv/bin/python tools/inventory_legacy.py
.venv/bin/python tools/extract_rule_fixture.py
```

공식 참고: [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses), [KoreanLunarCalendar](https://github.com/usingsky/korean_lunar_calendar_py), [lunar-python](https://github.com/6tail/lunar-python).

기존 IAM 계정에서는 Anthropic 사용 목적 양식·조직 SCP 거부 이력이 있었습니다. 현재는 사용자 승인 AI 전용 계정과 장기 키를 별도로 검증합니다. `/health`의 `ai_configured=true`는 설정 준비만 뜻하며 모델의 실제 권한은 AI POST 결과로 확인합니다. 사용 목적 양식이 필요한 계정에서는 `bedrock_use_case_required`로 안내합니다. [AWS 모델 접근 안내](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)

미설정은 `bedrock_not_configured`, 양식 미제출은 `bedrock_use_case_required`, 계정 검증 진행은 `bedrock_account_verification`으로 구분합니다. 원본 계산만 확인하려면 `include_ai=false`를 선택합니다.

AI 실제 테스트(2026-11-19): 일일·연인 심리분석·평생의 V5 결과를 확인했습니다. 원본 계산은 변하지 않았고 해석3/4/13항목이 반환됐습니다. 초기 문장 품질 보완을 포함해 모델 전송은 총6회였으며 테스트 시점 잔여94회입니다. 근거가 없는 선택키·당사주 문자만으로 성격이나 시기별 길흉을 단정하지 않고 일반 조언·확인 질문으로 제한합니다. 이 테스트 이후 CR-018에서 연간 사주 기반 AI 해석 모드를 추가했습니다. 기존 DB 점수 재현은 제공하지 않습니다.

연간 실행 예시·해석 범위·미제공 항목은 [연간 AI 안내](docs/annual-ai.md)를 따릅니다.

CR-019: DLL 의존11종과 실행없는 관련 메뉴 진단4개를 제거했습니다. `career`와 `career_category`도 공개 계약에서 제거했습니다. [상세 제거 목록](../docs/removed-dll-services.md)을 참고하세요.

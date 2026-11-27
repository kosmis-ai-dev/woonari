# Python API 환경설정 · CR-025 / T-045

Python API의 `app.config.Settings`가 소셜 로그인·AI·DB 설정을 직접 읽습니다. 로컬과 배포 서버에서 같은 Python 설정 항목을 사용하며, API 실행을 위해 프로젝트 관리용 GitHub·AWS CLI 계정을 배포 서버에 복사할 필요가 없습니다. 이번 변경은 실행 구조를 준비한 것이며 실제 운영 서버 배포나 세 제공자의 로그인 완료를 뜻하지 않습니다.

## 설정 파일과 우선순위

기본 파일은 저장소의 `python_api/.env`입니다. 파일은 Git·배포 패키지에 포함하지 않고, 각 실행 환경에 따로 준비합니다. 소유자는 API를 실행하는 OS 사용자, 파일 권한은 `600`이어야 합니다. 심볼릭 링크나 다른 사용자에게 공개된 파일은 거부합니다.

Python을 직접 실행할 때 우선순위는 **프로세스 환경변수 → 선택한 `.env` → 코드의 기본값**입니다. 공식 `./woonari` 실행기는 다른 프로젝트의 키가 섞이지 않도록 상속된 앱 환경변수를 정리한 뒤 Python 설정 파일을 읽습니다. 다른 작업 폴더에서 실행해도 해당 폴더의 `.env`를 찾지 않습니다. 별도 파일을 사용하려면 `WOONARI_ENV_FILE`에 존재하는 설정 파일의 **절대 경로**를 지정합니다. 지정한 파일이 없거나 잘못되면 다른 파일로 대체하지 않고 시작을 중단합니다. 패키지만 설치한 환경에서는 이 절대 경로나 프로세스 환경변수를 사용합니다.

`.env`는 셸 스크립트가 아닙니다. `KEY=VALUE`로 작성하며, `$NAME`·`${NAME}`을 다른 환경변수로 치환하거나 명령을 실행하지 않습니다. 같은 항목을 대소문자만 바꾸어 중복 작성하지 마세요. 비밀값은 터미널 명령 인자·채팅·소스 코드에 넣지 않습니다.

## 로컬에서 입력할 파일

기존 `.local` API 설정으로 운세를 실행하던 환경은 프로젝트 루트에서 먼저 전체 설정을 이전합니다.

```sh
./woonari config migrate-api
./woonari auth status
```

이 명령은 기존 AI 설정·Bedrock 장기 키·소셜 앱 설정·MySQL 접속정보를 `python_api/.env`에 모읍니다. 기존 파일과 사용량 기록을 보존하며, 기존 `.env`를 교체할 때는 `.local/woonari/config-backups/`에 비공개 백업을 남깁니다. MySQL 접속정보 이전에는 기존 전용 AWS 계정의 Secrets Manager 조회 권한이 필요합니다. 이전 후 API 실행은 DB에 직접 접속하며 GitHub·AWS CLI 관리 계정은 이전하지 않습니다. 이전을 마친 뒤에는 `.env`를 직접 수정하고, 이전 명령을 일반 설정 수정용으로 반복 실행하지 않습니다.

**기존 AI 설정이 있는 환경은 `auth init`보다 `config migrate-api`를 먼저 실행하세요.** 소셜 항목만 있는 새 `.env`를 먼저 만들면 API가 그 파일을 전체 설정으로 선택하므로 이전 AI·DB 설정을 함께 읽지 않습니다.

새 환경의 소셜 설정 파일만 준비할 때는 다음 명령을 사용합니다.

```sh
./woonari auth init
./woonari auth status
```

`auth init`은 `python_api/.env`가 없을 때만 생성합니다. 기존 `.local/woonari/auth/providers.env`가 있으면 권한과 형식을 검사한 뒤 소셜 설정만 복사하고 원본을 보존합니다. AI·DB 설정은 추가하지 않습니다. 이미 존재하는 `.env`의 값이나 수정 시각은 변경하지 않습니다. 생성 후 편집기에서 소셜 로그인·AI·DB 값을 입력하세요. `auth status`는 소셜 설정 여부와 콜백 주소만 보여주며 실제 키를 출력하거나 제공자 로그인을 실행하지 않습니다.

공식 로컬 실행은 계속 `./woonari start|stop|status`를 사용합니다. 변경한 설정은 재시작 후 반영됩니다. Swagger는 `http://127.0.0.1:9090/docs`입니다.

## 소셜 로그인 항목

| 항목 | 입력할 값 |
|---|---|
| `AUTH_PUBLIC_BASE_URL` | 로컬은 `http://127.0.0.1:9090`, 운영은 공개 API의 HTTPS 주소 |
| `KAKAO_CLIENT_ID` | 카카오 REST API 키 |
| `KAKAO_CLIENT_SECRET` | 카카오 Client secret |
| `GOOGLE_CLIENT_ID` | Google 웹 애플리케이션 OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | 해당 Google Client secret |
| `NAVER_CLIENT_ID` | 네이버 로그인 애플리케이션 Client ID |
| `NAVER_CLIENT_SECRET` | 해당 네이버 Client secret |

제공자 콘솔의 콜백 주소는 `{AUTH_PUBLIC_BASE_URL}/v1/auth/kakao/callback`, `/v1/auth/google/callback`, `/v1/auth/naver/callback`입니다. 운영 주소로 바꾸면 각 콘솔에도 그 주소를 등록해야 합니다. `GET /v1/auth/providers`의 `configured=true`는 필요한 값이 있다는 뜻이며, 실제 로그인 성공 여부는 별도 브라우저 테스트로 확인합니다.

## AI·DB·상태 저장 항목

| 항목 | 용도 |
|---|---|
| `WOONARI_ENV` | `development`, `test`, `production` 중 하나 |
| `WOONARI_STATE_DIR` | AI 호출 한도 등 영속 상태를 보존하는 절대 경로 |
| `WOONARI_DB_BACKEND` | 개발 기본값 `sqlite`, 실제 MySQL 연결은 `mysql` |
| `WOONARI_DB_HOST`, `WOONARI_DB_PORT` | MySQL 호스트와 포트, 기본 포트 `3306` |
| `WOONARI_DB_NAME` | 서비스 DB 이름 `woonari` |
| `WOONARI_DB_USER`, `WOONARI_DB_PASSWORD` | 이 DB에 접속할 전용 사용자와 암호 |
| `WOONARI_DB_CA_FILE` | 별도 CA가 필요할 때 PEM 파일의 절대 경로. 비어 있으면 기본 신뢰 CA 사용 |
| `AI_PROVIDER` | `bedrock` 또는 `openai` |
| `BEDROCK_AUTH_MODE` | 현재 승인한 장기 키 방식은 `api_key` |
| `AWS_BEARER_TOKEN_BEDROCK` | Bedrock 장기 키 |
| `BEDROCK_ACCOUNT_ID` | 해당 장기 키를 발급한 AI 계정의 12자리 ID |
| `BEDROCK_REGION`, `BEDROCK_MODEL_ID` | 사용할 리전과 모델 또는 추론 프로필 ID |
| `BEDROCK_MAX_TOKENS` | 출력 토큰 상한, 기본값 `8192` |
| `AI_DAILY_CALL_LIMIT` | 한국시간 하루 모델 전송 시도 한도, `1`~`100`, 기본값 `100` |
| `AI_TIMEOUT_SECONDS`, `AI_MAX_CONCURRENCY` | AI 요청 제한, 기본값 `45`초·`4`개 |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | OpenAI를 선택할 때의 키와 모델 |
| `API_KEY` | 선택 사항. 설정하면 운세 API에 `X-API-Key` 필요 |

Bedrock AI 계정은 DB 계정과 별도 사용합니다. 장기 키의 계정·리전·추론 프로필 검증과 일일 호출 한도는 유지됩니다. 배포용 Python 직접 실행은 `api_key` 방식을 사용합니다. `iam`은 Python 설정 파일이 없는 기존 공식 로컬 실행기의 전용 AWS CLI 연결에만 남겨 두며 배포용 인증으로 자동 대체하지 않습니다. MySQL 연결은 TLS 인증서와 호스트명을 검증하며 접속 실패 시 다른 DB로 전환하지 않습니다.

현재 로컬 설정을 이전할 때 `WOONARI_STATE_DIR`는 기존 `.local/woonari`의 절대 경로를 유지합니다. `ai/usage.sqlite3`와 잠금 기록을 함께 보존하며 삭제·초기화로 호출 한도를 새로 만들지 않습니다. 기존 `.local` 설정 파일은 이전 기록으로 보존하되 새 Python 설정을 수정합니다.

## 배포용 설정 예시

아래 빈 값은 배포 환경에서 직접 입력해야 합니다. 이 예시만으로 서버를 시작할 수는 없습니다.

```dotenv
WOONARI_ENV=production
WOONARI_STATE_DIR=/var/lib/woonari
WOONARI_DB_BACKEND=mysql
WOONARI_DB_HOST=
WOONARI_DB_PORT=3306
WOONARI_DB_NAME=woonari
WOONARI_DB_USER=
WOONARI_DB_PASSWORD=
WOONARI_DB_CA_FILE=

AUTH_PUBLIC_BASE_URL=https://api.example.com
KAKAO_CLIENT_ID=
KAKAO_CLIENT_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=

AI_PROVIDER=bedrock
BEDROCK_AUTH_MODE=api_key
AWS_BEARER_TOKEN_BEDROCK=
BEDROCK_ACCOUNT_ID=
BEDROCK_REGION=
BEDROCK_MODEL_ID=
BEDROCK_MAX_TOKENS=8192
AI_DAILY_CALL_LIMIT=100
AI_TIMEOUT_SECONDS=45
AI_MAX_CONCURRENCY=4
API_KEY=
```

운영에서는 세 제공자의 6개 값, 공개 HTTPS 주소, 명시적인 `woonari` MySQL 설정과 영속 상태 경로가 필수입니다. 개발용 loopback 주소·SQLite·상태 경로 누락은 운영 시작 단계에서 거부합니다. 상태 디렉터리는 실행 사용자가 소유한 `700` 권한의 영속 저장소로 준비하고, 재배포 후에도 같은 경로를 사용합니다. 파일 권한이 잘못된 기존 디렉터리를 서버가 임의 변경하지 않습니다.

예를 들어 비공개 설정을 `/srv/woonari/runtime/api.env`에 준비했다면 다음처럼 Python API를 직접 실행할 수 있습니다. 경로는 실제 배포 위치에 맞게 바꾸세요.

```sh
WOONARI_ENV_FILE=/srv/woonari/runtime/api.env \
  /srv/woonari/python_api/.venv/bin/python -m uvicorn app.main:app \
  --app-dir /srv/woonari/python_api --host 127.0.0.1 --port 9090 --no-access-log
```

배포 서버는 MySQL의 기존 운세 데이터와 신규 `woonari_auth_*` 6개 표에 접근할 수 있어야 합니다. 시작 시 인증 스키마를 읽기 전용으로 확인한 뒤 AI 클라이언트를 준비하며, 실행 중 테이블을 생성하지 않습니다. 키 설정 확인과 실제 로그인·모델 호출 검증은 구분하고, 준비된 운영 주소에서 카카오·Google·네이버 로그인을 각각 확인하세요.

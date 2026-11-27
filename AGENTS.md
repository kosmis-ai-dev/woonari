# Woonari 프로젝트 작업 규칙

이 저장소는 다른 프로젝트와 별개다. API·대시보드·GitHub·AWS·AI 설정을 혼용하지 않는다.

## 독립 실행·계정

- 공식 진입점은 저장소 루트의 `./woonari`다. 로컬 실행/종료/상태는 `./woonari start|stop|status`로 관리한다.
- API/Swagger는 `127.0.0.1:9090` 고정, 전용 보드는 `127.0.0.1:18101`이다. 다른 프로젝트의 8000/4800 서버나 공용 허브를 이 프로젝트로 안내하거나 종료하지 않는다.
- API 실행 설정·키는 사용자 지시(CR-025)에 따라 `python_api/.env`에서 읽는다. Git·배포 패키지에는 포함하지 않고 권한600을 유지한다. 관리용 계정·토큰·캐시·로그는 `.local/woonari/`에 둔다. 전역 설정과 다른 프로젝트의 파일을 변경하지 않는다.
- Git은 `./woonari git ...`, GitHub 인증은 `./woonari gh ...`를 사용한다. 작업 사본은 `.publish/woonari`, 승인된 origin은 `https://github.com/kosmis-ai-dev/woonari.git`이다.
- 전용 GitHub 로그인명과 커밋 작성자가 미지정이면 추정하거나 공용 Git/SSH/Keychain 계정으로 대체하지 않는다. 기존의 다른 계정 인증을 재사용하지 않는다.
- AWS CLI는 `./woonari aws ...`를 사용한다. 신규 12자리 계정 ID와 전용 `woonari` 프로필의 실제 계정 일치 확인이 필요하다. 기존 계정·default 프로필·환경 키·공유 `~/.aws`로 대체하지 않는다. 승인된 Bedrock 장기 키 모드는 고정한 HTTPS 엔드포인트를 직접 호출한다.
- 사용자 승인에 따라 AI의 장기 키 발급 계정은 DB·Secrets Manager용 Woonari AWS 계정과 별도로 사용한다. `BEDROCK_ACCOUNT_ID`에 고정한 AI 계정은 해당 키의 인증된 추론 프로필 응답으로 검증한다. AI 설정을 바꿀 때 기존 AWS 프로필·DB 계정을 변경하지 않는다.
- AI 제공자·모델·인증모드·일일한도와 `AWS_BEARER_TOKEN_BEDROCK`는 Python Settings에서 읽는다. `BEDROCK_AUTH_MODE=api_key`일 때 고정 HTTPS 추론 프로필 응답의 실제 AI 계정을 검증한 뒤 모델 전송 직전에만 한도를 예약한다. 공식 실행기는 상속된 앱 환경변수를 제거하며, Python 직접 실행은 전용 프로세스 환경변수 또는 절대경로 `WOONARI_ENV_FILE`을 사용할 수 있다. 기존 `.local` 파일은 이관 원본으로 보존하며 Python `.env`가 없는 기존 실행에만 호환한다.
- AI 모델 전송은 `WOONARI_STATE_DIR/ai/usage.sqlite3`의 한국시간 일일 시도 한도(최대100)를 공유한다. 현재 로컬 `WOONARI_STATE_DIR`는 기존 `.local/woonari`를 유지한다. 기록 삭제·초기화로 한도를 우회하거나 자동 재시도로 호출을 늘리지 않는다. 키·프롬프트·사용자 식별자를 사용량 기록에 넣지 않는다.
- 서비스 DB는 Python Settings의 `WOONARI_DB_BACKEND=mysql` 및 `WOONARI_DB_*`로 명시한다. 만세력·판정자료·인증 저장소는 같은 `woonari` DB에 TLS로 연결하고 시작 시 인증 스키마를 읽기 전용 검증한다. 운영은 명시적인 MySQL·전용 영속 상태 경로가 필수이며 실패 시 SQLite로 대체하지 않는다. 기존 Secrets Manager/전용 AWS CLI는 관리·명시적 설정 이관용으로 보존한다.
- 실제 계정이 미확인이라면 인증 연결을 완료했다고 보고하지 않는다. 비밀번호·토큰·액세스 키를 채팅/명령 인자/로그/소스에 기록하지 않는다.
- 원본 ASP의 연결 정보는 과거 참조 자료다. 신규 프로젝트의 실제 DB·AWS 인증으로 사용하지 않는다.
- 소셜 로그인 앱 설정은 Python Settings의 매체별 Client ID·secret과 `AUTH_PUBLIC_BASE_URL`을 읽는다. 운영은 세 제공자 키와 공개 HTTPS 주소를 검증한다. 인증 데이터는 신규 `woonari_auth_*` 6개 표에 저장하고 과거 회원을 이관하지 않는다. 제공자 토큰을 저장하지 않고 자체 세션 토큰은 해시만 저장한다. 회원 사주 정보는 Bearer 토큰의 본인에게만 연결하며 생년월일·시각·성별·달력·윤달 원입력을 보존한다. 실제 제공자 로그인을 확인하지 않았으면 연결 완료로 보고하지 않는다.
- 세부 실행 절차는 `docs/isolated-environment.md`를 따른다.

## Python 전용 작업본

- 활성 실행·개발 코드는 `python_api/`다. ASP·IIS·COM과 원본 ASP 파일 읽기에 의존하지 않는다.
- 원본은 `.local/woonari/archive/`에 비공개 보관하며 Git·배포 사본에 복사하지 않는다. 문서의 ASP 경로·줄 번호는 출처 기록이다.
- 서비스별 Python 모듈은 개발용 `app.service_engine.service_catalog()`의 `python_module`로 확인한다. 공개 `GET /v1/un-services`는 호출 경로와 입력 안내만 반환한다. 정적 규칙은 `python_api/app/data/`에 포함한다.
- CR-018 사용자 승인(2026-11-24)에 따라 연간 un 본문은 만세력/기존 사주와 대상 연도 근거를 AI가 해석한다. 연간 운세 DB·별점·점수·부적은 사용하지 않으며 기존 ASP 연간 결과 재현과 구분한다. 다른 미확보 판정 DB·누락 원본을 AI나 일반 운세 라이브러리로 대체하지 않는다. 부분 계산·자료 진단과 해석 준비 상태를 구분한다.
- CR-019(2026-11-25)에 따라 DLL/COM 의존 운세11종과 실행없는 관련 메뉴4개를 활성 서비스에서 제거한다. 삭제한 직업 `career` kind·입력·호출 경로를 재노출하지 않는다. frozen 출처자료와 비공개 원본/DB는 보존하며, 일일·연간 본문의 직장 관련 해석처럼 DLL을 사용하지 않는 항목은 유지한다.
- 개발·검증·출처 관리 절차는 `docs/python-only.md`와 `python_api/docs/source-rules.md`를 따른다.

<!-- proj-kit:start -->
## 프로젝트 보드 (.project) 규칙

- 작업 전 `node .project/_tools/project-dashboard.mjs status`로 현황을 확인한다.
- 데이터 구조는 `.project/_tools/SCHEMA.md`를 따른다.
- 코드 변경은 반드시 작업(T번호)이나 수정 요청(CR번호)에 연결한다.
  - 새 요구사항 / 기획 → `proj-plan`
  - 워크플로 작업 진행 → `proj-work`
  - 수정·추가 요청 → `proj-change`
- 기능 명세(`features/*.json`의 `spec`)는 항상 현재 코드와 일치해야 한다. 코드를 바꿨으면 명세도 같이 바꾼다.
- `.project` 파일을 고친 뒤에는 `check`를 실행해 오류 0을 확인한다.
- 커밋 메시지: `[T-007][F03] 요약 (CR-002)`. 코드와 `.project` 변경은 같은 커밋.
- `.project/_tools/`는 수정하지 않는다.
- 사용자 지시(CR-017, 2026-11-23)에 따라 이 프로젝트는 `main`에서 계속 작업하고, 작업·명세 갱신과 관련 검증을 마친 변경을 전용 계정으로 `main`에 push한다. 별도 push 승인을 반복해서 요청하지 않는다.
- 기존 게시 브랜치 `publish/python-api-20261123`은 원격 main에 커밋이 보존되고 기본 브랜치 전환을 확인한 뒤 삭제한다. force push·임의 브랜치 삭제·머지는 별도 지시 없이 하지 않는다.
<!-- proj-kit:end -->

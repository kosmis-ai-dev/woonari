# Woonari · Python un API

상용 ASP에서 확인한 계산·분류·선택 규칙을 Python FastAPI로 옮긴 독립 프로젝트입니다. Python이 판정과 출력항목을 확정하고, AI가 그 근거에 맞는 한국어 해석을 작성합니다.

현재 해석 선택키를 계산하는 **62개**, 달력 계산 전용 **2개**를 제공합니다. 추가 전환 항목은 166개이며, 이 중 109개는 부분 계산과 필요한 자료를 반환합니다. 기존 10종까지 합하면 Python 실행 항목은 176개입니다. 전체 조사 목록 306개에는 자료·원본 확인이 필요한 217개, 묶음·보조 코드 17개, 과거판 8개가 포함됩니다. 전체 상용 서비스 전환 완료를 뜻하지 않습니다.

## 실행

Python 3.11 이상과 프로젝트 보드용 Node가 필요합니다. 이미 준비된 이 데스크탑에서는 저장소 루트에서 실행합니다.

```sh
./woonari start
./woonari status
./woonari stop
```

- Swagger: http://127.0.0.1:9090/docs
- 프로젝트 보드: http://127.0.0.1:18101/
- 전체 실행 안내: `GET /v1/un-services`
- 항목 실행: `POST /v1/un/{id}` — Swagger의 한글 이름과 예시를 사용합니다.
- 원인·필요 자료: `GET /v1/asp-services` — 보관 원본에서 만든 진단 자료입니다.

새 환경의 설치·입력·AI 설정은 [API 안내](python_api/README.md), 전용 계정 설정은 [독립 환경 안내](docs/isolated-environment.md)를 따릅니다. [비회원 un 자료 전체 복원](docs/un-data-restore.md)에서 78개 표의 복원·서비스 연결·진단 방법을 확인하세요. [연간 자료 상세](docs/mssql-restore.md)에는 2027년 초기 행 문제가 정리되어 있습니다.

## 개발 구성

- `python_api/app/`: 만세력·사주·un 계산, 원본 선택표, AI 연결, API
- `python_api/app/data/`: 원본 기반 DB 스냅샷과 판정표·서비스 목록
- `python_api/tests/`: 고정된 원본 판정 사례·경계·API 계약 검증
- `python_api/tools/data/`: 원문이 없는 출처 해시·줄 번호·메뉴 조사 자료
- `tools/`, `woonari`: 프로젝트 전용 실행·AWS·DB·Git 도구
- `.project/`: 기획·작업·기능 명세·수정 요청·대시보드

ASP와 사이트 자산은 활성 프로젝트에서 분리해 `.local/woonari/archive/`에 비공개 보관합니다. API 실행과 테스트는 ASP 파일·IIS·COM을 사용하지 않습니다. 기록의 ASP 경로는 출처 표기이며 활성 파일 경로가 아닙니다. [Python 전용 작업 안내](docs/python-only.md)를 참고하세요.

만세력은 전용 MySQL `woonari` DB의 73,414행을 조회합니다. 오프라인 테스트용 SQLite 스냅샷과 검증된 윤달 표시 10행 교정표도 포함합니다. 원본 행과 해시는 유지합니다. [DB 안내](python_api/docs/manse_database.md)

## 지원 범위와 AI

기본 예시의 `include_ai=true`는 해석 생성, `false`는 계산·자료 진단입니다. 결과 본문은 `content`, 계산 근거는 `analysis`, 부족한 자료는 `analysis.unresolved_dependencies`에 나옵니다. 자료가 필요한 항목의 계산을 AI로 대신하지 않습니다. [전체 목록과 제약](python_api/docs/legacy_services.md)

연간 un은 CR-018 사주 기반 AI 해석으로 2027년을 포함해 1900~2050년을 지원합니다. 만세력과 기존 사주 계산을 유지하며 연간 운세 본문·별점·점수 DB는 사용하지 않습니다. 별점·점수·부적은 미제공입니다. 현재 MySQL에는 만세력과 선별 복원한 비회원 un 자료가 있습니다. 일부 서비스는 별도 판정 DB·누락된 결과 소스·DLL 계산 또는 원본 비교 자료가 필요합니다.

AI는 사용자가 승인한 AI 전용 AWS 계정의 Bedrock 장기 키를 사용하며, DB·Secrets Manager용 Woonari AWS 계정과 분리합니다. 설정·키·사용량은 `.local/woonari/`에만 저장합니다. Woonari의 AI 모델 전송은 **한국시간 하루 최대 100회**이며 전송 후 오류도 차감합니다. `GET /v1/ai-usage`에서 사용·잔여·다음 초기화 시각을 확인합니다. 계산 요청 `include_ai=false`는 차감하지 않습니다. `/health`의 `ai_configured=true`는 필수 설정 존재이며 실제 접근 권한은 개별 POST로 확인합니다.

## 검증·배포 사본

ASP 원본이 없는 작업본에서 테스트 1,349개와 하위 사례 40개를 통과했습니다. 실제 MySQL API의 한글 예시 306개도 AI 호출 없이 모두 HTTP 200을 확인했습니다. 배포 wheel은 별도 폴더에서 계산을 실행하고 규칙·DB를 포함한 런타임 파일 44개가 소스와 동일한지 검증했습니다.

```sh
python_api/.venv/bin/python -m pytest -q python_api/tests tools
python_api/.venv/bin/ruff check python_api/app python_api/tests python_api/tools tools
node .project/_tools/project-dashboard.mjs check
python3 tools/prepare_github.py
python3 tools/prepare_github.py --verify
```

배포 사본은 `.publish/woonari`이며 Python 코드·테스트·출처 메타데이터·보드만 포함합니다. `.local`의 원본 보관본·인증·키·로그와 가상환경·빌드 결과는 제외합니다. Git은 `./woonari git ...`, AWS는 `./woonari aws ...`로 관리합니다. 다른 프로젝트의 인증이나 기본 계정을 사용하지 않습니다.

AI 실제 테스트(2026-11-19): 일일·연인 심리분석·평생의 V5 결과를 확인했습니다. 원본 계산은 변하지 않았고 해석3/4/13항목이 반환됐습니다. 초기 문장 품질 보완을 포함해 모델 전송은 총6회였으며 테스트 시점 잔여94회입니다. 근거가 없는 선택키·당사주 문자만으로 성격이나 시기별 길흉을 단정하지 않고 일반 조언·확인 질문으로 제한합니다. 이 테스트는 당시의 검증 이력입니다. 현재 연간 본문은 CR-018에서 승인한 사주 기반 AI 해석이며 기존 DB 별점·점수 재현과 구분합니다.

## 2027년 연간 AI un · CR-018
Swagger의 `POST /v1/fortunes/yearly`에서 2027년 첫 예시를 실행합니다. `include_ai=true`는 실제 Claude 본문, false는 개인 사주와 연도 근거만 반환합니다. 점수는 빈 배열이고 연간 근거의 별점·점수는 null입니다. 세부 안내는 [연간 AI 해석](python_api/docs/annual-ai.md)을 따릅니다.

# Woonari · Python un API

생년월일시와 조회 날짜로 사주·운세를 계산하고, AI가 그 결과에 맞는 한국어 해석을 작성하는 독립 프로젝트입니다. API에는 운세 본문과 결과 데이터만 제공합니다.

## 실행

Python 3.11 이상과 프로젝트 보드용 Node가 필요합니다. 준비된 작업 환경의 저장소 루트에서 실행합니다.

```sh
./woonari start
./woonari status
./woonari stop
```

- Swagger: <http://127.0.0.1:9090/docs>
- 프로젝트 보드: <http://127.0.0.1:18101/>
- 운세 목록·호출 경로·입력: `GET /v1/un-services`
- 기본 운세 목록: `GET /v1/fortunes`
- 운세 실행: `POST /v1/un/{id}` 또는 `POST /v1/fortunes/{kind}`
- 사주 계산: `POST /v1/saju`

설치·입력·응답·AI 설정은 [API 안내](python_api/README.md), 계정별 설정은 [독립 환경 안내](docs/isolated-environment.md)를 따릅니다.

## 운세 결과 보기

Swagger 최상단 **서비스 운세 · AI 본문 제공**에 선별17종의 대표 API를 모았습니다. 현재 결과를 제공하는 항목만 표시합니다. [17종과 입력 조건](docs/service-offerings.md)을 확인하세요.

첫 예시의 `include_ai=true`는 AI 본문을 생성합니다. 응답의 `content`에서 운세를 읽고 `interpretation`에서 요약·항목별 해석·실천 조언을 확인합니다. `interpretation.sections`는 `topic`·`text`로 구성되며 `result`에는 사주·점수·기간·계산 결과가 담깁니다.

두 번째 예시의 `include_ai=false`는 AI 호출 없이 `result`만 반환합니다. 현재 지원하지 않는 결과는 `503 result_unavailable`입니다. 공개 응답에 개발 상태·출처 파일·내부 검증 계약을 포함하지 않습니다.

연간 un은 **2027년 포함1900~2050년**을 지원하며 개인 사주와 대상 연도를 바탕으로 본문을 작성합니다. 별점·점수·부적은 제공하지 않습니다.

AI는 사용자가 지정한 전용 Bedrock 계정을 사용하며 DB·Secrets Manager 계정과 분리합니다. 설정·키·로그·사용량은 `.local/woonari/`에만 저장합니다. 모델 전송은 **한국시간 하루 최대100회**이고 전송 후 오류도 차감합니다. `GET /v1/ai-usage`에서 잔여 사용량을 확인할 수 있으며 계산 요청은 차감하지 않습니다.

## 개발 구성과 검증

- `python_api/app/`: 사주·운세 계산, AI 연결, API와 공개 응답 변환
- `python_api/app/data/`: 달력 데이터와 정적 규칙
- `python_api/tests/`: 계산 경계·입력·응답·AI 계약 검증
- `tools/`, `woonari`: 프로젝트 전용 실행·AWS·DB·Git 도구
- `.project/`: 기획·작업·기능 명세·수정 요청·대시보드

내부 모듈 매핑과 출처 관리 절차는 [Python 전용 작업 안내](docs/python-only.md)를 따릅니다. 내부 조사 목록은 공개 카탈로그와 구분하며 미완성 진단 항목을 성공한 운세 결과로 제공하지 않습니다.

```sh
python_api/.venv/bin/python -m pytest -q python_api/tests tools
python_api/.venv/bin/ruff check python_api/app python_api/tests python_api/tools tools
node .project/_tools/project-dashboard.mjs check
python3 tools/prepare_github.py
python3 tools/prepare_github.py --verify
```

배포 사본은 `.publish/woonari`이며 `.local`의 인증·키·로그·개인 입력·사용량 기록과 가상환경·빌드 결과는 제외합니다. Git은 `./woonari git ...`, AWS는 `./woonari aws ...`로 관리하며 다른 프로젝트의 인증이나 기본 계정을 사용하지 않습니다.

## 소셜 로그인

카카오·구글·네이버 로그인 API를 Swagger의 **소셜 로그인 · 카카오·구글·네이버** 그룹에서 확인합니다. 로그인 시작·콜백·신규회원 생성·Bearer 토큰·내정보·갱신·로그아웃을 제공합니다. `./woonari auth init|status`로 전용 앱 설정을 준비하고 `./woonari db init-auth`로 신규 인증 표를 생성합니다. 실제 로그인은 앱 키 설정 후 확인합니다. [설정과 호출 가이드](docs/social-login.md)

**회원 사주 정보** 그룹의 `GET/PUT/PATCH /v1/auth/me/birth`로 로그인한 본인의 생년월일·태어난 시/분·성별·양력/음력·윤달 정보를 조회·저장·수정합니다. [입력 예시와 수정 규칙](docs/social-login.md#회원-사주-정보-저장수정)을 참고하세요.

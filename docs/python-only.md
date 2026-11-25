# Python 전용 작업 안내 · CR-012 / T-025

활성 작업 폴더는 `/Users/kosmis/work/kosmis/un`이며 API 코드는 `python_api/app`에 있습니다. 이 폴더에서 Python 계산·API·테스트를 수정하면 됩니다. IIS·Classic ASP·COM 설치는 필요하지 않습니다.

## 로컬 실행

```sh
./woonari start
./woonari status
./woonari stop
```

Swagger는 http://127.0.0.1:9090/docs, 전용 작업 보드는 http://127.0.0.1:18101/ 입니다. 다른 프로젝트의 서버·계정·환경 파일은 사용하지 않습니다. 신규 환경의 Python 의존성은 `python_api/requirements.lock`으로 설치하며, 전용 설정은 `./woonari init`으로 생성합니다. [설치와 설정](../python_api/README.md)

## 서비스 수정·테스트

기본 9종은 `app/fortunes.py`와 `app/legacy_*.py`, 추가 전환 서비스는 `app/ported_direct.py`, `ported_loveunse.py`, `ported_remaining.py`, `ported_interlife.py`, `ported_template.py` 및 `ported_interlife_*.py`에 있습니다. 공통 실행은 `service_engine.py`, 입력·출력은 `service_models.py`, API는 `main.py`입니다. 필요한 정적 규칙은 `app/data/*.json`에 포함합니다.

`GET /v1/un-services`에서 한글 이름과 `id`를 찾고 `python_module`에 표시된 Python 모듈을 수정합니다. 값이 `null`이면 실행 알고리즘이 확보되지 않은 진단 항목입니다. 큰 조건표는 해당 모듈이 읽는 JSON 규칙도 함께 확인합니다.

Swagger의 **Python 추가 전환 · 계산 가능**에서 원하는 한글 이름을 선택합니다. 기본 예시로 AI 해석을 요청하거나 `include_ai=false`로 계산만 확인합니다. 달력 전용 2개는 AI 요청 없이 실행합니다. **자료 진단** 항목에서는 `analysis.unresolved_dependencies`와 전체 목록의 `issues[].required_materials`를 확인합니다.

현재 공식 MySQL 실행 기준 해석 준비 **65개**, 달력 계산 전용 **2개**, 부분 계산 **108개**로 Python 실행 경로는 **175개**입니다. 활성 목록 **291개**는 준비65·계산전용2·자료필요199·묶음/보조17·과거판8로 구성됩니다. DLL 의존11종과 실행없는 관련 메뉴 진단4개를 제거했습니다. 추가 Python 핸들러166개와 기본9종을 구분하며, 원본/자료가 필요한 미구현91개를 완료된 운세로 세지 않습니다.

원본 자체의 달력·분기·배열·변수 덮어쓰기 등은 확인된 규칙을 따릅니다. `source_limits`에 설명한 제약과 입력별 오류를 확인하세요. 서로 다른 ASP 엔진의 달력을 공통 라이브러리 값으로 일괄 대체하지 않습니다. 상용 서버의 실제 결과와 전체 동일성은 아직 검증되지 않았습니다.

```sh
python_api/.venv/bin/python -m pytest -q python_api/tests tools
python_api/.venv/bin/ruff check python_api/app python_api/tests python_api/tools tools
node .project/_tools/project-dashboard.mjs check
```

작업 전 보드 상태를 확인하고 변경을 T/CR에 연결합니다. 코드를 바꾸면 기능 명세도 갱신합니다.

## ASP 보관과 출처

원본 ASP·과거 사이트·영상·이미지·운영 설정은 `.local/woonari/archive/legacy-asp-20261118/`에 비공개 보관합니다. 되돌릴 수 있는 보관이며 Git·배포 사본에는 넣지 않습니다. 활성 소스 루트와 배포 사본에는 ASP 파일을 두지 않습니다.

`python_api/tools/data/legacy_source_inventory.json`은 원문이 없는 파일 해시·줄 수·메뉴 조사 자료입니다. 두 `docs/*source_manifest.json`의 해시는 보관 원본에 대한 출처 기록입니다. 파일 경로·줄 번호는 과거 원본을 가리킵니다. 테스트는 고정된 이식 결과와 출처 메타데이터를 검증하므로 원본 파일 없이 실행됩니다. 원본이 없는 조사 도구는 고정 자료를 사용했다고 명시하며 새로 소스를 읽었다고 표시하지 않습니다.

미확보 항목을 해결하려면 전체 목록의 필요 자료를 확보한 뒤 Python 모듈·판정표·입력 검증·회귀 사례를 추가합니다. 특히 `yearfortune` 판정 데이터, `tbAisyo`, NHCP5 내부 계산, 행성 분류표, interlife 판정 값과 누락된 결과 소스는 본 만세력 DB에 없습니다. 원문 문구를 AI로 교체하는 작업과 이러한 판정을 복구하는 작업을 구분합니다.

## DB·AI·Git

공식 실행은 전용 시크릿을 통해 MySQL `woonari` DB를 조회합니다. 테스트는 동일한 73,414행의 SQLite 스냅샷을 사용합니다. `.local/woonari`의 DB/AWS/AI/Git 설정은 비공개이며 배포하지 않습니다.

Bedrock Claude는 명시한 IAM 또는 사용자 승인 AI 전용 계정의 장기 키 모드를 사용합니다. 장기 키는 `.local/woonari/ai/bedrock.env`에만 두며, `api.env`의 `BEDROCK_AUTH_MODE=api_key`와 `BEDROCK_ACCOUNT_ID`로 발급 계정을 고정합니다. DB·CLI 계정은 유지합니다. 모델 전송 시도는 한국시간 하루 최대100회, 재시작·동시 요청에도 합계를 유지하며 전송 후 실패도 차감합니다. `GET /v1/ai-usage`는 잔여 횟수를 제공하고 초과 시429입니다. 계산·원본자료 미완성·입력 오류·전송 전 키 검증 실패는 차감하지 않습니다. 사용량DB를 삭제해 초기화하지 마세요. `/health`는 설정 존재, 실제 생성은 POST 결과로 확인합니다.

Git 작업 사본은 `.publish/woonari`입니다. 다음 명령은 Python 전용 사본으로 동기화하며 사본의 과거 ASP·자산을 제거하고 `.git` 이력은 보존합니다.

```sh
python3 tools/prepare_github.py
python3 tools/prepare_github.py --verify
./woonari git status --short
```

실제 커밋·푸시는 전용 GitHub 로그인명·작성자와 저장소 쓰기 권한을 확인한 뒤 수행합니다. 공용 인증으로 대체하지 않습니다.

작업트리에서 ASP를 지워도 과거 커밋에 ASP·사이트 자산이 있으면 함께 전송될 수 있습니다. Python 전용 최초 게시에는 기존 로컬 참조를 보존한 채 부모 커밋이 없는 새 게시 브랜치를 준비합니다.

```sh
./woonari git prepare-python-branch publish/python-api-20261123
```

이 명령은 검증된 게시 사본만 스테이징하며 작성자를 추정하거나 커밋·인증·네트워크 요청을 수행하지 않습니다. 이전 브랜치와 파일은 보존하고, 실패하면 기존 HEAD와 index로 복원합니다. 이후 지정된 작성자로 커밋한 뒤 `./woonari git push`를 실행합니다. push는 ASP·비공개 경로·과거 사이트 자산이 도달 가능한 이력에 포함돼 있으면 중단합니다. 강제로 덮어쓰지 않습니다. CR-017 사용자 지시에 따라 최초 게시 브랜치는 main으로 전환 후 삭제하며 이후 검증된 변경은 main에 계속 push합니다.

AI 실제 테스트(2026-11-19): 일일·연인 심리분석·평생의 V5 결과를 확인했습니다. 원본 계산은 변하지 않았고 해석3/4/13항목이 반환됐습니다. 초기 문장 품질 보완을 포함해 모델 전송은 총6회였으며 테스트 시점 잔여94회입니다. 근거가 없는 선택키·당사주 문자만으로 성격이나 시기별 길흉을 단정하지 않고 일반 조언·확인 질문으로 제한합니다. 이 검증 이후 CR-018 사용자 승인으로 사주 기반 연간 AI 해석을 추가했습니다. 2027년 본문은 생성하고 기존 연간 DB 별점·점수는 제공하지 않습니다.

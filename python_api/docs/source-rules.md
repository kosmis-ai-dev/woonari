# 원본 규칙과 Python 개발 · CR-012

서비스 실행 코드는 모두 Python입니다. 작은 계산은 `app/ported_*.py`에 직접 옮겼고, 큰 조건표·명식 표시·자미 계산은 `app/data/*.json`의 정적 표와 구조화된 조건 트리를 Python 실행기가 처리합니다. ASP 파일·IIS·COM·동적 `eval`/`exec`는 실행하지 않습니다.

## 파일 역할

| 위치 | 역할 |
|---|---|
| `app/service_engine.py` | 서비스 등록·입력 검증·계산 근거·해석 출력계약 구성 |
| `app/ported_direct.py`, `ported_loveunse.py`, `ported_remaining.py`, `ported_template.py` | 원본별 산술·표·분기·선택키 |
| `app/ported_interlife*.py` | interlife의 개별 서비스·전용 달력·표시·원본행 바인딩 |
| `app/ported_data_rules.py` | 달력·택일·방위·심리 선택 등 원본행을 소비하는 규칙 |
| `app/ported_ziwei.py` | 정적 조건 트리를 처리하는 제한된 Python 계산 실행기 |
| `app/data/*.json` | 원본에서 추출한 표·배열·조건·출처 해시·서비스 목록 |
| `tests/fixtures/`, `tools/data/` | 독립적으로 동결한 기대값과 원문 없는 출처 정보 |

조건 트리는 공개 API의 입력이 아닙니다. 서비스 입력은 생년월일과 각 Swagger에 설명된 값만 받습니다. 원본 연결 함수와 SQL 조회는 계산에서 분리하며, 정적 규칙의 SQL 문자열을 실제 DB에 실행하지 않습니다. 현재 실제 DB 연결은 전용 MySQL 만세력 저장소입니다.

## 원본행과 미확정 값

확인되지 않은 원본행은 `Missing`으로 추적합니다. 이는 VB의 미할당 `Empty`, DB의 `NULL`과 다릅니다. 빈 값·정수·문자열·논리값의 원본 계산 규칙을 유지하며, 판정을 좌우하는 미확정 값을 0이나 임의 코드로 채우지 않습니다.

HTML을 포함한 내부 문자열도 원본 그대로 보존합니다. 원본은 표시 문자열을 다시 읽어 분류하기도 하므로 HTML 제거는 공개 결과를 구성할 때만 적용합니다. 계산을 관찰하는 내부 함수도 원래 식의 자료형·리터럴 비교 의미를 유지해야 합니다.

`source_rows`, `source_fields` 등 조사 입력이 있는 항목은 지정된 열과 자료형을 검증합니다. 수동으로 입력한 행을 실제 원본 DB 자료로 인증하지 않으며 이 입력으로 AI 차단을 우회하지 않습니다. 실제 판정 데이터를 확보하면 검증된 서버 저장소와 연결한 뒤 해석 준비 상태·개인정보 제외·실서비스 대조를 다시 확인합니다.

공통 헤더가 읽는 모든 테이블이 개별 결과에 필요한 것은 아닙니다. 실제 출력·선택키·점수·분기에 도달하는 의존성을 기준으로 판단합니다. DB 본문이 단순 출력인 경우와 본문 안의 표시를 읽어 다시 분기하는 경우도 구분합니다.

## 수정 기준

도메인 수식을 바꿀 때는 해당 Python 모듈 또는 정적 규칙을 고치고, 원본 사례·경계·이전 변수 상태를 검증하는 회귀 사례를 추가합니다. 원본 결함을 의도적으로 고치는 변경은 출처 규칙 보존과 구분해 작업/수정 요청에 기록합니다. 원본 해시를 새 코드의 해시로 덮어쓰지 않습니다.

VB 자료형 차이는 결과를 바꿀 수 있습니다. 문자열 두 개의 `+`, 음수 `Mod`, 기본 `ByRef`, 반복문의 제어변수, `NULL`과 미할당 값 등을 일반적인 Python 산술로 일괄 대체하지 않습니다. 특히 리터럴과 변수 비교는 다르게 동작합니다. [Microsoft의 VBScript 비교 설명](https://learn.microsoft.com/en-us/archive/blogs/ericlippert/typing-hard-can-trip-you-up), [Microsoft 연산 우선순위](https://learn.microsoft.com/en-us/office/vba/language/reference/user-interface-help/operator-precedence)를 참고하세요.

일부 원본 문법의 호환성은 [Wine의 VBScript 구현](https://github.com/wine-mirror/wine/tree/master/dlls/vbscript)과 언어 회귀 사례도 조사했습니다. 이 조사는 현재 상용 IIS 서버에서 동일 결과를 관측했다는 뜻은 아닙니다. 원본 난수는 범위·분기·요청 상태를 보존하되 IIS 난수 시드별 동일 수열을 검증했다고 주장하지 않습니다.

전체 테스트와 API 입력 예시는 ASP 원본을 읽지 않습니다. 동결된 원본 표·기대값·해시와 Python 출력·오류·자료형·출력계약을 확인합니다. 실제 원본 DB/DLL·상용 서버의 전체 실행 등가성은 해당 자료를 확보한 후 별도로 검증합니다.

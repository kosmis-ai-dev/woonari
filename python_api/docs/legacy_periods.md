# CR-001 / T-005 — 월간·연간 원본 판정 이식

구현은 `app/legacy_periods.py`의 `decide_period(kind, request, saju)`입니다. ASP의 계산·분기·조회 조건을 반환하며, 본문 데이터나 수치 판정을 AI가 대신 계산하도록 하지 않습니다.

## 월간

기준 소스는 `old/unse/monthluck/main_end.asp` 전체입니다. 공통 계산 근거는 `function/dokebi.asp`의 `CalcSaju`와 `CalcMemNo`입니다.

- `Left(CalcMemNo(...), 1)`을 `memno`로 사용합니다.
- 성별 SQL 값은 남성 `남`, 여성 `녀`입니다.
- ASP 서버의 `Date()`는 API의 명시적 `target_date`에 대응합니다.
- `manse`에서 읽는 월주 원본 값은 절입 전 월주입니다. `div_name`이 홀수이면 월주 인덱스를 1 올리고 59→0으로 순환합니다. 소스는 월간 조회 시 절입 시각을 비교하지 않습니다. 따라서 입춘 날짜의 오전 요청도 이미 다음 월주로 분기합니다.
- 최종 본문 조회는 `monthfor WHERE memno=... AND yukgap_no=... AND sex=...`, 선택 열은 `contents`입니다. 이 키를 그대로 AI의 결과 작성 근거로 전달할 수 있습니다.

제공된 `tb_manse` DB의 `m_gan/m_ji`를 절입 전 월주로 대응하고, `div_name/div_hour/div_min`을 원본 그대로 사용합니다. 월 범위는 DB의 홀수 절기 날짜부터 다음 홀수 절기 날짜를 표시합니다. 다음 절입 날짜를 하루 줄이지 않는 이유는 원본의 표시 계약을 보존하기 위해서입니다. 1900-01-01~01-05는 이전 절입이 제공 DB 밖이므로 월간 조회를 `calendar_boundary_unavailable`로 거절합니다. `1945-06-06 div_name=8`도 원본 그대로여서 해당 월의 파생 표시기간은 05-06~07-07입니다.

제공 `tb_manse`에는 `disp_day` 열이 없습니다. `replacement_disp_day`는 위 절입 날짜로 생성한 대체 기본 데이터이며, 원본 값과 완전히 동일하다는 뜻이 아닙니다. 이 불확실성은 결과의 `facts.calendar_replacement.limitation`에 남깁니다. 계산값·점수 DB를 대신 추정하는 것은 없습니다.

## 과거 ASP 연간 진단

CR-018 이후 공개 yearly API는 `app/annual_ai.py`의 사주 기반 AI 해석으로 실행합니다. 아래 내용은 과거 ASP 동일 결과 재현의 진단/단위 테스트 기록이며 현재 API의 연도 제한이나 AI 차단 조건이 아닙니다.

기준 소스는 `old/unse/2014yearluck/main_end.asp` 전체입니다. 실제 연도 선택은 파일명이나 오늘의 입춘 기준 연도가 아니라 소스의 `code` 분기를 따릅니다.

- `code`가 빈 경우 원본 기본값은 **2013**입니다. API는 `target_date`가 필수이므로 그 연도를 `code`에 대응시키고, 원본 기본값은 사실로 기록합니다.
- 원본 `Select Case`에는 **2001~2014**만 있습니다. 그 외 연도는 `legacy_year_unsupported` 오류로 거절합니다. 사주 간지의 60년 순환으로 임의 확장하지 않습니다.
- `memno`와 `sex`는 월간과 같은 원본 매핑입니다.
- 원본 선택 조건은 `yearfortune WHERE memno=... AND sex=... AND year_pillar=... ORDER BY num`입니다. 본문과 함께 선택하던 열도 그대로 기록합니다.
- `period_start/end`는 조회하는 code 연도의 API 범위입니다. 원본 각 행의 `solar` 표시 범위가 재현된 것은 아닙니다.

이 소스는 `section`, `star_cnt`, `solar`, `mark1`~`mark11`을 **DB에서 그대로 읽습니다**. 별 개수·운세 그래프 수치·항목 구간을 계산하는 ASP 산식이 없습니다. 원본 행을 확보하지 못했으므로 이 값은 `None`이며 `unresolved`에 기록합니다. `sol1`~`sol5` 부적 선택도 본문 `content`와 별도의 원본 DB 판정이므로 AI가 원본 값처럼 생성하면 안 됩니다.

원본의 다음 조건은 표현식으로 보존하되, 실제 행이 없으므로 실행 결과는 미확정입니다.

- `section <> 0`: DB `star_cnt`만큼 별 표시
- `section < 20`: DB `solar` 기간 표시
- `section = 0 And sol1 <> ''`: 본문/부적 출력 분기
- `section < 20 And CStr(code) > '2003'`: DB `mark1`~`mark11` 그래프 표시
- `num` 정렬 후 행 인덱스 8부터 월별 제목 분기

이 모듈은 신규 정오 표본이나 대체 점수를 만들지 않습니다. 연간 본문의 선택키는 복원했지만, 본문만 AI로 바꾸면서 기존 상용 숫자·분류까지 동일하게 제공하려면 위 DB 메타데이터가 필요합니다.

## 검증

CR-014 백업 복원 결과, 구 `yearfortune del`은 0행이다. 다른 구조의 `TB_yearLuck` 7,000행과 `TB_yearLuck_mon` 1,200행을 확보했으나 새 키·성별·항목 매핑은 미검증이다. 2021~2050년 연간 행은 본문이 비어 있고 별점 1·점수 0인 초기 행이며, **2027년 140행도 완성된 판정이 아니다**. 따라서 과거 ASP 동일 결과 재현용 진단의 미확보 상태는 유지한다. 현재 사주 기반 연간 AI 해석은 이 자료와 무관하게 실행한다. 공식 서버의 `GET /v1/restored-data?year=2027`에서 별도 MySQL 적재 상태와 필요한 매핑을 확인한다. 자세한 내용은 [복원 안내](../../docs/mssql-restore.md)를 따른다.

`tests/test_legacy_t_005.py`는 월간의 입춘 당일 조기 전환·전날 분기·짝수 절기·59→0·성별·절기 기간, 연간 14개 명시적 연도 분기·빈 code 기본값·지원 밖 연도 거절·DB 숫자 미생성을 검증합니다. 원본 MSSQL 실행 결과와의 동일성 검증은 아닙니다.

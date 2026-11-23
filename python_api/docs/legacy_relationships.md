# CR-001 / T-007: 직업·연애·숙명의 궁합 판정 경로

상용 ASP에서 확인되는 분기와 문구 선택 경로를 보존한다. ASP·SQL·COM을 실행하지 않으며 원본 접속정보를 읽거나 사용하지 않는다. 공통 `CalcSaju`/`CalcMemNo`의 기초 만세력 데이터 대체는 상위 계산 모듈에서 처리한다.

## 연애운: 문구 선택키 이식 완료

원본 `old/unse/loveluck/main_end.asp:91-123`:

1. `CalcSaju` 결과로 `CalcMemNo`를 호출한다.
2. `rsDokebi = Left(dokebiNo,3)`으로 일주 분류코드를 만든다. 선행 0도 보존한다.
3. 남성은 `m`, 여성은 `f` 필드를 선택한다.
4. `tbLoveLuck WHERE dokebi=rsDokebi`에서 아래 다섯 필드를 조회한다.

| 출력 | 남성 필드 | 여성 필드 |
|---|---|---|
| 인연을 만날 시기 | time_m | time_f |
| 인연의 성격 | youtype | youtype |
| 인연의 직업 | youjob | youjob |
| 인연과 만날 장소 | locate | locate |
| 사랑 스타일·전략 | method_m | method_f |

`decide_relationship('love',...)`는 이 다섯 선택키를 각각 반환한다. 이전의 당일 점수 재사용을 제거했으며 조회 날짜에 따라 일주 분류코드를 바꾸지 않는다. 기존 DB 문구는 사용하지 않고, 확정된 분류코드·사주 근거·출력 항목으로 AI가 문장을 생성한다. DB 문구의 의미나 표현까지 동일하다고 주장하지 않는다.

## 직업운: 원본 분기 이식, DLL 내부 판정 미확보

원본 `old/unse/carrerluck/main_end.asp:1351-1559`의 최종 직업운 문구는 `NHCP5.NHUnse`의 결과다. `accountlist.input10`은 선택한 동기 분류 `soCode`이며 A~E 각각 세 개의 소주제를 가진다. F는 전체 A1~E3를 조회한다. `tmpCode='002'`는 고정이다.

`career_dispatch(category)`는 원본과 같은 순서로 `getNHResult('002', category+'1'..'3')` 호출과 `unseResult[0]` 출력 항목을 반환한다. F의 경우 15개 모두 반환한다. 제목은 ASP `Select Case soCode`의 문자열을 보존한다. 요청의 `career_category`는 기존 `accountlist.input10`에 대응한다.

`getNHResult` 내부 계산·분류를 추출할 DLL 소스가 현재 폴더에 없다. 따라서 카테고리가 있어도 `unresolved`가 남으며, 일일 취업점수 또는 임의 직업 추천으로 대신하지 않는다. 원본의 사주 오기·신살 등 화면 계산 일부는 별도 부가 표시이며 이 모듈은 이를 이식 완료했다고 표시하지 않는다. DLL 최종 판단을 원본과 일치시키려면 원본 DLL 구현 또는 판정 명세가 필요하다.

## 숙명의 궁합: 27숙 분류 의존성을 보존

원본 `old/unse/fatewedluck/main_end.asp:5-15`는 다음 네 항목을 고정한다.

1. `saju_harmony_1`: 당신의 마음
2. `saju_harmony_2`: 상대의 마음
3. `saju_harmony_3`: 두사람의 숙명
4. `saju_harmony_4`: 두사람의 숙명에 대한 조언

실제 선택키는 `function/b_include/lib_sajumaster.asp:4-28,223-260`에서 결정된다. 양력 출생일 `YYYY-MM-DD`에 대해 `tbAisyo.aisyo`를 조회한다. 이것은 문구가 아닌 판정용 분류 데이터다. 본인의 `MyAisyo`와 상대의 `YouAisyo`를 확인한 뒤:

- 본인 마음: `tbSajuMaster_mobile1(menu='destiny', keyno=1xx)` + `2xx`, xx=MyAisyo
- 상대 마음: 같은 menu, xx=YouAisyo
- 두사람의 숙명: `menu='harmony', keyno=3xx`
- 숙명에 대한 조언: `menu='harmony', keyno=4xx`
- 마지막 두 항목의 xx는 `AisyoTbl(MyAisyo-1)(YouAisyo-1)`이다.

`AisyoTbl` 전체 28×28 값은 `_SajuManseryuk.asp:39-66`에서 이식했다. 20번 슬롯은 원본처럼 전부 0이며, 테이블은 대칭이라고 가정하면 안 된다. 예를 들어 `[1,19]`는 2, `[19,1]`은 1이다. `harmony_content_selectors(my_aisyo,other_aisyo)`는 분류 데이터가 준비되었을 때 원본의 여섯 조회키를 만든다.

현재 날짜별 `tbAisyo` 원본 데이터가 없으므로 `decide_relationship('compatibility',...)`는 두 출생일의 분류 조회키와 네 출력 항목을 보존하고 `unresolved`를 반환한다. 기존에 임의로 추가했던 육합·충 기반 궁합으로 대체하지 않는다. 원본은 본인/상대 성별 슬롯을 각각 1/2로 고정했지만 이 네 항목의 선택키에는 성별이 사용되지 않는다. 결제·회원·이름 치환·HTML 변환은 운세 판정에서 분리한다.

## 검증

`tests/test_legacy_t_007.py`는 성별별 연애 필드, 일주 분류의 선행 0, 조회 날짜 독립성, 직업 A~F 분기·15개 순서, 미확보 DLL 차단 상태, 음력→한국 양력 후 27숙 조회일, 방향성 있는 궁합 선택키, 전체 원본 테이블 784칸의 SHA-256 스냅샷을 검사한다. 원본 서비스의 DB/DLL이 실행된 결과와 전체 동일성은 미검증 상태다.

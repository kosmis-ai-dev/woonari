# ASP 전체 서비스·문제 조사표

현재 이식 검토: 2026-11-18 · CR-012 / T-024

- 306개 항목: 해석 계약 준비 62, 계산전용 2, 원본 자료/계약 확인 필요 217, 묶음·보조 17, 과거판 8. 추가 Python 핸들러 166개와 기존 /v1/fortunes 경로 10개를 구분합니다.
- 기본 음양력·간지·절입은 사용자 제공 script.sql의 dbo.tb_manse 73,414행을 조회합니다. 원본 데이터 범위는 1900-01-01~2100-12-31이며 공개 API 범위는 기존 1900~2050년을 유지합니다.
- 공식 ./woonari 실행은 제공된 만세력 데이터를 적재한 MySQL woonari.tb_manse를 조회하도록 구성됩니다. 선택한 DB 조회가 실패해도 독립 달력이나 다른 DB로 자동 대체하지 않습니다.
- ASP의 절입 분·00:30 일주 경계와 함수별 23:30 시주 규칙을 적용합니다. 검증된 lunar-leap-flags-v1 교정표로 윤달 표시 오류 10행을 조회 시 수정해 원본의 음력 중복 4건과 잘못된 평달·윤달 구분을 해결합니다. 원본 행·해시는 보존하며 교정 후 미해결 중복만 422 ambiguous_lunar_date로 거부합니다. 고정 UTC+09:00이며 역사적 DST·진태양시를 추가 보정하지 않습니다.
- ASP/DB/DLL을 실제 실행한 결과와의 완전한 등가성은 정적 분석만으로 보장하지 않습니다.
- tb_manse 적재가 yearfortune·tbAisyo·직업 DLL의 별도 판정 자료 확보를 뜻하지 않습니다. 연간·직업·궁합은 계속 진단 전용이며 문구를 AI로 생성하는 단계와 판정 자료를 구분합니다.
- interlife의 실제 출력 의존성을 확인한 leaf만 개별 이식했습니다. 기본 날짜가 전용 코드·행번호·월장·점수·대운 프로필과 같다고 가정하지 않습니다. 개별 상태와 미확정 필드를 확인하세요.
- 모든 진단 GET은 ASP/SQL/COM/AI를 호출하지 않습니다. AI 생성 여부는 서버 설정과 실제 POST 호출로 별도 확인합니다.
- 확인된 의존성만 개별 항목에 표시합니다. needs_review는 추가 추적/대조가 필요한 부분입니다.
- 새로운 실제 계산/부분 계산 핸들러는 POST /v1/un/{service_id}로 테스트합니다. test_path=null인 원본 자료 대기 항목의 같은 POST는 문제 진단만 반환하며 계산 구현 완료를 뜻하지 않습니다. 기존 10개 /v1/fortunes/{kind}는 그대로 제공합니다.
- ready는 코드의 판정·문구 출력 계약 준비 상태입니다. AI 전용 장기 키의 실제 발급 계정과 추론 프로필을 검증하며, IAM·장기 키의 모델 권한/FTU(사용 사례 등록) 상태는 별도이므로 설정 존재만으로 실제 AI 생성 성공을 보장하지 않습니다. Woonari 모델 전송은 한국시간 일일 최대100회이며 GET /v1/ai-usage로 확인합니다.
- 원본 결과 ASP/분기 누락, 외부 제공사 구현 미확보, DLL 내부 판정 불투명, 메뉴 연결 미확정은 서로 다른 차단 사유로 보존합니다. 외부 동영상 6개도 자체 판정 코드가 없어 계속 차단합니다.

레코드에는 실제 서비스/메뉴 변형/과거판/묶음/보조 코드/소스 누락 선언이 포함됩니다. 이름이나 경로가 같은 변형은 독립 알고리즘 수가 아니며, 동일 이름의 서로 다른 원본은 자동 병합하지 않습니다.

## 상태별 수량

| 상태 | 개수 |
|---|---:|
| `archived` | 8 |
| `source_required` | 217 |
| `reference` | 17 |
| `ready` | 62 |
| `calculation_only` | 2 |

ready는 계산·해석 계약 준비이며 실제 AI 생성 성공과 별개입니다. 계산전용은 include_ai=false입니다. test_path가 없는 항목의 POST는 자료 진단만 반환합니다.

## 전체 목록

| 원본 이름 | 식별자 | 상태 | 계산 경로 | 미확정 조건 |
|---|---|---|---|---|
| 2010~2011 도통비결 | `1011yearluck` | 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요 | 진단만 | source_year_specific, numeric_metadata_in_text_table |
| 2011~2012 도통비결 | `1112yearluck` | 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요 | 진단만 | source_year_specific, numeric_metadata_in_text_table |
| 2012~2013 도통비결 | `1213yearluck` | 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요 | 진단만 | source_year_specific, numeric_metadata_in_text_table |
| 2009 도통비결 | `2009yearluck` | 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요 | 진단만 | source_year_specific, numeric_metadata_in_text_table |
| 2010 도통비결 | `2010yearluck` | 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요 | 진단만 | source_year_specific, numeric_metadata_in_text_table |
| 2011 도통비결 | `2011yearluck` | 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요 | 진단만 | source_year_specific, numeric_metadata_in_text_table |
| 2012 도통비결 | `2012yearluck` | 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요 | 진단만 | source_year_specific, numeric_metadata_in_text_table |
| 2013 도통비결 | `2013yearluck` | 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요 | 진단만 | source_year_specific, numeric_metadata_in_text_table |
| 2014 도통비결 | `2014yearluck` | 조회키 진단 가능 · 원본 판정 자료 필요 | /v1/fortunes/yearly | legacy_year_unsupported, yearfortune_decision_data_missing |
| 운세 결과 메일·파일 다운로드 | `fso` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | auxiliary_delivery |
| 인맥 구축·조직 관리법 | `humanorganizationmanagement` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/humanorganizationmanagement | 실행 제약은 상세 참조 |
| 상사와의 관계 | `mastermanrelations` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/mastermanrelations | planet_fdastro_classification_missing |
| 사회 속의 나의 명예 | `socialmyhonor` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/socialmyhonor | planet_fdastro_classification_missing |
| 성인운세 모음 | `adultluck` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | collection_needs_subservice_audit |
| 나의 운세처방 | `adviceluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/adviceluck | major_luck_display_boundary_missing |
| 연인 심리분석 | `analysisluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/analysisluck | 실행 제약은 상세 참조 |
| 동물점 | `animalluck` | 원본 DLL 판정 소스·대조 검증 필요 | 진단만 | opaque_com_rule |
| 나의 원초적 본능 | `basicluck` | 원본 DLL 판정 소스·대조 검증 필요 | 진단만 | opaque_com_rule |
| 바이오리듬 | `bioluck` | 계산·선택키 이식 완료 · AI 연결 설정 필요 | /v1/fortunes/biorhythm | 실행 제약은 상세 참조 |
| 탄생일운세 | `birthluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/birthluck | historical_birth_reference_data_missing |
| 혈액형운세 | `bloodluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/bloodluck | 실행 제약은 상세 참조 |
| 비즈니스 성공운 | `businessluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/businessluck | 실행 제약은 상세 참조 |
| 월운세 달력 | `calendarluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/calendarluck | missing_rule_rows |
| 차량번호운세 | `carluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/carluck | 실행 제약은 상세 참조 |
| 나에게 맞는 직업 | `carrerluck` | 조회키 진단 가능 · 원본 판정 자료 필요 | /v1/fortunes/career | nhcp5_calculation_missing |
| 주역점 | `coinluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/coinluck | hexagram_name_mapping_missing |
| 나와 맞는 이성 궁합 | `correctyouluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/correctyouluck | 실행 제약은 상세 참조 |
| 상담용 오기 | `counselluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/counselluck | major_luck_num_disp_day_missing |
| 띠별궁합풀이 | `ddiluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/ddiluck | 실행 제약은 상세 참조 |
| 숙명의 궁합 | `fatewedluck` | 조회키 진단 가능 · 원본 판정 자료 필요 | /v1/fortunes/compatibility | aisyo_classification_missing |
| 내 몸의 기 | `fivegiluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/fivegiluck | major_luck_num_disp_day_missing |
| 탄생화운세 | `flowerluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/flowerluck | birth_flower_identity_missing |
| 격국풀이 — 내 삶의 나침반 | `gyukgukluck` | 원본 DLL 판정 소스·대조 검증 필요 | 진단만 | opaque_com_rule |
| 한자운세 | `hanjaluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/hanjaluck | source_hanja_key_and_keyword_unverified |
| 휴대폰운세 | `hpluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/hpluck | 실행 제약은 상세 참조 |
| 이상형찾기 | `idealluck` | 원본 DLL 판정 소스·대조 검증 필요 | 진단만 | opaque_com_rule |
| 인터라이프 운세 모음 | `interlife` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | interlife_subservices_mixed_status, original_header_include_missing |
| 탄생석운세 | `jewelryluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/jewelryluck | birth_stone_identity_missing |
| 주민번호운세 | `juminluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/juminluck | 실행 제약은 상세 참조 |
| 주소지운세 | `jusoluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/jusoluck | 실행 제약은 상세 참조 |
| 평생운세 | `lifeluck` | 계산·선택키 이식 완료 · AI 연결 설정 필요 | /v1/fortunes/lifetime | 실행 제약은 상세 참조 |
| 로또운세 | `lottoluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/lottoluck | 실행 제약은 상세 참조 |
| 사랑과 결혼 | `loveandluck` | 원본 DLL 판정 소스·대조 검증 필요 | 진단만 | opaque_com_rule |
| 러브 어드바이스 | `loveluck` | 계산·선택키 이식 완료 · AI 연결 설정 필요 | /v1/fortunes/love | 실행 제약은 상세 참조 |
| 웨딩예감 | `loverluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loverluck | 실행 제약은 상세 참조 |
| 파라미터형 종합 운세 | `loveunse` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | im6_missing_subservice_selector |
| 사랑만들기 | `makingloveluck` | 원본 DLL 판정 소스·대조 검증 필요 | 진단만 | opaque_com_rule |
| 결혼택일 | `marriageluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/marriageluck | missing_auspicious_day_rules |
| 미팅 연애운세 | `meetluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/meetluck | 실행 제약은 상세 참조 |
| 심리테스트 | `mindluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/mindluck | missing_questionnaire_graph |
| 명품 평생재물운 | `moneyluck` | 계산·선택키 이식 완료 · AI 연결 설정 필요 | /v1/fortunes/wealth | 실행 제약은 상세 참조 |
| 이달의 운세 | `monthluck` | 계산·선택키 이식 완료 · AI 연결 설정 필요 | /v1/fortunes/monthly | 실행 제약은 상세 참조 |
| 이사택일 | `moveluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/moveluck | missing_auspicious_day_rules |
| 정통궁합 | `originalwedluck` | 원본 DLL 판정 소스·대조 검증 필요 | 진단만 | opaque_com_rule |
| 서로를 성장시키는 비결 | `ourgrowthluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/ourgrowthluck | 실행 제약은 상세 참조 |
| 향수점 | `perfumeluck` | 원본 DLL 판정 소스·대조 검증 필요 | 진단만 | opaque_com_rule |
| 명품 개인종합운세 | `perluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/perluck | 실행 제약은 상세 참조 |
| 도통 전생록 | `preluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/preluck | 실행 제약은 상세 참조 |
| 궁합신살처방 | `sinsalluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/sinsalluck | source_gpcheck_state_required |
| 로또운세 SMS서비스 | `smslottoluck` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | delivery_workflow_separate |
| 오늘의 운세 SMS서비스 | `smstodayluck` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | delivery_workflow_separate |
| 자녀교육법 | `sonluck` | 원본 DLL 판정 소스·대조 검증 필요 | 진단만 | opaque_com_rule |
| 별자리운세 | `starluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/starluck | star_blood_harmony_classification_missing |
| 학생운세 | `studentluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/studentluck | 실행 제약은 상세 참조 |
| 명품 평생애정운 | `sweetluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/sweetluck | 실행 제약은 상세 참조 |
| 오늘의 운세 | `todayluck` | 계산·선택키 이식 완료 · AI 연결 설정 필요 | /v1/fortunes/daily | 실행 제약은 상세 참조 |
| 궁합 UP 가이드 | `wedupluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/wedupluck | planet_fdastro_classification_missing |
| 이번주 운세 | `weekluck` | 계산·선택키 이식 완료 · AI 연결 설정 필요 | /v1/fortunes/weekly | 실행 제약은 상세 참조 |
| 불륜일까? 사랑일까? | `adultluck-affairorloveluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/adultluck-affairorloveluck | 실행 제약은 상세 참조 |
| 부부의 침실 궁합 | `adultluck-bedroommatchingluck` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/adultluck-bedroommatchingluck | planet_fdastro_classification_missing |
| 연인과의 최고 절정의 기술 | `adultluck-lovertechniqueluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/adultluck-lovertechniqueluck | 실행 제약은 상세 참조 |
| 연인의 음란한 소망 | `adultluck-loverwishluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/adultluck-loverwishluck | 실행 제약은 상세 참조 |
| 금단의 섹스 진단 | `adultluck-prohibitionsexluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/adultluck-prohibitionsexluck | 실행 제약은 상세 참조 |
| 은밀한 섹스스타일 | `adultluck-sexluck` | 원본 DLL 판정 소스·대조 검증 필요 | 진단만 | opaque_com_rule |
| 별자리 속궁합 | `adultluck-starcoupleluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/adultluck-starcoupleluck | 실행 제약은 상세 참조 |
| 시간대별 섹스 바이오 | `adultluck-timesexbioluck` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/adultluck-timesexbioluck | 실행 제약은 상세 참조 |
| 운세 메인 메뉴 | `unse-main` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | 실행 제약은 상세 참조 |
| 무료 운세 메인 메뉴 | `unse-free-main` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | 실행 제약은 상세 참조 |
| 동영상운세 메뉴·외부서비스 연결 | `unse-moving-main` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | 실행 제약은 상세 참조 |
| 동영상운세 프레임 | `unse-moving-frame` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | 실행 제약은 상세 참조 |
| 동영상운세 미리보기·전달 | `unse-moving-preview` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | 실행 제약은 상세 참조 |
| 운세 AJAX 전달 도구 | `unse-div` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | 실행 제약은 상세 참조 |
| 연간운세 광고 배너 | `unse-ad-billyear` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | 실행 제약은 상세 참조 |
| 2012년 간지 조견표 | `fivegiluck-age1` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | 실행 제약은 상세 참조 |
| 기의 분류 | `fivegiluck-chart` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | 실행 제약은 상세 참조 |
| 음양 오행 | `fivegiluck-cosmic` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | 실행 제약은 상세 참조 |
| 이번주 로또운세 | `loveunse-lotto` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-lotto | 실행 제약은 상세 참조 |
| 오늘의 섹스운세 | `loveunse-eroticwoto` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-eroticwoto | 실행 제약은 상세 참조 |
| 오늘의 섹스감도 | `loveunse-sexwoman` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-sexwoman | 실행 제약은 상세 참조 |
| 오늘의 경마운세 | `loveunse-horse` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-horse | 실행 제약은 상세 참조 |
| 탄생화운세 | `loveunse-birth-flower` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-birth-flower | 실행 제약은 상세 참조 |
| 혈액형 궁합 | `loveunse-blood-blood` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-blood-blood | 실행 제약은 상세 참조 |
| 플라워운세 | `loveunse-flower` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-flower | 실행 제약은 상세 참조 |
| 오늘의 게임운세 | `loveunse-game` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-game | 실행 제약은 상세 참조 |
| 주간운세 | `loveunse-jugan-unse` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-jugan-unse | 실행 제약은 상세 참조 |
| 왕자의 오늘 데이트 | `loveunse-prince-date` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-prince-date | 실행 제약은 상세 참조 |
| 왕자의 오늘 사랑 | `loveunse-prince-love-today` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-prince-love-today | 실행 제약은 상세 참조 |
| 왕자의 오늘운세 | `loveunse-prince-today` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-prince-today | 실행 제약은 상세 참조 |
| 공주의 오늘 데이트 | `loveunse-princess-date` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-princess-date | 실행 제약은 상세 참조 |
| 공주의 오늘 사랑 | `loveunse-princess-love-today` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-princess-love-today | 실행 제약은 상세 참조 |
| 공주의 오늘운세 | `loveunse-princess-today` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-princess-today | 실행 제약은 상세 참조 |
| 별자리운세 | `loveunse-star-un` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-star-un | 실행 제약은 상세 참조 |
| 첫 데이트 궁합 | `loveunse-firstdate` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-firstdate | 실행 제약은 상세 참조 |
| 첫 섹스 만족도 | `loveunse-firstsex` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-firstsex | 실행 제약은 상세 참조 |
| 오늘의 고스톱운세 | `loveunse-gostop` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-gostop | 실행 제약은 상세 참조 |
| 궁합 | `loveunse-gunghap` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-gunghap | 실행 제약은 상세 참조 |
| 오늘의 레저운세 | `loveunse-leisure` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-leisure | 실행 제약은 상세 참조 |
| 평생사주 | `loveunse-life-all` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-life-all | 실행 제약은 상세 참조 |
| 속궁합 | `loveunse-sok-gonghap` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-sok-gonghap | 실행 제약은 상세 참조 |
| 별자리와 혈액형 심리 | `loveunse-star-blood` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-star-blood | 실행 제약은 상세 참조 |
| 오늘의 데이트운세 | `loveunse-today-date-unse` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-today-date-unse | 실행 제약은 상세 참조 |
| 오늘의 엽기운세 | `loveunse-yupgi-dosa` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/loveunse-yupgi-dosa | 실행 제약은 상세 참조 |
| 관상보기 (마의상법) | `interlife-faceface` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/interlife-faceface | 실행 제약은 상세 참조 |
| 오늘의 띠별운세 | `interlife-free-1` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/interlife-free-1 | 실행 제약은 상세 참조 |
| 사주명식 | `interlife-free-11` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-free-11 | interlife_full_chart_profile_unverified |
| 음양력변환 | `interlife-free-12` | Python 계산 전용 완료 · AI 해석 대상 아님 | /v1/un/interlife-free-12 | 실행 제약은 상세 참조 |
| 꿈해몽 | `interlife-free-13` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-free-13 | dream_search_index_missing |
| 태몽 | `interlife-free-14` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-free-14 | dream_search_index_missing |
| 별자리운세 | `interlife-free-2` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/interlife-free-2 | 실행 제약은 상세 참조 |
| 혈액형운세 | `interlife-free-3` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/interlife-free-3 | 실행 제약은 상세 참조 |
| 주민번호운세 | `interlife-free-4` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-free-4 | source_selector_binding_unverified |
| 행운번호운세 | `interlife-free-5` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-free-5 | lucky_number_classification_missing |
| 혈액형궁합 | `interlife-free-6` | Python 계산·출력 선택키 완료 · AI 생성 설정 필요 | /v1/un/interlife-free-6 | 실행 제약은 상세 참조 |
| 웰빙주택운 | `interlife-free-7` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-free-7 | interlife_month_branch_profile_unverified |
| 바이오리듬 | `interlife-free-8` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-free-8 | interlife_serial_day_contract_unverified |
| 정통궁합(속궁합,겉궁합) | `interlife-gunghap-1` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-1 | interlife_source_execution_unverified |
| 이성의 성격 | `interlife-gunghap-10` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-10 | interlife_source_execution_unverified |
| 인연수1 | `interlife-gunghap-11` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-11 | interlife_source_execution_unverified |
| 인연수2 | `interlife-gunghap-12` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-12 | interlife_source_execution_unverified |
| 속궁합 | `interlife-gunghap-13` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-13 | interlife_source_execution_unverified |
| 겉궁합 | `interlife-gunghap-14` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-14 | interlife_source_execution_unverified |
| 애정운 | `interlife-gunghap-15` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-15 | interlife_source_execution_unverified |
| 부부화합운 | `interlife-gunghap-16` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-16 | interlife_source_execution_unverified |
| 섹스운 | `interlife-gunghap-17` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-17 | interlife_source_execution_unverified |
| 천생복덕운 | `interlife-gunghap-18` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-18 | interlife_source_execution_unverified |
| 사상체질궁합 | `interlife-gunghap-2` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-2 | interlife_source_execution_unverified |
| 용신으로 보는 연인애정운 | `interlife-gunghap-3` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-3 | interlife_source_execution_unverified |
| 그이의 러브스타일 보기 | `interlife-gunghap-4` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-4 | interlife_source_execution_unverified |
| 섹스 토정비결 | `interlife-gunghap-5` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-5 | interlife_source_execution_unverified |
| 침실 섹스궁합 | `interlife-gunghap-6` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-6 | interlife_source_execution_unverified |
| 결혼배필운 | `interlife-gunghap-7` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-7 | interlife_source_execution_unverified |
| 인연은 몇 명 | `interlife-gunghap-8` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-8 | interlife_source_execution_unverified |
| 애인부부운 | `interlife-gunghap-9` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-gunghap-9 | interlife_source_execution_unverified |
| 자미두수 | `interlife-jum-1` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-1 | interlife_ziwei_array_profile_unverified |
| 질병건강운 | `interlife-jum-10` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-10 | interlife_source_execution_unverified |
| 주거가택운 | `interlife-jum-11` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-11 | interlife_source_execution_unverified |
| 사업합작운 | `interlife-jum-12` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-12 | interlife_source_execution_unverified |
| 직장상사운 | `interlife-jum-13` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-13 | interlife_source_execution_unverified |
| 직장부하운 | `interlife-jum-14` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-14 | interlife_source_execution_unverified |
| 육임단시 | `interlife-jum-15` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-15 | interlife_source_execution_unverified |
| 64괘 운세분석 | `interlife-jum-16` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-16 | interlife_hexagram_state_contract_unverified |
| 주역점 | `interlife-jum-2` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-2 | interlife_indirect_numeric_score_missing |
| 주역신수비결 | `interlife-jum-3` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-3 | interlife_source_execution_unverified |
| 영험한 첨 | `interlife-jum-4` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-4 | interlife_source_execution_unverified |
| 단시점 | `interlife-jum-5` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-5 | interlife_source_execution_unverified |
| 육효 | `interlife-jum-6` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-6 | interlife_source_execution_unverified |
| 자식운 | `interlife-jum-7` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-7 | interlife_source_execution_unverified |
| 형제운 | `interlife-jum-8` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-8 | interlife_source_execution_unverified |
| 적성운 | `interlife-jum-9` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-jum-9 | interlife_source_execution_unverified |
| 로또번호운세 | `interlife-lotto-1` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-lotto-1 | interlife_lotto_calendar_profile_unverified |
| 사주명식 | `interlife-manse-1` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-manse-1 | interlife_full_chart_profile_unverified |
| 음양력변환 | `interlife-manse-2` | Python 계산 전용 완료 · AI 해석 대상 아님 | /v1/un/interlife-manse-2 | 실행 제약은 상세 참조 |
| 자동이름풀이 (성 1자·이름 1자) | `interlife-name-1` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-name-1 | interlife_source_execution_unverified |
| 자동이름풀이 (성 1자·이름 2자) | `interlife-name-2` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-name-2 | interlife_source_execution_unverified |
| 자동이름풀이 (성 1자·이름 3자) | `interlife-name-3` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-name-3 | interlife_source_execution_unverified |
| 자동이름풀이 (성 2자·이름 1자) | `interlife-name-4` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-name-4 | interlife_source_execution_unverified |
| 자동이름풀이 (성 2자·이름 2자) | `interlife-name-5` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-name-5 | interlife_source_execution_unverified |
| 셀프용신작명 | `interlife-name-6` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-name-6 | interlife_source_execution_unverified |
| 성씨추명학 | `interlife-name-7` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-name-7 | interlife_source_execution_unverified |
| 올해의토정비결 | `interlife-saju-1` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-1 | interlife_source_execution_unverified |
| 자평명리학 오늘의 운세 | `interlife-saju-10` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-10 | interlife_source_execution_unverified |
| 당사주 평생총운 | `interlife-saju-11` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-11 | interlife_source_execution_unverified |
| 사주로 보는 심리분석 | `interlife-saju-12` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-12 | interlife_source_execution_unverified |
| 살풀이 | `interlife-saju-13` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-13 | interlife_source_execution_unverified |
| 성격운세 | `interlife-saju-14` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-14 | interlife_source_execution_unverified |
| 초년운 | `interlife-saju-15` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-15 | interlife_source_execution_unverified |
| 중년운 | `interlife-saju-16` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-16 | interlife_source_execution_unverified |
| 말년운 | `interlife-saju-17` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-17 | interlife_source_execution_unverified |
| 직업운 | `interlife-saju-18` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-18 | interlife_source_execution_unverified |
| 재물운 | `interlife-saju-19` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-19 | interlife_source_execution_unverified |
| 새해신수 | `interlife-saju-2` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-2 | interlife_source_execution_unverified |
| 선천적기질운 | `interlife-saju-20` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-20 | interlife_source_execution_unverified |
| 태어난계절에따른운 | `interlife-saju-21` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-21 | interlife_source_execution_unverified |
| 자평명리학 평생총운 | `interlife-saju-3` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-3 | interlife_source_execution_unverified |
| 인생풀이 | `interlife-saju-4` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-4 | interlife_source_execution_unverified |
| 사주운세 | `interlife-saju-5` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-5 | interlife_source_execution_unverified |
| 십년대운풀이 | `interlife-saju-6` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-6 | interlife_source_execution_unverified |
| 전생운 | `interlife-saju-7` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-7 | interlife_source_execution_unverified |
| 질병운 | `interlife-saju-8` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-8 | interlife_source_execution_unverified |
| 나의 오행기운세 | `interlife-saju-9` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-saju-9 | interlife_source_execution_unverified |
| 결혼택일 | `interlife-selectDay-1` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-selectDay-1 | interlife_source_execution_unverified |
| 이사택일 | `interlife-selectDay-2` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-selectDay-2 | interlife_source_execution_unverified |
| 특정일운세 | `interlife-selectDay-3` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-selectDay-3 | interlife_source_execution_unverified |
| 천생운 | `interlife-theme-1` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-1 | interlife_source_execution_unverified |
| 현재 운세풀이 | `interlife-theme-10` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-10 | interlife_source_execution_unverified |
| 현재나의운 분석 | `interlife-theme-11` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-11 | interlife_source_execution_unverified |
| 사업운총평 | `interlife-theme-12` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-12 | interlife_source_execution_unverified |
| 재물 모으는 법 | `interlife-theme-13` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-13 | interlife_source_execution_unverified |
| 재물손실 막는 법 | `interlife-theme-14` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-14 | interlife_source_execution_unverified |
| 재테크비법 | `interlife-theme-15` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-15 | interlife_finance_selector_profile_unverified |
| 타로점성술 | `interlife-theme-2` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-2 | interlife_tarot_classification_missing |
| 신통방통 동전점 | `interlife-theme-3` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-3 | interlife_coin_classification_missing |
| 탄생석점 | `interlife-theme-4` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-4 | interlife_birthstone_classification_missing |
| 나의길흉숫자 | `interlife-theme-5` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-5 | interlife_source_execution_unverified |
| 방위점 | `interlife-theme-6` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-6 | interlife_source_execution_unverified |
| 나의 수호천사와 타로점 | `interlife-theme-7` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-7 | interlife_source_execution_unverified |
| 나의별자리사랑 | `interlife-theme-8` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-8 | interlife_source_execution_unverified |
| 피해야할상대 | `interlife-theme-9` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-theme-9 | interlife_source_execution_unverified |
| 육임정단 | `interlife-yukim-1` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-yukim-1 | interlife_woljang_classification_unverified |
| 지두법(길흉속지법) | `interlife-yukim-2` | Python 부분 계산 완료 · 판정 자료/계약 필요 | /v1/un/interlife-yukim-2 | interlife_source_execution_unverified |
| 자동이름풀이 (공통 결과 처리) | `interlife-name-puri` | 묶음·보조 코드 · 개별 계산 대상 아님 | 진단만 | 실행 제약은 상세 참조 |
| 미니만세력 | `interlife-free-9` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_source_missing |
| 일반만세력 | `interlife-free-10` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_source_missing |
| 좋은글 알림SMS | `missing-todayprovluck` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_source_missing |
| 월운세 바탕화면 | `missing-monthbgluck` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_source_missing |
| 나의 인생스타일 | `missing-comforyou` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_source_missing |
| 도통 만세력 | `missing-manseluck` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_source_missing |
| 주식투자에 좋은 사주는? | `stockluck-m1` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_source_missing |
| 무료 대박주식운세 | `stockluck-m2` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_source_missing |
| 사주추천종목알림이SMS | `stockluck-m6` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_source_missing |
| 프리미엄 대박주식운세 | `stockluck-m3` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_source_missing |
| 급등주 대박주식운세 | `stockluck-m4` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_source_missing |
| 기운보강 + 주식부적 | `stockluck-m5` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_source_missing |
| 적중 2012 토정비결 | `external-video-b` | 외부 제공사 구현 미확보 · 생성 차단 | 진단만 | external_implementation_missing |
| 적중 궁합 | `external-video-f` | 외부 제공사 구현 미확보 · 생성 차단 | 진단만 | external_implementation_missing |
| 적중 취업운 | `external-video-c` | 외부 제공사 구현 미확보 · 생성 차단 | 진단만 | external_implementation_missing |
| 나의 전생 얼굴보기 | `external-video-d` | 외부 제공사 구현 미확보 · 생성 차단 | 진단만 | external_implementation_missing |
| 미래 내 배우자 얼굴 | `external-video-e` | 외부 제공사 구현 미확보 · 생성 차단 | 진단만 | external_implementation_missing |
| 미래 내 아이 얼굴 | `external-video-a` | 외부 제공사 구현 미확보 · 생성 차단 | 진단만 | external_implementation_missing |
| 우리 애정스타일 | `missing-richgung` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_source_missing |
| 궁합풀이 | `missing-weddingluck` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_source_missing |
| 오늘의 사랑운 | `loveunse-love-today` | 원본 결과 소스·분기 누락 · 생성 차단 | 진단만 | result_branch_missing |
| 직장운 | `menu-im15` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 대인관계운 | `menu-im16` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 캐리어우먼 성공진단 | `menu-im19` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 캐리어우먼으로서의 명예 | `menu-im20` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 캐리어우먼의 일과 가정 | `menu-im21` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 재물모으는 법 | `menu-im22` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 재물손실막는법 | `menu-im23` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 재테크비법 | `menu-im24` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 피해야 할 상대 | `menu-im25` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 비지니스 성공비결 | `menu-im26` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 비즈니스극복운 | `menu-im27` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 사업운총평 | `menu-im28` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 사업합작운 | `menu-im29` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 이상형찿기 | `menu-im30` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 나의연인은어떤사람 | `menu-im31` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 당신과관계된이성들 | `menu-im32` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 미팅연애운세 | `menu-im33` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 사랑만들기 | `menu-im34` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 나의매력 | `menu-im35` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 나는이성에게어떤사람 | `menu-im36` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 이성의성격 | `menu-im37` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 성격분석 | `menu-im38` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 현실도분석 | `menu-im39` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 결혼조건분석 | `menu-im40` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 오늘의 무료데이트운세 | `menu-im41` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 첫 데이트 궁합 | `menu-im42` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 러브어드바이스 | `menu-im43` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 왕자의 오늘 데이트 운세 | `menu-im44` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 공주의 오늘 데이트 운세 | `menu-im45` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 왕자의 오늘 운세 | `menu-im46` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 공주의 오늘 운세 | `menu-im47` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 왕자의 오늘 사랑 운세 | `menu-im48` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 공주의 오늘 사랑 운세 | `menu-im49` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 우리애정스타일 | `menu-im50` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 명품애정운세 | `menu-im51` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 화해하기위한상대파악 | `menu-im52` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 이별후연인의마음 | `menu-im53` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 무료궁합 | `menu-im54` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 띠별궁합풀이 | `menu-im55` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 나와맞는이성궁합 | `menu-im56` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 찰떡궁합 | `menu-im57` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 숙명의궁합 | `menu-im58` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 서로를 성장시키는비결 | `menu-im59` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 결혼택일 | `menu-im60` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 웨딩 타임머신 | `menu-im61` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 사랑과결혼 | `menu-im62` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 두사람의 숙명진단 | `menu-im63` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 별자리운세 | `menu-im64` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 별자리속궁합 | `menu-im65` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 혈액형운세 | `menu-im66` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 혈액형궁합 | `menu-im67` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_target_missing |
| 꿈해몽 | `menu-im68` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 심리테스트 | `menu-im69` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 향수점 | `menu-im70` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 동물점 | `menu-im71` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 전생록 | `menu-im72` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 주역점 | `menu-im73` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 주민번호운세 | `menu-im74` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 휴대폰운세 | `menu-im75` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 주소지운세 | `menu-im76` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 차량번호운세 | `menu-im77` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 탄생일운세 | `menu-im78` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 탄생화운세 | `menu-im79` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 탄생석운세 | `menu-im80` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 경마운세 | `menu-im81` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 고스톱운세 | `menu-im82` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 게임운세 | `menu-im83` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 레저운세 | `menu-im84` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 엽기운세 | `menu-im85` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 적중궁합 | `menu-im86` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 적중취업운 | `menu-im87` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 적중궁합 | `menu-im88` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 미래내배우자얼굴 | `menu-im89` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |
| 미래내아이얼굴 | `menu-im90` | 원본 메뉴 연결·실행 계약 미확정 | 진단만 | menu_dispatch_missing |

## 2010~2011 도통비결 (1011yearluck)

- 상태: archived · 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요
- 원본: `old/unse/1011yearluck`
- 진단: GET /v1/asp-services/1011yearluck

### source_year_specific (confirmed)

원인: 각 디렉터리의 과거 연도/쌍연도 code, section 및 갑자 선택 분기를 사용하는 기존 연운 버전

영향: 현재 연도로 바꿔 적용했다고 보장할 수 없음

해결:

1. 과거 버전별 code/갑자/section 및 출력 항목을 먼저 이식한다.
2. 지원 연도 범위를 명시하고 임의로2026등에 확장하지 않는다.

필요 자료:

- 각 버전의 실제 지원연도/코드 확인

판단 근거:

- `old/unse/1011yearluck/main_end.asp:12` — If code = "" Then code = "2010"
- `old/unse/1011yearluck/main_end.asp:379` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY num"
- `old/unse/1011yearluck/main_end.asp:1055` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & "ORDER BY num"

### numeric_metadata_in_text_table (confirmed)

원인: yearfortune 조회는 문구뿐 아니라 star_cnt와 solar도 포함한다. 별점/기간 필드가 DB에 섞여 있으므로 테이블 전체를 '문구'로 취급할 수 없음. mark1~mark11 및 버전별 ORDER BY num/imsi_2009y도 확인 대상이다.

영향: AI가 원본 숫자 별점을 임의 생성해서는 안 됨

해결:

1. 원본 star_cnt/solar 등 실제 사용 필드를 조사해 판정 데이터만 제공하거나 해당 분류 규칙을 복원한다.

필요 자료:

- yearfortune의 star_cnt/solar/mark1~mark11/section/num 등 판정 열과 키 또는 동등한 판정 명세

판단 근거:

- `old/unse/1011yearluck/main_end.asp:379` — SELECT includes star_cnt,solar

검토 범위/실행 제약:

- 연도별/두해 비교판은 현행 API yearly와 별도 원본 버전이다. 파일명이 다르다는 이유만으로 동일 계산으로 병합하면 안 된다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/unse/1011yearluck/main_end.asp:30` — 원본 결제 서비스명 pkind
- `old/unse/1011yearluck/main_end.asp:12` — If code = "" Then code = "2010"
- `old/unse/1011yearluck/main_end.asp:379` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY num"
- `old/unse/1011yearluck/main_end.asp:1055` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & "ORDER BY num"

## 2011~2012 도통비결 (1112yearluck)

- 상태: archived · 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요
- 원본: `old/unse/1112yearluck`
- 진단: GET /v1/asp-services/1112yearluck

### source_year_specific (confirmed)

원인: 각 디렉터리의 과거 연도/쌍연도 code, section 및 갑자 선택 분기를 사용하는 기존 연운 버전

영향: 현재 연도로 바꿔 적용했다고 보장할 수 없음

해결:

1. 과거 버전별 code/갑자/section 및 출력 항목을 먼저 이식한다.
2. 지원 연도 범위를 명시하고 임의로2026등에 확장하지 않는다.

필요 자료:

- 각 버전의 실제 지원연도/코드 확인

판단 근거:

- `old/unse/1112yearluck/main_end.asp:12` — If code = "" Then code = "2011"
- `old/unse/1112yearluck/main_end.asp:379` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY num"
- `old/unse/1112yearluck/main_end.asp:1018` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & "ORDER BY num"

### numeric_metadata_in_text_table (confirmed)

원인: yearfortune 조회는 문구뿐 아니라 star_cnt와 solar도 포함한다. 별점/기간 필드가 DB에 섞여 있으므로 테이블 전체를 '문구'로 취급할 수 없음. mark1~mark11 및 버전별 ORDER BY num/imsi_2009y도 확인 대상이다.

영향: AI가 원본 숫자 별점을 임의 생성해서는 안 됨

해결:

1. 원본 star_cnt/solar 등 실제 사용 필드를 조사해 판정 데이터만 제공하거나 해당 분류 규칙을 복원한다.

필요 자료:

- yearfortune의 star_cnt/solar/mark1~mark11/section/num 등 판정 열과 키 또는 동등한 판정 명세

판단 근거:

- `old/unse/1112yearluck/main_end.asp:379` — SELECT includes star_cnt,solar

검토 범위/실행 제약:

- 연도별/두해 비교판은 현행 API yearly와 별도 원본 버전이다. 파일명이 다르다는 이유만으로 동일 계산으로 병합하면 안 된다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/unse/1112yearluck/main_end.asp:30` — 원본 결제 서비스명 pkind
- `old/unse/1112yearluck/main_end.asp:12` — If code = "" Then code = "2011"
- `old/unse/1112yearluck/main_end.asp:379` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY num"
- `old/unse/1112yearluck/main_end.asp:1018` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & "ORDER BY num"

## 2012~2013 도통비결 (1213yearluck)

- 상태: archived · 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요
- 원본: `old/unse/1213yearluck`
- 진단: GET /v1/asp-services/1213yearluck

### source_year_specific (confirmed)

원인: 각 디렉터리의 과거 연도/쌍연도 code, section 및 갑자 선택 분기를 사용하는 기존 연운 버전

영향: 현재 연도로 바꿔 적용했다고 보장할 수 없음

해결:

1. 과거 버전별 code/갑자/section 및 출력 항목을 먼저 이식한다.
2. 지원 연도 범위를 명시하고 임의로2026등에 확장하지 않는다.

필요 자료:

- 각 버전의 실제 지원연도/코드 확인

판단 근거:

- `old/unse/1213yearluck/main_end.asp:26` — If code = "" Then code = "2012"
- `old/unse/1213yearluck/main_end.asp:394` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY num"
- `old/unse/1213yearluck/main_end.asp:1034` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & "ORDER BY num"

### numeric_metadata_in_text_table (confirmed)

원인: yearfortune 조회는 문구뿐 아니라 star_cnt와 solar도 포함한다. 별점/기간 필드가 DB에 섞여 있으므로 테이블 전체를 '문구'로 취급할 수 없음. mark1~mark11 및 버전별 ORDER BY num/imsi_2009y도 확인 대상이다.

영향: AI가 원본 숫자 별점을 임의 생성해서는 안 됨

해결:

1. 원본 star_cnt/solar 등 실제 사용 필드를 조사해 판정 데이터만 제공하거나 해당 분류 규칙을 복원한다.

필요 자료:

- yearfortune의 star_cnt/solar/mark1~mark11/section/num 등 판정 열과 키 또는 동등한 판정 명세

판단 근거:

- `old/unse/1213yearluck/main_end.asp:394` — SELECT includes star_cnt,solar

검토 범위/실행 제약:

- 연도별/두해 비교판은 현행 API yearly와 별도 원본 버전이다. 파일명이 다르다는 이유만으로 동일 계산으로 병합하면 안 된다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/side_include/sub_unse.asp:59` — 도통비결 (12'13')
- `old/side_include/sub_unse_.asp:62` — 도통비결 (12'13')
- `old/unse/1213yearluck/main_end.asp:44` — 원본 결제 서비스명 pkind
- `old/unse/1213yearluck/main_end.asp:26` — If code = "" Then code = "2012"
- `old/unse/1213yearluck/main_end.asp:394` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY num"
- `old/unse/1213yearluck/main_end.asp:1034` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & "ORDER BY num"

## 2009 도통비결 (2009yearluck)

- 상태: archived · 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요
- 원본: `old/unse/2009yearluck`
- 진단: GET /v1/asp-services/2009yearluck

### source_year_specific (confirmed)

원인: 각 디렉터리의 과거 연도/쌍연도 code, section 및 갑자 선택 분기를 사용하는 기존 연운 버전

영향: 현재 연도로 바꿔 적용했다고 보장할 수 없음

해결:

1. 과거 버전별 code/갑자/section 및 출력 항목을 먼저 이식한다.
2. 지원 연도 범위를 명시하고 임의로2026등에 확장하지 않는다.

필요 자료:

- 각 버전의 실제 지원연도/코드 확인

판단 근거:

- `old/unse/2009yearluck/main_end.asp:604` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11, imsi_2009y" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY imsi_2009y"
- `old/unse/2009yearluck/main_end.asp:612` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY num"

### numeric_metadata_in_text_table (confirmed)

원인: yearfortune 조회는 문구뿐 아니라 star_cnt와 solar도 포함한다. 별점/기간 필드가 DB에 섞여 있으므로 테이블 전체를 '문구'로 취급할 수 없음. mark1~mark11 및 버전별 ORDER BY num/imsi_2009y도 확인 대상이다.

영향: AI가 원본 숫자 별점을 임의 생성해서는 안 됨

해결:

1. 원본 star_cnt/solar 등 실제 사용 필드를 조사해 판정 데이터만 제공하거나 해당 분류 규칙을 복원한다.

필요 자료:

- yearfortune의 star_cnt/solar/mark1~mark11/section/num 등 판정 열과 키 또는 동등한 판정 명세

판단 근거:

- `old/unse/2009yearluck/main_end.asp:604` — SELECT includes star_cnt,solar

검토 범위/실행 제약:

- 연도별/두해 비교판은 현행 API yearly와 별도 원본 버전이다. 파일명이 다르다는 이유만으로 동일 계산으로 병합하면 안 된다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/unse/2009yearluck/main.asp:1` — 소스 진입 파일; 한국어명은 소개/경로 의미에서 확인 필요
- `old/unse/2009yearluck/main_end.asp:604` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11, imsi_2009y" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY imsi_2009y"
- `old/unse/2009yearluck/main_end.asp:612` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY num"

## 2010 도통비결 (2010yearluck)

- 상태: archived · 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요
- 원본: `old/unse/2010yearluck`
- 진단: GET /v1/asp-services/2010yearluck

### source_year_specific (confirmed)

원인: 각 디렉터리의 과거 연도/쌍연도 code, section 및 갑자 선택 분기를 사용하는 기존 연운 버전

영향: 현재 연도로 바꿔 적용했다고 보장할 수 없음

해결:

1. 과거 버전별 code/갑자/section 및 출력 항목을 먼저 이식한다.
2. 지원 연도 범위를 명시하고 임의로2026등에 확장하지 않는다.

필요 자료:

- 각 버전의 실제 지원연도/코드 확인

판단 근거:

- `old/unse/2010yearluck/main_end.asp:598` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY num"

### numeric_metadata_in_text_table (confirmed)

원인: yearfortune 조회는 문구뿐 아니라 star_cnt와 solar도 포함한다. 별점/기간 필드가 DB에 섞여 있으므로 테이블 전체를 '문구'로 취급할 수 없음. mark1~mark11 및 버전별 ORDER BY num/imsi_2009y도 확인 대상이다.

영향: AI가 원본 숫자 별점을 임의 생성해서는 안 됨

해결:

1. 원본 star_cnt/solar 등 실제 사용 필드를 조사해 판정 데이터만 제공하거나 해당 분류 규칙을 복원한다.

필요 자료:

- yearfortune의 star_cnt/solar/mark1~mark11/section/num 등 판정 열과 키 또는 동등한 판정 명세

판단 근거:

- `old/unse/2010yearluck/main_end.asp:598` — SELECT includes star_cnt,solar

검토 범위/실행 제약:

- 연도별/두해 비교판은 현행 API yearly와 별도 원본 버전이다. 파일명이 다르다는 이유만으로 동일 계산으로 병합하면 안 된다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/side_include/sub_unse.asp:61` — 도통비결 (2010')
- `old/side_include/sub_unse_.asp:64` — 도통비결 (2010')
- `old/unse/2010yearluck/main_end.asp:598` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY num"

## 2011 도통비결 (2011yearluck)

- 상태: archived · 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요
- 원본: `old/unse/2011yearluck`
- 진단: GET /v1/asp-services/2011yearluck

### source_year_specific (confirmed)

원인: 각 디렉터리의 과거 연도/쌍연도 code, section 및 갑자 선택 분기를 사용하는 기존 연운 버전

영향: 현재 연도로 바꿔 적용했다고 보장할 수 없음

해결:

1. 과거 버전별 code/갑자/section 및 출력 항목을 먼저 이식한다.
2. 지원 연도 범위를 명시하고 임의로2026등에 확장하지 않는다.

필요 자료:

- 각 버전의 실제 지원연도/코드 확인

판단 근거:

- `old/unse/2011yearluck/main_end.asp:631` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY num"

### numeric_metadata_in_text_table (confirmed)

원인: yearfortune 조회는 문구뿐 아니라 star_cnt와 solar도 포함한다. 별점/기간 필드가 DB에 섞여 있으므로 테이블 전체를 '문구'로 취급할 수 없음. mark1~mark11 및 버전별 ORDER BY num/imsi_2009y도 확인 대상이다.

영향: AI가 원본 숫자 별점을 임의 생성해서는 안 됨

해결:

1. 원본 star_cnt/solar 등 실제 사용 필드를 조사해 판정 데이터만 제공하거나 해당 분류 규칙을 복원한다.

필요 자료:

- yearfortune의 star_cnt/solar/mark1~mark11/section/num 등 판정 열과 키 또는 동등한 판정 명세

판단 근거:

- `old/unse/2011yearluck/main_end.asp:631` — SELECT includes star_cnt,solar

검토 범위/실행 제약:

- 연도별/두해 비교판은 현행 API yearly와 별도 원본 버전이다. 파일명이 다르다는 이유만으로 동일 계산으로 병합하면 안 된다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/side_include/sub_unse.asp:60` — 도통비결 (2011')
- `old/side_include/sub_unse_.asp:63` — 도통비결 (2011')
- `old/unse/2011yearluck/main_end.asp:631` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY num"

## 2012 도통비결 (2012yearluck)

- 상태: archived · 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요
- 원본: `old/unse/2012yearluck`
- 진단: GET /v1/asp-services/2012yearluck

### source_year_specific (confirmed)

원인: 각 디렉터리의 과거 연도/쌍연도 code, section 및 갑자 선택 분기를 사용하는 기존 연운 버전

영향: 현재 연도로 바꿔 적용했다고 보장할 수 없음

해결:

1. 과거 버전별 code/갑자/section 및 출력 항목을 먼저 이식한다.
2. 지원 연도 범위를 명시하고 임의로2026등에 확장하지 않는다.

필요 자료:

- 각 버전의 실제 지원연도/코드 확인

판단 근거:

- `old/unse/2012yearluck/main_end.asp:655` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY num"

### numeric_metadata_in_text_table (confirmed)

원인: yearfortune 조회는 문구뿐 아니라 star_cnt와 solar도 포함한다. 별점/기간 필드가 DB에 섞여 있으므로 테이블 전체를 '문구'로 취급할 수 없음. mark1~mark11 및 버전별 ORDER BY num/imsi_2009y도 확인 대상이다.

영향: AI가 원본 숫자 별점을 임의 생성해서는 안 됨

해결:

1. 원본 star_cnt/solar 등 실제 사용 필드를 조사해 판정 데이터만 제공하거나 해당 분류 규칙을 복원한다.

필요 자료:

- yearfortune의 star_cnt/solar/mark1~mark11/section/num 등 판정 열과 키 또는 동등한 판정 명세

판단 근거:

- `old/unse/2012yearluck/main_end.asp:655` — SELECT includes star_cnt,solar

검토 범위/실행 제약:

- 연도별/두해 비교판은 현행 API yearly와 별도 원본 버전이다. 파일명이 다르다는 이유만으로 동일 계산으로 병합하면 안 된다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/side_include/sub_unse.asp:57` — 도통비결 (2012')
- `old/side_include/sub_unse_.asp:60` — 도통비결 (2012')
- `old/unse/2012yearluck/main_end.asp:655` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " ORDER BY num"

## 2013 도통비결 (2013yearluck)

- 상태: archived · 과거 연도판 · 별도 연도 계약/판정 자료 검토 필요
- 원본: `old/unse/2013yearluck`
- 진단: GET /v1/asp-services/2013yearluck

### source_year_specific (confirmed)

원인: 각 디렉터리의 과거 연도/쌍연도 code, section 및 갑자 선택 분기를 사용하는 기존 연운 버전

영향: 현재 연도로 바꿔 적용했다고 보장할 수 없음

해결:

1. 과거 버전별 code/갑자/section 및 출력 항목을 먼저 이식한다.
2. 지원 연도 범위를 명시하고 임의로2026등에 확장하지 않는다.

필요 자료:

- 각 버전의 실제 지원연도/코드 확인

판단 근거:

- `old/unse/2013yearluck/main_end.asp:12` — If code = "" Then code = "2013"
- `old/unse/2013yearluck/main_end.asp:111` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " order by num"

### numeric_metadata_in_text_table (confirmed)

원인: yearfortune 조회는 문구뿐 아니라 star_cnt와 solar도 포함한다. 별점/기간 필드가 DB에 섞여 있으므로 테이블 전체를 '문구'로 취급할 수 없음. mark1~mark11 및 버전별 ORDER BY num/imsi_2009y도 확인 대상이다.

영향: AI가 원본 숫자 별점을 임의 생성해서는 안 됨

해결:

1. 원본 star_cnt/solar 등 실제 사용 필드를 조사해 판정 데이터만 제공하거나 해당 분류 규칙을 복원한다.

필요 자료:

- yearfortune의 star_cnt/solar/mark1~mark11/section/num 등 판정 열과 키 또는 동등한 판정 명세

판단 근거:

- `old/unse/2013yearluck/main_end.asp:111` — SELECT includes star_cnt,solar

검토 범위/실행 제약:

- 연도별/두해 비교판은 현행 API yearly와 별도 원본 버전이다. 파일명이 다르다는 이유만으로 동일 계산으로 병합하면 안 된다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/side_include/sub_unse.asp:58` — 도통비결 (2013')
- `old/side_include/sub_unse_.asp:61` — 도통비결 (2013')
- `old/xmlpath/unse.xml:90` — unsekind txt
- `old/js/unseform.js:62` — CID actionurl dispatch
- `old/unse/2013yearluck/main_end.asp:12` — If code = "" Then code = "2013"
- `old/unse/2013yearluck/main_end.asp:111` — sql = "SELECT memno, section, sex, content, sol1, sol2, sol3, sol4, sol5, star_cnt, solar " sql = sql & ", mark1, mark2, mark3, mark4, mark5, mark6, mark7, mark8, mark9, mark10, mark11" sql = sql & " FROM yearfortune " sql = sql & " WHERE memno = " & memno sql = sql & " AND sex = '" & sex & "'" sql = sql & " AND year_pillar = '" & setPillar & "'" sql = sql & " order by num"

## 2014 도통비결 (2014yearluck)

- 상태: source_required · 조회키 진단 가능 · 원본 판정 자료 필요
- 원본: `old/unse/2014yearluck`
- 진단: GET /v1/asp-services/2014yearluck
- 계산/부분 계산: POST /v1/fortunes/yearly

### legacy_year_unsupported (confirmed)

원인: 이 원본 결과 코드의 연도별 간지 분기는 2001~2014년만 정의되어 있습니다. 2026년 올해는 지원하지 않습니다.

영향: 지원 범위 밖 POST는 422 legacy_year_unsupported입니다. AI가 올해의 판정을 만들도록 요청하지 않습니다.

해결:

1. 올해용 상용 판정 명세/분기와 실제 대조 결과를 확보합니다.
2. 그 명세에 따라 연간 계산을 확장하고 경계 테스트를 통과시킵니다.

필요 자료:

- 2026년 이후 연간 판정 규칙·연도별 출력 항목 및 원본 샘플

판단 근거:

- `old/xmlpath/unse.xml:99` — unsekind txt

### yearfortune_decision_data_missing (confirmed)

원인: yearfortune에는 본문 외 section/star_cnt/solar/mark1~mark11/num 및 부적 선택을 정하는 값이 있으나 현재 제공된 판정 데이터가 없습니다.

영향: 허용 연도에서도 ready_for_ai=false이며 include_ai=true는 503입니다.

해결:

1. 원본 선택키(memno/sex/year_pillar)별 비문구 열과 행 순서/부적 선택 의미를 확보합니다.
2. 해당 데이터나 동등하게 검증한 규칙을 연결한 후 AI 문장화를 허용합니다.

필요 자료:

- yearfortune의 키·section·star_cnt·solar·mark1~mark11·num 및 sol1~sol5 선택 구조 (문구 본문은 AI로 대체 가능)

판단 근거:

- `old/xmlpath/unse.xml:99` — unsekind txt

검토 범위/실행 제약:

- 연도별/두해 비교판은 현행 API yearly와 별도 원본 버전이다. 파일명이 다르다는 이유만으로 동일 계산으로 병합하면 안 된다.

원본 근거:

- `old/xmlpath/unse.xml:99` — unsekind txt
- `old/js/unseform.js:67` — CID actionurl dispatch

## 운세 결과 메일·파일 다운로드 (fso)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse/FSO`
- 진단: GET /v1/asp-services/fso

### auxiliary_delivery (confirmed)

원인: 결과 다운로드/메일전송 도구이며 독립 운세 판정이 아니다. 외부 print.asp 호출·SMTP 컴포넌트가 포함된다.

영향: 운세목록에 보통서비스처럼 노출하면 혼동됨

해결:

1. 카탈로그에서 보조기능으로 분류하거나 결과생성API 범위에서 제외한다.
2. 파일/메일기능이필요할때 별도요청으로 다룬다.

판단 근거:

- `old/unse/FSO/download.asp:5` — getUrl fetch helper
- `old/unse/FSO/download.asp:35` — SmtpExpress.SendMail helper

검토 범위/실행 제약:

- 운세 판정 서비스가 아닌 메일/다운로드 지원 도구.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/unse/FSO/download.asp:1` — 소스 진입 파일; 한국어명은 소개/경로 의미에서 확인 필요

## 인맥 구축·조직 관리법 (humanorganizationmanagement)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/HumanOrganizationManagement`
- 진단: GET /v1/asp-services/humanorganizationmanagement
- 계산/부분 계산: POST /v1/un/humanorganizationmanagement

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_template의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, unverified_saju_array_profile. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: SajuManseryuk의 DLL 실제 실행 결과와 동일성은 미검증입니다.
- 실행 제약: 허용된 기본 만세력 대체 범위에서 dotong 사주를 時/日/月/年 1-based KAN/SI에 대응합니다.
- 실행 제약: 藏干·통변성·12운성은 _SajuManseryuk.asp의 정적 표와 날짜 분기를 그대로 적용합니다.
- 실행 제약: 미사용 대운·세운 배열과 tbAisyo 준비 조회는 생성하지 않습니다.
- CR-012 / T-024: app.ported_template의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/HumanOrganizationManagement/main_end.asp:15` — 원본 출력 소항목
- `old/unse/HumanOrganizationManagement/main_end.asp:34` — 원본 결제 서비스명 pkind
- `old/unse/HumanOrganizationManagement/main_end.asp:14` — L_item_code_Text = "saju_bizhostility_1|saju_bizhostility_2|saju_bizhostility_3|saju_bizhostility_4"
- `old/unse/HumanOrganizationManagement/main_end.asp:1424` — Dim MyAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(Birthday_Sun,12) & "') ORDER BY fdDate DESC" '				adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/HumanOrganizationManagement/main_end.asp:1443` — Dim OtherAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(OtherBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/HumanOrganizationManagement/main_end.asp:1462` — Dim ThirdAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(ThirdBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/HumanOrganizationManagement/main_end.asp:14` — item codes saju_bizhostility
- `function/b_include/_SajuManseryuk.asp:93` — SajuManseryuk uses DllManse.SajuGanJi

## 상사와의 관계 (mastermanrelations)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/MasterManRelations`
- 진단: GET /v1/asp-services/mastermanrelations
- 계산/부분 계산: POST /v1/un/mastermanrelations

### planet_fdastro_classification_missing (confirmed)

원인: astro_business_1: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다. astro_business_2: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다. astro_business_3: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- tbSavianAstro_Planet_*의 fdDate/fdAstro 원본 행성 분류

판단 근거:

- `old/unse/MasterManRelations/main_end.asp:15` — 원본 출력 소항목
- `old/unse/MasterManRelations/main_end.asp:33` — 원본 결제 서비스명 pkind
- `old/unse/MasterManRelations/main_end.asp:14` — L_item_code_Text = "saju_bizmanpower_1|saju_bizmanpower_2|saju_bizmanpower_3|astro_business_1|astro_business_2|astro_business_3"
- `old/unse/MasterManRelations/main_end.asp:251` — Dim MyAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(Birthday_Sun,12) & "') ORDER BY fdDate DESC" '				adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/MasterManRelations/main_end.asp:270` — Dim OtherAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(OtherBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/MasterManRelations/main_end.asp:289` — Dim ThirdAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(ThirdBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/MasterManRelations/main_end.asp:251` — active astro item code path queries planet series
- `function/b_include/lib_astrology.asp:180` — planet position query used to compose content key

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- CR-012 / T-024: app.ported_template의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, missing_planet_position_data. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_template의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/MasterManRelations/main_end.asp:15` — 원본 출력 소항목
- `old/unse/MasterManRelations/main_end.asp:33` — 원본 결제 서비스명 pkind
- `old/unse/MasterManRelations/main_end.asp:14` — L_item_code_Text = "saju_bizmanpower_1|saju_bizmanpower_2|saju_bizmanpower_3|astro_business_1|astro_business_2|astro_business_3"
- `old/unse/MasterManRelations/main_end.asp:251` — Dim MyAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(Birthday_Sun,12) & "') ORDER BY fdDate DESC" '				adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/MasterManRelations/main_end.asp:270` — Dim OtherAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(OtherBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/MasterManRelations/main_end.asp:289` — Dim ThirdAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(ThirdBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/MasterManRelations/main_end.asp:251` — active astro item code path queries planet series
- `function/b_include/lib_astrology.asp:180` — planet position query used to compose content key

## 사회 속의 나의 명예 (socialmyhonor)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/SocialMyHonor`
- 진단: GET /v1/asp-services/socialmyhonor
- 계산/부분 계산: POST /v1/un/socialmyhonor

### planet_fdastro_classification_missing (confirmed)

원인: astro_aspect_society_4: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다. astro_aspect_society_3: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다. astro_aspect_society_2: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다. astro_aspect_society_1: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- tbSavianAstro_Planet_*의 fdDate/fdAstro 원본 행성 분류

판단 근거:

- `old/unse/SocialMyHonor/main_end.asp:14` — 원본 출력 소항목
- `old/unse/SocialMyHonor/main_end.asp:33` — 원본 결제 서비스명 pkind
- `old/unse/SocialMyHonor/main_end.asp:13` — L_item_code_Text = "astro_aspect_society_4|astro_aspect_society_3|astro_aspect_society_2|astro_aspect_society_1"
- `old/unse/SocialMyHonor/main_end.asp:240` — Dim MyAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(Birthday_Sun,12) & "') ORDER BY fdDate DESC" '				adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/SocialMyHonor/main_end.asp:259` — Dim OtherAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(OtherBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/SocialMyHonor/main_end.asp:278` — Dim ThirdAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(ThirdBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/SocialMyHonor/main_end.asp:240` — active astro item code path queries planet series
- `function/b_include/lib_astrology.asp:180` — planet position query used to compose content key

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- CR-012 / T-024: app.ported_template의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, missing_planet_position_data. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_template의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/SocialMyHonor/main_end.asp:14` — 원본 출력 소항목
- `old/unse/SocialMyHonor/main_end.asp:33` — 원본 결제 서비스명 pkind
- `old/unse/SocialMyHonor/main_end.asp:13` — L_item_code_Text = "astro_aspect_society_4|astro_aspect_society_3|astro_aspect_society_2|astro_aspect_society_1"
- `old/unse/SocialMyHonor/main_end.asp:240` — Dim MyAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(Birthday_Sun,12) & "') ORDER BY fdDate DESC" '				adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/SocialMyHonor/main_end.asp:259` — Dim OtherAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(OtherBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/SocialMyHonor/main_end.asp:278` — Dim ThirdAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(ThirdBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/SocialMyHonor/main_end.asp:240` — active astro item code path queries planet series
- `function/b_include/lib_astrology.asp:180` — planet position query used to compose content key

## 성인운세 모음 (adultluck)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse/adultluck`
- 진단: GET /v1/asp-services/adultluck

### collection_needs_subservice_audit (confirmed)

원인: 성인운세 입구는 인증쿠키 분기 후8개 하위디렉터리로 연결한다. 항목별로 NHCP DLL/서양점성DB/사주배열/주기공식 의존성이 다름.

영향: adultluck을 단일ready서비스로 취급할 수 없음

해결:

1. 하위8개를 각각 명칭·입력·소스·필수의존성으로 분리한다.
2. 원본성인확인 흐름의 역할을 새API접근정책과 분리해 명시한다.

판단 근거:

- `old/unse/adultluck/main.asp:4` — adultyn cookie gating

검토 범위/실행 제약:

- 개별 운세가 아닌 메뉴/여러 결과 엔진의 컨테이너. 하위 서비스는 별도 목록으로 센다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/unse/adultluck/main.asp:1` — 소스 진입 파일; 한국어명은 소개/경로 의미에서 확인 필요

## 나의 운세처방 (adviceluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/adviceluck`
- 진단: GET /v1/asp-services/adviceluck
- 계산/부분 계산: POST /v1/un/adviceluck

### major_luck_display_boundary_missing (confirmed)

원인: 원본 manse.disp_day 표시값이 제공 DB에 없어 월간 표시기간의 완전 동일성은 미확정입니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- 원본 manse.disp_day 표시기간의 정의와 대조 결과

판단 근거:

- `old/side_include/sub_unse.asp:152` — 나의 운세처방
- `old/side_include/sub_unse_.asp:156` — 나의 운세처방
- `old/xmlpath/unse.xml:33` — unsekind txt
- `old/js/unseform.js:27` — CID actionurl dispatch
- `old/unse/adviceluck/main_end.asp:154` —  Dim sql_main,rs_manse,vyp,mpi,vmp,div_name,disp_day sql_main = "Select lyear,year_pillar,month_pillar,div_name,disp_day from manse where syear = " & vyear & " and smonth = " & vmonth & " and sday = " & vday  If QueryCheck(sql_main) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/adviceluck/main_end.asp:220` —  Dim sql, rs, todaycontent sql = "select male,female from fortune_basic where yukgap='" & vmp & "' and daygan = '" & ilgan & "' " 'esponse.write sql  If QueryCheck(sql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5"

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:152` — 나의 운세처방
- `old/side_include/sub_unse_.asp:156` — 나의 운세처방
- `old/xmlpath/unse.xml:33` — unsekind txt
- `old/js/unseform.js:27` — CID actionurl dispatch
- `old/unse/adviceluck/main_end.asp:154` —  Dim sql_main,rs_manse,vyp,mpi,vmp,div_name,disp_day sql_main = "Select lyear,year_pillar,month_pillar,div_name,disp_day from manse where syear = " & vyear & " and smonth = " & vmonth & " and sday = " & vday  If QueryCheck(sql_main) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/adviceluck/main_end.asp:220` —  Dim sql, rs, todaycontent sql = "select male,female from fortune_basic where yukgap='" & vmp & "' and daygan = '" & ilgan & "' " 'esponse.write sql  If QueryCheck(sql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5"

## 연인 심리분석 (analysisluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/analysisluck`
- 진단: GET /v1/asp-services/analysisluck
- 계산/부분 계산: POST /v1/un/analysisluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/analysisluck/main_end.asp:18` — 원본 결제 서비스명 pkind
- `old/unse/analysisluck/main_end.asp:1358` — Dim lmyYear, lmyMonth, lmyDay, lSQL, lRs lSQL = "SELECT syear, smonth, sday " lSQL = lSQL & "FROM manse " lSQL = lSQL & "WHERE lyear = " & myYear & " and lmonth = " & myMonth & " and lday = " & myDay If myLunmonth = "윤" Then lSQL = lSQL & " AND lunmonth = 1" Else

## 동물점 (animalluck)

- 상태: source_required · 원본 DLL 판정 소스·대조 검증 필요
- 원본: `old/unse/animalluck`
- 진단: GET /v1/asp-services/animalluck

### opaque_com_rule (confirmed)

원인: 최종 결과가 NHCP5.NHUnse.getNHResult('013')의 unseResult에서 나오며 내부 판정은 ASP에 없음.

영향: 새 점수/AI 추정으로 대체하면 기존 상용 판정 보존 불가

해결:

1. DLL의 내부 판정 소스/명세 또는 원본 Windows 검증 환경을 확보한다.
2. 서비스 입력→결과 분류/결과 배열의 회귀 샘플로 Python 이식을 검증한다.
3. 판정이 미확정인 동안 AI 문구 생성을 허용하지 않는다.

필요 자료:

- NHCP5.NHUnse 구현 소스 또는 판정 명세, 대조 실행 가능한 Windows 환경/DLL

판단 근거:

- `old/unse/animalluck/main_end.asp:131` — getNHResult call
- `function/eqFunctions.asp:2` — setIsSolar/setIsLeap/setGender original input conversion

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/side_include/sub_unse.asp:88` — 동물점
- `old/side_include/sub_unse_.asp:92` — 동물점
- `old/unse/animalluck/main_end.asp:131` — tmpRlt = objNH.getNHResult(tmpCode)

## 나의 원초적 본능 (basicluck)

- 상태: source_required · 원본 DLL 판정 소스·대조 검증 필요
- 원본: `old/unse/basicluck`
- 진단: GET /v1/asp-services/basicluck

### opaque_com_rule (confirmed)

원인: 최종 결과가 NHCP5.NHUnse.getNHResult(tmpCode)의 unseResult에서 나오며 내부 판정은 ASP에 없음.

영향: 새 점수/AI 추정으로 대체하면 기존 상용 판정 보존 불가

해결:

1. DLL의 내부 판정 소스/명세 또는 원본 Windows 검증 환경을 확보한다.
2. 서비스 입력→결과 분류/결과 배열의 회귀 샘플로 Python 이식을 검증한다.
3. 판정이 미확정인 동안 AI 문구 생성을 허용하지 않는다.

필요 자료:

- NHCP5.NHUnse 구현 소스 또는 판정 명세, 대조 실행 가능한 Windows 환경/DLL

판단 근거:

- `old/unse/basicluck/main_end.asp:1401` — getNHResult call
- `function/eqFunctions.asp:2` — setIsSolar/setIsLeap/setGender original input conversion

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/side_include/sub_unse.asp:66` — 나의 원초적 본능
- `old/side_include/sub_unse_.asp:69` — 나의 원초적 본능
- `old/xmlpath/unse.xml:66` — unsekind txt
- `old/js/unseform.js:47` — CID actionurl dispatch
- `old/unse/basicluck/main_end.asp:1401` — tmpRlt = objNH.getNHResult(tmpCode)

## 바이오리듬 (bioluck)

- 상태: ready · 계산·선택키 이식 완료 · AI 연결 설정 필요
- 원본: `old/unse/bioluck`
- 진단: GET /v1/asp-services/bioluck
- 계산/부분 계산: POST /v1/fortunes/biorhythm

검토 범위/실행 제약:


원본 근거:

- `old/side_include/sub_unse.asp:95` — 바이오리듬
- `old/side_include/sub_unse_.asp:99` — 바이오리듬
- `old/xmlpath/unse.xml:10` — unsekind txt
- `old/js/unseform.js:12` — CID actionurl dispatch

## 탄생일운세 (birthluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/birthluck`
- 진단: GET /v1/asp-services/birthluck
- 계산/부분 계산: POST /v1/un/birthluck

### historical_birth_reference_data_missing (confirmed)

원인: wiki_story·wiki_person의 실제 사건·인물 자료가 없어 원본 전체 페이지는 미완성입니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- wiki_story의 e_name/e_contents/e_date 및 wiki_person의 e_year/e_name/e_contents 사실 자료

판단 근거:

- `old/side_include/sub_unse.asp:96` — 탄생일운세
- `old/side_include/sub_unse_.asp:100` — 탄생일운세
- `old/unse/birthluck/main_end.asp:119` — Dim lmyYear, lmyMonth, lmyDay, lSQL, lRs lSQL = "SELECT syear, smonth, sday " lSQL = lSQL & "FROM manse " lSQL = lSQL & "WHERE lyear = " & myYear & " and lmonth = " & myMonth & " and lday = " & myDay If myLunmonth = "윤" Then lSQL = lSQL & " AND lunmonth = 1" Else
- `old/unse/birthluck/main_end.asp:134` — Else lSQL = "SELECT lyear, lmonth, lday " lSQL = lSQL & "FROM manse " lSQL = lSQL & "WHERE syear = " & myYear & " and smonth = " & myMonth & " and sday = " & myDay Set lRs = Dbcon.Execute(lSQL) lmyYear = lRs("lyear") lmyMonth = lRs("lmonth")
- `old/unse/birthluck/main_end.asp:159` —  SQL = "SELECT unse " SQL = SQL & "FROM birthluck WHERE month = " & realMonth & " AND day = " & realDay Set Rs = Dbcon.Execute(SQL)  If Rs.EOF Or Rs.BOF Then Response.Redirect "/ScriptError.asp?ErrorNum=2"

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:96` — 탄생일운세
- `old/side_include/sub_unse_.asp:100` — 탄생일운세
- `old/unse/birthluck/main_end.asp:119` — Dim lmyYear, lmyMonth, lmyDay, lSQL, lRs lSQL = "SELECT syear, smonth, sday " lSQL = lSQL & "FROM manse " lSQL = lSQL & "WHERE lyear = " & myYear & " and lmonth = " & myMonth & " and lday = " & myDay If myLunmonth = "윤" Then lSQL = lSQL & " AND lunmonth = 1" Else
- `old/unse/birthluck/main_end.asp:134` — Else lSQL = "SELECT lyear, lmonth, lday " lSQL = lSQL & "FROM manse " lSQL = lSQL & "WHERE syear = " & myYear & " and smonth = " & myMonth & " and sday = " & myDay Set lRs = Dbcon.Execute(lSQL) lmyYear = lRs("lyear") lmyMonth = lRs("lmonth")
- `old/unse/birthluck/main_end.asp:159` —  SQL = "SELECT unse " SQL = SQL & "FROM birthluck WHERE month = " & realMonth & " AND day = " & realDay Set Rs = Dbcon.Execute(SQL)  If Rs.EOF Or Rs.BOF Then Response.Redirect "/ScriptError.asp?ErrorNum=2"

## 혈액형운세 (bloodluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/bloodluck`
- 진단: GET /v1/asp-services/bloodluck
- 계산/부분 계산: POST /v1/un/bloodluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet, additional_input_required. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:94` — 혈액형운세
- `old/side_include/sub_unse_.asp:98` — 혈액형운세
- `old/unse/bloodluck/main_end.asp:56` —   sSql = "select data1,data2,data3,data4,data5,data6,data7 from blood " sSql = sSql & "where gender='" & gender & "' and blood='" & blood & "'"  If QueryCheck(ssql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5"
- `old/unse/bloodluck/main_end.asp:56` — blood WHERE gender,blood; data1..7

## 비즈니스 성공운 (businessluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/businessluck`
- 진단: GET /v1/asp-services/businessluck
- 계산/부분 계산: POST /v1/un/businessluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:70` — 비즈니스 성공운
- `old/side_include/sub_unse_.asp:73` — 비즈니스 성공운
- `old/unse/businessluck/main_end.asp:31` — 원본 결제 서비스명 pkind
- `old/unse/businessluck/main_end.asp:1388` — Dim lmyYear, lmyMonth, lmyDay, lSQL, lRs lSQL = "SELECT syear, smonth, sday " lSQL = lSQL & "FROM manse " lSQL = lSQL & "WHERE lyear = " & myYear & " and lmonth = " & myMonth & " and lday = " & myDay If myLunmonth = "윤" Then lSQL = lSQL & " AND lunmonth = 1" Else

## 월운세 달력 (calendarluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/calendarluck`
- 진단: GET /v1/asp-services/calendarluck
- 계산/부분 계산: POST /v1/un/calendarluck

### missing_rule_rows (confirmed)

원인: tbCalUnse의 실제11행과 do_num/성별 선택 근거가 미확보입니다. 조사용 행을 입력해도 실제 DB 검증은 완료되지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 기본 일진/음력은 제공된 tb_manse 조회를 사용한다.
2. tbCalUnse 규칙행 또는 원본 코드상 대응표를 확보해11항목 비교를 이식한다.

필요 자료:

- tbCalUnse do_num/sex/unsecode별 change/chungan/jiji

판단 근거:

- `old/side_include/sub_unse.asp:39` — " else response.write " " end if %>월운세 달력
- `old/unse/calendarluck/main_end.asp:138` — '### 해당월의 각일주 ### Dim i, fixGanji(31), fixLmonth(31), fixLday(31) sSql = "select day_pillar,lmonth,lday from manse where syear = " & dyear & " and smonth = " & dmonth  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/calendarluck/main_end.asp:157` — '### 항목의 일진 비교 ### Dim unsetype(11), change(11), goodgan(11),  jiji(11) sSql = "select unsetype,change, chungan, jiji from tbCalUnse " sSql = sSql & " where do_num = " & Left(id,1) sSql = sSql & " and sex = '" & gender & "'" sSql = sSql & " order by unsecode" 
- `old/unse/calendarluck/main_end.asp:157` — select unsetype,change,chungan,jiji; per-row arrays
- `old/unse/calendarluck/main_end.asp:138` — month day_pillar,lmonth,lday

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- CR-012 / T-024: app.ported_data_rules의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:39` — " else response.write " " end if %>월운세 달력
- `old/unse/calendarluck/main_end.asp:138` — '### 해당월의 각일주 ### Dim i, fixGanji(31), fixLmonth(31), fixLday(31) sSql = "select day_pillar,lmonth,lday from manse where syear = " & dyear & " and smonth = " & dmonth  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/calendarluck/main_end.asp:157` — '### 항목의 일진 비교 ### Dim unsetype(11), change(11), goodgan(11),  jiji(11) sSql = "select unsetype,change, chungan, jiji from tbCalUnse " sSql = sSql & " where do_num = " & Left(id,1) sSql = sSql & " and sex = '" & gender & "'" sSql = sSql & " order by unsecode" 
- `old/unse/calendarluck/main_end.asp:157` — select unsetype,change,chungan,jiji; per-row arrays
- `old/unse/calendarluck/main_end.asp:138` — month day_pillar,lmonth,lday

## 차량번호운세 (carluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/carluck`
- 진단: GET /v1/asp-services/carluck
- 계산/부분 계산: POST /v1/un/carluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:113` — 차량번호운세
- `old/side_include/sub_unse_.asp:117` — 차량번호운세
- `old/unse/carluck/main_end.asp:126` — Dim desc1,desc2,desc3,number_unse  sSql = "select desc1,desc2,desc3 from tbSaju_otherunse where unse='carnum' and sipkyuk_code='" & sipkyuk_code & "'"  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End

## 나에게 맞는 직업 (carrerluck)

- 상태: source_required · 조회키 진단 가능 · 원본 판정 자료 필요
- 원본: `old/unse/carrerluck`
- 진단: GET /v1/asp-services/carrerluck
- 계산/부분 계산: POST /v1/fortunes/career

### nhcp5_calculation_missing (confirmed)

원인: NHCP5.NHUnse.getNHResult('002', A1~E3)가 계산을 수행하며 DLL 내부 판정이 소스에 없습니다.

영향: 카테고리 A~F와 호출키는 진단할 수 있으나 최종 결과/AI 생성은 503으로 차단합니다.

해결:

1. DLL의 구현 소스·판정 명세 또는 원본 실행 환경에서 분류 결과를 확보합니다.
2. 15항목의 입력→분류/출력 계약을 이식하고 대조 검증합니다.

필요 자료:

- NHCP5.NHUnse DLL 또는 구현 소스/판정 명세와 대조 실행 환경

판단 근거:

- `old/side_include/sub_unse.asp:69` — 나에게 맞는 직업

검토 범위/실행 제약:


원본 근거:

- `old/side_include/sub_unse.asp:69` — 나에게 맞는 직업
- `old/side_include/sub_unse_.asp:72` — 나에게 맞는 직업
- `old/unse/carrerluck/main_end.asp:34` — 원본 결제 서비스명 pkind
- `old/xmlpath/unse.xml:108` — unsekind txt
- `old/js/unseform.js:72` — CID actionurl dispatch

## 주역점 (coinluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/coinluck`
- 진단: GET /v1/asp-services/coinluck
- 계산/부분 계산: POST /v1/un/coinluck

### hexagram_name_mapping_missing (confirmed)

원인: 원본 6효 코드에 대응하는 64괘 이름 매핑이 DB에 있어 임의 괘명을 생성하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- tbsaju_juyuk의 6효 코드별 code_name 괘명 매핑

판단 근거:

- `old/side_include/sub_unse.asp:92` — 주역점
- `old/side_include/sub_unse_.asp:96` — 주역점
- `old/unse/coinluck/main_end.asp:45` —  Dim sql, RS, title, total, content, code sql = "select code,code_name,total," & bt & " from tbsaju_juyuk where code = '" & yut & "'"   If QueryCheck(sql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5"
- `old/unse/coinluck/main_end.asp:17` — yut0..5 concatenation
- `old/unse/coinluck/main_end.asp:45` — query code,code_name,total,dynamic bt

검토 범위/실행 제약:

- main1/main_end1은 주역점의 입력·표시 변형이며 별도 명칭의 서비스가 아니다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet, additional_input_required. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:92` — 주역점
- `old/side_include/sub_unse_.asp:96` — 주역점
- `old/unse/coinluck/main_end.asp:45` —  Dim sql, RS, title, total, content, code sql = "select code,code_name,total," & bt & " from tbsaju_juyuk where code = '" & yut & "'"   If QueryCheck(sql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5"
- `old/unse/coinluck/main_end.asp:17` — yut0..5 concatenation
- `old/unse/coinluck/main_end.asp:45` — query code,code_name,total,dynamic bt

## 나와 맞는 이성 궁합 (correctyouluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/correctyouluck`
- 진단: GET /v1/asp-services/correctyouluck
- 계산/부분 계산: POST /v1/un/correctyouluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/correctyouluck/main_end.asp:15` — 원본 출력 소항목
- `old/unse/correctyouluck/main_end.asp:33` — 원본 결제 서비스명 pkind
- `old/unse/correctyouluck/main_end.asp:14` — L_item_code_Text = "cabala_harmony"
- `old/unse/correctyouluck/main_end.asp:224` — Dim MyAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(Birthday_Sun,12) & "') ORDER BY fdDate DESC" '				adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/correctyouluck/main_end.asp:243` — Dim OtherAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(OtherBirthday_Sun,12) & "') ORDER BY fdDate DESC" '				adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/correctyouluck/main_end.asp:262` — Dim ThirdAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(ThirdBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 

## 상담용 오기 (counselluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/counselluck`
- 진단: GET /v1/asp-services/counselluck
- 계산/부분 계산: POST /v1/un/counselluck

### major_luck_num_disp_day_missing (confirmed)

원인: 상담오기 원본에는 남녀 대운 include가 함께 출력됩니다. 이 계산에 쓰는 manse.num·disp_day가 제공 tb_manse에 없어 대운 시작나이·구간은 확정하지 않습니다. 오행 그래프·간지·육신·운성의 부분 계산은 제공합니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- 원본 manse.num의 연속 일수 정의와 disp_day 대운 표시기간
- 대운 시작 나이·구간의 원본 대조 결과

판단 근거:

- `old/unse/counselluck/main.asp:79` — 태어난 사주로 분석한 상담용 오기
- `old/unse/counselluck/main_end.asp:77` — male CalcSaju
- `old/unse/counselluck/main_end.asp:340` — female CalcSaju
- `old/unse/counselluck/main_end.asp:189` — male ki-kind branches

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_pair_saju_formulas. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/counselluck/main.asp:79` — 태어난 사주로 분석한 상담용 오기
- `old/unse/counselluck/main_end.asp:77` — male CalcSaju
- `old/unse/counselluck/main_end.asp:340` — female CalcSaju
- `old/unse/counselluck/main_end.asp:189` — male ki-kind branches

## 띠별궁합풀이 (ddiluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/ddiluck`
- 진단: GET /v1/asp-services/ddiluck
- 계산/부분 계산: POST /v1/un/ddiluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_inline_zodiac. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_love.asp:41` — 띠별궁합풀이
- `old/unse/free_main.asp:115` — 
- `old/unse/ddiluck/main_end.asp:82` — CalcSaju YearJi
- `old/unse/ddiluck/main_end.asp:89` — Di1..12/Di1a..12a source strings
- `old/unse/ddiluck/main_end.asp:160` — Select Case YearJi dispatch

## 숙명의 궁합 (fatewedluck)

- 상태: source_required · 조회키 진단 가능 · 원본 판정 자료 필요
- 원본: `old/unse/fatewedluck`
- 진단: GET /v1/asp-services/fatewedluck
- 계산/부분 계산: POST /v1/fortunes/compatibility

### aisyo_classification_missing (confirmed)

원인: 숙명의 궁합은 두 양력 생일을 tbAisyo.aisyo의 27숙 분류로 바꾼 후 방향성 표와 문구 선택키를 적용합니다. 현재 Python 프로젝트에는 해당 날짜 분류 자료를 확보·연결하지 않았습니다.

영향: 후속 표/선택 공식이 있어도 최종 궁합 분류를 확정할 수 없어 AI 생성은 503입니다.

해결:

1. solar birth date→aisyo 원본 분류표 또는 동등한 분류 규칙을 확보합니다.
2. 원본 날짜 범위·분류값을 검증한 뒤 기존 방향성 궁합 표와 연결합니다.

필요 자료:

- tbAisyo의 날짜 키→aisyo 열 또는 원본 27숙 날짜 분류 규칙/샘플

판단 근거:

- `old/unse/fatewedluck/main_end.asp:15` — 원본 출력 소항목

검토 범위/실행 제약:


원본 근거:

- `old/unse/fatewedluck/main_end.asp:15` — 원본 출력 소항목
- `old/unse/fatewedluck/main_end.asp:32` — 원본 결제 서비스명 pkind

## 내 몸의 기 (fivegiluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/fivegiluck`
- 진단: GET /v1/asp-services/fivegiluck
- 계산/부분 계산: POST /v1/un/fivegiluck

### major_luck_num_disp_day_missing (confirmed)

원인: 원본 manse.num의 연속 일수 계약과 disp_day 시작·종료 값이 제공 tb_manse에 없습니다. 대운 시작 나이와10개 대운구간을 임의 생성하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- 원본 manse.num의 연속 일수 정의와 disp_day 대운 표시기간
- 대운 시작 나이·10개 구간의 원본 대조 결과

판단 근거:

- `old/side_include/sub_unse.asp:154` — 내 몸의 기
- `old/side_include/sub_unse_.asp:158` — 내 몸의 기
- `old/unse/fivegiluck/main_end.asp:270` — Dim dateDef,LargeFlow,Direction  sSql = "select num, month_pillar, disp_day from manse " if myLunsol="음" then sSql = sSql & " where syear = " &  iyear &  " and smonth = " & imonth & " and sday = " & iday else sSql = sSql & " where syear = " &  myYear &  " and smonth = " & myMonth & " and sday = " & myDay
- `old/unse/fivegiluck/main_end.asp:293` — Rs.close  sSql = "select num from manse " sSql = sSql & " where syear = " & left(disp_day,4) sSql = sSql & " and smonth = " & mid(disp_day,5,2) sSql = sSql & " and sday = " & mid(disp_day,7,2) 
- `old/unse/fivegiluck/main_end.asp:327` — Rs.close  sSql = "select num from manse " sSql = sSql & " where syear = " & left(disp_day,4) sSql = sSql & " and smonth = " & mid(disp_day,5,2) sSql = sSql & " and sday = " & mid(disp_day,7,2) 
- `old/unse/fivegiluck/main_end.asp:270` — num,month_pillar,disp_day
- `old/unse/fivegiluck/main_end.asp:293` — term-boundary num lookup

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_custom_calendar_semantics. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:154` — 내 몸의 기
- `old/side_include/sub_unse_.asp:158` — 내 몸의 기
- `old/unse/fivegiluck/main_end.asp:270` — Dim dateDef,LargeFlow,Direction  sSql = "select num, month_pillar, disp_day from manse " if myLunsol="음" then sSql = sSql & " where syear = " &  iyear &  " and smonth = " & imonth & " and sday = " & iday else sSql = sSql & " where syear = " &  myYear &  " and smonth = " & myMonth & " and sday = " & myDay
- `old/unse/fivegiluck/main_end.asp:293` — Rs.close  sSql = "select num from manse " sSql = sSql & " where syear = " & left(disp_day,4) sSql = sSql & " and smonth = " & mid(disp_day,5,2) sSql = sSql & " and sday = " & mid(disp_day,7,2) 
- `old/unse/fivegiluck/main_end.asp:327` — Rs.close  sSql = "select num from manse " sSql = sSql & " where syear = " & left(disp_day,4) sSql = sSql & " and smonth = " & mid(disp_day,5,2) sSql = sSql & " and sday = " & mid(disp_day,7,2) 
- `old/unse/fivegiluck/main_end.asp:270` — num,month_pillar,disp_day
- `old/unse/fivegiluck/main_end.asp:293` — term-boundary num lookup

## 탄생화운세 (flowerluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/flowerluck`
- 진단: GET /v1/asp-services/flowerluck
- 계산/부분 계산: POST /v1/un/flowerluck

### birth_flower_identity_missing (confirmed)

원인: 원본 날짜별 꽃이름·꽃말·분류·원산지 자료가 없어 임의 배정하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- flowerluck의 날짜별 name_h/name_e/fw_word/fw_column/origin 분류 자료

판단 근거:

- `old/side_include/sub_unse.asp:97` — 탄생화운세
- `old/side_include/sub_unse_.asp:101` — 탄생화운세
- `old/unse/flowerluck/main_end.asp:94` — Dim lmyYear, lmyMonth, lmyDay, lSQL, lRs lSQL = "SELECT syear, smonth, sday " lSQL = lSQL & "FROM manse " lSQL = lSQL & "WHERE lyear = " & myYear & " and lmonth = " & myMonth & " and lday = " & myDay If myLunmonth = "윤" Then lSQL = lSQL & " AND lunmonth = 1" Else
- `old/unse/flowerluck/main_end.asp:124` —  SQL = "SELECT name_h, name_e, fw_word, fw_column, origin, story, unse " SQL = SQL & "FROM flowerluck WHERE month = " & realMonth & " AND day = " & realDay Set Rs = Dbcon.Execute(SQL)  If Rs.EOF Or Rs.BOF Then Response.Redirect "/ScriptError.asp?ErrorNum=2"

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:97` — 탄생화운세
- `old/side_include/sub_unse_.asp:101` — 탄생화운세
- `old/unse/flowerluck/main_end.asp:94` — Dim lmyYear, lmyMonth, lmyDay, lSQL, lRs lSQL = "SELECT syear, smonth, sday " lSQL = lSQL & "FROM manse " lSQL = lSQL & "WHERE lyear = " & myYear & " and lmonth = " & myMonth & " and lday = " & myDay If myLunmonth = "윤" Then lSQL = lSQL & " AND lunmonth = 1" Else
- `old/unse/flowerluck/main_end.asp:124` —  SQL = "SELECT name_h, name_e, fw_word, fw_column, origin, story, unse " SQL = SQL & "FROM flowerluck WHERE month = " & realMonth & " AND day = " & realDay Set Rs = Dbcon.Execute(SQL)  If Rs.EOF Or Rs.BOF Then Response.Redirect "/ScriptError.asp?ErrorNum=2"

## 격국풀이 — 내 삶의 나침반 (gyukgukluck)

- 상태: source_required · 원본 DLL 판정 소스·대조 검증 필요
- 원본: `old/unse/gyukgukluck`
- 진단: GET /v1/asp-services/gyukgukluck

### opaque_com_rule (confirmed)

원인: 최종 결과가 NHCP5.NHUnse.getNHResult('001')의 unseResult에서 나오며 내부 판정은 ASP에 없음.

영향: 새 점수/AI 추정으로 대체하면 기존 상용 판정 보존 불가

해결:

1. DLL의 내부 판정 소스/명세 또는 원본 Windows 검증 환경을 확보한다.
2. 서비스 입력→결과 분류/결과 배열의 회귀 샘플로 Python 이식을 검증한다.
3. 판정이 미확정인 동안 AI 문구 생성을 허용하지 않는다.

필요 자료:

- NHCP5.NHUnse 구현 소스 또는 판정 명세, 대조 실행 가능한 Windows 환경/DLL

판단 근거:

- `old/unse/gyukgukluck/main_end.asp:1361` — getNHResult call
- `function/eqFunctions.asp:2` — setIsSolar/setIsLeap/setGender original input conversion

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/unse/gyukgukluck/main.asp:81` — 고유한 사주 틀을 격이라 하며 내 삶의 나침반 서비스라고 소개
- `old/unse/gyukgukluck/main_end.asp:1361` — tmpRlt = objNH.getNHResult(tmpCode)

## 한자운세 (hanjaluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/hanjaluck`
- 진단: GET /v1/asp-services/hanjaluck
- 계산/부분 계산: POST /v1/un/hanjaluck

### source_hanja_key_and_keyword_unverified (confirmed)

원인: 원본 fun_ji_num의 미할당 반환값과 EndDay의 양력월말 사용을 검증해야 하므로 kwai 코드를 임의 확정하지 않습니다. hanja_luck 코드별 실제 한자 키워드 자료가 필요합니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- 원본 fun_ji_num 반환값 및 EndDay 경계의 대조 결과
- hanja_luck의 코드별 keyword 실제 한자 자료

판단 근거:

- `old/side_include/sub_unse.asp:41` — 한자운세
- `old/side_include/sub_unse_.asp:43` — 한자운세
- `old/unse/hanjaluck/main_end.asp:180` — Dim SqlQuery If  MEM_SEX = "남" Then SqlQuery = "select keyword, content from hanja_luck where code = 'M_01"&kwai&"'" else SqlQuery = "select keyword, content from hanja_luck where code = 'F_01"&kwai&"'" End If '	response.write SqlQuery
- `old/unse/hanjaluck/main_end.asp:182` — SqlQuery = "select keyword, content from hanja_luck where code = 'M_01"&kwai&"'" else SqlQuery = "select keyword, content from hanja_luck where code = 'F_01"&kwai&"'" End If '	response.write SqlQuery set SqlRs = DbCon.execute(SqlQuery) 

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:41` — 한자운세
- `old/side_include/sub_unse_.asp:43` — 한자운세
- `old/unse/hanjaluck/main_end.asp:180` — Dim SqlQuery If  MEM_SEX = "남" Then SqlQuery = "select keyword, content from hanja_luck where code = 'M_01"&kwai&"'" else SqlQuery = "select keyword, content from hanja_luck where code = 'F_01"&kwai&"'" End If '	response.write SqlQuery
- `old/unse/hanjaluck/main_end.asp:182` — SqlQuery = "select keyword, content from hanja_luck where code = 'M_01"&kwai&"'" else SqlQuery = "select keyword, content from hanja_luck where code = 'F_01"&kwai&"'" End If '	response.write SqlQuery set SqlRs = DbCon.execute(SqlQuery) 

## 휴대폰운세 (hpluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/hpluck`
- 진단: GET /v1/asp-services/hpluck
- 계산/부분 계산: POST /v1/un/hpluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:111` — 휴대폰운세
- `old/side_include/sub_unse_.asp:115` — 휴대폰운세
- `old/unse/hpluck/main_end.asp:142` — Dim desc1,desc2,desc3,desc4,desc5,desc6,number_unse  sSql = "select desc1,desc2,desc3,desc4,desc5,desc6 from tbSaju_otherunse where unse='Hp' and sipkyuk_code='" & sipkyuk_code & "'"  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End

## 이상형찾기 (idealluck)

- 상태: source_required · 원본 DLL 판정 소스·대조 검증 필요
- 원본: `old/unse/idealluck`
- 진단: GET /v1/asp-services/idealluck

### opaque_com_rule (confirmed)

원인: 최종 결과가 NHCP5.NHUnse.getNHResult('020')의 unseResult에서 나오며 내부 판정은 ASP에 없음.

영향: 새 점수/AI 추정으로 대체하면 기존 상용 판정 보존 불가

해결:

1. DLL의 내부 판정 소스/명세 또는 원본 Windows 검증 환경을 확보한다.
2. 서비스 입력→결과 분류/결과 배열의 회귀 샘플로 Python 이식을 검증한다.
3. 판정이 미확정인 동안 AI 문구 생성을 허용하지 않는다.

필요 자료:

- NHCP5.NHUnse 구현 소스 또는 판정 명세, 대조 실행 가능한 Windows 환경/DLL

판단 근거:

- `old/unse/idealluck/main_end.asp:1396` — getNHResult call
- `function/eqFunctions.asp:2` — setIsSolar/setIsLeap/setGender original input conversion

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/side_include/sub_love.asp:39` — 이상형찾기
- `old/unse/idealluck/main_end.asp:27` — 원본 결제 서비스명 pkind
- `old/unse/idealluck/main_end.asp:1396` — tmpRlt = objNH.getNHResult(tmpCode)

## 인터라이프 운세 모음 (interlife)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife

### interlife_subservices_mixed_status (confirmed)

원인: interlife는 개별 leaf 5종 해석 계약·2종 음양력 계산·2종 부분 검색을 Python화했으며 나머지는 별도 계산 프로필/판정 자료 검증이 필요합니다.

영향: 이 묶음 자체를 하나의 계산 서비스로 세지 않습니다. 하위 항목의 현재 상태를 확인합니다.

해결:

1. 이 목록의 하위 항목별 이슈에 따라 순서대로 이식합니다.
2. 기존 Python 사주 계산과 동명이어도 원본 입력·경계·출력 계약을 먼저 대조합니다.

판단 근거:

- `old/unse/interlife/main.asp:1` — 소스 진입 파일; 한국어명은 소개/경로 의미에서 확인 필요

### original_header_include_missing (confirmed)

원인: 입력폼에서 참조하는 /Dotong_Title.inc가 보관본에 없습니다.

영향: ASP를 그대로 실행할 때 헤더 include 문제가 날 수 있습니다. Python 계산 API에는 해당 화면 헤더가 필수는 아닙니다.

해결:

1. ASP 화면 재현이 필요하면 원본 include를 확보하거나 화면 헤더를 대체합니다.
2. Python API는 계산 입력 계약만 이식하고 화면 include와 분리합니다.

판단 근거:

- `old/unse/interlife/forms/gunghap_6.asp:6` — 실제 SSI include 대상이 저장소에서 발견되지 않음
- `old/unse/interlife/forms/gunghap_5.asp:6` — 실제 SSI include 대상이 저장소에서 발견되지 않음
- `old/unse/interlife/forms/gunghap_17.asp:6` — 실제 SSI include 대상이 저장소에서 발견되지 않음
- `old/unse/interlife/forms/gunghap_10.asp:6` — 실제 SSI include 대상이 저장소에서 발견되지 않음
- `old/unse/interlife/forms/theme_9.asp:6` — 실제 SSI include 대상이 저장소에서 발견되지 않음
- `old/unse/interlife/forms/gunghap_13.asp:6` — 실제 SSI include 대상이 저장소에서 발견되지 않음
- `old/unse/interlife/forms/gunghap_8.asp:6` — 실제 SSI include 대상이 저장소에서 발견되지 않음
- `old/unse/interlife/forms/gunghap_9.asp:6` — 실제 SSI include 대상이 저장소에서 발견되지 않음

검토 범위/실행 제약:

- 개별 운세가 아닌 메뉴/여러 결과 엔진의 컨테이너. 하위 서비스는 별도 목록으로 센다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/unse/interlife/main.asp:1` — 소스 진입 파일; 한국어명은 소개/경로 의미에서 확인 필요

## 탄생석운세 (jewelryluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/jewelryluck`
- 진단: GET /v1/asp-services/jewelryluck
- 계산/부분 계산: POST /v1/un/jewelryluck

### birth_stone_identity_missing (confirmed)

원인: stoneluck의 월별 보석이름·상징 자료가 없어 임의 배정하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- stoneluck의 월별 stname_h/stname_e/symbol 분류 자료

판단 근거:

- `old/side_include/sub_unse.asp:98` — 탄생석운세
- `old/side_include/sub_unse_.asp:102` — 탄생석운세
- `old/unse/jewelryluck/main_end.asp:64` —  SQL = "SELECT stname_h, stname_e, symbol, unse " SQL = SQL & "FROM stoneluck WHERE month = " & realMonth Set Rs = Dbcon.Execute(SQL)  If Rs.EOF Or Rs.BOF Then Response.Redirect "/ScriptError.asp?ErrorNum=2"

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:98` — 탄생석운세
- `old/side_include/sub_unse_.asp:102` — 탄생석운세
- `old/unse/jewelryluck/main_end.asp:64` —  SQL = "SELECT stname_h, stname_e, symbol, unse " SQL = SQL & "FROM stoneluck WHERE month = " & realMonth Set Rs = Dbcon.Execute(SQL)  If Rs.EOF Or Rs.BOF Then Response.Redirect "/ScriptError.asp?ErrorNum=2"

## 주민번호운세 (juminluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/juminluck`
- 진단: GET /v1/asp-services/juminluck
- 계산/부분 계산: POST /v1/un/juminluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:110` — 주민번호 운세
- `old/side_include/sub_unse_.asp:114` — 주민번호 운세
- `old/unse/juminluck/main_end.asp:115` —  Dim jumin_unse sSql="select code,desc1 from tbSaju_jumin where code='"& sumJumin &"'"  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End

## 주소지운세 (jusoluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/jusoluck`
- 진단: GET /v1/asp-services/jusoluck
- 계산/부분 계산: POST /v1/un/jusoluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:112` — 주소지운세
- `old/side_include/sub_unse_.asp:116` — 주소지운세
- `old/unse/jusoluck/main_end.asp:162` — Dim desc1,desc2,desc3,desc4,desc5,desc6, number_unse  sSql = "select desc1,desc2,desc3,desc4,desc5,desc6 from tbSaju_otherunse where unse='juso' and sipkyuk_code='" & sipkyuk_code & "'"  If QueryCheck(ssql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End

## 평생운세 (lifeluck)

- 상태: ready · 계산·선택키 이식 완료 · AI 연결 설정 필요
- 원본: `old/unse/lifeluck`
- 진단: GET /v1/asp-services/lifeluck
- 계산/부분 계산: POST /v1/fortunes/lifetime

검토 범위/실행 제약:


원본 근거:

- `old/side_include/sub_unse.asp:56` — 평생운세
- `old/side_include/sub_unse_.asp:59` — 평생운세
- `old/xmlpath/unse.xml:74` — unsekind txt
- `old/js/unseform.js:52` — CID actionurl dispatch

## 로또운세 (lottoluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/lottoluck`
- 진단: GET /v1/asp-services/lottoluck
- 계산/부분 계산: POST /v1/un/lottoluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_rng_semantics. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:109` — 로또운세
- `old/side_include/sub_unse_.asp:113` — 로또운세
- `old/unse/lottoluck/main_end.asp:611` — Randomize; Int(45*Rnd+1)
- `old/unse/lottoluck/main_end.asp:632` — lastnum=37 hardcoded extraction count

## 사랑과 결혼 (loveandluck)

- 상태: source_required · 원본 DLL 판정 소스·대조 검증 필요
- 원본: `old/unse/loveandluck`
- 진단: GET /v1/asp-services/loveandluck

### opaque_com_rule (confirmed)

원인: 최종 결과가 NHCP5.NHUnse.getNHResult('007')의 unseResult에서 나오며 내부 판정은 ASP에 없음.

영향: 새 점수/AI 추정으로 대체하면 기존 상용 판정 보존 불가

해결:

1. DLL의 내부 판정 소스/명세 또는 원본 Windows 검증 환경을 확보한다.
2. 서비스 입력→결과 분류/결과 배열의 회귀 샘플로 Python 이식을 검증한다.
3. 판정이 미확정인 동안 AI 문구 생성을 허용하지 않는다.

필요 자료:

- NHCP5.NHUnse 구현 소스 또는 판정 명세, 대조 실행 가능한 Windows 환경/DLL

판단 근거:

- `old/unse/loveandluck/main_end.asp:1402` — getNHResult call
- `function/eqFunctions.asp:2` — setIsSolar/setIsLeap/setGender original input conversion

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/side_include/sub_love.asp:40` — 사랑과 결혼
- `old/unse/loveandluck/main_end.asp:26` — 원본 결제 서비스명 pkind
- `old/unse/loveandluck/main_end.asp:1402` — tmpRlt = objNH.getNHResult(tmpCode)

## 러브 어드바이스 (loveluck)

- 상태: ready · 계산·선택키 이식 완료 · AI 연결 설정 필요
- 원본: `old/unse/loveluck`
- 진단: GET /v1/asp-services/loveluck
- 계산/부분 계산: POST /v1/fortunes/love

검토 범위/실행 제약:


원본 근거:

- `old/side_include/sub_love.asp:42` — 러브어드바이스
- `old/unse/free_main.asp:189` — 러브어드바이스

## 웨딩예감 (loverluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loverluck`
- 진단: GET /v1/asp-services/loverluck
- 계산/부분 계산: POST /v1/un/loverluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loverluck/main_end.asp:18` — 원본 결제 서비스명 pkind
- `old/unse/loverluck/main_end.asp:1346` — Dim lmyYear, lmyMonth, lmyDay, lSQL, lRs lSQL = "SELECT syear, smonth, sday " lSQL = lSQL & "FROM manse " lSQL = lSQL & "WHERE lyear = " & myYear & " and lmonth = " & myMonth & " and lday = " & myDay If myLunmonth = "윤" Then lSQL = lSQL & " AND lunmonth = 1" Else

## 파라미터형 종합 운세 (loveunse)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse

### im6_missing_subservice_selector (confirmed)

원인: IM6의 평생사주 메뉴는 loveunse/main_end.asp로 보내지만 life_all 분기 선택값이 연결되어 있지 않습니다. 이 폴더는 26개 결과 분기의 모음입니다.

영향: 폴더 전체를 평생사주 하나로 호출하면 원본 의도와 다른 경로가 됩니다.

해결:

1. 평생사주는 loveunse=life_all 입력 계약으로 분리합니다.
2. 하위 각 서비스의 helper 계산·조회 선택키를 별도로 이식합니다.

판단 근거:

- `old/js/unseform.js:32` — IM6 메뉴 라우팅; 하위 선택값 확인 필요
- `old/unse/loveunse/main_end.asp:282` — life_all 결과 분기

검토 범위/실행 제약:

- 단일 평생사주 구현이 아니라 loveunse 요청값을 분기하는 종합 운세 엔진이다.
- IM6 메뉴명은 평생사주이지만 JS actionurl에는 loveunse=life_all이 없어 메뉴명만으로 실제 실행을 보장할 수 없다.
- 동일 폴더의 main_end2/main_end__/main_re 및 백업 파일은 활성 main.asp 분기에 노출된 독립 서비스로 세지 않았다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/xmlpath/unse.xml:41` — unsekind txt
- `old/js/unseform.js:32` — CID actionurl dispatch
- `old/unse/loveunse/top_loveunse.asp:61` — 요청 loveunse값으로 제목·소개 분기
- `old/unse/loveunse/main_end.asp:76` — dbtable값으로26개 서비스와2개 남성 내부 분기
- `old/unse/loveunse/main_end.asp:383` — <table width="770" border="0" cellspacing="0" cellpadding="0" bgcolor="F3F3F3"> <% sql = "select "&contentnum&" from hm_"& dbtable & sexFolder if dbtable = "star_blood" or dbtable = "star_un" then sql = sql & " where code='"&dbQuery & number(0) & "'" else sql = sql & " where code='"&dbQuery & number & "'"

## 사랑만들기 (makingloveluck)

- 상태: source_required · 원본 DLL 판정 소스·대조 검증 필요
- 원본: `old/unse/makingloveluck`
- 진단: GET /v1/asp-services/makingloveluck

### opaque_com_rule (confirmed)

원인: 최종 결과가 NHCP5.NHUnse.getNHResult('008')의 unseResult에서 나오며 내부 판정은 ASP에 없음.

영향: 새 점수/AI 추정으로 대체하면 기존 상용 판정 보존 불가

해결:

1. DLL의 내부 판정 소스/명세 또는 원본 Windows 검증 환경을 확보한다.
2. 서비스 입력→결과 분류/결과 배열의 회귀 샘플로 Python 이식을 검증한다.
3. 판정이 미확정인 동안 AI 문구 생성을 허용하지 않는다.

필요 자료:

- NHCP5.NHUnse 구현 소스 또는 판정 명세, 대조 실행 가능한 Windows 환경/DLL

판단 근거:

- `old/unse/makingloveluck/main_end.asp:1401` — getNHResult call
- `function/eqFunctions.asp:2` — setIsSolar/setIsLeap/setGender original input conversion

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/side_include/sub_love.asp:38` — 사랑만들기
- `old/unse/makingloveluck/main_end.asp:29` — 원본 결제 서비스명 pkind
- `old/unse/makingloveluck/main_end.asp:1401` — tmpRlt = objNH.getNHResult(tmpCode)

## 결혼택일 (marriageluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/marriageluck`
- 진단: GET /v1/asp-services/marriageluck
- 계산/부분 계산: POST /v1/un/marriageluck

### missing_auspicious_day_rules (confirmed)

원인: chosenday/tbLuckDay의 원본 판정행이 미확보입니다. 입력한 행은 조사용이며 결과가 계산되어도 실제 원본 데이터 인증이나 AI 해석 허용으로 바뀌지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 기본 일진 변환과 chosenday 추가 판정값을 구분한다.
2. 원본 chosenday, tbLuckDay의 판정행/명세를 확보한다.
3. 독립 캘린더로 신규 공식을 넣지 말고 표 선택·합산 순서와 나이 계산을 보존한다.

필요 자료:

- chosenday 날짜별18개 실제 판정 플래그
- tbLuckDay 성별·나이mod8별 luckDay

판단 근거:

- `old/side_include/sub_unse.asp:139` — 결혼 택일
- `old/side_include/sub_unse_.asp:143` — 결혼 택일
- `old/unse/marriageluck/main_end.asp:72` — 원본 결제 서비스명 pkind
- `old/unse/marriageluck/main_end.asp:209` — newDay =0 if dMonth=2 then sSql = " select sday from chosenday " sSql = sSql & " where div_name=1 " sSql = sSql & " and syear=" & dyear sSql = sSql & " and smonth=" & dmonth 
- `old/unse/marriageluck/main_end.asp:246` — end if  sSql = "select lyear,syear,smonth,sday from manse " sSql = sSql& " where (syear = " & myYear_m & " and smonth = " & myMonth_m & " and sday = " & myDay_m & ") " sSql = sSql& " or (syear = " & myYear_f & " and smonth = " & myMonth_f & " and sday = " & myDay_f & ") "  If QueryCheck(sSql) = False Then
- `old/unse/marriageluck/main_end.asp:280` —  sSql = "select male,female,luckDesc, luckDay,luckDayNo " sSql = sSql& " from tbLuckDay " sSql = sSql& " where luck='대길'" sSql = sSql& " and ( male=" & restAge_m & " or female=" & restAge_f & ")"  If QueryCheck(sSql) = False Then
- `old/unse/marriageluck/main_end.asp:315` —  sSql = "select male,female,luckDesc, luckDay,luckDayNo " sSql = sSql& " from tbLuckDay " sSql = sSql& " where luck='대길'" sSql = sSql& " and ( male=" & restAge_m & " or female=" & restAge_f & ")"  If QueryCheck(sSql) = False Then
- `old/unse/marriageluck/main_end.asp:819` — sSql = sSql& ", hap_chunduk, hap_wolduk, sipak_il, sipak_daepae " sSql = sSql& ", weekday, year_pillar, month_pillar " sSql = sSql& " from chosenday " sSql = sSql& " where syear = " & dyear & " and smonth = " & dmonth  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5"
- `old/unse/marriageluck/main_end.asp:814` — chosenday flags selected for day scoring
- `old/unse/marriageluck/main_end.asp:279` — tbLuckDay sex/age-specific flags

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- CR-012 / T-024: app.ported_data_rules의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:139` — 결혼 택일
- `old/side_include/sub_unse_.asp:143` — 결혼 택일
- `old/unse/marriageluck/main_end.asp:72` — 원본 결제 서비스명 pkind
- `old/unse/marriageluck/main_end.asp:209` — newDay =0 if dMonth=2 then sSql = " select sday from chosenday " sSql = sSql & " where div_name=1 " sSql = sSql & " and syear=" & dyear sSql = sSql & " and smonth=" & dmonth 
- `old/unse/marriageluck/main_end.asp:246` — end if  sSql = "select lyear,syear,smonth,sday from manse " sSql = sSql& " where (syear = " & myYear_m & " and smonth = " & myMonth_m & " and sday = " & myDay_m & ") " sSql = sSql& " or (syear = " & myYear_f & " and smonth = " & myMonth_f & " and sday = " & myDay_f & ") "  If QueryCheck(sSql) = False Then
- `old/unse/marriageluck/main_end.asp:280` —  sSql = "select male,female,luckDesc, luckDay,luckDayNo " sSql = sSql& " from tbLuckDay " sSql = sSql& " where luck='대길'" sSql = sSql& " and ( male=" & restAge_m & " or female=" & restAge_f & ")"  If QueryCheck(sSql) = False Then
- `old/unse/marriageluck/main_end.asp:315` —  sSql = "select male,female,luckDesc, luckDay,luckDayNo " sSql = sSql& " from tbLuckDay " sSql = sSql& " where luck='대길'" sSql = sSql& " and ( male=" & restAge_m & " or female=" & restAge_f & ")"  If QueryCheck(sSql) = False Then
- `old/unse/marriageluck/main_end.asp:819` — sSql = sSql& ", hap_chunduk, hap_wolduk, sipak_il, sipak_daepae " sSql = sSql& ", weekday, year_pillar, month_pillar " sSql = sSql& " from chosenday " sSql = sSql& " where syear = " & dyear & " and smonth = " & dmonth  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5"
- `old/unse/marriageluck/main_end.asp:814` — chosenday flags selected for day scoring
- `old/unse/marriageluck/main_end.asp:279` — tbLuckDay sex/age-specific flags

## 미팅 연애운세 (meetluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/meetluck`
- 진단: GET /v1/asp-services/meetluck
- 계산/부분 계산: POST /v1/un/meetluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_love.asp:43` — 미팅 연애운세
- `old/unse/free_main.asp:114` — 
- `old/unse/meetluck/main_end.asp:133` —  Dim sql , RS, content1, content2 sql = "select content1,content2 from Meeting_Unse where Name = '" & Name & "' and Gender = '" & Sex & "'"  If QueryCheck(sql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End

## 심리테스트 (mindluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/mindluck`
- 진단: GET /v1/asp-services/mindluck
- 계산/부분 계산: POST /v1/un/mindluck

### missing_questionnaire_graph (confirmed)

원인: 원본 문항·선택지·결과 행의 수와 정렬 대응이 미확보입니다. jump_position/점수구간은 현재 활성 화면에서 미사용이며 새로운 채점·질문 전이를 만들지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 질문·답안·분기·점수구간 데이터를 확보한다.
2. 설문세션과 답안 입력을 별도 API로 설계하고 결과 문장만 AI 교체한다.

필요 자료:

- mental_content 최초행 content_num
- mental_member 정렬된 선택지 수·member_num
- mental_result 정렬된 result_num 대응

판단 근거:

- `old/side_include/sub_unse.asp:99` — 심리테스트
- `old/side_include/sub_unse_.asp:103` — 심리테스트
- `old/unse/mindluck/main_end.asp:56` — imgsrc= "sub_01.gif"  sql = "SELECT count(mental_id) As cnt FROM mental_main WHERE type='사랑'" Set Rs = DbCon.Execute(sql) If (Rs.BOF Or Rs.EOF) = False Then love_cnt = Rs("cnt") Else
- `old/unse/mindluck/main_end.asp:66` — Set Rs = Nothing  sql = "SELECT mental_id, title FROM mental_main " sql = sql & "WHERE type='사랑' ORDER BY mental_id DESC " Set Rs = DbCon.Execute(sql)  If (Rs.BOF Or Rs.EOF) = False Then
- `old/unse/mindluck/main_end.asp:89` — imgsrc= "sub_02.gif"  sql = "SELECT count(mental_id) As cnt FROM mental_main WHERE type='우정'" Set Rs = DbCon.Execute(sql) If (Rs.BOF Or Rs.EOF) = False Then friend_cnt = Rs("cnt") Else
- `old/unse/mindluck/main_end.asp:99` — Set Rs = Nothing  sql = "SELECT mental_id, title FROM mental_main " sql = sql & "WHERE type='우정' ORDER BY mental_id DESC " Set Rs = DbCon.Execute(sql)  If (Rs.BOF Or Rs.EOF) = False Then
- `old/unse/mindluck/main_end.asp:122` — imgsrc= "sub_03.gif"  sql = "SELECT count(mental_id) As cnt FROM mental_main WHERE type='성격'" Set Rs = DbCon.Execute(sql) If (Rs.BOF Or Rs.EOF) = False Then character_cnt = Rs("cnt") Else
- `old/unse/mindluck/main_end.asp:132` — Set Rs = Nothing  sql = "SELECT mental_id, title FROM mental_main " sql = sql & "WHERE type='성격' ORDER BY mental_id DESC " Set Rs = DbCon.Execute(sql)  If (Rs.BOF Or Rs.EOF) = False Then
- `old/unse/mindluck/main_end.asp:155` — imgsrc= "sub_04.gif"  sql = "SELECT count(mental_id) As cnt FROM mental_main WHERE type='기타'" Set Rs = DbCon.Execute(sql) If (Rs.BOF Or Rs.EOF) = False Then etc_cnt = Rs("cnt") Else
- `old/unse/mindluck/main_end.asp:165` — Set Rs = Nothing  sql = "SELECT mental_id, title FROM mental_main " sql = sql & "WHERE type='기타' ORDER BY mental_id DESC " Set Rs = DbCon.Execute(sql)  If (Rs.BOF Or Rs.EOF) = False Then
- `old/unse/mindluck/main_end.asp:200` — mental_member jump_position
- `old/unse/mindluck/main_end.asp:222` — mental_result start_point/end_point

검토 범위/실행 제약:

- 개별 심리테스트 제목과 mental_id 목록은 DB 동적 데이터여서 소스만으로 전부 열거할 수 없다. main.asp의 love/friend/character/etc 네 분류는 확인된다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- CR-012 / T-024: app.ported_data_rules의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:99` — 심리테스트
- `old/side_include/sub_unse_.asp:103` — 심리테스트
- `old/unse/mindluck/main_end.asp:56` — imgsrc= "sub_01.gif"  sql = "SELECT count(mental_id) As cnt FROM mental_main WHERE type='사랑'" Set Rs = DbCon.Execute(sql) If (Rs.BOF Or Rs.EOF) = False Then love_cnt = Rs("cnt") Else
- `old/unse/mindluck/main_end.asp:66` — Set Rs = Nothing  sql = "SELECT mental_id, title FROM mental_main " sql = sql & "WHERE type='사랑' ORDER BY mental_id DESC " Set Rs = DbCon.Execute(sql)  If (Rs.BOF Or Rs.EOF) = False Then
- `old/unse/mindluck/main_end.asp:89` — imgsrc= "sub_02.gif"  sql = "SELECT count(mental_id) As cnt FROM mental_main WHERE type='우정'" Set Rs = DbCon.Execute(sql) If (Rs.BOF Or Rs.EOF) = False Then friend_cnt = Rs("cnt") Else
- `old/unse/mindluck/main_end.asp:99` — Set Rs = Nothing  sql = "SELECT mental_id, title FROM mental_main " sql = sql & "WHERE type='우정' ORDER BY mental_id DESC " Set Rs = DbCon.Execute(sql)  If (Rs.BOF Or Rs.EOF) = False Then
- `old/unse/mindluck/main_end.asp:122` — imgsrc= "sub_03.gif"  sql = "SELECT count(mental_id) As cnt FROM mental_main WHERE type='성격'" Set Rs = DbCon.Execute(sql) If (Rs.BOF Or Rs.EOF) = False Then character_cnt = Rs("cnt") Else
- `old/unse/mindluck/main_end.asp:132` — Set Rs = Nothing  sql = "SELECT mental_id, title FROM mental_main " sql = sql & "WHERE type='성격' ORDER BY mental_id DESC " Set Rs = DbCon.Execute(sql)  If (Rs.BOF Or Rs.EOF) = False Then
- `old/unse/mindluck/main_end.asp:155` — imgsrc= "sub_04.gif"  sql = "SELECT count(mental_id) As cnt FROM mental_main WHERE type='기타'" Set Rs = DbCon.Execute(sql) If (Rs.BOF Or Rs.EOF) = False Then etc_cnt = Rs("cnt") Else
- `old/unse/mindluck/main_end.asp:165` — Set Rs = Nothing  sql = "SELECT mental_id, title FROM mental_main " sql = sql & "WHERE type='기타' ORDER BY mental_id DESC " Set Rs = DbCon.Execute(sql)  If (Rs.BOF Or Rs.EOF) = False Then
- `old/unse/mindluck/main_end.asp:200` — mental_member jump_position
- `old/unse/mindluck/main_end.asp:222` — mental_result start_point/end_point

## 명품 평생재물운 (moneyluck)

- 상태: ready · 계산·선택키 이식 완료 · AI 연결 설정 필요
- 원본: `old/unse/moneyluck`
- 진단: GET /v1/asp-services/moneyluck
- 계산/부분 계산: POST /v1/fortunes/wealth

검토 범위/실행 제약:


원본 근거:

- `old/side_include/sub_unse.asp:67` — 名品 평생 재물운
- `old/side_include/sub_unse_.asp:70` — 名品 평생 재물운
- `old/xmlpath/unse.xml:58` — unsekind txt
- `old/js/unseform.js:42` — CID actionurl dispatch

## 이달의 운세 (monthluck)

- 상태: ready · 계산·선택키 이식 완료 · AI 연결 설정 필요
- 원본: `old/unse/monthluck`
- 진단: GET /v1/asp-services/monthluck
- 계산/부분 계산: POST /v1/fortunes/monthly

검토 범위/실행 제약:


원본 근거:

- `old/side_include/sub_unse.asp:38` — " else response.write " " end if %>이달의 운세
- `old/xmlpath/unse.xml:26` — unsekind txt
- `old/js/unseform.js:22` — CID actionurl dispatch

## 이사택일 (moveluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/moveluck`
- 진단: GET /v1/asp-services/moveluck
- 계산/부분 계산: POST /v1/un/moveluck

### missing_auspicious_day_rules (confirmed)

원인: chosenday/tbLuckDay의 원본 판정행이 미확보입니다. 입력한 행은 조사용이며 결과가 계산되어도 실제 원본 데이터 인증이나 AI 해석 허용으로 바뀌지 않습니다. tbLocation의 실제 나이별 방위·분류 행이 미확보입니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 기본 일진 변환과 chosenday 추가 판정값을 구분한다.
2. 원본 chosenday, tbLuckDay, tbLocation의 판정행/명세를 확보한다.
3. 독립 캘린더로 신규 공식을 넣지 말고 표 선택·합산 순서와 나이 계산을 보존한다.

필요 자료:

- chosenday 날짜별18개 실제 판정 플래그
- tbLuckDay 성별·나이mod8별 luckDay
- tbLocation gender/age_0..8별 실제 방향·cont_idx

판단 근거:

- `old/side_include/sub_unse.asp:140` — 이사 택일
- `old/side_include/sub_unse_.asp:144` — 이사 택일
- `old/unse/moveluck/main.asp:61` — 입력 myOption에 따른 두 결과 경로
- `old/unse/moveluck/main_end1.asp:608` — chosenday flags selected for day scoring
- `old/unse/moveluck/main_end1.asp:199` — tbLuckDay sex/age-specific flags
- `old/unse/moveluck/main.asp:61` — two form action branches
- `old/unse/moveluck/main_end2.asp:218` — male/female age_n directions

검토 범위/실행 제약:

- move_day.asp는 선택 날짜 상세, move_des.asp는 설명이므로 별도 운세 서비스로 세지 않았다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- CR-012 / T-024: app.ported_data_rules의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:140` — 이사 택일
- `old/side_include/sub_unse_.asp:144` — 이사 택일
- `old/unse/moveluck/main.asp:61` — 입력 myOption에 따른 두 결과 경로
- `old/unse/moveluck/main_end1.asp:608` — chosenday flags selected for day scoring
- `old/unse/moveluck/main_end1.asp:199` — tbLuckDay sex/age-specific flags
- `old/unse/moveluck/main.asp:61` — two form action branches
- `old/unse/moveluck/main_end2.asp:218` — male/female age_n directions

## 정통궁합 (originalwedluck)

- 상태: source_required · 원본 DLL 판정 소스·대조 검증 필요
- 원본: `old/unse/originalwedluck`
- 진단: GET /v1/asp-services/originalwedluck

### opaque_com_rule (confirmed)

원인: 최종 결과가 NHCP5.NHUnse.getNHResult('003')의 unseResult에서 나오며 내부 판정은 ASP에 없음.

영향: 새 점수/AI 추정으로 대체하면 기존 상용 판정 보존 불가

해결:

1. DLL의 내부 판정 소스/명세 또는 원본 Windows 검증 환경을 확보한다.
2. 서비스 입력→결과 분류/결과 배열의 회귀 샘플로 Python 이식을 검증한다.
3. 판정이 미확정인 동안 AI 문구 생성을 허용하지 않는다.

필요 자료:

- NHCP5.NHUnse 구현 소스 또는 판정 명세, 대조 실행 가능한 Windows 환경/DLL

판단 근거:

- `old/unse/originalwedluck/main_end.asp:189` — getNHResult call
- `function/eqFunctions.asp:2` — setIsSolar/setIsLeap/setGender original input conversion

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/unse/originalwedluck/main_end.asp:30` — 원본 결제 서비스명 pkind
- `old/unse/originalwedluck/main_end.asp:189` — tmpRlt = objNH.getNHResult(tmpCode)

## 서로를 성장시키는 비결 (ourgrowthluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/ourgrowthluck`
- 진단: GET /v1/asp-services/ourgrowthluck
- 계산/부분 계산: POST /v1/un/ourgrowthluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_template의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, unverified_saju_array_profile. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: SajuManseryuk의 DLL 실제 실행 결과와 동일성은 미검증입니다.
- 실행 제약: 허용된 기본 만세력 대체 범위에서 dotong 사주를 時/日/月/年 1-based KAN/SI에 대응합니다.
- 실행 제약: 藏干·통변성·12운성은 _SajuManseryuk.asp의 정적 표와 날짜 분기를 그대로 적용합니다.
- 실행 제약: 미사용 대운·세운 배열과 tbAisyo 준비 조회는 생성하지 않습니다.
- CR-012 / T-024: app.ported_template의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/ourgrowthluck/main_end.asp:15` — 원본 출력 소항목
- `old/unse/ourgrowthluck/main_end.asp:33` — 원본 결제 서비스명 pkind
- `old/unse/ourgrowthluck/main_end.asp:14` — L_item_code_Text = "saju_marrycheck_1|saju_marrycheck_2|saju_marrycheck_3|saju_marrycheck_4"
- `old/unse/ourgrowthluck/main_end.asp:228` — Dim MyAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(Birthday_Sun,12) & "') ORDER BY fdDate DESC" '				adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/ourgrowthluck/main_end.asp:247` — Dim OtherAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(OtherBirthday_Sun,12) & "') ORDER BY fdDate DESC" '				adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/ourgrowthluck/main_end.asp:266` — Dim ThirdAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(ThirdBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/ourgrowthluck/main_end.asp:14` — item codes saju_marrycheck
- `function/b_include/_SajuManseryuk.asp:93` — SajuManseryuk uses DllManse.SajuGanJi

## 향수점 (perfumeluck)

- 상태: source_required · 원본 DLL 판정 소스·대조 검증 필요
- 원본: `old/unse/perfumeluck`
- 진단: GET /v1/asp-services/perfumeluck

### opaque_com_rule (confirmed)

원인: 최종 결과가 NHCP5.NHUnse.getNHResult('017')의 unseResult에서 나오며 내부 판정은 ASP에 없음.

영향: 새 점수/AI 추정으로 대체하면 기존 상용 판정 보존 불가

해결:

1. DLL의 내부 판정 소스/명세 또는 원본 Windows 검증 환경을 확보한다.
2. 서비스 입력→결과 분류/결과 배열의 회귀 샘플로 Python 이식을 검증한다.
3. 판정이 미확정인 동안 AI 문구 생성을 허용하지 않는다.

필요 자료:

- NHCP5.NHUnse 구현 소스 또는 판정 명세, 대조 실행 가능한 Windows 환경/DLL

판단 근거:

- `old/unse/perfumeluck/main_end.asp:133` — getNHResult call
- `function/eqFunctions.asp:2` — setIsSolar/setIsLeap/setGender original input conversion

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/side_include/sub_unse.asp:87` — 향수점
- `old/side_include/sub_unse_.asp:91` — 향수점
- `old/unse/perfumeluck/main_end.asp:133` — tmpRlt = objNH.getNHResult(tmpCode)

## 명품 개인종합운세 (perluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/perluck`
- 진단: GET /v1/asp-services/perluck
- 계산/부분 계산: POST /v1/un/perluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:68` — 名品 개인종합운세
- `old/side_include/sub_unse_.asp:71` — 名品 개인종합운세
- `old/xmlpath/unse.xml:50` — unsekind txt
- `old/js/unseform.js:37` — CID actionurl dispatch
- `old/unse/perluck/main_end.asp:187` —  if myLunsol = "양" then sSql = "Select lyear,lmonth,lday,lunmonth from manse where syear= '" & myYear &"' and smonth= '" & myMonth &"' and sday= '" & myDay &"'"  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/perluck/main_end.asp:233` — Dim Result1,Temp1,Temp2,Temp3  sSql = "select content from totalun where title= '" & YearJi &"'"  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/perluck/main_end.asp:259` —   sSql = "select content from totalun where title= '" & Temp1 &"'"  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/perluck/main_end.asp:284` — Temp2 = threedb(int(Temp2))  sSql = "select content from totalun where title= '" & Temp2 &"'"  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/perluck/main_end.asp:309` — Temp3 = fourdb(int(Temp3))  sSql = "select content from totalun where title= '" & Temp3 &"'"  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/perluck/main_end.asp:380` — End Select  sSql = "select content from totalun where title= '" & know &"'"  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/perluck/main_end.asp:399` — REM ########################################################################### 장애운 시작 Dim Result6 sSql = "select content from totalun where title= '" & KnowTemp &"'"  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/perluck/main_end.asp:540` — End Select  sSql = "select content from totalun where" & sQuery  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End

## 도통 전생록 (preluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/preluck`
- 진단: GET /v1/asp-services/preluck
- 계산/부분 계산: POST /v1/un/preluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:77` — 도통 전생록
- `old/side_include/sub_unse_.asp:80` — 도통 전생록
- `old/unse/preluck/main_end.asp:91` — '### 양력생일일 경우 음력생일 찾기 Dim sSql, Rs, rs_pillar, rs_bmonth, rs_bday sSql = "select year_pillar,lmonth,lday from manse " sSql = sSql & " where " & rs_lunsol & "year=" & myYear sSql = sSql & " and " & rs_lunsol & "month=" & myMonth sSql = sSql & " and " & rs_lunsol & "day=" & myDay 
- `old/unse/preluck/main_end.asp:112` — '### 전생자료찾기 sSql = "select div_flag,content,character,parent,child " sSql = sSql& " from tbPreLife " sSql = sSql& " where (div_flag=1 and div_date=" & (rs_pillar+1) & ")" sSql = sSql& " or (div_flag=2 and div_date=" & rs_bmonth & ")" sSql = sSql& " or (div_flag=3 and div_date=" & rs_bday  & ")" 

## 궁합신살처방 (sinsalluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/sinsalluck`
- 진단: GET /v1/asp-services/sinsalluck
- 계산/부분 계산: POST /v1/un/sinsalluck

### source_gpcheck_state_required (confirmed)

원인: 궁합신살 본문은 이전 요청의 gpcheck 쿠키와 함수 호출 수에 의존합니다. legacy_gpcheck 숫자 배열이 없어 원본 gp_content 최종 선택을 확정하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- 해당 원본 요청의 gpcheck 상태 또는 명시적 legacy_gpcheck 숫자 배열

판단 근거:

- `old/side_include/sub_love.asp:78` — 궁합신살처방
- `old/unse/sinsalluck/main_end.asp:132` — Dim Rs, scharacter Dim sumso, posbreak, partso, sSql sSql = "select content from gp_character where male = '" & M_DayGan & "' and female = '" & F_DayGan & "' "  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/sinsalluck/main_end.asp:408` — Dim i, sql, num, title, content for i = 1 to gp_func_count sql = "Select num,title,content from gp_content where num = " & gpcheck_arr(i)  If QueryCheck(sql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End

검토 범위/실행 제약:

- 메뉴의 /love/sinsalluck 경로는 보관본의 old/unse/sinsalluck에 대응한다.
- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_love.asp:78` — 궁합신살처방
- `old/unse/sinsalluck/main_end.asp:132` — Dim Rs, scharacter Dim sumso, posbreak, partso, sSql sSql = "select content from gp_character where male = '" & M_DayGan & "' and female = '" & F_DayGan & "' "  If QueryCheck(sSql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/sinsalluck/main_end.asp:408` — Dim i, sql, num, title, content for i = 1 to gp_func_count sql = "Select num,title,content from gp_content where num = " & gpcheck_arr(i)  If QueryCheck(sql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End

## 로또운세 SMS서비스 (smslottoluck)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse/smslottoluck`
- 진단: GET /v1/asp-services/smslottoluck

### delivery_workflow_separate (confirmed)

원인: main_end는 신청정보·기간·전화번호를 저장하고 SMS전송큐에 안내문을 넣는 신청/전달흐름이다. 해당페이지에 실제 일일/주간 배치생성의 전체판정이 들어있지 않다.

영향: 이를 계산API로 바꾸기만 하면 원본배치/일정/동의흐름을 재현하지 못함

해결:

1. 운세계산과 구독·스케줄·SMS전송을 별도기능으로 분리한다.
2. 실제배치생성/발송스크립트를 추적해야 전체서비스 대응이 가능하다.

필요 자료:

- SMS 구독까지 구현할 경우 원본 배치 생성·예약 발송 스크립트

판단 근거:

- `old/unse/smslottoluck/main_end.asp:83` — subscription input and delivery queue flow

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.

원본 근거:

- `old/side_include/sub_unse.asp:35` — 로또운세 SMS서비스
- `old/side_include/sub_unse_.asp:37` — 로또운세 SMS서비스

## 오늘의 운세 SMS서비스 (smstodayluck)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse/smstodayluck`
- 진단: GET /v1/asp-services/smstodayluck

### delivery_workflow_separate (confirmed)

원인: main_end는 신청정보·기간·전화번호를 저장하고 SMS전송큐에 안내문을 넣는 신청/전달흐름이다. 해당페이지에 실제 일일/주간 배치생성의 전체판정이 들어있지 않다.

영향: 이를 계산API로 바꾸기만 하면 원본배치/일정/동의흐름을 재현하지 못함

해결:

1. 운세계산과 구독·스케줄·SMS전송을 별도기능으로 분리한다.
2. 실제배치생성/발송스크립트를 추적해야 전체서비스 대응이 가능하다.

필요 자료:

- SMS 구독까지 구현할 경우 원본 배치 생성·예약 발송 스크립트

판단 근거:

- `old/unse/smstodayluck/main_end.asp:192` — subscription input and delivery queue flow

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.

원본 근거:

- `old/side_include/sub_unse.asp:33` — 오늘의운세 SMS서비스
- `old/side_include/sub_unse_.asp:35` — 오늘의운세 SMS서비스
- `old/xmlpath/unse.xml:82` — unsekind txt
- `old/js/unseform.js:57` — CID actionurl dispatch
- `old/unse/smstodayluck/main_end.asp:193` —  sSql = "select amount,input1,input2,input3,input4,input5,input6,input7,input8,input9,input10,input11,input12,input13 " sSql = sSql & " from todaysms_buddy " sSql = sSql & " where pid='" & pid & "'" sSql = sSql & " and ad_yn='Y'"  If QueryCheck(sSql) = False Then

## 자녀교육법 (sonluck)

- 상태: source_required · 원본 DLL 판정 소스·대조 검증 필요
- 원본: `old/unse/sonluck`
- 진단: GET /v1/asp-services/sonluck

### opaque_com_rule (confirmed)

원인: 최종 결과가 NHCP5.NHUnse.getNHResult('011')의 unseResult에서 나오며 내부 판정은 ASP에 없음.

영향: 새 점수/AI 추정으로 대체하면 기존 상용 판정 보존 불가

해결:

1. DLL의 내부 판정 소스/명세 또는 원본 Windows 검증 환경을 확보한다.
2. 서비스 입력→결과 분류/결과 배열의 회귀 샘플로 Python 이식을 검증한다.
3. 판정이 미확정인 동안 AI 문구 생성을 허용하지 않는다.

필요 자료:

- NHCP5.NHUnse 구현 소스 또는 판정 명세, 대조 실행 가능한 Windows 환경/DLL

판단 근거:

- `old/unse/sonluck/main_end.asp:1396` — getNHResult call
- `function/eqFunctions.asp:2` — setIsSolar/setIsLeap/setGender original input conversion

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.

원본 근거:

- `old/side_include/sub_unse.asp:75` — 자녀 교육법
- `old/side_include/sub_unse_.asp:78` — 자녀 교육법
- `old/unse/sonluck/main_end.asp:32` — 원본 결제 서비스명 pkind
- `old/unse/sonluck/main_end.asp:1396` — tmpRlt = objNH.getNHResult(tmpCode)

## 별자리운세 (starluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/starluck`
- 진단: GET /v1/asp-services/starluck
- 계산/부분 계산: POST /v1/un/starluck

### star_blood_harmony_classification_missing (confirmed)

원인: 원본 harmony의 궁합 혈액형 분류가 DB에 있어 임의 분류하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- tbStarLuck.harmony의 원본 궁합 혈액형 분류

판단 근거:

- `old/side_include/sub_unse.asp:93` — 별자리운세
- `old/side_include/sub_unse_.asp:97` — 별자리운세
- `old/unse/starluck/main_end.asp:51` —  Dim Rs, strSQL strSQL =" Select * From tbStarLuck where bloodtype = '"& bloodtype &"' and gender = '"& gender&"' and startdate = '"& startdate &"'" '	  response.write strSQL  If QueryCheck(strSQL) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5"
- `old/unse/starluck/main_end.asp:18` — input fields
- `old/unse/starluck/main_end.asp:51` — tbStarLuck WHERE bloodtype,gender,startdate

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet, additional_input_required. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:93` — 별자리운세
- `old/side_include/sub_unse_.asp:97` — 별자리운세
- `old/unse/starluck/main_end.asp:51` —  Dim Rs, strSQL strSQL =" Select * From tbStarLuck where bloodtype = '"& bloodtype &"' and gender = '"& gender&"' and startdate = '"& startdate &"'" '	  response.write strSQL  If QueryCheck(strSQL) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5"
- `old/unse/starluck/main_end.asp:18` — input fields
- `old/unse/starluck/main_end.asp:51` — tbStarLuck WHERE bloodtype,gender,startdate

## 학생운세 (studentluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/studentluck`
- 진단: GET /v1/asp-services/studentluck
- 계산/부분 계산: POST /v1/un/studentluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet, legacy_age_behavior. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_unse.asp:76` — 학생운세
- `old/side_include/sub_unse_.asp:79` — 학생운세
- `old/unse/studentluck/main_end.asp:84` — if age > 60 then
- `old/unse/studentluck/main_end.asp:103` — Dim content1_Gender,content2_Gender,content1_School,content2_School  sql = "select content1,content2,content3 from Exam_Unse where ilgan = '" & ilgan & "' and sex = '" & sex & "'"  If QueryCheck(sql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/studentluck/main_end.asp:118` — Set RS = nothing  sql = "select content1,content2 from Gender_Unse where ilgan = '" & ilgan & "' and sex = '" & sex & "'"  If QueryCheck(sql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/studentluck/main_end.asp:133` —   sql = "select content1,content2 from School_Unse where ilgan = '" & ilgan & "' and sex = '" & sex & "'"  If QueryCheck(sql) = False Then Response.Redirect "/ScriptError.asp?ErrorNum=5" Response.End
- `old/unse/studentluck/main_end.asp:81` — age=year(now)-myYear; if age>60 warning
- `old/unse/studentluck/main_end.asp:93` — after warning CalcSaju still called

## 명품 평생애정운 (sweetluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/sweetluck`
- 진단: GET /v1/asp-services/sweetluck
- 계산/부분 계산: POST /v1/un/sweetluck

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- 확인한 실행 분기는 코드로 선택키를 만들고 결과 문구를 조회합니다. 원본 문구 DB 확보는 AI 전환의 선행 조건이 아닙니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, not_ported_yet. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_love.asp:34` — 名品 평생애정운
- `old/unse/sweetluck/main_end.asp:34` — 원본 결제 서비스명 pkind
- `old/unse/sweetluck/main_end.asp:1377` —  '### 초년 ### sSql = "select " & viewField & " from sweetluck where yukgap = '" &  ypillar & "' and daygan = '" & DayGan & "'" Set Rs = Dbcon.execute(sSql)  '''myCho = replace(Rs(0),chr(10),"<br>") 
- `old/unse/sweetluck/main_end.asp:1386` —  '### 장년 ### sSql = "select " & viewField & " from sweetluck where yukgap = '" &  mpillar & "' and daygan = '" & DayGan & "'" Set Rs = Dbcon.execute(sSql)  ''myJang = replace(Rs(0),chr(10),"<br>") 
- `old/unse/sweetluck/main_end.asp:1395` —  '### 중년 ### sSql = "select " & viewField & " from sweetluck where yukgap = '" &  dpillar & "' and daygan = '" & DayGan & "'" Set Rs = Dbcon.execute(sSql)  '''myJung = replace(Rs(0),chr(10),"<br>") 
- `old/unse/sweetluck/main_end.asp:1404` —  '### 말년 ### sSql = "select " & viewField & " from sweetluck where yukgap = '" &  tpillar & "' and daygan = '" & DayGan & "'" Set Rs = Dbcon.execute(sSql)  '''myMal = replace(Rs(0),chr(10),"<br>") 

## 오늘의 운세 (todayluck)

- 상태: ready · 계산·선택키 이식 완료 · AI 연결 설정 필요
- 원본: `old/unse/todayluck`
- 진단: GET /v1/asp-services/todayluck
- 계산/부분 계산: POST /v1/fortunes/daily

검토 범위/실행 제약:


원본 근거:

- `old/side_include/sub_unse.asp:36` — " else response.write " " end if %>오늘의 운세
- `old/xmlpath/unse.xml:3` — unsekind txt
- `old/js/unseform.js:7` — CID actionurl dispatch

## 궁합 UP 가이드 (wedupluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/wedupluck`
- 진단: GET /v1/asp-services/wedupluck
- 계산/부분 계산: POST /v1/un/wedupluck

### planet_fdastro_classification_missing (confirmed)

원인: astro_harmony_1: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다. astro_harmony_2: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다. astro_harmony_3: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다. astro_harmony_4: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- tbSavianAstro_Planet_*의 fdDate/fdAstro 원본 행성 분류

판단 근거:

- `old/unse/wedupluck/main_end.asp:15` — 원본 출력 소항목
- `old/unse/wedupluck/main_end.asp:32` — 원본 결제 서비스명 pkind
- `old/unse/wedupluck/main_end.asp:14` — L_item_code_Text = "astro_harmony_1|astro_harmony_2|astro_harmony_3|astro_harmony_4"
- `old/unse/wedupluck/main_end.asp:227` — Dim MyAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(Birthday_Sun,12) & "') ORDER BY fdDate DESC" '				adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/wedupluck/main_end.asp:246` — Dim OtherAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(OtherBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/wedupluck/main_end.asp:265` — Dim ThirdAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(ThirdBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/wedupluck/main_end.asp:227` — active astro item code path queries planet series
- `function/b_include/lib_astrology.asp:180` — planet position query used to compose content key

검토 범위/실행 제약:

- 운세 최종 선택/판정에 쓰는 경로 중심의 정적 코드검토. ASP/DB/DLL 실제실행 동일성은 미검증.
- CR-012 / T-024: app.ported_template의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, missing_planet_position_data. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_template의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/wedupluck/main_end.asp:15` — 원본 출력 소항목
- `old/unse/wedupluck/main_end.asp:32` — 원본 결제 서비스명 pkind
- `old/unse/wedupluck/main_end.asp:14` — L_item_code_Text = "astro_harmony_1|astro_harmony_2|astro_harmony_3|astro_harmony_4"
- `old/unse/wedupluck/main_end.asp:227` — Dim MyAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(Birthday_Sun,12) & "') ORDER BY fdDate DESC" '				adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/wedupluck/main_end.asp:246` — Dim OtherAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(OtherBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/wedupluck/main_end.asp:265` — Dim ThirdAstroSign(9) For i = 1 to 10 strSQL = "SELECT TOP 1 fdAstro FROM tbSavianAstro_Planet_" & i & " WHERE (fdDate < '" & LEFT(ThirdBirthday_Sun,12) & "') ORDER BY fdDate DESC" adoCmd.CommandType = adCmdText adoCmd.CommandText = strSQL adoCmd.Execute 
- `old/unse/wedupluck/main_end.asp:227` — active astro item code path queries planet series
- `function/b_include/lib_astrology.asp:180` — planet position query used to compose content key

## 이번주 운세 (weekluck)

- 상태: ready · 계산·선택키 이식 완료 · AI 연결 설정 필요
- 원본: `old/unse/weekluck`
- 진단: GET /v1/asp-services/weekluck
- 계산/부분 계산: POST /v1/fortunes/weekly

검토 범위/실행 제약:


원본 근거:

- `old/side_include/sub_unse.asp:37` — " else response.write " " end if %>이번주 운세
- `old/xmlpath/unse.xml:18` — unsekind txt
- `old/js/unseform.js:17` — CID actionurl dispatch

## 불륜일까? 사랑일까? (adultluck-affairorloveluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/adultluck/affairorloveluck`
- 진단: GET /v1/asp-services/adultluck-affairorloveluck
- 계산/부분 계산: POST /v1/un/adultluck-affairorloveluck

검토 범위/실행 제약:

- adultluck 부모와 별도 운세 서비스이며 나이 확인 화면/성인 동의 도구는 별도 서비스로 세지 않는다.
- 정적 소스 검토; 실제 ASP 실행은 미검증
- CR-012 / T-024: app.ported_template의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, unverified_saju_array_profile. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: SajuManseryuk의 DLL 실제 실행 결과와 동일성은 미검증입니다.
- 실행 제약: 허용된 기본 만세력 대체 범위에서 dotong 사주를 時/日/月/年 1-based KAN/SI에 대응합니다.
- 실행 제약: 藏干·통변성·12운성은 _SajuManseryuk.asp의 정적 표와 날짜 분기를 그대로 적용합니다.
- 실행 제약: 미사용 대운·세운 배열과 tbAisyo 준비 조회는 생성하지 않습니다.
- CR-012 / T-024: app.ported_template의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/adultluck/affairorloveluck/main_end.asp:15` — 원본 결과 항목
- `old/unse/adultluck/affairorloveluck/main_end.asp:34` — 원본 서비스명 pkind
- `old/unse/adultluck/affairorloveluck/main_end.asp:14` — fixed items
- `function/b_include/lib_sajumaster.asp:668` — saju_immorality dispatch

## 부부의 침실 궁합 (adultluck-bedroommatchingluck)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/adultluck/bedroommatchingluck`
- 진단: GET /v1/asp-services/adultluck-bedroommatchingluck
- 계산/부분 계산: POST /v1/un/adultluck-bedroommatchingluck

### planet_fdastro_classification_missing (confirmed)

원인: women_astroharmony: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다. women_mymarry: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다. astro_attraction: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- tbSavianAstro_Planet_*의 fdDate/fdAstro 원본 행성 분류

판단 근거:

- `old/unse/adultluck/bedroommatchingluck/main_end.asp:15` — 원본 결과 항목
- `old/unse/adultluck/bedroommatchingluck/main_end.asp:34` — 원본 서비스명 pkind
- `old/unse/adultluck/bedroommatchingluck/main_end.asp:14` — four mixed women/astro itemcodes
- `function/b_include/lib_women.asp:15` — loveharmony formulas
- `function/b_include/lib_women.asp:50` — AstroType from MyAstroSign
- `function/b_include/lib_women.asp:67` — planet pair angle classes

검토 범위/실행 제약:

- adultluck 부모와 별도 운세 서비스이며 나이 확인 화면/성인 동의 도구는 별도 서비스로 세지 않는다.
- 정적 소스 검토; 실제 ASP 실행은 미검증
- CR-012 / T-024: app.ported_template의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, missing_planet_position_data. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_template의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/adultluck/bedroommatchingluck/main_end.asp:15` — 원본 결과 항목
- `old/unse/adultluck/bedroommatchingluck/main_end.asp:34` — 원본 서비스명 pkind
- `old/unse/adultluck/bedroommatchingluck/main_end.asp:14` — four mixed women/astro itemcodes
- `function/b_include/lib_women.asp:15` — loveharmony formulas
- `function/b_include/lib_women.asp:50` — AstroType from MyAstroSign
- `function/b_include/lib_women.asp:67` — planet pair angle classes

## 연인과의 최고 절정의 기술 (adultluck-lovertechniqueluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/adultluck/lovertechniqueluck`
- 진단: GET /v1/asp-services/adultluck-lovertechniqueluck
- 계산/부분 계산: POST /v1/un/adultluck-lovertechniqueluck

검토 범위/실행 제약:

- adultluck 부모와 별도 운세 서비스이며 나이 확인 화면/성인 동의 도구는 별도 서비스로 세지 않는다.
- 정적 소스 검토; 실제 ASP 실행은 미검증
- CR-012 / T-024: app.ported_template의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, unverified_saju_array_profile. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: SajuManseryuk의 DLL 실제 실행 결과와 동일성은 미검증입니다.
- 실행 제약: 허용된 기본 만세력 대체 범위에서 dotong 사주를 時/日/月/年 1-based KAN/SI에 대응합니다.
- 실행 제약: 藏干·통변성·12운성은 _SajuManseryuk.asp의 정적 표와 날짜 분기를 그대로 적용합니다.
- 실행 제약: 미사용 대운·세운 배열과 tbAisyo 준비 조회는 생성하지 않습니다.
- CR-012 / T-024: app.ported_template의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/adultluck/lovertechniqueluck/main_end.asp:15` — 원본 결과 항목
- `old/unse/adultluck/lovertechniqueluck/main_end.asp:34` — 원본 서비스명 pkind
- `old/unse/adultluck/lovertechniqueluck/main_end.asp:14` — fixed items
- `function/b_include/lib_sajumaster.asp:754` — exact sexlove3..8 key mapping

## 연인의 음란한 소망 (adultluck-loverwishluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/adultluck/loverwishluck`
- 진단: GET /v1/asp-services/adultluck-loverwishluck
- 계산/부분 계산: POST /v1/un/adultluck-loverwishluck

검토 범위/실행 제약:

- adultluck 부모와 별도 운세 서비스이며 나이 확인 화면/성인 동의 도구는 별도 서비스로 세지 않는다.
- 정적 소스 검토; 실제 ASP 실행은 미검증
- CR-012 / T-024: app.ported_template의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, unverified_saju_array_profile. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: SajuManseryuk의 DLL 실제 실행 결과와 동일성은 미검증입니다.
- 실행 제약: 허용된 기본 만세력 대체 범위에서 dotong 사주를 時/日/月/年 1-based KAN/SI에 대응합니다.
- 실행 제약: 藏干·통변성·12운성은 _SajuManseryuk.asp의 정적 표와 날짜 분기를 그대로 적용합니다.
- 실행 제약: 미사용 대운·세운 배열과 tbAisyo 준비 조회는 생성하지 않습니다.
- CR-012 / T-024: app.ported_template의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/adultluck/loverwishluck/main_end.asp:15` — 원본 결과 항목
- `old/unse/adultluck/loverwishluck/main_end.asp:33` — 원본 서비스명 pkind
- `old/unse/adultluck/loverwishluck/main_end.asp:14` — fixed items
- `function/b_include/lib_sajumaster.asp:754` — exact sexlove3..8 key mapping

## 금단의 섹스 진단 (adultluck-prohibitionsexluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/adultluck/prohibitionsexluck`
- 진단: GET /v1/asp-services/adultluck-prohibitionsexluck
- 계산/부분 계산: POST /v1/un/adultluck-prohibitionsexluck

검토 범위/실행 제약:

- adultluck 부모와 별도 운세 서비스이며 나이 확인 화면/성인 동의 도구는 별도 서비스로 세지 않는다.
- 정적 소스 검토; 실제 ASP 실행은 미검증
- CR-012 / T-024: app.ported_template의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, unverified_saju_array_profile. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: SajuManseryuk의 DLL 실제 실행 결과와 동일성은 미검증입니다.
- 실행 제약: 허용된 기본 만세력 대체 범위에서 dotong 사주를 時/日/月/年 1-based KAN/SI에 대응합니다.
- 실행 제약: 藏干·통변성·12운성은 _SajuManseryuk.asp의 정적 표와 날짜 분기를 그대로 적용합니다.
- 실행 제약: 미사용 대운·세운 배열과 tbAisyo 준비 조회는 생성하지 않습니다.
- CR-012 / T-024: app.ported_template의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/adultluck/prohibitionsexluck/main_end.asp:15` — 원본 결과 항목
- `old/unse/adultluck/prohibitionsexluck/main_end.asp:33` — 원본 서비스명 pkind
- `old/unse/adultluck/prohibitionsexluck/main_end.asp:14` — fixed items
- `function/b_include/lib_sajumaster.asp:477` — sexcheck branch

## 은밀한 섹스스타일 (adultluck-sexluck)

- 상태: source_required · 원본 DLL 판정 소스·대조 검증 필요
- 원본: `old/unse/adultluck/sexluck`
- 진단: GET /v1/asp-services/adultluck-sexluck

### opaque_com_rule (confirmed)

원인: NHCP5.NHUnse.getNHResult('012')가 최종 결과를 만든다.

영향: 기존 상용 분류/출력항목을 일반 AI 답변으로 대신하면 안 됨

해결:

1. 원본별 계산·선택키·출력계약을 분리 이식한다.
2. 필수 판정자료를 확보하거나 원본과 동등함을 검증하기 전까지 AI 결과 생성을 차단한다.

필요 자료:

- NHCP5.NHUnse DLL의 구현 소스·판정 명세 또는 대조 실행 환경

판단 근거:

- `old/unse/adultluck/sexluck/main_end.asp:38` — default tmpCode012
- `old/unse/adultluck/sexluck/main_end.asp:1400` — opaque getNHResult

검토 범위/실행 제약:

- adultluck 부모와 별도 운세 서비스이며 나이 확인 화면/성인 동의 도구는 별도 서비스로 세지 않는다.
- 정적 소스 검토; 실제 ASP 실행은 미검증

원본 근거:

- `old/unse/adultluck/sexluck/main_end.asp:43` — 원본 서비스명 pkind

## 별자리 속궁합 (adultluck-starcoupleluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/adultluck/starcoupleluck`
- 진단: GET /v1/asp-services/adultluck-starcoupleluck
- 계산/부분 계산: POST /v1/un/adultluck-starcoupleluck

검토 범위/실행 제약:

- adultluck 부모와 별도 운세 서비스이며 나이 확인 화면/성인 동의 도구는 별도 서비스로 세지 않는다.
- 정적 소스 검토; 실제 ASP 실행은 미검증
- CR-012 / T-024: app.ported_direct의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, code_rules_plus_narrative_lookup. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_direct의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/side_include/sub_love.asp:64` — 별자리 속궁합 메뉴
- `old/unse/adultluck/starcoupleluck/main_end.asp:3` — dbcon_test include
- `old/unse/adultluck/starcoupleluck/main_end.asp:52` — StarsexLuck WHERE gender/day

## 시간대별 섹스 바이오 (adultluck-timesexbioluck)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/adultluck/timesexbioluck`
- 진단: GET /v1/asp-services/adultluck-timesexbioluck
- 계산/부분 계산: POST /v1/un/adultluck-timesexbioluck

검토 범위/실행 제약:

- adultluck 부모와 별도 운세 서비스이며 나이 확인 화면/성인 동의 도구는 별도 서비스로 세지 않는다.
- 정적 소스 검토; 실제 ASP 실행은 미검증
- CR-012 / T-024: app.ported_remaining의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, code_rules_plus_narrative_lookup. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_remaining의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/adultluck/timesexbioluck/main_end.asp:15` — 원본 결과 항목
- `old/unse/adultluck/timesexbioluck/main_end.asp:34` — 원본 서비스명 pkind
- `old/unse/adultluck/timesexbioluck/main_end.asp:14` — single item
- `function/b_include/lib_sajumaster.asp:730` — 28-day sinusoid and 12 time slots

## 운세 메인 메뉴 (unse-main)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse`
- 진단: GET /v1/asp-services/unse-main

검토 범위/실행 제약:

- 이 파일을 별도 계산 운세로 세지 않는다.

원본 근거:

- `old/unse/main.asp:1` — 루트 보조/메뉴 파일

## 무료 운세 메인 메뉴 (unse-free-main)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse`
- 진단: GET /v1/asp-services/unse-free-main

검토 범위/실행 제약:

- 이 파일을 별도 계산 운세로 세지 않는다.

원본 근거:

- `old/unse/free_main.asp:1` — 루트 보조/메뉴 파일

## 동영상운세 메뉴·외부서비스 연결 (unse-moving-main)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse`
- 진단: GET /v1/asp-services/unse-moving-main

검토 범위/실행 제약:

- 이 파일을 별도 계산 운세로 세지 않는다.

원본 근거:

- `old/unse/moving_main.asp:1` — 루트 보조/메뉴 파일

## 동영상운세 프레임 (unse-moving-frame)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse`
- 진단: GET /v1/asp-services/unse-moving-frame

검토 범위/실행 제약:

- 이 파일을 별도 계산 운세로 세지 않는다.

원본 근거:

- `old/unse/moving_frame.asp:1` — 루트 보조/메뉴 파일

## 동영상운세 미리보기·전달 (unse-moving-preview)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse`
- 진단: GET /v1/asp-services/unse-moving-preview

검토 범위/실행 제약:

- 이 파일을 별도 계산 운세로 세지 않는다.

원본 근거:

- `old/unse/moving_preview.asp:1` — 루트 보조/메뉴 파일

## 운세 AJAX 전달 도구 (unse-div)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse`
- 진단: GET /v1/asp-services/unse-div

검토 범위/실행 제약:

- 이 파일을 별도 계산 운세로 세지 않는다.

원본 근거:

- `old/unse/div.asp:1` — 루트 보조/메뉴 파일

## 연간운세 광고 배너 (unse-ad-billyear)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse`
- 진단: GET /v1/asp-services/unse-ad-billyear

검토 범위/실행 제약:

- 이 파일을 별도 계산 운세로 세지 않는다.

원본 근거:

- `old/unse/ad_billyear.asp:1` — 루트 보조/메뉴 파일

## 2012년 간지 조견표 (fivegiluck-age1)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse/fivegiluck`
- 진단: GET /v1/asp-services/fivegiluck-age1

검토 범위/실행 제약:

- 해설/조견표 페이지이며 별도 개인 판정 운세가 아니다.

원본 근거:

- `old/side_include/sub_unse.asp:156` — 명시적 도움말 메뉴

## 기의 분류 (fivegiluck-chart)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse/fivegiluck`
- 진단: GET /v1/asp-services/fivegiluck-chart

검토 범위/실행 제약:

- 해설/조견표 페이지이며 별도 개인 판정 운세가 아니다.

원본 근거:

- `old/side_include/sub_unse.asp:157` — 명시적 도움말 메뉴

## 음양 오행 (fivegiluck-cosmic)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse/fivegiluck`
- 진단: GET /v1/asp-services/fivegiluck-cosmic

검토 범위/실행 제약:

- 해설/조견표 페이지이며 별도 개인 판정 운세가 아니다.

원본 근거:

- `old/side_include/sub_unse.asp:158` — 명시적 도움말 메뉴

## 이번주 로또운세 (loveunse-lotto)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-lotto
- 계산/부분 계산: POST /v1/un/loveunse-lotto
- 원본 분기: `{"loveunse": "lotto"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- 이 분기의 원본 계산은 VB 산술/내장 달력으로 확인됩니다. hm_*는 최종 문구 전용이며 원본 문구 DB는 AI 전환의 선행 조건이 아닙니다. FSO readFile/XMLHTTP 선언은 실제 호출되지 않아 외부 의존성으로 분류하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: not_ported_source_logic, source_calendar_variable_unassigned, server_clock_and_partial_date. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:65` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:77` — 원본 실제 결과 계산 분기
- `old/unse/loveunse/main_end.asp:77` — lotto 분기
- `old/unse/loveunse/main_end.asp:78` — number = lotto_unse(user_year,user_month,user_day,user_hour,user_sol,user_sex,target_year,target_month)
- `old/unse/loveunse/main_end.asp:383` — 동적 hm_* SELECT
- `old/unse/loveunse/main_end.asp:418` — Replace(Rs(i),'##','') 문구 출력
- `function/loveunse.asp:299` — lotto_unse 함수 본문, 산술/내장 달력만 호출
- `old/unse/loveunse/main_end.asp:23` — user_calendar=fn_RA('myLunsol')
- `old/unse/loveunse/main_end.asp:30` — user1_calendar 할당
- `old/unse/loveunse/main_end.asp:37` — user2_calendar 할당
- `function/loveunse.asp:310` — Date() 및 월요일 역산
- `function/loveunse.asp:325` — 요청 조회년/월과 server 월요일 day를 혼합

## 오늘의 섹스운세 (loveunse-eroticwoto)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-eroticwoto
- 계산/부분 계산: POST /v1/un/loveunse-eroticwoto
- 원본 분기: `{"loveunse": "eroticwoto"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- 이 분기의 원본 계산은 VB 산술/내장 달력으로 확인됩니다. hm_*는 최종 문구 전용이며 원본 문구 DB는 AI 전환의 선행 조건이 아닙니다. FSO readFile/XMLHTTP 선언은 실제 호출되지 않아 외부 의존성으로 분류하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: not_ported_source_logic. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:72` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:86` — 원본 실제 결과 계산 분기
- `old/unse/loveunse/main_end.asp:86` — eroticwoto 분기
- `old/unse/loveunse/main_end.asp:87` — number=game_unse(user_year,user_month,user_day,user_hour,user_calendar,user_sex,target_year,target_month,target_day)
- `old/unse/loveunse/main_end.asp:383` — 동적 hm_* SELECT
- `old/unse/loveunse/main_end.asp:418` — Replace(Rs(i),'##','') 문구 출력
- `function/loveunse.asp:386` — game_unse 함수 본문, 산술/내장 달력만 호출

## 오늘의 섹스감도 (loveunse-sexwoman)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-sexwoman
- 계산/부분 계산: POST /v1/un/loveunse-sexwoman
- 원본 분기: `{"loveunse": "sexwoman"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- 이 분기의 원본 계산은 VB 산술/내장 달력으로 확인됩니다. hm_*는 최종 문구 전용이며 원본 문구 DB는 AI 전환의 선행 조건이 아닙니다. FSO readFile/XMLHTTP 선언은 실제 호출되지 않아 외부 의존성으로 분류하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: not_ported_source_logic. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:78` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:106` — 원본 실제 결과 계산 분기
- `old/unse/loveunse/main_end.asp:106` — sexwoman 분기
- `old/unse/loveunse/main_end.asp:107` — number = game_unse(user_year,user_month,user_day,user_hour,user_calendar,user_sex,target_year,target_month,target_day)
- `old/unse/loveunse/main_end.asp:383` — 동적 hm_* SELECT
- `old/unse/loveunse/main_end.asp:418` — Replace(Rs(i),'##','') 문구 출력
- `function/loveunse.asp:386` — game_unse 함수 본문, 산술/내장 달력만 호출

## 오늘의 경마운세 (loveunse-horse)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-horse
- 계산/부분 계산: POST /v1/un/loveunse-horse
- 원본 분기: `{"loveunse": "horse"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- 이 분기의 원본 계산은 VB 산술/내장 달력으로 확인됩니다. hm_*는 최종 문구 전용이며 원본 문구 DB는 AI 전환의 선행 조건이 아닙니다. FSO readFile/XMLHTTP 선언은 실제 호출되지 않아 외부 의존성으로 분류하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: not_ported_source_logic, server_clock_and_partial_date, horse_option_offset_uninitialized. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:84` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:122` — 원본 실제 결과 계산 분기
- `old/unse/loveunse/main_end.asp:122` — horse 분기
- `old/unse/loveunse/main_end.asp:123` — number = horse_unse(user_year,user_month,user_day,user_hour,user_calendar,user_sex,target_year,target_month,target_day,day_oo)
- `old/unse/loveunse/main_end.asp:383` — 동적 hm_* SELECT
- `old/unse/loveunse/main_end.asp:418` — Replace(Rs(i),'##','') 문구 출력
- `function/loveunse.asp:343` — horse_unse 함수 본문, 산술/내장 달력만 호출
- `function/loveunse.asp:354` — Date() 및 월요일 역산
- `function/loveunse.asp:369` — 요청 조회년/월과 server 월요일 day를 혼합
- `old/unse/loveunse/main_end.asp:71` — day_oo 초기화의 분기 조건
- `old/unse/loveunse/main_end.asp:123` — horse_unse에 day_oo 전달
- `function/loveunse.asp:369` — lll 가산

## 탄생화운세 (loveunse-birth-flower)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-birth-flower
- 계산/부분 계산: POST /v1/un/loveunse-birth-flower
- 원본 분기: `{"loveunse": "birth_flower"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:90` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:130` — 원본 실제 결과 계산 분기

## 혈액형 궁합 (loveunse-blood-blood)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-blood-blood
- 계산/부분 계산: POST /v1/un/loveunse-blood-blood
- 원본 분기: `{"loveunse": "blood_blood"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:95` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:138` — 원본 실제 결과 계산 분기

## 플라워운세 (loveunse-flower)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-flower
- 계산/부분 계산: POST /v1/un/loveunse-flower
- 원본 분기: `{"loveunse": "flower"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- 이 분기의 원본 계산은 VB 산술/내장 달력으로 확인됩니다. hm_*는 최종 문구 전용이며 원본 문구 DB는 AI 전환의 선행 조건이 아닙니다. FSO readFile/XMLHTTP 선언은 실제 호출되지 않아 외부 의존성으로 분류하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: not_ported_source_logic, source_calendar_variable_unassigned. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:101` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:149` — 원본 실제 결과 계산 분기
- `old/unse/loveunse/main_end.asp:149` — flower 분기
- `old/unse/loveunse/main_end.asp:150` — number  = flower(user_year,user_month,user_day,user_hour,user_sol,user_sex,target_year,target_month,target_day)
- `old/unse/loveunse/main_end.asp:383` — 동적 hm_* SELECT
- `old/unse/loveunse/main_end.asp:418` — Replace(Rs(i),'##','') 문구 출력
- `function/loveunse.asp:484` — flower 함수 본문, 산술/내장 달력만 호출
- `old/unse/loveunse/main_end.asp:23` — user_calendar=fn_RA('myLunsol')
- `old/unse/loveunse/main_end.asp:30` — user1_calendar 할당
- `old/unse/loveunse/main_end.asp:37` — user2_calendar 할당

## 오늘의 게임운세 (loveunse-game)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-game
- 계산/부분 계산: POST /v1/un/loveunse-game
- 원본 분기: `{"loveunse": "game"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- 이 분기의 원본 계산은 VB 산술/내장 달력으로 확인됩니다. hm_*는 최종 문구 전용이며 원본 문구 DB는 AI 전환의 선행 조건이 아닙니다. FSO readFile/XMLHTTP 선언은 실제 호출되지 않아 외부 의존성으로 분류하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: not_ported_source_logic, source_calendar_variable_unassigned. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:107` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:157` — 원본 실제 결과 계산 분기
- `old/unse/loveunse/main_end.asp:157` — game 분기
- `old/unse/loveunse/main_end.asp:158` — number  = game_unse(user_year,user_month,user_day,user_hour,user_sol,user_sex,target_year,target_month,target_day)
- `old/unse/loveunse/main_end.asp:383` — 동적 hm_* SELECT
- `old/unse/loveunse/main_end.asp:418` — Replace(Rs(i),'##','') 문구 출력
- `function/loveunse.asp:386` — game_unse 함수 본문, 산술/내장 달력만 호출
- `old/unse/loveunse/main_end.asp:23` — user_calendar=fn_RA('myLunsol')
- `old/unse/loveunse/main_end.asp:30` — user1_calendar 할당
- `old/unse/loveunse/main_end.asp:37` — user2_calendar 할당

## 주간운세 (loveunse-jugan-unse)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-jugan-unse
- 계산/부분 계산: POST /v1/un/loveunse-jugan-unse
- 원본 분기: `{"loveunse": "jugan_unse"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:113` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:165` — 원본 실제 결과 계산 분기

## 왕자의 오늘 데이트 (loveunse-prince-date)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-prince-date
- 계산/부분 계산: POST /v1/un/loveunse-prince-date
- 원본 분기: `{"loveunse": "prince_date"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:118` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:172` — 원본 실제 결과 계산 분기

## 왕자의 오늘 사랑 (loveunse-prince-love-today)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-prince-love-today
- 계산/부분 계산: POST /v1/un/loveunse-prince-love-today
- 원본 분기: `{"loveunse": "prince_love_today"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:125` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:180` — 원본 실제 결과 계산 분기

## 왕자의 오늘운세 (loveunse-prince-today)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-prince-today
- 계산/부분 계산: POST /v1/un/loveunse-prince-today
- 원본 분기: `{"loveunse": "prince_today"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:131` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:190` — 원본 실제 결과 계산 분기

## 공주의 오늘 데이트 (loveunse-princess-date)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-princess-date
- 계산/부분 계산: POST /v1/un/loveunse-princess-date
- 원본 분기: `{"loveunse": "princess_date"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:137` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:199` — 원본 실제 결과 계산 분기

## 공주의 오늘 사랑 (loveunse-princess-love-today)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-princess-love-today
- 계산/부분 계산: POST /v1/un/loveunse-princess-love-today
- 원본 분기: `{"loveunse": "princess_love_today"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:149` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:207` — 원본 실제 결과 계산 분기

## 공주의 오늘운세 (loveunse-princess-today)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-princess-today
- 계산/부분 계산: POST /v1/un/loveunse-princess-today
- 원본 분기: `{"loveunse": "princess_today"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:155` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:217` — 원본 실제 결과 계산 분기

## 별자리운세 (loveunse-star-un)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-star-un
- 계산/부분 계산: POST /v1/un/loveunse-star-un
- 원본 분기: `{"loveunse": "star_un"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:161` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:227` — 원본 실제 결과 계산 분기

## 첫 데이트 궁합 (loveunse-firstdate)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-firstdate
- 계산/부분 계산: POST /v1/un/loveunse-firstdate
- 원본 분기: `{"loveunse": "firstdate"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- 이 분기의 원본 계산은 VB 산술/내장 달력으로 확인됩니다. hm_*는 최종 문구 전용이며 원본 문구 DB는 AI 전환의 선행 조건이 아닙니다. FSO readFile/XMLHTTP 선언은 실제 호출되지 않아 외부 의존성으로 분류하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: not_ported_source_logic, source_calendar_variable_unassigned, source_gender_zero_vs_request_one_two. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:167` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:237` — 원본 실제 결과 계산 분기
- `old/unse/loveunse/main_end.asp:237` — firstdate 분기
- `old/unse/loveunse/main_end.asp:238` — number = gunghab(user_year,user_month,user_day,user_hour,user_sol,user_sex,user2_year,user2_month,user2_day,user2_hour,user2_sol,user2_sex)
- `old/unse/loveunse/main_end.asp:383` — 동적 hm_* SELECT
- `old/unse/loveunse/main_end.asp:418` — Replace(Rs(i),'##','') 문구 출력
- `function/loveunse.asp:166` — gunghab 함수 본문, 산술/내장 달력만 호출
- `old/unse/loveunse/main_end.asp:23` — user_calendar=fn_RA('myLunsol')
- `old/unse/loveunse/main_end.asp:30` — user1_calendar 할당
- `old/unse/loveunse/main_end.asp:37` — user2_calendar 할당
- `old/unse/loveunse/main_end.asp:24` — 요청 성별 남1/여2
- `function/loveunse.asp:184` — 함수 성별=0 분기

## 첫 섹스 만족도 (loveunse-firstsex)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-firstsex
- 계산/부분 계산: POST /v1/un/loveunse-firstsex
- 원본 분기: `{"loveunse": "firstsex"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- 이 분기의 원본 계산은 VB 산술/내장 달력으로 확인됩니다. hm_*는 최종 문구 전용이며 원본 문구 DB는 AI 전환의 선행 조건이 아닙니다. FSO readFile/XMLHTTP 선언은 실제 호출되지 않아 외부 의존성으로 분류하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: not_ported_source_logic, source_gender_zero_vs_request_one_two. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:173` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:248` — 원본 실제 결과 계산 분기
- `old/unse/loveunse/main_end.asp:248` — firstsex 분기
- `old/unse/loveunse/main_end.asp:249` — number = deepsex(user_year,user_month,user_day,user_hour,user_calendar,user_sex,user2_year,user2_month,user2_day,user2_hour,user2_calendar,user2_sex)
- `old/unse/loveunse/main_end.asp:383` — 동적 hm_* SELECT
- `old/unse/loveunse/main_end.asp:418` — Replace(Rs(i),'##','') 문구 출력
- `function/loveunse.asp:415` — deepsex 함수 본문, 산술/내장 달력만 호출
- `old/unse/loveunse/main_end.asp:24` — 요청 성별 남1/여2
- `function/loveunse.asp:433` — 함수 성별=0 분기

## 오늘의 고스톱운세 (loveunse-gostop)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-gostop
- 계산/부분 계산: POST /v1/un/loveunse-gostop
- 원본 분기: `{"loveunse": "gostop"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- 이 분기의 원본 계산은 VB 산술/내장 달력으로 확인됩니다. hm_*는 최종 문구 전용이며 원본 문구 DB는 AI 전환의 선행 조건이 아닙니다. FSO readFile/XMLHTTP 선언은 실제 호출되지 않아 외부 의존성으로 분류하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: not_ported_source_logic. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:179` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:258` — 원본 실제 결과 계산 분기
- `old/unse/loveunse/main_end.asp:258` — gostop 분기
- `old/unse/loveunse/main_end.asp:259` — number = game_unse(user_year,user_month,user_day,user_hour,user_calendar,user_sex,target_year,target_month,target_day)
- `old/unse/loveunse/main_end.asp:383` — 동적 hm_* SELECT
- `old/unse/loveunse/main_end.asp:418` — Replace(Rs(i),'##','') 문구 출력
- `function/loveunse.asp:386` — game_unse 함수 본문, 산술/내장 달력만 호출

## 궁합 (loveunse-gunghap)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-gunghap
- 계산/부분 계산: POST /v1/un/loveunse-gunghap
- 원본 분기: `{"loveunse": "gunghap"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- 소개문에는 혈액형이 언급되지만 result 분기는 별도 gunghab 함수이다. 제목과 구현을 임의로 합치지 않는다.
- 이 분기의 원본 계산은 VB 산술/내장 달력으로 확인됩니다. hm_*는 최종 문구 전용이며 원본 문구 DB는 AI 전환의 선행 조건이 아닙니다. FSO readFile/XMLHTTP 선언은 실제 호출되지 않아 외부 의존성으로 분류하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: not_ported_source_logic, source_gender_zero_vs_request_one_two. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:185` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:266` — 원본 실제 결과 계산 분기
- `old/unse/loveunse/main_end.asp:266` — gunghap 분기
- `old/unse/loveunse/main_end.asp:267` — number=gunghab(user_year,user_month,user_day,user_hour,user_calendar,user_sex,user2_year,user2_month,user2_day,user2_hour,user2_calendar,user2_sex)
- `old/unse/loveunse/main_end.asp:383` — 동적 hm_* SELECT
- `old/unse/loveunse/main_end.asp:418` — Replace(Rs(i),'##','') 문구 출력
- `function/loveunse.asp:166` — gunghab 함수 본문, 산술/내장 달력만 호출
- `old/unse/loveunse/main_end.asp:24` — 요청 성별 남1/여2
- `function/loveunse.asp:184` — 함수 성별=0 분기

## 오늘의 레저운세 (loveunse-leisure)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-leisure
- 계산/부분 계산: POST /v1/un/loveunse-leisure
- 원본 분기: `{"loveunse": "leisure"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- 이 분기의 원본 계산은 VB 산술/내장 달력으로 확인됩니다. hm_*는 최종 문구 전용이며 원본 문구 DB는 AI 전환의 선행 조건이 아닙니다. FSO readFile/XMLHTTP 선언은 실제 호출되지 않아 외부 의존성으로 분류하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: not_ported_source_logic. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:192` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:272` — 원본 실제 결과 계산 분기
- `old/unse/loveunse/main_end.asp:272` — leisure 분기
- `old/unse/loveunse/main_end.asp:273` — number  = yupgi1_unse(user_year,user_month,user_day,user_hour,user_calendar,user_sex,target_year,target_month,target_day)
- `old/unse/loveunse/main_end.asp:383` — 동적 hm_* SELECT
- `old/unse/loveunse/main_end.asp:418` — Replace(Rs(i),'##','') 문구 출력
- `function/loveunse.asp:87` — yupgi1_unse 함수 본문, 산술/내장 달력만 호출

## 평생사주 (loveunse-life-all)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-life-all
- 계산/부분 계산: POST /v1/un/loveunse-life-all
- 원본 분기: `{"loveunse": "life_all"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- IM6 평생사주의 이름과 대응되는 실제 분기는 life_all이다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:198` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:281` — 원본 실제 결과 계산 분기

## 속궁합 (loveunse-sok-gonghap)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-sok-gonghap
- 계산/부분 계산: POST /v1/un/loveunse-sok-gonghap
- 원본 분기: `{"loveunse": "sok_gonghap"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:203` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:292` — 원본 실제 결과 계산 분기

## 별자리와 혈액형 심리 (loveunse-star-blood)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-star-blood
- 계산/부분 계산: POST /v1/un/loveunse-star-blood
- 원본 분기: `{"loveunse": "star_blood"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:209` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:301` — 원본 실제 결과 계산 분기

## 오늘의 데이트운세 (loveunse-today-date-unse)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-today-date-unse
- 계산/부분 계산: POST /v1/un/loveunse-today-date-unse
- 원본 분기: `{"loveunse": "today_date_unse"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:217` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:310` — 원본 실제 결과 계산 분기

## 오늘의 엽기운세 (loveunse-yupgi-dosa)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-yupgi-dosa
- 계산/부분 계산: POST /v1/un/loveunse-yupgi-dosa
- 원본 분기: `{"loveunse": "yupgi_dosa"}`

검토 범위/실행 제약:

- 같은 이름의 다른 폴더 구현과 별개의 원본 구현이다.
- 원본 제목 주석은 여성용으로 한정한다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 원본 UI 코드 및 계산 quirks를 보존한 정적 이식이며 ASP 서버 실 실행 대조는 하지 않았습니다.
- 실행 제약: 선택 키는 원본 문구 분류이며 점수·길흉·당첨 확률을 뜻하지 않습니다.
- 실행 제약: 음력 날짜 유효성과 조회일 선후 관계는 원본 평달 배열로 검증하며 윤달 및 배열 범위 밖 입력은 거절합니다.
- 실행 제약: 명시적 미변환 프로필은 날짜 검증 후 계산에 사용할 입력 숫자만 변환하지 않습니다.
- CR-012 / T-024: app.ported_loveunse의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:223` — 원본 요청값별 서비스 소개
- `old/unse/loveunse/main_end.asp:318` — 원본 실제 결과 계산 분기

## 관상보기 (마의상법) (interlife-faceface)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-faceface
- 계산/부분 계산: POST /v1/un/interlife-faceface

검토 범위/실행 제약:

- 13개 파일은 한 관상 서비스의 입력·확인·결과 흐름이며 13종 별도 운세가 아님.
- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 최종 faceface_13 결과에 실제 출력되는 19개 문구만 원본 순서로 선택합니다. 중간 설문 화면은 새 결과 서비스로 만들지 않습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_1.asp:5` — UNSE_TITLE = "관상보기"
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_1.asp:35` — alert('얼굴 형태를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_10.asp:5` — UNSE_TITLE = "관상보기"
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_10.asp:36` — alert('입술의 크기를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_10.asp:52` — alert('윗입술의 두께를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_10.asp:68` — alert('입술의 형태를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_10.asp:84` — alert('입술 끝의 모양을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_10.asp:101` — alert('아랫입술의 주름을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_11.asp:5` — UNSE_TITLE = "관상보기"
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_11.asp:36` — alert('턱의 모양을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_12.asp:5` — UNSE_TITLE = "관상보기"
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_12.asp:26` — face_style 입력 요약 및 faceface_13.asp로 전송하는 확인 화면
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_13.asp:5` — UNSE_TITLE = "관상보기"
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_13.asp:24` — 선택형 face_style 값으로 T063 분류를 조회하는 최종 결과 화면
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_2.asp:5` — UNSE_TITLE = "관상보기"
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_2.asp:36` — alert('이마의 모양을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_2.asp:52` — alert('이마의 폭을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_2.asp:68` — alert('이마의 주름살을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_3.asp:5` — UNSE_TITLE = "관상보기"
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_3.asp:36` — alert('눈썹의 모양을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_3.asp:52` — alert('눈썹의 길이를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_3.asp:68` — alert('눈썹 털의 상태를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_3.asp:84` — alert('눈썹 사이의 넓이를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_3.asp:100` — alert('눈썹 사이의 주름살을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_4.asp:5` — UNSE_TITLE = "관상보기"
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_4.asp:36` — alert('눈의 크기를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_4.asp:52` — alert('눈의 모양을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_4.asp:68` — alert('눈동자의 위치를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_4.asp:84` — alert('눈꼬리 주변의 주름을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_4.asp:100` — alert('눈꼬리의 모양을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_4.asp:116` — alert('눈꺼풀의 두께를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_5.asp:5` — UNSE_TITLE = "관상보기"
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_5.asp:39` — alert('귀의 출발점 위치를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_5.asp:55` — alert('귀바퀴의 크기를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_5.asp:71` — alert('귓볼의 모양을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_5.asp:87` — alert('귀의 모양을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_6.asp:5` — UNSE_TITLE = "관상보기"
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_6.asp:36` — alert('코의 길이를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_6.asp:52` — alert('콧대의 높이를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_6.asp:68` — alert('콧등의 형태를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_6.asp:84` — alert('콧망울의 모양을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_6.asp:100` — alert('콧구멍의 모양을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_6.asp:116` — alert('준두부위의 모양을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_7.asp:5` — UNSE_TITLE = "관상보기"
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_7.asp:36` — alert('광대뼈의 모양을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_8.asp:5` — UNSE_TITLE = "관상보기"
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_8.asp:36` — alert('법령의 모양을 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_9.asp:5` — UNSE_TITLE = "관상보기"
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_9.asp:36` — alert('인중의 넓이를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_9.asp:52` — alert('인중의 길이를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_9.asp:68` — alert('인중의 형태를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_9.asp:84` — alert('코와 입 사이의 넓이를 선택하세요!');
- `old/unse/interlife/UNSE_DATA/unse/faceface/faceface_9.asp:100` — alert('인중의 모습을 선택하세요!');

## 오늘의 띠별운세 (interlife-free-1)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-free-1
- 계산/부분 계산: POST /v1/un/interlife-free-1

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, interlife_calendar_classification_mansedata, interlife_solar_term_boundary_manse_data, conditional_leap_file_path. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 이 leaf는 본인 생년월일·사주를 사용하지 않고 server Date()의 MMDD별 12띠 문구를 조회합니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_1.asp:30` — UNSE_TITLE = "오늘의 띠별운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 사주명식 (interlife-free-11)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-free-11
- 계산/부분 계산: POST /v1/un/interlife-free-11

### interlife_full_chart_profile_unverified (confirmed)

원인: source_row_required: source_birth_rows.birth.day_e source_row_required: source_birth_rows.birth.day_h source_row_required: source_birth_rows.birth.jeolip source_row_required: source_birth_rows.selected.month_e source_row_required: source_birth_rows.selected.month_h source_row_required: source_birth_rows.selected.year_e source_row_required: source_birth_rows.selected.year_h source_row_required: source_current_record.no source_row_required: source_current_record.umyear_e source_row_required: source_current_record.umyear_h source_unassigned_state: 원본 외부 입력이 미할당입니다: daeun10_no, daeun1_no, daeun2_no, daeun3_no, daeun4_no, daeun5_no, daeun6_no, daeun7_no, daeun8_no, daeun9_no, my_age source_syntax_anomaly: 원본 VB 블록의 // 주석형 행을 계산식과 구분해 보존했습니다. 원본 배포의 주석 처리 상태를 확인해야 합니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- source_birth_rows.birth.{no,number,day_h,day_e,jeolip}
- source_birth_rows.selected.{number,year_h,year_e,month_h,month_e}
- source_current_record.{no,umyear_h,umyear_e}
- source_state.{my_age,daeun1_no..daeun10_no}; 원본에 할당문 없는 외부 입력

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_11.asp:7` — UNSE_TITLE = "사주명식"
- `old/unse/interlife/UNSE_DATA/solve/F/F029.asp:27` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/F/F029.asp:27` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_chart의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_11.asp:7` — UNSE_TITLE = "사주명식"
- `old/unse/interlife/UNSE_DATA/solve/F/F029.asp:27` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/F/F029.asp:27` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 음양력변환 (interlife-free-12)

- 상태: calculation_only · Python 계산 전용 완료 · AI 해석 대상 아님
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-free-12
- 계산/부분 계산: POST /v1/un/interlife-free-12

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, interlife_calendar_classification_mansedata, conditional_leap_file_path. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: 기본 달력 변환만 tb_manse 교정 조회로 대응합니다. f_Saju 명식·대운 배열과의 동일성을 뜻하지 않습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_12.asp:7` — UNSE_TITLE = "음양력변환"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 꿈해몽 (interlife-free-13)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-free-13
- 계산/부분 계산: POST /v1/un/interlife-free-13

### dream_search_index_missing (confirmed)

원인: F020 원본 검색 인덱스(DB_title, DB_num)와 검색 일치 행수·순서가 미확보입니다. AI가 검색 결과 제목·개수·원본 행을 임의 생성하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- F020의 DB_title/DB_num 원본 검색 인덱스와 결과 행수·순서

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_13.asp:4` — UNSE_TITLE = "꿈해몽 / 태몽"
- `old/unse/interlife/data/moneyDATA.dat:22` — 무료 운세 항목13=꿈해몽, 항목14=태몽; UNSE_TITLE은 둘 모두 꿈해몽 / 태몽

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_13.asp:4` — UNSE_TITLE = "꿈해몽 / 태몽"
- `old/unse/interlife/data/moneyDATA.dat:22` — 무료 운세 항목13=꿈해몽, 항목14=태몽; UNSE_TITLE은 둘 모두 꿈해몽 / 태몽

## 태몽 (interlife-free-14)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-free-14
- 계산/부분 계산: POST /v1/un/interlife-free-14

### dream_search_index_missing (confirmed)

원인: F007 원본 검색 인덱스(DB_title_1, DB_num)와 검색 일치 행수·순서가 미확보입니다. AI가 검색 결과 제목·개수·원본 행을 임의 생성하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- F007의 DB_title_1/DB_num 원본 검색 인덱스와 결과 행수·순서

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_14.asp:4` — UNSE_TITLE = "꿈해몽 / 태몽"
- `old/unse/interlife/data/moneyDATA.dat:22` — 무료 운세 항목13=꿈해몽, 항목14=태몽; UNSE_TITLE은 둘 모두 꿈해몽 / 태몽

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_14.asp:4` — UNSE_TITLE = "꿈해몽 / 태몽"
- `old/unse/interlife/data/moneyDATA.dat:22` — 무료 운세 항목13=꿈해몽, 항목14=태몽; UNSE_TITLE은 둘 모두 꿈해몽 / 태몽

## 별자리운세 (interlife-free-2)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-free-2
- 계산/부분 계산: POST /v1/un/interlife-free-2

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, interlife_calendar_classification_mansedata, interlife_solar_term_boundary_manse_data, conditional_leap_file_path. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: loveunse와 다른 원본 별자리 경계를 사용합니다. 원본은 solar_month가 아니라 request_month/day를 사용합니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_2.asp:30` — UNSE_TITLE = "별자리운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 혈액형운세 (interlife-free-3)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-free-3
- 계산/부분 계산: POST /v1/un/interlife-free-3

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, interlife_calendar_classification_mansedata, interlife_solar_term_boundary_manse_data, conditional_leap_file_path. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_3.asp:30` — UNSE_TITLE = "혈액형운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 주민번호운세 (interlife-free-4)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-free-4
- 계산/부분 계산: POST /v1/un/interlife-free-4

### source_selector_binding_unverified (confirmed)

원인: 원본 T046은 주민번호를 읽지 않고 mm+yy+dd를 합산합니다. yy/mm은 함수 로컬이고 전역 dd는 천간 배열로 덮입니다. On Error Resume Next 이후 unmyung의 Empty/기존값 상태에 따른 10 보정 결과를 실제 ASP와 대조해야 하며 생일 합으로 고치지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- T046 mm/yy/dd 전역 상태와 오류 후 unmyung 값의 실제 ASP 실행 근거

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_4.asp:30` — UNSE_TITLE = "주민번호운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름
- `old/unse/interlife/UNSE_DATA/solve/T/T046.asp:6` — T-023/T-024 실제 leaf 실행 계약 재검토

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- 공통 사주 include 참조와 실제 leaf 출력 의존성을 구분했습니다. 이 leaf의 현재 차단 원인은 개별 selector/분류 계약이며 공통 달력의 일괄 필수 의존을 주장하지 않습니다.
- CR-012 / T-024: app.ported_interlife_dependencies의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_4.asp:30` — UNSE_TITLE = "주민번호운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름
- `old/unse/interlife/UNSE_DATA/solve/T/T046.asp:6` — T-023/T-024 실제 leaf 실행 계약 재검토

## 행운번호운세 (interlife-free-5)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-free-5
- 계산/부분 계산: POST /v1/un/interlife-free-5

### lucky_number_classification_missing (confirmed)

원인: F019의 성별별 吉/凶/半吉半凶 실제 분류가 없어 색상·기호와 최종 길흉 판정을 확정할 수 없습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- F019.DB_express/DB_express_1 실제 吉/凶/半吉半凶 분류

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_5.asp:30` — UNSE_TITLE = "행운번호운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름
- `old/unse/interlife/UNSE_DATA/solve/F/F019.asp:65` — T-023/T-024 실제 leaf 실행 계약 재검토

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- 공통 사주 include 참조와 실제 leaf 출력 의존성을 구분했습니다. 이 leaf의 현재 차단 원인은 개별 selector/분류 계약이며 공통 달력의 일괄 필수 의존을 주장하지 않습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_5.asp:30` — UNSE_TITLE = "행운번호운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름
- `old/unse/interlife/UNSE_DATA/solve/F/F019.asp:65` — T-023/T-024 실제 leaf 실행 계약 재검토

## 혈액형궁합 (interlife-free-6)

- 상태: ready · Python 계산·출력 선택키 완료 · AI 생성 설정 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-free-6
- 계산/부분 계산: POST /v1/un/interlife-free-6

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, interlife_calendar_classification_mansedata, interlife_solar_term_boundary_manse_data, conditional_leap_file_path. 원본 근거 줄은 sources에 보존합니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_6.asp:30` — UNSE_TITLE = "혈액형궁합"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 웰빙주택운 (interlife-free-7)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-free-7
- 계산/부분 계산: POST /v1/un/interlife-free-7

### interlife_month_branch_profile_unverified (confirmed)

원인: 원본 mansedata.month_e·number·jeolip의 일자/절입 의미가 미확보입니다. tb_manse raw 월지를 원본 my_month_e로 추정 대입하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- mansedata.month_e 원본 월지
- mansedata.number/jeolip 일자·2월 절입 분기 의미

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_7.asp:30` — UNSE_TITLE = "웰빙주택운"
- `old/unse/interlife/UNSE_DATA/solve/F/F012.asp:6` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_7.asp:30` — UNSE_TITLE = "웰빙주택운"
- `old/unse/interlife/UNSE_DATA/solve/F/F012.asp:6` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 바이오리듬 (interlife-free-8)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-free-8
- 계산/부분 계산: POST /v1/un/interlife-free-8

### interlife_serial_day_contract_unverified (confirmed)

원인: LunarToSolar.num 원본 세 조회값과 연속 일수 의미가 미확보입니다. 날짜 ordinal 또는 tb_manse.idx를 원본 num으로 대체하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- LunarToSolar.solar_date→num 원본 값과 num의 연속 일수 정의

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_8.asp:30` — UNSE_TITLE = "바이오리듬"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름
- `old/unse/interlife/UNSE_DATA/solve/F/F024.asp:50` — T-023/T-024 실제 leaf 실행 계약 재검토

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- 공통 사주 include 참조와 실제 leaf 출력 의존성을 구분했습니다. 이 leaf의 현재 차단 원인은 개별 selector/분류 계약이며 공통 달력의 일괄 필수 의존을 주장하지 않습니다.
- CR-012 / T-024: app.ported_interlife_dependencies의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/free/free_8.asp:30` — UNSE_TITLE = "바이오리듬"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름
- `old/unse/interlife/UNSE_DATA/solve/F/F024.asp:50` — T-023/T-024 실제 leaf 실행 계약 재검토

## 정통궁합(속궁합,겉궁합) (interlife-gunghap-1)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-1
- 계산/부분 계산: POST /v1/un/interlife-gunghap-1

### interlife_source_execution_unverified (confirmed)

원인: G022.db_data [old/unse/interlife/UNSE_DATA/solve/G/G022.asp:79; 호출 1] G024.result_var [old/unse/interlife/UNSE_DATA/solve/G/G024.asp:29; 호출 1] G024.result_var [old/unse/interlife/UNSE_DATA/solve/G/G024.asp:33; 호출 1] Y001.db_data [old/unse/interlife/UNSE_DATA/solve/Y/Y001.asp:7; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- G022.db_data [old/unse/interlife/UNSE_DATA/solve/G/G022.asp:79; 호출 1]
- G024.result_var [old/unse/interlife/UNSE_DATA/solve/G/G024.asp:29; 호출 1]
- G024.result_var [old/unse/interlife/UNSE_DATA/solve/G/G024.asp:33; 호출 1]
- Y001.db_data [old/unse/interlife/UNSE_DATA/solve/Y/Y001.asp:7; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_1.asp:30` — UNSE_TITLE = "정통궁합(속궁합,겉궁합)"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& your_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = '"& your_number &"'")
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_1.asp:30` — UNSE_TITLE = "정통궁합(속궁합,겉궁합)"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& your_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = '"& your_number &"'")
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 이성의 성격 (interlife-gunghap-10)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-10
- 계산/부분 계산: POST /v1/un/interlife-gunghap-10

### interlife_source_execution_unverified (confirmed)

원인: G005.db_data [old/unse/interlife/UNSE_DATA/solve/G/G005.asp:34; 호출 1] G007.db_data [old/unse/interlife/UNSE_DATA/solve/G/G007.asp:34; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] toC_yongsin_01.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_10.asp:78; 호출 1] toC_yongsin_01.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_10.asp:78; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- G005.db_data [old/unse/interlife/UNSE_DATA/solve/G/G005.asp:34; 호출 1]
- G007.db_data [old/unse/interlife/UNSE_DATA/solve/G/G007.asp:34; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- toC_yongsin_01.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_10.asp:78; 호출 1]
- toC_yongsin_01.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_10.asp:78; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_10.asp:30` — UNSE_TITLE = "이성의 성격"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_10.asp:78` — Set rs = ldb.execute("SELECT * FROM toC_yongsin_01 WHERE title = '"& my_day_h & my_month_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_10.asp:30` — UNSE_TITLE = "이성의 성격"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_10.asp:78` — Set rs = ldb.execute("SELECT * FROM toC_yongsin_01 WHERE title = '"& my_day_h & my_month_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 인연수1 (interlife-gunghap-11)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-11
- 계산/부분 계산: POST /v1/un/interlife-gunghap-11

### interlife_source_execution_unverified (confirmed)

원인: G005.db_data [old/unse/interlife/UNSE_DATA/solve/G/G005.asp:34; 호출 1] G033.ADO_getrows [old/unse/interlife/UNSE_DATA/solve/G/G033.asp:63; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] toC_yongsin_01.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_11.asp:78; 호출 1] toC_yongsin_01.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_11.asp:78; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- G005.db_data [old/unse/interlife/UNSE_DATA/solve/G/G005.asp:34; 호출 1]
- G033.ADO_getrows [old/unse/interlife/UNSE_DATA/solve/G/G033.asp:63; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- toC_yongsin_01.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_11.asp:78; 호출 1]
- toC_yongsin_01.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_11.asp:78; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_11.asp:30` — UNSE_TITLE = "인연수1"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:23` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"' or umyear_e = '"& s_umyear_e3 &"' or umyear_e = '"& s_umyear_e4 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:32` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:41` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:50` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:59` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:453` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:462` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:471` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:480` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:491` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"' or umyear_e = '"& s_umyear_e3 &"' or umyear_e = '"& s_umyear_e4 &"'"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_11.asp:78` — Set rs = ldb.execute("SELECT * FROM toC_yongsin_01 WHERE title = '"& my_day_h & my_month_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_11.asp:30` — UNSE_TITLE = "인연수1"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:23` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"' or umyear_e = '"& s_umyear_e3 &"' or umyear_e = '"& s_umyear_e4 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:32` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:41` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:50` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:59` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:453` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:462` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:471` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:480` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:491` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"' or umyear_e = '"& s_umyear_e3 &"' or umyear_e = '"& s_umyear_e4 &"'"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_11.asp:78` — Set rs = ldb.execute("SELECT * FROM toC_yongsin_01 WHERE title = '"& my_day_h & my_month_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 인연수2 (interlife-gunghap-12)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-12
- 계산/부분 계산: POST /v1/un/interlife-gunghap-12

### interlife_source_execution_unverified (confirmed)

원인: G005.db_data [old/unse/interlife/UNSE_DATA/solve/G/G005.asp:34; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] toC_manse_sub.ADO_getrows [old/unse/interlife/UNSE_DATA/solve/G/G034.asp:36; 호출 1] toC_yongsin_01.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_12.asp:78; 호출 1] toC_yongsin_01.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_12.asp:78; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- G005.db_data [old/unse/interlife/UNSE_DATA/solve/G/G005.asp:34; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- toC_manse_sub.ADO_getrows [old/unse/interlife/UNSE_DATA/solve/G/G034.asp:36; 호출 1]
- toC_yongsin_01.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_12.asp:78; 호출 1]
- toC_yongsin_01.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_12.asp:78; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_12.asp:30` — UNSE_TITLE = "인연수2"
- `old/unse/interlife/UNSE_DATA/solve/G/G034.asp:36` — Set rs = ldb.execute("SELECT umyear_h, umyear_e, no FROM toC_manse_sub WHERE umyear_e = '"& choice_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_12.asp:78` — Set rs = ldb.execute("SELECT * FROM toC_yongsin_01 WHERE title = '"& my_day_h & my_month_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_12.asp:30` — UNSE_TITLE = "인연수2"
- `old/unse/interlife/UNSE_DATA/solve/G/G034.asp:36` — Set rs = ldb.execute("SELECT umyear_h, umyear_e, no FROM toC_manse_sub WHERE umyear_e = '"& choice_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_12.asp:78` — Set rs = ldb.execute("SELECT * FROM toC_yongsin_01 WHERE title = '"& my_day_h & my_month_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 속궁합 (interlife-gunghap-13)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-13
- 계산/부분 계산: POST /v1/un/interlife-gunghap-13

### interlife_source_execution_unverified (confirmed)

원인: G016.db_data [old/unse/interlife/UNSE_DATA/solve/G/G016.asp:7; 호출 1] G016.db_numerical [old/unse/interlife/UNSE_DATA/solve/G/G016.asp:7; 호출 1] Y003.db_numerical [old/unse/interlife/UNSE_DATA/solve/Y/Y003.asp:13; 호출 1] Y003.result_var [old/unse/interlife/UNSE_DATA/solve/Y/Y003.asp:13; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- G016.db_data [old/unse/interlife/UNSE_DATA/solve/G/G016.asp:7; 호출 1]
- G016.db_numerical [old/unse/interlife/UNSE_DATA/solve/G/G016.asp:7; 호출 1]
- Y003.db_numerical [old/unse/interlife/UNSE_DATA/solve/Y/Y003.asp:13; 호출 1]
- Y003.result_var [old/unse/interlife/UNSE_DATA/solve/Y/Y003.asp:13; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_13.asp:30` — UNSE_TITLE = "속궁합"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/G/G016.asp:7` — set rs = ldb.execute("select DB_data, DB_numerical from G016 where DB_express = '"& woon12_daygi &"-"& y12woonsung &"'")
- `old/unse/interlife/UNSE_DATA/solve/Y/Y003.asp:13` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM Y003 WHERE DB_express like '"& my_day_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_13.asp:30` — UNSE_TITLE = "속궁합"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/G/G016.asp:7` — set rs = ldb.execute("select DB_data, DB_numerical from G016 where DB_express = '"& woon12_daygi &"-"& y12woonsung &"'")
- `old/unse/interlife/UNSE_DATA/solve/Y/Y003.asp:13` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM Y003 WHERE DB_express like '"& my_day_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 겉궁합 (interlife-gunghap-14)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-14
- 계산/부분 계산: POST /v1/un/interlife-gunghap-14

### interlife_source_execution_unverified (confirmed)

원인: S006.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S006.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S061.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1] S061.result_var [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1] Y001.db_data [old/unse/interlife/UNSE_DATA/solve/Y/Y001.asp:7; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S006.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S006.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S061.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1]
- S061.result_var [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1]
- Y001.db_data [old/unse/interlife/UNSE_DATA/solve/Y/Y001.asp:7; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_14.asp:30` — UNSE_TITLE = "겉궁합"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& your_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = '"& your_number &"'")
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM S061 WHERE DB_express = '"& total_11 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_14.asp:30` — UNSE_TITLE = "겉궁합"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& your_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = '"& your_number &"'")
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM S061 WHERE DB_express = '"& total_11 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 애정운 (interlife-gunghap-15)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-15
- 계산/부분 계산: POST /v1/un/interlife-gunghap-15

### interlife_source_execution_unverified (confirmed)

원인: S081.result_var [old/unse/interlife/UNSE_DATA/solve/S/S081.asp:13; 호출 1] mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/solve/S_S094_S101_sol.asp:5; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/solve/S_S094_S101_sol.asp:5; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_15.asp:67; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_15.asp:67; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S081.result_var [old/unse/interlife/UNSE_DATA/solve/S/S081.asp:13; 호출 1]
- mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/solve/S_S094_S101_sol.asp:5; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/solve/S_S094_S101_sol.asp:5; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_15.asp:67; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_15.asp:67; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_15.asp:30` — UNSE_TITLE = "애정운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S_S094_S101_sol.asp:5` — Set rs = ldb.execute("select year_h from mansedata where no = '"& Replace(Date, "-", "") &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_15.asp:67` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_15.asp:30` — UNSE_TITLE = "애정운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S_S094_S101_sol.asp:5` — Set rs = ldb.execute("select year_h from mansedata where no = '"& Replace(Date, "-", "") &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_15.asp:67` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 부부화합운 (interlife-gunghap-16)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-16
- 계산/부분 계산: POST /v1/un/interlife-gunghap-16

### interlife_source_execution_unverified (confirmed)

원인: G001.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] G001.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S053.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S053.asp:87; 호출 1] S053.result_var [old/unse/interlife/UNSE_DATA/solve/S/S053.asp:87; 호출 1] S054.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1] S054.db_title [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1] S054.result_var [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1] S056.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1] S056.db_title [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1] S056.result_var [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- G001.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- G001.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S053.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S053.asp:87; 호출 1]
- S053.result_var [old/unse/interlife/UNSE_DATA/solve/S/S053.asp:87; 호출 1]
- S054.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1]
- S054.db_title [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1]
- S054.result_var [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1]
- S056.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1]
- S056.db_title [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1]
- S056.result_var [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_16.asp:30` — UNSE_TITLE = "부부화합운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& your_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = '"& your_number &"'")
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S053.asp:87` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM S053 WHERE DB_express = '"& total_08 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116` — Set rs = ldb.execute("SELECT DB_title, DB_data, "& choie_data &" as result_var, DB_numerical FROM S054 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116` — Set rs = ldb.execute("SELECT DB_title, DB_data, "& choie_data &" as result_var, DB_numerical FROM S056 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_16.asp:30` — UNSE_TITLE = "부부화합운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& your_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = '"& your_number &"'")
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S053.asp:87` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM S053 WHERE DB_express = '"& total_08 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116` — Set rs = ldb.execute("SELECT DB_title, DB_data, "& choie_data &" as result_var, DB_numerical FROM S054 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116` — Set rs = ldb.execute("SELECT DB_title, DB_data, "& choie_data &" as result_var, DB_numerical FROM S056 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 섹스운 (interlife-gunghap-17)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-17
- 계산/부분 계산: POST /v1/un/interlife-gunghap-17

### interlife_source_execution_unverified (confirmed)

원인: S054.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1] S054.db_title [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1] S054.result_var [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1] S061.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1] S061.result_var [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S054.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1]
- S054.db_title [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1]
- S054.result_var [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1]
- S061.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1]
- S061.result_var [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_17.asp:30` — UNSE_TITLE = "섹스운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116` — Set rs = ldb.execute("SELECT DB_title, DB_data, "& choie_data &" as result_var, DB_numerical FROM S054 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM S061 WHERE DB_express = '"& total_11 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_17.asp:30` — UNSE_TITLE = "섹스운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116` — Set rs = ldb.execute("SELECT DB_title, DB_data, "& choie_data &" as result_var, DB_numerical FROM S054 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM S061 WHERE DB_express = '"& total_11 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 천생복덕운 (interlife-gunghap-18)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-18
- 계산/부분 계산: POST /v1/un/interlife-gunghap-18

### interlife_source_execution_unverified (confirmed)

원인: S049.db_title [old/unse/interlife/UNSE_DATA/solve/S/S049.asp:106; 호출 1] S057.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S057.asp:114; 호출 1] S057.db_title [old/unse/interlife/UNSE_DATA/solve/S/S057.asp:114; 호출 1] S058.db_title [old/unse/interlife/UNSE_DATA/solve/S/S058.asp:112; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S049.db_title [old/unse/interlife/UNSE_DATA/solve/S/S049.asp:106; 호출 1]
- S057.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S057.asp:114; 호출 1]
- S057.db_title [old/unse/interlife/UNSE_DATA/solve/S/S057.asp:114; 호출 1]
- S058.db_title [old/unse/interlife/UNSE_DATA/solve/S/S058.asp:112; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_18.asp:30` — UNSE_TITLE = "천생복덕운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S057.asp:114` — Set rs = ldb.execute("SELECT DB_title, DB_data, DB_numerical FROM S057 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_18.asp:30` — UNSE_TITLE = "천생복덕운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S057.asp:114` — Set rs = ldb.execute("SELECT DB_title, DB_data, DB_numerical FROM S057 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 사상체질궁합 (interlife-gunghap-2)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-2
- 계산/부분 계산: POST /v1/un/interlife-gunghap-2

### interlife_source_execution_unverified (confirmed)

원인: S056.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1] S056.db_title [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1] S056.result_var [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1] T024.result_var [old/unse/interlife/UNSE_DATA/solve/T/T024.asp:17; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:142; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:67; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:142; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:67; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.no [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:250; 호출 1] mansedata.umdate [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:250; 호출 1] mansedata.umyear_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:250; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S056.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1]
- S056.db_title [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1]
- S056.result_var [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1]
- T024.result_var [old/unse/interlife/UNSE_DATA/solve/T/T024.asp:17; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:142; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:67; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:142; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:67; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.no [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:250; 호출 1]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:250; 호출 1]
- mansedata.umyear_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:250; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:30` — UNSE_TITLE = "사상체질궁합"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& your_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = '"& your_number &"'")
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:67` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:142` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:250` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like  '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:9793` — sql = "SELECT * FROM mansedata WHERE umdate like  '"& cc &"'"
- `old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116` — Set rs = ldb.execute("SELECT DB_title, DB_data, "& choie_data &" as result_var, DB_numerical FROM S056 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:30` — UNSE_TITLE = "사상체질궁합"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& your_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = '"& your_number &"'")
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:67` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:142` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:250` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like  '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_2.asp:9793` — sql = "SELECT * FROM mansedata WHERE umdate like  '"& cc &"'"
- `old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116` — Set rs = ldb.execute("SELECT DB_title, DB_data, "& choie_data &" as result_var, DB_numerical FROM S056 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 용신으로 보는 연인애정운 (interlife-gunghap-3)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-3
- 계산/부분 계산: POST /v1/un/interlife-gunghap-3

### interlife_source_execution_unverified (confirmed)

원인: G033.ADO_getrows [old/unse/interlife/UNSE_DATA/solve/G/G033.asp:63; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] toC_manse_sub.ADO_getrows [old/unse/interlife/UNSE_DATA/solve/G/G034.asp:36; 호출 1] toC_yongsin_01.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_3.asp:78; 호출 1] toC_yongsin_01.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_3.asp:78; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- G033.ADO_getrows [old/unse/interlife/UNSE_DATA/solve/G/G033.asp:63; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- toC_manse_sub.ADO_getrows [old/unse/interlife/UNSE_DATA/solve/G/G034.asp:36; 호출 1]
- toC_yongsin_01.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_3.asp:78; 호출 1]
- toC_yongsin_01.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_3.asp:78; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_3.asp:30` — UNSE_TITLE = "용신으로 보는 연인애정운"
- `old/unse/interlife/UNSE_DATA/solve/G/G034.asp:36` — Set rs = ldb.execute("SELECT umyear_h, umyear_e, no FROM toC_manse_sub WHERE umyear_e = '"& choice_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:23` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"' or umyear_e = '"& s_umyear_e3 &"' or umyear_e = '"& s_umyear_e4 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:32` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:41` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:50` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:59` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:453` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:462` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:471` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:480` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:491` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"' or umyear_e = '"& s_umyear_e3 &"' or umyear_e = '"& s_umyear_e4 &"'"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_3.asp:78` — Set rs = ldb.execute("SELECT * FROM toC_yongsin_01 WHERE title = '"& my_day_h & my_month_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_3.asp:30` — UNSE_TITLE = "용신으로 보는 연인애정운"
- `old/unse/interlife/UNSE_DATA/solve/G/G034.asp:36` — Set rs = ldb.execute("SELECT umyear_h, umyear_e, no FROM toC_manse_sub WHERE umyear_e = '"& choice_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:23` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"' or umyear_e = '"& s_umyear_e3 &"' or umyear_e = '"& s_umyear_e4 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:32` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:41` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:50` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:59` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:453` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:462` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:471` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:480` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:491` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"' or umyear_e = '"& s_umyear_e3 &"' or umyear_e = '"& s_umyear_e4 &"'"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_3.asp:78` — Set rs = ldb.execute("SELECT * FROM toC_yongsin_01 WHERE title = '"& my_day_h & my_month_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 그이의 러브스타일 보기 (interlife-gunghap-4)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-4
- 계산/부분 계산: POST /v1/un/interlife-gunghap-4

### interlife_source_execution_unverified (confirmed)

원인: G003.db_numerical [old/unse/interlife/UNSE_DATA/solve/G/G003.asp:16; 호출 1] S081.result_var [old/unse/interlife/UNSE_DATA/solve/S/S081.asp:13; 호출 1] Y001.db_data [old/unse/interlife/UNSE_DATA/solve/Y/Y001.asp:7; 호출 1] Y003.db_numerical [old/unse/interlife/UNSE_DATA/solve/Y/Y003.asp:13; 호출 1] Y003.result_var [old/unse/interlife/UNSE_DATA/solve/Y/Y003.asp:13; 호출 1] mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:171; 호출 1] mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:273; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:171; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:273; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:135; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:135; 호출 1] mansedata.umdate [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:78; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:90; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:90; 호출 1] source_policy.source_terms_required tojung_gabja.il [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:257; 호출 1] tojung_gabja.tae [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:249; 호출 1] tojung_gabja.wol [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:253; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- G003.db_numerical [old/unse/interlife/UNSE_DATA/solve/G/G003.asp:16; 호출 1]
- S081.result_var [old/unse/interlife/UNSE_DATA/solve/S/S081.asp:13; 호출 1]
- Y001.db_data [old/unse/interlife/UNSE_DATA/solve/Y/Y001.asp:7; 호출 1]
- Y003.db_numerical [old/unse/interlife/UNSE_DATA/solve/Y/Y003.asp:13; 호출 1]
- Y003.result_var [old/unse/interlife/UNSE_DATA/solve/Y/Y003.asp:13; 호출 1]
- mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:171; 호출 1]
- mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:273; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:171; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:273; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:135; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:135; 호출 1]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:78; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:90; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:90; 호출 1]
- source_policy.source_terms_required
- tojung_gabja.il [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:257; 호출 1]
- tojung_gabja.tae [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:249; 호출 1]
- tojung_gabja.wol [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:253; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:30` — UNSE_TITLE = "그이의 러브스타일 보기"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:78` — Set rs = ldb.execute("SELECT umdate FROM mansedata WHERE no = '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:90` — Set rs = ldb.execute("SELECT year_h, year_e FROM mansedata WHERE umdate = '"& current_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:135` — Set rs = ldb.execute("SELECT month_h, month_e FROM mansedata WHERE umdate = '"& see_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:171` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:185` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate_kk &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:273` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE umdate = '"& um_y_m_d &"'")
- `old/unse/interlife/UNSE_DATA/solve/G/G003.asp:16` — Set rs = ldb.execute("select DB_data, DB_numerical from G003 where DB_express = '"& serial_no &"'")
- `old/unse/interlife/UNSE_DATA/solve/Y/Y003.asp:13` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM Y003 WHERE DB_express like '"& my_day_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:249` — Set rs = ldb.execute("SELECT tae FROM tojung_gabja WHERE gabja = '"& result_year &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:253` — Set rs = ldb.execute("SELECT wol FROM tojung_gabja WHERE gabja = '"& result_month &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:257` — Set rs = ldb.execute("SELECT il FROM tojung_gabja WHERE gabja = '"& result_day &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:30` — UNSE_TITLE = "그이의 러브스타일 보기"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:78` — Set rs = ldb.execute("SELECT umdate FROM mansedata WHERE no = '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:90` — Set rs = ldb.execute("SELECT year_h, year_e FROM mansedata WHERE umdate = '"& current_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:135` — Set rs = ldb.execute("SELECT month_h, month_e FROM mansedata WHERE umdate = '"& see_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:171` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:185` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate_kk &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:273` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE umdate = '"& um_y_m_d &"'")
- `old/unse/interlife/UNSE_DATA/solve/G/G003.asp:16` — Set rs = ldb.execute("select DB_data, DB_numerical from G003 where DB_express = '"& serial_no &"'")
- `old/unse/interlife/UNSE_DATA/solve/Y/Y003.asp:13` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM Y003 WHERE DB_express like '"& my_day_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:249` — Set rs = ldb.execute("SELECT tae FROM tojung_gabja WHERE gabja = '"& result_year &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:253` — Set rs = ldb.execute("SELECT wol FROM tojung_gabja WHERE gabja = '"& result_month &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_4.asp:257` — Set rs = ldb.execute("SELECT il FROM tojung_gabja WHERE gabja = '"& result_day &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 섹스 토정비결 (interlife-gunghap-5)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-5
- 계산/부분 계산: POST /v1/un/interlife-gunghap-5

### interlife_source_execution_unverified (confirmed)

원인: S006.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S006.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S061.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1] S061.result_var [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1] Y001.db_data [old/unse/interlife/UNSE_DATA/solve/Y/Y001.asp:7; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S006.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S006.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S061.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1]
- S061.result_var [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1]
- Y001.db_data [old/unse/interlife/UNSE_DATA/solve/Y/Y001.asp:7; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_5.asp:30` — UNSE_TITLE = "섹스 토정비결"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM S061 WHERE DB_express = '"& total_11 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_5.asp:30` — UNSE_TITLE = "섹스 토정비결"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM S061 WHERE DB_express = '"& total_11 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 침실 섹스궁합 (interlife-gunghap-6)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-6
- 계산/부분 계산: POST /v1/un/interlife-gunghap-6

### interlife_source_execution_unverified (confirmed)

원인: G020.db_data_m [old/unse/interlife/UNSE_DATA/solve/G/G020.asp:16; 호출 1] G020.db_data_w [old/unse/interlife/UNSE_DATA/solve/G/G020.asp:21; 호출 1] G020.db_numerical [old/unse/interlife/UNSE_DATA/solve/G/G020.asp:16; 호출 1] S081.result_var [old/unse/interlife/UNSE_DATA/solve/S/S081.asp:13; 호출 1] mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:171; 호출 1] mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:273; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:171; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:273; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:135; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:135; 호출 1] mansedata.umdate [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:78; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:90; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:90; 호출 1] tojung_gabja.il [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:257; 호출 1] tojung_gabja.tae [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:249; 호출 1] tojung_gabja.wol [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:253; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- G020.db_data_m [old/unse/interlife/UNSE_DATA/solve/G/G020.asp:16; 호출 1]
- G020.db_data_w [old/unse/interlife/UNSE_DATA/solve/G/G020.asp:21; 호출 1]
- G020.db_numerical [old/unse/interlife/UNSE_DATA/solve/G/G020.asp:16; 호출 1]
- S081.result_var [old/unse/interlife/UNSE_DATA/solve/S/S081.asp:13; 호출 1]
- mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:171; 호출 1]
- mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:273; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:171; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:273; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:135; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:135; 호출 1]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:78; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:90; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:90; 호출 1]
- tojung_gabja.il [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:257; 호출 1]
- tojung_gabja.tae [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:249; 호출 1]
- tojung_gabja.wol [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:253; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:30` — UNSE_TITLE = "침실 섹스궁합"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& your_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = '"& your_number &"'")
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:78` — Set rs = ldb.execute("SELECT umdate FROM mansedata WHERE no = '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:90` — Set rs = ldb.execute("SELECT year_h, year_e FROM mansedata WHERE umdate = '"& current_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:135` — Set rs = ldb.execute("SELECT month_h, month_e FROM mansedata WHERE umdate = '"& see_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:171` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:185` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate_kk &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:273` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE umdate = '"& um_y_m_d &"'")
- `old/unse/interlife/UNSE_DATA/solve/G/G020.asp:16` — Set rs = ldb.execute("SELECT DB_data_m, DB_numerical FROM G020 WHERE DB_express = '"& F_gabza_str(result_man) &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:249` — Set rs = ldb.execute("SELECT tae FROM tojung_gabja WHERE gabja = '"& result_year &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:253` — Set rs = ldb.execute("SELECT wol FROM tojung_gabja WHERE gabja = '"& result_month &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:257` — Set rs = ldb.execute("SELECT il FROM tojung_gabja WHERE gabja = '"& result_day &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:30` — UNSE_TITLE = "침실 섹스궁합"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& your_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = '"& your_number &"'")
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:78` — Set rs = ldb.execute("SELECT umdate FROM mansedata WHERE no = '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:90` — Set rs = ldb.execute("SELECT year_h, year_e FROM mansedata WHERE umdate = '"& current_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:135` — Set rs = ldb.execute("SELECT month_h, month_e FROM mansedata WHERE umdate = '"& see_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:171` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:185` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate_kk &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:273` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE umdate = '"& um_y_m_d &"'")
- `old/unse/interlife/UNSE_DATA/solve/G/G020.asp:16` — Set rs = ldb.execute("SELECT DB_data_m, DB_numerical FROM G020 WHERE DB_express = '"& F_gabza_str(result_man) &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:249` — Set rs = ldb.execute("SELECT tae FROM tojung_gabja WHERE gabja = '"& result_year &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:253` — Set rs = ldb.execute("SELECT wol FROM tojung_gabja WHERE gabja = '"& result_month &"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_6.asp:257` — Set rs = ldb.execute("SELECT il FROM tojung_gabja WHERE gabja = '"& result_day &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 결혼배필운 (interlife-gunghap-7)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-7
- 계산/부분 계산: POST /v1/un/interlife-gunghap-7

### interlife_source_execution_unverified (confirmed)

원인: G005.db_data [old/unse/interlife/UNSE_DATA/solve/G/G005.asp:34; 호출 1] S061.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1] S061.result_var [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- G005.db_data [old/unse/interlife/UNSE_DATA/solve/G/G005.asp:34; 호출 1]
- S061.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1]
- S061.result_var [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_7.asp:30` — UNSE_TITLE = "결혼배필운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM S061 WHERE DB_express = '"& total_11 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_7.asp:30` — UNSE_TITLE = "결혼배필운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM S061 WHERE DB_express = '"& total_11 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 인연은 몇 명 (interlife-gunghap-8)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-8
- 계산/부분 계산: POST /v1/un/interlife-gunghap-8

### interlife_source_execution_unverified (confirmed)

원인: G005.db_data [old/unse/interlife/UNSE_DATA/solve/G/G005.asp:34; 호출 1] G012.db_numerical [old/unse/interlife/UNSE_DATA/solve/G/G012.asp:9; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required toC_yongsin_01.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_8.asp:78; 호출 1] toC_yongsin_01.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_8.asp:78; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- G005.db_data [old/unse/interlife/UNSE_DATA/solve/G/G005.asp:34; 호출 1]
- G012.db_numerical [old/unse/interlife/UNSE_DATA/solve/G/G012.asp:9; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required
- toC_yongsin_01.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_8.asp:78; 호출 1]
- toC_yongsin_01.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_8.asp:78; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_8.asp:30` — UNSE_TITLE = "인연은 몇 명"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/G/G012.asp:9` — set rs = ldb.execute("select DB_data, DB_numerical from G012 where DB_express = '"& serial_no &"'")		'올해연분매칭포인트
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_8.asp:78` — Set rs = ldb.execute("SELECT * FROM toC_yongsin_01 WHERE title = '"& my_day_h & my_month_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_8.asp:30` — UNSE_TITLE = "인연은 몇 명"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/G/G012.asp:9` — set rs = ldb.execute("select DB_data, DB_numerical from G012 where DB_express = '"& serial_no &"'")		'올해연분매칭포인트
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_8.asp:78` — Set rs = ldb.execute("SELECT * FROM toC_yongsin_01 WHERE title = '"& my_day_h & my_month_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 애인부부운 (interlife-gunghap-9)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-gunghap-9
- 계산/부분 계산: POST /v1/un/interlife-gunghap-9

### interlife_source_execution_unverified (confirmed)

원인: G005.db_data [old/unse/interlife/UNSE_DATA/solve/G/G005.asp:34; 호출 1] G007.db_data [old/unse/interlife/UNSE_DATA/solve/G/G007.asp:34; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] toC_yongsin_01.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_9.asp:78; 호출 1] toC_yongsin_01.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_9.asp:78; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- G005.db_data [old/unse/interlife/UNSE_DATA/solve/G/G005.asp:34; 호출 1]
- G007.db_data [old/unse/interlife/UNSE_DATA/solve/G/G007.asp:34; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- toC_yongsin_01.ADO_bof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_9.asp:78; 호출 1]
- toC_yongsin_01.ADO_eof [old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_9.asp:78; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_9.asp:30` — UNSE_TITLE = "애인부부운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_9.asp:78` — Set rs = ldb.execute("SELECT * FROM toC_yongsin_01 WHERE title = '"& my_day_h & my_month_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_9.asp:30` — UNSE_TITLE = "애인부부운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/gunghap/gunghap_9.asp:78` — Set rs = ldb.execute("SELECT * FROM toC_yongsin_01 WHERE title = '"& my_day_h & my_month_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 자미두수 (interlife-jum-1)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-1
- 계산/부분 계산: POST /v1/un/interlife-jum-1

### interlife_ziwei_array_profile_unverified (confirmed)

원인: source_ziwei_birth_required: 원본 연간지와 음력 월일 또는 실제 출생일·선택 번호 행이 필요합니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- source_ziwei_birth.{year_h,year_e,lunar_year,lunar_month,lunar_day} 또는 원본 출생 선택 행의 연간지/기본 음력 날짜
- source_current_record.{no,umdate,umyear_h?,umyear_e}

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_1.asp:15` — UNSE_TITLE = "자미두수"
- `old/unse/interlife/UNSE_DATA/unse/jum/jum_1.asp:11` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/S_J017_J030_sol.asp:48` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like  '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_J017_J030_sol.asp:9591` — sql = "SELECT * FROM mansedata WHERE umdate like  '"& cc &"'"
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_chart의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_1.asp:15` — UNSE_TITLE = "자미두수"
- `old/unse/interlife/UNSE_DATA/unse/jum/jum_1.asp:11` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/S_J017_J030_sol.asp:48` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like  '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_J017_J030_sol.asp:9591` — sql = "SELECT * FROM mansedata WHERE umdate like  '"& cc &"'"
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 질병건강운 (interlife-jum-10)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-10
- 계산/부분 계산: POST /v1/un/interlife-jum-10

### interlife_source_execution_unverified (confirmed)

원인: S021.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S021.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S083.result_var [old/unse/interlife/UNSE_DATA/solve/S/S083.asp:16; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S021.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S021.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S083.result_var [old/unse/interlife/UNSE_DATA/solve/S/S083.asp:16; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_10.asp:30` — UNSE_TITLE = "질병건강운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_10.asp:30` — UNSE_TITLE = "질병건강운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 주거가택운 (interlife-jum-11)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-11
- 계산/부분 계산: POST /v1/un/interlife-jum-11

### interlife_source_execution_unverified (confirmed)

원인: J048.db_data [old/unse/interlife/UNSE_DATA/solve/J/J048.asp:11; 호출 1] T034.db_data [old/unse/interlife/UNSE_DATA/solve/T/T034.asp:14; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- J048.db_data [old/unse/interlife/UNSE_DATA/solve/J/J048.asp:11; 호출 1]
- T034.db_data [old/unse/interlife/UNSE_DATA/solve/T/T034.asp:14; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_11.asp:30` — UNSE_TITLE = "주거가택운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_11.asp:30` — UNSE_TITLE = "주거가택운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 사업합작운 (interlife-jum-12)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-12
- 계산/부분 계산: POST /v1/un/interlife-jum-12

### interlife_source_execution_unverified (confirmed)

원인: N010.db_data [old/unse/interlife/UNSE_DATA/solve/N/N010.asp:7; 호출 1] N010.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N010.asp:7; 호출 1] S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] source_policy.source_terms_required surioheng.bal [old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:77; 호출 1] surioheng.bal [old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:91; 호출 1] surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:77; 호출 1] surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:91; 호출 1] surioheng.su [old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:77; 호출 1] surioheng.su [old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:91; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- N010.db_data [old/unse/interlife/UNSE_DATA/solve/N/N010.asp:7; 호출 1]
- N010.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N010.asp:7; 호출 1]
- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- source_policy.source_terms_required
- surioheng.bal [old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:77; 호출 1]
- surioheng.bal [old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:91; 호출 1]
- surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:77; 호출 1]
- surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:91; 호출 1]
- surioheng.su [old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:77; 호출 1]
- surioheng.su [old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:91; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:30` — UNSE_TITLE = "사업합작운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/N/N010.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N010 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:77` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& msung &"'")
- `old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:91` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& ysung &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:30` — UNSE_TITLE = "사업합작운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/N/N010.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N010 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:77` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& msung &"'")
- `old/unse/interlife/UNSE_DATA/unse/jum/jum_12.asp:91` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& ysung &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 직장상사운 (interlife-jum-13)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-13
- 계산/부분 계산: POST /v1/un/interlife-jum-13

### interlife_source_execution_unverified (confirmed)

원인: N011.db_data [old/unse/interlife/UNSE_DATA/solve/N/N011.asp:7; 호출 1] N011.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N011.asp:7; 호출 1] S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] surioheng.bal [old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:77; 호출 1] surioheng.bal [old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:91; 호출 1] surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:77; 호출 1] surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:91; 호출 1] surioheng.su [old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:77; 호출 1] surioheng.su [old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:91; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- N011.db_data [old/unse/interlife/UNSE_DATA/solve/N/N011.asp:7; 호출 1]
- N011.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N011.asp:7; 호출 1]
- S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- surioheng.bal [old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:77; 호출 1]
- surioheng.bal [old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:91; 호출 1]
- surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:77; 호출 1]
- surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:91; 호출 1]
- surioheng.su [old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:77; 호출 1]
- surioheng.su [old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:91; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:30` — UNSE_TITLE = "직장상사운"
- `old/xmlpath/unse.xml:132` — unsekind txt
- `old/js/unseform.js:87` — CID actionurl dispatch
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/N/N011.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N011 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:77` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& msung &"'")
- `old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:91` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& ysung &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:30` — UNSE_TITLE = "직장상사운"
- `old/xmlpath/unse.xml:132` — unsekind txt
- `old/js/unseform.js:87` — CID actionurl dispatch
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/N/N011.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N011 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:77` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& msung &"'")
- `old/unse/interlife/UNSE_DATA/unse/jum/jum_13.asp:91` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& ysung &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 직장부하운 (interlife-jum-14)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-14
- 계산/부분 계산: POST /v1/un/interlife-jum-14

### interlife_source_execution_unverified (confirmed)

원인: N012.db_data [old/unse/interlife/UNSE_DATA/solve/N/N012.asp:7; 호출 1] N012.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N012.asp:7; 호출 1] S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] surioheng.bal [old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:77; 호출 1] surioheng.bal [old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:91; 호출 1] surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:77; 호출 1] surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:91; 호출 1] surioheng.su [old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:77; 호출 1] surioheng.su [old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:91; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- N012.db_data [old/unse/interlife/UNSE_DATA/solve/N/N012.asp:7; 호출 1]
- N012.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N012.asp:7; 호출 1]
- S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- surioheng.bal [old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:77; 호출 1]
- surioheng.bal [old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:91; 호출 1]
- surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:77; 호출 1]
- surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:91; 호출 1]
- surioheng.su [old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:77; 호출 1]
- surioheng.su [old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:91; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:30` — UNSE_TITLE = "직장부하운"
- `old/xmlpath/unse.xml:142` — unsekind txt
- `old/js/unseform.js:92` — CID actionurl dispatch
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/N/N012.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N012 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:77` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& msung &"'")
- `old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:91` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& ysung &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름
- `old/sub/writeform/form8.asp:23` — cid 입력; 서비스 sel/urlinfo 전달 확인 필요
- `old/unse/interlife/x2_write.asp:471` — 직장부하운 유료 pkind→jum/14 매핑
- `old/unse/interlife/x2_write.asp:538` — 일반 입력 sel=request(sel)

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:30` — UNSE_TITLE = "직장부하운"
- `old/xmlpath/unse.xml:142` — unsekind txt
- `old/js/unseform.js:92` — CID actionurl dispatch
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/N/N012.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N012 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:77` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& msung &"'")
- `old/unse/interlife/UNSE_DATA/unse/jum/jum_14.asp:91` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& ysung &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름
- `old/sub/writeform/form8.asp:23` — cid 입력; 서비스 sel/urlinfo 전달 확인 필요
- `old/unse/interlife/x2_write.asp:471` — 직장부하운 유료 pkind→jum/14 매핑
- `old/unse/interlife/x2_write.asp:538` — 일반 입력 sel=request(sel)

## 육임단시 (interlife-jum-15)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-15
- 계산/부분 계산: POST /v1/un/interlife-jum-15

### interlife_source_execution_unverified (confirmed)

원인: S016.0 [old/unse/interlife/UNSE_DATA/solve/S/S016.asp:46; 호출 1] S016.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S016.asp:46; 호출 1] S058.db_title [old/unse/interlife/UNSE_DATA/solve/S/S058.asp:112; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S016.0 [old/unse/interlife/UNSE_DATA/solve/S/S016.asp:46; 호출 1]
- S016.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S016.asp:46; 호출 1]
- S058.db_title [old/unse/interlife/UNSE_DATA/solve/S/S058.asp:112; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_15.asp:30` — UNSE_TITLE = "육임단시"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S016.asp:46` — set rs = ldb.execute("select DB_data, DB_numerical from S016 where DB_express = '"& dan5 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_15.asp:30` — UNSE_TITLE = "육임단시"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S016.asp:46` — set rs = ldb.execute("select DB_data, DB_numerical from S016 where DB_express = '"& dan5 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 64괘 운세분석 (interlife-jum-16)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-16
- 계산/부분 계산: POST /v1/un/interlife-jum-16

### interlife_hexagram_state_contract_unverified (confirmed)

원인: J033.DB_title의 실제 괘명·도식 자료가 없어 괘 이름과 원본 해설 대상을 확정할 수 없습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- J033.DB_title 실제 괘명·도식

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_16.asp:30` — UNSE_TITLE = "64괘 운세분석"
- `old/unse/interlife/UNSE_DATA/solve/J/J015.asp:6` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_16.asp:30` — UNSE_TITLE = "64괘 운세분석"
- `old/unse/interlife/UNSE_DATA/solve/J/J015.asp:6` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 주역점 (interlife-jum-2)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-2
- 계산/부분 계산: POST /v1/un/interlife-jum-2

### interlife_indirect_numeric_score_missing (confirmed)

원인: J033.DB_title의 실제 괘명·도식 자료가 없어 괘 이름과 원본 해설 대상을 확정할 수 없습니다. S007→F_dang4_6_db와 S008/S006/S005/S002→F_woonday의 실제 DB_numerical 값이 미확보이며 source 사주/서버 월·일 코드의 원본 의미도 검증해야 합니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- J033.DB_title 실제 괘명·도식
- S008.DB_data 실제 행운색상
- S002/S005/S006/S007/S008.DB_numerical 실제 점수
- 원본 f_Saju·서버 년월일 코드 매핑

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_2.asp:64` — UNSE_TITLE = "주역점"
- `old/unse/interlife/UNSE_DATA/solve/S/S007.asp:10` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_dependencies의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_2.asp:64` — UNSE_TITLE = "주역점"
- `old/unse/interlife/UNSE_DATA/solve/S/S007.asp:10` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 주역신수비결 (interlife-jum-3)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-3
- 계산/부분 계산: POST /v1/un/interlife-jum-3

### interlife_source_execution_unverified (confirmed)

원인: S027.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S027.asp:11; 호출 1] S082.result_var [old/unse/interlife/UNSE_DATA/solve/S/S082.asp:15; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S027.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S027.asp:11; 호출 1]
- S082.result_var [old/unse/interlife/UNSE_DATA/solve/S/S082.asp:15; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_3.asp:30` — UNSE_TITLE = "주역신수비결"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S027.asp:11` — set rs = ldb.execute("select DB_data, DB_numerical from S027 where DB_express = '"& serial_no &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_3.asp:30` — UNSE_TITLE = "주역신수비결"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S027.asp:11` — set rs = ldb.execute("select DB_data, DB_numerical from S027 where DB_express = '"& serial_no &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 영험한 첨 (interlife-jum-4)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-4
- 계산/부분 계산: POST /v1/un/interlife-jum-4

### interlife_source_execution_unverified (confirmed)

원인: J036.db_title [old/unse/interlife/UNSE_DATA/solve/J/J036.asp:12; 호출 1] J036.db_title_1 [old/unse/interlife/UNSE_DATA/solve/J/J036.asp:12; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- J036.db_title [old/unse/interlife/UNSE_DATA/solve/J/J036.asp:12; 호출 1]
- J036.db_title_1 [old/unse/interlife/UNSE_DATA/solve/J/J036.asp:12; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_4.asp:30` — UNSE_TITLE = "영험한 첨"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_4.asp:30` — UNSE_TITLE = "영험한 첨"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 단시점 (interlife-jum-5)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-5
- 계산/부분 계산: POST /v1/un/interlife-jum-5

### interlife_source_execution_unverified (confirmed)

원인: J050.db_data [old/unse/interlife/UNSE_DATA/solve/J/J050.asp:95; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/J/J050.asp:39; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- J050.db_data [old/unse/interlife/UNSE_DATA/solve/J/J050.asp:95; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/J/J050.asp:39; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_5.asp:30` — UNSE_TITLE = "단시점"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/J/J050.asp:39` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like  '"& no &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_5.asp:30` — UNSE_TITLE = "단시점"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/J/J050.asp:39` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like  '"& no &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 육효 (interlife-jum-6)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-6
- 계산/부분 계산: POST /v1/un/interlife-jum-6

### interlife_source_execution_unverified (confirmed)

원인: J051.db_data [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:19; 호출 1] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] juyek_6hyo.gung [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:284; 호출 1] juyek_6hyo.gung [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:321; 호출 1] juyek_6hyo.hapchung [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:284; 호출 1] juyek_6hyo.hapchung [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:321; 호출 1] juyek_6hyo.sehyo [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:284; 호출 1] juyek_6hyo.title [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:284; 호출 1] juyek_6hyo.title [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:321; 호출 1] manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:61; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:61; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:61; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:61; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:61; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:61; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- J051.db_data [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:19; 호출 1]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- juyek_6hyo.gung [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:284; 호출 1]
- juyek_6hyo.gung [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:321; 호출 1]
- juyek_6hyo.hapchung [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:284; 호출 1]
- juyek_6hyo.hapchung [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:321; 호출 1]
- juyek_6hyo.sehyo [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:284; 호출 1]
- juyek_6hyo.title [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:284; 호출 1]
- juyek_6hyo.title [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:321; 호출 1]
- manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:61; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:61; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:61; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:61; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:61; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/J/J051.asp:61; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_6.asp:64` — UNSE_TITLE = "육효"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/J/J051.asp:61` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like '"& no &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/J/J051.asp:284` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/J/J051.asp:321` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_6.asp:64` — UNSE_TITLE = "육효"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/J/J051.asp:61` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like '"& no &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/J/J051.asp:284` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/J/J051.asp:321` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 자식운 (interlife-jum-7)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-7
- 계산/부분 계산: POST /v1/un/interlife-jum-7

### interlife_source_execution_unverified (confirmed)

원인: mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_7.asp:30` — UNSE_TITLE = "자식운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_7.asp:30` — UNSE_TITLE = "자식운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 형제운 (interlife-jum-8)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-8
- 계산/부분 계산: POST /v1/un/interlife-jum-8

### interlife_source_execution_unverified (confirmed)

원인: S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_8.asp:30` — UNSE_TITLE = "형제운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_8.asp:30` — UNSE_TITLE = "형제운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 적성운 (interlife-jum-9)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-jum-9
- 계산/부분 계산: POST /v1/un/interlife-jum-9

### interlife_source_execution_unverified (confirmed)

원인: S049.db_title [old/unse/interlife/UNSE_DATA/solve/S/S049.asp:106; 호출 1] S079.result_var [old/unse/interlife/UNSE_DATA/solve/S/S079.asp:15; 호출 1] S080.result_var [old/unse/interlife/UNSE_DATA/solve/S/S080.asp:15; 호출 1] S081.result_var [old/unse/interlife/UNSE_DATA/solve/S/S081.asp:13; 호출 1] S085.result_var [old/unse/interlife/UNSE_DATA/solve/S/S085.asp:13; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S049.db_title [old/unse/interlife/UNSE_DATA/solve/S/S049.asp:106; 호출 1]
- S079.result_var [old/unse/interlife/UNSE_DATA/solve/S/S079.asp:15; 호출 1]
- S080.result_var [old/unse/interlife/UNSE_DATA/solve/S/S080.asp:15; 호출 1]
- S081.result_var [old/unse/interlife/UNSE_DATA/solve/S/S081.asp:13; 호출 1]
- S085.result_var [old/unse/interlife/UNSE_DATA/solve/S/S085.asp:13; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_9.asp:30` — UNSE_TITLE = "적성운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/jum/jum_9.asp:30` — UNSE_TITLE = "적성운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 로또번호운세 (interlife-lotto-1)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-lotto-1
- 계산/부분 계산: POST /v1/un/interlife-lotto-1

### interlife_lotto_calendar_profile_unverified (confirmed)

원인: 원본 mansedata의 A~J·01~12 간지/number/jeolip와 tb_manse 원시 간지·절입 필드의 대응이 미검증입니다. 기본 달력 후보와 원본 산술을 제공하며 원본 최종 판정으로 확정하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- 원본 행번호/이웃행 의미와 시간 경계·숫자 배열 대조 결과

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/lotto/lotto_1.asp:8` — UNSE_TITLE = "로또번호운세"
- `old/unse/interlife/UNSE_DATA/unse/lotto/lotto_1.asp:86` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/sajujowha2.asp:22` — sql = "SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& c_ymd_jeolip &"'"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha2.asp:41` — sql = "SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = '"& c_number &"'"
- `old/unse/interlife/UNSE_DATA/unse/lotto/lotto_1.asp:86` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& c_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/unse/lotto/lotto_1.asp:105` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = '"& c_number &"'")
- `old/unse/interlife/UNSE_DATA/unse/lotto/lotto_1.asp:344` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like  '"& no_current &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_extra의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/lotto/lotto_1.asp:8` — UNSE_TITLE = "로또번호운세"
- `old/unse/interlife/UNSE_DATA/unse/lotto/lotto_1.asp:86` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/sajujowha2.asp:22` — sql = "SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& c_ymd_jeolip &"'"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha2.asp:41` — sql = "SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = '"& c_number &"'"
- `old/unse/interlife/UNSE_DATA/unse/lotto/lotto_1.asp:86` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& c_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/unse/lotto/lotto_1.asp:105` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = '"& c_number &"'")
- `old/unse/interlife/UNSE_DATA/unse/lotto/lotto_1.asp:344` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like  '"& no_current &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 사주명식 (interlife-manse-1)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-manse-1
- 계산/부분 계산: POST /v1/un/interlife-manse-1

### interlife_full_chart_profile_unverified (confirmed)

원인: source_row_required: source_birth_rows.birth.day_e source_row_required: source_birth_rows.birth.day_h source_row_required: source_birth_rows.birth.jeolip source_row_required: source_birth_rows.selected.month_e source_row_required: source_birth_rows.selected.month_h source_row_required: source_birth_rows.selected.year_e source_row_required: source_birth_rows.selected.year_h source_row_required: source_current_record.no source_row_required: source_current_record.umyear_e source_row_required: source_current_record.umyear_h source_unassigned_state: 원본 외부 입력이 미할당입니다: daeun10_no, daeun1_no, daeun2_no, daeun3_no, daeun4_no, daeun5_no, daeun6_no, daeun7_no, daeun8_no, daeun9_no, my_age source_syntax_anomaly: 원본 VB 블록의 // 주석형 행을 계산식과 구분해 보존했습니다. 원본 배포의 주석 처리 상태를 확인해야 합니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- source_birth_rows.birth.{no,number,day_h,day_e,jeolip}
- source_birth_rows.selected.{number,year_h,year_e,month_h,month_e}
- source_current_record.{no,umyear_h,umyear_e}
- source_state.{my_age,daeun1_no..daeun10_no}; 원본에 할당문 없는 외부 입력

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/manse/manse_1.asp:7` — UNSE_TITLE = "사주명식"
- `old/unse/interlife/UNSE_DATA/solve/F/F029.asp:27` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/F/F029.asp:27` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_chart의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/manse/manse_1.asp:7` — UNSE_TITLE = "사주명식"
- `old/unse/interlife/UNSE_DATA/solve/F/F029.asp:27` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/F/F029.asp:27` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 음양력변환 (interlife-manse-2)

- 상태: calculation_only · Python 계산 전용 완료 · AI 해석 대상 아님
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-manse-2
- 계산/부분 계산: POST /v1/un/interlife-manse-2

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시로 입력·계산/선택키·출력 계약을 확인했습니다. 실제 ASP 서버/DLL/AI 호출 등가성 검증과는 구분합니다.
- 기존 정적 추적 항목을 현재 Python 실행 결과에 맞춰 재분류했습니다: python_not_ported, interlife_calendar_classification_mansedata, conditional_leap_file_path. 원본 근거 줄은 sources에 보존합니다.
- 실행 제약: interlife-free-12와 같은 달력 표시 계약입니다. 원본에 AI 해석문구가 없습니다.
- CR-012 / T-024: app.ported_interlife의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/manse/manse_2.asp:7` — UNSE_TITLE = "음양력변환"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 자동이름풀이 (성 1자·이름 1자) (interlife-name-1)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-name-1
- 계산/부분 계산: POST /v1/un/interlife-name-1

### interlife_source_execution_unverified (confirmed)

원인: N002.db_data [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1] N002.db_express [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1] N003.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1] N003.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1] N004.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1] N004.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1] N005.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1] N005.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1] N015.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1] N015.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- N002.db_data [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1]
- N002.db_express [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1]
- N003.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1]
- N003.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1]
- N004.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1]
- N004.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1]
- N005.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1]
- N005.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1]
- N015.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1]
- N015.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]

판단 근거:

- `old/unse/interlife/incs/info.asp:38` — menuNAME의 자동이름풀이 성/이름 글자수별 다섯 항목
- `old/unse/interlife/UNSE_DATA/unse/name/name_1.asp:1` — <!-- #include virtual = "/unse/interlife/UNSE_DATA/unse/name/name_puri.asp" -->
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/common/function.asp:629` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin =  '"& namevar &"' and hangul = '"& hangulvar &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14` — Set rs = ldb.execute("SELECT DB_express, DB_title_1, DB_title, DB_data, DB_numerical FROM N015 WHERE DB_title_1 like '%"& mokwha_all &"%'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/incs/info.asp:38` — menuNAME의 자동이름풀이 성/이름 글자수별 다섯 항목
- `old/unse/interlife/UNSE_DATA/unse/name/name_1.asp:1` — <!-- #include virtual = "/unse/interlife/UNSE_DATA/unse/name/name_puri.asp" -->
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/common/function.asp:629` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin =  '"& namevar &"' and hangul = '"& hangulvar &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14` — Set rs = ldb.execute("SELECT DB_express, DB_title_1, DB_title, DB_data, DB_numerical FROM N015 WHERE DB_title_1 like '%"& mokwha_all &"%'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 자동이름풀이 (성 1자·이름 2자) (interlife-name-2)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-name-2
- 계산/부분 계산: POST /v1/un/interlife-name-2

### interlife_source_execution_unverified (confirmed)

원인: N002.db_data [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1] N002.db_express [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1] N003.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1] N003.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1] N004.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1] N004.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1] N005.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1] N005.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1] N015.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1] N015.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- N002.db_data [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1]
- N002.db_express [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1]
- N003.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1]
- N003.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1]
- N004.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1]
- N004.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1]
- N005.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1]
- N005.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1]
- N015.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1]
- N015.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]

판단 근거:

- `old/unse/interlife/incs/info.asp:38` — menuNAME의 자동이름풀이 성/이름 글자수별 다섯 항목
- `old/unse/interlife/UNSE_DATA/unse/name/name_2.asp:1` — <!-- #include virtual = "/unse/interlife/UNSE_DATA/unse/name/name_puri.asp" -->
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/common/function.asp:629` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin =  '"& namevar &"' and hangul = '"& hangulvar &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14` — Set rs = ldb.execute("SELECT DB_express, DB_title_1, DB_title, DB_data, DB_numerical FROM N015 WHERE DB_title_1 like '%"& mokwha_all &"%'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/incs/info.asp:38` — menuNAME의 자동이름풀이 성/이름 글자수별 다섯 항목
- `old/unse/interlife/UNSE_DATA/unse/name/name_2.asp:1` — <!-- #include virtual = "/unse/interlife/UNSE_DATA/unse/name/name_puri.asp" -->
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/common/function.asp:629` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin =  '"& namevar &"' and hangul = '"& hangulvar &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14` — Set rs = ldb.execute("SELECT DB_express, DB_title_1, DB_title, DB_data, DB_numerical FROM N015 WHERE DB_title_1 like '%"& mokwha_all &"%'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 자동이름풀이 (성 1자·이름 3자) (interlife-name-3)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-name-3
- 계산/부분 계산: POST /v1/un/interlife-name-3

### interlife_source_execution_unverified (confirmed)

원인: N002.db_data [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1] N002.db_express [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1] N003.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1] N003.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1] N004.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1] N004.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1] N005.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1] N005.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1] N015.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1] N015.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- N002.db_data [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1]
- N002.db_express [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1]
- N003.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1]
- N003.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1]
- N004.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1]
- N004.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1]
- N005.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1]
- N005.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1]
- N015.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1]
- N015.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]

판단 근거:

- `old/unse/interlife/incs/info.asp:38` — menuNAME의 자동이름풀이 성/이름 글자수별 다섯 항목
- `old/unse/interlife/UNSE_DATA/unse/name/name_3.asp:1` — <!-- #include virtual = "/unse/interlife/UNSE_DATA/unse/name/name_puri.asp" -->
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/common/function.asp:629` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin =  '"& namevar &"' and hangul = '"& hangulvar &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14` — Set rs = ldb.execute("SELECT DB_express, DB_title_1, DB_title, DB_data, DB_numerical FROM N015 WHERE DB_title_1 like '%"& mokwha_all &"%'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/incs/info.asp:38` — menuNAME의 자동이름풀이 성/이름 글자수별 다섯 항목
- `old/unse/interlife/UNSE_DATA/unse/name/name_3.asp:1` — <!-- #include virtual = "/unse/interlife/UNSE_DATA/unse/name/name_puri.asp" -->
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/common/function.asp:629` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin =  '"& namevar &"' and hangul = '"& hangulvar &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14` — Set rs = ldb.execute("SELECT DB_express, DB_title_1, DB_title, DB_data, DB_numerical FROM N015 WHERE DB_title_1 like '%"& mokwha_all &"%'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 자동이름풀이 (성 2자·이름 1자) (interlife-name-4)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-name-4
- 계산/부분 계산: POST /v1/un/interlife-name-4

### interlife_source_execution_unverified (confirmed)

원인: N002.db_data [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1] N002.db_express [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1] N003.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1] N003.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1] N004.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1] N004.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1] N005.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1] N005.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1] N015.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1] N015.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- N002.db_data [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1]
- N002.db_express [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1]
- N003.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1]
- N003.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1]
- N004.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1]
- N004.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1]
- N005.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1]
- N005.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1]
- N015.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1]
- N015.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]

판단 근거:

- `old/unse/interlife/incs/info.asp:38` — menuNAME의 자동이름풀이 성/이름 글자수별 다섯 항목
- `old/unse/interlife/UNSE_DATA/unse/name/name_4.asp:1` — <!-- #include virtual = "/unse/interlife/UNSE_DATA/unse/name/name_puri.asp" -->
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/common/function.asp:629` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin =  '"& namevar &"' and hangul = '"& hangulvar &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14` — Set rs = ldb.execute("SELECT DB_express, DB_title_1, DB_title, DB_data, DB_numerical FROM N015 WHERE DB_title_1 like '%"& mokwha_all &"%'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/incs/info.asp:38` — menuNAME의 자동이름풀이 성/이름 글자수별 다섯 항목
- `old/unse/interlife/UNSE_DATA/unse/name/name_4.asp:1` — <!-- #include virtual = "/unse/interlife/UNSE_DATA/unse/name/name_puri.asp" -->
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/common/function.asp:629` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin =  '"& namevar &"' and hangul = '"& hangulvar &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14` — Set rs = ldb.execute("SELECT DB_express, DB_title_1, DB_title, DB_data, DB_numerical FROM N015 WHERE DB_title_1 like '%"& mokwha_all &"%'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 자동이름풀이 (성 2자·이름 2자) (interlife-name-5)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-name-5
- 계산/부분 계산: POST /v1/un/interlife-name-5

### interlife_source_execution_unverified (confirmed)

원인: N002.db_data [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1] N002.db_express [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1] N003.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1] N003.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1] N004.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1] N004.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1] N005.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1] N005.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1] N015.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1] N015.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4] namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4] namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- N002.db_data [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1]
- N002.db_express [old/unse/interlife/UNSE_DATA/solve/N/N002.asp:17; 호출 1]
- N003.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1]
- N003.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N003.asp:19; 호출 1]
- N004.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1]
- N004.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N004.asp:11; 호출 1]
- N005.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1]
- N005.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N005.asp:11; 호출 1]
- N015.ADO_bof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1]
- N015.ADO_eof [old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4]
- namedata.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 1]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 2]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 3]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 4]
- namedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:629; 호출 5]

판단 근거:

- `old/unse/interlife/incs/info.asp:38` — menuNAME의 자동이름풀이 성/이름 글자수별 다섯 항목
- `old/unse/interlife/UNSE_DATA/unse/name/name_5.asp:1` — <!-- #include virtual = "/unse/interlife/UNSE_DATA/unse/name/name_puri.asp" -->
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/common/function.asp:629` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin =  '"& namevar &"' and hangul = '"& hangulvar &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14` — Set rs = ldb.execute("SELECT DB_express, DB_title_1, DB_title, DB_data, DB_numerical FROM N015 WHERE DB_title_1 like '%"& mokwha_all &"%'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/incs/info.asp:38` — menuNAME의 자동이름풀이 성/이름 글자수별 다섯 항목
- `old/unse/interlife/UNSE_DATA/unse/name/name_5.asp:1` — <!-- #include virtual = "/unse/interlife/UNSE_DATA/unse/name/name_puri.asp" -->
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/common/function.asp:629` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin =  '"& namevar &"' and hangul = '"& hangulvar &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N015.asp:14` — Set rs = ldb.execute("SELECT DB_express, DB_title_1, DB_title, DB_data, DB_numerical FROM N015 WHERE DB_title_1 like '%"& mokwha_all &"%'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 셀프용신작명 (interlife-name-6)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-name-6
- 계산/부분 계산: POST /v1/un/interlife-name-6

### interlife_source_execution_unverified (confirmed)

원인: mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_server_variable

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_server_variable

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/name/name_6-2.asp:8` — UNSE_TITLE = "셀프용신작명"
- `old/unse/interlife/UNSE_DATA/solve/N/N001_2.asp:111` — [ 용신셀프작명 총 4 단계에서 3 단계 진행중입니다. ]
- `old/unse/interlife/UNSE_DATA/unse/name/name_6-3.asp:9` — UNSE_TITLE = "셀프용신작명"
- `old/unse/interlife/UNSE_DATA/solve/N/N001_3.asp:123` — [ 용신셀프작명 총 4 단계에서 4 단계 진행중입니다. ]
- `old/unse/interlife/UNSE_DATA/unse/name/name_6-4.asp:9` — UNSE_TITLE = "셀프용신작명"
- `old/unse/interlife/UNSE_DATA/solve/N/N001_4.asp:90` — [ 용신셀프작명 결과 ]
- `old/unse/interlife/UNSE_DATA/unse/name/name_6.asp:9` — UNSE_TITLE = "셀프용신작명"
- `old/unse/interlife/UNSE_DATA/solve/N/N001_1.asp:137` — [ 용신셀프작명 총 4 단계에서 2 단계 진행중입니다. ]
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/N/N001_4.asp:97` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin = '"& hanja1 &"' and hanjano = '"& hanjano1 &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N001_4.asp:104` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin = '"& hanja_select2 &"' and hanjano = '"& j &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N001_4.asp:112` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin = '"& hanja_select3 &"' and hanjano = '"& k &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N001_3.asp:216` — Set rs = ldb.execute("SELECT hanjawin, hanjano, hangul, what, bulcomment FROM namedata WHERE hanjawin <> '' and hanjano = '"& j &"'  and mokwha = '"& mokwha2_ch &"' and newold = 0 "& where_plus_var &" order by hanjano")
- `old/unse/interlife/UNSE_DATA/solve/N/N001_3.asp:221` — Set rs = ldb.execute("SELECT hanjawin, hanjano, hangul, what, bulcomment FROM namedata WHERE hanjawin <> '' and hanjano = '7'  and mokwha = '5' and newold = 0 "& where_plus_var &" order by hanjano")
- `old/unse/interlife/UNSE_DATA/solve/N/N001_3.asp:279` — Set rs = ldb.execute("SELECT hanjawin, hanjano, hangul, what, bulcomment FROM namedata WHERE hanjawin <> '' and hanjano = '"& k &"'  and mokwha = '"& mokwha3_ch &"' and newold = 0 "& where_plus_var &" order by hanjano")
- `old/unse/interlife/UNSE_DATA/solve/N/N001_3.asp:291` — Set rs = ldb.execute("SELECT hanjawin, hanjano, hangul, what, bulcomment FROM namedata WHERE hanjawin <> '' and hanjano = '7'  and mokwha = '5' and newold = 0 "& where_plus_var &" order by hanjano")
- `old/unse/interlife/UNSE_DATA/solve/N/N001_1.asp:12` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin =  '"& name12_1 &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 셀프용신작명 단일 서비스의 후속 처리 단계.
- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/name/name_6-2.asp:8` — UNSE_TITLE = "셀프용신작명"
- `old/unse/interlife/UNSE_DATA/solve/N/N001_2.asp:111` — [ 용신셀프작명 총 4 단계에서 3 단계 진행중입니다. ]
- `old/unse/interlife/UNSE_DATA/unse/name/name_6-3.asp:9` — UNSE_TITLE = "셀프용신작명"
- `old/unse/interlife/UNSE_DATA/solve/N/N001_3.asp:123` — [ 용신셀프작명 총 4 단계에서 4 단계 진행중입니다. ]
- `old/unse/interlife/UNSE_DATA/unse/name/name_6-4.asp:9` — UNSE_TITLE = "셀프용신작명"
- `old/unse/interlife/UNSE_DATA/solve/N/N001_4.asp:90` — [ 용신셀프작명 결과 ]
- `old/unse/interlife/UNSE_DATA/unse/name/name_6.asp:9` — UNSE_TITLE = "셀프용신작명"
- `old/unse/interlife/UNSE_DATA/solve/N/N001_1.asp:137` — [ 용신셀프작명 총 4 단계에서 2 단계 진행중입니다. ]
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/N/N001_4.asp:97` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin = '"& hanja1 &"' and hanjano = '"& hanjano1 &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N001_4.asp:104` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin = '"& hanja_select2 &"' and hanjano = '"& j &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N001_4.asp:112` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin = '"& hanja_select3 &"' and hanjano = '"& k &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N001_3.asp:216` — Set rs = ldb.execute("SELECT hanjawin, hanjano, hangul, what, bulcomment FROM namedata WHERE hanjawin <> '' and hanjano = '"& j &"'  and mokwha = '"& mokwha2_ch &"' and newold = 0 "& where_plus_var &" order by hanjano")
- `old/unse/interlife/UNSE_DATA/solve/N/N001_3.asp:221` — Set rs = ldb.execute("SELECT hanjawin, hanjano, hangul, what, bulcomment FROM namedata WHERE hanjawin <> '' and hanjano = '7'  and mokwha = '5' and newold = 0 "& where_plus_var &" order by hanjano")
- `old/unse/interlife/UNSE_DATA/solve/N/N001_3.asp:279` — Set rs = ldb.execute("SELECT hanjawin, hanjano, hangul, what, bulcomment FROM namedata WHERE hanjawin <> '' and hanjano = '"& k &"'  and mokwha = '"& mokwha3_ch &"' and newold = 0 "& where_plus_var &" order by hanjano")
- `old/unse/interlife/UNSE_DATA/solve/N/N001_3.asp:291` — Set rs = ldb.execute("SELECT hanjawin, hanjano, hangul, what, bulcomment FROM namedata WHERE hanjawin <> '' and hanjano = '7'  and mokwha = '5' and newold = 0 "& where_plus_var &" order by hanjano")
- `old/unse/interlife/UNSE_DATA/solve/N/N001_1.asp:12` — Set rs = ldb.execute("SELECT * FROM namedata WHERE hanjawin =  '"& name12_1 &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 성씨추명학 (interlife-name-7)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-name-7
- 계산/부분 계산: POST /v1/un/interlife-name-7

### interlife_source_execution_unverified (confirmed)

원인: N008.db_data [old/unse/interlife/UNSE_DATA/solve/N/N008.asp:7; 호출 1] N008.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N008.asp:7; 호출 1] N009.db_data [old/unse/interlife/UNSE_DATA/solve/N/N009.asp:7; 호출 1] N009.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N009.asp:7; 호출 1] N010.db_data [old/unse/interlife/UNSE_DATA/solve/N/N010.asp:7; 호출 1] N010.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N010.asp:7; 호출 1] N011.db_data [old/unse/interlife/UNSE_DATA/solve/N/N011.asp:7; 호출 1] N011.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N011.asp:7; 호출 1] N012.db_data [old/unse/interlife/UNSE_DATA/solve/N/N012.asp:7; 호출 1] N012.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N012.asp:7; 호출 1] N013.db_data [old/unse/interlife/UNSE_DATA/solve/N/N013.asp:7; 호출 1] N013.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N013.asp:7; 호출 1] N014.db_data [old/unse/interlife/UNSE_DATA/solve/N/N014.asp:7; 호출 1] N014.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N014.asp:7; 호출 1] surioheng.bal [old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:31; 호출 1] surioheng.bal [old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:45; 호출 1] surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:31; 호출 1] surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:45; 호출 1] surioheng.su [old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:31; 호출 1] surioheng.su [old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:45; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- N008.db_data [old/unse/interlife/UNSE_DATA/solve/N/N008.asp:7; 호출 1]
- N008.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N008.asp:7; 호출 1]
- N009.db_data [old/unse/interlife/UNSE_DATA/solve/N/N009.asp:7; 호출 1]
- N009.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N009.asp:7; 호출 1]
- N010.db_data [old/unse/interlife/UNSE_DATA/solve/N/N010.asp:7; 호출 1]
- N010.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N010.asp:7; 호출 1]
- N011.db_data [old/unse/interlife/UNSE_DATA/solve/N/N011.asp:7; 호출 1]
- N011.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N011.asp:7; 호출 1]
- N012.db_data [old/unse/interlife/UNSE_DATA/solve/N/N012.asp:7; 호출 1]
- N012.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N012.asp:7; 호출 1]
- N013.db_data [old/unse/interlife/UNSE_DATA/solve/N/N013.asp:7; 호출 1]
- N013.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N013.asp:7; 호출 1]
- N014.db_data [old/unse/interlife/UNSE_DATA/solve/N/N014.asp:7; 호출 1]
- N014.db_numerical [old/unse/interlife/UNSE_DATA/solve/N/N014.asp:7; 호출 1]
- surioheng.bal [old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:31; 호출 1]
- surioheng.bal [old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:45; 호출 1]
- surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:31; 호출 1]
- surioheng.hangul [old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:45; 호출 1]
- surioheng.su [old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:31; 호출 1]
- surioheng.su [old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:45; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:4` — UNSE_TITLE = "성씨추명학"
- `old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:15` — UNSE_TITLE = "성씨추명학"
- `old/unse/interlife/UNSE_DATA/solve/N/N008.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N008 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N009.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N009 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N010.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N010 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N011.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N011 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N012.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N012 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N013.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N013 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N014.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N014 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:31` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& msung &"'")
- `old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:45` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& ysung &"'")

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:4` — UNSE_TITLE = "성씨추명학"
- `old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:15` — UNSE_TITLE = "성씨추명학"
- `old/unse/interlife/UNSE_DATA/solve/N/N008.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N008 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N009.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N009 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N010.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N010 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N011.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N011 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N012.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N012 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N013.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N013 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/N/N014.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM N014 WHERE DB_express = '"& number_var &"'")
- `old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:31` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& msung &"'")
- `old/unse/interlife/UNSE_DATA/unse/name/name_7.asp:45` — Set rs = ldb.execute("SELECT hangul, hanja, su, bal FROM surioheng WHERE hanja like '"& ysung &"'")

## 올해의토정비결 (interlife-saju-1)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-1
- 계산/부분 계산: POST /v1/un/interlife-saju-1

### interlife_source_execution_unverified (confirmed)

원인: S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S028.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S028.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1] S082.result_var [old/unse/interlife/UNSE_DATA/solve/S/S082.asp:15; 호출 1] S110.db_data_1 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1] S110.db_data_10 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1] S110.db_data_11 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1] S110.db_data_12 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1] S110.db_data_2 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1] S110.db_data_3 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1] S110.db_data_4 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1] S110.db_data_5 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1] S110.db_data_6 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1] S110.db_data_7 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1] S110.db_data_8 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1] S110.db_data_9 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1] mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:172; 호출 1] mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:274; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:172; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:274; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:136; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:136; 호출 1] mansedata.umdate [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:79; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:91; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:91; 호출 1] source_policy.source_terms_required tojung_gabja.il [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:258; 호출 1] tojung_gabja.tae [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:250; 호출 1] tojung_gabja.wol [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:254; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S028.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S028.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1]
- S082.result_var [old/unse/interlife/UNSE_DATA/solve/S/S082.asp:15; 호출 1]
- S110.db_data_1 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1]
- S110.db_data_10 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1]
- S110.db_data_11 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1]
- S110.db_data_12 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1]
- S110.db_data_2 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1]
- S110.db_data_3 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1]
- S110.db_data_4 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1]
- S110.db_data_5 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1]
- S110.db_data_6 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1]
- S110.db_data_7 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1]
- S110.db_data_8 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1]
- S110.db_data_9 [old/unse/interlife/UNSE_DATA/solve/S/S110.asp:7; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1]
- mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:172; 호출 1]
- mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:274; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:172; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:274; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:136; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:136; 호출 1]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:79; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:91; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:91; 호출 1]
- source_policy.source_terms_required
- tojung_gabja.il [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:258; 호출 1]
- tojung_gabja.tae [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:250; 호출 1]
- tojung_gabja.wol [old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:254; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:31` — UNSE_TITLE = "올해의토정비결"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:79` — Set rs = ldb.execute("SELECT umdate FROM mansedata WHERE no = '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:91` — Set rs = ldb.execute("SELECT year_h, year_e FROM mansedata WHERE umdate = '"& current_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:136` — Set rs = ldb.execute("SELECT month_h, month_e FROM mansedata WHERE umdate = '"& see_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:172` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:186` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate_kk &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:274` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE umdate = '"& um_y_m_d &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:250` — Set rs = ldb.execute("SELECT tae FROM tojung_gabja WHERE gabja = '"& result_year &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:254` — Set rs = ldb.execute("SELECT wol FROM tojung_gabja WHERE gabja = '"& result_month &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:258` — Set rs = ldb.execute("SELECT il FROM tojung_gabja WHERE gabja = '"& result_day &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:31` — UNSE_TITLE = "올해의토정비결"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:79` — Set rs = ldb.execute("SELECT umdate FROM mansedata WHERE no = '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:91` — Set rs = ldb.execute("SELECT year_h, year_e FROM mansedata WHERE umdate = '"& current_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:136` — Set rs = ldb.execute("SELECT month_h, month_e FROM mansedata WHERE umdate = '"& see_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:172` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:186` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate_kk &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:274` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE umdate = '"& um_y_m_d &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:250` — Set rs = ldb.execute("SELECT tae FROM tojung_gabja WHERE gabja = '"& result_year &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:254` — Set rs = ldb.execute("SELECT wol FROM tojung_gabja WHERE gabja = '"& result_month &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_1.asp:258` — Set rs = ldb.execute("SELECT il FROM tojung_gabja WHERE gabja = '"& result_day &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 자평명리학 오늘의 운세 (interlife-saju-10)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-10
- 계산/부분 계산: POST /v1/un/interlife-saju-10

### interlife_source_execution_unverified (confirmed)

원인: mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/unse/saju/saju_10.asp:67; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/unse/saju/saju_10.asp:67; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/unse/saju/saju_10.asp:67; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/unse/saju/saju_10.asp:67; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_10.asp:30` — UNSE_TITLE = "자평명리학 오늘의 운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_10.asp:67` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_10.asp:30` — UNSE_TITLE = "자평명리학 오늘의 운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_10.asp:67` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 당사주 평생총운 (interlife-saju-11)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-11
- 계산/부분 계산: POST /v1/un/interlife-saju-11

### interlife_source_execution_unverified (confirmed)

원인: S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_11.asp:30` — UNSE_TITLE = "당사주 평생총운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_11.asp:30` — UNSE_TITLE = "당사주 평생총운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 사주로 보는 심리분석 (interlife-saju-12)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-12
- 계산/부분 계산: POST /v1/un/interlife-saju-12

### interlife_source_execution_unverified (confirmed)

원인: S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1] T060.db_numerical [old/unse/interlife/UNSE_DATA/solve/T/T060.asp:9; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1]
- T060.db_numerical [old/unse/interlife/UNSE_DATA/solve/T/T060.asp:9; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_12.asp:30` — UNSE_TITLE = "사주로 보는 심리분석"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/T/T060.asp:9` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM T060 WHERE DB_express = '"& total &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_12.asp:30` — UNSE_TITLE = "사주로 보는 심리분석"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/T/T060.asp:9` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM T060 WHERE DB_express = '"& total &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 살풀이 (interlife-saju-13)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-13
- 계산/부분 계산: POST /v1/un/interlife-saju-13

### interlife_source_execution_unverified (confirmed)

원인: S007.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S007.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/etc/s126_sal_data.asp:565; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/etc/s126_sal_data.asp:565; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/etc/s126_sal_data.asp:565; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/etc/s126_sal_data.asp:565; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/etc/s126_sal_data.asp:565; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S007.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S007.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/etc/s126_sal_data.asp:565; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/etc/s126_sal_data.asp:565; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/etc/s126_sal_data.asp:565; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/etc/s126_sal_data.asp:565; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/etc/s126_sal_data.asp:565; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_13.asp:30` — UNSE_TITLE = "살풀이"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/etc/s126_sal_data.asp:565` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like  '"& no &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_13.asp:30` — UNSE_TITLE = "살풀이"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/etc/s126_sal_data.asp:565` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like  '"& no &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 성격운세 (interlife-saju-14)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-14
- 계산/부분 계산: POST /v1/un/interlife-saju-14

### interlife_source_execution_unverified (confirmed)

원인: S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_14.asp:30` — UNSE_TITLE = "성격운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_14.asp:30` — UNSE_TITLE = "성격운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 초년운 (interlife-saju-15)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-15
- 계산/부분 계산: POST /v1/un/interlife-saju-15

### interlife_source_execution_unverified (confirmed)

원인: S018.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S018.asp:9; 호출 1] S026.db_data [old/unse/interlife/UNSE_DATA/solve/S/S026.asp:7; 호출 1] S030.db_data [old/unse/interlife/UNSE_DATA/solve/S/S030.asp:22; 호출 1] S048.db_title [old/unse/interlife/UNSE_DATA/solve/S/S048.asp:81; 호출 1] S050.db_title [old/unse/interlife/UNSE_DATA/solve/S/S050.asp:110; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:75; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:75; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.no [old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:183; 호출 1] mansedata.umdate [old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:183; 호출 1] mansedata.umyear_e [old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:183; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S018.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S018.asp:9; 호출 1]
- S026.db_data [old/unse/interlife/UNSE_DATA/solve/S/S026.asp:7; 호출 1]
- S030.db_data [old/unse/interlife/UNSE_DATA/solve/S/S030.asp:22; 호출 1]
- S048.db_title [old/unse/interlife/UNSE_DATA/solve/S/S048.asp:81; 호출 1]
- S050.db_title [old/unse/interlife/UNSE_DATA/solve/S/S050.asp:110; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:75; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:75; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.no [old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:183; 호출 1]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:183; 호출 1]
- mansedata.umyear_e [old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:183; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:30` — UNSE_TITLE = "초년운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:75` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:183` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like  '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:9726` — sql = "SELECT * FROM mansedata WHERE umdate like  '"& cc &"'"
- `old/unse/interlife/UNSE_DATA/solve/S/S018.asp:9` — set rs = ldb.execute("select DB_data, DB_numerical from S018 where DB_express = '"& dang1 &"'")		'초년운
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:30` — UNSE_TITLE = "초년운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:75` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:183` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like  '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_15.asp:9726` — sql = "SELECT * FROM mansedata WHERE umdate like  '"& cc &"'"
- `old/unse/interlife/UNSE_DATA/solve/S/S018.asp:9` — set rs = ldb.execute("select DB_data, DB_numerical from S018 where DB_express = '"& dang1 &"'")		'초년운
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 중년운 (interlife-saju-16)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-16
- 계산/부분 계산: POST /v1/un/interlife-saju-16

### interlife_source_execution_unverified (confirmed)

원인: S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S019.0 [old/unse/interlife/UNSE_DATA/solve/S/S019.asp:17; 호출 1] S019.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S019.asp:17; 호출 1] S028.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S028.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1] S051.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110; 호출 1] S051.db_title [old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110; 호출 1] S082.result_var [old/unse/interlife/UNSE_DATA/solve/S/S082.asp:15; 호출 1] S083.result_var [old/unse/interlife/UNSE_DATA/solve/S/S083.asp:16; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S019.0 [old/unse/interlife/UNSE_DATA/solve/S/S019.asp:17; 호출 1]
- S019.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S019.asp:17; 호출 1]
- S028.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S028.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1]
- S051.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110; 호출 1]
- S051.db_title [old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110; 호출 1]
- S082.result_var [old/unse/interlife/UNSE_DATA/solve/S/S082.asp:15; 호출 1]
- S083.result_var [old/unse/interlife/UNSE_DATA/solve/S/S083.asp:16; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_16.asp:30` — UNSE_TITLE = "중년운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S019.asp:17` — set rs = ldb.execute("select DB_data, DB_numerical from S019 where DB_express = '"& dang2 &"'")		'중년운
- `old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110` — Set rs = ldb.execute("SELECT DB_title, DB_data, DB_numerical FROM S051 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_16.asp:30` — UNSE_TITLE = "중년운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S019.asp:17` — set rs = ldb.execute("select DB_data, DB_numerical from S019 where DB_express = '"& dang2 &"'")		'중년운
- `old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110` — Set rs = ldb.execute("SELECT DB_title, DB_data, DB_numerical FROM S051 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 말년운 (interlife-saju-17)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-17
- 계산/부분 계산: POST /v1/un/interlife-saju-17

### interlife_source_execution_unverified (confirmed)

원인: F011.db_data [old/unse/interlife/UNSE_DATA/solve/F/F011.asp:16; 호출 1] S007.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 2] S007.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 2] S008.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S008.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 3] S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 3] S020.0 [old/unse/interlife/UNSE_DATA/solve/S/S020.asp:18; 호출 1] S020.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S020.asp:18; 호출 1] S021.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S021.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S051.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110; 호출 1] S051.db_title [old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110; 호출 1] S083.result_var [old/unse/interlife/UNSE_DATA/solve/S/S083.asp:16; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- F011.db_data [old/unse/interlife/UNSE_DATA/solve/F/F011.asp:16; 호출 1]
- S007.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 2]
- S007.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 2]
- S008.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S008.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 3]
- S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 3]
- S020.0 [old/unse/interlife/UNSE_DATA/solve/S/S020.asp:18; 호출 1]
- S020.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S020.asp:18; 호출 1]
- S021.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S021.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S051.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110; 호출 1]
- S051.db_title [old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110; 호출 1]
- S083.result_var [old/unse/interlife/UNSE_DATA/solve/S/S083.asp:16; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_17.asp:30` — UNSE_TITLE = "말년운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S020.asp:18` — set rs = ldb.execute("select DB_data, DB_numerical from S020 where DB_express = '"& dang3 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110` — Set rs = ldb.execute("SELECT DB_title, DB_data, DB_numerical FROM S051 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_17.asp:30` — UNSE_TITLE = "말년운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S020.asp:18` — set rs = ldb.execute("select DB_data, DB_numerical from S020 where DB_express = '"& dang3 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110` — Set rs = ldb.execute("SELECT DB_title, DB_data, DB_numerical FROM S051 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 직업운 (interlife-saju-18)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-18
- 계산/부분 계산: POST /v1/un/interlife-saju-18

### interlife_source_execution_unverified (confirmed)

원인: S030.db_data [old/unse/interlife/UNSE_DATA/solve/S/S030.asp:22; 호출 1] S048.db_title [old/unse/interlife/UNSE_DATA/solve/S/S048.asp:81; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S030.db_data [old/unse/interlife/UNSE_DATA/solve/S/S030.asp:22; 호출 1]
- S048.db_title [old/unse/interlife/UNSE_DATA/solve/S/S048.asp:81; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_18.asp:30` — UNSE_TITLE = "직업운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_18.asp:30` — UNSE_TITLE = "직업운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 재물운 (interlife-saju-19)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-19
- 계산/부분 계산: POST /v1/un/interlife-saju-19

### interlife_source_execution_unverified (confirmed)

원인: S027.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S027.asp:11; 호출 1] S082.result_var [old/unse/interlife/UNSE_DATA/solve/S/S082.asp:15; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S027.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S027.asp:11; 호출 1]
- S082.result_var [old/unse/interlife/UNSE_DATA/solve/S/S082.asp:15; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_19.asp:30` — UNSE_TITLE = "재물운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S027.asp:11` — set rs = ldb.execute("select DB_data, DB_numerical from S027 where DB_express = '"& serial_no &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_19.asp:30` — UNSE_TITLE = "재물운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S027.asp:11` — set rs = ldb.execute("select DB_data, DB_numerical from S027 where DB_express = '"& serial_no &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 새해신수 (interlife-saju-2)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-2
- 계산/부분 계산: POST /v1/un/interlife-saju-2

### interlife_source_execution_unverified (confirmed)

원인: J048.db_data [old/unse/interlife/UNSE_DATA/solve/J/J048.asp:11; 호출 1] S007.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S007.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S026.db_data [old/unse/interlife/UNSE_DATA/solve/S/S026.asp:7; 호출 1] S082.result_var [old/unse/interlife/UNSE_DATA/solve/S/S082.asp:15; 호출 1] S101.db_data_1 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1] S101.db_data_10 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1] S101.db_data_11 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1] S101.db_data_12 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1] S101.db_data_2 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1] S101.db_data_3 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1] S101.db_data_4 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1] S101.db_data_5 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1] S101.db_data_6 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1] S101.db_data_7 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1] S101.db_data_8 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1] S101.db_data_9 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1] S103.db_data [old/unse/interlife/UNSE_DATA/solve/S/S103.asp:7; 호출 1] S122.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:777; 호출 1] S122.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:777; 호출 1] T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:108; 호출 1] mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:210; 호출 1] mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/unse/saju/saju_2.asp:66; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:108; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:210; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/unse/saju/saju_2.asp:66; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:72; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:72; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:15; 호출 1] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:27; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:27; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required tojung_gabja.il [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:194; 호출 1] tojung_gabja.tae [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:186; 호출 1] tojung_gabja.wol [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:190; 호출 1] unse_DB.umyear_e [old/unse/interlife/UNSE_DATA/solve/S/S122.asp:35; 호출 1] unse_DB.umyear_h [old/unse/interlife/UNSE_DATA/solve/S/S122.asp:35; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- J048.db_data [old/unse/interlife/UNSE_DATA/solve/J/J048.asp:11; 호출 1]
- S007.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S007.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S026.db_data [old/unse/interlife/UNSE_DATA/solve/S/S026.asp:7; 호출 1]
- S082.result_var [old/unse/interlife/UNSE_DATA/solve/S/S082.asp:15; 호출 1]
- S101.db_data_1 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1]
- S101.db_data_10 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1]
- S101.db_data_11 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1]
- S101.db_data_12 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1]
- S101.db_data_2 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1]
- S101.db_data_3 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1]
- S101.db_data_4 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1]
- S101.db_data_5 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1]
- S101.db_data_6 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1]
- S101.db_data_7 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1]
- S101.db_data_8 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1]
- S101.db_data_9 [old/unse/interlife/UNSE_DATA/solve/S/S101.asp:7; 호출 1]
- S103.db_data [old/unse/interlife/UNSE_DATA/solve/S/S103.asp:7; 호출 1]
- S122.ADO_bof [old/unse/interlife/UNSE_DATA/common/function.asp:777; 호출 1]
- S122.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:777; 호출 1]
- T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:108; 호출 1]
- mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:210; 호출 1]
- mansedata.ADO_bof [old/unse/interlife/UNSE_DATA/unse/saju/saju_2.asp:66; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:108; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:210; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/unse/saju/saju_2.asp:66; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:72; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:72; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:15; 호출 1]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:27; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:27; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required
- tojung_gabja.il [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:194; 호출 1]
- tojung_gabja.tae [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:186; 호출 1]
- tojung_gabja.wol [old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:190; 호출 1]
- unse_DB.umyear_e [old/unse/interlife/UNSE_DATA/solve/S/S122.asp:35; 호출 1]
- unse_DB.umyear_h [old/unse/interlife/UNSE_DATA/solve/S/S122.asp:35; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_2.asp:30` — UNSE_TITLE = "새해신수"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:15` — Set rs = ldb.execute("SELECT umdate FROM mansedata WHERE no = '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:27` — Set rs = ldb.execute("SELECT year_h, year_e FROM mansedata WHERE umdate = '"& current_umdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:72` — Set rs = ldb.execute("SELECT month_h, month_e FROM mansedata WHERE umdate = '"& see_umdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:108` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:122` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate_kk &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:210` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE umdate = '"& um_y_m_d &"'")
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_2.asp:66` — Set rs = ldb.execute("select year_h from mansedata where no = '"& Replace(Date, "-", "") &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:186` — Set rs = ldb.execute("SELECT tae FROM tojung_gabja WHERE gabja = '"& result_year &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:190` — Set rs = ldb.execute("SELECT wol FROM tojung_gabja WHERE gabja = '"& result_month &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:194` — Set rs = ldb.execute("SELECT il FROM tojung_gabja WHERE gabja = '"& result_day &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_2.asp:30` — UNSE_TITLE = "새해신수"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:15` — Set rs = ldb.execute("SELECT umdate FROM mansedata WHERE no = '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:27` — Set rs = ldb.execute("SELECT year_h, year_e FROM mansedata WHERE umdate = '"& current_umdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:72` — Set rs = ldb.execute("SELECT month_h, month_e FROM mansedata WHERE umdate = '"& see_umdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:108` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:122` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE umdate = '"& see01_umdate_kk &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:210` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE umdate = '"& um_y_m_d &"'")
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_2.asp:66` — Set rs = ldb.execute("select year_h from mansedata where no = '"& Replace(Date, "-", "") &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:186` — Set rs = ldb.execute("SELECT tae FROM tojung_gabja WHERE gabja = '"& result_year &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:190` — Set rs = ldb.execute("SELECT wol FROM tojung_gabja WHERE gabja = '"& result_month &"'")
- `old/unse/interlife/UNSE_DATA/solve/S_S103_S110_sol.asp:194` — Set rs = ldb.execute("SELECT il FROM tojung_gabja WHERE gabja = '"& result_day &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 선천적기질운 (interlife-saju-20)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-20
- 계산/부분 계산: POST /v1/un/interlife-saju-20

### interlife_source_execution_unverified (confirmed)

원인: S030.db_data [old/unse/interlife/UNSE_DATA/solve/S/S030.asp:22; 호출 1] S048.db_title [old/unse/interlife/UNSE_DATA/solve/S/S048.asp:81; 호출 1] S085.result_var [old/unse/interlife/UNSE_DATA/solve/S/S085.asp:13; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S030.db_data [old/unse/interlife/UNSE_DATA/solve/S/S030.asp:22; 호출 1]
- S048.db_title [old/unse/interlife/UNSE_DATA/solve/S/S048.asp:81; 호출 1]
- S085.result_var [old/unse/interlife/UNSE_DATA/solve/S/S085.asp:13; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_20.asp:30` — UNSE_TITLE = "선천적기질운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_20.asp:30` — UNSE_TITLE = "선천적기질운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 태어난계절에따른운 (interlife-saju-21)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-21
- 계산/부분 계산: POST /v1/un/interlife-saju-21

### interlife_source_execution_unverified (confirmed)

원인: S058.db_title [old/unse/interlife/UNSE_DATA/solve/S/S058.asp:112; 호출 1] T013.db_data [old/unse/interlife/UNSE_DATA/solve/T/T013.asp:8; 호출 1] T022.result_var [old/unse/interlife/UNSE_DATA/solve/T/T022.asp:13; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S058.db_title [old/unse/interlife/UNSE_DATA/solve/S/S058.asp:112; 호출 1]
- T013.db_data [old/unse/interlife/UNSE_DATA/solve/T/T013.asp:8; 호출 1]
- T022.result_var [old/unse/interlife/UNSE_DATA/solve/T/T022.asp:13; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_21.asp:30` — UNSE_TITLE = "태어난계절에따른운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_21.asp:30` — UNSE_TITLE = "태어난계절에따른운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 자평명리학 평생총운 (interlife-saju-3)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-3
- 계산/부분 계산: POST /v1/un/interlife-saju-3

### interlife_source_execution_unverified (confirmed)

원인: S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S022.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S022.asp:13; 호출 1] S027.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S027.asp:11; 호출 1] S064.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S064.asp:7; 호출 1] S067.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S067.asp:7; 호출 1] S068.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S068.asp:7; 호출 1] S082.result_var [old/unse/interlife/UNSE_DATA/solve/S/S082.asp:15; 호출 1] manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S022.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S022.asp:13; 호출 1]
- S027.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S027.asp:11; 호출 1]
- S064.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S064.asp:7; 호출 1]
- S067.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S067.asp:7; 호출 1]
- S068.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S068.asp:7; 호출 1]
- S082.result_var [old/unse/interlife/UNSE_DATA/solve/S/S082.asp:15; 호출 1]
- manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_3.asp:30` — UNSE_TITLE = "자평명리학 평생총운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S022.asp:13` — set rs = ldb.execute("select DB_data, DB_numerical from S022 where DB_express = '"& dang5 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S027.asp:11` — set rs = ldb.execute("select DB_data, DB_numerical from S027 where DB_express = '"& serial_no &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S064.asp:7` — Set rs = ldb.execute("SELECT DB_data_1, DB_numerical FROM S064 WHERE DB_express = '"& my_day_h_org & my_day_e_org &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S067.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM S067 WHERE DB_express = '"& my_hour_e_org &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S068.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM S068 WHERE DB_express = '"& my_day_h_org & my_day_e_org &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_3.asp:30` — UNSE_TITLE = "자평명리학 평생총운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S022.asp:13` — set rs = ldb.execute("select DB_data, DB_numerical from S022 where DB_express = '"& dang5 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S027.asp:11` — set rs = ldb.execute("select DB_data, DB_numerical from S027 where DB_express = '"& serial_no &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S064.asp:7` — Set rs = ldb.execute("SELECT DB_data_1, DB_numerical FROM S064 WHERE DB_express = '"& my_day_h_org & my_day_e_org &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S067.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM S067 WHERE DB_express = '"& my_hour_e_org &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S068.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM S068 WHERE DB_express = '"& my_day_h_org & my_day_e_org &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 인생풀이 (interlife-saju-4)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-4
- 계산/부분 계산: POST /v1/un/interlife-saju-4

### interlife_source_execution_unverified (confirmed)

원인: F011.db_data [old/unse/interlife/UNSE_DATA/solve/F/F011.asp:16; 호출 1] S007.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S007.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S008.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S008.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 3] S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 3] S045.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S045.asp:7; 호출 1] S046.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S046.asp:7; 호출 1] S047.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S047.asp:7; 호출 1] S048.db_title [old/unse/interlife/UNSE_DATA/solve/S/S048.asp:81; 호출 1] S049.db_title [old/unse/interlife/UNSE_DATA/solve/S/S049.asp:106; 호출 1] S050.db_title [old/unse/interlife/UNSE_DATA/solve/S/S050.asp:110; 호출 1] S051.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110; 호출 1] S051.db_title [old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110; 호출 1] S053.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S053.asp:87; 호출 1] S053.result_var [old/unse/interlife/UNSE_DATA/solve/S/S053.asp:87; 호출 1] S054.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1] S054.db_title [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1] S054.result_var [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1] S055.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S055.asp:118; 호출 1] S055.result_var [old/unse/interlife/UNSE_DATA/solve/S/S055.asp:118; 호출 1] S056.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1] S056.db_title [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1] S056.result_var [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1] S057.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S057.asp:114; 호출 1] S057.db_title [old/unse/interlife/UNSE_DATA/solve/S/S057.asp:114; 호출 1] S058.db_title [old/unse/interlife/UNSE_DATA/solve/S/S058.asp:112; 호출 1] S061.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1] S061.result_var [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1] S063.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S063.asp:7; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- F011.db_data [old/unse/interlife/UNSE_DATA/solve/F/F011.asp:16; 호출 1]
- S007.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S007.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S008.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S008.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 3]
- S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 3]
- S045.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S045.asp:7; 호출 1]
- S046.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S046.asp:7; 호출 1]
- S047.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S047.asp:7; 호출 1]
- S048.db_title [old/unse/interlife/UNSE_DATA/solve/S/S048.asp:81; 호출 1]
- S049.db_title [old/unse/interlife/UNSE_DATA/solve/S/S049.asp:106; 호출 1]
- S050.db_title [old/unse/interlife/UNSE_DATA/solve/S/S050.asp:110; 호출 1]
- S051.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110; 호출 1]
- S051.db_title [old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110; 호출 1]
- S053.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S053.asp:87; 호출 1]
- S053.result_var [old/unse/interlife/UNSE_DATA/solve/S/S053.asp:87; 호출 1]
- S054.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1]
- S054.db_title [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1]
- S054.result_var [old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116; 호출 1]
- S055.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S055.asp:118; 호출 1]
- S055.result_var [old/unse/interlife/UNSE_DATA/solve/S/S055.asp:118; 호출 1]
- S056.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1]
- S056.db_title [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1]
- S056.result_var [old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116; 호출 1]
- S057.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S057.asp:114; 호출 1]
- S057.db_title [old/unse/interlife/UNSE_DATA/solve/S/S057.asp:114; 호출 1]
- S058.db_title [old/unse/interlife/UNSE_DATA/solve/S/S058.asp:112; 호출 1]
- S061.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1]
- S061.result_var [old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28; 호출 1]
- S063.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S063.asp:7; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_4.asp:30` — UNSE_TITLE = "인생풀이"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S045.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM S045 WHERE DB_express = '"& my_year_e_org &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S046.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM S046 WHERE DB_express = '"& total_02 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S047.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM S047 WHERE DB_express = '"& total_03 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110` — Set rs = ldb.execute("SELECT DB_title, DB_data, DB_numerical FROM S051 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S053.asp:87` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM S053 WHERE DB_express = '"& total_08 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116` — Set rs = ldb.execute("SELECT DB_title, DB_data, "& choie_data &" as result_var, DB_numerical FROM S054 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S055.asp:118` — Set rs = ldb.execute("SELECT DB_data, "& choie_data &" as result_var, DB_numerical FROM S055 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116` — Set rs = ldb.execute("SELECT DB_title, DB_data, "& choie_data &" as result_var, DB_numerical FROM S056 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S057.asp:114` — Set rs = ldb.execute("SELECT DB_title, DB_data, DB_numerical FROM S057 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM S061 WHERE DB_express = '"& total_11 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S063.asp:7` — Set rs = ldb.execute("select DB_data, DB_numerical from S063 where DB_express = '"& my_year_h_org & my_year_e_org &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_4.asp:30` — UNSE_TITLE = "인생풀이"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S045.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM S045 WHERE DB_express = '"& my_year_e_org &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S046.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM S046 WHERE DB_express = '"& total_02 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S047.asp:7` — Set rs = ldb.execute("SELECT DB_data, DB_numerical FROM S047 WHERE DB_express = '"& total_03 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S051.asp:110` — Set rs = ldb.execute("SELECT DB_title, DB_data, DB_numerical FROM S051 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S053.asp:87` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM S053 WHERE DB_express = '"& total_08 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S054.asp:116` — Set rs = ldb.execute("SELECT DB_title, DB_data, "& choie_data &" as result_var, DB_numerical FROM S054 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S055.asp:118` — Set rs = ldb.execute("SELECT DB_data, "& choie_data &" as result_var, DB_numerical FROM S055 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S056.asp:116` — Set rs = ldb.execute("SELECT DB_title, DB_data, "& choie_data &" as result_var, DB_numerical FROM S056 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S057.asp:114` — Set rs = ldb.execute("SELECT DB_title, DB_data, DB_numerical FROM S057 WHERE DB_express = '"& total_05 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S061.asp:28` — Set rs = ldb.execute("SELECT "& choie_data &" as result_var, DB_numerical FROM S061 WHERE DB_express = '"& total_11 &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S063.asp:7` — Set rs = ldb.execute("select DB_data, DB_numerical from S063 where DB_express = '"& my_year_h_org & my_year_e_org &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 사주운세 (interlife-saju-5)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-5
- 계산/부분 계산: POST /v1/un/interlife-saju-5

### interlife_source_execution_unverified (confirmed)

원인: S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S028.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S028.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S028.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S028.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_5.asp:30` — UNSE_TITLE = "사주운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_5.asp:30` — UNSE_TITLE = "사주운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 십년대운풀이 (interlife-saju-6)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-6
- 계산/부분 계산: POST /v1/un/interlife-saju-6

### interlife_source_execution_unverified (confirmed)

원인: mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465; 호출 1] mansedata.umyear_e [old/unse/interlife/UNSE_DATA/unse/saju/saju_6.asp:47; 호출 1] mansedata.umyear_h [old/unse/interlife/UNSE_DATA/unse/saju/saju_6.asp:47; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465; 호출 1]
- mansedata.umyear_e [old/unse/interlife/UNSE_DATA/unse/saju/saju_6.asp:47; 호출 1]
- mansedata.umyear_h [old/unse/interlife/UNSE_DATA/unse/saju/saju_6.asp:47; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_6.asp:11` — UNSE_TITLE = "십년대운풀이"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_6.asp:47` — Set rs = ldb.execute("SELECT umyear_h, umyear_e FROM mansedata WHERE no = '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_6.asp:11` — UNSE_TITLE = "십년대운풀이"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/saju/saju_6.asp:47` — Set rs = ldb.execute("SELECT umyear_h, umyear_e FROM mansedata WHERE no = '"& current_ymd &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 전생운 (interlife-saju-7)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-7
- 계산/부분 계산: POST /v1/un/interlife-saju-7

### interlife_source_execution_unverified (confirmed)

원인: S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_7.asp:30` — UNSE_TITLE = "전생운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_7.asp:30` — UNSE_TITLE = "전생운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 질병운 (interlife-saju-8)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-8
- 계산/부분 계산: POST /v1/un/interlife-saju-8

### interlife_source_execution_unverified (confirmed)

원인: S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S028.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S028.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1] S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S028.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S028.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:135; 호출 1]
- S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_8.asp:30` — UNSE_TITLE = "질병운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_8.asp:30` — UNSE_TITLE = "질병운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 나의 오행기운세 (interlife-saju-9)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-saju-9
- 계산/부분 계산: POST /v1/un/interlife-saju-9

### interlife_source_execution_unverified (confirmed)

원인: S079.result_var [old/unse/interlife/UNSE_DATA/solve/S/S079.asp:15; 호출 1] S080.result_var [old/unse/interlife/UNSE_DATA/solve/S/S080.asp:15; 호출 1] S081.result_var [old/unse/interlife/UNSE_DATA/solve/S/S081.asp:13; 호출 1] S082.result_var [old/unse/interlife/UNSE_DATA/solve/S/S082.asp:15; 호출 1] S083.result_var [old/unse/interlife/UNSE_DATA/solve/S/S083.asp:16; 호출 1] S084.result_var [old/unse/interlife/UNSE_DATA/solve/S/S084.asp:16; 호출 1] S085.result_var [old/unse/interlife/UNSE_DATA/solve/S/S085.asp:13; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S079.result_var [old/unse/interlife/UNSE_DATA/solve/S/S079.asp:15; 호출 1]
- S080.result_var [old/unse/interlife/UNSE_DATA/solve/S/S080.asp:15; 호출 1]
- S081.result_var [old/unse/interlife/UNSE_DATA/solve/S/S081.asp:13; 호출 1]
- S082.result_var [old/unse/interlife/UNSE_DATA/solve/S/S082.asp:15; 호출 1]
- S083.result_var [old/unse/interlife/UNSE_DATA/solve/S/S083.asp:16; 호출 1]
- S084.result_var [old/unse/interlife/UNSE_DATA/solve/S/S084.asp:16; 호출 1]
- S085.result_var [old/unse/interlife/UNSE_DATA/solve/S/S085.asp:13; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_9.asp:30` — UNSE_TITLE = "나의 오행기운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/saju/saju_9.asp:30` — UNSE_TITLE = "나의 오행기운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 결혼택일 (interlife-selectDay-1)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-selectDay-1
- 계산/부분 계산: POST /v1/un/interlife-selectDay-1

### interlife_source_execution_unverified (confirmed)

원인: mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9] mansedata.no [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:249; 호출 1] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9]
- mansedata.no [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:249; 호출 1]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 10]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 11]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 12]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 13]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 14]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 15]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 16]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 17]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 18]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 19]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 20]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 21]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 22]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 23]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 24]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 25]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 26]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 27]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 28]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 29]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 2]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 30]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 3]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 4]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 5]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 6]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 7]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 8]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317; 호출 9]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/selectDay/selectDay_1.asp:14` — UNSE_TITLE = "결혼택일"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& your_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = '"& your_number &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S111.asp:238` — Set rs = ldb.execute("SELECT no, year_e FROM mansedata WHERE umdate = '"& temp_lunar &"' and youn = '"& youn &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S111.asp:249` — Set rs = ldb.execute("SELECT no, year_e FROM mansedata WHERE no = '"& temp_solar &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e, day_h, day_e, jeol, umdate FROM mansedata WHERE no = '"& j &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/selectDay/selectDay_1.asp:14` — UNSE_TITLE = "결혼택일"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:10` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& your_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha_your.asp:35` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = '"& your_number &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S111.asp:238` — Set rs = ldb.execute("SELECT no, year_e FROM mansedata WHERE umdate = '"& temp_lunar &"' and youn = '"& youn &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S111.asp:249` — Set rs = ldb.execute("SELECT no, year_e FROM mansedata WHERE no = '"& temp_solar &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S111.asp:317` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e, day_h, day_e, jeol, umdate FROM mansedata WHERE no = '"& j &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 이사택일 (interlife-selectDay-2)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-selectDay-2
- 계산/부분 계산: POST /v1/un/interlife-selectDay-2

### interlife_source_execution_unverified (confirmed)

원인: mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9] mansedata.no [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:246; 호출 1] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9]
- mansedata.no [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:246; 호출 1]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 10]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 11]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 12]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 13]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 14]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 15]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 16]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 17]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 18]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 19]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 20]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 21]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 22]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 23]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 24]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 25]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 26]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 27]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 28]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 29]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 2]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 30]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 3]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 4]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 5]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 6]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 7]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 8]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311; 호출 9]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/selectDay/selectDay_2.asp:10` — UNSE_TITLE = "이사택일"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/S/S112.asp:235` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE umdate = '"& temp_lunar &"' and youn = '"& youn &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S112.asp:246` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& temp_solar &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& j &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/selectDay/selectDay_2.asp:10` — UNSE_TITLE = "이사택일"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/S/S112.asp:235` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE umdate = '"& temp_lunar &"' and youn = '"& youn &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S112.asp:246` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& temp_solar &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S112.asp:311` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no = '"& j &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 특정일운세 (interlife-selectDay-3)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-selectDay-3
- 계산/부분 계산: POST /v1/un/interlife-selectDay-3

### interlife_source_execution_unverified (confirmed)

원인: S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/selectDay/selectDay_3.asp:30` — UNSE_TITLE = "특정일운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/selectDay/selectDay_3.asp:30` — UNSE_TITLE = "특정일운세"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 천생운 (interlife-theme-1)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-1
- 계산/부분 계산: POST /v1/un/interlife-theme-1

### interlife_source_execution_unverified (confirmed)

원인: T023.db_numerical [old/unse/interlife/UNSE_DATA/solve/T/T023.asp:13; 호출 1] T023.result_var [old/unse/interlife/UNSE_DATA/solve/T/T023.asp:13; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- T023.db_numerical [old/unse/interlife/UNSE_DATA/solve/T/T023.asp:13; 호출 1]
- T023.result_var [old/unse/interlife/UNSE_DATA/solve/T/T023.asp:13; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_1.asp:30` — UNSE_TITLE = "천생운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/T/T023.asp:13` — set rs = ldb.execute("select "& choie_data &" as result_var, DB_numerical from T023 where DB_express = '"& serial_no &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_1.asp:30` — UNSE_TITLE = "천생운"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/T/T023.asp:13` — set rs = ldb.execute("select "& choie_data &" as result_var, DB_numerical from T023 where DB_express = '"& serial_no &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 현재 운세풀이 (interlife-theme-10)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-10
- 계산/부분 계산: POST /v1/un/interlife-theme-10

### interlife_source_execution_unverified (confirmed)

원인: S013.db_data [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:198; 호출 1] S013.db_data [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208; 호출 1] S013.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208; 호출 1] S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1] T023.db_numerical [old/unse/interlife/UNSE_DATA/solve/T/T023.asp:13; 호출 1] T023.result_var [old/unse/interlife/UNSE_DATA/solve/T/T023.asp:13; 호출 1] manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S013.db_data [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:198; 호출 1]
- S013.db_data [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208; 호출 1]
- S013.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208; 호출 1]
- S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1]
- T023.db_numerical [old/unse/interlife/UNSE_DATA/solve/T/T023.asp:13; 호출 1]
- T023.result_var [old/unse/interlife/UNSE_DATA/solve/T/T023.asp:13; 호출 1]
- manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_10.asp:30` — UNSE_TITLE = "현재 운세풀이"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S013 where DB_express = '"& toYG_sibsin+1 &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/T/T023.asp:13` — set rs = ldb.execute("select "& choie_data &" as result_var, DB_numerical from T023 where DB_express = '"& serial_no &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_10.asp:30` — UNSE_TITLE = "현재 운세풀이"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S013 where DB_express = '"& toYG_sibsin+1 &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/T/T023.asp:13` — set rs = ldb.execute("select "& choie_data &" as result_var, DB_numerical from T023 where DB_express = '"& serial_no &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 현재나의운 분석 (interlife-theme-11)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-11
- 계산/부분 계산: POST /v1/un/interlife-theme-11

### interlife_source_execution_unverified (confirmed)

원인: S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_11.asp:30` — UNSE_TITLE = "현재나의운 분석"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_11.asp:30` — UNSE_TITLE = "현재나의운 분석"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 사업운총평 (interlife-theme-12)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-12
- 계산/부분 계산: POST /v1/un/interlife-theme-12

### interlife_source_execution_unverified (confirmed)

원인: S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S058.db_title [old/unse/interlife/UNSE_DATA/solve/S/S058.asp:112; 호출 1] manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S058.db_title [old/unse/interlife/UNSE_DATA/solve/S/S058.asp:112; 호출 1]
- manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_12.asp:30` — UNSE_TITLE = "사업운총평"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_12.asp:30` — UNSE_TITLE = "사업운총평"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 재물 모으는 법 (interlife-theme-13)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-13
- 계산/부분 계산: POST /v1/un/interlife-theme-13

### interlife_source_execution_unverified (confirmed)

원인: S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S058.db_title [old/unse/interlife/UNSE_DATA/solve/S/S058.asp:112; 호출 1] manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S_S087_S092_sol.asp:8; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S_S087_S092_sol.asp:8; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S058.db_title [old/unse/interlife/UNSE_DATA/solve/S/S058.asp:112; 호출 1]
- manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/S_S087_S092_sol.asp:8; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/S_S087_S092_sol.asp:8; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_13.asp:30` — UNSE_TITLE = "재물 모으는 법"
- `old/unse/interlife/UNSE_DATA/solve/S_S087_S092_sol.asp:8` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_13.asp:30` — UNSE_TITLE = "재물 모으는 법"
- `old/unse/interlife/UNSE_DATA/solve/S_S087_S092_sol.asp:8` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 재물손실 막는 법 (interlife-theme-14)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-14
- 계산/부분 계산: POST /v1/un/interlife-theme-14

### interlife_source_execution_unverified (confirmed)

원인: S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_e [old/unse/interlife/UNSE_DATA/unse/theme/theme_14.asp:67; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/unse/theme/theme_14.asp:67; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/unse/theme/theme_14.asp:67; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/unse/theme/theme_14.asp:67; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_14.asp:30` — UNSE_TITLE = "재물손실 막는 법"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/theme/theme_14.asp:67` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_14.asp:30` — UNSE_TITLE = "재물손실 막는 법"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/theme/theme_14.asp:67` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 재테크비법 (interlife-theme-15)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-15
- 계산/부분 계산: POST /v1/un/interlife-theme-15

### interlife_finance_selector_profile_unverified (confirmed)

원인: 원본 mansedata의 A~J·01~12 간지/number/jeolip와 tb_manse 원시 간지·절입 필드의 대응이 미검증입니다. 기본 달력 후보와 원본 산술을 제공하며 원본 최종 판정으로 확정하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- 원본 nam/nam4 배열·일간·합성키의 실행 대조 결과

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_15.asp:30` — UNSE_TITLE = "재테크비법"
- `old/unse/interlife/UNSE_DATA/unse/theme/theme_15.asp:11` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/theme/theme_15.asp:67` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_extra의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_15.asp:30` — UNSE_TITLE = "재테크비법"
- `old/unse/interlife/UNSE_DATA/unse/theme/theme_15.asp:11` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/unse/theme/theme_15.asp:67` — Set rs = ldb.execute("SELECT day_h, day_e FROM mansedata WHERE no like '"& signdate &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 타로점성술 (interlife-theme-2)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-2
- 계산/부분 계산: POST /v1/un/interlife-theme-2

### interlife_tarot_classification_missing (confirmed)

원인: T043의 실제 카드명과 S009의 실제 성씨 자료가 미확보입니다. AI가 사실 이름을 임의로 붙이지 않습니다. F019의 성별별 吉/凶/半吉半凶 실제 분류가 없어 색상·기호와 최종 길흉 판정을 확정할 수 없습니다. 원본 mansedata 년지/월지와 f_Saju·서버 일간의 코드 바인딩을 검증해야 하며 조사용 source_fields는 원본 DB 검증을 대체하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- F019.DB_express/DB_express_1 실제 길흉 분류
- T043.DB_title 실제 카드명
- S009.DB_data 실제 성씨
- mansedata year_e/month_e 및 f_Saju/용신 코드 매핑

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_2.asp:64` — UNSE_TITLE = "타로점성술"
- `old/unse/interlife/UNSE_DATA/solve/F/F019.asp:65` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_dependencies의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_2.asp:64` — UNSE_TITLE = "타로점성술"
- `old/unse/interlife/UNSE_DATA/solve/F/F019.asp:65` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 신통방통 동전점 (interlife-theme-3)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-3
- 계산/부분 계산: POST /v1/un/interlife-theme-3

### interlife_coin_classification_missing (confirmed)

원인: F019의 성별별 吉/凶/半吉半凶 실제 분류가 없어 색상·기호와 최종 길흉 판정을 확정할 수 없습니다. 원본 mansedata 년지/월지와 f_Saju·서버 일간의 코드 바인딩을 검증해야 하며 조사용 source_fields는 원본 DB 검증을 대체하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- F019.DB_express/DB_express_1 실제 길흉 분류
- mansedata.year_e 원본 년지 의미

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_3.asp:64` — UNSE_TITLE = "신통방통 동전점"
- `old/unse/interlife/UNSE_DATA/solve/F/F019.asp:65` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_dependencies의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_3.asp:64` — UNSE_TITLE = "신통방통 동전점"
- `old/unse/interlife/UNSE_DATA/solve/F/F019.asp:65` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 탄생석점 (interlife-theme-4)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-4
- 계산/부분 계산: POST /v1/un/interlife-theme-4

### interlife_birthstone_classification_missing (confirmed)

원인: F019의 성별별 吉/凶/半吉半凶 실제 분류가 없어 색상·기호와 최종 길흉 판정을 확정할 수 없습니다. 원본 mansedata 년지/월지와 f_Saju·서버 일간의 코드 바인딩을 검증해야 하며 조사용 source_fields는 원본 DB 검증을 대체하지 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- F019.DB_express/DB_express_1 실제 길흉 분류
- mansedata.year_e 원본 년지 의미

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_4.asp:30` — UNSE_TITLE = "탄생석점"
- `old/unse/interlife/UNSE_DATA/solve/F/F019.asp:65` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_dependencies의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_4.asp:30` — UNSE_TITLE = "탄생석점"
- `old/unse/interlife/UNSE_DATA/solve/F/F019.asp:65` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 나의길흉숫자 (interlife-theme-5)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-5
- 계산/부분 계산: POST /v1/un/interlife-theme-5

### interlife_source_execution_unverified (confirmed)

원인: S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1] S058.db_title [old/unse/interlife/UNSE_DATA/solve/S/S058.asp:112; 호출 1] T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1]
- S058.db_title [old/unse/interlife/UNSE_DATA/solve/S/S058.asp:112; 호출 1]
- T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_5.asp:30` — UNSE_TITLE = "나의길흉숫자"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_5.asp:30` — UNSE_TITLE = "나의길흉숫자"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 방위점 (interlife-theme-6)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-6
- 계산/부분 계산: POST /v1/un/interlife-theme-6

### interlife_source_execution_unverified (confirmed)

원인: J048.db_data [old/unse/interlife/UNSE_DATA/solve/J/J048.asp:11; 호출 1] S013.db_data [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:198; 호출 1] S013.db_data [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208; 호출 1] S013.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208; 호출 1] manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- J048.db_data [old/unse/interlife/UNSE_DATA/solve/J/J048.asp:11; 호출 1]
- S013.db_data [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:198; 호출 1]
- S013.db_data [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208; 호출 1]
- S013.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208; 호출 1]
- manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_6.asp:30` — UNSE_TITLE = "방위점"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S013 where DB_express = '"& toYG_sibsin+1 &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_6.asp:30` — UNSE_TITLE = "방위점"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S013 where DB_express = '"& toYG_sibsin+1 &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:268` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot &"'")
- `old/unse/interlife/UNSE_DATA/solve/yukhyo.asp:307` — Set rs = ldb.execute("SELECT * FROM juyek_6hyo WHERE juyek like  '"& num_tot_jigue &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 나의 수호천사와 타로점 (interlife-theme-7)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-7
- 계산/부분 계산: POST /v1/un/interlife-theme-7

### interlife_source_execution_unverified (confirmed)

원인: S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1] S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1] S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1] T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1] manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1] manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S009.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S009.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 1]
- S010.db_data [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S010.db_numerical [old/unse/interlife/UNSE_DATA/common/function.asp:425; 호출 2]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:198; 호출 1]
- S014.db_data [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- S014.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208; 호출 1]
- T028.db_data [old/unse/interlife/UNSE_DATA/solve/T/T028.asp:12; 호출 1]
- manse_data.2 [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54; 호출 1]
- manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_7.asp:64` — UNSE_TITLE = "나의수호타로점"
- `old/unse/interlife/incs/info.asp:105` — theme menuNAME: 나의수호천사와타로점
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_7.asp:64` — UNSE_TITLE = "나의수호타로점"
- `old/unse/interlife/incs/info.asp:105` — theme menuNAME: 나의수호천사와타로점
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S014.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S014 where DB_express = '"& toYG_sibsin &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 나의별자리사랑 (interlife-theme-8)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-8
- 계산/부분 계산: POST /v1/un/interlife-theme-8

### interlife_source_execution_unverified (confirmed)

원인: G019.db_data [old/unse/interlife/UNSE_DATA/solve/G/G019.asp:7; 호출 1] G024.result_var [old/unse/interlife/UNSE_DATA/solve/G/G024.asp:29; 호출 1] G024.result_var [old/unse/interlife/UNSE_DATA/solve/G/G024.asp:33; 호출 1] G033.ADO_getrows [old/unse/interlife/UNSE_DATA/solve/G/G033.asp:63; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] toC_manse_sub.ADO_getrows [old/unse/interlife/UNSE_DATA/solve/G/G034.asp:36; 호출 1] toC_yongsin_01.ADO_bof [old/unse/interlife/UNSE_DATA/unse/theme/theme_8.asp:78; 호출 1] toC_yongsin_01.ADO_eof [old/unse/interlife/UNSE_DATA/unse/theme/theme_8.asp:78; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- G019.db_data [old/unse/interlife/UNSE_DATA/solve/G/G019.asp:7; 호출 1]
- G024.result_var [old/unse/interlife/UNSE_DATA/solve/G/G024.asp:29; 호출 1]
- G024.result_var [old/unse/interlife/UNSE_DATA/solve/G/G024.asp:33; 호출 1]
- G033.ADO_getrows [old/unse/interlife/UNSE_DATA/solve/G/G033.asp:63; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- toC_manse_sub.ADO_getrows [old/unse/interlife/UNSE_DATA/solve/G/G034.asp:36; 호출 1]
- toC_yongsin_01.ADO_bof [old/unse/interlife/UNSE_DATA/unse/theme/theme_8.asp:78; 호출 1]
- toC_yongsin_01.ADO_eof [old/unse/interlife/UNSE_DATA/unse/theme/theme_8.asp:78; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_8.asp:30` — UNSE_TITLE = "나의별자리사랑"
- `old/unse/interlife/UNSE_DATA/solve/G/G034.asp:36` — Set rs = ldb.execute("SELECT umyear_h, umyear_e, no FROM toC_manse_sub WHERE umyear_e = '"& choice_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:23` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"' or umyear_e = '"& s_umyear_e3 &"' or umyear_e = '"& s_umyear_e4 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:32` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:41` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:50` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:59` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:453` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:462` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:471` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:480` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:491` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"' or umyear_e = '"& s_umyear_e3 &"' or umyear_e = '"& s_umyear_e4 &"'"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/theme/theme_8.asp:78` — Set rs = ldb.execute("SELECT * FROM toC_yongsin_01 WHERE title = '"& my_day_h & my_month_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_8.asp:30` — UNSE_TITLE = "나의별자리사랑"
- `old/unse/interlife/UNSE_DATA/solve/G/G034.asp:36` — Set rs = ldb.execute("SELECT umyear_h, umyear_e, no FROM toC_manse_sub WHERE umyear_e = '"& choice_var &"'")
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:23` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"' or umyear_e = '"& s_umyear_e3 &"' or umyear_e = '"& s_umyear_e4 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:32` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:41` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:50` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:59` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:453` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:462` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:471` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:480` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"'"
- `old/unse/interlife/UNSE_DATA/solve/G/G033.asp:491` — sql = "SELECT umyear_h, umyear_e, umyear_ho, umyear_eo, no FROM toC_manse_sub  WHERE umyear_h = '"& s_umyear_h1 &"' or umyear_h = '"& s_umyear_h2 &"' or umyear_e = '"& s_umyear_e1 &"' or umyear_e = '"& s_umyear_e2 &"' or umyear_e = '"& s_umyear_e3 &"' or umyear_e = '"& s_umyear_e4 &"'"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/unse/theme/theme_8.asp:78` — Set rs = ldb.execute("SELECT * FROM toC_yongsin_01 WHERE title = '"& my_day_h & my_month_e &"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 피해야할상대 (interlife-theme-9)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-theme-9
- 계산/부분 계산: POST /v1/un/interlife-theme-9

### interlife_source_execution_unverified (confirmed)

원인: S013.db_data [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:198; 호출 1] S013.db_data [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208; 호출 1] S013.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208; 호출 1] S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1] manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1] source_policy.source_terms_required

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- S013.db_data [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:198; 호출 1]
- S013.db_data [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208; 호출 1]
- S013.db_numerical [old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208; 호출 1]
- S040.db_data [old/unse/interlife/UNSE_DATA/solve/S/S040.asp:22; 호출 1]
- manse_data.weul [old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.jeolip [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30; 호출 1]
- source_policy.source_terms_required

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_9.asp:30` — UNSE_TITLE = "피해야할상대"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S013 where DB_express = '"& toYG_sibsin+1 &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 독립 계산용 div24.dat/suntolun.dat 원본 파일이 보관되어 있습니다. 데이터 전무로 분류하지 않습니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/theme/theme_9.asp:30` — UNSE_TITLE = "피해야할상대"
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:7` — Set rs = ldb.execute("SELECT number, day_h, day_e, jeolip FROM mansedata WHERE no = '"& my_ymd_jeolip &"'")
- `old/unse/interlife/UNSE_DATA/solve/sajujowha.asp:30` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e FROM mansedata WHERE number = "& my_number)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:465` — Set rs = ldb.execute("select umdate from mansedata where no = "& current_yy)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:475` — Set rs = ldb.execute("SELECT number, jeolip FROM mansedata WHERE no = "& no)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:497` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/daeun_sipsin.asp:534` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE number = "& i)
- `old/unse/interlife/UNSE_DATA/solve/S/S013.asp:208` — set rs = ldb.execute("select DB_data, DB_numerical from S013 where DB_express = '"& toYG_sibsin+1 &"-"& woon_z &"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:8` — set rs = ldb.execute("select * from manse_data where neun='"& Year(Now) &"' and weul='2'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:54` — set rs = ldb.execute("select * from manse_data where neun='"&toyear&"' and weul='"&tomonth&"'")
- `old/unse/interlife/UNSE_DATA/solve/saju_date.asp:161` — set rs = ldb.execute("select * from manse_data where neun='"&sunY&"' and weul='"&sunM&"'")
- `old/unse/interlife/UNSE_DATA/solve/f_Saju.asp:2902` — GetFile의 윤달 파일 경로와 저장소 파일 위치가 다름

## 육임정단 (interlife-yukim-1)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-yukim-1
- 계산/부분 계산: POST /v1/un/interlife-yukim-1

### interlife_woljang_classification_unverified (confirmed)

원인: mansedata.woljang 원본 날짜별 월장과 일간 값의 검증 자료가 필요합니다. 입력 조사값만으로 원본 판정이 검증되지는 않습니다.

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 명시된 판정 필드·입력 바인딩·실행 상태를 확보하거나 보관된 원본 계약으로 검증합니다.
2. 확정한 키·필드와 경계 대조 테스트를 통과시킨 뒤 해당 문구 항목에만 AI 생성을 연결합니다.

필요 자료:

- mansedata.woljang 날짜별 월장
- mansedata.day_h 원본 일간

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/yukim/yukim_1.asp:5` — UNSE_TITLE = "육임정단"
- `old/unse/interlife/UNSE_DATA/solve/J/J045.asp:37` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/J/J045.asp:37` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e, day_h, day_e, umdate, youn, jeol, woljang FROM mansedata WHERE no like  '"& today_day &"'")

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_dependencies의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/yukim/yukim_1.asp:5` — UNSE_TITLE = "육임정단"
- `old/unse/interlife/UNSE_DATA/solve/J/J045.asp:37` — T-023/T-024 실제 leaf 실행 계약 재검토
- `old/unse/interlife/UNSE_DATA/solve/J/J045.asp:37` — Set rs = ldb.execute("SELECT year_h, year_e, month_h, month_e, day_h, day_e, umdate, youn, jeol, woljang FROM mansedata WHERE no like  '"& today_day &"'")

## 지두법(길흉속지법) (interlife-yukim-2)

- 상태: source_required · Python 부분 계산 완료 · 판정 자료/계약 필요
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-yukim-2
- 계산/부분 계산: POST /v1/un/interlife-yukim-2

### interlife_source_execution_unverified (confirmed)

원인: J052.cnt [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:592; 호출 1] mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2] mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1] mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1] mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1] mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1] mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1] mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1] mansedata.woljang [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1] mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1] mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1] mansedata.youn [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1] yukim_720.gongmang_01 [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:325; 호출 1] yukim_720.gongmang_02 [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:325; 호출 1]

영향: 현재 부분 계산과 자료 진단만 제공합니다. 미확정 판정값을 AI가 대신 생성하지 않습니다.

해결:

1. 아래 실제 소비 테이블·컬럼과 원본 실행 상태를 확보합니다.
2. 검증된 서버 자료 저장소를 연결하고 상용 입출력 사례로 분기·선택값을 대조합니다.
3. 조사 입력 source_rows는 정답 자료의 인증을 뜻하지 않으며 AI 차단을 해제하지 않습니다.

필요 자료:

- J052.cnt [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:592; 호출 1]
- mansedata.ADO_eof [old/unse/interlife/UNSE_DATA/common/function.asp:512; 호출 2]
- mansedata.day_e [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1]
- mansedata.day_h [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1]
- mansedata.jeol [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1]
- mansedata.month_e [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1]
- mansedata.month_h [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1]
- mansedata.umdate [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1]
- mansedata.woljang [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1]
- mansedata.year_e [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1]
- mansedata.year_h [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1]
- mansedata.youn [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12; 호출 1]
- yukim_720.gongmang_01 [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:325; 호출 1]
- yukim_720.gongmang_02 [old/unse/interlife/UNSE_DATA/solve/J/J052.asp:325; 호출 1]

판단 근거:

- `old/unse/interlife/UNSE_DATA/unse/yukim/yukim_2.asp:5` — UNSE_TITLE = "지두법(길흉속지법)"
- `old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like '"& no &"'")
- `old/unse/interlife/UNSE_DATA/solve/J/J052.asp:325` — Set rs = ldb.execute("SELECT * FROM yukim_720 WHERE ganji like  '"& llday &"' and guk like  '"& temp_guk &"'")

검토 범위/실행 제약:

- 동일 이름의 기존 Python API가 있더라도 이 엔진과 동일하다고 간주하지 않습니다.
- include/solve를 포함하는 정적 조사이며 실제 ASP/DB 실행 대조는 미실행입니다.
- 공통 헤더 include로 모든 서비스가 육효 DB를 사용하는 것으로 오판하지 않도록 yukhyo_data=N인 항목에서 해당 헤더 후손 의존성을 제외했습니다. 미지정 값은 동적 호출 전에는 필요 여부를 단정하지 않습니다.
- CR-012 / T-024: app.ported_interlife_leaves의 기본 예시 계산/선택키 계약을 확인했습니다. ASP 서버·DLL·AI 실호출 등가 검증을 뜻하지 않습니다.

원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/yukim/yukim_2.asp:5` — UNSE_TITLE = "지두법(길흉속지법)"
- `old/unse/interlife/UNSE_DATA/solve/J/J052.asp:12` — Set rs = ldb.execute("SELECT * FROM mansedata WHERE no like '"& no &"'")
- `old/unse/interlife/UNSE_DATA/solve/J/J052.asp:325` — Set rs = ldb.execute("SELECT * FROM yukim_720 WHERE ganji like  '"& llday &"' and guk like  '"& temp_guk &"'")

## 자동이름풀이 (공통 결과 처리) (interlife-name-puri)

- 상태: reference · 묶음·보조 코드 · 개별 계산 대상 아님
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-name-puri

검토 범위/실행 제약:


원본 근거:

- `old/unse/interlife/UNSE_DATA/unse/name/name_puri.asp:10` — UNSE_TITLE = "자동이름풀이"

## 미니만세력 (interlife-free-9)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-free-9

### result_source_missing (confirmed)

원인: moneyDATA.dat에는 선언되어 있지만 저장소에 해당 결과 ASP가 없습니다.

영향: 원본 결과 파일을 분석할 수 없어 해당 서비스의 동일 이식이 불가능합니다.

해결:

1. 원본 ASP 결과 파일 및 연결된 계산 자료 확보 후 분석·이식합니다.

필요 자료:

- 누락된 old/unse/interlife/UNSE_DATA/unse/free/free_9.asp와 연결 계산 자료

판단 근거:

- `old/unse/interlife/data/moneyDATA.dat:22` — 원본 연결 선언

검토 범위/실행 제약:


원본 근거:

- `old/unse/interlife/data/moneyDATA.dat:22` — 원본 연결 선언

## 일반만세력 (interlife-free-10)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/unse/interlife`
- 진단: GET /v1/asp-services/interlife-free-10

### result_source_missing (confirmed)

원인: moneyDATA.dat에는 선언되어 있지만 저장소에 해당 결과 ASP가 없습니다.

영향: 원본 결과 파일을 분석할 수 없어 해당 서비스의 동일 이식이 불가능합니다.

해결:

1. 원본 ASP 결과 파일 및 연결된 계산 자료 확보 후 분석·이식합니다.

필요 자료:

- 누락된 old/unse/interlife/UNSE_DATA/unse/free/free_10.asp와 연결 계산 자료

판단 근거:

- `old/unse/interlife/data/moneyDATA.dat:22` — 원본 연결 선언

검토 범위/실행 제약:


원본 근거:

- `old/unse/interlife/data/moneyDATA.dat:22` — 원본 연결 선언

## 좋은글 알림SMS (missing-todayprovluck)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/unse/todayprovluck`
- 진단: GET /v1/asp-services/missing-todayprovluck

### result_source_missing (confirmed)

원인: 원본 메뉴가 가리키는 old/unse/todayprovluck/main.asp 파일이 현재 보관본에 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- old/unse/todayprovluck/main.asp 및 연결된 계산 코드

판단 근거:

- `old/side_include/sub_unse.asp:34` — 원본 메뉴에 존재하나 대상 소스 없음

검토 범위/실행 제약:

- UI 메뉴 선언은 있으나 현재 보관본에 구현 파일이 없어 원본 판정 이식이 불가능하다.

원본 근거:

- `old/side_include/sub_unse.asp:34` — 원본 메뉴에 존재하나 대상 소스 없음

## 월운세 바탕화면 (missing-monthbgluck)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/unse/monthbgluck`
- 진단: GET /v1/asp-services/missing-monthbgluck

### result_source_missing (confirmed)

원인: 원본 메뉴가 가리키는 old/unse/monthbgluck/main_end.asp 파일이 현재 보관본에 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- old/unse/monthbgluck/main_end.asp 및 연결된 계산 코드

판단 근거:

- `old/side_include/sub_unse.asp:40` — 원본 메뉴에 존재하나 대상 소스 없음

검토 범위/실행 제약:

- UI 메뉴 선언은 있으나 현재 보관본에 구현 파일이 없어 원본 판정 이식이 불가능하다.

원본 근거:

- `old/side_include/sub_unse.asp:40` — 원본 메뉴에 존재하나 대상 소스 없음

## 나의 인생스타일 (missing-comforyou)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/unse/comforyou`
- 진단: GET /v1/asp-services/missing-comforyou

### result_source_missing (confirmed)

원인: 원본 메뉴가 가리키는 old/unse/comforyou/richsaju/default.asp 파일이 현재 보관본에 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- old/unse/comforyou/richsaju/default.asp 및 연결된 계산 코드

판단 근거:

- `old/side_include/sub_unse.asp:55` — 원본 메뉴에 존재하나 대상 소스 없음

검토 범위/실행 제약:

- UI 메뉴 선언은 있으나 현재 보관본에 구현 파일이 없어 원본 판정 이식이 불가능하다.

원본 근거:

- `old/side_include/sub_unse.asp:55` — 원본 메뉴에 존재하나 대상 소스 없음

## 도통 만세력 (missing-manseluck)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/unse/manseluck`
- 진단: GET /v1/asp-services/missing-manseluck

### result_source_missing (confirmed)

원인: 원본 메뉴가 가리키는 old/unse/manseluck/main.asp 파일이 현재 보관본에 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- old/unse/manseluck/main.asp 및 연결된 계산 코드

판단 근거:

- `old/side_include/sub_unse.asp:155` — 원본 메뉴에 존재하나 대상 소스 없음

검토 범위/실행 제약:

- UI 메뉴 선언은 있으나 현재 보관본에 구현 파일이 없어 원본 판정 이식이 불가능하다.

원본 근거:

- `old/side_include/sub_unse.asp:155` — 원본 메뉴에 존재하나 대상 소스 없음

## 주식투자에 좋은 사주는? (stockluck-m1)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/unse/stockluck`
- 진단: GET /v1/asp-services/stockluck-m1

### result_source_missing (confirmed)

원인: 원본 메뉴가 가리키는 old/unse/stockluck/main.asp 파일이 현재 보관본에 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- old/unse/stockluck/main.asp 및 연결된 계산 코드

판단 근거:

- `old/side_include/sub_unse.asp:172` — pflag별 별도 메뉴 서비스

검토 범위/실행 제약:

- 메뉴별 pflag가 달라 독립 소서비스 선언이다. stockluck 소스 폴더 미확보.

원본 근거:

- `old/side_include/sub_unse.asp:172` — pflag별 별도 메뉴 서비스

## 무료 대박주식운세 (stockluck-m2)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/unse/stockluck`
- 진단: GET /v1/asp-services/stockluck-m2

### result_source_missing (confirmed)

원인: 원본 메뉴가 가리키는 old/unse/stockluck/main.asp 파일이 현재 보관본에 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- old/unse/stockluck/main.asp 및 연결된 계산 코드

판단 근거:

- `old/side_include/sub_unse.asp:173` — pflag별 별도 메뉴 서비스

검토 범위/실행 제약:

- 메뉴별 pflag가 달라 독립 소서비스 선언이다. stockluck 소스 폴더 미확보.

원본 근거:

- `old/side_include/sub_unse.asp:173` — pflag별 별도 메뉴 서비스

## 사주추천종목알림이SMS (stockluck-m6)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/unse/stockluck`
- 진단: GET /v1/asp-services/stockluck-m6

### result_source_missing (confirmed)

원인: 원본 메뉴가 가리키는 old/unse/stockluck/main.asp 파일이 현재 보관본에 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- old/unse/stockluck/main.asp 및 연결된 계산 코드

판단 근거:

- `old/side_include/sub_unse.asp:175` — pflag별 별도 메뉴 서비스

검토 범위/실행 제약:

- 메뉴별 pflag가 달라 독립 소서비스 선언이다. stockluck 소스 폴더 미확보.

원본 근거:

- `old/side_include/sub_unse.asp:175` — pflag별 별도 메뉴 서비스

## 프리미엄 대박주식운세 (stockluck-m3)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/unse/stockluck`
- 진단: GET /v1/asp-services/stockluck-m3

### result_source_missing (confirmed)

원인: 원본 메뉴가 가리키는 old/unse/stockluck/main.asp 파일이 현재 보관본에 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- old/unse/stockluck/main.asp 및 연결된 계산 코드

판단 근거:

- `old/side_include/sub_unse.asp:176` — pflag별 별도 메뉴 서비스

검토 범위/실행 제약:

- 메뉴별 pflag가 달라 독립 소서비스 선언이다. stockluck 소스 폴더 미확보.

원본 근거:

- `old/side_include/sub_unse.asp:176` — pflag별 별도 메뉴 서비스

## 급등주 대박주식운세 (stockluck-m4)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/unse/stockluck`
- 진단: GET /v1/asp-services/stockluck-m4

### result_source_missing (confirmed)

원인: 원본 메뉴가 가리키는 old/unse/stockluck/main.asp 파일이 현재 보관본에 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- old/unse/stockluck/main.asp 및 연결된 계산 코드

판단 근거:

- `old/side_include/sub_unse.asp:177` — pflag별 별도 메뉴 서비스

검토 범위/실행 제약:

- 메뉴별 pflag가 달라 독립 소서비스 선언이다. stockluck 소스 폴더 미확보.

원본 근거:

- `old/side_include/sub_unse.asp:177` — pflag별 별도 메뉴 서비스

## 기운보강 + 주식부적 (stockluck-m5)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/unse/stockluck`
- 진단: GET /v1/asp-services/stockluck-m5

### result_source_missing (confirmed)

원인: 원본 메뉴가 가리키는 old/unse/stockluck/main.asp 파일이 현재 보관본에 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- old/unse/stockluck/main.asp 및 연결된 계산 코드

판단 근거:

- `old/side_include/sub_unse.asp:178` — pflag별 별도 메뉴 서비스

검토 범위/실행 제약:

- 메뉴별 pflag가 달라 독립 소서비스 선언이다. stockluck 소스 폴더 미확보.

원본 근거:

- `old/side_include/sub_unse.asp:178` — pflag별 별도 메뉴 서비스

## 적중 2012 토정비결 (external-video-b)

- 상태: source_required · 외부 제공사 구현 미확보 · 생성 차단
- 원본: `외부 제공사 서비스`
- 진단: GET /v1/asp-services/external-video-b

### external_implementation_missing (confirmed)

원인: 외부 사이트 입력 페이지로 연결하며 이 저장소에는 해당 제공사의 결과 계산 코드가 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- 제공사 소스/연동 명세 및 대조 결과

판단 근거:

- `old/side_include/sub_unse.asp:124` — 외부 동영상 서비스 링크

검토 범위/실행 제약:

- 외부 공급자의 서비스이며 이 저장소에는 판정 구현이 없다.

원본 근거:

- `old/side_include/sub_unse.asp:124` — 외부 동영상 서비스 링크

## 적중 궁합 (external-video-f)

- 상태: source_required · 외부 제공사 구현 미확보 · 생성 차단
- 원본: `외부 제공사 서비스`
- 진단: GET /v1/asp-services/external-video-f

### external_implementation_missing (confirmed)

원인: 외부 사이트 입력 페이지로 연결하며 이 저장소에는 해당 제공사의 결과 계산 코드가 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- 제공사 소스/연동 명세 및 대조 결과

판단 근거:

- `old/side_include/sub_unse.asp:125` — 외부 동영상 서비스 링크

검토 범위/실행 제약:

- 외부 공급자의 서비스이며 이 저장소에는 판정 구현이 없다.

원본 근거:

- `old/side_include/sub_unse.asp:125` — 외부 동영상 서비스 링크

## 적중 취업운 (external-video-c)

- 상태: source_required · 외부 제공사 구현 미확보 · 생성 차단
- 원본: `외부 제공사 서비스`
- 진단: GET /v1/asp-services/external-video-c

### external_implementation_missing (confirmed)

원인: 외부 사이트 입력 페이지로 연결하며 이 저장소에는 해당 제공사의 결과 계산 코드가 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- 제공사 소스/연동 명세 및 대조 결과

판단 근거:

- `old/side_include/sub_unse.asp:126` — 외부 동영상 서비스 링크

검토 범위/실행 제약:

- 외부 공급자의 서비스이며 이 저장소에는 판정 구현이 없다.

원본 근거:

- `old/side_include/sub_unse.asp:126` — 외부 동영상 서비스 링크

## 나의 전생 얼굴보기 (external-video-d)

- 상태: source_required · 외부 제공사 구현 미확보 · 생성 차단
- 원본: `외부 제공사 서비스`
- 진단: GET /v1/asp-services/external-video-d

### external_implementation_missing (confirmed)

원인: 외부 사이트 입력 페이지로 연결하며 이 저장소에는 해당 제공사의 결과 계산 코드가 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- 제공사 소스/연동 명세 및 대조 결과

판단 근거:

- `old/side_include/sub_unse.asp:127` — 외부 동영상 서비스 링크

검토 범위/실행 제약:

- 외부 공급자의 서비스이며 이 저장소에는 판정 구현이 없다.

원본 근거:

- `old/side_include/sub_unse.asp:127` — 외부 동영상 서비스 링크

## 미래 내 배우자 얼굴 (external-video-e)

- 상태: source_required · 외부 제공사 구현 미확보 · 생성 차단
- 원본: `외부 제공사 서비스`
- 진단: GET /v1/asp-services/external-video-e

### external_implementation_missing (confirmed)

원인: 외부 사이트 입력 페이지로 연결하며 이 저장소에는 해당 제공사의 결과 계산 코드가 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- 제공사 소스/연동 명세 및 대조 결과

판단 근거:

- `old/side_include/sub_unse.asp:128` — 외부 동영상 서비스 링크

검토 범위/실행 제약:

- 외부 공급자의 서비스이며 이 저장소에는 판정 구현이 없다.

원본 근거:

- `old/side_include/sub_unse.asp:128` — 외부 동영상 서비스 링크

## 미래 내 아이 얼굴 (external-video-a)

- 상태: source_required · 외부 제공사 구현 미확보 · 생성 차단
- 원본: `외부 제공사 서비스`
- 진단: GET /v1/asp-services/external-video-a

### external_implementation_missing (confirmed)

원인: 외부 사이트 입력 페이지로 연결하며 이 저장소에는 해당 제공사의 결과 계산 코드가 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- 제공사 소스/연동 명세 및 대조 결과

판단 근거:

- `old/side_include/sub_unse.asp:129` — 외부 동영상 서비스 링크

검토 범위/실행 제약:

- 외부 공급자의 서비스이며 이 저장소에는 판정 구현이 없다.

원본 근거:

- `old/side_include/sub_unse.asp:129` — 외부 동영상 서비스 링크

## 우리 애정스타일 (missing-richgung)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/unse/comforyou/richgung`
- 진단: GET /v1/asp-services/missing-richgung

### result_source_missing (confirmed)

원인: 원본 메뉴가 가리키는 old/unse/comforyou/richgung/default.asp 파일이 현재 보관본에 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- old/unse/comforyou/richgung/default.asp 및 연결된 계산 코드

판단 근거:

- `old/side_include/sub_love.asp:32` — 원본 메뉴에 존재하나 대상 소스 없음

검토 범위/실행 제약:

- 현재 보관본에 구현 파일이 없으므로 원본 판정 이식이 불가능하다.

원본 근거:

- `old/side_include/sub_love.asp:32` — 원본 메뉴에 존재하나 대상 소스 없음

## 궁합풀이 (missing-weddingluck)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/love/weddingluck`
- 진단: GET /v1/asp-services/missing-weddingluck

### result_source_missing (confirmed)

원인: 원본 메뉴가 가리키는 old/love/weddingluck/main.asp 파일이 현재 보관본에 없습니다.

영향: 원본 판정과 결과 항목을 현재 코드로 확인할 수 없습니다.

해결:

1. 원본 구현 소스 또는 제공사의 입력/결과 계약과 판정 규칙을 확보합니다.
2. 사용할 서비스인지 결정한 뒤 원본 등가 검증과 이식을 진행합니다.

필요 자료:

- old/love/weddingluck/main.asp 및 연결된 계산 코드

판단 근거:

- `old/side_include/sub_love.asp:33` — 원본 메뉴에 존재하나 대상 소스 없음

검토 범위/실행 제약:

- old/unse/originalwedluck/정통궁합과 동일 구현이라는 근거가 없어 임의 연결하지 않는다.

원본 근거:

- `old/side_include/sub_love.asp:33` — 원본 메뉴에 존재하나 대상 소스 없음

## 오늘의 사랑운 (loveunse-love-today)

- 상태: source_required · 원본 결과 소스·분기 누락 · 생성 차단
- 원본: `old/unse/loveunse`
- 진단: GET /v1/asp-services/loveunse-love-today
- 원본 분기: `{"loveunse": "love_today"}`

### result_branch_missing (confirmed)

원인: 소개문에는 love_today가 있지만 main_end.asp 실제 결과 Select Case에는 해당 분기가 없습니다.

영향: 입력값을 전달해도 대응하는 원본 결과 분기가 확인되지 않습니다.

해결:

1. 의도한 결과 분기 소스/명세를 확보하거나 이 메뉴를 제외합니다.
2. 다른 사랑운 분기를 자동 대입하지 않고 결정한 규칙으로 구현합니다.

필요 자료:

- love_today 결과 분기 또는 원본 동작 명세

판단 근거:

- `old/unse/loveunse/top_loveunse.asp:143` — 제목 분기에만 존재하는 love_today

검토 범위/실행 제약:

- top 소개문에는 선언되어 있지만 main_end.asp의 실제 Select Case에는 해당 분기가 없다. princess_love_today로 임의 대체하지 않는다.

원본 근거:

- `old/unse/loveunse/top_loveunse.asp:143` — 제목 분기에만 존재하는 love_today

## 직장운 (menu-im15)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/jobluck`
- 진단: GET /v1/asp-services/menu-im15

### menu_target_missing (confirmed)

원인: IM15 메뉴는 /unse/jobluck/main_end.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/jobluck/main_end.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:116` — unsekind txt
- `old/js/unseform.js:77` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:116` — unsekind txt
- `old/js/unseform.js:77` — CID actionurl dispatch

## 대인관계운 (menu-im16)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im16

### menu_target_missing (confirmed)

원인: IM16 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:124` — unsekind txt
- `old/js/unseform.js:82` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:124` — unsekind txt
- `old/js/unseform.js:82` — CID actionurl dispatch

## 캐리어우먼 성공진단 (menu-im19)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im19

### menu_target_missing (confirmed)

원인: IM19 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:152` — unsekind txt
- `old/js/unseform.js:97` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:152` — unsekind txt
- `old/js/unseform.js:97` — CID actionurl dispatch

## 캐리어우먼으로서의 명예 (menu-im20)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im20

### menu_target_missing (confirmed)

원인: IM20 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:160` — unsekind txt
- `old/js/unseform.js:102` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:160` — unsekind txt
- `old/js/unseform.js:102` — CID actionurl dispatch

## 캐리어우먼의 일과 가정 (menu-im21)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im21

### menu_target_missing (confirmed)

원인: IM21 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:168` — unsekind txt
- `old/js/unseform.js:107` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:168` — unsekind txt
- `old/js/unseform.js:107` — CID actionurl dispatch

## 재물모으는 법 (menu-im22)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im22

### menu_target_missing (confirmed)

원인: IM22 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:176` — unsekind txt
- `old/js/unseform.js:112` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:176` — unsekind txt
- `old/js/unseform.js:112` — CID actionurl dispatch

## 재물손실막는법 (menu-im23)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im23

### menu_target_missing (confirmed)

원인: IM23 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:186` — unsekind txt
- `old/js/unseform.js:117` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:186` — unsekind txt
- `old/js/unseform.js:117` — CID actionurl dispatch

## 재테크비법 (menu-im24)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im24

### menu_target_missing (confirmed)

원인: IM24 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:196` — unsekind txt
- `old/js/unseform.js:122` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:196` — unsekind txt
- `old/js/unseform.js:122` — CID actionurl dispatch

## 피해야 할 상대 (menu-im25)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im25

### menu_target_missing (confirmed)

원인: IM25 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:206` — unsekind txt
- `old/js/unseform.js:127` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:206` — unsekind txt
- `old/js/unseform.js:127` — CID actionurl dispatch

## 비지니스 성공비결 (menu-im26)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im26

### menu_target_missing (confirmed)

원인: IM26 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:215` — unsekind txt
- `old/js/unseform.js:132` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:215` — unsekind txt
- `old/js/unseform.js:132` — CID actionurl dispatch

## 비즈니스극복운 (menu-im27)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im27

### menu_target_missing (confirmed)

원인: IM27 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:223` — unsekind txt
- `old/js/unseform.js:137` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:223` — unsekind txt
- `old/js/unseform.js:137` — CID actionurl dispatch

## 사업운총평 (menu-im28)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im28

### menu_target_missing (confirmed)

원인: IM28 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:231` — unsekind txt
- `old/js/unseform.js:142` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:231` — unsekind txt
- `old/js/unseform.js:142` — CID actionurl dispatch

## 사업합작운 (menu-im29)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im29

### menu_target_missing (confirmed)

원인: IM29 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:242` — unsekind txt
- `old/js/unseform.js:147` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:242` — unsekind txt
- `old/js/unseform.js:147` — CID actionurl dispatch

## 이상형찿기 (menu-im30)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im30

### menu_target_missing (confirmed)

원인: IM30 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:259` — unsekind txt
- `old/js/unseform.js:156` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:259` — unsekind txt
- `old/js/unseform.js:156` — CID actionurl dispatch

## 나의연인은어떤사람 (menu-im31)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im31

### menu_target_missing (confirmed)

원인: IM31 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:268` — unsekind txt
- `old/js/unseform.js:161` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:268` — unsekind txt
- `old/js/unseform.js:161` — CID actionurl dispatch

## 당신과관계된이성들 (menu-im32)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im32

### menu_target_missing (confirmed)

원인: IM32 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:276` — unsekind txt
- `old/js/unseform.js:166` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:276` — unsekind txt
- `old/js/unseform.js:166` — CID actionurl dispatch

## 미팅연애운세 (menu-im33)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im33

### menu_target_missing (confirmed)

원인: IM33 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:285` — unsekind txt
- `old/js/unseform.js:171` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:285` — unsekind txt
- `old/js/unseform.js:171` — CID actionurl dispatch

## 사랑만들기 (menu-im34)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im34

### menu_target_missing (confirmed)

원인: IM34 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:294` — unsekind txt
- `old/js/unseform.js:176` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:294` — unsekind txt
- `old/js/unseform.js:176` — CID actionurl dispatch

## 나의매력 (menu-im35)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im35

### menu_target_missing (confirmed)

원인: IM35 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:303` — unsekind txt
- `old/js/unseform.js:181` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:303` — unsekind txt
- `old/js/unseform.js:181` — CID actionurl dispatch

## 나는이성에게어떤사람 (menu-im36)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im36

### menu_target_missing (confirmed)

원인: IM36 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:312` — unsekind txt
- `old/js/unseform.js:186` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:312` — unsekind txt
- `old/js/unseform.js:186` — CID actionurl dispatch

## 이성의성격 (menu-im37)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im37

### menu_target_missing (confirmed)

원인: IM37 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:321` — unsekind txt
- `old/js/unseform.js:191` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:321` — unsekind txt
- `old/js/unseform.js:191` — CID actionurl dispatch

## 성격분석 (menu-im38)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im38

### menu_target_missing (confirmed)

원인: IM38 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:331` — unsekind txt
- `old/js/unseform.js:196` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:331` — unsekind txt
- `old/js/unseform.js:196` — CID actionurl dispatch

## 현실도분석 (menu-im39)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im39

### menu_target_missing (confirmed)

원인: IM39 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:343` — unsekind txt
- `old/js/unseform.js:201` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:343` — unsekind txt
- `old/js/unseform.js:201` — CID actionurl dispatch

## 결혼조건분석 (menu-im40)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im40

### menu_target_missing (confirmed)

원인: IM40 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:355` — unsekind txt
- `old/js/unseform.js:206` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:355` — unsekind txt
- `old/js/unseform.js:206` — CID actionurl dispatch

## 오늘의 무료데이트운세 (menu-im41)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im41

### menu_target_missing (confirmed)

원인: IM41 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:372` — unsekind txt
- `old/js/unseform.js:211` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:372` — unsekind txt
- `old/js/unseform.js:211` — CID actionurl dispatch

## 첫 데이트 궁합 (menu-im42)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im42

### menu_target_missing (confirmed)

원인: IM42 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:382` — unsekind txt
- `old/js/unseform.js:216` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:382` — unsekind txt
- `old/js/unseform.js:216` — CID actionurl dispatch

## 러브어드바이스 (menu-im43)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im43

### menu_target_missing (confirmed)

원인: IM43 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:391` — unsekind txt
- `old/js/unseform.js:221` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:391` — unsekind txt
- `old/js/unseform.js:221` — CID actionurl dispatch

## 왕자의 오늘 데이트 운세 (menu-im44)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im44

### menu_target_missing (confirmed)

원인: IM44 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:400` — unsekind txt
- `old/js/unseform.js:226` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:400` — unsekind txt
- `old/js/unseform.js:226` — CID actionurl dispatch

## 공주의 오늘 데이트 운세 (menu-im45)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im45

### menu_target_missing (confirmed)

원인: IM45 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:410` — unsekind txt
- `old/js/unseform.js:231` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:410` — unsekind txt
- `old/js/unseform.js:231` — CID actionurl dispatch

## 왕자의 오늘 운세 (menu-im46)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im46

### menu_target_missing (confirmed)

원인: IM46 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:421` — unsekind txt
- `old/js/unseform.js:236` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:421` — unsekind txt
- `old/js/unseform.js:236` — CID actionurl dispatch

## 공주의 오늘 운세 (menu-im47)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im47

### menu_target_missing (confirmed)

원인: IM47 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:431` — unsekind txt
- `old/js/unseform.js:241` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:431` — unsekind txt
- `old/js/unseform.js:241` — CID actionurl dispatch

## 왕자의 오늘 사랑 운세 (menu-im48)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im48

### menu_target_missing (confirmed)

원인: IM48 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:440` — unsekind txt
- `old/js/unseform.js:246` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:440` — unsekind txt
- `old/js/unseform.js:246` — CID actionurl dispatch

## 공주의 오늘 사랑 운세 (menu-im49)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im49

### menu_target_missing (confirmed)

원인: IM49 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:449` — unsekind txt
- `old/js/unseform.js:251` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:449` — unsekind txt
- `old/js/unseform.js:251` — CID actionurl dispatch

## 우리애정스타일 (menu-im50)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im50

### menu_target_missing (confirmed)

원인: IM50 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:460` — unsekind txt
- `old/js/unseform.js:256` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:460` — unsekind txt
- `old/js/unseform.js:256` — CID actionurl dispatch

## 명품애정운세 (menu-im51)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im51

### menu_target_missing (confirmed)

원인: IM51 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:468` — unsekind txt
- `old/js/unseform.js:261` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:468` — unsekind txt
- `old/js/unseform.js:261` — CID actionurl dispatch

## 화해하기위한상대파악 (menu-im52)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im52

### menu_target_missing (confirmed)

원인: IM52 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:477` — unsekind txt
- `old/js/unseform.js:266` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:477` — unsekind txt
- `old/js/unseform.js:266` — CID actionurl dispatch

## 이별후연인의마음 (menu-im53)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im53

### menu_target_missing (confirmed)

원인: IM53 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:485` — unsekind txt
- `old/js/unseform.js:271` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:485` — unsekind txt
- `old/js/unseform.js:271` — CID actionurl dispatch

## 무료궁합 (menu-im54)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im54

### menu_target_missing (confirmed)

원인: IM54 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:493` — unsekind txt
- `old/js/unseform.js:276` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:493` — unsekind txt
- `old/js/unseform.js:276` — CID actionurl dispatch

## 띠별궁합풀이 (menu-im55)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im55

### menu_target_missing (confirmed)

원인: IM55 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:502` — unsekind txt
- `old/js/unseform.js:281` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:502` — unsekind txt
- `old/js/unseform.js:281` — CID actionurl dispatch

## 나와맞는이성궁합 (menu-im56)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im56

### menu_target_missing (confirmed)

원인: IM56 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:510` — unsekind txt
- `old/js/unseform.js:286` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:510` — unsekind txt
- `old/js/unseform.js:286` — CID actionurl dispatch

## 찰떡궁합 (menu-im57)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im57

### menu_target_missing (confirmed)

원인: IM57 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:519` — unsekind txt
- `old/js/unseform.js:291` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:519` — unsekind txt
- `old/js/unseform.js:291` — CID actionurl dispatch

## 숙명의궁합 (menu-im58)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im58

### menu_target_missing (confirmed)

원인: IM58 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:527` — unsekind txt
- `old/js/unseform.js:296` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:527` — unsekind txt
- `old/js/unseform.js:296` — CID actionurl dispatch

## 서로를 성장시키는비결 (menu-im59)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im59

### menu_target_missing (confirmed)

원인: IM59 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:535` — unsekind txt
- `old/js/unseform.js:301` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:535` — unsekind txt
- `old/js/unseform.js:301` — CID actionurl dispatch

## 결혼택일 (menu-im60)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im60

### menu_target_missing (confirmed)

원인: IM60 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:545` — unsekind txt
- `old/js/unseform.js:306` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:545` — unsekind txt
- `old/js/unseform.js:306` — CID actionurl dispatch

## 웨딩 타임머신 (menu-im61)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im61

### menu_target_missing (confirmed)

원인: IM61 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:555` — unsekind txt
- `old/js/unseform.js:311` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:555` — unsekind txt
- `old/js/unseform.js:311` — CID actionurl dispatch

## 사랑과결혼 (menu-im62)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im62

### menu_target_missing (confirmed)

원인: IM62 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:565` — unsekind txt
- `old/js/unseform.js:316` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:565` — unsekind txt
- `old/js/unseform.js:316` — CID actionurl dispatch

## 두사람의 숙명진단 (menu-im63)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im63

### menu_target_missing (confirmed)

원인: IM63 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:574` — unsekind txt
- `old/js/unseform.js:322` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:574` — unsekind txt
- `old/js/unseform.js:322` — CID actionurl dispatch

## 별자리운세 (menu-im64)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im64

### menu_target_missing (confirmed)

원인: IM64 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:583` — unsekind txt
- `old/js/unseform.js:327` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:583` — unsekind txt
- `old/js/unseform.js:327` — CID actionurl dispatch

## 별자리속궁합 (menu-im65)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im65

### menu_target_missing (confirmed)

원인: IM65 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:591` — unsekind txt
- `old/js/unseform.js:332` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:591` — unsekind txt
- `old/js/unseform.js:332` — CID actionurl dispatch

## 혈액형운세 (menu-im66)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im66

### menu_target_missing (confirmed)

원인: IM66 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:599` — unsekind txt
- `old/js/unseform.js:337` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:599` — unsekind txt
- `old/js/unseform.js:337` — CID actionurl dispatch

## 혈액형궁합 (menu-im67)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/unse/astrosaju`
- 진단: GET /v1/asp-services/menu-im67

### menu_target_missing (confirmed)

원인: IM67 메뉴는 /unse/astrosaju/detail.asp로 보내지만 보관본에 해당 파일이 없습니다.

영향: 이 메뉴 경로의 원본 판정·입력 분기를 확인할 수 없습니다.

해결:

1. 누락된 연결 ASP 및 include/판정 자료를 확보합니다.
2. 다른 폴더에 같은 이름이 있어도 동일 엔진인지 먼저 대조합니다.
3. 사용할 메뉴를 확정하고 실행 경로와 Python 입력 계약을 연결합니다.

필요 자료:

- old/unse/astrosaju/detail.asp 및 연결 include/판정 명세

판단 근거:

- `old/xmlpath/unse.xml:607` — unsekind txt
- `old/js/unseform.js:342` — CID actionurl dispatch

검토 범위/실행 제약:

- 동일 actionurl을 쓰더라도 CID가 다른 메뉴는 별도 서비스 선언이다. 추가 분류 입력/폼이 필요하며 실행 로직 동일성을 뜻하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:607` — unsekind txt
- `old/js/unseform.js:342` — CID actionurl dispatch

## 꿈해몽 (menu-im68)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im68

### menu_dispatch_missing (confirmed)

원인: XML에 IM68 (꿈해몽) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:616` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:616` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 심리테스트 (menu-im69)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im69

### menu_dispatch_missing (confirmed)

원인: XML에 IM69 (심리테스트) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:625` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:625` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 향수점 (menu-im70)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im70

### menu_dispatch_missing (confirmed)

원인: XML에 IM70 (향수점) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:634` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:634` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 동물점 (menu-im71)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im71

### menu_dispatch_missing (confirmed)

원인: XML에 IM71 (동물점) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:643` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:643` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 전생록 (menu-im72)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im72

### menu_dispatch_missing (confirmed)

원인: XML에 IM72 (전생록) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:652` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:652` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 주역점 (menu-im73)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im73

### menu_dispatch_missing (confirmed)

원인: XML에 IM73 (주역점) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:661` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:661` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 주민번호운세 (menu-im74)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im74

### menu_dispatch_missing (confirmed)

원인: XML에 IM74 (주민번호운세) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:670` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:670` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 휴대폰운세 (menu-im75)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im75

### menu_dispatch_missing (confirmed)

원인: XML에 IM75 (휴대폰운세) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:679` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:679` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 주소지운세 (menu-im76)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im76

### menu_dispatch_missing (confirmed)

원인: XML에 IM76 (주소지운세) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:688` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:688` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 차량번호운세 (menu-im77)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im77

### menu_dispatch_missing (confirmed)

원인: XML에 IM77 (차량번호운세) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:697` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:697` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 탄생일운세 (menu-im78)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im78

### menu_dispatch_missing (confirmed)

원인: XML에 IM78 (탄생일운세) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:706` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:706` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 탄생화운세 (menu-im79)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im79

### menu_dispatch_missing (confirmed)

원인: XML에 IM79 (탄생화운세) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:715` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:715` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 탄생석운세 (menu-im80)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im80

### menu_dispatch_missing (confirmed)

원인: XML에 IM80 (탄생석운세) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:724` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:724` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 경마운세 (menu-im81)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im81

### menu_dispatch_missing (confirmed)

원인: XML에 IM81 (경마운세) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:733` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:733` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 고스톱운세 (menu-im82)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im82

### menu_dispatch_missing (confirmed)

원인: XML에 IM82 (고스톱운세) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:742` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:742` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 게임운세 (menu-im83)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im83

### menu_dispatch_missing (confirmed)

원인: XML에 IM83 (게임운세) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:751` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:751` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 레저운세 (menu-im84)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im84

### menu_dispatch_missing (confirmed)

원인: XML에 IM84 (레저운세) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:760` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:760` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 엽기운세 (menu-im85)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im85

### menu_dispatch_missing (confirmed)

원인: XML에 IM85 (엽기운세) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:769` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:769` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 적중궁합 (menu-im86)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im86

### menu_dispatch_missing (confirmed)

원인: XML에 IM86 (적중궁합) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:778` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:778` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 적중취업운 (menu-im87)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im87

### menu_dispatch_missing (confirmed)

원인: XML에 IM87 (적중취업운) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:787` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:787` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 적중궁합 (menu-im88)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im88

### menu_dispatch_missing (confirmed)

원인: XML에 IM88 (적중궁합) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:796` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:796` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 미래내배우자얼굴 (menu-im89)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im89

### menu_dispatch_missing (confirmed)

원인: XML에 IM89 (미래내배우자얼굴) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:805` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:805` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

## 미래내아이얼굴 (menu-im90)

- 상태: source_required · 원본 메뉴 연결·실행 계약 미확정
- 원본: `old/xmlpath`
- 진단: GET /v1/asp-services/menu-im90

### menu_dispatch_missing (confirmed)

원인: XML에 IM90 (미래내아이얼굴) 이름은 선언되어 있으나 JS의 실행 경로/입력폼 매핑이 없습니다.

영향: 메뉴 이름만으로 어느 계산 엔진과 입력을 호출해야 하는지 확정할 수 없습니다.

해결:

1. 실제 운영 메뉴 연결 또는 사용할 원본 결과 엔진을 확인합니다.
2. 같은 이름의 다른 원본과 동일한 서비스인지 검증하고 명시적으로 연결합니다.

필요 자료:

- 실제 배포본 메뉴→실행 경로/입력폼/분기값 또는 해당 서비스 명세

판단 근거:

- `old/xmlpath/unse.xml:814` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

검토 범위/실행 제약:

- XML itemvalue의 /sample.asp는 다른23항목과 동일한 결혼 설명을 가진 예시값이다. 실제 결과 경로로 취급하지 않는다.
- 이름이 같은 별도 보관 서비스가 있어도 이 메뉴코드의 실행 경로로 임의 대입하지 않는다.

원본 근거:

- `old/xmlpath/unse.xml:814` — 원본 XML 이름 선언
- `old/js/unseform.js:347` — switch 종료까지 IM1~67만 존재하여 이 코드의 실행 분기 없음
- `old/xmlpath/left.xml:134` — 좌측 메뉴에는 IM1~67만 존재하여 이 코드의 메뉴 링크 없음

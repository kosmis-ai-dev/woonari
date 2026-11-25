# 서비스 운세 Swagger 그룹

[Swagger](http://127.0.0.1:9090/docs) 최상단 **서비스 운세 · AI 본문 제공**에는 개인 사주·대상 연도·생일에 따른 운세 본문을 제공하는 대표 POST를 모았습니다. 각 항목의 입력 조건과 해석 범위를 확인한 뒤 실행하세요.

| 운세명 | 대표 POST 경로 |
|---|---|
| 오늘의 un | `/v1/fortunes/daily` |
| 이번주 un | `/v1/fortunes/weekly` |
| 이달의 un | `/v1/fortunes/monthly` |
| 연간 un (2027년 포함) | `/v1/fortunes/yearly` |
| 평생un | `/v1/fortunes/lifetime` |
| 명품 평생재물운 | `/v1/fortunes/wealth` |
| 러브 어드바이스 | `/v1/fortunes/love` |
| 바이오리듬 | `/v1/fortunes/biorhythm` |
| 명품 평생애정운 | `/v1/un/sweetluck` |
| 학생un | `/v1/un/studentluck` |
| 인맥 구축·조직 관리법 | `/v1/un/humanorganizationmanagement` |
| 미팅 연애un | `/v1/un/meetluck` |
| 띠별궁합풀이 | `/v1/un/ddiluck` |
| 서로를 성장시키는 비결 | `/v1/un/ourgrowthluck` |
| 탄생화un | `/v1/un/flowerluck` |
| 탄생석un | `/v1/un/jewelryluck` |
| 도통 전생록 | `/v1/un/preluck` |

현재 실행 환경에서 필요한 자료가 준비된 항목만 표시합니다. 꽃·보석 자료가 준비되지 않은 환경에서는 해당 두 항목을 제외한 15종이 표시됩니다. 미지원 항목은 목록과 Swagger에서 제외하며 직접 요청하면 `503 result_unavailable`로 응답합니다.

첫 번째 예시는 `include_ai=true`로 AI 본문을 생성합니다. `content`에서 결과 글을 읽고 `interpretation.summary`, `interpretation.sections`의 `topic`·`text`, `interpretation.practical_advice`에서 구조화된 해석을 확인합니다. `result`에는 해당 운세의 계산 결과가 담깁니다.

두 번째 예시는 `include_ai=false`로 AI 호출·차감 없이 `result`만 반환합니다. 응답에 출처·개발 상태·내부 검증 계약은 포함하지 않습니다. AI 본문 요청은 한국시간 일일 최대 100회의 공통 한도를 사용합니다.

- 서로를 성장시키는 비결: `birth`와 `partner`를 모두 입력합니다.
- 탄생석: 양력 입력만 AI 본문을 제공합니다.
- 띠별궁합: 본인 띠와12띠 전체 관계 풀이이며 27숙 숙명궁합과 다릅니다.
- 전생: 전통적인 상징 풀이이며 실제 전생 사실을 확인하는 기능은 아닙니다.
- 바이오리듬: 주기 계산의 해석이며 건강 진단이 아닙니다.
- 연간: 해당 양력 연도 전체에 대한 AI 해석이며 별점·점수·부적은 제공하지 않습니다.

추가 콘텐츠와 다른 호출 경로는 **기타 콘텐츠 · AI 해석**, 달력 도구는 **계산 도구 · 본문 없음**에 표시합니다. 현재 결과를 제공하지 못하는 항목의 진단 API는 공개하지 않습니다.

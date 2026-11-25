"""CR-020 / T-040: selected consumer-facing Swagger operations, not AI gates.

Each service has one canonical operation. Selection does not override runtime
readiness or certify that every generated interpretation has passed human review.
"""

SERVICE_TAG = "서비스 운세 · AI 본문 제공"
OTHER_TAG = "기타 콘텐츠 · AI 해석"
CALCULATION_TAG = "계산 도구 · 본문 없음"
DIAGNOSTIC_TAG = "개발 진단 · 본문 없음"

# Descriptions describe actual inputs and interpretation scope, not extra rules.
SERVICE_OFFERINGS = {
    "/v1/fortunes/daily": ("오늘의 un", "조회 날짜를 입력합니다. 당일 점수와 어제·오늘·내일 본문 작성 범위를 구분합니다."),
    "/v1/fortunes/weekly": ("이번주 un", "조회 날짜가 속한 일요일~토요일의 주간 해석입니다."),
    "/v1/fortunes/monthly": ("이달의 un", "조회 날짜의 절기 기준 월간 해석입니다."),
    "/v1/fortunes/yearly": ("연간 un", "2027년 포함 1900~2050년을 지원합니다. 사주·연도 근거를 AI가 해석하고 별점·점수·부적은 제공하지 않습니다."),
    "/v1/fortunes/lifetime": ("평생un", "lifeluck의 평생 사주 해석입니다. 별도 원본의 평생사주 메뉴와 구분합니다."),
    "/v1/fortunes/wealth": ("명품 평생재물운", "개인 사주에 따른 재물 관련 해석입니다. 실제 수입·투자 수익 예측으로 제공하지 않습니다."),
    "/v1/fortunes/love": ("러브 어드바이스", "본인의 생년월일시로 인연과 연애 주제를 해석합니다."),
    "/v1/fortunes/biorhythm": ("바이오리듬", "출생일 이후 주기 계산의 해석입니다. 실제 건강 상태를 진단하지 않습니다."),
    "/v1/un/sweetluck": ("명품 평생애정운", "본인의 생년월일시로 애정 관련 주제를 해석합니다."),
    "/v1/un/studentluck": ("학생un", "본인의 생년월일시로 학업·학습 관련 주제를 해석합니다."),
    "/v1/un/humanorganizationmanagement": ("인맥 구축·조직 관리법", "본인의 생년월일시로 사회생활·조직 관련 주제를 해석합니다."),
    "/v1/un/meetluck": ("미팅 연애un", "본인의 생년월일시로 만남·연애 관련 주제를 해석합니다."),
    "/v1/un/ddiluck": ("띠별궁합풀이", "본인 띠와 12띠 전체의 관계 풀이입니다. 상대방 입력을 받는 숙명의 궁합과 구분합니다."),
    "/v1/un/ourgrowthluck": ("서로를 성장시키는 비결", "본인 birth와 상대방 partner의 생년월일시가 모두 필요합니다."),
    "/v1/un/flowerluck": ("탄생화un", "복원된 날짜별 꽃 자료 연결이 필요합니다. 생일에 해당하는 꽃과 상징을 해석합니다."),
    "/v1/un/jewelryluck": ("탄생석un", "양력 입력만 지원합니다. 복원된 월별 보석 자료 연결이 필요하며 음력 요청의 AI 본문은 차단됩니다."),
    "/v1/un/preluck": ("도통 전생록", "복원된 원문 자료의 전통적인 상징 풀이입니다. 실제 전생 사실을 확인하는 기능은 아닙니다.")
}


def service_offering_description(path: str) -> str:
    offering = SERVICE_OFFERINGS.get(path)
    if offering is None:
        return ""
    return (
        "**서비스 제공 대상:** " + offering[0] + "  \n" + offering[1]
        + "\n\n첫 번째 **AI 본문 생성** 예시는 `include_ai=true`이며 결과 글은 `content`에서 확인합니다. "
        "**계산만 확인** 예시는 `include_ai=false`로 본문 없이 계산 근거만 반환합니다."
    )


def service_operation_tag(path: str, *, ready: bool, calculation_only: bool = False) -> str:
    if ready and path in SERVICE_OFFERINGS:
        return SERVICE_TAG
    if calculation_only:
        return CALCULATION_TAG
    return OTHER_TAG if ready else DIAGNOSTIC_TAG

"""CR-012: active common-template selectors over explicitly mapped basic pillars.

The original UI labels its four columns 時/日/月/年 (_function.asp:27-30),
then renders KAN/SI at those indexes (:41-51). Only those basic fields and the
source's explicit postprocessing tables are mapped. DAEUN/SEUN are not supplied.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.calendar import solar_birth
from app.errors import DomainError
from app.models import SajuResult
from app.rules import BRANCHES, STEMS

if TYPE_CHECKING:
    from app.service_models import ServiceRequest

HAN = (
    (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
    (2, 1, 4, 3, 6, 5, 8, 7, 10, 9),
    (9, 10, 1, 2, 3, 4, 5, 6, 7, 8),
    (10, 9, 2, 1, 4, 3, 6, 5, 8, 7),
    (7, 8, 9, 10, 1, 2, 3, 4, 5, 6),
    (8, 7, 10, 9, 2, 1, 4, 3, 6, 5),
    (5, 6, 7, 8, 9, 10, 1, 2, 3, 4),
    (6, 5, 8, 7, 10, 9, 2, 1, 4, 3),
    (3, 4, 5, 6, 7, 8, 9, 10, 1, 2),
    (4, 3, 6, 5, 8, 7, 10, 9, 2, 1),
)
UN12_JAPAN = (
    (4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 12, 11, 10),
    (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12),
    (12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1),
    (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12),
    (12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1),
    (10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (3, 2, 1, 12, 11, 10, 9, 8, 7, 6, 5, 4),
    (7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6),
    (6, 5, 4, 3, 2, 1, 12, 11, 10, 9, 8, 7),
)
HIDDEN_STEMS = (10, 6, 1, 2, 5, 3, 4, 6, 7, 8, 5, 9)
SOURCE_LIMITS = [
    "SajuManseryuk의 DLL 실제 실행 결과와 동일성은 미검증입니다.",
    "허용된 기본 만세력 대체 범위에서 dotong 사주를 時/日/月/年 1-based KAN/SI에 대응합니다.",
    "藏干·통변성·12운성은 _SajuManseryuk.asp의 정적 표와 날짜 분기를 그대로 적용합니다.",
    "미사용 대운·세운 배열과 tbAisyo 준비 조회는 생성하지 않습니다.",
]


def _spec(name, directory, codes, topics, *, partner=False, saju=True, ready=True):
    return {"name": name, "original_name": name, "directory": directory,
            "requires_birth": True, "requires_partner": partner, "uses_saju": saju,
            "example_parameters": {}, "parameter_help": {}, "ready": ready,
            "source_limits": SOURCE_LIMITS if saju else [], "codes": codes, "topics": topics}


SERVICES = {
    "humanorganizationmanagement": _spec("인맥 구축·조직 관리법", "HumanOrganizationManagement",
        ("saju_bizhostility_1", "saju_bizhostility_2", "saju_bizhostility_3", "saju_bizhostility_4"),
        ("비즈니스맨으로서의 적성과 결점", "재능을 살리기 위한 적합한 직장", "관리직으로서의 자질", "성공적인 인간관계 구축법")),
    "ourgrowthluck": _spec("서로를 성장시키는 비결", "ourgrowthluck",
        ("saju_marrycheck_1", "saju_marrycheck_2", "saju_marrycheck_3", "saju_marrycheck_4"),
        ("몸과 마음의 모순으로 발생하는 당신의 성격결점", "상대의 성격결점", "상대의 모자란면", "상대를 성장시키는 법"), partner=True),
    "adultluck-affairorloveluck": _spec("불륜일까? 사랑일까?", "adultluck/affairorloveluck",
        ("saju_immorality_11", "saju_immorality_12", "saju_immorality_13"),
        ("가정있는 상대가 당신에게 마음이 흔들릴까", "사랑쟁취 후 당신이 조심해야 할 것", "두 사람은 진정한 행복일까"), partner=True),
    "adultluck-prohibitionsexluck": _spec("금단의 섹스 진단", "adultluck/prohibitionsexluck",
        ("saju_sexcheck_0", "saju_sexcheck_1", "saju_sexcheck_2", "saju_sexcheck_3"),
        ("금단의 섹스진단", "섹스에 대한 정신적 사고방식", "섹스에 대한 육체적 경향", "직장이나 클럽등에서 섹스의 유혹에 빠진다면")),
    "adultluck-lovertechniqueluck": _spec("연인과의 최고 절정의 기술", "adultluck/lovertechniqueluck",
        ("saju_sexlove_6", "saju_sexlove_4", "saju_sexlove_8"),
        ("섹스에 대한 탐욕성", "섹스 절정의 장소", "섹스 체위"), partner=True),
    "adultluck-loverwishluck": _spec("연인의 음란한 소망", "adultluck/loverwishluck",
        ("saju_sexlove_3", "saju_sexlove_7", "saju_sexlove_5"),
        ("연인의 음란한 소망", "연인의 소망 충족을 위한 사랑 기술", "성적 욕망의 급소자극 기술"), partner=True),
    "mastermanrelations": _spec("상사와의 관계", "MasterManRelations",
        ("saju_bizmanpower_1", "saju_bizmanpower_2", "saju_bizmanpower_3", "astro_business_1", "astro_business_2", "astro_business_3"),
        ("당신이 일을 하는 목적과 목적을 달성하기 위한 수단", "목적달성을위해서 상사와 어떻게 사귀면좋은가", "당신의 비즈니스에서 금전감각은 문제없는가", "성공적인 관계유지를 위한 포인트", "상사가 이 도수의 사람인 경우", "부하가 이 도수의 사람인 경우"), ready=False),
    "socialmyhonor": _spec("사회 속의 나의 명예", "SocialMyHonor",
        ("astro_aspect_society_4", "astro_aspect_society_3", "astro_aspect_society_2", "astro_aspect_society_1"),
        ("사회속에 자신", "사회적 지위와 운명", "사회적 명예", "사회적 책임과 역할"), saju=False, ready=False),
    "wedupluck": _spec("궁합 UP 가이드", "wedupluck",
        ("astro_harmony_1", "astro_harmony_2", "astro_harmony_3", "astro_harmony_4"),
        ("궁합총평", "사랑UP", "행복도 UP", "지성도 UP 비법"), partner=True, saju=False, ready=False),
    "adultluck-bedroommatchingluck": _spec("부부의 침실 궁합", "adultluck/bedroommatchingluck",
        ("women_loveharmony", "women_astroharmony", "women_mymarry", "astro_attraction"),
        ("주간러브침실궁합", "연애성 궁합", "연애,결혼운 진단", "당신의 매력"), partner=True, saju=False, ready=False),
}


def _zokan_month(month, day):
    value = month * 100 + day
    for start, end, stem in (
        (204, 311, 1), (312, 417, 2), (418, 505, 5), (506, 612, 3),
        (613, 719, 4), (720, 806, 6), (807, 914, 7), (915, 1020, 8),
        (1021, 1106, 5), (1107, 1213, 9), (1214, 1231, 10), (101, 118, 10), (119, 203, 6),
    ):
        if start <= value <= end:
            return stem
    raise DomainError("invalid_manse_record", "기본 만세력 날짜를 확인하세요.", 503)


def basic_profile(saju: SajuResult, solar_date) -> dict:
    if saju is None or saju.policy.calculation_profile != "dotong":
        raise DomainError("service_saju_required", "dotong 기준의 기본 사주 계산이 필요합니다.")
    order = ("hour", "day", "month", "year")
    kan = [STEMS.index(saju.pillars[key].stem) + 1 for key in order]
    si = [BRANCHES.index(saju.pillars[key].branch) + 1 for key in order]
    zokan = [HIDDEN_STEMS[index - 1] for index in si]
    zokan[2] = _zokan_month(solar_date.month, solar_date.day)
    return {
        "order": list(order), "KAN": kan, "SI": si, "ZOKAN": zokan,
        "UN12": [UN12_JAPAN[k - 1][s - 1] for k, s in zip(kan, si)],
        "TUHEN": [HAN[0][value - 1] for value in kan],
        "TUHEN2": [HAN[0][value - 1] for value in zokan],
    }


def _selector(code, topic, table, menu, key, *, sex=None, unresolved=False):
    where = {"menu": menu, "keyno": key}
    if sex is not None:
        where["sex"] = str(sex)
    return {"id": code, "table": table, "where": where, "columns": ["content"],
            "topics": {"content": topic}, "purpose": "원본 활성 분기의 문구 선택키를 AI 문장화",
            **({"key_unresolved": True} if unresolved else {})}


def _key(prefix, value):
    return int(f"{prefix}{value:02d}")


def _birth(request, partner=False):
    value = request.partner if partner else request.birth
    if value is None:
        raise DomainError("service_partner_required" if partner else "service_birth_required",
                          "상대방 생년월일이 필요합니다." if partner else "생년월일이 필요합니다.")
    return value


def _sexcheck(code, profile):
    part = int(code.rsplit("_", 1)[1])
    if part == 0:
        return 0
    if part == 1:
        return _key(1, profile["KAN"][1])
    if part == 2:
        return _key(2, UN12_JAPAN[profile["KAN"][1] - 1][profile["SI"][1] - 1])
    return _key(3, HAN[0][profile["KAN"][2] - 1])


def _love_harmony(request):
    mine = (request.target_date - solar_birth(_birth(request)).date()).days
    yours = (request.target_date - solar_birth(_birth(request, True)).date()).days
    my_health, my_love = mine % 23, mine % 28
    your_health, your_love = yours % 23, yours % 28
    love_point = abs(your_love - my_love) if my_love < your_love else my_love
    health_point = abs(your_health - my_health) if my_health < your_health else my_health
    return int(round((love_point + health_point) / 2)) + 1


def decide(service_id: str, request: ServiceRequest, saju: SajuResult | None,
           partner: SajuResult | None) -> dict:
    if service_id not in SERVICES:
        raise DomainError("service_not_found", "해당 공통 이식 서비스를 찾을 수 없습니다.", 404)
    if request.parameters:
        raise DomainError("invalid_service_parameters", "이 서비스에는 추가 parameters를 사용하지 않습니다.")
    spec = SERVICES[service_id]
    birth = _birth(request)
    solar = solar_birth(birth)
    gender = 1 if birth.gender == "male" else 2
    facts = {"active_codes": list(spec["codes"])}
    mine = yours = None
    if spec["uses_saju"]:
        mine = basic_profile(saju, solar.date())
        facts.update(basic_calendar_adapter=mine, source_limits=list(SOURCE_LIMITS))
    if spec["requires_partner"]:
        other = _birth(request, True)
        if spec["uses_saju"]:
            yours = basic_profile(partner, solar_birth(other).date())
            facts["partner_basic_calendar_adapter"] = yours
    selectors, unresolved = [], []
    for code, topic in zip(spec["codes"], spec["topics"]):
        part = int(code.rsplit("_", 1)[1]) if code.rsplit("_", 1)[1].isdigit() else None
        if code.startswith("saju_bizhostility_"):
            value = mine["KAN"][1] if part == 1 else HAN[0][mine["KAN"][2] - 1]
            selectors.append(_selector(code, topic, "tbSajuMaster_mobile1", "bizhostility",
                                       _key({1: 1, 2: 2, 3: 4, 4: 5}[part], value)))
        elif code.startswith("saju_marrycheck_"):
            if part in (1, 2):
                value = UN12_JAPAN[0][(mine if part == 1 else yours)["SI"][1] - 1]
                key = _key(1, value)
            else:
                value = HAN[0][yours["KAN"][2] - 1]
                key = _key(part, value)
                if part == 4:
                    key = int(str(key) + ("2" if gender == 1 else "1"))
            selectors.append(_selector(code, topic, "tbSajuMaster_mobile1", "marrycheck", key))
        elif code.startswith("saju_immorality_"):
            if part == 11:
                value = HAN[yours["KAN"][1] - 1][mine["KAN"][1] - 1]
                prefix = 1 if gender % 2 == 0 else 2
            elif part == 12:
                value = yours["TUHEN2"][2]
                prefix = 3 if gender % 2 == 0 else 4
            else:
                value = HAN[mine["KAN"][1] - 1][yours["KAN"][1] - 1]
                prefix = 5 if gender % 2 == 0 else 6
            selectors.append(_selector(code, topic, "tbWedding_Content", "immorality", _key(prefix, value)))
        elif code.startswith("saju_sexcheck_"):
            selectors.append(_selector(code, topic, "tbSajuMaster_mobile1", "sexcheck", _sexcheck(code, mine)))
        elif code.startswith("saju_sexlove_"):
            if part == 3:
                value = UN12_JAPAN[0][yours["SI"][1] - 1]
            elif part in (4, 5):
                value = yours["KAN"][1]
            else:
                value = mine["ZOKAN"][1]
            sex = 3 - gender if part in (3, 4, 5) else gender
            selectors.append(_selector(code, topic, "tbSexLove_Content", "", _key(part, value), sex=sex))
        elif code.startswith("saju_bizmanpower_"):
            if part == 1:
                first, second = sorted((HAN[0][mine["KAN"][2] - 1] // 2,
                                        HAN[0][mine["KAN"][3] - 1] // 2))
                key = _key(4, first * 10 + second)
            elif part == 2:
                key = _key(2, HAN[0][mine["KAN"][2] - 1])
            else:
                key = _key(3, UN12_JAPAN[0][mine["SI"][1] - 1])
            selectors.append(_selector(code, topic, "tbSajuMaster_mobile1", "bizmanpower", key))
        elif code == "women_loveharmony":
            selectors.append({"id": code, "table": "tbLoveHarmony", "where": {"keyno": _love_harmony(request)},
                              "columns": ["content"], "topics": {"content": topic},
                              "purpose": "原本23/28일 나머지 비교식과 CInt 반올림으로 본문 선택"})
        else:
            if code.startswith("astro_business_") or code.startswith("astro_harmony_"):
                planets = [1]
            elif code.startswith("astro_aspect_society_"):
                planets = list({1, int(("17", "16", "15", "12")[part - 1][1])})
            elif code == "astro_attraction":
                planets = [4]
            elif code == "women_astroharmony":
                planets = [1]
            else:
                # lib_women:71-72 uses indexes 5,4,1,2 without subtracting one.
                planets = [2, 3, 5, 6]
            for planet in sorted(planets):
                selectors.append({"id": f"{code}-planet-{planet}",
                                  "table": f"tbSavianAstro_Planet_{planet}",
                                  "where": {"fdDate": {"lt": None}}, "columns": ["fdAstro"],
                                  "role": "calculation", "narrative": False,
                                  "purpose": "본인/상대 양력 생년월일시의 직전 행성 분류 자료 필요(원문 미전송)"})
            table = {"women_astroharmony": "tbAstroHarmony", "women_mymarry": "tbMyMarry"}.get(code, "tbSavianAstro_Content")
            selectors.append({"id": code, "table": table, "where": {"keyno": None},
                              "columns": ["content"], "topics": {"content": topic},
                              "key_unresolved": True, "purpose": "행성 분류 자료 확보 후 원본 선택키 계산"})
            unresolved.append(f"{code}: 원본 fdAstro 행성 분류 자료가 없어 선택키를 확정할 수 없습니다.")
    return {"source": f"old/unse/{spec['directory']}/main_end.asp", "facts": facts,
            "selectors": selectors, "unresolved": unresolved}

"""CR-012/T-024: remaining direct ASP selectors and observable calculations."""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from app.calendar import solar_birth
from app.errors import DomainError
from app.legacy_life_wealth import legacy_profile, sipkyuk
from app.manse_store import ManseDataError, get_manse_store
from app.models import SajuResult
from app.rules import BRANCHES, STEM_ELEMENTS, STEMS, ten_god

if TYPE_CHECKING:
    from app.service_models import ServiceRequest

_DATA = json.loads((Path(__file__).parent / "data/ported_remaining_rules.json").read_text("utf-8"))


def _service(*, saju=True, partner=False, ready=True, parameters=None, help_text=""):
    return {
        "requires_birth": True, "requires_partner": partner, "uses_saju": saju,
        "example_parameters": parameters or {}, "parameter_help": help_text, "ready": ready,
    }


SERVICES = {
    "ddiluck": _service(),
    "adultluck-timesexbioluck": _service(saju=False),
    "counselluck": _service(ready=False),
    "fivegiluck": _service(ready=False),
    "lottoluck": _service(parameters={"seed": 20261118}, help_text="seed는 재현용 정수입니다. 번호는 원본 난수 절차에 따라 생성합니다."),
    "loverluck": _service(saju=False),
    "meetluck": _service(),
    "perluck": _service(),
    "sinsalluck": _service(partner=True, ready=False, help_text="legacy_gpcheck는 원본 이전 요청의 gpcheck 숫자 코드를 순서대로 담은 배열입니다. 생략하면 쿠키 의존 본문은 확정하지 않습니다."),
    "studentluck": _service(),
    "sweetluck": _service(),
}


def _result(service_id: str, facts=None, selectors=None, unresolved=None):
    source = (
        "old/unse/adultluck/timesexbioluck/main_end.asp"
        if service_id == "adultluck-timesexbioluck"
        else f"old/unse/{service_id}/main_end.asp"
    )
    return {"source": source, "facts": facts or {}, "selectors": selectors or [], "unresolved": unresolved or []}


def _selector(identifier, table, where, columns, topic, **extra):
    return {
        "id": identifier, "table": table, "where": where, "columns": columns,
        "purpose": topic, "topics": {column: topic for column in columns}, **extra,
    }


def _required_saju(saju):
    if saju is None:
        raise DomainError("birth_required", "이 서비스에는 생년월일시로 계산한 사주가 필요합니다.")
    return saju


def _sex(request) -> str:
    return "여" if request.birth.gender == "female" else "남"


def _ddiluck(saju):
    branch = saju.pillars["year"].branch
    order = _DATA["ddiluck"]["order"][branch]
    rows, selectors = [], []
    for index, key in enumerate(order, 1):
        zodiac = BRANCHES[int(key[2:].removesuffix("a")) - 1]
        anchor = _DATA["ddiluck"]["anchors"][key]
        rows.append({"position": index, "branch": zodiac, "favorable": not key.endswith("a"), "meaning_anchor": anchor})
        selectors.append(_selector(
            f"zodiac-{index}", "inline:ddiluck", {"year_branch": branch, "anchor": key}, ["content"],
            f"{zodiac} 띠와의 관계", source_anchor=anchor,
        ))
    return _result("ddiluck", {"year_branch": branch, "ordered_zodiac_relations": rows}, selectors)


def _hour_bio(request):
    birth_date = solar_birth(request.birth).date()
    elapsed = (request.target_date - birth_date).days
    rhythm = math.sin((elapsed / 28) * 2 * 3.141592)
    code = "1" if rhythm < 0 else "2"
    slots = ("06", "08", "10", "12", "14", "16", "18", "20", "22", "00", "02", "04")
    selectors = [
        _selector(f"hour-{slot}", "tbSexLove_Content", {"menu": "", "sex": "", "keyno": int(code + slot)}, ["content"], f"{slot}시부터 두 시간의 바이오리듬")
        for slot in slots
    ]
    return _result("adultluck-timesexbioluck", {
        "helper": "function/b_include/lib_sajumaster.asp:730-751",
        "elapsed_days": elapsed, "cycle_days": 28, "source_pi": 3.141592,
        "rhythm": rhythm, "sign_key": code, "ordered_hour_slots": slots,
        "source_rule": "saju_sexlove_12 uses dates, not SajuManseryuk arrays",
    }, selectors)


def _meet(saju, request):
    # main_end.asp:96-122 has its own 1-based EarthRoot ordering.
    own = (STEMS.index(saju.day_master) + 2) // 2
    other = ("寅卯巳午辰丑戌未申酉亥子".index(saju.pillars["day"].branch) + 2) // 2
    if other >= 4:
        other -= 1
    label = ("비견", "식상", "재성", "관성", "인성")[(other - own) % 5]
    return _result("meetluck", {"six_sin_group": label}, [
        _selector("meeting", "Meeting_Unse", {"Name": label, "Gender": "2" if _sex(request) == "여" else "1"}, ["content1", "content2"], "미팅·연애의 성향과 조언")
    ])


def _student(saju, request):
    number = int(saju.legacy_memno[0])
    sex = 2 if request.birth.gender == "female" else 1
    age = request.target_date.year - request.birth.year
    where = {"ilgan": number, "sex": sex}
    selectors = [
        _selector("exam", "Exam_Unse", where, ["content1", "content2", "content3"], "학업·시험"),
        _selector("student-relations", "Gender_Unse", where, ["content1", "content2"], "학생의 이성 관계"),
        _selector("school", "School_Unse", where, ["content1", "content2"], "학교 생활"),
    ]
    return _result("studentluck", {
        "ilgan_memno_digit": number, "legacy_age": age,
        "source_over_60_alert": age > 60,
        "alert_semantics": "원본은 60세 초과 시 script 알림만 쓰고 Response.End 없이 계산을 계속함",
    }, selectors)


def _lover(request):
    solar = solar_birth(request.birth)
    zodiac_index = (solar.year - 1900) % 12
    number = ((11 - zodiac_index) + solar.month) % 12
    tables = ("love_lover", "love_knowhow", "love_temptation", "love_slaves", "love_meet", "love_mylover_man" if request.birth.gender == "male" else "love_mylover_woman")
    topics = ("인연 찾기", "데이트 기술", "관심 표현", "서로의 애정", "만남의 기회", "배우자 성향")
    return _result("loverluck", {"solar_year_index": zodiac_index, "solar_month": solar.month, "selected_num": number}, [
        _selector(f"lover-{index}", table, {"Num": number}, ["Content"], topic)
        for index, (table, topic) in enumerate(zip(tables, topics), 1)
    ])


def _sweet(saju, request):
    field = "loveWoman" if request.birth.gender == "female" else "loveMan"
    profile = legacy_profile(saju)
    offset = 3 if request.birth.gender == "female" else 2
    element = "목화토금수"[("목화토금수".index(STEM_ELEMENTS[saju.day_master]) + offset) % 5]
    stages = ("초년", "장년", "중년", "말년")
    selectors = [
        _selector(f"love-period-{name}", "sweetluck", {"yukgap": saju.pillars[name].hanja, "daygan": saju.day_master}, [field], f"{topic}의 애정 흐름")
        for name, topic in zip(("year", "month", "day", "hour"), stages)
    ]
    return _result("sweetluck", {"profile": profile, "relationship_element": element, "selected_column": field}, selectors)


def _counsel(saju, partner):
    profiles = {"birth": legacy_profile(saju)}
    if partner is not None:
        profiles["partner"] = legacy_profile(partner)
    # Counsel uses the shared weights/relations, but has no per-pillar sinsal block.
    for profile in profiles.values():
        profile.pop("sinsal")
    largest = max(value for profile in profiles.values() for value in profile["weighted_five_ki"].values())
    divisor = largest / 100 if largest > 100 else 1
    return _result("counselluck", {
        "profiles": profiles, "shared_graph_divisor": divisor,
        "source_weights": "각 지지 twelvePercent×1, 년월시 천간 자체운성×0.5, 일간60; 공망은 표시만 하고 차감하지 않음",
        "major_luck": {"available": False, "source": "counselluck/daeunsu_m.asp:19, daeunsu_f.asp:24"},
    }, unresolved=["상담오기 원본에는 남녀 대운 include가 함께 출력됩니다. 이 계산에 쓰는 manse.num·disp_day가 제공 tb_manse에 없어 대운 시작나이·구간은 확정하지 않습니다. 오행 그래프·간지·육신·운성의 부분 계산은 제공합니다."])


def _fivegi(saju, request):
    forward = (request.birth.gender == "male") == (STEMS.index(saju.pillars["year"].stem) % 2 == 0)
    return _result("fivegiluck", {
        "profile": legacy_profile(saju), "major_luck_direction": "+" if forward else "-",
        "source_largeflow_rounding": "dateDef / 3; remainder 2면 +1, 이후 각 구간 Int(LargeFlow)",
        "major_luck": {"available": False},
    }, [
        _selector("birth-manse-extra", "manse", {"solar_date": solar_birth(request.birth).date().isoformat()}, ["num", "month_pillar", "disp_day"], "원본 대운 경계 자료", role="calculation", narrative=False)
    ], ["원본 manse.num의 연속 일수 계약과 disp_day 시작·종료 값이 제공 tb_manse에 없습니다. 대운 시작 나이와10개 대운구간을 임의 생성하지 않습니다."])


def _lotto_yongsin(saju):
    p = saju.pillars
    gods = [ten_god(saju.day_master, p[name].stem if part == "s" else p[name].branch) for name, part in (("year", "s"), ("year", "b"), ("month", "s"), ("month", "b"), ("day", "b"), ("hour", "s"), ("hour", "b"))]
    counts = Counter(gods)
    supportive = {"인수", "편인", "비견", "겁재"}
    points = int(gods[3] in supportive) + int(gods[4] in supportive) + int(sum(god in supportive for god in gods) >= 3)
    strong = points >= 2
    selected = ""
    if strong:
        a, b, c = counts["비견"] + counts["겁재"], counts["편인"], counts["인수"]
        d, e = b + c, counts["정관"] + counts["편관"]
        if (a >= 3 and e >= 2) or (d >= 2 and e >= 2):
            selected = "식신"
        elif a >= 2:
            selected = "정관"
        elif b >= 2:
            selected = "편재"
        elif c >= 2 or d >= 2:
            selected = "정재"
        elif e >= 2:
            selected = "식신"
        elif a + b + c >= 2 or gods[3] == "인수" or gods[5] == "비견":
            selected = "정재"
    elif counts["식신"] >= 2:
        selected = "편인"
    elif counts["상관"] >= 2:
        selected = "인수"
    elif sum(counts[key] for key in ("식신", "상관", "편관", "정관", "편재", "정재")) >= 3:
        selected = "비견"
    elif counts["식신"] + counts["상관"] >= 2:
        selected = "인수"
    else:
        selected = "상관"
    offsets = {"비견": 0, "겁재": 0, "식신": 1, "상관": 1, "정재": 2, "편재": 2, "정관": 3, "편관": 3, "인수": 4, "편인": 4}
    element = "목화토금수"[("목화토금수".index(STEM_ELEMENTS[saju.day_master]) + offsets[selected]) % 5] if selected else None
    return gods, points, strong, selected, element


def _lotto(saju, request):
    seed = request.parameters.get("seed")
    if seed is not None and (type(seed) is not int or not 0 <= seed <= 2**32 - 1):
        raise DomainError("invalid_parameter", "seed는 0~4294967295 정수여야 합니다.")
    rng = random.Random(seed)
    gods, points, strong, selected, element = _lotto_yongsin(saju)
    if element is None:
        return _result("lottoluck", {"six_spirits": gods, "strength_points": points}, unresolved=["원본 신강 분기가 해당 입력의 용신을 할당하지 않았습니다. 번호 선택 기준을 임의 보완하지 않습니다."])
    positions = {"목": [3, 5, 8, 11, 24], "화": [2, 5, 7, 9, 14], "토": [0, 1, 5, 6, 10], "금": [4, 5, 9, 13, 36], "수": [1, 5, 6, 7, 16]}[element]
    values = [0] * 6
    rows = []
    for _ in range(37):
        for index in range(6):
            for _attempt in range(10000):
                candidate = int(45 * rng.random()) + 1
                if candidate not in values:
                    values[index] = candidate
                    break
            else:
                raise DomainError("rng_unavailable", "중복 없는 번호를 선택하지 못했습니다.", 503)
        values.sort()
        rows.append(values.copy())
    chosen = [rows[index] for index in positions]
    # The final page reads savebuffer left by its fifth displayed combination.
    explanation_index = chosen[-1][-1] % 10
    return _result("lottoluck", {
        "six_spirits": gods, "strength_points": points, "strength": "신강" if strong else "신약",
        "selected_yongsin": selected, "selected_element": element, "source_positions": positions,
        "generated_sample_count": 37, "selected_combinations": chosen, "seed_supplied": seed is not None,
        "method": "원본처럼 37표본을 만들며 직전 표본의6개 배열을 유지한 채 중복 재추첨하고 각 표본을 정렬함",
        "randomness_note": "번호는 난수 예시이며 실제 당첨 결과나 확률을 예측하는 값이 아님. VBScript 난수열 자체의 바이트 동일성은 주장하지 않음",
        "explanation_index": explanation_index, "meaning_anchor": _DATA["lotto_anchors"][str(explanation_index)],
    }, [_selector("lotto-meaning", "inline:lottoluck", {"solve_un": explanation_index}, ["content"], "원본 번호 선택에 따른 조언", source_anchor=_DATA["lotto_anchors"][str(explanation_index)])])


def _perluck(saju, request):
    table = _DATA["perluck"]
    yj, yg, dj = saju.pillars["year"].branch, saju.pillars["year"].stem, saju.pillars["day"].branch
    lunar_month, lunar_day = saju.lunar_birth["month"], saju.lunar_birth["day"]
    first = (table["onedb"].index(yj) + lunar_month) % 12
    second = (first + lunar_day) % 12
    # Temp3 is uninitialised and added to itself; preserve Empty-as-zero.
    third = second
    titles = [yj, table["twodb"][first], table["threedb"][second], table["fourdb"][third], *table["year_day_titles"][yj + dj]]
    selectors = [_selector(f"total-{index}", "totalun", {"title": title}, ["content"], topic) for index, (title, topic) in enumerate(zip(titles, ("초년", "중년", "말년", "총운", "자식·능력", "장애")), 1)]
    unresolved = []
    selected_cases = {}
    variables = {"result7": yg + str(lunar_month), "result11": yj + str(lunar_month), "result12": yg + dj, "result13": yj + str(lunar_month)}
    lengths = {"result7": {2: 1, 5: 2, 8: 3}, "result11": {2: 1, 3: 1, 5: 2, 8: 3, 11: 3, 14: 3, 17: 3}, "result12": {2: 1, 3: 1, 5: 2, 8: 3, 11: 3}, "result13": {2: 1, 3: 1, 5: 2, 8: 3, 11: 3}}
    for result, value in variables.items():
        matched = [entry["title"] for entry in table[result] if value in entry["cases"]]
        selected_cases[result] = matched
        topic = {"result7": "흉화살", "result11": "출세", "result12": "재물", "result13": "인연"}[result]
        if not matched:
            selectors.append(_selector(result, "inline:perluck", {"section": result, "case": "empty"}, ["content"], topic, source_anchor=table["fallback_anchors"][result]))
            continue
        count = lengths[result].get(len("|".join(matched)))
        if count is None:
            unresolved.append(f"perluck {result} 원본 sQuery 분기가 길이 {len('|'.join(matched))}에 정의되지 않았습니다.")
        else:
            selectors.append(_selector(result, "totalun", {"title": {"in": matched[:count]}}, ["content"], topic))
    solar = solar_birth(request.birth).date()
    md = solar.month * 100 + solar.day
    zodiac_rows = [(321, 420, "화성", "양좌", "뇌대장소"), (421, 520, "금성", "황소좌", "수강췌약"), (521, 621, "수성", "쌍둥이좌", "뇌강기약"), (622, 722, "달", "게좌", "강위약간"), (723, 822, "태양", "사자좌", "강심약관"), (823, 923, "수성", "처녀좌", "관강슬약"), (924, 1022, "금성", "천칭좌", "요대두소"), (1023, 1122, "명왕성", "전갈좌", "기강심약"), (1123, 1224, "목성", "사수좌", "강심약간"), (1225, 1231, "토성", "염소좌", "간강위약"), (101, 119, "토성", "염소좌", "간강위약"), (120, 218, "천왕성", "물독좌", "관강심약"), (219, 320, "해왕성", "물고기좌", "대뇌소위")]
    _, _, planet, sign, health = next(row for row in zodiac_rows if row[0] <= md <= row[1])
    selectors.extend((
        _selector("total-8", "totalun", {"part": "금전 및 행운", "title": planet}, ["content"], "금전·행운"),
        _selector("total-9", "totalun", {"part": "적성", "title": sign}, ["content"], "적성"),
        _selector("total-10", "totalun", {"title": health}, ["content"], "전통적 생활 성향"),
        _selector("total-14", "totalun", {"title": sipkyuk(saju.pillars["month"].branch, saju.day_master)}, ["content"], "직업 성향"),
    ))
    # This specific source's second lunar→solar lookup omits the leap flag.
    try:
        store = get_manse_store()
        raw_candidates = getattr(store, "raw_store", store).lunar_candidates(saju.lunar_birth["year"], lunar_month, lunar_day)
    except ManseDataError as error:
        raise DomainError(error.code, str(error), 503 if error.code == "manse_unavailable" else 422) from None
    if len(raw_candidates) > 1:
        unresolved.append("perluck의 별자리용 음력→양력 재조회가 윤달 조건 없이 여러 날짜를 반환합니다. 원본 선택 순서가 확정되지 않아 별자리3항목의 동일성은 미확정입니다.")
    return _result("perluck", {"lunar_month": lunar_month, "lunar_day": lunar_day, "Temp3_uses_empty_zero": True, "selected_case_titles": selected_cases, "profile": legacy_profile(saju)}, selectors, unresolved)


def _gp_rule(name, first, second):
    """Exact finite source branches, including direction and last checknum wins."""
    return _DATA["sinsalluck"]["tables"]["gp_" + name.lower()].get(
        first + "|" + second, {"match": "", "content_id": 0},
    )


def _sinsal(saju, partner, request):
    male, female = (partner, saju) if request.birth.gender == "female" else (saju, partner)
    m, f = male.pillars, female.pillars
    sections, calls = {}, []

    def group(section, entries):
        text = ""
        for name, first, second in entries:
            rule = _gp_rule(name, first, second)
            text += rule["match"]
            if rule["match"] or rule["content_id"]:
                calls.append({"section": section, "function": "Gp_" + name, "inputs": [first, second], **rule})
        sections[section] = text.strip()

    for period in ("year", "month", "day", "hour"):
        a, b = m[period], f[period]
        if period == "year":
            positive = [("GanHap", a.stem, b.stem), ("YukHap", a.branch, b.branch), ("SamHap", a.branch, b.branch)]
            negative = [(name, a.branch, b.branch) for name in ("Chung", "Pa", "Hae")]
        elif period == "month":
            positive = [("GanHap", a.stem, b.stem), ("YukHap", m["year"].branch, b.branch), ("YukHap", a.branch, f["year"].branch)]
            negative = [(name, a.branch, b.branch) for name in ("Chung", "Pa", "Hae")]
        else:
            positive = ([("GanHap", a.stem, b.stem)] if period == "day" else []) + [("YukHap", a.branch, b.branch), ("InSamHap", a.branch, b.branch)]
            negative = [("GanChung", a.stem, b.stem), ("InChung", a.branch, b.branch)]
        group(period + "_combinations", positive)
        group(period + "_conflicts", negative)
    for gender, own, other in (("male", m, f), ("female", f, m)):
        direction = "m2f" if gender == "male" else "f2m"
        y, oy = own["year"], other["year"]
        year_entries = [
            ("WonJin_" + direction, y.branch, oy.branch),
            ("GoGwa_" + direction, y.stem, other["month"].branch),
            ("GoGwa2_" + direction, y.branch, oy.branch),
            ("Relation", y.stem, oy.stem), ("SamJae", y.branch, oy.branch),
        ]
        if gender == "male":
            year_entries.append(("SamJae2_m2f", y.branch, oy.branch))
        year_entries.append(("JiSal", y.branch, oy.branch))
        group(gender + "_year", year_entries)
        group(gender + "_month", [("WolJi", own["month"].branch, other["month"].hanja)])
        group(gender + "_day", [
            ("ILGan", own["day"].stem, other["day"].branch),
            ("ILJi", own["day"].branch, other["day"].branch),
            ("DoWha", own["day"].branch, other["day"].branch),
        ])
    supplied = request.parameters.get("legacy_gpcheck")
    whitelist = {row["content_id"] for table in _DATA["sinsalluck"]["tables"].values() for row in table.values()} - {0}
    if supplied is not None and (
        not isinstance(supplied, list) or len(supplied) > 64
        or any(type(value) is not int or value not in whitelist for value in supplied)
    ):
        raise DomainError("invalid_service_parameters", "legacy_gpcheck는 원본 판정 코드 화이트리스트에 있는 정수의 배열이며 최대64개입니다.")
    # Request.Cookies is fixed during the request; response writes never update it.
    incoming = "|" + "|".join(map(str, supplied)) if supplied else ""
    pending = [call["content_id"] for call in calls if call["content_id"] and f"|{call['content_id']}|" not in incoming]
    cookie_count = len(pending)
    selectors = [_selector("pair-character", "gp_character", {"male": male.day_master, "female": female.day_master}, ["content"], "두 사람의 성격 조화")]
    unresolved = []
    if supplied is None:
        unresolved.append("궁합신살 본문은 이전 요청의 gpcheck 쿠키와 함수 호출 수에 의존합니다. legacy_gpcheck 숫자 배열이 없어 원본 gp_content 최종 선택을 확정하지 않습니다.")
    elif len(supplied) < cookie_count:
        unresolved.append("원본 gp_func_count가 이전 gpcheck 배열 길이를 초과하여 원본 gpcheck_arr(i) 조회가 실패하는 상태입니다. 새 판정 코드로 조용히 대체하지 않습니다.")
    else:
        selectors.extend(
            _selector(f"sinsal-{index}", "gp_content", {"num": code}, ["title", "content"], "궁합신살의 전통적 의미")
            for index, code in enumerate(supplied[:cookie_count], 1)
        )
    if request.partner is not None and request.birth.gender == request.partner.gender:
        unresolved.append("원본은 남자·여자 역할별 두 입력을 사용합니다. 동일 성별 입력의 역할 대응이 정의되지 않아 방향별 본문 동일성을 확정하지 않습니다.")
    return _result("sinsalluck", {
        "male_day_stem": male.day_master, "female_day_stem": female.day_master,
        "source_helper": "old/unse/sinsalluck/gp_func.asp", "matched_sections": sections,
        "matched_source_calls": calls, "gp_func_count": cookie_count,
        "response_cookie_write_count": cookie_count,
        "response_cookie_last_append": pending[-1] if pending else None,
        "incoming_cookie_code_count": len(supplied) if supplied is not None else None,
        "cookie_contract": "Response.Cookies의 값은 같은 요청 Request.Cookies에 반영되지 않으며, 포함 검사는 |코드| 문자열·최종 조회는 이전 배열의 앞 gp_func_count개를 사용함",
    }, selectors, unresolved)


def decide(service_id: str, request: ServiceRequest, saju: SajuResult | None, partner: SajuResult | None) -> dict:
    if service_id not in SERVICES:
        raise DomainError("service_not_supported", "지원하지 않는 원본 서비스입니다.", 404)
    if request.birth is None:
        raise DomainError("birth_required", "생년월일시를 입력해 주세요.")
    allowed = {"seed"} if service_id == "lottoluck" else {"legacy_gpcheck"} if service_id == "sinsalluck" else set()
    if set(request.parameters) - allowed:
        raise DomainError("invalid_service_parameters", "이 서비스의 parameters 이름·허용 범위를 확인하세요.")
    if service_id == "adultluck-timesexbioluck":
        return _hour_bio(request)
    if service_id == "loverluck":
        return _lover(request)
    saju = _required_saju(saju)
    if service_id == "ddiluck":
        return _ddiluck(saju)
    if service_id == "meetluck":
        return _meet(saju, request)
    if service_id == "studentluck":
        return _student(saju, request)
    if service_id == "sweetluck":
        return _sweet(saju, request)
    if service_id == "counselluck":
        return _counsel(saju, partner)
    if service_id == "fivegiluck":
        return _fivegi(saju, request)
    if service_id == "lottoluck":
        return _lotto(saju, request)
    if service_id == "perluck":
        return _perluck(saju, request)
    return _sinsal(saju, _required_saju(partner), request)

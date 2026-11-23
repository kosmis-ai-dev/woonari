"""CR-001 / T-006: preserve lifeluck and moneyluck ASP decisions.

The original text-table lookup is represented as an immutable selection contract;
the caller may replace those text rows with AI prose, but not change the keys.
This module performs no SQL/COM calls and does not use replacement daily scores.
"""

from app.errors import DomainError
from app.models import FortuneRequest, SajuResult
from app.rules import (
    BRANCHES,
    GANJI,
    STEMS,
    life_stage,
    ten_god,
)

LIFETIME_SOURCE = "old/unse/lifeluck/main_end.asp"
WEALTH_SOURCE = "old/unse/moneyluck/main_end.asp"
HELPER_SOURCE = "function/dotong_function.asp"

# dotong_function.asp:396-413 / 541-562, including the 2006-11-13 revisions.
TWELVE_PERCENT = {
    "태": 40,
    "양": 50,
    "장생": 90,
    "목욕": 30,
    "관대": 80,
    "건록": 80,
    "제왕": 100,
    "쇠": 60,
    "병": 50,
    "사": 10,
    "묘": 10,
    "절": 10,
}
ELEMENT_HANJA = dict(zip("목화토금수", ("木", "火", "土", "金", "水")))
SIPKYUK_CODES = {
    "비견": "1",
    "겁재": "2",
    "식신": "3",
    "상관": "4",
    "편재": "5",
    "정재": "6",
    "편관": "7",
    "정관": "8",
    "편인": "9",
    "인수": "0",
}
GONGMANG = ("戌亥", "申酉", "午未", "辰巳", "寅卯", "子丑")


def sipkyuk(month_branch: str, day_stem: str) -> str:
    """SipKyuk(月支, 日干), dotong_function.asp:1319-1366.

    The explicit original 120-case table is equivalent to the source's SixSpirit
    mapping followed by this numeric code. Tests compare all original cases.
    """
    return SIPKYUK_CODES[ten_god(day_stem, month_branch)]


def dang_code(branch: str) -> str:
    """cg_dang (子=a, 丑=b, ...), source:1411-1428."""
    return "abcdefghijkl"[BRANCHES.index(branch)]


def dangsaju_code(first_branch: str, second_branch: str) -> str:
    """cg_dangsaju's 144-case ordered difference table, source:1432-1451."""
    return "abcdefghijkl"[(BRANCHES.index(second_branch) - BRANCHES.index(first_branch)) % 12]


def _pairs(text: str, definitions: tuple[str, ...]) -> str:
    return "".join(
        value + " " for value in definitions if all(char in text for char in value.split("(")[0])
    )


def legacy_hyung(branches: str) -> str:
    """Preserve the source's two-character global Replace for self-punishments.

    Do not replace it with a count >= 2 test: those differ for adjacent duplicates.
    """
    result = _pairs(
        branches,
        ("寅巳(刑)", "巳申(刑)", "申寅(刑)", "丑戌(刑)", "戌未(刑)", "未丑(刑)", "子卯(刑)"),
    )
    for char in "辰午酉亥":
        if char in branches:
            pos = branches.index(char)
            remaining = branches.replace(branches[pos : pos + 2], "")
            if char in remaining:
                result += char * 2 + "(刑) "
    return result


def _relations(stems: str, branches: str) -> dict:
    gan = _pairs(stems, ("甲己(土)", "乙庚(金)", "丙辛(水)", "丁壬(木)", "戊癸(火)"))
    yuk = _pairs(branches, ("子丑(土)", "寅亥(木)", "戌卯(火)", "辰酉(金)", "申巳(水)", "午未"))
    sam = _pairs(branches, ("申子辰(水)", "巳酉丑(金)", "寅午戌(火)", "亥卯未(木)"))
    half = _pairs(
        branches,
        (
            "申子(水)",
            "辰子(水)",
            "巳酉(金)",
            "丑酉(金)",
            "寅午(火)",
            "戌午(火)",
            "亥卯(木)",
            "未卯(木)",
        ),
    )
    hyung = legacy_hyung(branches)
    chung = _pairs(
        branches, ("子午(沖)", "丑未(沖)", "寅申(沖)", "卯酉(沖)", "辰戌(沖)", "巳亥(沖)")
    )
    pa = _pairs(branches, ("子酉(破)", "午卯(破)", "申巳(破)", "寅亥(破)", "辰丑(破)", "戌未(破)"))
    hae = _pairs(branches, ("子未(害)", "丑午(害)", "寅巳(害)", "卯辰(害)", "申亥(害)", "酉戌(害)"))
    return {
        "GanHap": gan,
        "YukHap": yuk,
        "SamHap": sam,
        "HalfHap": half,
        "Hyung": hyung,
        "Chung": chung,
        "Pa": pa,
        "Hae": hae,
        "HapL": gan + yuk + sam + half,
        "PaL": hyung + chung + pa + hae,
    }


def _group_result(first: str, second: str, groups, targets) -> bool:
    return any(first in group and second == target for group, target in zip(groups, targets))


def _sinsal(pillars: dict[str, str]) -> dict[str, str]:
    """Original call order and even the hour GoSin/GwaSuk day-branch arguments."""
    day_stem, day_branch = pillars["day"]
    year_branch = pillars["year"][1]
    month_branch = pillars["month"][1]
    stem_index = STEMS.index(day_stem)
    same_stem = (
        ("양인", "卯辰午未午未酉戌子丑"),
        ("비인", "酉戌子丑子丑卯辰午未"),
        ("금여", "辰巳未申未申戌亥丑寅"),
        ("암록", "亥戌申未申未巳辰寅丑"),
        ("문창성", "巳午申酉申酉亥子寅卯"),
    )
    groups = ("寅午戌", "申子辰", "巳酉丑", "亥卯未")
    virtues = dict(zip("寅卯辰巳午未申酉戌亥子丑", "丁申壬辛亥甲癸寅丙乙巳庚"))
    output = {}
    for name in ("year", "month", "day", "hour"):
        stem, branch = pillars[name]
        matches = []
        # YangIn / BeeIn / GoyGang / GumYe / AmRok / MunChang
        for label, mapping in same_stem[:2]:
            if branch == mapping[stem_index]:
                matches.append(label)
        if stem + branch in {"庚辰", "壬辰", "戊戌", "庚戌"}:
            matches.append("괴강")
        for label, mapping in same_stem[2:]:
            if branch == mapping[stem_index]:
                matches.append(label)
        if _group_result(
            day_stem,
            branch,
            ("甲戊庚", "乙己", "丙丁", "壬癸", "辛"),
            ("丑", "子", "亥", "巳", "午"),
        ) or _group_result(
            day_stem,
            branch,
            ("甲戊庚", "乙己", "丙丁", "壬癸", "辛"),
            ("未", "申", "酉", "卯", "寅"),
        ):
            matches.append("천을귀인")
        if virtues[month_branch] in stem + branch:
            matches.append("천덕귀인")
        if _group_result(month_branch, stem, ("寅午戌", "亥卯未", "申子辰", "巳酉丑"), "丙甲壬庚"):
            matches.append("월덕귀인")
        if name != "day":
            for label, targets in (
                ("장성", "午子酉卯"),
                ("화개", "戌辰丑未"),
                ("역마", "申寅亥巳"),
                ("도화", "卯酉午子"),
            ):
                if _group_result(day_branch, branch, groups, targets):
                    matches.append(label)
        if name != "year":
            # H_SinsalL deliberately passes DayJi, not HourJi (source life:415-420).
            opposite = day_branch if name == "hour" else branch
            if _group_result(
                year_branch, opposite, ("子丑亥", "寅卯辰", "巳午未", "申酉戌"), "寅巳申亥"
            ):
                matches.append("고신")
            if _group_result(
                year_branch, opposite, ("子丑亥", "寅卯辰", "巳午未", "申酉戌"), "戌丑辰未"
            ):
                matches.append("과숙")
        output[name] = "".join(label + " " for label in matches)
    return output


def legacy_profile(saju: SajuResult) -> dict:
    """Shared profile from lifeluck:242-422 / moneyluck:1138-1333.

    These are source-weighted 오기 values, not the earlier 8-character count.
    """
    pillars = {name: p.hanja for name, p in saju.pillars.items()}
    day_stem = pillars["day"][0]
    weighted = dict.fromkeys("목화토금수", 0.0)
    percentages, stages, own_stages, spirits = {}, {}, {}, {}
    gong = GONGMANG[GANJI.index(pillars["day"]) // 10]
    gong_by_pillar = {}
    contributions = []
    for name in ("year", "month", "day", "hour"):
        p = saju.pillars[name]
        stage = life_stage(day_stem, p.branch)
        stages[name] = stage
        percentages[name] = TWELVE_PERCENT[stage]
        weighted[p.branch_element] += TWELVE_PERCENT[stage]
        contributions.append(
            {
                "pillar": name,
                "part": "branch",
                "element": p.branch_element,
                "stage": stage,
                "weight": 1,
                "value": TWELVE_PERCENT[stage],
            }
        )
        if name == "day":
            # 2006-11-17: old 100 changed to 60, independently of day life stage.
            weighted[p.stem_element] += 60
            contributions.append(
                {
                    "pillar": name,
                    "part": "stem",
                    "element": p.stem_element,
                    "stage": None,
                    "weight": 1,
                    "value": 60,
                }
            )
        else:
            own = life_stage(p.stem, p.branch)
            own_stages[name] = own
            value = TWELVE_PERCENT[own] * 0.5
            weighted[p.stem_element] += value
            gong_by_pillar[name] = gong if p.branch in gong else ""
            contributions.append(
                {
                    "pillar": name,
                    "part": "stem",
                    "element": p.stem_element,
                    "stage": own,
                    "weight": 0.5,
                    "value": value,
                }
            )
        spirits[name] = {"branch": ten_god(day_stem, p.branch)}
        if name != "day":
            spirits[name]["stem"] = ten_god(day_stem, p.stem)
    stems = "".join(pillars[name][0] for name in ("year", "month", "day", "hour"))
    branches = "".join(pillars[name][1] for name in ("year", "month", "day", "hour"))
    largest = max(weighted.values())
    return {
        "source": HELPER_SOURCE + ":244-1044",
        "pillars": pillars,
        "life_stages": stages,
        "life_stage_percent": percentages,
        "own_pillar_life_stages": own_stages,
        "six_spirits": spirits,
        "weighted_five_ki": weighted,
        "five_ki_contributions": contributions,
        "graph_divisor": largest / 100 if largest > 100 else 1,
        "gongmang": {"GongL": gong, "by_pillar": gong_by_pillar},
        "relations": _relations(stems, branches),
        "sinsal": _sinsal(pillars),
    }


def _selector(identifier, table, where, columns, purpose):
    return {
        "id": identifier,
        "table": table,
        "where": where,
        "columns": columns,
        "purpose": purpose,
    }


def _lifetime(saju: SajuResult) -> dict:
    pillars = {k: p.hanja for k, p in saju.pillars.items()}
    code = sipkyuk(pillars["month"][1], pillars["day"][0])
    early = dang_code(pillars["year"][1])
    middle = dangsaju_code(pillars["year"][1], pillars["month"][1])
    late = dangsaju_code(pillars["month"][1], pillars["day"][1])
    selectors = []
    bindings = []
    for index, (key, label) in enumerate(
        (("values", "가치관"), ("character", "성품"), ("advice", "어드바이스")), 1
    ):
        identifier = "lifetime-private-" + key
        selectors.append(
            _selector(
                identifier,
                "tbSaju_private",
                {"hname": pillars["day"]},
                [f"desc{index}"],
                "평생운세 " + label,
            )
        )
        bindings.append(
            {
                "output_variable": f"private{index}",
                "selector_id": identifier,
                "column": f"desc{index}",
            }
        )
    for index, (key, label) in enumerate(
        (
            ("type", "나의 타입"),
            ("strengths", "장점"),
            ("relations", "대인관계"),
            ("advice", "어드바이스"),
            ("summary", "요점정리"),
        ),
        1,
    ):
        identifier = "lifetime-social-" + key
        selectors.append(
            _selector(
                identifier,
                "tbSaju_otherunse",
                {"sipkyuk_code": code, "unse": "social"},
                [f"desc{index}"],
                "사회적 운세 " + label,
            )
        )
        bindings.append(
            {
                "output_variable": f"social{index}",
                "selector_id": identifier,
                "column": f"desc{index}",
            }
        )
    for key, variable, value, column, label in (
        ("early", "year_unse", early, "desc1", "초년운"),
        ("middle", "mon_unse", middle, "desc2", "중년운"),
        ("late", "day_unse", late, "desc3", "말년운"),
    ):
        identifier = "lifetime-dangsaju-" + key
        selectors.append(
            _selector(identifier, "tbSaju_dangsaju", {"dang_code": value}, [column], label)
        )
        bindings.append({"output_variable": variable, "selector_id": identifier, "column": column})
    for index in (1, 2):
        identifier = f"lifetime-money-{index}"
        selectors.append(
            _selector(
                identifier,
                "tbSaju_otherunse",
                {"sipkyuk_code": code, "unse": "money"},
                [f"desc{index}"],
                f"재물운 {index}",
            )
        )
        bindings.append(
            {
                "output_variable": f"money{index}",
                "selector_id": identifier,
                "column": f"desc{index}",
            }
        )
    return {
        "source": LIFETIME_SOURCE,
        "facts": {
            "sipkyuk_code": code,
            "sipkyuk_ten_god": ten_god(pillars["day"][0], pillars["month"][1]),
            "dangsaju": {"year_dang": early, "mon_dang": middle, "day_dang": late},
            "profile": legacy_profile(saju),
            "output_bindings": bindings,
            "excluded_non_narrative": [
                {
                    "component": "daeun",
                    "source": LIFETIME_SOURCE + ":459-626,812-859",
                    "reason": "대운 출력표는 HTML 주석 처리됨. in_ypillar/in_mpillar/my_minute는 해당 실행 소스에 할당되지 않아 임의 복구하지 않음.",
                },
                {
                    "component": "jikjang/job",
                    "source": LIFETIME_SOURCE + ":182-190",
                    "reason": "조회되나 이 페이지의 실제 결과에는 출력되지 않는 항목이므로 AI 출력항목에서 제외.",
                },
            ],
        },
        "selectors": selectors,
        "unresolved": [],
    }


def _wealth(saju: SajuResult, gender: str) -> dict:
    selectors, bindings = [], []
    for name, label, variable in (
        ("year", "초년", "myCho"),
        ("month", "장년", "myJang"),
        ("day", "중년", "myJung"),
        ("hour", "말년", "myMal"),
    ):
        identifier = "wealth-" + name
        selectors.append(
            _selector(
                identifier,
                "Moneyluck",
                {"yukgap": saju.pillars[name].hanja, "daygan": saju.day_master},
                ["Money"],
                label + " 재물운",
            )
        )
        bindings.append({"output_variable": variable, "selector_id": identifier, "column": "Money"})
    # Render-time branches at moneyluck:2636-2715; keep the actual controlled
    # element mapping rather than let AI substitute a modern favorable-element rule.
    element_index = "목화토금수".index(saju.pillars["day"].stem_element)
    element_names = ("목(木)", "화(火)", "토(土)", "금(金)", "수(水)")
    colors = ("청(靑)", "적(赤)", "황(黃)", "백(白)", "흑(黑)")
    wealth_index = (element_index + 2) % 5
    weighted = legacy_profile(saju)
    return {
        "source": WEALTH_SOURCE,
        "facts": {
            "profile": weighted,
            "output_bindings": bindings,
            "dokebi": ("M" if gender == "male" else "F") + saju.legacy_memno,
            "memno": saju.legacy_memno[0],
            "day_element_hanja": ELEMENT_HANJA[saju.pillars["day"].stem_element],
            "mybar": str("목화토금수".index(saju.pillars["day"].stem_element) + 1),
            "rendered_inline": {
                "source": WEALTH_SOURCE + ":2636-2721",
                "fivegi": element_names[element_index],
                "color": colors[element_index],
                "notfivegi": element_names[wealth_index],
                "notcolor": colors[wealth_index],
                "wealth_ki": weighted["weighted_five_ki"]["목화토금수"[wealth_index]],
                "wealth_spirits": ["정재", "편재"],
                "other_source_explanation": "원본 2717행: 비견·겁재 또는 인수·편인이 많으면 재물운이 약하다는 설명. ASP에 '많음'의 수치 기준은 없어 임계값/점수를 추가하지 않습니다.",
                "source_interpretation_rule": "일간이 이기는 오행의 기둥이 높을수록 재물운이 좋고 많다는 원본 설명. 신강/용신 계산으로 대체하지 않음.",
            },
        },
        "selectors": selectors,
        "unresolved": [],
    }


def decide_life_wealth(kind: str, request: FortuneRequest, saju: SajuResult) -> dict:
    """Use a source-specific dotong CalcSaju result supplied by the caller."""
    if kind == "lifetime":
        return _lifetime(saju)
    if kind == "wealth":
        return _wealth(saju, request.birth.gender)
    raise DomainError("unsupported_legacy_kind", "평생운세 또는 재물운을 지정해 주세요.")

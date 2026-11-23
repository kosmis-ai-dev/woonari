"""CR-012/T-024: original row-consuming rules; supplied rows stay investigation-only."""

from __future__ import annotations

import re
from calendar import monthrange
from datetime import date

from app.calendar import _birth_record, calculate_saju
from app.errors import DomainError
from app.manse_store import get_manse_store
from app.ported_interlife import _selector
from app.rules import BRANCHES, STEMS

SALS = ("sal_chun", "sal_pima", "sal_hongsa", "sal_susa", "sal_mangra", "sal_chunjuk", "sal_gocho",
        "sal_guigi", "sal_wangmang", "sal_sipak", "sal_wolap", "sal_wol", "sal_hwangsa")
FLAGS = (*SALS, "yellow_black", "hap_chunduk", "hap_wolduk", "sipak_il", "sipak_daepae")
GOOD_MONTHS = (
    ("중계", "옹고", "여민", "부주", "여신", "대리"),
    ("부주", "여민", "옹고", "중계", "대리", "여신"),
    ("여신", "대리", "중계", "옹고", "여민", "부주"),
    ("대리", "여신", "부주", "여민", "옹고", "중계"),
    ("여민", "부주", "여신", "대리", "중계", "옹고"),
    ("옹고", "중계", "대리", "여신", "부주", "여민"),
)


def _spec(name, sources, *, birth=True, partner=False, parameters=None, materials=()):
    return {"name": name, "original_name": name, "requires_birth": birth, "requires_partner": partner,
            "uses_saju": False, "ready": False, "example_parameters": parameters or {},
            "parameter_help": {}, "source": sources, "required_source_fields": list(materials),
            "source_limits": ["원본 DB 행의 비교·합산은 이식하나 입력한 조사용 source_rows는 실제 DB로 인증되지 않습니다. 최종 AI 차단은 유지합니다."]}


SERVICES = {
    "calendarluck": _spec("월un 달력", "old/unse/calendarluck/main_end.asp:138-174,402-423",
                          materials=("tbCalUnse do_num/sex/unsecode별 change/chungan/jiji",)),
    "marriageluck": _spec("결혼택일", "old/unse/marriageluck/main_end.asp:195-407,814-938", partner=True,
                          materials=("chosenday 날짜별18개 실제 판정 플래그", "tbLuckDay 성별·나이mod8별 luckDay")),
    "moveluck": _spec("이사택일", "old/unse/moveluck/main_end1.asp:139-269,608-715; old/unse/moveluck/main_end2.asp:142-258",
                      parameters={"mode": "single"}, materials=("chosenday 날짜별18개 실제 판정 플래그", "tbLuckDay 성별·나이mod8별 luckDay", "tbLocation gender/age_0..8별 실제 방향·cont_idx")),
    "mindluck": _spec("심리테스트", "old/unse/mindluck/main_end.asp:186-237,256-265,350-365,401-408", birth=False,
                      parameters={"mental_id": 1, "answer_index": 0},
                      materials=("mental_content 최초행 content_num", "mental_member 정렬된 선택지 수·member_num", "mental_result 정렬된 result_num 대응")),
}
for key, spec in SERVICES.items():
    spec["parameter_help"]["source_rows"] = "선택: 이 서비스가 사용하는 고정 열만 받는 원본 행 조사 객체. 표/SQL을 지정하지 못하며 입력해도 실제 DB 인증이나 AI 차단을 우회하지 않습니다."
    if key != "mindluck":
        spec["parameter_help"]["year"] = "조회 양력 연도(1900~2050). 생략하면 target_date의 연도입니다."
        spec["parameter_help"]["month"] = "조회 양력 월(1~12). 생략하면 target_date의 월입니다."
SERVICES["calendarluck"]["parameter_help"]["do_num"] = "선택: 원본 Left(id,1)의 숫자 코드 0~9. 로그인 ID 원문을 받거나 사주에서 추정하지 않습니다."
SERVICES["moveluck"]["parameter_help"]["mode"] = "single은 본인 성별 경로, couple은 원본 남자/여자 두 칸 경로입니다. couple의 birth는 남자 칸, partner는 여자 칸입니다."
SERVICES["mindluck"]["parameter_help"].update({
    "mental_id": "원본 심리테스트 양수 ID. 실제 문항/선택지 구조는 별도 원본 자료가 필요합니다.",
    "answer_index": "선택: 화면에 표시되는 선택지 인덱스 0~3. 원본은 점수 계산 없이 같은 인덱스의 result를 표시합니다.",
})


def _invalid(message="원본 조사 행의 허용 열·형식·범위를 확인하세요."):
    raise DomainError("invalid_service_parameters", message)


def _integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        _invalid()
    return value


def _rows(value, required, optional=(), limit=100):
    if value is None:
        return None
    if not isinstance(value, list) or len(value) > limit:
        _invalid()
    for row in value:
        if not isinstance(row, dict) or not set(required) <= row.keys() or set(row) - set(required) - set(optional):
            _invalid()
    return value


def _source_rows(request, allowed):
    rows = request.parameters.get("source_rows", {})
    if not isinstance(rows, dict) or set(rows) - set(allowed):
        _invalid()
    return rows


def _month(request):
    year = _integer(request.parameters.get("year", request.target_date.year), 1900, 2050)
    month = _integer(request.parameters.get("month", request.target_date.month), 1, 12)
    count = monthrange(year, month)[1]
    store = get_manse_store()
    rows = [store.solar_record(date(year, month, day)) for day in range(1, count + 1)]
    calendar = [{"day": day, "day_pillar": STEMS[int(row["d_gan"])] + BRANCHES[int(row["d_ji"])],
                 "lunar_month": int(row["l_mon"]), "lunar_day": int(row["l_day"])}
                for day, row in enumerate(rows, 1)]
    lichun = next((day for day, row in enumerate(rows, 1) if month == 2 and int(row["div_name"]) == 1), 0)
    return year, month, calendar, lichun


def _data_selector(identifier, table, where, columns, purpose):
    result = _selector(identifier, table, where, columns, purpose)
    result.update(role="calculation", narrative=False)
    return result


def calendar_icons(pillar, rules):
    """The source merges positional rows8/9 into icon8 and never prints icon9."""
    stem, branch = pillar

    def matches(row):
        return branch == row["jiji"] and (stem == row["change"] or stem != row["chungan"])

    return [index for index in (*range(1, 9), 10, 11)
            if matches(rules[index - 1]) or index == 8 and matches(rules[8])]


def _calendarluck(request):
    year, month, calendar, _ = _month(request)
    do_num = request.parameters.get("do_num")
    if do_num is not None:
        _integer(do_num, 0, 9)
    rules = _rows(_source_rows(request, {"cal_rules"}).get("cal_rules"), ("unsecode", "change", "chungan", "jiji"), limit=11)
    if rules is not None:
        if len(rules) != 11:
            _invalid("cal_rules에는 원본 unsecode가 서로 다른 정확히11행이 필요합니다.")
        for row in rules:
            _integer(row["unsecode"], 0, 99999)
            if any(not isinstance(row[key], str) or len(row[key]) != 1 for key in ("change", "chungan", "jiji")) or row["change"] not in STEMS or row["chungan"] not in STEMS or row["jiji"] not in BRANCHES:
                _invalid()
        if len({row["unsecode"] for row in rules}) != 11:
            _invalid()
        rules = sorted(rules, key=lambda row: row["unsecode"])
    for day in calendar:
        day["icons"] = calendar_icons(day["day_pillar"], rules) if rules is not None else None
    selector = _data_selector("calendar-rules", "tbCalUnse", {"do_num": do_num, "sex": "남" if request.birth.gender == "male" else "여"},
                              ["unsetype", "change", "chungan", "jiji"], "unsecode 순서의 원본11개 일진 판정 규칙")
    selector["order_by"] = "unsecode"
    return {"year": year, "month": month, "monthly_calendar": calendar,
            "source_do_num": do_num, "rules_supplied_for_investigation": rules is not None,
            "source_icon9_is_merged_into8": True}, [selector], ["tbCalUnse의 실제11행과 do_num/성별 선택 근거가 미확보입니다. 조사용 행을 입력해도 실제 DB 검증은 완료되지 않습니다."]


def score_day(flags, daegil):
    """Shared marriage/moving order: any harm replaces all prior positive points."""
    harmful = sum(flags[key] for key in SALS) + 10 * flags["sipak_il"] + 10 * flags["sipak_daepae"]
    score = 50 + 13 * flags["yellow_black"] + 19 * daegil + 9 * flags["hap_chunduk"] + 9 * flags["hap_wolduk"]
    if harmful:
        score = 50 - harmful
    if daegil and not harmful and not flags["yellow_black"]:
        score = 81
    icons = []
    if daegil and not harmful and flags["yellow_black"]:
        icons = ["대길", "황도"] + (["천덕합"] if flags["hap_chunduk"] else []) + (["월덕합"] if flags["hap_wolduk"] else [])
    return {"score": score, "harmful_count_weighted": harmful, "daegil": daegil,
            "mark": "▼" if score < 50 else "■" if score == 50 else "▲", "icons": icons}


def _luck_days(value):
    rows = _rows(value, ("male", "female", "luckDay"), limit=100)
    if rows is not None:
        for row in rows:
            _integer(row["male"], 0, 7)
            _integer(row["female"], 0, 7)
            if not isinstance(row["luckDay"], str) or len(row["luckDay"]) != 1 or row["luckDay"] not in BRANCHES:
                _invalid()
    return rows


def _chosen_days(value, count):
    rows = _rows(value, ("day", *FLAGS), limit=31)
    if rows is not None:
        for row in rows:
            _integer(row["day"], 1, count)
            if any(type(row[key]) is not bool for key in FLAGS):
                _invalid()
        if len({row["day"] for row in rows}) != len(rows):
            _invalid()
    return {row["day"]: row for row in rows} if rows is not None else None


def _age(birth, use_year):
    _, raw = _birth_record(birth)
    return use_year - int(raw["l_year"]) + 1


def _couple(request, required):
    if required and request.partner is None:
        raise DomainError("missing_partner", "이 원본 경로에는 partner가 필요합니다.")


def _month_guidance(request, month):
    result = []
    for birth in (request.birth, request.partner):
        fixed = birth.model_copy(update={"hour": 10, "minute": 0})
        branch = calculate_saju(fixed, "dotong").pillars["year"].branch
        row = GOOD_MONTHS[BRANCHES.index(branch) % 6]
        good = [row.index("대리") + 1, row.index("중계") + 1]
        result.append({"birth_year_branch_at_source_10am": branch, "current_month_class": row[(month - 1) % 6], "base_good_months": good})
    male = sorted(result[0]["base_good_months"])
    return {"roles": result, "source_arGoodMon_from_male_only": [*male, male[0] + 6, male[1] + 6],
            "source_existGoodMon": bool(set(result[0]["base_good_months"]) & set(result[1]["base_good_months"]))}


def _directions(value, ages, single_gender):
    rows = _rows(value, ("gender", "cont_idx", *(f"age_{i}" for i in range(9))), limit=8)
    if rows is None:
        return None
    for row in rows:
        _integer(row["gender"], 0, 1)
        _integer(row["cont_idx"], 0, 100)
        if any(not isinstance(row[f"age_{i}"], str) or re.fullmatch(r"[동서남북東西南北()（）\s]{1,12}", row[f"age_{i}"]) is None for i in range(9)):
            _invalid()
    if single_gender is not None:
        chosen = [row for row in rows if row["gender"] == single_gender]
        if len(chosen) != 4:
            _invalid("single locations에는 원본 해당 성별4행이 필요합니다.")
        return {"mode": "single", "directions": [{"direction": row[f"age_{ages[0] % 9}"], "description_index": row["cont_idx"]} for row in chosen[:4]]}
    ordered = sorted(rows, key=lambda row: row["gender"])
    if len(ordered) != 8 or [row["gender"] for row in ordered] != [0] * 4 + [1] * 4:
        _invalid("couple locations에는 원본 남자4행·여자4행이 필요합니다.")
    # Original uses recordset position i<4, then column2 for remaining rows.
    values = [row[f"age_{ages[0 if i < 4 else 1] % 9}"] for i, row in enumerate(ordered)]
    slots = [None] * 16  # Original Dim arrResult(15), including overlapping k/k+4 writes.
    matches, overflow = [], False
    for i in range(4):
        for j in range(4, 8):
            if values[i] == values[j]:
                k = len(matches)
                matches.append((i, j))
                slots[k] = i
                if k + 4 >= len(slots):
                    overflow = True
                    break
                slots[k + 4] = j
        if overflow:
            break
    displayed = None if overflow else [
        {"male_index": slots[i] or 0, "female_recordset_index": slots[i + 4] or 0,
         "direction": values[slots[i] or 0]} for i in range(len(matches))
    ]
    return {"mode": "couple", "male": values[:4], "female": values[4:],
            "source_display_path": "male_only_fallback" if not matches else "shared_pairs",
            "source_display_pairs": displayed, "source_array_overflow": overflow,
            "source_overlapping_arrResult": slots}


def _chosen_service(service_id, request):
    marriage = service_id == "marriageluck"
    mode = "couple" if marriage else request.parameters.get("mode", "single")
    if not isinstance(mode, str) or mode not in {"single", "couple"}:
        _invalid("mode는 single 또는 couple이어야 합니다.")
    _couple(request, mode == "couple")
    year, month, calendar, lichun = _month(request)
    source = _source_rows(request, {"luck_days", "chosen_days", "locations"} if not marriage else {"luck_days", "chosen_days"})
    luck = _luck_days(source.get("luck_days"))
    flags = _chosen_days(source.get("chosen_days"), len(calendar))
    age_year = year - 1 if month == 1 else year
    births = (request.birth, request.partner) if mode == "couple" else (request.birth,)
    ages = [_age(birth, age_year) for birth in births]
    if any(age < 1 for age in ages):
        raise DomainError("target_before_birth", "조회월은 출생 이후여야 합니다.")
    genders = (0, 1) if mode == "couple" else (0 if request.birth.gender == "male" else 1,)
    selectors = []
    for index, (age, gender) in enumerate(zip(ages, genders)):
        column = "male" if gender == 0 else "female"
        selectors.append(_data_selector(f"luck-{index}", "tbLuckDay", {"luck": "대길", column: age % 8}, ["luckDay", "luckDayNo", "luckDesc"], "성별·음력생년 나이mod8 길일"))
        if lichun:
            selectors.append(_data_selector(f"luck-before-{index}", "tbLuckDay", {"luck": "대길", column: (age - 1) % 8}, ["luckDay", "luckDayNo", "luckDesc"], "2월 입춘일 전 나이−1 길일"))
    selectors.append(_data_selector("chosen-days", "chosenday", {"syear": year, "smonth": month}, ["day_pillar", *FLAGS], "날짜별 원본18개 판정 플래그"))
    for day in calendar:
        age_shift = 1 if lichun and day["day"] < lichun else 0
        matches = None if luck is None else [any(row["luckDay"] == day["day_pillar"][1] and row["male" if gender == 0 else "female"] == (age - age_shift) % 8 for row in luck) for age, gender in zip(ages, genders)]
        row = flags.get(day["day"]) if flags is not None else None
        day.update(before_lichun_age_shift=age_shift, role_daegil=matches,
                   original_scoring=score_day(row, all(matches)) if row is not None and matches is not None else None)
    facts = {"mode": mode, "year": year, "month": month, "age_year": age_year, "source_ages": ages,
             "source_age_mod8": [age % 8 for age in ages], "source_age_mod9": [age % 9 for age in ages],
             "lichun_day": lichun, "monthly_calendar": calendar,
             "calendar_adapter": "허용된 교정 tb_manse 기본 음력생년·일진·입춘; 추가 판정플래그는 대체하지 않음"}
    if marriage:
        facts["month_guidance"] = _month_guidance(request, month)
    else:
        single = genders[0] if mode == "single" else None
        facts["direction_results"] = _directions(source.get("locations"), ages, single)
        where = {"luck": 0, **({"gender": single} if single is not None else {})}
        direction_columns = [f"age_{age % 9}" for age in ages]
        selectors.append(_data_selector("directions", "tbLocation", where, ["gender", *direction_columns, "content", "cont_idx"], "나이mod9별 원본 방위; couple은 gender순 첫4행/뒤4행 비교"))
    return facts, selectors, ["chosenday/tbLuckDay의 원본 판정행이 미확보입니다. 입력한 행은 조사용이며 결과가 계산되어도 실제 원본 데이터 인증이나 AI 해석 허용으로 바뀌지 않습니다."] + ([] if marriage else ["tbLocation의 실제 나이별 방위·분류 행이 미확보입니다."])


def _mindluck(request):
    mental_id = _integer(request.parameters.get("mental_id"), 1, 2_147_483_647)
    selected = request.parameters.get("answer_index")
    if selected is not None:
        _integer(selected, 0, 3)
    source = _source_rows(request, {"questions", "members", "results"})
    questions = _rows(source.get("questions"), ("content_num",), limit=100)
    members = _rows(source.get("members"), ("content_num", "member_num"), ("jump_position",), limit=11)
    results = _rows(source.get("results"), ("result_num",), ("start_point", "end_point"), limit=11)
    for rows in (questions, members, results):
        for row in rows or []:
            for key, value in row.items():
                _integer(value, -2_147_483_648 if key in {"jump_position", "start_point", "end_point"} else 0, 2_147_483_647)
    content = questions[0]["content_num"] if questions else None  # SQL has no ORDER BY: first recordset row.
    choices = sorted((row for row in members or [] if row["content_num"] == content), key=lambda row: row["member_num"])
    outcomes = sorted(results or [], key=lambda row: row["result_num"])
    result_id = outcomes[selected]["result_num"] if selected is not None and selected < len(choices) and selected < len(outcomes) else None
    facts = {"mental_id": mental_id, "selected_index": selected, "first_recordset_content_num": content,
             "visible_member_numbers": [row["member_num"] for row in choices[:4]],
             "selected_result_num": result_id, "jump_position_used": False, "score_range_used": False,
             "source_max_visible_choices": 4, "source_selection_rule": "ORDER BY member_num 인덱스와 ORDER BY result_num의 같은 인덱스"}
    selectors = [_data_selector("question-structure", "mental_content", {"mental_id": mental_id}, ["content_num"], "원본 첫 recordset 질문 구조"),
                 _data_selector("choice-structure", "mental_member", {"mental_id": mental_id, "content_num": content}, ["member_num", "jump_position"], "member_num순 선택지 구조"),
                 _data_selector("result-structure", "mental_result", {"mental_id": mental_id}, ["result_num", "start_point", "end_point"], "result_num순 결과 구조"),
                 _selector("result", "mental_result", {"mental_id": mental_id, "result_num": result_id}, ["result"], "선택지와 같은 순서의 원본 결과 문장")]
    return facts, selectors, ["원본 문항·선택지·결과 행의 수와 정렬 대응이 미확보입니다. jump_position/점수구간은 현재 활성 화면에서 미사용이며 새로운 채점·질문 전이를 만들지 않습니다."]


def decide(service_id, request, saju=None, partner=None):
    if service_id not in SERVICES:
        raise DomainError("unsupported_service", "이 모듈에 없는 원본 DB 규칙 서비스입니다.")
    metadata = SERVICES[service_id]
    if set(request.parameters) - set(metadata["parameter_help"]):
        _invalid("이 서비스에서 지원하지 않는 parameters 항목이 있습니다.")
    if metadata["requires_birth"] and request.birth is None:
        raise DomainError("missing_birth", "이 서비스에는 birth가 필요합니다.")
    if service_id == "calendarluck":
        facts, selectors, unresolved = _calendarluck(request)
    elif service_id == "mindluck":
        facts, selectors, unresolved = _mindluck(request)
    else:
        facts, selectors, unresolved = _chosen_service(service_id, request)
    return {"source": metadata["source"], "facts": facts, "selectors": selectors, "unresolved": unresolved}

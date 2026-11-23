"""CR-012/T-024: remaining interlife arithmetic, with actual missing facts blocked.

Optional source_fields are typed investigation inputs, not trusted DB records.
They never make a partial service ready or bypass the required original data.
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime
from pathlib import Path
from secrets import randbelow
from types import SimpleNamespace

from app.calendar import solar_birth
from app.errors import DomainError
from app.ported_interlife import KST, ROOT, _hexagrams, _lucky_number, _selector, _zodiac
from app.ported_interlife import SERVICES as INTERLIFE_SERVICES
from app.rules import BRANCHES, STEMS

TABLES = json.loads((Path(__file__).with_name("data") / "interlife_dependency_tables.json").read_text(encoding="utf-8"))
SOURCE_HELP = "선택: 원본에서 검증한 코드 필드만 입력하는 조사용 객체. DB 자료로 인증되지 않으며 입력해도 최종 AI 차단은 유지합니다."


def _spec(name, leaf, parameters=None, *, birth=False):
    return {"name": name, "original_name": name, "requires_birth": birth,
            "requires_partner": False, "uses_saju": False, "ready": False,
            "example_parameters": parameters or {}, "parameter_help": {},
            "source": ROOT + leaf,
            "source_limits": ["원본에 있는 산술·선택·추첨은 계산하되 미확보 판정 자료나 미검증 달력 바인딩을 AI가 채우지 않습니다."]}


SERVICES = {
    "interlife-free-4": _spec("주민번호un", "unse/free/free_4.asp:77-80"),
    "interlife-free-8": _spec("바이오리듬", "solve/F/F024.asp:19-178", birth=True),
    "interlife-theme-2": _spec("타로점성술", "unse/theme/theme_2.asp:8-57,111-155"),
    "interlife-theme-3": _spec("신통방통 동전점", "unse/theme/theme_3.asp:8-57,111-135"),
    "interlife-theme-4": _spec("탄생석점", "unse/theme/theme_4.asp:25,77-95", birth=True),
    "interlife-jum-2": _spec("주역점", "unse/jum/jum_2.asp:8-57,111-142"),
    "interlife-yukim-1": _spec("육임정단", "solve/J/J045.asp:37-48,149-347,530-717,900-920", {"what": "01"}),
}
for service, spec in SERVICES.items():
    if service != "interlife-free-4":
        spec["parameter_help"]["server_time"] = "선택: 원본 Now/Date를 재현할 ISO 날짜시각. 기본은 한국시간 현재이며 target_date나 birth로 서버 시각을 바꾸지 않습니다."
    if service in {"interlife-theme-2", "interlife-theme-3", "interlife-theme-4", "interlife-jum-2", "interlife-yukim-1"}:
        spec["parameter_help"]["source_fields"] = SOURCE_HELP
    if service.startswith("interlife-theme-"):
        spec["parameter_help"]["tele_cookie"] = "선택: 이전 F019 4자리 숫자(가상 예:1234). 원문을 반환하지 않으며 전화번호 전체는 받지 않습니다."
SERVICES["interlife-free-8"]["parameter_help"]["day_numbers"] = "선택: 원본 LunarToSolar의 정수 from_num/see_num/to_num 세 값. 원본과 대조되지 않은 입력은 조사용이며 자동 승인되지 않습니다."
SERVICES["interlife-theme-2"]["parameter_help"]["intSuja_cookie"] = "선택: 이전 타로 카드 1~21. 생략하면 원본과 같은 1~21 범위에서 추첨합니다."
SERVICES["interlife-theme-3"]["parameter_help"].update({
    "coins": "선택: 새 a/b/c/d 동전 선택 정수 1/2 네 개. 이전 쿠키보다 우선합니다.",
    "intSuja_num": "선택: 이전 네 동전 쿠키, 예:1212. coins가 없을 때 사용합니다.",
})
SERVICES["interlife-jum-2"]["parameter_help"].update({
    key: value for key, value in INTERLIFE_SERVICES["interlife-jum-16"]["parameter_help"].items() if key != "source_request_date"
})
SERVICES["interlife-yukim-1"]["parameter_help"]["what"] = "원본 질문 코드 01~16. 사업/취직/이혼/가출/질병/구재/주식/시험/임신/대인/도난/길흉/소송/매매/이동/혼인 순서입니다."
for service, fields in {
    "interlife-free-4": ["T046 mm/yy/dd 전역 상태와 오류 후 unmyung 값의 실제 ASP 실행 근거"],
    "interlife-free-8": ["LunarToSolar.solar_date→num 원본 값과 num의 연속 일수 정의"],
    "interlife-theme-2": ["F019.DB_express/DB_express_1 실제 길흉 분류", "T043.DB_title 실제 카드명", "S009.DB_data 실제 성씨", "mansedata year_e/month_e 및 f_Saju/용신 코드 매핑"],
    "interlife-theme-3": ["F019.DB_express/DB_express_1 실제 길흉 분류", "mansedata.year_e 원본 년지 의미"],
    "interlife-theme-4": ["F019.DB_express/DB_express_1 실제 길흉 분류", "mansedata.year_e 원본 년지 의미"],
    "interlife-jum-2": ["J033.DB_title 실제 괘명·도식", "S008.DB_data 실제 행운색상", "S002/S005/S006/S007/S008.DB_numerical 실제 점수", "원본 f_Saju·서버 년월일 코드 매핑"],
    "interlife-yukim-1": ["mansedata.woljang 날짜별 월장", "mansedata.day_h 원본 일간"],
}.items():
    SERVICES[service]["required_source_fields"] = fields


def _clock(parameters):
    value = parameters.get("server_time")
    if value is None:
        return datetime.now(KST).replace(tzinfo=None)
    if not isinstance(value, str):
        raise DomainError("invalid_service_parameters", "server_time은 ISO 날짜시각 문자열이어야 합니다.")
    try:
        parsed = datetime.fromisoformat(value)
        if "T" not in value or not 1901 <= parsed.year <= 2050:
            raise ValueError
        return parsed.astimezone(KST).replace(tzinfo=None) if parsed.tzinfo else parsed
    except ValueError as exc:
        raise DomainError("invalid_service_parameters", "server_time의 날짜시각을 확인하세요.") from exc


def _fields(parameters):
    fields = parameters.get("source_fields", {})
    ranges = {"Xyeargan": (1, 10), "Xyeargi": (1, 12), "Xdaygan": (1, 10),
              "todaygan": (1, 10), "todaygi": (1, 12), "Tmonth": (1, 12), "yong_code": (0, 5)}
    symbols = {"my_year_e": BRANCHES, "my_year_h_org": "ABCDEFGHIJ",
               "my_year_e_org": tuple(f"{i:02d}" for i in range(1, 13)),
               "my_month_e_org": tuple(f"{i:02d}" for i in range(1, 13)),
               "woljang": BRANCHES, "lday_h": STEMS}
    if not isinstance(fields, dict) or set(fields) - set(ranges) - set(symbols):
        raise DomainError("invalid_service_parameters", "source_fields에 허용된 원본 코드만 입력하세요.")
    for key, value in fields.items():
        valid = (type(value) is int and ranges[key][0] <= value <= ranges[key][1]) if key in ranges else (
            isinstance(value, str) and value in symbols[key]
            and (not isinstance(symbols[key], str) or len(value) == 1)
        )
        if not valid:
            raise DomainError("invalid_service_parameters", "source_fields의 원본 코드 범위를 확인하세요.")
    return fields


def _row(identifier, table, key, columns, purpose, *, field="DB_express", numeric=False):
    result = _selector(identifier, table, {field: key}, columns, purpose)
    if key is None:
        result["key_unresolved"] = True
    if numeric:
        result.update(narrative=False, role="calculation")
    return result


def _source_key(fields, table, q):
    if q is None or "Xyeargi" not in fields:
        return None
    value = (q + fields["Xyeargi"]) % (10 if table == "S008" else 12)
    return str(value or 1)


def _season_key(fields):
    if not {"my_year_h_org", "my_year_e_org", "my_month_e_org"} <= fields.keys():
        return None
    code = fields["my_year_h_org"] + fields["my_year_e_org"] + fields["my_month_e_org"]
    result = None
    for group in TABLES["s058_ordered_groups"]:
        if code in group["codes"]:
            result = group["result"]
    return "01" if result in {"11", "12"} else result


def _animal(solar):
    year_code = solar.year % 100
    if year_code < 48:
        year_code += 48
    if year_code > 92:
        year_code -= 51
    column = (year_code - 2) % 9
    # The source fills tabb(1..9), but reads yun1=0..8. Empty index0 coerces to 0.
    base = TABLES["janimal_months"][solar.month - 1][column - 1] if column else 0
    number = (base + solar.day) % 60
    return {"year_code": year_code, "table_column": column, "source_empty_column_zero": column == 0,
            "animal_code": number, "keyword": TABLES["janimal_animals"].get(str(number))}


def _bio(request, clock):
    numbers = request.parameters.get("day_numbers")
    facts = {"source_birth_calendar_action": "원본 request 연월일을 변환 없이 solar_date 조회키로 사용",
             "day_numbers": None, "original_total_days": None, "original_ment_num": None,
             "calendar_ordinal_used_as_original_num": False,
             "source_february_graph_days": 28}
    unresolved = ["LunarToSolar.num 원본 세 조회값과 연속 일수 의미가 미확보입니다. 날짜 ordinal 또는 tb_manse.idx를 원본 num으로 대체하지 않습니다."]
    key = None
    if numbers is not None:
        if not isinstance(numbers, dict) or set(numbers) != {"from_num", "see_num", "to_num"} or any(type(v) is not int or abs(v) > 2_000_000_000 for v in numbers.values()):
            raise DomainError("invalid_service_parameters", "day_numbers에는 from_num/see_num/to_num 정수 세 값만 입력하세요.")
        elapsed = numbers["see_num"] - numbers["from_num"]
        phases = []
        for period, danger in ((23, 12), (28, 14), (33, 17)):
            remainder = elapsed % period if elapsed >= 0 else -((-elapsed) % period)
            phases.append(1 if remainder in {0, danger} else 2 if 0 < remainder < danger else 3 if danger < remainder < period else None)
        key = str((phases[0] - 1) * 9 + (phases[1] - 1) * 3 + phases[2]) if all(phases) else None
        facts.update(source_day_numbers_supplied=True, original_total_days=elapsed, original_total_life_days=numbers["to_num"] - numbers["from_num"],
                     original_phase_classes=phases, original_ment_num=key,
                     source_scores={name: [math.floor(math.sin((elapsed + offset) / period * 2 * math.pi) * 100) for offset in (-1, 0, 1)]
                                    for name, period in (("physical", 23), ("emotion", 28), ("mental", 33))})
        graph_days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[clock.month - 1]
        facts["source_monthly_graph"] = {
            name: [math.floor(math.sin((elapsed + day - clock.day) / period * 2 * math.pi) * 100)
                   for day in range(1, graph_days + 1)]
            for name, period in (("physical", 23), ("emotion", 28), ("mental", 33))
        }
        unresolved = ["입력된 day_numbers의 원본 LunarToSolar.num 일치 여부가 검증되지 않았습니다. 조사용 계산 결과이며 AI 최종 해석은 차단합니다."]
    else:
        try:
            raw = date(request.birth.year, request.birth.month, request.birth.day)
            facts["independent_calendar_day_difference"] = (clock.date() - raw).days
        except ValueError:
            facts["independent_calendar_day_difference"] = None
    return facts, [_row("biorhythm", "F024", key, ["DB_data"], "원본 세 주기 27구간 해설", field="DB_express")], unresolved


def _year_selector(fields):
    branch = fields.get("my_year_e")
    return _row("year-animal", "S040", str(BRANCHES.index(branch) + 1) if branch else None, ["DB_data"], "원본 년지별 설명")


def _f019(parameters, sex):
    return _lucky_number({"sex": sex, "tele_cookie": parameters.get("tele_cookie")})


def _yukim(parameters, clock, fields):
    what = parameters.get("what", "01")
    if not isinstance(what, str) or what not in {f"{i:02d}" for i in range(1, 17)}:
        raise DomainError("invalid_service_parameters", "what은 원본 01~16 코드여야 합니다.")
    # Original Hour(Now)&Minute(Now) has no zero padding. String comparisons
    # are retained, including source 01:05 -> '15' -> 未 rather than 丑.
    hhmm = str(clock.hour) + str(clock.minute)
    branch = "子" if hhmm < "0131" or hhmm >= "2331" else None
    for index in range(1, 12):
        if f"{index * 2 - 1:02d}31" <= hhmm < f"{index * 2 + 1:02d}31":
            branch = BRANCHES[index]
    visit = randbelow(238722) % 12
    adjusted = TABLES["j045_jumc_transforms"][branch][visit] if branch else None
    woljang = fields.get("woljang")
    target = BRANCHES[(BRANCHES.index(woljang) + 6 - BRANCHES.index(adjusted)) % 12] if woljang and adjusted else None
    selector = _selector("yukim", "J045", {"DB_express_1": target, "DB_express": fields.get("lday_h")}, [f"DB_data_{int(what)}"], "원본 질문별 육임 설명")
    if target is None or fields.get("lday_h") is None:
        selector["key_unresolved"] = True
    return {"what": what, "original_unpadded_hhmm": hhmm, "time_branch": branch, "visit_na": visit,
            "visit_draw_range_before_mod": [0, 238721], "adjusted_time_branch": adjusted,
            "source_woljang": woljang, "chenban_05": target}, [selector], ["mansedata.woljang 원본 날짜별 월장과 일간 값의 검증 자료가 필요합니다. 입력 조사값만으로 원본 판정이 검증되지는 않습니다."]


def decide(service_id, request, saju=None, partner=None):
    if service_id not in SERVICES:
        raise DomainError("unsupported_service", "이 모듈에 없는 interlife 서비스입니다.")
    spec, parameters = SERVICES[service_id], request.parameters
    if set(parameters) - set(spec["parameter_help"]):
        raise DomainError("invalid_service_parameters", "지원하지 않는 interlife parameters 항목이 있습니다.")
    if spec["requires_birth"] and request.birth is None:
        raise DomainError("birth_required", "이 서비스에는 birth가 필요합니다.")
    facts, selectors, unresolved = {"source_profile": "interlife-source-dependency-partial-v1"}, [], []
    if service_id == "interlife-free-4":
        facts.update(source_globals={"yy": "Empty outside b_saju_Click local scope", "mm": "Empty outside b_saju_Click local scope", "dd": list("庚辛壬癸甲乙丙丁戊己庚辛")},
                     failed_sum="global dd is an array; mm+yy+dd is not numeric", original_selector_key=None,
                     post_error_empty_unmyung_fallback_candidate=10, resident_number_read_by_leaf=False)
        selectors = [_row("resident-number", "T046", None, ["DB_data"], "미검증 원본 오류 처리 후 선택키")]
        unresolved = ["원본 T046은 주민번호를 읽지 않고 mm+yy+dd를 합산합니다. yy/mm은 함수 로컬이고 전역 dd는 천간 배열로 덮입니다. On Error Resume Next 이후 unmyung의 Empty/기존값 상태에 따른 10 보정 결과를 실제 ASP와 대조해야 하며 생일 합으로 고치지 않습니다."]
    else:
        clock = _clock(parameters)
        facts["source_server_time"] = clock.isoformat()
        fields = _fields(parameters)
        if service_id == "interlife-free-8":
            values, selectors, unresolved = _bio(request, clock)
            facts.update(values)
        elif service_id == "interlife-yukim-1":
            values, selectors, unresolved = _yukim(parameters, clock, fields)
            facts.update(values)
        elif service_id == "interlife-jum-2":
            values, selectors, unresolved = _hexagrams(SimpleNamespace(birth=clock, parameters={key: parameters[key] for key in ("rd", "sticks", "sticks_z", "sticks_zz") if key in parameters}), with_birth_number=False)
            facts.update(values, birth_input_ignored=True, source_Xtodaygan_and_Xtodaygi="unassigned Empty -> numeric 0")
            day, year = fields.get("Xdaygan"), fields.get("Xyeargi")
            color_p = day % 10 or 10 if day is not None else None
            place_p = day % 12 or 12 if day is not None else None
            todaygan, todaygi = fields.get("todaygan"), fields.get("todaygi")
            life = TABLES["towoonsung"][todaygan - 1][todaygi - 1] if todaygan and todaygi else None
            sv = 14 - fields["Xyeargan"] if "Xyeargan" in fields else None
            if sv is not None and sv > 12:
                sv -= 12
            dang = (sv + fields["Tmonth"] - 1) % 12 if sv is not None and "Tmonth" in fields else None
            facts.update(available_source_life_stage_code=life, available_source_dang12=dang, source_year_branch_code=year)
            for table, q in (("S008", color_p), ("S007", None), ("S006", life), ("S005", life), ("S002", life)):
                key = str(dang or 1) if table == "S007" and dang is not None else _source_key(fields, table, q)
                selectors.append(_row(table, table, key, ["DB_data"], "원본 현재 un 설명", field="DB_express" if table == "S007" else "DB_num"))
                if table == "S008":
                    selectors[-1].update(narrative=False, role="calculation", purpose="원본 실제 행운색상")
                selectors.append(_row(table + "-score", table, key, ["DB_numerical"], "원본 실제 판정 점수", field="DB_express" if table == "S007" else "DB_num", numeric=True))
            facts["unused_place_expression"] = place_p
            unresolved += ["S007→F_dang4_6_db와 S008/S006/S005/S002→F_woonday의 실제 DB_numerical 값이 미확보이며 source 사주/서버 월·일 코드의 원본 의미도 검증해야 합니다."]
        else:
            forced_male = service_id in {"interlife-theme-2", "interlife-theme-3"}
            sex = "남" if forced_male or request.birth.gender == "male" else "여"
            facts["original_forced_server_male_profile"] = forced_male
            if service_id == "interlife-theme-2":
                card = parameters.get("intSuja_cookie")
                if card is None:
                    card = randbelow(21) + 1
                if type(card) is not int or not 1 <= card <= 21:
                    raise DomainError("invalid_service_parameters", "intSuja_cookie는 1~21 정수여야 합니다.")
                under, over = randbelow(8) + 1, randbelow(8) + 1
                lucky = (clock.year + clock.month + clock.day + clock.hour + clock.minute) % 5 or 1
                zodiac, serial = _zodiac(clock.month, clock.day)
                graph = randbelow(2) + 7
                facts.update(tarot_card=card, trigrams={"under": under, "over": over}, raw_server_datetime_sum_mod5=lucky,
                             source_zodiac=zodiac, original_unassigned_T039_graph_draw=graph, birth_input_ignored=True)
                selectors = [_row("tarot", "T043", str(card), ["DB_data"], "원본 타로 카드 설명"), _year_selector(fields),
                             _row("number", "T028", str(lucky), ["DB_data"], "원본 숫자 설명", field="DB_num"),
                             _row("surname", "S009", None, ["DB_data"], "원본 용신/오늘 일간 성씨 설명", field="DB_num"),
                             _row("trigrams", "J009", str(over) + str(under), ["DB_data"], "원본 상하괘 설명"),
                             _row("place", "S010", _source_key(fields, "S010", fields.get("Xdaygan")), ["DB_data"], "원본 장소 설명", field="DB_num"),
                             _row("zodiac-number", "T039", str(serial), ["DB_data"], "원본 별자리 숫자 설명"),
                             _row("season", "S058", _season_key(fields), ["DB_title", "DB_data"], "원본 계절 분기 설명")]
                selectors[3].update(narrative=False, role="calculation", purpose="원본 실제 성씨")
                if {"todaygan", "yong_code"} <= fields.keys():
                    p = fields["yong_code"] or 1
                    selectors[3]["where"]["DB_num"] = _source_key(fields, "S009", int(str(p) + str((fields["todaygan"] + 1) // 2)))
                    if selectors[3]["where"]["DB_num"] is not None:
                        selectors[3].pop("key_unresolved", None)
                selectors.append(_row("tarot-name", "T043", str(card), ["DB_title"], "원본 실제 카드명", numeric=True))
                unresolved.append("T043의 실제 카드명과 S009의 실제 성씨 자료가 미확보입니다. AI가 사실 이름을 임의로 붙이지 않습니다.")
            elif service_id == "interlife-theme-3":
                coins = parameters.get("coins")
                cookie = parameters.get("intSuja_num")
                if coins is None and cookie is not None:
                    if not isinstance(cookie, str) or len(cookie) != 4 or any(char not in "12" for char in cookie):
                        raise DomainError("invalid_service_parameters", "intSuja_num은 1/2로 된 네 자리 문자열이어야 합니다.")
                    coins = [int(char) for char in cookie]
                if coins is None:
                    coins = [randbelow(2) + 1 for _ in range(4)]
                if not isinstance(coins, list) or len(coins) != 4 or any(type(value) is not int or value not in {1, 2} for value in coins):
                    raise DomainError("invalid_service_parameters", "coins는 1/2 정수 네 개 배열이어야 합니다.")
                first, second = randbelow(8) + 1, randbelow(8) + 1
                facts.update(coin_key="".join(map(str, coins)), independent_draws={"J047": first, "J048": second}, birth_input_ignored=True)
                selectors = [_row("coins", "T048", facts["coin_key"], ["DB_data"], "원본 네 동전 설명"), _year_selector(fields),
                             _row("coin-first", "J047", str(first), ["DB_data"], "원본 첫 독립 추첨", field="DB_num"),
                             _row("coin-second", "J048", str(second), ["DB_data"], "원본 두 번째 독립 추첨", field="DB_num")]
            else:
                animal = _animal(solar_birth(request.birth))
                facts.update(animal=animal, original_input_month=request.birth.month)
                selectors = [_row("birth-month", "T052", str(request.birth.month), ["DB_data"], "원본 입력 월별 설명"), _year_selector(fields),
                             _selector("animal-keyword", "T013", {"DB_express": {"operator": "sql_like", "pattern": "%" + (animal["keyword"] or "") + "%"}}, ["DB_data"], "원본 동물 키워드 일치 설명")]
                if animal["keyword"] is None:
                    unresolved.append("Janimal의 relt=0에는 원본 동물 항목이 없어 빈 검색어로 첫 행을 조회합니다. 원본 결과 행/정렬을 확보해야 합니다.")
            values, f019, missing = _f019(parameters, sex)
            facts["f019"] = values
            unresolved += missing
            selectors += f019
            unresolved.append("원본 mansedata 년지/월지와 f_Saju·서버 일간의 코드 바인딩을 검증해야 하며 조사용 source_fields는 원본 DB 검증을 대체하지 않습니다.")
    return {"source": spec["source"], "facts": facts, "selectors": selectors, "unresolved": unresolved}

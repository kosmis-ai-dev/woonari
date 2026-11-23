"""CR-012 / T-024: direct ASP selection rules, without its narrative databases."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from app.calendar import ganji_from_row, solar_birth
from app.errors import DomainError
from app.legacy_life_wealth import sipkyuk
from app.manse_store import ManseDataError, get_manse_store
from app.models import SajuResult
from app.rules import GANJI, ten_god

if TYPE_CHECKING:
    from app.service_models import ServiceRequest


def _spec(name, *, birth=False, saju=False, parameters=None, help=None, ready=True):
    return {
        "name": name.replace("운세", "un"), "original_name": name,
        "requires_birth": birth, "requires_partner": False, "uses_saju": saju,
        "example_parameters": parameters or {}, "parameter_help": help or {}, "ready": ready,
    }


SERVICES = {
    "analysisluck": _spec("연인 심리분석", birth=True),
    "businessluck": _spec("비즈니스 성공운", birth=True),
    "birthluck": _spec("탄생일운세", birth=True, ready=False),
    "bloodluck": _spec("혈액형운세", parameters={"gender": "남", "blood": "AB"}, help={
        "gender": "남/여. 생략하면 원본 기본값 남", "blood": "A/B/AB/O. 생략하면 원본 기본값 AB",
    }),
    "carluck": _spec("차량번호운세", birth=True, saju=True, parameters={"mycar1": "1234"}, help={
        "mycar1": "차량번호의 숫자 4자리. 입력 원문은 응답과 AI에 보내지 않습니다.",
    }),
    "hpluck": _spec("휴대폰운세", birth=True, saju=True,
                    parameters={"myHp1": "010", "myHp2": "0000", "myHp3": "0000"}, help={
        "myHp1/myHp2/myHp3": "전화번호의 숫자 3구간. 각 구간 정수의 합으로 계산하며 원문은 반환하지 않습니다.",
    }),
    "juminluck": _spec("주민번호운세", parameters={"myJumin1": "000000", "myJumin2": "0000000"},
                      help={"myJumin1/myJumin2": "앞 6자리/뒤 7자리. 예시는 가짜 값이며 계산 후 원문을 응답·AI에 보내지 않습니다."}),
    "jusoluck": _spec("주소지운세", birth=True, saju=True,
                      parameters={"zipcode": "000000", "addr": "테스트12길3", "addr2": "4층5호"},
                      help={"zipcode": "원본 규칙의 6자리 우편번호. 현행 5자리로 자동 대체하지 않습니다.",
                            "addr/addr2": "주소의 연속 숫자 구간만 계산합니다. 입력 원문은 반환하지 않습니다."}),
    "preluck": _spec("도통 전생록", birth=True),
    "correctyouluck": _spec("나와 맞는 이성 궁합", birth=True),
    "flowerluck": _spec("탄생화운세", birth=True, ready=False),
    "jewelryluck": _spec("탄생석운세", birth=True, ready=False),
    "coinluck": _spec("주역점", ready=False, parameters={
        "bt": "money", **{f"yut{i}": str(i % 2) for i in range(6)},
    }, help={"bt": "money/business/exam/love/home", "yut0~yut5": "각각 0 또는 1. 원본의 동전 6번 결과 순서입니다."}),
    "starluck": _spec("별자리운세", ready=False,
                      parameters={"gender": "남", "bloodtype": "AB", "startdate": "0121"}, help={
        "gender": "남/여", "bloodtype": "A/B/AB/O", "startdate": "원본 별자리 선택코드. 생일로 임의 재계산하지 않습니다.",
    }),
    "adultluck-starcoupleluck": _spec("별자리 속궁합",
                                     parameters={"gender": "남", "startdate": "0121"}, help={
        "gender": "남/여", "startdate": "원본 별자리 선택코드. 성인 대상 서비스입니다.",
    }),
    "hanjaluck": _spec("한자운세", birth=True, saju=True, ready=False),
    "adviceluck": _spec("나의 운세처방", birth=True, saju=True, ready=False),
}

STAR_CODES = ("0121", "0219", "0321", "0421", "0522", "0622", "0723", "0823", "0924", "1024", "1123", "1222")
STAR_NAMES = ("물병자리", "물고기자리", "양자리", "황소자리", "쌍둥이자리", "게자리", "사자자리", "처녀자리", "천칭자리", "전갈자리", "사수자리", "염소자리")
STAR_PLANETS = ("천왕성", "해왕성", "화성", "금성", "수성", "달", "태양", "수성", "금성", "명왕성", "목성", "토성")
STAR_STONES = ("에메랄드,옥", "오팔,에메랄드", "루비,토파스", "블루사파이어,터키석", "에메랄드,박옥", "오팔,마노", "루비,다이아몬드", "사파이어,제스피", "오팔,에메랄드", "황옥,오팔", "다이아몬드,루비", "터키석,사파이어")
STAR_NUMBERS = ("4", "7", "9", "6", "5", "2", "1", "5", "6", "0", "3", "8")
INVALID_PARAMETERS = "해당 서비스의 parameters 이름·형식·허용 범위를 확인하세요."


def _invalid():
    raise DomainError("invalid_service_parameters", INVALID_PARAMETERS)


def _parameters(request, allowed):
    values = request.parameters
    if not isinstance(values, dict) or set(values) - set(allowed):
        _invalid()
    return values


def _digits(values, key, minimum, maximum=None):
    value = values.get(key)
    maximum = minimum if maximum is None else maximum
    if not isinstance(value, str) or re.fullmatch(rf"[0-9]{{{minimum},{maximum}}}", value) is None:
        _invalid()
    return value


def _choice(values, key, choices, default=None):
    value = values.get(key, default)
    if value == "" and default is not None:
        value = default
    if not isinstance(value, str) or value not in choices:
        _invalid()
    return value


def _birth(request):
    if request.birth is None:
        raise DomainError("service_birth_required", "이 서비스에는 생년월일 입력이 필요합니다.")
    return request.birth


def _solar(request):
    return solar_birth(_birth(request))


def _raw_record(day):
    try:
        return get_manse_store().solar_record(day)
    except ManseDataError as error:
        raise DomainError("manse_unavailable", "만세력 DB를 사용할 수 없습니다.", 503) from error


def _saju(value):
    if value is None:
        raise DomainError("service_birth_required", "이 서비스에는 사주 계산 결과가 필요합니다.")
    return value


def _selector(ident, table, where, topics, *, calculation=False):
    result = {"id": ident, "table": table, "where": where, "columns": list(topics),
              "topics": topics, "purpose": "원본 문구 선택키 보존 후 AI 문장화"}
    if calculation:
        result.update(role="calculation", narrative=False, purpose="원본 분류·사실 자료 확인 필요")
    return result


def _result(service_id, facts, selectors, unresolved=()):
    directory = service_id.replace("adultluck-", "adultluck/")
    return {"source": f"old/unse/{directory}/main_end.asp", "facts": facts,
            "selectors": selectors, "unresolved": list(unresolved)}


def _number(service_id, request, saju):
    values = _parameters(request, {
        "carluck": {"mycar1"}, "hpluck": {"myHp1", "myHp2", "myHp3"},
        "jusoluck": {"zipcode", "addr", "addr2"},
    }[service_id])
    if service_id == "carluck":
        total = int(_digits(values, "mycar1", 4))
        kind, count = "carnum", 3
    elif service_id == "hpluck":
        total = sum(int(_digits(values, f"myHp{i}", 2 if i == 1 else 3, 4)) for i in (1, 2, 3))
        kind, count = "Hp", 6
    else:
        postal = _digits(values, "zipcode", 6)
        first, second = values.get("addr"), values.get("addr2")
        if not isinstance(first, str) or not isinstance(second, str) or not first.strip() or len(first) + len(second) > 1000:
            _invalid()
        chunks = re.findall(r"[0-9]+", first + second)
        numbers = [int(chunk) for chunk in chunks]
        # ASP CInt raises for an overflowing numeric group or accumulated sum.
        if any(number > 32767 for number in numbers) or sum(numbers) > 32767:
            _invalid()
        total = int(postal[:3]) + int(postal[3:]) + sum(numbers)
        kind, count = "juso", 4
    pillar = GANJI[(total - 1) % 60]
    day_master = _saju(saju).day_master
    code = sipkyuk(pillar[0], day_master)
    return _result(service_id, {
        "number_pillar": pillar, "day_master": day_master, "sipkyuk_code": code,
        "sipkyuk_ten_god": ten_god(day_master, pillar[0]),
        "input_privacy": "번호·주소 원문을 응답과 AI에 포함하지 않음",
    }, [_selector("number-reading", "tbSaju_otherunse", {"unse": kind, "sipkyuk_code": code},
                  {f"desc{i}": f"{SERVICES[service_id]['name']} {i}" for i in range(1, count + 1)})])


def _solar_month(service_id, request):
    _parameters(request, set())
    birthday = _solar(request)
    remainder = (birthday.year - 1900) % 12
    key = ((11 - remainder) + birthday.month) % 12
    if service_id == "analysisluck":
        social = ((11 - remainder) + birthday.month) % 144
        tables = (("love_mind", "생각 알아보기", key), ("love_lifestyle", "라이프 스타일", key),
                  ("love_social", "사교성", social), ("love_hobby", "취미와 기호", key))
    else:
        social = None
        tables = (("life_personality", "인격/성품", key), ("life_aptitude", "직무 적성", key),
                  ("life_advice", "인간관계 충고", key), ("life_basic", "사업전략의 기본", key))
    facts = {"year_cycle_remainder": remainder, "selection_number": key}
    if social is not None:
        facts.update(social_selection_number=social,
                     source_rule="social의 Mod144 식에도 원본 intMyDee(Mod12)를 사용")
    return _result(service_id, facts, [_selector(table, table, {"Num": number}, {"Content": topic})
                                     for table, topic, number in tables])


def _calendar_service(service_id, request):
    _parameters(request, set())
    birthday = _solar(request)
    where = {"month": birthday.month, "day": birthday.day}
    if service_id == "preluck":
        row = _raw_record(birthday.date())
        year_key = GANJI.index(ganji_from_row(row, "y")) + 1
        facts = {"raw_year_pillar_index_plus_one": year_key,
                 "lunar_month_key": row["l_mon"], "lunar_day_key": row["l_day"],
                 "year_rule": "시간 절입 보정 전 원본 일자 행의 year_pillar+1"}
        selectors = [
            _selector("past-year", "tbPreLife", {"div_flag": 1, "div_date": year_key}, {
                "content": "회원님의 전생은", "character": "전생 성품", "parent": "부모 인연", "child": "자녀 인연",
            }),
            _selector("past-month", "tbPreLife", {"div_flag": 2, "div_date": row["l_mon"]}, {"content": "생월 인연"}),
            _selector("past-day", "tbPreLife", {"div_flag": 3, "div_date": row["l_day"]}, {"content": "생일 인연"}),
        ]
        return _result(service_id, facts, selectors)
    if service_id == "birthluck":
        return _result(service_id, {"solar_month_day_key": where}, [
            _selector("birth-reading", "birthluck", where, {"unse": "탄생일 un"}),
            _selector("birth-events", "wiki_story", where,
                      {"e_name": "사건명", "e_contents": "사건 자료", "e_date": "사건 날짜"}, calculation=True),
            _selector("birth-people", "wiki_person", where,
                      {"e_year": "출생 연도", "e_name": "인물명", "e_contents": "인물 자료"}, calculation=True),
        ], ["wiki_story·wiki_person의 실제 사건·인물 자료가 없어 원본 전체 페이지는 미완성입니다."])
    if service_id == "flowerluck":
        return _result(service_id, {"solar_month_day_key": where}, [
            _selector("flower-facts", "flowerluck", where, {
                "name_h": "한글 꽃이름", "name_e": "영문 꽃이름", "fw_word": "꽃말",
                "fw_column": "식물 분류", "origin": "원산지",
            }, calculation=True),
            _selector("flower-reading", "flowerluck", where, {"story": "탄생화 이야기", "unse": "탄생화 un"}),
        ], ["원본 날짜별 꽃이름·꽃말·분류·원산지 자료가 없어 임의 배정하지 않습니다."])
    unresolved = ["stoneluck의 월별 보석이름·상징 자료가 없어 임의 배정하지 않습니다."]
    if request.birth.calendar == "lunar":
        unresolved.append("원본 탄생석 음력 분기는 lmyMonth/lmyDay가 미할당입니다. 양력 변환 후보만 진단하며 원본 동작 동일성을 확정하지 않습니다.")
    return _result(service_id, {"solar_month_candidate": birthday.month}, [
        _selector("stone-facts", "stoneluck", {"month": birthday.month}, {
            "stname_h": "한글 보석명", "stname_e": "영문 보석명", "symbol": "상징",
        }, calculation=True),
        _selector("stone-reading", "stoneluck", {"month": birthday.month}, {"unse": "탄생석 un"}),
    ], unresolved)


def _cabala(request):
    _parameters(request, set())
    birthday = _solar(request)
    number = sum(int(char) for char in birthday.strftime("%Y%m%d"))
    for _ in range(2):
        if number > 9:
            number = number // 10 + number % 10
    return _result("correctyouluck", {"birth_number": number, "active_mode": "cabala_harmony"}, [
        _selector(f"birth-number-{other}", "tbCabala_Content", {
            "menu": "cabala_harmony", "keyno": number * 10 + other,
        }, {"content1": f"탄생수 {other}와의 궁합", "content2": f"탄생수 {other}와의 교제법"})
        for other in range(1, 10)
    ])


def _stars(service_id, request):
    adult = service_id.startswith("adultluck-")
    allowed = {"gender", "startdate"} | (set() if adult else {"bloodtype"})
    values = _parameters(request, allowed)
    gender = _choice(values, "gender", ("남", "여"))
    start = _choice(values, "startdate", STAR_CODES)
    index = STAR_CODES.index(start)
    facts = {"zodiac_code": start, "zodiac_name": STAR_NAMES[index], "gender": gender}
    if adult:
        return _result(service_id, facts, [_selector("star-couple", "StarsexLuck", {
            "gender": gender, "day": start,
        }, {"title": "별자리 속궁합 제목", "contents": "별자리 성향", "sex": "별자리 속궁합"})])
    blood = _choice(values, "bloodtype", ("A", "B", "AB", "O"))
    where = {"gender": gender, "bloodtype": blood, "startdate": start}
    facts.update(bloodtype=blood, guardian_planet=STAR_PLANETS[index],
                 lucky_stones=STAR_STONES[index], lucky_number=STAR_NUMBERS[index])
    return _result(service_id, facts, [
        _selector("star-harmony", "tbStarLuck", where, {"harmony": "나와 찰떡궁합 혈액형"}, calculation=True),
        _selector("star-reading", "tbStarLuck", where, {
            "character": "성격", "relation": "대인관계", "working": "직업운",
            "money": "금전운", "love": "사랑운", "marriage": "결혼운",
        }),
    ], ["원본 harmony의 궁합 혈액형 분류가 DB에 있어 임의 분류하지 않습니다."])


def _advice(request, saju):
    _parameters(request, set())
    day = request.target_date
    lookup_day = day.replace(day=day.day + 10) if len(str(day.day)) < 2 else day
    row = _raw_record(lookup_day)
    day_master = _saju(saju).day_master
    year_index = GANJI.index(ganji_from_row(row, "y")) + int(row["l_year"] < day.year)
    month_pillar = ganji_from_row(row, "m")
    unresolved = ["원본 manse.disp_day 표시값이 제공 DB에 없어 월간 표시기간의 완전 동일성은 미확정입니다."]

    def recommendations(pillar):
        gods = (ten_god(day_master, pillar[0]), ten_god(day_master, pillar[1]))
        result = []
        for choices, ids in (({"정재", "편재"}, [1]), ({"정관", "편관"}, [2]),
                             ({"겁재"}, [23]), ({"상관"}, [23, 36])):
            if choices.intersection(gods):
                result.extend(ids)
        yang = dict(zip("甲乙丙丁戊己庚辛壬癸", "卯辰午未午未酉戌子丑"))
        bee = dict(zip("甲乙丙丁戊己庚辛壬癸", "酉戌子丑子丑卯辰午未"))
        if pillar[1] in (yang[day_master], bee[day_master]):
            result.append(25)
        return result

    if year_index > 59:
        year_pillar, year_ids = None, None
        unresolved.append("원본 year_pillar+1이 60이 되는 분기에 ganji 범위 보정이 없습니다.")
    else:
        year_pillar = GANJI[year_index]
        year_ids = recommendations(year_pillar)
    column = "female" if _birth(request).gender == "female" else "male"
    return _result("adviceluck", {
        "source_calendar_date": lookup_day.isoformat(), "day_shift_applied": lookup_day != day,
        "year_pillar": year_pillar, "month_pillar": month_pillar,
        "year_recommendation_ids": year_ids, "month_recommendation_ids": recommendations(month_pillar),
        "source_gender_comparison": "find_bujuk의 남자/여자 비교를 입력 남/여로 임의 정상화하지 않음",
    }, [_selector("advice-month", "fortune_basic", {"yukgap": month_pillar, "daygan": day_master},
                  {column: "이번 달 운세처방"})], unresolved)


def decide(service_id: str, request: ServiceRequest, saju: SajuResult | None,
           partner: SajuResult | None) -> dict:
    if service_id not in SERVICES:
        raise DomainError("service_not_found", "해당 직접 이식 서비스를 찾을 수 없습니다.", 404)
    if service_id in {"analysisluck", "businessluck"}:
        return _solar_month(service_id, request)
    if service_id in {"carluck", "hpluck", "jusoluck"}:
        return _number(service_id, request, saju)
    if service_id in {"birthluck", "preluck", "flowerluck", "jewelryluck"}:
        return _calendar_service(service_id, request)
    if service_id == "correctyouluck":
        return _cabala(request)
    if service_id in {"starluck", "adultluck-starcoupleluck"}:
        return _stars(service_id, request)
    if service_id == "adviceluck":
        return _advice(request, saju)
    if service_id == "bloodluck":
        values = _parameters(request, {"gender", "blood"})
        where = {"gender": _choice(values, "gender", ("남", "여"), "남"),
                 "blood": _choice(values, "blood", ("A", "B", "AB", "O"), "AB")}
        return _result(service_id, where, [_selector("blood-reading", "blood", where, dict(zip(
            (f"data{i}" for i in range(1, 8)), ("특징", "기본성격", "사회성", "인간성", "가치관", "감정", "업무성"),
        )))])
    if service_id == "juminluck":
        values = _parameters(request, {"myJumin1", "myJumin2"})
        total = sum(int(char) for char in _digits(values, "myJumin1", 6) + _digits(values, "myJumin2", 7))
        code = 3 if total > 60 else total
        return _result(service_id, {"selection_code": code}, [
            _selector("resident-reading", "tbSaju_jumin", {"code": str(code)}, {"desc1": "주민번호 un"}),
        ])
    if service_id == "coinluck":
        values = _parameters(request, {"bt", *(f"yut{i}" for i in range(6))})
        topic = _choice(values, "bt", ("money", "business", "exam", "love", "home"))
        code = "".join(_choice(values, f"yut{i}", ("0", "1")) for i in range(6))
        topics = dict(zip(("money", "business", "exam", "love", "home"),
                          ("금전·재물운", "실물·매매운", "학업·시험운", "이성·연애운", "가정·생활운")))
        return _result(service_id, {"line_code": code, "topic": topic}, [
            _selector("coin-name", "tbsaju_juyuk", {"code": code}, {"code_name": "64괘 이름"}, calculation=True),
            _selector("coin-reading", "tbsaju_juyuk", {"code": code}, {"total": "총평", topic: topics[topic]}),
        ], ["원본 6효 코드에 대응하는 64괘 이름 매핑이 DB에 있어 임의 괘명을 생성하지 않습니다."])
    _parameters(request, set())
    gender = _birth(request).gender
    return _result("hanjaluck", {
        "code_prefix": "M_01" if gender == "male" else "F_01",
        "target_year": request.target_date.year,
        "source_branch_number_bug": "pillarcall.asp fun_ji_num이 gan에 값을 쓰고 미할당 ji를 반환",
    }, [_selector("hanja-keyword", "hanja_luck", {"code": None}, {"keyword": "올해의 한자"}, calculation=True),
        _selector("hanja-reading", "hanja_luck", {"code": None}, {"content": "한자 un"})], [
        "원본 fun_ji_num의 미할당 반환값과 EndDay의 양력월말 사용을 검증해야 하므로 kwai 코드를 임의 확정하지 않습니다.",
        "hanja_luck 코드별 실제 한자 키워드 자료가 필요합니다.",
    ])

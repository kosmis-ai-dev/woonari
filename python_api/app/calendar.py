"""CR-010 / T-019: apply ASP CalcSaju rules to the supplied tb_manse rows."""

from datetime import date, datetime, time, timedelta, timezone
from typing import NoReturn

from app.errors import DomainError
from app.manse_store import ManseDataError, get_manse_store
from app.models import Birth, CalendarPolicy, Pillar, SajuResult
from app.rules import BRANCH_ELEMENTS, GANJI, HANGUL, STEM_ELEMENTS, life_stage, ten_god

KST = timezone(timedelta(hours=9))
MIN_DATE, MAX_DATE = date(1900, 1, 1), date(2050, 12, 31)


def check_range(value: date):
    if not MIN_DATE <= value <= MAX_DATE:
        raise DomainError("date_out_of_range", "지원 양력 범위는 1900-01-01 ~ 2050-12-31입니다.")


def _raise_store_error(exc: ManseDataError) -> NoReturn:
    code = exc.code
    messages = {
        "ambiguous_lunar_date": "검증된 교정표 적용 후에도 같은 음력·윤달 날짜가 중복되어 양력 날짜를 확정할 수 없습니다. 원본 데이터를 확인해 주세요.",
        "invalid_lunar_date": "제공된 만세력 DB에 해당 음력/윤달 날짜가 없습니다.",
        "date_not_found": "제공된 만세력 DB에 해당 양력 날짜가 없습니다.",
        "invalid_datetime": "만세력 절기 조회 시각을 확인해 주세요.",
        "manse_unavailable": "만세력 DB를 사용할 수 없습니다. 제공된 원본 데이터의 DB 구축 상태를 확인해 주세요."
    }
    status = 422 if code in {
        "ambiguous_lunar_date", "invalid_lunar_date", "date_not_found", "invalid_datetime"
    } else 503
    raise DomainError(code, messages.get(code, messages["manse_unavailable"]), status) from exc


def _solar_record(value: date) -> dict:
    check_range(value)
    try:
        return get_manse_store().solar_record(value)
    except ManseDataError as exc:
        _raise_store_error(exc)


def _birth_record(birth: Birth) -> tuple[datetime, dict]:
    if birth.calendar == "lunar":
        try:
            row = get_manse_store().lunar_record(
                birth.year, birth.month, birth.day, birth.leap_month
            )
        except ManseDataError as exc:
            _raise_store_error(exc)
        solar_date = date(row["s_year"], row["s_mon"], row["s_day"])
        check_range(solar_date)
    else:
        solar_date = date(birth.year, birth.month, birth.day)
        row = _solar_record(solar_date)
    value = datetime.combine(solar_date, time(birth.hour, birth.minute), tzinfo=KST)
    return value, row


def solar_birth(birth: Birth) -> datetime:
    """Resolve the supplied lunar/solar date through tb_manse, without fallback."""
    return _birth_record(birth)[0]


def ganji_from_row(row: dict, prefix: str) -> str:
    """Map zero-based gan/ji columns to the ASP's 甲子=0 sixty-pillar order."""
    gan, ji = int(row[f"{prefix}_gan"]), int(row[f"{prefix}_ji"])
    if not (0 <= gan < 10 and 0 <= ji < 12 and gan % 2 == ji % 2):
        raise DomainError("invalid_manse_record", "원본 만세력 행의 간지 인덱스를 확인해 주세요.", 503)
    return GANJI[(6 * gan - 5 * ji) % 60]


def day_ganji(value: date) -> str:
    # Do not cache by date: a deliberate DB reimport must be visible immediately.
    return ganji_from_row(_solar_record(value), "d")


def pillar(value: str, day_master: str) -> Pillar:
    stem, branch = value
    return Pillar(
        hanja=value,
        hangul="".join(HANGUL[x] for x in value),
        stem=stem,
        branch=branch,
        stem_element=STEM_ELEMENTS[stem],
        branch_element=BRANCH_ELEMENTS[branch],
        stem_ten_god=ten_god(day_master, stem),
        branch_ten_god=ten_god(day_master, branch),
        life_stage=life_stage(day_master, branch)
    )


def _year_month(row: dict, value: datetime) -> tuple[str, str]:
    year = GANJI.index(ganji_from_row(row, "y"))
    month = GANJI.index(ganji_from_row(row, "m"))
    division = int(row["div_name"])
    # A division-day row contains the pre-division pillars. ASP compares the
    # original hour/minute integers, including the supplied div_hour=24 value.
    if division % 2 and (value.hour, value.minute) >= (row["div_hour"], row["div_min"]):
        if division == 1:
            year = (year + 1) % 60
        month = (month + 1) % 60
    return GANJI[year], GANJI[month]


def period_pillars(value: datetime) -> dict[str, str]:
    """Use raw daily pillars and the source's minute-level year/month boundary."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=KST)
    else:
        value = value.astimezone(KST)
    row = _solar_record(value.date())
    year, month = _year_month(row, value)
    return {"year": year, "month": month, "day": ganji_from_row(row, "d")}


def _solar_term_window(value: datetime) -> dict:
    try:
        previous, following = get_manse_store().solar_terms(value)
    except ManseDataError as exc:
        _raise_store_error(exc)

    def event(item: dict | None) -> dict | None:
        if item is None:
            return None
        return {"name": item["name"], "at": item["at"]}

    return {"previous": event(previous), "next": event(following)}


def calculate_saju(birth: Birth, profile: str = "today_inline") -> SajuResult:
    if profile not in {"today_inline", "dotong"}:
        raise DomainError("invalid_calculation_profile", "알 수 없는 ASP 사주 계산 프로필입니다.")
    value, row = _birth_record(birth)
    year, month = _year_month(row, value)
    raw_day_index = GANJI.index(ganji_from_row(row, "d"))
    minutes = value.hour * 60 + value.minute
    slot = ((minutes + 30) // 120) % 12
    # Compute hour before the 00:30 day correction, exactly as both ASP profiles.
    hour_day_index = raw_day_index + int(profile == "dotong" and minutes >= 1410)
    hour_index = hour_day_index % 10 % 5 * 12 + slot
    day = GANJI[(raw_day_index - int(minutes < 30)) % 60]
    values = {"year": year, "month": month, "day": day, "hour": GANJI[hour_index]}
    pillars = {name: pillar(gz, day[0]) for name, gz in values.items()}
    elements = dict.fromkeys("목화토금수", 0)
    for p in pillars.values():
        elements[p.stem_element] += 1
        elements[p.branch_element] += 1
    gan, ji = "己壬丁甲辛戊癸丙乙庚", "寅卯辰巳午未申酉戌亥子丑"
    memno = "".join(
        f"{gan.index(values[k][0])}{ji.index(values[k][1]) + 1:02d}"
        for k in ("day", "month", "year")
    )
    return SajuResult(
        solar_birth=value.isoformat(),
        lunar_birth={
            "year": row["l_year"],
            "month": row["l_mon"],
            "day": row["l_day"],
            "leap_month": bool(row["leafMon_YN"])
        },
        pillars=pillars,
        day_master=day[0],
        elements=elements,
        legacy_memno=memno,
        solar_term_window=_solar_term_window(value),
        major_luck={
            "available": False,
            "method": "not-substituted",
            "reason": "운세별 ASP에 없는 공통 대운을 임의 계산하지 않습니다."
        },
        policy=CalendarPolicy(
            version="asp-manse-db-v4",
            lunar_correction_version="lunar-leap-flags-v1",
            data_backend=get_manse_store().backend,
            calculation_profile=profile,
            lunar_calendar="사용자 제공 dbo.tb_manse 음양력 조회 + lunar-leap-flags-v1 윤달 교정 10행",
            solar_terms="dbo.tb_manse div_name/div_hour/div_min; ASP 절입 분부터 적용",
            hour_boundary=(
                "dotong_function.asp: 23:30부터 다음날 일간으로 자시 계산"
                if profile == "dotong"
                else "today/week inline 및 dokebi.asp: 23:30에도 당일 일간으로 자시 계산"
            ),
            limitations=[
                "tb_manse 원본과 해시는 보존하며 승인된 윤달 표시 교정표 10행만 조회 시 적용함",
                "교정표의 출처·원본값 불일치 시 조회를 중단하고, 미해결 중복 음력키는 임의 선택하지 않음",
                "1945-06-06 절기번호 8 등 원본 데이터의 특이값을 그대로 보존함",
                "공개 API 양력 범위 1900~2050년; 원본 데이터는 1900~2100년 보존",
                "역사적 표준시/DST/출생지별 진태양시 추가 보정 미지원",
                "원본 ASP 서버의 실제 실행 결과 및 미확보 대운/DLL 판정은 미검증"
            ]
        )
    )

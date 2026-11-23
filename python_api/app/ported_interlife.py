"""CR-012 / T-024: verified interlife leaf inputs and text selectors.

The shared f_Saju preamble is not a replacement calendar profile.  These leaves
use only their actual output dependencies.  Dream result membership remains
unresolved; basic solar/lunar display uses the approved corrected tb_manse map.
"""

from datetime import date, datetime, timedelta, timezone
from secrets import randbelow

from app.calendar import _birth_record
from app.errors import DomainError
from app.models import SajuResult
from app.rules import BRANCHES
from app.service_models import ServiceRequest

ROOT = "old/unse/interlife/UNSE_DATA/"
KST = timezone(timedelta(hours=9))

# Literal radio values in faceface_1..12.asp; not read from ASP at runtime.
FACE_OPTIONS = {
    "face_style1": [
        "갑자형",
        "신자형",
        "전자형",
        "원자형",
        "유자형",
        "목자형",
        "역삼각형",
        "왕자형",
        "삼각형",
        "타원형"
    ],
    "face_style2": [
        "이마M자형",
        "이마둥근형",
        "이마네모형",
        "이마발애형",
        "이마참자형"
    ],
    "face_style3": [
        "이마폭적당",
        "이마폭넓음",
        "이마폭좁음"
    ],
    "face_style4": [
        "이마주름살한개",
        "이마주름살복잡",
        "이마주름살세개",
        "이마주름살기러기",
        "이마주름살활형",
        "이마주름살현침"
    ],
    "face_style5": [
        "눈썹반달형",
        "눈썹산형",
        "눈썹끝이솟은형",
        "눈썹끝이처진형",
        "눈썹일자형",
        "눈썹팔자형",
        "눈썹반갈형"
    ],
    "face_style6": [
        "눈썹길이적당",
        "눈썹길이길음",
        "눈썹길이짧음"
    ],
    "face_style7": [
        "눈썹털적당",
        "눈썹털많음",
        "눈썹털적음",
        "눈썹털끊김"
    ],
    "face_style7_1": [
        "미간사이넓음",
        "미간사이좁음",
        "미간사이적당"
    ],
    "face_style7_2": [
        "미간주름살한개",
        "미간주름살두개",
        "미간주름살세개",
        "미간주름살십자",
        "미간주름살없음"
    ],
    "face_style8": [
        "눈크기적당",
        "눈크기크다",
        "눈크기적다"
    ],
    "face_style9": [
        "눈모양튀어나옴",
        "눈모양움푹꺼짐",
        "눈모양적당"
    ],
    "face_style10": [
        "눈동자위치적당",
        "하부삼백안",
        "상부삼백안",
        "사백안"
    ],
    "face_style11": [
        "눈꼬리주름한개",
        "눈꼬리주름두개",
        "눈꼬리주름많음",
        "눈꼬리주름없음"
    ],
    "face_style12": [
        "눈꼬리적당",
        "눈꼬리올라감",
        "눈꼬리내려감"
    ],
    "face_style13": [
        "눈꺼풀적당",
        "윗눈꺼풀두꺼움",
        "아래눈꺼풀두꺼움",
        "위아래다두꺼움"
    ],
    "face_style14": [
        "귀출발눈썹",
        "귀출발눈썹눈꼬리중간",
        "귀출발눈꼬리"
    ],
    "face_style15": [
        "귀바퀴적당",
        "귀바퀴크다",
        "귀바퀴적다"
    ],
    "face_style16": [
        "귓볼살집적당",
        "귓볼살집많다",
        "귓볼살집적다"
    ],
    "face_style17": [
        "귀모양둥글다",
        "귀모양오똑섬",
        "귀모양옆으로누움",
        "귀모양길다"
    ],
    "face_style18": [
        "코길이적당",
        "코길이길다",
        "코길이짧다"
    ],
    "face_style19": [
        "콧대높이적당",
        "콧대높이높다",
        "콧대높이낮다"
    ],
    "face_style20": [
        "콧등이적당",
        "콧등이층계",
        "콧등중간이높다",
        "콧등이우로휨",
        "콧등이좌로휨",
        "매부리코"
    ],
    "face_style21": [
        "콧망울적당",
        "콧망울살찜",
        "콧망울여윔"
    ],
    "face_style22": [
        "콧구멍적당",
        "콧구멍크다",
        "콧구멍적다",
        "들창코",
        "좌우콧구멍다름"
    ],
    "face_style23": [
        "코끝부분보통",
        "코끝부분주름",
        "코끝부분붉음",
        "코끝부분점",
        "콧마루주름"
    ],
    "face_style24": [
        "광대뼈적당",
        "광대뼈앞으로돌출",
        "광대뼈옆으로돌출",
        "광대뼈앞옆돌출",
        "광대뼈함몰"
    ],
    "face_style25": [
        "법령넓다",
        "법령입으로들어감",
        "법령좌우길이다름",
        "법령이중",
        "법령끊어짐",
        "법령입에워삼",
        "법령상부수평",
        "법령에점",
        "법령이 없다"
    ],
    "face_style26": [
        "인중넓이적당",
        "인중넓이넓다",
        "인중넓이좁다"
    ],
    "face_style27": [
        "인중길이적당",
        "인중길이길다",
        "인중길이짧다"
    ],
    "face_style28": [
        "인중아래위가적당",
        "인중상부넓다",
        "인중하부넓다"
    ],
    "face_style29": [
        "코와입사이적당",
        "코와입사이넓다",
        "코와입사이좁다"
    ],
    "face_style30": [
        "인중모습이보통",
        "인중에가로주름",
        "인중에점흉터",
        "인중이희미함"
    ],
    "face_style31": [
        "입술크기적당",
        "입술크기크다",
        "입술크기적다"
    ],
    "face_style32": [
        "윗입술두께적당",
        "윗입술두께두껍다",
        "윗입술두께엷다"
    ],
    "face_style33": [
        "입의튀어나옴이적당",
        "윗입술이앞으로돌출",
        "아랫입술이앞으로돌출",
        "입이앞으로튀어나옴",
        "입이안으로들어갔다"
    ],
    "face_style34": [
        "입술끝이적당",
        "입술끝이내려감",
        "입술끝이올라감"
    ],
    "face_style36": [
        "아랫입술의주름적당",
        "아랫입술의주름많음",
        "아랫입술의주름없음"
    ],
    "face_style37": [
        "턱모양적당",
        "턱모양뾰족",
        "턱모양각형",
        "턱이짧다",
        "턱이길다",
        "턱이주걱턱",
        "턱이오목턱",
        "턱이두겹"
    ]
}
FACE_REQUIRED = (
    "face_style1", "face_style2", "face_style4", "face_style6", "face_style7_1",
    "face_style8", "face_style9", "face_style11", "face_style12", "face_style10",
    "face_style16", "face_style14", "face_style18", "face_style20", "face_style25",
    "face_style30", "face_style27", "face_style31", "face_style34", "face_style37",
    "face_style3"
)
FACE_EXAMPLE = {key: FACE_OPTIONS[key][0] for key in FACE_REQUIRED}


def _metadata(name: str, source: str, parameters: dict, help_text: dict, **flags) -> dict:
    return {
        "name": name,
        "requires_birth": False,
        "requires_partner": False,
        "uses_saju": False,
        "example_parameters": parameters,
        "parameter_help": help_text,
        "ready": True,
        "source": ROOT + source,
        **flags
    }


SERVICES = {
    "interlife-faceface": _metadata(
        "관상보기 (마의상법)",
        "unse/faceface/faceface_13.asp:21-123",
        {"sex": "남", "face": FACE_EXAMPLE},
        {
            "sex": "원본 성별 입력: 남 또는 여. 사진에서 성별을 추정하지 않습니다.",
            "face": "사용자가 직접 고른 원본 face_style 선택값 객체입니다. 예시의 필수 21항목을 입력하며 허용값은 face_options에서 확인합니다."
        },
        face_options=FACE_OPTIONS,
        required_face_parameters=list(FACE_REQUIRED),
        source_limits=["최종 faceface_13 결과에 실제 출력되는 19개 문구만 원본 순서로 선택합니다. 중간 설문 화면은 새 결과 서비스로 만들지 않습니다."]
    ),
    "interlife-free-1": _metadata(
        "오늘의 띠별un",
        "solve/F/F022.asp:4-178",
        {},
        {"server_date": "선택: 원본 Date()를 재현할 YYYY-MM-DD. 생략하면 한국시간 오늘입니다. 원본처럼 개인 띠 하나가 아닌 12띠 전체를 출력합니다."},
        source_limits=["이 leaf는 본인 생년월일·사주를 사용하지 않고 server Date()의 MMDD별 12띠 문구를 조회합니다."]
    ),
    "interlife-free-2": _metadata(
        "별자리un",
        "solve/setting_var.asp:10-45; " + ROOT + "solve/F/F013.asp:6-15",
        {},
        {"source_profile": "기본 asp_ui는 양력만 허용합니다. asp_original_unconverted를 명시하면 음력 입력의 월·일 숫자를 변환 없이 사용하던 원본 leaf를 재현합니다."},
        requires_birth=True,
        source_limits=["loveunse와 다른 원본 별자리 경계를 사용합니다. 원본은 solar_month가 아니라 request_month/day를 사용합니다."]
    ),
    "interlife-free-3": _metadata(
        "혈액형un",
        "solve/F/F033.asp:6-22",
        {"sex": "남", "blood": "A"},
        {
            "sex": "원본 성별: 남 또는 여. 남은 DB_data_m, 여는 DB_data_w입니다.",
            "blood": "혈액형 A/B/O/AB 또는 원본 blood_01/02/03/04입니다. 순서는 A/B/O/AB입니다."
        }
    ),
    "interlife-free-6": _metadata(
        "혈액형궁합",
        "solve/F/F034.asp:6-23",
        {"bloodm": "A", "bloodw": "B"},
        {
            "bloodm": "첫 번째 원본 남자 칸: A/B/O/AB 또는 bloodm_01/02/03/04.",
            "bloodw": "두 번째 원본 여자 칸: A/B/O/AB 또는 bloodw_01/02/03/04. 두 입력의 순서를 보존합니다."
        }
    ),
    "interlife-free-5": _metadata(
        "행운번호un",
        "solve/F/F019.asp:8-120",
        {"sex": "남", "tele": "1234"},
        {
            "sex": "원본 성별 남/여. 길흉 분류 열은 각각 DB_express/DB_express_1입니다.",
            "tele": "원본 4자리 선택 숫자. 예시는 가상 값이며 전화번호 전체를 입력하지 않습니다. 생략하면 원본처럼 각 자리 0~8을 추첨합니다.",
            "tele_cookie": "선택: 원본의 이전 4자리 선택 숫자. 원본처럼 tele보다 우선하며 API는 쿠키를 저장하지 않습니다."
        },
        ready=False,
        source_limits=["인접 두 자리 합 3개와 네 자리 총합만 계산·반환하며 입력 숫자 원문은 반환하거나 AI에 전송하지 않습니다.", "F019의 실제 길흉 분류(吉/凶/半吉半凶)가 없어 최종 AI 해석은 차단합니다."]
    ),
    "interlife-free-7": _metadata(
        "웰빙주택un",
        "solve/F/F012.asp:7; " + ROOT + "solve/sajujowha.asp:7-35,134-145",
        {}, {}, requires_birth=True, ready=False,
        source_limits=["tb_manse의 실제 월지와 원본 선택키를 분리합니다. mansedata.month_e·number·jeolip의 의미가 확인되기 전 원본 F012 선택키로 대입하지 않습니다."]
    ),
    "interlife-jum-16": _metadata(
        "64괘 un 분석",
        "solve/J/J015.asp:6-11; " + ROOT + "solve/J/J033.asp:7-166,193-369",
        {"rd": 1, "sticks": [1, 2, 1, 2, 1, 2], "sticks_z": [2, 1, 2, 1, 2, 1], "sticks_zz": [1, 1, 2, 2, 1, 1]},
        {
            "rd": "선택: 원본 강조 효 1~6. 생략하면 독립 추첨합니다. 원본에서 다른 효를 자동 반전시키는 입력은 아닙니다.",
            "sticks": "선택: 현재 괘의 첫 효부터 여섯 효까지 정수 배열(0/1/2). 0은 원본처럼 2로 바꾸며 생략/null 항목은 1~2 추첨입니다.",
            "sticks_z": "선택: 미래 괘의 독립된 여섯 효 배열. 현재 괘에서 자동으로 파생하지 않습니다.",
            "sticks_zz": "선택: 과거 괘의 독립된 여섯 효 배열. 표시 순서는 과거/현재/미래입니다.",
            "source_request_date": "선택: 원본 사주 준비 후 request_year/month/day의 실제 타입·값 객체(year/month/day). 기본은 Form 문자열·월일2자리입니다. 일반 경로는 문자열 + 연결이며 윤달 Sun_Value=3 ByRef 변환 후 정수3개이면 숫자 합입니다. 입력해도 원본 인증을 대신하지 않습니다."
        },
        requires_birth=True, ready=False,
        source_limits=["J015는 Form 문자열의 + 연결 후 Mod65를 적용합니다. 기본 API 매핑은 월일2자리이며 명시 source_request_date로 원본 padding·윤달 ByRef 정수 변환 상태를 재현합니다.", "J033의 효 선택·독립4~8추첨과 실제 DB_title 괘명·도식 미확정 차단을 보존합니다."]
    ),
    "interlife-free-12": _metadata(
        "음양력변환",
        "unse/free/free_12.asp:29-48",
        {},
        {},
        requires_birth=True,
        calculation_only=True,
        source_limits=["기본 달력 변환만 tb_manse 교정 조회로 대응합니다. f_Saju 명식·대운 배열과의 동일성을 뜻하지 않습니다."]
    ),
    "interlife-manse-2": _metadata(
        "음양력변환",
        "unse/manse/manse_2.asp:24-43",
        {},
        {},
        requires_birth=True,
        calculation_only=True,
        source_limits=["interlife-free-12와 같은 달력 표시 계약입니다. 원본에 AI 해석문구가 없습니다."]
    ),
    "interlife-free-13": _metadata(
        "꿈해몽",
        "unse/free/free_13.asp:19-20,80; " + ROOT + "solve/F/F020.asp:4-55",
        {"dream_name": "호랑이", "page": 1},
        {
            "dream_name": "원본 검색어. DB_title 안의 [검색어]를 찾습니다.",
            "name1": "dream_name이 빈 경우 원본 helper에서 사용하는 대체 검색어입니다.",
            "page": "원본 검색 페이지, 1 이상 정수. 페이지당 20행입니다."
        },
        ready=False,
        source_limits=["검색 행수·제목·DB_num 정렬을 결정할 원본 F020 인덱스가 필요합니다. AI가 검색된 원본 행을 만들어 내지 않습니다."]
    ),
    "interlife-free-14": _metadata(
        "태몽",
        "unse/free/free_14.asp:19-20,80; " + ROOT + "solve/F/F007.asp:4-27",
        {"name1": "호랑이", "page": 1},
        {
            "name1": "실제 F007 helper가 검색하는 입력 이름입니다.",
            "dream_name": "원본 외부 페이지가 받지만 F007 검색어로 전달하지 않는 값입니다. 자동으로 name1에 복사하지 않습니다.",
            "page": "원본 검색 페이지, 1 이상 정수. 페이지당 20행입니다."
        },
        ready=False,
        source_limits=["F007은 name1을 사용합니다. 원본 DB 제목·행수·전체 DB_num 기반 페이지 경계가 미확보라 최종 해석을 차단합니다."]
    )
}
for _service, _required in {
    "interlife-free-5": ["F019.DB_express/DB_express_1 실제 吉/凶/半吉半凶 분류"],
    "interlife-free-7": ["mansedata.month_e 원본 월지", "mansedata.number/jeolip 일자·2월 절입 분기 의미"],
    "interlife-jum-16": ["J033.DB_title 실제 괘명·도식"],
}.items():
    SERVICES[_service]["required_source_fields"] = _required


def _text(parameters: dict, key: str) -> str:
    value = parameters.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DomainError("invalid_service_parameters", f"{key}에 문자열 입력이 필요합니다.")
    return value


def _sex(parameters: dict) -> str:
    sex = parameters.get("sex")
    if not isinstance(sex, str) or sex not in {"남", "여"}:
        raise DomainError("invalid_service_parameters", "sex는 남 또는 여여야 합니다.")
    return sex


def _blood(parameters: dict, key: str, prefix: str) -> str:
    value = _text(parameters, key)
    codes = {prefix + "01": "A", prefix + "02": "B", prefix + "03": "O", prefix + "04": "AB"}
    blood = codes.get(value, value.upper())
    if blood not in {"A", "B", "O", "AB"}:
        raise DomainError("invalid_service_parameters", f"{key}의 원본 혈액형 선택값을 확인해 주세요.")
    return blood


def _selector(identifier: str, table: str, where: dict, columns: list[str], purpose: str) -> dict:
    return {
        "id": identifier,
        "table": table,
        "where": where,
        "columns": columns,
        "purpose": purpose,
        "narrative": True,
        "role": "narrative"
    }


def _server_date(parameters: dict) -> date:
    value = parameters.get("server_date")
    if value is None:
        return datetime.now(KST).date()
    if not isinstance(value, str):
        raise DomainError("invalid_service_parameters", "server_date는 YYYY-MM-DD 문자열이어야 합니다.")
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError
        return parsed
    except ValueError as exc:
        raise DomainError("invalid_service_parameters", "server_date를 YYYY-MM-DD 형식의 유효한 날짜로 입력해 주세요.") from exc


def _zodiac(month: int, day: int) -> tuple[str, int]:
    """Literal ordered If/ElseIf table in setting_var.asp, not generic zodiac."""
    conditions = (
        (month == 12 and day > 23 or month == 1 and day < 21, "염소자리", 12),
        (month == 1 and day > 20 or month == 2 and day < 20, "물병자리", 1),
        (month == 2 and day > 19 or month == 3 and day < 21, "물고기자리", 2),
        (month == 3 and day > 20 or month == 4 and day < 21, "양자리", 3),
        (month == 4 and day > 20 or month == 5 and day < 22, "황소자리", 4),
        (month == 5 and day > 21 or month == 6 and day < 22, "쌍둥이자리", 5),
        (month == 6 and day > 21 or month == 7 and day < 24, "게자리", 6),
        (month == 7 and day > 23 or month == 8 and day < 24, "사자자리", 7),
        (month == 8 and day > 23 or month == 9 and day < 24, "처녀자리", 8),
        (month == 9 and day > 23 or month == 10 and day < 24, "천칭자리", 9),
        (month == 10 and day > 23 or month == 11 and day < 23, "전갈자리", 10)
    )
    return next(((label, number) for matched, label, number in conditions if matched), ("사수자리", 11))


def _face(parameters: dict) -> tuple[dict, list[dict]]:
    sex = _sex(parameters)
    face = parameters.get("face")
    if not isinstance(face, dict) or set(face) - set(FACE_OPTIONS):
        raise DomainError("invalid_service_parameters", "face에는 원본 face_style 선택값 객체를 입력해 주세요.")
    if any(key not in face for key in FACE_REQUIRED):
        raise DomainError("invalid_service_parameters", "face에 최종 결과를 계산할 필수 21개 선택값이 필요합니다.")
    if any(not isinstance(value, str) or value not in FACE_OPTIONS[key] for key, value in face.items()):
        raise DomainError("invalid_service_parameters", "face 값이 원본 라디오 선택지에 없습니다. face_options를 확인해 주세요.")
    forehead = "이마참자형||이마발애형" if face["face_style2"] in {"이마참자형", "이마발애형"} else "이마M자형||이마둥근형||이마네모형"
    wrinkles = "이마주름살복잡||이마주름살한개" if face["face_style4"] in {"이마주름살복잡", "이마주름살한개"} else "이마주름살세개||이마주름살기러기||이마주름살활형||이마주름살현침"
    eyebrows = "눈썹길이길음||눈썹길이적당" if face["face_style6"] in {"눈썹길이길음", "눈썹길이적당"} else "눈썹길이짧음"
    spacing = "미간사이넓음||미간사이적당" if face["face_style7_1"] in {"미간사이넓음", "미간사이적당"} else "미간사이좁음"
    # faceface_13:112-123 print order differs from the data assignment order.
    outputs = (
        ("data_1", face["face_style1"], "얼굴 형태"),
        ("data_2", forehead + "&&" + wrinkles, "이마 모양과 주름"),
        ("data_3", eyebrows + "&&" + spacing, "눈썹 길이와 미간"),
        ("data_4_1", face["face_style8"], "눈 크기"),
        ("data_4_2", face["face_style9"], "눈 모양"),
        ("data_4_3", face["face_style11"], "눈꼬리 주름"),
        ("data_4_4", face["face_style12"], "눈꼬리"),
        ("data_4_5", face["face_style10"], "눈동자 위치"),
        ("data_5_1", face["face_style16"], "귓볼"),
        ("data_5_2", face["face_style14"], "귀 위치"),
        ("data_8", face["face_style30"], "인중 모습"),
        ("data_7", face["face_style25"], "법령"),
        ("data_9", face["face_style27"], "인중 길이"),
        ("data_10", face["face_style31"], "입술 크기"),
        ("data_10_1", face["face_style34"], "입술 끝"),
        ("data_12", face["face_style3"], "이마 폭"),
        ("data_6_1", face["face_style18"], "코 길이"),
        ("data_6_2", face["face_style20"], "콧등"),
        ("data_11", face["face_style37"], "턱 모양")
    )
    column = "DB_data_m" if sex == "남" else "DB_data_w"
    selectors = [
        _selector(identifier, "T063", {"DB_express": key}, [column], topic)
        for identifier, key, topic in outputs
    ]
    return {
        "source_profile": "interlife-faceface-final-v1",
        "selection_method": "사용자가 직접 선택한 원본 관상 항목; 사진 분석·형상 추정 없음",
        "result_column": column,
        "printed_items": 19,
        "unused_source_queries": "직업·가족·부부용 보조 query는 최종 HTML에 출력되지 않아 해석 항목에 추가하지 않습니다."
    }, selectors


def _dream(service_id: str, parameters: dict) -> tuple[dict, list[dict], list[str]]:
    ordinary = service_id == "interlife-free-13"
    if ordinary:
        keyword = parameters.get("dream_name") or parameters.get("name1")
    else:
        keyword = parameters.get("name1")
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        field = "dream_name 또는 name1" if ordinary else "name1"
        raise DomainError("invalid_service_parameters", f"{field}에 1~200자 검색어를 입력해 주세요.")
    page = parameters.get("page", 1)
    if type(page) is not int or not 1 <= page <= 100000:
        raise DomainError("invalid_service_parameters", "page는 1~100000 정수여야 합니다.")
    table, title = ("F020", "DB_title") if ordinary else ("F007", "DB_title_1")
    pattern = "%![" + keyword + "!]%" if ordinary else "%" + keyword + "%"
    condition = {"operator": "sql_like", "pattern": pattern}
    if ordinary:
        condition["escape"] = "!"
    selector = _selector("dream-search", table, {title: condition}, [title, "DB_data"], "원본 꿈 검색 결과")
    selector.update({
        "narrative": False,
        "role": "calculation",
        "pagination": {
            "page": page,
            "size": 20,
            "order": "DB_num DESC",
            "boundary_top_count": (page - 1) * 20 + 1,
            "boundary_query_applies_keyword_filter": ordinary
        }
    })
    facts = {
        "source_profile": "interlife-dream-search-v1",
        "keyword_binding": "dream_name, empty fallback name1" if ordinary else "name1 only",
        "page_size": 20,
        "result_count": None,
        "original_result_titles": None,
        "dream_name_copied_to_name1": False,
        "source_pagination_quirk": "F007 경계 DB_num subquery에는 검색어 필터가 없습니다." if not ordinary else "F020 경계 subquery도 같은 검색어로 제한합니다."
    }
    return facts, [selector], [
        f"{table} 원본 검색 인덱스({title}, DB_num)와 검색 일치 행수·순서가 미확보입니다. AI가 검색 결과 제목·개수·원본 행을 임의 생성하지 않습니다."
    ]


def _lucky_number(parameters: dict) -> tuple[dict, list[dict], list[str]]:
    sex = _sex(parameters)
    if any(value is not None and not isinstance(value, str)
           for value in (parameters.get("tele"), parameters.get("tele_cookie"))):
        raise DomainError("invalid_service_parameters", "선택 숫자는 네 자리 문자열이어야 합니다.")
    selected = parameters.get("tele_cookie") or parameters.get("tele")
    generated = not selected
    if generated:
        digits = [randbelow(9) for _ in range(4)]
        mode = "generated_digits_0_to_8"
    else:
        if not isinstance(selected, str) or len(selected) != 4 or any(char not in "0123456789" for char in selected):
            raise DomainError("invalid_service_parameters", "선택 숫자는 0~9로 된 정확히 네 자리 문자열이어야 합니다.")
        digits = [int(char) for char in selected]
        mode = "tele_cookie" if parameters.get("tele_cookie") else "tele"
    adjacent = [digits[index] + digits[index + 1] for index in range(3)]
    total = sum(digits)
    classification = "DB_express" if sex == "남" else "DB_express_1"
    selectors = []
    selected_sums = [(f"adjacent-{index + 1}", value) for index, value in enumerate(adjacent) if value != 0]
    selected_sums.append(("total", total))
    for identifier, number in selected_sums:
        where = {"DB_num": str(number)}
        selectors.append(_selector(identifier, "F019", where, ["DB_title", "DB_data"], "원본 수리 번호별 제목·설명"))
        selectors.append({**_selector(identifier + "-classification", "F019", where, [classification], "원본 길흉 분류"),
                          "narrative": False, "role": "calculation"})
    return {
        "source_profile": "interlife-f019-number-sums-v1", "selection_mode": mode,
        "adjacent_sums": adjacent, "total_sum": total,
        "classification_column": classification, "classification": None,
        "source_rng_digit_range": [0, 8], "input_digits_disclosed": False,
    }, selectors, ["F019의 성별별 吉/凶/半吉半凶 실제 분류가 없어 색상·기호와 최종 길흉 판정을 확정할 수 없습니다."]


def _six_lines(parameters: dict, key: str) -> list[int]:
    value = parameters.get(key)
    if value is None:
        value = [None] * 6
    if not isinstance(value, list) or len(value) != 6:
        raise DomainError("invalid_service_parameters", "괘 입력은 각 여섯 효 배열이어야 합니다.")
    result = []
    for item in value:
        if item is None:
            result.append(randbelow(2) + 1)
        elif type(item) is int and item in {0, 1, 2}:
            result.append(2 if item == 0 else item)
        else:
            raise DomainError("invalid_service_parameters", "효 값은 0/1/2 또는 null이어야 합니다.")
    return result


def _hexagrams(request: ServiceRequest, *, with_birth_number=True) -> tuple[dict, list[dict], list[str]]:
    parameters = request.parameters
    highlight = parameters.get("rd")
    if highlight is None:
        highlight = randbelow(6) + 1
    elif type(highlight) is not int or not 1 <= highlight <= 6:
        raise DomainError("invalid_service_parameters", "rd는 1~6 정수여야 합니다.")
    current = _six_lines(parameters, "sticks")
    future = _six_lines(parameters, "sticks_z")
    past = _six_lines(parameters, "sticks_zz")
    # Source draw order is Tb_J032, Tb_J033, Tb_J034, displayed as past/current/future.
    scores = {name: randbelow(5) + 4 for name in ("past", "current", "future")}
    keys = {name: "".join(map(str, lines)) for name, lines in (("past", past), ("current", current), ("future", future))}
    selectors = []
    birth_facts = {}
    if with_birth_number:
        values = parameters.get("source_request_date", {"year": str(request.birth.year), "month": f"{request.birth.month:02d}", "day": f"{request.birth.day:02d}"})
        if not isinstance(values, dict) or set(values) != {"year", "month", "day"}:
            raise DomainError("invalid_service_parameters", "source_request_date에는 year/month/day 세 원본 값만 입력하세요.")
        strings, integers = all(type(value) is str for value in values.values()), all(type(value) is int for value in values.values())
        if not strings and not integers:
            raise DomainError("invalid_service_parameters", "원본 날짜 상태는 문자열 세 값 또는 윤달 변환 후 정수 세 값이어야 합니다.")
        if strings and any(not value or len(value) > (4 if key == "year" else 2) or any(char not in "0123456789" for char in value) for key, value in values.items()):
            raise DomainError("invalid_service_parameters", "원본 날짜 문자열의 숫자 형식·길이를 확인하세요.")
        year, month, day = (int(values[name]) for name in ("year", "month", "day"))
        if not 1900 <= year <= 2050 or not 1 <= month <= 12 or not 1 <= day <= 31:
            raise DomainError("invalid_service_parameters", "원본 날짜 상태의 연월일 범위를 확인하세요.")
        key = int(values["month"] + values["year"] + values["day"]) % 65 if strings else (month + year + day) % 65
        birth_facts = {"source_birth_date_mod65": key, "source_birth_date_variant": "form_strings" if strings else "leap_byref_numeric",
                       "source_request_date_supplied": "source_request_date" in parameters,
                       "default_form_day_padding": "two_digits"}
        selectors.append(_selector("birth-number", "J015", {"DB_express": str(key)}, ["DB_data"], "원본 문자열 + 또는 윤달 ByRef 숫자 + 후 Mod65"))
    for name, number in keys.items():
        where = {"DB_express": number}
        selectors.append({**_selector(name + "-name", "J033", where, ["DB_title"], "실제 괘명·원본 도식"),
                          "narrative": False, "role": "calculation"})
        selectors.append(_selector(name, "J033", where, [f"DB_data_{index}" for index in range(1, 9)], "원본 과거/현재/미래 해설 8항목"))
    return {
        "source_profile": "interlife-j015-j033-draws-v2", **birth_facts,
        "highlighted_line": highlight, "hexagram_keys": keys,
        "random_graph_scores": scores, "score_basis": "원본의 독립 Rnd 4~8 추첨값; 사주나 DB 판정 점수가 아닙니다.",
        "independent_three_hexagrams": True, "hexagram_names": None,
    }, selectors, ["J033.DB_title의 실제 괘명·도식 자료가 없어 괘 이름과 원본 해설 대상을 확정할 수 없습니다."]


def decide(
    service_id: str,
    request: ServiceRequest,
    saju: SajuResult | None = None,
    partner: SajuResult | None = None
) -> dict:
    if service_id not in SERVICES:
        raise DomainError("unsupported_service", "이 모듈에 이식되지 않은 interlife 서비스입니다.")
    metadata = SERVICES[service_id]
    parameters = request.parameters
    if set(parameters) - set(metadata["parameter_help"]):
        raise DomainError("invalid_service_parameters", "이 interlife 서비스에서 지원하지 않는 parameters 항목이 있습니다.")
    if metadata["requires_birth"] and request.birth is None:
        raise DomainError("birth_required", "이 서비스에는 birth가 필요합니다.")
    facts: dict = {"source_profile": "interlife-leaf-v1", "shared_saju_preamble_used": False}
    selectors: list[dict] = []
    unresolved: list[str] = []
    notes: list[str] = []

    if service_id == "interlife-faceface":
        face_facts, selectors = _face(parameters)
        facts.update(face_facts)
    elif service_id == "interlife-free-1":
        server = _server_date(parameters)
        key = server.strftime("%m%d")
        animals = ((11, "쥐띠"), (12, "소띠"), (1, "범띠"), (2, "토끼띠"), (3, "용띠"), (4, "뱀띠"), (5, "말띠"), (6, "양띠"), (7, "원숭이띠"), (8, "닭띠"), (9, "개띠"), (10, "돼지띠"))
        selectors = [
            _selector(f"animal-{code:02d}", "F022", {"DB_express": f"{key}{code:02d}"}, ["DB_data"], name)
            for code, name in animals
        ]
        facts.update({"source_date": server.isoformat(), "default_clock": "UTC+09:00", "all_twelve_animals": True, "personal_birth_used": False})
    elif service_id == "interlife-free-2":
        profile = parameters.get("source_profile", "asp_ui")
        if not isinstance(profile, str) or profile not in {"asp_ui", "asp_original_unconverted"}:
            raise DomainError("invalid_service_parameters", "source_profile 값을 확인해 주세요.")
        if request.birth.calendar == "lunar" and profile != "asp_original_unconverted":
            raise DomainError("interlife_raw_lunar_zodiac", "이 원본은 입력 월·일 숫자로 별자리를 고릅니다. 양력으로 입력하거나 source_profile=asp_original_unconverted로 원본 미변환 동작을 명시해 주세요.")
        name, number = _zodiac(request.birth.month, request.birth.day)
        column = "DB_data_m" if request.birth.gender == "male" else "DB_data_w"
        selectors = [_selector("zodiac", "F013", {"DB_express": name}, [column], "별자리un")]
        facts.update({"zodiac": {"name": name, "source_serial_no": number}, "calendar_action": "explicit_original_unconverted_lunar_digits" if request.birth.calendar == "lunar" else "solar_input", "source_boundary_table": ROOT + "solve/setting_var.asp:10-45"})
    elif service_id == "interlife-free-3":
        blood = _blood(parameters, "blood", "blood_")
        column = "DB_data_m" if _sex(parameters) == "남" else "DB_data_w"
        selectors = [_selector("blood", "F033", {"DB_express": blood}, ["DB_data", column], "혈액형 공통 설명과 성별 설명")]
        facts["blood_type"] = blood
    elif service_id == "interlife-free-6":
        male = _blood(parameters, "bloodm", "bloodm_")
        female = _blood(parameters, "bloodw", "bloodw_")
        selectors = [_selector("blood-pair", "F034", {"DB_express": male, "DB_express_1": female}, ["DB_data"], "혈액형궁합")]
        facts["ordered_blood_types"] = [male, female]
    elif service_id == "interlife-free-5":
        values, selectors, unresolved = _lucky_number(parameters)
        facts.update(values)
    elif service_id == "interlife-free-7":
        solar, row = _birth_record(request.birth)
        raw_month_branch = BRANCHES[int(row["m_ji"])]
        facts.update({
            "source_profile": "interlife-f012-unverified-month-binding-v1",
            "available_tb_manse_month_branch": raw_month_branch,
            "available_tb_manse_month_branch_code": (int(row["m_ji"]) - 2) % 12 + 1,
            "source_month_e": None,
            "source_february_only_before_jeolip_row_decrement": True,
            "available_basic_calendar_is_original_month_e": False,
            "source_birth_month": solar.month,
        })
        selectors = [_selector("housing", "F012", {"DB_express": None}, ["DB_data"], "원본 my_month_e별 웰빙주택 설명")]
        selectors[0]["key_unresolved"] = True
        unresolved = ["원본 mansedata.month_e·number·jeolip의 일자/절입 의미가 미확보입니다. tb_manse raw 월지를 원본 my_month_e로 추정 대입하지 않습니다."]
    elif service_id == "interlife-jum-16":
        values, selectors, unresolved = _hexagrams(request)
        facts.update(values)
    elif service_id in {"interlife-free-12", "interlife-manse-2"}:
        value, row = _birth_record(request.birth)
        facts.update({
            "source_profile": "tb-manse-basic-calendar-v4",
            "calendar_conversion": {
                "solar": {"year": value.year, "month": value.month, "day": value.day},
                "lunar": {"year": int(row["l_year"]), "month": int(row["l_mon"]), "day": int(row["l_day"]), "leap_month": bool(row["leafMon_YN"])},
                "hour": request.birth.hour,
                "minute": request.birth.minute
            },
            "lunar_correction_version": "lunar-leap-flags-v1",
            "saju_or_major_luck_equivalence_claimed": False
        })
        notes.append("원본 출력은 양력·음력 생년월일시 표시뿐인 계산전용 서비스입니다. AI 해석문구를 생성하지 않습니다.")
    else:
        dream_facts, selectors, unresolved = _dream(service_id, parameters)
        facts.update(dream_facts)

    return {
        "source": metadata["source"],
        "facts": facts,
        "selectors": selectors,
        "unresolved": unresolved,
        "notes": notes
    }

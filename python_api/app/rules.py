"""T-001/T-002: function/function.asp and valueDef.asp rules, expressed without globals."""

from app.models import Score

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
GANJI = tuple(STEMS[i % 10] + BRANCHES[i % 12] for i in range(60))
HANGUL = dict(zip(STEMS + BRANCHES, "갑을병정무기경신임계자축인묘진사오미신유술해"))
ELEMENTS = "목화토금수"
STEM_ELEMENTS = dict(zip(STEMS, "목목화화토토금금수수"))
BRANCH_ELEMENTS = dict(zip(BRANCHES, "수토목목토화화토금금토수"))
# Legacy compareZone*: branches are represented by their primary stem.
BRANCH_STEMS = dict(zip(BRANCHES, "癸己甲乙戊丙丁己庚辛戊壬"))
LIFE_STAGES = ("장생", "목욕", "관대", "건록", "제왕", "쇠", "병", "사", "묘", "절", "태", "양")
LIFE_STARTS = dict(zip(STEMS, "亥午寅酉寅酉巳子申卯"))
TOPICS = (
    ("love", "애정·만남"),
    ("career", "취업·시험·계약"),
    ("movement", "이동·변화"),
    ("wealth", "재물"),
    ("conflict", "시비·오해"),
    ("separation", "관계 갈등"),
    ("caution", "주의 필요도"),
    ("ideas", "아이디어"),
)


def ten_god(day_stem: str, other: str) -> str:
    other = BRANCH_STEMS.get(other, other)
    a, b = STEMS.index(day_stem), STEMS.index(other)
    diff = (b // 2 - a // 2) % 5
    names = (
        ("비견", "겁재"),
        ("식신", "상관"),
        ("편재", "정재"),
        ("편관", "정관"),
        ("편인", "인수"),
    )
    return names[diff][int(a % 2 != b % 2)]


def daily_ten_god(day_stem: str, other: str) -> str:
    """Exact function.asp compareZone8 VB-string value, not a silent typo repair.

    VBScript treats two quotes inside a quoted string as a literal quote.
    The commercial snapshot therefore returns 인수\"비견 for 辛/辰. Only the
    daily/week function.asp path calls this table; do not leak it into SipKyuk.
    """
    if day_stem == "辛" and other == "辰":
        return '인수"비견'
    return ten_god(day_stem, other)


def life_stage(day_stem: str, branch: str) -> str:
    direction = 1 if STEMS.index(day_stem) % 2 == 0 else -1
    offset = (BRANCHES.index(branch) - BRANCHES.index(LIFE_STARTS[day_stem])) * direction
    return LIFE_STAGES[offset % 12]


def _scoring(good, bad, weakened, general=True):
    b1, b2 = good
    w1, w2 = bad
    if general and b1 and b2 and weakened:
        return 90
    if general and (b1 or b2) and weakened:
        return 75
    if (b1 or b2) and (w1 or w2):
        return 70
    if b1 and b2:
        return 100
    if b1 or b2:
        return 80
    if general and weakened and (w1 or w2):
        return 40
    if w1 and w2:
        return 10
    if w1 or w2:
        return 30
    return 55 if general else 45


def legacy_scores(
    day_stem: str, target_pillar: str, gender: str, *, temp_chk: bool | None = None
) -> list[Score]:
    """Preserve score direction: high caution is NOT a favorable outcome."""
    stem, branch = target_pillar
    gods = (daily_ten_god(day_stem, stem), daily_ten_god(day_stem, branch))
    weak = (life_stage(day_stem, branch) in {"사", "묘", "절"}) if temp_chk is None else temp_chk
    money, officer = {"편재", "정재"}, {"편관", "정관"}
    good = [
        money if gender == "male" else officer,
        officer,
        {"상관"},
        money,
        {"상관"},
        {"겁재"} if gender == "male" else {"상관", "겁재"},
        set(),
        {"편인"},
    ]
    bad = (
        [{"겁재"}, {"상관"}, officer, {"겁재"}, {"인수"}, {"정관"}, set(), set()]
        if gender == "male"
        else [{"상관"}, {"상관"}, officer, {"겁재"}, {"인수"}, {"인수"}, set(), set()]
    )
    result = []
    for index, (key, label) in enumerate(TOPICS):
        bs = tuple(g in good[index] for g in gods)
        ws = tuple(g in bad[index] for g in gods)
        weakened = weak and any(bs)
        if index == 1:
            # Original case 2 clears B before checking M, so M is never set here.
            bs = tuple(b and not weak for b in bs)
            weakened = False
        if index == 6:
            position = STEMS.index(day_stem)
            blade = branch in ("卯辰午未午未酉戌子丑"[position], "酉戌子丑子丑卯辰午未"[position])
            raw = (90 if weak else 100) if blade else 20
        else:
            raw = _scoring(bs, ws, weakened, general=index not in {2, 4, 5})
            if index == 7 and raw == 90:
                raw = 70
        caution = index in {2, 4, 5, 6}
        result.append(
            Score(
                key=key,
                label=label,
                raw=raw,
                direction="caution" if caution else "opportunity",
                favorable=100 - raw if caution else raw,
            )
        )
    return result

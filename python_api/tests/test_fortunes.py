from datetime import date

import pytest

from app.errors import DomainError
from app.fortunes import analyze
from app.models import FortuneKind, FortuneRequest
from app.rules import BRANCHES, STEMS, daily_ten_god, legacy_scores, life_stage, ten_god


def request(**kwargs):
    return FortuneRequest(
        **(
            {
                "birth": {
                    "year": 1990,
                    "month": 5,
                    "day": 17,
                    "hour": 14,
                    "minute": 30,
                    "gender": "male",
                },
                "target_date": "2026-11-02",
                "include_ai": False,
            }
            | kwargs
        )
    )


def test_all_ten_gods_and_life_stage_cycles():
    assert ten_god("甲", "甲") == "비견"
    assert ten_god("甲", "乙") == "겁재"
    assert ten_god("甲", "癸") == "인수"
    assert ten_god("辛", "丑") == "편인"
    for stem in STEMS:
        assert len({ten_god(stem, other) for other in STEMS}) == 10
        assert len({life_stage(stem, b) for b in BRANCHES}) == 12


def test_legacy_known_scores_and_directions():
    # 甲日, 戊辰: 편재/편재, 衰 -> money and male love 100.
    scores = {s.key: s for s in legacy_scores("甲", "戊辰", "male")}
    assert scores["love"].raw == scores["wealth"].raw == 100
    assert scores["caution"].raw == 20
    assert scores["caution"].favorable == 80
    # 甲日, 己未: 정재/정재, 墓 -> weakened score 90.
    assert legacy_scores("甲", "己未", "male")[0].raw == 90
    # Career case-2 clears good flags in 死/墓/絶, preserving original ordering.
    assert legacy_scores("甲", "庚申", "male")[1].raw == 55


@pytest.mark.parametrize("kind", list(FortuneKind))
def test_every_supported_fortune_returns_evidence(kind):
    data = request()
    if kind == FortuneKind.yearly:
        data.target_date = date(2005, 11, 2)
    if kind == FortuneKind.compatibility:
        data.partner = data.birth.model_copy(update={"year": 1992, "gender": "female"})
    result = analyze(kind, data)
    assert result.evidence
    assert len({e.id for e in result.evidence}) == len(result.evidence)
    assert result.period_start <= result.target_date <= result.period_end


def test_week_preserves_sunday_interval_and_original_sticky_state():
    result = analyze(FortuneKind.weekly, request())
    assert result.period_start == date(2026, 11, 1)
    assert result.period_end == date(2026, 11, 7)
    days = [e for e in result.evidence if e.topic == "daily"]
    assert len(days) == 7
    assert all(e.facts["tempChk"] for e in days)  # 壬日: first Sunday 卯 is 死.
    fifth = next(e for e in days if e.facts["date"] == "2026-11-05")
    daily = analyze(FortuneKind.daily, request(target_date="2026-11-05"))
    assert fifth.facts["life_stage"] == "양"
    assert fifth.facts["scores"][1]["raw"] == 55
    assert daily.scores[1].raw == 80


def test_month_and_year_use_original_keys_not_new_samples():
    month = analyze(FortuneKind.monthly, request(target_date="2024-02-10"))
    assert month.selectors[0]["table"] == "monthfor"
    assert set(month.selectors[0]["where"]) == {"memno", "yukgap_no", "sex"}
    assert not any(e.id.startswith("period-") for e in month.evidence)
    assert not month.scores
    year = analyze(FortuneKind.yearly, request(target_date="2027-01-01"))
    assert year.selectors == []
    assert year.method == "asp-saju-ai-yearly-v1"
    assert year.ready_for_ai
    assert len(year.narrative_contract) == 7
    assert year.scores == []


def test_compatibility_requires_partner_and_other_types_reject_it():
    with pytest.raises(DomainError, match="partner"):
        analyze(FortuneKind.compatibility, request())
    r = request()
    r.partner = r.birth
    with pytest.raises(DomainError, match="partner"):
        analyze(FortuneKind.daily, r)


def test_target_before_birth_is_rejected():
    with pytest.raises(DomainError, match="출생일"):
        analyze(FortuneKind.biorhythm, request(target_date="1989-01-01"))


def test_biorhythm_birth_day_and_known_quarter_cycle():
    zero = analyze(FortuneKind.biorhythm, request(target_date="1990-05-17"))
    assert all(
        r["value"] == 0 and r["state"] == "critical" for r in zero.evidence[-1].facts["rhythms"]
    )
    week = analyze(FortuneKind.biorhythm, request(target_date="1990-05-24"))
    assert week.evidence[-1].facts["rhythms"][1]["value"] == 100


def test_week_does_not_silently_clip_original_seven_day_interval():
    r = request(target_date="1900-01-01")
    r.birth = r.birth.model_copy(update={"year": 1900, "month": 1, "day": 1})
    with pytest.raises(DomainError):
        analyze(FortuneKind.weekly, r)
    last = analyze(FortuneKind.weekly, request(target_date="2050-12-31"))
    assert (last.period_end - last.period_start).days == 6


def test_love_does_not_reuse_daily_scores_and_preserves_all_five_slots():
    result = analyze(FortuneKind.love, request())
    assert result.scores == []
    assert result.ready_for_ai
    assert len(result.narrative_contract) == 5
    assert all(s["table"] == "tbLoveLuck" for s in result.selectors)


def test_unresolved_legacy_dependencies_are_not_ai_targets():
    r = request()
    r.partner = r.birth
    compatibility = analyze(FortuneKind.compatibility, r)
    assert not compatibility.ready_for_ai
    assert not compatibility.narrative_contract
    assert compatibility.unresolved_dependencies
    career = analyze(FortuneKind.career, request(career_category="F"))
    assert not career.ready_for_ai
    assert len(career.selectors) == 15
    assert not career.narrative_contract


def test_original_week_star_threshold_gaps_are_preserved():
    from app.fortunes import _week_stars

    assert _week_stars(336) == 0
    assert _week_stars(340) == 5  # Original unhandled gap falls through to Else.
    assert _week_stars(344) == 1


def test_all_220_ten_god_cells_match_extracted_original_tables():
    import json
    from pathlib import Path

    original = json.loads((Path(__file__).parent / "fixtures" / "legacy_ten_gods.json").read_text())
    checked = 0
    for group in ("stems", "branches"):
        for master, mapping in original[group].items():
            for other, expected in mapping.items():
                assert daily_ten_god(master, other) == expected
                checked += 1
    assert checked == 220


def test_source_vb_escaped_quote_is_preserved_only_in_daily_table():
    assert daily_ten_god("辛", "辰") == '인수"비견'
    assert ten_god("辛", "辰") == "인수"
    assert legacy_scores("辛", "庚辰", "male")[4].raw == 45


@pytest.mark.parametrize(
    "kind,expected_count",
    [
        (FortuneKind.daily, 3),
        (FortuneKind.weekly, 1),
        (FortuneKind.monthly, 1),
        (FortuneKind.lifetime, 13),
        (FortuneKind.wealth, 4),
        (FortuneKind.love, 5),
        (FortuneKind.biorhythm, 1),
    ],
)
def test_ready_contracts_cover_original_rendered_slots(kind, expected_count):
    result = analyze(kind, request())
    assert result.ready_for_ai
    assert len(result.narrative_contract) == expected_count
    assert len({t.id for t in result.narrative_contract}) == expected_count
    assert not result.unresolved_dependencies


def test_biorhythm_and_weekly_keep_selected_original_inline_meaning():
    from app.legacy_inline import BIO_MENT, WEEK_DESC

    week = analyze(FortuneKind.weekly, request()).evidence[-1].facts
    assert week["original_inline_anchor"] == WEEK_DESC[week["grade"]]
    bio = analyze(FortuneKind.biorhythm, request()).evidence[-1].facts
    assert bio["original_inline_anchor"] == BIO_MENT[bio["ment_index"]]

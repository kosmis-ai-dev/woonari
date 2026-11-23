import hashlib
import json

from app.legacy_inline import BIO_MENT, WEEK_DESC


def test_all_27_original_biorhythm_branches_are_present():
    assert list(BIO_MENT) == list(range(1, 28))
    assert all(isinstance(text, str) and text for text in BIO_MENT.values())


def test_original_appends_and_missing_spaces_are_preserved():
    # ment(8) has three assignments; the last append intentionally has no leading space.
    assert BIO_MENT[8] == (
        "오로지 기대할 것은 지성리듬뿐이다. "
        "불안정한 신체리듬때문에 끝장난 기분이 들 것이고 감성적으로는 우울하다."
        "조심해야 할 날이다."
    )
    assert (
        BIO_MENT[14]
        == "세 개의 리듬이 모두 고조기!!! 바로 당신의 날이니 절호의 기회를 최대로 활용하라."
    )
    assert BIO_MENT[27] == (
        "신체,감성,지성의 세 리듬이 모두 저조기이다. "
        "그렇게 불안해하지 말고 좋은 날을 기다리며 휴식을 취해라."
    )


def test_source_weekly_branch_keys_and_personal_name_placeholder():
    assert list(WEEK_DESC) == ["very_good", "effort", "act", "review", "prepare"]
    for key, value in WEEK_DESC.items():
        assert value.count("{name}") == (0 if key == "review" else 1)
    assert WEEK_DESC["effort"].format(name="이용자") == (
        "이번 한 주는 <b>이용자</b>님의 노력여하에 따라 그 결과가 비례하는 그런 한 주가 됩니다. "
        "해야할 일의 먼저와 나중, 그리고 중요함과 가벼움을 잘 가려서 성실하고 활기차게 생활하세요."
    )


def test_review_source_text_is_not_replaced_by_generic_advice():
    assert WEEK_DESC["review"] == (
        "이번 한주는 다시 한번 되돌아 보고 신중하게 대처하는 자세가 필요한 때입니다. "
        "새로운 일의 시작보다는 이미 진행되고 일을 점검하는 기회로 삼으시면 좋습니다."
    )


def test_exact_source_extraction_snapshot():
    # Computed from ASP literal/append parsing before creating legacy_inline.py.
    snapshot = json.dumps(
        {"bio": BIO_MENT, "week": WEEK_DESC}, ensure_ascii=False, separators=(",", ":")
    ).encode()
    assert (
        hashlib.sha256(snapshot).hexdigest()
        == "7779370b7c2b1b0b9e97f325ee4e0195f7fac56e9d460586a20294fd5d71a2c1"
    )

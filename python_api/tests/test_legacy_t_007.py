import hashlib
import json
from types import SimpleNamespace

import pytest

from app.calendar import calculate_saju
from app.errors import DomainError
from app.legacy_relationships import (
    AISYO_TABLE,
    CAREER_TITLES,
    career_dispatch,
    decide_relationship,
    harmony_content_selectors,
)
from app.models import FortuneRequest


def request(**changes):
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
            | changes
        )
    )


def test_love_exact_day_class_and_gender_columns():
    data = request()
    saju = calculate_saju(data.birth)
    male = decide_relationship("love", data, saju)
    female_data = request(birth=data.birth.model_dump() | {"gender": "female"})
    female = decide_relationship("love", female_data, calculate_saju(female_data.birth))
    assert male["unresolved"] == female["unresolved"] == []
    assert all(s["where"] == {"dokebi": saju.legacy_memno[:3]} for s in male["selectors"])
    assert [s["columns"] for s in male["selectors"]] == [
        ["time_m"],
        ["youtype"],
        ["youjob"],
        ["locate"],
        ["method_m"],
    ]
    assert [s["columns"] for s in female["selectors"]] == [
        ["time_f"],
        ["youtype"],
        ["youjob"],
        ["locate"],
        ["method_f"],
    ]
    assert all(s["table"] == "tbLoveLuck" for s in male["selectors"])


def test_love_keeps_leading_zero_and_does_not_use_target_day_scores():
    data = request()
    saju = calculate_saju(data.birth).model_copy(update={"legacy_memno": "005206307"})
    result = decide_relationship("love", data, saju)
    assert result["facts"]["dokebi"] == "005"
    assert result["selectors"][0]["where"] == {"dokebi": "005"}
    other_day = data.model_copy(update={"target_date": data.target_date.replace(day=3)})
    assert decide_relationship("love", other_day, saju) == result
    assert "scores" not in result["facts"]


@pytest.mark.parametrize("category", list("ABCDE"))
def test_career_single_category_preserves_002_and_three_subcodes(category):
    calls = career_dispatch(category)
    assert [c["where"] for c in calls] == [
        {"method": "getNHResult", "tmpCode": "002", "soCode": f"{category}{i}"} for i in (1, 2, 3)
    ]
    assert [c["purpose"] for c in calls] == list(CAREER_TITLES[category])
    assert all(c["table"] == "NHCP5.NHUnse" for c in calls)


def test_career_F_dispatches_all_fifteen_in_source_order():
    calls = career_dispatch("F")
    assert len(calls) == 15
    assert [c["where"]["soCode"] for c in calls] == [f"{a}{i}" for a in "ABCDE" for i in (1, 2, 3)]
    assert calls[0]["purpose"] == "신분상승을 위하여"
    assert calls[-1]["purpose"] == "부와 명예를 동시에 갖고 싶어서"


def test_career_missing_original_input_and_opaque_dll_remain_unresolved():
    data = request()
    result = decide_relationship(
        "career", SimpleNamespace(career_category=None), calculate_saju(data.birth)
    )
    assert len(result["unresolved"]) == 2
    assert result["selectors"] == []
    result = decide_relationship(
        "career", SimpleNamespace(career_category="A"), calculate_saju(data.birth)
    )
    assert len(result["unresolved"]) == 1
    assert "NHCP5.NHUnse" in result["unresolved"][0]
    assert len(result["selectors"]) == 3


def test_invalid_career_category_is_not_silently_defaulted():
    with pytest.raises(DomainError):
        career_dispatch("G")


def test_compatibility_reads_original_aisyo_classification_before_any_text():
    data = request()
    saju = calculate_saju(data.birth)
    partner = calculate_saju(data.birth.model_copy(update={"year": 1992, "gender": "female"}))
    result = decide_relationship("compatibility", data, saju, partner)
    assert result["unresolved"]
    assert [s["table"] for s in result["selectors"]] == ["tbAisyo", "tbAisyo"]
    assert all(s["role"] == "calculation" and s["narrative"] is False for s in result["selectors"])
    assert [s["where"] for s in result["selectors"]] == [
        {"birth": "1990-05-17"},
        {"birth": "1992-05-17"},
    ]
    assert [x["id"] for x in result["facts"]["output_fields"]] == [
        f"saju_harmony_{i}" for i in (1, 2, 3, 4)
    ]
    assert "branch_pairs" not in result["facts"]


def test_compatibility_uses_converted_korean_solar_date_for_aisyo():
    data = request(
        birth={
            "year": 2023,
            "month": 2,
            "day": 1,
            "hour": 12,
            "gender": "male",
            "calendar": "lunar",
            "leap_month": True,
        }
    )
    saju = calculate_saju(data.birth)
    result = decide_relationship("compatibility", data, saju, saju)
    assert result["selectors"][0]["where"] == {"birth": "2023-03-22"}


def test_compatibility_requires_partner():
    data = request()
    with pytest.raises(DomainError):
        decide_relationship("compatibility", data, calculate_saju(data.birth))


def test_harmony_content_keys_preserve_source_directional_table():
    forward = harmony_content_selectors(1, 19)
    reverse = harmony_content_selectors(19, 1)
    assert [s["where"]["keyno"] for s in forward] == [101, 201, 119, 219, 302, 402]
    assert [s["where"]["keyno"] for s in reverse] == [119, 219, 101, 201, 301, 401]
    assert [s["where"]["menu"] for s in forward] == ["destiny"] * 4 + ["harmony"] * 2
    assert all(s["table"] == "tbSajuMaster_mobile1" for s in forward)


@pytest.mark.parametrize("value", [0, 29, -1, True, "1"])
def test_harmony_unknown_classification_is_not_guessed(value):
    with pytest.raises(DomainError):
        harmony_content_selectors(value, 1)


def test_aisyo_blank_slot_and_matrix_dimensions_preserved():
    assert len(AISYO_TABLE) == 28
    assert all(len(row) == 28 for row in AISYO_TABLE)
    assert set(AISYO_TABLE[19]) == {0}
    assert [s["where"]["keyno"] for s in harmony_content_selectors(20, 1)][-2:] == [300, 400]


def test_source_table_sha256_snapshot():
    # Digest extracted from _SajuManseryuk.asp:39-66, independent of the Python table.
    encoded = json.dumps(AISYO_TABLE, separators=(",", ":")).encode()
    assert (
        hashlib.sha256(encoded).hexdigest()
        == "09024720a8fddca15e1e6b0a1050a30d43a9482f2ec8cb713b94b8c220560025"
    )

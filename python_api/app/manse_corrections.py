"""CR-010 / T-019: apply reviewed leap flags while retaining original DB records."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from app.manse_store import ManseDataError

UNAVAILABLE = "검증된 윤달 교정표와 원본 만세력 자료가 일치하지 않습니다."


@dataclass(frozen=True)
class _Correction:
    solar_date: str
    original_idx: int
    lunar_date: tuple[int, int, int]
    original_leap: int
    corrected_leap: int


def _manifest() -> tuple[dict, tuple[_Correction, ...]]:
    try:
        payload = json.loads(
            (Path(__file__).resolve().parent / "data/manse_corrections.json").read_text("utf-8")
        )
        if (
            payload["schema_version"] != 1
            or payload["version"] != "lunar-leap-flags-v1"
            or payload["field"] != "leafMon_YN"
            or payload["row_count"] != 73414
            or len(payload["corrections"]) != 10
            or any(re.fullmatch(r"[a-f0-9]{64}", payload[key]) is None
                   for key in ("source_sha256", "data_sha256"))
        ):
            raise ValueError
        entries = []
        for value in payload["corrections"]:
            solar = date.fromisoformat(value["solar_date"])
            lunar = tuple(value["lunar_date"])
            if (
                solar.isoformat() != value["solar_date"]
                or type(value["original_idx"]) is not int
                or value["original_idx"] <= 0
                or len(lunar) != 3
                or any(type(part) is not int for part in lunar)
                or not 1 <= lunar[1] <= 12
                or not 1 <= lunar[2] <= 30
                or type(value["original_leap"]) is not int
                or type(value["corrected_leap"]) is not int
                or {value["original_leap"], value["corrected_leap"]} != {0, 1}
                or not value["evidence"]
            ):
                raise ValueError
            entries.append(_Correction(
                value["solar_date"], value["original_idx"], lunar,
                value["original_leap"], value["corrected_leap"],
            ))
        if len({entry.solar_date for entry in entries}) != len(entries):
            raise ValueError
        return payload, tuple(entries)
    except (OSError, KeyError, ValueError, TypeError, RecursionError):
        raise ManseDataError("manse_unavailable", "윤달 교정표를 확인할 수 없습니다.") from None


_POLICY, _CORRECTIONS = _manifest()
CORRECTION_VERSION = _POLICY["version"]
CORRECTION_COUNT = len(_CORRECTIONS)
SOURCE_SHA256 = _POLICY["source_sha256"]
DATA_SHA256 = _POLICY["data_sha256"]
_BY_SOLAR = {item.solar_date: item for item in _CORRECTIONS}
_BY_LUNAR: dict[tuple[int, int, int], tuple[_Correction, ...]] = {}
for _entry in _CORRECTIONS:
    _BY_LUNAR[_entry.lunar_date] = (*_BY_LUNAR.get(_entry.lunar_date, ()), _entry)


def _verify_source(metadata: Mapping) -> None:
    if (
        not isinstance(metadata, Mapping)
        or metadata.get("source_sha256") != SOURCE_SHA256
        or metadata.get("data_sha256") != DATA_SHA256
        or metadata.get("row_count") != _POLICY["row_count"]
    ):
        raise ManseDataError("manse_unavailable", UNAVAILABLE)


def apply_correction(record: Mapping, metadata: Mapping) -> dict:
    """Copy a row and change only its reviewed leap flag, after source checks."""
    if not isinstance(record, Mapping):
        raise ManseDataError("manse_unavailable", UNAVAILABLE)
    result = dict(record)
    correction = _BY_SOLAR.get(result.get("sDate"))
    if correction is None:
        return result
    _verify_source(metadata)
    solar = date.fromisoformat(correction.solar_date)
    expected = {
        "idx": correction.original_idx,
        "s_year": solar.year, "s_mon": solar.month, "s_day": solar.day,
        "l_year": correction.lunar_date[0], "l_mon": correction.lunar_date[1],
        "l_day": correction.lunar_date[2], "leafMon_YN": correction.original_leap,
    }
    if any(type(result.get(key)) is not int or result[key] != value
           for key, value in expected.items()):
        raise ManseDataError("manse_unavailable", UNAVAILABLE)
    result["leafMon_YN"] = correction.corrected_leap
    return result


class CorrectedManseStore:
    """API view over an unchanged raw store, with explicit, versioned corrections."""

    def __init__(self, raw_store):
        self.raw_store = raw_store

    @property
    def backend(self) -> str:
        return self.raw_store.backend

    def metadata(self) -> dict:
        return self.raw_store.metadata()

    def iter_records(self):
        # Export/import fingerprints describe the source, never the API view.
        return self.raw_store.iter_records()

    def solar_terms(self, moment: datetime):
        return self.raw_store.solar_terms(moment)

    def solar_record(self, day: date) -> dict:
        record = self.raw_store.solar_record(day)
        metadata = self.raw_store.metadata() if record.get("sDate") in _BY_SOLAR else {}
        return apply_correction(record, metadata)

    def lunar_record(self, year: int, month: int, day: int, leap: bool | int) -> dict:
        if (
            any(type(value) is not int for value in (year, month, day))
            or not 1 <= month <= 12
            or not 1 <= day <= 30
            or type(leap) not in (bool, int)
            or leap not in (0, 1)
        ):
            raise ManseDataError("invalid_lunar_date", "음력 날짜와 윤달 여부를 확인해 주세요.")
        corrections = _BY_LUNAR.get((year, month, day))
        if corrections is None:
            return self.raw_store.lunar_record(year, month, day, leap)
        metadata = self.raw_store.metadata()
        _verify_source(metadata)
        candidates = self.raw_store.lunar_candidates(year, month, day)
        if any(sum(record.get("sDate") == correction.solar_date for record in candidates) != 1
               for correction in corrections):
            raise ManseDataError("manse_unavailable", UNAVAILABLE)
        rows = [apply_correction(record, metadata) for record in candidates]
        selected = [record for record in rows if record["leafMon_YN"] == int(leap)]
        if len(selected) > 1:
            raise ManseDataError(
                "ambiguous_lunar_date", "같은 음력 날짜의 양력 후보가 중복되어 날짜를 확정할 수 없습니다."
            )
        if not selected:
            raise ManseDataError("invalid_lunar_date", "해당 음력 날짜의 원본 만세력 자료가 없습니다.")
        return selected[0]

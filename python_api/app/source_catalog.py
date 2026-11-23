"""CR-015: source availability in service guides, without database calls or rows."""

import json
from pathlib import Path

from app.source_archive import VERIFIED_TABLE_ALIASES

REGISTRY_PATH = Path(__file__).with_name("data") / "fortune_archive_registry.json"
_cached: tuple[int, int, dict] | None = None
API_TABLES = {"yearly": ["yearfortune"], "monthly": ["monthfor"],
              "compatibility": ["tbAisyo"],
              "lifetime": ["tbSaju_private", "tbSaju_dangsaju", "tbSaju_otherunse"],
              "wealth": ["Moneyluck"], "love": ["tbSajuMaster_mobile1"]}
CANDIDATES = {
    "yearfortune": ["yearfortune del", "TB_yearLuck"],
    "monthfor": ["TB_MonthFor del", "TB_monLuck"],
    "blood": ["TB_bloodTypeLuck"],
    "birthluck": ["TB_birthDayLuck"],
    "stoneluck": ["TB_birthStoneLuck"],
    "tbSaju_dangsaju": ["TB_Saju_DangSaju"],
    "Moneyluck": ["TB_MoneyLuck"],
}


def registry_snapshot() -> dict:
    """Public metadata only. This does not attest the current server connection."""
    global _cached
    try:
        stamp = REGISTRY_PATH.stat()
        if _cached is not None and _cached[:2] == (stamp.st_mtime_ns, stamp.st_size):
            return _cached[2]
        value = json.loads(REGISTRY_PATH.read_bytes())
        if not isinstance(value, dict) or value.get("format") != "woonari.fortune-archive.v1":
            raise ValueError
        tables = value.get("tables")
        if not isinstance(tables, list) or any(
            not isinstance(t, dict) or not isinstance(t.get("source_table"), str)
            or type(t.get("row_count")) is not int or t["row_count"] < 0 for t in tables
        ):
            raise ValueError
        _cached = (stamp.st_mtime_ns, stamp.st_size, value)
        return value
    except (OSError, ValueError, TypeError, KeyError):
        return {"tables": []}


def service_archive_status(item: dict) -> dict:
    registry = registry_snapshot()
    tables = {t["source_table"].casefold(): t for t in registry["tables"]}
    aliases = {a.casefold(): b for a, b in VERIFIED_TABLE_ALIASES.items()}
    candidates = {a.casefold(): b for a, b in CANDIDATES.items()}
    names = list(API_TABLES.get(item.get("api_kind"), []))
    for dependency in item.get("dependencies", []):
        if isinstance(dependency.get("name"), str):
            names.append(dependency["name"])
        for field in dependency.get("calculation_fields", []):
            if isinstance(field.get("table"), str):
                names.append(field["table"])
    results = []
    for name in dict.fromkeys(names):
        alias = aliases.get(name.casefold())
        spec = tables.get((alias or name).casefold())
        if spec is not None:
            results.append({
                "requested_table": name, "source_table": spec["source_table"],
                "row_count": spec["row_count"],
                "status": "restored_definition" if spec["row_count"] else "restored_empty",
                "lookup_mapping": "verified" if alias is not None else "not_verified",
            })
        else:
            matches = [tables[c.casefold()] for c in candidates.get(name.casefold(), [])
                       if c.casefold() in tables]
            results.append({
                "requested_table": name, "status": "not_found_exact",
                "lookup_mapping": "not_verified",
                "candidates": [{"source_table": c["source_table"], "row_count": c["row_count"]}
                               for c in matches],
            })
    return {
        "basis": "backup_registry_snapshot", "actual_connection_checked": False,
        "tables": results, "status_path": "/v1/source-data",
        "service_key_coverage": (
            "source_text_keys_absent_general_advice_only"
            if item.get("id") in {"carluck", "hpluck", "jusoluck"} and tables
            else "not_checked_in_catalog"
        ),
        "note": "복원된 행과 서비스별 계산 완료는 별개입니다. 현재 연결·행 검증은 실행 또는 전체 복원 자료 조회에서 확인합니다.",
    }

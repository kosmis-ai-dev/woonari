"""Read-only commercial ASP provenance hashes, or explicit frozen provenance.

No SQL configuration is included. A snapshot fallback preserves recorded byte
hashes; it does not claim to verify original files absent from a Python export.
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [
    *[
        f"old/unse/{name}/main_end.asp"
        for name in (
            "todayluck",
            "weekluck",
            "monthluck",
            "2014yearluck",
            "lifeluck",
            "moneyluck",
            "carrerluck",
            "loveluck",
            "fatewedluck",
            "bioluck",
        )
    ],
    "function/function.asp",
    "function/valueDef.asp",
    "function/dokebi.asp",
    "function/dotong_function.asp",
    "function/b_include/_SajuManseryuk.asp",
    "function/b_include/lib_sajumaster.asp",
    "function/b_include/_detail_lib.asp",
]


def manifest():
    missing = [path for path in SOURCES if not (ROOT / path).is_file()]
    snapshot = None
    if missing:
        try:
            from .source_inventory import load_snapshot
        except ImportError:
            from source_inventory import load_snapshot
        snapshot = load_snapshot()
    return {
        "change": "CR-001",
        "baseline": "2026-11-02",
        "scope": "Provided source snapshot, not independently verified deployed server version",
        "source_verification": "frozen-source-inventory" if missing else "original-source-files",
        "sources": [
            {"path": path, "sha256": (
                hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                if (ROOT / path).is_file() else snapshot["files"][path]["sha256"]
            )}
            for path in SOURCES
        ],
    }


if __name__ == "__main__":
    print(json.dumps(manifest(), ensure_ascii=False, indent=2))

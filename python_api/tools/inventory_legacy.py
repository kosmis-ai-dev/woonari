"""Read-only inventory. Run from python_api: python tools/inventory_legacy.py.

No ASP, SQL or COM is executed; no original DB credentials are read or printed.
The output is source-reference information, NOT evidence that a module was fully ported.
"""

import json
import re
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORTUNES = ROOT / "old" / "unse"
PORTS = {
    "todayluck": ("daily", "asp-commercial"),
    "weekluck": ("weekly", "asp-commercial"),
    "bioluck": ("biorhythm", "asp-commercial"),
    "monthluck": ("monthly", "asp-commercial"),
    "2014yearluck": ("yearly", "requires-original-dependency"),
    "lifeluck": ("lifetime", "asp-commercial"),
    "moneyluck": ("wealth", "asp-commercial"),
    "carrerluck": ("career", "requires-original-dependency"),
    "loveluck": ("love", "asp-commercial"),
    "fatewedluck": ("compatibility", "requires-original-dependency"),
}


def inventory():
    if not FORTUNES.is_dir():
        try:
            from .source_inventory import load_snapshot
        except ImportError:
            from source_inventory import load_snapshot
        result = deepcopy(load_snapshot()["legacy_inventory"])
        result["source_verification"] = "frozen-source-inventory"
        result["note"] += " Source files are absent; these are frozen source-reference facts, not verification of present source files."
        return result
    rows = []
    for folder in sorted(FORTUNES.iterdir()):
        if not folder.is_dir():
            continue
        tables, components, includes = set(), set(), set()
        files = sorted(folder.rglob("*.asp"))
        for file in files:
            data = file.read_bytes()
            try:
                source = data.decode("utf-8")
            except UnicodeDecodeError:
                source = data.decode("cp949", errors="replace")
            tables.update(
                x.lower() for x in re.findall(r"\bfrom\s+\[?([a-zA-Z_][a-zA-Z_0-9]*)", source, re.I)
            )
            components.update(
                re.findall(
                    r'(?:CreateObject|PROGID)\s*(?:\(\s*["\x27]|=\s*["\x27]?)([a-zA-Z0-9_.]+)',
                    source,
                    re.I,
                )
            )
            includes.update(
                re.findall(
                    r'<!--\s*#include\s+(?:virtual|file)\s*=\s*["\x27]([^"\x27]+)', source, re.I
                )
            )
        api, method = PORTS.get(folder.name, (None, "not-ported"))
        rows.append(
            {
                "directory": str(folder.relative_to(ROOT)),
                "asp_files": len(files),
                "entry_candidates": [
                    str(f.relative_to(ROOT))
                    for f in files
                    if f.name in {"main_end.asp", "main.asp", "print.asp"}
                ],
                "table_references_heuristic": sorted(tables),
                "components": sorted(components),
                "includes": sorted(includes),
                "api_kind": api,
                "method": method,
            }
        )
    return {
        "schema_version": 2,
        "source_verification": "original-source-files",
        "note": "CR-009/T-018: original ASP decision/text-selector ports. Seven API kinds ready using the supplied tb_manse DB source (73,414 daily rows, 1900-2100; public API remains 1900-2050). The official runtime queries the imported MySQL woonari.tb_manse with no automatic calendar fallback. Yearly/career/compatibility still need original non-text dependencies. Remaining directories, including interlife, are not ported. Static dependency references are heuristic, not runtime tracing.",
        "directories": rows,
    }


if __name__ == "__main__":
    print(json.dumps(inventory(), ensure_ascii=False, indent=2))

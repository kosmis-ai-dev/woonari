"""Extract actual VBScript literals, including escaped quotes, without executing ASP.

This snapshot preserves observable irregularities in the Chinese-character half;
it must not normalize a missing comma/escaped double quote into an intended value.
"""

import json
import re
from pathlib import Path


def parse_vb_string_array(expression: str) -> list[str]:
    """Parse only static Array(...) string values: VB `""` means one literal quote."""
    expression = re.sub(r"_\s*\r?\n", "", expression).strip()
    values = []
    end = 0
    for token in re.finditer(r'"((?:[^\"]|\"\")*)"', expression):
        gap = expression[end : token.start()].strip()
        if gap != ("," if values else ""):
            raise ValueError("Only comma-separated VB string literals are supported")
        values.append(token.group(1).replace('""', '"'))
        end = token.end()
    if not values or expression[end:].strip():
        raise ValueError("Invalid or unsupported VB string array expression")
    return values


def extract_tables(source: str) -> dict:
    tables = {"stems": {}, "branches": {}}
    for kind, key, count in (("Chon", "stems", 10), ("Zone", "branches", 12)):
        for i, stem in enumerate("甲乙丙丁戊己庚辛壬癸", 1):
            block = re.search(
                rf"function compare{kind}{i}\(s\)(.*?)end function", source, re.S | re.I
            )[1]
            symbols = parse_vb_string_array(re.search(r"baseData = array\((.*?)\)", block)[1])[
                :count
            ]
            gods = parse_vb_string_array(re.search(r"arSixGod = array\((.*?)\)", block)[1])[:count]
            if len(symbols) != count or len(gods) != count:
                raise ValueError(f"Missing source table values for compare{kind}{i}")
            tables[key][stem] = dict(zip(symbols, gods))
    return {
        "source": "function/function.asp:469-650",
        "literal_semantics": "VBScript doubled double quotes are one embedded quote; no lexical repairs",
        "source_irregularities": [
            {
                "day_stem": "辛",
                "branch": "辰",
                "value": '인수"비견',
                "reason": 'compareZone8: source Array contains "인수""비견" as one VB string',
            }
        ],
        **tables,
    }


def cli_output(root: Path | None = None) -> dict:
    """Report fresh extraction or an explicitly identified frozen rule fixture."""
    root = root or Path(__file__).resolve().parents[2]
    original = root / "function/function.asp"
    if original.is_file():
        result = extract_tables(original.read_bytes().decode("cp949"))
        result["provenance"] = {"mode": "original-source-files", "fresh_extraction": True}
        return result
    fixture_path = "python_api/tests/fixtures/legacy_ten_gods.json"
    result = json.loads((root / fixture_path).read_text(encoding="utf-8"))
    try:
        from .source_inventory import load_snapshot
    except ImportError:
        from source_inventory import load_snapshot
    result["provenance"] = {
        "mode": "frozen-rule-fixture", "fresh_extraction": False,
        "fixture": fixture_path,
        "source_sha256": load_snapshot()["files"]["function/function.asp"]["sha256"],
        "note": "Original ASP is absent; this is the previously audited literal fixture, not a fresh extraction.",
    }
    return result


if __name__ == "__main__":
    print(json.dumps(cli_output(), ensure_ascii=False, indent=2))

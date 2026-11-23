"""CR-012/T-025: portable, content-free provenance for the supplied ASP source.

Run ``python tools/source_inventory.py --freeze`` from python_api while the
original source is present. The snapshot records hashes, line counts and menu /
directory facts; it never copies ASP, XML, SQL, or connection-string contents.
Frozen provenance cannot verify source files which are no longer distributed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = Path(__file__).with_name("data") / "legacy_source_inventory.json"
ASP_ROOTS = ("old", "function", "include", "sub")


def tree_sha256(files: dict[str, dict]) -> str:
    """Hash path + byte hash + line count, independent of JSON formatting."""
    encoded = "".join(
        f"{path}\0{entry['sha256']}\0{entry['lines']}\n"
        for path, entry in sorted(files.items())
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_snapshot(path: Path = SNAPSHOT) -> dict:
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("schema_version") != 1 or snapshot.get("source_tree_sha256") != tree_sha256(snapshot["files"]):
        raise ValueError("The frozen source inventory is invalid.")
    return snapshot


def freeze(root: Path = ROOT) -> dict:
    """Build only from the supplied original files, never from another snapshot."""
    # Restrict enumeration to original source roots. Local credentials, caches,
    # publication worktrees and virtual environments are never traversed.
    originals = set(root.glob("*.asp"))
    for directory in ASP_ROOTS:
        originals.update(
            path for path in (root / directory).rglob("*")
            if path.is_file() and path.suffix.lower() == ".asp"
        )
    fortunes = root / "old/unse"
    xml_path = root / "old/xmlpath/unse.xml"
    if not originals or not fortunes.is_dir() or not xml_path.is_file():
        raise ValueError("Original ASP source and its XML menu are required to freeze provenance.")

    referenced_paths = {
        "old/xmlpath/unse.xml",
        "old/unse/interlife/UNSE_DATA/data/div24.dat",
        "old/unse/interlife/UNSE_DATA/data/suntolun.dat",
        "old/unse/interlife/UNSE_DATA/data/YunDat.dat",
        "old/unse/interlife/data/moneyDATA.dat",
        "old/unse/interlife/UNSE_DATA/etc/tranceJS.js",
    }
    for name in ("source_manifest.json", "catalog_source_manifest.json"):
        manifest = json.loads((root / "python_api/docs" / name).read_text(encoding="utf-8"))
        referenced_paths.update(entry["path"] for entry in manifest["sources"])
    catalog = json.loads((root / "python_api/app/data/legacy_services.json").read_text(encoding="utf-8"))
    items = catalog["items"] if "items" in catalog else catalog["services"]
    for item in items:
        referenced_paths.update(source["path"] for source in item["sources"])
        for issue in item["issues"]:
            referenced_paths.update(source["path"] for source in issue["sources"])
    originals.update(root / path for path in referenced_paths)
    files = {}
    for path in sorted(originals):
        data = path.read_bytes()
        files[path.relative_to(root).as_posix()] = {
            "sha256": hashlib.sha256(data).hexdigest(), "lines": len(data.splitlines()),
        }
    xml = xml_path.read_bytes().decode("cp949")
    # Import only after defining the snapshot helpers so direct script execution
    # and package imports both keep inventory_legacy's fallback acyclic.
    try:
        from .inventory_legacy import inventory
    except ImportError:
        from inventory_legacy import inventory
    return {
        "schema_version": 1,
        "change": "CR-012/T-025",
        "scope": "Frozen metadata of the supplied source; not an independently verified deployed server version.",
        "contents": "Paths, SHA-256 byte hashes, line counts, directory/menu facts and heuristic reference identifiers only. No source bodies or credentials.",
        "asp_roots": list(ASP_ROOTS),
        "source_tree_sha256": tree_sha256(files),
        "files": files,
        "unse_directories": sorted(path.relative_to(root).as_posix() for path in fortunes.iterdir() if path.is_dir()),
        "xml_menu": {
            "source": "old/xmlpath/unse.xml",
            "declarations": [{"content_code": node.attrib["id"], "original_name": node.attrib["txt"]}
                             for node in ElementTree.fromstring(xml)],
        },
        "legacy_inventory": inventory(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true", help="Create a content-free snapshot from original source files.")
    options = parser.parse_args()
    if options.freeze:
        snapshot = freeze()
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"files": len(snapshot["files"]), "source_tree_sha256": snapshot["source_tree_sha256"]}))
    else:
        snapshot = load_snapshot()
        print(json.dumps({"files": len(snapshot["files"]), "source_tree_sha256": snapshot["source_tree_sha256"]}))

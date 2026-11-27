"""CR-012 / T-025: publish the independent Python project.

Only value-free findings are written to PUBLICATION.json. This command neither
logs in nor pushes. Credentials are never passed as command-line arguments.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from project_context import clean_env
from repository_secrets import redact

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "https://github.com/kosmis-ai-dev/woonari.git"
BRANCH = "import/asp-python-20261103"
SKIP_DIRECTORIES = {
    ".git", ".publish", ".publish-tools", ".local", ".venv", "venv", "__pycache__",
    ".pytest_cache", ".ruff_cache",
}
SKIP_FILES = {
    ".DS_Store": "OS metadata",
    "sftp-config.json": "live SFTP configuration",
    "WS_FTP.LOG": "operational FTP log",
}
SKIP_PATTERNS = {
    "*.mdb": "unreviewed Access database; possible user records",
    "*.accdb": "unreviewed Access database; possible user records",
    "*.sublime-workspace": "local editor state",
    "*.pyc": "Python cache", "*.pyo": "Python cache",
    "*.pem": "key/certificate material", "*.key": "key material",
    "*.pfx": "key/certificate material", "*.p12": "key/certificate material",
}
TEXT_EXTENSIONS = {
    ".asp", ".inc", ".xml", ".json", ".txt", ".js", ".mjs", ".html",
    ".htm", ".css", ".vbs", ".config", ".ini", ".yaml", ".yml", ".sql",
    ".md", ".py", ".toml", ".csv", ".dat", ".bak", ".project",
}
PUBLICATION_CODE = {
    "tools/repository_secrets.py", "tools/test_repository_secrets.py",
    "tools/prepare_github.py", "tools/test_prepare_github.py",
    "tools/project_context.py", "tools/test_project_context.py",
    "tools/isolated_runtime.py", "tools/test_isolated_runtime.py",
    "tools/isolated_git.py", "tools/test_isolated_git.py",
    "tools/isolated_aws.py", "tools/test_isolated_aws.py",
    "tools/test_isolated_db.py",
    "tools/test_manse_import.py", "tools/test_mysql_manse.py",
    "tools/test_mysql_restored_fortune.py",
    "tools/test_mysql_fortune_archive.py",
    "tools/test_isolated_bedrock.py",
    "tools/test_bedrock_key.py",
    "tools/test_auth_setup.py",
    "tools/test_python_env_migration.py",
    "tools/aws_cli_entry.py",
    "tools/woonari_git_credential.py",
}
LFS_FILES: list[str] = []
INVENTORY = "python_api/tools/data/legacy_source_inventory.json"
MANIFESTS = [
    "python_api/docs/source_manifest.json", "python_api/docs/catalog_source_manifest.json",
]


def exclusion(path: Path) -> str | None:
    relative = path.relative_to(ROOT)
    if any(part in SKIP_DIRECTORIES or part.endswith(".egg-info") for part in relative.parts):
        return "local environment/cache/publication checkout"
    name = relative.name
    if name in SKIP_FILES:
        return SKIP_FILES[name]
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return "runtime environment secrets"
    if relative.parts[0] == "_gabia" or relative.as_posix().startswith("old/log/injection_log/"):
        return "operational usage/security log"
    if relative.as_posix().startswith(("python_api/build/", "python_api/dist/")):
        return "Python build output"
    for pattern, reason in SKIP_PATTERNS.items():
        if fnmatch.fnmatch(name.lower(), pattern):
            return reason
    if path.is_symlink():
        return "symlink; external targets are not copied"
    return None


def source_files():
    # Avoid entering ignored trees, especially the publication destination itself.
    pending = [ROOT]
    while pending:
        folder = pending.pop()
        for path in sorted(folder.iterdir()):
            reason = exclusion(path)
            if path.is_dir() and not path.is_symlink():
                if not reason:
                    pending.append(path)
            elif path.is_file() or path.is_symlink():
                yield path, reason


def sanitize(data: bytes, relative: str):
    # These files contain deliberately fake security-test values and regex rules.
    # The supplied dashboard tools are copied byte-for-byte, never modified.
    if relative in PUBLICATION_CODE or relative.startswith((".project/_tools/", "python_api/tests/")):
        return data, []
    suffix = Path(relative).suffix.lower()
    if suffix not in TEXT_EXTENSIONS and relative != "readme.txt":
        return data, []
    if b"\0" in data[:8192]:
        return data, []
    return redact(data, relative)


def publication_bytes(data: bytes, relative: str):
    sanitized, findings = sanitize(data, relative)
    if findings and (relative.endswith(".py") or relative.startswith("python_api/app/")):
        raise RuntimeError(f"Runtime source requires credential review before publication: {relative}")
    return sanitized, findings


def asp_code_structure(data: bytes) -> list[bytes]:
    """Compare server-side control flow independently of credential literals."""
    result = []
    for code in re.findall(rb"<%(.*?)%>", data, re.DOTALL):
        # VB doubles a quote within a string. Mask strings before comments so an
        # apostrophe inside a literal cannot hide a changed expression.
        code = re.sub(rb'"(?:[^\"]|"\")*"', b'""', code)
        code = re.sub(rb"'[^\r\n]*", b"", code)
        code = re.sub(rb"(?im)(^|:)\s*Rem\b[^\r\n]*", rb"\1", code)
        result.append(code)
    return result


def refresh_manifests(destination: Path):
    """Original hashes remain provenance after ASP is privately archived."""
    inventory_path = destination / INVENTORY
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    # The fixture is value-free metadata, not copied source or a runtime input.
    entries = inventory["files"]
    indexed = entries if isinstance(entries, dict) else {entry["path"]: entry for entry in entries}
    for relative in MANIFESTS:
        metadata = json.loads((destination / relative).read_text(encoding="utf-8"))
        for source in metadata["sources"]:
            assert indexed[source["path"]]["sha256"] == source["sha256"], source["path"]


def reject_destination_symlinks(destination: Path):
    # Never write through a stale checkout link before the mirror prunes it.
    if destination.is_symlink() or any(path.is_symlink() for path in destination.rglob("*")):
        raise RuntimeError("Publication checkout contains a symlink; no files were written.")


def prune_publication(destination: Path, expected: set[str]):
    """Mirror authorized source removals in this derived checkout, preserving Git."""
    for path in sorted(destination.iterdir()):
        if path.name == ".git":
            continue
        if path.is_dir() and not path.is_symlink():
            for child in sorted(path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
                relative = child.relative_to(destination).as_posix()
                if child.is_symlink() or child.is_file():
                    if relative not in expected:
                        child.unlink()
                elif child.is_dir() and not any(child.iterdir()):
                    child.rmdir()
            if not any(path.iterdir()):
                path.rmdir()
        elif path.relative_to(destination).as_posix() not in expected:
            path.unlink()


def assert_publication_paths(destination: Path, expected: set[str]):
    """Reject stale/unexpected files, including tracked files now ignored by Git."""
    if (destination / ".git").is_dir():
        result = subprocess.run(
            ["git", "-C", str(destination), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            check=True, capture_output=True, env=clean_env(),
        )
        actual = {
            path.decode("utf-8") for path in result.stdout.split(b"\0")
            if path and ((destination / path.decode("utf-8")).exists()
                         or (destination / path.decode("utf-8")).is_symlink())
        }
    else:
        actual = {
            path.relative_to(destination).as_posix()
            for path in destination.rglob("*")
            if path.is_file() and not exclusion(ROOT / path.relative_to(destination))
        }
    extra = actual - expected - {"PUBLICATION.json"}
    if extra:
        raise RuntimeError("Unexpected publication files: " + ", ".join(sorted(extra)))


def prepare(destination: Path):
    destination = destination.resolve()
    if destination != ROOT / ".publish/woonari":
        raise SystemExit("Use the dedicated .publish/woonari checkout; originals cannot be overwritten.")
    destination.mkdir(parents=True, exist_ok=True)
    reject_destination_symlinks(destination)
    copied, excluded, changed = [], [], []
    for source, reason in source_files():
        relative = source.relative_to(ROOT).as_posix()
        if reason:
            excluded.append({"path": relative, "reason": reason})
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        original = source.read_bytes()
        sanitized, findings = publication_bytes(original, relative)
        if re.findall(rb"\r\n|\r|\n", original) != re.findall(rb"\r\n|\r|\n", sanitized):
            raise RuntimeError(f"Source line endings changed: {relative}")
        target.write_bytes(sanitized)
        shutil.copystat(source, target)
        copied.append({"path": relative, "bytes": len(sanitized)})
        if findings:
            changed.append({
                "path": relative,
                "lines": original.count(b"\n") + 1,
                "findings": [{"kind": f["kind"], "line": f["line"]} for f in findings],
                "published_sha256": hashlib.sha256(sanitized).hexdigest(),
            })
    refresh_manifests(destination)
    prune_publication(destination, {item["path"] for item in copied})
    report = {
        "change": "CR-012", "task": "T-025",
        "prepared_date": datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat(),
        "repository": REMOTE, "branch": BRANCH,
        "scope": "Python API, source-derived rules, frozen provenance, tests, tools and project board. Original ASP and site assets are excluded.",
        "files": len(copied), "bytes": sum(item["bytes"] for item in copied),
        "asp_files": sum(item["path"].lower().endswith(".asp") for item in copied),
        "credential_values_stored_in_report": False,
        "original_source_modified": False,
        "redacted_files": changed,
        "excluded": excluded,
        "excluded_directory_rules": sorted(SKIP_DIRECTORIES | {"_gabia", "old/log/injection_log", "python_api/build", "python_api/dist"}),
        "exclusion_counts": dict(Counter(item["reason"] for item in excluded)),
        "lfs": [{"path": path, "bytes": (destination / path).stat().st_size, "sha256": hashlib.sha256((destination / path).read_bytes()).hexdigest()} for path in LFS_FILES],
        "validation": {
            "line_endings": "preserved", "active_asp_files": 0,
            "archived_provenance_asp_files": 1445,
            "source_manifest": "original hashes cross-checked with frozen provenance; ASP absent",
            "python_tests": "run separately in the publication checkout before push",
        },
    }
    (destination / "PUBLICATION.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files":report["files"], "asp_files":report["asp_files"], "redacted_files":len(changed), "excluded_files":len(excluded), "lfs_files":len(LFS_FILES)}, ensure_ascii=False))


def verify(destination: Path):
    reject_destination_symlinks(destination)
    report = json.loads((destination / "PUBLICATION.json").read_text(encoding="utf-8"))
    asp_files = sum(1 for source, reason in source_files() if not reason and source.suffix.lower() == ".asp")
    assert report["asp_files"] == asp_files == 0
    residual = []
    checked = 0
    expected_paths = set()
    for source, reason in source_files():
        if reason:
            continue
        relative = source.relative_to(ROOT).as_posix()
        expected_paths.add(relative)
        target = destination / relative
        assert target.is_file(), relative
        original = source.read_bytes()
        expected, _ = publication_bytes(original, relative)
        actual = target.read_bytes()
        assert actual == expected, f"Unexpected publication change: {relative}"
        if relative.lower().endswith(".asp"):
            assert asp_code_structure(original) == asp_code_structure(actual), f"ASP expression changed outside a string/comment: {relative}"
        _, findings = sanitize(actual, relative)
        residual.extend({"path": f["path"], "line": f["line"], "kind": f["kind"]} for f in findings)
        checked += 1
    assert_publication_paths(destination, expected_paths)
    refresh_manifests(destination)
    if residual:
        print(json.dumps(residual, ensure_ascii=False))
        raise SystemExit("Unresolved credential patterns in publication copy")
    print(json.dumps({"verified_files": checked, "asp_files": asp_files, "residual_credential_patterns": 0, "source_manifests": "matched_frozen_provenance"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    destination = ROOT / ".publish/woonari"
    verify(destination) if args.verify else prepare(destination)

"""CR-012/T-025: provenance tools remain honest without distributed ASP files."""

import json
from pathlib import Path

import pytest

from tools import inventory_legacy, source_manifest
from tools.extract_rule_fixture import cli_output
from tools.source_inventory import load_snapshot


def test_snapshot_rejects_changed_file_metadata(tmp_path):
    snapshot = load_snapshot()
    snapshot["files"]["function/function.asp"]["lines"] += 1
    altered = tmp_path / "altered.json"
    altered.write_text(json.dumps(snapshot), encoding="utf-8")
    with pytest.raises(ValueError, match="frozen source inventory"):
        load_snapshot(altered)


def test_source_manifest_uses_recorded_hashes_when_originals_are_absent(monkeypatch, tmp_path):
    monkeypatch.setattr(source_manifest, "ROOT", tmp_path)
    result = source_manifest.manifest()
    assert result["source_verification"] == "frozen-source-inventory"
    snapshot = load_snapshot()
    assert result["sources"] == [
        {"path": path, "sha256": snapshot["files"][path]["sha256"]}
        for path in source_manifest.SOURCES
    ]


def test_inventory_returns_frozen_facts_when_originals_are_absent(monkeypatch, tmp_path):
    monkeypatch.setattr(inventory_legacy, "FORTUNES", tmp_path / "old/unse")
    result = inventory_legacy.inventory()
    assert result["source_verification"] == "frozen-source-inventory"
    assert result["directories"] == load_snapshot()["legacy_inventory"]["directories"]
    assert "not verification of present source files" in result["note"]


def test_rule_fixture_cli_marks_an_absent_source_as_frozen(tmp_path):
    fixture = Path(__file__).with_name("fixtures") / "legacy_ten_gods.json"
    target = tmp_path / "python_api/tests/fixtures/legacy_ten_gods.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(fixture.read_bytes())
    output = cli_output(tmp_path)
    provenance = output.pop("provenance")
    assert output == json.loads(fixture.read_text(encoding="utf-8"))
    assert provenance["mode"] == "frozen-rule-fixture"
    assert provenance["fresh_extraction"] is False
    assert provenance["source_sha256"] == load_snapshot()["files"]["function/function.asp"]["sha256"]

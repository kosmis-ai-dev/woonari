"""Publication must not pick up stale secrets or alter synthetic test fixtures."""

import json
import subprocess

import prepare_github
import pytest
from prepare_github import (
    ROOT,
    asp_code_structure,
    assert_publication_paths,
    exclusion,
    prune_publication,
    publication_bytes,
    reject_destination_symlinks,
    sanitize,
)


def git(folder, *args):
    subprocess.run(["git", "-C", str(folder), *args], check=True, capture_output=True)


def test_unexpected_untracked_file_is_rejected(tmp_path):
    git(tmp_path, "init")
    (tmp_path / "source.asp").write_text("<% Response.Write 1 %>")
    (tmp_path / "forgotten-secret.txt").write_text("synthetic stale file")
    with pytest.raises(RuntimeError, match="forgotten-secret.txt"):
        assert_publication_paths(tmp_path, {"source.asp"})


def test_tracked_file_is_rejected_even_if_it_is_now_ignored(tmp_path):
    git(tmp_path, "init")
    (tmp_path / "old-connection.env").write_text("synthetic stale file")
    git(tmp_path, "add", "old-connection.env")
    (tmp_path / ".gitignore").write_text("*.env\n")
    with pytest.raises(RuntimeError, match="old-connection.env"):
        assert_publication_paths(tmp_path, {".gitignore"})


def test_source_and_allowed_ignored_cache_can_coexist(tmp_path):
    git(tmp_path, "init")
    (tmp_path / ".gitignore").write_text("__pycache__/\n")
    (tmp_path / "source.asp").write_text("<% Response.Write 1 %>")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__/local.pyc").write_bytes(b"cache")
    (tmp_path / "PUBLICATION.json").write_text("{}")
    assert_publication_paths(tmp_path, {".gitignore", "source.asp"})


def test_python_only_sync_removes_old_source_and_preserves_git(tmp_path):
    git(tmp_path, "init")
    (tmp_path / "old").mkdir()
    (tmp_path / "old/source.asp").write_text("synthetic old source")
    git(tmp_path, "add", "old/source.asp")
    (tmp_path / "app.py").write_text("print('current')")
    prune_publication(tmp_path, {"app.py"})
    assert (tmp_path / ".git").is_dir()
    assert (tmp_path / "app.py").is_file()
    assert not (tmp_path / "old").exists()
    # Pending tracked deletions are allowed; existing unexpected files are not.
    assert_publication_paths(tmp_path, {"app.py"})


def test_existing_checkout_symlink_is_rejected_before_copying(tmp_path):
    outside = tmp_path / "other-project"
    outside.mkdir()
    original = outside / "app.py"
    original.write_text("synthetic unrelated source")
    destination = tmp_path / "publication"
    destination.mkdir()
    (destination / "tools").symlink_to(outside, target_is_directory=True)
    with pytest.raises(RuntimeError, match="symlink"):
        reject_destination_symlinks(destination)
    assert original.read_text() == "synthetic unrelated source"


def test_verification_rejects_removed_provenance_entries(tmp_path, monkeypatch):
    source_root, destination = tmp_path / "source", tmp_path / "publication"
    expected = {"sources": [{"path": "original.asp", "sha256": "0" * 64}]}
    relatives = [*prepare_github.MANIFESTS, prepare_github.INVENTORY]
    for relative in relatives:
        original, published = source_root / relative, destination / relative
        original.parent.mkdir(parents=True, exist_ok=True)
        published.parent.mkdir(parents=True, exist_ok=True)
        value = ({"files": {"original.asp": {"sha256": "0" * 64}}}
                 if relative == prepare_github.INVENTORY else expected)
        original.write_text(json.dumps(value))
        published.write_text(json.dumps(value if relative == prepare_github.INVENTORY else {"sources": []}))
    (destination / "PUBLICATION.json").write_text('{"asp_files": 0}')
    monkeypatch.setattr(prepare_github, "ROOT", source_root)
    monkeypatch.setattr(prepare_github, "source_files", lambda: iter(
        (source_root / relative, None) for relative in relatives
    ))
    with pytest.raises(AssertionError, match="Unexpected publication change"):
        prepare_github.verify(destination)


def test_runtime_logic_is_never_silently_changed_by_credential_sanitization():
    source = b'api_key = "synthetic-not-a-real-key"\n'
    with pytest.raises(RuntimeError, match="credential review") as error:
        publication_bytes(source, "python_api/app/config.py")
    assert "synthetic-not-a-real-key" not in str(error.value)
    assert publication_bytes(source, "python_api/tests/test_fixture.py") == (source, [])


def test_test_fixtures_are_preserved_but_live_settings_are_redacted():
    fixture = b'api_key = "synthetic-fixture-value"\r\n'
    assert sanitize(fixture, "python_api/tests/test_fixture.py") == (fixture, [])
    sanitized, findings = sanitize(fixture, "settings.py")
    assert sanitized != fixture
    assert findings
    assert sanitized.count(b"\r\n") == 1
    assert exclusion(ROOT / "old/uncatch.mdb")
    assert exclusion(ROOT / "python_api/.env")
    assert exclusion(ROOT / "python_api/.env.example") is None
    assert exclusion(ROOT / ".local/woonari/config.json")
    assert exclusion(ROOT / ".local/woonari/aws/credentials")
    assert exclusion(ROOT / ".local/woonari/github/hosts.yml")
    assert exclusion(ROOT / ".local/woonari/api.env")


def test_asp_structure_allows_literal_replacement_but_rejects_expression_changes():
    source = b'<% conn.Open "server=" & host & ";PWD=" & password\r\n x="synthetic" \' comment\r\n%>'
    literal_change = source.replace(b'"synthetic"', b'"REDACTED"').replace(b"comment", b"other comment")
    expression_change = source.replace(b' & password', b' & another_variable')
    assert asp_code_structure(source) == asp_code_structure(literal_change)
    assert asp_code_structure(source) != asp_code_structure(expression_change)

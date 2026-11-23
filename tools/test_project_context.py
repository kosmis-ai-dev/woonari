"""Check the boundary that keeps inherited accounts out of project commands."""

import copy
import json
import os

import project_context as context
import pytest


def test_clean_env_removes_inherited_accounts_and_process_configuration(monkeypatch):
    injected = {
        "OPENAI_API_KEY": "synthetic-other-project", "OPENAI_MODEL": "other-model",
        "OPENAI_BASE_URL": "https://other.invalid", "OPENAI_ORG_ID": "other",
        "OPENAI_PROJECT_ID": "other", "API_KEY": "other", "AWS_ACCESS_KEY_ID": "other",
        "AWS_SECRET_ACCESS_KEY": "other", "AWS_SESSION_TOKEN": "other",
        "AWS_PROFILE": "other", "AWS_CONFIG_FILE": "/other/config",
        "GH_TOKEN": "other", "GITHUB_TOKEN": "other", "GH_CONFIG_DIR": "/other/gh",
        "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "credential.helper",
        "GIT_CONFIG_VALUE_0": "osxkeychain", "GIT_SSH_COMMAND": "ssh",
        "SSH_AUTH_SOCK": "/other/ssh", "PYTHONPATH": "/other/python",
        "VIRTUAL_ENV": "/other/venv", "HTTP_PROXY": "http://other.invalid",
        "HTTPS_PROXY": "http://other.invalid", "SSL_CERT_FILE": "/other/ca",
    }
    for key, value in injected.items():
        monkeypatch.setenv(key, value)
    env = context.clean_env()
    assert not (set(injected) & set(env))
    assert env["GIT_CONFIG_GLOBAL"] == os.devnull
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert "/other/" not in env["PATH"]


@pytest.mark.parametrize("field,value", [
    ("project", "other"), ("api_port", 480), ("api_port", 18101), ("dashboard_port", 9090),
    ("git.login", "email@example.invalid"), ("git.repository", "https://other.invalid/repo"),
    ("aws.account_id", "123"), ("aws.profile", "default"),
])
def test_invalid_identity_and_collision_config_is_rejected(field, value):
    cfg = copy.deepcopy(context.DEFAULTS)
    if "." in field:
        section, key = field.split(".")
        cfg[section][key] = value
    else:
        cfg[field] = value
    with pytest.raises(RuntimeError):
        context.validate_config(cfg)


def test_private_state_does_not_follow_symlink(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / ".local").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(context, "ROOT", root)
    with pytest.raises(RuntimeError, match="symlink"):
        context.private_dir(root / ".local/woonari")


def test_load_config_uses_fixed_port_for_existing_installation(tmp_path, monkeypatch):
    state = tmp_path / ".local/woonari"
    config_file = state / "config.json"
    monkeypatch.setattr(context, "ROOT", tmp_path)
    monkeypatch.setattr(context, "STATE", state)
    monkeypatch.setattr(context, "CONFIG_FILE", config_file)
    previous = {**context.DEFAULTS, "api_port": 18100, "dashboard_port": 18102}
    context.write_private(config_file, json.dumps(previous))

    assert context.load_config() == {**previous, "api_port": 9090}


def test_private_files_are_created_with_owner_only_permissions(tmp_path, monkeypatch):
    monkeypatch.setattr(context, "ROOT", tmp_path)
    path = tmp_path / ".local/woonari/config.json"
    context.write_private(path, "{}\n")
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700

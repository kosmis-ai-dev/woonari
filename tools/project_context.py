"""T-013 / CR-006: private project state and an environment without account fallback."""

from __future__ import annotations

import copy
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".local" / "woonari"
CONFIG_FILE = STATE / "config.json"
API_PORT = 9090
DEFAULTS = {
    "project": "woonari",
    "api_port": API_PORT,
    "dashboard_port": 18101,
    "git": {
        "repository": "https://github.com/kosmis-ai-dev/woonari.git",
        "login": "",
        "name": "",
        "email": "",
    },
    "aws": {"account_id": "", "profile": "woonari", "region": "ap-northeast-2"},
}


def fail(message: str) -> NoReturn:
    raise RuntimeError(message)


def private_dir(path: Path) -> Path:
    path = Path(path)
    if not path.is_relative_to(ROOT / ".local"):
        fail("Private state must stay inside this project's .local directory.")
    current = ROOT
    for part in path.relative_to(ROOT).parts:
        current /= part
        if current.is_symlink():
            fail("Private state cannot use a symlink.")
        current.mkdir(mode=0o700, exist_ok=True)
        current.chmod(0o700)
    return path


def write_private(path: Path, content: str) -> None:
    private_dir(path.parent)
    if path.is_symlink():
        fail("Private files cannot use a symlink.")
    descriptor, name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.chmod(name, 0o600)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def validate_config(config: dict) -> dict:
    if not isinstance(config, dict) or set(config) != set(DEFAULTS):
        fail("Invalid project config keys. Run ./woonari init.")
    if config["project"] != "woonari":
        fail("This configuration does not belong to Woonari.")
    for key in ("git", "aws"):
        section = config[key]
        if not isinstance(section, dict) or set(section) != set(DEFAULTS[key]):
            fail(f"Invalid {key} configuration keys.")
        if any(not isinstance(value, str) or "\n" in value or "\r" in value
               for value in section.values()):
            fail(f"Invalid {key} configuration values.")
    if type(config["api_port"]) is not int or config["api_port"] != API_PORT:
        fail(f"The Woonari API port is fixed at {API_PORT}.")
    dashboard_port = config["dashboard_port"]
    if type(dashboard_port) is not int or not 1024 <= dashboard_port <= 65535:
        fail("The dashboard port must be an integer between 1024 and 65535.")
    if dashboard_port == API_PORT:
        fail(f"Set dashboard_port to a port other than {API_PORT} in {CONFIG_FILE}.")
    if config["git"]["repository"] != DEFAULTS["git"]["repository"]:
        fail("Only the designated Woonari repository is allowed.")
    if config["aws"]["profile"] != "woonari":
        fail("Only the project AWS profile 'woonari' is allowed.")
    account_id = config["aws"]["account_id"]
    if account_id and not re.fullmatch(r"[0-9]{12}", account_id):
        fail("AWS account ID must have 12 digits.")
    login = config["git"]["login"]
    if login and not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", login):
        fail("git.login must be a GitHub username, not an email address.")
    if not re.fullmatch(r"[a-z]{2}(?:-[a-z]+)+-[0-9]+", config["aws"]["region"]):
        fail("Invalid AWS region.")
    return config


def load_config() -> dict:
    private_dir(STATE)
    if not CONFIG_FILE.exists() or CONFIG_FILE.is_symlink():
        fail("Project configuration is missing. Run ./woonari init first.")
    CONFIG_FILE.chmod(0o600)
    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if isinstance(config, dict) and "api_port" in config:
            # Older installations stored a configurable API port.
            config["api_port"] = API_PORT
        return validate_config(config)
    except (ValueError, TypeError):
        fail("Project configuration is invalid; no external account will be used.")


def save_config(config: dict) -> None:
    validate_config(config)
    write_private(CONFIG_FILE, json.dumps(config, ensure_ascii=False, indent=2) + "\n")


def init() -> dict:
    private_dir(STATE)
    if not CONFIG_FILE.exists():
        save_config(copy.deepcopy(DEFAULTS))
    config = load_config()
    env_file = STATE / "api.env"
    if not env_file.exists():
        write_private(env_file, (ROOT / "python_api/.env.example").read_text(encoding="utf-8"))
    for folder in ("aws", "github", "xdg", "bin", "logs"):
        private_dir(STATE / folder)
    # Register the installed Node executable once; child processes never inherit
    # the caller's PATH (which may point at another project's virtualenv).
    node_link = STATE / "bin/node"
    if not node_link.exists() and not node_link.is_symlink():
        node = shutil.which("node")
        if node:
            node_link.symlink_to(Path(node).resolve())
    for name in ("config", "credentials"):
        path = STATE / "aws" / name
        if not path.exists():
            write_private(path, "")
    return config


def clean_env() -> dict[str, str]:
    # Keep the real OS home for normal OS operation; never redirect HOME or read
    # credentials from it. Account wrappers explicitly pin their own stores.
    allowed = ("HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "LC_CTYPE", "TERM",
               "TMPDIR", "TMP", "TEMP", "SYSTEMROOT", "WINDIR", "COMSPEC")
    env = {key: os.environ[key] for key in allowed if key in os.environ}
    env.update({
        "PATH": os.pathsep.join((str(STATE / "bin"), "/opt/homebrew/bin", "/usr/local/bin",
                                 "/usr/bin", "/bin", "/usr/sbin", "/sbin")),
        "XDG_CONFIG_HOME": str(STATE / "xdg"),
        "PYTHONNOUSERSITE": "1",
        "PYTHONUNBUFFERED": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "GCM_INTERACTIVE": "never",
    })
    return env

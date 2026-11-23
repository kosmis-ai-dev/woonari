"""T-013 / CR-006: AWS configuration, cache and account boundary for Woonari."""

from __future__ import annotations

import configparser
import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from project_context import ROOT, STATE, clean_env, fail, load_config, private_dir

BOOTSTRAP = ROOT / "tools/aws_cli_entry.py"
BLOCKED_OPTIONS = (
    "--profile", "--endpoint-url", "--no-sign-request", "--no-verify-ssl", "--ca-bundle",
    "--debug", "--cli-auto-prompt", "--cli-input-json", "--cli-input-yaml",
    "--role-arn", "--assume-role-arn",
)
UNSAFE_PROFILE_KEYS = {
    "credential_process", "credential_source", "source_profile", "role_arn",
    "web_identity_token_file", "endpoint_url", "services", "ca_bundle",
    "cli_legacy_plugin_path", "plugins",
}


def aws_environment(config: dict) -> dict[str, str]:
    env = clean_env()
    directory = STATE / "aws"
    env.update({
        "AWS_CONFIG_FILE": str(directory / "config"),
        "AWS_SHARED_CREDENTIALS_FILE": str(directory / "credentials"),
        "AWS_PROFILE": "woonari",
        "AWS_DEFAULT_PROFILE": "woonari",
        "AWS_REGION": config["aws"]["region"],
        "AWS_DEFAULT_REGION": config["aws"]["region"],
        "AWS_EC2_METADATA_DISABLED": "true",
        "AWS_IGNORE_CONFIGURED_ENDPOINT_URLS": "true",
        "AWS_LOGIN_CACHE_DIRECTORY": str(directory / "login/cache"),
        "AWS_CLI_AUTO_PROMPT": "off",
        "AWS_PAGER": "",
        "AWS_MAX_ATTEMPTS": "1",
        "BOTO_CONFIG": os.devnull,
    })
    return env


def cli_prefix(env: dict[str, str]) -> list[str]:
    executable = shutil.which("aws", path=env["PATH"])
    if not executable:
        fail("AWS CLI is not installed. No other account will be used.")
    executable_path = Path(executable).resolve()
    try:
        with executable_path.open("rb") as stream:
            first_line = stream.readline(1024).decode("utf-8")
        shebang = shlex.split(first_line[2:].strip()) if first_line.startswith("#!") else []
    except (OSError, UnicodeError, ValueError):
        shebang = []
    if (len(shebang) != 1 or not Path(shebang[0]).is_absolute()
            or not Path(shebang[0]).name.startswith("python")
            or not os.access(shebang[0], os.X_OK)):
        fail("This AWS CLI installation cannot isolate SSO caches. A Python-based official CLI is required.")
    return [shebang[0], "-I", str(BOOTSTRAP), str(STATE / "aws")]


def _read_ini(path: Path) -> configparser.RawConfigParser:
    if path.is_symlink():
        fail("AWS configuration cannot use symlinks.")
    parser = configparser.RawConfigParser()
    if path.exists():
        path.chmod(0o600)
        try:
            with path.open(encoding="utf-8") as stream:
                parser.read_file(stream)
        except (configparser.Error, UnicodeError):
            fail("The project's AWS configuration is invalid.")
    return parser


def validate_profile(
    config: dict, *, required: bool = True, protect_response: bool = False,
) -> None:
    account_id = config["aws"]["account_id"]
    if not re.fullmatch(r"[0-9]{12}", account_id):
        fail("Set the new AWS account ID in .local/woonari/config.json first. Existing accounts are blocked.")
    files = [(_read_ini(STATE / "aws/config"), "profile woonari"),
             (_read_ini(STATE / "aws/credentials"), "woonari")]
    found = False
    for parser, section in files:
        if parser.defaults():
            fail("AWS DEFAULT configuration is not allowed; use the project profile only.")
        for name in parser.sections():
            if name != section and not (section == "profile woonari" and name.startswith("sso-session ")):
                fail("The AWS store may contain only the Woonari profile and its SSO session.")
            values = dict(parser.items(name))
            if protect_response and values.get("cli_history", "").strip().lower() == "enabled":
                fail("AWS CLI history must be disabled in the project profile to protect sensitive responses.")
            if any(key in values for key in UNSAFE_PROFILE_KEYS):
                fail("External AWS credential providers, role chains and custom endpoints are blocked.")
            for key in ("sso_account_id", "aws_account_id"):
                if key in values and values[key] != account_id:
                    fail("The configured AWS profile belongs to a different account.")
        if parser.has_section(section):
            values = dict(parser.items(section))
            if values.get("sso_session") and not parser.has_section("sso-session " + values["sso_session"]):
                fail("The project SSO session configuration is missing.")
            found |= bool(values.get("aws_access_key_id") or values.get("sso_account_id"))
    if required and not found:
        fail("The project AWS profile has no credentials or SSO configuration. Use ./woonari aws configure sso.")


def validate_arguments(args: list[str]) -> None:
    if not args:
        fail("Use ./woonari aws <service> <operation>, configure sso, or --version.")
    for arg in args:
        option = arg.split("=", 1)[0]
        if option.startswith("--") and any(blocked.startswith(option) for blocked in BLOCKED_OPTIONS):
            fail("AWS account, endpoint, credential and debug overrides are blocked by the project wrapper.")
    command = args[0]
    if command.startswith("-") and args != ["--version"]:
        fail("Place the AWS service first; global account overrides are not accepted.")
    shared_config_operations = {"codeartifact": "login", "eks": "update-kubeconfig"}
    blocked_operation = shared_config_operations.get(command)
    if blocked_operation and any(
        arg and not arg.startswith("-") and blocked_operation.startswith(arg)
        for arg in args[1:]
    ):
        fail("AWS commands that modify shared pip/npm or kubeconfig settings are blocked.")
    supported_auth = (["configure"], ["configure", "sso"], ["configure", "list"],
                      ["sso", "login"], ["sso", "login", "--no-browser"],
                      ["sso", "login", "--no-browser", "--use-device-code"])
    if command in {"login", "logout", "configure", "sso", "sso-oidc"} and args not in supported_auth:
        fail("Only project configure/configure sso/configure list and sso login are supported.")
    if command == "sts" and len(args) > 1 and args[1] != "get-caller-identity":
        fail("STS credential/role switching is blocked; use the designated project account.")


def assert_account(prefix: list[str], env: dict[str, str], account_id: str) -> dict:
    try:
        identity = subprocess.run(
            [*prefix, "sts", "get-caller-identity", "--output", "json", "--no-cli-pager"],
            env=env, cwd=ROOT, capture_output=True, text=True, check=False, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        fail("AWS identity verification failed or timed out. The requested command was not executed.")
    if identity.returncode:
        fail("Project AWS authentication failed. Authenticate the new account; existing accounts are blocked.")
    try:
        data = json.loads(identity.stdout)
    except (ValueError, TypeError):
        fail("AWS identity verification returned an invalid response.")
    if not isinstance(data, dict) or data.get("Account") != account_id:
        fail("AWS account mismatch. The requested command was not executed.")
    return data


def main(args: list[str]) -> int:
    validate_arguments(args)
    config = load_config()
    for relative in ("", "sso/cache", "cli/cache", "boto/cache", "login/cache"):
        private_dir(STATE / "aws" / relative)
    env = aws_environment(config)
    if args == ["--version"]:
        prefix = cli_prefix(env)
        return subprocess.run([*prefix, *args], env=env, cwd=ROOT, check=False).returncode
    interactive = args[:1] == ["configure"] and args != ["configure", "list"]
    validate_profile(
        config, required=not interactive, protect_response=args[0] in {"secretsmanager", "bedrock-runtime"},
    )
    prefix = cli_prefix(env)
    if interactive:
        result = subprocess.run([*prefix, *args], env=env, cwd=ROOT, check=False)
        if result.returncode == 0:
            validate_profile(config)
        return result.returncode
    if args[:2] == ["sso", "login"]:
        result = subprocess.run([*prefix, *args], env=env, cwd=ROOT, check=False)
        if result.returncode:
            return result.returncode
        assert_account(prefix, env, config["aws"]["account_id"])
        print("Woonari AWS account verified.")
        return 0
    assert_account(prefix, env, config["aws"]["account_id"])
    return subprocess.run([*prefix, *args], env=env, cwd=ROOT, check=False).returncode

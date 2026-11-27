"""CR-025 / T-045: prepare Python social settings and Woonari auth tables."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_api"))
sys.path.insert(0, str(ROOT / "tools"))

from app.auth_models import SocialProvider
from app.auth_settings import (
    load_auth_settings,
    load_local_auth_settings,
    local_auth_source,
)
from app.auth_store import MySQLAuthStore
from app.errors import DomainError
from project_context import STATE, fail

PROVIDERS_FILE = STATE / "auth/providers.env"
PYTHON_ENV_FILE = ROOT / "python_api/.env"
TEMPLATE = """# Woonari Python API 소셜 로그인 설정. 값은 채팅·Git에 넣지 마세요.
WOONARI_ENV=development
# 운영은 HTTPS API 주소로 변경하고 같은 callback을 각 제공자 콘솔에 등록합니다.
AUTH_PUBLIC_BASE_URL=http://127.0.0.1:9090
# 카카오 REST API 키와 Client secret
KAKAO_CLIENT_ID=
KAKAO_CLIENT_SECRET=
# Google 웹 애플리케이션 OAuth Client ID와 secret
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
# 네이버 로그인 애플리케이션 Client ID와 secret
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
"""


def initialize_settings() -> None:
    path = PYTHON_ENV_FILE
    # The source folder is not private state: never chmod the package directory.
    if (
        not path.is_absolute() or path.parent != ROOT / "python_api"
        or path.parent.is_symlink() or ROOT.is_symlink() or path.is_symlink()
        or not path.parent.is_dir()
    ):
        raise RuntimeError("Python API 전용 환경설정 경로를 확인하세요.")
    if not path.exists():
        if PROVIDERS_FILE.is_symlink():
            raise DomainError("auth_configuration_invalid", "소셜 로그인 전용 설정을 확인하세요.", 503)
        if PROVIDERS_FILE.exists():
            # Validate before copying; preserve quoting, dollar signs and comments.
            load_auth_settings(PROVIDERS_FILE)
            content = b"WOONARI_ENV=development\n" + PROVIDERS_FILE.read_bytes()
        else:
            content = TEMPLATE.encode("utf-8")
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
        except BaseException:
            path.unlink(missing_ok=True)
            raise
    # Existing canonical and legacy secrets are never replaced or printed.
    load_local_auth_settings(python_env_file=path, legacy_file=PROVIDERS_FILE)


def status() -> dict:
    settings = load_local_auth_settings(python_env_file=PYTHON_ENV_FILE, legacy_file=PROVIDERS_FILE)
    source = local_auth_source(python_env_file=PYTHON_ENV_FILE, legacy_file=PROVIDERS_FILE)
    if source == str(PYTHON_ENV_FILE):
        source = "python_api/.env"
    elif source == str(PROVIDERS_FILE):
        source = ".local/woonari/auth/providers.env"
    return {
        "settings_file": source,
        "providers": [
            {
                "provider": str(provider), "configured": settings.configured(provider),
                "callback_url": settings.callback_url(provider), "actual_login_verified": False
            }
            for provider in SocialProvider
        ]
    }


def initialize_database() -> dict:
    from isolated_db import database_config, mysql_connector

    config = database_config()
    if config["database"] != "woonari" or config["manse_backend"] != "mysql":
        fail("전용 woonari MySQL 설정이 필요합니다. 다른 DB에 인증 테이블을 만들지 않습니다.")
    store = MySQLAuthStore(mysql_connector("woonari"))
    store.initialize()
    return {"database": "woonari", "authentication_tables": store.counts()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="woonari auth")
    parser.add_argument("command", choices=["init", "status", "init-db"])
    options = parser.parse_args(argv)
    if options.command == "init":
        initialize_settings()
    if options.command == "init-db":
        result = initialize_database()
    else:
        result = status()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DomainError as error:
        print(f"Woonari: {error.message}", file=sys.stderr)
        raise SystemExit(1) from None
    except (OSError, RuntimeError, ValueError):
        print("Woonari: 소셜 로그인 설정 또는 DB 준비 상태를 확인하세요.", file=sys.stderr)
        raise SystemExit(1) from None

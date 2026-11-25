"""CR-022 / T-042: prepare only Woonari social settings and new auth tables."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_api"))
sys.path.insert(0, str(ROOT / "tools"))

from app.auth_models import SocialProvider
from app.auth_settings import load_auth_settings
from app.auth_store import MySQLAuthStore
from app.errors import DomainError
from project_context import STATE, fail, private_dir, write_private

PROVIDERS_FILE = STATE / "auth/providers.env"
TEMPLATE = """# Woonari 전용 소셜 로그인 설정. 값은 채팅·Git에 넣지 마세요.
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
    private_dir(PROVIDERS_FILE.parent)
    if not PROVIDERS_FILE.exists():
        write_private(PROVIDERS_FILE, TEMPLATE)
    # Existing secrets are never replaced or printed.
    load_auth_settings(PROVIDERS_FILE)


def status() -> dict:
    settings = load_auth_settings(PROVIDERS_FILE)
    return {
        "settings_file": ".local/woonari/auth/providers.env",
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

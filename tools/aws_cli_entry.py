"""T-013 / CR-006: run the installed AWS CLI with project-only AWS caches.

AWS CLI's SSO/assume-role cache paths are computed from ``~/.aws`` at import
time. Redirect only that expansion before importing the official CLI; HOME and
all other user paths are unchanged. Unsupported CLI layouts fail closed.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def install_path_redirect(aws_directory: Path):
    original = os.path.expanduser

    def expanduser(path):
        value = os.fspath(path)
        prefix = b"~/.aws" if isinstance(value, bytes) else "~/.aws"
        slash = b"/" if isinstance(value, bytes) else "/"
        if value == prefix or value.startswith(prefix + slash):
            destination = os.fsencode(aws_directory) if isinstance(value, bytes) else str(aws_directory)
            return destination + value[len(prefix):]
        return original(path)

    os.path.expanduser = expanduser
    return original


def verify_cache_paths(aws_directory: Path) -> dict[str, str]:
    from awscli.customizations import assumerole
    from awscli.customizations.sso import utils
    from botocore.credentials import SSOProvider
    from botocore.tokens import SSOTokenProvider
    from botocore.utils import JSONFileCache

    actual = {
        "assume_role": assumerole.CACHE_DIR,
        "sso_cli": utils.SSO_TOKEN_DIR,
        "sso_credentials": SSOProvider._SSO_TOKEN_CACHE_DIR,
        "sso_tokens": SSOTokenProvider._SSO_TOKEN_CACHE_DIR,
        "botocore": JSONFileCache.CACHE_DIR,
    }
    expected = {
        "assume_role": aws_directory / "cli/cache",
        "sso_cli": aws_directory / "sso/cache",
        "sso_credentials": aws_directory / "sso/cache",
        "sso_tokens": aws_directory / "sso/cache",
        "botocore": aws_directory / "boto/cache",
    }
    if any(Path(actual[key]).resolve() != path.resolve() for key, path in expected.items()):
        raise RuntimeError("AWS CLI cache isolation could not be verified; operation blocked.")
    return {key: str(value) for key, value in actual.items()}


def main() -> int:
    if len(sys.argv) < 3:
        raise RuntimeError("Use ./woonari aws; this bootstrap is not a standalone AWS entry point.")
    aws_directory = Path(sys.argv[1]).resolve()
    root = Path(__file__).resolve().parents[1]
    if aws_directory != root / ".local/woonari/aws":
        raise RuntimeError("AWS state must belong to this project.")
    os.umask(0o077)
    install_path_redirect(aws_directory)
    import awscli.clidriver

    caches = verify_cache_paths(aws_directory)
    if sys.argv[2:] == ["--woonari-cache-check"]:
        print(json.dumps({"cache_isolation": "ok", "paths": caches}))
        return 0
    sys.argv = ["aws", *sys.argv[2:]]
    return awscli.clidriver.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ImportError, AttributeError, RuntimeError) as exc:
        print(f"Woonari AWS: {exc}", file=sys.stderr)
        raise SystemExit(2) from None

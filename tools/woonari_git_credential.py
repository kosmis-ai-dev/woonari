"""T-013 / F06 / CR-006: repository-bound Git credential protocol entry point."""

import sys

from isolated_git import credential_main

if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise RuntimeError("Git 인증 프로토콜 작업이 필요합니다.")
        raise SystemExit(credential_main(sys.argv[1], sys.stdin.read(16384)))
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)

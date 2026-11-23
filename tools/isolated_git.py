"""T-013 / F06 / CR-006: Git and GitHub commands with project-only identity.

Only the sanitized publication checkout is writable through this module. Account
verification fails closed; no ambient token, SSH agent or OS Git helper is used.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import uuid
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

from project_context import ROOT, STATE, clean_env, fail, load_config, private_dir


def publication_repository(root: Path) -> Path:
    """Use a published clone itself, never an arbitrary source-root repository."""
    if (root / "PUBLICATION.json").is_file() and (root / ".git").is_dir():
        return root
    return root / ".publish" / "woonari"


REPOSITORY = publication_repository(ROOT)
REMOTE = "https://github.com/kosmis-ai-dev/woonari.git"
API_REPOSITORY = "repos/kosmis-ai-dev/woonari"
READ_COMMANDS = {"status", "diff", "log", "show", "ls-files", "rev-parse"}
PYTHON_DIRECTORIES = {".project", "docs", "python_api", "tools"}
PYTHON_ROOT_FILES = {".gitattributes", ".gitignore", "AGENTS.md", "README.md", "PUBLICATION.json", "woonari"}
PRIVATE_PARTS = {".local", ".git", ".publish", ".publish-tools", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
FORBIDDEN_SUFFIXES = {".asp", ".inc", ".vbs", ".bak", ".sql", ".mdb", ".accdb", ".pem", ".key", ".pfx", ".p12", ".zip", ".gz", ".tar", ".tgz", ".avi", ".mp4", ".db", ".sqlite", ".sqlite3"}
LFS_HEADER = b"version https://git-lfs.github.com/spec/v1\n"


def isolated_env(*, interactive: bool = False) -> dict[str, str]:
    """Use project-only Git and GitHub configuration paths."""
    env = {
        key: value for key, value in clean_env().items()
        if not key.startswith(("GIT_", "GH_", "GITHUB_", "SSH_", "GCM_"))
    }
    private_dir(STATE)
    for relative in ("github", "git", "xdg", "bin"):
        private_dir(STATE / relative)
    global_config = STATE / "git" / "global.config"
    if global_config.is_symlink():
        fail("전용 Git 설정에 심볼릭 링크를 사용할 수 없습니다.")
    global_config.touch(mode=0o600, exist_ok=True)
    global_config.chmod(0o600)
    env.update({
        "PATH": str(STATE / "bin") + os.pathsep + env.get("PATH", os.defpath),
        "GH_CONFIG_DIR": str(STATE / "github"),
        "XDG_CONFIG_HOME": str(STATE / "xdg"),
        "GH_HOST": "github.com",
        "GH_PAGER": "cat",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": str(global_config),
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS": "/usr/bin/false",
        "SSH_ASKPASS": "/usr/bin/false",
        "GIT_SSH_COMMAND": "/usr/bin/false",
        "GIT_PAGER": "cat",
        "GCM_INTERACTIVE": "never",
    })
    if not interactive:
        env["GH_PROMPT_DISABLED"] = "1"
    return env


def _tool(name: str, env: dict[str, str]) -> str:
    executable = shutil.which(name, path=env["PATH"])
    if not executable:
        fail(f"{name} 실행 파일이 필요합니다.")
    return executable


def _git(args: list[str], env: dict[str, str], *, capture: bool = False, input_text=None, binary: bool = False):
    return subprocess.run(
        [_tool("git", env), "-C", str(REPOSITORY), *args],
        env=env, text=not binary, input=input_text, capture_output=capture, check=False,
    )


def _github(args: list[str], env: dict[str, str], *, capture: bool = False, input_text=None):
    return subprocess.run(
        [_tool("gh", env), *args], env=env, text=True,
        input=input_text, capture_output=capture, check=False,
    )


def _secure_gh_files() -> None:
    for name in ("hosts.yml", "config.yml"):
        path = STATE / "github" / name
        if path.is_symlink() or (path.exists() and not path.is_file()):
            fail("전용 GitHub 인증 설정은 일반 파일이어야 합니다.")
        if path.exists():
            if hasattr(os, "getuid") and path.stat().st_uid != os.getuid():
                fail("전용 GitHub 인증 설정의 파일 소유자가 다릅니다.")
            path.chmod(0o600)


def _private_gh_token(config: dict) -> str:
    """Read an owner-only token file or the active private hosts entry."""
    _secure_gh_files()
    token_file = STATE / "github/token"
    if token_file.is_symlink() or (token_file.exists() and not token_file.is_file()):
        fail("전용 GitHub token은 심볼릭 링크가 없는 일반 파일이어야 합니다.")
    if token_file.exists():
        info = token_file.stat()
        if hasattr(os, "getuid") and info.st_uid != os.getuid():
            fail("전용 GitHub token 파일의 소유자가 다릅니다.")
        if info.st_mode & 0o777 != 0o600:
            fail("전용 GitHub token 파일 권한을 600으로 설정하세요.")
        try:
            value = token_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            fail("전용 GitHub token 파일을 읽을 수 없습니다.")
        if not re.fullmatch(r"[A-Za-z0-9_]+\n?", value):
            fail("전용 GitHub token 파일에는 유효한 토큰 한 줄이 필요합니다.")
        return value.rstrip("\n")
    path = STATE / "github/hosts.yml"
    if not path.is_file():
        fail("저장소 전용 GitHub 토큰을 .local/woonari/github/token 파일에 한 줄로 저장하고 권한을 600으로 설정하세요.")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        fail("프로젝트 전용 GitHub 인증 형식을 확인할 수 없습니다.")
    scopes = []
    values = {}
    for line in lines:
        match = re.fullmatch(r"( *)([A-Za-z0-9_.-]+):(?: +([A-Za-z0-9_-]+))? *", line)
        if not match:
            continue
        spaces, key, value = match.groups()
        while scopes and scopes[-1][0] >= len(spaces):
            scopes.pop()
        field = (*[entry[1] for entry in scopes], key)
        if value is None:
            scopes.append((len(spaces), key))
        else:
            values[field] = value
    user = values.get(("github.com", "user"), "")
    token = values.get(("github.com", "users", user, "oauth_token")) or values.get(("github.com", "oauth_token"))
    if user.casefold() != config["git"]["login"].casefold() or not token:
        fail("전용 파일의 활성 GitHub 계정과 토큰이 필요합니다. 공용 Keychain 인증은 사용하지 않습니다.")
    return token


def _git_settings(config: dict) -> dict:
    settings = config.get("git", {})
    if settings.get("repository") != REMOTE:
        fail("이 프로젝트의 승인된 GitHub 저장소 주소와 설정이 다릅니다.")
    return settings


def configure_repository(config: dict | None = None, env: dict[str, str] | None = None) -> None:
    """Install local protections too, so ordinary Git cannot use OS credentials."""
    config = load_config() if config is None else config
    settings = _git_settings(config)
    env = isolated_env() if env is None else env
    if REPOSITORY.resolve() != REPOSITORY or not (REPOSITORY / ".git").is_dir():
        fail("검증된 배포 작업 사본 .publish/woonari가 필요합니다.")
    if (REPOSITORY / ".git").is_symlink():
        fail("전용 Git 작업 사본에 외부 .git 링크를 사용할 수 없습니다.")
    origin = _git(["config", "--local", "--get", "remote.origin.url"], env, capture=True)
    if origin.returncode or origin.stdout.strip() != REMOTE:
        fail("Git origin이 승인된 Woonari 저장소와 다릅니다.")
    helper = (
        "!" + shlex.quote(sys.executable) + " "
        + shlex.quote(str(ROOT / "tools" / "woonari_git_credential.py"))
    )
    values = {
        "user.name": settings.get("name", ""),
        "user.email": settings.get("email", ""),
        "user.useConfigOnly": "true",
        "credential.useHttpPath": "true",
        "credential.interactive": "false",
        "core.sshCommand": "/usr/bin/false",
        "http.extraHeader": "",
        "http.proxy": "",
        "lfs.url": REMOTE + "/info/lfs",
        "lfs.pushurl": REMOTE + "/info/lfs",
        "remote.origin.lfsurl": REMOTE + "/info/lfs",
        "remote.origin.lfspushurl": REMOTE + "/info/lfs",
    }
    for key, value in values.items():
        result = _git(["config", "--local", "--replace-all", key, value], env, capture=True)
        if result.returncode:
            fail("프로젝트 전용 Git 설정 적용에 실패했습니다.")
    # Empty helper first resets helpers inherited by direct Git from system/global config.
    reset = _git(["config", "--local", "--replace-all", "credential.helper", ""], env, capture=True)
    add = _git(["config", "--local", "--add", "credential.helper", helper], env, capture=True)
    if reset.returncode or add.returncode:
        fail("프로젝트 전용 Git 인증 설정 적용에 실패했습니다.")


def verify_account(config: dict, env: dict[str, str], *, require_write: bool = False) -> None:
    expected = _git_settings(config).get("login", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", expected):
        fail("프로젝트 전용 GitHub 로그인 이름을 먼저 설정하세요.")
    env["GH_TOKEN"] = _private_gh_token(config)
    account = _github(["api", "--hostname", "github.com", "user"], env, capture=True)
    if account.returncode:
        fail("프로젝트 전용 GitHub 인증이 필요합니다. 기존 공용 계정으로 대체하지 않습니다.")
    try:
        actual = json.loads(account.stdout)["login"]
    except (ValueError, KeyError, TypeError):
        fail("GitHub 계정 확인 응답을 검증할 수 없습니다.")
    if not isinstance(actual, str) or actual.casefold() != expected.casefold():
        fail("인증된 GitHub 계정이 프로젝트 전용 계정과 다릅니다.")
    if require_write:
        repository = _github(["api", "--hostname", "github.com", API_REPOSITORY], env, capture=True)
        if repository.returncode:
            fail("전용 GitHub 계정의 저장소 권한을 확인할 수 없습니다.")
        try:
            result = json.loads(repository.stdout)
            permitted = (
                result.get("full_name", "").casefold() == "kosmis-ai-dev/woonari"
                and result.get("permissions", {}).get("push") is True
            )
        except (ValueError, TypeError, AttributeError):
            permitted = False
        if not permitted:
            fail("전용 GitHub 계정에 Woonari 저장소 쓰기 권한이 없습니다.")


def _identity(settings: dict) -> None:
    if not settings.get("name", "").strip() or not settings.get("email", "").strip():
        fail("프로젝트 전용 Git 작성자 이름과 이메일을 먼저 설정하세요.")
    if any("\n" in settings[key] or "\r" in settings[key] for key in ("name", "email")):
        fail("Git 작성자 이름과 이메일 형식이 올바르지 않습니다.")


def _current_branch(env: dict[str, str]) -> str:
    result = _git(["branch", "--show-current"], env, capture=True)
    branch = result.stdout.strip()
    if result.returncode or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", branch):
        fail("현재 Git 작업 브랜치를 확인할 수 없습니다.")
    if branch.casefold() in {"main", "master"}:
        fail("이 명령은 main/master 직접 push를 허용하지 않습니다. 작업 브랜치를 사용하세요.")
    return branch


def _python_path(relative: str) -> bool:
    path = Path(relative)
    if path.is_absolute() or not path.parts or any(ord(char) < 32 for char in relative):
        return False
    if any(part.casefold() in PRIVATE_PARTS or part in {".", ".."} for part in path.parts):
        return False
    if len(path.parts) == 1:
        return relative in PYTHON_ROOT_FILES or relative in PYTHON_DIRECTORIES
    if path.parts[0] not in PYTHON_DIRECTORIES:
        return False
    if path.name.startswith(".env") and path.name != ".env.example":
        return False
    if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return relative == "python_api/app/data/manse.sqlite3"
    return True


def assert_python_history(env: dict[str, str]) -> None:
    """T-036 / CR-016: check every reachable object, including removed ancestors."""
    objects = _git(["-c", "core.quotePath=false", "rev-list", "--objects", "HEAD"], env, capture=True)
    if objects.returncode:
        fail("Python 배포 커밋 이력을 확인할 수 없습니다.")
    identifiers = set()
    attributes = set()
    for line in objects.stdout.splitlines():
        identifier, _, path = line.partition(" ")
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", identifier):
            fail("Git 이력의 객체 목록 형식을 확인할 수 없습니다.")
        identifiers.add(identifier)
        if path:
            if not _python_path(path):
                fail("이 배포 이력에 ASP·사이트 자산·개인 설정·백업이 포함되어 있습니다. Python 전용 배포 브랜치를 준비하세요.")
            if Path(path).name == ".gitattributes":
                attributes.add(identifier)
    if not identifiers:
        fail("먼저 Python 배포 파일을 커밋하세요.")
    # rev-list de-duplicates blobs. Inspect each commit tree as well so aliases
    # of an already-seen blob cannot hide a forbidden historical path.
    commits = _git(["rev-list", "HEAD"], env, capture=True)
    if commits.returncode:
        fail("Git 커밋 목록을 확인할 수 없습니다.")
    for commit in commits.stdout.splitlines():
        tree = _git(["ls-tree", "-r", "--name-only", "-z", commit], env, capture=True)
        if tree.returncode or any(not _python_path(path) for path in tree.stdout.split("\0") if path):
            fail("과거 커밋에 Python 배포 범위 밖의 파일이 있습니다. Python 전용 배포 브랜치를 준비하세요.")
    details = _git(
        ["cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        env, capture=True, input_text="\n".join(sorted(identifiers)) + "\n",
    )
    if details.returncode:
        fail("Git 배포 객체의 크기와 종류를 확인할 수 없습니다.")
    for line in details.stdout.splitlines():
        fields = line.split()
        if len(fields) != 3 or fields[0] not in identifiers or not fields[2].isdigit():
            fail("Git 배포 객체 정보를 검증할 수 없습니다.")
        identifier, kind, size = fields
        if kind != "blob" or (int(size) > 1024 and identifier not in attributes):
            continue
        content = _git(["cat-file", "blob", identifier], env, capture=True, binary=True)
        if content.returncode:
            fail("Git 배포 파일을 검증할 수 없습니다.")
        if content.stdout.startswith(LFS_HEADER) or (identifier in attributes and b"filter=lfs" in content.stdout):
            fail("이 배포 이력에 Git LFS 파일 또는 설정이 포함되어 있습니다. Python 전용 배포 브랜치를 준비하세요.")


def _verified_python_paths() -> set[str]:
    import prepare_github

    if not (REPOSITORY / "PUBLICATION.json").is_file():
        fail("검증된 Python 배포 사본과 PUBLICATION.json이 필요합니다.")
    # The verifier prints aggregate findings only. Keep preparation output concise.
    with redirect_stdout(io.StringIO()):
        prepare_github.verify(REPOSITORY)
    expected = {
        path.relative_to(prepare_github.ROOT).as_posix()
        for path, reason in prepare_github.source_files() if not reason
    } | {"PUBLICATION.json"}
    if not all(_python_path(path) for path in expected):
        fail("검증된 배포 사본에 Python 프로젝트 외 파일이 있습니다.")
    return expected


def _write_exclusive(path: Path, data: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)


def prepare_python_branch(name: str, env: dict[str, str]) -> int:
    """Create an unborn publication branch without restoring the old working tree."""
    if not re.fullmatch(r"publish/python-api-[0-9]{8}", name):
        fail("배포 브랜치 이름은 publish/python-api-YYYYMMDD 형식이어야 합니다.")
    try:
        datetime.strptime(name.rsplit("-", 1)[1], "%Y%m%d")
    except ValueError:
        fail("배포 브랜치 날짜가 올바르지 않습니다.")
    gitdir = REPOSITORY / ".git"
    if (gitdir / "worktrees").exists():
        fail("연결된 Git worktree가 있는 저장소는 이 준비 명령을 지원하지 않습니다.")
    for relative in ("HEAD", "index"):
        if (gitdir / relative).is_symlink():
            fail("Git HEAD 또는 index에 심볼릭 링크를 사용할 수 없습니다.")
    if (gitdir / "index.lock").exists():
        fail("다른 Git 작업이 진행 중입니다. 완료 후 다시 실행하세요.")
    reference = f"refs/heads/{name}"
    exists = _git(["show-ref", "--verify", "--quiet", reference], env, capture=True)
    if exists.returncode != 1:
        fail("이미 존재하거나 확인할 수 없는 배포 브랜치입니다. 새 이름을 사용하세요.")
    previous = _git(["symbolic-ref", "--quiet", "HEAD"], env, capture=True)
    if previous.returncode or not previous.stdout.strip().startswith("refs/heads/"):
        fail("현재 HEAD가 로컬 작업 브랜치를 가리켜야 합니다.")
    expected = _verified_python_paths()
    backup = private_dir(STATE / "git" / "publication-branches" / uuid.uuid4().hex)
    head = (gitdir / "HEAD").read_bytes()
    index_path = gitdir / "index"
    index = index_path.read_bytes() if index_path.exists() else None
    _write_exclusive(backup / "HEAD", head)
    if index is not None:
        _write_exclusive(backup / "index", index)
    _write_exclusive(backup / "state.json", json.dumps({
        "previous_ref": previous.stdout.strip(), "new_ref": reference,
        "index_existed": index is not None,
    }).encode("utf-8"))
    try:
        for command in (
            ["symbolic-ref", "HEAD", reference],
            ["read-tree", "--empty"],
            ["add", "--all", "--", *sorted(expected)],
        ):
            if _git(command, env, capture=True).returncode:
                fail("Python 배포 브랜치 준비에 실패했습니다. 기존 HEAD와 index를 복구합니다.")
        staged = _git(["ls-files", "-z"], env, capture=True)
        if staged.returncode or set(staged.stdout.split("\0")) - {""} != expected:
            fail("스테이징된 파일이 검증된 Python 배포 목록과 다릅니다.")
        object_format = _git(["rev-parse", "--show-object-format"], env, capture=True)
        entries = _git(["ls-files", "--stage", "-z"], env, capture=True)
        algorithm = object_format.stdout.strip()
        if object_format.returncode or entries.returncode or algorithm not in {"sha1", "sha256"}:
            fail("스테이징된 Git 객체 형식을 확인할 수 없습니다.")
        for entry in entries.stdout.split("\0"):
            if not entry:
                continue
            metadata, path = entry.split("\t", 1)
            _, actual_hash, stage = metadata.split()
            data = (REPOSITORY / path).read_bytes()
            expected_hash = hashlib.new(algorithm, f"blob {len(data)}\0".encode() + data).hexdigest()
            if stage != "0" or actual_hash != expected_hash:
                fail("Git 필터가 배포 파일 바이트를 변경했습니다. 기존 HEAD와 index를 복구합니다.")
    except BaseException:
        for path, value in ((gitdir / "HEAD", head), (index_path, index)):
            if value is None:
                path.unlink(missing_ok=True)
            else:
                temporary = path.with_name(f".{path.name}.woonari-{uuid.uuid4().hex}")
                _write_exclusive(temporary, value)
                temporary.replace(path)
        raise
    print(f"Python 전용 배포 브랜치 준비 완료: {name} ({len(expected)}개 파일 스테이징)")
    return 0


def _git_command(args: list[str], config: dict, env: dict[str, str]) -> int:
    if not args:
        args = ["status", "--short", "--branch"]
    command, *options = args
    # Global Git overrides, external diff helpers and output redirection bypass isolation.
    forbidden = ("--git-dir", "--work-tree", "--exec-path", "--config-env", "--output", "--ext-diff", "--textconv")
    if command.startswith("-") or any(item.startswith(forbidden) for item in options):
        fail("격리를 우회하는 Git 옵션은 허용하지 않습니다.")
    configure_repository(config, env)
    if command == "prepare-python-branch" and len(options) == 1:
        return prepare_python_branch(options[0], env)
    if command in READ_COMMANDS or command == "branch" and options in ([], ["--list"], ["--show-current"]):
        pass
    elif command == "add":
        _identity(_git_settings(config))
    elif command == "commit":
        _identity(_git_settings(config))
        # An explicit message keeps editors and alternate author sources out of this path.
        remaining = list(options)
        while remaining:
            if remaining.pop(0) not in {"-m", "--message"} or not remaining:
                fail("전용 커밋은 commit -m '작업 메시지' 형식만 지원합니다.")
            remaining.pop(0)
        if not options:
            fail("커밋 메시지가 필요합니다.")
    elif command == "fetch" and options in ([], ["origin"]):
        verify_account(config, env)
        args = ["fetch", "--prune", "origin"]
    elif command == "push":
        _identity(_git_settings(config))
        branch = _current_branch(env)
        if options not in (
            [], ["origin"], ["origin", branch], ["-u"], ["--set-upstream"],
            ["-u", "origin", branch], ["--set-upstream", "origin", branch],
        ):
            fail("origin의 현재 작업 브랜치만 push할 수 있습니다. 강제·삭제·임의 ref push는 차단됩니다.")
        assert_python_history(env)
        verify_account(config, env, require_write=True)
        args = ["push", "--set-upstream", "origin", branch]
    else:
        fail("지원하지 않는 Git 명령입니다. status/diff/log/show/ls-files/branch/add/commit/fetch/push를 사용하세요.")
    return _git(args, env).returncode


def _gh_command(args: list[str], config: dict, env: dict[str, str]) -> int:
    if args in ([], ["--help"], ["help"]):
        print("woonari gh auth login | auth status | api user | api repos/kosmis-ai-dev/woonari")
        return 0
    if args in (["auth", "login"], ["auth", "login", "--web"]):
        if not _git_settings(config).get("login", "").strip():
            fail("먼저 프로젝트 전용 GitHub 로그인 이름을 설정하세요.")
        verify_account(config, env)
        print("프로젝트 전용 GitHub 계정 인증을 확인했습니다.")
        return 0
    if args == ["auth", "status"]:
        if not any((STATE / "github" / name).exists() or (STATE / "github" / name).is_symlink()
                   for name in ("token", "hosts.yml")):
            print("전용 GitHub 인증이 설정되지 않았습니다. .local/woonari/github/token 파일을 설정하세요.")
            return 1
        verify_account(config, env)
        print("프로젝트 전용 GitHub 계정 인증을 확인했습니다.")
        return 0
    if args in (["api", "user"], ["api", API_REPOSITORY]):
        verify_account(config, env)
        return _github(["api", "--hostname", "github.com", args[1]], env).returncode
    fail("이 프로젝트의 gh는 로그인·인증 상태·지정된 계정/저장소 조회만 지원합니다.")


def credential_main(operation: str, request: str) -> int:
    """Git credential protocol: output only to Git, never display tokens to users."""
    if operation != "get":
        return 0  # No writes/deletes to shared Keychain credentials.
    fields = dict(line.split("=", 1) for line in request.splitlines() if "=" in line)
    path = fields.get("path", "").rstrip("/")
    allowed_path = (
        path in {"kosmis-ai-dev/woonari", "kosmis-ai-dev/woonari.git", "kosmis-ai-dev/woonari.git/info/lfs"}
        or path.startswith("kosmis-ai-dev/woonari.git/info/lfs/")
    )
    if (
        fields.get("protocol") != "https"
        or fields.get("host") != "github.com"
        or not allowed_path
    ):
        fail("다른 저장소에 Woonari 인증을 제공하지 않습니다.")
    config = load_config()
    env = isolated_env()
    verify_account(config, env, require_write=True)
    result = _github(["auth", "git-credential", "get"], env, capture=True, input_text=request)
    if result.returncode:
        fail("전용 GitHub 인증 정보를 불러올 수 없습니다.")
    sys.stdout.write(result.stdout)
    return 0


def main(args: list[str]) -> int:
    config = load_config()
    env = isolated_env()
    _git_settings(config)
    if args and args[0] == "gh":
        return _gh_command(args[1:], config, env)
    if not args or args[0] != "git":
        fail("git 또는 gh 명령이 필요합니다.")
    return _git_command(args[1:], config, env)


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)

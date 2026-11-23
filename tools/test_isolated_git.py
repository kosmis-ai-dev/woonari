"""T-013 / CR-006: prevent cross-project identity and credential fallback."""

import copy
import hashlib
import json
import subprocess
from types import SimpleNamespace

import isolated_git as subject
import project_context
import pytest


@pytest.fixture
def project(tmp_path, monkeypatch):
    state = tmp_path / ".local" / "woonari"
    repo = tmp_path / ".publish" / "woonari"
    for module in (project_context, subject):
        monkeypatch.setattr(module, "ROOT", tmp_path)
        monkeypatch.setattr(module, "STATE", state)
    monkeypatch.setattr(project_context, "CONFIG_FILE", state / "config.json")
    monkeypatch.setattr(subject, "REPOSITORY", repo)
    config = copy.deepcopy(project_context.DEFAULTS)
    config["git"].update(login="woonari-user", name="Woonari developer", email="project@example.test")
    project_context.save_config(config)
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", str(repo)], env=subject.isolated_env(), capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(repo), "remote", "add", "origin", subject.REMOTE],
        env=subject.isolated_env(), capture_output=True, check=True,
    )
    hosts = state / "github/hosts.yml"
    hosts.write_text("github.com:\n    user: woonari-user\n    oauth_token: synthetic_project_token\n")
    hosts.chmod(0o600)
    return config, repo, state


def fake_result(stdout="", code=0):
    return SimpleNamespace(stdout=stdout, stderr="", returncode=code)


def test_original_uses_nested_publication_even_with_source_root_git(tmp_path):
    (tmp_path / ".git").mkdir()
    assert subject.publication_repository(tmp_path) == tmp_path / ".publish/woonari"


def test_published_clone_uses_its_own_repository_root(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "PUBLICATION.json").write_text("{}\n")
    assert subject.publication_repository(tmp_path) == tmp_path


def test_external_account_environment_is_removed(project, monkeypatch):
    for key in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GIT_CONFIG_COUNT",
                "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0", "GIT_AUTHOR_EMAIL", "SSH_AUTH_SOCK",
                "GIT_ASKPASS", "AWS_ACCESS_KEY_ID"):
        monkeypatch.setenv(key, "ambient-other-project-value")
    env = subject.isolated_env()
    assert "GH_TOKEN" not in env
    assert "GITHUB_TOKEN" not in env
    assert "GIT_AUTHOR_EMAIL" not in env
    assert "GIT_CONFIG_COUNT" not in env
    assert "SSH_AUTH_SOCK" not in env
    assert "AWS_ACCESS_KEY_ID" not in env
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert env["GIT_ASKPASS"] == "/usr/bin/false"
    assert env["GIT_CONFIG_GLOBAL"] == str(project[2] / "git/global.config")
    assert env["GH_CONFIG_DIR"] == str(project[2] / "github")


def test_local_config_blocks_global_identity_and_helpers_without_editing_shared_file(project, monkeypatch, tmp_path):
    config, repo, _ = project
    shared = tmp_path / "shared.gitconfig"
    shared.write_text("[user]\n name = Other project\n email = other@example.test\n[credential]\n helper = store\n")
    before = shared.read_bytes()
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(shared))
    subject.configure_repository(config)
    assert shared.read_bytes() == before
    inherited = {"PATH": "/usr/bin:/bin", "GIT_CONFIG_GLOBAL": str(shared), "GIT_CONFIG_NOSYSTEM": "1"}
    email = subprocess.run(["git", "-C", str(repo), "config", "user.email"], env=inherited, capture_output=True, text=True, check=True)
    helpers = subprocess.run(["git", "-C", str(repo), "config", "--get-all", "credential.helper"], env=inherited, capture_output=True, text=True, check=True)
    assert email.stdout.strip() == "project@example.test"
    assert helpers.stdout.splitlines()[0:2] == ["store", ""]
    assert "woonari_git_credential.py" in helpers.stdout.splitlines()[2]


def test_empty_identity_overrides_shared_identity_and_blocks_commit(project, monkeypatch):
    config, repo, _ = project
    config["git"]["name"] = ""
    config["git"]["email"] = ""
    monkeypatch.setattr(subject, "load_config", lambda: config)
    with pytest.raises(RuntimeError, match="작성자"):
        subject.main(["git", "commit", "-m", "synthetic test"])
    result = subprocess.run(["git", "-C", str(repo), "var", "GIT_AUTHOR_IDENT"], env=subject.isolated_env(), capture_output=True, text=True, check=False)
    assert result.returncode != 0


def test_status_works_without_account_but_push_fails_closed(project, monkeypatch):
    config, _, _ = project
    config["git"]["login"] = ""
    monkeypatch.setattr(subject, "load_config", lambda: config)
    assert subject.main(["git", "status", "--short"]) == 0
    monkeypatch.setattr(subject, "_current_branch", lambda env: "work/isolation")
    monkeypatch.setattr(subject, "assert_python_history", lambda env: None)
    monkeypatch.setattr(subject, "_github", lambda *a, **k: pytest.fail("must not contact GitHub without login"))
    with pytest.raises(RuntimeError, match="로그인 이름"):
        subject.main(["git", "push"])


def test_wrong_origin_is_rejected_before_any_account_query(project, monkeypatch):
    _, repo, _ = project
    subprocess.run(["git", "-C", str(repo), "remote", "set-url", "origin", "https://github.com/other/project.git"], env=subject.isolated_env(), check=True)
    monkeypatch.setattr(subject, "_github", lambda *a, **k: pytest.fail("wrong origin must not authenticate"))
    with pytest.raises(RuntimeError, match="origin"):
        subject.main(["git", "fetch"])


def test_wrong_github_account_is_rejected(project, monkeypatch):
    config, _, _ = project
    monkeypatch.setattr(subject, "_github", lambda *a, **k: fake_result(json.dumps({"login": "another-user"})))
    with pytest.raises(RuntimeError, match="계정.*다릅니다"):
        subject.verify_account(config, subject.isolated_env(), require_write=True)


@pytest.mark.parametrize("payload", [
    {"full_name": "kosmis-ai-dev/woonari", "permissions": {"push": False}},
    {"full_name": "other/project", "permissions": {"push": True}},
    {"full_name": "kosmis-ai-dev/woonari", "permissions": {"push": "true"}},
])
def test_repo_write_permission_must_be_boolean_and_for_exact_repository(project, monkeypatch, payload):
    config, _, _ = project
    answers = iter([{"login": "woonari-user"}, payload])
    monkeypatch.setattr(subject, "_github", lambda *a, **k: fake_result(json.dumps(next(answers))))
    with pytest.raises(RuntimeError, match="쓰기 권한"):
        subject.verify_account(config, subject.isolated_env(), require_write=True)


@pytest.mark.parametrize("args", [
    ["-c", "credential.helper=store", "push"],
    ["config", "--global", "user.email", "other@example.test"],
    ["push", "--force"], ["push", "--delete", "origin", "work/isolation"],
    ["push", "https://github.com/other/project.git"],
    ["commit", "--author", "Other <other@example.test>", "-m", "test"],
    ["diff", "--output=/tmp/unrelated-file"],
])
def test_git_escape_routes_are_rejected(project, monkeypatch, args):
    monkeypatch.setattr(subject, "_current_branch", lambda env: "work/isolation")
    monkeypatch.setattr(subject, "_github", lambda *a, **k: pytest.fail("rejected operation must not authenticate"))
    with pytest.raises(RuntimeError):
        subject.main(["git", *args])


def test_master_branch_push_is_blocked(project):
    _, repo, _ = project
    subprocess.run(["git", "-C", str(repo), "symbolic-ref", "HEAD", "refs/heads/master"], env=subject.isolated_env(), check=True)
    with pytest.raises(RuntimeError, match="master"):
        subject.main(["git", "push"])


def test_push_runs_only_exact_branch_after_correct_account_and_write_check(project, monkeypatch):
    events = []
    original_git = subject._git
    def git(args, env, **kwargs):
        if args[0] == "push":
            events.append(("push", args))
            return fake_result()
        return original_git(args, env, **kwargs)
    def github(args, env, **kwargs):
        events.append(("github", args[-1]))
        if args[-1] == "user":
            return fake_result(json.dumps({"login": "woonari-user"}))
        return fake_result(json.dumps({"full_name": "kosmis-ai-dev/woonari", "permissions": {"push": True}}))
    monkeypatch.setattr(subject, "_git", git)
    monkeypatch.setattr(subject, "_github", github)
    monkeypatch.setattr(subject, "_current_branch", lambda env: "work/isolation")
    monkeypatch.setattr(subject, "assert_python_history", lambda env: None)
    assert subject.main(["git", "push"]) == 0
    assert events == [
        ("github", "user"), ("github", subject.API_REPOSITORY),
        ("push", ["push", "--set-upstream", "origin", "work/isolation"]),
    ]


def test_authentication_failure_does_not_echo_provider_output(project, monkeypatch):
    config, _, _ = project
    monkeypatch.setattr(subject, "_github", lambda *a, **k: fake_result("synthetic-sensitive-provider-output", 1))
    with pytest.raises(RuntimeError) as error:
        subject.verify_account(config, subject.isolated_env())
    assert "synthetic-sensitive-provider-output" not in str(error.value)


@pytest.mark.parametrize("args", [
    ["auth", "token"], ["auth", "status", "--show-token"],
    ["api", "user", "--method", "DELETE"], ["api", "repos/other/project"],
    ["auth", "setup-git"], ["repo", "create"],
])
def test_gh_cannot_bypass_wrapper(project, monkeypatch, args):
    monkeypatch.setattr(subject, "_github", lambda *a, **k: pytest.fail("unsupported gh must not execute"))
    with pytest.raises(RuntimeError):
        subject.main(["gh", *args])


def test_credentials_are_bound_to_repository_and_lfs_uses_same_account(project, monkeypatch, capsys):
    requests = []
    def github(args, env, **kwargs):
        requests.append(args)
        if args[-1] == "user":
            return fake_result(json.dumps({"login": "woonari-user"}))
        if args[-1] == subject.API_REPOSITORY:
            return fake_result(json.dumps({"full_name": "kosmis-ai-dev/woonari", "permissions": {"push": True}}))
        return fake_result("username=synthetic-user\npassword=synthetic-credential\n")
    monkeypatch.setattr(subject, "_github", github)
    with pytest.raises(RuntimeError, match="다른 저장소"):
        subject.credential_main("get", "protocol=https\nhost=github.com\npath=other/project.git\n")
    assert requests == []
    assert subject.credential_main("get", "protocol=https\nhost=github.com\npath=kosmis-ai-dev/woonari.git/info/lfs\n") == 0
    assert "synthetic-credential" in capsys.readouterr().out
    assert len(requests) == 3
    assert subject.credential_main("store", "password=not-stored\n") == 0
    assert len(requests) == 3


def test_login_verifies_project_token_without_invoking_cli_login(project, monkeypatch):
    calls = []
    def github(args, env, **kwargs):
        calls.append((args, env))
        return fake_result(json.dumps({"login": "woonari-user"}))
    monkeypatch.setattr(subject, "_github", github)
    assert subject.main(["gh", "auth", "login"]) == 0
    assert calls[0][0] == ["api", "--hostname", "github.com", "user"]
    assert calls[0][1]["GIT_CONFIG_GLOBAL"] == str(project[2] / "git/global.config")
    assert calls[0][1]["GH_TOKEN"] == "synthetic_project_token"
    assert len(calls) == 1


def local_git(project, *args, check=True):
    return subprocess.run(
        ["git", "-C", str(project[1]), *args], env=subject.isolated_env(),
        text=True, capture_output=True, check=check,
    )


@pytest.fixture
def prepared_python_tree(project, monkeypatch):
    config, repo, _ = project
    subject.configure_repository(config)
    (repo / "old").mkdir()
    (repo / "old/original.asp").write_text("<% Response.Write 1 %>\n")
    (repo / "README.md").write_text("old snapshot\n")
    local_git(project, "add", "--all")
    local_git(project, "commit", "-m", "synthetic old ASP commit")
    old_ref = local_git(project, "symbolic-ref", "HEAD").stdout.strip()
    old_commit = local_git(project, "rev-parse", "HEAD").stdout.strip()
    (repo / "old/original.asp").unlink()
    (repo / "old").rmdir()
    (repo / "README.md").write_text("Python API\n")
    (repo / "python_api/app").mkdir(parents=True)
    (repo / "python_api/app/main.py").write_text('print("Python API")\n')
    (repo / "PUBLICATION.json").write_text('{"asp_files": 0}\n')
    expected = {"README.md", "python_api/app/main.py", "PUBLICATION.json"}
    monkeypatch.setattr(subject, "_verified_python_paths", lambda: set(expected))
    monkeypatch.setattr(subject, "_github", lambda *a, **k: pytest.fail("preparation must not authenticate"))
    return project, expected, old_ref, old_commit


def test_old_asp_ancestor_is_rejected_after_working_tree_removal(prepared_python_tree):
    project, _, _, _ = prepared_python_tree
    local_git(project, "add", "--all")
    local_git(project, "commit", "-m", "synthetic removal")
    local_git(project, "branch", "-m", "work/legacy")
    assert not (project[1] / "old/original.asp").exists()
    with pytest.raises(RuntimeError, match="ASP|과거"):
        subject.main(["git", "push"])


def test_new_python_branch_preserves_old_ref_files_and_has_no_parent(prepared_python_tree, monkeypatch):
    project, expected, old_ref, old_commit = prepared_python_tree
    config, repo, state = project
    original_files = {path: (repo / path).read_bytes() for path in expected}
    author = dict(config["git"])
    config["git"].update(login="", name="", email="")
    monkeypatch.setattr(subject, "load_config", lambda: config)
    assert subject.main(["git", "prepare-python-branch", "publish/python-api-20261123"]) == 0
    assert local_git(project, "rev-parse", "--verify", "HEAD", check=False).returncode != 0
    assert local_git(project, "rev-parse", old_ref).stdout.strip() == old_commit
    assert {path: (repo / path).read_bytes() for path in expected} == original_files
    assert set(local_git(project, "ls-files", "-z").stdout.split("\0")) - {""} == expected
    backups = list((state / "git/publication-branches").iterdir())
    assert len(backups) == 1
    assert all(path.stat().st_mode & 0o077 == 0 for path in backups[0].iterdir())
    config["git"].update(author)
    subject.configure_repository(config)
    local_git(project, "commit", "-m", "synthetic Python root")
    assert len(local_git(project, "rev-list", "--parents", "-n", "1", "HEAD").stdout.split()) == 1
    subject.assert_python_history(subject.isolated_env())


@pytest.mark.parametrize("name", [
    "main", "publish/python-api-2026112", "publish/python-api-20260230",
    "publish/python-api-20261123/extra", "refs/heads/publish/python-api-20261123",
])
def test_invalid_preparation_branch_name_keeps_head_and_index(prepared_python_tree, name):
    project, _, _, _ = prepared_python_tree
    gitdir = project[1] / ".git"
    before = ((gitdir / "HEAD").read_bytes(), (gitdir / "index").read_bytes())
    with pytest.raises(RuntimeError):
        subject.main(["git", "prepare-python-branch", name])
    assert before == ((gitdir / "HEAD").read_bytes(), (gitdir / "index").read_bytes())


def test_committed_destination_branch_is_rejected(prepared_python_tree):
    project, _, _, _ = prepared_python_tree
    local_git(project, "branch", "publish/python-api-20261123")
    before = local_git(project, "symbolic-ref", "HEAD").stdout
    with pytest.raises(RuntimeError, match="존재"):
        subject.main(["git", "prepare-python-branch", "publish/python-api-20261123"])
    assert local_git(project, "symbolic-ref", "HEAD").stdout == before


def test_preparation_failure_restores_head_and_index_without_checkout(prepared_python_tree, monkeypatch):
    project, expected, old_ref, old_commit = prepared_python_tree
    gitdir = project[1] / ".git"
    head, index = (gitdir / "HEAD").read_bytes(), (gitdir / "index").read_bytes()
    files = {path: (project[1] / path).read_bytes() for path in expected}
    original_git = subject._git
    def git(args, env, **kwargs):
        if args[0] == "add":
            return fake_result(code=1)
        assert args[0] != "checkout"
        return original_git(args, env, **kwargs)
    monkeypatch.setattr(subject, "_git", git)
    with pytest.raises(RuntimeError, match="준비에 실패"):
        subject.main(["git", "prepare-python-branch", "publish/python-api-20261123"])
    assert (gitdir / "HEAD").read_bytes() == head
    assert (gitdir / "index").read_bytes() == index
    assert local_git(project, "rev-parse", old_ref).stdout.strip() == old_commit
    assert {path: (project[1] / path).read_bytes() for path in expected} == files


def test_git_clean_filter_cannot_change_staged_publication_bytes(prepared_python_tree):
    project, expected, _, _ = prepared_python_tree
    repo = project[1]
    (repo / ".gitattributes").write_text("python_api/app/main.py filter=fixture\n")
    expected.add(".gitattributes")
    local_git(project, "config", "filter.fixture.clean", "sed 's/print/modified/'")
    local_git(project, "config", "filter.fixture.required", "true")
    head = (repo / ".git/HEAD").read_bytes()
    index = (repo / ".git/index").read_bytes()
    original = (repo / "python_api/app/main.py").read_bytes()
    with pytest.raises(RuntimeError, match="필터"):
        subject.main(["git", "prepare-python-branch", "publish/python-api-20261123"])
    assert (repo / ".git/HEAD").read_bytes() == head
    assert (repo / ".git/index").read_bytes() == index
    assert (repo / "python_api/app/main.py").read_bytes() == original


def test_same_unborn_python_branch_can_refresh_verified_metadata(prepared_python_tree):
    project, _, old_ref, old_commit = prepared_python_tree
    command = ["git", "prepare-python-branch", "publish/python-api-20261123"]
    assert subject.main(command) == 0
    (project[1] / "PUBLICATION.json").write_text('{"asp_files": 0, "checked": true}\n')
    assert subject.main(command) == 0
    staged = local_git(project, "show", ":PUBLICATION.json").stdout
    assert json.loads(staged)["checked"] is True
    assert local_git(project, "rev-parse", old_ref).stdout.strip() == old_commit
    assert local_git(project, "rev-parse", "--verify", "HEAD", check=False).returncode != 0


def test_preparation_uses_real_verifier_and_rejects_absent_manifest(project, monkeypatch):
    import prepare_github
    monkeypatch.setattr(prepare_github, "verify", lambda dest: pytest.fail("missing manifest must fail first"))
    with pytest.raises(RuntimeError, match="PUBLICATION"):
        subject.main(["git", "prepare-python-branch", "publish/python-api-20261123"])


def test_preparation_rejects_symlinked_index(prepared_python_tree):
    project, _, _, _ = prepared_python_tree
    repo = project[1]
    original_index = repo / ".git/index"
    backup = project[2] / "external-index"
    original_index.replace(backup)
    original_index.symlink_to(backup)
    with pytest.raises(RuntimeError, match="심볼릭"):
        subject.main(["git", "prepare-python-branch", "publish/python-api-20261123"])


@pytest.mark.parametrize("path,data", [
    ("python_api/.local/cache.json", b"{}"),
    ("python_api/app/legacy.asp", b"<% 1 %>"),
    ("images/site.png", b"synthetic site image"),
    ("python_api/app/data/raw.sql", b"synthetic dump"),
    ("python_api/app/data/reference.dat", b"version https://git-lfs.github.com/spec/v1\noid sha256:synthetic\nsize 1\n"),
])
def test_history_blocks_private_asp_site_database_and_lfs(project, path, data):
    subject.configure_repository(project[0])
    file = project[1] / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(data)
    local_git(project, "add", "--all")
    local_git(project, "commit", "-m", "synthetic disallowed tree")
    with pytest.raises(RuntimeError):
        subject.assert_python_history(subject.isolated_env())


def test_private_file_token_is_required_without_global_keychain_fallback(project, monkeypatch):
    (project[2] / "github/hosts.yml").write_text("github.com:\n    user: woonari-user\n")
    monkeypatch.setattr(subject, "_github", lambda *a, **k: pytest.fail("must not try global keychain"))
    with pytest.raises(RuntimeError, match="Keychain"):
        subject.verify_account(project[0], subject.isolated_env())


def test_gh_auth_symlink_is_rejected_before_login(project, monkeypatch):
    hosts = project[2] / "github/hosts.yml"
    hosts.unlink()
    external = project[2] / "external-hosts.yml"
    external.write_text("synthetic shared settings")
    hosts.symlink_to(external)
    digest = hashlib.sha256(external.read_bytes()).digest()
    monkeypatch.setattr(subject, "_github", lambda *a, **k: pytest.fail("symlink auth must not execute"))
    with pytest.raises(RuntimeError, match="일반 파일"):
        subject.main(["gh", "auth", "login"])
    assert hashlib.sha256(external.read_bytes()).digest() == digest


def test_account_verification_passes_only_project_file_token_to_gh(project, monkeypatch):
    seen = []
    monkeypatch.setattr(subject, "_github", lambda args, env, **k: (
        seen.append(env["GH_TOKEN"]) or fake_result(json.dumps({"login": "woonari-user"}))
    ))
    subject.verify_account(project[0], subject.isolated_env())
    assert seen == ["synthetic_project_token"]


def test_modern_per_user_gh_token_is_accepted_without_root_token(project):
    hosts = project[2] / "github/hosts.yml"
    hosts.write_text(
        "github.com:\n    users:\n        another-user:\n            oauth_token: unrelated_token\n"
        "        woonari-user:\n            oauth_token: dedicated_token\n    user: woonari-user\n"
    )
    assert subject._private_gh_token(project[0]) == "dedicated_token"


def test_another_users_nested_token_cannot_replace_missing_dedicated_token(project):
    (project[2] / "github/hosts.yml").write_text(
        "github.com:\n    users:\n        another-user:\n            oauth_token: unrelated_token\n"
        "    user: woonari-user\n"
    )
    with pytest.raises(RuntimeError, match="Keychain"):
        subject._private_gh_token(project[0])


def test_auth_file_ownership_is_checked_before_chmod(project, monkeypatch):
    hosts = project[2] / "github/hosts.yml"
    hosts.chmod(0o644)
    actual_uid = subject.os.getuid()
    monkeypatch.setattr(subject.os, "getuid", lambda: actual_uid + 1)
    with pytest.raises(RuntimeError, match="소유자"):
        subject._secure_gh_files()
    assert hosts.stat().st_mode & 0o777 == 0o644


def test_private_token_file_is_preferred_and_its_value_is_never_printed(project, monkeypatch, capsys):
    token = project[2] / "github/token"
    token.write_text("preferred_project_token\n")
    token.chmod(0o600)
    seen = []
    def github(args, env, **kwargs):
        seen.append((args, env["GH_TOKEN"]))
        return fake_result(json.dumps({"login": "woonari-user"}))
    monkeypatch.setattr(subject, "_github", github)
    assert subject.main(["gh", "auth", "login", "--web"]) == 0
    assert seen == [(["api", "--hostname", "github.com", "user"], "preferred_project_token")]
    assert "preferred_project_token" not in capsys.readouterr().out


def test_missing_project_token_never_invokes_login_or_keychain(project, monkeypatch, capsys):
    (project[2] / "github/hosts.yml").unlink()
    monkeypatch.setattr(subject, "_github", lambda *a, **k: pytest.fail("missing token must not invoke gh"))
    with pytest.raises(RuntimeError, match=r"\.local/woonari/github/token"):
        subject.main(["gh", "auth", "login"])
    assert subject.main(["gh", "auth", "status"]) == 1
    assert "설정되지 않았습니다" in capsys.readouterr().out


@pytest.mark.parametrize("value", ["", "two tokens", "one\ntwo\n", " leading_space"])
def test_invalid_private_token_file_is_rejected_before_network(project, monkeypatch, value):
    path = project[2] / "github/token"
    path.write_text(value)
    path.chmod(0o600)
    monkeypatch.setattr(subject, "_github", lambda *a, **k: pytest.fail("invalid token must not invoke gh"))
    with pytest.raises(RuntimeError, match="한 줄"):
        subject.main(["gh", "auth", "login"])


def test_private_token_permissions_are_rejected_without_chmod(project, monkeypatch):
    path = project[2] / "github/token"
    path.write_text("synthetic_private_token")
    path.chmod(0o644)
    monkeypatch.setattr(subject, "_github", lambda *a, **k: pytest.fail("public token must not invoke gh"))
    with pytest.raises(RuntimeError, match="600"):
        subject.main(["gh", "auth", "login"])
    assert path.stat().st_mode & 0o777 == 0o644


def test_private_token_symlink_is_rejected_without_reading_or_editing_target(project, monkeypatch):
    external = project[2] / "external-token"
    external.write_text("synthetic_external_token")
    (project[2] / "github/token").symlink_to(external)
    before = external.stat().st_mode
    monkeypatch.setattr(subject, "_github", lambda *a, **k: pytest.fail("linked token must not invoke gh"))
    with pytest.raises(RuntimeError, match="심볼릭"):
        subject.main(["gh", "auth", "login"])
    assert external.stat().st_mode == before


def test_auth_status_verifies_only_saved_project_token(project, monkeypatch):
    calls = []
    def github(args, env, **kwargs):
        calls.append(args)
        return fake_result(json.dumps({"login": "woonari-user"}))
    monkeypatch.setattr(subject, "_github", github)
    assert subject.main(["gh", "auth", "status"]) == 0
    assert calls == [["api", "--hostname", "github.com", "user"]]


@pytest.mark.parametrize("branch", ["main", "work/isolation"])
def test_authorized_main_push_keeps_exact_ref_and_account_guards(project, monkeypatch, branch):
    events = []
    monkeypatch.setattr(subject, "configure_repository", lambda *a: None)
    monkeypatch.setattr(subject, "_current_branch", lambda env: branch)
    monkeypatch.setattr(subject, "assert_python_history", lambda env: events.append("history"))
    monkeypatch.setattr(subject, "verify_account", lambda c, e, **k: events.append(k))
    monkeypatch.setattr(subject, "_git", lambda args, env, **k: events.append(args) or fake_result())
    assert subject.main(["git", "push"]) == 0
    assert events == ["history", {"require_write": True}, ["push", "--set-upstream", "origin", branch]]


def test_promote_main_preserves_tip_and_removes_old_local_name(project):
    subject.configure_repository(project[0])
    repo = project[1]
    (repo / "README.md").write_text("Python only\n")
    local_git(project, "add", "--all")
    local_git(project, "commit", "-m", "synthetic Python")
    local_git(project, "branch", "-m", subject.RETIRED_BRANCH)
    head = local_git(project, "rev-parse", "HEAD").stdout
    assert subject.main(["git", "promote-main"]) == 0
    assert local_git(project, "branch", "--show-current").stdout.strip() == "main"
    assert local_git(project, "rev-parse", "HEAD").stdout == head
    assert local_git(project, "show-ref", "--verify", "--quiet", "refs/heads/" + subject.RETIRED_BRANCH, check=False).returncode == 1


@pytest.mark.parametrize("mismatch", ["unpublished", "wrong_default", "unpreserved"])
def test_delete_retired_branch_requires_published_main_default_and_preserved_commits(project, monkeypatch, mismatch):
    monkeypatch.setattr(subject, "verify_account", lambda *a, **k: None)
    monkeypatch.setattr(subject, "assert_python_history", lambda env: None)
    monkeypatch.setattr(subject, "_current_branch", lambda env: "main")
    monkeypatch.setattr(subject, "_github", lambda *a, **k: fake_result(json.dumps({"default_branch": "other" if mismatch == "wrong_default" else "main"})))
    calls = []
    def git(args, env, **kwargs):
        calls.append(args)
        if args[0] == "rev-parse": return fake_result("a" * 40 + "\n")
        if args[:2] == ["ls-remote", "--heads"]:
            ref = args[-1]
            sha = "b" * 40 if mismatch == "unpublished" or ref.endswith(subject.RETIRED_BRANCH) else "a" * 40
            return fake_result(sha + "\t" + ref + "\n")
        if args[0] == "merge-base": return fake_result(code=1)
        pytest.fail("must not push before preservation checks")
    monkeypatch.setattr(subject, "_git", git)
    with pytest.raises(RuntimeError):
        subject.delete_published_branch(project[0], subject.isolated_env())
    assert not any(args[0] == "push" for args in calls)


def test_retired_delete_only_sends_explicit_approved_ref(project, monkeypatch):
    calls = []
    monkeypatch.setattr(subject, "verify_account", lambda *a, **k: None)
    monkeypatch.setattr(subject, "assert_python_history", lambda env: None)
    monkeypatch.setattr(subject, "_published_main", lambda env: "a" * 40)
    monkeypatch.setattr(subject, "_github", lambda *a, **k: fake_result('{"default_branch":"main"}'))
    def git(args, env, **kwargs):
        calls.append(args)
        if args[0] == "ls-remote":
            return fake_result("a" * 40 + "\trefs/heads/" + subject.RETIRED_BRANCH + "\n")
        return fake_result()
    monkeypatch.setattr(subject, "_git", git)
    assert subject.delete_published_branch(project[0], subject.isolated_env()) == 0
    assert calls[-1] == ["push", "origin", "--delete", subject.RETIRED_BRANCH]


def test_default_main_change_is_fixed_and_hides_failed_provider_response(project, monkeypatch):
    calls = []
    monkeypatch.setattr(subject, "configure_repository", lambda *a: None)
    monkeypatch.setattr(subject, "verify_account", lambda *a, **k: None)
    monkeypatch.setattr(subject, "assert_python_history", lambda env: None)
    monkeypatch.setattr(subject, "_published_main", lambda env: "a" * 40)
    monkeypatch.setattr(subject, "_github", lambda args, env, **k: calls.append(args) or fake_result("sensitive", 1))
    with pytest.raises(RuntimeError, match="Administration") as err:
        subject.main(["gh", "set-default-main"])
    assert "sensitive" not in str(err.value)
    assert calls == [["api", "--hostname", "github.com", "--method", "PATCH", subject.API_REPOSITORY, "-f", "default_branch=main"]]

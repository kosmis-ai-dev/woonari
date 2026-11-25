"""CR-022: transactional identities, one-use OAuth state and session rotation."""

import hashlib
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from app.auth_models import SocialIdentity, SocialProvider
from app.auth_store import MySQLAuthStore, SQLiteAuthStore, _schema
from app.errors import DomainError


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


@pytest.fixture
def store(tmp_path):
    value = SQLiteAuthStore(tmp_path / "auth.sqlite3")
    value.initialize()
    return value


def identity(provider=SocialProvider.google, subject="provider-user", **profile):
    return SocialIdentity(provider=provider, subject=subject, **profile)


def login(store, *, label="one", person=None, now=1000, refresh_expires_at=5000):
    return store.login(
        person or identity(), access_hash=digest("access-" + label),
        refresh_hash=digest("refresh-" + label), access_expires_at=now + 100,
        refresh_expires_at=refresh_expires_at, now=now
    )


def rotate(store, old="one", new="two", *, now=1020, access_expires_at=1200):
    return store.rotate_refresh(
        digest("refresh-" + old), access_hash=digest("access-" + new),
        new_refresh_hash=digest("refresh-" + new), access_expires_at=access_expires_at, now=now
    )


def assert_error(code, function, *args, **kwargs):
    with pytest.raises(DomainError) as error:
        function(*args, **kwargs)
    assert error.value.code == code
    return error.value


def test_first_login_and_repeat_login_use_provider_subject_not_email(store):
    first = login(store, person=identity(email="same@example.test", nickname="첫 이름", email_verified=True))
    repeat = login(store, label="repeat", person=identity(email="changed@example.test", nickname="새 이름"))
    other_provider = login(store, label="kakao", person=identity(SocialProvider.kakao, email="same@example.test"))
    other_subject = login(store, label="other", person=identity(subject="other-user", email="same@example.test"))
    assert first.is_new_user and not repeat.is_new_user
    assert first.user.id == repeat.user.id
    assert repeat.user.nickname == "새 이름" and repeat.user.email_verified is False
    assert len({first.user.id, other_provider.user.id, other_subject.user.id}) == 3
    assert repeat.user.providers == [SocialProvider.google]
    assert store.counts()["woonari_auth_users"] == 3


def test_identity_subject_is_case_sensitive_and_profile_optional(store):
    lower = login(store, person=identity(subject="user"))
    upper = login(store, label="upper", person=identity(subject="USER"))
    assert lower.user.id != upper.user.id
    assert lower.user.nickname is None and lower.user.email is None
    assert lower.user.email_verified is False


def test_profile_verified_requires_strict_true_and_actual_email(store):
    value = login(store, person=identity(email=None, email_verified=True))
    assert value.user.email_verified is False
    value = login(store, label="two", person=identity(email="mail@example.test", email_verified=1))
    assert value.user.email_verified is False


def test_access_expiry_refresh_expiry_and_logout_isolate_sessions(store):
    first = login(store)
    second = login(store, label="other")
    assert store.authenticate(digest("access-one"), now=1099).id == first.user.id
    assert_error("unauthorized", store.authenticate, digest("access-one"), now=1100)
    store.logout(digest("access-one"), now=1020)
    store.logout(digest("access-one"), now=1021)
    assert_error("unauthorized", store.authenticate, digest("access-one"), now=1021)
    assert store.authenticate(digest("access-other"), now=1021).id == second.user.id
    assert_error("refresh_token_invalid", rotate, store, now=5000)


def test_refresh_rotation_invalidates_old_access_and_never_extends_refresh(store):
    first = login(store)
    value = rotate(store, access_expires_at=9000)
    assert not value.is_new_user and value.user.id == first.user.id
    assert value.refresh_expires_at == 5000
    assert_error("unauthorized", store.authenticate, digest("access-one"), now=1021)
    assert store.authenticate(digest("access-two"), now=4999).id == first.user.id
    assert_error("unauthorized", store.authenticate, digest("access-two"), now=5000)


def test_reusing_old_refresh_commits_family_revocation_but_not_other_sessions(store):
    login(store)
    login(store, label="separate")
    rotate(store)
    error = assert_error("token_reused", rotate, store, new="stolen", now=1021)
    assert error.status == 401
    assert_error("unauthorized", store.authenticate, digest("access-two"), now=1022)
    assert_error("refresh_token_invalid", rotate, store, old="two", new="third", now=1023)
    assert store.authenticate(digest("access-separate"), now=1023)


def test_concurrent_refresh_consumers_allow_one_rotation_then_revoke(store):
    login(store)
    def attempt(index):
        try:
            rotate(store, new=f"parallel-{index}")
            return "success", index
        except DomainError as error:
            return error.code, index
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, range(2)))
    assert sorted(result[0] for result in results) == ["success", "token_reused"]
    winner = next(index for status, index in results if status == "success")
    assert_error("unauthorized", store.authenticate, digest(f"access-parallel-{winner}"), now=1021)


def test_concurrent_first_logins_create_one_identity_and_user(store):
    def attempt(index):
        return login(store, label=f"parallel-{index}")
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(attempt, range(5)))
    assert len({value.user.id for value in results}) == 1
    assert sum(value.is_new_user for value in results) == 1
    counts = store.counts()
    assert counts["woonari_auth_users"] == counts["woonari_auth_identities"] == 1
    assert counts["woonari_auth_sessions"] == 5


def state(store, **values):
    parameters = {
        "provider": SocialProvider.google, "state_hash": digest("state"),
        "cookie_hash": digest("cookie"), "code_verifier": "v" * 64,
        "nonce": "n" * 32, "now": 1000, "expires_at": 1600
    }
    parameters.update(values)
    store.create_state(**parameters)


def consume(store, **values):
    parameters = {
        "provider": SocialProvider.google, "state_hash": digest("state"),
        "cookie_hash": digest("cookie"), "now": 1010
    }
    parameters.update(values)
    return store.consume_state(**parameters)


@pytest.mark.parametrize("override", [
    {"cookie_hash": digest("wrong")}, {"provider": SocialProvider.kakao},
    {"state_hash": digest("wrong")}
])
def test_wrong_cookie_provider_or_state_cannot_consume_legitimate_attempt(store, override):
    state(store)
    error = assert_error("oauth_state_invalid", consume, store, **override)
    assert error.status == 400
    attempt = consume(store)
    assert attempt.code_verifier == "v" * 64 and attempt.nonce == "n" * 32
    assert_error("oauth_state_invalid", consume, store)


def test_expired_state_is_rejected_and_cleaned_on_next_attempt(store):
    state(store)
    assert_error("oauth_state_invalid", consume, store, now=1600)
    state(store, state_hash=digest("next"), now=1600, expires_at=1700)
    assert store.counts()["woonari_auth_states"] == 1


def test_concurrent_state_consumption_is_one_use(store):
    state(store)
    def attempt(_):
        try:
            consume(store)
            return "success"
        except DomainError as error:
            return error.code
    with ThreadPoolExecutor(max_workers=3) as pool:
        assert sorted(pool.map(attempt, range(3))) == ["oauth_state_invalid", "oauth_state_invalid", "success"]


def test_database_contains_only_hashes_of_session_tokens_and_private_file_mode(store):
    login(store)
    rotate(store)
    with sqlite3.connect(store.path) as connection:
        rows = connection.execute("SELECT access_hash,refresh_hash FROM woonari_auth_sessions").fetchall()
        used = connection.execute("SELECT token_hash FROM woonari_auth_used_refresh").fetchall()
    assert rows == [(digest("access-two"), digest("refresh-two"))]
    assert used == [(digest("refresh-one"),)]
    raw = store.path.read_bytes()
    assert b"access-one" not in raw and b"refresh-two" not in raw
    assert store.path.stat().st_mode & 0o777 == 0o600
    assert store.path.parent.stat().st_mode & 0o777 == 0o700


def test_reopen_does_not_reset_existing_sessions(store):
    first = login(store)
    reopened = SQLiteAuthStore(store.path)
    assert reopened.authenticate(digest("access-one"), now=1010).id == first.user.id


def test_unknown_database_or_modified_schema_is_not_overwritten(tmp_path):
    path = tmp_path / "existing.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE unrelated (value TEXT)")
        connection.execute("INSERT INTO unrelated VALUES ('keep')")
    path.chmod(0o600)
    assert_error("auth_storage_unavailable", SQLiteAuthStore(path).initialize)
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT value FROM unrelated").fetchall() == [("keep",)]


def test_sqlite_schema_tampering_and_world_readable_file_are_rejected(store):
    with sqlite3.connect(store.path) as connection:
        connection.execute("ALTER TABLE woonari_auth_states ADD COLUMN surprise TEXT")
    assert_error("auth_storage_unavailable", SQLiteAuthStore(store.path).initialize)
    store.path.chmod(0o644)
    assert_error("auth_storage_unavailable", SQLiteAuthStore(store.path).initialize)


def test_symlink_database_and_non_private_directory_are_rejected(tmp_path):
    target = tmp_path / "target"
    target.write_text("keep")
    link = tmp_path / "linked.sqlite3"
    link.symlink_to(target)
    assert_error("auth_storage_unavailable", SQLiteAuthStore(link).initialize)
    public = tmp_path / "public"
    public.mkdir(mode=0o755)
    assert_error("auth_storage_unavailable", SQLiteAuthStore(public / "auth.sqlite3").initialize)
    assert target.read_text() == "keep"


def test_failed_session_insert_rolls_back_new_user(store):
    login(store)
    assert_error(
        "auth_storage_unavailable", store.login, identity(subject="another"),
        access_hash=digest("access-one"), refresh_hash=digest("new-refresh"),
        access_expires_at=1100, refresh_expires_at=5000, now=1000
    )
    assert store.counts()["woonari_auth_users"] == 1


@pytest.mark.parametrize("bad", ["raw-token", "x" * 64, "A" * 64, "0" * 63])
def test_store_refuses_unhashed_token_material(store, bad):
    assert_error("auth_storage_unavailable", store.authenticate, bad, now=1000)


class FailedConnection:
    def __call__(self):
        raise RuntimeError("must-not-leak-server-or-secret")


def test_mysql_connection_errors_are_neutral_and_runtime_does_not_run_ddl():
    store = MySQLAuthStore(FailedConnection())
    error = assert_error("auth_storage_unavailable", store.verify)
    assert "must-not-leak" not in error.message
    error = assert_error("auth_storage_unavailable", store.initialize)
    assert error.status == 503


class SchemaCursor:
    def __init__(self, connection):
        self.connection = connection
        self.description = []
        self.rows = []

    def execute(self, statement, parameters=()):
        self.connection.statements.append(statement)
        if statement == "SELECT DATABASE() AS name":
            columns, rows = ["name"], [(self.connection.database,)]
        elif statement.startswith("SELECT GET_LOCK"):
            columns, rows = ["acquired"], [(1,)]
        elif statement.startswith("SELECT RELEASE_LOCK"):
            columns, rows = ["released"], [(1,)]
        elif statement.startswith("SELECT TABLE_NAME,ENGINE"):
            columns = ["TABLE_NAME", "ENGINE"]
            rows = [(parameters[0], "InnoDB")] if self.connection.incompatible else []
        elif statement.startswith("SHOW FULL COLUMNS"):
            columns, rows = ["Field", "Type", "Collation", "Null", "Extra"], [("unexpected", "text", "utf8mb4_bin", "YES", "")]
        else:
            raise AssertionError("Unexpected database operation")
        self.description = [(name,) for name in columns]
        self.rows = rows

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self):
        pass


class SchemaConnection:
    def __init__(self, *, database="woonari", incompatible=False):
        self.database = database
        self.incompatible = incompatible
        self.statements = []

    def cursor(self):
        return SchemaCursor(self)

    def rollback(self):
        pass

    def close(self):
        pass


def test_mysql_runtime_missing_schema_never_creates_tables():
    connection = SchemaConnection()
    store = MySQLAuthStore(lambda: connection)
    assert_error("auth_storage_unavailable", store.authenticate, digest("access"), now=1000)
    assert all(not statement.startswith(("CREATE ", "ALTER ", "DROP ")) for statement in connection.statements)


def test_mysql_initialization_rejects_another_database_before_ddl():
    connection = SchemaConnection(database="another_project")
    assert_error("auth_storage_unavailable", MySQLAuthStore(lambda: connection).initialize)
    assert not any(statement.startswith("CREATE ") for statement in connection.statements)


def test_mysql_preflight_refuses_incompatible_existing_table_before_creating_anything():
    connection = SchemaConnection(incompatible=True)
    assert_error("auth_storage_unavailable", MySQLAuthStore(lambda: connection).initialize)
    assert any(statement.startswith("SHOW FULL COLUMNS") for statement in connection.statements)
    assert not any(statement.startswith(("CREATE ", "ALTER ", "DROP ")) for statement in connection.statements)


def test_sql_schema_never_touches_other_tables_and_identity_is_binary():
    statements = _schema(True)
    assert len(statements) == 5
    assert all(statement.startswith("CREATE TABLE IF NOT EXISTS woonari_auth_") for statement in statements)
    assert "subject VARCHAR(255) COLLATE utf8mb4_bin" in statements[1]
    assert "PRIMARY KEY (provider, subject)" in statements[1]
    assert not any("DROP " in value or "ALTER " in value for value in statements)


def test_relative_path_rejected():
    assert_error("auth_storage_unavailable", SQLiteAuthStore, Path("relative.sqlite3"))


def test_existing_private_store_is_not_chmodded(store):
    original = os.stat(store.path)
    SQLiteAuthStore(store.path).initialize()
    assert os.stat(store.path).st_ino == original.st_ino

"""CR-022: transactional identities, one-use OAuth state and session rotation."""

import hashlib
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from app.auth_models import SocialIdentity, SocialProvider
from app.auth_store import MySQLAuthStore, SQLiteAuthStore, _Cursor, _schema
from app.errors import DomainError
from app.models import Birth


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
    assert len(statements) == 6
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


def birth(**changes):
    return Birth.model_validate({
        "year": 1974, "month": 3, "day": 2, "hour": 8, "minute": 30,
        "gender": "male", "calendar": "solar", "leap_month": False, **changes
    })


def patch_birth(store, changes, *, label="one", now=1020, validator=lambda value: None):
    return store.patch_birth_profile(
        digest("access-" + label), changes, now=now, validator=validator
    )


def test_birth_profile_is_empty_until_owner_saves_and_keeps_original_calendar(store):
    login(store)
    absent = store.get_birth_profile(digest("access-one"), now=1010)
    assert absent.birth is None and absent.updated_at is None
    supplied = birth(year=2023, month=2, day=29, hour=0, minute=0, gender="female", calendar="lunar", leap_month=True)
    saved = store.put_birth_profile(digest("access-one"), supplied, now=1010)
    assert saved.birth.model_dump() == supplied.model_dump()
    assert store.get_birth_profile(digest("access-one"), now=1011) == saved
    assert saved.updated_at == 1010
    assert store.counts()["woonari_auth_birth_profiles"] == 1


def test_birth_put_replaces_one_profile_without_replacing_creation_time(store):
    login(store)
    store.put_birth_profile(digest("access-one"), birth(), now=1010)
    replacement = birth(year=1991, minute=0, gender="female")
    result = store.put_birth_profile(digest("access-one"), replacement, now=1020)
    assert result.birth == replacement and result.updated_at == 1020
    with sqlite3.connect(store.path) as connection:
        assert connection.execute("SELECT created_at,updated_at FROM woonari_auth_birth_profiles").fetchall() == [(1010, 1020)]


def test_birth_access_is_self_only_even_when_email_matches(store):
    login(store, person=identity(email="same@example.test"))
    login(store, label="other", person=identity(SocialProvider.kakao, email="same@example.test"))
    store.put_birth_profile(digest("access-one"), birth(), now=1010)
    assert store.get_birth_profile(digest("access-other"), now=1011).birth is None
    store.put_birth_profile(digest("access-other"), birth(year=1990), now=1012)
    assert store.get_birth_profile(digest("access-one"), now=1013).birth.year == 1974
    assert_error("invalid_birth_profile", patch_birth, store, {"user_id": "other-user"})
    assert store.get_birth_profile(digest("access-other"), now=1021).birth.year == 1990


@pytest.mark.parametrize("operation", ["get", "put", "patch"])
@pytest.mark.parametrize("invalidity", ["expired", "revoked", "unknown"])
def test_birth_reads_and_writes_require_a_current_session(store, operation, invalidity):
    login(store)
    store.put_birth_profile(digest("access-one"), birth(), now=1010)
    if invalidity == "revoked":
        store.logout(digest("access-one"), now=1011)
    token = digest("absent") if invalidity == "unknown" else digest("access-one")
    now = 1100 if invalidity == "expired" else 1020
    call = {
        "get": lambda: store.get_birth_profile(token, now=now),
        "put": lambda: store.put_birth_profile(token, birth(year=1990), now=now),
        "patch": lambda: store.patch_birth_profile(token, {"year": 1990}, now=now, validator=lambda value: None)
    }[operation]
    assert_error("unauthorized", call)
    with sqlite3.connect(store.path) as connection:
        assert connection.execute("SELECT birth_year,updated_at FROM woonari_auth_birth_profiles").fetchall() == [(1974, 1010)]


def test_patch_missing_birth_profile_is_not_an_implicit_partial_insert(store):
    login(store)
    error = assert_error("birth_profile_not_found", patch_birth, store, {"minute": 0})
    assert error.status == 404
    assert store.counts()["woonari_auth_birth_profiles"] == 0


def test_patch_preserves_omitted_fields_and_false_zero_values(store):
    login(store)
    supplied = birth(year=2023, month=2, day=29, calendar="lunar", leap_month=True)
    store.put_birth_profile(digest("access-one"), supplied, now=1010)
    seen = []
    result = patch_birth(store, {"leap_month": False, "hour": 0, "minute": 0}, validator=seen.append)
    assert len(seen) == 1 and seen[0] == result.birth
    assert result.birth.model_dump() == {**supplied.model_dump(), "leap_month": False, "hour": 0, "minute": 0}


@pytest.mark.parametrize("changes", [{"month": 2, "day": 30}, {"year": None}, {"gender": "unknown"}])
def test_invalid_merged_birth_patch_is_422_and_preserves_profile(store, changes):
    login(store)
    original = store.put_birth_profile(digest("access-one"), birth(), now=1010)
    error = assert_error("invalid_birth_profile", patch_birth, store, changes)
    assert error.status == 422
    assert store.get_birth_profile(digest("access-one"), now=1021) == original


def test_calendar_validator_failure_rolls_back_before_birth_write(store):
    login(store)
    original = store.put_birth_profile(digest("access-one"), birth(), now=1010)
    def invalid_calendar(value):
        assert value.calendar == "lunar"
        raise DomainError("invalid_lunar_date", "유효한 음력 날짜가 아닙니다.", 422)
    error = assert_error("invalid_lunar_date", patch_birth, store, {"calendar": "lunar"}, validator=invalid_calendar)
    assert error.status == 422
    assert store.get_birth_profile(digest("access-one"), now=1021) == original


def test_concurrent_sessions_patch_disjoint_fields_without_lost_updates(store):
    login(store)
    login(store, label="other")
    store.put_birth_profile(digest("access-one"), birth(), now=1010)
    requests = [("one", {"hour": 0}), ("other", {"minute": 0})]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda item: patch_birth(store, item[1], label=item[0]), requests))
    final = store.get_birth_profile(digest("access-one"), now=1021)
    assert final.birth.hour == final.birth.minute == 0
    assert len(results) == 2 and final.birth.year == 1974


def test_v1_sqlite_schema_upgrade_preserves_sessions_state_and_marker(store):
    person = login(store)
    state(store)
    with sqlite3.connect(store.path) as connection:
        connection.execute("DROP TABLE woonari_auth_birth_profiles")
        connection.execute("PRAGMA user_version=1")
        marker = connection.execute("PRAGMA application_id").fetchone()[0]
    upgraded = SQLiteAuthStore(store.path)
    assert upgraded.authenticate(digest("access-one"), now=1010).id == person.user.id
    assert consume(upgraded).nonce == "n" * 32
    assert upgraded.get_birth_profile(digest("access-one"), now=1011).birth is None
    with sqlite3.connect(store.path) as connection:
        assert connection.execute("PRAGMA application_id").fetchone()[0] == marker
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2


def test_incompatible_legacy_schema_is_not_partially_upgraded(store):
    login(store)
    with sqlite3.connect(store.path) as connection:
        connection.execute("DROP TABLE woonari_auth_birth_profiles")
        connection.execute("PRAGMA user_version=1")
        connection.execute("ALTER TABLE woonari_auth_states ADD COLUMN unexpected TEXT")
    assert_error("auth_storage_unavailable", SQLiteAuthStore(store.path).initialize)
    with sqlite3.connect(store.path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "woonari_auth_birth_profiles" not in tables
        assert connection.execute("SELECT COUNT(*) FROM woonari_auth_users").fetchone()[0] == 1


def test_corrupt_stored_birth_is_storage_error_and_not_repaired(store):
    login(store)
    store.put_birth_profile(digest("access-one"), birth(), now=1010)
    with sqlite3.connect(store.path) as connection:
        connection.execute("UPDATE woonari_auth_birth_profiles SET leap_month=7")
    error = assert_error("auth_storage_unavailable", store.get_birth_profile, digest("access-one"), now=1011)
    assert error.status == 503 and "7" not in error.message


class BirthSchemaCursor:
    def __init__(self, *, corrupt=None):
        self.corrupt = corrupt
        self.description = []
        self.rows = []
        self.statements = []

    def execute(self, statement, parameters=()):
        self.statements.append(statement)
        if statement.startswith("SELECT TABLE_NAME,ENGINE"):
            fields, rows = ["TABLE_NAME", "ENGINE"], [("woonari_auth_birth_profiles", "InnoDB")]
        elif statement.startswith("SHOW FULL COLUMNS"):
            fields = ["Field", "Type", "Collation", "Null", "Extra"]
            names = [
                "user_id", "birth_year", "birth_month", "birth_day", "birth_hour", "birth_minute",
                "gender", "calendar", "leap_month", "created_at", "updated_at"
            ]
            types = {"user_id": "char(36)", "gender": "varchar(6)", "calendar": "varchar(5)"}
            rows = [(name, types.get(name, "bigint"), "utf8mb4_bin" if name in types else None, "NO", "") for name in names]
            if self.corrupt == "nullable":
                rows[1] = (*rows[1][:3], "YES", "")
            elif self.corrupt == "type":
                rows[6] = ("gender", "varchar(10)", "utf8mb4_bin", "NO", "")
            elif self.corrupt == "collation":
                rows[7] = ("calendar", "varchar(5)", "utf8mb4_general_ci", "NO", "")
        elif statement.startswith("SHOW INDEX"):
            fields = ["Non_unique", "Key_name", "Seq_in_index", "Column_name"]
            rows = [] if self.corrupt == "unique" else [(0, "PRIMARY", 1, "user_id")]
        elif statement.startswith("SELECT COLUMN_NAME,REFERENCED_TABLE_NAME"):
            fields = ["COLUMN_NAME", "REFERENCED_TABLE_NAME", "REFERENCED_COLUMN_NAME"]
            rows = [] if self.corrupt == "foreign" else [("user_id", "woonari_auth_users", "id")]
        else:
            raise AssertionError("Unexpected schema query")
        self.description = [(field,) for field in fields]
        self.rows = rows

    def fetchall(self):
        return self.rows


def test_mysql_birth_schema_requires_types_owner_key_binary_fields_and_fk():
    raw = BirthSchemaCursor()
    assert MySQLAuthStore._verify_mysql(_Cursor(raw, True), "woonari_auth_birth_profiles")
    assert not any(statement.startswith(("CREATE ", "ALTER ", "DROP ")) for statement in raw.statements)


@pytest.mark.parametrize("corruption", ["nullable", "type", "collation", "unique", "foreign"])
def test_mysql_birth_schema_does_not_accept_incompatible_existing_table(corruption):
    raw = BirthSchemaCursor(corrupt=corruption)
    assert_error("auth_storage_unavailable", MySQLAuthStore._verify_mysql, _Cursor(raw, True), "woonari_auth_birth_profiles")
    assert not any(statement.startswith(("CREATE ", "ALTER ", "DROP ")) for statement in raw.statements)


def test_mysql_additive_initialization_creates_only_the_missing_birth_table(monkeypatch):
    class AdditiveCursor(SchemaCursor):
        def execute(self, statement, parameters=()):
            if statement.startswith("CREATE TABLE"):
                assert "woonari_auth_birth_profiles (" in statement
                self.connection.statements.append(statement)
                self.connection.birth_exists = True
            elif statement.startswith("SHOW INDEX"):
                self.connection.statements.append(statement)
                table = statement.split()[-1]
                column = "refresh_expires_at" if table.endswith("sessions") else "expires_at"
                self.description = [("Key_name",)]
                self.rows = [(f"idx_{table}_{column}",)]
            else:
                super().execute(statement, parameters)

    class AdditiveConnection(SchemaConnection):
        birth_exists = False
        committed = False

        def cursor(self):
            return AdditiveCursor(self)

        def commit(self):
            self.committed = True

    connection = AdditiveConnection()
    monkeypatch.setattr(
        MySQLAuthStore, "_verify_mysql",
        staticmethod(lambda cursor, table: table != "woonari_auth_birth_profiles" or connection.birth_exists)
    )
    MySQLAuthStore(lambda: connection).initialize()
    creates = [statement for statement in connection.statements if statement.startswith("CREATE ")]
    assert len(creates) == 1 and "woonari_auth_birth_profiles (" in creates[0]
    assert connection.committed and connection.birth_exists
    assert not any(statement.startswith(("ALTER ", "DROP ")) for statement in connection.statements)

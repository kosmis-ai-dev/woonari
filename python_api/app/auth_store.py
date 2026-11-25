"""CR-022 / T-042: private OAuth attempts and hashed application sessions.

Only the five new authentication tables are created. Existing tables are never
altered, and an incompatible schema stops authentication instead of being reset.
"""

from __future__ import annotations

import os
import re
import sqlite3
import stat
import threading
import uuid
from collections.abc import Callable, Mapping
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any, Protocol

from app.auth_models import AuthUser, OAuthAttempt, SocialIdentity, SocialProvider, StoredLogin
from app.errors import DomainError

_APPLICATION_ID = 0x574E4155
_HASH = re.compile(r"[a-f0-9]{64}\Z")
_TABLES = {
    "woonari_auth_users": (
        "id", "nickname", "email", "email_verified", "created_at", "updated_at"
    ),
    "woonari_auth_identities": (
        "provider", "subject", "user_id", "created_at", "updated_at"
    ),
    "woonari_auth_sessions": (
        "id", "user_id", "access_hash", "refresh_hash", "access_expires_at",
        "refresh_expires_at", "revoked_at", "created_at", "updated_at"
    ),
    "woonari_auth_used_refresh": ("token_hash", "session_id", "expires_at"),
    "woonari_auth_states": (
        "state_hash", "cookie_hash", "provider", "code_verifier", "nonce", "expires_at", "created_at"
    )
}


def _unavailable() -> DomainError:
    return DomainError("auth_storage_unavailable", "로그인 저장소를 사용할 수 없습니다.", 503)


def _unauthorized(code: str = "unauthorized") -> DomainError:
    return DomainError(code, "로그인 정보가 만료되었거나 유효하지 않습니다.", 401)


def _hash(value: str) -> None:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise _unavailable()


def _identity(value: SocialIdentity) -> SocialIdentity:
    if (
        not isinstance(value.subject, str) or not 1 <= len(value.subject) <= 255
        or any(ord(char) < 32 for char in value.subject)
    ):
        raise DomainError("social_login_failed", "소셜 계정 정보를 확인할 수 없습니다.", 401)
    try:
        provider = SocialProvider(value.provider)
    except ValueError:
        raise DomainError("social_login_failed", "소셜 계정 정보를 확인할 수 없습니다.", 401) from None
    return SocialIdentity(
        provider=provider, subject=value.subject,
        nickname=value.nickname[:100] if isinstance(value.nickname, str) and value.nickname else None,
        email=value.email[:320] if isinstance(value.email, str) and value.email else None,
        email_verified=value.email_verified is True and bool(value.email)
    )


class AuthStore(Protocol):
    def initialize(self) -> None: ...

    def create_state(
        self, *, provider: SocialProvider, state_hash: str, cookie_hash: str,
        code_verifier: str, nonce: str, now: int, expires_at: int
    ) -> None: ...

    def consume_state(
        self, *, provider: SocialProvider, state_hash: str, cookie_hash: str, now: int
    ) -> OAuthAttempt: ...

    def login(
        self, identity: SocialIdentity, *, access_hash: str, refresh_hash: str,
        access_expires_at: int, refresh_expires_at: int, now: int
    ) -> StoredLogin: ...

    def authenticate(self, access_hash: str, *, now: int) -> AuthUser: ...

    def rotate_refresh(
        self, refresh_hash: str, *, access_hash: str, new_refresh_hash: str,
        access_expires_at: int, now: int
    ) -> StoredLogin: ...

    def logout(self, access_hash: str, *, now: int) -> None: ...


def _schema(mysql: bool) -> list[str]:
    text = "VARCHAR(100)" if mysql else "TEXT"
    identifier = "CHAR(36) CHARACTER SET ascii COLLATE ascii_bin" if mysql else "TEXT"
    digest = "CHAR(64) CHARACTER SET ascii COLLATE ascii_bin" if mysql else "TEXT"
    provider = "VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin" if mysql else "TEXT"
    subject = "VARCHAR(255) COLLATE utf8mb4_bin" if mysql else "TEXT COLLATE BINARY"
    secret = "VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin" if mysql else "TEXT"
    email = "VARCHAR(320)" if mysql else "TEXT"
    integer = "BIGINT" if mysql else "INTEGER"
    suffix = " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin" if mysql else ""
    return [
        f"CREATE TABLE IF NOT EXISTS woonari_auth_users (id {identifier} PRIMARY KEY, "
        f"nickname {text} NULL, email {email} NULL, email_verified {integer} NOT NULL, "
        f"created_at {integer} NOT NULL, updated_at {integer} NOT NULL){suffix}",
        f"CREATE TABLE IF NOT EXISTS woonari_auth_identities (provider {provider} NOT NULL, "
        f"subject {subject} NOT NULL, user_id {identifier} NOT NULL, created_at {integer} NOT NULL, "
        f"updated_at {integer} NOT NULL, PRIMARY KEY (provider, subject), "
        "FOREIGN KEY (user_id) REFERENCES woonari_auth_users(id))" + suffix,
        f"CREATE TABLE IF NOT EXISTS woonari_auth_sessions (id {identifier} PRIMARY KEY, "
        f"user_id {identifier} NOT NULL, access_hash {digest} NOT NULL UNIQUE, "
        f"refresh_hash {digest} NOT NULL UNIQUE, access_expires_at {integer} NOT NULL, "
        f"refresh_expires_at {integer} NOT NULL, revoked_at {integer} NULL, "
        f"created_at {integer} NOT NULL, updated_at {integer} NOT NULL, "
        "FOREIGN KEY (user_id) REFERENCES woonari_auth_users(id))" + suffix,
        f"CREATE TABLE IF NOT EXISTS woonari_auth_used_refresh (token_hash {digest} PRIMARY KEY, "
        f"session_id {identifier} NOT NULL, expires_at {integer} NOT NULL, "
        "FOREIGN KEY (session_id) REFERENCES woonari_auth_sessions(id))" + suffix,
        f"CREATE TABLE IF NOT EXISTS woonari_auth_states (state_hash {digest} PRIMARY KEY, "
        f"cookie_hash {digest} NOT NULL, provider {provider} NOT NULL, "
        f"code_verifier {secret} NOT NULL, nonce {secret} NOT NULL, "
        f"expires_at {integer} NOT NULL, created_at {integer} NOT NULL){suffix}"
    ]


class _Cursor:
    def __init__(self, cursor: Any, mysql: bool):
        self.cursor = cursor
        self.mysql = mysql

    def execute(self, statement: str, parameters: tuple = ()) -> None:
        self.cursor.execute(statement if self.mysql else statement.replace("%s", "?"), parameters)

    def all(self) -> list[dict]:
        columns = [column[0] for column in self.cursor.description or ()]
        return [dict(row) if isinstance(row, Mapping) else dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def one(self) -> dict | None:
        values = self.all()
        return values[0] if values else None


class _Store:
    mysql = False

    def __init__(self):
        self._initialized = False
        self._initialize_lock = threading.Lock()

    def _connect(self):
        raise NotImplementedError

    def _ensure(self) -> None:
        if not self._initialized:
            self.initialize()

    @property
    def _locked(self) -> str:
        return " FOR UPDATE" if self.mysql else ""

    @contextmanager
    def _transaction(self):
        self._ensure()
        connection = None
        cursor = None
        try:
            connection = self._connect()
            if self.mysql:
                connection.begin()
            else:
                connection.execute("BEGIN IMMEDIATE")
            cursor = connection.cursor()
            yield _Cursor(cursor, self.mysql)
            connection.commit()
        except DomainError:
            if connection is not None:
                with suppress(Exception):
                    connection.rollback()
            raise
        except Exception:
            if connection is not None:
                with suppress(Exception):
                    connection.rollback()
            raise _unavailable() from None
        finally:
            if cursor is not None:
                with suppress(Exception):
                    cursor.close()
            if connection is not None:
                with suppress(Exception):
                    connection.close()

    def create_state(
        self, *, provider: SocialProvider, state_hash: str, cookie_hash: str,
        code_verifier: str, nonce: str, now: int, expires_at: int
    ) -> None:
        _hash(state_hash)
        _hash(cookie_hash)
        if not (43 <= len(code_verifier) <= 128 and 20 <= len(nonce) <= 128 and expires_at > now):
            raise _unavailable()
        with self._transaction() as cursor:
            cursor.execute("DELETE FROM woonari_auth_states WHERE expires_at <= %s", (now,))
            cursor.execute(
                "INSERT INTO woonari_auth_states "
                "(state_hash,cookie_hash,provider,code_verifier,nonce,expires_at,created_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (state_hash, cookie_hash, str(provider), code_verifier, nonce, expires_at, now)
            )

    def consume_state(
        self, *, provider: SocialProvider, state_hash: str, cookie_hash: str, now: int
    ) -> OAuthAttempt:
        _hash(state_hash)
        _hash(cookie_hash)
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT code_verifier,nonce FROM woonari_auth_states WHERE state_hash=%s "
                "AND cookie_hash=%s AND provider=%s AND expires_at>%s" + self._locked,
                (state_hash, cookie_hash, str(provider), now)
            )
            row = cursor.one()
            if row is None:
                raise DomainError("oauth_state_invalid", "로그인 요청이 만료되었거나 유효하지 않습니다.", 400)
            cursor.execute("DELETE FROM woonari_auth_states WHERE state_hash=%s", (state_hash,))
            return OAuthAttempt(code_verifier=row["code_verifier"], nonce=row["nonce"])

    @staticmethod
    def _user(cursor: _Cursor, user_id: str) -> AuthUser:
        cursor.execute("SELECT id,nickname,email,email_verified,created_at FROM woonari_auth_users WHERE id=%s", (user_id,))
        row = cursor.one()
        if row is None:
            raise _unavailable()
        cursor.execute("SELECT provider FROM woonari_auth_identities WHERE user_id=%s ORDER BY provider", (user_id,))
        return AuthUser(
            id=row["id"], nickname=row["nickname"], email=row["email"],
            email_verified=bool(row["email_verified"]), created_at=row["created_at"],
            providers=[SocialProvider(item["provider"]) for item in cursor.all()]
        )

    def login(
        self, identity: SocialIdentity, *, access_hash: str, refresh_hash: str,
        access_expires_at: int, refresh_expires_at: int, now: int
    ) -> StoredLogin:
        identity = _identity(identity)
        _hash(access_hash)
        _hash(refresh_hash)
        if not now < access_expires_at <= refresh_expires_at:
            raise _unavailable()
        # Serialize a provider key even before its first identity row exists.
        # SQLite BEGIN IMMEDIATE covers all writers. MySQL uses a short advisory
        # lock on a one-way digest, preventing first-login gap-lock races.
        with self._login_lock(identity):
            with self._transaction() as cursor:
                cursor.execute(
                    "SELECT user_id FROM woonari_auth_identities WHERE provider=%s AND subject=%s" + self._locked,
                    (str(identity.provider), identity.subject)
                )
                row = cursor.one()
                is_new = row is None
                user_id = str(uuid.uuid4()) if is_new else row["user_id"]
                if is_new:
                    cursor.execute(
                        "INSERT INTO woonari_auth_users (id,nickname,email,email_verified,created_at,updated_at) "
                        "VALUES (%s,%s,%s,%s,%s,%s)",
                        (user_id, identity.nickname, identity.email, int(identity.email_verified), now, now)
                    )
                    cursor.execute(
                        "INSERT INTO woonari_auth_identities (provider,subject,user_id,created_at,updated_at) "
                        "VALUES (%s,%s,%s,%s,%s)",
                        (str(identity.provider), identity.subject, user_id, now, now)
                    )
                else:
                    cursor.execute(
                        "UPDATE woonari_auth_users SET nickname=%s,email=%s,email_verified=%s,updated_at=%s WHERE id=%s",
                        (identity.nickname, identity.email, int(identity.email_verified), now, user_id)
                    )
                    cursor.execute(
                        "UPDATE woonari_auth_identities SET updated_at=%s WHERE provider=%s AND subject=%s",
                        (now, str(identity.provider), identity.subject)
                    )
                cursor.execute(
                    "INSERT INTO woonari_auth_sessions "
                    "(id,user_id,access_hash,refresh_hash,access_expires_at,refresh_expires_at,revoked_at,created_at,updated_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,NULL,%s,%s)",
                    (str(uuid.uuid4()), user_id, access_hash, refresh_hash, access_expires_at, refresh_expires_at, now, now)
                )
                return StoredLogin(self._user(cursor, user_id), is_new, refresh_expires_at)

    @contextmanager
    def _login_lock(self, identity: SocialIdentity):
        yield

    def authenticate(self, access_hash: str, *, now: int) -> AuthUser:
        _hash(access_hash)
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT user_id FROM woonari_auth_sessions WHERE access_hash=%s "
                "AND access_expires_at>%s AND refresh_expires_at>%s AND revoked_at IS NULL",
                (access_hash, now, now)
            )
            row = cursor.one()
            if row is None:
                raise _unauthorized()
            return self._user(cursor, row["user_id"])

    def rotate_refresh(
        self, refresh_hash: str, *, access_hash: str, new_refresh_hash: str,
        access_expires_at: int, now: int
    ) -> StoredLogin:
        for digest in (refresh_hash, access_hash, new_refresh_hash):
            _hash(digest)
        with self._refresh_lock(refresh_hash):
            return self._rotate_refresh(
                refresh_hash, access_hash=access_hash, new_refresh_hash=new_refresh_hash,
                access_expires_at=access_expires_at, now=now
            )

    @contextmanager
    def _refresh_lock(self, refresh_hash: str):
        yield

    def _rotate_refresh(
        self, refresh_hash: str, *, access_hash: str, new_refresh_hash: str,
        access_expires_at: int, now: int
    ) -> StoredLogin:
        result = None
        replay = False
        with self._transaction() as cursor:
            cursor.execute(
                "SELECT id,user_id,refresh_expires_at,revoked_at FROM woonari_auth_sessions "
                "WHERE refresh_hash=%s" + self._locked, (refresh_hash,)
            )
            row = cursor.one()
            if row is None:
                cursor.execute(
                    "SELECT session_id FROM woonari_auth_used_refresh WHERE token_hash=%s AND expires_at>%s" + self._locked,
                    (refresh_hash, now)
                )
                used = cursor.one()
                if used is None:
                    raise _unauthorized("refresh_token_invalid")
                cursor.execute(
                    "UPDATE woonari_auth_sessions SET revoked_at=%s,updated_at=%s WHERE id=%s AND revoked_at IS NULL",
                    (now, now, used["session_id"])
                )
                replay = True
            elif row["revoked_at"] is not None or row["refresh_expires_at"] <= now:
                raise _unauthorized("refresh_token_invalid")
            else:
                expiry = min(access_expires_at, row["refresh_expires_at"])
                if expiry <= now:
                    raise _unauthorized("refresh_token_invalid")
                cursor.execute(
                    "INSERT INTO woonari_auth_used_refresh (token_hash,session_id,expires_at) VALUES (%s,%s,%s)",
                    (refresh_hash, row["id"], row["refresh_expires_at"])
                )
                cursor.execute(
                    "UPDATE woonari_auth_sessions SET access_hash=%s,refresh_hash=%s,access_expires_at=%s,updated_at=%s WHERE id=%s",
                    (access_hash, new_refresh_hash, expiry, now, row["id"])
                )
                result = StoredLogin(self._user(cursor, row["user_id"]), False, row["refresh_expires_at"])
        # Raising only after the transaction commits preserves replay revocation.
        if replay:
            raise _unauthorized("token_reused")
        if result is None:
            raise _unavailable()
        return result

    def logout(self, access_hash: str, *, now: int) -> None:
        _hash(access_hash)
        with self._transaction() as cursor:
            cursor.execute("SELECT id FROM woonari_auth_sessions WHERE access_hash=%s" + self._locked, (access_hash,))
            row = cursor.one()
            if row is None:
                raise _unauthorized()
            cursor.execute(
                "UPDATE woonari_auth_sessions SET revoked_at=%s,updated_at=%s WHERE id=%s AND revoked_at IS NULL",
                (now, now, row["id"])
            )

    def counts(self) -> dict[str, int]:
        with self._transaction() as cursor:
            result = {}
            for table in _TABLES:
                cursor.execute(f"SELECT COUNT(*) AS total FROM {table}")
                result[table] = int(cursor.one()["total"])
            return result

    def close(self) -> None:
        pass


class SQLiteAuthStore(_Store):
    """Independent development store; official runtime injects MySQL instead."""

    def __init__(self, path: Path):
        super().__init__()
        self.path = Path(path)
        if not self.path.is_absolute() or ".." in self.path.parts:
            raise _unavailable()

    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialize(self) -> None:
        with self._initialize_lock:
            if self._initialized:
                return
            connection = None
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                parent = self.path.parent.lstat()
                if not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid() or parent.st_mode & 0o077:
                    raise _unavailable()
                created = False
                try:
                    descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                    os.close(descriptor)
                    created = True
                except FileExistsError:
                    pass
                info = self.path.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                    raise _unavailable()
                connection = self._connect()
                connection.execute("BEGIN IMMEDIATE")
                application_id = connection.execute("PRAGMA application_id").fetchone()[0]
                if application_id != _APPLICATION_ID and not (created and application_id == 0):
                    raise _unavailable()
                existing = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
                if existing and existing != set(_TABLES):
                    raise _unavailable()
                if not existing:
                    for statement in _schema(False):
                        connection.execute(statement)
                    for table, columns in (
                        ("woonari_auth_identities", "user_id"), ("woonari_auth_sessions", "user_id"),
                        ("woonari_auth_sessions", "refresh_expires_at"), ("woonari_auth_used_refresh", "session_id"),
                        ("woonari_auth_states", "expires_at")
                    ):
                        connection.execute(f"CREATE INDEX idx_{table}_{columns} ON {table}({columns})")
                    connection.execute(f"PRAGMA application_id={_APPLICATION_ID}")
                    connection.execute("PRAGMA user_version=1")
                self._verify_sqlite(connection)
                connection.commit()
                self._initialized = True
            except DomainError:
                if connection:
                    connection.rollback()
                raise
            except Exception:
                if connection:
                    connection.rollback()
                raise _unavailable() from None
            finally:
                if connection:
                    connection.close()

    @staticmethod
    def _verify_sqlite(connection) -> None:
        if connection.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise _unavailable()
        def normalize(sql):
            return " ".join(sql.replace("IF NOT EXISTS ", "").split()).lower()

        for (table, expected), statement in zip(_TABLES.items(), _schema(False)):
            columns = tuple(row[1] for row in connection.execute(f"PRAGMA table_info({table})"))
            if columns != expected:
                raise _unavailable()
            stored = connection.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()[0]
            if normalize(stored) != normalize(statement):
                raise _unavailable()
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise _unavailable()


class MySQLAuthStore(_Store):
    mysql = True

    def __init__(self, connector: Callable[[], Any]):
        super().__init__()
        self.connector = connector

    def _connect(self):
        return self.connector()

    def _ensure(self) -> None:
        if not self._initialized:
            self.verify()

    @contextmanager
    def _login_lock(self, identity: SocialIdentity):
        import hashlib

        name = "wn-auth-" + hashlib.sha256((str(identity.provider) + "\0" + identity.subject).encode()).hexdigest()[:48]
        with self._advisory_lock(name):
            yield

    @contextmanager
    def _refresh_lock(self, refresh_hash: str):
        with self._advisory_lock("wn-refresh-" + refresh_hash[:48]):
            yield

    @contextmanager
    def _advisory_lock(self, name: str):
        connection = None
        cursor = None
        try:
            self._ensure()
            connection = self._connect()
            cursor = connection.cursor()
            cursor.execute("SELECT GET_LOCK(%s, 5)", (name,))
            value = cursor.fetchone()
            acquired = next(iter(value.values())) if isinstance(value, Mapping) else value[0]
            if acquired != 1:
                raise _unavailable()
            yield
        except DomainError:
            raise
        except Exception:
            raise _unavailable() from None
        finally:
            if cursor is not None:
                with suppress(Exception):
                    cursor.execute("SELECT RELEASE_LOCK(%s)", (name,))
                    cursor.close()
            if connection is not None:
                with suppress(Exception):
                    connection.close()

    @staticmethod
    def _verify_mysql(cursor: _Cursor, table: str) -> bool:
        cursor.execute("SELECT TABLE_NAME,ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s", (table,))
        table_row = cursor.one()
        if table_row is None:
            return False
        if table_row["ENGINE"] != "InnoDB":
            raise _unavailable()
        cursor.execute(f"SHOW FULL COLUMNS FROM {table}")
        columns = cursor.all()
        if tuple(row["Field"] for row in columns) != _TABLES[table]:
            raise _unavailable()
        for row in columns:
            field, data_type = row["Field"], str(row["Type"]).lower()
            expected_type = (
                "char(36)" if field in {"id", "user_id", "session_id"}
                else "char(64)" if field.endswith("_hash") or field == "token_hash"
                else "varchar(16)" if field == "provider"
                else "varchar(255)" if field == "subject"
                else "varchar(128)" if field in {"code_verifier", "nonce"}
                else "varchar(100)" if field == "nickname"
                else "varchar(320)" if field == "email"
                else "bigint"
            )
            if expected_type == "bigint":
                if not re.fullmatch(r"bigint(?:\([0-9]+\))?", data_type):
                    raise _unavailable()
            elif data_type != expected_type:
                raise _unavailable()
            nullable = field in {"nickname", "email", "revoked_at"}
            if (row["Null"] == "YES") != nullable or row["Extra"]:
                raise _unavailable()
            if row["Field"] in {"id", "user_id", "session_id", "provider", "subject", "state_hash", "cookie_hash", "access_hash", "refresh_hash", "token_hash"}:
                if not str(row["Collation"]).endswith("_bin"):
                    raise _unavailable()
        cursor.execute(f"SHOW INDEX FROM {table}")
        indexes = cursor.all()
        unique = {}
        for row in indexes:
            if int(row["Non_unique"]) == 0:
                unique.setdefault(row["Key_name"], []).append((int(row["Seq_in_index"]), row["Column_name"]))
        unique_columns = {tuple(column for _, column in sorted(values)) for values in unique.values()}
        expected_unique = {
            "woonari_auth_users": {("id",)},
            "woonari_auth_identities": {("provider", "subject")},
            "woonari_auth_sessions": {("id",), ("access_hash",), ("refresh_hash",)},
            "woonari_auth_used_refresh": {("token_hash",)},
            "woonari_auth_states": {("state_hash",)}
        }[table]
        if unique_columns != expected_unique:
            raise _unavailable()
        cursor.execute(
            "SELECT COLUMN_NAME,REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME "
            "FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() "
            "AND TABLE_NAME=%s AND REFERENCED_TABLE_NAME IS NOT NULL", (table,)
        )
        foreign_keys = {
            (row["COLUMN_NAME"], row["REFERENCED_TABLE_NAME"], row["REFERENCED_COLUMN_NAME"])
            for row in cursor.all()
        }
        expected_foreign = (
            {("user_id", "woonari_auth_users", "id")} if table in {"woonari_auth_identities", "woonari_auth_sessions"}
            else {("session_id", "woonari_auth_sessions", "id")} if table == "woonari_auth_used_refresh"
            else set()
        )
        if foreign_keys != expected_foreign:
            raise _unavailable()
        return True

    def verify(self) -> None:
        """Verify deployed schema without issuing DDL during API requests."""
        with self._initialize_lock:
            if self._initialized:
                return
            connection = None
            raw = None
            try:
                connection = self._connect()
                raw = connection.cursor()
                cursor = _Cursor(raw, True)
                cursor.execute("SELECT DATABASE() AS name")
                if cursor.one()["name"] != "woonari":
                    raise _unavailable()
                if not all(self._verify_mysql(cursor, table) for table in _TABLES):
                    raise _unavailable()
                self._initialized = True
            except DomainError:
                raise
            except Exception:
                raise _unavailable() from None
            finally:
                if raw is not None:
                    with suppress(Exception):
                        raw.close()
                if connection is not None:
                    with suppress(Exception):
                        connection.close()

    def initialize(self) -> None:
        with self._initialize_lock:
            if self._initialized:
                return
            connection = None
            raw = None
            try:
                connection = self._connect()
                raw = connection.cursor()
                cursor = _Cursor(raw, True)
                cursor.execute("SELECT DATABASE() AS name")
                if cursor.one()["name"] != "woonari":
                    raise _unavailable()
                cursor.execute("SELECT GET_LOCK('woonari_auth_schema_v1',5) AS acquired")
                if cursor.one()["acquired"] != 1:
                    raise _unavailable()
                # Preflight everything before creating even one missing table.
                existing = {table for table in _TABLES if self._verify_mysql(cursor, table)}
                for table, statement in zip(_TABLES, _schema(True)):
                    if table not in existing:
                        cursor.execute(statement)
                for table in _TABLES:
                    self._verify_mysql(cursor, table)
                # Query indexes before adding to keep repeated initialization safe.
                for table, column in (
                    ("woonari_auth_sessions", "refresh_expires_at"),
                    ("woonari_auth_used_refresh", "expires_at"),
                    ("woonari_auth_states", "expires_at")
                ):
                    cursor.execute(f"SHOW INDEX FROM {table}")
                    name = f"idx_{table}_{column}"
                    if not any(row["Key_name"] == name for row in cursor.all()):
                        cursor.execute(f"CREATE INDEX {name} ON {table}({column})")
                connection.commit()
                self._initialized = True
            except DomainError:
                if connection:
                    with suppress(Exception):
                        connection.rollback()
                raise
            except Exception:
                if connection:
                    with suppress(Exception):
                        connection.rollback()
                raise _unavailable() from None
            finally:
                if raw is not None:
                    with suppress(Exception):
                        raw.execute("SELECT RELEASE_LOCK('woonari_auth_schema_v1')")
                        raw.close()
                if connection is not None:
                    with suppress(Exception):
                        connection.close()

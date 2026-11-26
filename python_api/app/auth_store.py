"""CR-022 / T-042: private OAuth attempts and hashed application sessions.

Only the dedicated authentication tables are created. Existing tables are never
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

from app.auth_models import (
    AuthUser,
    MemberBirthProfile,
    OAuthAttempt,
    SocialIdentity,
    SocialProvider,
    StoredLogin,
)
from app.errors import DomainError
from app.models import Birth

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
    ),
    "woonari_auth_birth_profiles": (
        "user_id", "birth_year", "birth_month", "birth_day", "birth_hour", "birth_minute",
        "gender", "calendar", "leap_month", "created_at", "updated_at"
    )
}
_LEGACY_TABLES = tuple(_TABLES)[:-1]
_BIRTH_FIELDS = ("year", "month", "day", "hour", "minute", "gender", "calendar", "leap_month")


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

    def get_birth_profile(self, access_hash: str, *, now: int) -> MemberBirthProfile: ...

    def put_birth_profile(self, access_hash: str, birth: Birth, *, now: int) -> MemberBirthProfile: ...

    def patch_birth_profile(
        self, access_hash: str, changes: dict, *, now: int, validator: Callable[[Birth], None]
    ) -> MemberBirthProfile: ...


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
        f"expires_at {integer} NOT NULL, created_at {integer} NOT NULL){suffix}",
        f"CREATE TABLE IF NOT EXISTS woonari_auth_birth_profiles (user_id {identifier} PRIMARY KEY, "
        f"birth_year {integer} NOT NULL, birth_month {integer} NOT NULL, birth_day {integer} NOT NULL, "
        f"birth_hour {integer} NOT NULL, birth_minute {integer} NOT NULL, "
        "gender VARCHAR(6) NOT NULL, calendar VARCHAR(5) NOT NULL, "
        f"leap_month {integer} NOT NULL, created_at {integer} NOT NULL, updated_at {integer} NOT NULL, "
        "FOREIGN KEY (user_id) REFERENCES woonari_auth_users(id))" + suffix
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

    def _birth_user(self, cursor: _Cursor, access_hash: str, now: int, *, lock: bool) -> str:
        cursor.execute(
            "SELECT user_id FROM woonari_auth_sessions WHERE access_hash=%s "
            "AND access_expires_at>%s AND refresh_expires_at>%s AND revoked_at IS NULL"
            + (self._locked if lock else ""),
            (access_hash, now, now)
        )
        session = cursor.one()
        if session is None:
            raise _unauthorized()
        user_id = session["user_id"]
        if lock:
            # All sessions of one member serialize through the same user row,
            # including the first profile insert when no profile row exists yet.
            cursor.execute("SELECT id FROM woonari_auth_users WHERE id=%s" + self._locked, (user_id,))
            if cursor.one() is None:
                raise _unavailable()
        return user_id

    def _birth_row(self, cursor: _Cursor, user_id: str, *, lock: bool = False) -> dict | None:
        cursor.execute(
            "SELECT birth_year,birth_month,birth_day,birth_hour,birth_minute,gender,calendar,"
            "leap_month,created_at,updated_at FROM woonari_auth_birth_profiles WHERE user_id=%s"
            + (self._locked if lock else ""), (user_id,)
        )
        return cursor.one()

    @staticmethod
    def _birth_profile(row: dict | None) -> MemberBirthProfile:
        if row is None:
            return MemberBirthProfile()
        try:
            if type(row["leap_month"]) is not int or row["leap_month"] not in (0, 1):
                raise ValueError
            if (
                type(row["created_at"]) is not int or type(row["updated_at"]) is not int
                or row["created_at"] < 0 or row["updated_at"] < row["created_at"]
            ):
                raise ValueError
            values = {
                field: row[f"birth_{field}"] if field in {"year", "month", "day", "hour", "minute"}
                else bool(row["leap_month"]) if field == "leap_month" else row[field]
                for field in _BIRTH_FIELDS
            }
            return MemberBirthProfile(birth=Birth.model_validate(values), updated_at=row["updated_at"])
        except (KeyError, TypeError, ValueError):
            # Database corruption is a storage failure, not user-supplied data.
            raise _unavailable() from None

    @staticmethod
    def _validated_birth(values: dict) -> Birth:
        try:
            return Birth.model_validate(values)
        except (TypeError, ValueError):
            raise DomainError("invalid_birth_profile", "생년월일시·성별·양력/음력 입력을 확인하세요.", 422) from None

    def get_birth_profile(self, access_hash: str, *, now: int) -> MemberBirthProfile:
        _hash(access_hash)
        with self._transaction() as cursor:
            user_id = self._birth_user(cursor, access_hash, now, lock=False)
            return self._birth_profile(self._birth_row(cursor, user_id))

    @staticmethod
    def _write_birth(cursor: _Cursor, user_id: str, birth: Birth, now: int, *, existing: bool) -> None:
        values = (
            birth.year, birth.month, birth.day, birth.hour, birth.minute,
            birth.gender, birth.calendar, int(birth.leap_month)
        )
        if existing:
            cursor.execute(
                "UPDATE woonari_auth_birth_profiles SET birth_year=%s,birth_month=%s,birth_day=%s,"
                "birth_hour=%s,birth_minute=%s,gender=%s,calendar=%s,leap_month=%s,updated_at=%s "
                "WHERE user_id=%s", (*values, now, user_id)
            )
        else:
            cursor.execute(
                "INSERT INTO woonari_auth_birth_profiles "
                "(user_id,birth_year,birth_month,birth_day,birth_hour,birth_minute,gender,calendar,"
                "leap_month,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (user_id, *values, now, now)
            )

    def put_birth_profile(self, access_hash: str, birth: Birth, *, now: int) -> MemberBirthProfile:
        _hash(access_hash)
        birth = self._validated_birth(birth.model_dump())
        with self._transaction() as cursor:
            user_id = self._birth_user(cursor, access_hash, now, lock=True)
            row = self._birth_row(cursor, user_id, lock=True)
            if row is not None:
                self._birth_profile(row)
            self._write_birth(cursor, user_id, birth, now, existing=row is not None)
            return MemberBirthProfile(birth=birth, updated_at=now)

    def patch_birth_profile(
        self, access_hash: str, changes: dict, *, now: int, validator: Callable[[Birth], None]
    ) -> MemberBirthProfile:
        _hash(access_hash)
        with self._transaction() as cursor:
            user_id = self._birth_user(cursor, access_hash, now, lock=True)
            profile = self._birth_profile(self._birth_row(cursor, user_id, lock=True))
            if profile.birth is None:
                raise DomainError("birth_profile_not_found", "저장된 생년월일시가 없습니다. 먼저 전체 정보를 저장하세요.", 404)
            birth = self._validated_birth({**profile.birth.model_dump(), **changes})
            validator(birth)
            self._write_birth(cursor, user_id, birth, now, existing=True)
            return MemberBirthProfile(birth=birth, updated_at=now)

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
                if existing and existing not in (set(_TABLES), set(_LEGACY_TABLES)):
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
                    connection.execute("PRAGMA user_version=2")
                elif existing == set(_LEGACY_TABLES):
                    # Only the exact, marked v1 schema can receive this additive
                    # migration. Existing users, identities and sessions survive.
                    self._verify_sqlite(connection, legacy=True)
                    connection.execute(_schema(False)[-1])
                    connection.execute("PRAGMA user_version=2")
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
    def _verify_sqlite(connection, *, legacy: bool = False) -> None:
        if connection.execute("PRAGMA user_version").fetchone()[0] != (1 if legacy else 2):
            raise _unavailable()
        def normalize(sql):
            return " ".join(sql.replace("IF NOT EXISTS ", "").split()).lower()

        tables = list(_TABLES.items())[:len(_LEGACY_TABLES)] if legacy else _TABLES.items()
        for (table, expected), statement in zip(tables, _schema(False)):
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
                else "varchar(6)" if field == "gender"
                else "varchar(5)" if field == "calendar"
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
            if row["Field"] in {"id", "user_id", "session_id", "provider", "subject", "state_hash", "cookie_hash", "access_hash", "refresh_hash", "token_hash", "gender", "calendar"}:
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
            "woonari_auth_states": {("state_hash",)},
            "woonari_auth_birth_profiles": {("user_id",)}
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
            {("user_id", "woonari_auth_users", "id")} if table in {"woonari_auth_identities", "woonari_auth_sessions", "woonari_auth_birth_profiles"}
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

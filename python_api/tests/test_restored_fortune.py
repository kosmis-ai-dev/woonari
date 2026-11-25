"""CR-014: staging coverage must never authorize a personal AI judgment."""

import json
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import app.restored_fortune as restored
from app.ai_quota import DailyAIQuota
from app.config import Settings
from app.errors import DomainError
from app.main import create_app


def provenance(source, count):
    digest = restored.DATA_HASHES[source]
    payload = {
        "format": "woonari.restored-fortune.v1", "source_table": source,
        "source_sha256": restored.SOURCE_HASHES[source], "data_sha256": digest,
        "row_count": count, "mapping_status": "unverified",
    }
    return (source, restored.SOURCE_HASHES[source], digest, count, json.dumps(payload))


class Connection:
    def __init__(self, *, year_counts=(140, Decimal(0), Decimal(140), 140)):
        self.database = "woonari"
        self.metadata = [provenance("TB_yearLuck", 7000), provenance("TB_yearLuck_mon", 1200)]
        self.year_counts = year_counts
        self.total_counts = [7000, 1200]
        self.queries = []
        self.closed = False

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def execute(self, sql, parameters=()):
        assert sql.startswith("SELECT ")
        self.queries.append((sql, parameters))
        if "DATABASE()" in sql:
            self.result = [(self.database,)]
        elif "metadata" in sql:
            self.result = self.metadata
        elif "SUM(" in sql:
            self.result = [self.year_counts]
        else:
            self.result = [(self.total_counts.pop(0),)]

    def fetchone(self):
        return self.result[0]

    def fetchall(self):
        return self.result

    def close(self):
        self.closed = True


def test_present_2027_rows_are_reported_as_empty_templates():
    connection = Connection()
    value = restored.MySQLRestoredFortuneStore(lambda: connection).status(2027)
    assert value["annual"]["row_count"] == 140
    assert value["annual"]["placeholder_rows"] == 140
    assert value["annual"]["nonempty_content_rows"] == 0
    assert not value["annual"]["all_rows_have_content"]
    assert not value["ready_for_ai"]
    assert "초기 행" in value["issues"][0]
    assert value["required_mapping"]
    assert connection.queries[-1][1] == (2027,)
    assert connection.closed
    assert "contents" not in value


def test_nonempty_historical_rows_still_require_source_mapping():
    connection = Connection(year_counts=(140, Decimal(140), Decimal(0), 140))
    value = restored.MySQLRestoredFortuneStore(lambda: connection).status(2020)
    assert value["annual"]["all_rows_have_content"]
    assert value["annual"]["placeholder_rows"] == 0
    assert not value["ready_for_ai"]
    assert "매핑" in value["issues"][-1]


@pytest.mark.parametrize("corrupt", ["database", "missing_metadata", "hash", "count", "coverage"])
def test_missing_or_mismatched_source_is_unavailable(corrupt):
    connection = Connection()
    if corrupt == "database":
        connection.database = "another_project"
    elif corrupt == "missing_metadata":
        connection.metadata.pop()
    elif corrupt == "hash":
        row = connection.metadata[0]
        connection.metadata[0] = (row[0], "b" * 64, *row[2:])
    elif corrupt == "count":
        connection.total_counts[0] -= 1
    else:
        connection.year_counts = (140, Decimal(0), Decimal(140), 139)
    with pytest.raises(DomainError) as error:
        restored.MySQLRestoredFortuneStore(lambda: connection).status(2027)
    assert error.value.code == "restored_data_unavailable"
    assert error.value.status == 503
    assert connection.closed


def test_connection_failure_does_not_echo_driver_details():
    def connect():
        raise RuntimeError("private-database-password")

    with pytest.raises(DomainError) as error:
        restored.MySQLRestoredFortuneStore(connect).status(2027)
    assert "private-database-password" not in error.value.message


@pytest.mark.parametrize("year", [2000, 2051, True, "2027"])
def test_invalid_years_do_not_reach_store(year, monkeypatch):
    monkeypatch.setattr(restored, "_factory", lambda: pytest.fail("store must not be opened"))
    with pytest.raises(DomainError) as error:
        restored.restored_data_status(year)
    assert error.value.code == "invalid_restored_year"


def test_swagger_diagnostic_is_authorized_and_never_calls_ai(tmp_path, monkeypatch):
    monkeypatch.setattr(restored, "_factory", lambda: restored.MySQLRestoredFortuneStore(Connection))
    interpreter = SimpleNamespace(close=AsyncMock(), interpret=AsyncMock())
    quota = DailyAIQuota(tmp_path / "usage.sqlite3", private_root=tmp_path)
    application = create_app(
        Settings(_env_file=None, api_key="synthetic-test-api"),
        interpreter_factory=lambda _: interpreter, ai_quota=quota,
    )
    with TestClient(application) as client:
        assert client.get("/v1/restored-data").status_code == 404
        headers = {"X-API-Key": "synthetic-test-api"}
        response = client.get("/v1/restored-data?year=2027", headers=headers)
        assert response.status_code == 404
        assert client.get("/v1/restored-data?year=2051", headers=headers).status_code == 404
        assert client.get("/v1/ai-usage", headers=headers).json()["used"] == 0
        assert "/v1/restored-data" not in client.get("/openapi.json").json()["paths"]
    interpreter.interpret.assert_not_called()


def test_unconfigured_diagnostics_do_not_claim_a_database_connection(monkeypatch):
    monkeypatch.setattr(restored, "_factory", None)
    assert restored.restored_data_status()["status"] == "not_connected"

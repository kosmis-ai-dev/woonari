"""CR-012: public service examples execute their ported source contracts."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ai import interpretation_payload
from app.config import Settings
from app.main import create_app
from app.models import Interpretation
from app.service_engine import analyze_service, handlers
from app.service_models import ServiceRequest

BIRTH = {"year": 1990, "month": 5, "day": 17, "hour": 14, "minute": 30, "gender": "male"}
PARTNER = {**BIRTH, "year": 1992, "month": 7, "day": 15, "gender": "female"}


class ContractInterpreter:
    name, model = "contract-test", "no-network"

    def __init__(self):
        self.calls = 0

    async def interpret(self, analysis):
        self.calls += 1
        return Interpretation(
            summary="원본 계산을 따르는 모의 해석입니다.",
            sections=[{
                "target_id": target.id, "topic": target.topic,
                "text": "판정 근거를 살펴 차분히 행동해 보세요.",
                "evidence_ids": target.evidence_ids,
            } for target in analysis.narrative_contract],
            practical_advice=["오늘 할 일을 정리해 보세요."],
        )

    async def close(self):
        pass


@pytest.fixture(scope="module")
def client():
    interpreter = ContractInterpreter()
    application = create_app(
        Settings(_env_file=None, api_key=None), interpreter_factory=lambda _: interpreter,
    )
    with TestClient(application) as value:
        yield value, application.openapi(), interpreter


def _sample(metadata):
    body = {
        "target_date": "2026-11-18", "include_ai": False,
        "parameters": metadata.get("example_parameters", {}),
    }
    if metadata.get("requires_birth"):
        body["birth"] = BIRTH
    if metadata.get("requires_partner"):
        body["partner"] = PARTNER
    return body


def test_every_registered_service_example_runs_its_python_rules(client):
    api, _, interpreter = client
    calls = interpreter.calls
    for service_id, (_, metadata) in handlers().items():
        response = api.post(f"/v1/un/{service_id}", json=_sample(metadata))
        assert response.status_code == 200, (service_id, response.text)
        data = response.json()
        assert data["analysis"]["service_id"] == service_id
        assert data["content"] is None
        if not metadata.get("ready", True):
            assert data["analysis"]["unresolved_dependencies"], service_id
        elif metadata.get("calculation_only"):
            assert data["analysis"]["calculation_only"], service_id
            assert not data["analysis"]["unresolved_dependencies"], service_id
        else:
            assert data["analysis"]["ready_for_ai"], service_id
        if not data["analysis"]["ready_for_ai"] and not data["analysis"]["calculation_only"]:
            assert data["analysis"]["unresolved_dependencies"], service_id
    assert interpreter.calls == calls


def test_ready_services_deliver_validated_human_content_with_mock_transport(client):
    api, _, interpreter = client
    for service_id, (_, metadata) in handlers().items():
        if not metadata.get("ready", True) or metadata.get("calculation_only"):
            continue
        response = api.post(f"/v1/un/{service_id}", json={**_sample(metadata), "include_ai": True})
        assert response.status_code == 200, (service_id, response.text)
        data = response.json()
        assert next(iter(data)) == "content"
        assert data["content"].startswith("원본 계산을 따르는 모의 해석입니다.")
        assert len(data["interpretation"]["sections"]) == len(data["analysis"]["narrative_contract"])
    assert interpreter.calls > 0


@pytest.mark.parametrize("service_id", ["menu-im68", "menu-im90"])
def test_missing_algorithm_is_diagnostic_and_never_delegated_to_ai(client, service_id):
    api, _, interpreter = client
    body = {"target_date": "2026-11-18", "include_ai": False}
    before = interpreter.calls
    result = api.post(f"/v1/un/{service_id}", json=body)
    assert result.status_code == 200
    assert result.json()["analysis"]["unresolved_dependencies"]
    blocked = api.post(f"/v1/un/{service_id}", json={**body, "include_ai": True})
    assert blocked.status_code == 503
    assert interpreter.calls == before


def test_existing_service_adapter_preserves_the_original_decisions():
    result = analyze_service("todayluck", ServiceRequest(
        birth=BIRTH, target_date="2026-11-18", include_ai=False,
    ))
    assert result.kind == "daily"
    assert result.ready_for_ai and len(result.scores) == 8
    assert interpretation_payload(result)["requested_focus"] == result.title


@pytest.mark.parametrize("service_id", ["interlife-free-12", "interlife-manse-2"])
def test_calendar_only_service_rejects_ai_and_returns_calculation(client, service_id):
    api, _, interpreter = client
    metadata = handlers()[service_id][1]
    body = _sample(metadata)
    before = interpreter.calls
    response = api.post(f"/v1/un/{service_id}", json=body)
    assert response.status_code == 200
    analysis = response.json()["analysis"]
    assert analysis["calculation_only"] and not analysis["ready_for_ai"]
    assert not analysis["unresolved_dependencies"]
    response = api.post(f"/v1/un/{service_id}", json={**body, "include_ai": True})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ai_not_applicable"
    assert interpreter.calls == before


def test_non_saju_service_payload_uses_the_ported_service_context():
    result = analyze_service("analysisluck", ServiceRequest(
        birth=BIRTH, target_date="2026-11-18", include_ai=False,
    ))
    assert result.saju is None
    assert [s["where"]["Num"] for s in result.selectors] == [10] * 4
    assert len(result.narrative_contract) == 4
    payload = interpretation_payload(result)
    assert payload["kind"] == "analysisluck"
    assert payload["requested_focus"] == "연인 심리분석"


def test_python_rules_do_not_read_asp_source_at_runtime(monkeypatch):
    read_text, read_bytes = Path.read_text, Path.read_bytes

    def guarded(original):
        def read(path, *args, **kwargs):
            assert path.suffix.lower() != ".asp", "ASP source is provenance, not a runtime dependency."
            return original(path, *args, **kwargs)
        return read

    monkeypatch.setattr(Path, "read_text", guarded(read_text))
    monkeypatch.setattr(Path, "read_bytes", guarded(read_bytes))
    for service_id, (_, metadata) in handlers().items():
        assert analyze_service(service_id, ServiceRequest(**_sample(metadata))).service_id == service_id


def test_unknown_service_and_invalid_existing_parameters_are_safe(client):
    api, _, _ = client
    response = api.post("/v1/un/no-such-service", json={"target_date": "2026-11-18", "include_ai": False})
    assert response.status_code == 404
    response = api.post("/v1/un/todayluck", json={
        "birth": BIRTH, "target_date": "2026-11-18", "include_ai": False,
        "parameters": {"unknown_input": ["private-fixture"]},
    })
    assert response.status_code == 422
    assert "private-fixture" not in response.text


def test_service_catalog_and_concrete_korean_operations_cover_all_items(client):
    api, schema, _ = client
    items = api.get("/v1/un-services").json()["items"]
    assert len(items) == len({item["id"] for item in items}) == 291
    for item in items:
        operation = schema["paths"][f"/v1/un/{item['id']}"]["post"]
        assert item["name"] in operation["summary"]
        assert not any(p["in"] == "query" for p in operation.get("parameters", []))


@pytest.mark.parametrize("service_id,parameters", [
    ("loveunse-life-all", {}),
    ("loveunse-flower", {"source_profile": "asp_original_unconverted"}),
])
def test_loveunse_api_validates_birth_order_using_its_original_calendar(client, service_id, parameters):
    api, _, _ = client
    # Original lun2sol=1990-10-18; tb_manse gives 1990-10-19 for this lunar date.
    body = {"birth": {**BIRTH, "year": 1990, "month": 9, "day": 1, "calendar": "lunar"},
            "target_date": "1990-10-18", "include_ai": False, "parameters": parameters}
    response = api.post(f"/v1/un/{service_id}", json=body)
    assert response.status_code == 200
    if parameters:
        assert response.json()["analysis"]["evidence"][0]["facts"]["self_profile"]["calendar_action"] == "explicit_original_unconverted_lunar_digits"
    previous = api.post(f"/v1/un/{service_id}", json={**body, "target_date": "1990-10-17"})
    assert previous.status_code == 422
    assert previous.json()["error"]["code"] == "target_before_birth"


def test_loveunse_calendar_hook_checks_partner_and_never_calls_manse_for_dates(client, monkeypatch):
    api, _, _ = client
    monkeypatch.setattr("app.service_engine.solar_birth", lambda _: pytest.fail("source-specific date must not use tb_manse"))
    body = {"birth": BIRTH, "partner": {**PARTNER, "year": 1990, "month": 9, "day": 1, "calendar": "lunar"},
            "target_date": "1990-10-18", "include_ai": False}
    assert api.post("/v1/un/loveunse-gunghap", json=body).status_code == 200
    previous = api.post("/v1/un/loveunse-gunghap", json={**body, "target_date": "1990-10-17"})
    assert previous.status_code == 422
    assert previous.json()["error"]["code"] == "target_before_birth"


def test_explicit_unconverted_profile_preserves_digits_without_allowing_invalid_dates(client):
    api, _, _ = client
    body = {"birth": {**BIRTH, "month": 1, "day": 30, "calendar": "lunar"},
            "target_date": "2026-11-18", "include_ai": False,
            "parameters": {"source_profile": "asp_original_unconverted"}}
    invalid = api.post("/v1/un/loveunse-flower", json=body)
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "invalid_loveunse_lunar_date"
    invalid_type = api.post("/v1/un/loveunse-flower", json={**body, "parameters": {"source_profile": []}})
    assert invalid_type.status_code == 422
    assert invalid_type.json()["error"]["code"] == "invalid_service_parameters"

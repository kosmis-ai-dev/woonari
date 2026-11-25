"""CR-013 / T-028: all public AI routes share one durable attempt limit.

The actual Bedrock interpreter validates simulated Converse responses. No API
key, AWS transport or real model is used, including when the allowance is spent.
"""

import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.ai_quota import DailyAIQuota
from app.bedrock import TOOL_NAME, BedrockInterpreter
from app.config import Settings
from app.main import create_app

BIRTH = {"year": 1990, "month": 5, "day": 17, "hour": 14, "minute": 30, "gender": "male"}
DAY = "2026-11-19"


class SimulatedConverse:
    def __init__(self, *, fail=False):
        self.calls = 0
        self.fail = fail

    async def __call__(self, request):
        self.calls += 1
        if self.fail:
            raise RuntimeError("private-simulated-upstream-detail")
        payload = json.loads(request["messages"][0]["content"][0]["text"])
        interpretation = {
            "summary": "계산 결과를 따르는 모의 해석입니다.",
            "sections": [{
                "target_id": target["id"], "topic": target["topic"],
                "text": "확정한 근거를 살펴 차분하게 계획을 세워 보세요.",
                "evidence_ids": target["evidence_ids"],
            } for target in payload["narrative_contract"]],
            "practical_advice": ["오늘 할 일의 우선순위를 정해 보세요."],
        }
        return {"stopReason": "tool_use", "output": {"message": {
            "role": "assistant", "content": [{"toolUse": {
                "toolUseId": "simulated-tool", "name": TOOL_NAME,
                "input": interpretation,
            }}],
        }}}


def quota_at(tmp_path):
    private = tmp_path / "private"
    return DailyAIQuota(
        private / "ai/usage.sqlite3", private_root=private, limit=2,
        clock=lambda: datetime(2026, 11, 19, 3, tzinfo=UTC),
    )


def application(quota, transport, *, api_key=None):
    settings = Settings(
        _env_file=None, ai_provider="bedrock", api_key=api_key,
        bedrock_model_id="fixture-claude-model", bedrock_region="ap-northeast-2",
    )
    return create_app(
        settings, ai_quota=quota,
        interpreter_factory=lambda config: BedrockInterpreter(config, invoker=transport),
    )


def request(*, include_ai=True):
    return {"birth": BIRTH, "target_date": DAY, "include_ai": include_ai}


def test_aliases_and_additional_services_share_limit_across_app_restart(tmp_path):
    transport = SimulatedConverse()
    first_quota = quota_at(tmp_path)
    with TestClient(application(first_quota, transport)) as client:
        initial = client.get("/v1/ai-usage")
        assert initial.status_code == 200
        assert initial.json()["used"] == 0 and initial.json()["remaining"] == 2
        response = client.post("/v1/fortunes/daily", json=request())
        assert response.status_code == 200
        assert response.json()["content"]
        assert len(response.json()["interpretation"]["sections"]) == 3
        assert client.get("/v1/ai-usage").json()["used"] == 1

    # A fresh app/interpreter/quota object must retain the same day's allowance.
    with TestClient(application(quota_at(tmp_path), transport)) as client:
        # Changing the requested fortune date cannot open another daily budget.
        response = client.post("/v1/un/todayluck", json={
            **request(), "target_date": "2001-11-19", "parameters": {},
        })
        assert response.status_code == 200
        exhausted = client.post("/v1/un/analysisluck", json={**request(), "parameters": {}})
        assert exhausted.status_code == 429
        assert exhausted.json()["error"]["code"] == "ai_daily_limit_reached"
        status = client.get("/v1/ai-usage").json()
        assert (status["limit"], status["used"], status["remaining"]) == (2, 2, 0)
        assert status["date"] == DAY and status["timezone"] == "Asia/Seoul"
        assert status["reset_at"] == "2026-11-20T00:00:00+09:00"
    assert transport.calls == 2


def test_calculation_invalid_and_unready_requests_do_not_consume_allowance(tmp_path):
    transport = SimulatedConverse()
    quota = quota_at(tmp_path)
    with TestClient(application(quota, transport)) as client:
        assert client.post("/v1/fortunes/daily", json=request(include_ai=False)).status_code == 200
        invalid = client.post("/v1/fortunes/daily", json={**request(), "target_date": "not-a-date"})
        assert invalid.status_code == 422
        annual_calculation = client.post(
            "/v1/fortunes/yearly", json={**request(), "target_date": "2027-01-01", "include_ai": False},
        )
        assert annual_calculation.status_code == 200
        assert annual_calculation.json()["result"]["kind"] == "yearly"
        unavailable = client.post("/v1/un/menu-im90", json={"target_date": DAY, "include_ai": True})
        assert unavailable.status_code == 503
        assert unavailable.json()["error"]["code"] == "result_unavailable"
        calculation = client.post("/v1/un/interlife-free-12", json={**request(), "parameters": {}})
        assert calculation.status_code == 422
        assert calculation.json()["error"]["code"] == "ai_not_applicable"
        assert client.post("/v1/saju", json={"birth": BIRTH}).status_code == 200
        for _ in range(2):
            status = client.get("/v1/ai-usage").json()
            assert (status["used"], status["remaining"]) == (0, 2)
    assert transport.calls == 0


def test_failed_upstream_attempts_are_not_refunded(tmp_path):
    transport = SimulatedConverse(fail=True)
    quota = quota_at(tmp_path)
    with TestClient(application(quota, transport)) as client:
        for path in ("/v1/fortunes/daily", "/v1/un/analysisluck"):
            failure = client.post(path, json=request())
            assert failure.status_code == 502
            assert failure.json()["error"]["code"] == "ai_upstream_error"
            assert "private-simulated-upstream-detail" not in failure.text
        exhausted = client.post("/v1/un/todayluck", json=request())
        assert exhausted.status_code == 429
        assert client.get("/v1/ai-usage").json()["used"] == 2
    assert transport.calls == 2


def test_usage_endpoint_requires_api_auth_and_never_consumes_a_call(tmp_path):
    transport = SimulatedConverse()
    quota = quota_at(tmp_path)
    api_key = "test-api-key-not-an-aws-key"
    with TestClient(application(quota, transport, api_key=api_key)) as client:
        unauthorized = client.get("/v1/ai-usage")
        assert unauthorized.status_code == 401
        response = client.get("/v1/ai-usage", headers={"X-API-Key": api_key})
        assert response.status_code == 200
        assert response.json()["used"] == 0
        assert response.json()["remaining"] == 2
        assert api_key not in response.text
    assert transport.calls == 0


def test_yearly_aliases_share_persistent_daily_limit(tmp_path):
    transport = SimulatedConverse()
    quota = quota_at(tmp_path)
    with TestClient(application(quota, transport)) as client:
        body = {**request(), "target_date": "2027-01-01"}
        first = client.post("/v1/fortunes/yearly", json=body)
        assert first.status_code == 200, first.text
        second = client.post("/v1/un/2014yearluck", json={**body, "parameters": {}})
        assert second.status_code == 200, second.text
        third = client.post("/v1/fortunes/yearly", json=body)
        assert third.status_code == 429
        assert third.json()["error"]["code"] == "ai_daily_limit_reached"
        assert client.get("/v1/ai-usage").json()["used"] == 2
    assert transport.calls == 2

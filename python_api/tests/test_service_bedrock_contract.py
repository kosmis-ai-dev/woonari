"""T-024: every ready source contract survives the real adapter with mock transport.

This verifies Python serialization and tool-response validation, not AWS access
or the quality of externally generated prose.
"""

import asyncio
import json

from app.bedrock import TOOL_NAME, BedrockInterpreter
from app.config import Settings
from app.legacy_catalog import services
from app.service_engine import analyze_service, handlers
from app.service_models import ServiceRequest


def test_all_ready_services_serialize_and_validate_bedrock_tool_contracts():
    async def check():
        seen = []

        async def invoke(request):
            payload = json.loads(request["messages"][0]["content"][0]["text"])
            assert "1990-05-17T14:30" not in json.dumps(payload)
            assert request["inferenceConfig"]["maxTokens"] == 8192
            seen.append(payload["kind"])
            result = {
                "summary": "모의 전송 검증용 한국어 해석입니다.",
                "sections": [{
                    "target_id": item["id"], "topic": item["topic"],
                    "text": "확정한 계산 근거를 살펴 차분히 계획을 세워 보세요.",
                    "evidence_ids": item["evidence_ids"],
                } for item in payload["narrative_contract"]],
                "practical_advice": ["오늘 할 일을 차근차근 정리해 보세요."],
            }
            return {"stopReason": "tool_use", "output": {"message": {
                "role": "assistant", "content": [{"toolUse": {
                    "toolUseId": "mock-contract", "name": TOOL_NAME, "input": result,
                }}],
            }}}

        backend = BedrockInterpreter(Settings(
            _env_file=None, ai_provider="bedrock", bedrock_region="ap-northeast-2",
            bedrock_model_id="global.anthropic.claude-sonnet-4-6",
        ), invoker=invoke)
        for item in services():
            if item["status"] != "ready":
                continue
            metadata = handlers().get(item["id"], (None, {}))[1]
            body = {"target_date": "2026-11-18", "parameters": metadata.get("example_parameters", {})}
            birth = {"year": 1990, "month": 5, "day": 17, "hour": 14, "minute": 30, "gender": "male"}
            if metadata.get("requires_birth") or item.get("api_kind"):
                body["birth"] = birth
            if metadata.get("requires_partner"):
                body["partner"] = {**birth, "year": 1992, "gender": "female"}
            analysis = analyze_service(item["id"], ServiceRequest(**body))
            response = await backend.interpret(analysis)
            assert len(response.sections) == len(analysis.narrative_contract), item["id"]
        assert len(seen) == 63
        assert "yearly" in seen
        await backend.close()

    asyncio.run(check())

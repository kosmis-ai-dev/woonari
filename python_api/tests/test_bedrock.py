"""CR-011 / T-021: validate Claude's contract through a fake Converse transport."""

import asyncio
import json
from copy import deepcopy
from unittest.mock import AsyncMock

import pytest

from app.bedrock import TOOL_NAME, BedrockInterpreter, interpretation_schema
from app.config import Settings
from app.errors import DomainError
from app.fortunes import analyze
from app.models import FortuneKind, FortuneRequest, Interpretation


@pytest.fixture
def analysis():
    return analyze(
        FortuneKind.daily,
        FortuneRequest(
            birth={"year": 1990, "month": 5, "day": 17, "hour": 14, "gender": "male"},
            target_date="2026-11-02",
            include_ai=False,
        ),
    )


def interpretation(analysis):
    return Interpretation(
        summary="확정된 계산 근거를 설명하는 모의 응답입니다.",
        sections=[
            {
                "target_id": target.id,
                "topic": target.topic,
                "text": "해당 항목의 근거를 설명합니다.",
                "evidence_ids": target.evidence_ids,
            }
            for target in analysis.narrative_contract
        ],
        practical_advice=["우선순위를 정해 차분히 진행하세요."],
    )


def response(analysis):
    return {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"toolUse": {
                    "toolUseId": "fixture-tool-use",
                    "name": TOOL_NAME,
                    "input": interpretation(analysis).model_dump(),
                }}],
            }
        },
    }


def provider(invoker=None, **changes):
    settings = Settings(
        _env_file=None,
        **({
            "ai_provider": "bedrock",
            "bedrock_model_id": "fixture-claude-model",
            "bedrock_region": "ap-northeast-2",
            "bedrock_max_tokens": 1234,
        } | changes),
    )
    return BedrockInterpreter(settings, invoker=invoker)


def test_converse_request_preserves_contract_and_omits_private_birth(analysis):
    invoker = AsyncMock(return_value=response(analysis))
    before = analysis.model_dump()
    result = asyncio.run(provider(invoker).interpret(analysis))

    assert result == interpretation(analysis)
    assert analysis.model_dump() == before
    invoker.assert_awaited_once()
    request = invoker.call_args.args[0]
    assert request["modelId"] == "fixture-claude-model"
    assert request["inferenceConfig"] == {"maxTokens": 1234}
    assert request["messages"][0]["role"] == "user"
    payload = json.loads(request["messages"][0]["content"][0]["text"])
    assert payload["kind"] == "daily"
    assert payload["narrative_contract"] == [
        target.model_dump(mode="json") for target in analysis.narrative_contract
    ]
    encoded = json.dumps(payload, ensure_ascii=False)
    assert "1990-05-17" not in encoded
    assert "solar_birth" not in encoded and "legacy_memno" not in encoded
    assert "birth" not in payload and "name" not in payload
    tools = request["toolConfig"]["tools"]
    assert len(tools) == 1
    assert tools[0]["toolSpec"]["name"] == TOOL_NAME
    schema = tools[0]["toolSpec"]["inputSchema"]["json"]
    assert schema == interpretation_schema(analysis)
    section = schema["$defs"]["InterpretationSection"]["properties"]
    assert section["target_id"]["enum"] == [t.id for t in analysis.narrative_contract]
    assert section["topic"]["enum"] == list(dict.fromkeys(t.topic for t in analysis.narrative_contract))
    assert section["evidence_ids"]["items"]["enum"] == [e.id for e in analysis.evidence]
    assert "enum" not in Interpretation.model_json_schema()["$defs"]["InterpretationSection"]["properties"]["target_id"]
    assert request["toolConfig"]["toolChoice"] == {"tool": {"name": TOOL_NAME}}


def test_unresolved_source_is_rejected_before_calling_claude(analysis):
    unresolved = analysis.model_copy(update={"ready_for_ai": False})
    invoker = AsyncMock()
    with pytest.raises(DomainError) as error:
        asyncio.run(provider(invoker).interpret(unresolved))
    assert error.value.code == "legacy_dependency_unavailable"
    assert error.value.status == 503
    invoker.assert_not_called()


def test_missing_bedrock_settings_or_transport_never_fakes_an_answer(analysis):
    for changes, connected in [({}, False), ({"bedrock_model_id": ""}, True),
                               ({"bedrock_region": ""}, True)]:
        invoker = AsyncMock() if connected else None
        with pytest.raises(DomainError) as error:
            asyncio.run(provider(invoker, **changes).interpret(analysis))
        assert error.value.code == "bedrock_not_configured"
        assert error.value.status == 503
        if invoker is not None:
            invoker.assert_not_called()


def test_missing_tool_response_is_rejected(analysis):
    malformed = response(analysis)
    malformed["output"]["message"]["content"] = [{"text": "도구 결과가 없습니다."}]
    invoker = AsyncMock(return_value=malformed)
    with pytest.raises(DomainError) as error:
        asyncio.run(provider(invoker).interpret(analysis))
    assert error.value.code == "ai_invalid_response"
    assert error.value.status == 502


def test_malformed_tool_input_is_rejected_without_echoing_it(analysis):
    malformed = response(analysis)
    malformed["output"]["message"]["content"][0]["toolUse"]["input"] = "private-invalid-input"
    with pytest.raises(DomainError) as error:
        asyncio.run(provider(AsyncMock(return_value=malformed)).interpret(analysis))
    assert error.value.code == "ai_invalid_response"
    assert "private-invalid-input" not in error.value.message


def test_wrong_role_tool_name_and_multiple_tools_are_rejected(analysis):
    for mutation in ("role", "name", "multiple"):
        malformed = response(analysis)
        message = malformed["output"]["message"]
        if mutation == "role":
            message["role"] = "user"
        elif mutation == "name":
            message["content"][0]["toolUse"]["name"] = "unknown_tool"
        else:
            message["content"].append(deepcopy(message["content"][0]))
        with pytest.raises(DomainError) as error:
            asyncio.run(provider(AsyncMock(return_value=malformed)).interpret(analysis))
        assert error.value.code == "ai_invalid_response", mutation


def test_token_limit_and_refusal_do_not_return_partial_content(analysis):
    for reason in ("max_tokens", "refusal"):
        incomplete = response(analysis)
        incomplete["stopReason"] = reason
        with pytest.raises(DomainError) as error:
            asyncio.run(provider(AsyncMock(return_value=incomplete)).interpret(analysis))
        assert error.value.code == "ai_incomplete_response", reason
        assert error.value.status == 502


def test_original_target_and_evidence_are_enforced(analysis):
    for mutation, expected in [
        ("target", "ai_contract_mismatch"),
        ("evidence", "ai_invalid_evidence"),
    ]:
        invalid = response(analysis)
        section = invalid["output"]["message"]["content"][0]["toolUse"]["input"]["sections"][0]
        if mutation == "target":
            section["target_id"] = "invented-target"
        else:
            section["evidence_ids"] = ["imaginary-evidence"]
        with pytest.raises(DomainError) as error:
            asyncio.run(provider(AsyncMock(return_value=invalid)).interpret(analysis))
        assert error.value.code == expected, mutation
        assert error.value.status == 502


def test_fixed_labels_are_bound_by_python_without_changing_prose_or_input(analysis):
    incoming = response(analysis)
    section = incoming["output"]["message"]["content"][0]["toolUse"]["input"]["sections"][0]
    section["topic"] = "모델이 바꾼 표현"
    invoker = AsyncMock(return_value=incoming)
    result = asyncio.run(provider(invoker).interpret(analysis))
    assert result == interpretation(analysis)
    assert section["topic"] == "모델이 바꾼 표현"


def test_label_binding_does_not_repair_duplicate_targets_or_bad_evidence(analysis):
    for mutation, expected in (("duplicate", "ai_contract_mismatch"),
                               ("evidence", "ai_invalid_evidence")):
        incoming = response(analysis)
        sections = incoming["output"]["message"]["content"][0]["toolUse"]["input"]["sections"]
        sections[0]["topic"] = "모델이 바꾼 표현"
        if mutation == "duplicate":
            sections[1]["target_id"] = sections[0]["target_id"]
        else:
            sections[0]["evidence_ids"] = ["unknown-evidence"]
        with pytest.raises(DomainError) as error:
            asyncio.run(provider(AsyncMock(return_value=incoming)).interpret(analysis))
        assert error.value.code == expected


def test_account_verification_and_unknown_transport_errors_are_sanitized(analysis):
    for code, expected, status in [
        ("bedrock_account_verification", "bedrock_account_verification", 503),
        ("bedrock_use_case_required", "bedrock_use_case_required", 503),
        ("unrecognized_private_code", "ai_upstream_error", 502),
    ]:
        failure = RuntimeError("private-transport-detail-and-prompt")
        failure.code = code
        with pytest.raises(DomainError) as error:
            asyncio.run(provider(AsyncMock(side_effect=failure)).interpret(analysis))
        assert error.value.code == expected
        assert error.value.status == status
        assert "private-transport-detail-and-prompt" not in error.value.message
        assert "unrecognized_private_code" not in error.value.message


def test_timeout_cancels_the_call_and_returns_a_safe_error(analysis):
    cancelled = []

    async def delayed(request):
        try:
            await asyncio.sleep(1)
        finally:
            cancelled.append(True)

    p = provider(delayed, ai_timeout_seconds=0.01)
    with pytest.raises(DomainError) as error:
        asyncio.run(p.interpret(analysis))
    assert error.value.code == "ai_timeout"
    assert error.value.status == 504
    assert cancelled == [True]

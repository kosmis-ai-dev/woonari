import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.ai import OpenAIInterpreter, interpretation_payload
from app.config import Settings
from app.errors import DomainError
from app.fortunes import analyze
from app.models import FortuneKind, FortuneRequest, Interpretation


def analysis():
    return analyze(
        FortuneKind.daily,
        FortuneRequest(
            birth={"year": 1990, "month": 5, "day": 17, "hour": 14, "gender": "male"},
            target_date="2026-11-02",
            include_ai=False,
        ),
    )


def parsed(evidence=None):
    targets = analysis().narrative_contract
    return Interpretation(
        summary="계산 근거에 따른 해석입니다.",
        sections=[
            {
                "target_id": t.id,
                "topic": t.topic,
                "text": "계산에 따른 설명입니다.",
                "evidence_ids": t.evidence_ids if evidence is None else [evidence],
            }
            for t in targets
        ],
        practical_advice=["작업 순서를 정해 보세요."],
    )


def provider():
    return OpenAIInterpreter(
        Settings(_env_file=None, openai_api_key=None, openai_model="test-model")
    )


def test_missing_key_does_not_silently_fake_ai():
    with pytest.raises(DomainError) as error:
        asyncio.run(provider().interpret(analysis()))
    assert error.value.status == 503
    assert error.value.code == "ai_not_configured"


def test_payload_omits_raw_birth_and_member_identifiers():
    payload = interpretation_payload(analysis())
    encoded = json.dumps(payload)
    assert "solar_birth" not in encoded
    assert "legacy_memno" not in encoded
    assert "1990-05-17" not in encoded
    assert payload["evidence"][0]["id"] == "natal"
    assert len(payload["narrative_contract"]) == 3
    assert payload["target_date"] == "2026-11-02"
    assert "어제/내일" in payload["score_scope"]


@pytest.mark.parametrize("text", ["favorable 80으로 좋습니다.", "선택 번호 32에 해당합니다."])
def test_customer_content_rejects_internal_calculation_labels(text):
    from app.ai import validate_interpretation

    value = parsed()
    value.sections[0].text = text
    with pytest.raises(DomainError) as error:
        validate_interpretation(value, analysis())
    assert error.value.code == "ai_internal_terms"


def test_structured_request_and_response():
    p = provider()
    parse = AsyncMock(return_value=SimpleNamespace(status="completed", output_parsed=parsed()))
    p.client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    result = asyncio.run(p.interpret(analysis()))
    assert result.summary == parsed().summary
    args = parse.call_args.kwargs
    assert args["store"] is False
    assert args["text_format"] is Interpretation
    assert json.loads(args["input"][0]["content"])["kind"] == "daily"


@pytest.mark.parametrize(
    "response,code",
    [
        (
            SimpleNamespace(status="completed", output_parsed=parsed("imaginary")),
            "ai_invalid_evidence",
        ),
        (SimpleNamespace(status="completed", output_parsed=None), "ai_incomplete_response"),
        (SimpleNamespace(status="incomplete", output_parsed=parsed()), "ai_incomplete_response"),
    ],
)
def test_invalid_or_refused_responses(response, code):
    p = provider()
    p.client = SimpleNamespace(responses=SimpleNamespace(parse=AsyncMock(return_value=response)))
    with pytest.raises(DomainError) as error:
        asyncio.run(p.interpret(analysis()))
    assert error.value.code == code


def test_timeout_is_bounded_and_reported():
    p = provider()
    p.timeout = 0.01

    async def delayed(**kwargs):
        await asyncio.sleep(1)

    p.client = SimpleNamespace(responses=SimpleNamespace(parse=delayed))
    with pytest.raises(DomainError) as error:
        asyncio.run(p.interpret(analysis()))
    assert error.value.status == 504


@pytest.mark.parametrize("mutation", ["omit", "duplicate", "extra", "change_title"])
def test_original_output_contract_is_enforced(mutation):
    from app.ai import validate_interpretation

    result = parsed()
    if mutation == "omit":
        result.sections.pop()
    elif mutation == "duplicate":
        result.sections.append(result.sections[0])
    elif mutation == "extra":
        result.sections[0].target_id = "invented_target"
    else:
        result.sections[0].topic = "새로운 운세 항목"
    with pytest.raises(DomainError) as error:
        validate_interpretation(result, analysis())
    assert error.value.code == "ai_contract_mismatch"


def test_unresolved_source_rule_blocks_ai_before_provider_call():
    r = FortuneRequest(
        birth={"year": 1990, "month": 5, "day": 17, "hour": 14, "gender": "male"},
        target_date="2026-11-02",
        career_category="A",
    )
    result = analyze(FortuneKind.career, r)
    p = provider()
    p.client = SimpleNamespace(responses=SimpleNamespace(parse=AsyncMock()))
    with pytest.raises(DomainError) as error:
        asyncio.run(p.interpret(result))
    assert error.value.code == "legacy_dependency_unavailable"
    p.client.responses.parse.assert_not_called()


def test_actual_openai_sdk_serialization_and_parsing_without_network():
    import httpx2
    from openai import AsyncOpenAI

    captured = []

    async def transport(request):
        captured.append(json.loads(request.content))
        return httpx2.Response(
            200,
            json={
                "id": "resp_test",
                "object": "response",
                "created_at": 1,
                "model": "fixture-model",
                "status": "completed",
                "output": [
                    {
                        "id": "msg_test",
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {
                                "type": "output_text",
                                "annotations": [],
                                "text": parsed().model_dump_json(),
                            }
                        ],
                    }
                ],
            },
        )

    async def run():
        p = provider()
        p.client = AsyncOpenAI(
            api_key="test-not-a-real-key",
            max_retries=0,
            http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(transport)),
        )
        try:
            return await p.interpret(analysis())
        finally:
            await p.close()

    assert asyncio.run(run()) == parsed()
    assert captured[0]["text"]["format"]["type"] == "json_schema"
    assert captured[0]["text"]["format"]["strict"] is True
    assert captured[0]["store"] is False

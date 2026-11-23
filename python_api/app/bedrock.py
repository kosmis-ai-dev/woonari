"""CR-011 / T-021: Claude writes the already-decided ASP output contract."""

import asyncio
import json
from collections.abc import Awaitable, Callable

from pydantic import ValidationError

from app.ai import SYSTEM_PROMPT, interpretation_payload, validate_interpretation
from app.config import Settings
from app.errors import DomainError
from app.models import Analysis, Interpretation
from app.service_models import ServiceAnalysis

TOOL_NAME = "return_interpretation"
ERRORS = {
    "bedrock_use_case_required": (
        "AWS Bedrock의 Anthropic 사용 목적 양식을 제출해야 Claude를 호출할 수 있습니다.", 503
    ),
    "bedrock_account_verification": (
        "AWS 계정 검증이 진행 중이어서 Bedrock 호출이 거부되었습니다. AWS 검증 완료 후 다시 실행하세요.", 503
    ),
    "bedrock_access_denied": ("Woonari AWS 계정의 Bedrock 모델 호출 권한을 확인하세요.", 503),
    "bedrock_account_mismatch": (
        "저장한 Bedrock 키의 AWS 계정이 Woonari 전용 계정과 다릅니다. 전용 계정의 키로 교체해 주세요.", 503
    ),
    "bedrock_model_unavailable": ("설정된 Bedrock 모델·리전·추론 프로필을 확인하세요.", 503),
    "ai_rate_limited": ("Bedrock 모델의 요청 한도에 도달했습니다.", 503),
    "ai_timeout": ("Bedrock AI 응답 시간이 초과되었습니다.", 504),
    "ai_upstream_error": ("Bedrock 모델 호출에 실패했습니다.", 502),
    "ai_invalid_response": ("Bedrock 응답 형식을 확인하지 못했습니다.", 502),
}


def interpretation_schema(analysis: Analysis | ServiceAnalysis) -> dict:
    """Give Claude only the identities and evidence allowed by this contract."""
    schema = Interpretation.model_json_schema()
    reference = schema["properties"]["sections"]["items"]["$ref"].rsplit("/", 1)[-1]
    section = schema["$defs"][reference]["properties"]
    section["target_id"]["enum"] = [target.id for target in analysis.narrative_contract]
    section["topic"]["enum"] = list(dict.fromkeys(
        target.topic for target in analysis.narrative_contract
    ))
    section["evidence_ids"]["items"]["enum"] = [e.id for e in analysis.evidence]
    return schema


class BedrockInterpreter:
    name = "bedrock"

    def __init__(
        self, settings: Settings, invoker: Callable[[dict], Awaitable[dict]] | None = None,
        *, reserve_call: Callable[[], object] | None = None,
    ):
        self.model = settings.bedrock_model_id
        self.region = settings.bedrock_region
        self.max_tokens = settings.bedrock_max_tokens
        self.timeout = settings.ai_timeout_seconds
        self.semaphore = asyncio.Semaphore(settings.ai_max_concurrency)
        self.invoker = invoker
        self.reserve_call = reserve_call

    async def close(self):
        # The injected transport owns and closes each individual CLI process.
        pass

    async def interpret(self, analysis: Analysis | ServiceAnalysis) -> Interpretation:
        if not analysis.ready_for_ai:
            raise DomainError(
                "legacy_dependency_unavailable", "원본 판정 의존성이 미확보되어 AI 생성을 중단했습니다.", 503
            )
        if not self.invoker or not self.model.strip() or not self.region.strip():
            raise DomainError(
                "bedrock_not_configured",
                "Woonari 전용 Bedrock 모델·리전과 AWS 호출 연결이 필요합니다. ./woonari start로 실행하세요.",
                503,
            )
        request = {
            "modelId": self.model,
            "messages": [{"role": "user", "content": [{"text": json.dumps(
                interpretation_payload(analysis), ensure_ascii=False
            )}]}],
            "system": [{"text": SYSTEM_PROMPT + (
                "\n완성한 해석은 return_interpretation 도구의 입력으로 반환하세요. "
                "이 도구는 결과를 제출하는 형식이며 새로운 판정이나 외부 작업을 수행하지 않습니다."
            )}],
            "inferenceConfig": {"maxTokens": self.max_tokens},
            "toolConfig": {
                "tools": [{"toolSpec": {
                    "name": TOOL_NAME, "description": "확정된 ASP 항목별 한국어 해석 결과를 제출합니다.",
                    "inputSchema": {"json": interpretation_schema(analysis)},
                }}],
                "toolChoice": {"tool": {"name": TOOL_NAME}},
            },
        }
        try:
            async with asyncio.timeout(self.timeout):
                async with self.semaphore:
                    if self.reserve_call is not None and not getattr(self.invoker, "reserves_ai_call", False):
                        await asyncio.to_thread(self.reserve_call)
                    response = await self.invoker(request)
        except TimeoutError:
            raise DomainError("ai_timeout", ERRORS["ai_timeout"][0], 504) from None
        except DomainError:
            # Quota exhaustion/state failures retain their original 429/503.
            raise
        except Exception as error:  # Transport details can contain prompt or connection data.
            code = getattr(error, "code", "ai_upstream_error")
            if code not in ERRORS:
                code = "ai_upstream_error"
            message, status = ERRORS[code]
            raise DomainError(code, message, status) from None
        try:
            if response["stopReason"] != "tool_use":
                raise DomainError(
                    "ai_incomplete_response", "Claude가 완전한 un 해석을 반환하지 못했습니다.", 502
                )
            message = response["output"]["message"]
            tools = [block["toolUse"] for block in message["content"] if "toolUse" in block]
            if message["role"] != "assistant" or len(tools) != 1 or tools[0]["name"] != TOOL_NAME:
                raise ValueError
            result = Interpretation.model_validate(tools[0]["input"])
        except DomainError:
            raise
        except (KeyError, TypeError, ValueError, ValidationError):
            raise DomainError("ai_invalid_response", ERRORS["ai_invalid_response"][0], 502) from None
        return validate_interpretation(result, analysis, bind_labels=True)

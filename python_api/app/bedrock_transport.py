"""CR-025 / T-045: portable Bedrock bearer transport with account verification.

Credentials stay in Settings and request headers. The transport only contacts
fixed AWS HTTPS endpoints, verifies the authenticated inference profile before
each cache period, and reserves one daily attempt immediately before a POST.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import re
from collections.abc import Awaitable, Callable
from time import monotonic
from urllib.parse import quote

import httpx

from app.config import Settings

KEY_LIMIT = 4096
REQUEST_LIMIT = 2 * 1024 * 1024
RESPONSE_LIMIT = 2 * 1024 * 1024
PROFILE_CACHE_SECONDS = 300


class BedrockInvocationError(RuntimeError):
    """Public errors never include credentials, prompts or upstream details."""

    def __init__(self, code: str, message: str, status: int = 503):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


def _configuration_error() -> BedrockInvocationError:
    return BedrockInvocationError(
        "bedrock_access_denied", "Bedrock API 키 환경설정의 값·형식을 확인하세요."
    )


def _api_key(settings: Settings) -> str:
    try:
        token = settings.aws_bearer_token_bedrock.get_secret_value()
        if (
            not isinstance(token, str)
            or not 100 <= len(token) <= KEY_LIMIT
            or not re.fullmatch(r"ABSK[A-Za-z0-9+/]+={0,2}", token)
        ):
            raise ValueError
        return token
    except (AttributeError, TypeError, ValueError):
        raise _configuration_error() from None


def _invalid_request() -> BedrockInvocationError:
    return BedrockInvocationError("ai_invalid_response", "Bedrock 요청을 구성하지 못했습니다.", 502)


def _validate_request(request: dict, model_id: str) -> bytes:
    if (
        not isinstance(request, dict)
        or set(request) - {"modelId", "messages", "system", "toolConfig", "inferenceConfig"}
        or request.get("modelId") != model_id
        or not isinstance(request.get("messages"), list)
        or not request["messages"]
        or not isinstance(request.get("system"), list)
        or not isinstance(request.get("toolConfig"), dict)
    ):
        raise _invalid_request()
    inference = request.get("inferenceConfig")
    if (
        not isinstance(inference, dict)
        or set(inference) - {"maxTokens", "temperature", "topP"}
        or type(inference.get("maxTokens")) is not int
        or not 1 <= inference["maxTokens"] <= 65536
    ):
        raise _invalid_request()
    for key in ("temperature", "topP"):
        if key in inference and (
            type(inference[key]) not in (int, float)
            or not math.isfinite(inference[key])
            or not 0 <= inference[key] <= 1
        ):
            raise _invalid_request()
    try:
        body = json.dumps(
            {key: value for key, value in request.items() if key != "modelId"},
            ensure_ascii=True, allow_nan=False, separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError, RecursionError):
        raise _invalid_request() from None
    if len(body) > REQUEST_LIMIT:
        raise _invalid_request()
    return body


def _aws_error(body: bytes) -> BedrockInvocationError:
    reason = body.lower()
    if b"use case details have not been submitted" in reason:
        return BedrockInvocationError(
            "bedrock_use_case_required", "AWS Bedrock의 Anthropic 사용 목적 양식을 제출해 주세요."
        )
    if b"account is currently being verified" in reason:
        return BedrockInvocationError(
            "bedrock_account_verification", "AWS의 Bedrock 계정 검증 완료 후 다시 실행해 주세요."
        )
    if any(value in reason for value in (
        b"accessdenied", b"access denied", b"not authorized", b"account mismatch",
        b"authentication failed", b"history must be disabled",
    )):
        return _configuration_error()
    if any(value in reason for value in (b"throttling", b"toomanyrequests", b"servicequotaexceeded")):
        return BedrockInvocationError("ai_rate_limited", "Bedrock 호출 한도에 도달했습니다.")
    if any(value in reason for value in (b"timeout", b"timed out")):
        return BedrockInvocationError("ai_timeout", "Bedrock 응답 시간이 초과되었습니다.", 504)
    if any(value in reason for value in (
        b"resourcenotfound", b"modelnotready", b"on-demand throughput", b"invalid model identifier",
        b"model identifier is invalid",
    )):
        return BedrockInvocationError(
            "bedrock_model_unavailable", "설정된 Bedrock 모델·리전을 사용할 수 없습니다."
        )
    return BedrockInvocationError("ai_upstream_error", "Bedrock 요청에 실패했습니다.", 502)


def _http_error(status: int, body: bytes) -> BedrockInvocationError:
    classified = _aws_error(body)
    if classified.code != "ai_upstream_error":
        return classified
    if status in {401, 403}:
        return _configuration_error()
    if status == 429:
        return BedrockInvocationError("ai_rate_limited", "Bedrock 호출 한도에 도달했습니다.")
    if status == 404:
        return BedrockInvocationError(
            "bedrock_model_unavailable", "설정된 Bedrock 모델·리전을 사용할 수 없습니다."
        )
    return classified


async def _json_request(
    client: httpx.AsyncClient, method: str, url: str, token: str, content: bytes | None = None
) -> dict:
    try:
        async with client.stream(
            method, url,
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
            content=content,
        ) as response:
            body = bytearray()
            async for chunk in response.aiter_bytes():
                if len(body) + len(chunk) > RESPONSE_LIMIT:
                    raise BedrockInvocationError(
                        "ai_invalid_response", "Bedrock 응답 크기 한도를 초과했습니다.", 502
                    )
                body.extend(chunk)
            if response.status_code != 200:
                raise _http_error(response.status_code, bytes(body))
            result = json.loads(body)
            if not isinstance(result, dict):
                raise TypeError
            return result
    except BedrockInvocationError:
        raise
    except httpx.TimeoutException:
        raise BedrockInvocationError("ai_timeout", "Bedrock 응답 시간이 초과되었습니다.", 504) from None
    except (httpx.HTTPError, OSError):
        raise BedrockInvocationError("ai_upstream_error", "Bedrock HTTPS 요청에 실패했습니다.", 502) from None
    except (ValueError, TypeError, RecursionError):
        raise BedrockInvocationError("ai_invalid_response", "Bedrock 응답 형식을 확인하지 못했습니다.", 502) from None


def _http_client(timeout: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        trust_env=False, follow_redirects=False, verify=True,
        timeout=httpx.Timeout(timeout, connect=min(5, timeout)),
        transport=httpx.AsyncHTTPTransport(retries=0, trust_env=False, verify=True),
    )


def make_bedrock_api_key_invoker(
    settings: Settings, *, reserve_call: Callable[[], object] | None = None,
) -> Callable[[dict], Awaitable[dict]]:
    """Bind the configured account, model and region without filesystem access."""
    if settings.bedrock_auth_mode != "api_key":
        raise BedrockInvocationError(
            "bedrock_access_denied", "Bedrock API 키 인증 방식 설정을 확인하세요."
        )
    account = settings.bedrock_account_id
    if not isinstance(account, str) or not re.fullmatch(r"[0-9]{12}", account):
        raise BedrockInvocationError(
            "bedrock_access_denied", "Bedrock AI 전용 계정 ID를 명시해 주세요."
        )
    model, region, timeout = (
        settings.bedrock_model_id, settings.bedrock_region, settings.ai_timeout_seconds
    )
    if (
        not isinstance(model, str)
        or len(model) > 256
        or not re.fullmatch(r"(?:global|apac|us|eu)\.anthropic\.claude-[A-Za-z0-9._:-]+", model)
        or not isinstance(region, str)
        or not re.fullmatch(r"[a-z]{2}(?:-[a-z]+)+-[0-9]+", region)
        or type(timeout) not in (int, float)
        or not math.isfinite(timeout)
        or not 0 < timeout <= 180
    ):
        raise BedrockInvocationError(
            "bedrock_model_unavailable", "명시적인 Claude 추론 프로필·리전·제한시간이 필요합니다."
        )
    _api_key(settings)
    encoded = quote(model, safe="")
    profile_url = f"https://bedrock.{region}.amazonaws.com/inference-profiles/{encoded}"
    model_url = f"https://bedrock-runtime.{region}.amazonaws.com/model/{encoded}/converse"
    lock = asyncio.Lock()
    verified_identity = None
    verified_until = 0.0

    async def verify(client: httpx.AsyncClient, token: str) -> None:
        nonlocal verified_identity, verified_until
        identity = (hashlib.sha256(token.encode("ascii")).digest(), account, model, region)
        async with lock:
            if identity == verified_identity and monotonic() < verified_until:
                return
            result = await _json_request(client, "GET", profile_url, token)
            actual = result.get("inferenceProfileArn")
            match = re.fullmatch(
                rf"arn:aws:bedrock:{re.escape(region)}:([0-9]{{12}}):inference-profile/{re.escape(model)}",
                actual if isinstance(actual, str) else "",
            )
            if match and match[1] != account:
                raise BedrockInvocationError(
                    "bedrock_account_mismatch", "Bedrock 키의 실제 계정과 지정한 AI 계정이 다릅니다."
                )
            if (
                actual != f"arn:aws:bedrock:{region}:{account}:inference-profile/{model}"
                or result.get("inferenceProfileId") != model
                or result.get("status") != "ACTIVE"
                or result.get("type") != "SYSTEM_DEFINED"
            ):
                raise BedrockInvocationError(
                    "bedrock_access_denied", "Bedrock 키의 실제 계정·리전·추론 프로필을 확인하세요."
                )
            verified_identity, verified_until = identity, monotonic() + PROFILE_CACHE_SECONDS

    async def verify_configuration() -> dict:
        token = _api_key(settings)
        try:
            async with asyncio.timeout(timeout):
                async with _http_client(timeout) as client:
                    await verify(client, token)
        except TimeoutError:
            raise BedrockInvocationError("ai_timeout", "Bedrock 계정 확인 시간이 초과되었습니다.", 504) from None
        return {"auth_mode": "api_key", "account_verified": True, "model_invoked": False}

    async def invoke(request: dict) -> dict:
        body = _validate_request(request, model)
        token = _api_key(settings)
        try:
            async with asyncio.timeout(timeout):
                async with _http_client(timeout) as client:
                    await verify(client, token)
                    if reserve_call is not None:
                        await asyncio.to_thread(reserve_call)
                    return await _json_request(client, "POST", model_url, token, body)
        except TimeoutError:
            raise BedrockInvocationError("ai_timeout", "Bedrock 응답 시간이 초과되었습니다.", 504) from None

    invoke.verify_configuration = verify_configuration
    invoke.preflight = verify_configuration
    invoke.reserves_ai_call = reserve_call is not None
    return invoke

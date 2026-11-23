"""CR-013/T-027: private Bedrock bearer key and authenticated account binding.

Only fixed AWS HTTPS endpoints are contacted. There is no ambient credential,
proxy, redirect, retry or IAM fallback. A server-authenticated inference-profile
ARN must match the dedicated project account before any model POST is sent.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import os
import re
import stat
import time
from collections.abc import Awaitable, Callable
from urllib.parse import quote

import httpx
from isolated_bedrock import (
    BedrockInvocationError,
    _aws_error,
    _inference,
    _invalid_request,
)
from project_context import STATE, private_dir

KEY_NAME = "AWS_BEARER_TOKEN_BEDROCK"
KEY_FILE_LIMIT = 65536
KEY_LIMIT = 4096
REQUEST_LIMIT = 2 * 1024 * 1024
RESPONSE_LIMIT = 2 * 1024 * 1024
PROFILE_CACHE_SECONDS = 300


def _configuration_error() -> BedrockInvocationError:
    return BedrockInvocationError(
        "bedrock_access_denied", "Woonari 전용 Bedrock 키 파일의 값·형식·권한을 확인해 주세요."
    )


def read_api_key() -> str:
    """Return the secret only to the transport; never include it in diagnostics."""
    try:
        directory = private_dir(STATE / "ai")
        path = directory / "bedrock.env"
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or stat.S_IMODE(metadata.st_mode) != 0o600
                or metadata.st_uid != os.geteuid()
                or metadata.st_nlink != 1
                or metadata.st_size > KEY_FILE_LIMIT
            ):
                raise _configuration_error()
            content = stream.read(KEY_FILE_LIMIT + 1)
        if len(content) > KEY_FILE_LIMIT:
            raise _configuration_error()
        assignments = []
        for line in content.decode("utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, separator, value = line.partition("=")
            if separator != "=" or key.strip() != KEY_NAME:
                raise _configuration_error()
            value = value.strip()
            if value[:1] in {"'", '"'}:
                if len(value) < 2 or value[-1] != value[0]:
                    raise _configuration_error()
                value = value[1:-1]
            assignments.append(value)
        if len(assignments) != 1:
            raise _configuration_error()
        token = assignments[0]
        # Long-lived keys use the ABSK prefix (AWS git-secrets recognizer).
        # A generous upper bound avoids depending on a particular alias length.
        if not 100 <= len(token) <= KEY_LIMIT or not re.fullmatch(r"ABSK[A-Za-z0-9+/]+={0,2}", token):
            raise _configuration_error()
        return token
    except BedrockInvocationError:
        raise
    except (OSError, UnicodeError, RuntimeError, ValueError):
        raise _configuration_error() from None


def _http_error(status: int, body: bytes) -> BedrockInvocationError:
    classified = _aws_error(body)
    if classified.code != "ai_upstream_error":
        return classified
    if status in {401, 403}:
        return BedrockInvocationError("bedrock_access_denied", "Woonari 전용 Bedrock 키의 인증·권한을 확인해 주세요.")
    if status == 429:
        return BedrockInvocationError("ai_rate_limited", "Bedrock 호출 한도에 도달했습니다. 잠시 후 다시 실행해 주세요.")
    if status == 404:
        return BedrockInvocationError("bedrock_model_unavailable", "설정된 Bedrock 모델·리전을 사용할 수 없습니다.")
    return classified


async def _json_request(client, method: str, url: str, token: str, content: bytes | None = None) -> dict:
    try:
        async with client.stream(
            method, url, headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
            content=content,
        ) as response:
            body = bytearray()
            async for chunk in response.aiter_bytes():
                if len(body) + len(chunk) > RESPONSE_LIMIT:
                    raise BedrockInvocationError("ai_invalid_response", "Bedrock 응답 크기 한도를 초과했습니다.", 502)
                body.extend(chunk)
            if response.status_code != 200:
                raise _http_error(response.status_code, bytes(body))
            data = json.loads(body)
            if not isinstance(data, dict):
                raise TypeError
            return data
    except BedrockInvocationError:
        raise
    except httpx.TimeoutException:
        raise BedrockInvocationError("ai_timeout", "Bedrock 응답 시간이 초과되었습니다.", 504) from None
    except (httpx.HTTPError, OSError):
        raise BedrockInvocationError("ai_upstream_error", "Bedrock 전용 HTTPS 요청에 실패했습니다.", 502) from None
    except (ValueError, TypeError, RecursionError):
        raise BedrockInvocationError("ai_invalid_response", "Bedrock 응답 형식을 확인하지 못했습니다.", 502) from None


def make_api_key_invoker(
    *, model_id: str, region: str, timeout: float,
    reserve_call: Callable[[], object] | None = None,
    expected_account_id: str | None = None,
) -> Callable[[dict], Awaitable[dict]]:
    if not isinstance(expected_account_id, str) or not re.fullmatch(r"[0-9]{12}", expected_account_id):
        raise BedrockInvocationError(
            "bedrock_access_denied", "장기 키 방식의 Woonari 전용 AI 계정 ID를 명시해 주세요."
        )
    if (
        not isinstance(model_id, str)
        or len(model_id) > 256
        or not re.fullmatch(r"(?:global|apac|us|eu)\.anthropic\.claude-[A-Za-z0-9._:-]+", model_id)
        or not isinstance(region, str)
        or not re.fullmatch(r"[a-z]{2}(?:-[a-z]+)+-[0-9]+", region)
        or type(timeout) not in (int, float)
        or not math.isfinite(timeout)
        or not 0 < timeout <= 180
    ):
        raise BedrockInvocationError(
            "bedrock_model_unavailable", "장기 키 방식에는 명시적인 Claude 추론 프로필·리전·제한시간이 필요합니다."
        )
    encoded = quote(model_id, safe="")
    profile_url = f"https://bedrock.{region}.amazonaws.com/inference-profiles/{encoded}"
    model_url = f"https://bedrock-runtime.{region}.amazonaws.com/model/{encoded}/converse"
    lock = asyncio.Lock()
    verified_identity = None
    verified_until = 0.0

    async def verify(client, token: str, account_id: str):
        nonlocal verified_identity, verified_until
        identity = (hashlib.sha256(token.encode("ascii")).digest(), account_id)
        async with lock:
            if identity == verified_identity and time.monotonic() < verified_until:
                return
            data = await _json_request(client, "GET", profile_url, token)
            expected = f"arn:aws:bedrock:{region}:{account_id}:inference-profile/{model_id}"
            actual_arn = data.get("inferenceProfileArn", "")
            account_match = re.fullmatch(
                rf"arn:aws:bedrock:{re.escape(region)}:([0-9]{{12}}):inference-profile/{re.escape(model_id)}",
                actual_arn if isinstance(actual_arn, str) else "",
            )
            if account_match and account_match[1] != account_id:
                raise BedrockInvocationError(
                    "bedrock_account_mismatch",
                    "저장한 Bedrock 키의 AWS 계정이 지정한 Woonari AI 계정과 다릅니다. AI 계정 설정과 키를 확인해 주세요.",
                )
            if (
                actual_arn != expected
                or data.get("inferenceProfileId") != model_id
                or data.get("status") != "ACTIVE"
                or data.get("type") != "SYSTEM_DEFINED"
            ):
                raise BedrockInvocationError(
                    "bedrock_access_denied", "Bedrock 키의 실제 계정·리전·추론 프로필이 Woonari 설정과 일치하지 않습니다."
                )
            verified_identity, verified_until = identity, time.monotonic() + PROFILE_CACHE_SECONDS

    def client():
        return httpx.AsyncClient(
            trust_env=False, follow_redirects=False,
            timeout=httpx.Timeout(timeout, connect=min(5, timeout)),
            transport=httpx.AsyncHTTPTransport(retries=0, trust_env=False),
        )

    async def preflight() -> dict:
        token, account = read_api_key(), expected_account_id
        try:
            async with asyncio.timeout(timeout):
                async with client() as connection:
                    await verify(connection, token, account)
        except TimeoutError:
            raise BedrockInvocationError("ai_timeout", "Bedrock 계정 확인 시간이 초과되었습니다.", 504) from None
        return {"auth_mode": "api_key", "account_verified": True, "model_invoked": False}

    async def invoke(request: dict) -> dict:
        _inference(request, model_id)
        try:
            body = json.dumps({key: value for key, value in request.items() if key != "modelId"},
                              ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()
        except (TypeError, ValueError, RecursionError):
            raise _invalid_request() from None
        if len(body) > REQUEST_LIMIT:
            raise _invalid_request()
        token, account = read_api_key(), expected_account_id
        try:
            async with asyncio.timeout(timeout):
                async with client() as connection:
                    await verify(connection, token, account)
                    if reserve_call is not None:
                        await asyncio.to_thread(reserve_call)
                    return await _json_request(connection, "POST", model_url, token, body)
        except TimeoutError:
            raise BedrockInvocationError("ai_timeout", "Bedrock 응답 시간이 초과되었습니다.", 504) from None

    # Read-only readiness verification is separately callable before a trial.
    # It never invokes a model and never returns token/account/ARN values.
    invoke.preflight = preflight
    invoke.reserves_ai_call = reserve_call is not None
    return invoke

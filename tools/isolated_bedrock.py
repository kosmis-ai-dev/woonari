"""CR-011/T-021, CR-013/T-027: Woonari-only Bedrock authentication boundaries."""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import signal
import tempfile
from collections.abc import Awaitable, Callable
from contextlib import suppress
from pathlib import Path

from project_context import ROOT, STATE, clean_env, private_dir


class BedrockInvocationError(RuntimeError):
    """A public error containing no CLI output, input, or account values."""

    def __init__(self, code: str, message: str, status: int = 503):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


def _invalid_request() -> BedrockInvocationError:
    return BedrockInvocationError("ai_invalid_response", "Bedrock 요청을 구성하지 못했습니다.", 502)


def _inference(request: dict, model_id: str) -> str:
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
    settings = request.get("inferenceConfig")
    if (
        not isinstance(settings, dict)
        or set(settings) - {"maxTokens", "temperature", "topP"}
        or type(settings.get("maxTokens")) is not int
        or not 1 <= settings["maxTokens"] <= 65536
    ):
        raise _invalid_request()
    for key in ("temperature", "topP"):
        if key in settings and (
            type(settings[key]) not in (int, float)
            or not math.isfinite(settings[key])
            or not 0 <= settings[key] <= 1
        ):
            raise _invalid_request()
    return json.dumps(settings, allow_nan=False, separators=(",", ":"))


def _write_request(path: Path, value) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        # ASCII JSON also works when the CLI's inherited locale is not UTF-8.
        json.dump(value, stream, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def _aws_error(stderr: bytes) -> BedrockInvocationError:
    reason = stderr.lower()
    if b"use case details have not been submitted" in reason:
        return BedrockInvocationError(
            "bedrock_use_case_required",
            "AWS Bedrock의 Anthropic 사용 목적 양식을 제출한 뒤 다시 실행해 주세요.",
        )
    if b"account is currently being verified" in reason:
        return BedrockInvocationError(
            "bedrock_account_verification",
            "AWS에서 신규 계정의 Bedrock 사용을 검증 중입니다. 검증 완료 후 다시 실행해 주세요.",
        )
    if any(value in reason for value in (
        b"accessdenied", b"access denied", b"not authorized", b"account mismatch",
        b"authentication failed", b"history must be disabled",
    )):
        return BedrockInvocationError(
            "bedrock_access_denied", "Woonari 전용 AWS 계정의 Bedrock 사용 권한과 인증 설정을 확인해 주세요."
        )
    if any(value in reason for value in (b"throttling", b"toomanyrequests", b"servicequotaexceeded")):
        return BedrockInvocationError("ai_rate_limited", "Bedrock 호출 한도에 도달했습니다. 잠시 후 다시 실행해 주세요.")
    if any(value in reason for value in (b"timeout", b"timed out")):
        return BedrockInvocationError("ai_timeout", "Bedrock 응답 시간이 초과되었습니다.", 504)
    if any(value in reason for value in (
        b"resourcenotfound", b"modelnotready", b"on-demand throughput", b"invalid model identifier",
        b"model identifier is invalid",
    )):
        return BedrockInvocationError(
            "bedrock_model_unavailable", "설정된 Bedrock 모델 또는 리전을 사용할 수 없습니다."
        )
    return BedrockInvocationError("ai_upstream_error", "Bedrock 호출에 실패했습니다.", 502)


async def _stop(process) -> None:
    """Kill only the process group created for this invocation, then reap it."""
    if process.returncode is None:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    with suppress(OSError, TimeoutError):
        await asyncio.wait_for(process.communicate(), timeout=2)


async def _run(command: list[str], timeout: float) -> tuple[int, bytes, bytes]:
    process = None
    spawning = asyncio.create_task(asyncio.create_subprocess_exec(
        *command,
        cwd=ROOT,
        env=clean_env(),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
    ))
    try:
        async with asyncio.timeout(timeout):
            # Shield process creation so cancellation cannot lose the PID before
            # the wrapper and its AWS CLI children can be stopped together.
            process = await asyncio.shield(spawning)
            stdout, stderr = await process.communicate()
            return process.returncode, stdout, stderr
    except (TimeoutError, asyncio.CancelledError) as error:
        if process is None:
            with suppress(OSError):
                process = await asyncio.shield(spawning)
        if process is not None:
            await asyncio.shield(_stop(process))
        if isinstance(error, asyncio.CancelledError):
            raise
        raise BedrockInvocationError("ai_timeout", "Bedrock 응답 시간이 초과되었습니다.", 504) from None
    except OSError:
        raise BedrockInvocationError("ai_upstream_error", "Bedrock 실행 도구를 시작하지 못했습니다.", 502) from None
    finally:
        if process is not None and process.returncode is None:
            await asyncio.shield(_stop(process))


def make_bedrock_invoker(
    *, model_id: str, region: str, timeout: float, auth_mode: str = "iam",
    reserve_call: Callable[[], object] | None = None,
    expected_account_id: str | None = None,
) -> Callable[[dict], Awaitable[dict]]:
    """Bind an explicit model and region; prompts stay in private temporary files."""
    if (
        not isinstance(model_id, str)
        or len(model_id) > 256
        or not re.fullmatch(r"(?:(?:global|apac|us|eu)\.)?anthropic\.claude-[A-Za-z0-9._:-]+", model_id)
        or not isinstance(region, str)
        or not re.fullmatch(r"[a-z]{2}(?:-[a-z]+)+-[0-9]+", region)
        or type(timeout) not in (int, float)
        or not math.isfinite(timeout)
        or not 0 < timeout <= 180
    ):
        raise BedrockInvocationError("bedrock_model_unavailable", "Bedrock 모델·리전·제한시간 설정을 확인해 주세요.")
    if auth_mode == "api_key":
        from bedrock_key import make_api_key_invoker

        return make_api_key_invoker(
            model_id=model_id, region=region, timeout=timeout, reserve_call=reserve_call,
            expected_account_id=expected_account_id,
        )
    if auth_mode != "iam":
        raise BedrockInvocationError("bedrock_access_denied", "Bedrock 전용 인증 방식을 확인해 주세요.")

    async def invoke(request: dict) -> dict:
        inference = _inference(request, model_id)
        temporary = None
        try:
            directory = private_dir(STATE / "ai/requests")
            temporary = tempfile.TemporaryDirectory(prefix="converse-", dir=directory)
            paths = {key: Path(temporary.name) / f"{key}.json" for key in ("messages", "system", "toolConfig")}
            for key, path in paths.items():
                _write_request(path, request[key])
            command = [
                str(ROOT / "woonari"), "aws", "bedrock-runtime", "converse",
                "--region", region, "--model-id", model_id,
                "--messages", "file://" + str(paths["messages"]),
                "--system", "file://" + str(paths["system"]),
                "--tool-config", "file://" + str(paths["toolConfig"]),
                "--inference-config", inference,
                "--output", "json", "--no-cli-pager",
                "--cli-connect-timeout", "5", "--cli-read-timeout", str(math.ceil(timeout)),
            ]
        except BedrockInvocationError:
            if temporary is not None:
                temporary.cleanup()
            raise
        except (OSError, RuntimeError, TypeError, ValueError):
            if temporary is not None:
                temporary.cleanup()
            raise BedrockInvocationError("ai_upstream_error", "Bedrock 전용 요청 파일을 처리하지 못했습니다.", 502) from None
        with temporary:
            if reserve_call is not None:
                await asyncio.to_thread(reserve_call)
            returncode, stdout, stderr = await _run(command, timeout)
        if returncode:
            raise _aws_error(stderr)
        try:
            response = json.loads(stdout)
            if not isinstance(response, dict):
                raise TypeError
        except (ValueError, TypeError, RecursionError):
            raise BedrockInvocationError("ai_invalid_response", "Bedrock 응답 형식을 확인하지 못했습니다.", 502) from None
        return response

    invoke.reserves_ai_call = reserve_call is not None
    return invoke

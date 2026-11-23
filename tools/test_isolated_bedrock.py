"""CR-011: private request files and bounded, isolated Bedrock subprocesses."""

import asyncio
import json
import signal
import stat
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import isolated_bedrock as bedrock
import pytest

MODEL = "global.anthropic.claude-sonnet-4-6"
REGION = "ap-northeast-2"
PRIVATE_TEXT = "synthetic-personal-prompt-한글"


def request():
    return {
        "modelId": MODEL,
        "messages": [{"role": "user", "content": [{"text": PRIVATE_TEXT}]}],
        "system": [{"text": "synthetic-private-system"}],
        "toolConfig": {"tools": [{"toolSpec": {"name": "interpretation", "inputSchema": {"json": {}}}}]},
        "inferenceConfig": {"maxTokens": 1000, "temperature": 0.2},
    }


@pytest.fixture
def private_state(monkeypatch, tmp_path):
    monkeypatch.setattr(bedrock, "STATE", tmp_path)

    def private(path):
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        path.chmod(0o700)
        return path

    monkeypatch.setattr(bedrock, "private_dir", private)
    return tmp_path


def invoker(timeout=5):
    return bedrock.make_bedrock_invoker(model_id=MODEL, region=REGION, timeout=timeout)


def process(stdout=b"{}", stderr=b"", code=0):
    return SimpleNamespace(pid=321123, returncode=code, communicate=AsyncMock(return_value=(stdout, stderr)))


def test_prompt_is_only_in_private_files_and_success_cleans_every_file(private_state, monkeypatch):
    observed = {}
    answer = {"output": {"message": {"content": [{"text": "result"}]}}}

    async def spawn(*args, **kwargs):
        observed.update(args=args, kwargs=kwargs)
        for option, key in (("--messages", "messages"), ("--system", "system"), ("--tool-config", "toolConfig")):
            path = Path(args[args.index(option) + 1].removeprefix("file://"))
            assert stat.S_IMODE(path.stat().st_mode) == 0o600
            assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
            assert json.loads(path.read_text()) == request()[key]
        return process(json.dumps(answer).encode())

    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "synthetic-unrelated-key")
    monkeypatch.setattr(bedrock.asyncio, "create_subprocess_exec", spawn)

    assert asyncio.run(invoker()(request())) == answer

    args, kwargs = observed["args"], observed["kwargs"]
    assert args[:4] == (str(bedrock.ROOT / "woonari"), "aws", "bedrock-runtime", "converse")
    assert args[args.index("--model-id") + 1] == MODEL
    assert args[args.index("--region") + 1] == REGION
    assert PRIVATE_TEXT not in " ".join(args)
    assert "synthetic-private-system" not in " ".join(args)
    assert json.loads(args[args.index("--inference-config") + 1])["maxTokens"] == 1000
    assert kwargs["start_new_session"] is True
    assert kwargs["cwd"] == bedrock.ROOT
    assert "AWS_ACCESS_KEY_ID" not in kwargs["env"]
    assert list((private_state / "ai/requests").iterdir()) == []


@pytest.mark.parametrize("stderr,code,status", [
    (b"ResourceNotFoundException: Model use case details have not been submitted for this account private-fixture", "bedrock_use_case_required", 503),
    (b"AccessDeniedException: Your account is currently being verified private-fixture", "bedrock_account_verification", 503),
    (b"AccessDeniedException private-fixture", "bedrock_access_denied", 503),
    (b"ThrottlingException private-fixture", "ai_rate_limited", 503),
    (b"Read timeout on endpoint URL private-fixture", "ai_timeout", 504),
    (b"ResourceNotFoundException private-fixture", "bedrock_model_unavailable", 503),
    (b"ValidationException: The provided model identifier is invalid private-fixture", "bedrock_model_unavailable", 503),
    (b"ServiceUnavailableException private-fixture", "ai_upstream_error", 502),
])
def test_aws_errors_are_classified_without_raw_output(private_state, monkeypatch, capsys, stderr, code, status):
    spawn = AsyncMock(return_value=process(b"private-output", stderr, 255))
    monkeypatch.setattr(bedrock.asyncio, "create_subprocess_exec", spawn)

    with pytest.raises(bedrock.BedrockInvocationError) as caught:
        asyncio.run(invoker()(request()))

    assert caught.value.code == code
    assert caught.value.status == status
    assert "private" not in caught.value.message
    assert "private" not in str(caught.value)
    assert capsys.readouterr() == ("", "")
    assert list((private_state / "ai/requests").iterdir()) == []


@pytest.mark.parametrize("response", [b"private-invalid-json", b"[]"])
def test_invalid_responses_have_safe_errors_and_cleanup(private_state, monkeypatch, response):
    monkeypatch.setattr(bedrock.asyncio, "create_subprocess_exec", AsyncMock(return_value=process(response)))
    with pytest.raises(bedrock.BedrockInvocationError) as caught:
        asyncio.run(invoker()(request()))
    assert caught.value.code == "ai_invalid_response"
    assert caught.value.status == 502
    assert "private" not in str(caught.value)
    assert list((private_state / "ai/requests").iterdir()) == []


@pytest.mark.parametrize("failure", ["spawn", "read"])
def test_subprocess_io_failure_is_safe_and_reaps_an_owned_child(private_state, monkeypatch, failure):
    child = process()
    child.returncode = None
    child.communicate.side_effect = [OSError("private-process-fixture"), (b"", b"")]
    spawn = AsyncMock(return_value=child)
    if failure == "spawn":
        spawn.side_effect = OSError("private-process-fixture")
    monkeypatch.setattr(bedrock.asyncio, "create_subprocess_exec", spawn)
    killed = []

    def killpg(pid, sig):
        killed.append((pid, sig))
        child.returncode = -9

    monkeypatch.setattr(bedrock.os, "killpg", killpg)
    with pytest.raises(bedrock.BedrockInvocationError) as caught:
        asyncio.run(invoker()(request()))

    assert caught.value.code == "ai_upstream_error"
    assert "private" not in str(caught.value)
    assert killed == ([(child.pid, signal.SIGKILL)] if failure == "read" else [])
    assert list((private_state / "ai/requests").iterdir()) == []


@pytest.mark.parametrize("change", [
    {"modelId": "another-model"},
    {"inferenceConfig": {}},
    {"inferenceConfig": {"maxTokens": 0}},
    {"inferenceConfig": {"maxTokens": 100, "stopSequences": [PRIVATE_TEXT]}},
])
def test_request_cannot_switch_models_or_put_text_in_argv(private_state, monkeypatch, change):
    spawn = AsyncMock()
    monkeypatch.setattr(bedrock.asyncio, "create_subprocess_exec", spawn)
    with pytest.raises(bedrock.BedrockInvocationError) as caught:
        asyncio.run(invoker()(request() | change))
    assert caught.value.code == "ai_invalid_response"
    spawn.assert_not_called()
    assert not (private_state / "ai/requests").exists()


@pytest.mark.parametrize("model,region,timeout", [
    ("--debug", REGION, 5), (MODEL, "--endpoint-url", 5), (MODEL, REGION, float("nan")),
    ("arn:aws:bedrock:ap-northeast-2:999999999999:inference-profile/other", REGION, 5),
])
def test_invalid_fixed_settings_never_create_an_invoker(model, region, timeout):
    with pytest.raises(bedrock.BedrockInvocationError) as caught:
        bedrock.make_bedrock_invoker(model_id=model, region=region, timeout=timeout)
    assert caught.value.code == "bedrock_model_unavailable"


def test_timeout_kills_owned_group_and_removes_private_files(private_state, monkeypatch):
    killed = []

    async def run():
        finished = asyncio.Event()
        child = SimpleNamespace(pid=321123, returncode=None)

        async def communicate():
            await finished.wait()
            child.returncode = -9
            return b"", b""

        child.communicate = communicate
        monkeypatch.setattr(bedrock.asyncio, "create_subprocess_exec", AsyncMock(return_value=child))

        def killpg(pid, sig):
            killed.append((pid, sig))
            finished.set()

        monkeypatch.setattr(bedrock.os, "killpg", killpg)
        with pytest.raises(bedrock.BedrockInvocationError) as caught:
            await invoker(0.01)(request())
        assert caught.value.code == "ai_timeout"
        assert caught.value.status == 504

    asyncio.run(run())
    assert killed == [(321123, signal.SIGKILL)]
    assert list((private_state / "ai/requests").iterdir()) == []


def test_cancellation_during_spawn_reaps_the_new_process_group(private_state, monkeypatch):
    killed = []

    async def run():
        spawning = asyncio.Event()
        allow_spawn = asyncio.Event()
        finished = asyncio.Event()
        child = SimpleNamespace(pid=321123, returncode=None)

        async def communicate():
            await finished.wait()
            child.returncode = -9
            return b"", b""

        child.communicate = communicate

        async def spawn(*args, **kwargs):
            assert kwargs["start_new_session"] is True
            spawning.set()
            await allow_spawn.wait()
            return child

        def killpg(pid, sig):
            killed.append((pid, sig))
            finished.set()

        monkeypatch.setattr(bedrock.asyncio, "create_subprocess_exec", spawn)
        monkeypatch.setattr(bedrock.os, "killpg", killpg)
        task = asyncio.create_task(invoker()(request()))
        await spawning.wait()
        task.cancel()
        allow_spawn.set()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(run())
    assert killed == [(321123, signal.SIGKILL)]
    assert list((private_state / "ai/requests").iterdir()) == []


def test_iam_reserves_once_immediately_before_cli_call(private_state, monkeypatch):
    calls = []

    async def run(command, timeout):
        calls.append("invoke")
        return 0, b"{}", b""

    monkeypatch.setattr(bedrock, "_run", run)
    action = bedrock.make_bedrock_invoker(
        model_id=MODEL, region=REGION, timeout=5, reserve_call=lambda: calls.append("reserve"),
    )
    assert asyncio.run(action(request())) == {}
    assert calls == ["reserve", "invoke"]
    assert action.reserves_ai_call is True
    assert list((private_state / "ai/requests").iterdir()) == []


def test_iam_quota_error_propagates_without_invocation_and_cleans_files(private_state, monkeypatch):
    run = AsyncMock()
    monkeypatch.setattr(bedrock, "_run", run)
    failure = RuntimeError("synthetic-daily-cap")

    def reserve():
        raise failure

    action = bedrock.make_bedrock_invoker(
        model_id=MODEL, region=REGION, timeout=5, reserve_call=reserve,
    )
    with pytest.raises(RuntimeError) as caught:
        asyncio.run(action(request()))
    assert caught.value is failure
    run.assert_not_called()
    assert list((private_state / "ai/requests").iterdir()) == []

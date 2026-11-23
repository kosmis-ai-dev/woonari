"""CR-013: explicit private-key ownership, account gate and bounded model POSTs."""

import asyncio
import json
import os
import stat

import bedrock_key as key
import httpx
import isolated_bedrock as bedrock
import project_context
import pytest

MODEL = "global.anthropic.claude-sonnet-4-6"
REGION = "ap-northeast-2"
ACCOUNT = "111111111111"
SYNTHETIC = "ABSK" + "A" * 120 + "=="


def request():
    return {
        "modelId": MODEL, "messages": [{"role": "user", "content": [{"text": "synthetic-private-prompt"}]}],
        "system": [{"text": "synthetic-private-system"}],
        "toolConfig": {"tools": []}, "inferenceConfig": {"maxTokens": 512},
    }


def profile(**changes):
    return {
        "inferenceProfileArn": f"arn:aws:bedrock:{REGION}:{ACCOUNT}:inference-profile/{MODEL}",
        "inferenceProfileId": MODEL, "status": "ACTIVE", "type": "SYSTEM_DEFINED", **changes,
    }


@pytest.fixture
def state(tmp_path, monkeypatch):
    monkeypatch.setattr(project_context, "ROOT", tmp_path)
    private = tmp_path / ".local/woonari"
    monkeypatch.setattr(key, "STATE", private)
    directory = project_context.private_dir(private / "ai")
    path = directory / "bedrock.env"
    path.write_text(key.KEY_NAME + "=" + SYNTHETIC + "\n")
    path.chmod(0o600)
    return path


def mocked_http(monkeypatch, handler):
    original_client = httpx.AsyncClient
    observed = []

    def transport(*, retries, trust_env):
        assert retries == 0
        assert trust_env is False
        return httpx.MockTransport(handler)

    def client(**kwargs):
        assert kwargs["trust_env"] is False
        assert kwargs["follow_redirects"] is False
        observed.append(kwargs)
        return original_client(**kwargs)

    monkeypatch.setattr(key.httpx, "AsyncHTTPTransport", transport)
    monkeypatch.setattr(key.httpx, "AsyncClient", client)
    return observed


def invoker(**kwargs):
    return bedrock.make_bedrock_invoker(
        model_id=MODEL, region=REGION, timeout=5, auth_mode="api_key", **kwargs,
        expected_account_id=ACCOUNT,
    )


def test_only_private_key_is_used_and_model_post_follows_account_gate_and_reservation(state, monkeypatch, capsys):
    events = []
    answer = {"stopReason": "tool_use", "output": {"message": {"role": "assistant"}}}
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "synthetic-unrelated-account")
    monkeypatch.setenv("HTTPS_PROXY", "http://synthetic-unrelated-proxy.invalid")

    def handler(req):
        assert req.headers["authorization"] == "Bearer " + SYNTHETIC
        events.append(req.method)
        if req.method == "GET":
            assert str(req.url) == f"https://bedrock.{REGION}.amazonaws.com/inference-profiles/{MODEL}"
            return httpx.Response(200, json=profile())
        assert str(req.url) == f"https://bedrock-runtime.{REGION}.amazonaws.com/model/{MODEL}/converse"
        assert json.loads(req.content) == {k: v for k, v in request().items() if k != "modelId"}
        return httpx.Response(200, json=answer)

    mocked_http(monkeypatch, handler)
    action = invoker(reserve_call=lambda: events.append("reserve"))

    async def run():
        assert await action.preflight() == {"auth_mode": "api_key", "account_verified": True, "model_invoked": False}
        assert await action(request()) == answer
        assert await action(request()) == answer

    asyncio.run(run())
    assert action.reserves_ai_call is True
    assert events == ["GET", "reserve", "POST", "reserve", "POST"]
    assert capsys.readouterr() == ("", "")
    assert state.read_text().strip().endswith(SYNTHETIC)


@pytest.mark.parametrize("changes,expected", [
    ({"inferenceProfileArn": f"arn:aws:bedrock:{REGION}:222222222222:inference-profile/{MODEL}"}, "bedrock_account_mismatch"),
    ({"inferenceProfileArn": f"arn:aws:bedrock:us-east-1:{ACCOUNT}:inference-profile/{MODEL}"}, "bedrock_access_denied"),
    ({"inferenceProfileArn": f"arn:aws:bedrock:{REGION}::inference-profile/{MODEL}"}, "bedrock_access_denied"),
    ({"inferenceProfileId": "another-profile"}, "bedrock_access_denied"),
    ({"status": "INACTIVE"}, "bedrock_access_denied"),
    ({"type": "APPLICATION"}, "bedrock_access_denied"),
])
def test_unverified_or_wrong_account_never_reserves_or_invokes_model(state, monkeypatch, changes, expected):
    events = []

    def handler(req):
        events.append(req.method)
        assert req.method == "GET"
        return httpx.Response(200, json=profile(**changes))

    mocked_http(monkeypatch, handler)
    with pytest.raises(bedrock.BedrockInvocationError) as caught:
        asyncio.run(invoker(reserve_call=lambda: events.append("reserve"))(request()))
    assert caught.value.code == expected
    assert caught.value.status == 503
    assert ACCOUNT not in str(caught.value) and SYNTHETIC not in str(caught.value)
    assert events == ["GET"]


def test_quota_failure_is_not_masked_and_no_model_post_is_sent(state, monkeypatch):
    calls = []

    def handler(req):
        calls.append(req.method)
        return httpx.Response(200, json=profile())

    class ReservationDenied(RuntimeError):
        pass

    error = ReservationDenied("synthetic-daily-cap")

    def reserve():
        raise error

    mocked_http(monkeypatch, handler)
    with pytest.raises(ReservationDenied) as caught:
        asyncio.run(invoker(reserve_call=reserve)(request()))
    assert caught.value is error
    assert calls == ["GET"]


def test_key_rotation_requires_new_authenticated_account_check(state, monkeypatch):
    calls = []

    def handler(req):
        calls.append((req.method, req.headers["authorization"]))
        return httpx.Response(200, json=profile() if req.method == "GET" else {})

    mocked_http(monkeypatch, handler)
    action = invoker()

    async def run():
        await action(request())
        state.write_text(key.KEY_NAME + "=" + "ABSK" + "B" * 120 + "==\n")
        await action(request())

    asyncio.run(run())
    assert [method for method, _ in calls] == ["GET", "POST", "GET", "POST"]
    assert calls[0][1] != calls[2][1]


@pytest.mark.parametrize("status,body,code", [
    (403, {"message": "Authentication failed " + SYNTHETIC}, "bedrock_access_denied"),
    (404, {"message": "Model use case details have not been submitted for this account"}, "bedrock_use_case_required"),
    (429, {"message": "synthetic quota " + SYNTHETIC}, "ai_rate_limited"),
    (503, {"message": "synthetic unavailable " + SYNTHETIC}, "ai_upstream_error"),
    (307, {"message": "synthetic redirect " + SYNTHETIC}, "ai_upstream_error"),
])
def test_model_errors_charge_once_without_retry_redirect_or_secret_exposure(state, monkeypatch, capsys, status, body, code):
    calls = []

    def handler(req):
        calls.append(req.method)
        if req.method == "GET":
            return httpx.Response(200, json=profile())
        return httpx.Response(status, json=body, headers={"Location": "https://unrelated.invalid"})

    mocked_http(monkeypatch, handler)
    with pytest.raises(bedrock.BedrockInvocationError) as caught:
        asyncio.run(invoker(reserve_call=lambda: calls.append("reserve"))(request()))
    assert caught.value.code == code
    assert SYNTHETIC not in str(caught.value)
    assert calls == ["GET", "reserve", "POST"]
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("content", [
    "", key.KEY_NAME + "=", "OTHER_KEY=value", "export " + key.KEY_NAME + "=" + SYNTHETIC,
    key.KEY_NAME + "=" + SYNTHETIC + "\n" + key.KEY_NAME + "=" + SYNTHETIC,
    key.KEY_NAME + "=not-a-bedrock-long-key", key.KEY_NAME + "=\"" + SYNTHETIC,
])
def test_invalid_private_file_is_rejected_without_echoing_values(state, content):
    state.write_text(content)
    with pytest.raises(bedrock.BedrockInvocationError) as caught:
        key.read_api_key()
    assert caught.value.code == "bedrock_access_denied"
    assert SYNTHETIC not in str(caught.value)


def test_quotes_comments_and_equal_padding_are_read_literally(state):
    state.write_text("# Woonari only\n\n" + key.KEY_NAME + "='" + SYNTHETIC + "'\n")
    assert key.read_api_key() == SYNTHETIC


def test_key_permission_symlink_hardlink_and_nonregular_files_fail_closed(state, tmp_path):
    state.chmod(0o644)
    with pytest.raises(bedrock.BedrockInvocationError):
        key.read_api_key()
    assert stat.S_IMODE(state.stat().st_mode) == 0o644
    state.chmod(0o600)
    original = tmp_path / "original-secret.env"
    state.rename(original)
    state.symlink_to(original)
    with pytest.raises(bedrock.BedrockInvocationError):
        key.read_api_key()
    state.unlink()
    os.link(original, state)
    with pytest.raises(bedrock.BedrockInvocationError):
        key.read_api_key()
    state.unlink()
    os.mkfifo(state, 0o600)
    with pytest.raises(bedrock.BedrockInvocationError):
        key.read_api_key()


def test_parent_symlink_and_oversized_file_fail_closed(state, tmp_path):
    state.write_bytes(b"A" * (key.KEY_FILE_LIMIT + 1))
    with pytest.raises(bedrock.BedrockInvocationError):
        key.read_api_key()
    parent = state.parent
    moved = tmp_path / "external-ai"
    parent.rename(moved)
    parent.symlink_to(moved, target_is_directory=True)
    with pytest.raises(bedrock.BedrockInvocationError):
        key.read_api_key()


def test_invalid_or_oversized_model_request_never_authenticates_or_reserves(state, monkeypatch):
    calls = []
    mocked_http(monkeypatch, lambda req: calls.append(req.method))
    for body in [request() | {"modelId": "other"}, request() | {"messages": [{"text": "X" * key.REQUEST_LIMIT}]}]:
        with pytest.raises(bedrock.BedrockInvocationError) as caught:
            asyncio.run(invoker(reserve_call=lambda: calls.append("reserve"))(body))
        assert caught.value.code == "ai_invalid_response"
    assert calls == []


def test_oversized_or_invalid_json_response_is_safe(state, monkeypatch):
    for body in [b"X" * (key.RESPONSE_LIMIT + 1), b"not-json", b"[]"]:
        def handler(req, body=body):
            return httpx.Response(200, json=profile()) if req.method == "GET" else httpx.Response(200, content=body)

        mocked_http(monkeypatch, handler)
        with pytest.raises(bedrock.BedrockInvocationError) as caught:
            asyncio.run(invoker()(request()))
        assert caught.value.code == "ai_invalid_response"


def test_timeout_during_metadata_does_not_reserve(state, monkeypatch):
    calls = []

    def handler(req):
        calls.append(req.method)
        raise httpx.ReadTimeout(SYNTHETIC)

    mocked_http(monkeypatch, handler)
    with pytest.raises(bedrock.BedrockInvocationError) as caught:
        asyncio.run(invoker(reserve_call=lambda: calls.append("reserve"))(request()))
    assert caught.value.code == "ai_timeout"
    assert SYNTHETIC not in str(caught.value)
    assert calls == ["GET"]


def test_cancellation_during_identity_lookup_sends_no_model_request(state, monkeypatch):
    calls = []

    async def run():
        entered = asyncio.Event()

        async def handler(req):
            calls.append(req.method)
            entered.set()
            await asyncio.Event().wait()

        mocked_http(monkeypatch, handler)
        task = asyncio.create_task(invoker(reserve_call=lambda: calls.append("reserve"))(request()))
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(run())
    assert calls == ["GET"]


@pytest.mark.parametrize("mode,model", [("implicit", MODEL), ("api_key", "anthropic.claude-base")])
def test_unknown_auth_or_unverifiable_base_model_never_chooses_another_authentication(mode, model):
    with pytest.raises(bedrock.BedrockInvocationError):
        bedrock.make_bedrock_invoker(
            model_id=model, region=REGION, timeout=5, auth_mode=mode, expected_account_id=ACCOUNT,
        )


@pytest.mark.parametrize("account_id", [None, "", "12345", "not-a-project-account"])
def test_api_key_mode_requires_explicit_ai_account_without_cli_account_fallback(account_id):
    with pytest.raises(bedrock.BedrockInvocationError) as caught:
        bedrock.make_bedrock_invoker(
            model_id=MODEL, region=REGION, timeout=5, auth_mode="api_key", expected_account_id=account_id,
        )
    assert caught.value.code == "bedrock_access_denied"

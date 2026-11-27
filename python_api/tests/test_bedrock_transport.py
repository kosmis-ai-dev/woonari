"""CR-025 / T-045: bearer transport uses mocked HTTPS, never AWS credentials."""

import asyncio
import json
import traceback
from copy import deepcopy
from unittest.mock import Mock

import httpx
import pytest
from pydantic import SecretStr

from app import bedrock_transport
from app.bedrock_transport import BedrockInvocationError, make_bedrock_api_key_invoker
from app.config import Settings
from app.errors import DomainError

MODEL = "apac.anthropic.claude-fixture-v1:0"
REGION = "ap-northeast-2"
ACCOUNT = "123456789012"
TOKEN = "ABSK" + "a" * 124


def settings(**changes):
    return Settings(
        _env_file=None,
        ai_provider="bedrock",
        bedrock_auth_mode="api_key",
        bedrock_account_id=ACCOUNT,
        bedrock_model_id=MODEL,
        bedrock_region=REGION,
        aws_bearer_token_bedrock=SecretStr(TOKEN),
    ).model_copy(update=changes)


def request():
    return {
        "modelId": MODEL,
        "messages": [{"role": "user", "content": [{"text": "private-fixture-prompt"}]}],
        "system": [{"text": "fixture system"}],
        "inferenceConfig": {"maxTokens": 1024},
        "toolConfig": {"tools": [], "toolChoice": {"auto": {}}},
    }


def profile(**changes):
    return {
        "inferenceProfileArn": f"arn:aws:bedrock:{REGION}:{ACCOUNT}:inference-profile/{MODEL}",
        "inferenceProfileId": MODEL,
        "status": "ACTIVE",
        "type": "SYSTEM_DEFINED",
    } | changes


@pytest.fixture
def install_http(monkeypatch):
    def install(handler):
        clients = []

        def client(timeout):
            result = httpx.AsyncClient(
                transport=httpx.MockTransport(handler), trust_env=False,
                follow_redirects=False, timeout=timeout,
            )
            clients.append(result)
            return result

        monkeypatch.setattr(bedrock_transport, "_http_client", client)
        return clients

    return install


def test_authenticated_profile_precedes_one_charged_post_with_fixed_endpoints(install_http):
    events, captured = [], []

    def handler(http_request):
        events.append(http_request.method)
        captured.append(http_request)
        if http_request.method == "GET":
            return httpx.Response(200, json=profile())
        return httpx.Response(200, json={"stopReason": "tool_use"})

    clients = install_http(handler)
    invoker = make_bedrock_api_key_invoker(settings(), reserve_call=lambda: events.append("reserve"))
    original = request()
    before = deepcopy(original)
    result = asyncio.run(invoker(original))

    assert result == {"stopReason": "tool_use"}
    assert events == ["GET", "reserve", "POST"]
    assert original == before
    assert invoker.reserves_ai_call is True
    assert str(captured[0].url) == (
        f"https://bedrock.{REGION}.amazonaws.com/inference-profiles/"
        "apac.anthropic.claude-fixture-v1%3A0"
    )
    assert str(captured[1].url) == (
        f"https://bedrock-runtime.{REGION}.amazonaws.com/model/"
        "apac.anthropic.claude-fixture-v1%3A0/converse"
    )
    assert captured[0].content == b""
    assert json.loads(captured[1].content) == {key: value for key, value in before.items() if key != "modelId"}
    for item in captured:
        assert item.headers["Authorization"] == "Bearer " + TOKEN
        assert item.headers["Content-Type"] == "application/json"
        assert item.url.scheme == "https" and item.url.userinfo == b""
    assert all(client.is_closed for client in clients)
    assert TOKEN not in repr(invoker)


def test_read_only_verification_never_reserves_or_posts_and_is_cached(install_http):
    calls = []
    reserve = Mock()

    def handler(http_request):
        calls.append(http_request.method)
        return httpx.Response(200, json=profile() if http_request.method == "GET" else {"ok": True})

    install_http(handler)
    invoker = make_bedrock_api_key_invoker(settings(), reserve_call=reserve)

    async def exercise():
        assert await invoker.verify_configuration() == {
            "auth_mode": "api_key", "account_verified": True, "model_invoked": False
        }
        await invoker.preflight()
        reserve.assert_not_called()
        assert calls == ["GET"]
        await invoker(request())

    asyncio.run(exercise())
    assert calls == ["GET", "POST"]
    reserve.assert_called_once_with()


def test_verification_cache_expires_after_five_minutes(install_http, monkeypatch):
    now = [10.0]
    monkeypatch.setattr(bedrock_transport, "monotonic", lambda: now[0])
    calls = []

    def handler(http_request):
        calls.append(http_request.method)
        return httpx.Response(200, json=profile() if http_request.method == "GET" else {})

    install_http(handler)
    invoker = make_bedrock_api_key_invoker(settings())

    async def exercise():
        await invoker.verify_configuration()
        now[0] = 309.9
        await invoker(request())
        now[0] = 310.0
        await invoker(request())

    asyncio.run(exercise())
    assert calls == ["GET", "POST", "GET", "POST"]
    assert invoker.reserves_ai_call is False


def test_rotated_in_memory_key_requires_new_profile_verification(install_http):
    captured = []

    def handler(http_request):
        captured.append((http_request.method, http_request.headers["Authorization"]))
        return httpx.Response(200, json=profile() if http_request.method == "GET" else {})

    install_http(handler)
    config = settings()
    invoker = make_bedrock_api_key_invoker(config)
    rotated = "ABSK" + "b" * 124

    async def exercise():
        await invoker(request())
        config.aws_bearer_token_bedrock = SecretStr(rotated)
        await invoker(request())

    asyncio.run(exercise())
    assert captured == [
        ("GET", "Bearer " + TOKEN), ("POST", "Bearer " + TOKEN),
        ("GET", "Bearer " + rotated), ("POST", "Bearer " + rotated),
    ]


def test_concurrent_calls_share_verification_but_each_reserves_one_attempt(install_http):
    calls, reserved = [], []

    async def handler(http_request):
        calls.append(http_request.method)
        await asyncio.sleep(0)
        return httpx.Response(200, json=profile() if http_request.method == "GET" else {})

    install_http(handler)
    invoker = make_bedrock_api_key_invoker(settings(), reserve_call=lambda: reserved.append(1))

    async def exercise():
        await asyncio.gather(*(invoker(request()) for _ in range(5)))

    asyncio.run(exercise())
    assert calls.count("GET") == 1
    assert calls.count("POST") == len(reserved) == 5


@pytest.mark.parametrize(("changes", "code"), [
    ({"inferenceProfileArn": f"arn:aws:bedrock:{REGION}:999999999999:inference-profile/{MODEL}"},
     "bedrock_account_mismatch"),
    ({"inferenceProfileArn": f"arn:aws:bedrock:us-east-1:{ACCOUNT}:inference-profile/{MODEL}"},
     "bedrock_access_denied"),
    ({"inferenceProfileArn": f"arn:aws:bedrock:{REGION}:{ACCOUNT}:inference-profile/wrong-model"},
     "bedrock_access_denied"),
    ({"inferenceProfileId": "wrong-model"}, "bedrock_access_denied"),
    ({"status": "INACTIVE"}, "bedrock_access_denied"),
    ({"type": "APPLICATION"}, "bedrock_access_denied"),
    ({"inferenceProfileArn": None}, "bedrock_access_denied"),
])
def test_bad_profile_never_posts_or_consumes_quota(changes, code, install_http):
    calls, reserve = [], Mock()

    def handler(http_request):
        calls.append(http_request.method)
        return httpx.Response(200, json=profile(**changes))

    install_http(handler)
    invoker = make_bedrock_api_key_invoker(settings(), reserve_call=reserve)
    with pytest.raises(BedrockInvocationError) as error:
        asyncio.run(invoker(request()))
    assert error.value.code == code
    assert calls == ["GET"]
    reserve.assert_not_called()
    assert ACCOUNT not in str(error.value) and MODEL not in str(error.value)


@pytest.mark.parametrize(("status", "body", "code"), [
    (403, b"private auth details", "bedrock_access_denied"),
    (429, b"private rate details", "ai_rate_limited"),
    (404, b"private missing details", "bedrock_model_unavailable"),
    (302, b"private redirect", "ai_upstream_error"),
    (500, b"use case details have not been submitted", "bedrock_use_case_required"),
    (500, b"account is currently being verified", "bedrock_account_verification"),
    (500, b"AccessDeniedException", "bedrock_access_denied"),
    (500, b"ThrottlingException", "ai_rate_limited"),
    (500, b"ModelNotReadyException", "bedrock_model_unavailable"),
    (500, b"timed out", "ai_timeout"),
    (500, b"unknown private error", "ai_upstream_error"),
])
def test_get_errors_are_classified_without_post_or_quota(status, body, code, install_http):
    calls, reserve = [], Mock()

    def handler(http_request):
        calls.append(http_request.method)
        return httpx.Response(status, content=body, headers={"Location": "https://wrong.invalid"})

    install_http(handler)
    with pytest.raises(BedrockInvocationError) as error:
        asyncio.run(make_bedrock_api_key_invoker(settings(), reserve_call=reserve)(request()))
    assert error.value.code == code
    assert body.decode() not in str(error.value)
    assert calls == ["GET"]
    reserve.assert_not_called()


def test_post_failure_is_not_retried_or_refunded_and_hides_upstream_details(install_http):
    calls, reserve = [], Mock()
    private = " ".join((TOKEN, ACCOUNT, MODEL, "private-fixture-prompt", "https://private.invalid"))

    def handler(http_request):
        calls.append(http_request.method)
        return httpx.Response(200, json=profile()) if http_request.method == "GET" else httpx.Response(
            503, content=private
        )

    install_http(handler)
    with pytest.raises(BedrockInvocationError) as error:
        asyncio.run(make_bedrock_api_key_invoker(settings(), reserve_call=reserve)(request()))
    assert calls == ["GET", "POST"]
    reserve.assert_called_once_with()
    assert error.value.code == "ai_upstream_error"
    formatted = "".join(traceback.format_exception(error.value))
    for value in private.split():
        assert value not in formatted


def test_quota_rejection_preserves_domain_error_and_never_posts(install_http):
    calls = []

    def handler(http_request):
        calls.append(http_request.method)
        return httpx.Response(200, json=profile())

    quota_error = DomainError("ai_daily_limit_reached", "오늘의 AI 호출 한도입니다.", 429)
    reserve = Mock(side_effect=quota_error)
    install_http(handler)
    with pytest.raises(DomainError) as error:
        asyncio.run(make_bedrock_api_key_invoker(settings(), reserve_call=reserve)(request()))
    assert error.value is quota_error
    assert calls == ["GET"]
    reserve.assert_called_once_with()


@pytest.mark.parametrize("key", ["", "short", "ABSK" + "a" * 96 + "\n", "ABSK" + "a" * 4096, "x" * 124])
def test_invalid_key_fails_before_any_http_or_quota(key, install_http):
    network, reserve = Mock(), Mock()
    install_http(network)
    with pytest.raises(BedrockInvocationError) as error:
        make_bedrock_api_key_invoker(settings(aws_bearer_token_bedrock=SecretStr(key)), reserve_call=reserve)
    assert error.value.code == "bedrock_access_denied"
    network.assert_not_called()
    reserve.assert_not_called()
    if key:
        assert key not in str(error.value)


@pytest.mark.parametrize(("field", "value", "code"), [
    ("bedrock_auth_mode", "iam", "bedrock_access_denied"),
    ("bedrock_auth_mode", "unknown", "bedrock_access_denied"),
    ("bedrock_account_id", "", "bedrock_access_denied"),
    ("bedrock_account_id", "12345678901", "bedrock_access_denied"),
    ("bedrock_account_id", 123456789012, "bedrock_access_denied"),
    ("bedrock_model_id", "anthropic.claude-fixture", "bedrock_model_unavailable"),
    ("bedrock_model_id", "apac.anthropic.claude-test/../../wrong", "bedrock_model_unavailable"),
    ("bedrock_model_id", "https://wrong.invalid", "bedrock_model_unavailable"),
    ("bedrock_model_id", "apac.anthropic.claude-" + "a" * 256, "bedrock_model_unavailable"),
    ("bedrock_region", "", "bedrock_model_unavailable"),
    ("bedrock_region", "us-east-1.wrong.invalid/", "bedrock_model_unavailable"),
    ("ai_timeout_seconds", 0, "bedrock_model_unavailable"),
    ("ai_timeout_seconds", 181, "bedrock_model_unavailable"),
    ("ai_timeout_seconds", True, "bedrock_model_unavailable"),
    ("ai_timeout_seconds", float("inf"), "bedrock_model_unavailable"),
    ("ai_timeout_seconds", float("nan"), "bedrock_model_unavailable"),
])
def test_invalid_binding_never_uses_http_or_quota(field, value, code, install_http):
    network, reserve = Mock(), Mock()
    install_http(network)
    with pytest.raises(BedrockInvocationError) as error:
        make_bedrock_api_key_invoker(settings(**{field: value}), reserve_call=reserve)
    assert error.value.code == code
    network.assert_not_called()
    reserve.assert_not_called()


@pytest.mark.parametrize("mutation", [
    "wrong-model", "missing-max", "bool-max", "zero-max", "large-max", "extra-inference",
    "nan", "missing-messages", "extra-field", "unserializable", "recursive", "oversized",
])
def test_invalid_request_does_not_verify_or_charge(mutation, install_http, monkeypatch):
    network, reserve = Mock(), Mock()
    install_http(network)
    data = request()
    if mutation == "wrong-model":
        data["modelId"] = "private-unapproved-model"
    elif mutation == "missing-max":
        data["inferenceConfig"] = {}
    elif mutation == "bool-max":
        data["inferenceConfig"]["maxTokens"] = True
    elif mutation == "zero-max":
        data["inferenceConfig"]["maxTokens"] = 0
    elif mutation == "large-max":
        data["inferenceConfig"]["maxTokens"] = 65537
    elif mutation == "extra-inference":
        data["inferenceConfig"]["unapproved"] = 1
    elif mutation == "nan":
        data["inferenceConfig"]["temperature"] = float("nan")
    elif mutation == "missing-messages":
        data["messages"] = []
    elif mutation == "extra-field":
        data["endpoint"] = "https://wrong.invalid"
    elif mutation == "unserializable":
        data["system"] = [object()]
    elif mutation == "recursive":
        data["system"].append(data)
    elif mutation == "oversized":
        monkeypatch.setattr(bedrock_transport, "REQUEST_LIMIT", 100)
    with pytest.raises(BedrockInvocationError) as error:
        asyncio.run(make_bedrock_api_key_invoker(settings(), reserve_call=reserve)(data))
    assert error.value.code == "ai_invalid_response"
    assert "private" not in str(error.value)
    network.assert_not_called()
    reserve.assert_not_called()


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("response_kind", ["large", "array", "invalid-json"])
def test_invalid_responses_are_bounded_and_do_not_trigger_retries(
    method, response_kind, install_http, monkeypatch
):
    monkeypatch.setattr(bedrock_transport, "RESPONSE_LIMIT", 1024)
    calls, reserve = [], Mock()

    def handler(http_request):
        calls.append(http_request.method)
        if http_request.method != method:
            return httpx.Response(200, json=profile())
        content = {"large": b"x" * 1025, "array": b"[]", "invalid-json": b"{private"}[response_kind]
        return httpx.Response(200, content=content)

    install_http(handler)
    with pytest.raises(BedrockInvocationError) as error:
        asyncio.run(make_bedrock_api_key_invoker(settings(), reserve_call=reserve)(request()))
    assert error.value.code == "ai_invalid_response"
    assert calls == (["GET"] if method == "GET" else ["GET", "POST"])
    assert reserve.call_count == (0 if method == "GET" else 1)


@pytest.mark.parametrize(("failure", "code"), [
    (httpx.ReadTimeout, "ai_timeout"), (httpx.ConnectError, "ai_upstream_error"),
])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_network_errors_are_generic_and_have_no_automatic_retry(method, failure, code, install_http):
    calls, reserve = [], Mock()

    def handler(http_request):
        calls.append(http_request.method)
        if http_request.method == method:
            raise failure("private-network-details " + TOKEN, request=http_request)
        return httpx.Response(200, json=profile())

    install_http(handler)
    with pytest.raises(BedrockInvocationError) as error:
        asyncio.run(make_bedrock_api_key_invoker(settings(), reserve_call=reserve)(request()))
    assert error.value.code == code
    assert calls == (["GET"] if method == "GET" else ["GET", "POST"])
    assert reserve.call_count == (0 if method == "GET" else 1)
    formatted = "".join(traceback.format_exception(error.value))
    assert TOKEN not in formatted and "private-network-details" not in formatted


def test_overall_verification_timeout_never_posts_or_reserves(install_http):
    calls, reserve = [], Mock()

    async def handler(http_request):
        calls.append(http_request.method)
        await asyncio.sleep(0.1)
        return httpx.Response(200, json=profile())

    install_http(handler)
    invoker = make_bedrock_api_key_invoker(settings(ai_timeout_seconds=0.01), reserve_call=reserve)
    with pytest.raises(BedrockInvocationError) as error:
        asyncio.run(invoker.verify_configuration())
    assert error.value.code == "ai_timeout" and error.value.status == 504
    assert calls == ["GET"]
    reserve.assert_not_called()


def test_default_http_client_disables_ambient_credentials_redirects_and_retries(monkeypatch):
    transport, client = Mock(), Mock()
    monkeypatch.setattr(bedrock_transport.httpx, "AsyncHTTPTransport", transport)
    monkeypatch.setattr(bedrock_transport.httpx, "AsyncClient", client)
    bedrock_transport._http_client(45)
    transport.assert_called_once_with(retries=0, trust_env=False, verify=True)
    kwargs = client.call_args.kwargs
    assert kwargs["trust_env"] is False and kwargs["follow_redirects"] is False
    assert kwargs["verify"] is True and kwargs["transport"] is transport.return_value
    assert kwargs["timeout"].connect == 5 and kwargs["timeout"].read == 45


def test_missing_rotated_key_cannot_reuse_cached_account_verification(install_http):
    calls, reserve = [], Mock()

    def handler(http_request):
        calls.append(http_request.method)
        return httpx.Response(200, json=profile())

    install_http(handler)
    config = settings()
    invoker = make_bedrock_api_key_invoker(config, reserve_call=reserve)

    async def exercise():
        await invoker.verify_configuration()
        config.aws_bearer_token_bedrock = SecretStr("")
        with pytest.raises(BedrockInvocationError) as error:
            await invoker(request())
        assert error.value.code == "bedrock_access_denied"

    asyncio.run(exercise())
    assert calls == ["GET"]
    reserve.assert_not_called()

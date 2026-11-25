"""CR-022 / T-042: browser-bound social login and service session contracts."""

import hashlib
import json
from contextlib import contextmanager
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest
from fastapi.testclient import TestClient

from app.auth_models import SocialIdentity, SocialProvider
from app.auth_settings import AuthSettings, load_auth_settings
from app.auth_store import SQLiteAuthStore
from app.config import Settings
from app.errors import DomainError
from app.main import create_app


class FakeOAuthGateway:
    def __init__(self):
        self.calls = []
        self.closed = False
        self.failure = None
        self.identities = {
            provider: SocialIdentity(
                provider=provider,
                subject=f"unit-subject-{provider}",
                nickname=f"{provider} 회원",
                email="shared@example.invalid",
                email_verified=provider != SocialProvider.naver
            )
            for provider in SocialProvider
        }

    def authorization_url(
        self, provider, *, client_id, redirect_uri, state, code_verifier, nonce
    ):
        query = urlencode({
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "nonce": nonce,
            "challenge": hashlib.sha256(code_verifier.encode()).hexdigest()
        })
        return f"https://{provider}.example.invalid/authorize?{query}"

    async def exchange(self, provider, **kwargs):
        self.calls.append((provider, kwargs))
        if self.failure:
            raise self.failure
        return self.identities[provider]

    async def close(self):
        self.closed = True


def configured_settings(**overrides):
    values = {
        f"{provider}_client_{kind}": f"unit-{provider}-{kind}"
        for provider in SocialProvider
        for kind in ("id", "secret")
    }
    return AuthSettings(**(values | overrides))


@pytest.fixture
def auth_context(tmp_path):
    @contextmanager
    def context(*, settings=None, api_key=None, base_url="http://testserver"):
        clock = [1_800_000_000]
        gateway = FakeOAuthGateway()
        store = SQLiteAuthStore(tmp_path / "auth" / "sessions.sqlite3")
        store.initialize()
        app = create_app(
            Settings(_env_file=None, api_key=api_key),
            auth_settings=settings or configured_settings(),
            auth_store=store,
            oauth_gateway=gateway,
            auth_clock=lambda: clock[0]
        )
        with TestClient(app, base_url=base_url) as client:
            yield client, gateway, clock, app
    return context


def begin(client, provider="kakao"):
    response = client.get(f"/v1/auth/{provider}/authorize")
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"authorization_url", "expires_in"}
    assert 0 < body["expires_in"] <= 600
    query = parse_qs(urlsplit(body["authorization_url"]).query)
    return query["state"][0], query


def login(client, provider="kakao"):
    state, _ = begin(client, provider)
    response = client.get(
        f"/v1/auth/{provider}/callback",
        params={"state": state, "code": "unit-authorization-code"}
    )
    assert response.status_code == 200, response.text
    return response.json()


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def assert_no_cache(response):
    assert "no-store" in response.headers["cache-control"]
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_provider_setup_is_public_but_secrets_are_not(auth_context):
    with auth_context(api_key="unit-existing-api-key") as (client, _, _, _):
        response = client.get("/v1/auth/providers")
        assert response.status_code == 200
        assert_no_cache(response)
        items = response.json()["items"]
        assert {item["provider"] for item in items} == {"kakao", "google", "naver"}
        assert all(item["configured"] is True for item in items)
        assert {item["name"] for item in items} == {"카카오", "구글", "네이버"}
        assert all(item["callback_url"] == f"http://127.0.0.1:9090/v1/auth/{item['provider']}/callback" for item in items)
        raw = response.text
        assert "unit-" not in raw and "client_secret" not in raw
        assert client.get("/v1/fortunes").status_code == 401


def test_missing_provider_settings_fail_before_exchange(auth_context):
    with auth_context(settings=AuthSettings()) as (client, gateway, _, _):
        assert all(not item["configured"] for item in client.get("/v1/auth/providers").json()["items"])
        for provider in SocialProvider:
            response = client.get(f"/v1/auth/{provider}/authorize")
            assert response.status_code == 503
            assert "authorization_url" not in response.json()
            assert "set-cookie" not in response.headers
            assert_no_cache(response)
        assert not gateway.calls


def test_login_bearer_does_not_replace_the_existing_fortune_api_key(auth_context):
    with auth_context(api_key="unit-existing-api-key") as (client, _, _, _):
        value = login(client)
        assert client.get("/v1/auth/me", headers=bearer(value["access_token"])).status_code == 200
        assert client.get("/v1/fortunes", headers=bearer(value["access_token"])).status_code == 401
        assert client.get("/v1/fortunes", headers={"X-API-Key": "unit-existing-api-key"}).status_code == 200


@pytest.mark.parametrize("provider", list(SocialProvider))
def test_three_provider_logins_issue_only_service_tokens(auth_context, provider):
    with auth_context() as (client, gateway, _, _):
        state, query = begin(client, provider)
        callback = client.get(
            f"/v1/auth/{provider}/callback",
            params={"state": state, "code": "unit-authorization-code"}
        )
        assert callback.status_code == 200, callback.text
        assert_no_cache(callback)
        value = callback.json()
        assert value["access_token"].startswith("wn_at_")
        assert value["refresh_token"].startswith("wn_rt_")
        assert value["token_type"] == "bearer"
        assert value["expires_in"] == 900
        assert value["refresh_expires_in"] == 30 * 24 * 60 * 60
        assert value["is_new_user"] is True
        assert value["user"]["providers"] == [provider]
        assert "subject" not in value["user"]
        assert gateway.calls[0][0] == provider
        sent = gateway.calls[0][1]
        assert sent["state"] == state
        assert sent["redirect_uri"] == query["redirect_uri"][0]
        assert sent["nonce"] == query["nonce"][0]
        assert hashlib.sha256(sent["code_verifier"].encode()).hexdigest() == query["challenge"][0]
        assert "client_secret" not in callback.text
        me = client.get("/v1/auth/me", headers=bearer(value["access_token"]))
        assert me.status_code == 200
        assert me.json() == value["user"]
        assert_no_cache(me)
        assert f"woonari_oauth_{provider}" not in client.cookies


def test_login_redirect_sets_browser_cookie_and_fixed_callback(auth_context):
    with auth_context() as (client, gateway, _, _):
        response = client.get("/v1/auth/google/login", follow_redirects=False)
        assert response.status_code in {302, 307}
        assert_no_cache(response)
        query = parse_qs(urlsplit(response.headers["location"]).query)
        assert query["redirect_uri"] == ["http://127.0.0.1:9090/v1/auth/google/callback"]
        cookie = SimpleCookie()
        cookie.load(response.headers["set-cookie"])
        state_cookie = cookie["woonari_oauth_google"]
        assert state_cookie["httponly"]
        assert state_cookie["samesite"].lower() == "lax"
        assert state_cookie["path"] == "/v1/auth"
        assert not state_cookie["secure"]
        assert not gateway.calls


@pytest.mark.parametrize("scheme", ["https", "HTTPS"])
def test_https_callback_requires_secure_cookie(auth_context, scheme):
    settings = configured_settings(auth_public_base_url=f"{scheme}://login.example.invalid")
    with auth_context(settings=settings, base_url="https://testserver") as (client, _, _, _):
        response = client.get("/v1/auth/naver/authorize")
        assert response.status_code == 200
        cookie = SimpleCookie()
        cookie.load(response.headers["set-cookie"])
        assert cookie["woonari_oauth_naver"]["secure"]
        query = parse_qs(urlsplit(response.json()["authorization_url"]).query)
        assert query["redirect_uri"] == [settings.callback_url(SocialProvider.naver)]


def test_state_is_browser_bound_and_invalid_attempt_does_not_burn_it(auth_context):
    with auth_context() as (client, gateway, _, app):
        state, _ = begin(client)
        attacker = TestClient(app)
        try:
            response = attacker.get("/v1/auth/kakao/callback", params={"state": state, "code": "unit-code"})
            assert response.status_code == 400
        finally:
            attacker.close()
        assert not gateway.calls
        response = client.get("/v1/auth/kakao/callback", params={"state": state, "code": "unit-code"})
        assert response.status_code == 200, response.text
        assert len(gateway.calls) == 1


def test_state_cannot_cross_providers_or_be_replayed(auth_context):
    with auth_context() as (client, gateway, _, _):
        state, _ = begin(client)
        cookie = client.cookies.get("woonari_oauth_kakao")
        client.cookies.set("woonari_oauth_google", cookie, path="/v1/auth")
        crossed = client.get("/v1/auth/google/callback", params={"state": state, "code": "unit-code"})
        assert crossed.status_code == 400
        assert not gateway.calls
        good = client.get("/v1/auth/kakao/callback", params={"state": state, "code": "unit-code"})
        assert good.status_code == 200
        client.cookies.set("woonari_oauth_kakao", cookie, path="/v1/auth")
        replay = client.get("/v1/auth/kakao/callback", params={"state": state, "code": "unit-code"})
        assert replay.status_code == 400
        assert len(gateway.calls) == 1


def test_state_expiry_denial_and_provider_failure_are_not_logins(auth_context):
    with auth_context() as (client, gateway, clock, _):
        state, _ = begin(client)
        clock[0] += 601
        expired = client.get("/v1/auth/kakao/callback", params={"state": state, "code": "unit-code"})
        assert expired.status_code == 400
        assert not gateway.calls
        state, _ = begin(client)
        denied = client.get("/v1/auth/kakao/callback", params={
            "state": state, "error": "access_denied", "error_description": "unit-sensitive-provider-message"
        })
        assert denied.status_code == 400
        assert "unit-sensitive-provider-message" not in denied.text
        assert not gateway.calls
        state, _ = begin(client)
        gateway.failure = DomainError("social_provider_error", "로그인을 완료하지 못했습니다.", 502)
        failure = client.get("/v1/auth/kakao/callback", params={"state": state, "code": "unit-code"})
        assert failure.status_code == 502
        assert_no_cache(failure)
        assert "access_token" not in failure.text
        replay = client.get("/v1/auth/kakao/callback", params={"state": state, "code": "unit-code"})
        assert replay.status_code == 400
        assert len(gateway.calls) == 1


@pytest.mark.parametrize("state", [None, "", "unit-malformed-state"])
def test_callback_without_valid_state_cannot_reach_a_provider(auth_context, state):
    with auth_context() as (client, gateway, _, _):
        begin(client)
        parameters = {"code": "unit-code"}
        if state is not None:
            parameters["state"] = state
        response = client.get("/v1/auth/kakao/callback", params=parameters)
        assert response.status_code == 400
        assert_no_cache(response)
        assert not gateway.calls
        assert "access_token" not in response.text


def test_callback_without_code_or_with_wrong_provider_identity_is_rejected(auth_context):
    with auth_context() as (client, gateway, _, _):
        state, _ = begin(client)
        missing = client.get("/v1/auth/kakao/callback", params={"state": state})
        assert missing.status_code == 400
        assert not gateway.calls
        state, _ = begin(client)
        gateway.identities[SocialProvider.kakao] = SocialIdentity(SocialProvider.google, "wrong-provider-subject")
        wrong = client.get("/v1/auth/kakao/callback", params={"state": state, "code": "unit-code"})
        assert wrong.status_code == 401
        assert "access_token" not in wrong.text
        assert "wrong-provider-subject" not in wrong.text


def test_refresh_validation_does_not_echo_the_supplied_secret(auth_context):
    with auth_context() as (client, _, _, _):
        response = client.post("/v1/auth/refresh", json={"refresh_token": "unit-sensitive"})
        assert response.status_code == 422
        assert "unit-sensitive" not in response.text
        assert_no_cache(response)


def test_refresh_rotation_reuse_revokes_its_session(auth_context):
    with auth_context() as (client, _, _, _):
        first = login(client)
        refreshed = client.post("/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
        assert refreshed.status_code == 200, refreshed.text
        assert_no_cache(refreshed)
        second = refreshed.json()
        assert second["user"]["id"] == first["user"]["id"]
        assert second["access_token"] != first["access_token"]
        assert second["refresh_token"] != first["refresh_token"]
        assert second["is_new_user"] is False
        assert client.get("/v1/auth/me", headers=bearer(first["access_token"])).status_code == 401
        assert client.get("/v1/auth/me", headers=bearer(second["access_token"])).status_code == 200
        reused = client.post("/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
        assert reused.status_code == 401
        assert client.get("/v1/auth/me", headers=bearer(second["access_token"])).status_code == 401
        assert client.post("/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}).status_code == 401


def test_access_and_refresh_expiration_use_server_time(auth_context):
    with auth_context() as (client, _, clock, _):
        first = login(client)
        clock[0] += first["expires_in"] + 1
        assert client.get("/v1/auth/me", headers=bearer(first["access_token"])).status_code == 401
        refreshed = client.post("/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
        assert refreshed.status_code == 200
        second = refreshed.json()
        assert second["refresh_expires_in"] < first["refresh_expires_in"]
        clock[0] += second["refresh_expires_in"] + 1
        assert client.post("/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}).status_code == 401


def test_logout_revokes_only_current_session(auth_context):
    with auth_context() as (client, _, _, _):
        first = login(client)
        second = login(client)
        assert second["is_new_user"] is False
        assert second["user"]["id"] == first["user"]["id"]
        out = client.post("/v1/auth/logout", headers=bearer(first["access_token"]))
        assert out.status_code == 200 and out.json() == {"logged_out": True}
        assert_no_cache(out)
        assert client.get("/v1/auth/me", headers=bearer(first["access_token"])).status_code == 401
        assert client.post("/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}).status_code == 401
        assert client.get("/v1/auth/me", headers=bearer(second["access_token"])).status_code == 200


def test_provider_identity_not_shared_email_controls_accounts(auth_context):
    with auth_context() as (client, gateway, _, _):
        kakao = login(client)
        google = login(client, "google")
        assert kakao["user"]["email"] == google["user"]["email"]
        assert kakao["user"]["id"] != google["user"]["id"]
        gateway.identities[SocialProvider.naver] = SocialIdentity(SocialProvider.naver, "minimal-unit-subject")
        naver = login(client, "naver")
        assert naver["user"]["email"] is None
        assert naver["user"]["nickname"] is None
        assert naver["user"]["email_verified"] is False


@pytest.mark.parametrize("header", [None, "Basic unit-value", "Bearer wn_at_invalid", "Bearer wn_rt_not-an-access-token"])
def test_private_routes_require_service_bearer(auth_context, header):
    with auth_context() as (client, _, _, _):
        headers = {"Authorization": header} if header else {}
        for method, path in [(client.get, "/v1/auth/me"), (client.post, "/v1/auth/logout")]:
            response = method(path, headers=headers)
            assert response.status_code == 401
            assert response.headers["www-authenticate"].lower() == "bearer"
            assert_no_cache(response)


def test_auth_swagger_is_separate_and_does_not_expose_app_secrets(auth_context):
    with auth_context() as (client, _, _, _):
        schema = client.get("/openapi.json").json()
        operations = {
            path: item for path, item in schema["paths"].items() if path.startswith("/v1/auth/")
        }
        assert len(operations) >= 7
        assert all("로그인" in operation["tags"][0] or "회원" in operation["tags"][0] for path in operations.values() for operation in path.values())
        raw = json.dumps(operations, ensure_ascii=False)
        assert "unit-kakao-secret" not in raw
        assert "ASP" not in raw and ".asp" not in raw
        token_fields = schema["components"]["schemas"]["LoginResult"]["properties"]
        assert "access_token" in token_fields and "refresh_token" in token_fields


def test_provider_file_ignores_ambient_credentials_and_rejects_insecure_file(tmp_path, monkeypatch):
    monkeypatch.setenv("KAKAO_CLIENT_ID", "unit-ambient-id")
    monkeypatch.setenv("KAKAO_CLIENT_SECRET", "unit-ambient-secret")
    path = tmp_path / "providers.env"
    assert not load_auth_settings(path).configured(SocialProvider.kakao)
    path.write_text("KAKAO_CLIENT_ID=unit-id\nKAKAO_CLIENT_SECRET=$KAKAO_CLIENT_SECRET\n")
    path.chmod(0o600)
    assert load_auth_settings(path).kakao_client_secret.get_secret_value() == "$KAKAO_CLIENT_SECRET"
    path.chmod(0o644)
    with pytest.raises(DomainError) as error:
        load_auth_settings(path)
    assert error.value.code == "auth_configuration_invalid"
    assert "unit-id" not in str(error.value)


@pytest.mark.parametrize("url", [
    "http://attacker.example.invalid", "http://127.0.0.1:8080", "https://example.invalid/callback",
    "https://user:pass@example.invalid", "https://example.invalid?redirect=evil", "https://example.invalid/#fragment"
])
def test_callback_origin_setting_cannot_be_an_open_redirect(url):
    with pytest.raises(ValueError):
        AuthSettings(auth_public_base_url=url)

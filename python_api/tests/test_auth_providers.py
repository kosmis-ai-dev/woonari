"""CR-022 / T-042: provider contracts without live credentials or accounts."""

import asyncio
import base64
import hashlib
import json
import time
from urllib.parse import parse_qs, urlsplit

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth_models import SocialProvider
from app.auth_providers import SocialOAuthGateway
from app.errors import DomainError

CLIENT_ID = "test-social-client"
CLIENT_SECRET = "test-social-secret"
REDIRECT = "http://127.0.0.1:9090/v1/auth/google/callback"
VERIFIER = "a" * 64
NONCE = "test-login-nonce"
SUBJECT = "AppSpecificUser-0123+/="


@pytest.fixture(scope="module")
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _claims(provider=SocialProvider.google, **overrides):
    return {
        "iss": "https://accounts.google.com" if provider == SocialProvider.google else "https://nid.naver.com",
        "aud": CLIENT_ID, "sub": SUBJECT, "exp": int(time.time()) + 300,
        "iat": int(time.time()), "nonce": NONCE, **overrides
    }


def _jwt(key, claims):
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "fixture-key"})


def _jwks(key):
    key_data = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()))
    return {"keys": [{**key_data, "kid": "fixture-key", "alg": "RS256", "use": "sig"}]}


def _exchange(provider, handler):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True) as client:
            gateway = SocialOAuthGateway(client)
            result = await gateway.exchange(
                provider, client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT, code="fixture-code", state="fixture-state",
                code_verifier=VERIFIER, nonce=NONCE
            )
            await gateway.close()
            assert not client.is_closed
            return result
    return asyncio.run(run())


@pytest.mark.parametrize("provider", list(SocialProvider))
def test_authorization_is_code_flow_with_s256_and_bound_redirect(provider):
    gateway = SocialOAuthGateway(httpx.AsyncClient(transport=httpx.MockTransport(lambda r: None)))
    url = gateway.authorization_url(
        provider, client_id=CLIENT_ID, redirect_uri=REDIRECT,
        state="one time +/ state", code_verifier=VERIFIER, nonce=NONCE
    )
    parsed = urlsplit(url)
    query = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert query["response_type"] == ["code"]
    assert query["redirect_uri"] == [REDIRECT]
    assert query["state"] == ["one time +/ state"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["code_challenge"] == [
        base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).rstrip(b"=").decode()
    ]
    assert VERIFIER not in url and CLIENT_SECRET not in url
    if provider != SocialProvider.kakao:
        assert query["nonce"] == [NONCE]
        assert "openid" in query["scope"][0].split()
    if provider == SocialProvider.naver:
        assert parsed.path == "/oauth2/authorize"
    asyncio.run(gateway._client.aclose())


@pytest.mark.parametrize("provider", [SocialProvider.google, SocialProvider.naver])
def test_oidc_exchange_verifies_claims_and_profile_identity(signing_key, provider):
    requests = []

    def handler(request):
        requests.append(request)
        if request.method == "POST":
            form = parse_qs(request.content.decode())
            assert form["code_verifier"] == [VERIFIER]
            assert form["client_secret"] == [CLIENT_SECRET]
            assert form["redirect_uri"] == [REDIRECT]
            assert request.url.query == b""
            if provider == SocialProvider.naver:
                assert request.url.path == "/oauth2/token"
                assert form["state"] == ["fixture-state"]
            return httpx.Response(200, json={
                "access_token": "provider-token", "token_type": "Bearer",
                "id_token": _jwt(signing_key, _claims(provider))
            })
        if request.url.path.endswith(("/certs", "/jwks")):
            return httpx.Response(200, json=_jwks(signing_key))
        assert request.headers["Authorization"] == "Bearer provider-token"
        if provider == SocialProvider.naver:
            return httpx.Response(200, json={"resultcode": "00", "response": {
                "id": SUBJECT, "nickname": "네이버 사용자", "email": "fixture@example.test",
                "email_verified": True
            }})
        return httpx.Response(200, json={
            "sub": SUBJECT, "name": "구글 사용자", "email": "fixture@example.test", "email_verified": True
        })

    result = _exchange(provider, handler)
    assert result.subject == SUBJECT
    assert result.email == "fixture@example.test"
    assert result.email_verified is (provider == SocialProvider.google)
    assert len(requests) == 3


@pytest.mark.parametrize("overrides", [
    {"aud": "other-client"}, {"iss": "https://attacker.invalid"},
    {"nonce": "other-nonce"}, {"exp": 1}, {"iat": 4_000_000_000},
    {"sub": ""}, {"sub": 123}, {"exp": str(4_000_000_000)},
    {"iat": True}, {"azp": "other-client"},
    {"aud": [CLIENT_ID, "other-client"]}
])
def test_oidc_rejects_invalid_signed_claims(signing_key, overrides):
    token = _jwt(signing_key, _claims(**overrides))

    def handler(request):
        if request.method == "POST":
            return httpx.Response(200, json={"access_token": "provider-token", "token_type": "Bearer", "id_token": token})
        return httpx.Response(200, json=_jwks(signing_key))

    with pytest.raises(DomainError) as failure:
        _exchange(SocialProvider.google, handler)
    assert failure.value.code == "social_login_failed" and failure.value.status == 401


@pytest.mark.parametrize("kind", ["signature", "algorithm", "missing_nonce", "missing_sub", "unknown_kid"])
def test_oidc_rejects_invalid_signature_header_or_required_claim(signing_key, kind):
    claims = _claims()
    if kind == "missing_nonce":
        del claims["nonce"]
    if kind == "missing_sub":
        del claims["sub"]
    if kind == "signature":
        token = _jwt(rsa.generate_private_key(public_exponent=65537, key_size=2048), claims)
    elif kind == "algorithm":
        token = jwt.encode(claims, "x" * 64, algorithm="HS256", headers={"kid": "fixture-key"})
    elif kind == "unknown_kid":
        token = jwt.encode(claims, signing_key, algorithm="RS256", headers={"kid": "untrusted-key"})
    else:
        token = _jwt(signing_key, claims)

    def handler(request):
        if request.method == "POST":
            return httpx.Response(200, json={"access_token": "provider-token", "token_type": "Bearer", "id_token": token})
        return httpx.Response(200, json=_jwks(signing_key))

    with pytest.raises(DomainError) as failure:
        _exchange(SocialProvider.google, handler)
    assert failure.value.code == "social_login_failed"


def test_google_accepts_documented_bare_issuer_and_optional_profile_omissions(signing_key):
    def handler(request):
        if request.method == "POST":
            return httpx.Response(200, json={"access_token": "provider-token", "token_type": "bearer", "id_token": _jwt(signing_key, _claims(iss="accounts.google.com"))})
        if request.url.path.endswith("/certs"):
            return httpx.Response(200, json=_jwks(signing_key))
        return httpx.Response(200, json={"sub": SUBJECT})
    identity = _exchange(SocialProvider.google, handler)
    assert identity.nickname is None and identity.email is None and identity.email_verified is False


@pytest.mark.parametrize("provider", [SocialProvider.google, SocialProvider.naver])
def test_oidc_userinfo_identity_must_match_verified_token(signing_key, provider):
    def handler(request):
        if request.method == "POST":
            return httpx.Response(200, json={"access_token": "provider-token", "token_type": "Bearer", "id_token": _jwt(signing_key, _claims(provider))})
        if request.url.path.endswith(("/certs", "/jwks")):
            return httpx.Response(200, json=_jwks(signing_key))
        profile = {"sub": "different-user"} if provider == SocialProvider.google else {"resultcode": "00", "response": {"id": "different-user"}}
        return httpx.Response(200, json=profile)
    with pytest.raises(DomainError) as failure:
        _exchange(provider, handler)
    assert failure.value.code == "social_login_failed"


@pytest.mark.parametrize("valid,verified,expected", [(True, True, True), (False, True, False), (True, False, False), (True, "true", False)])
def test_kakao_email_requires_both_strict_verification_flags(valid, verified, expected):
    def handler(request):
        if request.method == "POST":
            return httpx.Response(200, json={"access_token": "provider-token", "token_type": "bearer", "id_token": "not-used"})
        assert request.url.params["secure_resource"] == "true"
        return httpx.Response(200, json={"id": 123456789012345, "kakao_account": {
            "email": "fixture@example.test", "is_email_valid": valid,
            "is_email_verified": verified, "profile": {"nickname": "카카오 사용자"}
        }})
    identity = _exchange(SocialProvider.kakao, handler)
    assert identity.subject == "123456789012345"
    assert identity.email_verified is expected


@pytest.mark.parametrize("profile", [{"id": True}, {"id": "123"}, {"id": 0}, {}, {"id": -1}])
def test_kakao_rejects_malformed_identifier(profile):
    def handler(request):
        return httpx.Response(200, json={"access_token": "provider-token", "token_type": "bearer"} if request.method == "POST" else profile)
    with pytest.raises(DomainError) as failure:
        _exchange(SocialProvider.kakao, handler)
    assert failure.value.code == "social_login_failed"


def test_kakao_optional_profile_fields_are_not_required():
    def handler(request):
        return httpx.Response(200, json={"access_token": "provider-token", "token_type": "bearer"} if request.method == "POST" else {"id": 123})
    identity = _exchange(SocialProvider.kakao, handler)
    assert identity.subject == "123" and identity.nickname is None and identity.email is None


@pytest.mark.parametrize("kind,code,status", [
    ("timeout", "social_provider_error", 502), ("redirect", "social_provider_error", 502),
    ("invalid_json", "social_provider_error", 502), ("array", "social_provider_error", 502),
    ("upstream", "social_provider_error", 502), ("denied", "social_login_failed", 401),
    ("error_body", "social_login_failed", 401), ("missing_access", "social_provider_error", 502),
    ("mac_token", "social_provider_error", 502), ("header_injection", "social_provider_error", 502)
])
def test_provider_failures_are_neutral_and_are_not_retried(kind, code, status):
    calls = []
    def handler(request):
        calls.append(request)
        if kind == "timeout":
            raise httpx.ReadTimeout("sensitive-provider-message", request=request)
        if kind == "redirect":
            return httpx.Response(302, headers={"Location": "https://attacker.invalid/"})
        if kind == "invalid_json":
            return httpx.Response(200, text="sensitive-provider-message")
        if kind == "array":
            return httpx.Response(200, json=[])
        if kind == "upstream":
            return httpx.Response(503, text="sensitive-provider-message")
        if kind == "denied":
            return httpx.Response(401, text="sensitive-provider-message")
        if kind == "error_body":
            return httpx.Response(200, json={"error": "sensitive-provider-message"})
        data = {"token_type": "bearer"}
        if kind == "mac_token":
            data.update(access_token="provider-token", token_type="MAC")
        if kind == "header_injection":
            data.update(access_token="provider-token\r\nInjected: value")
        return httpx.Response(200, json=data)
    with pytest.raises(DomainError) as failure:
        _exchange(SocialProvider.kakao, handler)
    assert failure.value.code == code and failure.value.status == status
    assert "sensitive-provider-message" not in str(failure.value)
    assert len(calls) == 1


def test_default_client_disables_environment_proxies_and_redirects():
    async def run():
        gateway = SocialOAuthGateway()
        assert gateway._client.trust_env is False
        assert gateway._client.follow_redirects is False
        await gateway.close()
        assert gateway._client.is_closed
    asyncio.run(run())

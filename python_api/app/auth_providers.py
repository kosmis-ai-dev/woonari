"""CR-022 / T-042: fixed-endpoint social OAuth exchanges and verified identity."""

import base64
import hashlib
import hmac
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
import jwt

from app.auth_models import SocialIdentity, SocialProvider
from app.errors import DomainError


@dataclass(frozen=True)
class _Provider:
    authorize: str
    token: str
    userinfo: str
    issuer: str | tuple[str, ...] | None = None
    jwks: str | None = None
    scope: str | None = None


_PROVIDERS = {
    SocialProvider.kakao: _Provider(
        authorize="https://kauth.kakao.com/oauth/authorize",
        token="https://kauth.kakao.com/oauth/token",
        userinfo="https://kapi.kakao.com/v2/user/me"
    ),
    SocialProvider.google: _Provider(
        authorize="https://accounts.google.com/o/oauth2/v2/auth",
        token="https://oauth2.googleapis.com/token",
        userinfo="https://openidconnect.googleapis.com/v1/userinfo",
        issuer=("https://accounts.google.com", "accounts.google.com"),
        jwks="https://www.googleapis.com/oauth2/v3/certs",
        scope="openid profile email"
    ),
    SocialProvider.naver: _Provider(
        authorize="https://nid.naver.com/oauth2/authorize",
        token="https://nid.naver.com/oauth2/token",
        userinfo="https://openapi.naver.com/v1/nid/me",
        issuer="https://nid.naver.com",
        jwks="https://nid.naver.com/oauth2/jwks",
        scope="openid profile"
    )
}


def _failed() -> DomainError:
    return DomainError("social_login_failed", "소셜 로그인 인증을 확인할 수 없습니다. 다시 로그인해 주세요.", 401)


def _upstream() -> DomainError:
    return DomainError("social_provider_error", "소셜 로그인 제공자의 응답을 확인할 수 없습니다.", 502)


def _optional_text(value, maximum: int) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value[:maximum] if value else None


def _subject(value) -> str:
    if not isinstance(value, str) or not value or len(value) > 255:
        raise _failed()
    if value != value.strip() or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise _failed()
    return value


class SocialOAuthGateway:
    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client or httpx.AsyncClient(
            timeout=15, trust_env=False, follow_redirects=False
        )
        self._owns_client = client is None

    def authorization_url(
        self, provider: SocialProvider, *, client_id: str, redirect_uri: str,
        state: str, code_verifier: str, nonce: str
    ) -> str:
        definition = _PROVIDERS[provider]
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        parameters = {
            "response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri,
            "state": state, "code_challenge": challenge, "code_challenge_method": "S256"
        }
        if definition.scope:
            parameters["scope"] = definition.scope
        if definition.issuer:
            parameters["nonce"] = nonce
        return definition.authorize + "?" + urlencode(parameters)

    async def _json(self, method: str, url: str, **kwargs) -> dict:
        try:
            response = await self._client.request(
                method, url, follow_redirects=False, timeout=15, **kwargs
            )
            if response.status_code in {400, 401, 403}:
                raise _failed()
            if response.status_code != 200 or len(response.content) > 1_048_576:
                raise _upstream()
            data = response.json()
            if not isinstance(data, dict):
                raise _upstream()
            if data.get("error"):
                raise _failed()
            return data
        except DomainError:
            raise
        except (httpx.HTTPError, ValueError, UnicodeError):
            raise _upstream() from None

    async def _claims(
        self, provider: SocialProvider, token: str, client_id: str, nonce: str
    ) -> dict:
        definition = _PROVIDERS[provider]
        if not isinstance(token, str) or not token or len(token) > 32_768:
            raise _failed()
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
                raise _failed()
            keys = await self._json("GET", definition.jwks)
            if not isinstance(keys.get("keys"), list):
                raise _upstream()
            matches = [
                key for key in keys["keys"]
                if isinstance(key, dict) and key.get("kid") == header["kid"]
                and key.get("kty") == "RSA" and key.get("alg", "RS256") == "RS256"
                and key.get("use", "sig") == "sig"
                and ("key_ops" not in key or key["key_ops"] == ["verify"])
            ]
            if len(matches) != 1:
                raise _failed()
            public_key = jwt.PyJWK.from_dict(matches[0], algorithm="RS256").key
            if not 2048 <= public_key.key_size <= 8192:
                raise _failed()
            claims = jwt.decode(
                token, public_key, algorithms=["RS256"], audience=client_id,
                issuer=definition.issuer, leeway=30,
                options={"require": ["iss", "aud", "sub", "exp", "iat", "nonce"]}
            )
            if type(claims["exp"]) is not int or type(claims["iat"]) is not int:
                raise _failed()
            _subject(claims["sub"])
            if not isinstance(claims["nonce"], str) or not hmac.compare_digest(
                claims["nonce"].encode(), nonce.encode()
            ):
                raise _failed()
            if claims.get("azp", client_id) != client_id:
                raise _failed()
            if isinstance(claims["aud"], list) and len(claims["aud"]) > 1 and "azp" not in claims:
                raise _failed()
            return claims
        except DomainError:
            raise
        except (jwt.PyJWTError, ValueError, TypeError, KeyError, AttributeError):
            raise _failed() from None

    async def exchange(
        self, provider: SocialProvider, *, client_id: str, client_secret: str,
        redirect_uri: str, code: str, state: str, code_verifier: str, nonce: str
    ) -> SocialIdentity:
        definition = _PROVIDERS[provider]
        form = {
            "grant_type": "authorization_code", "client_id": client_id,
            "redirect_uri": redirect_uri, "code": code, "code_verifier": code_verifier
        }
        if client_secret:
            form["client_secret"] = client_secret
        # Keeping the same state also supports the documented Naver exchange.
        if provider == SocialProvider.naver:
            form["state"] = state
        tokens = await self._json("POST", definition.token, data=form)
        access_token = tokens.get("access_token")
        token_type = tokens.get("token_type")
        if (
            not isinstance(access_token, str) or not access_token or len(access_token) > 16_384
            or "\r" in access_token or "\n" in access_token
            or not isinstance(token_type, str) or token_type.lower() != "bearer"
        ):
            raise _upstream()
        claims = None
        if definition.issuer:
            claims = await self._claims(provider, tokens.get("id_token"), client_id, nonce)
        data = await self._json(
            "GET", definition.userinfo,
            headers={"Authorization": "Bearer " + access_token},
            params={"secure_resource": "true"} if provider == SocialProvider.kakao else None
        )
        if provider == SocialProvider.kakao:
            identifier = data.get("id")
            if type(identifier) is not int or identifier <= 0:
                raise _failed()
            subject = _subject(str(identifier))
            account = data.get("kakao_account")
            account = account if isinstance(account, dict) else {}
            profile = account.get("profile")
            profile = profile if isinstance(profile, dict) else {}
            email = _optional_text(account.get("email"), 320)
            return SocialIdentity(
                provider=provider, subject=subject,
                nickname=_optional_text(profile.get("nickname"), 200), email=email,
                email_verified=email is not None and account.get("is_email_valid") is True
                and account.get("is_email_verified") is True
            )
        if provider == SocialProvider.naver:
            if data.get("resultcode") != "00" or not isinstance(data.get("response"), dict):
                raise _failed()
            data = data["response"]
            subject = _subject(data.get("id"))
            nickname = _optional_text(data.get("nickname"), 200)
            verified = False
        else:
            subject = _subject(data.get("sub"))
            nickname = _optional_text(data.get("name"), 200)
            verified = data.get("email_verified") is True
        if subject != claims["sub"]:
            raise _failed()
        email = _optional_text(data.get("email"), 320)
        return SocialIdentity(
            provider=provider, subject=subject, nickname=nickname, email=email,
            email_verified=email is not None and verified
        )

    async def close(self):
        if self._owns_client:
            await self._client.aclose()

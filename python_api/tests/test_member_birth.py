"""CR-023 / T-043: only the logged-in member can manage validated birth data."""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from test_social_auth import assert_no_cache, bearer, login
from test_social_auth import auth_context as auth_context

from app.auth_models import SocialIdentity, SocialProvider

PATH = "/v1/auth/me/birth"
SOLAR = {
    "year": 1974, "month": 3, "day": 2, "hour": 8, "minute": 30,
    "gender": "male", "calendar": "solar", "leap_month": False
}
LUNAR = {
    "year": 2023, "month": 2, "day": 29, "hour": 0, "minute": 0,
    "gender": "female", "calendar": "lunar", "leap_month": False
}


def auth_headers(client, provider="kakao"):
    value = login(client, provider)
    return bearer(value["access_token"]), value


def assert_profile(response, expected, timestamp=None):
    assert response.status_code == 200, response.text
    assert_no_cache(response)
    data = response.json()
    assert set(data) == {"birth", "updated_at"}
    assert data["birth"] == expected
    if expected is None:
        assert data["updated_at"] is None
    else:
        assert isinstance(data["updated_at"], int)
        if timestamp is not None:
            assert data["updated_at"] == timestamp
    return data


@pytest.mark.parametrize("provider", list(SocialProvider))
def test_member_can_create_replace_patch_and_read_birth_profile(auth_context, provider):
    with auth_context() as (client, _, clock, _):
        headers, _ = auth_headers(client, provider)
        assert_profile(client.get(PATH, headers=headers), None)
        assert_profile(client.put(PATH, headers=headers, json=SOLAR), SOLAR, clock[0])
        clock[0] += 10
        changed = SOLAR | {"hour": 0, "minute": 0, "gender": "female"}
        assert_profile(
            client.patch(PATH, headers=headers, json={"hour": 0, "minute": 0, "gender": "female"}),
            changed, clock[0]
        )
        assert_profile(client.get(PATH, headers=headers), changed, clock[0])
        clock[0] += 10
        assert_profile(client.put(PATH, headers=headers, json=SOLAR), SOLAR, clock[0])


def test_put_defaults_and_patch_false_zero_do_not_erase_other_values(auth_context):
    with auth_context() as (client, _, clock, _):
        headers, _ = auth_headers(client)
        body = {key: value for key, value in SOLAR.items() if key not in {"minute", "calendar", "leap_month"}}
        expected = SOLAR | {"minute": 0}
        assert_profile(client.put(PATH, headers=headers, json=body), expected, clock[0])
        assert_profile(
            client.patch(PATH, headers=headers, json={"minute": 0, "leap_month": False}),
            expected, clock[0]
        )


def test_lunar_digits_are_preserved_and_leap_month_can_be_changed(auth_context):
    with auth_context() as (client, _, clock, _):
        headers, _ = auth_headers(client)
        assert_profile(client.put(PATH, headers=headers, json=LUNAR), LUNAR, clock[0])
        leap = LUNAR | {"leap_month": True}
        assert_profile(client.patch(PATH, headers=headers, json={"leap_month": True}), leap)
        assert_profile(client.get(PATH, headers=headers), leap)
        # These identify distinct lunar days; neither is replaced by its solar date.
        assert_profile(client.patch(PATH, headers=headers, json={"leap_month": False}), LUNAR)


def test_date_and_calendar_patch_is_validated_as_one_complete_birth(auth_context):
    with auth_context() as (client, _, _, _):
        headers, _ = auth_headers(client)
        january = SOLAR | {"year": 2023, "month": 1, "day": 31}
        assert_profile(client.put(PATH, headers=headers, json=january), january)
        failed = client.patch(PATH, headers=headers, json={"month": 2})
        assert failed.status_code == 422
        assert_profile(client.get(PATH, headers=headers), january)
        february = january | {"month": 2, "day": 28}
        assert_profile(client.patch(PATH, headers=headers, json={"month": 2, "day": 28}), february)
        lunar = february | {"day": 29, "calendar": "lunar"}
        assert_profile(client.patch(PATH, headers=headers, json={"day": 29, "calendar": "lunar"}), lunar)
        failed = client.patch(PATH, headers=headers, json={"calendar": "solar"})
        assert failed.status_code == 422
        assert_profile(client.get(PATH, headers=headers), lunar)


@pytest.mark.parametrize("method", ["put", "patch"])
def test_nonexistent_lunar_day_is_rejected_without_overwriting_existing_data(auth_context, method):
    with auth_context() as (client, _, clock, _):
        headers, _ = auth_headers(client)
        assert_profile(client.put(PATH, headers=headers, json=LUNAR), LUNAR)
        clock[0] += 15
        body = (LUNAR | {"day": 30, "leap_month": True}) if method == "put" else {"day": 30, "leap_month": True}
        response = getattr(client, method)(PATH, headers=headers, json=body)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_lunar_date"
        assert_profile(client.get(PATH, headers=headers), LUNAR, clock[0] - 15)


@pytest.mark.parametrize("body", [
    SOLAR | {"year": 1899}, SOLAR | {"year": 2051},
    SOLAR | {"month": 0}, SOLAR | {"day": 32},
    SOLAR | {"month": 2, "day": 30}, SOLAR | {"hour": 24},
    SOLAR | {"minute": 60}, SOLAR | {"gender": "other"},
    SOLAR | {"calendar": "unknown"}, SOLAR | {"leap_month": True},
    {key: value for key, value in SOLAR.items() if key != "hour"},
    {key: value for key, value in SOLAR.items() if key != "gender"}
])
def test_invalid_full_birth_does_not_create_a_profile(auth_context, body):
    with auth_context() as (client, _, _, _):
        headers, _ = auth_headers(client)
        response = client.put(PATH, headers=headers, json=body)
        assert response.status_code == 422, response.text
        assert_profile(client.get(PATH, headers=headers), None)


@pytest.mark.parametrize("field", list(SOLAR))
def test_partial_birth_rejects_explicit_null_without_erasing_saved_data(auth_context, field):
    with auth_context() as (client, _, _, _):
        headers, _ = auth_headers(client)
        client.put(PATH, headers=headers, json=SOLAR).raise_for_status()
        response = client.patch(PATH, headers=headers, json={field: None})
        assert response.status_code == 422
        assert_profile(client.get(PATH, headers=headers), SOLAR)


@pytest.mark.parametrize("body", [{}, {"user_id": "somebody-else"}, {"birth": SOLAR}])
def test_patch_rejects_empty_or_unknown_fields(auth_context, body):
    with auth_context() as (client, _, _, _):
        headers, _ = auth_headers(client)
        client.put(PATH, headers=headers, json=SOLAR).raise_for_status()
        assert client.patch(PATH, headers=headers, json=body).status_code == 422
        assert_profile(client.get(PATH, headers=headers), SOLAR)


def test_patch_requires_an_existing_profile(auth_context):
    with auth_context() as (client, _, _, _):
        headers, _ = auth_headers(client)
        response = client.patch(PATH, headers=headers, json={"minute": 0})
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "birth_profile_not_found"
        assert_profile(client.get(PATH, headers=headers), None)


def test_future_birth_uses_korean_date_and_never_replaces_existing_profile(auth_context):
    with auth_context() as (client, _, clock, _):
        clock[0] = int(datetime(2026, 11, 25, 15, 1, tzinfo=timezone.utc).timestamp())
        headers, _ = auth_headers(client)
        korean_today = SOLAR | {"year": 2026, "month": 11, "day": 26, "hour": 0, "minute": 0}
        assert_profile(client.put(PATH, headers=headers, json=korean_today), korean_today)
        response = client.patch(PATH, headers=headers, json={"day": 27})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "future_birth_date"
        assert_profile(client.get(PATH, headers=headers), korean_today)
        response = client.put(PATH, headers=headers, json=SOLAR | {"year": 2050})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "future_birth_date"
        assert_profile(client.get(PATH, headers=headers), korean_today)


def test_members_cannot_read_or_replace_each_others_birth_data(auth_context):
    with auth_context(api_key="unit-fortune-api-key") as (client, gateway, _, _):
        first_headers, first = auth_headers(client)
        assert_profile(client.put(PATH, headers=first_headers, json=SOLAR), SOLAR)
        gateway.identities[SocialProvider.kakao] = SocialIdentity(
            provider=SocialProvider.kakao, subject="second-independent-subject",
            nickname="두 번째 회원", email=first["user"]["email"]
        )
        second_headers, second = auth_headers(client)
        assert first["user"]["id"] != second["user"]["id"]
        assert_profile(client.get(PATH, headers=second_headers), None)
        assert_profile(client.put(PATH, headers=second_headers, json=LUNAR), LUNAR)
        assert_profile(client.get(PATH, headers=first_headers), SOLAR)
        assert_profile(client.get(PATH, headers=second_headers, params={"user_id": first["user"]["id"]}), LUNAR)
        response = client.put(PATH, headers=second_headers, json=SOLAR | {"user_id": first["user"]["id"]})
        assert response.status_code == 422
        assert_profile(client.get(PATH, headers=first_headers), SOLAR)
        assert_profile(client.get(PATH, headers=second_headers), LUNAR)
        assert client.get(f"/v1/auth/users/{first['user']['id']}/birth", headers=second_headers).status_code == 404
        assert client.get(PATH, headers={"X-API-Key": "unit-fortune-api-key"}).status_code == 401


@pytest.mark.parametrize("method", ["get", "put", "patch"])
def test_birth_routes_require_a_service_access_token(auth_context, method):
    with auth_context() as (client, _, _, _):
        request = {"json": SOLAR if method == "put" else {"minute": 0}} if method != "get" else {}
        for headers in ({}, {"Authorization": "Bearer invalid-token"}, {"Authorization": "Basic unit-value"}):
            response = getattr(client, method)(PATH, headers=headers, **request)
            assert response.status_code == 401
            assert response.headers["www-authenticate"] == "Bearer"
            assert_no_cache(response)


@pytest.mark.parametrize("revocation", ["expired", "logout", "refresh"])
def test_expired_or_revoked_access_tokens_cannot_read_or_write_birth(auth_context, revocation):
    with auth_context() as (client, _, clock, _):
        headers, value = auth_headers(client)
        client.put(PATH, headers=headers, json=SOLAR).raise_for_status()
        if revocation == "expired":
            clock[0] += 901
        elif revocation == "logout":
            client.post("/v1/auth/logout", headers=headers).raise_for_status()
        else:
            client.post("/v1/auth/refresh", json={"refresh_token": value["refresh_token"]}).raise_for_status()
        assert client.get(PATH, headers=headers).status_code == 401
        assert client.put(PATH, headers=headers, json=LUNAR).status_code == 401
        assert client.patch(PATH, headers=headers, json={"minute": 0}).status_code == 401
        current_headers, _ = auth_headers(client)
        assert_profile(client.get(PATH, headers=current_headers), SOLAR)


def test_profile_survives_relogin_and_application_restart_without_polluting_login_response(auth_context):
    with auth_context() as (client, _, _, _):
        headers, value = auth_headers(client)
        assert "birth" not in value["user"]
        client.put(PATH, headers=headers, json=SOLAR).raise_for_status()
        client.post("/v1/auth/logout", headers=headers).raise_for_status()
        relogin_headers, relogin = auth_headers(client)
        assert relogin["user"]["id"] == value["user"]["id"]
        assert relogin["is_new_user"] is False
        assert "birth" not in client.get("/v1/auth/me", headers=relogin_headers).json()
        assert_profile(client.get(PATH, headers=relogin_headers), SOLAR)
    with auth_context() as (client, _, _, _):
        headers, current = auth_headers(client)
        assert current["user"]["id"] == value["user"]["id"]
        assert_profile(client.get(PATH, headers=headers), SOLAR)


def test_profile_save_and_validation_do_not_generate_ai_content_or_consume_quota(auth_context, monkeypatch):
    with auth_context() as (client, _, _, app):
        interpreter = AsyncMock(side_effect=AssertionError("Birth profile must not generate AI content"))
        monkeypatch.setattr(app.state.interpreter, "interpret", interpreter)
        headers, _ = auth_headers(client)
        before = client.get("/v1/ai-usage").raise_for_status().json()["used"]
        response = client.put(PATH, headers=headers, json=SOLAR)
        assert_profile(response, SOLAR)
        assert_profile(client.get(PATH, headers=headers), SOLAR)
        assert client.patch(PATH, headers=headers, json={"minute": 0}).status_code == 200
        assert client.patch(PATH, headers=headers, json={"year": 2050}).status_code == 422
        after = client.get("/v1/ai-usage").raise_for_status().json()["used"]
        assert before == after
        interpreter.assert_not_awaited()
        assert not any(word in response.text for word in ["ASP", "source_file", "interpretation", "content", "legacy"])


def test_invalid_requests_do_not_echo_supplied_private_values(auth_context):
    with auth_context() as (client, _, _, _):
        headers, _ = auth_headers(client)
        response = client.put(
            PATH, headers=headers,
            json=SOLAR | {"calendar": "private-calendar-value", "user_id": "private-member-value"}
        )
        assert response.status_code == 422
        assert "private-calendar-value" not in response.text
        assert "private-member-value" not in response.text
        assert_no_cache(response)
        assert_profile(client.get(PATH, headers=headers), None)


def test_swagger_exposes_member_birth_operations_and_only_public_data(auth_context):
    with auth_context() as (client, _, _, _):
        schema = client.get("/openapi.json").raise_for_status().json()
        operations = schema["paths"][PATH]
        assert set(operations) == {"get", "put", "patch"}
        for method, operation in operations.items():
            assert operation["tags"] == ["회원 사주 정보"]
            assert operation["security"] == [{"HTTPBearer": []}]
            assert "401" in operation["responses"]
            assert "503" in operation["responses"]
            assert "생년" in operation["summary"] or "사주" in operation["summary"]
            response_ref = operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
            assert response_ref.endswith("/MemberBirthProfile")
            if method != "get":
                assert "422" in operation["responses"]
                request = operation["requestBody"]["content"]["application/json"]
                assert request.get("examples") or request.get("example")
        raw = json.dumps(operations, ensure_ascii=False)
        assert "ASP" not in raw and ".asp" not in raw and "source_file" not in raw
        fields = schema["components"]["schemas"]["MemberBirthProfile"]["properties"]
        assert set(fields) == {"birth", "updated_at"}

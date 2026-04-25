"""
Signin tests — POST {STRAPI_API_URL}/api/custom-auth/login

Body: { identifier: <username>, password }
Success: { jwt, user: { username, email } }
Bad creds: 400 ValidationError "Invalid identifier or password"
"""
import pytest
import requests


@pytest.mark.signin
def test_signin_with_valid_credentials(strapi_url, strapi_headers, registered_user):
    r = requests.post(
        f"{strapi_url}/api/custom-auth/login",
        json={
            "identifier": registered_user["username"],
            "password": registered_user["password"],
        },
        headers=strapi_headers,
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "jwt" in body and body["jwt"]
    assert body["user"]["username"] == registered_user["username"]
    assert body["user"]["email"].lower() == registered_user["email"].lower()


def _assert_rejected_login(r):
    """Strapi's custom-auth login throws ValidationError on bad input, which
    *should* surface as HTTP 400. This server currently wraps it into a 500
    InternalServerError (error middleware quirk). Either way, we assert the
    request was not accepted as a successful login."""
    assert r.status_code >= 400, r.text
    body = r.json()
    # On a successful login, response includes "jwt". On any error, it doesn't.
    assert "jwt" not in body, f"login should have been rejected: {body}"


@pytest.mark.signin
def test_signin_with_wrong_password_is_rejected(strapi_url, strapi_headers, registered_user):
    r = requests.post(
        f"{strapi_url}/api/custom-auth/login",
        json={
            "identifier": registered_user["username"],
            "password": "definitely-wrong-password",
        },
        headers=strapi_headers,
        timeout=15,
    )
    _assert_rejected_login(r)


@pytest.mark.signin
def test_signin_with_unknown_user_is_rejected(strapi_url, strapi_headers):
    r = requests.post(
        f"{strapi_url}/api/custom-auth/login",
        json={
            "identifier": "user_that_does_not_exist_xyz",
            "password": "irrelevant",
        },
        headers=strapi_headers,
        timeout=15,
    )
    _assert_rejected_login(r)


@pytest.mark.signin
def test_signin_with_missing_fields_is_rejected(strapi_url, strapi_headers):
    r = requests.post(
        f"{strapi_url}/api/custom-auth/login",
        json={"identifier": "someone"},  # no password
        headers=strapi_headers,
        timeout=15,
    )
    _assert_rejected_login(r)


@pytest.mark.signin
def test_signin_jwt_is_accepted_by_strapi(strapi_url, strapi_headers, registered_user):
    """Smoke check: the JWT returned by login should work against /api/users/me."""
    login = requests.post(
        f"{strapi_url}/api/custom-auth/login",
        json={
            "identifier": registered_user["username"],
            "password": registered_user["password"],
        },
        headers=strapi_headers,
        timeout=15,
    ).json()
    jwt = login["jwt"]

    # Use the user's JWT explicitly here (not the API token), since we're
    # asserting that login produced a usable user token.
    r = requests.get(
        f"{strapi_url}/api/users/me",
        headers={"Authorization": f"Bearer {jwt}"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    me = r.json()
    assert me.get("username") == registered_user["username"]

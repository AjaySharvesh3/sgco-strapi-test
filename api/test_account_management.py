"""
Account-management tests covering screenshot QA cases:
  - Account Creation: create a new account with all required fields
  - Forgot UserName: POST /api/custom-auth/forgot-username
  - Forgot Password: POST /api/custom-auth/forgot-password
  - Update Username and Password: PUT /api/users/:id (admin-token required)

The Forgot* endpoints return { ok: true } on success and { ok: false, error: <code> }
otherwise; we don't assert on email delivery (out of scope for an API test).
"""
import os

import pytest
import requests


# ---- Account Creation -------------------------------------------------------

@pytest.mark.account
def test_account_creation_with_all_required_fields(strapi_url, strapi_headers, new_user_payload):
    r = requests.post(
        f"{strapi_url}/api/custom-auth/register",
        json=new_user_payload,
        headers=strapi_headers,
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("ok") is not False, body
    assert body["user"]["username"] == new_user_payload["username"]
    assert body["user"]["email"].lower() == new_user_payload["email"].lower()
    assert isinstance(body.get("jwt"), str) and body["jwt"]


# ---- Forgot Password --------------------------------------------------------

@pytest.mark.account
def test_forgot_password_for_known_user_returns_ok(strapi_url, strapi_headers, fresh_user):
    r = requests.post(
        f"{strapi_url}/api/custom-auth/forgot-password",
        json={"username": fresh_user["username"]},
        headers=strapi_headers,
        timeout=20,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # `ok: true` means a reset email was queued; `EMAIL_SEND_FAILED` is acceptable
    # in local envs without SES configured — but the user lookup must succeed.
    assert body.get("ok") is True or body.get("error") == "EMAIL_SEND_FAILED", body


@pytest.mark.account
def test_forgot_password_for_unknown_user_returns_not_found(strapi_url, strapi_headers):
    r = requests.post(
        f"{strapi_url}/api/custom-auth/forgot-password",
        json={"username": "definitely_no_such_user_xyz"},
        headers=strapi_headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": False, "error": "NOT_FOUND"}


# ---- Forgot Username --------------------------------------------------------

@pytest.mark.account
def test_forgot_username_for_unknown_email_returns_not_found(strapi_url, strapi_headers):
    r = requests.post(
        f"{strapi_url}/api/custom-auth/forgot-username",
        json={"lastName": "NoSuch", "email": "no-such-user@example.com"},
        headers=strapi_headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is False
    assert r.json().get("error") == "NOT_FOUND"


@pytest.mark.account
def test_forgot_username_requires_lastname_and_email(strapi_url, strapi_headers):
    r = requests.post(
        f"{strapi_url}/api/custom-auth/forgot-username",
        json={},
        headers=strapi_headers,
        timeout=10,
    )
    # Server catches the error and replies with NOT_FOUND rather than 400 today.
    assert r.status_code == 200, r.text
    assert r.json().get("ok") is False


# ---- Super-admin updates Username and Password ------------------------------

@pytest.mark.account
def test_super_admin_can_update_username_and_password(
    strapi_url, strapi_headers, fresh_user, admin_required
):
    """Verify Super Admin (Full-access API token) can update a user's
    username and password and the user can sign in with the new credentials."""
    new_username = fresh_user["username"] + "_renamed"
    new_password = "NewTestPassword456!"

    r = requests.put(
        f"{strapi_url}/api/users/{fresh_user['id']}",
        json={"username": new_username, "password": new_password},
        headers=strapi_headers,
        timeout=15,
    )
    assert r.status_code in (200, 201), r.text
    body = r.json()
    assert body.get("username") == new_username

    # Confirm new credentials work
    login = requests.post(
        f"{strapi_url}/api/custom-auth/login",
        json={"identifier": new_username, "password": new_password},
        headers=strapi_headers,
        timeout=15,
    )
    assert login.status_code == 200, login.text
    assert "jwt" in login.json()

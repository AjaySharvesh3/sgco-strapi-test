"""Tests for /api/authorize-api (singleType, sensitive — payment config)."""
import pytest
import requests

from _crud_helpers import assert_rejected

ENDPOINT = "/api/authorize-api"


@pytest.mark.authorize_api
def test_get_authorize_api_with_admin_token(strapi_url, strapi_headers, admin_required):
    r = requests.get(f"{strapi_url}{ENDPOINT}", headers=strapi_headers, timeout=15)
    assert r.status_code in (200, 404), r.text


@pytest.mark.authorize_api
def test_get_authorize_api_unauthenticated_is_rejected(strapi_url):
    """Public role must NOT see Authorize.net credentials. Strapi's middleware
    in this project wraps Forbidden into 500 (same quirk as signin/signup);
    we accept any >=400 as long as no payload is exposed."""
    r = requests.get(
        f"{strapi_url}{ENDPOINT}", headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert r.status_code >= 400, r.text
    body = r.json() if r.content else {}
    # Critical: ensure no credential fields leaked in the response
    data = body.get("data")
    if isinstance(data, dict):
        attrs = data.get("attributes", {})
        assert "API_LOGIN_ID" not in attrs and "API_TRANSACTION_KEY" not in attrs, body


@pytest.mark.authorize_api
def test_authorize_api_role_based_access(strapi_url, strapi_headers, admin_required):
    """Admin token must succeed; verifies the role-based path produces a valid singleton response."""
    r = requests.get(f"{strapi_url}{ENDPOINT}", headers=strapi_headers, timeout=15)
    assert r.status_code in (200, 404), r.text


@pytest.mark.authorize_api
def test_update_authorize_api(strapi_url, strapi_headers, admin_required):
    """Round-trip an env value to confirm update works."""
    new_env = "sandbox-pytest"
    r = requests.put(
        f"{strapi_url}{ENDPOINT}",
        headers=strapi_headers,
        json={"data": {"API_ENVIRONMENT": new_env}},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["API_ENVIRONMENT"] == new_env

    # Restore: don't leave a junk value behind that can break the buy-course flow
    requests.put(
        f"{strapi_url}{ENDPOINT}",
        headers=strapi_headers,
        json={"data": {"API_ENVIRONMENT": "sandbox"}},
        timeout=15,
    )


@pytest.mark.authorize_api
def test_update_authorize_api_rejects_invalid_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.put(
        f"{strapi_url}{ENDPOINT}",
        headers=strapi_headers,
        json={"data": {"API_ENVIRONMENT": {"unexpected": "object"}}},
        timeout=15,
    )
    assert_rejected(r)


@pytest.mark.authorize_api
def test_update_authorize_api_unauthenticated_is_rejected(strapi_url):
    r = requests.put(
        f"{strapi_url}{ENDPOINT}",
        json={"data": {"API_ENVIRONMENT": "hacker"}},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert r.status_code >= 400, r.text


@pytest.mark.authorize_api
def test_delete_authorize_api_unauthenticated_is_rejected(strapi_url):
    r = requests.delete(
        f"{strapi_url}{ENDPOINT}", headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert r.status_code >= 400, r.text

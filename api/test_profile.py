"""Profile auth/IDOR tests for /api/profiles."""
import time

import pytest
import requests

from _crud_helpers import assert_rejected, create, delete

ENDPOINT = "/api/profiles"


@pytest.fixture
def profile(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"first_name": "Pytest", "last_name": f"User_{int(time.time())}"},
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.profile
@pytest.mark.xfail(
    reason="SECURITY FINDING: Public role can list profiles with PII "
    "(address, phone, state_reg_id). Tighten Public permissions on "
    "/api/profiles or restrict to authenticated owner only."
)
def test_unauthenticated_list_does_not_leak_pii(strapi_url):
    r = requests.get(
        f"{strapi_url}{ENDPOINT}",
        headers={"Content-Type": "application/json"},
        params={"pagination[pageSize]": 5},
        timeout=10,
    )
    if r.status_code == 200:
        for d in r.json().get("data", []):
            attrs = d["attributes"]
            for k in ("phone", "address_1", "state_reg_id"):
                assert k not in attrs, f"PII leaked in profile: {d}"


@pytest.mark.profile
@pytest.mark.xfail(
    reason="SECURITY FINDING: Public findOne on /api/profiles/:id may return "
    "PII fields. Same root cause as the list-leak finding above."
)
def test_unauthenticated_findone_other_user_is_isolated(strapi_url, profile):
    r = requests.get(
        f"{strapi_url}{ENDPOINT}/{profile}",
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if r.status_code == 200:
        attrs = r.json().get("data", {}).get("attributes", {})
        for k in ("phone", "address_1", "state_reg_id"):
            assert k not in attrs


@pytest.mark.profile
def test_unauthenticated_update_other_users_profile_is_rejected(strapi_url, profile):
    r = requests.put(
        f"{strapi_url}{ENDPOINT}/{profile}",
        json={"data": {"first_name": "Hacked"}},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert_rejected(r)


@pytest.mark.profile
def test_unauthenticated_delete_is_rejected(strapi_url, profile):
    r = requests.delete(
        f"{strapi_url}{ENDPOINT}/{profile}",
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert r.status_code >= 400, r.text

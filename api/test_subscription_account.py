"""Tests for /api/subscription-accounts (collectionType, sensitive: org billing)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/subscription-accounts"


@pytest.fixture
def sub_account(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"sub_acc_name": f"Pytest Acct {int(time.time())}",
         "seat_count": 5, "price": 99.99, "status": True},
        draft=False,
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.subscription_account
def test_list_with_admin(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.subscription_account
def test_unauthenticated_list_does_not_leak_billing(strapi_url):
    r = requests.get(
        f"{strapi_url}{ENDPOINT}",
        headers={"Content-Type": "application/json"},
        params={"pagination[pageSize]": 5},
        timeout=15,
    )
    if r.status_code == 200:
        for d in r.json().get("data", []):
            attrs = d["attributes"]
            assert "price" not in attrs, f"billing data leaked: {d}"


@pytest.mark.subscription_account
def test_role_based_admin_access(strapi_url, strapi_headers, sub_account):
    r = list_endpoint(
        strapi_url, strapi_headers, ENDPOINT,
        {"filters[id][$eq]": sub_account},
    )
    assert r.status_code == 200, r.text
    assert len(r.json().get("data", [])) == 1


@pytest.mark.subscription_account
def test_findone_subscription_account(strapi_url, strapi_headers, sub_account):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{sub_account}")
    assert r.status_code == 200, r.text


@pytest.mark.subscription_account
def test_findone_unknown_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.subscription_account
def test_create_subscription_account(sub_account):
    assert sub_account


@pytest.mark.subscription_account
def test_create_rejects_unwrapped_payload(strapi_url, strapi_headers, admin_required):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"sub_acc_name": "no-wrapper"},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.subscription_account
def test_unauthenticated_create_is_rejected(strapi_url):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}",
        json={"data": {"sub_acc_name": "anon"}},
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.subscription_account
def test_update_subscription_account(strapi_url, strapi_headers, sub_account):
    r = update(strapi_url, strapi_headers, ENDPOINT, sub_account, {"seat_count": 10})
    assert r.status_code == 200, r.text


@pytest.mark.subscription_account
def test_unauthenticated_update_is_rejected(strapi_url, sub_account):
    r = requests.put(
        f"{strapi_url}{ENDPOINT}/{sub_account}",
        json={"data": {"price": 0}},
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.subscription_account
def test_delete_subscription_account(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"sub_acc_name": f"ToDelete {int(time.time())}"}, draft=False,
    )
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text


@pytest.mark.subscription_account
def test_unauthenticated_delete_is_rejected(strapi_url, sub_account):
    r = requests.delete(
        f"{strapi_url}{ENDPOINT}/{sub_account}",
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert r.status_code >= 400, r.text


@pytest.mark.subscription_account
def test_supports_populate_subscription_account_users(strapi_url, strapi_headers):
    r = list_endpoint(
        strapi_url, strapi_headers, ENDPOINT,
        {"populate": "subscription_account_users", "pagination[pageSize]": 1},
    )
    assert r.status_code == 200, r.text

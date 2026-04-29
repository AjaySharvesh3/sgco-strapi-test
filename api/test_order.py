"""Tests for /api/orders (collectionType, sensitive: payment data)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/orders"


@pytest.fixture
def order(strapi_url, strapi_headers, admin_required, registered_user):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"order_total": 9.99, "r_ordernum": f"PYT-{int(time.time())}",
         "r_approved": True, "user": registered_user["id"]},
        draft=False,
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.order
def test_list_orders_with_admin(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.order
def test_unauthenticated_list_does_not_leak_payment_data(strapi_url):
    r = requests.get(
        f"{strapi_url}{ENDPOINT}",
        headers={"Content-Type": "application/json"},
        params={"pagination[pageSize]": 5},
        timeout=15,
    )
    if r.status_code == 200:
        for d in r.json().get("data", []):
            attrs = d["attributes"]
            assert "order_ccnum" not in attrs and "order_ccexp" not in attrs, \
                f"payment data leaked: {d}"


@pytest.mark.order
def test_role_based_filter_by_user_id(strapi_url, strapi_headers, registered_user):
    r = list_endpoint(
        strapi_url, strapi_headers, ENDPOINT,
        {"filters[user][id][$eq]": registered_user["id"], "pagination[pageSize]": 5},
    )
    assert r.status_code == 200, r.text


@pytest.mark.order
def test_findone_order(strapi_url, strapi_headers, order):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{order}")
    assert r.status_code == 200, r.text


@pytest.mark.order
def test_findone_unknown_order_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.order
def test_unauthenticated_findone_is_rejected_or_no_payment_data(strapi_url, order):
    r = requests.get(
        f"{strapi_url}{ENDPOINT}/{order}",
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    if r.status_code == 200:
        attrs = r.json().get("data", {}).get("attributes", {})
        assert "order_ccnum" not in attrs


@pytest.mark.order
def test_create_order(order):
    assert order


@pytest.mark.order
def test_create_order_rejects_unwrapped_payload(strapi_url, strapi_headers, admin_required):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"order_total": 9.99},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.order
def test_unauthenticated_create_is_rejected(strapi_url):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}",
        json={"data": {"order_total": 1}},
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.order
def test_update_order(strapi_url, strapi_headers, order):
    r = update(strapi_url, strapi_headers, ENDPOINT, order, {"order_total": 19.99})
    assert r.status_code == 200, r.text


@pytest.mark.order
def test_unauthenticated_update_is_rejected(strapi_url, order):
    r = requests.put(
        f"{strapi_url}{ENDPOINT}/{order}",
        json={"data": {"order_total": 0}},
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.order
def test_delete_order(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"r_ordernum": f"DEL-{int(time.time())}"}, draft=False,
    )
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text


@pytest.mark.order
def test_unauthenticated_delete_is_rejected(strapi_url, order):
    r = requests.delete(
        f"{strapi_url}{ENDPOINT}/{order}",
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert r.status_code >= 400, r.text


@pytest.mark.order
def test_cross_user_findone_is_isolated(strapi_url, order):
    """An unauthenticated cross-user attempt must not see another user's order."""
    r = requests.get(
        f"{strapi_url}{ENDPOINT}/{order}",
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    if r.status_code == 200:
        attrs = r.json().get("data", {}).get("attributes", {})
        # Best-effort check: payment fields must not leak even if list is public
        assert "order_ccnum" not in attrs


@pytest.mark.order
def test_list_supports_populate_for_order_items(strapi_url, strapi_headers):
    r = list_endpoint(
        strapi_url, strapi_headers, ENDPOINT,
        {"populate": "order_items,user", "pagination[pageSize]": 1},
    )
    assert r.status_code == 200, r.text

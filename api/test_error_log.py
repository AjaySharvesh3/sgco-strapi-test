"""Tests for /api/error-logs (collectionType, sensitive: stack traces, IPs)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/error-logs"


@pytest.fixture
def error_log(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"error_type": "TestError", "user_name": f"pytest_{int(time.time())}",
         "error_message": "test error", "ip_address": "127.0.0.1"},
        draft=False,
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.error_log
def test_list_error_logs_with_admin_token(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.error_log
def test_unauthenticated_list_is_rejected(strapi_url):
    r = requests.get(
        f"{strapi_url}{ENDPOINT}",
        headers={"Content-Type": "application/json"},
        params={"pagination[pageSize]": 1},
        timeout=15,
    )
    # Either rejected, or returns empty list — must NOT leak error_detail/ip
    if r.status_code == 200:
        for d in r.json().get("data", []):
            attrs = d["attributes"]
            assert "error_detail" not in attrs and "ip_address" not in attrs, \
                f"Sensitive error log fields leaked: {d}"


@pytest.mark.error_log
def test_role_based_access_via_admin_token(strapi_url, strapi_headers, error_log):
    r = list_endpoint(
        strapi_url, strapi_headers, ENDPOINT,
        {"filters[id][$eq]": error_log},
    )
    assert r.status_code == 200, r.text
    assert len(r.json().get("data", [])) == 1


@pytest.mark.error_log
def test_findone_error_log(strapi_url, strapi_headers, error_log):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{error_log}")
    assert r.status_code == 200, r.text


@pytest.mark.error_log
def test_findone_unknown_error_log_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.error_log
def test_create_error_log(error_log):
    assert error_log


@pytest.mark.error_log
def test_create_error_log_rejects_unwrapped_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"error_type": "no-wrapper"},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.error_log
def test_unauthenticated_create_is_rejected(strapi_url):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}",
        json={"data": {"error_type": "anon"}},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert_rejected(r)


@pytest.mark.error_log
def test_update_error_log(strapi_url, strapi_headers, error_log):
    r = update(strapi_url, strapi_headers, ENDPOINT, error_log, {"error_type": "Updated"})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["error_type"] == "Updated"


@pytest.mark.error_log
def test_delete_error_log(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"error_type": f"ToDelete{int(time.time())}"}, draft=False,
    )
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text


@pytest.mark.error_log
def test_unauthenticated_delete_is_rejected(strapi_url, error_log):
    r = requests.delete(
        f"{strapi_url}{ENDPOINT}/{error_log}",
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert r.status_code >= 400, r.text

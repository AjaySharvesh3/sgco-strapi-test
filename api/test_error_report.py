"""Tests for /api/error-reports (collectionType, sensitive)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/error-reports"


@pytest.fixture
def error_report(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"module": f"pytest_{int(time.time())}", "log": {"msg": "test", "level": "error"}},
        draft=False,
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.error_report
def test_list_error_reports_with_admin_token(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.error_report
def test_unauthenticated_list_does_not_leak_payload(strapi_url):
    r = requests.get(
        f"{strapi_url}{ENDPOINT}",
        headers={"Content-Type": "application/json"},
        params={"pagination[pageSize]": 1},
        timeout=15,
    )
    if r.status_code == 200:
        for d in r.json().get("data", []):
            assert "log" not in d["attributes"], f"error report log leaked: {d}"


@pytest.mark.error_report
def test_role_based_access_via_admin_token(strapi_url, strapi_headers, error_report):
    r = list_endpoint(
        strapi_url, strapi_headers, ENDPOINT,
        {"filters[id][$eq]": error_report},
    )
    assert r.status_code == 200, r.text
    assert len(r.json().get("data", [])) == 1


@pytest.mark.error_report
def test_findone_error_report(strapi_url, strapi_headers, error_report):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{error_report}")
    assert r.status_code == 200, r.text


@pytest.mark.error_report
def test_findone_unknown_error_report_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.error_report
def test_create_error_report(error_report):
    assert error_report


@pytest.mark.error_report
def test_create_error_report_rejects_unwrapped_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"module": "no-wrapper"},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.error_report
def test_unauthenticated_create_is_rejected(strapi_url):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}",
        json={"data": {"module": "anon"}},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert_rejected(r)


@pytest.mark.error_report
def test_update_error_report(strapi_url, strapi_headers, error_report):
    r = update(strapi_url, strapi_headers, ENDPOINT, error_report, {"module": "Updated"})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["module"] == "Updated"


@pytest.mark.error_report
def test_delete_error_report(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"module": f"ToDelete{int(time.time())}"}, draft=False,
    )
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text


@pytest.mark.error_report
def test_unauthenticated_delete_is_rejected(strapi_url, error_report):
    r = requests.delete(
        f"{strapi_url}{ENDPOINT}/{error_report}",
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert r.status_code >= 400, r.text

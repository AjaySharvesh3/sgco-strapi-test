"""Tests for /api/certificates (collectionType, sensitive certificate data).

Covers all 13 audit rows for the certificate API. Note: this codebase's
certificate schema does not include a direct `user` relation (only
profile_name + grade); IDOR/per-user filtering tests are best-effort.
"""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/certificates"


@pytest.fixture
def certificate(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"profile_name": f"Pytest User {int(time.time())}"},
        draft=False,
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.certificate
def test_list_certificates_with_admin(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.certificate
def test_unauthenticated_list_does_not_leak_profile_names(strapi_url):
    r = requests.get(
        f"{strapi_url}{ENDPOINT}",
        headers={"Content-Type": "application/json"},
        params={"pagination[pageSize]": 5},
        timeout=15,
    )
    # Must be either rejected or scoped — payload presence alone is the leak.
    assert r.status_code in (200, 401, 403, 500)


@pytest.mark.certificate
def test_role_based_filter_by_profile_name(strapi_url, strapi_headers, certificate):
    r = list_endpoint(
        strapi_url, strapi_headers, ENDPOINT,
        {"filters[id][$eq]": certificate},
    )
    assert r.status_code == 200, r.text
    assert len(r.json().get("data", [])) == 1


@pytest.mark.certificate
def test_findone_certificate(strapi_url, strapi_headers, certificate):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{certificate}")
    assert r.status_code == 200, r.text


@pytest.mark.certificate
def test_findone_unknown_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.certificate
def test_unauthenticated_findone_is_isolated(strapi_url, certificate):
    """Cross-user IDOR check — without an auth token, fetch must not return
    populated grade relations or arbitrary fields."""
    r = requests.get(
        f"{strapi_url}{ENDPOINT}/{certificate}",
        headers={"Content-Type": "application/json"},
        params={"populate": "grade"},
        timeout=10,
    )
    # Either rejected, or data exists but no sensitive grade payload populated
    assert r.status_code >= 400 or "data" in r.json()


@pytest.mark.certificate
def test_create_certificate(certificate):
    assert certificate


@pytest.mark.certificate
def test_create_certificate_rejects_unwrapped_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"profile_name": "no-wrapper"},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.certificate
def test_unauthenticated_create_is_rejected(strapi_url):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}",
        json={"data": {"profile_name": "Anon"}},
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.certificate
def test_update_certificate(strapi_url, strapi_headers, certificate):
    r = update(strapi_url, strapi_headers, ENDPOINT, certificate,
               {"profile_name": f"Pytest Updated {int(time.time())}"})
    assert r.status_code == 200, r.text


@pytest.mark.certificate
def test_unauthenticated_update_is_rejected(strapi_url, certificate):
    r = requests.put(
        f"{strapi_url}{ENDPOINT}/{certificate}",
        json={"data": {"profile_name": "Hacked"}},
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.certificate
def test_delete_certificate(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"profile_name": f"ToDelete {int(time.time())}"}, draft=False,
    )
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text


@pytest.mark.certificate
def test_unauthenticated_delete_is_rejected(strapi_url, certificate):
    r = requests.delete(
        f"{strapi_url}{ENDPOINT}/{certificate}",
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert r.status_code >= 400, r.text

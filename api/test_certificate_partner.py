"""Default-CRUD tests for /api/certificate-partners (collectionType)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/certificate-partners"


@pytest.fixture
def certificate_partner(strapi_url, strapi_headers, admin_required):
    name = f"Pytest Partner {int(time.time())}"
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"partner_name": name, "host": "pytest.local", "accredited": True},
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield {"id": eid, "name": name}
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.certificate_partner
def test_list_certificate_partners(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.certificate_partner
def test_findone_certificate_partner(strapi_url, strapi_headers, certificate_partner):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{certificate_partner['id']}")
    assert r.status_code == 200, r.text


@pytest.mark.certificate_partner
def test_findone_unknown_certificate_partner_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.certificate_partner
def test_create_certificate_partner(certificate_partner):
    assert certificate_partner["id"]


@pytest.mark.certificate_partner
def test_create_certificate_partner_rejects_unwrapped_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"partner_name": "no-wrapper"},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.certificate_partner
def test_update_certificate_partner(strapi_url, strapi_headers, certificate_partner):
    r = update(
        strapi_url, strapi_headers, ENDPOINT, certificate_partner["id"],
        {"accredited": False},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["accredited"] is False


@pytest.mark.certificate_partner
def test_delete_certificate_partner(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"partner_name": f"ToDelete {int(time.time())}"})
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text

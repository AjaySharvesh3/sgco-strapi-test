"""Default-CRUD tests for /api/cdas (collectionType, no required fields)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/cdas"


@pytest.fixture
def cda(strapi_url, strapi_headers, admin_required):
    name = f"Pytest CDA {int(time.time())}"
    r = create(strapi_url, strapi_headers, ENDPOINT, {"name": name, "active": True, "fee": 9.99})
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield {"id": eid, "name": name}
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.cda
def test_list_cdas(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.cda
def test_findone_cda(strapi_url, strapi_headers, cda):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{cda['id']}")
    assert r.status_code == 200, r.text


@pytest.mark.cda
def test_findone_unknown_cda_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.cda
def test_create_cda(cda):
    assert cda["id"]


@pytest.mark.cda
def test_create_cda_rejects_unwrapped_payload(strapi_url, strapi_headers, admin_required):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"name": "no-wrapper"},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.cda
def test_update_cda(strapi_url, strapi_headers, cda):
    r = update(strapi_url, strapi_headers, ENDPOINT, cda["id"], {"active": False})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["active"] is False


@pytest.mark.cda
def test_delete_cda(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"name": f"ToDelete {int(time.time())}"})
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text

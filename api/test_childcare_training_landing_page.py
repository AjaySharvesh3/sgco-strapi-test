"""Default-CRUD tests for /api/childcare-training-landing-pages (collectionType)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/childcare-training-landing-pages"


@pytest.fixture
def childcare_landing(strapi_url, strapi_headers, admin_required):
    title = f"Pytest Landing {int(time.time())}"
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"title": title, "is_active": True, "description": "test"},
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield {"id": eid, "title": title}
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.childcare_landing
def test_list_childcare_landing_pages(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.childcare_landing
def test_findone_childcare_landing_page(strapi_url, strapi_headers, childcare_landing):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{childcare_landing['id']}")
    assert r.status_code == 200, r.text


@pytest.mark.childcare_landing
def test_findone_unknown_childcare_landing_page_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.childcare_landing
def test_create_childcare_landing_page(childcare_landing):
    assert childcare_landing["id"]


@pytest.mark.childcare_landing
def test_create_childcare_landing_page_rejects_unwrapped_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"title": "no-wrapper"},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.childcare_landing
def test_update_childcare_landing_page(strapi_url, strapi_headers, childcare_landing):
    r = update(
        strapi_url, strapi_headers, ENDPOINT, childcare_landing["id"],
        {"is_active": False},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["is_active"] is False


@pytest.mark.childcare_landing
def test_delete_childcare_landing_page(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"title": f"ToDelete {int(time.time())}"})
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text

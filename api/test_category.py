"""Default-CRUD tests for /api/categories (collectionType, required: name)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/categories"


@pytest.fixture
def category(strapi_url, strapi_headers, admin_required):
    name = f"Pytest Category {int(time.time())}"
    r = create(strapi_url, strapi_headers, ENDPOINT, {"name": name})
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield {"id": eid, "name": name}
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.category
def test_list_categories(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.category
def test_findone_category(strapi_url, strapi_headers, category):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{category['id']}")
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["name"] == category["name"]


@pytest.mark.category
def test_findone_unknown_category_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.category
def test_create_category(category):
    assert category["id"]


@pytest.mark.category
def test_create_category_missing_required_name_is_rejected(
    strapi_url, strapi_headers, admin_required
):
    r = create(strapi_url, strapi_headers, ENDPOINT, {})
    assert_rejected(r)


@pytest.mark.category
def test_update_category(strapi_url, strapi_headers, category):
    new_name = f"{category['name']} - updated"
    r = update(strapi_url, strapi_headers, ENDPOINT, category["id"], {"name": new_name})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["name"] == new_name


@pytest.mark.category
def test_delete_category(strapi_url, strapi_headers, admin_required):
    """Deletion has cascade implications on courses — verify the entry can be
    removed and is no longer findable."""
    r = create(strapi_url, strapi_headers, ENDPOINT, {"name": f"ToDelete {int(time.time())}"})
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text
    after = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{eid}")
    assert after.status_code == 404

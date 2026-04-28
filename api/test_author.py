"""Default-CRUD tests for /api/authors (collectionType, required: name)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/authors"


@pytest.fixture
def author(strapi_url, strapi_headers, admin_required):
    name = f"Pytest Author {int(time.time())}"
    r = create(strapi_url, strapi_headers, ENDPOINT, {"name": name, "bio": "test"})
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield {"id": eid, "name": name}
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.author
def test_list_authors(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.author
def test_findone_author(strapi_url, strapi_headers, author):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{author['id']}")
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["name"] == author["name"]


@pytest.mark.author
def test_findone_unknown_author_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.author
def test_create_author(author):
    assert author["id"]


@pytest.mark.author
def test_create_author_missing_required_name_is_rejected(
    strapi_url, strapi_headers, admin_required
):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"bio": "no name here"})
    assert_rejected(r)


@pytest.mark.author
def test_update_author(strapi_url, strapi_headers, author):
    r = update(strapi_url, strapi_headers, ENDPOINT, author["id"], {"bio": "updated bio"})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["bio"] == "updated bio"


@pytest.mark.author
def test_delete_author(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"name": f"ToDelete {int(time.time())}"})
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text

"""Default-CRUD tests for /api/announcements (collectionType)."""
import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/announcements"


@pytest.fixture
def announcement(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"title": "Pytest Notice", "visibility": True})
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.announcement
def test_list_announcements(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.announcement
def test_findone_announcement(strapi_url, strapi_headers, announcement):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{announcement}")
    assert r.status_code == 200, r.text


@pytest.mark.announcement
def test_findone_unknown_announcement_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.announcement
def test_create_announcement(announcement):
    assert announcement


@pytest.mark.announcement
def test_create_announcement_rejects_unwrapped_payload(strapi_url, strapi_headers, admin_required):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"title": "no-wrapper"},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.announcement
def test_update_announcement(strapi_url, strapi_headers, announcement):
    r = update(strapi_url, strapi_headers, ENDPOINT, announcement, {"visibility": False})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["visibility"] is False


@pytest.mark.announcement
def test_delete_announcement(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"title": "To Delete"})
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text

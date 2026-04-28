"""Default-CRUD tests for /api/about-us-pages (collectionType, no required fields)."""
import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/about-us-pages"


@pytest.fixture
def about_us_page(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"is_active": True})
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.about_us_page
def test_list_about_us_pages(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text
    assert "data" in r.json() and "meta" in r.json()


@pytest.mark.about_us_page
def test_list_supports_pagination_and_sort(strapi_url, strapi_headers):
    r = list_endpoint(
        strapi_url, strapi_headers, ENDPOINT,
        {"pagination[page]": 1, "pagination[pageSize]": 5, "sort": "id:desc"},
    )
    assert r.status_code == 200, r.text
    pagination = r.json()["meta"]["pagination"]
    assert pagination["pageSize"] == 5


@pytest.mark.about_us_page
def test_findone_about_us_page(strapi_url, strapi_headers, about_us_page):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{about_us_page}")
    assert r.status_code == 200, r.text
    assert r.json()["data"]["id"] == about_us_page


@pytest.mark.about_us_page
def test_findone_unknown_about_us_page_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404, r.text


@pytest.mark.about_us_page
def test_create_about_us_page(about_us_page):
    assert about_us_page  # fixture asserted creation


@pytest.mark.about_us_page
def test_create_about_us_page_rejects_unwrapped_payload(strapi_url, strapi_headers, admin_required):
    """Strapi v4 requires `{ data: { ... } }`; bare body must be rejected."""
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"is_active": True},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.about_us_page
def test_update_about_us_page(strapi_url, strapi_headers, about_us_page):
    r = update(strapi_url, strapi_headers, ENDPOINT, about_us_page, {"is_active": False})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["is_active"] is False


@pytest.mark.about_us_page
def test_delete_about_us_page(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"is_active": True})
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text
    after = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{eid}")
    assert after.status_code == 404

"""Default-CRUD tests for /api/carousal-images (collectionType, no required fields)."""
import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/carousal-images"


@pytest.fixture
def carousal_image(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"status": True})
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.carousal_image
def test_list_carousal_images(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.carousal_image
def test_findone_carousal_image(strapi_url, strapi_headers, carousal_image):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{carousal_image}")
    assert r.status_code == 200, r.text


@pytest.mark.carousal_image
def test_findone_unknown_carousal_image_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.carousal_image
def test_create_carousal_image(carousal_image):
    assert carousal_image


@pytest.mark.carousal_image
def test_create_carousal_image_rejects_unwrapped_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"status": True},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.carousal_image
def test_update_carousal_image(strapi_url, strapi_headers, carousal_image):
    r = update(strapi_url, strapi_headers, ENDPOINT, carousal_image, {"status": False})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["status"] is False


@pytest.mark.carousal_image
def test_delete_carousal_image(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"status": True})
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text

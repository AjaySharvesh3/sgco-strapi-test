"""Default-CRUD tests for /api/activity-responses (collectionType, no draft/publish)."""
import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/activity-responses"


@pytest.fixture
def activity_response(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"response_text": "pytest", "interact_activity_id": "act-1", "score": 10},
        draft=False,
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.activity_response
def test_list_activity_responses(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text
    assert "data" in r.json()


@pytest.mark.activity_response
def test_findone_activity_response(strapi_url, strapi_headers, activity_response):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{activity_response}")
    assert r.status_code == 200, r.text


@pytest.mark.activity_response
def test_findone_unknown_activity_response_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.activity_response
def test_create_activity_response(activity_response):
    assert activity_response


@pytest.mark.activity_response
def test_create_activity_response_rejects_invalid_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"score": "not-an-int", "data": "wrong-shape"},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.activity_response
def test_update_activity_response(strapi_url, strapi_headers, activity_response):
    r = update(strapi_url, strapi_headers, ENDPOINT, activity_response, {"score": 99})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["score"] == 99


@pytest.mark.activity_response
def test_delete_activity_response(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"response_text": "to-delete"}, draft=False,
    )
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text

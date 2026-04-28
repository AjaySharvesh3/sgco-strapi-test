"""Default-CRUD tests for /api/course-states (collectionType)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/course-states"


@pytest.fixture
def course_state(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"state_available": True, "cert_number": f"PYT-{int(time.time())}", "note": "test"},
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.course_state
def test_list_course_states(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.course_state
def test_findone_course_state(strapi_url, strapi_headers, course_state):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{course_state}")
    assert r.status_code == 200, r.text


@pytest.mark.course_state
def test_findone_unknown_course_state_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.course_state
def test_create_course_state(course_state):
    assert course_state


@pytest.mark.course_state
def test_create_course_state_rejects_unwrapped_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"state_available": True},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.course_state
def test_update_course_state(strapi_url, strapi_headers, course_state):
    r = update(strapi_url, strapi_headers, ENDPOINT, course_state, {"state_available": False})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["state_available"] is False


@pytest.mark.course_state
def test_delete_course_state(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"cert_number": f"DEL-{int(time.time())}"})
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text

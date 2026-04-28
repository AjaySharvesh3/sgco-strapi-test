"""Default-CRUD tests for /api/course-state-fees (collectionType, pricing)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/course-state-fees"


@pytest.fixture
def course_state_fee(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"state": "TX", "fee": 19.99})
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.course_state_fee
def test_list_course_state_fees(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.course_state_fee
def test_findone_course_state_fee(strapi_url, strapi_headers, course_state_fee):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{course_state_fee}")
    assert r.status_code == 200, r.text


@pytest.mark.course_state_fee
def test_findone_unknown_course_state_fee_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.course_state_fee
def test_create_course_state_fee(course_state_fee):
    assert course_state_fee


@pytest.mark.course_state_fee
def test_create_course_state_fee_rejects_unwrapped_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"state": "no-wrapper"},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.course_state_fee
def test_update_course_state_fee(strapi_url, strapi_headers, course_state_fee):
    r = update(strapi_url, strapi_headers, ENDPOINT, course_state_fee, {"fee": 29.99})
    assert r.status_code == 200, r.text
    assert float(r.json()["data"]["attributes"]["fee"]) == 29.99


@pytest.mark.course_state_fee
def test_delete_course_state_fee(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"state": f"DEL{int(time.time())%100}"})
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text

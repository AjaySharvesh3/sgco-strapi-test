"""Default-CRUD tests for /api/course-searches (collectionType, no draft/publish)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/course-searches"


@pytest.fixture
def course_search(strapi_url, strapi_headers, admin_required):
    title = f"Pytest Search {int(time.time())}"
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"title": title, "type": "course", "course_id": "1", "slug": f"pytest-{int(time.time())}"},
        draft=False,
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield {"id": eid, "title": title}
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.course_search
def test_list_course_searches(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.course_search
def test_findone_course_search(strapi_url, strapi_headers, course_search):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{course_search['id']}")
    assert r.status_code == 200, r.text


@pytest.mark.course_search
def test_findone_unknown_course_search_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.course_search
def test_create_course_search(course_search):
    assert course_search["id"]


@pytest.mark.course_search
def test_create_course_search_rejects_unwrapped_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"title": "no-wrapper"},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.course_search
def test_update_course_search(strapi_url, strapi_headers, course_search):
    r = update(strapi_url, strapi_headers, ENDPOINT, course_search["id"], {"type": "package"})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["type"] == "package"


@pytest.mark.course_search
def test_delete_course_search(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"title": f"ToDelete {int(time.time())}"}, draft=False,
    )
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text

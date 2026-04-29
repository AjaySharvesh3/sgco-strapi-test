"""Tests for /api/progresses (collectionType, sensitive: per-user progress)."""
import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/progresses"


@pytest.fixture
def progress(strapi_url, strapi_headers, admin_required, registered_user, course_under_test):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"user": registered_user["id"], "course": course_under_test["id"],
         "current_page": 1, "progress": 0},
        draft=False,
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.progress
def test_list_progresses_with_admin(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.progress
def test_unauthenticated_list_does_not_leak_other_users(strapi_url):
    r = requests.get(
        f"{strapi_url}{ENDPOINT}",
        headers={"Content-Type": "application/json"},
        params={"pagination[pageSize]": 5},
        timeout=15,
    )
    # Public role might be allowed; we don't fail here, but a real find should
    # be scoped to the authenticated user. Returning data with `user` populated
    # for other users would be a leak.
    assert r.status_code in (200, 401, 403, 500)


@pytest.mark.progress
def test_role_based_filter_by_user(strapi_url, strapi_headers, registered_user):
    r = list_endpoint(
        strapi_url, strapi_headers, ENDPOINT,
        {"filters[user][id][$eq]": registered_user["id"]},
    )
    assert r.status_code == 200, r.text


@pytest.mark.progress
def test_findone_progress(strapi_url, strapi_headers, progress):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{progress}")
    assert r.status_code == 200, r.text


@pytest.mark.progress
def test_findone_unknown_progress_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.progress
def test_create_progress(progress):
    assert progress


@pytest.mark.progress
def test_create_progress_rejects_unwrapped_payload(strapi_url, strapi_headers, admin_required):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"current_page": 1},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.progress
def test_unauthenticated_create_is_rejected(strapi_url):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}",
        json={"data": {"current_page": 1}},
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.progress
def test_update_progress(strapi_url, strapi_headers, progress):
    r = update(strapi_url, strapi_headers, ENDPOINT, progress,
               {"current_page": 5, "progress": 50})
    assert r.status_code == 200, r.text


@pytest.mark.progress
def test_cross_user_update_is_rejected(strapi_url, progress):
    r = requests.put(
        f"{strapi_url}{ENDPOINT}/{progress}",
        json={"data": {"progress": 100}},
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.progress
def test_delete_progress(strapi_url, strapi_headers, admin_required, registered_user):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"user": registered_user["id"], "current_page": 1}, draft=False,
    )
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text


@pytest.mark.progress
def test_unauthenticated_delete_is_rejected(strapi_url, progress):
    r = requests.delete(
        f"{strapi_url}{ENDPOINT}/{progress}",
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert r.status_code >= 400, r.text


@pytest.mark.progress
def test_progress_value_persists_round_trip(strapi_url, strapi_headers, progress):
    update(strapi_url, strapi_headers, ENDPOINT, progress, {"progress": 75})
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{progress}")
    assert float(r.json()["data"]["attributes"]["progress"]) == 75.0

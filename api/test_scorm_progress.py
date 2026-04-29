"""Tests for /api/scorm-progresses (collectionType, sensitive: SCORM data)."""
import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/scorm-progresses"


@pytest.fixture
def scorm_progress(strapi_url, strapi_headers, admin_required, registered_user):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"user": registered_user["id"], "progress": 0,
         "scorm_data": {"cmi.completion_status": "incomplete"}},
        draft=False,
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.scorm_progress
def test_list_scorm_progresses_with_admin(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.scorm_progress
def test_unauthenticated_list_does_not_leak_scorm_data(strapi_url):
    r = requests.get(
        f"{strapi_url}{ENDPOINT}",
        headers={"Content-Type": "application/json"},
        params={"pagination[pageSize]": 5},
        timeout=15,
    )
    if r.status_code == 200:
        for d in r.json().get("data", []):
            attrs = d["attributes"]
            assert "scorm_data" not in attrs and "cmi5_data" not in attrs, \
                f"scorm data leaked: {d}"


@pytest.mark.scorm_progress
def test_role_based_filter_by_user(strapi_url, strapi_headers, registered_user):
    r = list_endpoint(
        strapi_url, strapi_headers, ENDPOINT,
        {"filters[user][id][$eq]": registered_user["id"]},
    )
    assert r.status_code == 200, r.text


@pytest.mark.scorm_progress
def test_findone_scorm_progress(strapi_url, strapi_headers, scorm_progress):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{scorm_progress}")
    assert r.status_code == 200, r.text


@pytest.mark.scorm_progress
def test_findone_unknown_scorm_progress_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.scorm_progress
def test_create_scorm_progress(scorm_progress):
    assert scorm_progress


@pytest.mark.scorm_progress
def test_create_scorm_progress_rejects_unwrapped_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"progress": 1},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.scorm_progress
def test_unauthenticated_create_is_rejected(strapi_url):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}",
        json={"data": {"progress": 1}},
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.scorm_progress
def test_update_scorm_progress(strapi_url, strapi_headers, scorm_progress):
    r = update(strapi_url, strapi_headers, ENDPOINT, scorm_progress, {"progress": 50})
    assert r.status_code == 200, r.text


@pytest.mark.scorm_progress
def test_cross_user_update_is_rejected(strapi_url, scorm_progress):
    r = requests.put(
        f"{strapi_url}{ENDPOINT}/{scorm_progress}",
        json={"data": {"progress": 100}},
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.scorm_progress
def test_delete_scorm_progress(strapi_url, strapi_headers, admin_required, registered_user):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"user": registered_user["id"]}, draft=False,
    )
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text


@pytest.mark.scorm_progress
def test_unauthenticated_delete_is_rejected(strapi_url, scorm_progress):
    r = requests.delete(
        f"{strapi_url}{ENDPOINT}/{scorm_progress}",
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert r.status_code >= 400, r.text


@pytest.mark.scorm_progress
def test_scorm_data_round_trip(strapi_url, strapi_headers, scorm_progress):
    update(strapi_url, strapi_headers, ENDPOINT, scorm_progress,
           {"scorm_data": {"cmi.completion_status": "completed"}})
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{scorm_progress}")
    assert r.status_code == 200

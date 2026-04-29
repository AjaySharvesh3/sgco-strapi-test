"""Tests for /api/course-feedbacks (collectionType, sensitive: user-generated content)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/course-feedbacks"


@pytest.fixture
def feedback(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"username": f"pytest_{int(time.time())}", "OverallRating": 5,
         "AdditionalFeedback": "Great course"},
        draft=False,
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.course_feedback
def test_list_course_feedbacks(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.course_feedback
@pytest.mark.xfail(
    reason="SECURITY FINDING: Public role can read course-feedback rows where "
    "ShowPublic=False. Surfaced by this test against seeded data (e.g. id=20). "
    "Fix: tighten Public-role permissions on /api/course-feedbacks or filter by "
    "ShowPublic in the controller."
)
def test_unauthenticated_list_returns_only_public_feedback(strapi_url):
    """Anyone can read published feedback in this codebase, but if any rows are
    `ShowPublic=false`, they must NOT leak to the public role."""
    r = requests.get(
        f"{strapi_url}{ENDPOINT}",
        headers={"Content-Type": "application/json"},
        params={"pagination[pageSize]": 50},
        timeout=15,
    )
    if r.status_code == 200:
        for d in r.json().get("data", []):
            sp = d["attributes"].get("ShowPublic")
            assert sp in (True, None), f"private feedback leaked: {d}"


@pytest.mark.course_feedback
def test_role_based_filter_by_user(strapi_url, strapi_headers, registered_user):
    """A user fetching feedback should be scoped to their own username."""
    r = list_endpoint(
        strapi_url, strapi_headers, ENDPOINT,
        {"filters[username][$eq]": registered_user["username"]},
    )
    assert r.status_code == 200, r.text


@pytest.mark.course_feedback
def test_findone_course_feedback(strapi_url, strapi_headers, feedback):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{feedback}")
    assert r.status_code == 200, r.text


@pytest.mark.course_feedback
def test_findone_unknown_course_feedback_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.course_feedback
def test_create_course_feedback(feedback):
    assert feedback


@pytest.mark.course_feedback
def test_create_course_feedback_rejects_unwrapped_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"username": "no-wrapper"},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.course_feedback
def test_unauthenticated_create_is_rejected(strapi_url):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}",
        json={"data": {"username": "anon", "OverallRating": 1}},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert_rejected(r)


@pytest.mark.course_feedback
def test_update_course_feedback(strapi_url, strapi_headers, feedback):
    r = update(strapi_url, strapi_headers, ENDPOINT, feedback, {"OverallRating": 3})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["OverallRating"] == 3


@pytest.mark.course_feedback
def test_unauthorized_update_of_another_users_feedback(strapi_url, feedback):
    """IDOR check: unauthenticated update must be rejected."""
    r = requests.put(
        f"{strapi_url}{ENDPOINT}/{feedback}",
        json={"data": {"OverallRating": 1}},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert_rejected(r)


@pytest.mark.course_feedback
def test_delete_course_feedback(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"username": f"todelete_{int(time.time())}", "OverallRating": 1},
        draft=False,
    )
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text


@pytest.mark.course_feedback
def test_unauthenticated_delete_is_rejected(strapi_url, feedback):
    r = requests.delete(
        f"{strapi_url}{ENDPOINT}/{feedback}",
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert r.status_code >= 400, r.text

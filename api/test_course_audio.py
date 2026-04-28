"""Default-CRUD tests for /api/course-audios (collectionType, no draft/publish)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/course-audios"


@pytest.fixture
def course_audio(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"audio_url": f"https://example.com/audio-{int(time.time())}.mp3",
         "language": "en", "is_active": True},
        draft=False,
    )
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.course_audio
def test_list_course_audios(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.course_audio
def test_findone_course_audio(strapi_url, strapi_headers, course_audio):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{course_audio}")
    assert r.status_code == 200, r.text


@pytest.mark.course_audio
def test_findone_unknown_course_audio_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.course_audio
def test_create_course_audio(course_audio):
    assert course_audio


@pytest.mark.course_audio
def test_create_course_audio_rejects_unwrapped_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"audio_url": "no-wrapper"},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.course_audio
def test_update_course_audio(strapi_url, strapi_headers, course_audio):
    r = update(strapi_url, strapi_headers, ENDPOINT, course_audio, {"is_active": False})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["is_active"] is False


@pytest.mark.course_audio
def test_delete_course_audio(strapi_url, strapi_headers, admin_required):
    r = create(
        strapi_url, strapi_headers, ENDPOINT,
        {"audio_url": f"https://example.com/del-{int(time.time())}.mp3"},
        draft=False,
    )
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text

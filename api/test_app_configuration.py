"""Tests for /api/app-configuration (singleType)."""
import pytest
import requests

from _crud_helpers import assert_rejected

ENDPOINT = "/api/app-configuration"


PUBLISHED = "2026-01-01T00:00:00.000Z"
# `publicationState=preview` lets PUT/DELETE see drafts on singleTypes, avoiding
# the "singleType.alreadyExists" error when an orphan draft exists.
PREVIEW = "?publicationState=preview"


def _ensure_published(strapi_url, strapi_headers):
    return requests.put(
        f"{strapi_url}{ENDPOINT}{PREVIEW}",
        headers=strapi_headers,
        json={"data": {"completed_hours_per_day_limit": 24, "publishedAt": PUBLISHED}},
        timeout=15,
    )


@pytest.mark.app_configuration
def test_get_app_configuration(strapi_url, strapi_headers, admin_required):
    """Single-type GET returns the singleton. We publish first to keep the test
    deterministic across reruns."""
    _ensure_published(strapi_url, strapi_headers)
    r = requests.get(f"{strapi_url}{ENDPOINT}", headers=strapi_headers, timeout=15)
    assert r.status_code == 200, r.text
    assert "data" in r.json()


@pytest.mark.app_configuration
def test_update_app_configuration(strapi_url, strapi_headers, admin_required):
    _ensure_published(strapi_url, strapi_headers)
    r = requests.put(
        f"{strapi_url}{ENDPOINT}{PREVIEW}",
        headers=strapi_headers,
        json={"data": {"completed_hours_per_day_limit": 8, "publishedAt": PUBLISHED}},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["completed_hours_per_day_limit"] == 8


@pytest.mark.app_configuration
def test_update_app_configuration_rejects_invalid_payload(
    strapi_url, strapi_headers, admin_required
):
    """Sending a non-int into an integer field must be rejected by validation."""
    _ensure_published(strapi_url, strapi_headers)
    r = requests.put(
        f"{strapi_url}{ENDPOINT}{PREVIEW}",
        headers=strapi_headers,
        json={"data": {"completed_hours_per_day_limit": "not-a-number"}},
        timeout=15,
    )
    assert_rejected(r)


@pytest.mark.app_configuration
def test_delete_app_configuration(strapi_url, strapi_headers, admin_required):
    """Delete then restore so the suite stays idempotent."""
    _ensure_published(strapi_url, strapi_headers)
    d = requests.delete(
        f"{strapi_url}{ENDPOINT}{PREVIEW}", headers=strapi_headers, timeout=15
    )
    assert d.status_code in (200, 204, 404), d.text
    restore = _ensure_published(strapi_url, strapi_headers)
    assert restore.status_code == 200, restore.text

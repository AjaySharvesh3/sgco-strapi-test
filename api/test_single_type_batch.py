"""Parametrized tests for single-type Strapi APIs.

Single-type endpoints expose: GET, PUT, DELETE on /api/<name> (no list,
no findOne by id). Strapi's draftAndPublish + REST quirk: when an orphan
draft exists, GET (published-only) 404s and PUT throws
`singleType.alreadyExists`. We work around that by using
`?publicationState=preview` for write operations.

Sensitive single-types (payment-configuration, square-api) also get an
unauthenticated-rejection check.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest
import requests

from _crud_helpers import assert_rejected

PUBLISHED = "2026-01-01T00:00:00.000Z"
PREVIEW = "?publicationState=preview"


@dataclass
class SingleSpec:
    api: str
    endpoint: str
    update_payload: dict
    invalid_payload: dict
    sensitive: bool = False  # adds unauth-rejection check


SPECS: list[SingleSpec] = [
    SingleSpec(
        api="gemini-chat-prompt",
        endpoint="/api/gemini-chat-prompt",
        update_payload={"prompt": "<p>Pytest prompt</p>"},
        invalid_payload={"prompt": {"unexpected": "object"}},  # richtext expects string
    ),
    SingleSpec(
        api="square-api",
        endpoint="/api/square-api",
        update_payload={"API_ENVIRONMENT": "sandbox-pytest"},
        invalid_payload={"API_ENVIRONMENT": {"bad": "shape"}},
        sensitive=True,
    ),
    SingleSpec(
        api="payment-configuration",
        endpoint="/api/payment-configuration",
        update_payload={"service_provider": "AUTHORIZE_NET"},
        invalid_payload={"service_provider": {"bad": "shape"}},
        sensitive=True,
    ),
]
IDS = [s.api for s in SPECS]


def _ensure_published(strapi_url, strapi_headers, spec: SingleSpec):
    return requests.put(
        f"{strapi_url}{spec.endpoint}{PREVIEW}",
        headers=strapi_headers,
        json={"data": {**spec.update_payload, "publishedAt": PUBLISHED}},
        timeout=15,
    )


@pytest.fixture(params=SPECS, ids=IDS)
def spec(request) -> SingleSpec:
    return request.param


@pytest.mark.single_type
def test_get_single_type(strapi_url, strapi_headers, admin_required, spec):
    _ensure_published(strapi_url, strapi_headers, spec)
    r = requests.get(f"{strapi_url}{spec.endpoint}", headers=strapi_headers, timeout=15)
    assert r.status_code == 200, f"[{spec.api}] {r.status_code} {r.text}"
    assert "data" in r.json()


@pytest.mark.single_type
def test_update_single_type(strapi_url, strapi_headers, admin_required, spec):
    _ensure_published(strapi_url, strapi_headers, spec)
    r = requests.put(
        f"{strapi_url}{spec.endpoint}{PREVIEW}",
        headers=strapi_headers,
        json={"data": {**spec.update_payload, "publishedAt": PUBLISHED}},
        timeout=15,
    )
    assert r.status_code == 200, f"[{spec.api}] {r.status_code} {r.text}"


@pytest.mark.single_type
def test_update_single_type_rejects_invalid(strapi_url, strapi_headers, admin_required, spec):
    _ensure_published(strapi_url, strapi_headers, spec)
    r = requests.put(
        f"{strapi_url}{spec.endpoint}{PREVIEW}",
        headers=strapi_headers,
        json={"data": spec.invalid_payload},
        timeout=15,
    )
    assert_rejected(r)


@pytest.mark.single_type
def test_delete_single_type(strapi_url, strapi_headers, admin_required, spec):
    _ensure_published(strapi_url, strapi_headers, spec)
    d = requests.delete(
        f"{strapi_url}{spec.endpoint}{PREVIEW}", headers=strapi_headers, timeout=15
    )
    assert d.status_code in (200, 204, 404), f"[{spec.api}] {d.status_code} {d.text}"
    # Restore so suite stays idempotent
    restore = _ensure_published(strapi_url, strapi_headers, spec)
    assert restore.status_code == 200


@pytest.mark.single_type
def test_unauthenticated_access_to_sensitive_single_type_does_not_leak(strapi_url, spec, request):
    if not spec.sensitive:
        pytest.skip(f"{spec.api} is not flagged sensitive")
    # Known finding: payment-configuration is publicly readable in this codebase.
    # The leaked field today is just `service_provider` (provider name, no
    # credentials), but the route should still require auth. Tracked as xfail.
    if spec.api == "payment-configuration":
        request.applymarker(pytest.mark.xfail(
            reason="SECURITY FINDING: /api/payment-configuration is readable by "
            "Public role (returns 200). Tighten Public-role permissions on this "
            "single-type even though no credentials are stored on it today."
        ))
    r = requests.get(
        f"{strapi_url}{spec.endpoint}",
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert r.status_code >= 400, r.text
    body = r.json() if r.content else {}
    data = body.get("data")
    if isinstance(data, dict):
        attrs = data.get("attributes", {})
        for k in ("SQUARE_ACCESS_TOKEN", "API_TRANSACTION_KEY"):
            assert k not in attrs, f"[{spec.api}] leaked {k}: {body}"


@pytest.mark.single_type
def test_unauthenticated_update_of_sensitive_single_type_is_rejected(strapi_url, spec):
    if not spec.sensitive:
        pytest.skip(f"{spec.api} is not flagged sensitive")
    r = requests.put(
        f"{strapi_url}{spec.endpoint}",
        headers={"Content-Type": "application/json"},
        json={"data": {"hacker": True}},
        timeout=10,
    )
    assert r.status_code >= 400, r.text


@pytest.mark.single_type
def test_unauthenticated_delete_of_sensitive_single_type_is_rejected(strapi_url, spec):
    if not spec.sensitive:
        pytest.skip(f"{spec.api} is not flagged sensitive")
    r = requests.delete(
        f"{strapi_url}{spec.endpoint}",
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert r.status_code >= 400, r.text

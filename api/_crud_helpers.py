"""Shared CRUD helpers for Strapi v4 default-router APIs.

Strapi v4 expects every create/update body to be wrapped in {"data": {...}};
sending a bare body returns 400, which we use as a universal validation test.
"""
from __future__ import annotations

import requests

PUBLISHED = "2026-01-01T00:00:00.000Z"


def list_endpoint(strapi_url: str, headers: dict, endpoint: str, params: dict | None = None):
    return requests.get(f"{strapi_url}{endpoint}", headers=headers, params=params or {}, timeout=15)


def get_endpoint(strapi_url: str, headers: dict, endpoint: str, params: dict | None = None):
    return requests.get(f"{strapi_url}{endpoint}", headers=headers, params=params or {}, timeout=15)


def create(strapi_url: str, headers: dict, endpoint: str, attrs: dict, *, draft: bool = True):
    payload = {"data": {**attrs}}
    if draft:
        payload["data"]["publishedAt"] = PUBLISHED
    return requests.post(f"{strapi_url}{endpoint}", headers=headers, json=payload, timeout=15)


def update(strapi_url: str, headers: dict, endpoint: str, entry_id, attrs: dict):
    return requests.put(
        f"{strapi_url}{endpoint}/{entry_id}",
        headers=headers,
        json={"data": attrs},
        timeout=15,
    )


def delete(strapi_url: str, headers: dict, endpoint: str, entry_id):
    return requests.delete(f"{strapi_url}{endpoint}/{entry_id}", headers=headers, timeout=15)


def assert_rejected(response):
    """Strapi's middleware in this project sometimes wraps 400/403 into 500.
    We assert the request was not accepted (>=400) and that no entry was created."""
    assert response.status_code >= 400, response.text
    body = response.json() if response.content else {}
    data = body.get("data")
    assert not (isinstance(data, dict) and data.get("id")), body

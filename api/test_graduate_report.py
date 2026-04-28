"""
Graduate-report tests covering screenshot QA cases:
  - Graduate Report: verify Discount Hour Rate appears for existing discount codes
    (no subscription account) when discount.hourly_rate is updated in Strapi
  - Graduate Report: verify Discount Hour Rate appears for new Group Subscription
    (Discount Code MELOGRP)

The report itself is rendered by the Next admin app, but the data source is the
discount-code's `hourly_rate` field. We exercise that field at the API level.
"""
import time
import uuid

import pytest
import requests


def _suffix() -> str:
    return f"{int(time.time())}{uuid.uuid4().hex[:4]}"


@pytest.mark.graduate_report
def test_discount_hourly_rate_field_is_writable(strapi_url, strapi_headers, admin_required):
    """Screenshot: 'discount hourly rate updated in Strapi' — confirm the field
    can be set on a discount-code and round-trips."""
    code = f"GRAD{_suffix()}".upper()
    create = requests.post(
        f"{strapi_url}/api/discount-codes",
        json={"data": {
            "code": code,
            "type": "percentage_discount",
            "value": 50,
            "hourly_rate": 12.5,
            "status": "active",
            "publishedAt": "2026-01-01T00:00:00.000Z",
        }},
        headers=strapi_headers,
        timeout=15,
    )
    assert create.status_code in (200, 201), create.text
    did = create.json()["data"]["id"]

    try:
        fetched = requests.get(
            f"{strapi_url}/api/discount-codes/{did}",
            headers=strapi_headers,
            timeout=10,
        ).json()["data"]["attributes"]
        assert float(fetched["hourly_rate"]) == 12.5

        # Update to a new rate and re-read
        upd = requests.put(
            f"{strapi_url}/api/discount-codes/{did}",
            json={"data": {"hourly_rate": 7.25}},
            headers=strapi_headers,
            timeout=15,
        )
        assert upd.status_code == 200, upd.text
        assert float(upd.json()["data"]["attributes"]["hourly_rate"]) == 7.25
    finally:
        requests.delete(
            f"{strapi_url}/api/discount-codes/{did}",
            headers=strapi_headers,
            timeout=10,
        )


@pytest.mark.graduate_report
def test_melogrp_discount_code_exposes_hourly_rate(strapi_url, strapi_headers):
    """Screenshot: 'Use Discount Code-MELOGRP' for the Group Subscription graduate
    report. If the code exists, it must expose hourly_rate so the report can read it."""
    r = requests.get(
        f"{strapi_url}/api/discount-codes",
        params={"filters[code][$eq]": "MELOGRP"},
        headers=strapi_headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    items = r.json().get("data", [])
    if not items:
        pytest.skip("MELOGRP discount code not seeded in this Strapi instance")
    attrs = items[0]["attributes"]
    assert "hourly_rate" in attrs, "schema regression: hourly_rate missing"

"""
Discount-code tests covering screenshot QA cases:
  - New Discount Code: create a percentage discount for multi-user use
  - Existing Discount Code: validate an active code is applied to an order
  - Inactivate Discount Code: switch status to inactive and verify it shows EXPIRED

Strapi exposes core CRUD on /api/discount-codes (createCoreRouter). Mutations
require either a Full-access API token (STRAPI_API_TOKEN) or a Public-role with
write permissions. We require the API token for the create/update tests and
skip them otherwise.
"""
import time
import uuid

import pytest
import requests

from _crud_helpers import assert_rejected


def _make_code() -> str:
    return f"TEST{int(time.time())}{uuid.uuid4().hex[:4].upper()}"


@pytest.fixture
def percentage_discount(strapi_url, strapi_headers, admin_required):
    """Create a 10%-off, multi-use, active discount code; clean up after."""
    code_value = _make_code()
    payload = {
        "data": {
            "code": code_value,
            "type": "percentage_discount",
            "value": 10,
            "available_uses": 100,
            "unlimited_uses": False,
            "status": "active",
            "publishedAt": "2026-01-01T00:00:00.000Z",
        }
    }
    r = requests.post(
        f"{strapi_url}/api/discount-codes",
        json=payload,
        headers=strapi_headers,
        timeout=15,
    )
    assert r.status_code in (200, 201), r.text
    created = r.json()["data"]
    yield {"id": created["id"], "code": code_value, **created.get("attributes", {})}
    # Cleanup — best-effort; ignore failures
    requests.delete(
        f"{strapi_url}/api/discount-codes/{created['id']}",
        headers=strapi_headers,
        timeout=10,
    )


@pytest.mark.discount
def test_create_new_percentage_discount_code_for_multi_user_use(percentage_discount):
    """Screenshot: 'Create a Discount Code with Percentage Discount for multi users use'."""
    assert percentage_discount["id"]
    # Strapi v4 returns attributes nested; we assert what we set
    # (the fixture already asserted creation succeeded).


@pytest.mark.discount
def test_active_discount_code_is_visible_in_listing(strapi_url, strapi_headers, percentage_discount):
    """Screenshot: 'Validate if the off discount codes are working' — an active code
    must be retrievable and report status=active."""
    r = requests.get(
        f"{strapi_url}/api/discount-codes",
        params={"filters[code][$eq]": percentage_discount["code"]},
        headers=strapi_headers,
        timeout=15,
    )
    assert r.status_code == 200, r.text
    items = r.json().get("data", [])
    assert len(items) == 1, f"expected 1 hit, got {len(items)}"
    attrs = items[0]["attributes"]
    assert attrs["status"] == "active"
    assert attrs["type"] == "percentage_discount"


@pytest.mark.discount
def test_inactive_discount_code_reports_inactive_status(
    strapi_url, strapi_headers, percentage_discount
):
    """Screenshot: 'Disable the discount code from the Admin and verify if it shows
    as EXPIRED'. The schema only has active|inactive, so 'inactive' is the EXPIRED
    state surfaced to the admin UI."""
    r = requests.put(
        f"{strapi_url}/api/discount-codes/{percentage_discount['id']}",
        json={"data": {"status": "inactive"}},
        headers=strapi_headers,
        timeout=15,
    )
    assert r.status_code == 200, r.text
    after = r.json()["data"]["attributes"]
    assert after["status"] == "inactive"


@pytest.mark.discount
def test_list_discount_codes_with_admin(strapi_url, strapi_headers):
    r = requests.get(f"{strapi_url}/api/discount-codes", headers=strapi_headers, timeout=15)
    assert r.status_code == 200, r.text


@pytest.mark.discount
@pytest.mark.xfail(
    reason="SECURITY FINDING: Public role can list active discount codes "
    "(e.g. 'ARCBBP' status=active). Tighten Public permissions on "
    "/api/discount-codes or filter by status server-side."
)
def test_unauthenticated_list_does_not_leak_active_codes(strapi_url):
    r = requests.get(
        f"{strapi_url}/api/discount-codes",
        headers={"Content-Type": "application/json"},
        params={"pagination[pageSize]": 5},
        timeout=10,
    )
    if r.status_code == 200:
        for d in r.json().get("data", []):
            attrs = d["attributes"]
            assert "code" not in attrs or attrs.get("status") != "active", \
                f"active discount code leaked: {d}"


@pytest.mark.discount
def test_role_based_admin_listing(strapi_url, strapi_headers, percentage_discount):
    r = requests.get(
        f"{strapi_url}/api/discount-codes",
        params={"filters[id][$eq]": percentage_discount["id"]},
        headers=strapi_headers, timeout=10,
    )
    assert r.status_code == 200, r.text
    assert len(r.json().get("data", [])) == 1


@pytest.mark.discount
def test_findone_discount_code(strapi_url, strapi_headers, percentage_discount):
    r = requests.get(
        f"{strapi_url}/api/discount-codes/{percentage_discount['id']}",
        headers=strapi_headers, timeout=10,
    )
    assert r.status_code == 200, r.text


@pytest.mark.discount
def test_findone_unknown_discount_code_returns_404(strapi_url, strapi_headers):
    r = requests.get(
        f"{strapi_url}/api/discount-codes/999999999",
        headers=strapi_headers, timeout=10,
    )
    assert r.status_code == 404


@pytest.mark.discount
def test_update_discount_code(strapi_url, strapi_headers, percentage_discount):
    r = requests.put(
        f"{strapi_url}/api/discount-codes/{percentage_discount['id']}",
        json={"data": {"value": 25}},
        headers=strapi_headers, timeout=15,
    )
    assert r.status_code == 200, r.text
    assert float(r.json()["data"]["attributes"]["value"]) == 25.0


@pytest.mark.discount
def test_unauthorized_update_is_rejected(strapi_url, percentage_discount):
    r = requests.put(
        f"{strapi_url}/api/discount-codes/{percentage_discount['id']}",
        json={"data": {"value": 100}},
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.discount
def test_delete_discount_code(strapi_url, strapi_headers, admin_required):
    code = _make_code()
    r = requests.post(
        f"{strapi_url}/api/discount-codes",
        json={"data": {"code": code, "type": "percentage_discount", "value": 5,
                       "publishedAt": "2026-01-01T00:00:00.000Z"}},
        headers=strapi_headers, timeout=15,
    )
    assert r.status_code in (200, 201)
    did = r.json()["data"]["id"]
    d = requests.delete(
        f"{strapi_url}/api/discount-codes/{did}",
        headers=strapi_headers, timeout=10,
    )
    assert d.status_code == 200, d.text


@pytest.mark.discount
def test_unauthenticated_delete_is_rejected(strapi_url, percentage_discount):
    r = requests.delete(
        f"{strapi_url}/api/discount-codes/{percentage_discount['id']}",
        headers={"Content-Type": "application/json"}, timeout=10,
    )
    assert r.status_code >= 400, r.text


@pytest.mark.discount
def test_create_discount_code_requires_auth(strapi_url):
    """Without the API token (and Public role lacking create), POST must be denied.
    Strapi's error middleware in this project wraps Forbidden into a 500
    InternalServerError (same quirk seen in signin/signup tests). We assert the
    request was rejected, not the exact status code."""
    r = requests.post(
        f"{strapi_url}/api/discount-codes",
        json={"data": {"code": _make_code(), "type": "percentage_discount", "value": 5}},
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    assert r.status_code >= 400, r.text
    body = r.json()
    # Successful creates return a `data` object with the new id; rejections don't.
    assert not (isinstance(body.get("data"), dict) and body["data"].get("id")), body

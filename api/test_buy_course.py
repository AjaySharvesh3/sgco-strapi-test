"""
Buy course tests — POST {NEXT_APP_API_URL}/orders

The Next.js /api/orders route:
  1. Authenticates an app user (internal).
  2. Loads course info for each item via GraphQL to Strapi.
  3. If total > 0, charges the card through Authorize.Net sandbox.
  4. Creates the order, order items, and progress rows in Strapi.
  5. Returns { status: "OK" | <errorCode>, message, errorMessage? }.

Prerequisites (see README.md):
  - Strapi running on STRAPI_API_URL with a real course whose id == TEST_COURSE_ID.
  - Next.js running on NEXT_APP_API_URL's host, pointing at that Strapi, with
    Authorize.Net sandbox credentials configured.
"""
import pytest
import requests


def _build_purchase_order(user_id: int, course: dict, card: dict, total: float) -> dict:
    return {
        "userId": user_id,
        "firstName": "Pytest",
        "lastName": "User",
        "cardNumber": card["cardNumber"],
        "expirationMonth": card["expirationMonth"],
        "expirationYear": card["expirationYear"],
        # Authorize.Net wants MMYY — the Next service builds this client-side,
        # but since we're hitting the API directly we must produce it ourselves.
        "expirationDate": f"{int(card['expirationMonth']):02d}{str(card['expirationYear'])[-2:]}",
        "securityCode": card["securityCode"],
        "zipCode": card["zipCode"],
        "totalAmount": total,
        "totalAfterDiscount": total,
        "items": [
            {
                "id": course["id"],
                "name": "Test Course",
                "typeKey": "course",
            }
        ],
        "discountCode": None,
    }


@pytest.mark.buy_course
def test_buy_course_with_valid_card_succeeds(
    next_api_url, registered_user, course_under_test, card_details
):
    payload = _build_purchase_order(
        user_id=registered_user["id"],
        course=course_under_test,
        card=card_details,
        total=course_under_test["fee"],
    )

    r = requests.post(
        f"{next_api_url}/orders",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("status") == "OK", (
        f"Expected payment OK, got: status={body.get('status')}, "
        f"errorMessage={body.get('errorMessage')}, body={body}"
    )


@pytest.mark.buy_course
def test_buy_course_with_invalid_card_is_rejected(
    next_api_url, registered_user, course_under_test, card_details
):
    # Authorize.Net sandbox rejects this number as "credit card number is invalid"
    bad_card = {**card_details, "cardNumber": "4111111111111112"}
    payload = _build_purchase_order(
        user_id=registered_user["id"],
        course=course_under_test,
        card=bad_card,
        total=course_under_test["fee"],
    )

    r = requests.post(
        f"{next_api_url}/orders",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("status") != "OK", f"Expected payment to be rejected: {body}"
    assert body.get("errorMessage") or body.get("message")


@pytest.mark.buy_course
def test_buy_free_course_skips_payment(
    next_api_url, registered_user, course_under_test, card_details
):
    """totalAfterDiscount == 0 → skip Authorize.Net call, create order directly."""
    payload = _build_purchase_order(
        user_id=registered_user["id"],
        course=course_under_test,
        card=card_details,
        total=0,
    )

    r = requests.post(
        f"{next_api_url}/orders",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("status") == "OK", f"Free-course order should succeed: {body}"

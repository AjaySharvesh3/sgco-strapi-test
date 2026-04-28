"""Default-CRUD tests for /api/chat-widget-controls (collectionType)."""
import time

import pytest
import requests

from _crud_helpers import (
    assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)

ENDPOINT = "/api/chat-widget-controls"


@pytest.fixture
def chat_widget_control(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"chat_widget_type": "Pytest Chat"})
    assert r.status_code in (200, 201), r.text
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, ENDPOINT, eid)


@pytest.mark.chat_widget_control
def test_list_chat_widget_controls(strapi_url, strapi_headers):
    r = list_endpoint(strapi_url, strapi_headers, ENDPOINT)
    assert r.status_code == 200, r.text


@pytest.mark.chat_widget_control
def test_findone_chat_widget_control(strapi_url, strapi_headers, chat_widget_control):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/{chat_widget_control}")
    assert r.status_code == 200, r.text


@pytest.mark.chat_widget_control
def test_findone_unknown_chat_widget_control_returns_404(strapi_url, strapi_headers):
    r = get_endpoint(strapi_url, strapi_headers, f"{ENDPOINT}/999999999")
    assert r.status_code == 404


@pytest.mark.chat_widget_control
def test_create_chat_widget_control(chat_widget_control):
    assert chat_widget_control


@pytest.mark.chat_widget_control
def test_create_chat_widget_control_rejects_unwrapped_payload(
    strapi_url, strapi_headers, admin_required
):
    r = requests.post(
        f"{strapi_url}{ENDPOINT}", json={"chat_widget_type": "no-wrapper"},
        headers=strapi_headers, timeout=10,
    )
    assert_rejected(r)


@pytest.mark.chat_widget_control
def test_update_chat_widget_control(strapi_url, strapi_headers, chat_widget_control):
    r = update(
        strapi_url, strapi_headers, ENDPOINT, chat_widget_control,
        {"chat_widget_type": "Pytest Updated"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["attributes"]["chat_widget_type"] == "Pytest Updated"


@pytest.mark.chat_widget_control
def test_delete_chat_widget_control(strapi_url, strapi_headers, admin_required):
    r = create(strapi_url, strapi_headers, ENDPOINT, {"chat_widget_type": f"ToDelete {int(time.time())}"})
    assert r.status_code in (200, 201)
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, ENDPOINT, eid)
    assert d.status_code == 200, d.text

"""Parametrized default-CRUD coverage for many Strapi v4 collection-type APIs.

Each spec produces 7 tests (list, findOne, findOne 404, create, create-invalid,
update, delete) — wired through pytest.mark.parametrize. Add a spec to extend
coverage; no new file needed.

For APIs with required fields, set `missing_required` to a payload that omits
them; we assert the create is rejected. For APIs with no required fields, we
fall back to sending an unwrapped body (Strapi v4 demands `{ data: { ... } }`)
which is also rejected.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

import pytest
import requests

from _crud_helpers import (
    PUBLISHED, assert_rejected, create, delete, get_endpoint, list_endpoint, update,
)


def _u() -> str:
    return f"{int(time.time())}{uuid.uuid4().hex[:4]}"


@dataclass
class Spec:
    api: str
    endpoint: str
    draft: bool
    create: dict
    update: dict
    missing_required: dict | None = None  # None → use unwrapped-payload test


SPECS: list[Spec] = [
    Spec("default-ad-media", "/api/default-ad-medias", True,
         {"ad_url": "https://example.com/a.jpg", "show_ad": True},
         {"show_ad": False}),
    Spec("exit-popup", "/api/exit-popups", True,
         {"popup_title": "Pytest", "is_active": True, "duration_in_second": 10},
         {"is_active": False}),
    Spec("featured-review", "/api/featured-reviews", True,
         {"review": "great", "rating": 5},
         {"rating": 4}),
    Spec("grade", "/api/grades", False,
         {"grade": 95, "pass_percentage": 80},
         {"grade": 99}),
    Spec("group-subscription-form-data", "/api/group-subscription-form-datas", False,
         {"first_name": "Pytest", "last_name": "User", "email": "pytest@example.com",
          "subscription_individuals_count": 5},
         {"subscription_individuals_count": 10}),
    Spec("healthcare-training-landing-page", "/api/healthcare-training-landing-pages", True,
         {"title": "Pytest Healthcare", "is_active": True},
         {"is_active": False}),
    Spec("help-category", "/api/help-categories", True,
         {"name": f"PytestHelp_{_u()}"},
         {"name": f"PytestHelpUpd_{_u()}"}),
    Spec("help-sub-category", "/api/help-sub-categories", True,
         {"name": f"PytestSub_{_u()}"},
         {"name": f"PytestSubUpd_{_u()}"}),
    Spec("hero-image", "/api/hero-images", True,
         {"name": f"PytestHero_{_u()}"},
         {"name": f"PytestHeroUpd_{_u()}"}),
    Spec("home-page-content", "/api/home-page-contents", True,
         {"title": "Pytest", "is_active": True},
         {"is_active": False}),
    Spec("home-page-marquee", "/api/home-page-marquees", False,
         {"name": f"PytestMar_{_u()}", "status": True, "speed": 30},
         {"speed": 50}),
    Spec("home-page-promotion-banner", "/api/home-page-promotion-banners", False,
         {"name": f"PytestPromo_{_u()}", "status": True},
         {"status": False}),
    Spec("hot-deal", "/api/hot-deals", True,
         {"title": "Pytest Hot", "is_active": True},
         {"is_active": False}),
    Spec("knowledge-collection", "/api/knowledge-collections", True,
         {"name": f"PytestKC_{_u()}", "active": True, "fee": 9.99},
         {"active": False}),
    Spec("legacy-category", "/api/legacy-categories", True,
         {"name": f"PytestLeg_{_u()}"},
         {"short_name": "PytestUpd"}),
    Spec("organization", "/api/organizations", True,
         {},  # schema has no public attributes
         {}),
    Spec("package", "/api/packages", True,
         {"name": f"PytestPkg_{_u()}", "active": True, "fee": 19.99},
         {"active": False}),
    Spec("page", "/api/pages", True,
         {"title": f"Pytest Page {_u()}", "slug": f"pytest-page-{_u()}", "status": True},
         {"status": False}),
    Spec("path-redirect", "/api/path-redirects", True,
         {"path_id": f"pytest-path-{_u()}", "type_key": "course"},
         {"type_key": "package"}),
    Spec("spot", "/api/spots", True,
         {"name": f"PytestSpot_{_u()}", "text_type": "Plain_Text"},
         {"text_type": "Rich_Text"}),
    Spec("state-info", "/api/state-infos", True,
         {"accreditation": "<p>test</p>"},
         {"other_information": "<p>updated</p>"}),
    Spec("sub-category", "/api/sub-categories", True,
         {"name": f"PytestSubCat_{_u()}"},
         {"name": f"PytestSubCatUpd_{_u()}"}),
    Spec("top-nav-sub-menu", "/api/top-nav-sub-menus", True,
         {"name": f"PytestNav_{_u()}", "href": "/pytest"},
         {"href": "/pytest-updated"}),
    Spec("topic", "/api/topics", True,
         {"name": f"PytestTopic_{_u()}"},
         {"name": f"PytestTopicUpd_{_u()}"}),
    Spec("training-landing-page", "/api/training-landing-pages", True,
         {"title": f"Pytest Training {_u()}", "show_public": True},
         {"show_public": False}),
    # Required-field APIs — `missing_required` is a payload that omits the
    # required attribute(s), letting us assert the API enforces them.
    Spec("post", "/api/posts", True,
         {"title": f"Pytest Post {_u()}", "body": "<p>test</p>"},
         {"meta_title": "updated"},
         missing_required={"author": "Pytest"}),  # missing title + body
    Spec("school", "/api/schools", True,
         {"name": f"Pytest School {_u()}"},
         {"order": 99},
         missing_required={"order": 1}),  # missing name
    Spec("state", "/api/states", True,
         {"name": f"PytestState_{_u()}", "abbreviation": _u()[:4].upper()},
         {"cert_message": "updated"},
         missing_required={"cert_message": "no name"}),  # missing name + abbreviation
]

IDS = [s.api for s in SPECS]


@pytest.fixture(params=SPECS, ids=IDS)
def spec(request) -> Spec:
    return request.param


@pytest.fixture
def created_entry(strapi_url, strapi_headers, admin_required, spec):
    r = create(strapi_url, strapi_headers, spec.endpoint, spec.create, draft=spec.draft)
    assert r.status_code in (200, 201), f"[{spec.api}] create failed: {r.status_code} {r.text}"
    eid = r.json()["data"]["id"]
    yield eid
    delete(strapi_url, strapi_headers, spec.endpoint, eid)


@pytest.mark.batch_crud
def test_list(strapi_url, strapi_headers, spec):
    r = list_endpoint(strapi_url, strapi_headers, spec.endpoint)
    assert r.status_code == 200, f"[{spec.api}] {r.status_code} {r.text}"
    assert "data" in r.json()


@pytest.mark.batch_crud
def test_findone(strapi_url, strapi_headers, spec, created_entry):
    r = get_endpoint(strapi_url, strapi_headers, f"{spec.endpoint}/{created_entry}")
    assert r.status_code == 200, f"[{spec.api}] {r.status_code} {r.text}"
    assert r.json()["data"]["id"] == created_entry


@pytest.mark.batch_crud
def test_findone_404(strapi_url, strapi_headers, spec):
    r = get_endpoint(strapi_url, strapi_headers, f"{spec.endpoint}/999999999")
    assert r.status_code == 404, f"[{spec.api}] expected 404 got {r.status_code} {r.text}"


@pytest.mark.batch_crud
def test_create(spec, created_entry):
    assert created_entry, f"[{spec.api}] no id returned"


@pytest.mark.batch_crud
def test_create_invalid(strapi_url, strapi_headers, admin_required, spec):
    if spec.missing_required is not None:
        # Wrapped payload missing required attributes
        r = requests.post(
            f"{strapi_url}{spec.endpoint}",
            json={"data": spec.missing_required},
            headers=strapi_headers,
            timeout=10,
        )
    else:
        # No required fields — send unwrapped body, which Strapi v4 rejects
        r = requests.post(
            f"{strapi_url}{spec.endpoint}",
            json=spec.create,
            headers=strapi_headers,
            timeout=10,
        )
    assert_rejected(r)


@pytest.mark.batch_crud
def test_update(strapi_url, strapi_headers, spec, created_entry):
    r = update(strapi_url, strapi_headers, spec.endpoint, created_entry, spec.update)
    assert r.status_code == 200, f"[{spec.api}] {r.status_code} {r.text}"


@pytest.mark.batch_crud
def test_delete(strapi_url, strapi_headers, admin_required, spec):
    r = create(strapi_url, strapi_headers, spec.endpoint, spec.create, draft=spec.draft)
    assert r.status_code in (200, 201), f"[{spec.api}] create-for-delete failed: {r.text}"
    eid = r.json()["data"]["id"]
    d = delete(strapi_url, strapi_headers, spec.endpoint, eid)
    assert d.status_code == 200, f"[{spec.api}] delete returned {d.status_code} {d.text}"

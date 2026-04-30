import json
import os
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


# ---- Run-record hook (writes results/run.json per pytest invocation) -------
#
# CI consumes this file along with the pytest-html report to update the
# gh-pages dashboard. Locally, it just sits in `results/` (gitignored).

_SESSION_START_TS: float | None = None


def pytest_sessionstart(session):
    global _SESSION_START_TS
    _SESSION_START_TS = time.time()


def _git_field(args: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=Path(__file__).parent.parent,
            stderr=subprocess.DEVNULL, timeout=2,
        ).decode().strip()
    except Exception:
        return ""


def pytest_sessionfinish(session, exitstatus):
    duration = round(time.time() - (_SESSION_START_TS or time.time()), 2)
    rep = session.config.pluginmanager.getplugin("terminalreporter")
    counts = {}
    if rep is not None:
        for k in ("passed", "failed", "skipped", "error", "xfailed", "xpassed"):
            counts[k] = len(rep.stats.get(k, []))

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "exitstatus": int(exitstatus),
        "duration_seconds": duration,
        "counts": counts,
        "git_sha": os.getenv("GITHUB_SHA") or _git_field(["rev-parse", "HEAD"]),
        "git_branch": os.getenv("GITHUB_REF_NAME") or _git_field(["rev-parse", "--abbrev-ref", "HEAD"]),
        "ci_run_id": os.getenv("GITHUB_RUN_ID", ""),
        "ci_run_url": (
            f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
            if os.getenv("GITHUB_REPOSITORY") and os.getenv("GITHUB_RUN_ID") else ""
        ),
    }

    out_dir = Path(__file__).parent.parent / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "run.json").write_text(json.dumps(record, indent=2))


def _env(key: str, default: str = "") -> str:
    val = os.getenv(key, default)
    if val == "":
        raise RuntimeError(f"Missing env var: {key}. Copy .env.example to .env and fill it in.")
    return val


def _service_up(url: str, timeout: float = 2.0) -> bool:
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.RequestException:
        return False


@pytest.fixture(scope="session")
def strapi_url() -> str:
    url = os.getenv("STRAPI_API_URL", "http://localhost:1337").rstrip("/")
    if not _service_up(f"{url}/_health"):
        pytest.skip(f"Strapi not reachable at {url}", allow_module_level=False)
    return url


@pytest.fixture(scope="session")
def next_api_url() -> str:
    url = os.getenv("NEXT_APP_API_URL", "http://localhost:3000/api").rstrip("/")
    base = url.rsplit("/api", 1)[0]
    if not _service_up(base):
        pytest.skip(f"Next.js not reachable at {base}", allow_module_level=False)
    return url


@pytest.fixture(scope="session")
def strapi_headers() -> dict:
    """Headers for Strapi calls. Includes Full-Access API token when STRAPI_API_TOKEN is set."""
    headers = {"Content-Type": "application/json"}
    token = os.getenv("STRAPI_API_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


@pytest.fixture(scope="session")
def card_details() -> dict:
    return {
        "cardNumber": _env("TEST_CARD_NUMBER", "4111111111111111"),
        "expirationMonth": _env("TEST_CARD_EXP_MONTH", "12"),
        "expirationYear": _env("TEST_CARD_EXP_YEAR", "2034"),
        "securityCode": _env("TEST_CARD_CVV", "123"),
        "zipCode": _env("TEST_ZIP_CODE", "10001"),
    }


@pytest.fixture(scope="session")
def course_under_test() -> dict:
    return {
        "id": int(_env("TEST_COURSE_ID", "1")),
        "fee": float(_env("TEST_COURSE_FEE", "10")),
    }


def make_unique_user() -> dict:
    """Return a fresh user payload — unique username/email per test run."""
    suffix = f"{int(time.time())}{uuid.uuid4().hex[:6]}"
    return {
        "username": f"pytest_{suffix}",
        "email": f"pytest_{suffix}@example.com",
        "password": "TestPassword123!",
        "first_name": "Pytest",
        "last_name": "User",
    }


@pytest.fixture
def new_user_payload() -> dict:
    return make_unique_user()


@pytest.fixture(scope="session")
def registered_user(strapi_url: str, strapi_headers: dict) -> dict:
    """Create one user shared across the session (used by signin + buy-course)."""
    payload = make_unique_user()
    r = requests.post(
        f"{strapi_url}/api/custom-auth/register",
        json=payload,
        headers=strapi_headers,
        timeout=15,
    )
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("ok") is not False, f"register returned error: {data}"
    assert "jwt" in data and "user" in data, f"unexpected register body: {data}"
    return {
        **payload,
        "id": data["user"]["id"],
        "jwt": data["jwt"],
    }


@pytest.fixture
def fresh_user(strapi_url: str, strapi_headers: dict) -> dict:
    """A brand-new user, function-scoped — useful for forgot-password / forgot-username."""
    payload = make_unique_user()
    r = requests.post(
        f"{strapi_url}/api/custom-auth/register",
        json=payload,
        headers=strapi_headers,
        timeout=15,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    return {**payload, "id": data["user"]["id"], "jwt": data.get("jwt", "")}


def _api_token_required():
    if not os.getenv("STRAPI_API_TOKEN", "").strip():
        pytest.skip("STRAPI_API_TOKEN not set; skipping admin-write test")


@pytest.fixture(scope="session")
def admin_required():
    """Yield-fixture form for tests that mutate Strapi admin-side data."""
    _api_token_required()
    return True

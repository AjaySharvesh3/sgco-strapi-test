# Backend API tests (pytest + requests)

Tests the three core flows against the running backend:

| Flow        | Endpoint                                              | File                  |
| ----------- | ----------------------------------------------------- | --------------------- |
| Signup      | `POST {STRAPI}/api/custom-auth/register`              | `test_signup.py`      |
| Signin      | `POST {STRAPI}/api/custom-auth/login`                 | `test_signin.py`      |
| Buy course  | `POST {NEXT}/api/orders` (Authorize.Net sandbox)      | `test_buy_course.py`  |

> Note — you asked about Selenium, but Selenium drives a browser UI, so it's
> the wrong tool for pure backend API testing. These tests use
> `pytest + requests`, which is the standard Python stack for HTTP APIs.
> If you later want a browser flow (filling forms, clicking buttons), we can
> add a Selenium or Playwright suite on top.

---

## 1. Prerequisites

### 1.1 Services must be running

From the project root, in two separate terminals:

```bash
# Terminal A — Strapi backend (signup + signin talk to this directly)
cd safegardclasses-strapi
yarn develop       # serves on http://localhost:1337

# Terminal B — Next.js (orders API lives here)
cd NEXT
yarn dev           # serves on http://localhost:3000
```

### 1.2 A real course must exist

The buy-course flow loads the course from Strapi by id. Either:
- Create one in the Strapi admin (`http://localhost:1337/admin` → Content
  Manager → Course), then note its id, or
- Hit `GET http://localhost:1337/api/courses` and pick any id from the
  response.

### 1.3 Authorize.Net sandbox

The Next.js `/api/orders` endpoint uses Authorize.Net. Make sure Next has
sandbox credentials (`API_ENVIRONMENT != 'production'`) so the test card
`4111111111111111` is accepted.

---

## 2. Install

```bash
cd tests/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configure

```bash
cp .env.example .env
# edit .env and set:
#   - STRAPI_API_TOKEN  (Full-Access token — see below)
#   - TEST_COURSE_ID / TEST_COURSE_FEE (a real course in Strapi)
```

### 3a. Create a Strapi Full-Access API token (recommended)

This lets the tests hit any endpoint without needing to grant the **Public**
role any extra permissions.

1. http://localhost:1337/admin → **Settings → API Tokens → Create new API Token**
2. **Name:** `pytest-automation`
3. **Token duration:** `Unlimited`
4. **Token type:** `Full access`
5. **Save** → copy the token (Strapi shows it **only once**).
6. Paste into `.env` as `STRAPI_API_TOKEN=<your token>`.

If you skip this, the alternative is enabling the `custom-auth.register` /
`custom-auth.loginByUsername` / etc. actions for the **Public** role under
*Settings → Users & Permissions Plugin → Roles → Public → Save*.

## 4. Run

All tests:

```bash
pytest
```

One flow at a time:

```bash
pytest -m signup
pytest -m signin
pytest -m buy_course
```

A single test:

```bash
pytest test_signup.py::test_signup_returns_jwt_and_user
```

More verbose output (useful when a buy-course test fails):

```bash
pytest -s -vv
```

---

## 5. What "passing" means

| Test                                                    | Validates                                                                             |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `test_signup_returns_jwt_and_user`                      | Strapi creates a user and returns a JWT + user body.                                  |
| `test_signup_duplicate_username_is_rejected`            | Re-registering the same username returns `{ ok: false, error: "already taken..." }`. |
| `test_signup_missing_password_is_rejected`              | Strapi's validator returns 400 when `password` is missing.                            |
| `test_signup_invalid_email_is_rejected`                 | Malformed email returns 400.                                                          |
| `test_signin_with_valid_credentials`                    | `/custom-auth/login` returns a JWT for a user who just signed up.                     |
| `test_signin_with_wrong_password_is_rejected`           | Bad password → 400 "Invalid identifier or password".                                  |
| `test_signin_with_unknown_user_is_rejected`             | Unknown identifier → 400.                                                             |
| `test_signin_with_missing_fields_is_rejected`           | Missing `password` field → 400.                                                       |
| `test_signin_jwt_is_accepted_by_strapi`                 | Returned JWT authenticates successfully against `/api/users/me`.                      |
| `test_buy_course_with_valid_card_succeeds`              | Order + Authorize.Net charge completes, response `status == "OK"`.                   |
| `test_buy_course_with_invalid_card_is_rejected`         | Invalid card → `status != "OK"` with an error message.                               |
| `test_buy_free_course_skips_payment`                    | `totalAfterDiscount == 0` path creates the order without hitting Authorize.Net.      |

A successful `pytest` run prints something like:

```
======================== 12 passed in 4.28s ========================
```

---

## 6. Manual validation checklist

After a green run, spot-check that the tests actually did what they claimed:

1. **Strapi admin → Content Manager → Users** — you should see fresh
   `pytest_<timestamp>_<hex>@example.com` users.
2. **Strapi admin → Content Manager → Order** — a new order for the user
   created in step 1 with the `TEST_COURSE_ID` line item.
3. **Strapi admin → Content Manager → Progress** — a new progress row
   linking that user to the course.
4. **Authorize.Net sandbox merchant interface** → Transaction Search —
   a matching successful transaction for `TEST_COURSE_FEE`.

---

## 7. Troubleshooting

| Symptom                                                              | Likely cause                                                                        |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `register failed: 403` or HTTP 500 on `/custom-auth/*`                | Missing / invalid `STRAPI_API_TOKEN`. Create a Full-Access token (see §3a) and paste into `.env`. |
| Signup returns `{ ok: false, error: "already taken..." }` on the first run | You're reusing an env where the user already exists. Tests always generate unique names — check env isolation. |
| `test_buy_course_with_valid_card_succeeds` times out                 | Next.js isn't running, or it can't reach Strapi — verify URLs in `.env`.            |
| `status != "OK"` in buy tests with the canonical test card           | Next.js is pointed at Authorize.Net production, not sandbox. Check `API_ENVIRONMENT`.|
| `ValidationError: password must be...`                               | Strapi has a custom password policy — edit `conftest.make_unique_user.password`.    |

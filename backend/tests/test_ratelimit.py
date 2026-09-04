"""A2 over HTTP: per-IP rate limiting on unauthenticated writes.

`POST /api/reflections` was unauthenticated, unthrottled and uncapped. These tests drive it
through the real ingress.

Each test picks its own X-Forwarded-For value so it gets its own window and cannot exhaust the
bucket the rest of the suite is using — the limiter keys on the forwarded chain because behind
the ingress every pod sees the same peer address.
"""
import os
import uuid

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api/v2"
PARTNERS = f"{BASE_URL}/api/partners"

LIMIT = int(os.environ.get("RK_RL_REFLECTIONS", "30"))


def _own_ip() -> dict:
    octet = uuid.uuid4().int
    return {"X-Forwarded-For": f"198.51.100.{octet % 200 + 10}, 10.0.0.1"}


@pytest.fixture(scope="module")
def http():
    return requests.Session()


def test_a_single_flag_check_is_unaffected(http):
    r = http.post(f"{API}/reflections", headers=_own_ip())
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "in_progress"


def test_the_window_closes_after_the_threshold(http):
    headers = _own_ip()
    statuses = [http.post(f"{API}/reflections", headers=headers).status_code
                for _ in range(LIMIT + 2)]
    assert statuses[0] == 200, "the first request must be allowed"
    assert 429 in statuses, f"limiter never fired in {LIMIT + 2} requests: {set(statuses)}"
    assert statuses.count(200) <= LIMIT, "more requests were allowed than the window permits"


def test_a_different_origin_is_not_punished_for_it(http):
    """One noisy caller must not lock out everybody else."""
    noisy = _own_ip()
    for _ in range(LIMIT + 1):
        http.post(f"{API}/reflections", headers=noisy)
    r = http.post(f"{API}/reflections", headers=_own_ip())
    assert r.status_code == 200, r.text


def test_an_oversized_body_is_refused(http):
    r = http.post(f"{PARTNERS}/apply", headers=_own_ip(),
                  json={"name": "Big Payload", "email": "big@example.com",
                        "audience_where": "practice", "audience_size": "100",
                        "why_it_fits": "x" * 40000})
    assert r.status_code in (413, 422), r.status_code

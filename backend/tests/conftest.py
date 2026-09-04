"""Test root for the backend (e2e) suite.

Paths and environment are derived from `__file__` here, once, so no test file hardcodes a pod
path — a suite that only runs in one environment is not a gate. `tests/test_ci_portability.py`
enforces that.

Also carries the test isolation for the A2 rate limiter.

The limiter buckets on the X-Forwarded-For chain, and the whole suite runs from one address, so
a hundred-plus registrations and logins in one run would exhaust a window that a real user never
would. Rather than raise the product's limits to fit the tests, every `requests.Session` created
in the suite gets its own forwarded address, so each test module runs in its own bucket.

Per-request headers still win, which is how tests/test_ratelimit.py drives the limiter directly.
"""
import os
import sys
import uuid

import pytest
import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(ROOT, "backend")

sys.path.insert(0, BACKEND)

load_dotenv(os.path.join(BACKEND, ".env"))
load_dotenv(os.path.join(ROOT, "frontend", ".env"))

os.environ.setdefault("RK_ALLOW_PLACEHOLDER_ALPHA", "1")


@pytest.fixture(scope="session", autouse=True)
def _isolate_rate_limit_buckets():
    original = requests.Session.__init__

    def patched(self, *args, **kwargs):
        original(self, *args, **kwargs)
        n = uuid.uuid4().int
        self.headers["X-Forwarded-For"] = f"198.18.{n % 254 + 1}.{n // 254 % 254 + 1}"

    requests.Session.__init__ = patched
    yield
    requests.Session.__init__ = original

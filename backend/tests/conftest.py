"""Test isolation for the A2 rate limiter.

The limiter buckets on the X-Forwarded-For chain, and the whole suite runs from one address, so
a hundred-plus registrations and logins in one run would exhaust a window that a real user never
would. Rather than raise the product's limits to fit the tests, every `requests.Session` created
in the suite gets its own forwarded address, so each test module runs in its own bucket.

Per-request headers still win, which is how tests/test_ratelimit.py drives the limiter directly.
"""
import uuid

import pytest
import requests


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

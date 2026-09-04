"""Test root for the offline suite.

Everything here derives from `__file__`. Nothing may hardcode a pod path: a suite that only runs
in one environment stops being a gate the moment it leaves it, which is the whole point of the CI
job. `tests/test_ci_portability.py` enforces that.
"""
import os
import sys

from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")

sys.path.insert(0, BACKEND)

load_dotenv(os.path.join(BACKEND, ".env"))
load_dotenv(os.path.join(ROOT, "frontend", ".env"))

# services/mrd.py refuses to load while the reliability constants are literature placeholders.
os.environ.setdefault("RK_ALLOW_PLACEHOLDER_ALPHA", "1")

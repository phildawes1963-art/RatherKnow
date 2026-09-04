"""Work order Batch A guards — offline. The HTTP side of A2 is in backend/tests/test_ratelimit.py.

Each test here fails on the code as it stood before its item and passes after.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
os.environ.setdefault("RK_ALLOW_PLACEHOLDER_ALPHA", "1")


# ---------------------------------------------------------------- A2 payload cap

class _FakeRequest:
    def __init__(self, headers):
        self.headers = headers
        self.client = None


def test_oversized_unauthenticated_body_is_refused():
    from fastapi import HTTPException
    from services.ratelimit import MAX_BODY_BYTES, assert_body_within_cap

    assert_body_within_cap(_FakeRequest({"content-length": str(MAX_BODY_BYTES)}))
    with pytest.raises(HTTPException) as exc:
        assert_body_within_cap(_FakeRequest({"content-length": str(MAX_BODY_BYTES + 1)}))
    assert exc.value.status_code == 413


def test_unauthenticated_writes_all_carry_a_limiter():
    """A new unauthenticated write must not be able to ship without one."""
    checks = {
        os.path.join(BACKEND, "routes", "mirror_v2.py"): ('limiter("reflections")', 3),
        os.path.join(BACKEND, "routes", "partners.py"): ('limiter("partners")', 1),
        os.path.join(BACKEND, "auth.py"): ('limiter("auth")', 4),
    }
    for path, (needle, count) in checks.items():
        source = open(path, encoding="utf-8").read()
        assert source.count(needle) >= count, f"{os.path.basename(path)} is missing a {needle} guard"


# ---------------------------------------------------------------- A4 blend rename

def test_blend_matrix_is_the_only_name_in_the_data():
    with open(os.path.join(BACKEND, "constants", "essential_data.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    assert "blend_matrix" in data
    assert "compatibility_matrix" not in data


def test_blend_read_still_produces_the_same_pair_output():
    """The rename is a name change only: same keys, same strings."""
    from services.essential_scoring import QuizAnswer, calculate_archetype_scores, get_blend_result

    answers = [QuizAnswer(question_id=i, answer=(5 if i % 2 else 2)) for i in range(1, 51)]
    scores = calculate_archetype_scores(answers)
    blend = get_blend_result(scores, "self_assessment")
    assert set(blend) == {"type_name", "description", "narrative"}
    assert all(isinstance(v, str) and v for v in blend.values())


# ---------------------------------------------------------------- A4 reverse-key guard

def test_reverse_key_guard_rejects_a_new_orphan():
    from services.essential_scoring import assert_reverse_keys_within_questions

    with pytest.raises(AssertionError) as exc:
        assert_reverse_keys_within_questions({"rock": {"questions": [3, 4], "reverse": [99]}})
    assert "inert" in str(exc.value)


def test_reverse_key_guard_passes_on_shipped_data():
    from services.essential_scoring import ARCHETYPES, assert_reverse_keys_within_questions

    assert_reverse_keys_within_questions(ARCHETYPES)


def test_the_only_acknowledged_orphan_is_diplomat_24():
    """The exception list is a record of one open decision, not a place to put more.

    Diplomat carries reverse=[24] and 24 is in Challenger's item set. Resolving it changes
    scoring or changes data, so it waits on a decision — but it must not grow a neighbour.
    """
    from services.essential_scoring import ARCHETYPES

    orphans = sorted((k, q) for k, a in ARCHETYPES.items() for q in a.get("reverse", [])
                     if q not in a["questions"])
    assert orphans == [("diplomat", 24)], f"Orphaned reverse keys changed: {orphans}"

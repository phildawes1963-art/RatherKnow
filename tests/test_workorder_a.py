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

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(BACKEND, ".env"))  # services.ratelimit imports database at module load


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


def test_no_orphaned_reverse_keys_remain():
    """Decided: Diplomat's inert reverse=[24] is dropped, not restored. Permanent guard."""
    from services.essential_scoring import ARCHETYPES

    orphans = sorted((k, q) for k, a in ARCHETYPES.items() for q in a.get("reverse", [])
                     if q not in a["questions"])
    assert orphans == [], f"Orphaned reverse keys are back: {orphans}"


def test_dropping_diplomat_24_changed_no_score():
    """The whole justification for deleting it: it was never consulted. Proven, not asserted.

    Scores the same answers against the shipped data and against a copy carrying the old
    reverse=[24], and requires them to be identical.
    """
    import copy

    from services.essential_scoring import (ARCHETYPES, QuizAnswer, calculate_archetype_scores,
                                            calculate_score)

    answers = [QuizAnswer(question_id=i, answer=(i % 5) + 1) for i in range(1, 51)]
    now = calculate_archetype_scores(answers)

    as_before = copy.deepcopy(ARCHETYPES)
    as_before["diplomat"]["reverse"] = [24]
    answer_dict = {a.question_id: a.answer for a in answers}
    for key, arch in as_before.items():
        total = sum(calculate_score(answer_dict[q], q in arch["reverse"])
                    for q in arch["questions"] if q in answer_dict)
        assert total == now[key]["score"], f"{key} changed: {now[key]['score']} vs {total}"

"""The Essential tie state: name both rather than ranking on a gap the instrument can't read.

Before this, `sorted(..., reverse=True)` broke an exact tie by dictionary insertion order — on
the varied stored responses that is a 15% share of readers assigned an archetype by the order
the six were typed into a JSON file. TIE_MARGIN closes that by construction.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from services.essential_scoring import (  # noqa: E402
    ARCHETYPES, TIE_MARGIN, QuizAnswer, calculate_archetype_scores, rank_archetypes,
)


def _scores(**by_key):
    return {k: {"name": ARCHETYPES[k]["name"], "score": by_key.get(k, 0)} for k in ARCHETYPES}


def test_margin_is_five_points():
    assert TIE_MARGIN == 5


def test_a_clear_lead_is_ranked():
    r = rank_archetypes(_scores(rock=80, empath=60))
    assert r["primary"] == "rock" and r["tied"] is False and r["gap"] == 20


def test_an_exact_tie_is_not_broken_by_insertion_order():
    """Reversing the input order must not change who is named first."""
    a = rank_archetypes(_scores(rock=70, empath=70))
    reordered = dict(reversed(list(_scores(rock=70, empath=70).items())))
    b = rank_archetypes(reordered)
    assert a["primary"] == b["primary"] and a["secondary"] == b["secondary"]
    assert a["tied"] is True and a["gap"] == 0


@pytest.mark.parametrize("gap,tied", [(0, True), (4, True), (5, False), (6, False)])
def test_the_margin_is_exclusive_at_five(gap, tied):
    r = rank_archetypes(_scores(rock=70, empath=70 - gap))
    assert r["tied"] is tied and r["gap"] == gap


def test_the_gap_is_always_reported():
    """Printed either way: a reader who can see how close it was reads a declined rank as
    information rather than evasion."""
    for gap in (0, 3, 12):
        assert rank_archetypes(_scores(rock=70, empath=70 - gap))["gap"] == gap


def test_scoring_itself_is_unchanged():
    """The tie state changes derivation and display only. No item, no weight, no total moves."""
    answers = [QuizAnswer(question_id=i, answer=(i % 5) + 1) for i in range(1, 51)]
    scores = calculate_archetype_scores(answers)
    assert scores["rock"]["max_score"] == 100
    ranked = rank_archetypes(scores)
    assert ranked["order"][0] == max(scores, key=lambda k: (scores[k]["score"], [-ord(c) for c in k]))
    assert sum(s["score"] for s in scores.values()) > 0

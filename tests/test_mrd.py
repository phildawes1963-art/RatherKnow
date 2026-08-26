"""MRD engine (rk-1.1.0 TRD T3.1, T3.2).

The reference profile is the paired standalone P150 sheet already used by test_composites.py.
Asserting the gates against it is what tells us, before any of this governs a report, how much
of the current output the thresholds would take away.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
os.environ.setdefault("RK_ALLOW_PLACEHOLDER_ALPHA", "1")

from services.mrd import (  # noqa: E402
    build_mrd, clusters, config, distinctiveness, flat_profile, mrd, mrd_for, pairwise, sem,
)

REFERENCE_PRIMARIES = {
    "A": 10, "C": 10, "E": 10, "F": 10, "G": 4, "H": 10, "I": 7, "L": 7,
    "M": 9, "N": 6, "O": 2, "Q1": 10, "Q2": 9, "Q3": 6, "Q4": 3,
}


def test_sem_and_mrd_arithmetic():
    assert round(sem(2.0, 0.75), 4) == 1.0
    # MRD = 1.645 * sqrt(1^2 + 1^2)
    assert round(mrd(2.0, 0.75, 0.75), 3) == 2.326
    assert round(sem(0.55, 0.75), 4) == 0.275


def test_thresholds_match_the_published_profile():
    assert mrd_for("personality_primaries") == 2.326
    assert mrd_for("personality_globals") == 1.802
    assert mrd_for("ei_subdimensions") == 0.64


def test_placeholder_alpha_is_declared():
    """Nothing may quietly ship on literature placeholders."""
    assert config()["placeholder"] is True


def test_pairwise_gate():
    t = mrd_for("ei_subdimensions")
    assert not pairwise(4.50, 4.67, t), "0.17 apart on EI is inside measurement error"
    assert pairwise(2.10, 4.60, t)


def test_flat_profile_gate():
    t = mrd_for("ei_subdimensions")
    # A one-point range across EI sub-dimensions is flatter than 2 x MRD: report the level,
    # rank nothing. This is what suppresses "where you're strongest" and "where the work is".
    assert flat_profile([3.4, 3.6, 3.9, 4.1, 4.4], t)
    assert not flat_profile([2.1, 3.0, 3.5, 4.2, 4.9], t)


def test_distinctiveness_gate():
    t = mrd_for("ei_subdimensions")
    close = {"a": 3.9, "b": 4.0, "c": 4.1, "d": 4.2}
    assert not any(distinctiveness(close, k, t) for k in close), "nothing in a tight set is distinct"
    spread = {"a": 1.4, "b": 3.9, "c": 4.0, "d": 4.1}
    assert distinctiveness(spread, "a", t)


def test_the_whole_reference_profile_collapses_into_one_cluster():
    """The finding that justifies shadow mode.

    On stens with SD 2 and alpha .75, MRD is 2.33 — wider than every adjacent gap in this
    profile (2, 3, 4, 6, 6, 7, 7, 9, then six tens). So the gates fold all fifteen primaries
    into a single undifferentiated cluster whose centroid IS the personal mean, and nothing in
    it is reportable. On a profile with six factors at the ceiling and one at sten 2, that is
    plainly too conservative to govern a report.

    Which is the point: enforcing these thresholds today would empty the Personality Mirror and
    trip the PRD §9 half-refund guarantee on almost every reading. Measure alpha first (D1).
    """
    t = mrd_for("personality_primaries")
    groups = clusters(REFERENCE_PRIMARIES, t)
    assert len(groups) == 1, [g["keys"] for g in groups]
    assert groups[0]["size"] == 15
    assert groups[0]["reportable"] is False
    # And the ends of that "cluster" are eight stens apart.
    assert max(REFERENCE_PRIMARIES.values()) - min(REFERENCE_PRIMARIES.values()) == 8


def test_clusters_split_when_a_gap_clears_the_threshold():
    t = mrd_for("personality_primaries")
    groups = clusters({"low": 2, "also_low": 3, "high": 9, "also_high": 10}, t)
    assert [g["keys"] for g in groups] == [["low", "also_low"], ["high", "also_high"]]
    assert all(g["reportable"] for g in groups)
    assert [g["direction"] for g in groups] == ["low", "high"]


def test_build_mrd_runs_in_shadow_mode_and_suppresses_nothing():
    result = {
        "instrument": "eq",
        "sub_scores": {f"s{i}": {"name": f"Sub {i}", "score": v, "domain": "d"}
                       for i, v in enumerate([3.6, 3.7, 3.9, 4.0, 4.1, 4.2, 4.3])},
        "domain_scores": {f"d{i}": {"name": f"Domain {i}", "score": v}
                          for i, v in enumerate([3.7, 3.9, 4.0, 4.1])},
        "strengths": [{"name": "Sub 6"}], "growth_areas": [{"name": "Sub 0"}],
    }
    block = build_mrd(result)
    assert block["mode"] == "shadow"
    assert block["placeholder_alpha"] is True
    flat = [s for s in block["scale_sets"] if s["scale_set"] == "ei_subdimensions"][0]
    assert flat["flat_profile"] is True
    gates = [s["gate"] for s in block["suppressions"]]
    assert "flat_profile" in gates
    # Shadow mode records the gate; the reader still gets the full result.
    assert result.get("strengths"), "nothing is removed from the result in shadow mode"


def test_build_mrd_returns_none_for_unrankable_instruments():
    assert build_mrd({"instrument": "essential", "delta": {}}) is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)

"""The cross-check displacement gate — three response sets, deliberately built.

The machine-generated sample cannot test this: everything in it sits mid-scale, so every
convergence claim gets suppressed and an implementation of the gate that read `return None`
would pass. So there are three sets here — one at the middle for the suppression path, one
displaced the same way for the emission path, one displaced opposite ways for the tension path.

Polarity is the trap. The closeness dimensions are inverted at source (distance from closeness
against warmth; need for reassurance against emotional stability), so a naive same-direction test
on raw scores reads a genuine agreement as a disagreement. The orientation is declared with the
reading in `_readings`, and the first test below locks it.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from crosscheck import (  # noqa: E402
    DISPLACEMENT_FLOOR, _readings, build_convergences, build_synthesis, build_tensions,
)


def _raw(pct):
    """A factor raw score that lands on the given percent of its own eight-item scale."""
    return round(8 + (pct / 100) * 32, 2)


def _factor(name, pct, high="High", low="Low"):
    return {"name": name, "raw_score": _raw(pct), "pole_high": high, "pole_low": low}


def _by(anx, avo, c_pct, a_pct, confidence="high"):
    """Personality is given as PERCENT OF EACH FACTOR'S OWN SCALE, never as a sten.

    A sten is a norm-referenced claim on a band table with no documented reference sample, so it
    is neither shown to a reader nor allowed to decide one. The raw score is what the fixture
    carries, because that is what a stored result carries and the percent is derived from it at
    read time.
    """
    return {
        "MI-AS-36": {
            "dimensions": {"anxiety": {"value": anx, "status": "scored"},
                           "avoidance": {"value": avo, "status": "scored"}},
            "confidence": confidence, "evidence_tier": "developmental",
        },
        "personality": {
            # Filler factors at mid-scale so the profile has an average to be displaced FROM.
            # Personality displacement is a distance from the reader's own profile average,
            # against an ABSOLUTE floor of 20 points of scale — absolute so that a flat profile
            # is not displaced however high it sits, and within-profile because the alternative
            # is the paused population claim.
            "factor_scores": {"C": _factor("Emotional Stability", c_pct, "Stable", "Reactive"),
                              "A": _factor("Warmth", a_pct, "Warm", "Reserved"),
                              **{k: _factor(k, 50) for k in ("E", "F", "G", "H", "I")}},
            "evidence_tier": "established",
        },
    }


def _kinds(entries):
    return {e["construct"]: e["kind"] for e in entries}


# --- polarity --------------------------------------------------------------------------------

def test_personality_displacement_is_within_profile_not_absolute():
    """A flat profile is not displaced however high it sits — and a factor at 95 in a profile
    averaging 63 is displaced when the same 95 in a profile of 95s is not."""
    flat = {(r["construct"], r["instrument"]): r for r in _readings(_by(4, 4, 95, 95))}
    flat_pers = flat[("steadiness", "personality")]
    by_flat = _by(4, 4, 95, 95)
    by_flat["personality"]["factor_scores"] = {
        "C": _factor("Emotional Stability", 95), "A": _factor("Warmth", 95)}
    only_nines = {(r["construct"], r["instrument"]): r for r in _readings(by_flat)}
    assert abs(only_nines[("steadiness", "personality")]["displacement"]) < 1.0
    assert abs(flat_pers["displacement"]) >= 1.0  # 95 against a profile average near 63


def test_the_closeness_dimensions_are_oriented_at_source():
    """High reassurance-need is LOW steadiness, and high distance is LOW closeness. If this ever
    flips, every same-direction test in this file silently inverts."""
    readings = {(r["construct"], r["instrument"]): r for r in _readings(_by(7, 7, 50, 50))}
    assert readings[("steadiness", "MI-AS-36")]["norm"] == 0.0
    assert readings[("closeness", "MI-AS-36")]["norm"] == 0.0
    assert readings[("steadiness", "MI-AS-36")]["polarity"] == "inverted"
    assert readings[("closeness", "MI-AS-36")]["polarity"] == "inverted"
    settled = {(r["construct"], r["instrument"]): r for r in _readings(_by(1, 1, 50, 50))}
    assert settled[("steadiness", "MI-AS-36")]["norm"] == 1.0


# --- set one: the middle. The suppression path -----------------------------------------------

def test_two_mid_scale_readings_are_not_convergence():
    """The defect this gate exists for: the scale midpoint is the modal outcome under
    uninformative responding, so two instruments landing there is not evidence of anything."""
    out = build_convergences(_by(4.0, 4.0, 50, 50))
    assert _kinds(out) == {"steadiness": "null", "closeness": "null"}
    for e in out:
        assert "not where your selecting is happening" in e["body"]


def test_no_superlative_survives_anywhere():
    """"The most reliable thing in this document" was a claim about the instrument, made inside a
    personal reading, and uncheckable by the person holding it."""
    everything = build_convergences(_by(1.5, 1.5, 95, 95)) + build_convergences(_by(4, 4, 50, 50))
    blob = " ".join(e["body"] for e in everything).lower()
    assert "most reliable thing" not in blob


# --- set two: displaced the same way. The emission path --------------------------------------

def test_a_genuine_agreement_still_fires():
    """Low reassurance-need with high stability, and low distance with high warmth: both
    displaced, both the same way once orientation is applied."""
    out = build_convergences(_by(1.5, 1.5, 95, 95))
    assert _kinds(out).get("steadiness") == "agreement"
    assert _kinds(out).get("closeness") == "agreement"
    body = next(e for e in out if e["construct"] == "steadiness")["body"]
    assert "toward the high end" in body
    assert "1.5" in body and "95" in body  # both values quoted


def test_an_agreement_inherits_the_weaker_input():
    """Developmental beats established, and low beats high: a pair is read at the authority of
    the weaker instrument in it, not the stronger."""
    out = build_convergences(_by(1.5, 1.5, 95, 95, confidence="low"))
    entry = next(e for e in out if e["kind"] == "agreement")
    assert entry["evidence_tier"] == "developmental"
    assert entry["confidence"] == "low"
    assert "inherits the weaker" in entry["body"]


# --- set three: displaced opposite ways. The tension path ------------------------------------

def test_an_opposite_facing_pair_is_a_tension():
    """High distance from closeness against high warmth — warmth given widely while closeness
    stays out of reach."""
    out = build_tensions(_by(4.0, 6.5, 50, 95), [])
    assert _kinds(out).get("closeness") == "tension"


def test_one_displaced_and_one_at_the_middle_is_neither():
    """Reported as the single reading it is, not dressed as two instruments agreeing."""
    out = build_convergences(_by(1.2, 4.0, 50, 50))
    assert _kinds(out).get("steadiness") == "single"
    entry = next(e for e in out if e["construct"] == "steadiness")
    assert entry["sources"] == ["Closeness Mirror"]
    assert "one reading rather than two agreeing" in entry["body"]


def test_the_floor_is_the_middle_third():
    assert abs(DISPLACEMENT_FLOOR - 1 / 6) < 1e-9


# --- the summary -----------------------------------------------------------------------------

def test_the_summary_does_not_claim_a_driver_from_a_low_confidence_middle():
    """Two null readings were being turned into a positive claim about what the selection runs
    on, sourced entirely from an instrument its own section calls provisional."""
    by = _by(4.2, 3.7, 50, 50, confidence="low")
    by["essential"] = {
        "delta": {"overall": 10.8, "biggest": "rock", "elevation": 10.2, "elevation_share": 0.94},
        "self": {"primary": {"name": "The Challenger", "key": "challenger"}, "tie": {"tied": False}},
        "ideal": {"primary": {"name": "The Challenger", "key": "challenger"}, "tie": {"tied": False}},
    }
    s = build_synthesis(by, [], [])
    assert "selection actually runs on" not in s["body"]
    assert "recognition rather than reassurance" not in s["body"]


def test_the_summary_does_not_contradict_itself_when_both_lenses_match():
    """"Wanting the same thing back" and "a complement rather than a copy" were being printed in
    the same document from two different rules."""
    by = _by(4.2, 3.7, 50, 50)
    by["essential"] = {
        "delta": {"overall": 10.8, "biggest": "rock"},
        "self": {"primary": {"name": "The Challenger", "key": "challenger"}, "tie": {"tied": False}},
        "ideal": {"primary": {"name": "The Challenger", "key": "challenger"}, "tie": {"tied": False}},
    }
    s = build_synthesis(by, [], [])
    assert "degree rather than in kind" in s["body"]
    assert "complement rather than a copy" not in s["body"]


# --- which test each side passed (Q4) --------------------------------------------------------

def test_an_agreement_names_both_tests_and_does_not_pretend_they_are_the_same():
    """The Closeness side clears an absolute position rule; the Personality side clears an
    absolute distance from the reader's own profile average. Both absolute, absolute about
    different things, and the body says so rather than smoothing it over."""
    out = build_convergences(_by(1.5, 1.5, 95, 95))
    body = next(e for e in out if e["kind"] == "agreement")["body"]
    assert "outside the middle third" in body
    assert "from your own profile average" in body
    assert "20 points of its own scale" in body


def test_a_tension_names_both_tests_too():
    out = build_tensions(_by(4.0, 6.5, 50, 95), [])
    body = next(e for e in out if e["kind"] == "tension")["body"]
    assert "outside the middle third" in body and "from your own profile average" in body


def test_a_single_reading_names_the_one_test_it_passed():
    out = build_convergences(_by(1.2, 4.0, 50, 50))
    entry = next(e for e in out if e["kind"] == "single")
    assert "outside the middle third" in entry["body"]
    assert "one reading rather than two agreeing" in entry["body"]

"""Locks the second-order composite equations and their known residuals.

The globals are arithmetic on the primaries. If anyone ever edits a weight, this fails —
which is deliberate: hard rule 1 says scoring is frozen, and a composite equation is scoring.

The reference profile is a real paired sheet (a user's standalone P150 report) used to
document where our composites agree with other 16PF-style instruments and where they don't.
It is a REGRESSION FIXTURE, not a calibration target: the gains stay at 1.0.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants.p150_data import P150_GLOBAL_FACTORS, GLOBAL_CALIBRATION, compute_global_scores
from composites import build_composites, RESIDUAL_KEYS

# 16PF-style second-order loadings, as shipped.
EXPECTED_EQUATIONS = {
    "extraversion": {"A": 0.3, "F": 0.4, "H": 0.4, "N": -0.3, "Q2": -0.5},
    "anxiety": {"C": -0.4, "L": 0.3, "O": 0.4, "Q4": 0.4},
    "receptivity": {"A": 0.3, "I": 0.5, "M": 0.3, "Q1": 0.4},
    "independence": {"E": 0.5, "H": 0.4, "L": 0.2, "Q1": 0.3},
    "self_control": {"F": -0.3, "G": 0.4, "M": -0.3, "Q3": 0.4},
}

# Paired reference sheet: primaries as printed on a standalone P150 report.
REFERENCE_PRIMARIES = {
    "A": 10, "C": 10, "E": 10, "F": 10, "G": 4, "H": 10, "I": 7, "L": 7,
    "M": 9, "N": 6, "O": 2, "Q1": 10, "Q2": 9, "Q3": 6, "Q4": 3,
}
# What our equations produce from those same primaries (documented, not tuned).
EXPECTED_REFERENCE_GLOBALS = {
    "extraversion": 8.55,
    "anxiety": 1.75,
    "receptivity": 10.0,
    "independence": 10.0,
    "self_control": 2.7,
}


def _factor_scores(primaries):
    return {k: {"sten": v, "name": k} for k, v in primaries.items()}


def test_equations_unchanged():
    for key, expected in EXPECTED_EQUATIONS.items():
        assert P150_GLOBAL_FACTORS[key]["factors"] == expected, f"{key} equation edited"


def test_gains_remain_uncalibrated():
    """A gain fitted to one person would bake that person's distortion into everyone."""
    for key in EXPECTED_EQUATIONS:
        assert GLOBAL_CALIBRATION.get(key) == 1.0, f"{key} gain is no longer 1.0"


def test_reference_profile_reproduces():
    globals_ = compute_global_scores(_factor_scores(REFERENCE_PRIMARIES))
    for key, expected in EXPECTED_REFERENCE_GLOBALS.items():
        assert globals_[key]["score_precise"] == expected, (
            f"{key}: {globals_[key]['score_precise']} != {expected}")


def test_self_control_is_low_for_reference_profile():
    """Sanity check on direction: G 4 / Q3 6 with F 10 / M 9 must give LOW self-control.

    Both the weighted equation and a plain reversed mean agree on this. A standalone report
    printing an average self-control from these primaries is not reproducible by either
    method — which is exactly the kind of disagreement the provenance block exists to expose.
    """
    globals_ = compute_global_scores(_factor_scores(REFERENCE_PRIMARIES))
    assert globals_["self_control"]["score"] <= 4
    plain = (REFERENCE_PRIMARIES["G"] + REFERENCE_PRIMARIES["Q3"]
             + (11 - REFERENCE_PRIMARIES["F"]) + (11 - REFERENCE_PRIMARIES["M"])) / 4
    assert plain <= 4


def test_provenance_exposes_every_contribution():
    result = {"instrument": "personality", "factor_scores": _factor_scores(REFERENCE_PRIMARIES)}
    prov = build_composites(result)
    assert prov is not None
    for key, equation in EXPECTED_EQUATIONS.items():
        block = prov["globals"][key]
        assert {c["factor"] for c in block["contributions"]} == set(equation)
        for c in block["contributions"]:
            assert c["sten"] == REFERENCE_PRIMARIES[c["factor"]]
            assert c["contribution"] == round(c["weight"] * (c["sten"] - 5.5), 2)
            assert c["direction"] == ("raises" if c["weight"] > 0 else "lowers")
    for key in RESIDUAL_KEYS:
        assert prov["globals"][key]["known_residual"] is True
    assert prov["globals"]["receptivity"]["polarity_note"]


if __name__ == "__main__":
    test_equations_unchanged()
    test_gains_remain_uncalibrated()
    test_reference_profile_reproduces()
    test_self_control_is_low_for_reference_profile()
    test_provenance_exposes_every_contribution()
    print("COMPOSITE EQUATIONS OK")

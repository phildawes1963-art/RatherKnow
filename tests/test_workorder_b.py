"""Work order Batch B guards.

B1 · the factor count a reader is shown must match what is scored.
B2 · MRD diagnostics must be readable in comparable units, per scale set.
B3 · findings only, no code change — the guard here is that the report exists and still names
     what it found, so it cannot quietly disappear before the question is answered.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
os.environ.setdefault("RK_ALLOW_PLACEHOLDER_ALPHA", "1")

LOCKED = json.load(open(os.path.join(ROOT, "frontend", "src", "content", "locked_copy.json"),
                        encoding="utf-8"))


# ---------------------------------------------------------------- B1

def test_personality_instructions_name_the_factors_that_are_scored():
    from constants.p150_data import P150_FACTORS

    scored = len(P150_FACTORS)
    assert scored == 15, f"factor count changed to {scored} — the reader-facing copy must follow"

    source = open(os.path.join(BACKEND, "routes", "mirror_v2.py"), encoding="utf-8").read()
    assert "sixteen primary factors" not in source, "copy claims sixteen primaries; fifteen are scored"
    assert "fifteen primary factors" in source
    # The mirrors-summary headline is the same claim on another surface, found in review.
    assert "16 factors scored" not in source, "the summary headline still claims 16 factors"
    assert f"{scored} factors scored" in source


def test_personality_scope_copy_matches_the_locked_register():
    """The sentence is hash-locked. The backend must not drift from it silently."""
    locked = LOCKED["instrument_instructions"]["personality_scope"]
    source = open(os.path.join(BACKEND, "routes", "mirror_v2.py"), encoding="utf-8").read()
    assert locked in source, f"backend copy no longer matches the locked register:\n{locked}"


# ---------------------------------------------------------------- B2

def test_mrd_in_sd_units_is_equal_for_scale_sets_sharing_an_alpha():
    """The point of the ratio: 2.326 stens and 0.451 EI-domain points are the same instrument
    quality on different units. Sets sharing an alpha must report the same MRD/SD."""
    from services.mrd import config, mrd_sd_units_for

    by_alpha = {}
    for name, spec in config()["scale_sets"].items():
        by_alpha.setdefault(spec["alpha"], []).append(mrd_sd_units_for(name))
    for alpha, ratios in by_alpha.items():
        assert len(set(ratios)) == 1, f"alpha {alpha} gave differing MRD/SD: {ratios}"

    assert mrd_sd_units_for("personality_primaries") == pytest.approx(1.163, abs=0.005)
    assert mrd_sd_units_for("personality_globals") == pytest.approx(0.901, abs=0.005)
    assert (mrd_sd_units_for("closeness_dimensions")
            == pytest.approx(mrd_sd_units_for("personality_globals"), abs=0.005))


def test_every_evaluated_scale_set_reports_both_units():
    from services.mrd import build_mrd

    factors = {k: {"name": f"F{k}", "sten": s}
               for k, s in zip("ACEFGHILMNO", [5, 6, 5, 6, 5, 6, 5, 6, 5, 6, 5])}
    gates = build_mrd({"instrument": "personality", "factor_scores": factors})
    assert gates and gates["scale_sets"]
    for s in gates["scale_sets"]:
        assert s["mrd"] > 0
        assert s["mrd_sd_units"] > 0, f"{s['scale_set']} reports no SD-unit threshold"


def test_diagnostics_report_a_rate_per_scale_set():
    source = open(os.path.join(BACKEND, "routes", "mirror_v2.py"), encoding="utf-8").read()
    assert '"suppression_rate"] = round(bucket["suppressed"]' in source, \
        "per-scale-set suppression rate is not computed"
    assert '"mrd_sd_units"' in source


# ---------------------------------------------------------------- B3

def test_the_norms_provenance_finding_is_on_the_record():
    path = os.path.join(ROOT, "docs", "B3_NORMS_PROVENANCE.md")
    text = open(path, encoding="utf-8").read()
    for needed in ("super-admin config over defaults", "No n", "raw_to_sten", "STEN_PCT"):
        assert needed in text, f"B3 report no longer states: {needed}"


def test_the_snapshot_still_carries_no_population_metadata():
    """If this fails, provenance has been added — good. Update the B3 report and this test."""
    with open(os.path.join(BACKEND, "constants", "p150_norms_snapshot.json"), encoding="utf-8") as fh:
        snap = json.load(fh)
    assert set(snap) == {"exported_at", "source", "factors"}, \
        "norms snapshot metadata changed — B3 findings need revisiting"
    assert "n" not in snap and "population" not in snap

"""Provenance for the five global dimensions.

The globals are not measured. They are second-order composites of the fifteen primary
factors, and any disagreement with another P150/16PF-style report almost always lives in
the composite equation or the raw→sten norms rather than in the answers. So we publish the
equation: which primaries feed each dimension, in which direction, and with what weight.

Read-time only. Nothing here changes a score (hard rule 1: scoring is frozen).
"""
from constants.p150_data import P150_GLOBAL_FACTORS, GLOBAL_CALIBRATION

FACTOR_NAMES = {
    "A": "Warmth", "C": "Emotional Stability", "E": "Dominance", "F": "Liveliness",
    "G": "Rule-Consciousness", "H": "Social Boldness", "I": "Sensitivity", "L": "Vigilance",
    "M": "Abstractedness", "N": "Privateness", "O": "Apprehension", "Q1": "Openness to Change",
    "Q2": "Self-Reliance", "Q3": "Perfectionism", "Q4": "Tension",
}

# Where a dimension is commonly published under the opposite pole elsewhere.
POLARITY_NOTES = {
    "receptivity": (
        "Published elsewhere as Tough-Mindedness, which is the same axis read from the opposite end: "
        "high Receptivity is low Tough-Mindedness. A 10 here and a 1 there are the same finding."
    ),
}

COMPOSITE_NOTE = (
    "Global dimensions are derived, not measured. Each is a weighted sum of primary factors — "
    "global = 5.5 + Σ(weight × (factor sten − 5.5)) — so it can only be as good as the primaries "
    "feeding it, and it can legitimately differ from another report that uses different weights or "
    "different norms. The primaries are the measurement; the composite is arithmetic on top of it."
)

RESIDUAL_NOTE = (
    "Two composites are known to sit further from other 16PF-style instruments than the rest: "
    "Receptivity and Self-Control. We publish that rather than tuning the equation to match a single "
    "sheet — a gain fitted to one person would bake one person's distortion into everyone's score. "
    "If a composite here disagrees with another report, check the primaries it is built from first: "
    "if those agree, the difference is the equation, not your answers."
)

# Composites whose residual against other instruments is documented and unresolved.
RESIDUAL_KEYS = ("receptivity", "self_control")


def global_provenance(factor_scores: dict) -> dict:
    """Per-global: the contributing primaries, their direction, weight and current sten."""
    out = {}
    for key, meta in P150_GLOBAL_FACTORS.items():
        contributions = []
        for fkey, weight in meta["factors"].items():
            factor = factor_scores.get(fkey) or {}
            sten = factor.get("sten")
            contributions.append({
                "factor": fkey,
                "name": factor.get("name") or FACTOR_NAMES.get(fkey, fkey),
                "weight": weight,
                "direction": "raises" if weight > 0 else "lowers",
                "sten": sten,
                "contribution": None if sten is None else round(weight * (sten - 5.5), 2),
            })
        contributions.sort(key=lambda c: -abs(c["contribution"] or 0))
        out[key] = {
            "name": meta["name"],
            "equation": "5.5 + Σ(weight × (sten − 5.5))",
            "gain": GLOBAL_CALIBRATION.get(key, 1.0),
            "contributions": contributions,
            "polarity_note": POLARITY_NOTES.get(key),
            "known_residual": key in RESIDUAL_KEYS,
        }
    return out


def build_composites(result: dict) -> dict | None:
    """The whole provenance block for a personality result."""
    factor_scores = result.get("factor_scores")
    if not factor_scores:
        return None
    return {
        "note": COMPOSITE_NOTE,
        "residual_note": RESIDUAL_NOTE,
        "residual_dimensions": [P150_GLOBAL_FACTORS[k]["name"] for k in RESIDUAL_KEYS],
        "globals": global_provenance(factor_scores),
    }

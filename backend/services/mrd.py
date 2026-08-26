"""Minimum Reportable Difference engine (rk-1.1.0 PRD §7.1, TRD §3.1).

Nothing in a report should describe two scores as different when the instrument cannot tell
them apart. This module decides what is distinguishable. It does not score and it does not
write prose.

MODE. Ships in **shadow** by default: every gate is evaluated and every would-be suppression
is recorded, but nothing is withheld from the reader. That is deliberate — the guarantee in
PRD §9 refunds half when fewer than three Reads fire, so the suppression rate has to be
observed on real profiles before it becomes a contractual promise. Flip
`RK_MRD_MODE=enforce` once the rate is known.
"""
import json
import math
import os
from functools import lru_cache

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "constants", "reliability_1_0_0.json")

MODE = os.environ.get("RK_MRD_MODE", "shadow")


@lru_cache(maxsize=1)
def config() -> dict:
    with open(os.path.abspath(_CONFIG_PATH), encoding="utf-8") as fh:
        cfg = json.load(fh)
    if cfg.get("placeholder") and os.environ.get("RK_ALLOW_PLACEHOLDER_ALPHA") != "1":
        raise RuntimeError(
            "reliability_1_0_0.json still holds placeholder alpha values. Measure internal "
            "consistency per scale and set placeholder=false, or set RK_ALLOW_PLACEHOLDER_ALPHA=1 "
            "to acknowledge that MRD thresholds are provisional."
        )
    return cfg


def sem(sd: float, alpha: float) -> float:
    return sd * math.sqrt(1 - alpha)


def mrd(sd: float, a1: float, a2: float, z: float = 1.645) -> float:
    return z * math.sqrt(sem(sd, a1) ** 2 + sem(sd, a2) ** 2)


def mrd_for(scale_set: str) -> float:
    cfg = config()
    s = cfg["scale_sets"][scale_set]
    return round(mrd(s["sd"], s["alpha"], s["alpha"], cfg["z"]), 3)


# ---------------------------------------------------------------- the three gates

def pairwise(a: float, b: float, threshold: float) -> bool:
    """True when the two scores may be described as different."""
    return abs(a - b) >= threshold


def flat_profile(values: list, threshold: float) -> bool:
    """True when the set is too flat to rank at all: report the level, no ordering."""
    if len(values) < 2:
        return True
    return (max(values) - min(values)) < 2 * threshold


def distinctiveness(values: dict, key: str, threshold: float) -> bool:
    """True when one scale may be named as high or low in its own right: it must clear the
    threshold from the personal mean AND from its nearest neighbour."""
    if len(values) < 2:
        return False
    v = values[key]
    mean = sum(values.values()) / len(values)
    others = [x for k, x in values.items() if k != key]
    nearest = min(abs(v - x) for x in others)
    return abs(v - mean) >= threshold and nearest >= threshold


def clusters(values: dict, threshold: float) -> list:
    """Group scales whose adjacent gaps fall under the threshold. A cluster is reportable
    when its centroid clears the threshold from the personal mean — which is how several
    tied-low scales get named as a group instead of one being promoted to 'the lowest'."""
    if not values:
        return []
    mean = sum(values.values()) / len(values)
    ordered = sorted(values.items(), key=lambda kv: kv[1])
    groups, current = [], [ordered[0]]
    for key, val in ordered[1:]:
        if abs(val - current[-1][1]) < threshold:
            current.append((key, val))
        else:
            groups.append(current)
            current = [(key, val)]
    groups.append(current)
    out = []
    for g in groups:
        centroid = sum(v for _, v in g) / len(g)
        out.append({
            "keys": [k for k, _ in g],
            "centroid": round(centroid, 2),
            "size": len(g),
            "reportable": abs(centroid - mean) >= threshold,
            "direction": "low" if centroid < mean else "high",
        })
    return out


# ---------------------------------------------------------------- per-instrument evaluation

def _evaluate_set(scale_set: str, values: dict, named: list) -> dict:
    """`values` is {key: score}. `named` is the keys the 1.0.0 report currently singles out —
    strengths, blind spots, growth areas. Those are what the gates would take away."""
    threshold = mrd_for(scale_set)
    numbers = list(values.values())
    spread = round(max(numbers) - min(numbers), 2) if numbers else 0.0
    is_flat = flat_profile(numbers, threshold)
    failed = [k for k in named if k in values and not distinctiveness(values, k, threshold)]
    return {
        "scale_set": scale_set,
        "label": config()["scale_sets"][scale_set]["label"],
        "mrd": threshold,
        "n": len(values),
        "range": spread,
        "flat_profile": is_flat,
        "clusters": clusters(values, threshold),
        "named_scales": named,
        "indistinct_named_scales": failed,
    }


def _suppressions(sets: list) -> list:
    out = []
    for s in sets:
        if s["flat_profile"]:
            out.append({
                "scale_set": s["scale_set"], "gate": "flat_profile",
                "detail": f"range {s['range']} < 2 x MRD {round(2 * s['mrd'], 2)} — level is reportable, ranking is not",
                "would_suppress": ["ranking", "strengths", "growth_areas"],
            })
        elif s["indistinct_named_scales"]:
            out.append({
                "scale_set": s["scale_set"], "gate": "distinctiveness",
                "detail": f"named scales within MRD {s['mrd']} of the personal mean or their nearest neighbour",
                "would_suppress": s["indistinct_named_scales"],
            })
    return out


def build_mrd(result: dict) -> dict | None:
    """Read-time MRD evaluation of one instrument result. Returns None where the instrument
    has no rankable scale set (Essential is within-person allocation; Flag Check is unscored)."""
    instrument = result.get("instrument")
    sets = []

    if instrument == "personality":
        factors = result.get("factor_scores") or {}
        if factors:
            values = {k: f["sten"] for k, f in factors.items() if f.get("sten") is not None}
            named = [f["name"] for f in (result.get("strengths") or []) + (result.get("blind_spots") or [])]
            by_name = {f["name"]: k for k, f in factors.items()}
            sets.append(_evaluate_set("personality_primaries", values,
                                      [by_name[n] for n in named if n in by_name]))
        globals_ = result.get("global_scores") or {}
        if globals_:
            sets.append(_evaluate_set("personality_globals",
                                      {k: g["score_precise"] for k, g in globals_.items()}, []))

    elif instrument == "eq":
        subs = result.get("sub_scores") or {}
        if subs:
            named = [s["name"] for s in (result.get("strengths") or []) + (result.get("growth_areas") or [])]
            by_name = {s["name"]: k for k, s in subs.items()}
            sets.append(_evaluate_set("ei_subdimensions", {k: s["score"] for k, s in subs.items()},
                                      [by_name[n] for n in named if n in by_name]))
        domains = result.get("domain_scores") or {}
        if domains:
            sets.append(_evaluate_set("ei_domains", {k: d["score"] for k, d in domains.items()}, []))

    elif instrument == "MI-AS-36":
        dims = {k: d["value"] for k, d in (result.get("dimensions") or {}).items()
                if d.get("status") == "scored" and d.get("value") is not None}
        if len(dims) == 2:
            sets.append(_evaluate_set("closeness_dimensions", dims, []))

    if not sets:
        return None

    cfg = config()
    return {
        "profile": cfg["profile_version"],
        "mode": MODE,
        "placeholder_alpha": bool(cfg.get("placeholder")),
        "note": (
            "Thresholds are provisional: the reliabilities behind them are literature placeholders, "
            "not measured values for these item banks. In shadow mode nothing is withheld — the gates "
            "are recorded so the suppression rate can be observed before it governs a report."
        ),
        "scale_sets": sets,
        "suppressions": _suppressions(sets),
    }

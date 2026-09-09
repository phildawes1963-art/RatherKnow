"""Percent-of-scale for the fifteen primary factors, derived at read time.

One place, because five surfaces need the same numbers and the last time each derived its own the
sten leaked back into two of them. Stored results keep their raw scores and their stens; nothing
here writes to a snapshot.

`loudest_entries` is deliberately recomputed at render rather than read from `result["loudest"]`.
That stored field was computed under the retired 1.5-sten floor, so for every result written
before disp-1.5.0 it names factors on a basis the reader is no longer shown. A display version
must not serve a value a scoring version produced under a different rule.
"""
from constants.p150_data import P150_FACTORS
from services.reportable import FACTOR_FLOOR_PP, factor_pct
from services.within_person import loudest


def factor_pcts(factor_scores: dict) -> dict:
    """{factor_key: percent of its own usable range}. Prefers the stored value, derives the rest."""
    out = {}
    for key, f in (factor_scores or {}).items():
        if key not in P150_FACTORS:
            continue
        if f.get("pct_of_scale") is not None:
            out[key] = f["pct_of_scale"]
        elif f.get("raw_score") is not None:
            out[key] = factor_pct(f["raw_score"], len(P150_FACTORS[key]["items"]))
    return out


def loudest_entries(factor_scores: dict) -> list:
    """The factors clearing the absolute floor, furthest first. Empty for a flat profile."""
    pcts = factor_pcts(factor_scores)
    picked = loudest(pcts, floor=FACTOR_FLOOR_PP)
    out = []
    for key, dev in picked["named"]:
        f = factor_scores[key]
        out.append({"factor": key, "name": f["name"], "pct_of_scale": pcts[key],
                    "deviation": dev,
                    "pole": f["pole_high"] if dev > 0 else f["pole_low"]})
    return out

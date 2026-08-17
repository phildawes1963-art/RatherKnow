"""Closeness Mirror (MI-AS-36) scoring — pure function per MI-TRD-002 §7."""
import json
import os
from functools import lru_cache

SCORING_VERSION = "1.0.0"
_BANK_PATH = os.path.join(os.path.dirname(__file__), "..", "constants", "closeness_bank_1_0_0.json")

FACETS = {
    "A1": [1, 2, 3], "A2": [4, 5, 6], "A3": [7, 8, 9],
    "A4": [10, 11, 12], "A5": [13, 14, 15], "A6": [16, 17, 18],
    "V1": [19, 20, 21], "V2": [22, 23, 24], "V3": [25, 26, 27],
    "V4": [28, 29, 30], "V5": [31, 32, 33], "V6": [34, 35, 36],
}


@lru_cache(maxsize=1)
def load_bank() -> dict:
    with open(os.path.abspath(_BANK_PATH), "r") as f:
        return json.load(f)


def _reversed_value(item: dict, raw: int) -> int:
    return 8 - raw if item["key"] == "R" else raw


def score_closeness(responses: dict) -> dict:
    """responses: {str(item_id): {"v": int 1-7, "ms": int|None}}, may include "VAL-IR"."""
    bank = load_bank()
    items = {it["id"]: it for it in bank["items"]}

    values = {}
    for iid, item in items.items():
        r = responses.get(str(iid))
        if r is not None and isinstance(r.get("v"), int) and 1 <= r["v"] <= 7:
            values[iid] = _reversed_value(item, r["v"])

    dims = {}
    for dim_key, id_range in (("anxiety", range(1, 19)), ("avoidance", range(19, 37))):
        answered = [values[i] for i in id_range if i in values]
        n_missing = 18 - len(answered)
        if n_missing >= 3:
            dims[dim_key] = {"value": None, "status": "not_scored", "n_answered": len(answered), "prorated": False}
        else:
            dims[dim_key] = {
                "value": round(sum(answered) / len(answered), 1),
                "status": "scored",
                "n_answered": len(answered),
                "prorated": n_missing > 0,
            }

    facets = {}
    for f_key, ids in FACETS.items():
        answered = [values[i] for i in ids if i in values]
        facets[f_key] = round(sum(answered) / len(answered), 1) if len(answered) >= 2 else None

    # Validity indices
    flags = []
    val_r = responses.get("VAL-IR")
    ir_answered = val_r is not None and isinstance(val_r.get("v"), int)
    ir_pass = ir_answered and val_r["v"] == bank["validity"][0]["expected"]
    if not ir_pass:
        flags.append("instructed_response")

    inconsistency_sum = 0
    for fwd, rev in bank["inconsistency_pairs"]:
        if fwd in values and rev in values:
            inconsistency_sum += abs(values[fwd] - values[rev])
    if inconsistency_sum >= 9:
        flags.append("inconsistency")

    long_string_max = 0
    run, prev = 0, None
    for seq_id in bank["order"]:
        r = responses.get(str(seq_id))
        raw = r.get("v") if r else None
        if raw is not None and raw == prev:
            run += 1
        elif raw is not None:
            run = 1
        else:
            run = 0
        prev = raw
        long_string_max = max(long_string_max, run)
    if long_string_max >= 7:
        flags.append("long_string")

    ms_values = [r["ms"] for r in responses.values() if isinstance(r.get("ms"), (int, float)) and r["ms"] > 0]
    mean_ms = round(sum(ms_values) / len(ms_values)) if ms_values else None
    if mean_ms is not None and mean_ms < 4000:
        flags.append("time_floor")

    confidence = "high" if len(flags) == 0 else ("moderate" if len(flags) == 1 else "low")

    return {
        "instrument": "MI-AS-36",
        "bank_version": bank["bank_version"],
        "scoring_version": SCORING_VERSION,
        "dimensions": dims,
        "facets": facets,
        "validity": {
            "instructed_response": "pass" if ir_pass else "fail",
            "inconsistency_sum": inconsistency_sum,
            "long_string_max": long_string_max,
            "mean_ms": mean_ms,
            "flags": flags,
        },
        "confidence": confidence,
        "evidence_tier": "developmental",
    }

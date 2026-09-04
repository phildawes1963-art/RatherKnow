"""Standalone P150 scorer for the Rather Know backend (v2 Personality Mirror).

Trimmed from mymirrorreport services/p150_scoring.py: the v2 instrument runs
130 items (no Switch module), so this scores factors, globals, validity,
strengths and blind spots only. Sten bands come from the frozen snapshot in
constants/p150_norms_snapshot.json.

TWO THINGS CHANGED WITH THE NORMS PAUSE (B3), NEITHER OF THEM A SCORE:

1. The absolute band label — Very High / High / Average / Low / Very Low — is no longer emitted.
   It is a population claim in one word, and the bands behind it have no documented reference
   sample (docs/B3_NORMS_PROVENANCE.md). The sten itself is untouched and still stored.

2. The extremes are selected by within-profile rank, not by sten >= 8 / sten <= 3. A fixed sten
   threshold says "high compared with other people"; furthest-from-your-own-profile-mean says
   "loudest in you", which is the claim the reader wanted and needs no norm at all. THREE in
   total, ranked on absolute distance in either direction — three above plus three below is six
   and dilutes the finding. Emitted as `loudest`, with strengths / blind_spots carried in
   parallel (the named ones that lean high, and the named ones that lean low) so nothing reading
   them breaks.
"""
import json
import os
from functools import lru_cache

from constants.p150_data import (
    P150_FACTORS, P150_REVERSED_ITEMS, P150_VALIDITY_ITEMS,
    P150_PERSONALITY_ITEMS, compute_global_scores,
)
from services.within_person import loudest

_SNAPSHOT_PATH = os.path.join(os.path.dirname(__file__), "..", "constants", "p150_norms_snapshot.json")


@lru_cache(maxsize=1)
def _bands():
    with open(_SNAPSHOT_PATH, encoding="utf-8") as fh:
        return json.load(fh)["factors"]


def _sten(factor_key: str, raw: int) -> int:
    bands = _bands()[factor_key]
    for b in bands:
        if b["raw_min"] <= raw <= b["raw_max"]:
            return b["sten"]
    ordered = sorted(bands, key=lambda x: x["sten"])
    return 1 if raw < ordered[0]["raw_min"] else 10


def _strip_band_labels(scores: dict) -> None:
    """Absolute band words are population claims. Remove them at the source rather than
    relying on every surface to remember not to render them."""
    for entry in scores.values():
        entry.pop("label", None)
        for sub in (entry.get("sub_clusters") or {}).values():
            sub.pop("label", None)


def score_p150_lite(all_responses: dict) -> dict:
    """`all_responses` maps str(item_id) -> int(1-5). Mirrors the MM scorer
    exactly for the blocks the v2 Personality Mirror result uses."""
    factor_scores = {}
    for factor_key, factor_data in P150_FACTORS.items():
        raw = 0
        for item_id in factor_data["items"]:
            val = int(all_responses.get(str(item_id), 3))
            if item_id in P150_REVERSED_ITEMS:
                val = 6 - val  # reverse: 5→1 … 1→5
            raw += val
        sten = _sten(factor_key, raw)
        factor_scores[factor_key] = {
            "name": factor_data["name"],
            "pole_low": factor_data["pole_low"],
            "pole_high": factor_data["pole_high"],
            "raw_score": raw,
            "sten": sten,
        }

    global_scores = compute_global_scores(factor_scores)
    _strip_band_labels(global_scores)

    sd_agree = 0
    for item in P150_VALIDITY_ITEMS:
        raw = int(all_responses.get(str(item["id"]), 3))
        if item.get("reverse"):
            if raw <= 2:
                sd_agree += 1
        else:
            if raw >= 4:
                sd_agree += 1
    sd_flag = "HIGH" if sd_agree >= 7 else ("ELEVATED" if sd_agree >= 4 else "NORMAL")

    likert_ids = [it["id"] for it in P150_PERSONALITY_ITEMS] + [it["id"] for it in P150_VALIDITY_ITEMS]
    midpoint_n = sum(1 for i in likert_ids if int(all_responses.get(str(i), 0)) == 3)
    midpoint_pct = round(midpoint_n / len(likert_ids) * 100, 1)
    ct_flag = "HIGH" if midpoint_pct >= 55 else ("ELEVATED" if midpoint_pct >= 40 else "NORMAL")

    picked = loudest({k: v["sten"] for k, v in factor_scores.items()})

    def _entry(key, dev):
        f = factor_scores[key]
        return {"factor": key, "name": f["name"], "sten": f["sten"], "deviation": dev,
                "pole": f["pole_high"] if dev > 0 else f["pole_low"]}

    loudest_named = [_entry(k, d) for k, d in picked["named"]]

    return {
        "factor_scores": factor_scores,
        "global_scores": global_scores,
        "validity": {
            "social_desirability": {"agree_count": sd_agree, "items": 10, "flag": sd_flag},
            "central_tendency": {"midpoint_count": midpoint_n, "midpoint_pct": midpoint_pct,
                                 "items": len(likert_ids), "flag": ct_flag},
            "flag": sd_flag,
        },
        "loudest": loudest_named,
        "profile_mean": picked["profile_mean"],
        "loudest_floor": picked["floor"],
        # Carried in parallel under the old names: the named factors that lean high, and those
        # that lean low. Same objects, nothing to coordinate.
        "strengths": [e for e in loudest_named if e["deviation"] > 0],
        "blind_spots": [e for e in loudest_named if e["deviation"] < 0],
    }

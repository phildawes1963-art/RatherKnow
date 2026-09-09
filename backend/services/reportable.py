"""What is large enough to report — the floors that decide whether a claim gets made at all.

Three of these were built for the Personality Mirror and never given to the others, which is how
the EI Mirror came to name a "strongest" domain across a total spread of 0.36 on a 1-5 scale.

The rule for every provisional constant here: set it so that it is MORE conservative than the
derived value is likely to be. A claim withdrawn later is worse than a claim never made.
"""
import math
import re

# --- the assumption chain, stated once ------------------------------------------------------
# SEM = SD * sqrt(1 - alpha), and the minimum reportable difference between two scores is
# MRD = 1.645 * sqrt(SEM_1^2 + SEM_2^2) (one-sided 95%).
#
# alpha is not measured for these banks. Rather than compute a floor from a placeholder and dress
# it as a derivation, we assume the pessimistic end of the plausible range: a low alpha produces a
# LARGER floor, so assuming it can only suppress claims we would otherwise have to retract.
ASSUMED_ALPHA = 0.70

# The other input is real, with one caveat that matters. The observed between-person SD of an EI
# domain score in the stored corpus is 0.294 after the low-variation records were quarantined —
# but that corpus is still overwhelmingly machine-generated, and randomly generated answers
# under-disperse relative to people. Using 0.294 would give MRD = 0.37, which is on the side that
# gets retracted. 0.60 is the plausible SD for a domain mean of Likert items among real
# respondents, and it is the larger of the two, so it is the one we take.
# Re-derive both inputs from real respondents when there are any.
EI_DOMAIN_SD = 0.60


def mrd(sd: float, alpha: float = ASSUMED_ALPHA) -> float:
    sem = sd * math.sqrt(1 - alpha)
    return round(1.645 * math.sqrt(2 * sem ** 2), 3)


EI_DOMAIN_MRD = mrd(EI_DOMAIN_SD)  # 0.765 on the 1-5 scale

# EI sub-dimensions get no highest/lowest at all. They are shorter scales, so their alpha is
# lower and their floor larger — quite possibly larger than the whole usable spread. Naming them
# would be the same defect one level down, so the numbers stay and the ranking goes.
FACET_NAMING_ALLOWED = False
FACET_SUPPRESSION_REASON = (
    "Sub-dimension scores are shown without a highest-or-lowest ranking. Each rests on a handful "
    "of items, so the difference between one and the next is smaller than the measurement error "
    "around either. The numbers are yours; the order between them is not information yet."
)

EI_FLAT_COPY = (
    "Your four domains sit within measurement error of one another. That is a finding — it means "
    "no single capacity is doing most of the work, and none is the obvious gap."
)


def ei_named(domain_scores: dict) -> dict:
    """Name a highest or lowest EI domain only where it clears the floor against the NEXT one.

    Against the next one, not against the mean: a score can sit well above the average of four
    and still be indistinguishable from the one directly below it.
    """
    scored = [(k, v["score"], v.get("name", k)) for k, v in domain_scores.items()
              if v.get("score") is not None]
    out = {"mrd": EI_DOMAIN_MRD, "highest": None, "lowest": None, "spread": None,
           "assumed_alpha": ASSUMED_ALPHA}
    if len(scored) < 2:
        return out
    ordered = sorted(scored, key=lambda t: -t[1])
    out["spread"] = round(ordered[0][1] - ordered[-1][1], 2)
    if ordered[0][1] - ordered[1][1] >= EI_DOMAIN_MRD:
        out["highest"] = {"key": ordered[0][0], "name": ordered[0][2], "score": ordered[0][1],
                          "margin": round(ordered[0][1] - ordered[1][1], 2)}
    if ordered[-2][1] - ordered[-1][1] >= EI_DOMAIN_MRD:
        out["lowest"] = {"key": ordered[-1][0], "name": ordered[-1][2], "score": ordered[-1][1],
                         "margin": round(ordered[-2][1] - ordered[-1][1], 2)}
    out["blocked"] = out["highest"] is None and out["lowest"] is None
    return out


# --- speeding -------------------------------------------------------------------------------
# A mean is the wrong statistic for a speeding check: a few slow items pull it up and it passes a
# respondent who raced through the rest. The right one is the proportion of items answered below
# a floor — and the floor belongs to the item, not to the instrument, because a six-word statement
# and a twenty-word statement are not the same reading task.
MS_PER_WORD = 300          # the common heuristic in careless-responding work
MIN_ITEM_FLOOR_MS = 1200   # even a three-word item needs the scale read once
SPEEDING_FLAG_PCT = 30.0   # flag when this share of items came in under their own floor


def item_floor_ms(text: str) -> int:
    words = len(re.findall(r"[\w'’-]+", text or ""))
    return max(MIN_ITEM_FLOOR_MS, MS_PER_WORD * words)


def speeding(responses: dict, texts: dict) -> dict:
    """responses: {item_id: {"ms": int}} · texts: {item_id: statement}. Ids compared as strings."""
    by_text = {str(k): v for k, v in texts.items()}
    below, total = 0, 0
    for iid, r in responses.items():
        ms = r.get("ms") if isinstance(r, dict) else None
        text = by_text.get(str(iid))
        if text is None or not isinstance(ms, (int, float)) or ms <= 0:
            continue
        total += 1
        if ms < item_floor_ms(text):
            below += 1
    if not total:
        return {"items_timed": 0, "below_floor": 0, "below_floor_pct": None, "flagged": False,
                "ms_per_word": MS_PER_WORD, "min_floor_ms": MIN_ITEM_FLOOR_MS}
    pct = round(100 * below / total, 1)
    return {"items_timed": total, "below_floor": below, "below_floor_pct": pct,
            "flagged": pct >= SPEEDING_FLAG_PCT, "ms_per_word": MS_PER_WORD,
            "min_floor_ms": MIN_ITEM_FLOOR_MS}


# --- social desirability --------------------------------------------------------------------
# The old cut flagged 4 of 10 as elevated, which is chance. "Agreed" here is a Likert threshold,
# not a coin flip: 4 or 5 on a 1-5 scale (1 or 2 reversed), so under content-blind responding
# p = 0.4, giving mean 4.0 and SD sqrt(10*0.4*0.6) = 1.55. The cut is set from that null, and the
# corpus then checks it rather than generating it: on the 446 clean stored profiles the counts run
# {5: 252, 4: 62, 3: 48, ...}, and 7+ catches 11 of them. Norming the cut to a percentile of our
# own distribution would have fixed the flag rate by construction, forever.
SD_ITEMS = 10
SD_NULL_P = 0.4
SD_ELEVATED_AT = 7   # ~+1.9 SD above the content-blind null
SD_HIGH_AT = 9       # ~+3.2 SD


def sd_flag(agree_count: int) -> str:
    if agree_count >= SD_HIGH_AT:
        return "HIGH"
    if agree_count >= SD_ELEVATED_AT:
        return "ELEVATED"
    return "NORMAL"


def sd_null_note() -> str:
    mean = SD_ITEMS * SD_NULL_P
    return (f"Agreeing with about {mean:.0f} of these {SD_ITEMS} is what content-blind answering "
            f"produces on its own, so only {SD_ELEVATED_AT} or more is read as anything.")

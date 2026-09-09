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

# And the rounding rule, which applies to every floor in this module: DERIVE, THEN ROUND UP,
# NEVER DOWN. Rounding a provisional floor down loosens a threshold that is already resting on an
# assumption; rounding up costs only claims that could not have been defended. So 19.109 points of
# scale becomes 20, and 0.765 on the 1-5 scale becomes 0.8. Both floors in a combined report are
# now rounded by the same logic, which is the other half of the reason.
ROUNDING_RULE = "derive, then round up, never down"


def round_up(value: float, step: float) -> float:
    return round(math.ceil(value / step - 1e-9) * step, 10)

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


EI_DOMAIN_MRD_DERIVED = mrd(EI_DOMAIN_SD)      # 0.765 on the 1-5 scale
EI_DOMAIN_MRD = round_up(EI_DOMAIN_MRD_DERIVED, 0.1)  # 0.8 — ROUNDING_RULE
EI_DOMAIN_FLOOR_BASIS = (
    f"provisional: {EI_DOMAIN_MRD:.1f} on the 1-5 scale, derived at {EI_DOMAIN_MRD_DERIVED:.3f} "
    f"from an assumed SD of {EI_DOMAIN_SD} and a pessimistic reliability of {ASSUMED_ALPHA:.2f}, "
    f"then rounded up. Non-provisional the day alpha is measured on this bank and the SD comes "
    f"from real respondents."
)

# EI sub-dimensions get no highest/lowest AND no figures. "Numeric but unranked" is
# self-defeating: fourteen numbers on a page are a ranking whatever order they are printed in, and
# a reader can re-sort four values in their head without help. Facet scales are shorter than
# domain scales, so their alpha is lower and their floor larger than the domain floor these
# figures already fail. The fourteen names stay, so the reader knows what was measured.
FACET_NAMING_ALLOWED = False
FACET_FIGURES_ALLOWED = False
FACET_SUPPRESSION_REASON = (
    "The fourteen sub-dimensions are named but not scored on this page. Each rests on a handful "
    "of items, so the difference between one and the next is smaller than the measurement error "
    "around either — and printing fourteen numbers is a ranking however they are ordered. The "
    "figures return when the reliability of this bank has been measured."
)

EI_FLAT_COPY = (
    "Your four domains sit within measurement error of one another. That is a finding — it means "
    "no single capacity is doing most of the work, and none is the obvious gap."
)


def _band(low: float, high: float) -> dict:
    """The shared band all four domains fall in, to the nearest half point.

    Not the four values rounded to the nearest 0.5: 3.5 printed against 3.0 is exactly the
    distinction the floor just refused to make, and ordering them alphabetically does not stop
    anyone re-sorting four numbers. One interval, and the audit figures beside it.
    """
    lo = math.floor(low * 2) / 2
    hi = math.ceil(high * 2) / 2
    if hi <= lo:
        hi = lo + 0.5
    return {"low": lo, "high": hi,
            "sentence": f"All four domains fall between {lo:.1f} and {hi:.1f} on the 1–5 scale."}


def ei_named(domain_scores: dict) -> dict:
    """Name a highest or lowest EI domain only where it clears the floor against the NEXT one.

    Against the next one, not against the mean: a score can sit well above the average of four
    and still be indistinguishable from the one directly below it.

    Two branches, and the presentation follows the branch. Where the domains separate, they are
    named and their figures shown. Where they do not, `resolved` is False and the surface prints
    the shared band plus the two audit numbers — observed spread and the floor — so the reader can
    see why nothing was named rather than being told to take it on trust.
    """
    scored = [(k, v["score"], v.get("name", k)) for k, v in domain_scores.items()
              if v.get("score") is not None]
    out = {"mrd": EI_DOMAIN_MRD, "highest": None, "lowest": None, "spread": None,
           "assumed_alpha": ASSUMED_ALPHA, "floor_basis": EI_DOMAIN_FLOOR_BASIS,
           "resolved": False, "band": None, "suppression_note": None}
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
    out["resolved"] = not out["blocked"]
    if not out["resolved"]:
        out["band"] = _band(ordered[-1][1], ordered[0][1])
        out["suppression_note"] = (
            f"The widest gap between any two of your four domains is {out['spread']:.2f}. The "
            f"smallest gap this instrument can resolve is {EI_DOMAIN_MRD:.1f}, so the individual "
            f"figures are not shown: printed side by side they would rank four things that are "
            f"not separated.")
    return out


# The Personality factors, same method one instrument further on. A sten is a norm-referenced
# claim — mean 5.5, SD 2, against a reference population — and the band table behind ours is an
# undocumented super-admin override whose widths run 2 to 8 raw points, which dumps most readers
# into stens 4 and 7. So no sten reaches a reader: the reader-facing layer works in
# percent-of-scale instead, compared WITHIN the profile (norm-free) and thresholded ABSOLUTELY
# (the floor does not move when someone answers flatly).
#
# The absolute part is the whole point. A floor set as a multiple of the reader's own profile SD
# would always fire — divide fifteen factors by their own spread and the largest lands near +1.8
# for everybody, including the flat profile that should name nothing. So the SD comes from the
# scale, not from the respondent.
#
# WHY 15 AND NOT range/6: the standard normal-range assumption is range ≈ 6 SD, i.e. 16.67 points
# of a 100-point scale, which derives a floor of 21.2 and rounds to 22. Both are defensible and
# 15 is the more permissive of the two. It is kept because it is the SAME assumption the EI domain
# floor already uses (0.60 of a four-point span is 15% of range), and one assumption shared across
# the two instruments in the same document is worth more than a slightly stricter floor on one of
# them. It is an assumption, not a measurement, and it is not taken from the stored corpus: the
# corpus is unknown-provenance synthetic data that cannot validate anything (§4 below), so
# deriving a floor from it on one page while saying that on another is not available.
FACTOR_SD_PP = 15.0
FACTOR_MRD_PP_DERIVED = mrd(FACTOR_SD_PP)               # 19.109 points of scale
FACTOR_FLOOR_PP = round_up(FACTOR_MRD_PP_DERIVED, 1.0)  # 20 — ROUNDING_RULE
FACTOR_FLOOR_BASIS = (
    f"provisional: {FACTOR_FLOOR_PP:g} points of scale from the reader's own profile average, "
    f"derived at {FACTOR_MRD_PP_DERIVED:.1f} from an assumed SD of {FACTOR_SD_PP:g} points and a "
    f"pessimistic reliability of {ASSUMED_ALPHA:.2f}, then rounded up. Absolute, so a flat profile "
    f"names nothing. Non-provisional the day alpha and a real between-person SD are measured on "
    f"this bank."
)


def factor_pct(raw_score: float, n_items: int) -> float:
    """A factor as percent of its own usable range, so 0 is every item at 1 and 100 at 5."""
    return round((raw_score - n_items) / (4 * n_items) * 100, 1)


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
# p = 0.4, giving mean 4.0 and SD sqrt(10*0.4*0.6) = 1.55. The cut is set from that null.
#
# THE CORPUS DOES NOT CHECK IT, and an earlier version of this comment said it did. Two
# signatures rule the stored profiles out as a check. Low variation: 1,587 of 5,206 results come
# from sessions answering on fewer than four distinct points, and are flagged and excluded.
# Patterned generation: of the profiles that survived that, 377 of 639 sat at EXACTLY five
# agreements, which is variance collapse rather than a binomial. Excluding the fixed-count
# records leaves n = 232 whose provenance is unknown, and 5 of those reach 7+ — 2.16% against the
# 5.48% the null expects, so the remainder does not reconcile with the null either. The cut is
# theoretical and stays theoretical until there are real respondents. Norming it to a percentile
# of our own distribution would fix the flag rate by construction, forever, which is worse.
SD_ITEMS = 10
SD_NULL_P = 0.4
SD_ELEVATED_AT = 7   # ~+1.9 SD above the content-blind null
SD_HIGH_AT = 9       # ~+3.2 SD
SD_CORPUS_STATUS = (
    "not validated against a corpus: the stored profiles show low variation and fixed-count "
    "generation signatures, and the n = 232 unknown-provenance remainder does not reconcile with "
    "the null (2.16% at 7+ against 5.48% expected)"
)


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

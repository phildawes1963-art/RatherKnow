"""The floors that decide whether a claim is made at all.

Covers the three constants that were set from evidence rather than convenience: the EI minimum
reportable difference, the per-item speeding floor, and the social-desirability cut.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from services.reportable import (  # noqa: E402
    ASSUMED_ALPHA, EI_DOMAIN_MRD, EI_DOMAIN_MRD_DERIVED, EI_DOMAIN_SD, FACET_FIGURES_ALLOWED,
    FACET_NAMING_ALLOWED, FACTOR_FLOOR_PP, FACTOR_MRD_PP_DERIVED, FACTOR_SD_PP,
    MIN_ITEM_FLOOR_MS, MS_PER_WORD, SD_CORPUS_STATUS, SD_ELEVATED_AT, SD_HIGH_AT, SD_NULL_P,
    ei_named, item_floor_ms, mrd, round_up, sd_flag, speeding,
)


def _domains(**scores):
    return {k: {"name": k.replace("_", " ").title(), "score": v} for k, v in scores.items()}


# --- the MRD ---------------------------------------------------------------------------------

def test_the_floor_is_derived_not_picked():
    """SEM = SD*sqrt(1-alpha); MRD = 1.645*sqrt(2*SEM^2). One assumption, stated."""
    assert ASSUMED_ALPHA == 0.70
    assert EI_DOMAIN_MRD_DERIVED == mrd(EI_DOMAIN_SD, 0.70) == 0.765
    assert EI_DOMAIN_MRD == 0.8


def test_every_floor_is_rounded_up_never_down():
    """The rule, applied to both floors in the same document so they are not rounded by two
    different logics. Rounding a provisional threshold down loosens something already resting on
    an assumption; rounding up costs only claims that could not have been defended."""
    assert EI_DOMAIN_MRD > EI_DOMAIN_MRD_DERIVED
    assert FACTOR_FLOOR_PP > FACTOR_MRD_PP_DERIVED
    assert round_up(0.765, 0.1) == 0.8
    assert round_up(19.109, 1.0) == 20.0
    assert round_up(0.8, 0.1) == 0.8, "an exact value must not be pushed a step further"


def test_the_personality_floor_shares_the_ei_assumption_and_is_absolute():
    """15 points of a 100-point scale is the same 15% of range as 0.60 of the EI four-point span.
    One assumption across the two instruments in a combined report, and neither of them taken
    from the stored corpus, which cannot validate anything."""
    assert FACTOR_SD_PP == 15.0
    assert EI_DOMAIN_SD / 4 * 100 == FACTOR_SD_PP
    assert FACTOR_MRD_PP_DERIVED == mrd(FACTOR_SD_PP, ASSUMED_ALPHA)


def test_a_pessimistic_alpha_produces_a_larger_floor():
    """Assuming low reliability can only suppress claims, never invent them — which is why a
    placeholder is allowed to sit here at all."""
    assert mrd(EI_DOMAIN_SD, 0.70) > mrd(EI_DOMAIN_SD, 0.85)


def test_the_floor_is_larger_than_the_synthetic_corpus_would_have_given():
    """The observed corpus SD of 0.294 is machine-generated and under-disperses; taking it would
    have set a floor of ~0.37 and named differences the derived floor later suppresses."""
    assert EI_DOMAIN_MRD > mrd(0.294, 0.70)


# --- EI naming -------------------------------------------------------------------------------

def test_a_third_of_a_point_names_nothing():
    """The spread that shipped in the sample report: 3.40 / 3.20 / 3.17 / 3.04."""
    named = ei_named(_domains(self_awareness=3.40, social_awareness=3.20,
                              self_management=3.17, relationship_management=3.04))
    assert named["highest"] is None and named["lowest"] is None
    assert named["blocked"] is True
    assert named["resolved"] is False
    assert named["spread"] == 0.36


def test_the_suppressed_branch_gives_one_band_and_the_two_audit_numbers():
    """Not the four values rounded to the nearest half point: 3.5 printed against 3.0 is exactly
    the distinction the floor refused to make. One interval, plus the spread and the floor, so a
    reader can check the suppression instead of taking it on trust."""
    named = ei_named(_domains(self_awareness=3.40, social_awareness=3.20,
                              self_management=3.17, relationship_management=3.04))
    assert named["band"] == {"low": 3.0, "high": 3.5,
                             "sentence": "All four domains fall between 3.0 and 3.5 on the 1–5 scale."}
    assert "0.36" in named["suppression_note"] and "0.8" in named["suppression_note"]


def test_the_resolved_branch_carries_no_band():
    named = ei_named(_domains(a=4.60, b=3.20, c=3.10, d=2.10))
    assert named["resolved"] is True
    assert named["band"] is None and named["suppression_note"] is None


def test_a_genuinely_spread_profile_still_names():
    """The flat case proves the floor blocks; this one proves it does not block everything."""
    named = ei_named(_domains(self_awareness=4.60, social_awareness=3.20,
                              self_management=3.10, relationship_management=2.10))
    assert named["highest"]["key"] == "self_awareness"
    assert named["lowest"]["key"] == "relationship_management"
    assert named["blocked"] is False


def test_the_margin_is_against_the_next_one_not_the_mean():
    """Two domains far above the average of four, but level with each other, name nothing: a
    score can beat the mean comfortably and still be indistinguishable from its neighbour."""
    named = ei_named(_domains(a=4.5, b=4.4, c=2.0, d=1.9))
    assert named["highest"] is None
    assert named["lowest"] is None


def test_facets_are_neither_ranked_nor_numbered():
    """"Numeric but unranked" is self-defeating: fourteen numbers are a ranking whatever order
    they are printed in, and facet scales are shorter than the domain scales whose floor these
    figures already fail."""
    assert FACET_NAMING_ALLOWED is False
    assert FACET_FIGURES_ALLOWED is False


# --- speeding --------------------------------------------------------------------------------

def test_the_floor_comes_from_the_item_not_the_instrument():
    short = item_floor_ms("Two words")
    long = item_floor_ms("A much longer statement that takes considerably more time to read than "
                         "the short one does")
    assert long > short
    assert short == MIN_ITEM_FLOOR_MS  # a three-word item still needs the scale read once
    assert long == MS_PER_WORD * 16


def test_speeding_reports_a_proportion_not_a_mean():
    texts = {1: "one two three four five six seven eight nine ten",  # floor 3000 ms
             2: "one two three four five six seven eight nine ten",
             3: "one two three four five six seven eight nine ten",
             4: "one two three four five six seven eight nine ten"}
    # Three raced, one dwelt. The mean is 8,875 ms and would pass; the proportion is 75%.
    responses = {1: {"ms": 500}, 2: {"ms": 500}, 3: {"ms": 500}, 4: {"ms": 34000}}
    out = speeding(responses, texts)
    assert out["below_floor_pct"] == 75.0
    assert out["flagged"] is True
    assert sum(r["ms"] for r in responses.values()) / 4 > 3000  # the mean it replaces


def test_careful_answering_is_not_flagged():
    texts = {i: "one two three four five six seven eight nine ten" for i in range(1, 5)}
    out = speeding({i: {"ms": 4000} for i in range(1, 5)}, texts)
    assert out["below_floor_pct"] == 0.0 and out["flagged"] is False


# --- social desirability ---------------------------------------------------------------------

@pytest.mark.parametrize("count,flag", [(0, "NORMAL"), (4, "NORMAL"), (6, "NORMAL"),
                                        (7, "ELEVATED"), (8, "ELEVATED"), (9, "HIGH"), (10, "HIGH")])
def test_the_cut_sits_above_the_content_blind_null(count, flag):
    """Agreement here is a Likert threshold (4 or 5 of 5), so p = 0.4 under content-blind
    answering: mean 4.0, SD 1.55. The old cut flagged 4 as elevated, which is chance itself."""
    assert sd_flag(count) == flag


def test_the_corpus_is_not_claimed_as_a_check_on_the_null():
    """It was, and it could not be. Low variation in 1,587 of 5,206 results, then 377 of 639 of
    the survivors at exactly five agreements — variance collapse, not a binomial. The n = 232
    unknown-provenance remainder reaches 7+ at 2.16% against the null's 5.48%, so it does not
    reconcile either."""
    assert "not validated against a corpus" in SD_CORPUS_STATUS
    assert "232" in SD_CORPUS_STATUS


def test_the_null_is_where_the_cut_came_from():
    expected = 10 * SD_NULL_P
    assert sd_flag(int(expected)) == "NORMAL"
    sd_units = (SD_ELEVATED_AT - expected) / (10 * SD_NULL_P * (1 - SD_NULL_P)) ** 0.5
    assert sd_units >= 1.9  # ~1.9 SD above chance; the old cut of 4 sat at 0.0
    assert SD_HIGH_AT > SD_ELEVATED_AT

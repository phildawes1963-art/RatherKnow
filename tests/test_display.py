"""Display layer (rk-1.1.0 TRD T4.1-T4.3)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

import pytest  # noqa: E402

from services.display import (  # noqa: E402
    DISPLAY_VERSION, NotNormReferenced, STEN_PCT, as_fraction, commonness,
    commonness_sentence, norm_cdf,
)


def test_sten_pct_matches_the_normal_curve():
    """The as-built scoring spec had 27 at sten 4 and 73 at sten 7. Both were wrong. This
    pins the table to Phi((sten - 5.5) / 2) so it cannot drift again."""
    for sten, pct in STEN_PCT.items():
        expected = round(100 * norm_cdf((sten - 5.5) / 2))
        assert abs(expected - pct) <= 1, f"sten {sten}: table {pct}, normal curve {expected}"


def test_the_two_corrected_cells():
    assert STEN_PCT[4] == 23
    assert STEN_PCT[7] == 77


def test_fractions_are_rounded_never_decimal():
    for pct in range(1, 51):
        f = as_fraction(pct)
        assert " in " in f and "." not in f, f


def test_commonness_direction_follows_the_midpoint():
    high = commonness(9)
    assert high["direction"] == "above" and high["share_pct"] == 4
    low = commonness(2)
    assert low["direction"] == "below" and low["share_pct"] == 4
    assert high["display_version"] == DISPLAY_VERSION


def test_commonness_sentence_names_the_pole_not_a_grade():
    s = commonness_sentence(9, "Assertive", "Deferential")
    assert "assertive" in s and "%" not in s and "sten" not in s.lower()
    assert commonness_sentence(2, "Assertive", "Deferential").count("deferential") == 1


def test_composites_are_refused():
    with pytest.raises(NotNormReferenced):
        commonness(8, composite=True)


def test_clamped_values_are_refused():
    with pytest.raises(NotNormReferenced):
        commonness(10, clamped=True)


def test_out_of_range_is_refused():
    with pytest.raises(NotNormReferenced):
        commonness(11)

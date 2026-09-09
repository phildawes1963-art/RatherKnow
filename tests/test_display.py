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


def test_every_population_statement_is_refused_while_norms_are_paused():
    """The norms pause (B3). Not deleted, refused: the day a reference sample exists with its n
    and composition published, NORM_REFERENCED goes True and these come back."""
    from services.display import NORM_REFERENCED

    assert NORM_REFERENCED is False, "norms un-paused — this test and the B3 report need updating"
    for call in (lambda: commonness(9), lambda: commonness(2),
                 lambda: commonness_sentence(9, "Assertive", "Deferential")):
        with pytest.raises(NotNormReferenced):
            call()


def test_the_population_layer_survives_intact_behind_the_switch():
    """Flipping the switch must restore the old behaviour exactly, or the pause has quietly
    become a deletion and the work to come back is unbounded."""
    import services.display as display

    display.NORM_REFERENCED = True
    try:
        high = commonness(9)
        assert high["direction"] == "above" and high["share_pct"] == 4
        low = commonness(2)
        assert low["direction"] == "below" and low["share_pct"] == 4
        assert high["display_version"] == DISPLAY_VERSION
        sentence = commonness_sentence(9, "Assertive", "Deferential")
        assert "assertive" in sentence and "%" not in sentence and "sten" not in sentence.lower()
        assert commonness_sentence(2, "Assertive", "Deferential").count("deferential") == 1
    finally:
        display.NORM_REFERENCED = False


def test_composites_are_refused():
    with pytest.raises(NotNormReferenced):
        commonness(8, composite=True)


def test_clamped_values_are_refused():
    with pytest.raises(NotNormReferenced):
        commonness(10, clamped=True)


def test_out_of_range_is_refused():
    with pytest.raises(NotNormReferenced):
        commonness(11)


def test_display_version_moved_with_the_pause():
    """Delivered narratives and PDFs are keyed on display_version, so a bump is how a reporting
    change ships without altering a document already sent. disp-1.0.0 documents keep serving the
    population layer they were rendered with."""
    assert DISPLAY_VERSION == "disp-1.5.1"

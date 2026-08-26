"""Display primitives (rk-1.1.0 PRD §7.2, TRD §4).

Pure functions. No database, no prose, no scoring. Input is a stored score; output is the
things a reader-facing surface is allowed to say about it.

Why commonness and not percentile: a 1-10 scale that is not a quality score gets read as
one — "Rule-Consciousness 3" reads as three out of ten, a fail. "About 1 in 9 people sit
further toward this end than you" carries the same information with no league-table valence,
and works on bidirectional traits where a percentile actively misleads.
"""
from math import erf, sqrt

DISPLAY_VERSION = "disp-1.0.0"

# Cumulative percentile at the midpoint of each sten band: 100 * Phi((sten - 5.5) / 2).
# Locked by test_display.py against the normal CDF so it cannot drift.
STEN_PCT = {1: 1, 2: 4, 3: 11, 4: 23, 5: 40, 6: 60, 7: 77, 8: 89, 9: 96, 10: 99}

# Rounded fractions only — never a decimal, never a two-digit percentile.
_FRACTIONS = [
    (1, "1 in 100"), (2, "1 in 50"), (3, "1 in 33"), (4, "1 in 25"), (5, "1 in 20"),
    (7, "1 in 14"), (10, "1 in 10"), (13, "1 in 8"), (17, "1 in 6"), (20, "1 in 5"),
    (25, "1 in 4"), (33, "1 in 3"), (40, "2 in 5"), (50, "1 in 2"),
]


def norm_cdf(z: float) -> float:
    return 0.5 * (1 + erf(z / sqrt(2)))


def as_fraction(pct: int) -> str:
    """Nearest plain-English fraction to a percentage of the population."""
    pct = max(1, min(50, int(round(pct))))
    return min(_FRACTIONS, key=lambda f: abs(f[0] - pct))[1]


class NotNormReferenced(ValueError):
    """Raised when a population statement is requested for something that has no norm behind
    it — a composite, a clamped value, or an instrument with no norm table."""


def commonness(sten: int, *, composite: bool = False, clamped: bool = False) -> dict:
    """A population statement for one normed primary factor sten.

    Refuses composites and clamped values (PRD §7.3): the globals are a weighted sum with
    uncalibrated gains then clipped to 1-10, and a clipped number cannot carry a defensible
    population claim.
    """
    if composite:
        raise NotNormReferenced(
            "Global dimensions are derived composites with uncalibrated gains. They show position "
            "and the published equation, never a population comparison."
        )
    if clamped:
        raise NotNormReferenced(
            "This value hit the 1-10 clamp, so its true position is unknown. No population "
            "statement is defensible."
        )
    if sten not in STEN_PCT:
        raise NotNormReferenced(f"sten {sten} is outside the 1-10 scale")

    pct_below = STEN_PCT[sten]
    if sten >= 6:
        share, direction = 100 - pct_below, "above"
    else:
        share, direction = pct_below, "below"
    return {
        "display_version": DISPLAY_VERSION,
        "sten": sten,
        "direction": direction,
        "share_pct": share,
        "fraction": as_fraction(share),
    }


def commonness_sentence(sten: int, pole_high: str, pole_low: str, **kw) -> str:
    c = commonness(sten, **kw)
    pole = pole_high if c["direction"] == "above" else pole_low
    return f"About {c['fraction']} people sit further toward {pole.lower()} than you."

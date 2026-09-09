"""Display primitives (rk-1.1.0 PRD §7.2, TRD §4).

Pure functions. No database, no prose, no scoring. Input is a stored score; output is the
things a reader-facing surface is allowed to say about it.

PAUSED, NOT DELETED. NORM_REFERENCED is False. The sten bands this layer converts have no
documented reference sample behind them (docs/B3_NORMS_PROVENANCE.md): the snapshot records no
n and no group, all fifteen factors share the generic default lower cut-offs, and the band
widths are near-uniform where a normed sten table is narrow in the middle and wide in the
tails. Arithmetic on the normal curve is correct arithmetic on an assumption this table does
not establish, so every population statement is refused at source. P4 says no band before
norms.

The machinery stays because the fix is a reference sample, not a rewrite: the day one exists,
with its n and composition published, NORM_REFERENCED goes True and this layer returns.
Meanwhile services/within_person.py carries the reader-facing load, saying only what needed no
norm in the first place.
"""
from math import erf, sqrt

DISPLAY_VERSION = "disp-1.4.0"
# 1.0.0 the population layer · 1.1.0 the norms pause · 1.2.0 the Everyday Mirror joins the
# combined reading · 1.2.1 the last sten leaks out of "how you choose" and the global rows ·
# 1.3.0 the Essential tie state: where the top two archetypes sit inside the margin the reading
# names both instead of ranking them, and prints the gap either way · 1.3.1 the tie note is
# labelled per lens and not printed twice when both lenses tie the same way. Same rule as 1.2.1:
# snapshots are write-once, so a rendering fix is a new version, never an edit to a stored file ·
# 1.3.2 a tied reading prints both archetype descriptions: a header naming two patterns above a
# body voicing only the first ranks them again in the reader's ear · 1.3.3 the PDF's loudest-traits
# heading no longer promises three above a list of one, and a profile with a single named trait
# gets a second choosing point instead of one · 1.3.4 the one-factor partial line is singular ·
# 1.4.0 the reportable floors: a convergence claim now requires both readings displaced from
# their own midpoint and displaced the same way (two mid-scale numbers agreeing is what
# uninformative answering produces), a cross-instrument claim inherits the weaker tier and
# confidence of its two inputs, EI domains are named only across a minimum reportable difference
# and EI facets not at all, the social-desirability cut moves above the content-blind null,
# speeding is measured per item instead of as a mean, and the Delta reports its elevation
# separately from its shape.
# Snapshots are keyed on this, so a bump means new renders differ and every document already
# delivered keeps exactly the bytes it was sent with.
#
# 1.2.1 exists because 1.2.0 was bumped before choosing.py was fixed, so snapshots written in
# between froze the pre-fix copy. Snapshots are write-once by design — the fix is a new version,
# never an edit to a stored document.

# The single switch. False until a reference sample exists and its n and composition are
# published. Nothing else in the codebase decides whether a population claim is allowed.
NORM_REFERENCED = False
NORM_PAUSE_REASON = (
    "Population comparisons are paused: the sten bands have no documented reference sample. "
    "See docs/B3_NORMS_PROVENANCE.md."
)

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
    if not NORM_REFERENCED:
        raise NotNormReferenced(NORM_PAUSE_REASON)
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

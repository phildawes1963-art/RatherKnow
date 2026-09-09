"""Within-person reading of a profile (norms pause, B3 decision).

The sten bands have no documented reference sample behind them (docs/B3_NORMS_PROVENANCE.md),
so every statement comparing a reader to other people is paused: no commonness fractions, no
percentile-flavoured language, and no absolute band labels. What survives is everything that
needed no norm in the first place — which way a factor leans, and how far it sits from the
reader's own middle.

That is also why the extremes selection moved. `sten >= 8` and `sten <= 3` are population
statements wearing a threshold: they say "high compared with other people". The three furthest
from the reader's own profile mean, in either direction, says "loudest in you" — no reference
sample required, and the claim the reader actually wanted. Three, not three each way: three above
plus three below is six, and six dilutes the finding.
"""
WITHIN_PERSON_VERSION = "wp-1.1.0"

LOUDEST_N = 3

# THE FLOOR IS ABSOLUTE, AND IT IS IN POINTS OF SCALE, NOT STENS.
#
# It was 1.5 stens. Two things were wrong with that. The sten is a norm-referenced claim against a
# reference population this product does not have, so it could not be the unit a norm-free reading
# is measured in; and the band table behind it is malformed anyway (widths of 2 to 8 raw points on
# Factor A, one sten spanning a quarter of the raw range). So the unit is now percent of the
# factor's own usable range, and the floor is `reportable.FACTOR_FLOOR_PP` — derived from an
# assumed scale SD and a pessimistic alpha, then rounded up.
#
# Absolute, not a fraction of the reader's own spread. A relative floor fires for everybody:
# standardise fifteen factors by their own SD and the largest always lands near +1.8, including in
# the flat profile that should name nothing at all. A flat profile naming nothing is the finding,
# not a failure, and the approved copy for it already exists.
from services.reportable import FACTOR_FLOOR_BASIS, FACTOR_FLOOR_PP  # noqa: E402

FLOOR = FACTOR_FLOOR_PP
FLOOR_BASIS = FACTOR_FLOOR_BASIS


def profile_mean(values: dict) -> float:
    return round(sum(values.values()) / len(values), 2) if values else 0.0


def deviations(values: dict) -> dict:
    mean = profile_mean(values)
    return {k: round(v - mean, 2) for k, v in values.items()}


def loudest(values: dict, floor: float = FLOOR, n: int = LOUDEST_N) -> dict:
    """The n scales furthest from the reader's own mean, in either direction.

    Ranked on absolute distance, so a low outlier outranks a smaller high one. Ties break on the
    key, so the same profile always produces the same document.
    """
    devs = deviations(values)
    clearing = [(k, d) for k, d in devs.items() if abs(d) >= floor]
    ranked = sorted(clearing, key=lambda kd: (-abs(kd[1]), kd[0]))[:n]
    return {
        "named": ranked,
        "high": [(k, d) for k, d in ranked if d > 0],
        "low": [(k, d) for k, d in ranked if d < 0],
        "profile_mean": profile_mean(values),
        "floor": floor,
    }


# Half the floor: a row leaning one way must be at least this far out before the sentence says so,
# and two factors on opposite sides of the reader's middle must not receive labels pointing in
# different directions over a difference the floor itself would refuse.
MIDDLE_BAND = FLOOR / 2


def factor_sentence(pole_high: str, pole_low: str, deviation: float, is_loudest: bool = False,
                    middle_band: float = None) -> str:
    """One row of the profile, said without reference to anybody else.

    No numeric distance on the ordinary rows: a number invites the reader to rank things the
    instrument cannot rank.
    """
    if abs(deviation) <= (MIDDLE_BAND if middle_band is None else middle_band):
        return f"Between the {pole_low.lower()} and {pole_high.lower()} ends, at your own middle."
    pole = pole_high if deviation > 0 else pole_low
    if is_loudest:
        # Not "one of the three": where only one or two clear the floor, three were not named.
        return f"Toward the {pole.lower()} end, and among those furthest from your own middle."
    return f"Toward the {pole.lower()} end."


def build_position(values: dict, meta: dict, floor: float = FLOOR) -> dict:
    """`values` is {key: score}; `meta` is {key: {"name", "pole_high", "pole_low"}}.

    Returns the read-time within-person layer: one row per scale, and which three are named.
    """
    if not values:
        return {}
    devs = deviations(values)
    picked = loudest(values, floor=floor)
    named = {k for k, _ in picked["named"]}
    rows = {}
    for key, dev in devs.items():
        m = meta.get(key, {})
        rows[key] = {
            "name": m.get("name", key),
            "value": values[key],
            "deviation": dev,
            "direction": "high" if dev > 0 else "low" if dev < 0 else "middle",
            "loudest": key in named,
            "sentence": factor_sentence(m.get("pole_high", "one"), m.get("pole_low", "the other"),
                                        dev, key in named,
                                        middle_band=floor / 2),
        }
    return {
        "version": WITHIN_PERSON_VERSION,
        "profile_mean": picked["profile_mean"],
        "floor": picked["floor"],
        "floor_basis": FLOOR_BASIS,
        "scales": rows,
        "loudest": [k for k, _ in picked["named"]],
    }

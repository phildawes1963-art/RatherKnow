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
WITHIN_PERSON_VERSION = "wp-1.0.0"

LOUDEST_N = 3

# PROVISIONAL DESIGN CHOICE, NOT A DERIVED THRESHOLD.
#
# A factor must sit at least this far from the reader's own profile mean before it is named.
# 1.0 sten is exactly one SEM at the placeholder alpha (SEM = 2*sqrt(1-0.75) = 1.0) — the weakest
# claim that is still a claim. The reader's own mean is an average of fifteen scores and so
# contributes almost no error of its own, giving an SEM of the deviation of about 1.03. 1.5 is
# roughly a 93% one-tailed interval and still leaves the feature usable.
#
# This becomes per-scale-set when D1 lands and alpha is measured: alpha = 0.85 would justify
# 1.27, alpha = 0.75 needs 1.65. Until then, this floor IS the interim gate on within-person
# distance claims, which is why RK_MRD_MODE stays in shadow rather than being asked to do the job.
FLOOR = 1.5
FLOOR_BASIS = "provisional: 1.5 sten, ~93% one-tailed at placeholder alpha; per-scale-set once D1 lands"


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


# One full sten step — see report_pdf.MIDDLE_BAND_STEN. Adjacent stens must not receive
# labels pointing in different directions.
MIDDLE_BAND = 1.0


def factor_sentence(pole_high: str, pole_low: str, deviation: float, is_loudest: bool = False) -> str:
    """One row of the profile, said without reference to anybody else.

    No numeric distance on the ordinary rows: a number invites the reader to rank things the
    instrument cannot rank.
    """
    if abs(deviation) <= MIDDLE_BAND:
        return f"Between the {pole_low.lower()} and {pole_high.lower()} ends, at your own middle."
    pole = pole_high if deviation > 0 else pole_low
    if is_loudest:
        # Not "one of the three": where only one or two clear the floor, three were not named.
        return f"Toward the {pole.lower()} end, and among those furthest from your own middle."
    return f"Toward the {pole.lower()} end."


def build_position(values: dict, meta: dict) -> dict:
    """`values` is {key: score}; `meta` is {key: {"name", "pole_high", "pole_low"}}.

    Returns the read-time within-person layer: one row per scale, and which three are named.
    """
    if not values:
        return {}
    devs = deviations(values)
    picked = loudest(values)
    named = {k for k, _ in picked["named"]}
    rows = {}
    for key, dev in devs.items():
        m = meta.get(key, {})
        rows[key] = {
            "name": m.get("name", key),
            "deviation": dev,
            "direction": "high" if dev > 0 else "low" if dev < 0 else "middle",
            "loudest": key in named,
            "sentence": factor_sentence(m.get("pole_high", "one"), m.get("pole_low", "the other"),
                                        dev, key in named),
        }
    return {
        "version": WITHIN_PERSON_VERSION,
        "profile_mean": picked["profile_mean"],
        "floor": picked["floor"],
        "floor_basis": FLOOR_BASIS,
        "scales": rows,
        "loudest": [k for k, _ in picked["named"]],
    }

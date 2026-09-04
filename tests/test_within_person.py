"""The within-person layer that replaced the population one (norms pause, B3).

These tests are the acceptance criteria for the pause: what stops being said, what starts being
said instead, and the property that makes the swap safe — no score moves.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
os.environ.setdefault("RK_ALLOW_PLACEHOLDER_ALPHA", "1")

from services.p150_lite import score_p150_lite  # noqa: E402
from services.within_person import (  # noqa: E402
    FLOOR, LOUDEST_N, WITHIN_PERSON_VERSION, build_position, factor_sentence, loudest,
    profile_mean,
)

META = {"A": {"name": "Warmth", "pole_high": "Warm", "pole_low": "Reserved"},
        "C": {"name": "Stability", "pole_high": "Stable", "pole_low": "Reactive"},
        "E": {"name": "Dominance", "pole_high": "Assertive", "pole_low": "Cooperative"}}


def _answers(value=3, overrides=None):
    a = {str(i): value for i in range(1, 141)}
    a.update(overrides or {})
    return a


# ---------------------------------------------------------------- selection

def test_loudest_is_measured_from_the_readers_own_mean():
    values = {"A": 9, "C": 5, "E": 1}
    picked = loudest(values)
    assert picked["profile_mean"] == 5.0
    assert [k for k, _ in picked["named"]] == ["A", "E"]
    assert [k for k, _ in picked["high"]] == ["A"]
    assert [k for k, _ in picked["low"]] == ["E"]


def test_three_in_total_not_three_each_way():
    """Three above plus three below is six, and six dilutes the finding."""
    values = {k: v for k, v in zip("ACEFGHILMNO", [10, 10, 10, 10, 1, 1, 1, 1, 5, 5, 5])}
    picked = loudest(values)
    assert len(picked["named"]) == LOUDEST_N == 3
    assert len(picked["high"]) + len(picked["low"]) == 3


def test_ranking_is_on_absolute_distance_so_a_low_outlier_outranks_a_smaller_high_one():
    values = {"A": 7, "C": 5, "E": 1, "F": 5, "G": 5}
    picked = loudest(values)
    assert [k for k, _ in picked["named"]][0] == "E"


def test_a_high_score_in_a_high_profile_is_not_loud():
    """The point of the change. Every factor at 9 used to be fifteen 'strengths' because 9 >= 8;
    within-person, a profile with no spread has no loudest anything."""
    flat_high = {k: 9 for k in "ACEFGHILMNO"}
    assert loudest(flat_high)["named"] == []


def test_a_low_score_can_be_loud_upward():
    """And the converse: in a profile that sits low, a 5 is the loudest thing in it. No sten
    threshold can express that, which is why the threshold had to go."""
    values = {"A": 5, "C": 2, "E": 2, "F": 2}
    assert [k for k, _ in loudest(values)["high"]] == ["A"]


def test_the_floor_stops_noise_being_promoted():
    barely = {"A": 5.4, "C": 5.0, "E": 4.6}
    assert loudest(barely)["named"] == []
    assert loudest(barely, floor=0.2)["named"] == [("A", 0.4), ("E", -0.4)]


def test_the_floor_is_the_agreed_one_and_records_why():
    """1.5 sten: about a 93% one-tailed interval at the placeholder alpha, where 1.0 is a single
    SEM. Provisional by decision, and it says so — it becomes per-scale-set when D1 lands."""
    from services.within_person import FLOOR_BASIS

    assert FLOOR == 1.5
    assert "provisional" in FLOOR_BASIS and "D1" in FLOOR_BASIS
    assert build_position({"A": 7, "C": 4}, META)["floor_basis"] == FLOOR_BASIS


def test_ties_break_deterministically():
    values = {"E": 8, "A": 8, "C": 2, "M": 5}
    first = loudest(values)
    second = loudest(dict(reversed(list(values.items()))))
    assert first["named"] == second["named"]


# ---------------------------------------------------------------- wording

def test_no_sentence_mentions_other_people():
    banned = ("people", "population", "percentile", "average person", "than most", "1 in ",
              "unusually", "common")
    values = {k: v for k, v in zip("ACE", [9, 5, 1])}
    block = build_position(values, META)
    for row in block["scales"].values():
        low = row["sentence"].lower()
        for term in banned:
            assert term not in low, f"population language survived: {row['sentence']}"


def test_no_ordinary_row_prints_a_distance():
    """A number invites the reader to rank things the instrument cannot rank."""
    plain = factor_sentence("Warm", "Reserved", 2.0, is_loudest=False)
    assert plain == "Toward the warm end."


def test_no_sentence_carries_a_band_word_or_a_number():
    for dev in (-3.0, -1.2, -0.5, 0.0, 0.5, 1.2, 3.0):
        s = factor_sentence("Warm", "Reserved", dev).lower()
        for band in ("very high", "very low", "average", "high", "low"):
            assert band not in s, f"band word in: {s}"
        assert not any(ch.isdigit() for ch in s), s


def test_the_sentence_names_the_pole_the_reader_leans_toward():
    assert "warm" in factor_sentence("Warm", "Reserved", 2.0).lower()
    assert "reserved" in factor_sentence("Warm", "Reserved", -2.0).lower()
    assert "at your own middle" in factor_sentence("Warm", "Reserved", 0.1).lower()


def test_named_rows_say_so_in_the_approved_words():
    assert (factor_sentence("Warm", "Reserved", 2.0, is_loudest=True)
            == "Toward the warm end, and one of the three furthest from your own middle.")


def test_build_position_is_versioned():
    block = build_position({"A": 7, "C": 4}, META)
    assert block["version"] == WITHIN_PERSON_VERSION == "wp-1.0.0"
    assert block["profile_mean"] == profile_mean({"A": 7, "C": 4})


# ---------------------------------------------------------------- the scorer

def test_no_band_label_is_emitted_anywhere():
    scored = score_p150_lite(_answers())
    for f in scored["factor_scores"].values():
        assert "label" not in f, f
    for g in scored["global_scores"].values():
        assert "label" not in g, g
        for sub in (g.get("sub_clusters") or {}).values():
            assert "label" not in sub, sub


def test_stens_and_raw_scores_are_untouched_by_the_pause():
    """The pause is a display decision. If a raw score or a sten moved, it was a scoring change
    in disguise. Hand-computed from the frozen bands: 130 answers of 3 → raw 24 on every factor."""
    scored = score_p150_lite(_answers(3))
    for key, f in scored["factor_scores"].items():
        assert f["raw_score"] == 24, f"{key} raw {f['raw_score']}"
        assert 1 <= f["sten"] <= 10


def _maxed(factor_key):
    """Answers that genuinely push one factor to its high pole, respecting reversals."""
    from constants.p150_data import P150_FACTORS, P150_REVERSED_ITEMS

    a = _answers(3)
    for item in P150_FACTORS[factor_key]["items"]:
        a[str(item)] = 1 if item in P150_REVERSED_ITEMS else 5
    return a


def test_extremes_come_from_within_profile_rank_not_a_sten_threshold():
    scored = score_p150_lite(_maxed("A"))
    assert [x["factor"] for x in scored["loudest"]] == ["A"]
    assert scored["loudest"][0]["deviation"] > 0
    assert len(scored["loudest"]) <= 3
    # old names carry the same entries, split by direction, so nothing reading them breaks
    assert scored["strengths"] == [e for e in scored["loudest"] if e["deviation"] > 0]
    assert scored["blind_spots"] == [e for e in scored["loudest"] if e["deviation"] < 0]


def test_a_uniformly_high_profile_names_no_extremes():
    scored = score_p150_lite(_answers(5))
    assert scored["loudest"] == [] and scored["strengths"] == []


def test_ei_reports_the_score_and_drops_the_grade():
    """Q1: High / Moderate / Developing implies a standard, and the 3.0 / 4.0 cut-offs have no
    documented reference sample either. The mean of the reader's own answers is a fact and stays."""
    source = open(os.path.join(BACKEND, "routes", "mirror_v2.py"), encoding="utf-8").read()
    eq = source.split("def _score_eq(")[1].split("def _commonness")[0]
    for banned in ('"Moderate"', '"Developing"', 'domain_band', 'overall_band'):
        assert banned not in eq, f"EI band label survived: {banned}"

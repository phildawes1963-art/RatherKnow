"""The Everyday Mirror (rk-everyday-mirror-instrument-draft.md §5-6)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from services.everyday_scoring import load_bank, score_everyday  # noqa: E402

BANK = load_bank()
DOMAINS = list(BANK["domains"])


def _all_a(ms=6000):
    """Every Block A item answered toward pole A; every Block B comparison won by the left domain.
    No side flipping, so value 1 is always option A / the left domain."""
    r = {i["id"]: {"v": 1, "ms": ms} for i in BANK["block_a"]}
    r.update({i["id"]: {"v": 1, "ms": ms} for i in BANK["block_b"]})
    return r


def test_bank_shape():
    assert len(BANK["block_a"]) == 28
    assert len(BANK["block_b"]) == 21  # 7C2 full round-robin
    assert len(BANK["domains"]) == 7
    per_domain = {d: 0 for d in DOMAINS}
    for item in BANK["block_a"]:
        per_domain[item["domain"]] += 1
    assert set(per_domain.values()) == {4}
    pairs = {frozenset((i["left"], i["right"])) for i in BANK["block_b"]}
    assert len(pairs) == 21, "Block B must be a full round-robin with no repeated pair"
    for item in BANK["block_b"]:
        assert item["left"] != item["right"]


def test_pretest_is_declared_outstanding():
    """The desirability pre-test is the one step that cannot be skipped. Until it runs, the
    instrument must say so rather than imply matched pairs."""
    assert BANK["pretest"]["status"] == "not_run"
    assert score_everyday(_all_a())["pretest_status"] == "not_run"


def test_block_a_positions_run_0_to_4():
    res = score_everyday(_all_a())
    for domain, pos in res["positions"].items():
        assert pos["position"] == 4, domain
        assert pos["status"] == "scored"
        assert BANK["domains"][domain]["pole_a"].lower() in pos["label"]

    flipped = {i["id"]: {"v": 2, "ms": 6000} for i in BANK["block_a"]}
    flipped.update({i["id"]: {"v": 1, "ms": 6000} for i in BANK["block_b"]})
    res_b = score_everyday(flipped)
    for domain, pos in res_b["positions"].items():
        assert pos["position"] == 0, domain
        assert BANK["domains"][domain]["pole_b"].lower() in pos["label"]


def test_side_map_maps_choices_back_to_poles():
    """The reader's left/right is randomised; the pole mapping must survive it."""
    responses = {i["id"]: {"v": 2, "ms": 6000} for i in BANK["block_a"]}
    responses.update({i["id"]: {"v": 1, "ms": 6000} for i in BANK["block_b"]})
    side_map = {i["id"]: "BA" for i in BANK["block_a"]}  # B rendered on the left
    res = score_everyday(responses, side_map)
    for domain, pos in res["positions"].items():
        assert pos["position"] == 4, f"{domain}: flipping the side must not move the pole"


def test_two_two_split_is_undifferentiated_not_a_midpoint():
    responses = _all_a()
    for item in BANK["block_a"]:
        if item["domain"] == "money" and item["id"] in ("A5_1", "A5_2"):
            responses[item["id"]] = {"v": 2, "ms": 6000}
    res = score_everyday(responses)
    money = res["positions"]["money"]
    assert money["status"] == "undifferentiated"
    assert money["label"] == "undifferentiated"
    assert "money" in res["validity"]["undifferentiated_domains"]
    # An undifferentiated domain never reaches the position x priority map.
    assert "money" not in [c["domain"] for c in res["map"]]


def test_block_b_wins_sum_to_21():
    res = score_everyday(_all_a())
    assert sum(p["wins"] for p in res["priority"]) == 21
    assert all(0 <= p["wins"] <= 6 for p in res["priority"])
    assert res["validity"]["block_b_complete"] is True


def test_a_transitive_ordering_has_no_circular_triads():
    """Left domain always wins, and block_b is listed in a consistent order, so the result is
    a strict ordering: zero intransitive triads, zeta = 1.0."""
    res = score_everyday(_all_a())
    assert res["validity"]["circular_triads"] == 0
    assert res["validity"]["zeta"] == 1.0
    assert "circular_triads" not in res["validity"]["flags"]
    assert [p["wins"] for p in res["priority"]] == [6, 5, 4, 3, 2, 1, 0]
    assert [p["rank"] for p in res["priority"]] == [1, 2, 3, 4, 5, 6, 7]


def test_circular_triads_are_detected_and_flagged():
    """A rock-paper-scissors ordering across all seven domains: every domain wins three and
    loses three, so no ranking is real. zeta must drop below the 0.70 trigger."""
    responses = {i["id"]: {"v": 1, "ms": 6000} for i in BANK["block_a"]}
    order = {d: i for i, d in enumerate(DOMAINS)}
    for item in BANK["block_b"]:
        li, ri = order[item["left"]], order[item["right"]]
        # cyclic dominance: i beats the next three indices modulo 7
        left_wins = (ri - li) % 7 in (1, 2, 3)
        responses[item["id"]] = {"v": 1 if left_wins else 2, "ms": 6000}
    res = score_everyday(responses)
    assert res["validity"]["circular_triads"] > 0
    assert res["validity"]["zeta"] < 0.70
    assert "circular_triads" in res["validity"]["flags"]
    assert res["confidence"] in ("moderate", "low")
    assert all(p["wins"] == 3 for p in res["priority"])
    assert all(p["tied"] for p in res["priority"])


def test_zeta_arithmetic():
    """zeta = 1 - 24d / (n^3 - n), n=7 so the denominator is 336; max d = 14 gives zeta = 0."""
    assert 7 ** 3 - 7 == 336
    assert round(1 - (24 * 14) / 336, 3) == 0.0
    assert round(1 - (24 * 4) / 336, 3) == 0.714  # just above the trigger
    assert round(1 - (24 * 5) / 336, 3) == 0.643  # just below


def test_side_bias_flag():
    responses = {i["id"]: {"v": 1, "ms": 6000} for i in BANK["block_a"]}
    responses.update({i["id"]: {"v": 1, "ms": 6000} for i in BANK["block_b"]})
    res = score_everyday(responses)
    assert res["validity"]["side_bias_left_pct"] == 100.0
    assert "side_bias" in res["validity"]["flags"]


def test_time_floor_flag():
    res = score_everyday(_all_a(ms=1200))
    # The mean was replaced by the share of items answered under their OWN floor (300 ms per word
    # of the item), so the flag is "speeding" and it fires on the proportion, not on an average.
    assert "speeding" in res["validity"]["flags"]
    assert res["validity"]["speeding"]["below_floor_pct"] >= 30.0
    assert score_everyday(_all_a(ms=6000))["validity"]["mean_ms"] == 6000


def test_thin_domain_is_not_scored():
    responses = _all_a()
    for item in BANK["block_a"]:
        if item["domain"] == "order" and item["id"] != "A3_1":
            del responses[item["id"]]
    res = score_everyday(responses)
    assert res["positions"]["order"]["status"] == "not_scored"
    assert res["positions"]["order"]["position"] is None


def test_the_map_names_the_four_corners():
    res = score_everyday(_all_a())
    cells = {c["cell"] for c in res["map"]}
    assert "non_negotiable" in cells, "extreme position + top-3 priority is a non-negotiable"
    assert "strong_but_tradeable" in cells, "extreme position + low priority is the surprising cell"
    for corner in res["map"]:
        assert corner["cell"] in {"non_negotiable", "strong_but_tradeable", "needs_settling", "low_friction"}


def test_no_compatibility_score_or_norms_anywhere():
    res = score_everyday(_all_a())
    # The claim_limit string is the refusal itself, so it names what it refuses. Scan everything else.
    scanned = {k: v for k, v in res.items() if k != "claim_limit"}
    blob = repr(scanned).lower()
    for banned in ("compatibility", "percentile", "norm_", "band"):
        assert banned not in blob, f"'{banned}' must never appear in an Everyday Mirror result"
    assert res["evidence_tier"] == "developmental"
    assert "not a compatibility score" in res["claim_limit"]


def test_no_item_id_contains_a_dot():
    """Answers are stored as `responses.<item_id>` in Mongo, where a dot is a nested path — a
    dotted id silently discards the answer. This caught exactly that on the first build."""
    for item in BANK["block_a"] + BANK["block_b"]:
        assert "." not in item["id"], item["id"]
        assert not item["id"].startswith("$"), item["id"]

"""The Everyday Mirror — forced-choice scoring (rk-everyday-mirror-instrument-draft.md §5-6).

Position (Block A) and priority (Block B). Position without priority is what every lifestyle
quiz already sells; the pair is the point — someone can be extreme on a domain and not care
whether a partner matches it.

Refusals, permanently: no compatibility score, no norms, no bands, no percentiles. The only
permitted claim is "here is where daily friction is likely to sit".

Responses are recorded as the option the reader saw on the LEFT (1) or RIGHT (2). Presentation
side is randomised per session and stored on the session, so the mapping back to poles happens
here and the reader never sees which side was which pole.
"""
import json
import os
from functools import lru_cache

SCORING_VERSION = "1.0.0"
_BANK_PATH = os.path.join(os.path.dirname(__file__), "..", "constants", "everyday_bank_1_0_0.json")

N_DOMAINS = 7
_TRIAD_DENOM = N_DOMAINS ** 3 - N_DOMAINS  # 336


@lru_cache(maxsize=1)
def load_bank() -> dict:
    with open(os.path.abspath(_BANK_PATH), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _chose_a(value: int, flipped: bool) -> bool:
    """value 1 = the reader picked the left-rendered option. `flipped` means B was on the left."""
    if flipped:
        return value == 2
    return value == 1


def _position_label(domain: dict, position: int) -> str:
    """Five positions on a labelled continuum, both poles always attached. No band, no grade."""
    return [
        f"clearly {domain['pole_b'].lower()}",
        f"leaning {domain['pole_b'].lower()}",
        "evenly split",
        f"leaning {domain['pole_a'].lower()}",
        f"clearly {domain['pole_a'].lower()}",
    ][position]


def _circular_triads(beats: dict, domains: list) -> int:
    """Intransitive triads in the round-robin: a>b, b>c, c>a. Max 14 for n=7."""
    d = 0
    n = len(domains)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                a, b, c = domains[i], domains[j], domains[k]
                cycle_one = beats.get((a, b)) and beats.get((b, c)) and beats.get((c, a))
                cycle_two = beats.get((a, c)) and beats.get((c, b)) and beats.get((b, a))
                if cycle_one or cycle_two:
                    d += 1
    return d


def score_everyday(responses: dict, side_map: dict | None = None) -> dict:
    """responses: {item_id: {"v": 1|2, "ms": int|None}}. side_map: {item_id: "AB"|"BA"}."""
    bank = load_bank()
    side_map = side_map or {}
    domains = list(bank["domains"])

    def flipped(item_id: str) -> bool:
        return side_map.get(item_id) == "BA"

    # ---------------- Block A: position ----------------
    a_items: dict = {d: [] for d in domains}
    for item in bank["block_a"]:
        a_items[item["domain"]].append(item)

    positions, left_choices, left_total = {}, 0, 0
    for domain_key, items in a_items.items():
        meta = bank["domains"][domain_key]
        answered, a_count = 0, 0
        for item in items:
            r = responses.get(item["id"])
            if r is None or r.get("v") not in (1, 2):
                continue
            answered += 1
            if r["v"] == 1:
                left_choices += 1
            left_total += 1
            if _chose_a(r["v"], flipped(item["id"])):
                a_count += 1
        if answered < 3:
            positions[domain_key] = {"name": meta["name"], "position": None, "status": "not_scored",
                                     "n_answered": answered}
            continue
        # A 2-2 split is 'undifferentiated', NOT a midpoint. They are different claims.
        undifferentiated = answered == 4 and a_count == 2
        positions[domain_key] = {
            "name": meta["name"],
            "pole_a": meta["pole_a"],
            "pole_b": meta["pole_b"],
            "position": a_count,
            "of": answered,
            "label": "undifferentiated" if undifferentiated else _position_label(meta, a_count),
            "status": "undifferentiated" if undifferentiated else "scored",
            "n_answered": answered,
        }

    # ---------------- Block B: priority ----------------
    wins = {d: 0 for d in domains}
    beats: dict = {}
    b_answered = 0
    for item in bank["block_b"]:
        r = responses.get(item["id"])
        if r is None or r.get("v") not in (1, 2):
            continue
        b_answered += 1
        if r["v"] == 1:
            left_choices += 1
        left_total += 1
        winner = item["left"] if _chose_a(r["v"], flipped(item["id"])) else item["right"]
        loser = item["right"] if winner == item["left"] else item["left"]
        wins[winner] += 1
        beats[(winner, loser)] = True

    complete_b = b_answered == len(bank["block_b"])
    ordered = sorted(domains, key=lambda d: (-wins[d], bank["domains"][d]["name"]))
    priority = []
    rank, prev_wins, prev_rank = 0, None, 0
    for d in ordered:
        rank += 1
        if wins[d] == prev_wins:
            shown_rank = prev_rank
        else:
            shown_rank, prev_rank, prev_wins = rank, rank, wins[d]
        priority.append({
            "domain": d, "name": bank["domains"][d]["name"], "wins": wins[d],
            "rank": shown_rank, "descriptor": bank["domains"][d]["descriptor"],
            "tied": sum(1 for x in domains if wins[x] == wins[d]) > 1,
        })

    # ---------------- Validity ----------------
    flags = []
    triads = _circular_triads(beats, domains) if complete_b else None
    zeta = round(1 - (24 * triads) / _TRIAD_DENOM, 3) if triads is not None else None
    if zeta is not None and zeta < 0.70:
        flags.append("circular_triads")

    side_bias = round(100 * left_choices / left_total, 1) if left_total else None
    if side_bias is not None and (side_bias > 80 or side_bias < 20):
        flags.append("side_bias")

    ms_values = [r["ms"] for r in responses.values()
                 if isinstance(r.get("ms"), (int, float)) and r["ms"] > 0]
    mean_ms = round(sum(ms_values) / len(ms_values)) if ms_values else None
    if mean_ms is not None and mean_ms < 3000:
        flags.append("time_floor")

    undiff = [k for k, v in positions.items() if v.get("status") == "undifferentiated"]

    # ---------------- The map: position x priority ----------------
    top_priority = {p["domain"] for p in priority if p["rank"] <= 3}
    corners = []
    for domain_key, pos in positions.items():
        if pos.get("position") is None or pos.get("status") == "undifferentiated":
            continue
        extreme = pos["position"] in (0, 4)
        high = domain_key in top_priority
        if extreme and high:
            cell = "non_negotiable"
        elif extreme and not high:
            cell = "strong_but_tradeable"
        elif not extreme and high:
            cell = "needs_settling"
        else:
            cell = "low_friction"
        corners.append({"domain": domain_key, "name": pos["name"], "cell": cell,
                        "position": pos["position"], "label": pos["label"],
                        "priority_rank": next(p["rank"] for p in priority if p["domain"] == domain_key)})

    return {
        "instrument": "MI-EV-49",
        "bank_version": bank["bank_version"],
        "scoring_version": SCORING_VERSION,
        "positions": positions,
        "priority": priority,
        "map": corners,
        "validity": {
            "circular_triads": triads,
            "zeta": zeta,
            "side_bias_left_pct": side_bias,
            "mean_ms": mean_ms,
            "undifferentiated_domains": undiff,
            "block_b_complete": complete_b,
            "flags": flags,
        },
        "confidence": "high" if not flags else ("moderate" if len(flags) == 1 else "low"),
        "evidence_tier": "developmental",
        "pretest_status": bank["pretest"]["status"],
        "claim_limit": (
            "This shows where daily friction is likely to sit. It is not a compatibility score, "
            "and there is no such thing here. No norms, no bands, no percentiles — these are your "
            "own choices ranked against each other, not against anyone else."
        ),
    }

"""The cross-check — agreements as signal, disagreements as findings.

Two jobs. First, the hand-written tension rules (kept verbatim from the original build).
Second, a construct-aligned comparison that always has something honest to say when two or
more instruments overlap: where two independent measures of the same underlying thing land
in the same place, that convergence is signal and is worth printing.

Everything here is derived at read time from stored snapshots. No rescoring, no invented
numbers: every statement quotes the two values it is comparing.
"""

from services.factor_pct import factor_pcts, loudest_entries
from services.reportable import FACTOR_FLOOR_PP, ei_named

# Retired as the deciding test, kept because stored code paths and tests still reference the
# idea: proximity on a normalised 0-1 scale was the old proxy for agreement. It cannot be mixed
# with the displacement measure below, because the two are in different units — an absolute
# scale position against a within-profile distance — so agreement is now decided in displacement
# units and these bands only widen or narrow how close "the same place" has to be.
AGREE_BAND = 0.14
TENSION_BAND = 0.30

# In displacement units, where 1.0 is the edge of "worth reporting" for that instrument. Two
# readings agree when both are displaced, displaced the same way, and land within one unit of
# each other. They pull apart when both are displaced in opposite directions.
AGREE_GAP_UNITS = 1.0

# Two readings both landing mid-scale is not convergent evidence. The midpoint is the modal
# outcome under uninformative responding — which is exactly why a machine-generated response set
# produced two agreements and no tensions — so convergence only carries information when both
# readings are displaced from their own midpoint, in the same direction.
#
# Outside the middle third of the scale, i.e. at least a sixth of the range away from the middle.
DISPLACEMENT_FLOOR = 1 / 6

# Every reading in _readings() is stored ALREADY ORIENTED so that a higher norm means more of the
# named construct — the closeness dimensions are inverted at source, because "distance from
# closeness" runs against "warmth". Polarity is therefore declared with the reading and never
# inferred from the sign of a raw score. `_readings` asserts it; test_crosscheck_gate locks it.
INSTRUMENT_LABEL = {
    "essential": "Essential Mirror",
    "MI-AS-36": "Closeness Mirror",
    "personality": "Personality Mirror",
    "eq": "EI Mirror",
}

TIER_RANK = {"established": 2, "developmental": 1}
CONFIDENCE_RANK = {"high": 3, "moderate": 2, "low": 1}


def _tier_and_confidence(by: dict, *instruments) -> dict:
    """A cross-instrument claim inherits the LOWER tier and the LOWER confidence of its inputs.

    A pair built on a Low-confidence developmental instrument cannot be presented with more
    authority than that instrument has on its own.
    """
    tiers, confs = [], []
    for key in instruments:
        r = by.get(key) or by.get("closeness" if key == "MI-AS-36" else key) or {}
        tiers.append((r.get("evidence_tier") or "developmental").lower())
        conf = (r.get("confidence") or "").lower()
        if conf in CONFIDENCE_RANK:
            confs.append(conf)
    tier = min(tiers, key=lambda t: TIER_RANK.get(t, 1)) if tiers else "developmental"
    confidence = min(confs, key=lambda c: CONFIDENCE_RANK[c]) if confs else None
    bits = [f"Read at the {tier} tier"]
    if confidence:
        bits.append(f"and at {confidence} confidence")
    return {
        "evidence_tier": tier,
        "confidence": confidence,
        "caveat": (" ".join(bits) + " — a comparison inherits the weaker of the two instruments "
                   "it is built from, not the stronger."),
    }


# Retired: the Personality Mirror's floor used to be expressed in stens, and so did this. Both
# are now `reportable.FACTOR_FLOOR_PP` — points of the factor's own scale, from the reader's own
# profile average. The old name is gone rather than left pointing at a different unit.


def _displacement(reading: dict) -> float:
    """Signed displacement in units where 1.0 is the edge of "worth reporting"."""
    return reading["displacement"]


def _test_phrase(reading: dict) -> str:
    """Which test this side of the pair passed, in words.

    The two sides do not pass the same test and the copy must not sound as if they do. Both
    thresholds are absolute, but they are absolute about different things: one is a position on
    the instrument's own scale, the other a distance from the reader's own profile average. The
    asymmetry is smaller than it was — the Personality side used to be relative to nothing at all
    — and it is stated rather than smoothed over.
    """
    if reading["instrument"] == "personality":
        return (f"{reading['label']} sits at least {FACTOR_FLOOR_PP:g} points of its own scale "
                f"from your own profile average, which is the smallest distance this instrument "
                f"can resolve")
    return (f"{reading['label']} sits outside the middle third of its own "
            f"{reading['scale'].split(',')[0]} scale")


def _displaced(reading: dict) -> bool:
    return abs(reading["displacement"]) >= 1.0


def _norm(value, low, high):
    if value is None:
        return None
    return max(0.0, min(1.0, (float(value) - low) / (high - low)))


def _readings(by):
    """Every available measure, normalised 0–1 and grouped by the construct it speaks to.

    Accepts either keying convention for the closeness instrument: sessions use "closeness",
    stored results use "MI-AS-36".
    """
    clo = by.get("MI-AS-36") or by.get("closeness")
    pers, eq, ess = by.get("personality"), by.get("eq"), by.get("essential")
    out = []

    def add(construct, instrument, label, raw, scale, norm, polarity="direct", displacement=None):
        """`norm` must already be oriented so higher = more of the construct.

        `polarity` records how it got there — "inverted" where the source scale runs the other
        way (distance from closeness against warmth; need for reassurance against stability).
        Declared here with the reading, so no downstream comparison has to infer it.

        `displacement` is the signed distance from this reading's own reference point, in units
        where 1.0 is the edge of "worth reporting", and it is declared per instrument because the
        instruments do not share a reference point. The Personality Mirror in particular must NOT
        use its absolute sten position: that position is the norm-referenced statement the
        product has paused, and the frozen band table compresses real answers into stens 4-8
        anyway, so nothing would ever register. It uses distance from the reader's own profile
        mean against the same 1.5-sten floor that decides which factors get named.
        """
        if norm is None:
            return
        if displacement is None:
            displacement = (norm - 0.5) / DISPLACEMENT_FLOOR
        out.append({"construct": construct, "instrument": instrument, "label": label,
                    "raw": raw, "scale": scale, "norm": norm, "polarity": polarity,
                    "displacement": displacement})

    if clo:
        anx = clo["dimensions"]["anxiety"]
        avo = clo["dimensions"]["avoidance"]
        if anx.get("status") == "scored":
            add("steadiness", "MI-AS-36", "settledness in closeness", anx["value"], "1–7 reassurance",
                1 - _norm(anx["value"], 1, 7), polarity="inverted")
        if avo.get("status") == "scored":
            add("closeness", "MI-AS-36", "ease with closeness", avo["value"], "1–7 distance",
                1 - _norm(avo["value"], 1, 7), polarity="inverted")
    if pers:
        f = pers["factor_scores"]
        # No sten reaches the reader, and none decides a claim about them either. A sten is a
        # norm-referenced statement — mean 5.5, SD 2, against a reference population — and one
        # printed two sections after "no band is shown, because the norms to justify one do not
        # exist" is the same claim in a different costume. Percent-of-scale instead, compared
        # within the profile and thresholded absolutely at reportable.FACTOR_FLOOR_PP.
        pcts = factor_pcts(f)
        own_mean = sum(pcts.values()) / len(pcts) if pcts else 50.0
        for key, construct, label in (("C", "steadiness", "emotional stability"),
                                      ("A", "closeness", "warmth"),
                                      ("Q2", "self_reliance", "self-reliance")):
            if key in pcts:
                add(construct, "personality", label, round(pcts[key]),
                    "points of scale, against your own profile average of "
                    f"{round(own_mean)}",
                    pcts[key] / 100,
                    displacement=(pcts[key] - own_mean) / FACTOR_FLOOR_PP)
    if eq:
        d = eq["domain_scores"]
        if "self_management" in d:
            add("steadiness", "eq", "self-management", d["self_management"]["score"], "1–5",
                _norm(d["self_management"]["score"], 1, 5))
        if "relationship_management" in d:
            add("repair", "eq", "relationship management", d["relationship_management"]["score"], "1–5",
                _norm(d["relationship_management"]["score"], 1, 5))
        if "social_awareness" in d:
            add("attunement", "eq", "social awareness", d["social_awareness"]["score"], "1–5",
                _norm(d["social_awareness"]["score"], 1, 5))
        if "self_awareness" in d:
            add("self_knowledge", "eq", "self-awareness", d["self_awareness"]["score"], "1–5",
                _norm(d["self_awareness"]["score"], 1, 5))
    if ess:
        dims = ess["self"].get("dimensions") or {}
        for name, construct in (("Emotional", "closeness"), ("Conflict", "repair"),
                                ("Intellectual", "attunement")):
            if name in dims:
                add(construct, "essential", f"{name.lower()} dimension", dims[name], "0–100",
                    _norm(dims[name], 0, 100))
    return out


CONSTRUCT_COPY = {
    "steadiness": {
        "name": "how settled you are",
        "agree": "Two instruments that share no questions put your steadiness in the same place, and both of them "
                 "put it away from the middle — which is what makes the agreement worth printing. For choosing, it "
                 "means the calm you bring is real rather than situational: you can trust your own read of a "
                 "situation instead of borrowing someone else's.",
        "tension": "The two disagree about how settled you actually are. Neither is wrong — general life and close "
                   "relationships run on separate circuitry. The question worth sitting with is which of those two "
                   "versions of you was doing the choosing, last time it mattered.",
    },
    "closeness": {
        "name": "how close you let people get",
        "agree": "Two independent measures land together on how much closeness you allow. That agreement means this "
                 "isn't a mood — it's a setting, and it's the one doing most of your selecting. People who match it "
                 "may read as easy, and people who don't as too much or too little.",
        "tension": "The instruments pull apart on closeness: one finds warmth, the other finds distance. Warmth given "
                   "widely and closeness let all the way in are different capacities, and the first can substitute "
                   "for the second for years without anyone noticing. Including you.",
    },
    "repair": {
        "name": "what you do when it goes wrong",
        "agree": "Both readings agree on how you handle conflict and repair. That's a stable input to your choosing: "
                 "you already know what a difficult conversation costs you, which means you can select for someone "
                 "who can hold one rather than for someone who avoids them.",
        "tension": "One instrument has you handling rupture well; the other doesn't. That gap usually means you can "
                   "manage a conflict in the abstract better than you can stay in one — which quietly shapes who you "
                   "choose: people who don't push.",
    },
    "attunement": {
        "name": "how much you pick up",
        "agree": "Two measures agree on how much you register about other people. Attunement this consistent is a "
                 "genuine advantage while choosing — the caution is that reading people well can make you confident "
                 "early, and confidence early is how the slow-arriving things get missed.",
        "tension": "The instruments disagree about how much you notice. Worth sitting with: is your attunement real "
                   "or reconstructed after the fact — do you see it at the time, or explain it beautifully later?",
    },
    "self_knowledge": {
        "name": "how well you read yourself",
        "agree": "Your self-knowledge reads consistently across instruments, which is the foundation the rest of this "
                 "rests on: choosing well is mostly knowing what you're actually reaching for.",
        "tension": "One reading has your self-knowledge high while another suggests the picture is less settled than "
                   "that. Not a contradiction — self-awareness is easiest to over-rate in exactly the area it's "
                   "thinnest.",
    },
    "self_reliance": {"name": "how much you lean on people", "agree": "", "tension": ""},
}


NULL_COPY = (
    "Neither instrument found a displacement to report here. They agree on that, which is itself a "
    "reading — it means this is not where your selecting is happening."
)


def build_convergences(by: dict, max_items: int = 3) -> list:
    """Where two instruments that share no questions land in the same place, away from the middle.

    Both readings must be displaced from their own midpoint and displaced the same way. Where
    neither is, the honest null is printed instead of a convergence claim. Where only one is, the
    displaced reading is reported on its own — one reading, not two agreeing.
    """
    readings = _readings(by)
    out = []
    seen = set()
    for i, a in enumerate(readings):
        for b in readings[i + 1:]:
            if a["construct"] != b["construct"] or a["instrument"] == b["instrument"]:
                continue
            copy = CONSTRUCT_COPY.get(a["construct"])
            if not copy or not copy["agree"]:
                continue
            distance = abs(a["norm"] - b["norm"])
            if a["construct"] in seen:
                continue
            da, dbb = _displacement(a), _displacement(b)
            n_displaced = sum((_displaced(a), _displaced(b)))
            same_direction = da * dbb > 0
            meta = _tier_and_confidence(by, a["instrument"], b["instrument"])
            quoted = (f"Your {a['label']} reads {a['raw']} ({a['scale']}) and your {b['label']} reads "
                      f"{b['raw']} ({b['scale']})")
            if n_displaced == 0:
                out.append({
                    "id": f"null-{a['construct']}",
                    "kind": "null",
                    "construct": a["construct"],
                    "sources": sorted({INSTRUMENT_LABEL[a["instrument"]], INSTRUMENT_LABEL[b["instrument"]]}),
                    "evidence_tier": meta["evidence_tier"],
                    "confidence": meta["confidence"],
                    "title": f"Nothing to report on {copy['name']}.",
                    "body": f"{quoted} — both close to the middle of their own scale. {NULL_COPY}",
                })
                seen.add(a["construct"])
                continue
            if n_displaced == 1:
                # One displaced, one on its own middle. That is neither agreement nor tension, so
                # the displaced reading is reported alone rather than dressed as convergence.
                one = a if _displaced(a) else b
                which = "high" if _displacement(one) > 0 else "low"
                out.append({
                    "id": f"single-{a['construct']}",
                    "kind": "single",
                    "construct": a["construct"],
                    "sources": [INSTRUMENT_LABEL[one["instrument"]]],
                    "evidence_tier": meta["evidence_tier"],
                    "confidence": meta["confidence"],
                    "title": f"One instrument has something to say about {copy['name']}.",
                    "body": (f"{quoted}. Only one of those clears its own instrument's "
                             f"displacement test, so this is one reading rather than two "
                             f"agreeing: {_test_phrase(one)}, toward the {which} end, while the "
                             f"other instrument found nothing to report here. {meta['caveat']}"),
                })
                seen.add(a["construct"])
                continue
            if not same_direction or abs(da - dbb) > AGREE_GAP_UNITS:
                # Displaced opposite ways, or displaced the same way but by very different
                # amounts. Neither is an agreement; an opposite-facing pair is picked up as a
                # tension instead.
                continue
            direction = "toward the high end" if da > 0 else "toward the low end"
            out.append({
                "id": f"agree-{a['construct']}",
                "kind": "agreement",
                "construct": a["construct"],
                "sources": sorted({INSTRUMENT_LABEL[a["instrument"]], INSTRUMENT_LABEL[b["instrument"]]}),
                "evidence_tier": meta["evidence_tier"],
                "confidence": meta["confidence"],
                "title": f"Both instruments agree on {copy['name']}.",
                "body": (f"{quoted} — {direction} on both, each by the test its own instrument "
                         f"allows: {_test_phrase(a)}, and {_test_phrase(b)}. {copy['agree']} "
                         f"{meta['caveat']}"),
            })
            seen.add(a["construct"])
    return out[:max_items]


def build_tensions(by: dict, existing: list, max_items: int = 4) -> list:
    """Construct-aligned disagreements, added after the hand-written rules."""
    readings = _readings(by)
    out = []
    seen = {f.get("construct") for f in existing if f.get("construct")}
    for i, a in enumerate(readings):
        for b in readings[i + 1:]:
            if a["construct"] != b["construct"] or a["instrument"] == b["instrument"]:
                continue
            copy = CONSTRUCT_COPY.get(a["construct"])
            if not copy or not copy["tension"] or a["construct"] in seen:
                continue
            # A tension needs both readings displaced and displaced in OPPOSITE directions.
            # One instrument away from its middle while the other sits on it is a single finding,
            # not a disagreement between two.
            if not (_displaced(a) and _displaced(b)):
                continue
            if _displacement(a) * _displacement(b) > 0:
                continue
            seen.add(a["construct"])
            hi, lo = (a, b) if a["norm"] > b["norm"] else (b, a)
            meta = _tier_and_confidence(by, a["instrument"], b["instrument"])
            out.append({
                "id": f"tension-{a['construct']}",
                "kind": "tension",
                "construct": a["construct"],
                "sources": sorted({INSTRUMENT_LABEL[a["instrument"]], INSTRUMENT_LABEL[b["instrument"]]}),
                "evidence_tier": meta["evidence_tier"],
                "confidence": meta["confidence"],
                "title": f"The instruments disagree about {copy['name']}.",
                "body": (
                    f"Your {hi['label']} reads {hi['raw']} ({hi['scale']}) while your {lo['label']} reads "
                    f"{lo['raw']} ({lo['scale']}) — displaced in opposite directions, each by the test its own "
                    f"instrument allows: {_test_phrase(hi)}, and {_test_phrase(lo)}. "
                    f"{copy['tension']} {meta['caveat']}"),
            })
    return out[:max_items]


def build_synthesis(by: dict, tensions: list, agreements: list) -> dict | None:
    """The short version: what the completed set says about how this person chooses.

    Every line here inherits the confidence of the instrument it came from. A claim sourced
    entirely from a Low-confidence instrument reading mid-scale is not emitted at all — the
    summary was the one place in the document where a hedge went missing on the way up.
    """
    if len(by) < 2:
        return None
    lines = []
    clo = by.get("MI-AS-36") or by.get("closeness")
    pers, eq, ess = by.get("personality"), by.get("eq"), by.get("essential")

    if ess:
        overall = ess["delta"]["overall"]
        self_tie = ess["self"].get("tie") or {}
        ideal_tie = ess["ideal"].get("tie") or {}
        self_name = (" and ".join(self_tie["names"]) if self_tie.get("tied")
                     else ess["self"]["primary"]["name"])
        ideal_name = (" and ".join(ideal_tie["names"]) if ideal_tie.get("tied")
                      else ess["ideal"]["primary"]["name"])
        if self_name == ideal_name:
            # Not "a moderate gap ... wanting the same thing back": the magnitude band and the
            # argmax match were reaching opposite conclusions in the same paragraph.
            lines.append(
                f"You described the same archetype you read as — {self_name} — but not the same amount of it. "
                f"The distance between the two lenses is {overall} points, so it sits in degree rather than in kind.")
        else:
            shape = ("a wide gap" if overall >= 15 else "a close match" if overall <= 6 else "a moderate gap")
            lines.append(
                f"You choose across {shape} — {overall} points between who you are and who you say you want — and "
                f"you read as {self_name} while describing wanting {ideal_name}.")
    if clo:
        anx = clo["dimensions"]["anxiety"].get("value")
        avo = clo["dimensions"]["avoidance"].get("value")
        conf = (clo.get("confidence") or "").lower()
        # Only where one dial is actually displaced. Two mid-range readings were being converted
        # into a positive claim about what the selection "runs on", and at low confidence.
        if anx is not None and avo is not None and conf != "low":
            if anx >= 4.5:
                lines.append("Up close, the thing your selection actually runs on is responsiveness — how quickly "
                             "someone signals back.")
            elif avo >= 4.5:
                lines.append("Up close, the thing your selection actually runs on is room — how little someone asks "
                             "of you.")
    if pers:
        # Furthest from the reader's own middle, on the absolute points-of-scale floor, and
        # recomputed here rather than read from the stored `loudest` — that field was written
        # under the retired sten floor.
        named = loudest_entries(pers["factor_scores"])
        highs = [e["name"].lower() for e in named if e["deviation"] > 0]
        lows = [e["name"].lower() for e in named if e["deviation"] < 0]
        # The instrument is named, because the Essential section answers the same question from
        # different evidence and the reader was being handed two answers with no way to tell why.
        if highs and lows:
            lines.append(
                f"On the Personality Mirror, the trait doing most of the noticing is {highs[0]}; the one you're most "
                f"likely to look for in someone else is {lows[0]}.")
        elif highs:
            lines.append(f"On the Personality Mirror, the trait doing most of the noticing is {highs[0]}.")
        elif lows:
            lines.append(f"On the Personality Mirror, the trait you're most likely to look for in someone else is "
                         f"{lows[0]}.")
        else:
            lines.append(
                "No single trait sits far enough from your own middle to be doing most of the noticing — an even "
                "profile, which spreads the selection pressure rather than concentrating it.")
    if eq:
        # Gated on the minimum reportable difference: the four domains span a third of a point on
        # a 1-5 scale often enough that "your weakest" is an ordering of measurement error.
        named = ei_named(eq["domain_scores"])
        if named["lowest"]:
            low = named["lowest"]
            lines.append(
                f"And the information most likely to reach you late is whatever {low['name'].lower()} would have "
                f"caught ({low['score']:.2f} of 5) — usually after the decision, not before it.")
        else:
            lines.append(
                f"Your four emotional-intelligence domains sit too close together to name one as the gap — the "
                f"widest difference between any two is {named['spread']:.2f} against a floor of "
                f"{named['mrd']:.1f} — which is itself worth knowing: there is no single capacity to shore up here.")

    if not lines:
        return None
    counts = f"{len([a for a in agreements if a.get('kind') == 'agreement'])} agreement(s), " \
             f"{len(tensions)} tension(s) and " \
             f"{len([a for a in agreements if a.get('kind') == 'null'])} place(s) where neither instrument " \
             f"found a displacement to report"
    return {
        "title": "How you choose — the short version",
        "body": " ".join(lines),
        "footnote": (
            f"Assembled from {len(by)} completed instruments: {counts}. Every sentence above is about you; none of it "
            "is a claim about anyone you might meet, and none of it predicts an outcome."),
    }

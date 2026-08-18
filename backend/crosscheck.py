"""The cross-check — agreements as signal, disagreements as findings.

Two jobs. First, the hand-written tension rules (kept verbatim from the original build).
Second, a construct-aligned comparison that always has something honest to say when two or
more instruments overlap: where two independent measures of the same underlying thing land
in the same place, that convergence is signal and is worth printing.

Everything here is derived at read time from stored snapshots. No rescoring, no invented
numbers: every statement quotes the two values it is comparing.
"""

AGREE_BAND = 0.14   # normalised distance under which two measures count as converging
TENSION_BAND = 0.30  # over which they count as pulling against each other

INSTRUMENT_LABEL = {
    "essential": "Essential Mirror",
    "MI-AS-36": "Closeness Mirror",
    "personality": "Personality Mirror",
    "eq": "EI Mirror",
}


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

    def add(construct, instrument, label, raw, scale, norm):
        if norm is not None:
            out.append({"construct": construct, "instrument": instrument, "label": label,
                        "raw": raw, "scale": scale, "norm": norm})

    if clo:
        anx = clo["dimensions"]["anxiety"]
        avo = clo["dimensions"]["avoidance"]
        if anx.get("status") == "scored":
            add("steadiness", "MI-AS-36", "settledness in closeness", anx["value"], "1–7 reassurance",
                1 - _norm(anx["value"], 1, 7))
        if avo.get("status") == "scored":
            add("closeness", "MI-AS-36", "ease with closeness", avo["value"], "1–7 distance",
                1 - _norm(avo["value"], 1, 7))
    if pers:
        f = pers["factor_scores"]
        if "C" in f:
            add("steadiness", "personality", "emotional stability", f["C"]["sten"], "1–10 sten",
                _norm(f["C"]["sten"], 1, 10))
        if "A" in f:
            add("closeness", "personality", "warmth", f["A"]["sten"], "1–10 sten", _norm(f["A"]["sten"], 1, 10))
        if "Q2" in f:
            add("self_reliance", "personality", "self-reliance", f["Q2"]["sten"], "1–10 sten",
                _norm(f["Q2"]["sten"], 1, 10))
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
        "agree": "Two instruments that share no questions put your steadiness in the same place. That convergence is "
                 "the most reliable thing in this document — when independent measures agree, the reading is doing "
                 "its job. For choosing, it means the calm you bring is real rather than situational: you can trust "
                 "your own read of a situation instead of borrowing someone else's.",
        "tension": "The two disagree about how settled you actually are. Neither is wrong — general life and close "
                   "relationships run on separate circuitry. The question worth sitting with is which of those two "
                   "versions of you was doing the choosing, last time it mattered.",
    },
    "closeness": {
        "name": "how close you let people get",
        "agree": "Two independent measures land together on how much closeness you allow. That agreement means this "
                 "isn't a mood — it's a setting, and it's the one doing most of your selecting. You'll consistently "
                 "read people who match it as easy, and people who don't as too much or too little.",
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


def build_convergences(by: dict, max_items: int = 3) -> list:
    """Where two instruments that share no questions land in the same place."""
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
            if distance > AGREE_BAND or a["construct"] in seen:
                continue
            seen.add(a["construct"])
            high = a["norm"] >= 0.6
            low = a["norm"] <= 0.4
            direction = "toward the high end" if high else ("toward the low end" if low else "around the middle")
            out.append({
                "id": f"agree-{a['construct']}",
                "kind": "agreement",
                "sources": sorted({INSTRUMENT_LABEL[a["instrument"]], INSTRUMENT_LABEL[b["instrument"]]}),
                "title": f"Both instruments agree on {copy['name']}.",
                "body": (
                    f"Your {a['label']} reads {a['raw']} ({a['scale']}) and your {b['label']} reads {b['raw']} "
                    f"({b['scale']}) — {direction} on both. {copy['agree']}"),
            })
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
            if abs(a["norm"] - b["norm"]) < TENSION_BAND:
                continue
            seen.add(a["construct"])
            hi, lo = (a, b) if a["norm"] > b["norm"] else (b, a)
            out.append({
                "id": f"tension-{a['construct']}",
                "kind": "tension",
                "construct": a["construct"],
                "sources": sorted({INSTRUMENT_LABEL[a["instrument"]], INSTRUMENT_LABEL[b["instrument"]]}),
                "title": f"The instruments disagree about {copy['name']}.",
                "body": (
                    f"Your {hi['label']} reads {hi['raw']} ({hi['scale']}) while your {lo['label']} reads "
                    f"{lo['raw']} ({lo['scale']}). {copy['tension']}"),
            })
    return out[:max_items]


def build_synthesis(by: dict, tensions: list, agreements: list) -> dict | None:
    """The short version: what the completed set says about how this person chooses."""
    if len(by) < 2:
        return None
    lines = []
    clo = by.get("MI-AS-36") or by.get("closeness")
    pers, eq, ess = by.get("personality"), by.get("eq"), by.get("essential")

    if ess:
        overall = ess["delta"]["overall"]
        shape = ("a wide gap" if overall >= 15 else "a close match" if overall <= 6 else "a moderate gap")
        self_name = ess["self"]["primary"]["name"]
        ideal_name = ess["ideal"]["primary"]["name"]
        pairing = (
            f"you read as {self_name} and you describe wanting the same thing back"
            if self_name == ideal_name
            else f"you read as {self_name} while describing wanting {ideal_name}"
        )
        lines.append(
            f"You choose across {shape} — {overall} points between who you are and who you say you want — and "
            f"{pairing}.")
    if clo:
        anx = clo["dimensions"]["anxiety"].get("value")
        avo = clo["dimensions"]["avoidance"].get("value")
        if anx is not None and avo is not None:
            driver = ("responsiveness — how quickly someone signals back"
                      if anx >= 4.5 else "room — how little someone asks of you"
                      if avo >= 4.5 else "recognition rather than reassurance")
            lines.append(f"Up close, the thing your selection actually runs on is {driver}.")
    if pers:
        ranked = sorted(pers["factor_scores"].values(), key=lambda f: -f["sten"])
        top = ranked[0]
        bottom = ranked[-1]
        lines.append(
            f"The trait doing most of the noticing is {top['name'].lower()} ({top['sten']} of 10); the one you're "
            f"most likely to look for in someone else is {bottom['name'].lower()} ({bottom['sten']} of 10).")
    if eq:
        worst = sorted(eq["domain_scores"].values(), key=lambda d: d["score"])[0]
        lines.append(
            f"And the information most likely to reach you late is whatever {worst['name'].lower()} would have "
            f"caught ({worst['score']} of 5) — usually after the decision, not before it.")

    if not lines:
        return None
    counts = f"{len(agreements)} agreement{'s' if len(agreements) != 1 else ''} and " \
             f"{len(tensions)} tension{'s' if len(tensions) != 1 else ''}"
    return {
        "title": "How you choose — the short version",
        "body": " ".join(lines),
        "footnote": (
            f"Assembled from {len(by)} completed instruments: {counts}. Every sentence above is about you; none of it "
            "is a claim about anyone you might meet, and none of it predicts an outcome."),
    }

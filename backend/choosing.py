"""How you choose — the translation layer.

RatherKnow is a study of how you choose. Each instrument measures something real; this
module turns those stored numbers into statements about *selection behaviour* — what you
reach for, what you excuse, what you'll read as a red flag and what you'll read as depth.

Derived at read time from the immutable snapshot. It never rescores, never labels, and
never says anything about another person — only about the reader's own choosing.
"""

from services.within_person import loudest

CHOOSING_LEAD = {
    "essential": "What the gap between your two lenses does at the point of choosing.",
    "MI-AS-36": "How these two settings behave when you're deciding whether to stay interested.",
    "personality": "Which of your own traits does the selecting — and what it selects for.",
    "eq": "What you notice, and what you miss, while you're choosing.",
    "MI-EV-49": "Where your daily friction is likely to sit — and which of it you'd actually defend.",
}

CLOSING = (
    "None of this is a verdict, and none of it is about anyone but you. It's a description of "
    "the mechanism you choose with — which is the only part of the process you control."
)


def _pt(title, body):
    return {"title": title, "body": body}


def _lens_name(lens: dict, primary: dict) -> str:
    """Both names where the top two sit inside the tie margin — the reading declines to rank
    them, so the prose must not quietly rank them anyway."""
    tie = lens.get("tie") or {}
    if tie.get("tied"):
        return f"{tie['names'][0]} and {tie['names'][1]}"
    return primary["name"]


def _essential(r):
    delta = r["delta"]
    scores = r["self"]["archetype_scores"]
    self_p, ideal_p = r["self"]["primary"], r["ideal"]["primary"]
    per = delta["per_archetype"]
    wants_more = sorted([(k, v) for k, v in per.items() if v > 0], key=lambda kv: -kv[1])
    already_is = sorted([(k, v) for k, v in per.items() if v < 0], key=lambda kv: kv[1])
    points = []

    if wants_more:
        k, v = wants_more[0]
        points.append(_pt(
            f"You select for what {scores[k]['name']} brings — and you don't carry it yourself.",
            f"Your stated want runs {v} points higher than your own score there. At the point of choosing, that "
            "shows up as disproportionate weight on evidence of this one quality — you'll notice it fast, rate it "
            "highly, and forgive a good deal elsewhere to keep it. Useful to know before the third date, not after."))
    if already_is:
        k, v = already_is[0]
        points.append(_pt(
            f"You quietly discount what {scores[k]['name']} brings — the thing you already are.",
            f"You score {abs(v)} points higher on this than the partner you describe. People tend to under-value "
            "what comes free to them, so this is the quality you're most likely to overlook in someone else, or to "
            "treat as ordinary when it's actually the fit."))

    overall = delta["overall"]
    if overall >= 15:
        points.append(_pt(
            "You're choosing across a wide gap, which raises the translation cost.",
            f"An average distance of {overall} points between your two lenses means the partner you describe is "
            "meaningfully unlike you. That can work deliberately — one brings the calm, the other brings the weather "
            "— but it means more of your choosing energy goes on difference and less on recognition. Worth deciding "
            "on purpose rather than by pull."))
    elif overall <= 6:
        points.append(_pt(
            "You're choosing close to home.",
            f"Only {overall} points separate who you are from who you say you want. Low friction, high recognition — "
            "and worth one question: are you selecting a companion, or selecting to be agreed with?"))
    else:
        points.append(_pt(
            "You're choosing a complement rather than a copy.",
            f"A moderate distance of {overall} points, concentrated in a couple of places. The work is naming which "
            "of those differences you actually want daily, and which you only want to admire."))

    shadow = r.get("shadow")
    if shadow:
        points.append(_pt(
            f"The pull you'll misread as chemistry: {shadow['name']}.",
            f"{shadow.get('warning', '')} This is the part of choosing that doesn't announce itself — it arrives as "
            "intensity around week six, not as a decision. Knowing its name is most of the defence."))

    points.append(_pt(
        "The two lenses were you both times.",
        f"You read as {_lens_name(r['self'], self_p)}, and you described {_lens_name(r['ideal'], ideal_p)}. Both "
        "sets of answers came from you, which is why this is a study of how you choose rather than a verdict on "
        "who's available."))

    ideal_key = ideal_p.get("key")
    if ideal_key and abs(per.get(ideal_key, 1)) < 1:
        points.append(_pt(
            f"You named {scores[ideal_key]['name']} as the partner you want — and you already score there.",
            f"The gap on this one is {per[ideal_key]}, which reads like a contradiction and isn't. The archetype "
            "you named is simply the highest score in that lens; the gap measures the distance between the two "
            "lenses. Both can be true at once, and together they say something specific: you are describing "
            "someone who carries about as much of this as you do. Not a complement — a match on the quality you "
            "lead with. That may mean recognition, and it may mean you both bring the same blind spot."))
    return points


def _closeness(r):
    dims = r["dimensions"]
    anx = dims["anxiety"].get("value") if dims["anxiety"].get("status") == "scored" else None
    avo = dims["avoidance"].get("value") if dims["avoidance"].get("status") == "scored" else None
    points = []

    if anx is not None:
        if anx >= 5:
            points.append(_pt(
                "You choose partly on responsiveness.",
                f"Reassurance sits at {anx} of 7. In practice that means speed of reply, warmth of tone and "
                "consistency of signal do a lot of your early selecting — and someone slow to reassure can read as "
                "uninterested when they're only slow. The risk isn't wanting reassurance; it's mistaking a steady "
                "person for a cold one."))
        elif anx <= 3:
            points.append(_pt(
                "You don't need much signal to keep choosing someone.",
                f"Reassurance sits at {anx} of 7 — you're not scanning for evidence that things are all right. That "
                "makes you easy to be with, and it also means you can stay in something under-fed for a "
                "long time without registering it as a problem."))
        else:
            points.append(_pt(
                "Reassurance isn't driving your choosing.",
                f"At {anx} of 7 you sit around the middle: you notice silence, you don't spiral in it. Whatever is "
                "steering your selection, this isn't the main lever."))

    if avo is not None:
        ease = round(8 - avo, 1)
        if avo >= 5:
            points.append(_pt(
                "You choose people who don't ask for much closeness at first.",
                f"Closeness itself sits further away for you ({avo} of 7 on distance). At the point of choosing, that "
                "tends to select for independence and low demand — qualities you'll describe as respectful of space. "
                "Worth checking whether you're choosing for compatibility or for room."))
        elif avo <= 3:
            points.append(_pt(
                "Closeness comes easily, so the deciding tends to happen early.",
                f"Distance reads low ({avo} of 7; ease {ease}). You let people in quickly, which means your choosing "
                "happens early — often before there's much evidence in. The information usually arrives later than "
                "your decision does."))
        else:
            points.append(_pt(
                "Closeness is neither the pull nor the brake.",
                f"At {avo} of 7 you sit mid-range on distance — intimacy is work sometimes and easy other times, "
                "which means it isn't the thing making your choices for you."))

    confidence = r.get("confidence")
    if confidence and confidence != "high":
        points.append(_pt(
            "Read this at the confidence it earned.",
            f"The validity checks put this reading at {confidence} confidence. Treat the direction as informative and "
            "the exact figures as provisional — and take it again when you have more patience for it."))
    return points


def _personality(r):
    """Selection is within-profile, and no sten reaches the reader.

    This used to pick on sten >= 7 / <= 4 and print "At 7 of 10 …". Both were leftovers of the
    population layer: a fixed sten threshold says "high compared with other people", and an
    x-of-10 invites the reader to read a bidirectional trait as a mark out of ten.
    """
    factors = r["factor_scores"]
    picked = loudest({k: f["sten"] for k, f in factors.items()})
    high = [factors[k] for k, d in picked["named"] if d > 0]
    low = [factors[k] for k, d in picked["named"] if d < 0]
    points = []

    for f in high:
        points.append(_pt(
            f"{f['name']} does a lot of your selecting.",
            f"You sit toward {f['pole_high'].lower()}, and further that way than most of your own profile. Traits "
            "this far from your own middle don't sit quietly — they set what you notice first in someone and what "
            f"you'll read as a dealbreaker. This may show up as over-weighting evidence of {f['pole_high'].lower()}, "
            "and as feeling the absence of it quickly."))
    for f in low:
        points.append(_pt(
            f"{f['name']} is where you'll shop for a partner to compensate.",
            f"You sit toward {f['pole_low'].lower()}, and further that way than most of your own profile. People "
            "commonly outsource the ends they sit furthest from: this is the trait you're most likely to find "
            f"magnetic in someone else, and most likely to resent later when {f['pole_high'].lower()} starts "
            "arriving as pressure rather than relief."))
    if not high and not low:
        points.append(_pt(
            "No single trait is driving your choosing.",
            "Your factors sit close to your own middle across the board, which means selection pressure is spread "
            "rather than concentrated, and no one trait is doing the choosing. Read the Closeness and Essential Mirrors for the lever this one didn't find."))

    sd = (r.get("validity") or {}).get("social_desirability", {})
    if sd.get("flag") == "HIGH":
        points.append(_pt(
            "One caveat about this reading.",
            "The validity check counts how many of the ten most flattering statements you agreed with, and you agreed "
            "with most of them. That doesn't "
            "invalidate the profile, but it does mean the version of you that answered may be the version you'd "
            "choose to be. Choosing is done by the ordinary-day version."))
    return points


def _eq(r):
    domains = sorted(r["domain_scores"].values(), key=lambda d: -d["score"])
    best, worst = domains[0], domains[-1]
    subs = sorted(r["sub_scores"].values(), key=lambda s: s["score"])
    points = [
        _pt(
            f"{best['name']} is your strongest instrument while choosing.",
            f"At {best['score']} of 5 this is the capacity most available to you when you're deciding about someone. "
            "It's also the one you'll trust too far — a strength used as a substitute for the others is how confident "
            "misreadings happen."),
        _pt(
            f"{worst['name']} is where your choosing loses information.",
            f"At {worst['score']} of 5 this is the thinnest of the four. Whatever this domain would normally catch — "
            "the pause, the pattern, the thing said sideways — is more likely to reach you late, which usually means "
            "after you've already decided."),
    ]
    if subs:
        s = subs[0]
        points.append(_pt(
            f"The narrowest capacity: {s['name'].lower()}.",
            f"{s['score']} of 5. Sub-dimensions this low tend to show up as a specific blind spot rather than a "
            "general weakness — worth watching for in the first month, when there's still a decision left to make."))
    overall = r.get("overall_score")
    if overall is not None and overall >= 4.0:
        points.append(_pt(
            "A high read is not the same as good choosing.",
            f"An overall of {overall} of 5 says you believe you handle feeling well — and this is a self-perception "
            "read, not an ability test. People who regulate well can stay in the wrong thing longer, precisely "
            "because they cope with it."))
    return points


def _everyday(r):
    """Position x priority. The valuable half is priority: what you'd actually defend."""
    positions = r["positions"]
    priority = r["priority"]
    cells: dict = {}
    for c in r["map"]:
        cells.setdefault(c["cell"], []).append(c)
    points = []

    for c in cells.get("non_negotiable", [])[:1]:
        points.append(_pt(
            f"{c['name']} is a genuine line, not a preference.",
            f"You sit {c['label']} on it, and you ranked it {_ordinal(c['priority_rank'])} of seven for what you'd "
            "need to agree on. Strong feeling plus high priority is the combination that produces a real "
            "non-negotiable — worth naming out loud early, because it won't negotiate itself later."))

    for c in cells.get("strong_but_tradeable", [])[:1]:
        points.append(_pt(
            f"{c['name']} is a strong preference you'd trade.",
            f"You sit {c['label']} here — as far from the middle as the instrument goes — and yet you ranked it "
            f"{_ordinal(c['priority_rank'])} of seven for needing agreement. That combination usually surprises "
            "people. It's the difference between what you feel strongly and what you'd defend, and it's the most "
            "useful thing on this page."))

    for c in cells.get("needs_settling", [])[:1]:
        points.append(_pt(
            f"On {c['name'].lower()} you're not fussy where it lands — only that it lands.",
            f"Your position is {c['label']}, but it ranks {_ordinal(c['priority_rank'])} of seven for needing "
            "agreement. That reads as: decide it, and I'll live with the answer. Left undecided, this is the kind "
            "of thing that gets re-litigated every few weeks."))

    top = priority[0] if priority else None
    bottom = priority[-1] if priority else None
    if top and bottom and not top["tied"]:
        points.append(_pt(
            "What you'd protect, and what you'd let go.",
            f"Across twenty-one either/ors, {top['descriptor']} won most often and {bottom['descriptor']} won "
            f"least. Neither is a virtue. It's a ranking of your own choices against each other — the order you'd "
            "spend agreement on if you couldn't have all of it, which is the actual situation."))
    elif top:
        tied_names = ", ".join(p["name"] for p in priority if p["wins"] == top["wins"])
        points.append(_pt(
            "Nothing came out clearly on top.",
            f"{tied_names} finished level across the twenty-one comparisons, which means no single thing is the one "
            "you'd defend first. That is a real answer rather than a missing one: your priorities are spread, so "
            "friction is more likely to arrive from whatever is loudest that week than from one standing line. "
            "The positions in the first half still hold."))

    undiff = r["validity"].get("undifferentiated_domains") or []
    if undiff:
        names = ", ".join(positions[d]["name"] for d in undiff)
        points.append(_pt(
            f"No position recorded on {names}.",
            "Your four answers split evenly, so there's nothing to report — and that is not the same as sitting in "
            "the middle. One says the questions didn't separate you; the other would claim a measurement we don't "
            "have. Reported as undifferentiated rather than invented."))

    zeta = r["validity"].get("zeta")
    if zeta is not None and zeta < 0.70:
        points.append(_pt(
            "Read the ranking as provisional.",
            f"Your comparisons contain enough loops — preferring A to B, B to C, and C back to A — that the "
            f"consistency index came out at {zeta}. That happens when the trade-offs are genuinely close, and it "
            "means the order above is softer than it looks. The positions in the first half are unaffected."))
    return points


def _ordinal(n):
    return {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh"}.get(n, str(n))


BUILDERS = {"essential": _essential, "MI-AS-36": _closeness, "personality": _personality,
            "eq": _eq, "MI-EV-49": _everyday}


def build_choosing(result: dict) -> dict | None:
    instrument = result.get("instrument")
    builder = BUILDERS.get(instrument)
    if not builder:
        return None
    try:
        points = builder(result)
    except (KeyError, TypeError, IndexError):
        return None
    if not points:
        return None
    return {
        "instrument": instrument,
        "lead": CHOOSING_LEAD[instrument],
        "points": _dedupe(points)[:5],
        "closing": CLOSING,
    }


def _dedupe(points: list) -> list:
    """No canned string renders twice in one document (PRD §8.1). Boilerplate that repeats
    verbatim reveals itself as boilerplate, so the second occurrence is dropped."""
    seen, out = set(), []
    for p in points:
        body = p.get("body", "").strip()
        if body and body in seen:
            continue
        seen.add(body)
        out.append(p)
    return out

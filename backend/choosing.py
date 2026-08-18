"""How you choose — the translation layer.

RatherKnow is a study of how you choose. Each instrument measures something real; this
module turns those stored numbers into statements about *selection behaviour* — what you
reach for, what you excuse, what you'll read as a red flag and what you'll read as depth.

Derived at read time from the immutable snapshot. It never rescores, never labels, and
never says anything about another person — only about the reader's own choosing.
"""

CHOOSING_LEAD = {
    "essential": "What the gap between your two lenses does at the point of choosing.",
    "MI-AS-36": "How these two settings behave when you're deciding whether to stay interested.",
    "personality": "Which of your own traits does the selecting — and what it selects for.",
    "eq": "What you notice, and what you miss, while you're choosing.",
}

CLOSING = (
    "None of this is a verdict, and none of it is about anyone but you. It's a description of "
    "the mechanism you choose with — which is the only part of the process you control."
)


def _pt(title, body):
    return {"title": title, "body": body}


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
        f"You read as {self_p['name']}, and you described {ideal_p['name']}. Both sets of answers came from you, "
        "which is why this is a study of how you choose rather than a verdict on who's available."))
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
                "makes you unusually easy to be with, and it also means you can stay in something under-fed for a "
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
                "Closeness comes easily, so you commit early.",
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
    factors = r["factor_scores"]
    ranked = sorted(factors.values(), key=lambda f: -f["sten"])
    high = [f for f in ranked if f["sten"] >= 7][:2]
    low = [f for f in ranked if f["sten"] <= 4][-2:]
    points = []

    for f in high:
        points.append(_pt(
            f"{f['name']} does a lot of your selecting.",
            f"At {f['sten']} of 10 you sit clearly toward {f['pole_high'].lower()}. Traits this far from the middle "
            "don't sit quietly — they set what you notice first in someone and what you'll read as a dealbreaker. "
            f"Expect to over-weight evidence of {f['pole_high'].lower()}, and to feel the absence of it quickly."))
    for f in low:
        points.append(_pt(
            f"{f['name']} is where you'll shop for a partner to compensate.",
            f"At {f['sten']} of 10 you sit toward {f['pole_low'].lower()}. People commonly outsource their low "
            "factors: this is the trait you're most likely to find magnetic in someone else, and most likely to "
            f"resent later when {f['pole_high'].lower()} starts arriving as pressure rather than relief."))
    if not high and not low:
        points.append(_pt(
            "No single trait is driving your choosing.",
            "Your factors sit close to the middle across the board, which means selection pressure is spread rather "
            "than concentrated. Read the Closeness and Essential Mirrors for the lever this one didn't find."))

    sd = (r.get("validity") or {}).get("social_desirability", {})
    if sd.get("flag") == "HIGH":
        points.append(_pt(
            "One caveat about this reading.",
            "The validity check noticed an unusually high level of agreement with flattering statements. That doesn't "
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


BUILDERS = {"essential": _essential, "MI-AS-36": _closeness, "personality": _personality, "eq": _eq}


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
        "points": points[:5],
        "closing": CLOSING,
    }

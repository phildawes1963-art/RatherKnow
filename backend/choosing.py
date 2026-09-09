"""How you choose — the translation layer.

RatherKnow is a study of how you choose. Each instrument measures something real; this
module turns those stored numbers into statements about *selection behaviour* — what you
reach for, what you excuse, what you'll read as a red flag and what you'll read as depth.

Derived at read time from the immutable snapshot. It never rescores, never labels, and
never says anything about another person — only about the reader's own choosing.
"""

from services.reportable import ei_named
from services.factor_pct import loudest_entries

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
            f"Your stated want runs {v:g} points higher than your own score there. At the point of choosing, that "
            "shows up as disproportionate weight on evidence of this one quality — you'll notice it fast, rate it "
            "highly, and forgive a good deal elsewhere to keep it. Useful to know before the third date, not after."))
    if already_is:
        k, v = already_is[0]
        points.append(_pt(
            f"You quietly discount what {scores[k]['name']} brings — the thing you already are.",
            f"You score {abs(v):g} points higher on this than the partner you describe. People tend to under-value "
            "what comes free to them, so this is the quality you're most likely to overlook in someone else, or to "
            "treat as ordinary when it's actually the fit."))

    overall = delta["overall"]
    same_archetype = _lens_name(r["self"], self_p) == _lens_name(r["ideal"], ideal_p)
    if same_archetype:
        # The magnitude band and the argmax match were reaching opposite conclusions in the same
        # section — "wanting the same thing back" against "a complement rather than a copy".
        # Where both lenses name the same pattern, the distance is in degree, not in kind.
        widest = scores[delta["biggest"]]["name"]
        points.append(_pt(
            "You described the same archetype you read as — but not the same amount of it.",
            f"Both lenses lead with the same pattern, so the distance of {overall:g} points between them is a "
            f"matter of degree rather than kind. It sits mostly in {widest}. What that asks is not whether you want someone "
            "unlike you, but how much more of your own leading quality you are hoping to be met with."))
    elif overall >= 15:
        points.append(_pt(
            "You're choosing across a wide gap, which raises the translation cost.",
            f"An average distance of {overall:g} points between your two lenses means the partner you describe is "
            "meaningfully unlike you. That can work deliberately — one brings the calm, the other brings the weather "
            "— but it means more of your choosing energy goes on difference and less on recognition. Worth deciding "
            "on purpose rather than by pull."))
    elif overall <= 6:
        points.append(_pt(
            "You're choosing close to home.",
            f"Only {overall:g} points separate who you are from who you say you want. Low friction, high recognition — "
            "and worth one question: are you selecting a companion, or selecting to be agreed with?"))
    else:
        points.append(_pt(
            "You're choosing a complement rather than a copy.",
            f"A moderate distance of {overall:g} points, concentrated in a couple of places. The work is naming which "
            "of those differences you actually want daily, and which you only want to admire."))

    shadow = r.get("shadow")
    if shadow:
        points.append(_pt(
            f"The pull you'll misread as chemistry: {shadow['name']}.",
            f"{shadow.get('warning', '')} This is the part of choosing that doesn't announce itself — it arrives as "
            "intensity rather than as a decision. Knowing its name is most of the defence."))

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
    """Selection is within-profile, on an absolute floor, and no sten reaches the reader.

    This used to pick on sten >= 7 / <= 4 and print "At 7 of 10 …". Both were leftovers of the
    population layer: a fixed sten threshold says "high compared with other people", and an
    x-of-10 invites the reader to read a bidirectional trait as a mark out of ten. It now picks on
    distance from the reader's own profile average, against an absolute floor in points of scale —
    absolute, so a flat profile names nothing rather than always producing a winner.
    """
    factors = r["factor_scores"]
    named = loudest_entries(factors)
    high = [factors[e["factor"]] for e in named if e["deviation"] > 0]
    low = [factors[e["factor"]] for e in named if e["deviation"] < 0]
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
            "commonly outsource the ends they sit furthest from: what you are short of tends to be what registers "
            f"hardest in someone else. Whether {f['pole_high'].lower()} then stays valuable or starts arriving as "
            "pressure is not something this measures."))
    if not high and not low:
        points.append(_pt(
            "No single trait is driving your choosing.",
            "Your factors sit close to your own middle across the board, which means selection pressure is spread "
            "rather than concentrated, and no one trait is doing the choosing. Read the Closeness and Essential Mirrors for the lever this one didn't find."))
    elif len(high) + len(low) < 2:
        # The 2–5 contract, and a real finding: one trait clearing the floor is a flatter profile
        # than the copy above it implies, and the reader should be told which it is.
        points.append(_pt(
            "Only one trait sits far enough out to be doing the selecting.",
            "The rest of your profile sits close to your own middle, so selection pressure is concentrated in one "
            "place rather than spread across several. That makes the trait above the load-bearing one: satisfy it "
            "and a good deal elsewhere tends to get forgiven, because the other fourteen factors are not arguing "
            "back."))

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
    # Named only where the difference clears the minimum reportable difference against the domain
    # next to it. The four domains routinely span a third of a point on a 1-5 scale, and "your
    # strongest" computed off that is an ordering of measurement error. Sub-dimensions get no
    # highest or lowest at all until the bank's reliability is measured — shorter scales, larger
    # floor, quite possibly larger than the whole usable spread.
    named = ei_named(r["domain_scores"])
    points = []
    if named["highest"]:
        best = named["highest"]
        points.append(_pt(
            f"{best['name']} is your strongest instrument while choosing.",
            f"At {best['score']:.2f} of 5 it sits {best['margin']:.2f} clear of the next domain — far enough apart to "
            "be read as a difference. It's the capacity most available to you when you're deciding about someone, "
            "and the one you'll trust too far: a strength used as a substitute for the others is how confident "
            "misreadings happen."))
    if named["lowest"]:
        worst = named["lowest"]
        points.append(_pt(
            f"{worst['name']} is where your choosing loses information.",
            f"At {worst['score']:.2f} of 5 it sits {worst['margin']:.2f} below the next domain up. Whatever this "
            "domain would normally catch — the pause, the pattern, the thing said sideways — is more likely to reach "
            "you late, which usually means after you've already decided."))
    if not points:
        points.append(_pt(
            "No single emotional capacity is doing most of the work.",
            f"The widest gap between any two of your four domains is {named['spread']:.2f} on the 1–5 scale, and "
            f"the smallest gap this instrument can resolve is {named['mrd']:.1f}. Naming a strongest or a weakest "
            "from that would be ranking measurement error. What it tells you instead is real: there is no one "
            "capacity to lean on here, and none to shore up first."))
    overall = r.get("overall_score")
    if overall is not None and overall >= 4.0:
        points.append(_pt(
            "A high read is not the same as good choosing.",
            f"An overall of {overall:.2f} of 5 says you believe you handle feeling well — and this is a self-perception "
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
            f"consistency index came out at {zeta:g} — on a 0–1 scale where 1 means no circular preferences at all, "
            "and below about 0.70 is where the ranking softens. A couple of loops in twenty-one forced choices is "
            "ordinary; this is more than that, and it usually means the trade-offs are genuinely close. The "
            "positions in the first half are unaffected."))
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

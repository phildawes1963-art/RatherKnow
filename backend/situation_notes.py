"""Situation framing for the printable report — mirrors the on-screen lens.

Framing only: the numbers are identical whatever situation the reader is in.
Kept server-side so the PDF never depends on the client for its wording.
"""

SITUATION_PDF_NOTES = {
    "single_dating": {
        "label": "Single & dating",
        "essential": "You’re reading this with the next person still theoretical, which is the most useful moment there is. Treat the gap below as a prediction rather than a post-mortem: it says which qualities you’ll over-weight on a third date, and which you’ll forgive too quickly.",
        "MI-AS-36": "Where you sit on these two axes is what the early weeks tend to feel like from the inside — how quickly you need a signal back, and how long it takes before closeness stops being work.",
        "personality": "Use this as a filter on your own story rather than on other people. The factors furthest from the middle are the ones you’ll notice missing in a partner within a month.",
        "eq": "These are the capacities that decide how the early months go once novelty stops carrying the conversation.",
    },
    "in_relationship": {
        "label": "In a relationship",
        "essential": "One caution first: nothing here is a scorecard on your partner, and this instrument never asked about them. Where your two lenses diverge is usually where the same argument keeps restarting — which makes it something to say out loud rather than something to conclude.",
        "MI-AS-36": "These dimensions are answered about relationships in general, so a single relationship can sit somewhere quite different. Read it as the default you bring into the room.",
        "personality": "The useful move isn’t comparison. It’s noticing which of your own factors your relationship is currently asking you to suppress, and whether that’s a season or a habit.",
        "eq": "Relationship management does the most work once two people are already committed. Read your lowest domain as the skill your relationship is most likely paying for.",
    },
    "post_breakup": {
        "label": "Post-breakup",
        "essential": "The window after an ending is short, and clearer than it will feel in six months. Read the gap below as what keeps being true across relationships, not as evidence about the one that just ended. Some endings are pattern; some are only timing, and no instrument can tell those apart for you.",
        "MI-AS-36": "Right after an ending both dimensions can read more extreme than your settled position — reassurance especially. That doesn’t make it wrong; it makes it worth taking again in a few months and comparing.",
        "personality": "This is the steadiest thing here: personality moves very little with a breakup, so use it as ground rather than as explanation.",
        "eq": "Self-management usually takes the hit in the weeks after an ending. Read a low domain as a state you’re in rather than a trait you have.",
    },
}


def situation_note(situation: str | None, instrument: str) -> str | None:
    block = SITUATION_PDF_NOTES.get(situation or "")
    if not block:
        return None
    note = block.get(instrument)
    return f"{block['label']} — {note}" if note else None

"""No stored snapshot at the current display_version may carry banned reader-facing copy.

This is the class of defect iteration 13 found: DISPLAY_VERSION was bumped before the copy fix
landed, so snapshots written in between froze the pre-fix wording — and snapshots are write-once,
so the wording could not be corrected in place. The version bump is the fix; this test is what
catches it next time, before a reader does.

Delivered snapshots at OLDER versions are deliberately not checked. They are a record of what was
said at the time, they are never re-rendered, and the methodology page accounts for them.
"""
import asyncio
import os
import re

from motor.motor_asyncio import AsyncIOMotorClient

from services.display import DISPLAY_VERSION

# Patterns, not substrings: "A moderate distance of 10.0 points" is the Essential Delta and is
# correct, as are the EI means ("4.2 of 5") and the item count ("2 of the 10 most flattering
# statements"). What must never appear is a sten presented as a mark out of ten.
BANNED_PATTERNS = (
    r"\bAt \d+ of 10\b",
    r"\(\d+ of 10\)",
    r"\bsten \d+\b",
)
BANNED_TERMS = ("population middle", "calibrated norm", "Very High", "Very Low", "unusually")


async def _offenders() -> list:
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    found = []
    async for doc in db.narratives.find({"display_version": DISPLAY_VERSION}, {"_id": 0}):
        blob = str(doc)
        for term in BANNED_TERMS:
            if term in blob:
                found.append(f"{doc.get('session_id')} — '{term}'")
        for pattern in BANNED_PATTERNS:
            hit = re.search(pattern, blob)
            if hit:
                found.append(f"{doc.get('session_id')} — {hit.group(0)!r}")
    return found


def test_no_current_narrative_carries_copy_that_no_longer_ships():
    offenders = asyncio.run(_offenders())
    assert not offenders, (
        f"snapshots at the current {DISPLAY_VERSION} carry copy that no longer ships. Snapshots are "
        "write-once: bump DISPLAY_VERSION rather than editing them.\n" + "\n".join(offenders[:10])
    )

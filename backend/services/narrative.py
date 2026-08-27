"""Narrative snapshotting (rk-1.1.0 TRD §1, T1.1 / T10.2).

Layer 2 (scores) is immutable already. Layer 3 (narrative) is derived at read time — commonness
strings, choosing points, composite provenance, MRD gates — and the mapping tables behind it are
versioned and correctable. The sten->percentile table had two wrong cells; correcting them must
not reach back into a report somebody has already been given.

So: on FIRST render the fully resolved narrative is persisted, and every later view serves that
snapshot. A `display_version` bump only affects reports rendered after it.

Write-once on (session_id, display_version) via $setOnInsert. Two readers racing the first render
of the same report cannot produce two different documents.
"""
from datetime import datetime, timezone

from database import db
from services.display import DISPLAY_VERSION

CONTENT_VERSION = "copy-1.1.0"


async def snapshot_narrative(session_id: str, resolved: dict, user_id: str | None = None,
                             situation: str | None = None) -> dict:
    """Persist the resolved narrative if this is its first render; return whichever wins.

    `resolved` is the read-time-enriched result. The stored copy is authoritative from here on.
    """
    key = {"session_id": session_id, "display_version": DISPLAY_VERSION, "situation": situation}
    await db.narratives.update_one(
        key,
        {"$setOnInsert": {
            **key,
            "content_version": CONTENT_VERSION,
            "user_id": user_id,
            "narrative": resolved,
            "rendered_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )
    stored = await db.narratives.find_one(key, {"_id": 0, "narrative": 1, "rendered_at": 1})
    return stored or {"narrative": resolved}


async def resolved_narrative(session_id: str, build, user_id: str | None = None,
                             situation: str | None = None) -> dict:
    """The narrative for a report: the snapshot if one exists, otherwise build it and snapshot.

    `build` is a zero-argument callable returning the freshly resolved narrative. It is only
    invoked when there is no snapshot for this display_version and situation.

    Why `situation` is part of the key: the reader chooses it and can deliberately change it to
    reframe their reports. Freezing exists to stop US silently rewriting a delivered document, not
    to stop the reader from asking for a different lens. Switching produces a new snapshot;
    switching back serves the original one, unchanged.
    """
    stored = await db.narratives.find_one(
        {"session_id": session_id, "display_version": DISPLAY_VERSION, "situation": situation},
        {"_id": 0, "narrative": 1},
    )
    if stored and stored.get("narrative"):
        return stored["narrative"]
    snap = await snapshot_narrative(session_id, build(), user_id=user_id, situation=situation)
    return snap["narrative"]


async def snapshot_pdf(session_id: str, kind: str, build, user_id: str | None = None,
                       situation: str | None = None) -> bytes:
    """The rendered PDF bytes: stored on first build, served from storage thereafter (T8.2).

    `kind` separates the single-instrument report from the combined one. For the combined report
    `session_id` is the user id, since it spans sessions. `situation` is part of the key for the
    same reason it is on the narrative: the reader controls it.
    """
    key = {"session_id": session_id, "kind": kind, "display_version": DISPLAY_VERSION,
           "situation": situation}
    stored = await db.rendered_pdfs.find_one(key, {"_id": 0, "pdf": 1})
    if stored and stored.get("pdf"):
        return bytes(stored["pdf"])
    pdf = build()
    await db.rendered_pdfs.update_one(
        key,
        {"$setOnInsert": {**key, "user_id": user_id, "pdf": pdf,
                          "bytes": len(pdf),
                          "rendered_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    winner = await db.rendered_pdfs.find_one(key, {"_id": 0, "pdf": 1})
    return bytes(winner["pdf"]) if winner and winner.get("pdf") else pdf


async def invalidate_combined(user_id: str) -> None:
    """The combined report spans instruments, so finishing another one legitimately changes it.

    Dropping the stored copy is not a rewrite of a delivered document: each single-instrument
    report keeps its own snapshot untouched. Only the roll-up is rebuilt.
    """
    await db.rendered_pdfs.delete_many({"session_id": user_id, "kind": "combined"})

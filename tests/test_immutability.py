"""Narrative snapshot immutability (rk-1.1.0 TRD T1.1, T10.1, T10.2).

Scores were already immutable. This covers layer three: the narrative is derived at read time
from versioned mapping tables, and the sten->percentile table has already needed one correction.
A correction must never reach back into a report someone has already been given.

pytest-asyncio is not installed, so each test drives its own loop and binds a fresh Motor client
to it — the module-level client in database.py belongs to the running server's loop.
"""
import asyncio
import os
import sys

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)
os.environ.setdefault("RK_ALLOW_PLACEHOLDER_ALPHA", "1")

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(BACKEND, ".env"))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

from services import narrative as narrative_mod  # noqa: E402
from services.display import DISPLAY_VERSION  # noqa: E402


def _run(coro_fn):
    """Run `coro_fn(db)` on a private loop with its own client, restoring the module's db after."""
    async def main():
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = client[os.environ["DB_NAME"]]
        original = narrative_mod.db
        narrative_mod.db = db
        try:
            await coro_fn(db)
        finally:
            narrative_mod.db = original
            client.close()

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()


def test_first_render_is_snapshotted_and_later_reads_serve_it():
    async def body(db):
        session_id = "test-snapshot-first-render"
        await db.narratives.delete_many({"session_id": session_id})
        calls = []

        def build_v1():
            calls.append("v1")
            return {"instrument": "personality", "commonness": {"factors": {"A": {"fraction": "1 in 4"}}}}

        first = await narrative_mod.resolved_narrative(session_id, build_v1, "u1")
        assert first["commonness"]["factors"]["A"]["fraction"] == "1 in 4"
        assert calls == ["v1"]

        def build_v2():
            calls.append("v2")
            return {"instrument": "personality", "commonness": {"factors": {"A": {"fraction": "1 in 40"}}}}

        second = await narrative_mod.resolved_narrative(session_id, build_v2, "u1")
        assert calls == ["v1"], "the builder must not run again once a snapshot exists"
        assert second == first
        await db.narratives.delete_many({"session_id": session_id})

    _run(body)


def test_display_version_bump_leaves_the_existing_snapshot_untouched():
    async def body(db):
        session_id = "test-snapshot-version-bump"
        await db.narratives.delete_many({"session_id": session_id})
        await narrative_mod.resolved_narrative(session_id, lambda: {"copy": "as delivered"}, "u1")
        delivered = await db.narratives.find_one(
            {"session_id": session_id, "display_version": DISPLAY_VERSION}, {"_id": 0, "narrative": 1})

        original = narrative_mod.DISPLAY_VERSION
        try:
            narrative_mod.DISPLAY_VERSION = "disp-1.0.1"  # a corrected mapping table ships
            after = await narrative_mod.resolved_narrative(session_id, lambda: {"copy": "corrected"}, "u1")
            assert after == {"copy": "corrected"}, "a report rendered after the bump gets the new copy"
        finally:
            narrative_mod.DISPLAY_VERSION = original

        still = await db.narratives.find_one(
            {"session_id": session_id, "display_version": DISPLAY_VERSION}, {"_id": 0, "narrative": 1})
        assert still == delivered, "the delivered report changed when the display version was bumped"
        assert still["narrative"]["copy"] == "as delivered"
        await db.narratives.delete_many({"session_id": session_id})

    _run(body)


def test_pdf_bytes_are_stored_on_first_build_and_served_after():
    async def body(db):
        session_id = "test-snapshot-pdf"
        await db.rendered_pdfs.delete_many({"session_id": session_id})
        builds = []

        def build():
            builds.append(1)
            return b"%PDF-1.4 first render"

        first = await narrative_mod.snapshot_pdf(session_id, "report", build, "u1")
        assert first == b"%PDF-1.4 first render"
        second = await narrative_mod.snapshot_pdf(session_id, "report", lambda: b"%PDF-1.4 rebuilt", "u1")
        assert second == first, "the stored PDF must be served, not rebuilt"
        assert len(builds) == 1
        await db.rendered_pdfs.delete_many({"session_id": session_id})

    _run(body)


def test_combined_pdf_is_invalidated_but_single_reports_are_not():
    """Finishing another instrument legitimately changes the roll-up. It must not touch the
    individual reports, which are the documents actually delivered per instrument."""
    async def body(db):
        user_id = "test-snapshot-user"
        await db.rendered_pdfs.delete_many({"user_id": user_id})
        await db.rendered_pdfs.delete_many({"session_id": "session-one"})

        await narrative_mod.snapshot_pdf("session-one", "report", lambda: b"%PDF single", user_id)
        await narrative_mod.snapshot_pdf(user_id, "combined", lambda: b"%PDF combined v1", user_id)

        await narrative_mod.invalidate_combined(user_id)

        single = await narrative_mod.snapshot_pdf("session-one", "report", lambda: b"%PDF rebuilt", user_id)
        assert single == b"%PDF single", "invalidating the roll-up must not touch a single report"
        combined = await narrative_mod.snapshot_pdf(user_id, "combined", lambda: b"%PDF combined v2", user_id)
        assert combined == b"%PDF combined v2"

        await db.rendered_pdfs.delete_many({"user_id": user_id})
        await db.rendered_pdfs.delete_many({"session_id": "session-one"})

    _run(body)

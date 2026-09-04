"""Per-IP rate limiting and payload caps for unauthenticated writes (work order A2).

Before this, `POST /api/reflections` was an unauthenticated, unthrottled, uncapped write: one
loop could fill the collection. The only 429 in the codebase was the partner-application dedupe
in routes/partners.py, which counts submissions per email over a day and is an application rule,
not a limiter — there was nothing to reuse.

Fixed window, counted in Mongo so it holds across pods rather than per-process. A window is a
document keyed on (bucket, client, window index) with a TTL-ish `expires_at`; `$inc` is atomic,
so two pods racing the same window cannot both be allowed through on the last slot.

LIMITATION, stated rather than hidden: the client key prefers the X-Forwarded-For chain because
behind the ingress every pod sees the same peer address. A caller can therefore choose its own
bucket by sending its own header. This raises the cost of casual abuse and bounds accidental
loops; it is not a defence against a determined attacker, which needs edge-level limiting.
"""
import math
import os
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from pymongo import ReturnDocument

from database import db

# Generous by design: these exist to stop loops and mailbox abuse, not to ration real use.
LIMITS = {
    "reflections": (int(os.environ.get("RK_RL_REFLECTIONS", "30")), 600),
    "partners": (int(os.environ.get("RK_RL_PARTNERS", "10")), 600),
    "auth": (int(os.environ.get("RK_RL_AUTH", "60")), 600),
}

# A cap on unauthenticated request bodies. The largest legitimate one is a partner application
# at roughly 800 characters; 16 KiB leaves room without leaving the door open.
MAX_BODY_BYTES = int(os.environ.get("RK_MAX_UNAUTH_BODY", str(16 * 1024)))


def client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def assert_body_within_cap(request: Request) -> None:
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="That request body is larger than we accept.")


async def enforce(request: Request, bucket: str) -> None:
    """Count this request against its window and refuse once the window is full."""
    assert_body_within_cap(request)
    limit, window = LIMITS[bucket]
    now = datetime.now(timezone.utc)
    index = math.floor(now.timestamp() / window)
    key = {"bucket": bucket, "client": client_key(request), "window": index}
    doc = await db.rate_limits.find_one_and_update(
        key,
        {"$inc": {"count": 1},
         "$setOnInsert": {**key, "expires_at": (now + timedelta(seconds=window * 2)).isoformat()}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    if (doc or {}).get("count", 1) > limit:
        raise HTTPException(
            status_code=429,
            detail="That's more requests than we accept from one place in a few minutes. Try again shortly.",
        )


def limiter(bucket: str):
    """FastAPI dependency: `Depends(limiter("reflections"))`."""
    async def _dep(request: Request):
        await enforce(request, bucket)
    return _dep

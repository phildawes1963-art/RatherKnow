"""Partner programme applications (rk-landing-and-partner-copy.md, page two §8).

Four questions and a name. Read by a human, answered by a human — the page promises that, so
there is no auto-approval, no scoring of applicants, and no tier system.

Open endpoint: a practitioner should not need an account to apply. Rate-limited per email and
per remote address so it cannot be used as a mailbox.
"""
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from database import db
from services.ratelimit import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/partners", tags=["Partners"])

MAX_PER_WINDOW = 3
WINDOW_HOURS = 24

AUDIENCE_PLACES = {
    "practice": "A private practice or client list",
    "newsletter": "A newsletter or mailing list",
    "social": "A social following",
    "podcast": "A podcast or video channel",
    "organisation": "An organisation, clinic or training body",
    "other": "Somewhere else",
}


class PartnerApplication(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    audience_where: str
    audience_size: str = Field(min_length=1, max_length=60)
    why_it_fits: str = Field(min_length=10, max_length=600)


def _client_key(request: Request) -> str:
    """Prefer the forwarded chain: behind the ingress every pod sees the same peer address."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.get("/audience-options")
async def audience_options():
    return {"options": [{"value": k, "label": v} for k, v in AUDIENCE_PLACES.items()]}


@router.post("/apply")
async def apply(data: PartnerApplication, request: Request,
                _rl=Depends(limiter("partners"))):
    if data.audience_where not in AUDIENCE_PLACES:
        raise HTTPException(status_code=400, detail="Unknown audience type")
    if not re.search(r"[a-zA-Z]", data.why_it_fits):
        raise HTTPException(status_code=400, detail="Tell us in a sentence why this fits your audience")

    since = (datetime.now(timezone.utc) - timedelta(hours=WINDOW_HOURS)).isoformat()
    email = data.email.lower()
    recent = await db.partner_applications.count_documents(
        {"submitted_at": {"$gte": since},
         "$or": [{"email": email}, {"client_key": _client_key(request)}]}
    )
    if recent >= MAX_PER_WINDOW:
        raise HTTPException(status_code=429, detail="We already have your application — give us a few days.")

    doc = {
        "id": str(uuid.uuid4()),
        "name": data.name.strip(),
        "email": email,
        "audience_where": data.audience_where,
        "audience_where_label": AUDIENCE_PLACES[data.audience_where],
        "audience_size": data.audience_size.strip(),
        "why_it_fits": data.why_it_fits.strip(),
        "status": "unread",
        "client_key": _client_key(request),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.partner_applications.insert_one(dict(doc))
    logger.info("partner application received: %s", doc["id"])
    return {
        "received": True,
        "message": (
            "That's with us. We read these ourselves, so it's a few days rather than a few minutes — "
            "and we do say no to some, with a reason."
        ),
    }

"""Platform-scheduled maintenance endpoints (.emergent/crons.yml).

Authenticated by a shared secret, not by a user session: the caller is the platform scheduler.
"""
import asyncio
import hmac
import logging
import os

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException

from routes.junction import purge_unclaimed

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cron", tags=["Cron"])

_SEEN: set = set()


def _authorise(authorization: str | None) -> None:
    secret = os.environ["WEBHOOK_CRON_SECRET"]
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorised")
    if not hmac.compare_digest(authorization.split(" ", 1)[1], secret):
        raise HTTPException(status_code=401, detail="Unauthorised")


@router.post("/junction-purge")
async def junction_purge(background: BackgroundTasks, authorization: str | None = Header(default=None),
                         x_webhook_id: str | None = Header(default=None)):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    _authorise(authorization)
    run_id = x_webhook_id or "manual"
    if run_id in _SEEN and run_id != "manual":
        return {"accepted": True, "duplicate": True, "run_id": run_id}
    _SEEN.add(run_id)
    background.add_task(_run_purge)
    return {"accepted": True, "run_id": run_id}


async def _run_purge() -> None:
    try:
        deleted = await purge_unclaimed()
        logger.info("junction purge complete: %s deleted", deleted)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("junction purge failed")

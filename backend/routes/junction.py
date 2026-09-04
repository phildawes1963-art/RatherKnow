"""The Junction Check (rk-C1-junction-check-build-spec.md).

Six questions of plain fact about where a life is heading. Free, no account, under ten minutes.

WHAT THIS MODULE MUST NEVER GROW:

* **No scoring.** No scorer is imported and none may be added. The counting below counts items
  the reader could not answer — a count of unanswered questions, not a measure of the reader.
  There is no scale, no band, no norm and no comparison to anybody.
* **No second person.** A junction document has one `user_id` field and no field that can name,
  reference or key to another respondent. That is schema-level prevention: there is nowhere to
  put a second person, so no later feature can quietly acquire one.
* **The share link carries the questions, never the answers.** `/share-payload` returns the bank
  and nothing else. No route accepts a sender id, returns a recipient's answers, or joins two
  documents, and there is no pair token or callback by which one could.
* **No alignment language.** Not a score, not a percentage, not "you agree on four of six".
  Enforced by tests/test_junction_guards.py rather than by good intentions.

Anonymous by default: the offer to save comes after the answers are shown, never before, and
claiming reuses POST /api/auth/claim rather than a second claim path.
"""
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from auth import get_optional_user
from database import db
from services.ratelimit import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/junction", tags=["Junction Check"])

_BANK_PATH = os.path.join(os.path.dirname(__file__), "..", "constants", "junction_bank_1_0_0.json")
with open(os.path.abspath(_BANK_PATH), encoding="utf-8") as _fh:
    BANK = json.load(_fh)

ITEMS = BANK["items"]
RETENTION_DAYS = 90

_VALID = {}
for _item in ITEMS:
    _VALID[_item["id"]] = {o["value"] for o in _item["options"]}
    if _item.get("follow_up"):
        _VALID[_item["follow_up"]["id"]] = {o["value"] for o in _item["follow_up"]["options"]}

_UNDECIDED = {i["id"]: {o["value"] for o in i["options"] if o.get("undecided")} for i in ITEMS}

# Spelled, because "2 of the six" reads like a score and "two of the six" reads like a sentence.
_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}


class Answer(BaseModel):
    item_id: str
    value: str = Field(max_length=40)


class AnswersPut(BaseModel):
    answers: list[Answer] = Field(max_length=20)


def _questions() -> dict:
    """The shareable object: everything a reader needs to answer, and no answers."""
    return {"instrument": BANK["instrument"], "bank_version": BANK["bank_version"],
            "first_screen": BANK["first_screen"], "items": ITEMS, "share": BANK["share"]}


def _payload(doc: dict) -> dict:
    return {"junction_id": doc["id"], "status": doc["status"], **_questions(),
            "answers": doc.get("answers", {}), "result": doc.get("result")}


def _label(item: dict, answer_id: str, value: str) -> str:
    source = item if answer_id == item["id"] else item["follow_up"]
    for o in source["options"]:
        if o["value"] == value:
            return o["label"]
    return value


def _written_back(answers: dict) -> list:
    """Their own answers, in the bank's order, with the junction framing beside each."""
    out = []
    for item in ITEMS:
        value = answers.get(item["id"])
        if value is None:
            continue
        said = _label(item, item["id"], value)
        follow = item.get("follow_up")
        if follow and answers.get(follow["id"]):
            said = f"{said} — {_label(item, follow['id'], answers[follow['id']])}"
        out.append({"item_id": item["id"], "title": item["title"], "said": said,
                    "framing": item["framing"]})
    return out


def _finding(answers: dict) -> dict:
    """The only inference this instrument makes: which of the six the reader could not answer.

    A count of unanswered items. Not a score — nothing here is added up, ranked, banded or
    compared with anybody, and an unanswered item is a finding rather than a deduction.
    """
    copy = BANK["result"]
    undecided = [i for i in ITEMS
                 if answers.get(i["id"]) in _UNDECIDED[i["id"]] or answers.get(i["id"]) is None]
    labels = [i["short_label"] for i in undecided]
    if not undecided:
        return {"undecided_count": 0, "undecided_items": [],
                "lead": copy["all_answered_lead"], "body": copy["all_answered_body"]}
    if len(labels) == 1:
        joined = labels[0]
    else:
        joined = ", ".join(labels[:-1]) + f" and {labels[-1]}"
    lead = (copy["undecided_lead"]
            .replace("{count}", _WORDS.get(len(labels), str(len(labels))))
            .replace("{items}", joined))
    return {"undecided_count": len(labels), "undecided_items": [i["id"] for i in undecided],
            "lead": lead, "body": copy["undecided_body"]}


@router.get("/share-payload")
async def share_payload():
    """What a share link resolves to: the six questions. There is deliberately no parameter on
    this route, so it cannot be pointed at anybody's answers."""
    return _questions()


@router.post("/start")
async def start(_rl=Depends(limiter("junction"))):
    doc = {
        "id": str(uuid.uuid4()),
        "instrument": BANK["instrument"],
        "bank_version": BANK["bank_version"],
        "status": "in_progress",
        "user_id": None,
        "answers": {},
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.junction_answers.insert_one(dict(doc))
    return _payload(doc)


@router.get("/{junction_id}")
async def get_junction(junction_id: str):
    doc = await db.junction_answers.find_one({"id": junction_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return _payload(doc)


@router.put("/{junction_id}/answers")
async def put_answers(junction_id: str, data: AnswersPut, _rl=Depends(limiter("junction"))):
    doc = await db.junction_answers.find_one({"id": junction_id}, {"_id": 0, "id": 1, "status": 1})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    updates = {}
    for a in data.answers:
        if a.item_id not in _VALID:
            raise HTTPException(status_code=400, detail=f"Unknown item {a.item_id}")
        if a.value not in _VALID[a.item_id]:
            raise HTTPException(status_code=400, detail=f"Unknown answer for {a.item_id}")
        updates[f"answers.{a.item_id}"] = a.value
    if updates:
        await db.junction_answers.update_one({"id": junction_id}, {"$set": updates})
    return {"saved": len(updates)}


@router.post("/{junction_id}/complete")
async def complete(junction_id: str, _rl=Depends(limiter("junction")),
                   user: dict | None = Depends(get_optional_user)):
    doc = await db.junction_answers.find_one({"id": junction_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    answers = doc.get("answers", {})
    if not any(answers.get(i["id"]) for i in ITEMS):
        raise HTTPException(status_code=400, detail="Nothing answered yet")

    result = {
        "instrument": BANK["instrument"],
        "bank_version": BANK["bank_version"],
        "answers_heading": BANK["result"]["answers_heading"],
        "finding_heading": BANK["result"]["finding_heading"],
        "written_back": _written_back(answers),
        "finding": _finding(answers),
        "discomfort_note": BANK["result"]["discomfort_note"],
        "closing_lead": BANK["result"]["closing_lead"],
        "closing_body": BANK["result"]["closing_body"],
        "share": BANK["share"],
    }
    await db.junction_answers.update_one(
        {"id": junction_id},
        {"$set": {"status": "complete", "result": result,
                  "completed_at": datetime.now(timezone.utc).isoformat()}},
    )
    return result


async def purge_unclaimed(days: int = RETENTION_DAYS) -> int:
    """Anonymous answers are deleted at 90 days unless claimed onto an account.

    Built with the module rather than deferred: an anonymous instrument that keeps its answers
    indefinitely is a retention problem acquired by default.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    res = await db.junction_answers.delete_many({"user_id": None, "started_at": {"$lt": cutoff}})
    logger.info("junction purge: %s unclaimed documents older than %s days", res.deleted_count, days)
    return res.deleted_count

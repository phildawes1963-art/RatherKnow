"""C1 · the Junction Check over HTTP (build spec §10 acceptance).

Anonymous end to end, claim onto an account afterwards, rate limiting, and the retention job.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api/v2/junction"
AUTH = f"{BASE_URL}/api/auth"

ANSWERS_ALL_SIX = [
    ("j1", "yes"), ("j1b", "2_to_5"), ("j2", "settled"), ("j2b", "within_hour"),
    ("j3", "i_move"), ("j4", "later"), ("j5", "prefer_not"), ("j6", "one_exclusive"),
]
ANSWERS_TWO_UNSURE = [
    ("j1", "no"), ("j2", "open"), ("j2b", "no_distance"), ("j3", "never_thought"),
    ("j4", "now"), ("j5", "no"), ("j6", "dont_know_yet"),
]


def _own_ip() -> dict:
    n = uuid.uuid4().int
    return {"X-Forwarded-For": f"203.0.113.{n % 250 + 1}"}


@pytest.fixture(scope="module")
def http():
    return requests.Session()


def _run(http, answers):
    r = http.post(f"{API}/start", headers=_own_ip(), timeout=20)
    assert r.status_code == 200, r.text
    jid = r.json()["junction_id"]
    body = {"answers": [{"item_id": k, "value": v} for k, v in answers]}
    r = http.put(f"{API}/{jid}/answers", json=body, headers=_own_ip(), timeout=20)
    assert r.status_code == 200, r.text
    r = http.post(f"{API}/{jid}/complete", headers=_own_ip(), timeout=20)
    assert r.status_code == 200, r.text
    return jid, r.json()


# ---------------------------------------------------------------- the reader's journey

def test_the_six_questions_are_served_without_an_account(http):
    r = http.get(f"{API}/share-payload", headers=_own_ip(), timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert data["instrument"] == "RK-JC-6"
    assert len(data["items"]) == 6
    assert "for somebody else" in data["first_screen"]["instruction"]


def test_a_reader_with_no_account_completes_end_to_end(http):
    _, result = _run(http, ANSWERS_ALL_SIX)
    assert [row["item_id"] for row in result["written_back"]] == ["j1", "j2", "j3", "j4", "j5", "j6"]
    assert result["written_back"][0]["said"] == "Yes — Two to five years"
    assert result["finding"]["undecided_count"] == 0
    assert "all six" in result["finding"]["lead"]
    assert result["closing_lead"].startswith("A junction passed is passed")


def test_what_they_could_not_answer_is_named(http):
    _, result = _run(http, ANSWERS_TWO_UNSURE)
    finding = result["finding"]
    assert finding["undecided_count"] == 2
    assert "who moves" in finding["lead"] and "whether this is exclusive" in finding["lead"]
    assert "not a failure" in finding["body"]


def test_prefer_not_to_say_appears_as_chosen_not_as_missing(http):
    _, result = _run(http, ANSWERS_ALL_SIX)
    faith = next(r for r in result["written_back"] if r["item_id"] == "j5")
    assert faith["said"] == "Prefer not to say"


def test_the_result_carries_no_score_band_or_alignment(http):
    _, result = _run(http, ANSWERS_ALL_SIX)
    import json as _json

    text = _json.dumps(result).lower()
    for banned in ("compatib", "aligned", "percentage", "band", "sten", "norm", "you agree on",
                   "traffic light"):
        assert banned not in text, f"the junction result contains {banned}"
    for key in ("score", "scores", "percentile"):
        assert key not in result


def test_nothing_answered_cannot_be_completed(http):
    r = http.post(f"{API}/start", headers=_own_ip(), timeout=20)
    jid = r.json()["junction_id"]
    r = http.post(f"{API}/{jid}/complete", headers=_own_ip(), timeout=20)
    assert r.status_code == 400


def test_an_unknown_answer_is_refused(http):
    r = http.post(f"{API}/start", headers=_own_ip(), timeout=20)
    jid = r.json()["junction_id"]
    r = http.put(f"{API}/{jid}/answers", headers=_own_ip(), timeout=20,
                 json={"answers": [{"item_id": "j1", "value": "maybe_one_day"}]})
    assert r.status_code == 400


def test_an_unfinished_check_resumes(http):
    r = http.post(f"{API}/start", headers=_own_ip(), timeout=20)
    jid = r.json()["junction_id"]
    http.put(f"{API}/{jid}/answers", json={"answers": [{"item_id": "j1", "value": "no"}]},
             headers=_own_ip(), timeout=20)
    again = http.get(f"{API}/{jid}", headers=_own_ip(), timeout=20).json()
    assert again["answers"]["j1"] == "no"
    assert again["status"] == "in_progress"


# ---------------------------------------------------------------- claiming

def test_an_anonymous_check_claims_onto_an_account_created_afterwards(http):
    jid, _ = _run(http, ANSWERS_TWO_UNSURE)
    email = f"TEST_junction+{uuid.uuid4().hex[:10]}@ratherknow.com"
    reg = http.post(f"{AUTH}/register", headers=_own_ip(), timeout=20, json={
        "name": "Junction Claimer", "email": email, "password": "knowmore123",
        "situation": "single_dating"})
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]
    r = http.post(f"{AUTH}/claim", headers={**_own_ip(), "Authorization": f"Bearer {token}"},
                  json={"session_ids": [jid]}, timeout=20)
    assert r.status_code == 200, r.text
    assert r.json()["claimed"] == 1


def test_a_claimed_check_cannot_be_claimed_by_a_second_account(http):
    jid, _ = _run(http, ANSWERS_ALL_SIX)
    tokens = []
    for _ in range(2):
        email = f"TEST_junction+{uuid.uuid4().hex[:10]}@ratherknow.com"
        r = http.post(f"{AUTH}/register", headers=_own_ip(), timeout=20, json={
            "name": "Claimer", "email": email, "password": "knowmore123",
            "situation": "single_dating"})
        tokens.append(r.json()["access_token"])
    first = http.post(f"{AUTH}/claim", headers={**_own_ip(), "Authorization": f"Bearer {tokens[0]}"},
                      json={"session_ids": [jid]}, timeout=20)
    second = http.post(f"{AUTH}/claim", headers={**_own_ip(), "Authorization": f"Bearer {tokens[1]}"},
                       json={"session_ids": [jid]}, timeout=20)
    assert first.json()["claimed"] == 1
    assert second.json()["claimed"] == 0, "a second account claimed somebody else's answers"


# ---------------------------------------------------------------- rate limiting

def test_the_limiter_fires_and_a_single_completion_is_unaffected(http):
    headers = _own_ip()
    limit = int(os.environ.get("RK_RL_JUNCTION", "40"))
    statuses = [http.post(f"{API}/start", headers=headers, timeout=20).status_code
                for _ in range(limit + 2)]
    assert statuses[0] == 200
    assert 429 in statuses, f"limiter never fired: {set(statuses)}"
    # somebody else, same moment
    assert http.post(f"{API}/start", headers=_own_ip(), timeout=20).status_code == 200


def test_an_oversized_body_is_refused(http):
    r = http.put(f"{API}/{uuid.uuid4()}/answers", headers=_own_ip(), timeout=20,
                 json={"answers": [{"item_id": "j1", "value": "x" * 30000}]})
    assert r.status_code in (413, 422), r.status_code


# ---------------------------------------------------------------- retention

def test_the_cron_endpoint_refuses_without_the_secret(http):
    url = f"{BASE_URL}/api/cron/junction-purge"
    assert http.post(url, headers=_own_ip(), timeout=20).status_code == 401
    assert http.post(url, headers={**_own_ip(), "Authorization": "Bearer wrong"},
                     timeout=20).status_code == 401


def test_the_purge_deletes_unclaimed_answers_older_than_ninety_days(http):
    """Plants an aged unclaimed document and an aged claimed one, runs the job, and checks that
    only the unclaimed one goes."""
    import asyncio

    from motor.motor_asyncio import AsyncIOMotorClient

    old = (datetime.now(timezone.utc) - timedelta(days=91)).isoformat()
    unclaimed, claimed = str(uuid.uuid4()), str(uuid.uuid4())

    async def plant():
        db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
        await db.junction_answers.insert_many([
            {"id": unclaimed, "user_id": None, "status": "complete", "answers": {"j1": "no"},
             "started_at": old},
            {"id": claimed, "user_id": "someone", "status": "complete", "answers": {"j1": "no"},
             "started_at": old},
        ])

    asyncio.run(plant())

    r = http.post(f"{BASE_URL}/api/cron/junction-purge", timeout=25,
                  headers={**_own_ip(), "Authorization": f"Bearer {os.environ['WEBHOOK_CRON_SECRET']}",
                           "X-Webhook-Id": str(uuid.uuid4())})
    assert r.status_code == 200 and r.json()["accepted"] is True

    import time

    for _ in range(10):
        gone = http.get(f"{API}/{unclaimed}", headers=_own_ip(), timeout=20).status_code == 404
        if gone:
            break
        time.sleep(1)
    assert gone, "the unclaimed document survived the purge"
    assert http.get(f"{API}/{claimed}", headers=_own_ip(), timeout=20).status_code == 200, \
        "the purge deleted a claimed document"

"""Iteration 3 backend tests:
- Password reset (happy path, security invariants, token single-use, expiry, no enumeration)
- Session ownership 403 on responses/complete/result (regression from iter2)
- Situation framing does not change scoring (identical answers -> identical numbers)
"""
import os
import uuid
import hashlib
import asyncio
import datetime as dt
import pytest
import requests
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


def _uniq(prefix="rst"):
    return f"TEST_{prefix}+{uuid.uuid4().hex[:10]}@ratherknow.com"


def _hash_token(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


@pytest.fixture(scope="session")
def http():
    return requests.Session()


@pytest.fixture(scope="session")
def mongo():
    client = MongoClient(MONGO_URL)
    return client[DB_NAME]


def _run(coro):
    return coro  # no-op — mongo calls are sync now


def _register(http, situation="single_dating", pw="knowmore123"):
    email = _uniq()
    r = http.post(f"{API}/auth/register", json={
        "name": "Reset User", "email": email, "password": pw, "situation": situation,
    }, timeout=20)
    assert r.status_code == 200, r.text
    return email.lower(), r.json()["access_token"]


# ---------- Password reset: happy path ----------
def test_forgot_password_returns_sent_true_for_existing_user(http, mongo):
    email, _ = _register(http)
    r = http.post(f"{API}/auth/forgot-password", json={"email": email}, timeout=30)
    assert r.status_code == 200, r.text
    assert r.json() == {"sent": True}

    # A single password_resets doc exists, and token_hash is a sha256 hex string (never raw)
    docs = list(mongo.password_resets.find({}))
    user = mongo.users.find_one({"email": email})
    mine = [d for d in docs if d["user_id"] == str(user["_id"])]
    assert len(mine) == 1
    doc = mine[0]
    assert "token_hash" in doc and len(doc["token_hash"]) == 64
    assert "token" not in doc
    # Expiry ~60 minutes from now
    exp = dt.datetime.fromisoformat(doc["expires_at"])
    delta = (exp - dt.datetime.now(dt.timezone.utc)).total_seconds()
    assert 3300 < delta < 3900  # 55–65 minutes


def test_forgot_password_no_enumeration(http):
    r = http.post(f"{API}/auth/forgot-password",
                  json={"email": _uniq("ghost")}, timeout=30)
    assert r.status_code == 200
    assert r.json() == {"sent": True}


# ---------- Reset security ----------
def test_reset_password_garbage_token_400(http):
    r = http.post(f"{API}/auth/reset-password",
                  json={"token": "x" * 40, "password": "newpassword1"}, timeout=20)
    assert r.status_code == 400


def test_reset_password_expired_token_400(http, mongo):
    email, _ = _register(http)
    user = mongo.users.find_one({"email": email})
    tok = uuid.uuid4().hex + uuid.uuid4().hex  # long enough
    mongo.password_resets.insert_one({
        "user_id": str(user["_id"]),
        "token_hash": _hash_token(tok),
        "expires_at": (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)).isoformat(),
        "used": False,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    })
    r = http.post(f"{API}/auth/reset-password",
                  json={"token": tok, "password": "newpassword1"}, timeout=20)
    assert r.status_code == 400


def test_reset_password_happy_path_and_single_use(http, mongo):
    email, _ = _register(http, pw="oldpassword1")
    user = mongo.users.find_one({"email": email})
    tok = uuid.uuid4().hex + uuid.uuid4().hex
    mongo.password_resets.insert_one({
        "user_id": str(user["_id"]),
        "token_hash": _hash_token(tok),
        "expires_at": (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=30)).isoformat(),
        "used": False,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    })
    # Reset succeeds and returns fresh access token
    r = http.post(f"{API}/auth/reset-password",
                  json={"token": tok, "password": "newpassword1"}, timeout=20)
    assert r.status_code == 200, r.text
    assert "access_token" in r.json()

    # Old password no longer works
    r = http.post(f"{API}/auth/login",
                  json={"email": email, "password": "oldpassword1"}, timeout=20)
    assert r.status_code == 401

    # New password works
    r = http.post(f"{API}/auth/login",
                  json={"email": email, "password": "newpassword1"}, timeout=20)
    assert r.status_code == 200

    # Second use of same token fails
    r = http.post(f"{API}/auth/reset-password",
                  json={"token": tok, "password": "anotherone1"}, timeout=20)
    assert r.status_code == 400


def test_reset_clears_lockout(http, mongo):
    email, _ = _register(http, pw="oldpassword1")
    # Trigger lockout
    for _ in range(6):
        http.post(f"{API}/auth/login",
                  json={"email": email, "password": "wrong-guess"}, timeout=20)
    r = http.post(f"{API}/auth/login",
                  json={"email": email, "password": "wrong-guess"}, timeout=20)
    assert r.status_code == 429

    # Mint a valid reset token and use it
    user = mongo.users.find_one({"email": email})
    tok = uuid.uuid4().hex + uuid.uuid4().hex
    mongo.password_resets.insert_one({
        "user_id": str(user["_id"]),
        "token_hash": _hash_token(tok),
        "expires_at": (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=30)).isoformat(),
        "used": False,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    })
    r = http.post(f"{API}/auth/reset-password",
                  json={"token": tok, "password": "newpassword1"}, timeout=20)
    assert r.status_code == 200
    # Login with new pw immediately allowed — lockout cleared
    r = http.post(f"{API}/auth/login",
                  json={"email": email, "password": "newpassword1"}, timeout=20)
    assert r.status_code == 200


# ---------- Session ownership: 403 across accounts (regression from iter2 fix) ----------
def _start_closeness(http, tok):
    hdr = {"Authorization": f"Bearer {tok}"}
    return http.post(f"{API}/v2/assessments",
                     json={"instrument": "closeness"}, headers=hdr, timeout=30).json()


def test_ownership_403_on_responses(http):
    _, tok_a = _register(http)
    _, tok_b = _register(http)
    s = _start_closeness(http, tok_a)
    sid = s["session_id"]
    batch = [{"item_id": it["id"], "value": 4} for it in s["items"][:5]]
    r = http.put(f"{API}/v2/assessments/{sid}/responses",
                 json={"responses": batch},
                 headers={"Authorization": f"Bearer {tok_b}"}, timeout=30)
    assert r.status_code == 403, r.text


def test_ownership_403_on_complete(http):
    _, tok_a = _register(http)
    _, tok_b = _register(http)
    s = _start_closeness(http, tok_a)
    sid = s["session_id"]
    hdr_a = {"Authorization": f"Bearer {tok_a}"}
    batch = [{"item_id": it["id"], "value": 4} for it in s["items"]]
    http.put(f"{API}/v2/assessments/{sid}/responses", json={"responses": batch}, headers=hdr_a, timeout=30)
    r = http.post(f"{API}/v2/assessments/{sid}/complete",
                  headers={"Authorization": f"Bearer {tok_b}"}, timeout=30)
    assert r.status_code == 403, r.text


def test_ownership_403_on_result_fetch(http):
    _, tok_a = _register(http)
    _, tok_b = _register(http)
    s = _start_closeness(http, tok_a)
    sid = s["session_id"]
    hdr_a = {"Authorization": f"Bearer {tok_a}"}
    batch = [{"item_id": it["id"], "value": 4} for it in s["items"]]
    http.put(f"{API}/v2/assessments/{sid}/responses", json={"responses": batch}, headers=hdr_a, timeout=30)
    http.post(f"{API}/v2/assessments/{sid}/complete", headers=hdr_a, timeout=30)
    r = http.get(f"{API}/v2/assessments/{sid}/result",
                 headers={"Authorization": f"Bearer {tok_b}"}, timeout=30)
    assert r.status_code == 403, r.text


# ---------- Situation-independence: identical answers give identical numbers ----------
def _complete_and_get_result(http, tok, instrument, value=4):
    hdr = {"Authorization": f"Bearer {tok}"}
    s = http.post(f"{API}/v2/assessments",
                  json={"instrument": instrument}, headers=hdr, timeout=30).json()
    sid = s["session_id"]
    batch = [{"item_id": it["id"], "value": value} for it in s["items"]]
    http.put(f"{API}/v2/assessments/{sid}/responses",
             json={"responses": batch}, headers=hdr, timeout=30)
    http.post(f"{API}/v2/assessments/{sid}/complete", headers=hdr, timeout=30)
    r = http.get(f"{API}/v2/assessments/{sid}/result", headers=hdr, timeout=30)
    assert r.status_code == 200
    j = r.json()
    # Drop per-session/user metadata; keep the scoring payload
    for k in ("session_id", "completed_at", "user_id", "algo_version", "instrument"):
        j.pop(k, None)
    return j


@pytest.mark.parametrize("instrument", ["essential", "personality", "eq", "closeness"])
def test_scoring_independent_of_situation(http, instrument):
    _, t_single = _register(http, situation="single_dating")
    _, t_rel = _register(http, situation="in_relationship")
    _, t_pb = _register(http, situation="post_breakup")
    r1 = _complete_and_get_result(http, t_single, instrument)
    r2 = _complete_and_get_result(http, t_rel, instrument)
    r3 = _complete_and_get_result(http, t_pb, instrument)
    # Result payload contains a `result` block with instrument-specific scores.
    # Compare that block only; ignore session/user metadata.
    assert r1 == r2 == r3, \
        f"{instrument}: scoring differed across situations"

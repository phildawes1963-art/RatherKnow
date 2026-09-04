"""Auth backend tests — register/login/me/claim, gating on /api/v2/assessments,
retrieval via /me/sessions, and brute-force lockout."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"

TEST_EMAIL = "test.user@ratherknow.com"
TEST_PW = "knowmore123"


def _uniq_email(prefix="user"):
    return f"TEST_{prefix}+{uuid.uuid4().hex[:10]}@ratherknow.com"


@pytest.fixture(scope="session")
def http():
    return requests.Session()


# ---------- register ----------
def test_register_returns_user_and_token(http):
    email = _uniq_email("reg")
    r = http.post(f"{API}/auth/register", json={
        "name": "Registered User", "email": email, "password": "knowmore123",
        "situation": "in_relationship",
    }, timeout=20)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["user"]["email"] == email.lower()
    assert j["user"]["situation"] == "in_relationship"
    assert j["user"]["situation_label"] == "In a relationship"
    assert isinstance(j["access_token"], str) and len(j["access_token"]) > 10


def test_register_normalises_email_lowercase(http):
    email = _uniq_email("Norm").upper()  # uppercase local+domain
    r = http.post(f"{API}/auth/register", json={
        "name": "Case User", "email": email, "password": "knowmore123",
        "situation": "single_dating",
    }, timeout=20)
    assert r.status_code == 200, r.text
    assert r.json()["user"]["email"] == email.lower()


def test_register_duplicate_email_409(http):
    email = _uniq_email("dup")
    r1 = http.post(f"{API}/auth/register", json={
        "name": "A", "email": email, "password": "knowmore123",
        "situation": "post_breakup",
    }, timeout=20)
    assert r1.status_code == 200
    r2 = http.post(f"{API}/auth/register", json={
        "name": "B", "email": email, "password": "knowmore123",
        "situation": "post_breakup",
    }, timeout=20)
    assert r2.status_code == 409, r2.text


def test_register_short_password_422(http):
    r = http.post(f"{API}/auth/register", json={
        "name": "Short", "email": _uniq_email("short"), "password": "abc",
        "situation": "single_dating",
    }, timeout=20)
    assert r.status_code == 422, r.text


def test_register_invalid_situation_422(http):
    r = http.post(f"{API}/auth/register", json={
        "name": "Sit", "email": _uniq_email("sit"), "password": "knowmore123",
        "situation": "married",
    }, timeout=20)
    assert r.status_code == 422, r.text


# ---------- login / me ----------
def test_login_success_shared_user(http):
    r = http.post(f"{API}/auth/login",
                  json={"email": TEST_EMAIL, "password": TEST_PW}, timeout=20)
    assert r.status_code == 200, r.text
    j = r.json()
    assert "access_token" in j
    assert j["user"]["email"] == TEST_EMAIL


def test_login_wrong_password_401(http):
    r = http.post(f"{API}/auth/login",
                  json={"email": TEST_EMAIL, "password": "nope-nope-nope"}, timeout=20)
    assert r.status_code == 401


def test_me_returns_situation_label(http):
    tok = http.post(f"{API}/auth/login",
                    json={"email": TEST_EMAIL, "password": TEST_PW}, timeout=20).json()["access_token"]
    r = http.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {tok}"}, timeout=20)
    assert r.status_code == 200
    u = r.json()["user"]
    assert u["email"] == TEST_EMAIL
    assert u["situation_label"] in ("Single & dating", "In a relationship", "Post-breakup")


def test_me_no_token_401(http):
    r = http.get(f"{API}/auth/me", timeout=20)
    assert r.status_code == 401


def test_me_garbage_token_401(http):
    r = http.get(f"{API}/auth/me", headers={"Authorization": "Bearer garbage.token.here"}, timeout=20)
    assert r.status_code == 401


# ---------- brute-force lockout (uses throwaway account so shared user isn't locked) ----------
def test_brute_force_lockout(http):
    email = _uniq_email("brute")
    http.post(f"{API}/auth/register", json={
        "name": "Brute", "email": email, "password": "knowmore123",
        "situation": "single_dating",
    }, timeout=20)
    for _ in range(5):
        r = http.post(f"{API}/auth/login",
                      json={"email": email, "password": "wrong-guess"}, timeout=20)
        assert r.status_code == 401
    # 6th attempt should be 429
    r = http.post(f"{API}/auth/login",
                  json={"email": email, "password": "wrong-guess"}, timeout=20)
    assert r.status_code == 429, r.text


# ---------- gating on /api/v2/assessments ----------
def test_assessment_start_requires_auth(http):
    r = http.post(f"{API}/v2/assessments", json={"instrument": "closeness"}, timeout=20)
    assert r.status_code == 401


def test_assessment_start_ok_with_bearer_and_stamps_user(http):
    tok = http.post(f"{API}/auth/login",
                    json={"email": TEST_EMAIL, "password": TEST_PW}, timeout=20).json()["access_token"]
    r = http.post(f"{API}/v2/assessments", json={"instrument": "closeness"},
                  headers={"Authorization": f"Bearer {tok}"}, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["session_id"]
    # Confirm session was stamped with user_id + situation_at_start (via mirrors summary + me/sessions)
    ms = http.get(f"{API}/auth/me/sessions",
                  headers={"Authorization": f"Bearer {tok}"}, timeout=20).json()
    assert any(s["session_id"] == j["session_id"] for s in ms["sessions"])


# ---------- flag check remains open (no auth) ----------
def test_flag_check_open_no_auth(http):
    r = http.post(f"{API}/v2/reflections", timeout=20)
    assert r.status_code == 200, r.text
    rid = r.json()["reflection_id"]
    body = [{"item_id": f"f{i+1}", "value": ((i % 3) + 1)} for i in range(8)]
    body.append({"item_id": "f-safety", "value": 1})
    r = http.put(f"{API}/v2/reflections/{rid}/responses", json={"responses": body}, timeout=20)
    assert r.status_code == 200, r.text
    r = http.post(f"{API}/v2/reflections/{rid}/complete", timeout=20)
    assert r.status_code == 200


# ---------- retrieval by login: completed session appears; other user can't see it ----------
def _complete_closeness(http, token):
    hdr = {"Authorization": f"Bearer {token}"}
    s = http.post(f"{API}/v2/assessments", json={"instrument": "closeness"}, headers=hdr, timeout=30).json()
    sid = s["session_id"]
    batch = [{"item_id": it["id"], "value": 4} for it in s["items"]]
    http.put(f"{API}/v2/assessments/{sid}/responses", json={"responses": batch}, headers=hdr, timeout=30)
    http.post(f"{API}/v2/assessments/{sid}/complete", headers=hdr, timeout=30)
    return sid


def test_me_sessions_lists_completed_only_for_owner(http):
    email_a = _uniq_email("A")
    email_b = _uniq_email("B")
    tok_a = http.post(f"{API}/auth/register", json={
        "name": "A", "email": email_a, "password": "knowmore123", "situation": "single_dating",
    }, timeout=20).json()["access_token"]
    tok_b = http.post(f"{API}/auth/register", json={
        "name": "B", "email": email_b, "password": "knowmore123", "situation": "in_relationship",
    }, timeout=20).json()["access_token"]

    sid = _complete_closeness(http, tok_a)

    a_sessions = http.get(f"{API}/auth/me/sessions",
                          headers={"Authorization": f"Bearer {tok_a}"}, timeout=20).json()["sessions"]
    mine = [s for s in a_sessions if s["session_id"] == sid]
    assert mine and mine[0]["status"] == "complete"

    b_sessions = http.get(f"{API}/auth/me/sessions",
                          headers={"Authorization": f"Bearer {tok_b}"}, timeout=20).json()["sessions"]
    assert not any(s["session_id"] == sid for s in b_sessions)


# ---------- claim ----------
def test_claim_only_attaches_unowned_and_not_stolen(http):
    # Owner completes a session
    email_owner = _uniq_email("own")
    email_thief = _uniq_email("thief")
    tok_owner = http.post(f"{API}/auth/register", json={
        "name": "Owner", "email": email_owner, "password": "knowmore123", "situation": "single_dating",
    }, timeout=20).json()["access_token"]
    tok_thief = http.post(f"{API}/auth/register", json={
        "name": "Thief", "email": email_thief, "password": "knowmore123", "situation": "single_dating",
    }, timeout=20).json()["access_token"]

    sid_owned = _complete_closeness(http, tok_owner)

    # Thief tries to claim the owned session
    r = http.post(f"{API}/auth/claim", json={"session_ids": [sid_owned]},
                  headers={"Authorization": f"Bearer {tok_thief}"}, timeout=20)
    assert r.status_code == 200
    assert r.json()["claimed"] == 0

    # Owner still sees it; thief does not
    ow = http.get(f"{API}/auth/me/sessions",
                  headers={"Authorization": f"Bearer {tok_owner}"}, timeout=20).json()["sessions"]
    assert any(s["session_id"] == sid_owned for s in ow)
    th = http.get(f"{API}/auth/me/sessions",
                  headers={"Authorization": f"Bearer {tok_thief}"}, timeout=20).json()["sessions"]
    assert not any(s["session_id"] == sid_owned for s in th)

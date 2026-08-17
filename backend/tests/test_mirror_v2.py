"""Backend tests for Mirror v2 (RatherKnow).
Covers instruments listing, per-instrument lifecycle, validation, findings,
Flag Check reflection lifecycle, and immutability.
"""
import os
import random
import pytest
import requests
from dotenv import load_dotenv
load_dotenv("/app/frontend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api/v2"

EXPECTED = {
    "essential":  {"total_items": 100, "evidence_tier": "Developmental", "scale": 5},
    "personality":{"total_items": 130, "evidence_tier": "Established",   "scale": 5},
    "eq":         {"total_items": 140, "evidence_tier": "Established",   "scale": 5},
    "closeness":  {"total_items": 37,  "evidence_tier": "Developmental", "scale": 7},
}


@pytest.fixture(scope="session")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    # Register a throwaway user and set Bearer token for gated instrument endpoints
    import uuid as _u
    email = f"pytest+{_u.uuid4().hex[:10]}@ratherknow.com"
    r = sess.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Pytest User", "email": email, "password": "knowmore123",
        "situation": "single_dating",
    }, timeout=30)
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    sess.headers.update({"Authorization": f"Bearer {token}"})
    return sess


@pytest.fixture(scope="session")
def s_noauth():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ---------- instruments listing ----------
def test_instruments_list(s):
    r = s.get(f"{API}/instruments", timeout=30)
    assert r.status_code == 200
    by_key = {i["key"]: i for i in r.json()["instruments"]}
    assert set(by_key) == set(EXPECTED)
    for k, exp in EXPECTED.items():
        assert by_key[k]["total_items"] == exp["total_items"], k
        assert by_key[k]["evidence_tier"] == exp["evidence_tier"], k


# ---------- helper: full instrument lifecycle ----------
def _run(s, instrument):
    exp = EXPECTED[instrument]
    r = s.post(f"{API}/assessments", json={"instrument": instrument}, timeout=30)
    assert r.status_code == 200, r.text
    sess = r.json()
    sid = sess["session_id"]
    assert len(sess["items"]) == exp["total_items"]
    n_points = exp["scale"]
    random.seed(42)
    # Batch responses in chunks of 60 to keep payload reasonable
    items = sess["items"]
    batch = [{"item_id": it["id"], "value": random.randint(1, n_points), "ms": 500} for it in items]
    for i in range(0, len(batch), 60):
        r = s.put(f"{API}/assessments/{sid}/responses", json={"responses": batch[i:i+60]}, timeout=30)
        assert r.status_code == 200, r.text
    # 409 before complete? no — 409 only if getting result while in progress
    gr = s.get(f"{API}/assessments/{sid}/result", timeout=30)
    assert gr.status_code == 409
    r = s.post(f"{API}/assessments/{sid}/complete", timeout=60)
    assert r.status_code == 200, r.text
    result = r.json()
    assert result["algo_version"] == "rk-1.0.0"
    assert result["session_id"] == sid
    return sid, result


def test_essential_lifecycle(s):
    sid, res = _run(s, "essential")
    assert "self" in res and "ideal" in res
    assert "delta" in res and "overall" in res["delta"] and "per_archetype" in res["delta"]
    assert res["self"]["primary"]["name"]
    assert res["ideal"]["primary"]["name"]


def test_personality_lifecycle(s):
    sid, res = _run(s, "personality")
    assert len(res["factor_scores"]) == 15, list(res["factor_scores"].keys())
    assert len(res["global_scores"]) == 5, list(res["global_scores"].keys())
    assert "validity" in res


def test_eq_lifecycle(s):
    sid, res = _run(s, "eq")
    assert len(res["domain_scores"]) == 4
    assert isinstance(res["overall_score"], (int, float))


def test_closeness_lifecycle_no_bands(s):
    sid, res = _run(s, "closeness")
    assert "dimensions" in res and "facets" in res and "validity" in res
    assert "confidence" in res
    # No bands / percentages / grades / risk labels
    import json as _j
    dump = _j.dumps(res).lower()
    for banned in ("band", "percentile", "%", "grade", "risk"):
        assert banned not in dump, f"forbidden token {banned!r} in closeness result"


# ---------- immutability ----------
def test_immutability_and_double_complete(s):
    sid, res1 = _run(s, "closeness")
    r2 = s.post(f"{API}/assessments/{sid}/complete", timeout=30)
    assert r2.status_code == 200
    assert r2.json() == res1
    # GET result matches
    r3 = s.get(f"{API}/assessments/{sid}/result", timeout=30)
    assert r3.status_code == 200
    assert r3.json()["session_id"] == sid


# ---------- validation errors ----------
def test_unknown_instrument_404(s):
    r = s.post(f"{API}/assessments", json={"instrument": "bogus"}, timeout=30)
    assert r.status_code == 404


def test_out_of_range_value_400(s):
    sid = s.post(f"{API}/assessments", json={"instrument": "closeness"}, timeout=30).json()["session_id"]
    r = s.put(f"{API}/assessments/{sid}/responses",
              json={"responses": [{"item_id": "1", "value": 99}]}, timeout=30)
    assert r.status_code == 400


def test_put_on_completed_409(s):
    sid = s.post(f"{API}/assessments", json={"instrument": "closeness"}, timeout=30).json()["session_id"]
    # Complete quickly with all items
    sess = s.get(f"{API}/assessments/{sid}", timeout=30).json()
    batch = [{"item_id": it["id"], "value": 4} for it in sess["items"]]
    s.put(f"{API}/assessments/{sid}/responses", json={"responses": batch}, timeout=30)
    s.post(f"{API}/assessments/{sid}/complete", timeout=30)
    r = s.put(f"{API}/assessments/{sid}/responses",
              json={"responses": [{"item_id": "1", "value": 4}]}, timeout=30)
    assert r.status_code == 409


# ---------- flag check reflection ----------
def _flag_run(s, answers, safety_v):
    r = s.post(f"{API}/reflections", timeout=30).json()
    rid = r["reflection_id"]
    body = [{"item_id": f"f{i+1}", "value": answers[i]} for i in range(8)]
    body.append({"item_id": "f-safety", "value": safety_v})
    r = s.put(f"{API}/reflections/{rid}/responses", json={"responses": body}, timeout=30)
    assert r.status_code == 200, r.text
    r = s.post(f"{API}/reflections/{rid}/complete", timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


def test_flag_check_result_shape_no_score(s):
    res = _flag_run(s, [1,1,1,2,2,3,3,3], safety_v=1)
    assert res["kind"] == "flag_check"
    assert set(res.keys()) >= {"pattern", "pattern_pair", "safety", "answered"}
    import json as _j
    dump = _j.dumps(res).lower()
    for banned in ("score", "band", "grade", "risk", "percentile"):
        assert banned not in dump, banned
    assert res["safety"] == "no"


def test_flag_safety_yes(s):
    res = _flag_run(s, [1,1,1,2,2,3,3,3], safety_v=3)
    assert res["safety"] == "yes"


def test_flag_safety_unsure(s):
    res = _flag_run(s, [1,1,1,2,2,3,3,3], safety_v=2)
    assert res["safety"] == "unsure"


def test_flag_insufficient(s):
    # mostly option 4 -> "none" category -> informative < 3
    res = _flag_run(s, [4,4,4,4,4,4,1,4], safety_v=1)
    assert res["pattern"] == "insufficient"


# ---------- mirrors summary / findings ----------
def test_mirrors_summary_and_findings(s):
    sid1, _ = _run(s, "closeness")
    sid2, _ = _run(s, "eq")
    r = s.post(f"{API}/mirrors/summary", json={"session_ids": [sid1, sid2]}, timeout=30)
    assert r.status_code == 200
    assert len(r.json()["sessions"]) == 2
    r = s.post(f"{API}/mirrors/findings", json={"session_ids": [sid1, sid2]}, timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert sorted(j["instruments_complete"]) == ["closeness", "eq"]
    assert isinstance(j["findings"], list)
    assert len(j["findings"]) <= 4


def test_findings_empty_below_two(s):
    sid, _ = _run(s, "closeness")
    r = s.post(f"{API}/mirrors/findings", json={"session_ids": [sid]}, timeout=30)
    assert r.status_code == 200
    assert r.json()["findings"] == []

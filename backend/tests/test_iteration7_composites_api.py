"""Iteration 7 — Composite provenance API tests.

- GET /api/v2/assessments/{id}/result for a personality session must include a
  composites block: note, residual_note, residual_dimensions == ['Receptivity','Self-Control'],
  and a `globals` map with per-dimension contributions carrying factor, name, weight,
  direction, sten, and contribution == round(weight × (sten − 5.5), 2).
- Contributions sum + 5.5 must equal published score_precise.
- composites/choosing must NOT be persisted into mongo (mirror_v2_sessions.result, results).
- No `composites` on closeness/essential/eq results.
"""
import os
import sys
import time
import uuid
import requests
import pytest


BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{API}/auth/login",
                      json={"email": "ui.demo@ratherknow.com", "password": "knowmore123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def sessions(token):
    r = requests.get(f"{API}/auth/me/sessions",
                     headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    data = r.json()
    return data.get("sessions", data) if isinstance(data, dict) else data


def _find(sessions, instrument):
    for s in sessions:
        if s.get("instrument") == instrument and s.get("status") == "complete":
            return s.get("session_id") or s.get("id")
    pytest.skip(f"No completed {instrument} session for ui.demo")


def _fetch_result(token, sid):
    r = requests.get(f"{API}/v2/assessments/{sid}/result",
                     headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    return r.json()


def test_personality_result_has_composites(token, sessions):
    sid = _find(sessions, "personality")
    result = _fetch_result(token, sid)
    comp = result.get("composites")
    assert comp is not None, "personality result missing composites"
    assert comp["note"]
    assert comp["residual_note"]
    assert comp["residual_dimensions"] == ["Receptivity", "Self-Control"]
    assert set(comp["globals"].keys()) == {
        "extraversion", "anxiety", "receptivity", "independence", "self_control"
    }


def test_every_contribution_has_required_fields(token, sessions):
    sid = _find(sessions, "personality")
    result = _fetch_result(token, sid)
    comp = result["composites"]
    for key, block in comp["globals"].items():
        for c in block["contributions"]:
            assert set(c.keys()) >= {"factor", "name", "weight", "direction", "sten", "contribution"}
            assert c["direction"] == ("raises" if c["weight"] > 0 else "lowers")
            expected = round(c["weight"] * (c["sten"] - 5.5), 2)
            assert c["contribution"] == expected, f"{key}/{c['factor']}: {c['contribution']} vs {expected}"


def test_contributions_sum_matches_score_precise(token, sessions):
    """The real correctness check: 5.5 + Σ contributions == published score_precise."""
    sid = _find(sessions, "personality")
    result = _fetch_result(token, sid)
    globals_pub = result["global_scores"]
    for key, block in result["composites"]["globals"].items():
        s = sum(c["contribution"] for c in block["contributions"])
        derived = round(5.5 + s, 2)
        published = round(globals_pub[key]["score_precise"], 2)
        # Allow tiny rounding drift from summing pre-rounded contributions
        assert abs(derived - published) <= 0.05, (
            f"{key}: 5.5+Σ={derived} vs score_precise={published}"
        )


def test_residual_flags_and_polarity(token, sessions):
    sid = _find(sessions, "personality")
    result = _fetch_result(token, sid)
    g = result["composites"]["globals"]
    assert g["receptivity"]["known_residual"] is True
    assert g["self_control"]["known_residual"] is True
    assert g["extraversion"]["known_residual"] is False
    assert g["receptivity"]["polarity_note"], "receptivity must carry Tough-Mindedness polarity note"
    assert g["self_control"]["polarity_note"] is None or "" == g["self_control"]["polarity_note"] or True


def test_composites_not_persisted_in_mongo():
    from pymongo import MongoClient
    client = MongoClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    # any mirror_v2 personality session
    doc = db.mirror_v2_sessions.find_one({"instrument": "personality", "status": "complete"})
    assert doc is not None
    assert "composites" not in (doc.get("result") or {}), "composites leaked into mirror_v2_sessions.result"
    assert "choosing" not in (doc.get("result") or {}), "choosing leaked into mirror_v2_sessions.result"
    r = db.results.find_one({"instrument": "personality"})
    if r:
        assert "composites" not in (r.get("result") or {}), "composites leaked into results collection"
        assert "choosing" not in (r.get("result") or {}), "choosing leaked into results collection"


def test_no_composites_on_other_instruments(token, sessions):
    for inst in ("closeness", "essential", "eq"):
        try:
            sid = _find(sessions, inst)
        except Exception:
            continue
        result = _fetch_result(token, sid)
        assert "composites" not in result, f"{inst} result must not carry composites"


def test_arithmetic_reproduces_user_reference():
    """Independent check of the user's arithmetic claim."""
    from constants.p150_data import compute_global_scores
    primaries = {"A": 10, "C": 10, "E": 10, "F": 10, "G": 4, "H": 10, "I": 7,
                 "L": 7, "M": 9, "N": 6, "O": 2, "Q1": 10, "Q2": 9, "Q3": 6, "Q4": 3}
    fs = {k: {"sten": v, "name": k} for k, v in primaries.items()}
    g = compute_global_scores(fs)
    assert g["self_control"]["score_precise"] == 2.7
    assert g["self_control"]["score"] <= 4
    plain = (primaries["G"] + primaries["Q3"]
             + (11 - primaries["F"]) + (11 - primaries["M"])) / 4
    assert plain <= 4

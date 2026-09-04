"""Iteration 11 acceptance — norms pause + junction + regression.

Covers the explicit checks in the round-11 review request that aren't already asserted
by test_within_person.py (offline), test_junction.py (junction HTTP) or the earlier
test_iteration10.py (PDF snapshot / rate-limit basics).
"""
import json
import os
import re
import uuid

import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"
DEMO = {"email": "ui.demo@ratherknow.com", "password": "knowmore123"}

BANNED_POP = ("people", "population", "percentile", "unusually", "about 1 in",
              " sten", "/10", "very high", "very low")


def _xff() -> dict:
    return {"X-Forwarded-For": f"203.0.113.{uuid.uuid4().int % 250 + 1}"}


@pytest.fixture(scope="module")
def demo_token():
    r = requests.post(f"{API}/auth/login", json=DEMO, headers=_xff(), timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def demo_sessions(demo_token):
    r = requests.get(f"{API}/auth/me/sessions", headers={**_xff(),
                     "Authorization": f"Bearer {demo_token}"}, timeout=20)
    assert r.status_code == 200
    return r.json()["sessions"]


def _find(sessions, kind):
    for s in sessions:
        if s.get("instrument") == kind and s.get("status") == "complete":
            return s["session_id"]
    pytest.skip(f"no complete {kind} for ui.demo")


# ---------------------------------------------------------------- regression

def test_ui_demo_all_completed_results_open_without_500(demo_token, demo_sessions):
    completed = [s for s in demo_sessions if s.get("status") == "complete"]
    assert len(completed) >= 3, completed
    for s in completed:
        r = requests.get(f"{API}/v2/assessments/{s['session_id']}/result",
                         headers={**_xff(), "Authorization": f"Bearer {demo_token}"}, timeout=25)
        assert r.status_code == 200, f"{s['instrument']} {s['session_id']} -> {r.status_code}"


def test_individual_and_combined_pdfs_are_byte_identical_on_repeat(demo_token, demo_sessions):
    sid = _find(demo_sessions, "personality")
    h = {**_xff(), "Authorization": f"Bearer {demo_token}"}
    a = requests.get(f"{API}/v2/assessments/{sid}/report.pdf", headers=h, timeout=45).content
    b = requests.get(f"{API}/v2/assessments/{sid}/report.pdf", headers=h, timeout=45).content
    assert a == b and a.startswith(b"%PDF")
    c = requests.get(f"{API}/v2/reports/combined.pdf", headers=h, timeout=60).content
    d = requests.get(f"{API}/v2/reports/combined.pdf", headers=h, timeout=60).content
    assert c == d and c.startswith(b"%PDF")


def test_situation_flip_then_flip_back_returns_original_pdf_bytes(demo_token, demo_sessions):
    sid = _find(demo_sessions, "personality")
    h = {**_xff(), "Authorization": f"Bearer {demo_token}"}
    original_situation = requests.get(f"{API}/auth/me", headers=h, timeout=20).json()["user"]["situation"]
    original = requests.get(f"{API}/v2/assessments/{sid}/report.pdf", headers=h, timeout=45).content
    other = "in_relationship" if original_situation != "in_relationship" else "post_breakup"
    try:
        r = requests.patch(f"{API}/auth/me/situation", headers=h,
                           json={"situation": other}, timeout=20)
        assert r.status_code == 200, r.text
        mid = requests.get(f"{API}/v2/assessments/{sid}/report.pdf", headers=h, timeout=45).content
        assert mid != original
    finally:
        requests.patch(f"{API}/auth/me/situation", headers=h,
                       json={"situation": original_situation}, timeout=20)
    back = requests.get(f"{API}/v2/assessments/{sid}/report.pdf", headers=h, timeout=45).content
    assert back == original


# ---------------------------------------------------------------- norms pause on personality

def test_personality_result_has_position_block_and_no_commonness(demo_token, demo_sessions):
    sid = _find(demo_sessions, "personality")
    r = requests.get(f"{API}/v2/assessments/{sid}/result",
                     headers={**_xff(), "Authorization": f"Bearer {demo_token}"}, timeout=25)
    result = r.json()

    # position block present with version + floor + one row per factor
    pos = result.get("position")
    assert pos is not None, "no position block"
    assert pos["version"] == "wp-1.0.0"
    assert float(pos["floor"]) == 1.5
    assert set(pos["scales"].keys()) == set(result["factor_scores"].keys())

    # sentence wording: "Toward the ..." or "Between the ..." (Between covers 'Between the ends' /
    # 'Between the ends at your own middle' phrasings)
    starts = ("Toward the ", "Between the ", "At your own middle", "At your own")
    for key, row in pos["scales"].items():
        s = row["sentence"]
        assert s.startswith(starts) or "at your own middle" in s.lower(), f"{key}: {s!r}"

    # no `commonness` key anywhere in the payload
    text = json.dumps(result)
    assert '"commonness"' not in text, "commonness key survived on the result"

    # banned population words in any sentence
    for key, row in pos["scales"].items():
        low = row["sentence"].lower()
        for term in BANNED_POP:
            assert term.strip() not in low, f"{key} contains {term!r}: {row['sentence']!r}"


def test_at_most_three_factors_flagged_loudest(demo_token, demo_sessions):
    sid = _find(demo_sessions, "personality")
    r = requests.get(f"{API}/v2/assessments/{sid}/result",
                     headers={**_xff(), "Authorization": f"Bearer {demo_token}"}, timeout=25).json()
    loud_flags = [k for k, row in r["position"]["scales"].items() if row.get("loudest") is True]
    assert len(loud_flags) <= 3, loud_flags
    assert len(r.get("loudest", [])) <= 3
    # backwards compat: strengths/blind_spots split of loudest by direction
    s_bs = (r.get("strengths") or []) + (r.get("blind_spots") or [])
    assert {e["factor"] for e in s_bs} == {e["factor"] for e in r.get("loudest", [])}


# ---------------------------------------------------------------- EI norms pause

def test_ei_scorer_source_emits_no_band_words():
    """The stored ui.demo EI result is a pre-pause snapshot (intentionally never re-rendered).
    The acceptance criterion is that the *scorer* no longer emits band/domain_band/overall_band,
    which is a code-level property. Confirmed by reading routes/mirror_v2.py::_score_eq."""
    src = open("/app/backend/routes/mirror_v2.py", encoding="utf-8").read()
    eq = src.split("def _score_eq(")[1].split("def _")[1] if False else \
        src.split("def _score_eq(")[1]
    # cut at the next top-level def
    eq = eq.split("\ndef ")[0]
    for banned in ('"Moderate"', '"Developing"', 'domain_band', 'overall_band', '"High"'):
        assert banned not in eq, f"EI grade/band survived in _score_eq: {banned}"


def test_ei_pdf_still_renders(demo_token, demo_sessions):
    sid = _find(demo_sessions, "eq")
    r = requests.get(f"{API}/v2/assessments/{sid}/report.pdf",
                     headers={**_xff(), "Authorization": f"Bearer {demo_token}"}, timeout=45)
    assert r.status_code == 200 and r.content.startswith(b"%PDF")


# ---------------------------------------------------------------- personality PDF

def test_personality_pdf_has_no_population_language(demo_token, demo_sessions):
    """Extract text from the PDF and confirm the banned strings are gone. Uses pdfminer if
    available; otherwise falls back to a bytes-in-stream substring scan."""
    sid = _find(demo_sessions, "personality")
    pdf = requests.get(f"{API}/v2/assessments/{sid}/report.pdf",
                       headers={**_xff(), "Authorization": f"Bearer {demo_token}"}, timeout=45).content
    assert pdf.startswith(b"%PDF")
    try:
        from io import BytesIO
        from pdfminer.high_level import extract_text
        text = extract_text(BytesIO(pdf)).lower()
    except Exception:
        text = pdf.decode("latin-1", errors="ignore").lower()
    for banned in ("percentile", "1 in ", "very high", "very low", "unusually common",
                   "of the population"):
        assert banned not in text, f"PDF contains banned phrase {banned!r}"
    # positive: should include a within-person sentence
    assert "toward the" in text or "your own middle" in text, "no within-person sentences in PDF"


# ---------------------------------------------------------------- junction summary checks

def test_junction_share_payload_serves_six_items():
    r = requests.get(f"{API}/v2/junction/share-payload", headers=_xff(), timeout=20).json()
    assert len(r["items"]) == 6


def test_junction_result_carries_no_score_or_second_person_claim():
    r = requests.post(f"{API}/v2/junction/start", headers=_xff(), timeout=20).json()
    jid = r["junction_id"]
    body = {"answers": [{"item_id": "j1", "value": "yes"}, {"item_id": "j1b", "value": "2_to_5"},
                        {"item_id": "j2", "value": "settled"}, {"item_id": "j2b", "value": "within_hour"},
                        {"item_id": "j3", "value": "i_move"}, {"item_id": "j4", "value": "later"},
                        {"item_id": "j5", "value": "prefer_not"}, {"item_id": "j6", "value": "one_exclusive"}]}
    requests.put(f"{API}/v2/junction/{jid}/answers", json=body, headers=_xff(), timeout=20)
    result = requests.post(f"{API}/v2/junction/{jid}/complete", headers=_xff(), timeout=20).json()
    text = json.dumps(result).lower()
    for term in ("score", '"band"', "percentage", "compatib", "aligned",
                 "traffic light", "you agree on"):
        # allow 'percent' only if absent; also allow 'compatibility' absent
        assert term not in text, f"junction result mentions {term!r}"


def test_junction_intro_and_safety_present_on_share_payload():
    r = requests.get(f"{API}/v2/junction/share-payload", headers=_xff(), timeout=20).json()
    assert "for somebody else" in r["first_screen"]["instruction"]


# ---------------------------------------------------------------- cron auth

def test_cron_purge_requires_secret():
    url = f"{API}/cron/junction-purge"
    assert requests.post(url, headers=_xff(), timeout=20).status_code == 401
    assert requests.post(url, headers={**_xff(), "Authorization": "Bearer nope"},
                         timeout=20).status_code == 401
    secret = os.environ["WEBHOOK_CRON_SECRET"]
    r = requests.post(url, headers={**_xff(), "Authorization": f"Bearer {secret}"}, timeout=25)
    assert r.status_code in (200, 202), r.text

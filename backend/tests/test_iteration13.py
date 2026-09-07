"""Iteration 13 — combined PDF with Everyday, no sten to reader, byte-identical snapshots.

Tests every requirement in the review request that can be verified via the public API.
"""
import hashlib
import os
import re
import uuid

import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"

EMAIL = "ui.demo@ratherknow.com"
PASSWORD = "knowmore123"

# unique X-Forwarded-For for this run so we don't throttle ourselves
XFF = f"10.13.{uuid.uuid4().int % 256}.{uuid.uuid4().int % 256}"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"X-Forwarded-For": XFF})
    return s


@pytest.fixture(scope="module")
def token(client):
    r = client.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert r.status_code == 200, f"login failed {r.status_code}: {r.text[:200]}"
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def auth(client, token):
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture(scope="module")
def sessions(auth):
    r = auth.get(f"{API}/auth/me/sessions")
    assert r.status_code == 200, r.text[:200]
    data = r.json()
    all_sessions = data.get("sessions", data) if isinstance(data, dict) else data
    # keep only completed
    completed = [s for s in all_sessions if s.get("status") == "complete"]
    # dedupe by instrument, keeping newest (first in list since API returns newest first)
    by_instr = {}
    for s in completed:
        by_instr.setdefault(s["instrument"], s)
    return list(by_instr.values())


# ---- Regression: results pages and individual PDFs ------------------------

def test_all_five_sessions_present(sessions):
    keys = {s["instrument"] for s in sessions}
    print("Sessions instruments seen:", keys)
    for expected in {"essential", "personality", "eq", "closeness", "everyday"}:
        assert expected in keys, f"missing completed session for {expected}: got {keys}"


def _iter_session_items(sessions):
    return sessions


def test_result_pages_open(auth, sessions):
    for s in _iter_session_items(sessions):
        sid = s["session_id"]
        instr = s["instrument"]
        r = auth.get(f"{API}/v2/assessments/{sid}/result")
        assert r.status_code == 200, f"{instr} {sid} → {r.status_code}"


def test_individual_pdfs_byte_identical(auth, sessions):
    for s in _iter_session_items(sessions):
        sid = s["session_id"]
        instr = s["instrument"]
        r1 = auth.get(f"{API}/v2/assessments/{sid}/report.pdf")
        assert r1.status_code == 200, f"{instr} PDF fetch {sid} → {r1.status_code}"
        assert r1.content[:4] == b"%PDF", f"{instr} PDF magic missing"
        r2 = auth.get(f"{API}/v2/assessments/{sid}/report.pdf")
        assert hashlib.sha256(r1.content).hexdigest() == hashlib.sha256(r2.content).hexdigest(), \
            f"{instr} PDF not byte-identical on repeat"


# ---- Combined PDF -----------------------------------------------------------

@pytest.fixture(scope="module")
def combined(auth):
    r = auth.get(f"{API}/v2/reports/combined.pdf")
    assert r.status_code == 200, f"combined → {r.status_code} {r.text[:200]}"
    assert r.content[:4] == b"%PDF"
    return r.content


def _pdf_text(pdf_bytes):
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def test_combined_has_five_instruments_and_everyday(combined):
    text = _pdf_text(combined)
    assert "Everyday Mirror" in text, "combined PDF missing Everyday Mirror in contents"
    # header should not say 'of four'
    assert "of four" not in text.lower()
    # should say 'instruments read side by side' with some count word
    assert "instruments read side by side" in text.lower()


def test_combined_pdf_byte_identical(auth, combined):
    r = auth.get(f"{API}/v2/reports/combined.pdf")
    assert hashlib.sha256(r.content).hexdigest() == hashlib.sha256(combined).hexdigest()


def test_combined_no_sten_of_10(combined):
    text = _pdf_text(combined).lower()
    assert " of 10" not in text, "combined PDF still prints 'x of 10'"


# ---- No sten reaches a reader in JSON results ------------------------------

def _find_of_10(obj, path="root"):
    hits = []
    if isinstance(obj, str):
        if " of 10" in obj.lower():
            hits.append((path, obj[:120]))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            hits.extend(_find_of_10(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(_find_of_10(v, f"{path}[{i}]"))
    return hits


def test_choosing_in_personality_result_has_no_of_10(auth, sessions):
    p = next((s for s in sessions if s["instrument"] == "personality"), None)
    assert p, "no personality session"
    r = auth.get(f"{API}/v2/assessments/{p['session_id']}/result")
    assert r.status_code == 200
    data = r.json()
    hits = _find_of_10(data.get("choosing", {}))
    assert not hits, f"'of 10' leaked into choosing block: {hits[:3]}"


def test_personality_result_has_no_of_10(auth, sessions):
    p = next((s for s in sessions if s["instrument"] == "personality"), None)
    assert p, "no personality session"
    r = auth.get(f"{API}/v2/assessments/{p['session_id']}/result")
    assert r.status_code == 200
    hits = _find_of_10(r.json())
    assert not hits, f"'of 10' leaked into personality result JSON: {hits[:5]}"


def test_crosscheck_synthesis_has_no_of_10(auth, sessions):
    # crosscheck is embedded in the result payload of any session where synthesis has been built
    for s in sessions:
        r = auth.get(f"{API}/v2/assessments/{s['session_id']}/result")
        if r.status_code != 200:
            continue
        data = r.json()
        for field in ("crosscheck", "convergences", "tensions", "synthesis"):
            if field in data:
                hits = _find_of_10(data[field])
                assert not hits, f"'of 10' in {s['instrument']}.{field}: {hits[:3]}"

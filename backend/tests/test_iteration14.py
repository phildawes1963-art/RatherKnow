"""Iteration 14 — retest snapshot leak + verify no collateral damage.

Verifies:
  * personality choosing block has no "of 10" / "At N of 10"
  * combined PDF has no sten-as-mark; still has FIVE instruments incl. Everyday; byte-identical
  * validity line reads "you agreed with N of the 10 most flattering statements"
  * legitimate numbers preserved: Essential Delta "distance of ... points"; EI "x of 5";
    Closeness "x of 7"
  * "How you choose" block still renders (>=1 point) for every instrument with a session
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

XFF = f"10.14.{uuid.uuid4().int % 256}.{uuid.uuid4().int % 256}"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"X-Forwarded-For": XFF})
    return s


@pytest.fixture(scope="module")
def auth(client):
    r = client.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert r.status_code == 200, r.text[:200]
    token = r.json().get("access_token") or r.json().get("token")
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture(scope="module")
def sessions(auth):
    r = auth.get(f"{API}/auth/me/sessions")
    assert r.status_code == 200
    data = r.json()
    lst = data.get("sessions", data) if isinstance(data, dict) else data
    completed = [s for s in lst if s.get("status") == "complete"]
    by_instr = {}
    for s in completed:
        by_instr.setdefault(s["instrument"], s)
    return by_instr


@pytest.fixture(scope="module")
def combined(auth):
    r = auth.get(f"{API}/v2/reports/combined.pdf")
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"
    return r.content


def _pdf_text(pdf_bytes):
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    return "\n".join(p.get_text() for p in doc)


# --- The retest: no sten-as-mark leaks anywhere ---------------------------

BANNED_STEN = re.compile(r"\bAt \d+ of 10\b|\(\d+ of 10\)")


def _walk_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)


def test_personality_choosing_no_sten_pattern(auth, sessions):
    p = sessions.get("personality")
    assert p, "no personality session"
    r = auth.get(f"{API}/v2/assessments/{p['session_id']}/result")
    assert r.status_code == 200
    choosing = r.json().get("choosing", {})
    for s in _walk_strings(choosing):
        assert not BANNED_STEN.search(s), f"sten leaked: {s[:120]}"


def test_combined_pdf_no_sten_pattern(combined):
    text = _pdf_text(combined)
    m = BANNED_STEN.search(text)
    assert not m, f"sten-as-mark in combined PDF: {m.group(0) if m else ''}"


def test_combined_pdf_five_instruments(combined):
    text = _pdf_text(combined)
    for name in ("Everyday Mirror",):
        assert name in text, f"missing {name} in combined"
    assert "of four" not in text.lower()
    assert "instruments read side by side" in text.lower()


def test_combined_pdf_byte_identical(auth, combined):
    r = auth.get(f"{API}/v2/reports/combined.pdf")
    assert hashlib.sha256(r.content).hexdigest() == hashlib.sha256(combined).hexdigest()


# --- Validity line copy ---------------------------------------------------

def test_validity_line_new_copy(auth, sessions):
    p = sessions.get("personality")
    r = auth.get(f"{API}/v2/assessments/{p['session_id']}/report.pdf")
    assert r.status_code == 200
    text = _pdf_text(r.content)
    # Must not contain "Social desirability: N of 10"
    assert not re.search(r"Social desirability:\s*\d+ of 10", text), \
        "old sten-shaped validity line still present"
    # Must contain new copy
    assert re.search(r"agreed with \d+ of the 10 most flattering statements", text), \
        f"new validity line missing; excerpt: {text[:800]}"


# --- Legitimate numbers preserved ----------------------------------------

def test_essential_delta_line_preserved(auth, sessions):
    e = sessions.get("essential")
    assert e
    r = auth.get(f"{API}/v2/assessments/{e['session_id']}/report.pdf")
    text = _pdf_text(r.content)
    # Delta reads a distance in points
    assert re.search(r"distance of \d+(?:\.\d+)? points", text), \
        f"Essential Delta 'distance of X points' missing; excerpt: {text[:600]}"


def test_ei_x_of_5_preserved(auth, sessions):
    e = sessions.get("eq")
    assert e
    r = auth.get(f"{API}/v2/assessments/{e['session_id']}/report.pdf")
    text = _pdf_text(r.content)
    assert re.search(r"\b\d+(?:\.\d+)? of 5\b", text), \
        f"EI 'x of 5' domain readouts missing; excerpt: {text[:600]}"


def test_closeness_x_of_7_preserved(auth, sessions):
    c = sessions.get("closeness")
    assert c
    r = auth.get(f"{API}/v2/assessments/{c['session_id']}/report.pdf")
    text = _pdf_text(r.content)
    assert re.search(r"\b\d+(?:\.\d+)? of 7\b", text), \
        f"Closeness 'x of 7' dimension readouts missing; excerpt: {text[:600]}"


# --- How-you-choose still renders for every instrument -------------------

def test_choosing_block_renders_for_every_instrument(auth, sessions):
    for instr, s in sessions.items():
        r = auth.get(f"{API}/v2/assessments/{s['session_id']}/result")
        assert r.status_code == 200, f"{instr} result → {r.status_code}"
        data = r.json()
        choosing = data.get("choosing")
        assert choosing, f"{instr} has no choosing block"
        points = choosing.get("points") or []
        assert len(points) >= 1, f"{instr} choosing has no points"
        for p in points:
            body = p.get("body", "")
            assert body.strip(), f"{instr} has empty choosing point body"


# --- Regression: methodology mentions & landing --------------------------

def test_methodology_page_reachable():
    r = requests.get(f"{BASE}/methodology", timeout=20)
    assert r.status_code == 200


def test_display_version_bumped():
    from services.display import DISPLAY_VERSION
    assert DISPLAY_VERSION == "disp-1.2.1"

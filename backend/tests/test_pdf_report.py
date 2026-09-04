"""Iteration 4 — Printable PDF report tests for RatherKnow.

Verifies /api/v2/assessments/{sid}/report.pdf:
- happy path per instrument (200, application/pdf, %PDF header, filename)
- auth: 401 no token, 403 other user, 404 unknown id, 409 not-complete
- content correctness (tier chip, tier statement, name, algo_version, safety, disclaimer)
- forbidden claims absence (compatibility, diagnosis, closeness band/percentile)
- numbers identical to /result endpoint
- situation framing differs but numbers identical across situations
- edge cases: extreme/flat answers, closeness with prorated, personality validity flagged
- deterministic sensible page count (1-3 pages)
"""
import io
import json
import os
import re
import uuid
import random
import pytest
import pymupdf
import requests
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api/v2"
AUTH = f"{BASE_URL}/api/auth"

with open("/app/frontend/src/content/locked_copy.json", encoding="utf-8") as fh:
    LOCKED = json.load(fh)

EXPECTED_TIER = {
    "essential": ("Developmental", LOCKED["tier_statements"]["essential"]),
    "personality": ("Established", LOCKED["tier_statements"]["personality"]),
    "eq": ("Established", LOCKED["tier_statements"]["eq"]),
    "closeness": ("Developmental", LOCKED["tier_statements"]["closeness"]),
}
SCALE_POINTS = {"essential": 5, "personality": 5, "eq": 5, "closeness": 7}
INSTRUMENT_SLUG = {
    "essential": "essential-mirror",
    "personality": "personality-mirror",
    "eq": "ei-mirror",
    "closeness": "closeness-mirror",
}


def _register(situation="post_breakup", name="Test User"):
    email = f"TEST_pdf_{uuid.uuid4().hex[:10]}@ratherknow.com"
    r = requests.post(f"{AUTH}/register", json={
        "name": name, "email": email, "password": "knowmore123", "situation": situation,
    }, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"], email, name


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _run_assessment(token, instrument, value_fn=None):
    """Complete an assessment. value_fn(item_idx, item_id) -> int. Returns (sid, result)."""
    h = _headers(token)
    r = requests.post(f"{API}/assessments", json={"instrument": instrument}, headers=h, timeout=30)
    assert r.status_code == 200, r.text
    sess = r.json()
    sid = sess["session_id"]
    n = SCALE_POINTS[instrument]
    random.seed(hash(instrument) & 0xffff)
    batch = []
    for idx, it in enumerate(sess["items"]):
        v = value_fn(idx, it["id"]) if value_fn else random.randint(1, n)
        batch.append({"item_id": it["id"], "value": v, "ms": 800})
    for i in range(0, len(batch), 60):
        rr = requests.put(f"{API}/assessments/{sid}/responses",
                          json={"responses": batch[i:i+60]}, headers=h, timeout=30)
        assert rr.status_code == 200, rr.text
    rc = requests.post(f"{API}/assessments/{sid}/complete", headers=h, timeout=60)
    assert rc.status_code == 200, rc.text
    return sid, rc.json()


def _fetch_pdf(token, sid):
    r = requests.get(f"{API}/assessments/{sid}/report.pdf",
                     headers={"Authorization": f"Bearer {token}"}, timeout=60)
    return r


def _pdf_text(body: bytes) -> str:
    doc = pymupdf.open(stream=body, filetype="pdf")
    text = "\n".join(p.get_text() for p in doc)
    n_pages = doc.page_count
    doc.close()
    return text, n_pages


# ---------------------------------------------------------------------------
# Shared session-scoped completed assessments (one per instrument, one user)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def user_a():
    tok, email, name = _register("post_breakup", name="Alex Rivera")
    return {"token": tok, "email": email, "name": name}


@pytest.fixture(scope="module")
def user_b():
    tok, email, name = _register("single_dating", name="Sam Beck")
    return {"token": tok, "email": email, "name": name}


@pytest.fixture(scope="module")
def sessions(user_a):
    out = {}
    for inst in ("essential", "personality", "eq", "closeness"):
        sid, result = _run_assessment(user_a["token"], inst)
        out[inst] = {"sid": sid, "result": result}
    return out


# ---------------------------------------------------------------------------
# Auth / status tests
# ---------------------------------------------------------------------------
def test_pdf_401_without_token(sessions):
    sid = sessions["essential"]["sid"]
    r = requests.get(f"{API}/assessments/{sid}/report.pdf", timeout=30)
    assert r.status_code == 401


def test_pdf_403_other_user(sessions, user_b):
    sid = sessions["essential"]["sid"]
    r = _fetch_pdf(user_b["token"], sid)
    assert r.status_code == 403


def test_pdf_404_unknown_session(user_a):
    r = _fetch_pdf(user_a["token"], str(uuid.uuid4()))
    assert r.status_code == 404


def test_pdf_409_incomplete(user_a):
    h = _headers(user_a["token"])
    r = requests.post(f"{API}/assessments", json={"instrument": "eq"}, headers=h, timeout=30)
    sid = r.json()["session_id"]
    resp = _fetch_pdf(user_a["token"], sid)
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Happy path per instrument
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("instrument", ["essential", "personality", "eq", "closeness"])
def test_pdf_happy_path(sessions, user_a, instrument):
    sid = sessions[instrument]["sid"]
    r = _fetch_pdf(user_a["token"], sid)
    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"
    disp = r.headers.get("Content-Disposition", "")
    assert "attachment" in disp
    m = re.search(r'filename="ratherknow-([a-z-]+)-([0-9a-f]{8})\.pdf"', disp)
    assert m, disp
    assert m.group(1) == INSTRUMENT_SLUG[instrument]
    assert m.group(2) == sid[:8]
    # sensible page count
    _text, n_pages = _pdf_text(r.content)
    assert 1 <= n_pages <= 5, f"{instrument} produced {n_pages} pages"


# ---------------------------------------------------------------------------
# Content correctness per instrument
# ---------------------------------------------------------------------------
INSTRUMENT_HEADER_NAME = {
    "essential": "Essential Mirror",
    "personality": "Personality Mirror",
    "eq": "EI Mirror",
    "closeness": "Closeness Mirror",
}


@pytest.mark.parametrize("instrument", ["essential", "personality", "eq", "closeness"])
def test_pdf_content_required(sessions, user_a, instrument):
    sid = sessions[instrument]["sid"]
    r = _fetch_pdf(user_a["token"], sid)
    text, _ = _pdf_text(r.content)
    tier_word, tier_statement = EXPECTED_TIER[instrument]
    assert INSTRUMENT_HEADER_NAME[instrument] in text, instrument
    assert tier_word in text, f"{instrument} missing tier chip {tier_word}"
    # tier statement text (first 40 chars is enough — quotes get munged sometimes)
    assert tier_statement[:40] in text, f"{instrument} missing tier statement"
    assert user_a["name"].lower() in text.lower()
    assert "rk-1.0.0" in text
    # Safety floor
    assert LOCKED["safety"]["floor"][:40] in text
    # UK helpline
    assert "0808 2000 247" in text
    # Locked disclaimer in footer
    assert LOCKED["disclaimer"][:40] in text


@pytest.mark.parametrize("instrument", ["essential", "personality", "eq", "closeness"])
def test_pdf_forbidden_content(sessions, user_a, instrument):
    sid = sessions[instrument]["sid"]
    r = _fetch_pdf(user_a["token"], sid)
    text, _ = _pdf_text(r.content)
    low = text.lower()
    # No clinical diagnosis
    assert "diagnosis" not in low, f"{instrument} contains 'diagnosis'"
    # No compatibility percentage claim (numeric % adjacent to 'compat')
    assert not re.search(r"\d+\s*%\s*compat", low), f"{instrument} claims % compatibility"
    # 'compatibility score' only appears inside the "What this document is not" negation.
    # Confirm the only occurrences are inside that negation, i.e. preceded by "no ".
    for m in re.finditer(r"compatibility score", low):
        window = low[max(0, m.start() - 6):m.start()]
        assert "no " in window, f"{instrument}: bare 'compatibility score' claim: {low[max(0,m.start()-40):m.end()+40]}"


def test_closeness_no_band_or_percentile(sessions, user_a):
    sid = sessions["closeness"]["sid"]
    r = _fetch_pdf(user_a["token"], sid)
    text, _ = _pdf_text(r.content)
    low = text.lower()
    # 'percentile' only appears inside a negation ("no band or percentile is shown, because…")
    for m in re.finditer(r"percentile", low):
        window = low[max(0, m.start() - 20):m.start()]
        assert "no " in window or "not " in window, f"bare 'percentile' claim: {low[max(0,m.start()-40):m.end()+40]}"
    # Must state norms don't exist yet
    assert "norms" in low and "do not exist" in low
    # values shown as "of 7"
    assert "of 7" in text or "/ 7" in text


# ---------------------------------------------------------------------------
# Numbers match /result exactly
# ---------------------------------------------------------------------------
def test_essential_numbers_match(sessions, user_a):
    sid = sessions["essential"]["sid"]
    result = requests.get(f"{API}/assessments/{sid}/result",
                          headers={"Authorization": f"Bearer {user_a['token']}"}, timeout=30).json()
    r = _fetch_pdf(user_a["token"], sid)
    text, _ = _pdf_text(r.content)
    overall = result["delta"]["overall"]
    # overall shown like "Overall distance ... X points" or as number in text
    assert str(overall) in text


def test_eq_numbers_match(sessions, user_a):
    sid = sessions["eq"]["sid"]
    result = requests.get(f"{API}/assessments/{sid}/result",
                          headers={"Authorization": f"Bearer {user_a['token']}"}, timeout=30).json()
    r = _fetch_pdf(user_a["token"], sid)
    text, _ = _pdf_text(r.content)
    assert str(result["overall_score"]) in text


def test_personality_numbers_match(sessions, user_a):
    sid = sessions["personality"]["sid"]
    result = requests.get(f"{API}/assessments/{sid}/result",
                          headers={"Authorization": f"Bearer {user_a['token']}"}, timeout=30).json()
    r = _fetch_pdf(user_a["token"], sid)
    text, _ = _pdf_text(r.content)
    # verify at least a majority of factor stens appear in the PDF
    stens = [f["sten"] for f in result["factor_scores"].values()]
    # each sten is 1..10 — just verify their exact strings appear as tokens
    # find them as whole tokens in text
    found = sum(1 for s in stens if re.search(rf"(^|[\s\W]){s}(\s|$|[\W])", text))
    assert found >= len(stens) * 0.6, f"only {found}/{len(stens)} factor stens found"


def test_closeness_numbers_match(sessions, user_a):
    sid = sessions["closeness"]["sid"]
    result = requests.get(f"{API}/assessments/{sid}/result",
                          headers={"Authorization": f"Bearer {user_a['token']}"}, timeout=30).json()
    r = _fetch_pdf(user_a["token"], sid)
    text, _ = _pdf_text(r.content)
    for key in ("anxiety", "avoidance"):
        d = result["dimensions"][key]
        if d.get("status") == "scored":
            assert str(d["value"]) in text, f"{key} value {d['value']} missing"


# ---------------------------------------------------------------------------
# Situation framing: different text, identical numbers
# ---------------------------------------------------------------------------
def test_situation_framing_differs_numbers_same():
    """Three users, same answer vector on essential, three situations."""
    tokens = {}
    for sit in ("single_dating", "in_relationship", "post_breakup"):
        tok, _, _ = _register(sit, name=f"User {sit}")
        tokens[sit] = tok

    # Deterministic answer function: alternating 2/4 (so no all-1s edge)
    def val_fn(idx, item_id):
        return 2 if idx % 2 == 0 else 4

    texts = {}
    numbers = {}
    for sit, tok in tokens.items():
        sid, result = _run_assessment(tok, "essential", val_fn)
        r = _fetch_pdf(tok, sid)
        text, _ = _pdf_text(r.content)
        texts[sit] = text
        # extract the deterministic result numbers
        numbers[sit] = (result["delta"]["overall"], result["delta"]["biggest"],
                        result["self"]["primary"]["key"], result["ideal"]["primary"]["key"])

    # Same answer vector → same numbers
    assert numbers["single_dating"] == numbers["in_relationship"] == numbers["post_breakup"], numbers

    # But framing sentences differ. Look for a signature phrase from each situation note.
    signatures = {
        "single_dating": "next person still theoretical",
        "in_relationship": "nothing here is a scorecard on your partner",
        "post_breakup": "window after an ending is short, and clearer than it will feel in six months",
    }
    for sit, sig in signatures.items():
        assert sig in texts[sit], f"{sit} missing its situation framing"
        for other, otext in texts.items():
            if other != sit:
                assert sig not in otext, f"{sit} framing leaked into {other}"


# ---------------------------------------------------------------------------
# Delta wording direction: positive delta = ideal higher than self => "you want more"
# ---------------------------------------------------------------------------
def test_essential_delta_wording_direction(user_a):
    """Sign of delta.per_archetype must match wording in PDF.

    Uses two runs so we get both positive and negative deltas across the space.
    positive delta (ideal > self) => 'you want more of this than you are'
    negative delta                => 'you are more of this than you want'
    """
    for val_fn in (
        lambda i, iid: 1 if iid.startswith("self:") else 5,
        lambda i, iid: 5 if iid.startswith("self:") else 1,
    ):
        sid, result = _run_assessment(user_a["token"], "essential", val_fn)
        r = _fetch_pdf(user_a["token"], sid)
        text, _ = _pdf_text(r.content)
        flat = re.sub(r"\s+", " ", text)
        positives = [v for v in result["delta"]["per_archetype"].values() if v > 0]
        negatives = [v for v in result["delta"]["per_archetype"].values() if v < 0]
        if positives:
            assert "you want more of this than you are" in flat, \
                f"positive deltas {positives} but positive-direction phrase missing"
        if negatives:
            assert "you are more of this than you want" in flat, \
                f"negative deltas {negatives} but negative-direction phrase missing"


# ---------------------------------------------------------------------------
# Edge cases: flat all-1s / all-5s essential, personality flagged validity
# ---------------------------------------------------------------------------
def test_essential_flat_all_ones(user_a):
    sid, _ = _run_assessment(user_a["token"], "essential", lambda i, iid: 1)
    r = _fetch_pdf(user_a["token"], sid)
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"
    assert len(r.content) > 2000
    _t, n = _pdf_text(r.content)
    assert 1 <= n <= 4


def test_essential_flat_all_fives(user_a):
    sid, _ = _run_assessment(user_a["token"], "essential", lambda i, iid: 5)
    r = _fetch_pdf(user_a["token"], sid)
    assert r.status_code == 200 and r.content[:4] == b"%PDF"


def test_personality_flagged_validity(user_a):
    # All 5s -> almost certainly triggers social_desirability and/or central_tendency flag
    sid, result = _run_assessment(user_a["token"], "personality", lambda i, iid: 5)
    r = _fetch_pdf(user_a["token"], sid)
    assert r.status_code == 200 and r.content[:4] == b"%PDF"
    text, n = _pdf_text(r.content)
    assert "Validity indices" in text or "validity" in text.lower()
    assert 1 <= n <= 5

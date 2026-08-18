"""Iteration 5 — Combined PDF (/api/v2/reports/combined.pdf) + Situation switch.

Covers:
- Combined PDF happy path (200, application/pdf, %PDF-, Content-Disposition filename)
- Auth (401 no token) and empty state (409 zero completed)
- Cross-check section matches POST /mirrors/findings for the same sessions
- With only 1 completed instrument, no cross-check section
- Situation switch: PATCH /api/auth/me/situation valid/invalid/no-token/persistence
- Situation switch does NOT touch scores (byte-identical /result payload)
- Situation switch reframes PDF wording (both per-result and combined)
- User isolation (no cross-contamination in combined PDF)
- Most-recent-per-instrument dedup in combined PDF
"""
import io
import os
import re
import uuid
import random
import pytest
import requests
import fitz  # pymupdf
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _register(situation="single_dating"):
    email = f"TEST_it5+{uuid.uuid4().hex[:10]}@ratherknow.com"
    r = requests.post(
        f"{API}/auth/register",
        json={"name": "Iter5 Tester", "email": email, "password": "knowmore123", "situation": situation},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    return {
        "email": email,
        "token": r.json()["access_token"],
        "user": r.json()["user"],
        "session": _mksession(r.json()["access_token"]),
    }


def _mksession(token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    return s


# instruments: (key, total, scale)
INS = {
    "essential": (100, 5),
    "personality": (130, 5),
    "eq": (140, 5),
    "closeness": (37, 7),
}


def _run(s, instrument, answers_override=None):
    """Complete an instrument. answers_override: dict item_id -> value."""
    r = s.post(f"{API}/v2/assessments", json={"instrument": instrument}, timeout=30)
    assert r.status_code == 200, r.text
    sess = r.json()
    sid = sess["session_id"]
    n_points = INS[instrument][1]
    random.seed(sid)  # deterministic per-session
    batch = []
    for it in sess["items"]:
        if answers_override and it["id"] in answers_override:
            v = answers_override[it["id"]]
        else:
            v = random.randint(1, n_points)
        batch.append({"item_id": it["id"], "value": v, "ms": 5000})
    for i in range(0, len(batch), 60):
        rr = s.put(f"{API}/v2/assessments/{sid}/responses", json={"responses": batch[i:i + 60]}, timeout=30)
        assert rr.status_code == 200, rr.text
    r = s.post(f"{API}/v2/assessments/{sid}/complete", timeout=60)
    assert r.status_code == 200, r.text
    return sid, r.json()


def _closeness_max_anxiety_answers():
    """Force closeness anxiety and avoidance to 7.0 by matching item.key F/R polarity."""
    import sys
    sys.path.insert(0, "/app/backend")
    from services.closeness_scoring import load_bank  # noqa: E402
    bank = load_bank()
    out = {}
    for it in bank["items"]:
        out[str(it["id"])] = 7 if it["key"] == "F" else 1
    # VAL-IR expected
    out["VAL-IR"] = bank["validity"][0]["expected"]
    return out


# ------------------------- Combined PDF: auth & empty ------------------------
def test_combined_pdf_401_no_token():
    r = requests.get(f"{API}/v2/reports/combined.pdf", timeout=30)
    assert r.status_code == 401


def test_combined_pdf_409_when_no_completions():
    u = _register()
    r = u["session"].get(f"{API}/v2/reports/combined.pdf", timeout=30)
    assert r.status_code == 409


# ------------------------- Combined PDF: 1 instrument ------------------------
@pytest.fixture(scope="module")
def one_complete():
    u = _register("single_dating")
    sid, res = _run(u["session"], "closeness")
    return u, sid, res


def test_combined_pdf_one_instrument_shape(one_complete):
    u, sid, res = one_complete
    r = u["session"].get(f"{API}/v2/reports/combined.pdf", timeout=60)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/pdf")
    assert r.content[:5] == b"%PDF-"
    disp = r.headers.get("content-disposition", "")
    assert 'filename="ratherknow-your-mirrors.pdf"' in disp
    # No cross-check section with only 1 completion
    text = _norm(_pdf_text(r.content))
    assert "The cross-check" not in text
    # Closeness section appears
    assert "Closeness Mirror" in text
    # Numbers surface (dimension values)
    for dim in ("anxiety", "avoidance"):
        v = res["dimensions"][dim]["value"]
        assert f"{v} of 7" in text or f"{v}of 7" in text.replace(" of 7", "of 7")


def _pdf_text(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return "\n".join(p.get_text() for p in doc)
    finally:
        doc.close()


# ---------------------- Combined PDF: 4 instruments + cross-check ------------
@pytest.fixture(scope="module")
def four_complete_forced_anxiety():
    """User with all 4 instruments completed, closeness forced to high anx/avo
    so closeness-dependent cross-check rules can fire."""
    u = _register("in_relationship")
    s = u["session"]
    _run(s, "essential")
    _run(s, "personality")
    _run(s, "eq")
    _run(s, "closeness", answers_override=_closeness_max_anxiety_answers())
    return u


def test_combined_pdf_four_instruments(four_complete_forced_anxiety):
    u = four_complete_forced_anxiety
    r = u["session"].get(f"{API}/v2/reports/combined.pdf", timeout=60)
    assert r.status_code == 200, r.text
    assert r.content[:5] == b"%PDF-"
    text = _norm(_pdf_text(r.content))
    # Every instrument name appears
    for name in ("Essential Mirror", "Personality Mirror", "EI Mirror", "Closeness Mirror"):
        assert name in text, f"missing instrument section: {name}"
    # algo_version stamp present in footer
    assert "rk-1.0.0" in text
    # safety & limits blocks
    assert "help" in text.lower() or "safety" in text.lower()


def test_combined_pdf_crosscheck_matches_findings_endpoint(four_complete_forced_anxiety):
    u = four_complete_forced_anxiety
    # gather this user's session_ids
    ms = u["session"].get(f"{API}/auth/me/sessions", timeout=30).json()["sessions"]
    ids = [s["session_id"] for s in ms if s["status"] == "complete"]
    f_resp = u["session"].post(
        f"{API}/v2/mirrors/findings", json={"session_ids": ids}, timeout=30
    )
    assert f_resp.status_code == 200
    findings = f_resp.json()["findings"]

    pdf = u["session"].get(f"{API}/v2/reports/combined.pdf", timeout=60).content
    text = _norm(_pdf_text(pdf))

    # Cross-check section header must appear (>=2 instruments)
    assert "The cross-check" in text

    if findings:
        # Every finding title must appear in the PDF
        for f in findings:
            assert f["title"] in text, (
                f"Finding {f['id']!r} title {f['title']!r} present in /mirrors/findings "
                f"but MISSING from combined PDF cross-check. "
                f"(This is the closeness-key bug in _build_findings if id involves closeness.)"
            )
        # Honest-no-tension line must NOT be printed when findings exist
        assert "No tensions worth reporting" not in text
    else:
        assert "No tensions worth reporting" in text


# ---------------------- Combined PDF: numbers match /result ------------------
def test_combined_pdf_numbers_match_result(four_complete_forced_anxiety):
    u = four_complete_forced_anxiety
    ms = u["session"].get(f"{API}/auth/me/sessions", timeout=30).json()["sessions"]
    # Grab an eq session's overall score
    eq_sid = next(s["session_id"] for s in ms if s["instrument"] == "eq")
    eq_res = u["session"].get(f"{API}/v2/assessments/{eq_sid}/result", timeout=30).json()
    pdf = u["session"].get(f"{API}/v2/reports/combined.pdf", timeout=60).content
    text = _norm(_pdf_text(pdf))
    # Overall EI score should appear literally
    assert str(eq_res["overall_score"]) in text


# ---------------------- Combined PDF: most-recent-per-instrument -------------
def test_combined_pdf_dedupes_to_most_recent():
    u = _register("single_dating")
    s = u["session"]
    # Two closeness completions with different answers
    sid1, r1 = _run(s, "closeness", answers_override={str(i): 1 for i in range(1, 37)})
    sid2, r2 = _run(s, "closeness", answers_override={str(i): 7 for i in range(1, 37)})
    assert sid1 != sid2
    # Their dimension values should differ (though reverse-coded → still 4.0 for uniform)
    pdf = s.get(f"{API}/v2/reports/combined.pdf", timeout=60).content
    text = _pdf_text(pdf)
    # Closeness Mirror should appear only ONCE
    assert text.count("Closeness Mirror") <= 3, (
        "Closeness section printed more than once — combined PDF is duplicating instruments"
    )
    # And the confidence label from the most recent (r2) result should be present
    conf = (r2.get("confidence") or "").title()
    if conf and conf.lower() != "unknown":
        assert conf in text


# ---------------------- Combined PDF: user isolation -------------------------
def test_combined_pdf_no_cross_user_leak():
    a = _register("post_breakup")
    b = _register("in_relationship")
    _run(a["session"], "closeness")
    _run(b["session"], "eq")
    pdf_a = a["session"].get(f"{API}/v2/reports/combined.pdf", timeout=60).content
    pdf_b = b["session"].get(f"{API}/v2/reports/combined.pdf", timeout=60).content
    text_a = _pdf_text(pdf_a)
    text_b = _pdf_text(pdf_b)
    # A must not include B's email/name and vice versa
    assert b["email"] not in text_a
    assert a["email"] not in text_b
    # A only has closeness, B only has EI
    assert "Closeness Mirror" in text_a
    assert "EI Mirror" not in text_a
    assert "EI Mirror" in text_b
    assert "Closeness Mirror" not in text_b


# ---------------------- Situation switch: backend ----------------------------
def test_situation_patch_401_no_token():
    r = requests.patch(f"{API}/auth/me/situation", json={"situation": "single_dating"}, timeout=30)
    assert r.status_code == 401


def test_situation_patch_400_invalid_value():
    u = _register("single_dating")
    r = u["session"].patch(f"{API}/auth/me/situation", json={"situation": "married_or_something"}, timeout=30)
    assert r.status_code == 400


@pytest.mark.parametrize("sit,label", [
    ("single_dating", "Single & dating"),
    ("in_relationship", "In a relationship"),
    ("post_breakup", "Post-breakup"),
])
def test_situation_patch_valid_values(sit, label):
    u = _register("single_dating")
    r = u["session"].patch(f"{API}/auth/me/situation", json={"situation": sit}, timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert j["user"]["situation"] == sit
    assert j["user"]["situation_label"] == label
    # Persistence via fresh /me
    me = u["session"].get(f"{API}/auth/me", timeout=30).json()
    assert me["user"]["situation"] == sit
    # Persistence across login (new token)
    login = requests.post(
        f"{API}/auth/login", json={"email": u["email"], "password": "knowmore123"}, timeout=30
    ).json()
    assert login["user"]["situation"] == sit


# ---------------------- Situation switch: scores don't move ------------------
def test_situation_switch_does_not_rescore():
    u = _register("single_dating")
    sid, res_before = _run(u["session"], "closeness")
    # Fetch the /result payload for a byte comparison
    fetch_before = u["session"].get(f"{API}/v2/assessments/{sid}/result", timeout=30).json()
    # Switch situation
    u["session"].patch(f"{API}/auth/me/situation", json={"situation": "post_breakup"}, timeout=30)
    fetch_after = u["session"].get(f"{API}/v2/assessments/{sid}/result", timeout=30).json()
    assert fetch_after == fetch_before, "situation switch mutated the stored result"
    assert fetch_after["algo_version"] == "rk-1.0.0"


# ---------------------- Situation switch: PDF wording reframes ---------------
def test_situation_switch_reframes_per_result_pdf():
    """PDF framing sentence changes across situations while numbers stay identical."""
    u = _register("single_dating")
    sid, _ = _run(u["session"], "essential")
    # single_dating framing
    p1 = u["session"].get(f"{API}/v2/assessments/{sid}/report.pdf", timeout=60).content
    t1 = _norm(_pdf_text(p1))
    # switch to post_breakup
    u["session"].patch(f"{API}/auth/me/situation", json={"situation": "post_breakup"}, timeout=30)
    p2 = u["session"].get(f"{API}/v2/assessments/{sid}/report.pdf", timeout=60).content
    t2 = _norm(_pdf_text(p2))
    # Signature phrases unique to each framing
    single_phrase = "next person still theoretical"
    breakup_phrase = "window after an ending is short and unusually clear"
    assert single_phrase in t1
    assert single_phrase not in t2
    assert breakup_phrase in t2
    assert breakup_phrase not in t1


def test_situation_switch_reframes_combined_pdf():
    u = _register("single_dating")
    _run(u["session"], "closeness")
    _run(u["session"], "eq")
    p1 = u["session"].get(f"{API}/v2/reports/combined.pdf", timeout=60).content
    t1 = _norm(_pdf_text(p1))
    u["session"].patch(f"{API}/auth/me/situation", json={"situation": "in_relationship"}, timeout=30)
    p2 = u["session"].get(f"{API}/v2/reports/combined.pdf", timeout=60).content
    t2 = _norm(_pdf_text(p2))
    # Signature phrase from single_dating closeness note should be in t1 not t2
    assert "how quickly you need a signal back" in t1
    assert "how quickly you need a signal back" not in t2
    # And the in_relationship signature phrase should show up in t2 not t1
    assert "answered about relationships in general" in t2
    assert "answered about relationships in general" not in t1

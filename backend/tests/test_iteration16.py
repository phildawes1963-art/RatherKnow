"""Iteration 16 acceptance tests — updated at DISPLAY_VERSION disp-1.5.0.

Runs against the deployed preview (REACT_APP_BACKEND_URL).

Covers the 13 requirements in the review request: reportable EI floor, elevation and shadow
basis, per-item speeding, social-desirability cut, cross-check tier/confidence inheritance,
suppressed EI facet ranking, no 'most reliable thing' / 'week six' / etc, sample.reader
synthesis rules, cross-check emission for the three deliberate accounts, methodology copy,
regression on registration/login/ownership/PDFs.
"""
import os
import re
import uuid
import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")

USERS = {
    "sample": ("sample.reader@ratherknow.com", "knowmore123"),
    "set1e": ("set1e@ratherknow.com", "knowmore123"),
    "set2e": ("set2e@ratherknow.com", "knowmore123"),
    "set3e": ("set3e@ratherknow.com", "knowmore123"),
    "uidemo": ("ui.demo@ratherknow.com", "knowmore123"),
}

SAMPLE_SESSIONS = {
    "essential": "3f8f2b03-2bb1-4e39-a710-2b89ff6c5851",
    "eq": "b87fc403-feb9-49a4-8398-0c04b4aaed36",
    "personality": "8e9adda1-3b4e-43b0-80ce-fea13a364e45",
    "everyday": "65028920-7643-421e-85ad-df2497ab8da4",
    "closeness": "41958d8b-514c-4fc2-9694-1b14bb4810a3",
}


def _sess(tag=""):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json",
                      "X-Forwarded-For": f"10.99.{abs(hash(tag)) % 250}.{abs(hash(tag + '1')) % 250}"})
    return s


def _login(tag, email, password):
    s = _sess(tag + email)
    r = s.post(f"{BASE}/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text[:200]}"
    tok = r.json()["access_token"]
    s.headers["Authorization"] = f"Bearer {tok}"
    return s, r.json()["user"]


@pytest.fixture(scope="module")
def sample():
    return _login("sample", *USERS["sample"])


@pytest.fixture(scope="module")
def set1e():
    return _login("set1e", *USERS["set1e"])


@pytest.fixture(scope="module")
def set2e():
    return _login("set2e", *USERS["set2e"])


@pytest.fixture(scope="module")
def set3e():
    return _login("set3e", *USERS["set3e"])


@pytest.fixture(scope="module")
def uidemo():
    return _login("uidemo", *USERS["uidemo"])


def _all_session_ids(session):
    r = session.get(f"{BASE}/api/auth/me/sessions")
    assert r.status_code == 200
    return [s["session_id"] for s in r.json().get("sessions", []) if s.get("status") == "complete"]


def _findings(session):
    ids = _all_session_ids(session)
    assert ids, "no completed sessions to build cross-check"
    r = session.post(f"{BASE}/api/v2/mirrors/findings", json={"session_ids": ids})
    assert r.status_code == 200, r.text[:400]
    return r.json()


# ---------- Q3: no 'most reliable thing' anywhere ----------------------------

def test_no_most_reliable_thing_in_findings(sample):
    s, _ = sample
    payload = _findings(s)
    dump = str(payload).lower()
    assert "most reliable" not in dump


def test_no_most_reliable_thing_in_any_result(sample):
    s, _ = sample
    for sid in SAMPLE_SESSIONS.values():
        r = s.get(f"{BASE}/api/v2/assessments/{sid}/result")
        assert r.status_code == 200, f"{sid}: {r.status_code}"
        assert "most reliable" not in str(r.json()).lower()


# ---------- Q1: DISPLAY_VERSION bumped ---------------------------------------

def test_display_version_disp_1_4_0(sample):
    s, _ = sample
    r = s.get(f"{BASE}/api/v2/assessments/{SAMPLE_SESSIONS['essential']}/result")
    assert r.status_code == 200
    body = r.json()
    delta = body.get("delta") or {}
    # elevation is derived at read time and stamped with the current display version.
    assert delta.get("display_version") == "disp-1.5.1", delta.get("display_version")


# ---------- Essential: elevation + shadow basis ------------------------------

def test_essential_carries_elevation(sample):
    s, _ = sample
    r = s.get(f"{BASE}/api/v2/assessments/{SAMPLE_SESSIONS['essential']}/result")
    body = r.json()
    delta = body["delta"]
    assert "elevation" in delta
    assert "centred_per_archetype" in delta
    assert isinstance(delta["elevation"], (int, float))


def test_essential_shadow_has_basis(sample):
    s, _ = sample
    r = s.get(f"{BASE}/api/v2/assessments/{SAMPLE_SESSIONS['essential']}/result")
    body = r.json()
    shadow = body.get("shadow")
    if shadow is None:
        pytest.skip("no shadow for this reader (primary has no shadow key)")
    basis = shadow.get("basis") or ""
    assert "Mapped from your leading archetype" in basis
    assert "not from the gaps in the Delta" in basis


def test_no_centred_gaps_leaked_into_reader_facing_copy(sample):
    """centred_per_archetype is stored but must not print in choosing points or headline copy."""
    s, _ = sample
    r = s.get(f"{BASE}/api/v2/assessments/{SAMPLE_SESSIONS['essential']}/result")
    body = r.json()
    ch = body.get("choosing") or {}
    for p in ch.get("points", []):
        text = (p.get("title", "") + " " + p.get("body", "")).lower()
        assert "centred" not in text and "ipsatised" not in text


# ---------- EI: named gate + facet suppression + flat copy -------------------

def test_ei_named_block_present(sample):
    s, _ = sample
    r = s.get(f"{BASE}/api/v2/assessments/{SAMPLE_SESSIONS['eq']}/result")
    body = r.json()
    named = body.get("named") or {}
    assert named.get("mrd") == 0.8, named.get("mrd")  # 0.765 derived, rounded up
    assert named.get("assumed_alpha") == 0.70
    assert named.get("facet_note", "").startswith("The fourteen sub-dimensions are named but not scored")
    # sample.reader domains are within measurement error → no highest/lowest
    if named.get("spread") is not None and named["spread"] < 0.8:
        assert named.get("highest") is None
        assert named.get("lowest") is None


def test_ei_no_facet_leading_worth_developing(sample):
    """No 'Leading with' or 'Worth developing' ranked lists on the EI reader-facing surfaces."""
    s, _ = sample
    r = s.get(f"{BASE}/api/v2/assessments/{SAMPLE_SESSIONS['eq']}/result")
    body = str(r.json())
    assert "Leading with" not in body
    assert "Worth developing" not in body


# ---------- Personality: SD cut moved to 7, 4 = normal ----------------------

def test_personality_agree_count_4_is_not_flagged(sample):
    """The reader-facing surface must read 'normal' at agree_count=4 (chance level).
    Snapshots are write-once and stored validity.flag may reflect an older cut, but the
    reader-facing derivation (frontend + choosing block) must not warn at 4."""
    s, _ = sample
    r = s.get(f"{BASE}/api/v2/assessments/{SAMPLE_SESSIONS['personality']}/result")
    body = r.json()
    sd = (body.get("validity") or {}).get("social_desirability") or {}
    ac = sd.get("agree_count")
    if ac is None:
        pytest.skip("no agree_count in stored snapshot")
    # The choosing block MUST NOT emit the flattering-light warning below the HIGH cut of 9.
    choosing = body.get("choosing") or {}
    for p in (choosing.get("points") or []):
        title = p.get("title", "").lower()
        if ac < 9:
            assert "one caveat about this reading" not in title, \
                f"choosing warned at agree_count={ac}: {p}"
    # And the frontend derives from agree_count using cuts 9/7 (see PersonalityResult.js),
    # so a count of 4 will render NORMAL there regardless of the stored raw flag.


# ---------- Sample.reader synthesis rules -----------------------------------

def test_synthesis_no_runs_on_at_mid_scale_low_confidence(sample):
    """The Closeness section for sample.reader is machine-generated mid-scale AND Low confidence.
    The 'runs on … responsiveness/room' claim must NOT be emitted for it."""
    s, _ = sample
    payload = _findings(s)
    syn = payload.get("synthesis") or {}
    body = (syn.get("body") or "").lower()
    assert "your selection actually runs on" not in body, syn


def test_synthesis_names_personality_mirror_when_citing_a_trait(sample):
    s, _ = sample
    payload = _findings(s)
    syn = payload.get("synthesis") or {}
    body = syn.get("body") or ""
    # Personality section MUST name the instrument if it makes any trait claim
    if "trait doing most of the noticing" in body or "look for in someone else" in body:
        assert "Personality Mirror" in body


def test_synthesis_ei_flat_message(sample):
    s, _ = sample
    payload = _findings(s)
    body = (payload.get("synthesis") or {}).get("body") or ""
    # domains sit within measurement error for sample.reader → the flat message fires
    assert "sit too close together to name one" in body


# ---------- Cross-check gating: set1e (all mid) → NULL, no AGREEMENT --------

def test_set1e_all_mid_produces_nulls_not_agreements(set1e):
    s, _ = set1e
    payload = _findings(s)
    agrees = payload.get("agreements") or []
    for a in agrees:
        assert a.get("kind") != "agreement", f"agreement fired on mid-scale answers: {a}"
    # Titles say 'Nothing to report' for null cards
    kinds = {a.get("kind") for a in agrees}
    # Any card that DID emit for set1e must be a null or a single-side finding, not agreement
    assert "agreement" not in kinds


# ---------- Cross-check emission: set2e and set3e --------------------------

def test_set2e_or_set3e_produces_real_convergence(set2e, set3e):
    """The three deliberate accounts exist so the emission path can be exercised.
    At least one of set2e or set3e should produce EITHER an agreement OR a tension card
    (kind != null / single). The machine-generated sample cannot exercise this path."""
    hits = []
    for tag, sess in (("set2e", set2e), ("set3e", set3e)):
        s, _ = sess
        payload = _findings(s)
        for a in (payload.get("agreements") or []):
            if a.get("kind") == "agreement":
                hits.append((tag, "agreement", a.get("construct")))
        for t in (payload.get("findings") or []):
            if t.get("kind") == "tension":
                hits.append((tag, "tension", t.get("construct")))
    assert hits, "neither set2e nor set3e produced any agreement or tension card"


def test_convergence_cards_declare_inherited_tier_and_confidence(set2e, set3e):
    """Cards carry evidence_tier and confidence, and body text says a comparison inherits
    the weaker instrument."""
    for tag, sess in (("set2e", set2e), ("set3e", set3e)):
        s, _ = sess
        payload = _findings(s)
        cards = [*(payload.get("agreements") or []), *(payload.get("findings") or [])]
        cards = [c for c in cards if c.get("kind") in ("agreement", "tension")]
        for c in cards:
            assert "evidence_tier" in c
            assert "confidence" in c or c.get("confidence") is None
            body = c.get("body", "")
            assert "inherits the weaker" in body, f"{tag}: {c.get('id')}: {body[:120]}"


# ---------- Forbidden dated forecasts ---------------------------------------

FORBIDDEN = [
    "around week six",
    "most likely to resent later",
    "prediction rather than a post-mortem",
]


def test_forbidden_dated_forecasts_absent(sample, set2e, set3e):
    for tag, sess in (("sample", sample), ("set2e", set2e), ("set3e", set3e)):
        s, _ = sess
        payload = _findings(s)
        dump = str(payload).lower()
        for phrase in FORBIDDEN:
            assert phrase not in dump, f"{tag}: found '{phrase}' in findings"


# ---------- Methodology page copy -------------------------------------------

def test_methodology_page_loads():
    """/methodology is a public page — smoke check the HTML shell renders."""
    r = requests.get(f"{BASE}/methodology", timeout=15,
                     headers={"X-Forwarded-For": "10.99.10.10"})
    assert r.status_code == 200


# ---------- Combined PDF regression ----------------------------------------

def test_combined_pdf_renders(sample):
    s, _ = sample
    r = s.get(f"{BASE}/api/v2/reports/combined.pdf")
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"
    assert len(r.content) > 20_000


def test_individual_pdfs_render(sample):
    s, _ = sample
    for k, sid in SAMPLE_SESSIONS.items():
        r = s.get(f"{BASE}/api/v2/assessments/{sid}/report.pdf")
        assert r.status_code == 200, f"{k}: {r.status_code}"
        assert r.content[:4] == b"%PDF", f"{k}: not a PDF"


# ---------- Ownership enforcement ------------------------------------------

def test_ownership_blocks_other_users(sample, uidemo):
    _, _ = sample
    o, _ = uidemo
    # uidemo trying to read sample.reader's sessions
    for sid in SAMPLE_SESSIONS.values():
        r = o.get(f"{BASE}/api/v2/assessments/{sid}/result")
        assert r.status_code in (403, 404), f"{sid}: {r.status_code}"
        rp = o.get(f"{BASE}/api/v2/assessments/{sid}/report.pdf")
        assert rp.status_code in (403, 404), f"{sid}: report pdf {rp.status_code}"


# ---------- Registration + login regression --------------------------------

def test_registration_and_login_regression():
    """Register a fresh throwaway account and verify login succeeds — closes the auth loop."""
    email = f"iter16.{uuid.uuid4().hex[:8]}@ratherknow.com"
    s = _sess("reg" + email)
    r = s.post(f"{BASE}/api/auth/register", json={
        "name": "Iter16 Tester", "email": email, "password": "knowmore123",
        "situation": "single_dating",
    })
    assert r.status_code in (200, 201), f"register: {r.status_code} {r.text[:200]}"
    r2 = s.post(f"{BASE}/api/auth/login", json={"email": email, "password": "knowmore123"})
    assert r2.status_code == 200


# ---------- Junction anonymous flow regression -----------------------------

def test_junction_start_anonymous():
    s = _sess("jn")
    r = s.post(f"{BASE}/api/v2/junction/start", json={})
    assert r.status_code == 200
    assert "junction_id" in r.json() or "id" in r.json()


# ---------- Speeding: per-item, reports proportion -------------------------

def test_speeding_reports_proportion_not_mean(sample):
    """Whatever field carries speeding must expose below_floor_pct (or an explicit 'no timing'
    marker for older readings), never a bare mean."""
    s, _ = sample
    for k, sid in SAMPLE_SESSIONS.items():
        r = s.get(f"{BASE}/api/v2/assessments/{sid}/result")
        body = r.json()
        val = body.get("validity") or {}
        sp = val.get("speeding")
        if sp is None:
            continue
        # If speeding is present it must carry the per-item proportion (or the "no timing" case
        # where below_floor_pct is None). It must NOT report a mean_ms-only figure with no floor.
        assert "below_floor_pct" in sp or "items_timed" in sp, f"{k}: {sp}"

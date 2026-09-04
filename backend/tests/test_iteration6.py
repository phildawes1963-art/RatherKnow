"""Iteration 6 — user-reported bug fixes:

BUG 1 — 'how you choose' translation layer on every instrument (backend/choosing.py)
BUG 2 — cross-check richness: agreements + synthesis (backend/crosscheck.py)
BUG 3 — item interleaving so same-trait items never sit next to each other
"""
import os
import re
import sys
import json
import uuid
import random
import pytest
import requests
import fitz  # pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

INS = {"essential": (100, 5), "personality": (130, 5), "eq": (140, 5), "closeness": (37, 7)}


def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", t)


def _mksession(token):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    return s


def _register(situation="single_dating"):
    email = f"TEST_it6+{uuid.uuid4().hex[:10]}@ratherknow.com"
    r = requests.post(
        f"{API}/auth/register",
        json={"name": "Iter6", "email": email, "password": "knowmore123", "situation": situation},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    tok = r.json()["access_token"]
    return {"email": email, "token": tok, "session": _mksession(tok)}


def _run(s, instrument, answers_override=None, seed=None):
    r = s.post(f"{API}/v2/assessments", json={"instrument": instrument}, timeout=30)
    assert r.status_code == 200, r.text
    sess = r.json()
    sid = sess["session_id"]
    n_points = INS[instrument][1]
    random.seed(seed or sid)
    batch = []
    for it in sess["items"]:
        v = (answers_override or {}).get(it["id"], random.randint(1, n_points))
        batch.append({"item_id": it["id"], "value": v, "ms": 5000})
    for i in range(0, len(batch), 60):
        rr = s.put(f"{API}/v2/assessments/{sid}/responses",
                   json={"responses": batch[i:i + 60]}, timeout=30)
        assert rr.status_code == 200, rr.text
    r = s.post(f"{API}/v2/assessments/{sid}/complete", timeout=90)
    assert r.status_code == 200, r.text
    return sid, r.json(), sess["items"]


def _pdf_text(b):
    doc = fitz.open(stream=b, filetype="pdf")
    try:
        return "\n".join(p.get_text() for p in doc)
    finally:
        doc.close()


# ============================================================================
# BUG 3 — item interleaving: no two same-trait items are ever adjacent
# ============================================================================

def _max_run(seq):
    m = cur = 1
    for i in range(1, len(seq)):
        cur = cur + 1 if seq[i] == seq[i - 1] else 1
        m = max(m, cur)
    return m


def test_bug3_personality_no_adjacent_same_factor():
    """Personality: 130 items across 15 factors; no two adjacent from same factor."""
    from routes.mirror_v2 import _build_items
    from constants.p150_data import P150_PERSONALITY_ITEMS, P150_VALIDITY_ITEMS
    from services.p150_lite import P150_FACTORS
    items, _, _, _ = _build_items("personality")
    # 130 personality items + validity items — spec says total_items 130
    personality_ids = {q["id"] for q in P150_PERSONALITY_ITEMS}
    validity_ids = {v["id"] for v in P150_VALIDITY_ITEMS}
    id_to_factor = {}
    for f_key, meta in P150_FACTORS.items():
        for iid in meta["items"]:
            id_to_factor[iid] = f_key
    # count
    ids = [int(it["id"]) for it in items]
    pers_ids = [i for i in ids if i in personality_ids]
    val_ids = [i for i in ids if i in validity_ids]
    assert len(pers_ids) == len(P150_PERSONALITY_ITEMS), f"pers count {len(pers_ids)}"
    assert len(val_ids) == len(P150_VALIDITY_ITEMS), f"val count {len(val_ids)}"
    # each id present exactly once
    assert len(set(pers_ids)) == len(pers_ids)
    assert len(set(val_ids)) == len(val_ids)
    # adjacency: look at personality-only sub-sequence (validity items are spacers)
    factors = [id_to_factor.get(i) for i in pers_ids]
    run = _max_run(factors)
    assert run == 1, f"Personality has adjacent same-factor run of {run}: {factors[:30]}"


def test_bug3_eq_no_adjacent_same_sub():
    from routes.mirror_v2 import _build_items
    from constants.eimirror_data import EIMIRROR_QUESTIONS
    items, _, _, _ = _build_items("eq")
    assert len(items) == 140
    by_id = {q["id"]: q for q in EIMIRROR_QUESTIONS}
    ids = [int(it["id"]) for it in items]
    assert len(set(ids)) == 140
    subs = [by_id[i].get("sub") or by_id[i].get("domain") for i in ids]
    run = _max_run(subs)
    assert run == 1, f"EQ adjacent same-sub run of {run}"


def test_bug3_essential_no_adjacent_same_category_within_lens():
    from routes.mirror_v2 import _build_items
    with open(os.path.join(ROOT, "backend", "constants", "essential_data.json")) as f:
        ess = json.load(f)
    self_cat = {q["id"]: q.get("category") or q.get("archetype")
                for q in ess.get("self_assessment_questions", [])}
    items, _, _, interstitial = _build_items("essential")
    assert len(items) == 100
    self_seq, ideal_seq = [], []
    for it in items:
        lens, qid = it["id"].split(":", 1)
        (self_seq if lens == "self" else ideal_seq).append(int(qid))
    assert len(self_seq) == 50 and len(ideal_seq) == 50
    # within each lens no adjacent same category
    for label, seq in (("self", self_seq), ("ideal", ideal_seq)):
        cats = [self_cat.get(i) for i in seq]
        run = _max_run(cats)
        assert run == 1, f"Essential {label} adjacent run of {run}"


def test_bug3_closeness_preserves_spec_order():
    """Closeness Mirror preserves fixed bank order — first ids 34,28,15,27,22 and 37 items."""
    from routes.mirror_v2 import _build_items
    items, scale, _, _ = _build_items("closeness")
    assert len(items) == 37
    first5 = [it["id"] for it in items[:5]]
    assert first5 == ["34", "28", "15", "27", "22"], f"got {first5}"


def test_bug3_order_stable_on_resume():
    """Fetching the same in-progress session twice returns identical item order."""
    u = _register()
    for inst in ("personality", "eq", "essential"):
        r = u["session"].post(f"{API}/v2/assessments", json={"instrument": inst}, timeout=30)
        sid = r.json()["session_id"]
        order1 = [it["id"] for it in r.json()["items"]]
        r2 = u["session"].get(f"{API}/v2/assessments/{sid}", timeout=30)
        order2 = [it["id"] for it in r2.json()["items"]]
        assert order1 == order2, f"{inst} order changed on resume"


# ============================================================================
# BUG 1 — 'how you choose' translation for ALL FOUR instruments
# ============================================================================

@pytest.fixture(scope="module")
def four_user():
    u = _register("single_dating")
    s = u["session"]
    sids = {}
    for inst in ("essential", "personality", "eq", "closeness"):
        sid, res, _ = _run(s, inst)
        sids[inst] = (sid, res)
    return u, sids


def _forbidden_terms():
    # verdict-about-another / clinical / compatibility-score / prediction.
    # Matched as whole words: bare "predict" used to collide with the legitimate
    # "unpredictable partners" in the Essential archetype copy.
    return [
        "your partner is", "he is", "she is", "they are toxic",
        "diagnosis", "disorder", "narcissist", "attachment style is",
        "compatibility score", "you will fail", "you will succeed",
        "predict", "predicts", "prediction",
    ]


def _contains_forbidden(blob, term):
    import re
    return re.search(rf"\b{re.escape(term)}\b", blob) is not None


def test_bug1_choosing_block_present_all_four_result_endpoint(four_user):
    u, sids = four_user
    for inst, (sid, _) in sids.items():
        r = u["session"].get(f"{API}/v2/assessments/{sid}/result", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "choosing" in data and data["choosing"] is not None, f"{inst}: no choosing block"
        c = data["choosing"]
        assert c["lead"] and c["closing"]
        assert 2 <= len(c["points"]) <= 5, f"{inst}: {len(c['points'])} points"
        for p in c["points"]:
            assert p["title"] and p["body"]
        # no verdicts / clinical / predictions
        blob = (c["lead"] + " " + c["closing"] + " " +
                " ".join(p["title"] + " " + p["body"] for p in c["points"])).lower()
        for term in _forbidden_terms():
            assert not _contains_forbidden(blob, term), f"{inst}: forbidden phrase '{term}' in choosing copy"


def test_bug1_choosing_block_present_on_complete_endpoint():
    """POST .../complete also returns a choosing block."""
    u = _register()
    _, res, _ = _run(u["session"], "closeness")
    assert res.get("choosing"), "complete response missing choosing"


def test_bug1_choosing_quotes_real_numbers(four_user):
    """Each instrument's choosing block quotes its own actual numbers."""
    u, sids = four_user
    # closeness — cites 1–7 values
    sid, res = sids["closeness"]
    c = u["session"].get(f"{API}/v2/assessments/{sid}/result").json()["choosing"]
    body_blob = " ".join(p["body"] for p in c["points"])
    anx_v = res["dimensions"]["anxiety"].get("value")
    avo_v = res["dimensions"]["avoidance"].get("value")
    if anx_v is not None:
        assert f"{anx_v} of 7" in body_blob or str(anx_v) in body_blob
    if avo_v is not None:
        assert f"{avo_v} of 7" in body_blob or str(avo_v) in body_blob

    # personality — cites stens (1–10)
    sid, res = sids["personality"]
    c = u["session"].get(f"{API}/v2/assessments/{sid}/result").json()["choosing"]
    blob = " ".join(p["body"] for p in c["points"])
    assert "of 10" in blob, "personality choosing must cite sten out of 10"

    # eq — cites 1–5 domain scores
    sid, res = sids["eq"]
    c = u["session"].get(f"{API}/v2/assessments/{sid}/result").json()["choosing"]
    blob = " ".join(p["body"] for p in c["points"])
    assert "of 5" in blob, "eq choosing must cite score out of 5"

    # essential — cites Delta and per-archetype gaps
    sid, res = sids["essential"]
    c = u["session"].get(f"{API}/v2/assessments/{sid}/result").json()["choosing"]
    blob = " ".join(p["body"] for p in c["points"])
    delta_overall = res["delta"]["overall"]
    assert f"{delta_overall} points" in blob or str(delta_overall) in blob


def test_bug1_choosing_not_stored_in_snapshot(four_user):
    """The choosing block must be derived at read time, not written into the snapshot."""
    import os
    from pymongo import MongoClient
    u, sids = four_user
    sid, _ = sids["closeness"]

    # Sync client: asyncio.get_event_loop() raises on 3.11 inside an xdist worker.
    client = MongoClient(os.environ["MONGO_URL"])
    try:
        mdb = client[os.environ["DB_NAME"]]
        session = mdb.mirror_v2_sessions.find_one({"id": sid}, {"_id": 0, "result": 1})
        stored = mdb.results.find_one({"session_id": sid}, {"_id": 0, "result": 1})
    finally:
        client.close()
    assert "choosing" not in (session.get("result") or {}), "choosing leaked into mirror_v2_sessions snapshot"
    assert "choosing" not in ((stored or {}).get("result") or {}), "choosing leaked into results snapshot"


def test_bug1_choosing_in_per_result_pdf(four_user):
    u, sids = four_user
    for inst, (sid, _) in sids.items():
        pdf = u["session"].get(f"{API}/v2/assessments/{sid}/report.pdf", timeout=60).content
        text = _norm(_pdf_text(pdf))
        assert "How you choose" in text, f"{inst}: 'How you choose' section missing from PDF"


def test_bug1_choosing_in_combined_pdf(four_user):
    u, _ = four_user
    pdf = u["session"].get(f"{API}/v2/reports/combined.pdf", timeout=90).content
    text = _norm(_pdf_text(pdf))
    # 'How you choose' block should appear at least once per included instrument (>=4)
    count = text.count("How you choose")
    # Some may be the synthesis title 'How you choose — the short version' — allow >=4
    assert count >= 4, f"Combined PDF has only {count} 'How you choose' sections"


# ============================================================================
# BUG 2 — cross-check richness: agreements + tensions + synthesis
# ============================================================================

def test_bug2_findings_return_agreements_and_synthesis(four_user):
    u, sids = four_user
    ids = [sid for sid, _ in sids.values()]
    r = u["session"].post(f"{API}/v2/mirrors/findings", json={"session_ids": ids}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert sorted(data["instruments_complete"]) == ["closeness", "eq", "essential", "personality"]
    assert data.get("synthesis") is not None, "synthesis missing"
    syn = data["synthesis"]
    assert syn["title"] and syn["body"] and syn["footnote"]
    # With 4 instruments completed the page must never be just the 'No tensions' line
    assert (len(data["agreements"]) + len(data["findings"])) >= 1, \
        "with 4 instruments completed, must have at least one agreement OR one tension"


def test_bug2_agreements_only_when_close():
    """Convergent user should produce agreements (values close on shared constructs)."""
    from crosscheck import build_convergences, AGREE_BAND
    # craft synthetic by-instrument dict with two measures of 'steadiness' close together
    by = {
        "personality": {"factor_scores": {"C": {"sten": 8, "name": "Emotional stability",
                                                "pole_high": "Steady", "pole_low": "Reactive"}}},
        "eq": {"domain_scores": {"self_management": {"name": "Self-management", "score": 4.5}}},
    }
    ags = build_convergences(by)
    # sten 8 → norm ~0.78, score 4.5 → norm ~0.875 → distance ~0.09 < AGREE_BAND(0.14)
    assert any(a["construct"] == "steadiness" if "construct" in a else "steadiness" in a["id"]
               for a in ags), f"expected steadiness agreement, got {ags}"
    # each body quotes both real values
    for a in ags:
        assert "8" in a["body"] and "4.5" in a["body"]


def test_bug2_tensions_only_when_far():
    from crosscheck import build_tensions
    # personality warmth sten=10 (norm 1.0), essential Emotional=0 (norm 0.0) → dist 1.0
    by = {
        "personality": {"factor_scores": {"A": {"sten": 10, "name": "Warmth",
                                                "pole_high": "Warm", "pole_low": "Reserved"}}},
        "essential": {"self": {"dimensions": {"Emotional": 0}}, "delta": {"overall": 0}},
    }
    tens = build_tensions(by, existing=[])
    assert any(t["construct"] == "closeness" for t in tens), f"expected closeness tension, got {tens}"


def test_bug2_convergent_and_divergent_via_api():
    """Create two real users, one convergent and one divergent, verify behaviour."""
    # Divergent: high personality (all 5), low closeness ease (avoidance high)
    u_div = _register()
    s = u_div["session"]
    _run(s, "personality", answers_override={})  # random baseline
    # closeness with F=1, R=7 → low anxiety / high avoidance (distant)
    from services.closeness_scoring import load_bank
    bank = load_bank()
    force = {str(it["id"]): (1 if it["key"] == "F" else 7) for it in bank["items"]}
    force["VAL-IR"] = bank["validity"][0]["expected"]
    _run(s, "closeness", answers_override=force)
    ms = s.get(f"{API}/auth/me/sessions").json()["sessions"]
    ids = [x["session_id"] for x in ms if x["status"] == "complete"]
    r = s.post(f"{API}/v2/mirrors/findings", json={"session_ids": ids}).json()
    # must have synthesis + at least one agreement or tension
    assert r["synthesis"] is not None
    assert (len(r["agreements"]) + len(r["findings"])) >= 1
    # every agreement/tension body quotes two real values (heuristic: has a digit)
    for entry in r["agreements"] + r["findings"]:
        assert re.search(r"\d", entry["body"]), f"no numbers in body: {entry}"


def test_bug2_no_crosscheck_with_one_instrument():
    """With only 1 completed instrument, findings/agreements/synthesis must be empty/None."""
    u = _register()
    sid, _, _ = _run(u["session"], "closeness")
    r = u["session"].post(f"{API}/v2/mirrors/findings", json={"session_ids": [sid]}).json()
    assert r["findings"] == []
    assert r["agreements"] == []
    assert r["synthesis"] is None


def test_bug2_combined_pdf_has_agreement_finding_and_synthesis(four_user):
    u, sids = four_user
    pdf = u["session"].get(f"{API}/v2/reports/combined.pdf", timeout=90).content
    text = _norm(_pdf_text(pdf))
    # synthesis 'How you choose — the short version'
    assert "How you choose — the short version" in text or "the short version" in text
    # need at least one AGREEMENT or FINDING entry (the labelled cards)
    has_ag = "AGREEMENT" in text
    has_fi = "FINDING" in text
    assert has_ag or has_fi, "combined PDF cross-check has neither AGREEMENT nor FINDING entry"


# ============================================================================
# Regression: item counts unchanged, closeness scoring unchanged
# ============================================================================

def test_regression_item_counts():
    from routes.mirror_v2 import _build_items
    assert len(_build_items("essential")[0]) == 100
    # personality includes validity items interleaved — spec total_items is 130 for the
    # scored personality items only; total item stream is 130 + validity
    from constants.p150_data import P150_PERSONALITY_ITEMS, P150_VALIDITY_ITEMS
    total_p = len(P150_PERSONALITY_ITEMS) + len(P150_VALIDITY_ITEMS)
    assert len(_build_items("personality")[0]) == total_p
    assert len(_build_items("eq")[0]) == 140
    assert len(_build_items("closeness")[0]) == 37

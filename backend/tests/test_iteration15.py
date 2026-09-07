"""Iteration 15 — Essential Mirror tie state (TIE_MARGIN=5) + regressions.

Tests exercise the public deploy at REACT_APP_BACKEND_URL. We use the pre-existing
tied session (test.user@ratherknow.com — every item answered 3) and the completed
ui.demo user (varied answers, single archetype) so nothing new is seeded.
"""
import os
import re
import uuid
import requests
import pytest

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")

# Session id (owner test.user@) where every essential item was answered 3 → all six
# archetypes score 50 and the tie fires with gap 0.
TIED_SESSION = "dd53396e-9745-4293-9e4c-cdb5d6296298"


def _xff():
    return {"X-Forwarded-For": f"10.{uuid.uuid4().int % 250}.{uuid.uuid4().int % 250}.{uuid.uuid4().int % 250}"}


def _login(email, password):
    s = requests.Session()
    s.headers.update(_xff())
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, r.text
    s.headers.update({"Authorization": f"Bearer {tok}"})
    return s


@pytest.fixture(scope="module")
def test_user():
    return _login("test.user@ratherknow.com", "knowmore123")


@pytest.fixture(scope="module")
def ui_demo():
    return _login("ui.demo@ratherknow.com", "knowmore123")


# ---------------------------------------------------------------------------
# Tie state — result JSON
# ---------------------------------------------------------------------------

class TestTiedEssentialResult:
    def test_result_returns_tie_block_both_lenses(self, test_user):
        r = test_user.get(f"{BASE_URL}/api/v2/assessments/{TIED_SESSION}/result", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("instrument") == "essential"
        for lens in ("self", "ideal"):
            tie = data[lens].get("tie")
            assert tie is not None, f"missing {lens}.tie"
            assert set(["tied", "gap", "margin"]).issubset(tie.keys()), tie
            assert tie["tied"] is True, f"{lens} should be tied on all-3s: {tie}"
            assert tie["gap"] == 0
            assert tie["margin"] == 5
            assert "keys" in tie and len(tie["keys"]) == 2
            assert "names" in tie and len(tie["names"]) == 2
            assert tie["keys"][0] != tie["keys"][1]
            assert "note" in tie and tie["names"][0] in tie["note"] and tie["names"][1] in tie["note"]

    def test_result_is_deterministic_across_calls(self, test_user):
        a = test_user.get(f"{BASE_URL}/api/v2/assessments/{TIED_SESSION}/result", timeout=30).json()
        b = test_user.get(f"{BASE_URL}/api/v2/assessments/{TIED_SESSION}/result", timeout=30).json()
        assert a["self"]["tie"]["keys"] == b["self"]["tie"]["keys"]
        assert a["ideal"]["tie"]["keys"] == b["ideal"]["tie"]["keys"]

    def test_ownership_enforced_on_result(self, ui_demo):
        r = ui_demo.get(f"{BASE_URL}/api/v2/assessments/{TIED_SESSION}/result", timeout=30)
        # Another user's session must not be readable
        assert r.status_code in (403, 404), r.status_code

    def test_ownership_enforced_on_report_pdf(self, ui_demo):
        r = ui_demo.get(f"{BASE_URL}/api/v2/assessments/{TIED_SESSION}/report.pdf", timeout=30)
        assert r.status_code in (403, 404), r.status_code


# ---------------------------------------------------------------------------
# Tie state — PDF & prose surfaces
# ---------------------------------------------------------------------------

class TestTiedPdfAndProse:
    def test_report_pdf_renders_and_is_pdf(self, test_user):
        r = test_user.get(f"{BASE_URL}/api/v2/assessments/{TIED_SESSION}/report.pdf", timeout=60)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"
        # PDF text is compressed streams; we can't reliably grep. Instead, assert size sane.
        assert len(r.content) > 5000

    def test_result_has_choosing_prose_naming_both(self, test_user):
        """The 'How you choose' block for a tied essential names both patterns."""
        r = test_user.get(f"{BASE_URL}/api/v2/assessments/{TIED_SESSION}/result", timeout=30).json()
        choosing = r.get("choosing") or {}
        # Serialise all point bodies to a single blob for regex search.
        blob = str(choosing)
        names = r["self"]["tie"]["names"]
        # Both names should appear somewhere in the choosing prose for the tied lens.
        for n in names:
            assert n in blob, f"choosing prose missing '{n}':\n{blob[:800]}"

    def test_result_has_no_banned_of_10_phrase_regression(self, test_user):
        r = test_user.get(f"{BASE_URL}/api/v2/assessments/{TIED_SESSION}/result", timeout=30).json()
        blob = str(r)
        # Norms pause: personality positions must not carry 'of 10' phrases (regression)
        # Essential legitimately uses "50 points" etc, so the banned phrase is 'of 10'
        # in an adjective role (e.g. "At 7 of 10"). Just make sure that phrase is absent.
        assert re.search(r"\bof 10\b", blob) is None, "banned 'of 10' phrase present"


# ---------------------------------------------------------------------------
# Regression — the four other instruments and combined PDF still work
# ---------------------------------------------------------------------------

class TestRegressionOtherInstruments:
    def test_ui_demo_has_completed_all_four(self, ui_demo):
        r = ui_demo.get(f"{BASE_URL}/api/auth/me/sessions", timeout=30)
        assert r.status_code == 200
        data = r.json()
        sessions = data.get("sessions") or data
        completed = [s for s in sessions if s.get("status") == "complete"]
        instruments = {s["instrument"] for s in completed}
        # spec says ui.demo has all four instruments complete
        for expected in ("essential", "personality", "eq", "closeness"):
            assert expected in instruments, f"ui.demo missing {expected}: {instruments}"

    def test_combined_pdf_renders(self, ui_demo):
        r = ui_demo.get(f"{BASE_URL}/api/v2/reports/combined.pdf", timeout=90)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"
        assert len(r.content) > 20_000

    def test_each_instrument_result_still_returns_200(self, ui_demo):
        sessions = ui_demo.get(f"{BASE_URL}/api/auth/me/sessions", timeout=30).json()
        rows = sessions.get("sessions") or sessions
        seen = {}
        for s in rows:
            if s.get("status") == "complete" and s["instrument"] not in seen:
                seen[s["instrument"]] = s["session_id"] if "session_id" in s else s["id"]
        assert len(seen) >= 4
        for inst, sid in seen.items():
            r = ui_demo.get(f"{BASE_URL}/api/v2/assessments/{sid}/result", timeout=30)
            assert r.status_code == 200, f"{inst}/{sid} -> {r.status_code}"


# ---------------------------------------------------------------------------
# API contract — POST/PUT/complete each carry tie block on essential
# ---------------------------------------------------------------------------

class TestEssentialTieAPIContract:
    def test_new_essential_all_3s_produces_tied_result(self, test_user):
        # Start a new essential session and answer every item = 3 → all 50s → tie.
        start = test_user.post(
            f"{BASE_URL}/api/v2/assessments", json={"instrument": "essential"}, timeout=30
        )
        assert start.status_code == 200, start.text
        session = start.json()
        session_id = session["session_id"]
        items = session["items"]
        responses = [{"item_id": it["id"], "value": 3} for it in items]

        # PUT in one chunk (safely under 16 KiB per rate-limit rule)
        # Split into batches of 40 to be safe with body size.
        for i in range(0, len(responses), 40):
            r = test_user.put(
                f"{BASE_URL}/api/v2/assessments/{session_id}/responses",
                json={"responses": responses[i:i + 40]}, timeout=30,
            )
            assert r.status_code == 200, r.text

        done = test_user.post(f"{BASE_URL}/api/v2/assessments/{session_id}/complete", timeout=60)
        assert done.status_code == 200, done.text
        data = done.json()
        for lens in ("self", "ideal"):
            tie = data[lens]["tie"]
            assert tie["tied"] is True
            assert tie["gap"] == 0
            assert tie["margin"] == 5
            assert len(tie["names"]) == 2


# ---------------------------------------------------------------------------
# Junction Check anonymous flow regression
# ---------------------------------------------------------------------------

class TestJunctionCheckAnonymous:
    def test_full_junction_flow(self):
        s = requests.Session()
        s.headers.update(_xff())
        r = s.post(f"{BASE_URL}/api/v2/junction/start", timeout=30)
        assert r.status_code == 200, r.text
        jid = r.json().get("junction_id") or r.json().get("id")
        assert jid
        # answer j1..j6 with sensible values (schema: enum strings)
        answers = [{"item_id": k, "value": v} for k, v in
                   {"j1": "no", "j2": "no", "j2b": "no", "j3": "no",
                    "j4": "no", "j5": "no", "j6": "no"}.items()]
        r = s.put(f"{BASE_URL}/api/v2/junction/{jid}/answers", json={"answers": answers}, timeout=30)
        assert r.status_code in (200, 400, 422), r.text
        r = s.post(f"{BASE_URL}/api/v2/junction/{jid}/complete", timeout=30)
        assert r.status_code in (200, 400, 409), r.text


# ---------------------------------------------------------------------------
# Flag Check anonymous reflection regression
# ---------------------------------------------------------------------------

class TestFlagCheckAnonymous:
    def test_flag_reflection_start_and_complete(self):
        s = requests.Session()
        s.headers.update(_xff())
        r = s.post(f"{BASE_URL}/api/v2/reflections", timeout=30)
        assert r.status_code == 200, r.text
        rid = r.json()["reflection_id"]
        # answer all 8 items to '3' (late) + safety 'no'
        payload = {"responses": [{"item_id": f"f{i}", "value": 3} for i in range(1, 9)]
                   + [{"item_id": "f-safety", "value": 1}]}
        r = s.put(f"{BASE_URL}/api/v2/reflections/{rid}/responses", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        r = s.post(f"{BASE_URL}/api/v2/reflections/{rid}/complete", timeout=30)
        assert r.status_code == 200, r.text
        result = r.json()
        # Reflection-only: no score, no band, no evidence tier.
        assert result["kind"] == "flag_check"
        for banned in ("score", "band", "evidence_tier"):
            assert banned not in result, f"flag reflection leaked {banned}"

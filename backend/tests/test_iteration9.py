"""Iteration 9 tests — commonness display, snapshot immutability + situation switch,
Everyday Mirror lifecycle, Partners endpoint. Uses public backend URL."""
import os
import uuid
import pytest
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _base():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if v:
        return v.rstrip("/")
    try:
        with open(os.path.join(ROOT, "frontend", ".env")) as f:
            for ln in f:
                if ln.startswith("REACT_APP_BACKEND_URL="):
                    return ln.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass
    return "http://localhost:8001"


BASE = _base()
UI_DEMO = {"email": "ui.demo@ratherknow.com", "password": "knowmore123"}
TEST_USER = {"email": "test.user@ratherknow.com", "password": "knowmore123"}


def _login(creds):
    r = requests.post(f"{BASE}/api/auth/login", json=creds, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"login failed for {creds['email']}: {r.status_code}")
    j = r.json()
    return j.get("access_token") or j.get("token")


@pytest.fixture(scope="module")
def ui_token():
    return _login(UI_DEMO)


@pytest.fixture(scope="module")
def other_token():
    return _login(TEST_USER)


def _h(t):
    return {"Authorization": f"Bearer {t}"}


# ---------- Commonness display ----------
class TestPosition:
    """The population layer is paused (B3). What the reader gets is within-person only."""

    PERSONALITY_SID = "c92ddeea-b330-4ae2-9d80-121e888d7312"

    def test_personality_result_carries_a_within_person_position_for_every_factor(self, ui_token):
        r = requests.get(f"{BASE}/api/v2/assessments/{self.PERSONALITY_SID}/result", headers=_h(ui_token), timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        pos = data.get("position") or {}
        assert pos.get("version") == "wp-1.0.0", pos.get("version")
        assert pos.get("floor") == 1.5
        scales = pos.get("scales") or {}
        assert len(scales) == 15, f"expected 15 primary factors, got {len(scales)}"
        for k, row in scales.items():
            sentence = row.get("sentence") or ""
            assert sentence.startswith(("Toward the", "Between the")), f"{k}: {sentence!r}"
            low = sentence.lower()
            for banned in ("people", "population", "percentile", "unusually", "about 1 in",
                           "sten", "/10", "very high", "very low"):
                assert banned not in low, f"{k}: paused language survived: {sentence!r}"

    def test_no_population_block_is_returned_while_norms_are_paused(self, ui_token):
        r = requests.get(f"{BASE}/api/v2/assessments/{self.PERSONALITY_SID}/result", headers=_h(ui_token), timeout=20)
        assert "commonness" not in r.json(), "the paused population layer is still being served"

    def test_at_most_three_factors_are_named(self, ui_token):
        r = requests.get(f"{BASE}/api/v2/assessments/{self.PERSONALITY_SID}/result", headers=_h(ui_token), timeout=20)
        data = r.json()
        named = [k for k, row in (data["position"]["scales"]).items() if row["loudest"]]
        assert len(named) <= 3, named

    def test_composites_and_their_provenance_survive_the_pause(self, ui_token):
        """Everything within-person was supposed to be untouched. This is the check."""
        r = requests.get(f"{BASE}/api/v2/assessments/{self.PERSONALITY_SID}/result", headers=_h(ui_token), timeout=20)
        data = r.json()
        assert data.get("global_scores")
        comps = data.get("composites") or {}
        assert comps and "globals" in comps
        assert data.get("choosing")


# ---------- Snapshot immutability + situation switch ----------
class TestSnapshotImmutability:
    PERSONALITY_SID = "c92ddeea-b330-4ae2-9d80-121e888d7312"

    def test_pdf_bytes_identical_on_two_fetches(self, ui_token):
        u = f"{BASE}/api/v2/assessments/{self.PERSONALITY_SID}/report.pdf"
        r1 = requests.get(u, headers=_h(ui_token), timeout=30)
        r2 = requests.get(u, headers=_h(ui_token), timeout=30)
        assert r1.status_code == 200 and r2.status_code == 200
        assert len(r1.content) > 500
        assert r1.content == r2.content, f"PDFs differ: {len(r1.content)} vs {len(r2.content)}"

    def test_result_json_identical_on_two_fetches(self, ui_token):
        u = f"{BASE}/api/v2/assessments/{self.PERSONALITY_SID}/result"
        r1 = requests.get(u, headers=_h(ui_token), timeout=20).json()
        r2 = requests.get(u, headers=_h(ui_token), timeout=20).json()
        assert r1 == r2

    def test_situation_switch_changes_pdf_then_restores(self, ui_token):
        me = requests.get(f"{BASE}/api/auth/me", headers=_h(ui_token), timeout=15).json()
        original = me.get("situation") or "single_dating"
        alt = "in_relationship" if original != "in_relationship" else "post_breakup"

        u_pdf = f"{BASE}/api/v2/assessments/{self.PERSONALITY_SID}/report.pdf"

        pdf_orig = requests.get(u_pdf, headers=_h(ui_token), timeout=30).content

        rp = requests.patch(f"{BASE}/api/auth/me/situation", json={"situation": alt}, headers=_h(ui_token), timeout=15)
        assert rp.status_code == 200, rp.text
        try:
            pdf_alt = requests.get(u_pdf, headers=_h(ui_token), timeout=30).content
            assert pdf_alt != pdf_orig, "PDF did not change when situation changed"
            assert len(pdf_alt) > 500
        finally:
            rr = requests.patch(f"{BASE}/api/auth/me/situation", json={"situation": original}, headers=_h(ui_token), timeout=15)
            assert rr.status_code == 200

        pdf_restore = requests.get(u_pdf, headers=_h(ui_token), timeout=30).content
        assert pdf_restore == pdf_orig, "restored PDF differs from original snapshot"


# ---------- Everyday Mirror end-to-end ----------
class TestEverydayMirror:
    def _start(self, token):
        r = requests.post(f"{BASE}/api/v2/assessments", json={"instrument": "everyday"}, headers=_h(token), timeout=20)
        assert r.status_code == 200, r.text
        return r.json()

    def test_start_returns_49_forced_choice_items(self, ui_token):
        s = self._start(ui_token)
        items = s.get("items") or []
        assert len(items) == 49, f"expected 49 items, got {len(items)}"
        # No shared response scale for everyday
        assert not s.get("scale"), "everyday must not carry a shared response scale"
        # Interstitial present between blocks
        assert s.get("interstitial"), "expected an interstitial for everyday"
        # Block A: 28 items with id A*, Block B: 21 with id starting 'B:'
        block_a = [i for i in items if i["id"].startswith("A")]
        block_b = [i for i in items if i["id"].startswith("B:")]
        assert len(block_a) == 28 and len(block_b) == 21, f"blocks: A={len(block_a)} B={len(block_b)}"
        for it in items:
            assert it.get("kind") == "choice", f"{it['id']} kind should be 'choice'"
            opts = it.get("options") or []
            assert len(opts) == 2, f"{it['id']} needs exactly 2 options"
        # Block A comes before block B
        first_b_idx = next(i for i, it in enumerate(items) if it["id"].startswith("B:"))
        assert first_b_idx == 28, f"first B item should be at index 28, got {first_b_idx}"

    def test_reject_dotted_item_id(self, ui_token):
        s = self._start(ui_token)
        sid = s["session_id"]
        r = requests.put(
            f"{BASE}/api/v2/assessments/{sid}/responses",
            json={"responses": [{"item_id": "A1.1", "value": 1}]},
            headers=_h(ui_token), timeout=15,
        )
        assert r.status_code == 400, f"dotted id should be 400, got {r.status_code}: {r.text[:200]}"

    def test_side_map_stable_within_session_random_across(self, ui_token):
        s1 = self._start(ui_token)
        s2 = self._start(ui_token)
        # Item sequence identical (statement text order)
        ids1 = [i["id"] for i in s1["items"]]
        ids2 = [i["id"] for i in s2["items"]]
        assert ids1 == ids2, "item id sequence differs across sessions — must be identical"
        # Option ordering (side) should differ probabilistically across two sessions
        opts1 = [i["options"][0] for i in s1["items"]]
        opts2 = [i["options"][0] for i in s2["items"]]
        assert opts1 != opts2, "side_map identical across two sessions — randomisation not working"

        # Resume: refetch same session and compare option ordering — must be stable
        sid = s1["session_id"]
        r = requests.get(f"{BASE}/api/v2/assessments/{sid}", headers=_h(ui_token), timeout=15)
        assert r.status_code == 200
        items_resume = r.json().get("items") or []
        opts_resume = [i["options"][0] for i in items_resume]
        assert opts_resume == opts1, "side_map not stable on resume within one session"

    def test_complete_coherent_produces_scored_positions(self, ui_token):
        s = self._start(ui_token)
        sid = s["session_id"]
        items = s["items"]
        # Coherent: always pick option index 1 (i.e. value=1) — one side per item
        resp_list = [{"item_id": it["id"], "value": 1} for it in items]
        r = requests.put(
            f"{BASE}/api/v2/assessments/{sid}/responses",
            json={"responses": resp_list}, headers=_h(ui_token), timeout=30,
        )
        assert r.status_code == 200, r.text
        rc = requests.post(f"{BASE}/api/v2/assessments/{sid}/complete", headers=_h(ui_token), timeout=30)
        assert rc.status_code == 200, rc.text

        result = requests.get(f"{BASE}/api/v2/assessments/{sid}/result", headers=_h(ui_token), timeout=20).json()

        positions = result.get("positions") or {}
        priority = result.get("priority") or {}
        assert len(positions) == 7, f"expected 7 domain positions, got {len(positions)}: {list(positions.keys())}"
        assert len(priority) == 7, f"expected 7 priority ranks, got {len(priority)}"
        # priority is a list of {domain, wins, rank, ...}
        assert isinstance(priority, list), f"priority should be list, got {type(priority)}"
        wins_sum = sum((p.get("wins") or 0) for p in priority)
        assert wins_sum == 21, f"priority wins should sum to 21, got {wins_sum}"

        # No forbidden concepts as data keys/values (the disclosure NOTE itself may
        # contain the word 'compatibility' — that's the required refusal wording)
        forbidden_keys = ("compatibility_score", "norm_score", "percentile", "band_score")
        def _has_key(obj, keys):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if any(fk in k.lower() for fk in keys):
                        return True
                    if _has_key(v, keys):
                        return True
            elif isinstance(obj, list):
                return any(_has_key(x, keys) for x in obj)
            return False
        assert not _has_key(result, forbidden_keys), "forbidden data key present in everyday result"
        assert result.get("evidence_tier") == "developmental", f"evidence_tier={result.get('evidence_tier')}"
        assert result.get("pretest_status") == "not_run", f"pretest_status={result.get('pretest_status')}"
        # position x priority map key must exist (may be null/empty when domains are undifferentiated)
        assert "map" in result, "position x priority map key missing"

        # confidence label present
        assert result.get("confidence"), "confidence label missing"

        # validity: zeta consistency, side bias, undifferentiated domains
        val = result.get("validity") or {}
        assert "zeta" in val, f"zeta missing from validity: {list(val.keys())}"
        assert "side_bias_left_pct" in val or "side_bias" in val
        assert "undifferentiated_domains" in val, "undifferentiated_domains missing"

        # PDF snapshot: byte-identical on repeat fetch
        pdf1 = requests.get(f"{BASE}/api/v2/assessments/{sid}/report.pdf", headers=_h(ui_token), timeout=30)
        pdf2 = requests.get(f"{BASE}/api/v2/assessments/{sid}/report.pdf", headers=_h(ui_token), timeout=30)
        assert pdf1.status_code == 200 and pdf2.status_code == 200
        assert pdf1.content == pdf2.content, "Everyday PDF is not byte-identical across fetches"
        # PDF text must disclose developmental / not-run
        try:
            import fitz
            doc = fitz.open(stream=pdf1.content, filetype="pdf")
            text = "\n".join(p.get_text() for p in doc).lower()
            doc.close()
            assert "developmental" in text or "pre-test" in text or "pretest" in text or "not yet" in text, \
                "PDF missing developmental/pretest disclosure"
            # Confirm the required refusal wording is present
            assert "not a compatibility score" in text or "no compatibility" in text, \
                "PDF missing 'not a compatibility score' refusal"
        except ImportError:
            pass


# ---------- Partners ----------
class TestPartners:
    def test_audience_options(self):
        r = requests.get(f"{BASE}/api/partners/audience-options", timeout=15)
        assert r.status_code == 200
        opts = r.json().get("options") or []
        assert isinstance(opts, list) and len(opts) >= 3

    def test_apply_success_and_rate_limit_and_invalid_audience(self):
        email = f"partner_{uuid.uuid4().hex[:10]}@example.com"
        opts = requests.get(f"{BASE}/api/partners/audience-options", timeout=15).json()["options"]
        valid_aud = opts[0]["value"]

        # Use a unique X-Forwarded-For so we control the rate-limit bucket
        spoof_ip = f"203.0.113.{uuid.uuid4().int % 250 + 1}"
        headers = {"X-Forwarded-For": spoof_ip}

        payload = {
            "name": "Test Partner",
            "email": email,
            "audience_where": valid_aud,
            "audience_size": "about 1000 readers",
            "why_it_fits": "Testing the endpoint for iteration 9 review.",
        }
        codes = []
        r = None
        for _ in range(4):
            r = requests.post(f"{BASE}/api/partners/apply", json=payload, headers=headers, timeout=15)
            codes.append(r.status_code)
        assert codes[0] in (200, 201), f"first apply failed: {codes} {r.text[:200]}"
        assert codes[3] == 429, f"4th apply should be 429, got {codes}"

        # Invalid audience → 400 (use a fresh IP to avoid the rate limiter absorbing it as 429)
        fresh_ip = f"198.51.100.{uuid.uuid4().int % 250 + 1}"
        bad = dict(payload, email=f"bad_{uuid.uuid4().hex[:8]}@example.com", audience_where="__nope__")
        r_bad = requests.post(f"{BASE}/api/partners/apply", json=bad,
                              headers={"X-Forwarded-For": fresh_ip}, timeout=15)
        assert r_bad.status_code == 400, f"invalid audience should be 400, got {r_bad.status_code}: {r_bad.text[:200]}"


# ---------- Auth / ownership regressions ----------
class TestAuthOwnership:
    PERSONALITY_SID = "c92ddeea-b330-4ae2-9d80-121e888d7312"

    def test_anon_start_401(self):
        r = requests.post(f"{BASE}/api/v2/assessments", json={"instrument": "everyday"}, timeout=15)
        assert r.status_code == 401

    def test_cross_user_403_result(self, other_token):
        r = requests.get(f"{BASE}/api/v2/assessments/{self.PERSONALITY_SID}/result", headers=_h(other_token), timeout=15)
        assert r.status_code == 403

    def test_cross_user_403_pdf(self, other_token):
        r = requests.get(f"{BASE}/api/v2/assessments/{self.PERSONALITY_SID}/report.pdf", headers=_h(other_token), timeout=15)
        assert r.status_code == 403

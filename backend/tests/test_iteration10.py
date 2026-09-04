"""Iteration 10 — Batch A/B work order verification.

Covers: A2 rate limiting (reflections, auth, partners) and 16 KiB body cap;
A4 essential result carries both `blend` and `compatibility` (parallel names);
B1 personality instructions say "fifteen primary factors";
B2 /diagnostics/mrd returns mrd_sd_units per scale set and per-set suppression_rate;
regression: ui.demo (completed all instruments) still logs in, gets all results,
downloads individual + combined PDFs byte-identically on repeat.
"""
import os
import uuid
import time
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE, "REACT_APP_BACKEND_URL missing"

DEMO = ("ui.demo@ratherknow.com", "knowmore123")


# ----------------------------- helpers
def _xff():
    n = uuid.uuid4().int
    return f"203.0.{(n % 254) + 1}.{(n // 254) % 254 + 1}"


def _login(email, password):
    r = requests.post(f"{BASE}/api/auth/login",
                      json={"email": email, "password": password},
                      headers={"X-Forwarded-For": _xff()})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def demo_token():
    return _login(*DEMO)


# ----------------------------- REGRESSION: ui.demo full stack still works
class TestRegressionDemoUser:
    def test_login_and_me(self, demo_token):
        r = requests.get(f"{BASE}/api/auth/me",
                         headers={"Authorization": f"Bearer {demo_token}",
                                  "X-Forwarded-For": _xff()})
        assert r.status_code == 200
        assert r.json()["user"]["email"] == DEMO[0]

    def test_all_instrument_results_render(self, demo_token):
        s = requests.Session()
        s.headers.update({"Authorization": f"Bearer {demo_token}",
                          "X-Forwarded-For": _xff()})
        r = s.get(f"{BASE}/api/auth/me/sessions")
        assert r.status_code == 200
        sessions = r.json().get("sessions", [])
        complete = [x for x in sessions if x.get("status") == "complete"]
        assert len(complete) >= 4, f"expected demo to have 4+ complete instruments, got {len(complete)}"
        for sess in complete:
            sid = sess["session_id"]
            rr = s.get(f"{BASE}/api/v2/assessments/{sid}/result")
            assert rr.status_code == 200, f"result 500'd for {sess['instrument']} {sid}: {rr.text[:200]}"
            body = rr.json()
            assert body.get("instrument"), body

    def test_individual_pdf_byte_identical(self, demo_token):
        s = requests.Session()
        s.headers.update({"Authorization": f"Bearer {demo_token}",
                          "X-Forwarded-For": _xff()})
        sessions = s.get(f"{BASE}/api/auth/me/sessions").json()["sessions"]
        sid = next(x["session_id"] for x in sessions if x.get("status") == "complete")
        a = s.get(f"{BASE}/api/v2/assessments/{sid}/report.pdf")
        b = s.get(f"{BASE}/api/v2/assessments/{sid}/report.pdf")
        assert a.status_code == 200 and b.status_code == 200
        assert a.content[:4] == b"%PDF"
        assert a.content == b.content, "individual PDF not byte-identical on repeat fetch"

    def test_combined_pdf_byte_identical(self, demo_token):
        s = requests.Session()
        s.headers.update({"Authorization": f"Bearer {demo_token}",
                          "X-Forwarded-For": _xff()})
        a = s.get(f"{BASE}/api/v2/reports/combined.pdf")
        b = s.get(f"{BASE}/api/v2/reports/combined.pdf")
        assert a.status_code == 200, a.text[:200]
        assert a.content[:4] == b"%PDF"
        assert a.content == b.content, "combined PDF not byte-identical on repeat fetch"

    def test_situation_switch_and_restore(self, demo_token):
        s = requests.Session()
        s.headers.update({"Authorization": f"Bearer {demo_token}",
                          "X-Forwarded-For": _xff()})
        me = s.get(f"{BASE}/api/auth/me").json()["user"]
        original = me.get("situation") or "single_dating"
        other = "in_relationship" if original != "in_relationship" else "post_breakup"
        # Get baseline PDF
        sessions = s.get(f"{BASE}/api/auth/me/sessions").json()["sessions"]
        sid = next(x["session_id"] for x in sessions if x.get("status") == "complete")
        a = s.get(f"{BASE}/api/v2/assessments/{sid}/report.pdf").content
        # Switch
        r = s.patch(f"{BASE}/api/auth/me/situation", json={"situation": other})
        assert r.status_code == 200, r.text
        b = s.get(f"{BASE}/api/v2/assessments/{sid}/report.pdf").content
        # Restore
        r = s.patch(f"{BASE}/api/auth/me/situation", json={"situation": original})
        assert r.status_code == 200
        c = s.get(f"{BASE}/api/v2/assessments/{sid}/report.pdf").content
        assert a == c, "PDF did not restore byte-identical after situation flip-back"
        assert a != b, "PDF should differ under a different situation snapshot key"


# ----------------------------- A2 rate limiting
class TestA2RateLimit:
    def test_anon_flag_check_full_flow_not_throttled(self):
        xff = _xff()
        h = {"X-Forwarded-For": xff, "Content-Type": "application/json"}
        r = requests.post(f"{BASE}/api/v2/reflections", headers=h)
        assert r.status_code == 200, r.text
        rid = r.json()["reflection_id"]
        # answer 8 flag items and safety
        payload = {"responses": [{"item_id": f"f{i}", "value": 1} for i in range(1, 9)]
                                + [{"item_id": "f-safety", "value": 1}]}
        r = requests.put(f"{BASE}/api/v2/reflections/{rid}/responses", json=payload, headers=h)
        assert r.status_code == 200, r.text
        r = requests.post(f"{BASE}/api/v2/reflections/{rid}/complete", headers=h)
        assert r.status_code == 200, r.text
        assert r.json().get("kind") == "flag_check"

    def test_reflections_bucket_429_after_30_and_isolated_by_xff(self):
        me_xff = _xff()
        h = {"X-Forwarded-For": me_xff}
        seen_429 = False
        for i in range(45):
            r = requests.post(f"{BASE}/api/v2/reflections", headers=h)
            if r.status_code == 429:
                seen_429 = True
                assert i >= 25, f"limiter tripped too early at i={i}"
                break
        assert seen_429, "expected 429 within 45 rapid POSTs from same XFF"
        # different origin still served
        other = requests.post(f"{BASE}/api/v2/reflections",
                              headers={"X-Forwarded-For": _xff()})
        assert other.status_code == 200, \
            f"different XFF should not be blocked, got {other.status_code}: {other.text[:150]}"

    def test_auth_limiter_normal_use_ok(self):
        # A single registration + login should never hit the 60/10min auth bucket.
        xff = _xff()
        h = {"X-Forwarded-For": xff}
        email = f"TEST_i10_{uuid.uuid4().hex[:10]}@ratherknow.com"
        r = requests.post(f"{BASE}/api/auth/register",
                          json={"name": "T10", "email": email,
                                "password": "knowmore123", "situation": "single_dating"},
                          headers=h)
        assert r.status_code in (200, 201), r.text
        r = requests.post(f"{BASE}/api/auth/login",
                          json={"email": email, "password": "knowmore123"}, headers=h)
        assert r.status_code == 200, r.text
        r = requests.post(f"{BASE}/api/auth/forgot-password",
                          json={"email": email}, headers=h)
        assert r.status_code in (200, 202, 204), r.text

    def test_auth_failed_login_lockout_still_returns_429(self):
        xff = _xff()
        h = {"X-Forwarded-For": xff}
        email = f"TEST_lock_{uuid.uuid4().hex[:8]}@ratherknow.com"
        # register first
        requests.post(f"{BASE}/api/auth/register",
                      json={"name": "Lk", "email": email,
                            "password": "knowmore123", "situation": "single_dating"},
                      headers=h)
        # 5 wrong attempts
        codes = []
        for _ in range(6):
            r = requests.post(f"{BASE}/api/auth/login",
                              json={"email": email, "password": "wrongpass"}, headers=h)
            codes.append(r.status_code)
        assert 429 in codes, f"expected 429 lockout after 5 bad logins; got {codes}"

    def test_partner_apply_oversized_body_rejected(self):
        h = {"X-Forwarded-For": _xff(), "Content-Type": "application/json"}
        big = "x" * (40 * 1024)
        payload = {"name": "T", "email": f"test_{uuid.uuid4().hex[:8]}@ratherknow.com",
                   "audience_who": big, "audience_where": "practice",
                   "audience_scale": "under_100",
                   "audience_size": "10",
                   "why_it_fits": "clinicians using between-session reflection"}
        r = requests.post(f"{BASE}/api/partners/apply", json=payload, headers=h)
        assert r.status_code in (413, 422), \
            f"expected 413/422 for oversized body, got {r.status_code}: {r.text[:200]}"

    def test_partner_apply_normal_body_succeeds(self):
        h = {"X-Forwarded-For": _xff(), "Content-Type": "application/json"}
        payload = {"name": "Iter10",
                   "email": f"test_i10_{uuid.uuid4().hex[:8]}@ratherknow.com",
                   "audience_who": "clinicians who see young adults",
                   "audience_where": "practice",
                   "audience_scale": "under_100",
                   "audience_size": "50-100 clients",
                   "why_it_fits": "This tool would help our clients reflect on their relationship patterns in a structured, non-judgemental way between sessions."}
        r = requests.post(f"{BASE}/api/partners/apply", json=payload, headers=h)
        assert r.status_code in (200, 201), r.text


# ----------------------------- A4 essential blend+compatibility parallel
class TestA4EssentialBlend:
    def test_fresh_essential_completion_carries_both_blend_and_compatibility(self):
        """A4 rename: newly-scored Essential result must emit both `blend` (new name) and
        `compatibility` (old name in parallel) on both `self` and `ideal`, each with
        type_name/description/narrative."""
        xff = _xff()
        h = {"X-Forwarded-For": xff, "Content-Type": "application/json"}
        email = f"test_ess_{uuid.uuid4().hex[:10]}@ratherknow.com"
        r = requests.post(f"{BASE}/api/auth/register",
                          json={"name": "EssA4", "email": email,
                                "password": "knowmore123", "situation": "single_dating"},
                          headers=h)
        assert r.status_code in (200, 201), r.text
        token = r.json().get("access_token") or _login(email, "knowmore123")
        s = requests.Session()
        s.headers.update({"Authorization": f"Bearer {token}", "X-Forwarded-For": xff})
        r = s.post(f"{BASE}/api/v2/assessments", json={"instrument": "essential"})
        assert r.status_code == 200, r.text
        sid = r.json()["session_id"]
        items = r.json()["items"]
        # Answer with a mix so results are non-degenerate.
        responses = [{"item_id": it["id"], "value": (i % 5) + 1}
                     for i, it in enumerate(items)]
        # PUT in chunks to be gentle.
        for i in range(0, len(responses), 50):
            rr = s.put(f"{BASE}/api/v2/assessments/{sid}/responses",
                       json={"responses": responses[i:i+50]})
            assert rr.status_code == 200, rr.text
        rr = s.post(f"{BASE}/api/v2/assessments/{sid}/complete")
        assert rr.status_code == 200, rr.text
        body = rr.json()
        for lens in ("self", "ideal"):
            assert "blend" in body[lens], f"{lens}.blend missing (A4)"
            assert "compatibility" in body[lens], f"{lens}.compatibility missing (parallel)"
            for k in ("type_name", "description", "narrative"):
                assert k in body[lens]["blend"], f"{lens}.blend missing {k}"
                assert k in body[lens]["compatibility"], f"{lens}.compatibility missing {k}"
            # New name should equal old name (parallel emit)
            assert body[lens]["blend"] == body[lens]["compatibility"], \
                f"{lens}.blend and .compatibility should be identical while both carried"
        # PDF still renders (regression – A4 must not break the report path)
        pdf = s.get(f"{BASE}/api/v2/assessments/{sid}/report.pdf")
        assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"


# ----------------------------- B1 fifteen factors
class TestB1FifteenFactors:
    def test_personality_instructions_say_fifteen(self, demo_token):
        # Start (then immediately abandon) a personality session to fetch instructions.
        s = requests.Session()
        s.headers.update({"Authorization": f"Bearer {demo_token}",
                          "X-Forwarded-For": _xff()})
        r = s.post(f"{BASE}/api/v2/assessments", json={"instrument": "personality"})
        assert r.status_code == 200, r.text
        body = r.json()
        text = " ".join(body["instructions"]["paragraphs"]).lower()
        assert "fifteen primary factors" in text, \
            f"expected 'fifteen primary factors' in instructions; got: {text}"
        assert "sixteen" not in text, f"'sixteen' still present: {text}"


# ----------------------------- B2 MRD diagnostics
class TestB2MRDDiagnostics:
    def test_mrd_endpoint_returns_sd_units_and_per_set_rates(self, demo_token):
        r = requests.get(f"{BASE}/api/v2/diagnostics/mrd",
                         headers={"Authorization": f"Bearer {demo_token}",
                                  "X-Forwarded-For": _xff()})
        assert r.status_code == 200, r.text
        body = r.json()
        assert "suppression_rate" in body
        assert "by_scale_set" in body
        assert body["by_scale_set"], "by_scale_set should be non-empty"
        for name, bucket in body["by_scale_set"].items():
            assert "mrd" in bucket, f"{name} missing mrd"
            assert "mrd_sd_units" in bucket, f"{name} missing mrd_sd_units"
            assert "suppression_rate" in bucket, f"{name} missing per-set suppression_rate"
            assert isinstance(bucket["mrd_sd_units"], (int, float))

    def test_mrd_requires_auth(self):
        r = requests.get(f"{BASE}/api/v2/diagnostics/mrd",
                         headers={"X-Forwarded-For": _xff()})
        assert r.status_code in (401, 403), r.status_code

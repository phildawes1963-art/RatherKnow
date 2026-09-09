"""The answer export: your own answers back out again, unscored.

What matters here is fidelity, not presentation. The item text must be the text that was on
screen, the answer must be the answer given, and nothing in the document may depend on a display
or scoring version — it is the one artefact in the product that cannot go stale, and these tests
are what keep it that way.
"""
import os
import re
import sys

import requests

API = os.environ.get("RK_API", "http://localhost:8001") + "/api/v2"
AUTH = os.environ.get("RK_API", "http://localhost:8001") + "/api/auth"
EMAIL = "ui.demo@ratherknow.com"
PASSWORD = "knowmore123"

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _token():
    r = requests.post(f"{AUTH}/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def _headers():
    return {"Authorization": f"Bearer {_token()}"}


def test_export_needs_an_account():
    assert requests.get(f"{API}/answers/export.json", timeout=30).status_code in (401, 403)
    assert requests.get(f"{API}/answers/export.pdf", timeout=30).status_code in (401, 403)


def test_every_completed_sitting_is_in_the_export():
    h = _headers()
    sessions = requests.get(f"{AUTH}/me/sessions", headers=h, timeout=30).json()
    if isinstance(sessions, dict):
        sessions = sessions.get("sessions", [])
    complete = [s for s in sessions if isinstance(s, dict) and s.get("status") == "complete"]
    payload = requests.get(f"{API}/answers/export.json", headers=h, timeout=60).json()
    exported = {s["session_id"] for s in payload["sittings"]}
    # Every sitting, not one per instrument: a retake is the reader's own record too.
    for s in complete[:50]:
        assert s["session_id"] in exported or len(complete) > 50


def test_each_answer_carries_the_item_text_and_the_answer_in_words():
    payload = requests.get(f"{API}/answers/export.json", headers=_headers(), timeout=60).json()
    for sitting in payload["sittings"]:
        assert sitting["answered"] > 0
        for row in sitting["answers"]:
            assert row["question"], "an item came out with no text"
            assert row["answer"], "an answer came out with no wording"
            if row["value"] is not None and not row["options"]:
                # Likert: the word must be the scale label for the number given.
                assert sitting["scale"][row["value"] - 1] == row["answer"]
            if row["options"]:
                assert row["answer"] in row["options"]
                assert row["not_chosen"] in row["options"]
                assert row["not_chosen"] != row["answer"]


def test_the_forced_choice_side_flip_is_reproduced_as_the_reader_had_it():
    """Which option sat on the left was randomised per session, and 1 means "the left one". If the
    export ignored the session's own side map it would report half of these answers backwards."""
    payload = requests.get(f"{API}/answers/export.json", headers=_headers(), timeout=60).json()
    everyday = [s for s in payload["sittings"] if s["instrument"] == "everyday"]
    if not everyday:
        return
    seen = {}
    for sitting in everyday:
        for row in sitting["answers"]:
            if row["value"] == 1:
                seen.setdefault(row["item_id"], set()).add(row["answer"])
    # Across sittings, a value of 1 must have resolved to different options for at least one
    # item — otherwise the side map is being ignored and 1 is being read as "option A".
    assert any(len(v) > 1 for v in seen.values()) or len(everyday) < 2


def test_the_export_carries_no_scoring_and_no_version():
    payload = requests.get(f"{API}/answers/export.json", headers=_headers(), timeout=60).json()
    blob = str(payload).lower()
    for word in ("sten", "algo_version", "display_version", "archetype", "delta",
                 "factor_scores", "loudest", "validity"):
        assert not re.search(rf"\b{word}\b", blob), f"the raw answer export is carrying {word}"
    # And the shape is answers, not a scored result.
    assert set(payload) == {"user", "generated_at", "note", "sittings"}
    assert set(payload["sittings"][0]["answers"][0]) == {
        "n", "item_id", "question", "options", "value", "answer", "not_chosen", "seconds", "group"}


def test_the_pdf_builds_and_says_what_it_is_not():
    r = requests.get(f"{API}/answers/export.pdf", headers=_headers(), timeout=120)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert "ratherknow-your-answers.pdf" in r.headers.get("content-disposition", "")
    import pymupdf

    doc = pymupdf.open(stream=r.content, filetype="pdf")
    text = "".join(page.get_text() for page in doc)
    assert "Your answers." in text
    assert "raw record, not a reading" in text
    assert "Nothing here is scored" in text
    assert not re.search(r"sten\s*\d", text), "a sten reached the answer export"
    # And the answers themselves, in words.
    assert "Strongly agree" in text or "Agree" in text

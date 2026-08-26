"""Copy lint over the machine-written interpretation layer (rk-1.1.0 PRD §8.1, TRD T4.4).

Verb strength is bound to evidence class. Two of these instruments are developmental, and a
developmental instrument may not predict a reader's behaviour — so the prediction verbs are
banned in the narrative modules by static analysis rather than by editorial judgement.

Scope is deliberate. The bans apply to copy *about the reader*, which is why the patterns are
anchored on "you": "we will never sell your data" is a commitment about us and stays.
"""
import ast
import os

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")

# Narrative modules: everything here composes reader-facing prose from scores.
NARRATIVE_MODULES = ("choosing.py", "crosscheck.py", "situation_notes.py", "report_pdf.py", "composites.py")

# Prediction verbs, banned in all evidence classes (PRD §8.1).
BANNED = (
    "you will", "you'll always", "you always", "you'll never",
    "you'll consistently", "you consistently",
    "expect to", "you commit", "leading to",
)

# Third-person references: no output may describe a person who did not answer (P1).
THIRD_PARTY = ("your partner is", "they are probably", "your partner will", "he will", "she will")


def _string_literals(path: str):
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.lineno, node.value


def _offenders(terms):
    found = []
    for module in NARRATIVE_MODULES:
        path = os.path.join(BACKEND, module)
        if not os.path.exists(path):
            continue
        for lineno, text in _string_literals(path):
            low = text.lower()
            for term in terms:
                if term in low:
                    found.append(f"{module}:{lineno} — '{term}' in: {text[:90]}")
    return found


def test_no_prediction_verbs_in_narrative():
    offenders = _offenders(BANNED)
    assert not offenders, "Banned prediction verbs in reader-facing copy:\n" + "\n".join(offenders)


def test_no_claims_about_a_third_party():
    offenders = _offenders(THIRD_PARTY)
    assert not offenders, "Copy describing someone who did not answer:\n" + "\n".join(offenders)


def test_no_canned_string_renders_twice():
    """A paragraph that repeats verbatim reveals itself as boilerplate. The shadow-pull warning
    used to render twice within two pages of one report; this stops it recurring."""
    import sys
    sys.path.insert(0, BACKEND)
    from choosing import build_choosing

    result = {
        "instrument": "essential",
        "self": {"primary": {"key": "guardian", "name": "The Guardian"},
                 "archetype_scores": {k: {"name": k.title()} for k in
                                      ("guardian", "challenger", "empath", "diplomat", "explorer", "builder")},
                 },
        "ideal": {"primary": {"key": "diplomat", "name": "The Diplomat"}},
        "delta": {"per_archetype": {"guardian": -12.0, "challenger": 9.0, "empath": 4.0,
                                    "diplomat": 0.0, "explorer": 2.0, "builder": -3.0},
                  "overall": 5.0, "biggest": "guardian"},
        "shadow": {"key": "empath", "name": "The Empath", "gift": "depth", "warning": "A rescue dynamic."},
    }
    block = build_choosing(result)
    bodies = [p["body"] for p in block["points"]]
    assert len(bodies) == len(set(bodies)), "A canned paragraph rendered twice in one document"


if __name__ == "__main__":
    test_no_prediction_verbs_in_narrative()
    test_no_claims_about_a_third_party()
    test_no_canned_string_renders_twice()
    print("COPY LINT OK")

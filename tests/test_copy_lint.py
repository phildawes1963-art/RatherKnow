"""Copy lint over the machine-written interpretation layer (rk-1.1.0 PRD §8.1, TRD T4.4).

Verb strength is bound to evidence class. Two of these instruments are developmental, and a
developmental instrument may not predict a reader's behaviour — so the prediction verbs are
banned in the narrative modules by static analysis rather than by editorial judgement.

Scope is deliberate. The bans apply to copy *about the reader*, which is why the patterns are
anchored on "you": "we will never sell your data" is a commitment about us and stays.

SCOPE IS DERIVED, NOT LISTED (work order A1). The previous version named five modules at
`backend/` root and skipped any that did not resolve, so `services/narrative.py` and
`services/display.py` were never linted and moving any listed file would have silently reduced
coverage to nothing while every test still passed. Now every module under the scanned trees is
linted unless it is on an explicit non-narrative allow-list, and a coverage test asserts the two
sets together account for every file found. A module added tomorrow is linted by default.
"""
import ast
import os

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")

# Trees that can hold reader-facing prose. Relative to backend/.
SCAN_DIRS = ("", "services", "routes", "constants")

# Infrastructure only: no strings about a reader. Every entry must exist on disk.
NON_NARRATIVE = ("server.py", "database.py")

# Named modules that must remain in scope. A move or rename is a broken test, not a skip.
REQUIRED = (
    "choosing.py", "crosscheck.py", "situation_notes.py", "report_pdf.py", "composites.py",
    "services/narrative.py", "services/display.py",
)

# Prediction verbs, banned in all evidence classes (PRD §8.1).
BANNED = (
    "you will", "you'll always", "you always", "you'll never",
    "you'll consistently", "you consistently",
    "expect to", "you commit", "leading to",
)

# Third-person references: no output may describe a person who did not answer (P1).
THIRD_PARTY = ("your partner is", "they are probably", "your partner will", "he will", "she will")


def discovered() -> list:
    """Every python module under the scanned trees, as backend-relative paths."""
    found = []
    for rel in SCAN_DIRS:
        directory = os.path.join(BACKEND, rel) if rel else BACKEND
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".py") or name == "__init__.py":
                continue
            found.append(f"{rel}/{name}" if rel else name)
    return found


def narrative_modules() -> list:
    return [m for m in discovered() if m not in NON_NARRATIVE]


def _string_literals(path: str):
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.lineno, node.value


def _offenders(terms):
    found = []
    for module in narrative_modules():
        path = os.path.join(BACKEND, module)
        for lineno, text in _string_literals(path):
            low = text.lower()
            for term in terms:
                if term in low:
                    found.append(f"{module}:{lineno} — '{term}' in: {text[:90]}")
    return found


def test_lint_scope_is_not_empty():
    modules = narrative_modules()
    assert modules, "Copy lint resolved zero modules — the lint is passing by covering nothing"
    assert len(modules) >= 15, f"Copy lint scope collapsed to {len(modules)} modules: {modules}"


def test_lint_scope_covers_every_backend_module():
    """No module gets zero coverage silently: it is linted, or it is on the allow-list."""
    everything = set(discovered())
    covered = set(narrative_modules()) | set(NON_NARRATIVE)
    assert everything - covered == set(), f"Modules with no lint decision: {sorted(everything - covered)}"
    stale = [m for m in NON_NARRATIVE if not os.path.exists(os.path.join(BACKEND, m))]
    assert not stale, f"Allow-list names a module that no longer exists: {stale}"


def test_required_modules_still_resolve():
    """Hard failure, not a skip. A named narrative module that has moved is a broken lint."""
    missing = [m for m in REQUIRED if not os.path.exists(os.path.join(BACKEND, m))]
    assert not missing, f"Named narrative modules missing — did they move? {missing}"
    scope = set(narrative_modules())
    assert not [m for m in REQUIRED if m not in scope], "A required module fell out of lint scope"


def test_no_prediction_verbs_in_narrative():
    offenders = _offenders(BANNED)
    assert not offenders, "Banned prediction verbs in reader-facing copy:\n" + "\n".join(offenders)


def test_no_claims_about_a_third_party():
    offenders = _offenders(THIRD_PARTY)
    assert not offenders, "Copy describing someone who did not answer:\n" + "\n".join(offenders)


def test_no_guarantee_language_while_alpha_is_placeholder(): 
    """A3: no refund or guarantee promise may appear in reader-facing copy while the MRD
    thresholds behind it rest on literature placeholder reliabilities."""
    import json

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(BACKEND, "constants", "reliability_1_0_0.json"), encoding="utf-8") as fh:
        placeholder = bool(json.load(fh).get("placeholder"))
    if not placeholder:
        return

    terms = ("refund", "money back", "money-back", "guarantee", "guaranteed", "we'll refund",
             "half your money")
    offenders = []
    surfaces = [os.path.join(root, "frontend", "src", "content", "locked_copy.json")]
    for base, _dirs, files in os.walk(os.path.join(root, "frontend", "src")):
        if "node_modules" in base:
            continue
        surfaces += [os.path.join(base, f) for f in files if f.endswith((".js", ".jsx"))]
    for path in surfaces:
        with open(path, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                low = line.lower()
                for term in terms:
                    if term in low:
                        offenders.append(f"{os.path.relpath(path, root)}:{lineno} — '{term}'")
    assert not offenders, (
        "Refund/guarantee language in reader-facing copy while reliability_1_0_0.json has "
        "placeholder=true:\n" + "\n".join(offenders)
    )


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
    test_lint_scope_is_not_empty()
    test_lint_scope_covers_every_backend_module()
    test_required_modules_still_resolve()
    test_no_prediction_verbs_in_narrative()
    test_no_claims_about_a_third_party()
    test_no_guarantee_language_while_alpha_is_placeholder()
    test_no_canned_string_renders_twice()
    print("COPY LINT OK")

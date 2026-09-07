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

# Population claims about the reader. Banned while services/display.NORM_REFERENCED is False:
# the sten bands have no documented reference sample (docs/B3_NORMS_PROVENANCE.md), so any
# sentence positioning the reader against other people is a number without a population.
# Refusals are fine and are why these are phrased as assertions: "not population percentiles"
# says we do not do it, and stays.
POPULATION = ("unusually", "than most people", "more common than", "rarer than", "how common your",
              "1 in ")

# The one module exempt from POPULATION: it *is* the paused machinery, kept intact behind the
# switch so restoring it is one flag rather than a rewrite.
POPULATION_EXEMPT = ("services/display.py",)

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


def item_banks() -> list:
    """The JSON banks carry reader-facing copy too — the Junction Check's entire output is bank
    copy (spec C1 G4), and a lint that only reads .py would never see it."""
    d = os.path.join(BACKEND, "constants")
    return [os.path.join(d, n) for n in sorted(os.listdir(d)) if n.endswith(".json")]


# `label` holds an answer OPTION the reader picks about themselves ("I expect to move within a
# few years"). The bans are on copy *we* write about the reader, so option labels are out of
# scope — banning "expect to" in an answer the reader chooses would be banning the reader.
_BANK_SKIP_KEYS = ("label", "option_a", "option_b")


def _bank_strings(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if not k.startswith("_") and k not in _BANK_SKIP_KEYS:
                yield from _bank_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _bank_strings(v)
    elif isinstance(node, str):
        yield node


def _bank_offenders(terms):
    import json

    found = []
    for path in item_banks():
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        for text in _bank_strings(data):
            low = text.lower()
            for term in terms:
                if term in low:
                    found.append(f"{os.path.basename(path)} — '{term}' in: {text[:90]}")
    return found


def _offenders(terms, skip=()):
    found = []
    for module in narrative_modules():
        if module in skip:
            continue
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
    offenders = _offenders(BANNED) + _bank_offenders(BANNED)
    assert not offenders, "Banned prediction verbs in reader-facing copy:\n" + "\n".join(offenders)


def test_the_banks_are_in_scope():
    banks = item_banks()
    assert len(banks) >= 4, f"only {len(banks)} banks found — has constants/ moved?"
    assert any("junction_bank" in b for b in banks)


def test_no_claims_about_a_third_party():
    offenders = _offenders(THIRD_PARTY) + _bank_offenders(THIRD_PARTY)
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


def test_no_population_claims_while_norms_are_paused():
    """The norms pause (B3), enforced by static analysis rather than by remembering."""
    import sys

    sys.path.insert(0, BACKEND)
    from services.display import NORM_REFERENCED

    if NORM_REFERENCED:
        return
    offenders = _offenders(POPULATION, skip=POPULATION_EXEMPT)
    assert not offenders, (
        "Copy comparing the reader with other people while the norm bands have no documented "
        "reference sample:\n" + "\n".join(offenders)
    )


def test_the_paused_population_layer_is_still_isolated():
    """If the exempt module stops being the only place population copy lives, the pause has
    leaked and the exemption is hiding it."""
    assert POPULATION_EXEMPT == ("services/display.py",)
    assert os.path.exists(os.path.join(BACKEND, "services", "display.py"))


# B4: claims that put the product in breach of its own promise 07 ("no banded scores before norms
# exist to justify them"). The pause landed in display.py and locked_copy.json in Batch B, but the
# marketing pages were never in scope and the claims stayed live there.
NORM_CLAIMS = ("calibrated norms", "calibrated norm bands", "published norms", "population middle",
               "norm bands", "sten \u2265", "sten \u2264", "sten >=", "sten <=")

PUBLIC_PAGES = ("Landing.js", "Samples.js", "Promise.js", "Methodology.js", "Partners.js", "Faq.js",
                "Instruments.js", "Learn.js", "Home.js")


def public_surfaces() -> list:
    """Reader-facing pages plus the locked register. A page added here is covered by default."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(root, "frontend", "src")
    found = [os.path.join(src, "content", "locked_copy.json"),
             os.path.join(src, "lib", "mirrorTheme.js")]
    for base, _dirs, files in os.walk(os.path.join(src, "pages")):
        if "node_modules" in base:
            continue
        found += [os.path.join(base, f) for f in files if f.endswith((".js", ".jsx"))]
    return found


def test_the_public_pages_are_in_lint_scope():
    names = {os.path.basename(p) for p in public_surfaces()}
    missing = [p for p in PUBLIC_PAGES if p in ("Landing.js", "Samples.js", "Promise.js",
                                                "Methodology.js", "Partners.js", "Faq.js")
               and p not in names]
    assert not missing, f"public pages missing from lint scope — did they move? {missing}"
    assert "locked_copy.json" in names


def test_no_norm_claims_on_the_public_pages():
    """Promise 07 in the product's own words: no banded scores before norms exist to justify them.
    docs/B3_NORMS_PROVENANCE.md establishes that no reference sample is documented, so these
    strings are a breach of a published commitment rather than a matter of taste."""
    import json

    with open(os.path.join(BACKEND, "constants", "reliability_1_0_0.json"), encoding="utf-8") as fh:
        if not json.load(fh).get("placeholder"):
            return

    offenders = []
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for path in public_surfaces():
        for lineno, line in enumerate(open(path, encoding="utf-8"), 1):
            # `_note` keys are engineering notes in the register, not copy shown to a reader.
            if line.lstrip().startswith('"_note"'):
                continue
            low = line.lower()
            for term in NORM_CLAIMS:
                if term in low:
                    offenders.append(f"{os.path.relpath(path, root)}:{lineno} — '{term}'")
    assert not offenders, (
        "Norm/banding claims in reader-facing copy while no reference sample is documented:\n"
        + "\n".join(offenders))


def test_the_instrument_count_agrees_with_the_number_of_instruments():
    """The landing page said four and listed five."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    theme = open(os.path.join(root, "frontend", "src", "lib", "mirrorTheme.js"), encoding="utf-8").read()
    cards = theme.count("\n    key: '")
    assert cards == 5, f"INSTRUMENTS now has {cards} entries — the copy below needs to follow"

    words = {4: "four", 5: "five", 6: "six"}
    landing = open(os.path.join(root, "frontend", "src", "pages", "Landing.js"), encoding="utf-8").read()
    # Every page that states a total, not just the landing one: the same defect was live on the
    # dashboard, the FAQ and the combined PDF, each of which named four while five exist.
    pages = {"pages/Landing.js", "pages/Mirrors.js", "pages/Faq.js"}
    wrong = []
    for rel in pages:
        text = open(os.path.join(root, "frontend", "src", rel), encoding="utf-8").read().lower()
        for n, w in words.items():
            if n == cards:
                continue
            for phrase in (f"{w} instruments", f"{w} mirrors"):
                if phrase in text:
                    wrong.append(f"{rel}: '{phrase}'")
    assert not wrong, f"a page names the wrong number of instruments: {wrong}"
    assert f"{words[cards]} mirrors" in landing.lower(), "the landing page no longer states the count"

    pdf = open(os.path.join(BACKEND, "report_pdf.py"), encoding="utf-8").read()
    for n, w in words.items():
        if n != cards:
            assert f"of {w} instruments" not in pdf, f"the combined PDF claims {w} instruments"


def test_every_instrument_has_a_compressed_one_line_summary():
    """B5 S6: the cards carry a line each, with the paragraph kept for the methodology page."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    theme = open(os.path.join(root, "frontend", "src", "lib", "mirrorTheme.js"), encoding="utf-8").read()
    assert theme.count("\n    line: ") == 5, "an instrument is missing its one-line summary"


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
    test_the_banks_are_in_scope()
    test_no_claims_about_a_third_party()
    test_no_guarantee_language_while_alpha_is_placeholder()
    test_no_population_claims_while_norms_are_paused()
    test_the_public_pages_are_in_lint_scope()
    test_no_norm_claims_on_the_public_pages()
    test_the_instrument_count_agrees_with_the_number_of_instruments()
    test_every_instrument_has_a_compressed_one_line_summary()
    test_the_paused_population_layer_is_still_isolated()
    test_no_canned_string_renders_twice()
    print("COPY LINT OK")

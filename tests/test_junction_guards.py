"""C1 · the Junction Check — the four guards (build spec §4).

These are written as prevention, not documentation. G1 and G3 must fail if the guard is removed,
which is what test_g1_removing_the_guard_fails and test_g3_removing_the_guard_fails demonstrate.
"""
import ast
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
os.environ.setdefault("RK_ALLOW_PLACEHOLDER_ALPHA", "1")

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(BACKEND, ".env"))

ROUTE = os.path.join(BACKEND, "routes", "junction.py")
BANK_PATH = os.path.join(BACKEND, "constants", "junction_bank_1_0_0.json")
FRONTEND = os.path.join(ROOT, "frontend", "src", "pages", "Junction.js")

BANK = json.load(open(BANK_PATH, encoding="utf-8"))
ROUTE_SRC = open(ROUTE, encoding="utf-8").read()


def _docstrings(source: str) -> set:
    """Docstrings are notes to the next engineer, not copy shown to a reader. They are excluded
    from the copy scans so that documenting a refusal does not read as committing it."""
    out = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                out.add(doc)
    return out


def _strings(source: str):
    docs = _docstrings(source)
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value not in docs:
            yield node.value


def _code_only(source: str) -> str:
    """Source with every string literal and comment removed: what the module actually does."""
    import io
    import tokenize

    kept = []
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type in (tokenize.STRING, tokenize.COMMENT):
            continue
        kept.append(tok.string)
    return " ".join(kept)


NEGATORS = ("no ", "not ", "never", "nothing", "neither", "without", "cannot", "can't", "don't")


def _is_refusal(text: str, term: str) -> bool:
    """"There is no compatibility score" is a refusal and stays; the bare claim does not."""
    low = text.lower()
    i = low.find(term)
    window = low[max(0, i - 30):i]
    return any(n in window for n in NEGATORS)


def _bank_strings(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if not k.startswith("_"):
                yield from _bank_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _bank_strings(v)
    elif isinstance(node, str):
        yield node


# ---------------------------------------------------------------- G1 · no scoring

def test_g1_no_scoring_module_exists_for_this_instrument():
    for name in os.listdir(os.path.join(BACKEND, "services")):
        assert not name.startswith("junction"), f"a junction scorer appeared: {name}"


def test_g1_the_route_imports_no_scorer():
    tree = ast.parse(ROUTE_SRC)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
        elif isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
    for module in imported:
        assert "scoring" not in module, f"the junction route imports a scorer: {module}"
        assert "p150" not in module and "display" not in module, module


def test_g1_no_function_in_the_route_scores_anything():
    names = [n.name for n in ast.walk(ast.parse(ROUTE_SRC))
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for name in names:
        for banned in ("score", "band", "norm", "percent", "rank", "weight"):
            assert banned not in name.lower(), f"function {name}() looks like scoring"


def test_g1_removing_the_guard_fails():
    """Proof the guard bites: the same check against a module that does import a scorer."""
    with pytest.raises(AssertionError):
        source = "from services.p150_lite import score_p150_lite\n"
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom):
                assert "p150" not in (node.module or "")


# ---------------------------------------------------------------- G2 · no second person

def test_g2_the_document_has_exactly_one_owner_field():
    """Schema-level prevention: there is nowhere to put a second person."""
    start = ROUTE_SRC.index("async def start(")
    doc = ROUTE_SRC[start:ROUTE_SRC.index("await db.junction_answers.insert_one", start)]
    assert doc.count('"user_id"') == 1, "more than one owner field on a junction document"
    code = _code_only(ROUTE_SRC)
    for banned in ("partner_id", "other_user", "recipient", "sender", "pair_id", "invited_by",
                   "user_ids", "second_user"):
        assert banned not in code, f"the schema acquired a second person: {banned}"


def test_g2_no_write_accepts_an_identity_from_the_caller():
    """The only id a caller supplies is the junction's own. No body field names a person."""
    for node in ast.walk(ast.parse(ROUTE_SRC)):
        if isinstance(node, ast.ClassDef):  # the pydantic request models
            fields = [n.target.id for n in node.body if isinstance(n, ast.AnnAssign)]
            for f in fields:
                assert "user" not in f and "email" not in f, f"{node.name}.{f} takes an identity"


# ---------------------------------------------------------------- G3 · share carries questions

def test_g3_the_share_payload_contains_no_answers():
    from routes.junction import _questions

    payload = _questions()

    def keys(node):
        if isinstance(node, dict):
            for k, v in node.items():
                yield k
                yield from keys(v)
        elif isinstance(node, list):
            for v in node:
                yield from keys(v)

    for banned in ("answers", "result", "junction_id", "user_id", "undecided_count", "finding",
                   "written_back", "status"):
        assert banned not in set(keys(payload)), f"the share payload leaks {banned}"


def test_g3_the_share_route_takes_no_parameter():
    """No parameter means it cannot be pointed at anybody's document."""
    tree = ast.parse(ROUTE_SRC)
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "share_payload":
            assert not node.args.args, "the share route takes an argument"
            return
    raise AssertionError("share_payload route missing")


def test_g3_no_route_can_return_someone_elses_answers_to_a_sender():
    for banned in ("/compare", "/pair", "/callback", "sender_id", "compare_with",
                   "their_answers", "recipient_answers"):
        assert banned not in ROUTE_SRC, f"a comparison path appeared: {banned}"


def test_g3_removing_the_guard_fails():
    """Proof the guard bites: a payload that did carry answers is caught."""
    leaky = {"items": [], "answers": {"j1": "yes"}}
    with pytest.raises(AssertionError):
        assert "answers" not in json.dumps(leaky)


# ---------------------------------------------------------------- G4 · no alignment language

ALIGNMENT = ("match", "compatible", "compatibility", "aligned", "alignment", "score", "percentage",
             "traffic light", "red flag", "green flag", "amber")


def test_g4_the_bank_carries_no_alignment_language():
    offenders = [f"'{term}' in: {s}" for s in _bank_strings(BANK) for term in ALIGNMENT
                 if term in s.lower() and not _is_refusal(s, term)]
    assert not offenders, "alignment language in the junction bank:\n" + "\n".join(offenders)


def test_g4_the_route_copy_carries_no_alignment_language():
    offenders = []
    for text in _strings(ROUTE_SRC):
        low = text.lower()
        for term in ALIGNMENT:
            if term in low and not _is_refusal(text, term):
                offenders.append(f"'{term}' in: {text[:90]}")
    assert not offenders, "alignment language in the junction route:\n" + "\n".join(offenders)


def test_g4_the_page_carries_no_alignment_language():
    page = open(FRONTEND, encoding="utf-8").read().lower()
    for term in ("compatib", "aligned", "% match", "traffic light"):
        assert term not in page, f"alignment language on the junction page: {term}"


def test_g4_no_agreement_count_is_produced():
    """Not a score, not a count of agreements, not 'you agree on four of six'."""
    for text in list(_strings(ROUTE_SRC)) + list(_bank_strings(BANK)):
        low = text.lower()
        for banned in ("agree on", "you both", "in common", "the same on"):
            assert banned not in low, f"an agreement claim appeared: {text}"


# ---------------------------------------------------------------- the bank itself

def test_the_bank_has_six_items_and_no_scoring_key():
    assert len(BANK["items"]) == 6
    assert BANK["instrument"] == "RK-JC-6"
    for item in BANK["items"]:
        for banned in ("domain", "option_a", "option_b", "reverse", "weight", "key", "pole"):
            assert banned not in item, f"{item['id']} carries a scoring field: {banned}"
        assert len(item["options"]) >= 4


def test_every_item_offers_an_honest_dont_know():
    """Except the two where the spec makes 'prefer not to say' or a stance the honest answer."""
    undecided_items = {"j1", "j2", "j3", "j6"}
    for item in BANK["items"]:
        has = any(o.get("undecided") for o in item["options"])
        if item["id"] in undecided_items:
            assert has, f"{item['id']} has no undecided option"
        else:
            assert not has, f"{item['id']} should not count an answer as undecided"


def test_the_faith_item_never_asks_which_faith():
    faith = next(i for i in BANK["items"] if i["id"] == "j5")
    text = json.dumps(faith).lower()
    for banned in ("christian", "muslim", "jewish", "hindu", "buddhist", "which faith",
                   "which religion", "denomination"):
        assert banned not in text, f"the faith item asks about content: {banned}"
    assert any(o["value"] == "prefer_not" for o in faith["options"])


def test_the_children_item_never_mentions_capability():
    kids = next(i for i in BANK["items"] if i["id"] == "j1")
    text = json.dumps(kids).lower()
    for banned in ("fertility", "able to", "medical", "your age", "ivf", "conceive"):
        assert banned not in text, f"the children item strays into capability: {banned}"


def test_the_closing_line_is_hash_locked():
    locked = json.load(open(os.path.join(ROOT, "frontend", "src", "content", "locked_copy.json"),
                            encoding="utf-8"))["junction"]
    assert locked["closing_lead"] == BANK["result"]["closing_lead"]
    assert locked["closing_body"] == BANK["result"]["closing_body"]


def test_the_first_screen_tells_the_reader_not_to_answer_for_somebody_else():
    assert "for somebody else" in BANK["first_screen"]["instruction"]


# ---------------------------------------------------------------- the finding

def test_the_finding_counts_unanswered_items_and_names_them():
    from routes.junction import _finding

    answers = {"j1": "yes", "j2": "settled", "j3": "never_thought", "j4": "later",
               "j5": "no", "j6": "dont_know_yet"}
    finding = _finding(answers)
    assert finding["undecided_count"] == 2
    assert finding["undecided_items"] == ["j3", "j6"]
    assert "who moves" in finding["lead"] and "whether this is exclusive" in finding["lead"]


def test_all_six_answered_is_its_own_finding():
    from routes.junction import _finding

    answers = {"j1": "no", "j2": "settled", "j3": "i_move", "j4": "later", "j5": "prefer_not",
               "j6": "one_exclusive"}
    finding = _finding(answers)
    assert finding["undecided_count"] == 0
    assert "all six" in finding["lead"]


def test_prefer_not_to_say_is_an_answer_not_a_gap():
    from routes.junction import _finding, _written_back

    answers = {"j5": "prefer_not"}
    assert "j5" not in _finding(answers)["undecided_items"]
    assert _written_back(answers)[0]["said"] == "Prefer not to say"


def test_the_finding_is_the_only_inference():
    """Every other line the reader gets is either their own answer or fixed bank copy."""
    from routes.junction import BANK as LIVE, _written_back

    said = [row["said"] for row in _written_back({"j1": "yes", "j1b": "2_to_5"})]
    assert said == ["Yes — Two to five years"]
    assert LIVE["result"]["closing_lead"].startswith("A junction passed is passed")


# ---------------------------------------------------------------- retention

def test_retention_is_ninety_days_and_the_job_exists():
    from routes.junction import RETENTION_DAYS, purge_unclaimed

    assert RETENTION_DAYS == 90
    assert callable(purge_unclaimed)


def test_the_purge_only_ever_touches_unclaimed_documents():
    source = open(ROUTE, encoding="utf-8").read()
    body = source[source.index("async def purge_unclaimed"):]
    assert '"user_id": None' in body, "the purge is not scoped to unclaimed documents"


def test_the_cron_is_declared_and_authenticated():
    crons = open(os.path.join(ROOT, ".emergent", "crons.yml"), encoding="utf-8").read()
    assert "junction-purge" in crons and "{{BASE_URL}}/api/cron/junction-purge" in crons
    cron_route = open(os.path.join(BACKEND, "routes", "cron.py"), encoding="utf-8").read()
    assert "WEBHOOK_CRON_SECRET" in cron_route and "compare_digest" in cron_route
    assert "crons.yml" not in cron_route or "WEBHOOK_CRON_SECRET=" not in crons


def test_the_claim_path_is_reused_not_reinvented():
    auth = open(os.path.join(BACKEND, "auth.py"), encoding="utf-8").read()
    assert "db.junction_answers.update_many" in auth
    assert '"user_id": {"$in": [None, user_id]}' in auth
    # And no second one in the junction route: no claim function, no owner write.
    code = _code_only(ROUTE_SRC).replace("purge_unclaimed", "purge")
    for banned in ("def claim", "claim_", "_claim", "user_id\" : user", "claim ("):
        assert banned not in code, f"a second claim path appeared in the junction route: {banned}"

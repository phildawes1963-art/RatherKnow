"""No sten reaches a reader — the guard, not the intention (disp-1.5.0).

The sten got onto a reader's page because it was in the payload with nothing marking it and a
renderer picked it up. Documenting that it should not be shown is how it happens again, so this
walks the surfaces instead.

One exemption, and it is deliberate: the five global dimensions are computed in sten units
(`5.5 + Σ(weight × (sten − 5.5))`), so the published equation cannot be audited without them. It
lives in the collapsed provenance panel on the result page and in the equation note in the PDF,
labelled as arithmetic rather than as a comparison with anyone.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend", "src")
sys.path.insert(0, BACKEND)
os.environ.setdefault("RK_ALLOW_PLACEHOLDER_ALPHA", "1")

EXEMPT_FRONTEND = {"pages/results/PersonalityResult.js"}
# The scorer and the composite equation legitimately compute in stens. Every module that speaks
# to a reader must not.
READER_FACING_BACKEND = ("crosscheck.py", "choosing.py", "services/within_person.py",
                         "services/factor_pct.py")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _walk(root, suffixes):
    for base, _dirs, files in os.walk(root):
        for name in files:
            if name.endswith(suffixes):
                yield os.path.join(base, name)


def test_no_frontend_surface_reads_a_sten_except_the_composite_equation():
    offenders = {}
    for path in _walk(FRONTEND, (".js", ".jsx")):
        rel = os.path.relpath(path, FRONTEND).replace(os.sep, "/")
        hits = re.findall(r"\.sten\b|\[.sten.\]", _read(path))
        if hits and rel not in EXEMPT_FRONTEND:
            offenders[rel] = hits
    assert not offenders, f"a sten is being rendered: {offenders}"


def test_the_one_exemption_is_only_the_equation_and_is_labelled():
    src = _read(os.path.join(FRONTEND, "pages", "results", "PersonalityResult.js"))
    # Every occurrence must be a contribution row inside the provenance panel.
    for hit in re.finditer(r"\.sten\b", src):
        line_start = src.rfind("\n", 0, hit.start())
        line = src[line_start:src.find("\n", hit.end())]
        assert "c.sten" in line, f"a sten outside the composite equation: {line.strip()}"
    assert "The units below are stens" in src, "the exemption is not labelled"


def test_no_reader_facing_backend_module_reads_a_sten():
    offenders = {}
    for rel in READER_FACING_BACKEND:
        src = _read(os.path.join(BACKEND, rel))
        # Strip docstrings and comments: explaining the ban must not read as committing it.
        code = "\n".join(ln.split("#")[0] for ln in src.splitlines())
        hits = re.findall(r'\["sten"\]|\.get\("sten"|"sten":', code)
        if hits:
            offenders[rel] = hits
    assert not offenders, f"a reader-facing module still reads a sten: {offenders}"


def test_the_payload_marks_the_sten_not_for_display():
    from services.p150_lite import score_p150_lite

    scored = score_p150_lite({str(i): (i % 5) + 1 for i in range(1, 141)})
    marker = scored["not_for_display"]
    assert "factor_scores.*.sten" in marker["fields"]
    assert "reference population" in marker["reason"]
    assert "contributions" in marker["documented_exemption"]
    # And it is still stored, because it is the raw material for rebuilding the band table.
    assert all(1 <= f["sten"] <= 10 for f in scored["factor_scores"].values())


def test_an_even_profile_names_nothing_rather_than_the_highest_one_anyway():
    """The absolute floor exists for this case. A relative floor would name three factors here,
    and "fall back to the highest" is the always-fires defect in its purest form."""
    from services.p150_lite import score_p150_lite

    for value in (1, 3, 5):
        scored = score_p150_lite({str(i): value for i in range(1, 141)})
        assert scored["loudest"] == [], f"an even profile at {value} named something"
        assert scored["strengths"] == [] and scored["blind_spots"] == []


def test_the_position_layer_carries_a_percent_not_a_sten():
    from services.factor_pct import factor_pcts
    from services.p150_lite import score_p150_lite

    scored = score_p150_lite({str(i): (i % 5) + 1 for i in range(1, 141)})
    pcts = factor_pcts(scored["factor_scores"])
    assert len(pcts) == 15
    assert all(0 <= v <= 100 for v in pcts.values())
    # Derivable from a stored result that never had pct_of_scale written on it.
    stripped = {k: {kk: vv for kk, vv in f.items() if kk != "pct_of_scale"}
                for k, f in scored["factor_scores"].items()}
    assert factor_pcts(stripped) == pcts

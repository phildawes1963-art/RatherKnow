"""Guards on the archetype documents (docs/ARCHETYPES_GUIDE.md, docs/ARCHETYPES_SPEC.md).

The two documents exist because the honest account of the item allocation is currently internal
by instruction. The failure mode is the internal one leaking into the published surface, so that
is what these tests watch. They also check the guide against the shipped data, so the published
description cannot drift from the code.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)

from services.essential_scoring import ARCHETYPES  # noqa: E402

GUIDE = os.path.join(ROOT, "docs", "ARCHETYPES_GUIDE.md")
SPEC = os.path.join(ROOT, "docs", "ARCHETYPES_SPEC.md")
PUBLIC = os.path.join(ROOT, "frontend", "public")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_the_internal_spec_is_not_published():
    """Sections 4-7 record shipped defects. It must not reach frontend/public/."""
    for dirpath, _dirs, files in os.walk(PUBLIC):
        for name in files:
            assert "spec-INTERNAL" not in name, f"internal spec published at {dirpath}/{name}"
            assert name != "ARCHETYPES_SPEC.md", f"internal spec published at {dirpath}/{name}"


def test_the_guide_does_not_leak_the_internal_findings():
    """Overlap disclosure is internal-only by instruction, pending the re-allocation decision.
    If that decision changes, delete this test deliberately rather than letting it rot."""
    guide = _read(GUIDE).lower()
    for leak in ("shared item", "overlap", "inert", "defect", "linear combination",
                 "score nothing", "_compatibility"):
        assert leak not in guide, f"internal finding '{leak}' leaked into the published guide"


def test_the_guide_names_all_six_archetypes_as_shipped():
    guide = _read(GUIDE)
    for key, arch in ARCHETYPES.items():
        assert arch["name"] in guide, f"{key} ({arch['name']}) missing from the guide"
        assert f"## {arch['name']}" in guide, f"{arch['name']} has no section of its own"


def test_the_guide_shadow_map_matches_the_code():
    """The published shadow table is the thing most likely to drift from the data."""
    guide = _read(GUIDE)
    for key, arch in ARCHETYPES.items():
        shadow_name = ARCHETYPES[arch["shadow"]]["name"]
        row = re.search(rf"^\| {re.escape(arch['name'])} \| ([^|]+) \|", guide, re.M)
        assert row, f"{arch['name']} has no row in the shadow table"
        assert shadow_name in row.group(1), (
            f"{arch['name']}: guide says shadow is '{row.group(1).strip()}', code says {shadow_name}")


def test_the_guide_counter_types_match_the_code():
    guide = _read(GUIDE)
    for arch in ARCHETYPES.values():
        assert arch["counter_type"]["name"] in guide, f"missing counter-type {arch['counter_type']['name']}"


def test_the_guide_refuses_what_the_product_refuses():
    guide = _read(GUIDE).lower()
    assert "no compatibility score" in guide
    assert "developmental" in guide
    for banned in ("you will ", "expect to ", "guaranteed"):
        assert banned not in guide, f"prediction language '{banned}' in a developmental instrument's guide"


def test_the_spec_records_the_three_defects_and_the_naming_risk():
    spec = _read(SPEC)
    assert "7, 34 and 36" in spec, "the unallocated items must be named explicitly"
    assert "diplomat.reverse = [24]" in spec
    assert "60 scoring slots" in spec
    assert "compatibility" in spec


def test_the_spec_overlap_table_matches_the_code():
    """Recompute the overlap from the shipped item lists and check the documented figures."""
    spec = _read(SPEC)
    sets = {k: set(v["questions"]) for k, v in ARCHETYPES.items()}
    assert len(sets["challenger"] & sets["visionary"]) == 5
    assert len(sets["adventurer"] & sets["visionary"]) == 3
    assert sum(len(v) for v in sets.values()) == 60
    unused = set(range(1, 51)) - set().union(*sets.values())
    assert unused == {7, 34, 36}, unused
    assert 24 not in sets["diplomat"], "item 24 is now a Diplomat item — §6 of the spec is stale"
    assert "**5** | 1, 10, 33, 35, 40" in spec, "the documented challenger x visionary overlap is stale"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
    print("ARCHETYPE DOCS OK")

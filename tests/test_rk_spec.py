"""Guards on docs/RK_SPEC.md — the as-built product and technical specification.

A spec is only worth having if its numbers are true, and these are the numbers most likely to
drift out from under it. Each test reads the live code or config and checks the document against
it, so the spec fails loudly rather than quietly becoming fiction.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
os.environ.setdefault("RK_ALLOW_PLACEHOLDER_ALPHA", "1")

SPEC = os.path.join(ROOT, "docs", "RK_SPEC.md")
PUBLIC = os.path.join(ROOT, "frontend", "public")


def _spec():
    with open(SPEC, encoding="utf-8") as fh:
        return fh.read()


def test_the_spec_is_not_published():
    """Part III names shipped defects and live promises with nothing behind them."""
    for dirpath, _dirs, files in os.walk(PUBLIC):
        for name in files:
            assert name != "RK_SPEC.md", f"internal spec published at {dirpath}/{name}"
            assert "spec-INTERNAL" not in name, f"internal spec published at {dirpath}/{name}"


def test_instrument_table_matches_the_code():
    from routes.mirror_v2 import INSTRUMENTS
    spec = _spec()
    total = sum(v["total_items"] for v in INSTRUMENTS.values())
    assert f"**{total} items**" in spec, f"item total drifted; code says {total}"
    assert f"| Total items | {total} |" in spec
    assert f"Five instruments" in spec and len(INSTRUMENTS) == 5, len(INSTRUMENTS)
    for key, meta in INSTRUMENTS.items():
        row = re.search(rf"^\| `{key}` \| [^|]+ \| ([^|]+) \|", spec, re.M)
        assert row, f"{key} missing from the instrument table"
        assert str(meta["total_items"]) in row.group(1), (
            f"{key}: spec says '{row.group(1).strip()}', code says {meta['total_items']}")


def test_mrd_thresholds_match_the_engine():
    from services.mrd import mrd_for
    spec = _spec()
    for scale_set, expected in (
        ("Personality primaries", 2.326), ("Personality globals", 1.802),
        ("EI sub-dimensions", 0.640), ("EI domains", 0.451), ("Closeness dimensions", 0.991),
    ):
        key = {"Personality primaries": "personality_primaries",
               "Personality globals": "personality_globals",
               "EI sub-dimensions": "ei_subdimensions",
               "EI domains": "ei_domains",
               "Closeness dimensions": "closeness_dimensions"}[scale_set]
        assert abs(mrd_for(key) - expected) < 0.001, f"{key}: engine {mrd_for(key)}, spec {expected}"
        assert scale_set in spec


def test_version_stamps_match_the_code():
    from routes.mirror_v2 import ALGO_VERSION
    from services.display import DISPLAY_VERSION
    from services.narrative import CONTENT_VERSION
    from services.mrd import config
    spec = _spec()
    for value in (ALGO_VERSION, DISPLAY_VERSION, CONTENT_VERSION, config()["profile_version"]):
        assert f"`{value}`" in spec, f"version stamp {value} missing or stale in the spec"


def test_situations_match_the_code():
    from auth import SITUATIONS
    spec = _spec()
    for s in SITUATIONS:
        assert f"`{s}`" in spec, f"situation {s} missing from the spec"


def test_collections_named_in_the_spec_are_the_ones_in_use():
    """Every collection the §11 table documents must actually be referenced by the backend."""
    spec = _spec()
    section = spec.split("## 11. Data model")[1].split("## 12.")[0]
    documented = set(re.findall(r"^\| `([a-z_0-9]+)` \|", section, re.M))
    assert len(documented) >= 9, f"only found {documented} in the data-model table"
    source = ""
    for sub in ("routes", "services", ""):
        d = os.path.join(BACKEND, sub)
        for name in os.listdir(d):
            if name.endswith(".py"):
                with open(os.path.join(d, name), encoding="utf-8") as fh:
                    source += fh.read()
    for coll in documented:
        assert f"db.{coll}" in source, f"spec documents collection '{coll}' that nothing uses"


def test_the_defect_register_is_present_and_ordered():
    spec = _spec()
    ids = re.findall(r"^### (R\d+) — ", spec, re.M)
    assert ids, "the defect register is missing"
    assert ids == sorted(ids, key=lambda r: int(r[1:])), f"register out of order: {ids}"
    assert len(ids) >= 12, f"only {len(ids)} risks recorded"
    # The four that must never quietly disappear.
    for must in ("guarantee has no working mechanism", "Partner promises with nothing behind them",
                 "not independent", "No data retention"):
        assert must in spec, f"missing risk: {must}"


def test_flag_check_counts_and_constraint():
    """The Flag Check may never be scored. The spec has to keep saying so, and keep counting right."""
    from routes.mirror_v2 import FLAG_ITEMS, FLAG_SAFETY_ITEM
    spec = _spec()
    assert f"{len(FLAG_ITEMS)} items plus a safety item" in spec.replace("eight", "8"), (
        f"code has {len(FLAG_ITEMS)} flag items + safety")
    assert FLAG_SAFETY_ITEM["id"]
    assert "never scored, banded, labelled, risk-rated or diagnosed" in spec
    assert "mirror_v2_reflections" in spec


def test_no_payment_integration_is_claimed():
    """The spec must not describe a checkout that does not exist."""
    spec = _spec()
    assert "no payment integration exists" in spec
    assert "not yet purchasable" in spec
    assert not os.path.exists(os.path.join(BACKEND, "routes", "payments.py")), (
        "a payments route now exists — update §8 and Phase E of the spec")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
    print("RK SPEC OK")

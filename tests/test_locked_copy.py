"""Locked-copy register guards (HANDOFF §5a).

1. Hash test: every locked string is hashed; any edit fails the build until
   tests/locked_copy_hashes.json is deliberately regenerated
   (`python tests/test_locked_copy.py --regenerate`).
2. Lint: the word "validated" may only appear in copy about the Established
   instruments (Personality, EI).
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTER = os.path.join(ROOT, "frontend", "src", "content", "locked_copy.json")
HASHES = os.path.join(ROOT, "tests", "locked_copy_hashes.json")

ESTABLISHED_TERMS = ("five-factor", "Personality", "EI Mirror", "Established", "developmental instrument")


def _flatten(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            if k.startswith("_"):
                continue
            yield from _flatten(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _flatten(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, hashlib.sha256(node.encode("utf-8")).hexdigest()


def current_hashes():
    with open(REGISTER, encoding="utf-8") as fh:
        return dict(_flatten(json.load(fh)))


def strings():
    with open(REGISTER, encoding="utf-8") as fh:
        data = json.load(fh)

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if not k.startswith("_"):
                    yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)
        elif isinstance(node, str):
            yield node

    return list(walk(data))


def test_locked_copy_hashes_unchanged():
    with open(HASHES, encoding="utf-8") as fh:
        expected = json.load(fh)
    actual = current_hashes()
    changed = {k for k in expected if expected[k] != actual.get(k)}
    removed = set(expected) - set(actual)
    added = set(actual) - set(expected)
    assert not changed, f"Locked copy edited: {sorted(changed)}"
    assert not removed, f"Locked copy removed: {sorted(removed)}"
    assert not added, f"Locked copy added without register update: {sorted(added)}"


def test_validated_only_for_established_instruments():
    offenders = [s for s in strings()
                 if "validated" in s.lower() and not any(t.lower() in s.lower() for t in ESTABLISHED_TERMS)]
    assert not offenders, f'"validated" used outside Established context: {offenders}'


if __name__ == "__main__":
    if "--regenerate" in sys.argv:
        with open(HASHES, "w", encoding="utf-8") as fh:
            json.dump(current_hashes(), fh, indent=2, sort_keys=True)
        print(f"regenerated {HASHES}")
    else:
        test_locked_copy_hashes_unchanged()
        test_validated_only_for_established_instruments()
        print("LOCKED COPY OK")

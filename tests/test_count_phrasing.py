"""No reader-facing string may hardcode a count that the data decides.

Third instance of one defect: the PDF heading promised "the three furthest" above a list of one;
the partial line read "One of your factors sit"; the methodology note said "which three sit
furthest". Fixing them as they surface has not worked, so this sweeps the whole locked set and
the reader-facing modules instead.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCKED = os.path.join(ROOT, "frontend", "src", "content", "locked_copy.json")

# Counted phrasing about the loudest-traits set, which runs 0-3 depending on what clears the
# floor. Keys that legitimately hold one string per count are exempt by name.
BANNED = [
    re.compile(r"\bthe three (?:that sit |sitting )?furthest\b", re.I),
    re.compile(r"\bwhich three\b", re.I),
    re.compile(r"\byour three furthest\b", re.I),
    re.compile(r"\bmarks the three\b", re.I),
    re.compile(r"\bof your factors sit\b(?! far enough)", re.I),
]

COUNT_KEYED = {"loudest_heading_counted", "loudest_partial", "loudest_partial_one"}


def _strings(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _strings(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _strings(value, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def test_locked_copy_has_no_hardcoded_loudest_count():
    with open(LOCKED, encoding="utf-8") as fh:
        locked = json.load(fh)
    offenders = []
    for path, text in _strings(locked):
        if any(k in path for k in COUNT_KEYED):
            continue
        for pattern in BANNED:
            if pattern.search(text):
                offenders.append(f"{path} — {pattern.pattern} — {text[:120]}")
    assert not offenders, (
        "Reader-facing copy states a count the data decides:\n" + "\n".join(offenders))


def test_the_counted_heading_covers_every_count():
    with open(LOCKED, encoding="utf-8") as fh:
        locked = json.load(fh)
    headings = locked["position"]["loudest_heading_counted"]
    assert set(headings) == {"0", "1", "2", "3"}
    assert "three" not in headings["1"].lower()
    assert "three" in headings["3"].lower()


def test_backend_reader_copy_has_no_hardcoded_loudest_count():
    """The PDF builds its own headings, so it needs the same sweep."""
    offenders = []
    for name in ("report_pdf.py", "choosing.py", "crosscheck.py"):
        path = os.path.join(ROOT, "backend", name)
        with open(path, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                for pattern in BANNED:
                    if pattern.search(line):
                        offenders.append(f"{name}:{lineno} — {stripped[:110]}")
    assert not offenders, (
        "Backend reader-facing copy states a count the data decides:\n" + "\n".join(offenders))

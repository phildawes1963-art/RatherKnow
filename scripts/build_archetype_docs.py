"""Renders the two archetype documents to PDF.

    python3 scripts/build_archetype_docs.py

The guide is publishable and lands in frontend/public/docs/. The specification is INTERNAL —
sections 4-7 record shipped defects — so it is written next to its source in docs/ and must not
be moved into frontend/public/.

A test asserts the spec never appears under public/; see tests/test_archetype_docs.py.
"""
import os

import markdown
from xhtml2pdf import pisa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DOCS = os.path.join(ROOT, "frontend", "public", "docs")
INTERNAL_DOCS = os.path.join(ROOT, "docs")

JOBS = [
    ("ARCHETYPES_GUIDE.md", PUBLIC_DOCS, "ratherknow-archetypes.pdf"),
    ("ARCHETYPES_SPEC.md", INTERNAL_DOCS, "ratherknow-archetypes-spec-INTERNAL.pdf"),
]

CSS = """
@page { size: a4 portrait; margin: 20mm 18mm 18mm 18mm; }
body { font-family: Helvetica; font-size: 9pt; color: #2A2A24; line-height: 1.5; }
h1 { font-size: 21pt; color: #1C1C18; margin: 0 0 6pt 0; }
h2 { font-size: 13pt; color: #1C1C18; margin: 18pt 0 5pt 0; border-bottom: 0.6pt solid #C9C9C0;
     padding-bottom: 3pt; }
h3 { font-size: 10pt; color: #1C1C18; margin: 12pt 0 2pt 0; }
p { margin: 5pt 0; }
strong { color: #1C1C18; }
em { color: #3B3B34; }
code { font-family: Courier; font-size: 8pt; background: #F1F1EC; }
blockquote { margin: 6pt 0 6pt 8pt; padding-left: 8pt; border-left: 1.5pt solid #B9B9B0;
             color: #3B3B34; }
table { width: 100%; border-collapse: collapse; margin: 7pt 0 9pt 0; }
th { background: #1C1C18; color: #F6F6F2; font-size: 7.5pt; padding: 4pt; text-align: left; }
td { border-bottom: 0.4pt solid #DCDCD4; font-size: 8pt; padding: 4pt; vertical-align: top; }
li { margin: 3pt 0; }
hr { border: 0; border-top: 0.5pt solid #DCDCD4; margin: 12pt 0; }
"""


def build(src_name: str, out_dir: str, out_name: str) -> str:
    with open(os.path.join(INTERNAL_DOCS, src_name), encoding="utf-8") as fh:
        body = markdown.markdown(fh.read(), extensions=["tables", "fenced_code", "sane_lists"])
    html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, out_name)
    with open(out, "wb") as fh:
        result = pisa.CreatePDF(html, dest=fh, encoding="utf-8")
    if result.err:
        raise SystemExit(f"{src_name}: PDF build failed with {result.err} error(s)")
    return out


def main() -> None:
    for src, out_dir, out_name in JOBS:
        out = build(src, out_dir, out_name)
        print(f"wrote {out} ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    main()

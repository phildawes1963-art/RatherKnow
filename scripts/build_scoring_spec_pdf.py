"""Renders docs/SCORING_SPEC.md to a shareable PDF in frontend/public/docs/.

    python3 scripts/build_scoring_spec_pdf.py
"""
import os

import markdown
from xhtml2pdf import pisa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "SCORING_SPEC.md")
OUT_DIR = os.path.join(ROOT, "frontend", "public", "docs")
OUT = os.path.join(OUT_DIR, "ratherknow-scoring-spec.pdf")

CSS = """
@page { size: a4 portrait; margin: 20mm 18mm 18mm 18mm; }
body { font-family: Helvetica; font-size: 8.5pt; color: #2A2A24; line-height: 1.45; }
h1 { font-size: 20pt; color: #1C1C18; margin: 0 0 4pt 0; }
h2 { font-size: 12.5pt; color: #1C1C18; margin: 16pt 0 4pt 0; border-bottom: 0.6pt solid #C9C9C0;
     padding-bottom: 2pt; }
h3 { font-size: 9.5pt; color: #1C1C18; margin: 11pt 0 2pt 0; }
p { margin: 4pt 0; }
strong { color: #1C1C18; }
code { font-family: Courier; font-size: 8pt; background: #F1F1EC; }
pre { background: #F6F6F2; border: 0.5pt solid #DCDCD4; padding: 6pt; font-family: Courier;
      font-size: 7.5pt; color: #1C1C18; }
table { width: 100%; border-collapse: collapse; margin: 6pt 0 8pt 0; }
th { background: #1C1C18; color: #F6F6F2; font-size: 7.5pt; padding: 4pt; text-align: left; }
td { border-bottom: 0.4pt solid #DCDCD4; font-size: 7.5pt; padding: 4pt; vertical-align: top; }
li { margin: 2pt 0; }
hr { border: 0; border-top: 0.5pt solid #DCDCD4; margin: 10pt 0; }
"""


def main():
    with open(SRC, encoding="utf-8") as fh:
        body = markdown.markdown(fh.read(), extensions=["tables", "fenced_code", "sane_lists"])
    html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "wb") as fh:
        result = pisa.CreatePDF(html, dest=fh, encoding="utf-8")
    if result.err:
        raise SystemExit(f"PDF build failed with {result.err} error(s)")
    print(f"wrote {OUT} ({os.path.getsize(OUT)} bytes)")


if __name__ == "__main__":
    main()

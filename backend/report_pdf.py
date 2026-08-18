"""Printable report — a clean PDF of an immutable, already-scored result.

Renders only what the result already contains: no re-scoring, no new claims. Every page
carries the instrument's evidence tier from the locked register, the algo_version the
result was scored under, and the safety floor. Nothing about anyone but the reader.
"""
import io
import json
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
)

INK = colors.HexColor("#1C1C18")
INK_SOFT = colors.HexColor("#3B3B34")
MUTED = colors.HexColor("#6E6E66")
LINE = colors.HexColor("#D5D5CD")
SAGE = colors.HexColor("#7E8E77")
SLATE = colors.HexColor("#5B7284")
PAPER = colors.HexColor("#F6F6F2")

_REGISTER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend", "src", "content", "locked_copy.json",
)
with open(_REGISTER_PATH, encoding="utf-8") as _fh:
    LOCKED = json.load(_fh)

INSTRUMENT_META = {
    "essential": ("Essential Mirror", "Who you are — and who you say you want", "essential"),
    "personality": ("Personality Mirror", "A validated five-factor profile", "personality"),
    "eq": ("EI Mirror", "How you handle what you feel", "eq"),
    "MI-AS-36": ("Closeness Mirror", "How you are when you’re close to someone", "closeness"),
}

S = {
    "h1": ParagraphStyle("h1", fontName="Times-Roman", fontSize=25, leading=29, textColor=INK, spaceAfter=6),
    "kicker": ParagraphStyle("kicker", fontName="Helvetica", fontSize=7.5, leading=11, textColor=MUTED, spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName="Times-Roman", fontSize=15, leading=19, textColor=INK, spaceBefore=16, spaceAfter=6),
    "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=9, leading=13, textColor=INK, spaceBefore=9, spaceAfter=3),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=14.5, textColor=INK_SOFT, alignment=TA_LEFT, spaceAfter=7),
    "lead": ParagraphStyle("lead", fontName="Times-Italic", fontSize=12, leading=17, textColor=SLATE, spaceAfter=10),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=7.5, leading=11, textColor=MUTED, spaceAfter=5),
    "quote": ParagraphStyle("quote", fontName="Times-Roman", fontSize=12, leading=17, textColor=INK, leftIndent=10, spaceAfter=8),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=8.5, leading=12, textColor=INK_SOFT),
    "cellb": ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=8.5, leading=12, textColor=INK),
}


def _tier_chip(tier_key):
    chip = LOCKED["tier_chips"][tier_key]
    statement = LOCKED["tier_statements"][tier_key]
    tbl = Table(
        [[Paragraph(f"<b>{chip}</b>", S["cellb"]), Paragraph(statement, S["cell"])]],
        colWidths=[28 * mm, 132 * mm],
    )
    tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, LINE),
        ("BACKGROUND", (0, 0), (0, 0), PAPER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl


def _bar_table(rows, width=160 * mm, maximum=100.0, suffix=""):
    """rows: (label, value, sublabel). Draws a proportional bar with no invented banding."""
    data = []
    for label, value, sub in rows:
        pct = 0 if value is None else max(0.0, min(1.0, float(value) / maximum))
        bar_w = (72 * mm) * pct
        bar = Table([[""]], colWidths=[max(bar_w, 0.4 * mm)], rowHeights=[3.6 * mm])
        bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), SLATE), ("LINEBELOW", (0, 0), (-1, -1), 0, PAPER)]))
        holder = Table([[bar, ""]], colWidths=[max(bar_w, 0.4 * mm), 72 * mm - max(bar_w, 0.4 * mm)])
        holder.setStyle(TableStyle([
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#EDEDE7")),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        value_text = "not scored" if value is None else f"{value}{suffix}"
        data.append([Paragraph(label, S["cell"]), holder, Paragraph(f"<b>{value_text}</b> {sub or ''}", S["cell"])])
    tbl = Table(data, colWidths=[46 * mm, 72 * mm, width - 118 * mm])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]))
    return tbl


# ---------- per-instrument bodies ----------

def _essential(result, flow):
    self_p = result["self"]["primary"]
    ideal_p = result["ideal"]["primary"]
    delta = result["delta"]
    flow += [
        Paragraph("As yourself, and as the partner you say you want", S["h2"]),
        Paragraph(
            f"<b>You:</b> {self_p['name']} — {self_p['subtitle']}<br/>"
            f"<b>The partner you describe:</b> {ideal_p['name']} — {ideal_p['subtitle']}",
            S["body"]),
        Paragraph(self_p.get("description", ""), S["body"]),
        Paragraph("The Delta", S["h2"]),
        Paragraph(
            f"Overall distance between the two lenses: <b>{delta['overall']} points</b>. "
            f"The widest single gap is <b>{result['self']['archetype_scores'][delta['biggest']]['name']}</b>. "
            "A gap is not a fault — it is the part of the measurement that carries information.",
            S["body"]),
        _bar_table(
            [(result["self"]["archetype_scores"][k]["name"], abs(v),
              "you want more of this than you are" if v > 0 else
              ("you are more of this than you want" if v < 0 else "no gap"))
             for k, v in sorted(delta["per_archetype"].items(), key=lambda kv: -abs(kv[1]))],
            maximum=100.0, suffix=" pts"),
    ]
    shadow = result.get("shadow")
    if shadow:
        flow += [
            Paragraph("The shadow pull", S["h2"]),
            Paragraph(f"<b>{shadow['name']}</b> — {shadow.get('gift', '')}", S["body"]),
            Paragraph(shadow.get("warning", ""), S["body"]),
        ]
    gaps = result.get("dimension_gaps") or {}
    if gaps:
        flow += [
            Paragraph("Dimension by dimension", S["h2"]),
            Paragraph("Your own score, then the gap to the partner you describe.", S["small"]),
            _bar_table([(name, result["self"]["dimensions"][name], f"gap {gaps[name]:+d}") for name in gaps],
                       maximum=100.0),
        ]


def _personality(result, flow):
    flow += [Paragraph("Five global dimensions", S["h2"])]
    flow += [_bar_table([(g["name"], g["score"], g["label"]) for g in result["global_scores"].values()], maximum=10.0)]
    flow += [
        Paragraph("Fifteen primary factors", S["h2"]),
        Paragraph("Scored 1–10 (sten) against calibrated norm bands. Five is the middle of the population.", S["small"]),
    ]
    rows = [[Paragraph("<b>Factor</b>", S["cellb"]), Paragraph("<b>Low pole</b>", S["cellb"]),
             Paragraph("<b>High pole</b>", S["cellb"]), Paragraph("<b>Sten</b>", S["cellb"]),
             Paragraph("<b>Read</b>", S["cellb"])]]
    for f in result["factor_scores"].values():
        rows.append([Paragraph(f["name"], S["cell"]), Paragraph(f["pole_low"], S["cell"]),
                     Paragraph(f["pole_high"], S["cell"]), Paragraph(str(f["sten"]), S["cell"]),
                     Paragraph(f["label"], S["cell"])])
    tbl = Table(rows, colWidths=[42 * mm, 34 * mm, 34 * mm, 14 * mm, 36 * mm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, INK),
        ("LINEBELOW", (0, 1), (-1, -2), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]))
    flow.append(tbl)
    v = result.get("validity") or {}
    sd, ct = v.get("social_desirability", {}), v.get("central_tendency", {})
    flow += [
        Paragraph("Validity indices", S["h2"]),
        Paragraph(
            f"Social desirability: {sd.get('agree_count', '—')} of {sd.get('items', '—')} "
            f"({sd.get('flag', 'NORMAL').lower()}). Central tendency: {ct.get('flag', 'NORMAL').lower()}. "
            "These are reported rather than hidden — a flagged profile is still your profile, read with a caveat.",
            S["body"]),
    ]


def _eq(result, flow):
    flow += [
        Paragraph("Four domains", S["h2"]),
        Paragraph(
            f"Overall: <b>{result['overall_score']}</b> on a 1–5 scale ({result['overall_band'].lower()}). "
            "Bands are published descriptive thresholds, not population percentiles.", S["body"]),
        _bar_table([(d["name"], d["score"], d["band"]) for d in result["domain_scores"].values()], maximum=5.0),
    ]
    for title, key in (("Where you’re strongest", "strengths"), ("Where the work is", "growth_areas")):
        items = result.get(key) or []
        if items:
            flow += [Paragraph(title, S["h3"])]
            flow += [Paragraph(f"— {i['name']} ({i['score']}, {i['band'].lower()})", S["body"]) for i in items]
    flow += [Paragraph("Fourteen sub-dimensions", S["h2"])]
    flow += [_bar_table([(s["name"], s["score"], s["band"]) for s in result["sub_scores"].values()], maximum=5.0)]


def _closeness(result, flow):
    labels = {"anxiety": ("Reassurance", "how much ongoing signal you need that things are all right"),
              "avoidance": ("Closeness", "how easily closeness itself comes")}
    flow += [
        Paragraph("Two dimensions, no boxes", S["h2"]),
        Paragraph(
            "Both are continuous. There is no box you fall into, and neither position is a fault — "
            "each carries costs and each carries information. No band or percentile is shown, because "
            "the norms to justify one do not exist yet.", S["body"]),
    ]
    rows = []
    for key, (name, gloss) in labels.items():
        d = result["dimensions"][key]
        value = d.get("value") if d.get("status") == "scored" else None
        rows.append((f"{name}<br/><font size=7 color='#6E6E66'>{gloss}</font>", value, "of 7"))
    flow += [_bar_table(rows, maximum=7.0)]
    v = result.get("validity") or {}
    flow += [
        Paragraph("Confidence in this reading", S["h2"]),
        Paragraph(
            f"<b>{(result.get('confidence') or 'not established').title()}</b>. Four checks ran on your answers — an "
            f"instructed-response item, three consistency pairs, the longest identical-answer run "
            f"({v.get('long_string_max', '—')}), and a time floor (mean {v.get('mean_ms', '—')} ms per item). "
            "They set this label; nothing was deleted or silently corrected.", S["body"]),
        Paragraph(f"Item bank {result.get('bank_version', '—')} · scoring {result.get('scoring_version', '—')}", S["small"]),
    ]


BODIES = {"essential": _essential, "personality": _personality, "eq": _eq, "MI-AS-36": _closeness}


def build_report_pdf(*, result: dict, user: dict, situation_note: str | None = None) -> bytes:
    instrument = result["instrument"]
    name, tagline, tier_key = INSTRUMENT_META[instrument]
    buf = io.BytesIO()

    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=25 * mm, rightMargin=25 * mm, topMargin=22 * mm, bottomMargin=20 * mm,
        title=f"{name} — {user['name']}", author="Rather Know", subject=name,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body", showBoundary=0)

    completed = result.get("completed_at", "")
    try:
        stamped = datetime.fromisoformat(completed).strftime("%d %B %Y")
    except ValueError:
        stamped = completed[:10]

    def decorate(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(INK)
        canvas.setFont("Times-Roman", 10)
        canvas.drawString(25 * mm, A4[1] - 14 * mm, "Rather Know.")
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(A4[0] - 25 * mm, A4[1] - 14 * mm, f"{name} · {stamped}")
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(25 * mm, A4[1] - 17 * mm, A4[0] - 25 * mm, A4[1] - 17 * mm)
        canvas.line(25 * mm, 15 * mm, A4[0] - 25 * mm, 15 * mm)
        canvas.setFont("Helvetica", 6.5)
        canvas.drawString(25 * mm, 11 * mm, LOCKED["disclaimer"])
        canvas.drawRightString(A4[0] - 25 * mm, 11 * mm, f"Page {_doc.page} · scored under {result.get('algo_version', '—')}")
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=decorate)])

    flow = [
        Paragraph(f"PREPARED FOR {user['name'].upper()} · {stamped}", S["kicker"]),
        Paragraph(name, S["h1"]),
        Paragraph(tagline, S["lead"]),
        _tier_chip(tier_key),
        Spacer(1, 6 * mm),
    ]
    if situation_note:
        flow += [
            Paragraph("Read for where you are", S["h3"]),
            Paragraph(situation_note, S["body"]),
            Paragraph("The scoring never changes with your situation. Only the framing does.", S["small"]),
        ]

    BODIES[instrument](result, flow)

    flow += [
        Spacer(1, 8 * mm),
        KeepTogether([
            Paragraph("If you’re ever afraid of someone", S["h2"]),
            Paragraph(LOCKED["safety"]["headline"], S["body"]),
            Paragraph(LOCKED["safety"]["floor"], S["quote"]),
            Paragraph(
                "National Domestic Abuse Helpline 0808 2000 247 (free, 24 hours) · "
                "Respect Men’s Advice Line 0808 8010 327 · Galop 0800 999 5428 · "
                "Samaritans 116 123 · In immediate danger, call 999.", S["body"]),
        ]),
        KeepTogether([
            Paragraph("What this document is not", S["h2"]),
            Paragraph(
                "It contains no verdict on any other person — the instrument never asked about anyone but you. "
                "There is no compatibility score here, no clinical label, and no prediction. Results are "
                f"snapshots: this one was scored under {result.get('algo_version', '—')} and is never recomputed, "
                "so if the norms change later, this page still says exactly what it said on the day.", S["body"]),
            Paragraph(LOCKED["attribution"], S["small"]),
        ]),
    ]

    doc.build(flow)
    return buf.getvalue()

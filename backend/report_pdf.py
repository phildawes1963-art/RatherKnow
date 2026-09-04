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
    "MI-EV-49": ("Everyday Mirror", "Where you sit, and what you’d protect", "everyday"),
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
        Paragraph(
            "A zero gap is a finding too, and not a contradiction: where the archetype you named as the "
            "partner you want shows no gap, you are describing someone who already carries as much of that "
            "quality as you do. The named archetype is the highest score in that lens; the gap is the distance "
            "between the lenses. They answer different questions.", S["small"]),
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
            Paragraph("What this pull does at the point of choosing is set out in "
                      "“How you choose”, below.", S["small"]),
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
    flow += [
        Paragraph("Five global dimensions", S["h2"]),
        Paragraph(
            "These five are derived, not measured — each is a weighted sum of the primary factors below, "
            "clipped to the 1–10 scale. That is why they show a position and their equation rather than a "
            "population comparison: a clipped composite cannot carry one honestly.", S["small"]),
    ]
    # The band word (Very High … Very Low) is paused with the rest of the population layer, so the
    # third column shows where the number sits on its own scale. Older results still carry `label`
    # and are read from their own frozen narrative snapshot, never re-rendered through here.
    flow += [_bar_table([(g["name"], g["score"], f"{g['score']} of 10")
                         for g in result["global_scores"].values()], maximum=10.0)]
    from composites import build_composites
    prov = build_composites(result)
    if prov:
        clamped = [e for e in (prov.get("clamp_events") or [])]
        if clamped:
            flow += [Paragraph(
                "Clipped: " + "; ".join(
                    f"{e['name']} computes to {e['raw']} and is published as {e['published']}" for e in clamped)
                + ". The direction is unambiguous; the exact distance is not.", S["small"])]
        flow += [
            Paragraph("How each global dimension is built", S["h3"]),
            Paragraph(prov["note"], S["body"]),
        ]
        rows = [[Paragraph("<b>Dimension</b>", S["cellb"]), Paragraph("<b>Built from</b>", S["cellb"])]]
        for key, g in prov["globals"].items():
            parts = ", ".join(
                f"{c['name']} {c['weight']:+g}" for c in g["contributions"]
            )
            flag = " (known residual)" if g["known_residual"] else ""
            rows.append([Paragraph(g["name"] + flag, S["cell"]), Paragraph(parts, S["cell"])])
        tbl = Table(rows, colWidths=[46 * mm, 114 * mm], repeatRows=1)
        tbl.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, 0), 0.7, INK),
            ("LINEBELOW", (0, 1), (-1, -2), 0.35, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (0, -1), 0),
        ]))
        flow += [tbl, Paragraph(prov["residual_note"], S["small"])]
    flow += [
        Paragraph("Fifteen primary factors", S["h2"]),
        Paragraph(
            "Each factor is a position between two poles, and neither pole is better — both carry costs and both "
            "carry information. Each row says which way you lean and how far that sits from your own middle. "
            "Nothing in this table compares you with other people: the bands behind these scores have no "
            "published reference sample yet, so a comparison would be a number without a population.", S["small"]),
    ]
    from services.within_person import build_position
    scales = build_position(
        {k: f["sten"] for k, f in result["factor_scores"].items() if f.get("sten") is not None},
        {k: f for k, f in result["factor_scores"].items()},
    ).get("scales", {})
    rows = [[Paragraph("<b>Factor</b>", S["cellb"]), Paragraph("<b>Low pole</b>", S["cellb"]),
             Paragraph("<b>High pole</b>", S["cellb"]), Paragraph("<b>Where you sit</b>", S["cellb"])]]
    for key, f in result["factor_scores"].items():
        line = (scales.get(key) or {}).get("sentence", "")
        rows.append([Paragraph(f["name"], S["cell"]), Paragraph(f["pole_low"], S["cell"]),
                     Paragraph(f["pole_high"], S["cell"]), Paragraph(line, S["cell"])])
    tbl = Table(rows, colWidths=[38 * mm, 28 * mm, 28 * mm, 66 * mm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, INK),
        ("LINEBELOW", (0, 1), (-1, -2), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]))
    flow.append(tbl)
    loud = result.get("loudest") or []
    flow += [Paragraph("The three furthest from your own middle", S["h2"])]
    if loud:
        flow += [Paragraph(
            "Traits at this distance are the ones doing the selecting — what you notice first in somebody, "
            "and what you are most likely to over-weight.", S["small"])]
        flow += [Paragraph(f"— {e['name']}: toward the {e['pole'].lower()} end.", S["body"]) for e in loud]
    else:
        flow += [Paragraph(
            "None of your factors sits far enough from your own middle to name one confidently. That is a "
            "real result rather than a missing one.", S["body"])]

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
            f"Overall: <b>{result['overall_score']}</b> on a 1–5 scale. Each number is the mean of your own "
            "answers in that domain. There is no grade attached to it: a band word would imply a standard, "
            "and no reference sample is documented for these thresholds.", S["body"]),
        _bar_table([(d["name"], d["score"], f"{d['score']} of 5") for d in result["domain_scores"].values()],
                   maximum=5.0),
    ]
    for title, key in (("Your highest of the fourteen", "strengths"), ("Your lowest of the fourteen", "growth_areas")):
        items = result.get(key) or []
        if items:
            flow += [Paragraph(title, S["h3"])]
            flow += [Paragraph(f"— {i['name']} ({i['score']} of 5)", S["body"]) for i in items]
    flow += [Paragraph("Fourteen sub-dimensions", S["h2"])]
    flow += [_bar_table([(s["name"], s["score"], f"{s['score']} of 5") for s in result["sub_scores"].values()],
                        maximum=5.0)]


def _closeness(result, flow):
    # Both dimensions are DISTANCE scores: high = more of the thing named, not more ease.
    # Plotting the avoidance datum under an "ease" label inverted the chart against the prose.
    labels = {"anxiety": ("Need for reassurance", "how much ongoing signal you need that things are all right"),
              "avoidance": ("Distance from closeness", "how far away closeness itself sits — low means it comes easily")}
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
    avo = (result["dimensions"].get("avoidance") or {})
    if avo.get("status") == "scored" and avo.get("value") is not None:
        flow += [Paragraph(
            f"Read the second bar as distance, not ease. Yours reads {avo['value']} of 7, which means closeness "
            f"comes {'easily' if avo['value'] <= 3 else 'harder than average' if avo['value'] >= 5 else 'neither easily nor hard'} "
            "— a short bar is closeness arriving quickly.", S["small"])]
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


def _everyday(result, flow):
    CELLS = {
        "non_negotiable": "a genuine line",
        "strong_but_tradeable": "strong, but tradeable",
        "needs_settling": "not fussy — just needs settling",
        "low_friction": "unlikely to be where the friction is",
    }
    flow += [
        Paragraph("Where you sit", S["h2"]),
        Paragraph(
            "Four either/or choices per domain, so each position runs from 0 to 4 between two named poles. "
            "No band, no percentile, no norm — five possible positions, shown as position only. An even split "
            "is reported as undifferentiated rather than as a middle, because those are different claims.",
            S["small"]),
    ]
    rows = [[Paragraph("<b>Domain</b>", S["cellb"]), Paragraph("<b>Position</b>", S["cellb"]),
             Paragraph("<b>Between</b>", S["cellb"])]]
    for pos in result["positions"].values():
        if pos.get("position") is None:
            read = "not enough answers to place you"
            between = ""
        else:
            read = pos["label"]
            between = f"{pos['pole_b']} ← → {pos['pole_a']}"
        rows.append([Paragraph(pos["name"], S["cell"]), Paragraph(read, S["cell"]),
                     Paragraph(between, S["cell"])])
    tbl = Table(rows, colWidths=[36 * mm, 58 * mm, 66 * mm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, INK),
        ("LINEBELOW", (0, 1), (-1, -2), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]))
    flow += [tbl]

    flow += [
        Paragraph("What you'd protect", S["h2"]),
        Paragraph(
            "Twenty-one comparisons, every domain against every other once. Wins are your own choices ranked "
            "against each other — not against anyone else's.", S["small"]),
        _bar_table([(p["name"], p["wins"], p["descriptor"] + (" · tied" if p["tied"] else ""))
                    for p in result["priority"]], maximum=6.0, suffix=" of 6"),
    ]

    if result.get("map"):
        flow += [Paragraph("Position against priority", S["h2"]),
                 Paragraph("The corners are the interesting part.", S["small"])]
        rows = [[Paragraph("<b>Domain</b>", S["cellb"]), Paragraph("<b>Reads as</b>", S["cellb"])]]
        for c in sorted(result["map"], key=lambda x: x["priority_rank"]):
            rows.append([Paragraph(c["name"], S["cell"]),
                         Paragraph(f"{c['label']}, ranked {c['priority_rank']} of 7 — {CELLS[c['cell']]}", S["cell"])])
        tbl = Table(rows, colWidths=[36 * mm, 124 * mm], repeatRows=1)
        tbl.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, 0), 0.7, INK),
            ("LINEBELOW", (0, 1), (-1, -2), 0.35, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (0, -1), 0),
        ]))
        flow += [tbl]

    v = result.get("validity") or {}
    flow += [
        Paragraph("Confidence in this reading", S["h2"]),
        Paragraph(
            f"<b>{(result.get('confidence') or 'not established').title()}</b>. Three behavioural checks ran on the "
            f"choices themselves rather than on anything you told us: loops in your comparisons (consistency index "
            f"{v.get('zeta', '—')}), how often you picked the left-hand option when the sides were randomised "
            f"({v.get('side_bias_left_pct', '—')}%), and a time floor (mean {v.get('mean_ms', '—')} ms per item).",
            S["body"]),
        Paragraph(result.get("claim_limit", ""), S["body"]),
        Paragraph(
            "One outstanding caveat, published rather than buried: the option pairs have not yet been "
            "desirability pre-tested, so some may not be perfectly matched for how flattering they sound. Until "
            "that testing is done this instrument contributes to a reading and never anchors one alone.", S["small"]),
        Paragraph(f"Item bank {result.get('bank_version', '—')} · scoring {result.get('scoring_version', '—')}", S["small"]),
    ]


BODIES = {"essential": _essential, "personality": _personality, "eq": _eq, "MI-AS-36": _closeness,
          "MI-EV-49": _everyday}


def _choosing_block(result):
    """The 'how you choose' translation, printed under each instrument's numbers."""
    from choosing import build_choosing
    block = build_choosing(result)
    if not block:
        return []
    flow = [Paragraph("How you choose", S["h2"]), Paragraph(block["lead"], S["body"])]
    for p in block["points"]:
        flow.append(KeepTogether([Paragraph(p["title"], S["h3"]), Paragraph(p["body"], S["body"])]))
    flow.append(Paragraph(block["closing"], S["small"]))
    return flow


def _stamp(result: dict) -> str:
    completed = result.get("completed_at", "")
    try:
        return datetime.fromisoformat(completed).strftime("%d %B %Y")
    except ValueError:
        return completed[:10]


def _safety_block():
    return KeepTogether([
        Paragraph("If you’re ever afraid of someone", S["h2"]),
        Paragraph(LOCKED["safety"]["headline"], S["body"]),
        Paragraph(LOCKED["safety"]["floor"], S["quote"]),
        Paragraph(
            "National Domestic Abuse Helpline 0808 2000 247 (free, 24 hours) · "
            "Respect Men’s Advice Line 0808 8010 327 · Galop 0800 999 5428 · "
            "Samaritans 116 123 · In immediate danger, call 999.", S["body"]),
    ])


def _limits_block(versions: str):
    return KeepTogether([
        Paragraph("What this document is not", S["h2"]),
        Paragraph(
            "It contains no verdict on any other person — the instruments never asked about anyone but you. "
            "There is no compatibility score here, no clinical label, and no prediction. Results are "
            f"snapshots: scored under {versions} and never recomputed, so if the norms change later, these "
            "pages still say exactly what they said on the day.", S["body"]),
        Paragraph(LOCKED["attribution"], S["small"]),
    ])


def build_combined_pdf(*, results: list, user: dict, findings: list, situation_notes: dict,
                       agreements: list | None = None, synthesis: dict | None = None) -> bytes:
    """Every finished mirror plus the cross-check, in one document."""
    buf = io.BytesIO()
    versions = ", ".join(sorted({r.get("algo_version", "—") for r in results})) or "—"
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=25 * mm, rightMargin=25 * mm, topMargin=22 * mm, bottomMargin=20 * mm,
        title=f"Your mirrors — {user['name']}", author="Rather Know", subject="Combined report",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    today = datetime.now().strftime("%d %B %Y")

    def decorate(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(INK)
        canvas.setFont("Times-Roman", 10)
        canvas.drawString(25 * mm, A4[1] - 14 * mm, "Rather Know.")
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(A4[0] - 25 * mm, A4[1] - 14 * mm, f"Your mirrors · {today}")
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(25 * mm, A4[1] - 17 * mm, A4[0] - 25 * mm, A4[1] - 17 * mm)
        canvas.line(25 * mm, 15 * mm, A4[0] - 25 * mm, 15 * mm)
        canvas.setFont("Helvetica", 6.5)
        canvas.drawString(25 * mm, 11 * mm, LOCKED["disclaimer"])
        canvas.drawRightString(A4[0] - 25 * mm, 11 * mm, f"Page {_doc.page} · scored under {versions}")
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=decorate)])

    ordered = [r for key in ("essential", "MI-AS-36", "personality", "eq")
               for r in results if r["instrument"] == key]

    flow = [
        Paragraph(f"PREPARED FOR {user['name'].upper()} · {today}", S["kicker"]),
        Paragraph("Your mirrors", S["h1"]),
        Paragraph("Everything you’ve measured, read side by side", S["lead"]),
        Paragraph(
            f"{len(ordered)} of four instruments completed. Where they agree, that’s signal. Where they "
            "disagree, that’s not an error — it’s a finding, and usually the more interesting one.", S["body"]),
    ]
    contents = [[Paragraph("<b>Instrument</b>", S["cellb"]), Paragraph("<b>Evidence tier</b>", S["cellb"]),
                 Paragraph("<b>Completed</b>", S["cellb"])]]
    for r in ordered:
        name, _, tier_key = INSTRUMENT_META[r["instrument"]]
        contents.append([Paragraph(name, S["cell"]),
                         Paragraph(LOCKED["tier_chips"][tier_key], S["cell"]),
                         Paragraph(_stamp(r), S["cell"])])
    table = Table(contents, colWidths=[70 * mm, 45 * mm, 45 * mm])
    table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, INK),
        ("LINEBELOW", (0, 1), (-1, -2), 0.35, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]))
    flow += [Spacer(1, 4 * mm), table]

    if synthesis:
        flow += [
            Paragraph(synthesis["title"], S["h2"]),
            Paragraph(synthesis["body"], S["body"]),
            Paragraph(synthesis["footnote"], S["small"]),
        ]

    if len(ordered) >= 2:
        flow += [
            Paragraph("The cross-check", S["h2"]),
            Paragraph(
                "Two things happen when instruments that share no questions are read together. Where they agree, "
                "that convergence is signal. Where they pull apart, that’s a finding — and it’s usually the more "
                "interesting one. Neither is a verdict.", S["body"]),
        ]
        for a in (agreements or []):
            flow.append(KeepTogether([
                Paragraph("AGREEMENT · " + " × ".join(a.get("sources", [])).upper(), S["kicker"]),
                Paragraph(a["title"], S["h3"]),
                Paragraph(a["body"], S["body"]),
            ]))
        for f in findings:
            flow.append(KeepTogether([
                Paragraph("FINDING · " + " × ".join(f.get("sources", [])).upper(), S["kicker"]),
                Paragraph(f["title"], S["h3"]),
                Paragraph(f["body"], S["body"]),
            ]))
        if not findings:
            flow.append(Paragraph(
                "No tensions worth reporting — where your completed instruments overlap, they broadly agree. "
                "That’s signal too, and we won’t invent a disagreement to seem insightful.", S["body"]))

    for r in ordered:
        name, tagline, tier_key = INSTRUMENT_META[r["instrument"]]
        flow += [
            Spacer(1, 6 * mm),
            Paragraph(name.upper(), S["kicker"]),
            Paragraph(tagline, S["lead"]),
            _tier_chip(tier_key),
            Spacer(1, 3 * mm),
        ]
        note = situation_notes.get(r["instrument"])
        if note:
            flow += [Paragraph("Read for where you are", S["h3"]), Paragraph(note, S["body"])]
        BODIES[r["instrument"]](r, flow)
        flow += _choosing_block(r)

    flow += [Spacer(1, 8 * mm), _safety_block(), _limits_block(versions)]
    doc.build(flow)
    return buf.getvalue()


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
    flow += _choosing_block(result)

    flow += [
        Spacer(1, 8 * mm),
        _safety_block(),
        _limits_block(result.get("algo_version", "—")),
    ]

    doc.build(flow)
    return buf.getvalue()

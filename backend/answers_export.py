"""Your own answers, back out again — every item, as you answered it.

Not a reading. No scoring, no interpretation, no version-dependent display layer: the item as it
was put to you, the answer you gave, and how long you spent on it. That makes this the one
document here that cannot go stale, which is also why it is not snapshotted like the reports are —
it is rebuilt from the stored responses each time, because there is nothing in it to freeze.

Item text comes from the same builder the runner used (`routes.mirror_v2._build_items`), passed in
rather than imported, so the wording and the order are exactly what was on screen — including the
per-session side flip on the Everyday Mirror, where which option sat on the left was randomised.
"""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

from report_pdf import INK, LINE, LOCKED, MUTED, PAPER, S

INSTRUMENT_NAMES = {
    "essential": "Essential Mirror",
    "closeness": "Closeness Mirror",
    "personality": "Personality Mirror",
    "eq": "EI Mirror",
    "everyday": "Everyday Mirror",
}

# The two halves of the instruments that ask twice. Taken from the interstitial the runner shows
# between them, so the split in the document is the split the reader experienced.
GROUP_TITLES = {
    "essential": ("Answered as you", "Answered as the partner you say you want"),
    "everyday": ("Where you actually sit", "What you would need to agree on"),
}


def _when(value: str) -> str:
    try:
        return datetime.fromisoformat(value).strftime("%d %B %Y, %H:%M")
    except (ValueError, TypeError):
        return (value or "")[:16] or "—"


def answer_records(session: dict, items_for) -> dict:
    """One session, flattened: every item put to the reader and what they answered."""
    instrument = session["instrument"]
    items, scale, _instructions, interstitial = items_for(instrument, session)
    responses = session.get("responses") or {}
    split_at = (interstitial or {}).get("after_index")
    titles = GROUP_TITLES.get(instrument)

    rows = []
    for index, item in enumerate(items):
        answered = responses.get(item["id"]) or {}
        value = answered.get("v")
        if item.get("options"):
            # 1 is whichever option was rendered on the left for this session.
            chosen = item["options"][value - 1] if value in (1, 2) else None
            not_chosen = item["options"][2 - value] if value in (1, 2) else None
            answer = chosen or "not answered"
        else:
            chosen = not_chosen = None
            answer = (scale[value - 1] if scale and isinstance(value, int)
                      and 1 <= value <= len(scale) else "not answered")
        group = None
        if titles and split_at is not None:
            group = titles[0] if index <= split_at else titles[1]
        rows.append({
            "n": index + 1,
            "item_id": item["id"],
            "question": item["text"],
            "options": item.get("options"),
            "value": value,
            "answer": answer,
            "not_chosen": not_chosen,
            "seconds": round(answered["ms"] / 1000, 1) if answered.get("ms") else None,
            "group": group,
        })

    spent = [r["seconds"] for r in rows if r["seconds"]]
    return {
        "instrument": instrument,
        "instrument_name": INSTRUMENT_NAMES.get(instrument, instrument),
        "session_id": session["id"],
        "started_at": session.get("started_at"),
        "completed_at": session.get("completed_at"),
        "scale": scale,
        "items": len(rows),
        "answered": sum(1 for r in rows if r["value"] is not None),
        "minutes_on_items": round(sum(spent) / 60, 1) if spent else None,
        "answers": rows,
    }


def _table(rows: list) -> Table:
    data = [[Paragraph("<b>#</b>", S["cell"]), Paragraph("<b>Item</b>", S["cell"]),
             Paragraph("<b>Your answer</b>", S["cell"]), Paragraph("<b>Secs</b>", S["cell"])]]
    for r in rows:
        answer = r["answer"] if r["value"] is None else (
            f"{r['answer']}" if r["options"] else f"{r['value']} · {r['answer']}")
        # The forced-choice block names both options inside the question already; repeating them
        # underneath is just the same sentence twice.
        options = r["options"] if r["options"] and r["options"][0] not in r["question"] else None
        data.append([
            Paragraph(str(r["n"]), S["cell"]),
            Paragraph(r["question"] if not options
                      else f"{r['question']}<br/><font color='#9C9C93'>"
                           f"{options[0]} / {options[1]}</font>", S["cell"]),
            Paragraph(answer, S["cellb"]),
            Paragraph("—" if r["seconds"] is None else f"{r['seconds']:g}", S["cell"]),
        ])
    table = Table(data, colWidths=[8 * mm, 95 * mm, 45 * mm, 12 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE),
        ("LINEBELOW", (0, 1), (-1, -2), 0.25, colors.HexColor("#EDEDE8")),
        ("BACKGROUND", (0, 0), (-1, 0), PAPER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def build_answers_pdf(*, sessions: list, user: dict, items_for) -> bytes:
    records = [answer_records(s, items_for) for s in sessions]
    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm, topMargin=22 * mm, bottomMargin=20 * mm,
        title=f"Your answers — {user['name']}", author="Rather Know", subject="Your answers",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    stamped = datetime.now().strftime("%d %B %Y")

    def decorate(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(INK)
        canvas.setFont("Times-Roman", 10)
        canvas.drawString(20 * mm, A4[1] - 14 * mm, "Rather Know.")
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(A4[0] - 20 * mm, A4[1] - 14 * mm, f"Your answers · {stamped}")
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, A4[1] - 17 * mm, A4[0] - 20 * mm, A4[1] - 17 * mm)
        canvas.line(20 * mm, 15 * mm, A4[0] - 20 * mm, 15 * mm)
        canvas.setFont("Helvetica", 6.5)
        canvas.drawString(20 * mm, 11 * mm, LOCKED["disclaimer"])
        canvas.drawRightString(A4[0] - 20 * mm, 11 * mm, f"Page {_doc.page}")
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=decorate)])

    total = sum(r["answered"] for r in records)
    flow = [
        Paragraph(f"PREPARED FOR {user['name'].upper()} · {stamped}", S["kicker"]),
        Paragraph("Your answers.", S["h1"]),
        Paragraph(f"{total} answers across {len(records)} completed "
                  f"{'sitting' if len(records) == 1 else 'sittings'}, exactly as given.", S["lead"]),
        Paragraph(
            "This is the raw record, not a reading: every item as it was put to you, the answer "
            "you gave, and the seconds you spent on it. Nothing here is scored, weighted, "
            "reversed or interpreted — the reverse-keyed items appear as you answered them, not as "
            "the scorer reads them. The order is the order you saw, and on the Everyday Mirror "
            "which option sat on the left was randomised for you, so it is reproduced as you had "
            "it.", S["body"]),
        Paragraph(
            "It is rebuilt from your stored answers each time you download it, so unlike a report "
            "it carries no display or scoring version: there is nothing in it that a later change "
            "could alter.", S["small"]),
        Spacer(1, 4 * mm),
    ]

    for record in records:
        flow += [
            Paragraph(record["instrument_name"], S["h2"]),
            Paragraph(
                f"{record['answered']} of {record['items']} items · completed "
                f"{_when(record['completed_at'])}"
                + (f" · about {record['minutes_on_items']:g} minutes on the items"
                   if record["minutes_on_items"] else "")
                + f" · session {record['session_id'][:8]}", S["small"]),
        ]
        if record["scale"]:
            flow += [Paragraph("Scale: " + " · ".join(
                f"{i + 1} {label}" for i, label in enumerate(record["scale"])), S["small"])]
        groups: dict = {}
        for row in record["answers"]:
            groups.setdefault(row["group"], []).append(row)
        for title, rows in groups.items():
            if title:
                flow += [Paragraph(title, S["h3"])]
            flow += [_table(rows), Spacer(1, 3 * mm)]

    doc.build(flow)
    return buf.getvalue()

"""Render page one of a real report into a PNG for the landing page hero.

The landing page currently ships zero images, so a visitor never sees the thing they would be
getting. People buy reports by looking at reports. This renders an actual report through the
shipped PDF builder — not a mockup — so the picture cannot drift from the product.

    python scripts/build_hero_report_image.py
"""
import io
import os
import random
import sys

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)
os.environ.setdefault("RK_ALLOW_PLACEHOLDER_ALPHA", "1")

import fitz  # PyMuPDF

from report_pdf import build_report_pdf
from services.essential_scoring import (
    QuizAnswer, calculate_archetype_scores, calculate_dimension_scores, get_compatibility_result,
    ARCHETYPES,
)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "frontend", "public", "images", "sample-report-page.png")


def _lens(seed: int, quiz_type: str) -> dict:
    rng = random.Random(seed)
    answers = [QuizAnswer(question_id=q, answer=rng.choice([2, 3, 4, 4, 5])) for q in range(1, 51)]
    scores = calculate_archetype_scores(answers)
    ordered = sorted(scores.items(), key=lambda kv: kv[1]["score"], reverse=True)
    return {
        "primary": ordered[0][0], "secondary": ordered[1][0], "archetype_scores": scores,
        "compatibility": get_compatibility_result(scores, quiz_type),
        "dimensions": calculate_dimension_scores(answers),
    }


def sample_result() -> dict:
    self_r, ideal_r = _lens(7, "self_assessment"), _lens(29, "ideal_partner")
    delta = {k: round(ideal_r["archetype_scores"][k]["percentage"]
                      - self_r["archetype_scores"][k]["percentage"], 1) for k in ARCHETYPES}
    primary = ARCHETYPES[self_r["primary"]]
    shadow_key = primary.get("shadow")

    def brief(lens, key, field):
        a = ARCHETYPES[key]
        return {"key": key, "name": a["name"], "subtitle": a["subtitle"], "description": a.get(field, "")}

    return {
        "instrument": "essential",
        "self": {"primary": brief("self", self_r["primary"], "self_description"),
                 "secondary": brief("self", self_r["secondary"], "self_description"),
                 "archetype_scores": self_r["archetype_scores"],
                 "compatibility": self_r["compatibility"], "dimensions": self_r["dimensions"]},
        "ideal": {"primary": brief("ideal", ideal_r["primary"], "ideal_partner_description"),
                  "secondary": brief("ideal", ideal_r["secondary"], "ideal_partner_description"),
                  "archetype_scores": ideal_r["archetype_scores"],
                  "compatibility": ideal_r["compatibility"], "dimensions": ideal_r["dimensions"]},
        "delta": {"per_archetype": delta,
                  "overall": round(sum(abs(v) for v in delta.values()) / len(delta), 1),
                  "biggest": max(delta, key=lambda k: abs(delta[k]))},
        "shadow": ({"key": shadow_key, "name": ARCHETYPES[shadow_key]["name"],
                    "gift": ARCHETYPES[shadow_key]["subtitle"],
                    "warning": primary.get("shadow_warning", "")} if shadow_key else None),
        "dimension_gaps": {d: ideal_r["dimensions"][d] - self_r["dimensions"][d]
                           for d in self_r["dimensions"]},
        "evidence_tier": "developmental",
        "algo_version": "rk-1.0.0",
        "completed_at": "2026-06-01T10:00:00+00:00",
    }


def main() -> None:
    pdf = build_report_pdf(result=sample_result(),
                           user={"name": "Sample Reader", "situation": "single"})
    doc = fitz.open(stream=io.BytesIO(pdf), filetype="pdf")
    pix = doc[0].get_pixmap(dpi=150)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pix.save(OUT)
    print(f"{OUT} — {pix.width}x{pix.height}, {os.path.getsize(OUT)} bytes, {doc.page_count} pages in source")


if __name__ == "__main__":
    main()

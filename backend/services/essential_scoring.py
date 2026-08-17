"""Standalone Essential Mirror scoring for the Rather Know backend.

Extracted from mymirrorreport routes/dating_wellness.py (data frozen in
constants/essential_data.json via _export_data.py). Logic is a verbatim port:
6 archetypes scored over 50 items per lens, 5 display dimensions, and the
compatibility read keyed on the primary+secondary pair.
"""
import json
import os
from typing import Dict, List

from pydantic import BaseModel

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "constants", "essential_data.json")
with open(_DATA_PATH, encoding="utf-8") as _fh:
    _D = json.load(_fh)

SELF_ASSESSMENT_QUESTIONS = _D["self_assessment_questions"]
IDEAL_PARTNER_QUESTIONS = _D["ideal_partner_questions"]
ARCHETYPES = _D["archetypes"]
_COMPATIBILITY = _D["compatibility_matrix"]  # keyed "keyA|keyB" (sorted)


class QuizAnswer(BaseModel):
    question_id: int
    answer: int


def calculate_score(answer: int, reverse: bool = False) -> int:
    if reverse:
        answer = 6 - answer
    score_map = {5: 10, 4: 7, 3: 5, 2: 2, 1: 0}
    return score_map.get(answer, 0)


def calculate_archetype_scores(answers: List[QuizAnswer]) -> Dict[str, dict]:
    answer_dict = {a.question_id: a.answer for a in answers}
    results = {}
    for key, archetype in ARCHETYPES.items():
        total = 0
        for q_id in archetype["questions"]:
            if q_id in answer_dict:
                reverse = q_id in archetype["reverse"]
                total += calculate_score(answer_dict[q_id], reverse)
        max_score = len(archetype["questions"]) * 10
        percentage = (total / max_score) * 100 if max_score > 0 else 0
        results[key] = {
            "name": archetype["name"],
            "subtitle": archetype["subtitle"],
            "score": total,
            "max_score": max_score,
            "percentage": round(percentage, 1),
        }
    return results


def calculate_dimension_scores(answers: List[QuizAnswer]) -> Dict[str, int]:
    answer_dict = {a.question_id: a.answer for a in answers}
    dimensions = {
        "Values": list(range(1, 11)),
        "Lifestyle": list(range(11, 21)),
        "Conflict": list(range(21, 31)),
        "Intellectual": list(range(31, 41)),
        "Emotional": list(range(41, 51)),
    }
    results = {}
    for dim_name, q_ids in dimensions.items():
        total = sum(answer_dict.get(q_id, 3) for q_id in q_ids)
        max_score = len(q_ids) * 5
        results[dim_name] = round((total / max_score) * 100)
    return results


def get_compatibility_result(archetype_scores: Dict[str, dict], quiz_type: str) -> dict:
    sorted_archetypes = sorted(archetype_scores.items(), key=lambda x: x[1]["score"], reverse=True)
    primary = sorted_archetypes[0][0]
    secondary = sorted_archetypes[1][0]

    key = "|".join(sorted([primary, secondary]))
    if key in _COMPATIBILITY:
        compat = _COMPATIBILITY[key]
        narrative_key = "self_narrative" if quiz_type == "self_assessment" else "ideal_partner_narrative"
        return {
            "type_name": compat["type_name"],
            "description": compat["description"],
            "narrative": compat.get(narrative_key, compat["description"]),
        }

    primary_arch = ARCHETYPES[primary]
    desc_key = "self_description" if quiz_type == "self_assessment" else "ideal_partner_description"
    return {
        "type_name": f"The {primary_arch['name'].replace('The ', '')}",
        "description": primary_arch[desc_key],
        "narrative": primary_arch[desc_key],
    }

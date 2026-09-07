"""Standalone Essential Mirror scoring for the Rather Know backend.

Extracted from mymirrorreport routes/dating_wellness.py (data frozen in
constants/essential_data.json via _export_data.py). Logic is a verbatim port:
6 archetypes scored over 50 items per lens, 5 display dimensions, and the
blend read keyed on the primary+secondary pair.

Naming (work order A4): the pair read is a *blend* of two archetypes within one person. It was
called "compatibility" in the ported code, which in a single-player instrument names something
that does not exist here and never will. The data key, the function and the API field are all
"blend" now; the API keeps emitting "compatibility" alongside it so nothing already delivered or
already reading a result changes.
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
_BLEND = _D["blend_matrix"]  # keyed "keyA|keyB" (sorted)


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


TIE_MARGIN = 5
"""Points within which the top two archetypes are not ranked, only named together.

A provisional design choice, like the 1.5-sten loudest-trait floor — not a derived figure, and
to be re-derived when the item-bank alphas are measured. It is not the conservative option:
archetype scores have an SD of 11-13 points, so at the placeholder alpha the standard error of a
difference between two of them is around 8 points and a 90% interval on that is around 13. Five
is already generous to the instrument; three would have been chosen to hold the fire rate down,
which optimises for the archetype's prominence rather than for what the instrument can tell
apart. It fires on roughly 39% of varied stored responses. That costs less than it would have
before the Delta became the headline finding.

Below the margin the previous code broke ties by whatever `sorted(..., reverse=True)` returned
first, which for equal scores is dictionary insertion order — a 15% share of readers assigned an
archetype by the order the six were typed into a JSON file.
"""


def rank_archetypes(archetype_scores: Dict[str, dict]) -> dict:
    """Deterministic ordering plus the tie state. Ties break on key, never on insertion order."""
    ordered = sorted(archetype_scores.items(), key=lambda kv: (-kv[1]["score"], kv[0]))
    gap = ordered[0][1]["score"] - ordered[1][1]["score"]
    return {
        "order": [k for k, _ in ordered],
        "primary": ordered[0][0],
        "secondary": ordered[1][0],
        "gap": gap,
        "tied": gap < TIE_MARGIN,
        "margin": TIE_MARGIN,
    }


def get_blend_result(archetype_scores: Dict[str, dict], quiz_type: str) -> dict:
    ranked = rank_archetypes(archetype_scores)
    primary = ranked["primary"]
    secondary = ranked["secondary"]

    key = "|".join(sorted([primary, secondary]))
    if key in _BLEND:
        compat = _BLEND[key]
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


def assert_reverse_keys_within_questions(archetypes: dict = ARCHETYPES) -> None:
    """Import-time guard (work order A4): a reverse key outside its own item set is inert.

    `calculate_archetype_scores` only ever consults `reverse` for ids it is already iterating
    from `questions`, so an id listed in one and absent from the other reverses nothing and
    nothing reports it.

    Diplomat used to carry reverse=[24] while 24 sat in Challenger's item set. Decided and closed:
    the key is dropped, not restored. Restoring 24 would have changed scoring for new readers
    while delivered results stayed frozen — two populations under one version, worse than the
    defect — and 24 is forward-scored in Challenger where it reads correctly, so moving it would
    have changed two archetypes rather than one. Dropping it changes no score at all, which
    tests/test_workorder_a.py proves. The finding is recorded in docs/ARCHETYPES_SPEC.md.

    KNOWN_ORPHANS is empty and stays empty. Any orphan now fails at load.
    """
    KNOWN_ORPHANS: set = set()
    orphans = {(key, qid)
               for key, arch in archetypes.items()
               for qid in arch.get("reverse", [])
               if qid not in arch["questions"]}
    unexpected = orphans - KNOWN_ORPHANS
    if unexpected:
        raise AssertionError(
            "Archetype reverse keys outside their own item set — the reversal is inert: "
            f"{sorted(unexpected)}"
        )


assert_reverse_keys_within_questions()

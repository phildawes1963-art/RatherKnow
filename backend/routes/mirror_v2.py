"""Mirror v2 — the remodel. Anonymous, free, sessionised instruments.

Four instruments: essential (50×2 archetype), personality (P150 Likert core),
eq (EI Mirror 140), closeness (new MI-AS-36). No account required; the client
holds its session ids. Collection: mirror_v2_sessions.
"""
import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database import db

from services.essential_scoring import (
    SELF_ASSESSMENT_QUESTIONS, IDEAL_PARTNER_QUESTIONS, ARCHETYPES,
    QuizAnswer, calculate_archetype_scores, calculate_dimension_scores,
    get_compatibility_result,
)
from constants.p150_data import P150_PERSONALITY_ITEMS, P150_VALIDITY_ITEMS
from constants.eimirror_data import (
    EIMIRROR_QUESTIONS, EIMIRROR_DOMAINS, EIMIRROR_REVERSE_ITEMS, EIMIRROR_SCALE,
)
from services.closeness_scoring import load_bank, score_closeness

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2", tags=["Mirror v2"])

# Hard rule 1/2: scoring is frozen and every stored result is stamped and never recomputed.
ALGO_VERSION = "rk-1.0.0"

SCALE_5 = ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"]

INSTRUMENTS = {
    "essential": {
        "name": "Essential Mirror",
        "tagline": "Who you are — and who you say you want",
        "total_items": 100,
        "minutes": "About 25 minutes",
        "evidence_tier": "Developmental",
        "scale": SCALE_5,
        "allow_skip": False,
    },
    "personality": {
        "name": "Personality Mirror",
        "tagline": "A validated five-factor profile",
        "total_items": 130,
        "minutes": "15–20 minutes",
        "evidence_tier": "Established",
        "scale": SCALE_5,
        "allow_skip": False,
    },
    "eq": {
        "name": "EI Mirror",
        "tagline": "Goleman four-domain emotional intelligence read",
        "total_items": 140,
        "minutes": "15–20 minutes",
        "evidence_tier": "Established",
        "scale": SCALE_5,
        "allow_skip": False,
    },
    "closeness": {
        "name": "Closeness Mirror",
        "tagline": "How you are when you're close to someone",
        "total_items": 37,
        "minutes": "About 5 minutes",
        "evidence_tier": "Developmental",
        "scale": None,  # from bank
        "allow_skip": True,
    },
}


def _build_items(instrument: str):
    if instrument == "closeness":
        bank = load_bank()
        by_id = {it["id"]: it for it in bank["items"]}
        val = {v["id"]: v for v in bank["validity"]}
        items = []
        for iid in bank["order"]:
            if iid in val:
                items.append({"id": str(iid), "text": val[iid]["text"]})
            else:
                items.append({"id": str(iid), "text": by_id[iid]["text"]})
        return items, bank["scale"], bank["instructions"], None
    if instrument == "essential":
        items = [{"id": f"self:{q['id']}", "text": q["text"]} for q in SELF_ASSESSMENT_QUESTIONS]
        items += [{"id": f"ideal:{q['id']}", "text": q["text"]} for q in IDEAL_PARTNER_QUESTIONS]
        interstitial = {
            "after_index": len(SELF_ASSESSMENT_QUESTIONS) - 1,
            "title": "Now, the second lens.",
            "text": "You've just answered as yourself. Now answer the same kind of questions as the partner you think you want. Don't overthink it — the gap between the two sets of answers is the measurement.",
        }
        instructions = {
            "title": "Answered twice: once as you, once as who you want",
            "paragraphs": [
                "The first fifty statements are about who you are in relationships. The second fifty are about the partner you're looking for.",
                "The gap between those two sets of answers — the Delta — is what this instrument measures. Answer honestly, not aspirationally; the honest version is the useful one.",
                "There are no right answers, and nothing here is a diagnosis.",
            ],
        }
        return items, SCALE_5, instructions, interstitial
    if instrument == "personality":
        items = []
        vi = list(P150_VALIDITY_ITEMS)
        for i, q in enumerate(P150_PERSONALITY_ITEMS):
            items.append({"id": str(q["id"]), "text": q["text"]})
            if (i + 1) % 12 == 0 and vi:
                v = vi.pop(0)
                items.append({"id": str(v["id"]), "text": v["text"]})
        instructions = {
            "title": "Your five-factor profile",
            "paragraphs": [
                "One hundred and thirty statements about how you tend to think, feel and act. Answer as you generally are, not as you'd like to be.",
                "This is a validated five-factor personality measure. Your result maps sixteen primary factors and five global dimensions.",
                "There are no right answers. Go at whatever pace suits you — nothing is timed.",
            ],
        }
        return items, SCALE_5, instructions, None
    if instrument == "eq":
        items = [{"id": str(q["id"]), "text": q["text"]} for q in EIMIRROR_QUESTIONS]
        instructions = {
            "title": "How you handle what you feel",
            "paragraphs": [
                "One hundred and forty statements across four domains: self-awareness, self-management, social awareness and relationship management.",
                "Answer for how you actually are, day to day — not your best day, and not your worst.",
                "There are no right answers, and nothing is timed.",
            ],
        }
        return items, EIMIRROR_SCALE, instructions, None
    raise HTTPException(status_code=404, detail="Unknown instrument")


def _session_payload(session: dict) -> dict:
    items, scale, instructions, interstitial = _build_items(session["instrument"])
    meta = INSTRUMENTS[session["instrument"]]
    return {
        "session_id": session["id"],
        "instrument": session["instrument"],
        "name": meta["name"],
        "status": session["status"],
        "evidence_tier": meta["evidence_tier"],
        "allow_skip": meta["allow_skip"],
        "minutes": meta["minutes"],
        "items": items,
        "scale": scale,
        "instructions": instructions,
        "interstitial": interstitial,
        "responses": {k: v["v"] for k, v in session.get("responses", {}).items()},
    }


class StartRequest(BaseModel):
    instrument: str


class ResponseItem(BaseModel):
    item_id: str
    value: int
    ms: Optional[int] = None
    rev: Optional[int] = 0


class ResponsesPut(BaseModel):
    responses: List[ResponseItem]


class SummaryRequest(BaseModel):
    session_ids: List[str]


@router.get("/instruments")
async def list_instruments():
    out = []
    for key, meta in INSTRUMENTS.items():
        out.append({
            "key": key, "name": meta["name"], "tagline": meta["tagline"],
            "total_items": meta["total_items"], "minutes": meta["minutes"],
            "evidence_tier": meta["evidence_tier"],
        })
    return {"instruments": out}


@router.post("/assessments")
async def start_assessment(data: StartRequest):
    if data.instrument not in INSTRUMENTS:
        raise HTTPException(status_code=404, detail="Unknown instrument")
    session = {
        "id": str(uuid.uuid4()),
        "instrument": data.instrument,
        "status": "in_progress",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "responses": {},
    }
    if data.instrument == "closeness":
        session["bank_version"] = load_bank()["bank_version"]
    await db.mirror_v2_sessions.insert_one(dict(session))
    return _session_payload(session)


@router.get("/assessments/{session_id}")
async def get_assessment(session_id: str):
    session = await db.mirror_v2_sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_payload(session)


@router.put("/assessments/{session_id}/responses")
async def put_responses(session_id: str, data: ResponsesPut):
    session = await db.mirror_v2_sessions.find_one({"id": session_id}, {"_id": 0, "id": 1, "instrument": 1, "status": 1})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] == "complete":
        raise HTTPException(status_code=409, detail="Session already complete")
    meta = INSTRUMENTS[session["instrument"]]
    n_points = 7 if session["instrument"] == "closeness" else len(meta["scale"])
    updates = {}
    for r in data.responses:
        if not (1 <= r.value <= n_points):
            raise HTTPException(status_code=400, detail=f"Value out of range for {r.item_id}")
        updates[f"responses.{r.item_id}"] = {"v": r.value, "ms": r.ms, "rev": r.rev or 0}
    if updates:
        await db.mirror_v2_sessions.update_one({"id": session_id}, {"$set": updates})
    return {"saved": len(updates)}


def _score_essential(responses: dict) -> dict:
    lens_results = {}
    for lens, quiz_type in (("self", "self_assessment"), ("ideal", "ideal_partner")):
        answers = []
        for qid in range(1, 51):
            r = responses.get(f"{lens}:{qid}")
            if r is None:
                raise HTTPException(status_code=400, detail=f"Missing answers in the '{lens}' lens")
            answers.append(QuizAnswer(question_id=qid, answer=r["v"]))
        arch_scores = calculate_archetype_scores(answers)
        ordered = sorted(arch_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        lens_results[lens] = {
            "archetype_scores": arch_scores,
            "primary": ordered[0][0],
            "secondary": ordered[1][0],
            "compatibility": get_compatibility_result(arch_scores, quiz_type),
            "dimensions": calculate_dimension_scores(answers),
        }
    self_r, ideal_r = lens_results["self"], lens_results["ideal"]
    delta = {}
    for key in ARCHETYPES:
        d = round(ideal_r["archetype_scores"][key]["percentage"] - self_r["archetype_scores"][key]["percentage"], 1)
        delta[key] = d
    overall_delta = round(sum(abs(v) for v in delta.values()) / len(delta), 1)
    biggest_key = max(delta, key=lambda k: abs(delta[k]))
    primary_arch = ARCHETYPES[self_r["primary"]]
    shadow_key = primary_arch.get("shadow")
    shadow = None
    if shadow_key and shadow_key in ARCHETYPES:
        shadow = {
            "key": shadow_key,
            "name": ARCHETYPES[shadow_key]["name"],
            "gift": ARCHETYPES[shadow_key]["subtitle"],
            "warning": primary_arch.get("shadow_warning", ""),
        }
    dim_gaps = {
        dim: ideal_r["dimensions"][dim] - self_r["dimensions"][dim]
        for dim in self_r["dimensions"]
    }
    return {
        "instrument": "essential",
        "self": {
            "primary": {"key": self_r["primary"], **_arch_brief(self_r["primary"], "self_description")},
            "secondary": {"key": self_r["secondary"], **_arch_brief(self_r["secondary"], "self_description", desc=False)},
            "archetype_scores": self_r["archetype_scores"],
            "compatibility": self_r["compatibility"],
            "dimensions": self_r["dimensions"],
        },
        "ideal": {
            "primary": {"key": ideal_r["primary"], **_arch_brief(ideal_r["primary"], "ideal_partner_description")},
            "secondary": {"key": ideal_r["secondary"], **_arch_brief(ideal_r["secondary"], "ideal_partner_description", desc=False)},
            "archetype_scores": ideal_r["archetype_scores"],
            "compatibility": ideal_r["compatibility"],
            "dimensions": ideal_r["dimensions"],
        },
        "delta": {"per_archetype": delta, "overall": overall_delta, "biggest": biggest_key},
        "shadow": shadow,
        "dimension_gaps": dim_gaps,
        "evidence_tier": "developmental",
    }


def _arch_brief(key: str, desc_field: str, desc: bool = True) -> dict:
    a = ARCHETYPES[key]
    out = {"name": a["name"], "subtitle": a["subtitle"]}
    if desc:
        out["description"] = a.get(desc_field, "")
    return out


async def _score_personality(responses: dict) -> dict:
    from services.p150_lite import score_p150_lite
    answer_map = {k: v["v"] for k, v in responses.items()}
    if len(answer_map) < 130:
        raise HTTPException(status_code=400, detail="Incomplete assessment")
    scored = score_p150_lite(answer_map)
    return {
        "instrument": "personality",
        "factor_scores": scored["factor_scores"],
        "global_scores": scored["global_scores"],
        "validity": scored["validity"],
        "strengths": scored["strengths"],
        "blind_spots": scored["blind_spots"],
        "evidence_tier": "established",
    }


def _score_eq(responses: dict) -> dict:
    answer_map = {int(k): v["v"] for k, v in responses.items()}
    if len(answer_map) < 140:
        raise HTTPException(status_code=400, detail="Incomplete assessment")
    domain_scores, sub_scores = {}, {}
    for domain_key, domain_data in EIMIRROR_DOMAINS.items():
        domain_total, domain_count = 0, 0
        for sub_key, sub_data in domain_data["sub_dimensions"].items():
            sub_total = 0
            for item_id in sub_data["items"]:
                raw = answer_map.get(item_id, 3)
                if item_id in EIMIRROR_REVERSE_ITEMS:
                    raw = 6 - raw
                sub_total += raw
            sub_avg = round(sub_total / len(sub_data["items"]), 2)
            band = "High" if sub_avg >= 4.0 else "Moderate" if sub_avg >= 3.0 else "Developing"
            sub_scores[sub_key] = {"name": sub_data["name"], "domain": domain_key, "score": sub_avg, "band": band}
            domain_total += sub_total
            domain_count += len(sub_data["items"])
        domain_avg = round(domain_total / domain_count, 2)
        domain_band = "High" if domain_avg >= 4.0 else "Moderate" if domain_avg >= 3.0 else "Developing"
        domain_scores[domain_key] = {"name": domain_data["name"], "score": domain_avg, "band": domain_band,
                                     "description": domain_data["description"]}
    overall = round(sum(d["score"] for d in domain_scores.values()) / len(domain_scores), 2)
    overall_band = "High" if overall >= 4.0 else "Moderate" if overall >= 3.0 else "Developing"
    ordered = sorted(sub_scores.values(), key=lambda x: x["score"], reverse=True)
    return {
        "instrument": "eq",
        "domain_scores": domain_scores,
        "sub_scores": sub_scores,
        "overall_score": overall,
        "overall_band": overall_band,
        "strengths": ordered[:3],
        "growth_areas": ordered[-3:][::-1],
        "evidence_tier": "established",
    }


@router.post("/assessments/{session_id}/complete")
async def complete_assessment(session_id: str):
    session = await db.mirror_v2_sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] == "complete" and session.get("result"):
        return session["result"]
    responses = session.get("responses", {})
    instrument = session["instrument"]
    if instrument == "closeness":
        result = score_closeness(responses)
    elif instrument == "essential":
        result = _score_essential(responses)
    elif instrument == "personality":
        result = await _score_personality(responses)
    elif instrument == "eq":
        result = _score_eq(responses)
    else:
        raise HTTPException(status_code=400, detail="Unknown instrument")
    result["session_id"] = session_id
    result["algo_version"] = ALGO_VERSION
    result["completed_at"] = datetime.now(timezone.utc).isoformat()
    await db.mirror_v2_sessions.update_one(
        {"id": session_id},
        {"$set": {"status": "complete", "completed_at": result["completed_at"], "result": result}},
    )
    # Immutable snapshot: written once, never recomputed when norms change.
    await db.results.update_one(
        {"session_id": session_id},
        {"$setOnInsert": {"session_id": session_id, "instrument": instrument,
                          "algo_version": ALGO_VERSION, "result": result}},
        upsert=True,
    )
    return result


@router.get("/assessments/{session_id}/result")
async def get_result(session_id: str):
    session = await db.mirror_v2_sessions.find_one({"id": session_id}, {"_id": 0, "result": 1, "status": 1})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] != "complete" or not session.get("result"):
        raise HTTPException(status_code=409, detail="Session not complete")
    return session["result"]


def _headline(session: dict) -> str:
    result = session.get("result") or {}
    inst = session["instrument"]
    if session["status"] != "complete":
        n = len(session.get("responses", {}))
        return f"In progress — {n} of {INSTRUMENTS[inst]['total_items']} answered"
    if inst == "closeness":
        dims = result.get("dimensions", {})
        anx = dims.get("anxiety", {}).get("value")
        avo = dims.get("avoidance", {}).get("value")
        anx_s = f"{anx}" if anx is not None else "not scored"
        avo_s = f"{avo}" if avo is not None else "not scored"
        return f"Reassurance {anx_s} · Closeness {avo_s}"
    if inst == "essential":
        return (f"You: {result['self']['primary']['name']} · "
                f"You want: {result['ideal']['primary']['name']} · Delta {result['delta']['overall']}")
    if inst == "personality":
        s = result.get("strengths", [])
        return f"16 factors scored · {len(s)} marked strengths" if s else "16 factors scored"
    if inst == "eq":
        return f"Overall {result['overall_score']} — {result['overall_band']}"
    return ""


@router.post("/mirrors/summary")
async def mirrors_summary(data: SummaryRequest):
    ids = data.session_ids[:10]
    out = []
    if ids:
        cursor = db.mirror_v2_sessions.find({"id": {"$in": ids}}, {"_id": 0, "answers": 0})
        async for session in cursor:
            out.append({
                "session_id": session["id"],
                "instrument": session["instrument"],
                "name": INSTRUMENTS[session["instrument"]]["name"],
                "status": session["status"],
                "completed_at": session.get("completed_at"),
                "headline": _headline(session),
            })
    return {"sessions": out}


# ==================== FLAG CHECK (reflection, not a measure) ====================
# FR-N2: every item is self-referential. FR-N4: deliberately unscored — the
# rules below select wording, they never produce a number shown to anyone.
# Stored in mirror_v2_reflections, never mirror_v2_sessions (TRD §4).

FLAG_OPTIONS = [
    "I noticed early, and it changed how I read things",
    "I noticed early — and found a reason it was fine",
    "I only saw it afterwards, looking back",
    "It hasn't come up, or I honestly can't recall",
]
FLAG_CATEGORY = {1: "reprice", 2: "explain", 3: "late", 4: "none"}

FLAG_ITEMS = [
    {"id": "f1", "text": "The warmth or attention changed sharply — much more than the situation explained, or much less once you were secured."},
    {"id": "f2", "text": "You said no to something small, and it didn't quite stand — it got revisited, reframed, or renegotiated."},
    {"id": "f3", "text": "Over a stretch of weeks, you were clearly the one doing most of the reaching, planning or repairing."},
    {"id": "f4", "text": "You asked for something you needed, and came away feeling you'd done something wrong."},
    {"id": "f5", "text": "Feedback arrived dressed as care — and you left those conversations smaller, not clearer."},
    {"id": "f6", "text": "Time with your own friends or family somehow became harder to arrange, or more expensive to pay for afterwards."},
    {"id": "f7", "text": "A silence or withdrawal arrived without explanation, and you found yourself working to end it."},
    {"id": "f8", "text": "You noticed yourself editing the story of the relationship when telling friends — leaving out the parts that would worry them."},
]
FLAG_SAFETY_ITEM = {
    "id": "f-safety",
    "text": "One more, and it's different in kind. As you answered these, was any part of you thinking about someone you're currently afraid of?",
    "options": ["No", "I'm not sure", "Yes"],
}


def _flag_payload(doc: dict) -> dict:
    return {
        "reflection_id": doc["id"],
        "status": doc["status"],
        "items": FLAG_ITEMS,
        "options": FLAG_OPTIONS,
        "safety_item": FLAG_SAFETY_ITEM,
        "responses": {k: v["v"] for k, v in doc.get("responses", {}).items()},
        "result": doc.get("result"),
    }


@router.post("/reflections")
async def start_reflection():
    doc = {
        "id": str(uuid.uuid4()),
        "kind": "flag_check",
        "status": "in_progress",
        "entrance": "flag_check",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "responses": {},
    }
    await db.mirror_v2_reflections.insert_one(dict(doc))
    return _flag_payload(doc)


@router.get("/reflections/{reflection_id}")
async def get_reflection(reflection_id: str):
    doc = await db.mirror_v2_reflections.find_one({"id": reflection_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Reflection not found")
    return _flag_payload(doc)


@router.put("/reflections/{reflection_id}/responses")
async def put_reflection_responses(reflection_id: str, data: ResponsesPut):
    doc = await db.mirror_v2_reflections.find_one({"id": reflection_id}, {"_id": 0, "id": 1, "status": 1})
    if not doc:
        raise HTTPException(status_code=404, detail="Reflection not found")
    if doc["status"] == "complete":
        raise HTTPException(status_code=409, detail="Reflection already complete")
    valid_ids = {it["id"] for it in FLAG_ITEMS} | {FLAG_SAFETY_ITEM["id"]}
    updates = {}
    for r in data.responses:
        if r.item_id not in valid_ids:
            raise HTTPException(status_code=400, detail=f"Unknown item {r.item_id}")
        limit = 3 if r.item_id == "f-safety" else 4
        if not (1 <= r.value <= limit):
            raise HTTPException(status_code=400, detail=f"Value out of range for {r.item_id}")
        updates[f"responses.{r.item_id}"] = {"v": r.value}
    if updates:
        await db.mirror_v2_reflections.update_one({"id": reflection_id}, {"$set": updates})
    return {"saved": len(updates)}


@router.post("/reflections/{reflection_id}/complete")
async def complete_reflection(reflection_id: str):
    doc = await db.mirror_v2_reflections.find_one({"id": reflection_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Reflection not found")
    if doc["status"] == "complete" and doc.get("result"):
        return doc["result"]
    responses = doc.get("responses", {})
    counts = {"reprice": 0, "explain": 0, "late": 0, "none": 0}
    for item in FLAG_ITEMS:
        r = responses.get(item["id"])
        if r:
            counts[FLAG_CATEGORY[r["v"]]] += 1
    informative = counts["reprice"] + counts["explain"] + counts["late"]
    if informative < 3:
        pattern, pattern_pair = "insufficient", None
    else:
        ordered = sorted(
            [(k, v) for k, v in counts.items() if k != "none"],
            key=lambda x: x[1], reverse=True,
        )
        if ordered[0][1] == ordered[1][1]:
            pattern, pattern_pair = "mixed", [ordered[0][0], ordered[1][0]]
        else:
            pattern, pattern_pair = ordered[0][0], None
    safety_r = responses.get("f-safety")
    safety = {1: "no", 2: "unsure", 3: "yes"}.get(safety_r["v"] if safety_r else 1, "no")
    result = {
        "kind": "flag_check",
        "pattern": pattern,
        "pattern_pair": pattern_pair,
        "safety": safety,
        "answered": informative,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.mirror_v2_reflections.update_one(
        {"id": reflection_id},
        {"$set": {"status": "complete", "result": result}},
    )
    return result


# ==================== CROSS-CHECK FINDINGS ====================
# Rule-based tensions between completed instruments. Each rule fires only when
# its arithmetic condition holds. No verdicts, no invented numbers.

def _build_findings(by_instrument: dict) -> list:
    findings = []
    clo = by_instrument.get("closeness")
    pers = by_instrument.get("personality")
    eq = by_instrument.get("eq")
    ess = by_instrument.get("essential")

    anx = clo["dimensions"]["anxiety"]["value"] if clo else None
    avo = clo["dimensions"]["avoidance"]["value"] if clo else None

    def sten(k):
        return pers["factor_scores"].get(k, {}).get("sten") if pers else None

    def dom(k):
        return eq["domain_scores"][k]["score"] if eq else None

    if anx is not None and sten("C") is not None and anx >= 5 and sten("C") >= 7:
        findings.append({
            "id": "calm-general-alarmed-close",
            "sources": ["Personality Mirror", "Closeness Mirror"],
            "title": "Calm in general. Alarmed up close.",
            "body": f"The Personality Mirror reads you as emotionally stable across life in general. The Closeness Mirror has reassurance-seeking running clearly above the middle in close relationships specifically ({anx} on a 1–7 scale). Both can be true at once — closeness runs on its own circuitry. Worth sitting with: which of those two versions of you did the choosing, last time it mattered?",
        })
    if anx is not None and sten("L") is not None and anx <= 3 and sten("L") >= 7:
        findings.append({
            "id": "vigilant-general-settled-close",
            "sources": ["Personality Mirror", "Closeness Mirror"],
            "title": "Your guard lives somewhere unexpected.",
            "body": f"The Personality Mirror has you running vigilant in general — slow to extend trust. The Closeness Mirror finds you settled in close relationships ({anx} on reassurance, below the middle). The two disagree about where your caution actually operates. Worth sitting with: is closeness where your vigilance switches off — and is that earned, or is it just where you stop checking?",
        })
    if avo is not None and dom("relationship_management") is not None and avo >= 5 and dom("relationship_management") >= 4.0:
        findings.append({
            "id": "skilled-at-distant-in",
            "sources": ["EI Mirror", "Closeness Mirror"],
            "title": "Skilled at relationships. Distant in them.",
            "body": f"The EI Mirror has you rating your relationship management as high. The Closeness Mirror finds closeness itself sitting further away than the middle ({avo} on a 1–7 scale). Managing relationships well and letting one all the way in are different capacities — and the first can quietly substitute for the second for years without anyone noticing, including you.",
        })
    if avo is not None and sten("A") is not None and avo >= 5 and sten("A") >= 7:
        findings.append({
            "id": "warm-general-guarded-close",
            "sources": ["Personality Mirror", "Closeness Mirror"],
            "title": "Warm in general. Guarded up close.",
            "body": f"The Personality Mirror reads you as genuinely warm — attentive to people, easy to be around. The Closeness Mirror has intimacy itself kept at more of a distance ({avo} on a 1–7 scale). Warmth given widely can be a comfortable place to stand while closeness stays unentered. Worth sitting with: who gets the warmth, and who gets let in — and are they ever the same person?",
        })
    if avo is not None and sten("Q2") is not None and avo >= 5 and sten("Q2") <= 4:
        findings.append({
            "id": "leans-on-people-not-partner",
            "sources": ["Personality Mirror", "Closeness Mirror"],
            "title": "You lean on people. Just not on a partner.",
            "body": "The Personality Mirror has you group-oriented — comfortable relying on others in general life. The Closeness Mirror finds leaning on a partner specifically coming much less easily. The disagreement is the finding: support isn't hard for you, partnership-shaped support is. Worth sitting with: what does a partner represent that a friend doesn't?",
        })
    if anx is not None and dom("self_management") is not None and anx >= 5 and dom("self_management") >= 4.0:
        findings.append({
            "id": "composed-everywhere-but-here",
            "sources": ["EI Mirror", "Closeness Mirror"],
            "title": "Composed everywhere but here.",
            "body": f"The EI Mirror has your self-management high — you regulate well, by your own read. The Closeness Mirror finds the alarm running well above the middle in close relationships ({anx} on a 1–7 scale). Regulation that works everywhere except intimacy isn't failing; it's telling you where the oldest wiring lives. Worth sitting with rather than fixing.",
        })
    if ess and ess["delta"]["overall"] >= 15:
        findings.append({
            "id": "two-lenses-disagree",
            "sources": ["Essential Mirror"],
            "title": "Your two lenses disagree with each other.",
            "body": f"Within a single instrument, who you are and who you say you want sit {ess['delta']['overall']} points apart on average — a wide Delta. That's not a fault to correct; it's the most informative thing the instrument found. Worth sitting with: is the gap describing something you want to grow toward, or something you want someone else to carry for you?",
        })
    if eq and pers and eq.get("overall_score") is not None and eq["overall_score"] >= 4.0:
        sd_flag = pers.get("validity", {}).get("social_desirability", {}).get("flag")
        if sd_flag == "HIGH":
            findings.append({
                "id": "flattering-light",
                "sources": ["EI Mirror", "Personality Mirror"],
                "title": "A flattering light.",
                "body": "Two self-report instruments both came back glowing — and the Personality Mirror's validity check noticed you agreed with an unusually high number of very flattering statements. Nothing wrong with a good day. Worth sitting with: would an ordinary-day retake say the same?",
            })
    return findings[:4]


@router.post("/mirrors/findings")
async def mirrors_findings(data: SummaryRequest):
    ids = data.session_ids[:10]
    by_instrument = {}
    if ids:
        cursor = db.mirror_v2_sessions.find(
            {"id": {"$in": ids}, "status": "complete"}, {"_id": 0, "instrument": 1, "result": 1}
        )
        async for session in cursor:
            if session.get("result"):
                by_instrument[session["instrument"]] = session["result"]
    return {
        "instruments_complete": sorted(by_instrument.keys()),
        "findings": _build_findings(by_instrument) if len(by_instrument) >= 2 else [],
    }

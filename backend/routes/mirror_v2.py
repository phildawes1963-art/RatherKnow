"""Mirror v2 — the remodel. Free, sessionised instruments.

Four instruments: essential (50×2 archetype), personality (P150 Likert core),
eq (EI Mirror 140), closeness (new MI-AS-36). Starting an instrument requires an
account (name, email, situation) so results are retrievable by logging in; the
Flag Check reflection stays open to everyone. Collection: mirror_v2_sessions.
"""
import uuid
import random
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from database import db
from fastapi.responses import Response
from auth import get_current_user, assert_session_owner
from services.ratelimit import limiter
from report_pdf import build_report_pdf, build_combined_pdf
from answers_export import answer_records, build_answers_pdf
from choosing import build_choosing
from composites import build_composites
from services.reportable import (
    EI_FLAT_COPY, FACET_SUPPRESSION_REASON, FACTOR_FLOOR_PP, ei_named,
)
from services.factor_pct import factor_pcts, loudest_entries

from services.within_person import build_position
from services.mrd import build_mrd, MODE as MRD_MODE, config as mrd_config, mrd_sd_units_for
from services.display import (
    DISPLAY_VERSION, NotNormReferenced, commonness, commonness_sentence,
)
from crosscheck import build_convergences, build_tensions, build_synthesis
from situation_notes import situation_note

from services.essential_scoring import (
    SELF_ASSESSMENT_QUESTIONS, IDEAL_PARTNER_QUESTIONS, ARCHETYPES,
    QuizAnswer, calculate_archetype_scores, calculate_dimension_scores,
    get_blend_result, rank_archetypes,
)
from constants.p150_data import P150_PERSONALITY_ITEMS, P150_VALIDITY_ITEMS
from services.p150_lite import NOT_FOR_DISPLAY, P150_FACTORS
from constants.eimirror_data import (
    EIMIRROR_QUESTIONS, EIMIRROR_DOMAINS, EIMIRROR_REVERSE_ITEMS, EIMIRROR_SCALE,
)
from services.closeness_scoring import load_bank, score_closeness
from services.everyday_scoring import load_bank as load_everyday_bank, score_everyday
from services.narrative import (
    resolved_narrative, snapshot_pdf, invalidate_combined, CONTENT_VERSION,
)

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
    "everyday": {
        "name": "Everyday Mirror",
        "tagline": "Where you sit, and what you'd protect",
        "total_items": 49,
        "minutes": "About 7 minutes",
        "evidence_tier": "Developmental",
        "scale": None,  # forced choice: two options per item, rendered per session
        "allow_skip": True,
    },
}


def _spread(groups: list) -> list:
    """Interleave items so same-trait questions never sit next to each other.

    groups is a list of lists (one per factor / sub-dimension / archetype). Round-robin,
    rotating the starting group each pass so no single trait ever leads twice in a row.
    Deterministic: the order is the same on resume, and item ids are unchanged, so scoring
    (which is keyed on id) is completely unaffected.
    """
    buckets = [list(g) for g in groups if g]
    out = []
    pass_no = 0
    while any(buckets):
        live = [b for b in buckets if b]
        offset = pass_no % len(live)
        for i in range(len(live)):
            out.append(live[(i + offset) % len(live)].pop(0))
        buckets = [b for b in buckets if b]
        pass_no += 1
    return out


def _everyday_side_map() -> dict:
    """Randomise which pole is rendered on the left, per item, per session.

    Required by the instrument, not cosmetic: the side-bias validity index counts how often the
    reader picked the left-hand option, which only means anything if the side is random. Stored
    on the session so scoring can map the answer back to a pole.
    """
    bank = load_everyday_bank()
    ids = [i["id"] for i in bank["block_a"]] + [i["id"] for i in bank["block_b"]]
    return {iid: random.choice(("AB", "BA")) for iid in ids}


def _build_items(instrument: str, session: dict | None = None):
    if instrument == "everyday":
        bank = load_everyday_bank()
        side_map = (session or {}).get("presentation", {}).get("side_map", {})
        domains = bank["domains"]

        def sides(item_id, a, b):
            return [b, a] if side_map.get(item_id) == "BA" else [a, b]

        by_domain: dict = {}
        for item in bank["block_a"]:
            by_domain.setdefault(item["domain"], []).append(item)
        items = []
        for item in _spread(list(by_domain.values())):
            items.append({
                "id": item["id"], "kind": "choice",
                "text": "Which would you actually choose?",
                "options": sides(item["id"], item["option_a"], item["option_b"]),
            })
        block_a_count = len(items)
        for item in bank["block_b"]:
            left, right = domains[item["left"]]["descriptor"], domains[item["right"]]["descriptor"]
            a, b = sides(item["id"], left, right)
            items.append({
                "id": item["id"], "kind": "choice",
                "text": f"Which would matter more to agree on — {a}, or {b}?",
                "options": [a, b],
            })
        interstitial = {
            "after_index": block_a_count - 1,
            "title": "Now the harder half.",
            "text": ("You've said where you sit. This part asks what you'd protect — because you won't "
                     "agree on everything, and the things you feel most strongly about aren't always the "
                     "ones you'd defend. Twenty-one either/ors, and there's no way to keep both."),
        }
        instructions = {
            "title": "Where you sit, and what you'd protect",
            "paragraphs": [
                "Forty-nine either/or choices about ordinary life. Neither answer is ever better, and you "
                "can't like both — that's the format doing its job.",
                "The first twenty-eight ask where you actually sit on the things couples divide over. The "
                "last twenty-one ask which of those you'd need to agree on, and which you could live with.",
                "This is the only instrument here that asks about choices rather than self-description, "
                "which makes it the only one that can disagree with how you describe yourself.",
            ],
        }
        return items, None, instructions, interstitial
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
        # Same spread order in both lenses, so lens two reads as a parallel of lens one.
        by_archetype: dict = {}
        for q in SELF_ASSESSMENT_QUESTIONS:
            by_archetype.setdefault(q.get("category") or q.get("archetype") or "x", []).append(q)
        order = [q["id"] for q in _spread(list(by_archetype.values()))]
        self_by_id = {q["id"]: q for q in SELF_ASSESSMENT_QUESTIONS}
        ideal_by_id = {q["id"]: q for q in IDEAL_PARTNER_QUESTIONS}
        items = [{"id": f"self:{qid}", "text": self_by_id[qid]["text"]} for qid in order if qid in self_by_id]
        items += [{"id": f"ideal:{qid}", "text": ideal_by_id[qid]["text"]} for qid in order if qid in ideal_by_id]
        for q in IDEAL_PARTNER_QUESTIONS:  # any ideal item without a self twin
            if q["id"] not in order:
                items.append({"id": f"ideal:{q['id']}", "text": q["text"]})
        interstitial = {
            "after_index": len(SELF_ASSESSMENT_QUESTIONS) - 1,            "title": "Now, the second lens.",
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
        # Spread across the fifteen factors, then drop a validity item in every twelfth slot.
        by_factor = {k: [] for k in P150_FACTORS}
        item_by_id = {q["id"]: q for q in P150_PERSONALITY_ITEMS}
        for key, meta in P150_FACTORS.items():
            for iid in meta["items"]:
                if iid in item_by_id:
                    by_factor[key].append(item_by_id[iid])
        spread = _spread(list(by_factor.values()))
        placed = {q["id"] for q in spread}
        spread += [q for q in P150_PERSONALITY_ITEMS if q["id"] not in placed]
        items = []
        vi = list(P150_VALIDITY_ITEMS)
        for i, q in enumerate(spread):
            items.append({"id": str(q["id"]), "text": q["text"]})
            if (i + 1) % 12 == 0 and vi:
                v = vi.pop(0)
                items.append({"id": str(v["id"]), "text": v["text"]})
        items += [{"id": str(v["id"]), "text": v["text"]} for v in vi]
        instructions = {
            "title": "Your five-factor profile",
            "paragraphs": [
                "One hundred and thirty statements about how you tend to think, feel and act. Answer as you generally are, not as you'd like to be.",
                "This is a validated five-factor personality measure. Your result maps fifteen primary factors and five global dimensions.",
                "There are no right answers. Go at whatever pace suits you — nothing is timed.",
            ],
        }
        return items, SCALE_5, instructions, None
    if instrument == "eq":
        by_sub: dict = {}
        for q in EIMIRROR_QUESTIONS:
            by_sub.setdefault(q.get("sub") or q.get("domain") or "x", []).append(q)
        items = [{"id": str(q["id"]), "text": q["text"]} for q in _spread(list(by_sub.values()))]
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
    items, scale, instructions, interstitial = _build_items(session["instrument"], session)
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
async def start_assessment(data: StartRequest, user: dict = Depends(get_current_user)):
    if data.instrument not in INSTRUMENTS:
        raise HTTPException(status_code=404, detail="Unknown instrument")
    session = {
        "id": str(uuid.uuid4()),
        "instrument": data.instrument,
        "status": "in_progress",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "responses": {},
        "user_id": str(user["_id"]),
        "situation_at_start": user.get("situation"),
    }
    if data.instrument == "closeness":
        session["bank_version"] = load_bank()["bank_version"]
    if data.instrument == "everyday":
        session["bank_version"] = load_everyday_bank()["bank_version"]
        session["presentation"] = {"side_map": _everyday_side_map()}
    await db.mirror_v2_sessions.insert_one(dict(session))
    return _session_payload(session)


@router.get("/assessments/{session_id}")
async def get_assessment(session_id: str, user: dict = Depends(get_current_user)):
    session = await db.mirror_v2_sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await assert_session_owner(session, user)
    return _session_payload(session)


@router.put("/assessments/{session_id}/responses")
async def put_responses(session_id: str, data: ResponsesPut, user: dict = Depends(get_current_user)):
    session = await db.mirror_v2_sessions.find_one(
        {"id": session_id}, {"_id": 0, "id": 1, "instrument": 1, "status": 1, "user_id": 1}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await assert_session_owner(session, user)
    if session["status"] == "complete":
        raise HTTPException(status_code=409, detail="Session already complete")
    meta = INSTRUMENTS[session["instrument"]]
    if session["instrument"] == "everyday":
        n_points = 2
    elif session["instrument"] == "closeness":
        n_points = 7
    else:
        n_points = len(meta["scale"])
    updates = {}
    for r in data.responses:
        if not (1 <= r.value <= n_points):
            raise HTTPException(status_code=400, detail=f"Value out of range for {r.item_id}")
        # A dot in an item id would be read by Mongo as a nested path, silently discarding
        # the answer. Item banks must not use dotted ids.
        if "." in r.item_id or r.item_id.startswith("$"):
            raise HTTPException(status_code=400, detail=f"Invalid item id: {r.item_id}")
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
        ranked = rank_archetypes(arch_scores)
        lens_results[lens] = {
            "archetype_scores": arch_scores,
            "ranked": ranked,
            "primary": ranked["primary"],
            "secondary": ranked["secondary"],
            "blend": get_blend_result(arch_scores, quiz_type),
            "dimensions": calculate_dimension_scores(answers),
        }
    self_r, ideal_r = lens_results["self"], lens_results["ideal"]
    delta = {}
    for key in ARCHETYPES:
        d = round(ideal_r["archetype_scores"][key]["percentage"] - self_r["archetype_scores"][key]["percentage"], 1)
        delta[key] = d
    overall_delta = round(sum(abs(v) for v in delta.values()) / len(delta), 1)
    biggest_key = max(delta, key=lambda k: abs(delta[k]))
    delta_block = {"per_archetype": delta, "overall": overall_delta, "biggest": biggest_key}
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
            "tie": _tie_block(self_r, "self_description"),
            "archetype_scores": self_r["archetype_scores"],
            "blend": self_r["blend"],
            "compatibility": self_r["blend"],
            "dimensions": self_r["dimensions"],
        },
        "ideal": {
            "primary": {"key": ideal_r["primary"], **_arch_brief(ideal_r["primary"], "ideal_partner_description")},
            "secondary": {"key": ideal_r["secondary"], **_arch_brief(ideal_r["secondary"], "ideal_partner_description", desc=False)},
            "tie": _tie_block(ideal_r, "ideal_partner_description"),
            "archetype_scores": ideal_r["archetype_scores"],
            "blend": ideal_r["blend"],
            "compatibility": ideal_r["blend"],
            "dimensions": ideal_r["dimensions"],
        },
        "delta": delta_block,
        "shadow": shadow,
        "dimension_gaps": dim_gaps,
        "evidence_tier": "developmental",
    }


def _tie_block(lens_r: dict, desc_field: str) -> dict:
    """Names both when the top two sit inside the margin, instead of ranking them.

    The gap is printed either way: a reader who can see how close it was reads a declined rank
    as information rather than evasion.
    """
    ranked = lens_r["ranked"]
    scores = lens_r["archetype_scores"]
    a, b = ranked["primary"], ranked["secondary"]
    if not ranked["tied"]:
        return {
            "tied": False,
            "gap": ranked["gap"],
            "margin": ranked["margin"],
            "note": f"{scores[a]['name']} leads by {ranked['gap']} points.",
        }
    return {
        "tied": True,
        "gap": ranked["gap"],
        "margin": ranked["margin"],
        "keys": [a, b],
        "names": [scores[a]["name"], scores[b]["name"]],
        # Both descriptions, because a header naming two patterns above a body voicing only the
        # first would rank them again in the reader's ear.
        "descriptions": [ARCHETYPES[a].get(desc_field, ""), ARCHETYPES[b].get(desc_field, "")],
        "note": (
            f"{scores[a]['name']} and {scores[b]['name']} sit {ranked['gap']} points apart — "
            f"closer than the {ranked['margin']} points this instrument can tell apart. "
            "We name both rather than choosing between them."
        ),
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
        "loudest": scored["loudest"],
        "profile_mean": scored["profile_mean"],
        "loudest_floor": scored["loudest_floor"],
        # Old names, same objects (norms pause): nothing already reading these breaks.
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
            # No band word: High / Moderate / Developing implies a standard, and no standard is
            # documented for these 3.0 and 4.0 cut-offs any more than for the sten bands (B3).
            # A mean of 4.2 on a five-point scale is a fact about the reader's answers and stays.
            sub_scores[sub_key] = {"name": sub_data["name"], "domain": domain_key, "score": sub_avg}
            domain_total += sub_total
            domain_count += len(sub_data["items"])
        domain_avg = round(domain_total / domain_count, 2)
        domain_scores[domain_key] = {"name": domain_data["name"], "score": domain_avg,
                                     "description": domain_data["description"]}
    overall = round(sum(d["score"] for d in domain_scores.values()) / len(domain_scores), 2)
    ordered = sorted(sub_scores.values(), key=lambda x: x["score"], reverse=True)
    return {
        "instrument": "eq",
        "domain_scores": domain_scores,
        "sub_scores": sub_scores,
        "overall_score": overall,
        "strengths": ordered[:3],
        "growth_areas": ordered[-3:][::-1],
        "evidence_tier": "established",
    }


def _position(result: dict) -> dict | None:
    """The within-person layer for the primary factors (norms pause, B3 decision).

    Says only what needed no reference sample: which way each factor leans, how far it sits from
    the reader's own profile mean, and which are the loudest in their own profile. Derived at
    read time and versioned, so the mapping can be corrected without touching a delivered report.
    """
    factors = result.get("factor_scores") or {}
    # Percent-of-scale, derived at read time so stored results move with the fix. The sten is a
    # norm-referenced claim on a malformed band table — reportable.FACTOR_FLOOR_PP.
    values = factor_pcts(factors)
    if not values:
        return None
    meta = {k: {"name": f.get("name", k), "pole_high": f.get("pole_high", "one end"),
                "pole_low": f.get("pole_low", "the other end")} for k, f in factors.items()}
    block = build_position(values, meta, floor=FACTOR_FLOOR_PP)
    block["note"] = (
        "Each row shows which way you lean, as a position on that factor's own scale, and marks "
        "those sitting furthest from your own profile average — up to three, and none where none "
        "clears the floor. What they do not show is how you compare with anybody else: we have "
        "not yet established the reference sample that would make a comparison honest, so we are "
        "not making one."
    )
    return block


def _commonness(result: dict) -> dict | None:
    """Population statements for the one instrument that has a norm table (PRD §7.2).
    Derived at read time from the stored sten, and versioned so correcting the mapping
    cannot silently change an already-delivered report."""
    factors = result.get("factor_scores") or {}
    if not factors:
        return None
    out = {}
    for key, f in factors.items():
        sten = f.get("sten")
        if sten is None:
            continue
        try:
            out[key] = {
                **commonness(sten),
                "sentence": commonness_sentence(sten, f.get("pole_high", "this end"),
                                                f.get("pole_low", "the other end")),
            }
        except NotNormReferenced:
            continue
    if not out:
        return None
    return {"display_version": DISPLAY_VERSION, "factors": out,
            "excluded": "Global dimensions carry no population statement: they are clamped composites."}


def _elevation(result: dict) -> dict:
    """Elevation and shape, derived at read time.

    Describing an ideal partner as better on every pattern at once is a level shift, not a
    profile difference — and where it dominates, "the widest single gap" is mostly reporting that
    shift. Reporting the elevation is additive: it makes no existing claim untrue, so it costs no
    comparability and needs no scoring version.

    `centred_*` is computed and carried but NOT read by any reader-facing surface. Replacing the
    table with centred gaps changes which pattern is named as the widest — a different answer
    from the same data — and that waits for rk-1.1.0 alongside the other queued scoring work.
    """
    delta = result.get("delta") or {}
    per = delta.get("per_archetype") or {}
    if not per:
        return {}
    signed = list(per.values())
    elevation = round(sum(signed) / len(signed), 1)
    centred = {k: round(v - elevation, 1) for k, v in per.items()}
    overall = delta.get("overall") or 0
    return {
        "elevation": elevation,
        "elevation_share": round(abs(elevation) / overall, 2) if overall else None,
        "centred_per_archetype": centred,
        "centred_biggest": max(centred, key=lambda k: abs(centred[k])),
        "display_version": DISPLAY_VERSION,
    }


def _shadow_basis(result: dict, shadow: dict) -> str:
    """Where the shadow pull came from — the leading archetype, not the gap figures.

    Without this the reader cannot tell why a pattern was named when its printed gap is one of
    the smallest in the table.
    """
    primary = result["self"]["primary"]
    scores = result["self"]["archetype_scores"]
    own = scores.get(primary["key"], {}).get("percentage")
    gap = (result.get("delta") or {}).get("per_archetype", {}).get(shadow["key"])
    bits = [f"Mapped from your leading archetype, {primary['name']}"]
    if own is not None:
        bits.append(f"your highest score in that lens at {own:g} points")
    line = " — ".join(bits) + ", not from the gaps in the Delta"
    if gap is not None:
        line += f": {shadow['name']}'s own gap reads {gap:+g} points"
    return line + "."


def _with_choosing(result: dict) -> dict:
    """Attach read-time interpretation (choosing, composite provenance, MRD, commonness).
    Snapshot untouched."""
    extra = {}
    choosing = build_choosing(result)
    if choosing:
        extra["choosing"] = choosing
    if result.get("instrument") == "personality":
        composites = build_composites(result)
        if composites:
            extra["composites"] = composites
        position = _position(result)
        if position:
            extra["position"] = position
        # Recomputed at read time, never served from the stored field. `result["loudest"]` on any
        # result written before disp-1.5.0 was selected on the retired 1.5-sten floor, so serving
        # it would let a display version publish a value the old rule produced.
        extra["loudest"] = loudest_entries(result.get("factor_scores") or {})
        extra["strengths"] = [e for e in extra["loudest"] if e["deviation"] > 0]
        extra["blind_spots"] = [e for e in extra["loudest"] if e["deviation"] < 0]
        extra["loudest_floor"] = FACTOR_FLOOR_PP
        # Attached at read time as well as at score time, so a snapshot written before disp-1.5.0
        # carries the marker too. A renderer reading a legacy payload gets the same warning.
        extra["not_for_display"] = NOT_FOR_DISPLAY
        # Returns None while services/display.NORM_REFERENCED is False. Kept wired so the day a
        # reference sample exists, the population layer comes back without a code change here.
        common = _commonness(result)
        if common:
            extra["commonness"] = common
    if result.get("instrument") == "essential":
        extra["delta"] = {**result["delta"], **_elevation(result)}
        shadow = result.get("shadow")
        if shadow:
            extra["shadow"] = {**shadow, "basis": _shadow_basis(result, shadow)}
    if result.get("instrument") == "eq":
        # Derived at read time, like the Personality within-person layer: the floor can be
        # re-derived when the bank's reliability is measured without touching a stored result.
        extra["named"] = {**ei_named(result["domain_scores"]),
                          "display_version": DISPLAY_VERSION,
                          "facet_note": FACET_SUPPRESSION_REASON,
                          "flat_copy": EI_FLAT_COPY}
    if "mrd" not in result:
        gates = build_mrd(result)
        if gates:
            extra["mrd"] = gates
    return {**result, **extra} if extra else result


@router.post("/assessments/{session_id}/complete")
async def complete_assessment(session_id: str, user: dict = Depends(get_current_user)):
    session = await db.mirror_v2_sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await assert_session_owner(session, user)
    if session["status"] == "complete" and session.get("result"):
        return await resolved_narrative(session_id, lambda: _with_choosing(session["result"]),
                                        str(user["_id"]), user.get("situation"))
    responses = session.get("responses", {})
    instrument = session["instrument"]
    if instrument == "closeness":
        result = score_closeness(responses)
    elif instrument == "everyday":
        result = score_everyday(responses, (session.get("presentation") or {}).get("side_map"))
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
    # MRD gate evaluation is persisted, not just acted on (TRD T2.1): it is the audit trail
    # for why a report said less than it could have, and it drives the guarantee rate.
    gates = build_mrd(result)
    if gates:
        result["mrd"] = gates
    await db.mirror_v2_sessions.update_one(
        {"id": session_id},
        {"$set": {"status": "complete", "completed_at": result["completed_at"], "result": result}},
    )
    # Immutable snapshot: written once, never recomputed when norms change.
    await db.results.update_one(
        {"session_id": session_id},
        {"$setOnInsert": {"session_id": session_id, "instrument": instrument,
                          "algo_version": ALGO_VERSION, "result": result,
                          "user_id": session.get("user_id")}},
        upsert=True,
    )
    # Finishing an instrument legitimately changes the roll-up, so drop only the combined copy.
    await invalidate_combined(str(user["_id"]))
    return await resolved_narrative(session_id, lambda: _with_choosing(result), str(user["_id"]),
                                    user.get("situation"))


@router.get("/assessments/{session_id}/result")
async def get_result(session_id: str, user: dict = Depends(get_current_user)):
    session = await db.mirror_v2_sessions.find_one(
        {"id": session_id}, {"_id": 0, "result": 1, "status": 1, "user_id": 1}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await assert_session_owner(session, user)
    if session["status"] != "complete" or not session.get("result"):
        raise HTTPException(status_code=409, detail="Session not complete")
    # Snapshotted on first render: a display_version bump must never rewrite a delivered report.
    return await resolved_narrative(session_id, lambda: _with_choosing(session["result"]),
                                    str(user["_id"]), user.get("situation"))


@router.get("/reports/combined.pdf")
async def get_combined_pdf(user: dict = Depends(get_current_user)):
    """Every finished mirror plus the cross-check, in one printable document."""
    cursor = db.mirror_v2_sessions.find(
        {"user_id": str(user["_id"]), "status": "complete"},
        {"_id": 0, "instrument": 1, "result": 1, "completed_at": 1},
    )
    sessions = await cursor.to_list(50)
    if not sessions:
        raise HTTPException(status_code=409, detail="No completed instruments to print yet")

    # One result per instrument — the most recently completed. Keyed by
    # the session-side instrument string ("closeness", "essential", …) so
    # _build_findings can look up "closeness" consistently with the
    # /mirrors/findings endpoint (the stored result uses "MI-AS-36").
    best: dict = {}
    for s in sorted(sessions, key=lambda s: s.get("completed_at") or ""):
        best[s["instrument"]] = s["result"]
    # Read-time layers (elevation, the EI floor, the shadow's basis) are derived here too, or the
    # combined document silently shows less than the single-instrument one it is assembled from.
    best = {k: _with_choosing(v) for k, v in best.items()}
    results = list(best.values())

    findings = _build_findings(best) if len(best) >= 2 else []
    agreements = build_convergences(best) if len(best) >= 2 else []
    if len(best) >= 2:
        findings = findings + build_tensions(best, findings)
    synthesis = build_synthesis(best, findings, agreements)
    notes = {
        r["instrument"]: situation_note(user.get("situation"), r["instrument"])
        for r in results
    }
    pdf = await snapshot_pdf(
        str(user["_id"]), "combined",
        lambda: build_combined_pdf(
            results=results,
            user={"name": user["name"], "email": user["email"]},
            findings=findings,
            agreements=agreements,
            synthesis=synthesis,
            situation_notes={k: v for k, v in notes.items() if v},
        ),
        str(user["_id"]), user.get("situation"),
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="ratherknow-your-mirrors.pdf"'},
    )


@router.get("/answers/export.json")
async def export_answers_json(user: dict = Depends(get_current_user)):
    """Your own answers, machine-readable. Every completed sitting, nothing scored."""
    records = await _answer_export_records(user)
    return {"user": {"name": user["name"], "email": user["email"]},
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "note": ("The raw record: every item as it was put to you and the answer you gave. "
                     "Not scored, not reversed, not interpreted, and carrying no display or "
                     "scoring version — it is rebuilt from your stored answers on request."),
            "sittings": records}


@router.get("/answers/export.pdf")
async def export_answers_pdf(user: dict = Depends(get_current_user)):
    sessions = await _completed_sessions_with_responses(user)
    pdf = build_answers_pdf(
        sessions=sessions,
        user={"name": user["name"], "email": user["email"]},
        items_for=_build_items,
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="ratherknow-your-answers.pdf"'},
    )


async def _completed_sessions_with_responses(user: dict) -> list:
    """Every completed sitting, oldest first. Not one per instrument — if an instrument was taken
    twice, both sittings are the reader's own record and both belong in the export."""
    cursor = db.mirror_v2_sessions.find(
        {"user_id": str(user["_id"]), "status": "complete"},
        {"_id": 0, "id": 1, "instrument": 1, "responses": 1, "presentation": 1,
         "started_at": 1, "completed_at": 1},
    ).sort("completed_at", 1)
    sessions = await cursor.to_list(50)
    if not sessions:
        raise HTTPException(status_code=409, detail="No completed instruments to export yet")
    return sessions


async def _answer_export_records(user: dict) -> list:
    sessions = await _completed_sessions_with_responses(user)
    return [answer_records(s, _build_items) for s in sessions]


@router.get("/assessments/{session_id}/report.pdf")
async def get_report_pdf(session_id: str, user: dict = Depends(get_current_user)):
    """The printable report. Rendered from the stored snapshot — never rescored."""
    session = await db.mirror_v2_sessions.find_one(
        {"id": session_id}, {"_id": 0, "result": 1, "status": 1, "user_id": 1, "instrument": 1}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await assert_session_owner(session, user)
    if session["status"] != "complete" or not session.get("result"):
        raise HTTPException(status_code=409, detail="Session not complete")

    result = session["result"]
    pdf = await snapshot_pdf(
        session_id, "report",
        lambda: build_report_pdf(
            result=result,
            user={"name": user["name"], "email": user["email"]},
            situation_note=situation_note(user.get("situation"), result["instrument"]),
        ),
        str(user["_id"]), user.get("situation"),
    )
    slug = INSTRUMENTS[session["instrument"]]["name"].lower().replace(" ", "-")
    filename = f"ratherknow-{slug}-{session_id[:8]}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )



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
        return f"15 factors scored · {len(s)} marked strengths" if s else "15 factors scored"
    if inst == "eq":
        return f"Overall {result['overall_score']} of 5"
    return ""


@router.post("/mirrors/summary")
async def mirrors_summary(data: SummaryRequest, user: dict = Depends(get_current_user)):
    ids = data.session_ids[:10]
    out = []
    if ids:
        cursor = db.mirror_v2_sessions.find(
            {"id": {"$in": ids}, "user_id": str(user["_id"])}, {"_id": 0, "answers": 0}
        )
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
async def start_reflection(_rl=Depends(limiter("reflections"))):
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
async def put_reflection_responses(reflection_id: str, data: ResponsesPut,
                                   _rl=Depends(limiter("reflections"))):
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
async def complete_reflection(reflection_id: str, _rl=Depends(limiter("reflections"))):
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

    def pers_dev(k):
        """How far factor k sits from the reader's own profile average, in points of its scale.

        These rules used to fire on an absolute sten (>= 7, <= 4). That is a claim about other
        people, decided by a band table with no documented reference sample, and it does not
        belong in a reading that has stopped making population statements everywhere else. Same
        absolute floor as the loudest-trait selection: reportable.FACTOR_FLOOR_PP.
        """
        if not pers:
            return None
        pcts = factor_pcts(pers.get("factor_scores") or {})
        if k not in pcts or not pcts:
            return None
        return round(pcts[k] - sum(pcts.values()) / len(pcts), 1)

    def high(k):
        d = pers_dev(k)
        return d is not None and d >= FACTOR_FLOOR_PP

    def low(k):
        d = pers_dev(k)
        return d is not None and d <= -FACTOR_FLOOR_PP

    def dom(k):
        return eq["domain_scores"][k]["score"] if eq else None

    if anx is not None and high("C") and anx >= 5:
        findings.append({
            "id": "calm-general-alarmed-close",
            "sources": ["Personality Mirror", "Closeness Mirror"],
            "title": "Calm in general. Alarmed up close.",
            "body": f"The Personality Mirror has emotional stability sitting well above your own profile average — steadiness is one of the louder things in your profile. The Closeness Mirror has reassurance-seeking running clearly above the middle in close relationships specifically ({anx} on a 1–7 scale). Both can be true at once — closeness runs on its own circuitry. Worth sitting with: which of those two versions of you did the choosing, last time it mattered?",
        })
    if anx is not None and high("L") and anx <= 3:
        findings.append({
            "id": "vigilant-general-settled-close",
            "sources": ["Personality Mirror", "Closeness Mirror"],
            "title": "Your guard lives somewhere unexpected.",
            "body": f"The Personality Mirror has vigilance sitting well above your own profile average — slow to extend trust, relative to the rest of you. The Closeness Mirror finds you settled in close relationships ({anx} on reassurance, below the middle). The two disagree about where your caution actually operates. Worth sitting with: is closeness where your vigilance switches off — and is that earned, or is it just where you stop checking?",
        })
    if avo is not None and dom("relationship_management") is not None and avo >= 5 and dom("relationship_management") >= 4.0:
        findings.append({
            "id": "skilled-at-distant-in",
            "sources": ["EI Mirror", "Closeness Mirror"],
            "title": "Skilled at relationships. Distant in them.",
            "body": f"The EI Mirror has you rating your relationship management as high. The Closeness Mirror finds closeness itself sitting further away than the middle ({avo} on a 1–7 scale). Managing relationships well and letting one all the way in are different capacities — and the first can quietly substitute for the second for years without anyone noticing, including you.",
        })
    if avo is not None and high("A") and avo >= 5:
        findings.append({
            "id": "warm-general-guarded-close",
            "sources": ["Personality Mirror", "Closeness Mirror"],
            "title": "Warm in general. Guarded up close.",
            "body": f"The Personality Mirror has warmth sitting well above your own profile average — attentive to people, easy to be around. The Closeness Mirror has intimacy itself kept at more of a distance ({avo} on a 1–7 scale). Warmth given widely can be a comfortable place to stand while closeness stays unentered. Worth sitting with: who gets the warmth, and who gets let in — and are they ever the same person?",
        })
    if avo is not None and low("Q2") and avo >= 5:
        findings.append({
            "id": "leans-on-people-not-partner",
            "sources": ["Personality Mirror", "Closeness Mirror"],
            "title": "You lean on people. Just not on a partner.",
            "body": "The Personality Mirror has self-reliance sitting well below your own profile average — comfortable relying on others in general life. The Closeness Mirror finds leaning on a partner specifically coming much less easily. The disagreement is the finding: support isn't hard for you, partnership-shaped support is. Worth sitting with: what does a partner represent that a friend doesn't?",
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
                "body": "Two self-report instruments both came back glowing — and the Personality Mirror's validity check counts how many of the ten most flattering statements you agreed with. You agreed with most of them. Nothing wrong with a good day. Worth sitting with: would an ordinary-day retake say the same?",
            })
    return findings[:4]


@router.post("/mirrors/findings")
async def mirrors_findings(data: SummaryRequest, user: dict = Depends(get_current_user)):
    ids = data.session_ids[:10]
    by_instrument = {}
    if ids:
        cursor = db.mirror_v2_sessions.find(
            {"id": {"$in": ids}, "status": "complete", "user_id": str(user["_id"])},
            {"_id": 0, "instrument": 1, "result": 1},
        )
        async for session in cursor:
            if session.get("result"):
                by_instrument[session["instrument"]] = session["result"]
    tensions = _build_findings(by_instrument) if len(by_instrument) >= 2 else []
    agreements = build_convergences(by_instrument) if len(by_instrument) >= 2 else []
    if len(by_instrument) >= 2:
        tensions = tensions + build_tensions(by_instrument, tensions)
    return {
        "instruments_complete": sorted(by_instrument.keys()),
        "findings": tensions,
        "agreements": agreements,
        "synthesis": build_synthesis(by_instrument, tensions, agreements),
    }


# ==================== MRD SHADOW-MODE DIAGNOSTICS ====================
# The gates run in shadow: they record what they would have withheld, and withhold nothing.
# This endpoint is the point of that. Counts only — no answers, no identities.
#
# B2: rates are reported per scale set, not as one figure. A single rate is dominated by the
# fifteen personality primaries competing for distinction; the four-to-six element sets behave
# differently and one number hides that. mrd_sd_units travels alongside mrd for the same reason.

@router.get("/diagnostics/mrd")
async def mrd_diagnostics(user: dict = Depends(get_current_user)):
    profile = mrd_config()
    totals = {"results_examined": 0, "results_with_gates": 0, "results_with_any_suppression": 0}
    by_gate: dict = {}
    by_scale_set: dict = {}

    cursor = db.results.find({}, {"_id": 0, "instrument": 1, "result": 1})
    async for row in cursor:
        result = row.get("result") or {}
        totals["results_examined"] += 1
        gates = result.get("mrd") or build_mrd(result)
        if not gates:
            continue
        totals["results_with_gates"] += 1
        suppressions = gates.get("suppressions") or []
        if suppressions:
            totals["results_with_any_suppression"] += 1
        for s in suppressions:
            by_gate[s["gate"]] = by_gate.get(s["gate"], 0) + 1
        for s in gates.get("scale_sets") or []:
            bucket = by_scale_set.setdefault(s["scale_set"], {
                "evaluated": 0, "flat": 0, "indistinct_named": 0, "suppressed": 0,
                "mrd": s["mrd"],
                "mrd_sd_units": s.get("mrd_sd_units") or mrd_sd_units_for(s["scale_set"]),
            })
            bucket["evaluated"] += 1
            if s["flat_profile"]:
                bucket["flat"] += 1
            if s.get("indistinct_named_scales"):
                bucket["indistinct_named"] += 1
            if s["flat_profile"] or s.get("indistinct_named_scales"):
                bucket["suppressed"] += 1

    for bucket in by_scale_set.values():
        bucket["suppression_rate"] = round(bucket["suppressed"] / (bucket["evaluated"] or 1), 3)

    examined = totals["results_with_gates"] or 1
    return {
        "mode": MRD_MODE,
        "profile": profile["profile_version"],
        "placeholder_alpha": bool(profile.get("placeholder")),
        "totals": totals,
        "suppression_rate": round(totals["results_with_any_suppression"] / examined, 3),
        "by_gate": by_gate,
        "by_scale_set": by_scale_set,
        "note": (
            "Shadow mode: nothing was withheld from any reader. suppression_rate is the share of "
            "gate-eligible results where at least one gate would have fired; read the per-scale-set "
            "rates rather than the overall one, since the fifteen personality primaries dominate it. "
            "mrd_sd_units is the same threshold in standard deviations of its own scale — sets "
            "sharing an alpha share it exactly, which is why the small-unit sets are not the "
            "healthier instruments they appear to be."
        ),
    }

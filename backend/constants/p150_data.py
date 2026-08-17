"""
Personality 150 Assessment Data
- 120 personality items (15 factors × 8 items each)
- 10 validity check items (social desirability)
- 20 switch thinking cognitive items
"""

# ============== 16 PRIMARY FACTORS ==============
P150_FACTORS = {
    "A": {"name": "Warmth", "pole_low": "Reserved", "pole_high": "Warm", "items": list(range(1, 9))},
    "C": {"name": "Emotional Stability", "pole_low": "Reactive", "pole_high": "Stable", "items": list(range(9, 17))},
    "E": {"name": "Dominance", "pole_low": "Cooperative", "pole_high": "Assertive", "items": list(range(17, 25))},
    "F": {"name": "Liveliness", "pole_low": "Serious", "pole_high": "Spontaneous", "items": list(range(25, 33))},
    "G": {"name": "Rule-Consciousness", "pole_low": "Expedient", "pole_high": "Conscientious", "items": list(range(33, 41))},
    "H": {"name": "Social Boldness", "pole_low": "Shy", "pole_high": "Venturesome", "items": list(range(41, 49))},
    "I": {"name": "Sensitivity", "pole_low": "Tough-minded", "pole_high": "Tender-hearted", "items": list(range(49, 57))},
    "L": {"name": "Vigilance", "pole_low": "Trusting", "pole_high": "Suspicious", "items": list(range(57, 65))},
    "M": {"name": "Abstractedness", "pole_low": "Grounded", "pole_high": "Imaginative", "items": list(range(65, 73))},
    "N": {"name": "Privateness", "pole_low": "Forthright", "pole_high": "Discreet", "items": list(range(73, 81))},
    "O": {"name": "Apprehension", "pole_low": "Self-Assured", "pole_high": "Worried", "items": list(range(81, 89))},
    "Q1": {"name": "Openness to Change", "pole_low": "Traditional", "pole_high": "Experimenting", "items": list(range(89, 97))},
    "Q2": {"name": "Self-Reliance", "pole_low": "Group-Oriented", "pole_high": "Independent", "items": list(range(97, 105))},
    "Q3": {"name": "Perfectionism", "pole_low": "Flexible", "pole_high": "Organized", "items": list(range(105, 113))},
    "Q4": {"name": "Tension", "pole_low": "Relaxed", "pole_high": "Driven", "items": list(range(113, 121))},
}

# Even-positioned items within each factor are reverse-scored
P150_REVERSED_ITEMS = set()
for factor_data in P150_FACTORS.values():
    items = factor_data["items"]
    for i in range(1, len(items), 2):  # indices 1,3,5,7 → items at positions 2,4,6,8
        P150_REVERSED_ITEMS.add(items[i])

# ============== GLOBAL FACTOR MAPPINGS (Big Five) ==============
# The "receptivity" entry replaces the legacy "tough_mindedness" super-factor.
# Two reasons for the change (Feb 2026):
#   1. The previous all-negative-direction scoring formula clamped most
#      respondents to Sten 1 — the score was effectively unusable.
#   2. The 16PF Tough-Mindedness construct is a known split-cluster super-
#      factor (interpersonal/affective + intellectual/imaginative). We score
#      both sub-clusters separately under `sub_clusters` so respondents see
#      two genuinely useful scores instead of one composite that the data
#      doesn't always support.
P150_GLOBAL_FACTORS = {
    "extraversion": {
        "name": "Extraversion",
        "factors": {"A": 0.3, "F": 0.4, "H": 0.4, "N": -0.3, "Q2": -0.5},
        "description": "How you engage with the external world"
    },
    "anxiety": {
        "name": "Anxiety / Neuroticism",
        "factors": {"C": -0.4, "L": 0.3, "O": 0.4, "Q4": 0.4},
        "description": "Your emotional response patterns"
    },
    "receptivity": {
        "name": "Receptivity",
        "factors": {"A": 0.3, "I": 0.5, "M": 0.3, "Q1": 0.4},
        "description": "How open you are to people and to new ideas",
        "previous_name": "Tough-Mindedness",
        "sub_clusters": {
            "interpersonal_receptivity": {
                "name": "Interpersonal Receptivity",
                "factors": {"A": 0.3, "I": 0.5},
                "description": "Warmth and emotional attunement to others"
            },
            "intellectual_receptivity": {
                "name": "Intellectual Receptivity",
                "factors": {"M": 0.3, "Q1": 0.4},
                "description": "Imagination, abstraction and openness to new ideas"
            },
        },
    },
    "independence": {
        "name": "Independence",
        "factors": {"E": 0.5, "H": 0.4, "L": 0.2, "Q1": 0.3},
        "description": "Your autonomy in thought and action"
    },
    "self_control": {
        "name": "Self-Control",
        "factors": {"F": -0.3, "G": 0.4, "M": -0.3, "Q3": 0.4},
        "description": "How you regulate impulses and behaviour"
    },
}

# ── Global-factor calibration ─────────────────────────────────────────────────
# Per-global `gain` applied as:  global = 5.5 + gain * Σ(loading·(sten−5.5)).
# The weighted second-order equations (16PF-style loadings, decimal output) are a
# genuine improvement over the old equal-weight average and do NOT skew the
# population. Gains are deliberately held at 1.0: an n=1 calibration to a single
# trusted sheet (Philip Dawes) was trialled but NOT shipped — applying those
# gains (esp. Receptivity 0.29 / Self-Control 0.46) would have baked one person's
# distortion into every user's composite. At gain 1.0 the equations already track
# the trusted 16PF closely where the primaries are sound (Extraversion 8.45 vs
# 8.53, Independence 9.60 vs 9.58, Anxiety 3.55 vs 3.72); the residual on
# Receptivity/Self-Control is the HONEST signal that those constructs (and the
# raw→sten norms feeding them) need empirical re-anchoring — not a gain patch.
#   Re-fit (only with a real paired pool, n≥30+): python -m scripts.calibrate_p150_globals
GLOBAL_CALIBRATION = {
    "extraversion": 1.0,
    "anxiety": 1.0,
    "receptivity": 1.0,
    "independence": 1.0,
    "self_control": 1.0,
    "_meta": {"source": "uncalibrated_gain_1.0", "note": "n=1 gains trialled, not shipped (no population skew)"},
}


def score_global_factor(factor_scores: dict, factors_map: dict, gain: float = 1.0) -> float:
    """Compute a Big Five super-factor score from the underlying primary Stens.

    16PF-style weighted second-order equation, centred on the Sten midpoint so a
    perfectly average profile (every primary = 5.5) returns 5.5 exactly:
        global = 5.5 + gain · Σ( loading · (sten − 5.5) )
    Returns a continuous (decimal) Sten 1–10. `gain` carries the trusted-metric
    calibration (see GLOBAL_CALIBRATION); default 1.0 leaves the weighted sum
    on its native scale.
    """
    if not factors_map:
        return 5.5
    weighted = sum(w * (factor_scores[f_key]["sten"] - 5.5)
                   for f_key, w in factors_map.items())
    return max(1.0, min(10.0, 5.5 + gain * weighted))


def compute_global_scores(factor_scores: dict) -> dict:
    """Build the full `global_scores` dict from the 15 primary factor Stens.
    Each entry carries `score` (rounded Sten, for display/back-compat) and
    `score_precise` (the calibrated decimal). Sub-clusters inherit the parent's
    calibration gain so they sit on the same scale as the composite."""
    out = {}
    for gf_key, gf_data in P150_GLOBAL_FACTORS.items():
        gain = GLOBAL_CALIBRATION.get(gf_key, 1.0)
        precise = score_global_factor(factor_scores, gf_data["factors"], gain)
        score = max(1, min(10, round(precise)))
        entry = {
            "name": gf_data["name"],
            "description": gf_data["description"],
            "score": score,
            "score_precise": round(precise, 2),
            "calibrated_gain": gain,
            "label": get_sten_label(score),
        }
        sub_clusters = gf_data.get("sub_clusters")
        if sub_clusters:
            entry["sub_clusters"] = {}
            for sc_key, sc_data in sub_clusters.items():
                sc_precise = score_global_factor(factor_scores, sc_data["factors"], gain)
                sc_score = max(1, min(10, round(sc_precise)))
                entry["sub_clusters"][sc_key] = {
                    "name": sc_data["name"],
                    "description": sc_data["description"],
                    "score": sc_score,
                    "score_precise": round(sc_precise, 2),
                    "label": get_sten_label(sc_score),
                }
        out[gf_key] = entry
    return out

# ============== STEN SCORE CONVERSION ==============
def raw_to_sten(raw_score):
    """Convert raw factor score (8-40) to Sten (1-10)."""
    if raw_score <= 10: return 1
    if raw_score <= 12: return 2
    if raw_score <= 15: return 3
    if raw_score <= 18: return 4
    if raw_score <= 21: return 5
    if raw_score <= 24: return 6
    if raw_score <= 27: return 7
    if raw_score <= 30: return 8
    if raw_score <= 35: return 9
    return 10

def get_sten_label(sten):
    if sten <= 2: return "Very Low"
    if sten <= 4: return "Low"
    if sten <= 6: return "Average"
    if sten <= 8: return "High"
    return "Very High"

# ============== PERSONALITY ITEMS (1-120) ==============
P150_PERSONALITY_ITEMS = [
    # Factor A: Warmth (1-8)
    {"id": 1, "text": "I enjoy being around people and find social interactions energising."},
    {"id": 2, "text": "I prefer spending time alone rather than in group settings."},
    {"id": 3, "text": "I make an effort to help others feel comfortable and welcome."},
    {"id": 4, "text": "I find it difficult to show affection or warmth to others."},
    {"id": 5, "text": "I am genuinely interested in how other people are feeling."},
    {"id": 6, "text": "I tend to keep emotional distance from most people."},
    {"id": 7, "text": "People often tell me I am approachable and friendly."},
    {"id": 8, "text": "I find small talk with strangers uncomfortable and unnecessary."},
    # Factor C: Emotional Stability (9-16)
    {"id": 9, "text": "I remain calm under pressure and rarely feel overwhelmed."},
    {"id": 10, "text": "My mood can shift quickly depending on external events."},
    {"id": 11, "text": "I bounce back quickly from setbacks and disappointments."},
    {"id": 12, "text": "I often worry about things that might go wrong."},
    {"id": 13, "text": "I feel in control of my emotions most of the time."},
    {"id": 14, "text": "I can become irritable when things do not go as planned."},
    {"id": 15, "text": "Even in stressful situations, I think clearly and logically."},
    {"id": 16, "text": "Small frustrations can sometimes ruin my entire day."},
    # Factor E: Dominance (17-24)
    {"id": 17, "text": "I naturally take the lead in group situations."},
    {"id": 18, "text": "I generally defer to others when making group decisions."},
    {"id": 19, "text": "I am comfortable expressing disagreement with authority figures."},
    {"id": 20, "text": "I tend to go along with what others want to avoid conflict."},
    {"id": 21, "text": "I feel confident directing others and delegating tasks."},
    {"id": 22, "text": "I prefer to follow instructions rather than set the direction myself."},
    {"id": 23, "text": "In debates, I hold my ground even when outnumbered."},
    {"id": 24, "text": "I find it easier to agree with the majority than to stand out."},
    # Factor F: Liveliness (25-32)
    {"id": 25, "text": "I am spontaneous and enjoy doing things on impulse."},
    {"id": 26, "text": "I prefer to plan carefully before acting on anything."},
    {"id": 27, "text": "I bring energy and enthusiasm to social gatherings."},
    {"id": 28, "text": "I tend to be serious and measured in most situations."},
    {"id": 29, "text": "I love trying new activities and seeking novel experiences."},
    {"id": 30, "text": "I am more comfortable with routines and predictability."},
    {"id": 31, "text": "People describe me as cheerful and fun to be around."},
    {"id": 32, "text": "I often hold back from expressing excitement openly."},
    # Factor G: Rule-Consciousness (33-40)
    {"id": 33, "text": "I believe rules and standards should be followed consistently."},
    {"id": 34, "text": "I sometimes bend the rules if it seems more practical."},
    {"id": 35, "text": "I feel a strong sense of duty and obligation to do the right thing."},
    {"id": 36, "text": "I can be relaxed about deadlines if no one is checking."},
    {"id": 37, "text": "I follow the proper process even when no one would notice if I skipped it."},
    {"id": 38, "text": "I believe morality is relative and depends on the situation."},
    {"id": 39, "text": "I feel uncomfortable breaking rules, even small or unimportant ones."},
    {"id": 40, "text": "I sometimes cut corners to save time and effort."},
    # Factor H: Social Boldness (41-48)
    {"id": 41, "text": "I am comfortable speaking to large groups of people."},
    {"id": 42, "text": "I feel nervous and self-conscious in unfamiliar social settings."},
    {"id": 43, "text": "I enjoy meeting new people and putting myself out there."},
    {"id": 44, "text": "I tend to stay in the background in social situations."},
    {"id": 45, "text": "I do not hesitate to ask questions or speak up in meetings."},
    {"id": 46, "text": "I am cautious about drawing attention to myself."},
    {"id": 47, "text": "I handle criticism from others without taking it personally."},
    {"id": 48, "text": "I worry about what people think of me in social situations."},
    # Factor I: Sensitivity (49-56)
    {"id": 49, "text": "I am moved by art, music, and beauty in my surroundings."},
    {"id": 50, "text": "I prefer practical solutions over aesthetically pleasing ones."},
    {"id": 51, "text": "I am sensitive to other people's feelings and emotional states."},
    {"id": 52, "text": "I believe decisions should be based on logic, not emotions."},
    {"id": 53, "text": "I find myself deeply affected by stories of human suffering."},
    {"id": 54, "text": "I tend to focus on facts rather than feelings when problem-solving."},
    {"id": 55, "text": "I value kindness and empathy above efficiency and results."},
    {"id": 56, "text": "I think people are too sensitive about minor issues."},
    # Factor L: Vigilance (57-64)
    {"id": 57, "text": "I am cautious about trusting people until I know them well."},
    {"id": 58, "text": "I generally assume the best intentions in others."},
    {"id": 59, "text": "I pay close attention to inconsistencies in what people say."},
    {"id": 60, "text": "I rarely suspect that others have hidden motives."},
    {"id": 61, "text": "I question the motives behind favours and compliments."},
    {"id": 62, "text": "I am quick to forgive and move past disagreements."},
    {"id": 63, "text": "I keep track of who has wronged me in the past."},
    {"id": 64, "text": "I take people at face value without overthinking their intentions."},
    # Factor M: Abstractedness (65-72)
    {"id": 65, "text": "I often get lost in thought or daydreaming."},
    {"id": 66, "text": "I focus on practical matters and immediate tasks."},
    {"id": 67, "text": "I enjoy thinking about abstract concepts and theories."},
    {"id": 68, "text": "I prefer dealing with concrete, real-world problems."},
    {"id": 69, "text": "My mind frequently wanders to creative possibilities and what-ifs."},
    {"id": 70, "text": "I am very attentive to details and the task at hand."},
    {"id": 71, "text": "I am drawn to unconventional ideas that challenge the mainstream."},
    {"id": 72, "text": "I prefer straightforward, down-to-earth conversations."},
    # Factor N: Privateness (73-80)
    {"id": 73, "text": "I keep my thoughts and feelings to myself unless specifically asked."},
    {"id": 74, "text": "I am open and transparent about my feelings and opinions."},
    {"id": 75, "text": "I carefully consider what to share and with whom."},
    {"id": 76, "text": "I tend to speak freely without filtering my thoughts."},
    {"id": 77, "text": "I maintain a clear boundary between my personal and public life."},
    {"id": 78, "text": "People always know where they stand with me because I am direct."},
    {"id": 79, "text": "I can be diplomatic even when I disagree strongly."},
    {"id": 80, "text": "I find it hard to hide my true feelings in conversations."},
    # Factor O: Apprehension (81-88)
    {"id": 81, "text": "I often second-guess myself after making decisions."},
    {"id": 82, "text": "I feel confident about the choices I make."},
    {"id": 83, "text": "I am prone to feelings of guilt, even over small matters."},
    {"id": 84, "text": "I rarely dwell on past mistakes or worry about them."},
    {"id": 85, "text": "I tend to take criticism very personally and ruminate on it."},
    {"id": 86, "text": "I brush off negative feedback without losing confidence."},
    {"id": 87, "text": "I sometimes feel inadequate compared to my peers."},
    {"id": 88, "text": "I have a strong sense of self-worth that rarely wavers."},
    # Factor Q1: Openness to Change (89-96)
    {"id": 89, "text": "I actively seek out new ideas and different ways of doing things."},
    {"id": 90, "text": "I prefer the tried-and-tested approach to problem-solving."},
    {"id": 91, "text": "I enjoy questioning established conventions and traditions."},
    {"id": 92, "text": "I believe there is usually a good reason for the way things are done."},
    {"id": 93, "text": "I am excited by change and see it as an opportunity for growth."},
    {"id": 94, "text": "I feel unsettled when routines and familiar structures change."},
    {"id": 95, "text": "I challenge assumptions that others take for granted."},
    {"id": 96, "text": "I am more comfortable with stability than with constant innovation."},
    # Factor Q2: Self-Reliance (97-104)
    {"id": 97, "text": "I prefer to work through problems on my own before asking for help."},
    {"id": 98, "text": "I work best when collaborating with others as part of a team."},
    {"id": 99, "text": "I am comfortable making important decisions independently."},
    {"id": 100, "text": "I value group consensus over individual judgement."},
    {"id": 101, "text": "I enjoy solitary activities and am comfortable being alone."},
    {"id": 102, "text": "I feel most productive when surrounded by other people."},
    {"id": 103, "text": "I trust my own judgement even when others disagree."},
    {"id": 104, "text": "I often look to others for reassurance before acting."},
    # Factor Q3: Perfectionism (105-112)
    {"id": 105, "text": "I like to have everything planned and organised before I start."},
    {"id": 106, "text": "I am comfortable with a degree of mess and spontaneity in my work."},
    {"id": 107, "text": "I set high standards for myself and work hard to meet them."},
    {"id": 108, "text": "I am flexible about quality if it means finishing faster."},
    {"id": 109, "text": "I double-check my work to make sure it is free of errors."},
    {"id": 110, "text": "I sometimes submit work that is good enough rather than perfect."},
    {"id": 111, "text": "I feel frustrated when others do not share my commitment to quality."},
    {"id": 112, "text": "I can easily let go of small imperfections and move on."},
    # Factor Q4: Tension (113-120)
    {"id": 113, "text": "I often feel a sense of inner restlessness and urgency."},
    {"id": 114, "text": "I am generally relaxed and at ease, even with unfinished tasks."},
    {"id": 115, "text": "I have difficulty winding down and switching off from work."},
    {"id": 116, "text": "I rarely feel tense, even during busy periods."},
    {"id": 117, "text": "I feel driven to achieve more and never fully satisfied with my progress."},
    {"id": 118, "text": "I am content with my current pace and accomplishments."},
    {"id": 119, "text": "I notice physical signs of tension such as tight muscles or restlessness."},
    {"id": 120, "text": "I find it easy to relax and let go of stress."},
]

# ============== VALIDITY CHECK ITEMS (121-130) ==============
# Mixed-direction Saint scale (revised Jun 2026 in response to external
# psychometric review). Items 121, 124, 126, 128, 130 are SAINTLY items
# (high agreement = self-presentation tendency). Items 122, 123, 125, 127,
# 129 are UNIVERSALLY-TRUE items (high DISAGREEMENT = self-presentation
# tendency) — disagreeing with the universally-true statement is itself
# evidence of impression management. See `assessments_p150.py` for the
# combined scoring.
P150_VALIDITY_ITEMS = [
    {"id": 121, "text": "I have never told even a small lie.", "reverse": False},
    {"id": 122, "text": "I have occasionally felt irritated by another person's behaviour.", "reverse": True},
    {"id": 123, "text": "There have been times when I have not been entirely truthful in a conversation.", "reverse": True},
    {"id": 124, "text": "I have never felt jealous of someone else's success.", "reverse": False},
    {"id": 125, "text": "I sometimes find myself daydreaming when someone is speaking to me.", "reverse": True},
    {"id": 126, "text": "I have never said something I later regretted.", "reverse": False},
    {"id": 127, "text": "There are some people I find genuinely difficult to like.", "reverse": True},
    {"id": 128, "text": "I have never avoided a difficult conversation.", "reverse": False},
    {"id": 129, "text": "I have occasionally bent a rule when no one was watching.", "reverse": True},
    {"id": 130, "text": "I have never had an unkind thought about another person.", "reverse": False},
]

# ============== SWITCH THINKING ITEMS (131-150) ==============
# Original A Questions — used by DW Personality Mirror
P150_SWITCH_ITEMS_A = [
    {"id": 131, "text": "If all Bloops are Razzles, and all Razzles are Lazzles, which must be true?", "options": ["All Lazzles are Bloops", "All Bloops are Lazzles", "Some Razzles are not Bloops", "No Lazzles are Razzles"], "correct": 1},
    {"id": 132, "text": "A farmer has 17 sheep. All but 9 die. How many sheep are left?", "options": ["8", "9", "17", "0"], "correct": 1},
    {"id": 133, "text": "The word BLUE is printed in red ink. What colour is the ink?", "options": ["Blue", "Green", "Red", "Yellow"], "correct": 2},
    {"id": 134, "text": "If you rotate the letter N by 90 degrees clockwise, it most closely resembles which letter?", "options": ["Z", "M", "U", "S"], "correct": 0},
    {"id": 135, "text": "What comes next in the series: 2, 6, 12, 20, 30, ?", "options": ["40", "42", "36", "38"], "correct": 1},
    {"id": 136, "text": "A brick is typically used for building. Which of these is the most creative alternative use?", "options": ["A paperweight", "A doorstop", "A goal marker", "All of these equally"], "correct": 3},
    {"id": 137, "text": "If some teachers are musicians and all musicians are creative, which must be true?", "options": ["All teachers are creative", "Some teachers are creative", "No teachers are creative", "All creative people are musicians"], "correct": 1},
    {"id": 138, "text": "Book is to Reading as Fork is to:", "options": ["Kitchen", "Eating", "Metal", "Cooking"], "correct": 1},
    {"id": 139, "text": "In the sequence AABBAABBA, how many times does the pattern AB appear?", "options": ["2", "3", "4", "1"], "correct": 0},
    {"id": 140, "text": "If yesterday is two days after Monday, what day is today?", "options": ["Wednesday", "Thursday", "Friday", "Saturday"], "correct": 1},
    {"id": 141, "text": "If # means 'add 3' and * means 'multiply by 2', what is 4 # * ?", "options": ["14", "11", "10", "16"], "correct": 0},
    {"id": 142, "text": "A cube has 6 faces. If you cut one corner off, how many faces does the resulting shape have?", "options": ["5", "6", "7", "8"], "correct": 2},
    {"id": 143, "text": "Which of these words can be rearranged to form LISTEN?", "options": ["LISTED", "INSTAL", "SILENT", "NESTLE"], "correct": 2},
    {"id": 144, "text": "Which of these does NOT belong with the others: Dog, Cat, Goldfish, Hamster?", "options": ["Dog", "Cat", "Goldfish", "Hamster"], "correct": 2},
    {"id": 145, "text": "What comes next in the sequence: J, F, M, A, M, J, J, ?", "options": ["A", "S", "O", "N"], "correct": 0},
    {"id": 146, "text": "If A=1, B=2, C=3 and so on, what is the value of the word CAB?", "options": ["5", "6", "7", "8"], "correct": 1},
    {"id": 147, "text": "You face North, turn 90 degrees right, then 180 degrees, then 90 degrees left. Which direction do you face?", "options": ["North", "South", "East", "West"], "correct": 1},
    {"id": 148, "text": "If RED=1, BLUE=2, GREEN=3, what does BLUE + RED equal?", "options": ["PURPLE", "3", "GREEN", "Both B and C"], "correct": 3},
    {"id": 149, "text": "All roses are flowers. Some flowers fade quickly. Therefore:", "options": ["All roses fade quickly", "Some roses may fade quickly", "No roses fade quickly", "Roses are not flowers"], "correct": 1},
    {"id": 150, "text": "A clock shows 3:15. What is the angle between the hour and minute hands?", "options": ["0 degrees", "7.5 degrees", "15 degrees", "22.5 degrees"], "correct": 1},
]

# B Questions — used by P150 (My Mirror product)
P150_SWITCH_ITEMS = [
    {"id": 131, "text": "A cube has a Red top and a Blue bottom. Flip the cube upside down (a 180° rotation around a horizontal axis). What colour is the new top?", "options": ["Red", "Blue", "White", "Yellow"], "correct": 1},
    {"id": 132, "text": "Rule: a shape's colour flips (Black↔White) and its size flips (Large↔Small), but the shape stays the same. Example: Large Black Circle → Small White Circle. Apply the rule: Large Black Square → ?", "options": ["Small White Square", "Large White Square", "Small Black Square", "Small White Circle"], "correct": 0},
    {"id": 133, "text": "If 1+4 = 5 and 2+5 = 12 (Pattern: a+(a x b)). What is 3+6?", "options": ["9", "21", "18", "15"], "correct": 1},
    {"id": 134, "text": "Sequence: 2, 6, 12, 20. If the next step switches from 'Add the next even number' to 'Multiply the last increment by the first number,' what is the next number?", "options": ["30", "36", "40", "28"], "correct": 1},
    {"id": 135, "text": "If A=1, B=2, C=3 and the rule is 'Sum of letters,' CAB = 6. Switch rule: If a word contains a vowel, multiply the total by 2. What is BED?", "options": ["11", "7", "22", "14"], "correct": 2},
    {"id": 136, "text": "Pattern: 1, 4, 9, 16. The rule switches from 'n squared' to 'the sum of the digits of the next n squared.' What is the next number?", "options": ["7", "25", "13", "9"], "correct": 0},
    {"id": 137, "text": "If X+Y=XY and 2+2=4. If the rule switches to X+Y=(X to the power Y), what is 3+2?", "options": ["5", "6", "9", "8"], "correct": 2},
    {"id": 138, "text": "LAVA is to VALA. Switch to 'Delete the middle two letters, double each end': FIRE is to...", "options": ["FFEE", "ERFI", "FREE", "FIIE"], "correct": 0},
    {"id": 139, "text": "If a machine produces 10 units in 2 hours, and a second machine is twice as fast. Switch to 'Combined output': How many units do they make together in 2 hours?", "options": ["15", "25", "20", "30"], "correct": 3},
    {"id": 140, "text": "Think Backwards: You end with 5. The steps were 'Subtract 10' then 'Divide by 2.' What was the starting number?", "options": ["0", "15", "20", "30"], "correct": 2},
    {"id": 141, "text": "Sequence: 2, 4, 8, 16. Rule Switch: The next number is the sum of the last two numbers.", "options": ["32", "7", "24", "14"], "correct": 2},
    {"id": 142, "text": "'Large' is to 'Small.' Switch to 'Synonym': 'Quick' is to...", "options": ["Slow", "Rapid", "Quiet", "Delay"], "correct": 1},
    {"id": 143, "text": "A=1, B=2, C=3. Switch Rule: Vowels = 0, Consonants = 1. What is BED?", "options": ["11", "2", "7", "3"], "correct": 1},
    {"id": 144, "text": "Face North, turn 90\u00b0 right. The rule switches so 'Left' means 'Right'. You are told to turn Left \u2014 which way do you now face?", "options": ["South", "North", "West", "East"], "correct": 0},
    {"id": 145, "text": "1, 2, 3, 4. Rule Switch: The next number is the product of the first and last numbers in this sequence.", "options": ["5", "8", "4", "24"], "correct": 2},
    {"id": 146, "text": "'Cat' is to 'Kitten.' Switch to 'Opposite Gender': 'Stallion' is to...", "options": ["Mare", "Foal", "Horse", "Colt"], "correct": 0},
    {"id": 147, "text": "Matrix: Row 1 [2, 3]. Row 2 [4, 9]. Rule Switch for Row 3: Square the first number and subtract the second.", "options": ["[16, 81]", "[7]", "[13]", "[5]"], "correct": 1},
    {"id": 148, "text": "A clock is at 6:00. Rotate the hour hand 90 degrees clockwise. What time is it?", "options": ["3:00", "9:00", "12:00", "6:15"], "correct": 1},
    {"id": 149, "text": "If 2 machines make 2 parts in 2 minutes, how long does 1 machine take to make 1 part?", "options": ["2 minutes", "1 minute", "4 minutes", "0.5 minutes"], "correct": 0},
    {"id": 150, "text": "In a code, DOG = 26 (D=4, O=15, G=7). If the code switches to 'Reverse Alphabet', what is the first letter of CAT?", "options": ["3", "24", "26", "1"], "correct": 1},
]

# Build item-to-factor mapping
P150_ITEM_FACTOR_MAP = {}
for factor_key, factor_data in P150_FACTORS.items():
    for item_id in factor_data["items"]:
        P150_ITEM_FACTOR_MAP[item_id] = factor_key

# Switch thinking interpretation
def get_switch_label(score):
    if score <= 10: return "Low Flexibility"
    if score <= 16: return "Moderate Flexibility"
    return "High Agility"

def get_switch_description(score):
    if score <= 10:
        return "Prefers routine and structured approaches. May find rapid context-switching challenging."
    if score <= 16:
        return "Able to pivot between thinking modes with effort. Prefers to complete one thought before moving to the next."
    return "Fast learner and natural switch-thinker. Thrives in dynamic, multi-dimensional environments."

# Narrative blend profiles
P150_BLEND_PROFILES = {
    "burnout_risk": {
        "condition": lambda factors: factors.get("Q4", 0) >= 8 and factors.get("C", 0) <= 3,
        "label": "Burnout Risk",
        "description": "High inner tension combined with emotional reactivity creates vulnerability to chronic stress and burnout."
    },
    "innovator": {
        "condition": lambda factors, switch=0: factors.get("M", 0) >= 7 and switch >= 17,
        "label": "The Innovator",
        "description": "Rich imagination paired with high cognitive agility produces a natural capacity for breakthrough thinking."
    },
    "reliable_specialist": {
        "condition": lambda factors: factors.get("G", 0) >= 7 and factors.get("Q3", 0) >= 7,
        "label": "The Reliable Specialist",
        "description": "Strong rule-consciousness and perfectionism create exceptional reliability and attention to detail."
    },
    "social_catalyst": {
        "condition": lambda factors: factors.get("A", 0) >= 7 and factors.get("H", 0) >= 7 and factors.get("F", 0) >= 7,
        "label": "The Social Catalyst",
        "description": "Warmth, boldness, and liveliness combine to create a natural connector and energiser of groups."
    },
    "independent_thinker": {
        "condition": lambda factors: factors.get("Q2", 0) >= 7 and factors.get("Q1", 0) >= 7 and factors.get("E", 0) >= 7,
        "label": "The Independent Thinker",
        "description": "Self-reliance, openness to change, and assertiveness create a fiercely original mind."
    },
}


# ============== GLOSSARY ==============
P150_GLOSSARY_BIG_FIVE = [
    {
        "dimension": "Extraversion",
        "what_it_measures": "How energetically you engage with the external world — sociability, assertiveness, enthusiasm, and comfort in group settings.",
        "high_score": "Outgoing, talkative, energised by social interaction. Comfortable leading meetings, networking, and thinking out loud.",
        "low_score": "Reflective, reserved, energised by solitude. Prefers one-to-one conversations, written communication, and independent work.",
        "in_practice": "Extraverts often gravitate to client-facing, team-leadership, or public-speaking roles. Introverts often excel in research, analysis, strategy, or deep-focus roles."
    },
    {
        "dimension": "Anxiety / Neuroticism",
        "what_it_measures": "Emotional sensitivity, stress reactivity, and tendency to experience worry, tension, or self-doubt.",
        "high_score": "Heightened awareness of risk, prone to self-criticism and anticipatory worry. May experience stress physically (tension, restlessness).",
        "low_score": "Calm under pressure, emotionally steady, quick to recover from setbacks. Rarely ruminates or second-guesses.",
        "in_practice": "High scorers often bring vigilance and thoroughness but may need structured recovery time. Low scorers thrive in high-pressure environments but may overlook emotional signals."
    },
    {
        "dimension": "Receptivity",
        "what_it_measures": "How open you are to people and to ideas — empathy, sensitivity, imagination, and openness to change. Reported as two sub-clusters where the data supports it.",
        "high_score": "Empathetic, imaginative, values-led. Tunes into others' experiences. Drawn to new ideas, creative pursuits, and people-centred work.",
        "low_score": "Practical, data-driven, unsentimental. Focuses on what works rather than what feels right. Comfortable with concrete, established approaches and tough decisions.",
        "in_practice": "High receptivity suits counselling, design, R&D, and people-centred roles. Lower receptivity suits operations, engineering, finance, and roles requiring decisive practicality. The two sub-clusters — Interpersonal Receptivity (warmth + sensitivity) and Intellectual Receptivity (imagination + openness to change) — can move independently and are reported separately."
    },
    {
        "dimension": "Independence",
        "what_it_measures": "Your autonomy in thought and action — how much you rely on your own judgement versus seeking consensus and direction.",
        "high_score": "Self-directing, questioning, comfortable challenging authority. Prefers to form own opinions before consulting others.",
        "low_score": "Collaborative, consensus-seeking, respectful of established approaches. Values group harmony and shared decision-making.",
        "in_practice": "Highly independent people thrive in entrepreneurial, consultancy, or R&D settings. Those lower may prefer structured teams with clear reporting lines."
    },
    {
        "dimension": "Self-Control",
        "what_it_measures": "How you regulate impulses, organise your environment, and maintain focus on long-term goals.",
        "high_score": "Disciplined, methodical, detail-oriented. Follows processes, keeps commitments, plans ahead systematically.",
        "low_score": "Flexible, spontaneous, comfortable with ambiguity. Adapts quickly but may struggle with sustained routine.",
        "in_practice": "High self-control supports compliance, project management, and quality assurance roles. Lower self-control suits creative, agile, or rapid-response environments."
    },
]

P150_GLOSSARY_16PF = [
    {"factor": "A", "name": "Warmth", "low": "Reserved, detached, cool", "high": "Warm, outgoing, attentive to others",
     "practice": "High scorers create rapport easily and are drawn to people-facing roles. Low scorers may prefer task-focused or technical work."},
    {"factor": "C", "name": "Emotional Stability", "low": "Reactive, changeable, affected by feelings", "high": "Emotionally stable, adaptive, mature",
     "practice": "High scorers remain composed under pressure. Low scorers are more emotionally responsive, which can be both empathetic and draining."},
    {"factor": "E", "name": "Dominance", "low": "Cooperative, avoids conflict, accommodating", "high": "Assertive, competitive, forceful",
     "practice": "High scorers naturally step into leadership and negotiation. Low scorers excel in supportive, diplomatic, or mediating roles."},
    {"factor": "F", "name": "Liveliness", "low": "Serious, restrained, careful", "high": "Spontaneous, enthusiastic, energetic",
     "practice": "High scorers inject energy and positivity into teams. Low scorers bring steadiness, caution, and reflective depth."},
    {"factor": "G", "name": "Rule-Consciousness", "low": "Expedient, non-conforming, flexible about rules", "high": "Conscientious, conforming, moralistic",
     "practice": "High scorers uphold standards and processes reliably. Low scorers may challenge bureaucracy and prefer autonomy."},
    {"factor": "H", "name": "Social Boldness", "low": "Shy, timid, threat-sensitive", "high": "Bold, venturesome, thick-skinned",
     "practice": "High scorers handle public visibility and criticism with ease. Low scorers may need encouragement in high-exposure situations."},
    {"factor": "I", "name": "Sensitivity", "low": "Tough-minded, self-reliant, utilitarian", "high": "Tender-hearted, intuitive, sentimental",
     "practice": "High scorers tune into emotional nuance and aesthetics. Low scorers focus on outcomes and practicality."},
    {"factor": "L", "name": "Vigilance", "low": "Trusting, accepting, unsuspecting", "high": "Suspicious, sceptical, watchful",
     "practice": "High scorers are alert to risk and deception — valuable in audit, legal, or security. Low scorers build trust quickly but may overlook red flags."},
    {"factor": "M", "name": "Abstractedness", "low": "Grounded, practical, solution-focused", "high": "Imaginative, absent-minded, idea-oriented",
     "practice": "High scorers generate novel ideas and strategic visions. Low scorers execute reliably and stay focused on deliverables."},
    {"factor": "N", "name": "Privateness", "low": "Forthright, open, genuine", "high": "Discreet, diplomatic, private",
     "practice": "High scorers navigate politics and confidentiality well. Low scorers build trust through transparency and authenticity."},
    {"factor": "O", "name": "Apprehension", "low": "Self-assured, unworried, complacent", "high": "Worried, self-doubting, guilt-prone",
     "practice": "High scorers are thorough and self-critical — useful for quality roles. Low scorers project confidence and resilience."},
    {"factor": "Q1", "name": "Openness to Change", "low": "Traditional, attached to familiar", "high": "Experimenting, open-minded, freethinking",
     "practice": "High scorers drive innovation and transformation. Low scorers provide stability, institutional memory, and continuity."},
    {"factor": "Q2", "name": "Self-Reliance", "low": "Group-oriented, affiliative, joiners", "high": "Self-sufficient, solitary, resourceful",
     "practice": "High scorers work independently with minimal oversight. Low scorers thrive in collaborative, team-based environments."},
    {"factor": "Q3", "name": "Perfectionism", "low": "Flexible, tolerates disorder, undisciplined", "high": "Organised, compulsive, controlled",
     "practice": "High scorers deliver polished, precise work. Low scorers adapt to changing priorities and tolerate ambiguity."},
    {"factor": "Q4", "name": "Tension", "low": "Relaxed, placid, patient", "high": "Driven, impatient, high-strung",
     "practice": "High scorers are urgency-driven and highly motivated. Low scorers maintain perspective and avoid burnout under sustained demand."},
]

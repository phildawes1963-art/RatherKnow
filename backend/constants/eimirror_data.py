"""
EI Mirror Question Bank
140 items, 4 domains, 14 sub-dimensions (Jun 2026: Self-Awareness expanded
from 1 → 3 sub-dimensions / 10 → 30 items per external psychometric review)
5-point Likert: 1=Never, 2=Rarely, 3=Sometimes, 4=Often, 5=Always
~33% reverse-scored items to reduce social desirability bias.
Reverse items: score = 6 - raw_value (5->1, 4->2, 3->3, 2->4, 1->5)
"""

EIMIRROR_SCALE = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]

EIMIRROR_DOMAINS = {
    "self_awareness": {
        "name": "Self-Awareness",
        "description": "The ability to recognise and understand your own emotions, drives, and their effect on others.",
        "sub_dimensions": {
            "emotional_self_awareness": {
                "name": "Emotional Self-Awareness",
                "description": "Recognising your emotions and their effects as they happen.",
                "items": list(range(1, 11))
            },
            "emotional_expression": {
                "name": "Emotional Expression",
                "description": "Communicating your feelings to others in healthy, appropriate ways.",
                "items": list(range(121, 131))
            },
            "values_clarity": {
                "name": "Values & Identity Clarity",
                "description": "Knowing what matters to you and what guides your decisions under pressure.",
                "items": list(range(131, 141))
            },
        }
    },
    "self_management": {
        "name": "Self-Management",
        "description": "The ability to control or redirect disruptive impulses and moods, and the propensity to suspend judgement and think before acting.",
        "sub_dimensions": {
            "emotional_self_control": {
                "name": "Emotional Self-Control",
                "description": "Keeping disruptive emotions and impulses in check.",
                "items": list(range(11, 21))
            },
            "adaptability": {
                "name": "Adaptability",
                "description": "Flexibility in handling change and navigating uncertainty.",
                "items": list(range(21, 31))
            },
            "achievement_orientation": {
                "name": "Achievement Orientation",
                "description": "Striving to improve or meet a standard of personal excellence.",
                "items": list(range(31, 41))
            },
            "positive_outlook": {
                "name": "Positive Outlook",
                "description": "Seeing the positive in events, expecting the best from life.",
                "items": list(range(41, 51))
            }
        }
    },
    "social_awareness": {
        "name": "Social Awareness",
        "description": "The ability to understand the emotional makeup of other people and how to treat them according to their emotional reactions.",
        "sub_dimensions": {
            "empathy": {
                "name": "Empathy",
                "description": "Sensing others' feelings and perspectives, and taking an active interest in their concerns.",
                "items": list(range(51, 61))
            },
            "organisational_awareness": {
                "name": "Organisational Awareness",
                "description": "Reading group dynamics, understanding social networks and unspoken norms.",
                "items": list(range(61, 71))
            }
        }
    },
    "relationship_management": {
        "name": "Relationship Management",
        "description": "Proficiency in managing relationships and building networks, and an ability to find common ground and build rapport.",
        "sub_dimensions": {
            "influence": {
                "name": "Influence",
                "description": "Wielding effective tactics for persuasion and building consensus.",
                "items": list(range(71, 81))
            },
            "coach_and_mentor": {
                "name": "Coach & Mentor",
                "description": "Supporting others' development and helping them reach their potential.",
                "items": list(range(81, 91))
            },
            "conflict_management": {
                "name": "Conflict Management",
                "description": "Negotiating and resolving disagreements with tact and diplomacy.",
                "items": list(range(91, 101))
            },
            "teamwork": {
                "name": "Teamwork",
                "description": "Working with others towards shared goals and creating group synergy.",
                "items": list(range(101, 111))
            },
            "inspirational_leadership": {
                "name": "Inspirational Leadership",
                "description": "Inspiring and guiding individuals and groups through authenticity and purpose.",
                "items": list(range(111, 121))
            }
        }
    }
}

# ==================== QUESTIONS ====================
# reverse=True means agreeing with the statement indicates LOWER EI
# Scoring: reverse items use 6 - raw_value
EIMIRROR_QUESTIONS = [
    # === SELF-AWARENESS: Emotional Self-Awareness (1-10) ===
    {"id": 1, "text": "I notice the physical signs in my body that tell me an emotion is building.", "domain": "self_awareness", "sub": "emotional_self_awareness", "reverse": False},
    {"id": 2, "text": "I recognize how my current mood influences my decisions.", "domain": "self_awareness", "sub": "emotional_self_awareness", "reverse": False},
    {"id": 3, "text": "I am usually unaware of physical signs like a tight chest or racing heart when my emotions shift.", "domain": "self_awareness", "sub": "emotional_self_awareness", "reverse": True},
    {"id": 4, "text": "I am aware of the specific triggers that make me lose my cool.", "domain": "self_awareness", "sub": "emotional_self_awareness", "reverse": False},
    {"id": 5, "text": "I understand the deeper values that drive my emotional reactions.", "domain": "self_awareness", "sub": "emotional_self_awareness", "reverse": False},
    {"id": 6, "text": "I notice when my mood starts to negatively affect the people around me.", "domain": "self_awareness", "sub": "emotional_self_awareness", "reverse": False},
    {"id": 7, "text": "I tend to avoid thinking about my personal flaws and emotional limits.", "domain": "self_awareness", "sub": "emotional_self_awareness", "reverse": True},
    {"id": 8, "text": "I understand why I react defensively to certain types of criticism.", "domain": "self_awareness", "sub": "emotional_self_awareness", "reverse": False},
    {"id": 9, "text": "I often don't realise my emotions are clouding my judgement until it's too late.", "domain": "self_awareness", "sub": "emotional_self_awareness", "reverse": True},
    {"id": 10, "text": "I am aware of what my facial expressions and body language say to others.", "domain": "self_awareness", "sub": "emotional_self_awareness", "reverse": False},

    # === SELF-MANAGEMENT: Emotional Self-Control (11-20) ===
    {"id": 11, "text": "I stay level-headed during high-stakes personal situations.", "domain": "self_management", "sub": "emotional_self_control", "reverse": False},
    {"id": 12, "text": "I often say things I later regret when I am angry.", "domain": "self_management", "sub": "emotional_self_control", "reverse": True},
    {"id": 13, "text": "I can think rationally even when I am feeling intense sadness or fear.", "domain": "self_management", "sub": "emotional_self_control", "reverse": False},
    {"id": 14, "text": "I keep my composure even when I am feeling judged by others.", "domain": "self_management", "sub": "emotional_self_control", "reverse": False},
    {"id": 15, "text": "I wait until I've calmed down before addressing a personal grievance.", "domain": "self_management", "sub": "emotional_self_control", "reverse": False},
    {"id": 16, "text": "I find it hard to keep my temper around difficult people.", "domain": "self_management", "sub": "emotional_self_control", "reverse": True},
    {"id": 17, "text": "I have techniques to pull myself out of a bad mood.", "domain": "self_management", "sub": "emotional_self_control", "reverse": False},
    {"id": 18, "text": "I tend to snap at people when I am under pressure.", "domain": "self_management", "sub": "emotional_self_control", "reverse": True},
    {"id": 19, "text": "I manage my anxiety so it doesn't stop me from trying new things.", "domain": "self_management", "sub": "emotional_self_control", "reverse": False},
    {"id": 20, "text": "I stay consistent in my values even when things are going wrong.", "domain": "self_management", "sub": "emotional_self_control", "reverse": False},

    # === SELF-MANAGEMENT: Adaptability (21-30) ===
    {"id": 21, "text": "I am quick to change my plans when life throws a curveball.", "domain": "self_management", "sub": "adaptability", "reverse": False},
    {"id": 22, "text": "I feel very anxious when I don't know how a situation will turn out.", "domain": "self_management", "sub": "adaptability", "reverse": True},
    {"id": 23, "text": "I can handle multiple life stressors at once without burning out.", "domain": "self_management", "sub": "adaptability", "reverse": False},
    {"id": 24, "text": "I find new ways to achieve my goals if the original path is blocked.", "domain": "self_management", "sub": "adaptability", "reverse": False},
    {"id": 25, "text": "I tend to stick with what I know rather than trying new things.", "domain": "self_management", "sub": "adaptability", "reverse": True},
    {"id": 26, "text": "I can get along with people whose worldviews are the opposite of mine.", "domain": "self_management", "sub": "adaptability", "reverse": False},
    {"id": 27, "text": "I see life changes as exciting growth opportunities rather than threats.", "domain": "self_management", "sub": "adaptability", "reverse": False},
    {"id": 28, "text": "I am willing to admit I was wrong when I get better information.", "domain": "self_management", "sub": "adaptability", "reverse": False},
    {"id": 29, "text": "It takes me a long time to recover after a personal failure or rejection.", "domain": "self_management", "sub": "adaptability", "reverse": True},
    {"id": 30, "text": "I can adjust my social style to fit into different groups or settings.", "domain": "self_management", "sub": "adaptability", "reverse": False},

    # === SELF-MANAGEMENT: Achievement Orientation (31-40) ===
    {"id": 31, "text": "I hold myself to high standards in my personal projects.", "domain": "self_management", "sub": "achievement_orientation", "reverse": False},
    {"id": 32, "text": "I am always looking for ways to improve my health or skills.", "domain": "self_management", "sub": "achievement_orientation", "reverse": False},
    {"id": 33, "text": "I avoid taking risks even when it could help me achieve something I care about.", "domain": "self_management", "sub": "achievement_orientation", "reverse": True},
    {"id": 34, "text": "I set clear, meaningful goals for my personal future.", "domain": "self_management", "sub": "achievement_orientation", "reverse": False},
    {"id": 35, "text": "I ask friends I trust for feedback on how I can be a better person.", "domain": "self_management", "sub": "achievement_orientation", "reverse": False},
    {"id": 36, "text": "I often give in to short-term impulses at the expense of my long-term goals.", "domain": "self_management", "sub": "achievement_orientation", "reverse": True},
    {"id": 37, "text": "I keep trying to master a skill even when it gets difficult.", "domain": "self_management", "sub": "achievement_orientation", "reverse": False},
    {"id": 38, "text": "I take full responsibility for the outcomes of my life choices.", "domain": "self_management", "sub": "achievement_orientation", "reverse": False},
    {"id": 39, "text": "I set myself stretch goals that push beyond what's comfortable.", "domain": "self_management", "sub": "achievement_orientation", "reverse": False},
    {"id": 40, "text": "I am easily distracted from my goals by things that don't really matter.", "domain": "self_management", "sub": "achievement_orientation", "reverse": True},

    # === SELF-MANAGEMENT: Positive Outlook (41-50) ===
    {"id": 41, "text": "I tend to see the silver lining in most difficult situations.", "domain": "self_management", "sub": "positive_outlook", "reverse": False},
    {"id": 42, "text": "When I face a new challenge, I usually expect things to go wrong.", "domain": "self_management", "sub": "positive_outlook", "reverse": True},
    {"id": 43, "text": "I view personal mistakes as necessary steps to wisdom.", "domain": "self_management", "sub": "positive_outlook", "reverse": False},
    {"id": 44, "text": "I remain optimistic about my long-term future.", "domain": "self_management", "sub": "positive_outlook", "reverse": False},
    {"id": 45, "text": "I spend more time thinking about solutions than complaining about problems.", "domain": "self_management", "sub": "positive_outlook", "reverse": False},
    {"id": 46, "text": "I help my friends see the positive side of their struggles.", "domain": "self_management", "sub": "positive_outlook", "reverse": False},
    {"id": 47, "text": "I tend to assume people have selfish motives until they prove otherwise.", "domain": "self_management", "sub": "positive_outlook", "reverse": True},
    {"id": 48, "text": "I find small things to be grateful for every single day.", "domain": "self_management", "sub": "positive_outlook", "reverse": False},
    {"id": 49, "text": "I can find the humor in a situation even when I'm stressed.", "domain": "self_management", "sub": "positive_outlook", "reverse": False},
    {"id": 50, "text": "I doubt my ability to bounce back when life gets really tough.", "domain": "self_management", "sub": "positive_outlook", "reverse": True},

    # === SOCIAL AWARENESS: Empathy (51-60) ===
    {"id": 51, "text": "I can sense when a friend is upset before they say a word.", "domain": "social_awareness", "sub": "empathy", "reverse": False},
    {"id": 52, "text": "I often catch myself thinking about my own response instead of truly listening.", "domain": "social_awareness", "sub": "empathy", "reverse": True},
    {"id": 53, "text": "I understand the reasoning behind why someone feels hurt.", "domain": "social_awareness", "sub": "empathy", "reverse": False},
    {"id": 54, "text": "I can step into someone else's shoes to see their perspective.", "domain": "social_awareness", "sub": "empathy", "reverse": False},
    {"id": 55, "text": "I am sensitive to the different cultural or family backgrounds of others.", "domain": "social_awareness", "sub": "empathy", "reverse": False},
    {"id": 56, "text": "I notice when a stranger or acquaintance needs help or support.", "domain": "social_awareness", "sub": "empathy", "reverse": False},
    {"id": 57, "text": "When someone is upset, my first instinct is to jump in and try to fix things for them.", "domain": "social_awareness", "sub": "empathy", "reverse": True},
    {"id": 58, "text": "I can feel the vibe of a social gathering as soon as I enter.", "domain": "social_awareness", "sub": "empathy", "reverse": False},
    {"id": 59, "text": "I am someone people feel safe opening up to.", "domain": "social_awareness", "sub": "empathy", "reverse": False},
    {"id": 60, "text": "I often make decisions without considering how they will affect the people around me.", "domain": "social_awareness", "sub": "empathy", "reverse": True},

    # === SOCIAL AWARENESS: Organisational Awareness (61-70) ===
    {"id": 61, "text": "I can tell who really holds influence in a group, regardless of job titles.", "domain": "social_awareness", "sub": "organisational_awareness", "reverse": False},
    {"id": 62, "text": "I know who the natural leaders are in my family or friend group.", "domain": "social_awareness", "sub": "organisational_awareness", "reverse": False},
    {"id": 63, "text": "I sometimes feel out of touch with what matters most to my community or social circle.", "domain": "social_awareness", "sub": "organisational_awareness", "reverse": True},
    {"id": 64, "text": "I can see the social politics at play during family gatherings.", "domain": "social_awareness", "sub": "organisational_awareness", "reverse": False},
    {"id": 65, "text": "I know how to ask for help from the right people to get things done.", "domain": "social_awareness", "sub": "organisational_awareness", "reverse": False},
    {"id": 66, "text": "I pick up on shifts in the mood of a group before they're openly discussed.", "domain": "social_awareness", "sub": "organisational_awareness", "reverse": False},
    {"id": 67, "text": "I have accidentally brought up sensitive topics in social settings without realising it.", "domain": "social_awareness", "sub": "organisational_awareness", "reverse": True},
    {"id": 68, "text": "I notice the hidden tensions between people in a group.", "domain": "social_awareness", "sub": "organisational_awareness", "reverse": False},
    {"id": 69, "text": "I can predict how a change in a group (like a breakup or move) will affect everyone.", "domain": "social_awareness", "sub": "organisational_awareness", "reverse": False},
    {"id": 70, "text": "I tend to be unaware of the social issues that are affecting people around me.", "domain": "social_awareness", "sub": "organisational_awareness", "reverse": True},

    # === RELATIONSHIP MANAGEMENT: Influence (71-80) ===
    {"id": 71, "text": "I am persuasive when I want to convince friends of a plan.", "domain": "relationship_management", "sub": "influence", "reverse": False},
    {"id": 72, "text": "I can help a group reach a compromise that makes everyone happy.", "domain": "relationship_management", "sub": "influence", "reverse": False},
    {"id": 73, "text": "I tend to communicate the same way regardless of who I am talking to.", "domain": "relationship_management", "sub": "influence", "reverse": True},
    {"id": 74, "text": "I build deep trust with people to gain their support.", "domain": "relationship_management", "sub": "influence", "reverse": False},
    {"id": 75, "text": "I am seen as a reliable source of advice in my social circle.", "domain": "relationship_management", "sub": "influence", "reverse": False},
    {"id": 76, "text": "I can get people excited about a cause or event I care about.", "domain": "relationship_management", "sub": "influence", "reverse": False},
    {"id": 77, "text": "I use both logic and heart to help people see my point of view.", "domain": "relationship_management", "sub": "influence", "reverse": False},
    {"id": 78, "text": "My social circle is quite small and I find it hard to build new connections.", "domain": "relationship_management", "sub": "influence", "reverse": True},
    {"id": 79, "text": "I am good at negotiating chores or plans with my partner or family.", "domain": "relationship_management", "sub": "influence", "reverse": False},
    {"id": 80, "text": "I struggle to change people's minds once they've formed a negative impression of me.", "domain": "relationship_management", "sub": "influence", "reverse": True},

    # === RELATIONSHIP MANAGEMENT: Coach & Mentor (81-90) ===
    {"id": 81, "text": "I give encouragement that helps my friends reach their goals.", "domain": "relationship_management", "sub": "coach_and_mentor", "reverse": False},
    {"id": 82, "text": "I take a genuine interest in the personal growth of people I love.", "domain": "relationship_management", "sub": "coach_and_mentor", "reverse": False},
    {"id": 83, "text": "I rarely take the time to share my skills or knowledge with others.", "domain": "relationship_management", "sub": "coach_and_mentor", "reverse": True},
    {"id": 84, "text": "I am quick to praise the small wins of the people in my life.", "domain": "relationship_management", "sub": "coach_and_mentor", "reverse": False},
    {"id": 85, "text": "I avoid pushing my friends to try new things in case it upsets them.", "domain": "relationship_management", "sub": "coach_and_mentor", "reverse": True},
    {"id": 86, "text": "I am a patient listener when someone is trying to figure their life out.", "domain": "relationship_management", "sub": "coach_and_mentor", "reverse": False},
    {"id": 87, "text": "I can tell someone a hard truth in a way that is kind.", "domain": "relationship_management", "sub": "coach_and_mentor", "reverse": False},
    {"id": 88, "text": "I tend to take over and solve other people's problems for them.", "domain": "relationship_management", "sub": "coach_and_mentor", "reverse": True},
    {"id": 89, "text": "I share my life lessons openly to help others avoid the same mistakes.", "domain": "relationship_management", "sub": "coach_and_mentor", "reverse": False},
    {"id": 90, "text": "I act as a safe space for others to vent their worries.", "domain": "relationship_management", "sub": "coach_and_mentor", "reverse": False},

    # === RELATIONSHIP MANAGEMENT: Conflict Management (91-100) ===
    {"id": 91, "text": "I handle arguments with my partner or family with patience.", "domain": "relationship_management", "sub": "conflict_management", "reverse": False},
    {"id": 92, "text": "I tend to avoid awkward conversations even when they are necessary.", "domain": "relationship_management", "sub": "conflict_management", "reverse": True},
    {"id": 93, "text": "I hear out both sides of a story before taking a side in a friend's fight.", "domain": "relationship_management", "sub": "conflict_management", "reverse": False},
    {"id": 94, "text": "I am a peacemaker when there is tension in the room.", "domain": "relationship_management", "sub": "conflict_management", "reverse": False},
    {"id": 95, "text": "I stay objective when two people I care about are disagreeing.", "domain": "relationship_management", "sub": "conflict_management", "reverse": False},
    {"id": 96, "text": "I let small annoyances build up until they become major problems.", "domain": "relationship_management", "sub": "conflict_management", "reverse": True},
    {"id": 97, "text": "I care more about the relationship than being right in an argument.", "domain": "relationship_management", "sub": "conflict_management", "reverse": False},
    {"id": 98, "text": "I help people focus on what they do agree on.", "domain": "relationship_management", "sub": "conflict_management", "reverse": False},
    {"id": 99, "text": "I tend to shut down or walk away when conversations get emotionally difficult.", "domain": "relationship_management", "sub": "conflict_management", "reverse": True},
    {"id": 100, "text": "I am the first to apologize or reach out after a disagreement.", "domain": "relationship_management", "sub": "conflict_management", "reverse": False},

    # === RELATIONSHIP MANAGEMENT: Teamwork (101-110) ===
    {"id": 101, "text": "I contribute my fair share to household tasks or group plans.", "domain": "relationship_management", "sub": "teamwork", "reverse": False},
    {"id": 102, "text": "I enjoy collaborating with others on shared projects (like a trip).", "domain": "relationship_management", "sub": "teamwork", "reverse": False},
    {"id": 103, "text": "In group settings, I tend to let the louder voices dominate without speaking up.", "domain": "relationship_management", "sub": "teamwork", "reverse": True},
    {"id": 104, "text": "I actively work to create a sense of belonging in my groups.", "domain": "relationship_management", "sub": "teamwork", "reverse": False},
    {"id": 105, "text": "I celebrate our success rather than just my own.", "domain": "relationship_management", "sub": "teamwork", "reverse": False},
    {"id": 106, "text": "I encourage the shy people in a group to share their ideas.", "domain": "relationship_management", "sub": "teamwork", "reverse": False},
    {"id": 107, "text": "I am reliable \u2014 if I say I'll be there, I am there.", "domain": "relationship_management", "sub": "teamwork", "reverse": False},
    {"id": 108, "text": "I find it hard to go along with group decisions when I disagree.", "domain": "relationship_management", "sub": "teamwork", "reverse": True},
    {"id": 109, "text": "I rarely take the initiative to organise social events or bring people together.", "domain": "relationship_management", "sub": "teamwork", "reverse": True},
    {"id": 110, "text": "I am a loyal friend who stands by people in tough times.", "domain": "relationship_management", "sub": "teamwork", "reverse": False},

    # === RELATIONSHIP MANAGEMENT: Inspirational Leadership (111-120) ===
    {"id": 111, "text": "I live in a way that makes others want to be better versions of themselves.", "domain": "relationship_management", "sub": "inspirational_leadership", "reverse": False},
    {"id": 112, "text": "I practice what I preach when it comes to my values.", "domain": "relationship_management", "sub": "inspirational_leadership", "reverse": False},
    {"id": 113, "text": "I tend to hold back when a group needs someone to step up and take charge.", "domain": "relationship_management", "sub": "inspirational_leadership", "reverse": True},
    {"id": 114, "text": "I help others see the deeper meaning in their daily lives.", "domain": "relationship_management", "sub": "inspirational_leadership", "reverse": False},
    {"id": 115, "text": "I am the calm in the storm when my family or friends face a crisis.", "domain": "relationship_management", "sub": "inspirational_leadership", "reverse": False},
    {"id": 116, "text": "I help people see their own potential when they are feeling low.", "domain": "relationship_management", "sub": "inspirational_leadership", "reverse": False},
    {"id": 117, "text": "I sometimes put on a different persona depending on who I am with.", "domain": "relationship_management", "sub": "inspirational_leadership", "reverse": True},
    {"id": 118, "text": "I give others the confidence to take charge of their own lives.", "domain": "relationship_management", "sub": "inspirational_leadership", "reverse": False},
    {"id": 119, "text": "I find it difficult to mobilise others to help even when someone clearly needs it.", "domain": "relationship_management", "sub": "inspirational_leadership", "reverse": True},
    {"id": 120, "text": "I inspire others simply by staying true to my own vision of a good life.", "domain": "relationship_management", "sub": "inspirational_leadership", "reverse": False},
    # ============================================================
    # Self-Awareness expansion (Jun 2026) — 20 items added in response to
    # external psychometric review (which flagged Self-Awareness as
    # under-represented with only 1 sub-dimension / 10 items vs other
    # domains' 20-50). Brings EI Mirror to 140 items total.
    # ============================================================
    # Sub: Emotional Expression (121-130) — communicating feelings appropriately
    {"id": 121, "text": "I find it easy to tell colleagues when I'm feeling overwhelmed.", "domain": "self_awareness", "sub": "emotional_expression", "reverse": False},
    {"id": 122, "text": "I often suppress my feelings rather than share them, even with people I trust.", "domain": "self_awareness", "sub": "emotional_expression", "reverse": True},
    {"id": 123, "text": "I can express disagreement without being aggressive or shutting down.", "domain": "self_awareness", "sub": "emotional_expression", "reverse": False},
    {"id": 124, "text": "I struggle to find the right words when I want to talk about how I feel.", "domain": "self_awareness", "sub": "emotional_expression", "reverse": True},
    {"id": 125, "text": "I let people know when something is bothering me, rather than letting it build up.", "domain": "self_awareness", "sub": "emotional_expression", "reverse": False},
    {"id": 126, "text": "I tend to hide my emotions at work, even from people who would understand.", "domain": "self_awareness", "sub": "emotional_expression", "reverse": True},
    {"id": 127, "text": "I can say 'I'm not OK' to someone I trust when that's the truth.", "domain": "self_awareness", "sub": "emotional_expression", "reverse": False},
    {"id": 128, "text": "Expressing affection or appreciation openly makes me uncomfortable.", "domain": "self_awareness", "sub": "emotional_expression", "reverse": True},
    {"id": 129, "text": "I show vulnerability when it's appropriate to the relationship.", "domain": "self_awareness", "sub": "emotional_expression", "reverse": False},
    {"id": 130, "text": "When I'm upset, I prefer to deal with it alone rather than talk it through.", "domain": "self_awareness", "sub": "emotional_expression", "reverse": True},
    # Sub: Values & Identity Clarity (131-140) — knowing what matters under pressure
    {"id": 131, "text": "I have a clear sense of the principles that guide my decisions.", "domain": "self_awareness", "sub": "values_clarity", "reverse": False},
    {"id": 132, "text": "I sometimes find myself doing things that conflict with what I actually believe in.", "domain": "self_awareness", "sub": "values_clarity", "reverse": True},
    {"id": 133, "text": "I know what I would never compromise on, even under pressure.", "domain": "self_awareness", "sub": "values_clarity", "reverse": False},
    {"id": 134, "text": "It's hard for me to articulate what I stand for if someone asks me directly.", "domain": "self_awareness", "sub": "values_clarity", "reverse": True},
    {"id": 135, "text": "My choices in life feel aligned with what genuinely matters to me.", "domain": "self_awareness", "sub": "values_clarity", "reverse": False},
    {"id": 136, "text": "I make decisions that please others even when they don't sit right with me.", "domain": "self_awareness", "sub": "values_clarity", "reverse": True},
    {"id": 137, "text": "I can name two or three values that have shaped my biggest life decisions.", "domain": "self_awareness", "sub": "values_clarity", "reverse": False},
    {"id": 138, "text": "I'm not really sure what I want from my work or my life.", "domain": "self_awareness", "sub": "values_clarity", "reverse": True},
    {"id": 139, "text": "When my values are challenged, I can articulate them clearly without becoming defensive.", "domain": "self_awareness", "sub": "values_clarity", "reverse": False},
    {"id": 140, "text": "I feel like I'm living someone else's version of a good life rather than my own.", "domain": "self_awareness", "sub": "values_clarity", "reverse": True},
]

# Set of reverse-scored item IDs for quick lookup
EIMIRROR_REVERSE_ITEMS = {q["id"] for q in EIMIRROR_QUESTIONS if q.get("reverse")}

# Score interpretation bands
SCORE_BANDS = {
    (1.0, 2.0): {"label": "Developing", "description": "This area represents a significant growth opportunity."},
    (2.0, 3.0): {"label": "Emerging", "description": "You show some awareness here but there is room for meaningful development."},
    (3.0, 3.5): {"label": "Competent", "description": "You demonstrate a solid foundation in this area."},
    (3.5, 4.0): {"label": "Proficient", "description": "You perform well in this area and it is becoming a strength."},
    (4.0, 5.01): {"label": "Exemplary", "description": "This is a clear strength \u2014 your answers sit at the top of this scale."},
}

def get_score_band(score):
    for (low, high), band in SCORE_BANDS.items():
        if low <= score < high:
            return band
    return SCORE_BANDS[(4.0, 5.01)]

EIMIRROR_GLOSSARY = {
    "Self-Awareness": {
        "what": "The ability to recognise and understand your own emotions, drives, and their effect on others.",
        "high": "You have a clear understanding of your emotional landscape. You know what triggers you, why you feel the way you do, and how your moods ripple outward.",
        "low": "You may find it hard to name specific feelings or notice how your mood affects those around you. Building a regular self-reflection practice can help.",
    },
    "Self-Management": {
        "what": "The ability to control or redirect disruptive impulses and moods, and to adapt to changing circumstances.",
        "high": "You handle stress, setbacks, and change with composure. You channel emotions productively and maintain a positive, resilient outlook.",
        "low": "You may struggle with impulsivity, adapting to change, or maintaining motivation. Developing coping strategies and goal-setting habits can support growth.",
    },
    "Social Awareness": {
        "what": "The ability to understand the emotional makeup of other people and the dynamics of social groups.",
        "high": "You are highly attuned to others' feelings, can read a room, and understand group dynamics intuitively.",
        "low": "You may miss social cues or struggle to understand others' perspectives. Practicing active listening and empathy exercises can build this skill.",
    },
    "Relationship Management": {
        "what": "Proficiency in managing relationships and building networks, resolving conflicts, and inspiring others.",
        "high": "You build strong, trusting relationships. You navigate conflict with grace, inspire others, and create a sense of belonging.",
        "low": "You may find it difficult to influence, mentor, or collaborate effectively. Focusing on communication skills and conflict resolution techniques can help.",
    },
}

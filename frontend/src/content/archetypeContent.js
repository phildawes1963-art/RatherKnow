// Mirror Index brand tokens (spec: MIRROR~2.MD).
// Used by the new mirror-index/* pages. Pure constants — no React.

export const MI_COLORS = {
  indigoDeep: '#1E2A47',   // Primary brand — dark surfaces, nav, footer
  indigoSoft: '#3A4A6E',   // Secondary surfaces / hover
  ivory: '#FAF6F0',        // Primary background
  ivoryWarm: '#F2EBE0',    // Card surfaces, subtle dividers
  copper: '#B87D4B',       // Primary accent — CTAs, archetype highlights
  copperDeep: '#8B5A30',   // Hover/pressed copper
  sage: '#7BA098',         // Success / green flags
  terracotta: '#C8794A',   // Shadow content / caution
  graphite: '#2A2A2A',     // Primary text on ivory
  graphiteSoft: '#5A5A5A', // Secondary text
  ivoryOnDark: '#F2EBE0',  // Text on indigo
  warmGrey: '#D9D2C7',     // Hairlines, borders
};

// Inline-style helpers so child components can apply tokens without a global theme provider.
export const miStyle = {
  bg: { backgroundColor: MI_COLORS.ivory },
  bgWarm: { backgroundColor: MI_COLORS.ivoryWarm },
  bgDark: { backgroundColor: MI_COLORS.indigoDeep, color: MI_COLORS.ivoryOnDark },
  text: { color: MI_COLORS.graphite },
  textSoft: { color: MI_COLORS.graphiteSoft },
  textCopper: { color: MI_COLORS.copper },
  border: { borderColor: MI_COLORS.warmGrey },
  cardWarm: { backgroundColor: MI_COLORS.ivoryWarm, borderColor: MI_COLORS.warmGrey },
};

export const MI_FONTS = {
  display: "'Cormorant Garamond', Georgia, serif",
  body: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
};

// Six archetypes — v2 copy deck (Mirror-Index-v2-Copy-Deck).
// Renames: Adventurer → The Voyager, Visionary → The Torchbearer (internal keys unchanged).
// "How love lands" replaces the Love Languages mapping. Each archetype answers
// "drawn to" (its shadow) AND "drawn to you" (who chases it).
export const ARCHETYPE_CONTENT = {
  rock: {
    id: 'rock',
    name: 'The Rock',
    tagline: 'Stability & Tradition',
    symbol: 'I',
    accent: MI_COLORS.copper,
    epithet: 'Loyalty you can set your watch by.',
    selfDescription: 'You are the partner people count on. You show up, you follow through, you believe love is a daily practice rather than a grand gesture. Around you, life gets calmer — and that is not boring, it is the foundation everything else stands on.',
    shadowSide: 'The loyalty that steadies everyone can curdle into rigidity. You can mistake routine for love and silence for peace — staying too long in relationships that quietly stopped working, because leaving feels like breaking your word.',
    idealPartner: 'Someone who values continuity, honours commitments, and will not test your patience for sport.',
    greenFlags: ['Keeps small promises', 'Punctual without being told', 'Speaks well of past partners'],
    howLoveLands: 'Through acts: the lift from the station, the bill quietly paid, the promise kept when it was inconvenient.',
    shadowArchetype: 'empath',
    shadowArchetypeNote: 'The Empath. Their emotional depth offers what your discipline suppresses — but unaddressed, it becomes a rescue dynamic: you carry the relationship, and they expect you to.',
    drawnToYou: 'Voyagers and Torchbearers chase you — you are the ground under their flight. It works when they value your steadiness; it hurts when they only borrow it.',
  },
  challenger: {
    id: 'challenger',
    name: 'The Challenger',
    tagline: 'Intellect & Growth',
    symbol: 'II',
    accent: MI_COLORS.indigoSoft,
    epithet: 'Growth as devotion.',
    selfDescription: 'You love people into their potential. Debate is not conflict to you — it is attention, the most flattering kind. A partner who grows beside you is a partner you never get bored of, and you extend them the same courtesy.',
    shadowSide: 'The sharpening that feels like devotion to you can feel like assessment to them. You can turn the kitchen into a seminar room, and mistake a partner\u2019s need for comfort as an argument you are winning.',
    idealPartner: 'Someone who matches your curiosity, holds their own in a disagreement, and doesn\u2019t flinch when you push.',
    greenFlags: ['Curious about ideas, not just topics', 'Changes their mind when shown evidence', 'Asks questions back'],
    howLoveLands: 'Words about who they are becoming: seen progress, named. You noticed — that is the whole gift.',
    shadowArchetype: 'diplomat',
    shadowArchetypeNote: 'The Diplomat. Their agreeableness feels like peace at first — then the debates you live for stop coming, and the boredom arrives wearing resentment\u2019s coat.',
    drawnToYou: 'Empaths are pulled toward your clarity — your cool head promises steadiness for their weather. Handle that pull gently; it goes wrong when your rationality makes them feel \u201ctoo much\u201d.',
  },
  empath: {
    id: 'empath',
    name: 'The Empath',
    tagline: 'Connection & Intimacy',
    symbol: 'III',
    accent: MI_COLORS.terracotta,
    epithet: 'Feels the room before it speaks.',
    selfDescription: 'You notice the mood shift before the door closes. Vulnerability doesn\u2019t frighten you — it is the whole point, the way strangers become each other\u2019s people. You make hard conversations feel safe, which is rarer than any grand romance.',
    shadowSide: 'Attunement without boundaries becomes absorption. You can feel a partner\u2019s weather so vividly you forget to check your own, and call over-giving \u201clove\u201d until the resentment bill arrives.',
    idealPartner: 'Someone who can hold space for your depth without flinching, and who matches your emotional honesty without making you the translator.',
    greenFlags: ['Names their feelings', 'Apologises specifically', 'Notices when you\u2019re off without you saying'],
    howLoveLands: 'Presence and touch: the hand on the back, the question asked twice because the first answer was \u201cfine\u201d.',
    shadowArchetype: 'challenger',
    shadowArchetypeNote: 'The Challenger. Their brilliance feels like being chosen by clarity itself — until their cool read of your warm world leaves you feeling like a problem to be solved.',
    drawnToYou: 'Rocks are drawn to your depth — you are the feeling they never let themselves have. Beautiful when mutual; exhausting when you become their only emotional outlet.',
  },
  adventurer: {
    id: 'adventurer',
    name: 'The Voyager',
    tagline: 'Social & Lifestyle',
    symbol: 'IV',
    accent: MI_COLORS.sage,
    epithet: 'Turns ordinary days into stories.',
    selfDescription: 'Life with you has a plot. You say \u201clet\u2019s just go\u201d and mean it, order the strange thing on the menu, and believe the best memories are the unplanned ones. Love, for you, expands when it is shared with someone game.',
    shadowSide: 'The hunger for the next chapter can read as flight from this one. You can confuse restlessness with growth — and partners can love the adventure while quietly wondering if they are a destination or a stop.',
    idealPartner: 'Someone who brings their own energy to the trip, not just a willingness to come along.',
    greenFlags: ['Has their own plans, not just yours', 'Recovers well from disruption', 'Honest about what they don\u2019t enjoy'],
    howLoveLands: 'Time, spent generously: the trip planned around what you mentioned once, the phone face-down on the table.',
    shadowArchetype: 'rock',
    shadowArchetypeNote: 'The Rock. Their steadiness feels like home after all that motion — until home starts to feel like a schedule, and the walls you wanted become the walls you pace.',
    drawnToYou: 'Here is the honest answer: no archetype chases the Voyager by shadow. Nobody falls for you by accident — people choose you with their eyes open, for the life you make bigger. That is rarer than being someone\u2019s blind spot.',
  },
  diplomat: {
    id: 'diplomat',
    name: 'The Diplomat',
    tagline: 'Harmony & Communication',
    symbol: 'V',
    accent: MI_COLORS.indigoDeep,
    epithet: 'Says the hard thing, gently.',
    selfDescription: 'Anyone can keep the peace by going quiet. You do something harder: you say the difficult thing in a way that can be heard. You repair what others rupture, apologise like you mean it, and never weaponise the archive.',
    shadowSide: 'The skill that resolves everyone else\u2019s conflict can become a way of never having your own. You can broker so much peace that nobody — including you — knows what you actually want.',
    idealPartner: 'Someone who can hold their own ground without making you the negotiator, and who notices when you\u2019ve gone quiet.',
    greenFlags: ['Says \u201cI don\u2019t agree\u201d kindly', 'Asks what you want, not just what works for you', 'Names tension early'],
    howLoveLands: 'Being genuinely heard: the pause before the response, the \u201cI understand why\u201d that is actually true.',
    shadowArchetype: 'visionary',
    shadowArchetypeNote: 'The Torchbearer. Their certainty is magnetic when you hold every side of every question — until their mission starts reading your flexibility as absence of substance.',
    drawnToYou: 'Challengers seek you out — your grace under fire is the worthiest opponent their debates ever met. It works when they respect the skill; it fails when they mistake gentleness for surrender.',
  },
  visionary: {
    id: 'visionary',
    name: 'The Torchbearer',
    tagline: 'Purpose & Ambition',
    symbol: 'VI',
    accent: MI_COLORS.copperDeep,
    epithet: 'Love in service of a bigger arc.',
    selfDescription: 'Your life points somewhere, and love is a partnership in that direction. You include your partner in the dream and take their dreams personally — their ambitions get a champion the day you commit.',
    shadowSide: 'The mission can eat the marriage. Comfort is easy to sacrifice on purpose\u2019s altar — and a partner can feel like crew on your voyage rather than the reason for it.',
    idealPartner: 'Someone with their own arc — running parallel, not adjacent.',
    greenFlags: ['Names what they\u2019re building', 'Asks about yours, specifically', 'Has follow-through on small commitments'],
    howLoveLands: 'Belief, out loud — and service to the dream: they showed up to your thing, and they meant it.',
    shadowArchetype: 'rock',
    shadowArchetypeNote: 'The Rock. Their groundedness promises a base camp for the climb — until their practicality starts pricing your dreams, and \u201cbe realistic\u201d becomes the phrase you flinch at.',
    drawnToYou: 'Diplomats gravitate to your flame — your certainty is restful for someone who can argue every side. Guard it: the dynamic sours if your drive starts treating their care as weakness.',
  },
};

export const ARCHETYPE_ORDER = ['rock', 'challenger', 'empath', 'adventurer', 'diplomat', 'visionary'];

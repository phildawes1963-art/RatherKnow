// Shared theme tokens, instrument metadata, anonymous session store.
import { TIER_CHIPS, TIER_STATEMENTS } from '../content/register';

export const C = {
  bg: '#F6F6F2',
  ink: '#1C1C18',
  inkSoft: '#3B3B34',
  surface: '#FFFFFF',
  line: '#E4E4DE',
  muted: '#6E6E66',
  sage: '#7E8E77',
  slate: '#5B7284',
  ochre: '#C8AE93',
};

export const API = process.env.REACT_APP_BACKEND_URL;

export { TIER_STATEMENTS };

export const INSTRUMENTS = [
  {
    key: 'essential',
    name: 'Essential Mirror',
    tagline: 'Who you are — and who you say you want',
    blurb:
      'Fifty statements answered twice: once as yourself, once as the partner you think you want. The gap between the two — the Delta — is the measurement. You get a named pattern, its shadow, and the distance between your self and your stated want.',
    items: '50 questions × 2 lenses',
    minutes: 'About 25 minutes',
    tier: TIER_CHIPS.essential,
    accent: C.slate,
  },
  {
    key: 'closeness',
    name: 'Closeness Mirror',
    tagline: "How you are when you're close to someone",
    blurb:
      'Thirty-six statements measuring two things: how much reassurance you need, and how easily closeness comes. The result is a single point on two axes — no boxes, no types, no labels. New, and honest about it.',
    items: '36 statements',
    minutes: 'About 5 minutes',
    tier: TIER_CHIPS.closeness,
    accent: C.sage,
    isNew: true,
  },
  {
    key: 'personality',
    name: 'Personality Mirror',
    tagline: 'A validated five-factor profile',
    blurb:
      'A validated five-factor personality measure: fifteen primary factors and five global dimensions, scored against calibrated norms. The established backbone the other mirrors are cross-checked against.',
    items: '130 statements',
    minutes: '15–20 minutes',
    tier: TIER_CHIPS.personality,
    accent: C.ochre,
  },
  {
    key: 'eq',
    name: 'EI Mirror',
    tagline: 'How you handle what you feel',
    blurb:
      'A Goleman four-domain emotional intelligence read: self-awareness, self-management, social awareness and relationship management — the capacities that decide how love actually goes, whatever else they decide along the way.',
    items: '140 statements',
    minutes: '15–20 minutes',
    tier: TIER_CHIPS.eq,
    accent: C.slate,
  },
];

export const instrumentByKey = Object.fromEntries(INSTRUMENTS.map((i) => [i.key, i]));

// ---- Anonymous session store (localStorage) ----
const KEY = 'mi2.sessions';

export function readSessions() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || {};
  } catch {
    return {};
  }
}

export function saveSession(instrument, sessionId) {
  const all = readSessions();
  all[instrument] = sessionId;
  localStorage.setItem(KEY, JSON.stringify(all));
}

export function clearSession(instrument) {
  const all = readSessions();
  delete all[instrument];
  localStorage.setItem(KEY, JSON.stringify(all));
}

// Reflections (Flag Check) held apart from assessments — never blended (FR-N8).
const RKEY = 'mi2.reflections';

export function readReflections() {
  try {
    return JSON.parse(localStorage.getItem(RKEY)) || {};
  } catch {
    return {};
  }
}

export function saveReflection(kind, id) {
  const all = readReflections();
  all[kind] = id;
  localStorage.setItem(RKEY, JSON.stringify(all));
}

export function clearReflection(kind) {
  const all = readReflections();
  delete all[kind];
  localStorage.setItem(RKEY, JSON.stringify(all));
}

export function describeVsMidpoint(value) {
  if (value == null) return 'not scored';
  if (value >= 5.5) return 'clearly above the middle';
  if (value >= 4.5) return 'a little above the middle';
  if (value > 3.5) return 'around the middle';
  if (value > 2.5) return 'a little below the middle';
  return 'clearly below the middle';
}

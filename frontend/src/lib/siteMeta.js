// Site-wide metadata contract — mirrors docs/route_table.json.
export const SITE = {
  name: 'Rather Know',
  descriptor: 'a study of how you choose',
  baseUrl: 'https://ratherknow.com',
  ogImage: '/og/ratherknow-og.png',
};

export const NOINDEX_PREFIXES = ['/mirrors', '/results/'];

export function isIndexable(pathname) {
  return !NOINDEX_PREFIXES.some((p) => pathname === p || pathname.startsWith(p));
}

export const ARCH_SLUG_BY_KEY = {
  rock: 'the-rock',
  challenger: 'the-challenger',
  empath: 'the-empath',
  adventurer: 'the-voyager',
  diplomat: 'the-diplomat',
  visionary: 'the-torchbearer',
};

export const ARCH_KEY_BY_SLUG = Object.fromEntries(
  Object.entries(ARCH_SLUG_BY_KEY).map(([k, v]) => [v, k])
);

export const ARCHETYPE_SEO = {
  'the-rock': {
    title: 'The Rock — relationship archetype',
    description:
      'Loyal, steady, the safe harbour — and secretly drawn to the Empath who unsettles it all. The Rock archetype honestly told: gifts, shadow, green flags.',
    h1: 'The Rock — stability and tradition',
  },
  'the-challenger': {
    title: 'The Challenger — relationship archetype',
    description:
      "Growth as devotion — and a weakness for partners who won't argue back. The Challenger archetype: gifts, shadow, and who is quietly drawn to you.",
    h1: 'The Challenger — intellect and growth',
  },
  'the-empath': {
    title: 'The Empath — relationship archetype',
    description:
      'Feels the room before it speaks — and falls for the one who makes feeling seem like too much. The Empath archetype: gifts, shadow, green flags.',
    h1: 'The Empath — connection and intimacy',
  },
  'the-voyager': {
    title: 'The Voyager — relationship archetype',
    description:
      'Turns ordinary days into stories — then falls for stability and calls it home until it feels like a schedule. The Voyager archetype, honestly told.',
    h1: 'The Voyager — social and lifestyle',
  },
  'the-diplomat': {
    title: 'The Diplomat — relationship archetype',
    description:
      'Says the hard thing gently — and is drawn to the certainty that mistakes gentleness for weakness. The Diplomat archetype: gifts, shadow, green flags.',
    h1: 'The Diplomat — harmony and communication',
  },
  'the-torchbearer': {
    title: 'The Torchbearer — relationship archetype',
    description:
      'Love in service of a bigger arc — and a shadow-pull toward the practical partner who prices the dream. The Torchbearer archetype, honestly told.',
    h1: 'The Torchbearer — purpose and ambition',
  },
};

export const breadcrumbJsonLd = (crumbs) => ({
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: crumbs.map((c, i) => ({
    '@type': 'ListItem',
    position: i + 1,
    name: c.name,
    ...(c.path ? { item: `${SITE.baseUrl}${c.path}` } : {}),
  })),
});

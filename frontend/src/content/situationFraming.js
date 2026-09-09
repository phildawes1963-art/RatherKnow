// Report framing by situation. Interpretation, not a claim — kept out of the locked register
// on purpose, and never a different score: the same numbers, read for where you actually are.
export const SITUATION_LENS = {
  single_dating: {
    label: 'Single & dating',
    lead: 'Read this before the next one, not after.',
    essential:
      'You’re reading this with the next person still theoretical, which is the most useful moment there is. The gap below is something to watch for rather than something to explain: it names the qualities you are most likely to over-weight early, and the ones you are most likely to forgive too quickly. Watch for the shadow arriving as chemistry — the pull is strongest when nothing has gone wrong yet.',
    closeness:
      'Where you sit on these two axes is what the early weeks will feel like from the inside — how quickly you need a signal back, and how long it takes before closeness stops being work. Neither position is a fault; both change what you should be watching for in someone new.',
    personality:
      'Use this as a filter on your own story rather than on other people. The factors that sit furthest from the middle are the ones you’ll notice missing in a partner within a month.',
    eq:
      'These are the capacities that decide how the early months go once novelty stops carrying the conversation. The lowest domain is the one that will show up first, usually as “we just kept misreading each other”.',
    nudge: { label: 'The Closeness Mirror — 5 minutes', to: '/take/closeness' },
  },
  in_relationship: {
    label: 'In a relationship',
    lead: 'Read this as a conversation, not a verdict.',
    essential:
      'You’re reading this from inside something, so one caution first: the gap below is not a scorecard on your partner, and this instrument never asked about them. It describes what you carry and what you say you want. Where those two diverge is usually where the same argument keeps restarting — which makes it a thing to say out loud rather than a thing to conclude.',
    closeness:
      'These two dimensions are answered about relationships in general, so a single relationship can sit somewhere quite different. Read it as your default setting — the thing you bring into the room — rather than as a description of the one you’re in.',
    personality:
      'The useful move here isn’t comparison. It’s noticing which of your own factors your relationship is currently asking you to suppress, and whether that’s a season or a habit.',
    eq:
      'Relationship management is the domain that does the most work when two people are already committed. Read your lowest domain as the skill your relationship is most likely to be paying for.',
    nudge: { label: 'The EI Mirror — how you handle what you feel', to: '/take/eq' },
  },
  post_breakup: {
    label: 'Post-breakup',
    lead: 'Read this while you can still see it.',
    essential:
      'The window after an ending is short and unusually clear — the pattern is visible from outside for a while, and then the next person makes it invisible again. So read the gap below as the thing that keeps being true across relationships, not as evidence about the one that just ended. Some endings are pattern. Some are only timing, and no instrument can tell those apart for you.',
    closeness:
      'Right after an ending, both of these can read more extreme than your settled position — reassurance especially. That doesn’t make it wrong; it makes it worth taking again in a few months and comparing. Nothing here is a diagnosis of what went wrong.',
    personality:
      'This is the steadiest thing you’ll read today: personality doesn’t move much with a breakup, so use it as ground. It describes who you were before the ending and who you’ll still be after it.',
    eq:
      'Self-management usually takes the hit in the weeks after an ending. Read a low domain as a state you’re in rather than a trait you have — and take it again when the dust settles.',
    nudge: { label: 'Read: don’t waste the breakup', to: '/learn/dont-waste-the-breakup' },
  },
};

export const SITUATION_DISCLAIMER =
  'The scoring never changes with your situation — the numbers above are the same either way. Only the framing does.';

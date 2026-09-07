import { Link } from 'react-router-dom';
import Shell from '../components/Shell';
import { TIER_STATEMENTS } from '../lib/mirrorTheme';
import { TIER_CHIPS, DISCLAIMER, FLAG, ATTRIBUTION, METHOD_NOTE } from '../content/register';
import { breadcrumbJsonLd } from '../lib/siteMeta';

const SECTIONS = [
  {
    key: 'essential',
    name: 'Essential Mirror',
    measures:
      'Your relational pattern, read through two lenses: fifty statements answered as yourself, then fifty answered as the partner you say you want. Output: a primary and secondary archetype per lens, the per-pattern gaps between them (the Delta), a mapped shadow attraction, and five dimension scores per lens.',
    scoring:
      'Each of six archetypes is keyed to ten statements. Answers map to a 0–10 contribution per statement (with reverse-keyed items inverted), summed per archetype and expressed against the maximum. The Delta is the arithmetic difference between the two lenses — no weighting, no hidden model.',
    weaknesses: [
      'The items and the archetype framework are ours; their psychometric properties are still being established.',
      'Early internal-consistency estimates only (archetype core: exploratory, n≈90, α 0.68–0.74). No test–retest data yet.',
      'The archetype layer is interpretive. Treat it as a structured conversation starter, not a measurement of a settled trait.',
    ],
  },
  {
    key: 'closeness',
    name: 'Closeness Mirror (MI-AS-36)',
    measures:
      'Two continuous dimensions from the adult attachment literature — presented as Reassurance (how much ongoing signal you need that things are all right) and Closeness (how easily intimacy itself comes). Output: one point on two axes. Never a four-box type.',
    scoring:
      '36 items, 7-point scale, fixed presentation order, balanced keying (9 forward / 9 reverse per dimension). Reverse items are inverted (8 − answer); each dimension is the mean of its 18 items, prorated for up to two missing answers and refused beyond that. Four validity checks run on every submission — an instructed-response item, three consistency pairs, longest identical-answer run, and a time floor — and they set a confidence label rather than deleting anything.',
    weaknesses: [
      'The questions are ours, written for this instrument, and their properties are still being established — no reliability figures exist yet.',
      'No population norms, which is why no bands, categories or percentiles are shown. When pilot statistics exist (n = 300), computed values will be published with sample size and date.',
      'Answered about relationships in general; a single relationship can sit somewhere quite different.',
    ],
  },
  {
    key: 'personality',
    name: 'Personality Mirror',
    measures:
      'A validated five-factor personality profile: fifteen primary factors, each placed on a 1–10 scale (sten), aggregated into five global dimensions. Positions, not bands: no reference sample is documented for the band boundaries, so we do not report them as bands.',
    scoring:
      '130 Likert items (120 personality + 10 social-desirability checks). Reverse-keyed items inverted, factor raw scores converted to stens via the frozen band table, global dimensions computed as weighted factor composites. The band table carries no documented reference sample, which is why the reader is shown a position within their own profile rather than a band — see the scoring specification. Two validity indices — social desirability and central tendency — are reported, never hidden.',
    weaknesses: [
      'Self-report: it measures how you see yourself, honestly answered or not.',
      'The band table has no documented reference sample (no n, no group, no date), so nothing here is reported as high or low relative to other people. Results are comparable within a bank version.',
      'The five global dimensions are derived, not measured: each is a weighted sum of the primary factors — global = 5.5 + Σ(weight × (sten − 5.5)) — so a composite can only be as good as the primaries feeding it, and it can legitimately differ from another 16PF-style report that uses different weights or different norms. Every report here publishes the exact equation behind each dimension.',
      'Two composites are known to sit further from other 16PF-style instruments than the rest: Receptivity and Self-Control. We publish that residual rather than fitting the equation to a single sheet — a gain calibrated to one person would bake one person’s distortion into everyone’s score. It is flagged on the result itself.',
      'Receptivity is the same axis that other reports publish as Tough-Mindedness, read from the opposite end: a high Receptivity and a low Tough-Mindedness are the same finding, not a contradiction.',
    ],
  },
  {
    key: 'eq',
    name: 'EI Mirror',
    measures:
      'Emotional intelligence across Goleman’s four domains — self-awareness, self-management, social awareness, relationship management — with fourteen sub-dimensions.',
    scoring:
      '140 Likert items, roughly a third reverse-keyed. Sub-dimension and domain scores are straight means on the 1–5 scale, and that is what the reader is shown. The band words this instrument used to carry — High, Moderate, Developing, at cut-offs of 4.0 and 3.0 — have been withdrawn: a band word implies a standard, and no reference sample is documented for those cut-offs.',
    weaknesses: [
      'A self-perception read, not an ability test — it tells you how you believe you operate.',
      'The mean of your own answers in a domain is a fact; how that compares with other people is not something this instrument can tell you.',
    ],
  },
  {
    key: 'everyday',
    name: 'Everyday Mirror',
    measures:
      'Where you sit on seven dimensions of ordinary life — pace, people, order, novelty, money, recovery and time together — and then which of them you would actually need a partner to share.',
    scoring:
      'Forty-nine forced choices in two blocks. Block A places you on each dimension by making you pick between two ways of living rather than rate a statement about yourself; Block B asks which dimensions you would protect, and ranks them by how often you chose to protect them. Positions are reported as a lean toward one named end, never as a score out of anything, and the priority ranking is ordinal — first, second, third — with no interval claim attached to the gaps.',
    weaknesses: [
      'The desirability pre-test has not been run. Forced choice controls for the tendency to agree with everything, but only if the two options are equally attractive to say — and we have not yet tested whether one option in each pair sounds more flattering than the other. Until we have, a lean may partly reflect which answer sounded better rather than which one is true of you. This is the least-established instrument here and it is the one whose method we are publishing in most detail, deliberately.',
      'It is the only instrument here that can contradict what you said about yourself elsewhere, which is the point of it — but a contradiction is a finding to sit with, not an error to resolve in favour of one side.',
      'Seven dimensions of ordinary life are not all of ordinary life. The bank was written to cover the differences that recur, not to be exhaustive.',
    ],
  },
];

export default function Methodology() {
  return (
    <Shell
      title="Methodology"
      description="Every instrument's evidence tier, scoring, and stated weaknesses — in full."
      jsonLd={breadcrumbJsonLd([{ name: 'Rather Know', path: '/' }, { name: 'Methodology' }])}
    >
      <div className="max-w-3xl mx-auto px-5 sm:px-8 py-14 sm:py-20">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Methodology</p>
        <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="methodology-title">
          What each mirror can claim — and what it can’t.
        </h1>
        <p className="mt-5 text-base text-[#3B3B34] leading-relaxed">
          We would rather say less and be able to prove it. Every instrument here carries a published evidence tier.
          <strong> Established</strong> means the measure has a real evidence base and calibrated scoring.
          <strong> Developmental</strong> means the constructs are well replicated but the questions are ours and their
          properties are still being established. The word “validated” is reserved: it is used only of Established
          instruments, and never of the product as a whole.
        </p>

        <section className="mt-10 border-y border-[#1C1C18] py-8" data-testid="methodology-note">
          <h2 className="mi2-serif text-2xl text-[#1C1C18]">{METHOD_NOTE.heading}</h2>
          <div className="mt-5 space-y-4 text-base text-[#3B3B34] leading-relaxed max-w-2xl">
            <p>{METHOD_NOTE.lead}</p>
            <p>{METHOD_NOTE.established}</p>
            <p>{METHOD_NOTE.developmental}</p>
            <p data-testid="methodology-note-pause">{METHOD_NOTE.stopped_comparing}</p>
            <p className="text-[#1C1C18]">{METHOD_NOTE.removed_not_caveated}</p>
            <p>{METHOD_NOTE.what_is_left}</p>
            <p data-testid="methodology-note-provisional">{METHOD_NOTE.still_rests_on}</p>
            <p data-testid="methodology-note-delivered">{METHOD_NOTE.already_delivered}</p>
            <p className="text-[#1C1C18]">{METHOD_NOTE.if_ever}</p>
          </div>
        </section>

        <div className="mt-10 space-y-8">
          {SECTIONS.map((s) => {
            const tier = TIER_CHIPS[s.key];
            return (
              <section key={s.key} className="bg-white border border-[#E4E4DE] p-7" data-testid={`methodology-${s.key}`}>
                <div className="flex items-start justify-between gap-4">
                  <h2 className="mi2-serif text-2xl text-[#1C1C18]">{s.name}</h2>
                  <span
                    data-testid={`methodology-tier-${s.key}`}
                    className={`text-[11px] uppercase tracking-[0.1em] px-2 py-0.5 border shrink-0 ${
                      tier === 'Established' ? 'bg-[#1C1C18] text-[#F6F6F2] border-[#1C1C18]' : 'text-[#3B3B34] border-[#B9B9B0]'
                    }`}
                  >
                    {tier}
                  </span>
                </div>
                <p className="mt-2 text-sm text-[#5B7284]">{TIER_STATEMENTS[s.key]}</p>
                <div className="mt-5 space-y-4 text-sm text-[#3B3B34] leading-relaxed">
                  <div>
                    <p className="text-xs uppercase tracking-[0.12em] text-[#6E6E66] mb-1">What it measures</p>
                    <p>{s.measures}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.12em] text-[#6E6E66] mb-1">How it’s scored</p>
                    <p>{s.scoring}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.12em] text-[#6E6E66] mb-1">Stated weaknesses</p>
                    <ul className="list-disc pl-5 space-y-1">
                      {s.weaknesses.map((w, i) => <li key={i}>{w}</li>)}
                    </ul>
                  </div>
                </div>
              </section>
            );
          })}
        </div>

        <section className="mt-12 bg-white border border-[#E4E4DE] p-7" data-testid="methodology-flag-check">
          <div className="flex items-start justify-between gap-4">
            <h2 className="mi2-serif text-2xl text-[#1C1C18]">Flag Check</h2>
            <span className="text-[11px] uppercase tracking-[0.1em] px-2 py-0.5 border text-[#6E6E66] border-[#D5D5CD] shrink-0">Not an instrument</span>
          </div>
          <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">
            {FLAG.descriptor.charAt(0).toUpperCase() + FLAG.descriptor.slice(1)}. It produces no score, no band and
            carries no evidence tier — deliberately. The moment it produced a number it would become an audit of a
            relationship, and it would inherit an evidence burden it cannot carry. Its output is wording selected by
            simple observable rules from your own answers, and every question is about you — none asks you to
            characterise another person.
          </p>
        </section>

        <section className="mt-12 bg-[#1C1C18] text-[#F6F6F2] p-8" data-testid="methodology-refusals">
          <h2 className="mi2-serif text-2xl">What we refuse to produce.</h2>
          <ul className="mt-5 space-y-3 text-sm text-[#F6F6F2]/85 leading-relaxed">
            <li>— No compatibility percentages, and no invented numbers of any kind.</li>
            <li>— No verdict on any person who hasn’t taken the assessment. The instruments read you, never them.</li>
            <li>— No clinical labels — of you or of anyone you describe.</li>
            <li>— No promises about other people, and no timelines.</li>
            <li>— No bands or categories before norms exist to justify them.</li>
          </ul>
          <p className="mt-6 text-sm text-[#F6F6F2]/70">{DISCLAIMER}</p>
        </section>

        <p className="mt-10 text-xs text-[#6E6E66]" data-testid="methodology-attribution">
          {ATTRIBUTION}
        </p>

        <div className="mt-6 border border-[#E4E4DE] bg-white px-6 py-5" data-testid="methodology-spec-link">
          <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">The full working</p>
          <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed max-w-2xl">
            Every formula, item count, keying rule, band table and threshold behind the instruments and the Flag
            Check — including exactly which of them a percentile could honestly be derived from, and which of them
            have no population norms at all.
          </p>
          <a
            href="/docs/ratherknow-scoring-spec.pdf"
            target="_blank"
            rel="noreferrer"
            data-testid="methodology-spec-download"
            className="mt-3 inline-block text-sm underline underline-offset-4 text-[#1C1C18] hover:opacity-70"
          >
            Read the scoring specification (PDF) →
          </a>
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-5">
          <Link to="/take/essential" data-testid="methodology-cta" className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85">
            Start with the Essential Mirror
          </Link>
          <Link to="/safety" className="text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
            The safety page →
          </Link>
        </div>
      </div>
    </Shell>
  );
}

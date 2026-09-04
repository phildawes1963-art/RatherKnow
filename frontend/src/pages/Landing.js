import { Link } from 'react-router-dom';
import Shell from '../components/Shell';
import { INSTRUMENTS } from '../lib/mirrorTheme';
import { SITE } from '../lib/siteMeta';
import { FLAG, SAFETY, REGISTER } from '../content/register';

const Tier = ({ tier }) => (
  <span
    data-testid={`tier-chip-${tier.toLowerCase()}`}
    className={`inline-block text-[11px] uppercase tracking-[0.1em] px-2 py-0.5 border ${
      tier === 'Established' ? 'bg-[#1C1C18] text-[#F6F6F2] border-[#1C1C18]' : 'text-[#3B3B34] border-[#B9B9B0]'
    }`}
  >
    {tier}
  </span>
);

const PRICES = [
  {
    key: 'archetype',
    name: 'Your Archetype',
    price: 'Free',
    time: '13 minutes',
    body: 'The Essential Mirror. Your archetype, your Delta, and the full description. No card.',
    live: true,
  },
  {
    key: 'everyday',
    name: 'The Everyday Reading',
    price: '$14',
    time: '+7 minutes',
    body: 'Forty-nine either/or choices about ordinary life: where you sit, and what you would actually protect.',
    live: false,
  },
  {
    key: 'full',
    name: 'The Full Reading',
    price: '$29',
    time: '+40 minutes',
    body: 'The Personality, EI and Closeness Mirrors, and the whole thing read together rather than reported separately.',
    live: false,
  },
];

export default function Landing() {
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: SITE.name,
    url: SITE.baseUrl,
    description: 'Four psychometric instruments that measure how you choose in relationships.',
  };

  return (
    <Shell
      title=""
      description="Four psychometric instruments that measure how you choose in relationships. Free to start, and honest about their own evidence."
      jsonLd={jsonLd}
    >
      {/* 1 · Hero — one job: start the Essential Mirror. One time figure, and it's the first step's. */}
      <section className="max-w-6xl mx-auto px-5 sm:px-8 pt-16 pb-14 sm:pt-24 sm:pb-20">
        <div className="grid gap-12 lg:grid-cols-[1.15fr_0.85fr] lg:gap-16 items-center">
          <div>
            <p className="mi2-fade text-xs uppercase tracking-[0.18em] text-[#6E6E66]">
              Rather Know — {SITE.descriptor}
            </p>
            <h1
              className="mi2-fade mi2-serif mt-5 text-4xl sm:text-5xl lg:text-6xl leading-[1.05] tracking-tight text-[#1C1C18]"
              data-testid="hero-h1"
            >
              For people who’d rather <em className="text-[#5B7284]">know</em> than be reassured.
            </h1>
            <p className="mi2-fade-slow mt-7 text-base md:text-lg text-[#3B3B34] leading-relaxed max-w-xl">
              Four instruments that measure the one thing you actually control in a relationship: how you choose. Not
              who’s out there. Who’s doing the choosing.
            </p>
            <div className="mi2-fade-slow mt-9 flex flex-wrap items-center gap-4">
              <Link
                to="/register?next=%2Ftake%2Fessential"
                data-testid="hero-start"
                className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85"
              >
                Start free — 13 minutes
              </Link>
            </div>
            <p className="mi2-fade-slow mt-4 text-sm text-[#6E6E66]">
              No card. No profiles. Nobody else involved.
            </p>
          </div>

          {/* People buy reports by looking at reports. This is page one of a real one. */}
          <figure className="mi2-fade-slow" data-testid="hero-report-figure">
            <div className="border border-[#E4E4DE] bg-white p-2 shadow-[0_18px_50px_-24px_rgba(28,28,24,0.35)]">
              <img
                src="/images/sample-report-page.png"
                alt="Page one of an Essential Mirror report, showing the reader's archetype, the partner they described, and the Delta between them."
                width="1241"
                height="1754"
                loading="eager"
                data-testid="hero-report-image"
                className="w-full h-auto"
              />
            </div>
            <figcaption className="mt-3 text-xs text-[#6E6E66]">
              Page one of an Essential Mirror reading.{' '}
              <Link to="/samples" data-testid="hero-samples-link" className="underline underline-offset-4 hover:text-[#1C1C18]">
                See a full sample reading →
              </Link>
            </figcaption>
          </figure>
        </div>
      </section>

      {/* 2 · What you actually get */}
      <section className="border-y border-[#E4E4DE] bg-white/60">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-16 sm:py-20 grid gap-10 md:grid-cols-[1fr_1.1fr]">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">What you actually get</p>
            <h2 className="mi2-serif mt-3 text-2xl md:text-3xl text-[#1C1C18]" data-testid="what-you-get-h2">
              Thirteen minutes gets you this.
            </h2>
          </div>
          <div className="space-y-5 text-base text-[#3B3B34] leading-relaxed" data-testid="what-you-get-list">
            <p>
              A named pattern, and what it means in practice — not a label, a description you can check against your
              own life.
            </p>
            <p>The gap between who you are and who you say you want, measured and shown.</p>
            <p>
              The two qualities you’ll over-weight in someone else, and the one you’ll fail to notice because it comes
              free to you.
            </p>
            <p>And an honest account of what none of it can tell you.</p>

            <blockquote
              className="mi2-serif border-l-2 border-[#B9B9B0] pl-5 py-1 text-lg leading-relaxed text-[#1C1C18]"
              data-testid="report-excerpt"
            >
              “You reach hardest for steadiness. It’s the quality you’ll notice quickly in someone, weight heavily, and
              forgive a good deal to keep hold of. That’s worth knowing early rather than late.”
            </blockquote>
            <Link
              to="/samples"
              data-testid="samples-link"
              className="inline-block text-sm underline underline-offset-4 text-[#1C1C18] hover:opacity-70"
            >
              See a full sample reading →
            </Link>
          </div>
        </div>
      </section>

      {/* 3 · The one idea */}
      <section className="max-w-6xl mx-auto px-5 sm:px-8 py-16 sm:py-24">
        <div className="grid gap-10 md:grid-cols-[1fr_1.3fr] items-start">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">The one idea</p>
            <h2 className="mi2-serif mt-3 text-2xl md:text-3xl text-[#1C1C18]">The Delta.</h2>
            {/* Two dots and the line between them — the same visual the report uses. */}
            <div className="mt-8 max-w-xs" aria-hidden="true" data-testid="delta-diagram">
              <div className="relative h-px bg-[#B9B9B0]">
                <span className="absolute -top-[5px] left-0 w-2.5 h-2.5 rounded-full bg-[#1C1C18]" />
                <span className="absolute -top-[5px] right-0 w-2.5 h-2.5 rounded-full bg-[#5B7284]" />
              </div>
              <div className="mt-3 flex justify-between text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">
                <span>You</span>
                <span>Who you say you want</span>
              </div>
              <p className="mt-3 text-xs text-[#6E6E66]">The distance is the measurement.</p>
            </div>
          </div>
          <div className="space-y-5 text-base text-[#3B3B34] leading-relaxed">
            <p>
              You answer the same fifty questions twice — once as yourself, once as the partner you think you want.
            </p>
            <p>
              The distance between those two sets of answers is the measurement. It turns <em>“am I too picky?”</em>{' '}
              into something you can actually look at: not an opinion, and not a percentage pulled from the air — a
              distance, on a scale we show you the workings of.
            </p>
            <p className="text-[#1C1C18]">
              Most reports tell you what you’re like. This one tells you what you do with what you’re like.
            </p>
          </div>
        </div>
      </section>

      {/* 4 · What it refuses. Proof lands after desire, not before it. */}
      <section className="bg-[#1C1C18] text-[#F6F6F2]">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-16 sm:py-20 grid gap-10 sm:grid-cols-[1.1fr_1fr]">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-[#F6F6F2]/50">What it refuses</p>
            <p className="mi2-serif mt-4 text-2xl sm:text-3xl leading-snug" data-testid="honest-band">
              We cannot find you love. Nobody can.
            </p>
            <p className="mt-4 text-sm md:text-base text-[#F6F6F2]/75 leading-relaxed max-w-lg">
              Every promise here is about you, because you’re the only person we can honestly make one about.
            </p>
          </div>
          <ul className="space-y-3 text-sm text-[#F6F6F2]/85 self-center" data-testid="refusals-list">
            {[
              'No matching, no profiles, no other people.',
              'No compatibility score. Not now, not later.',
              'No types, no boxes, no quadrants.',
              'No predictions about how anything will go.',
              'No urgency, no countdowns, nothing expires.',
              'Every instrument publishes its own evidence tier, including the ones still being established.',
            ].map((line) => (
              <li key={line} className="flex gap-3">
                <span className="text-[#7E8E77]">—</span> {line}
              </li>
            ))}
            <li className="pt-2">
              <Link to="/promise" data-testid="promise-link" className="inline-block text-sm underline underline-offset-4 text-[#F6F6F2]/80 hover:text-[#F6F6F2]">
                Read the promise in full — seven promises, ten refusals →
              </Link>
            </li>
          </ul>
        </div>
      </section>

      {/* 5 · How it's built. No per-instrument doors: there is one way in. */}
      <section id="instruments" className="max-w-6xl mx-auto px-5 sm:px-8 py-16 sm:py-24">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">How it’s built</p>
        <h2 className="mi2-serif mt-3 text-2xl md:text-3xl text-[#1C1C18]">Four mirrors, cross-checked.</h2>
        <p className="mt-4 text-base text-[#3B3B34] max-w-2xl leading-relaxed">
          Each measures something different. Where they agree, that’s signal. Where they disagree, that’s a finding —
          and usually the more interesting one.
        </p>

        <dl className="mt-10 divide-y divide-[#E4E4DE] border-y border-[#E4E4DE]">
          {INSTRUMENTS.map((ins, i) => (
            <div
              key={ins.key}
              data-testid={`instrument-${ins.key}`}
              className="mi2-fade grid gap-2 sm:grid-cols-[minmax(0,15rem)_1fr_auto] sm:items-baseline py-5"
              style={{ animationDelay: `${i * 70}ms` }}
            >
              <dt className="mi2-serif text-lg text-[#1C1C18] flex items-center gap-3">
                {ins.name}
                <Tier tier={ins.tier} />
              </dt>
              <dd className="text-sm text-[#3B3B34] leading-relaxed">{ins.blurb}</dd>
              <dd className="text-xs text-[#6E6E66] sm:text-right whitespace-nowrap">{ins.items}</dd>
            </div>
          ))}
        </dl>

        <p className="mt-6 text-sm text-[#3B3B34] max-w-2xl leading-relaxed">
          Two are established instruments with published norms. Two are ours, built on established research, and still
          being established — we label them that way on every page they appear.{' '}
          <Link to="/methodology" data-testid="methodology-link" className="underline underline-offset-4 text-[#1C1C18] hover:opacity-70">
            How it’s scored, in full →
          </Link>
        </p>
        <p className="mt-6 text-sm text-[#6E6E66] max-w-2xl leading-relaxed">
          There’s one door in, and it’s the Essential Mirror. The rest unlock in sequence afterwards, in a fixed order
          that’s the same for everyone.
        </p>
      </section>

      {/* 6 · What it costs. A visitor who senses a paywall and can't find it becomes suspicious. */}
      <section className="border-y border-[#E4E4DE] bg-white/60">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-16 sm:py-20">
          <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">What it costs</p>
          <h2 className="mi2-serif mt-3 text-2xl md:text-3xl text-[#1C1C18]">Free to start, and honest about the rest.</h2>
          <div className="mt-10 grid gap-5 md:grid-cols-3" data-testid="pricing-tiers">
            {PRICES.map((t) => (
              <div key={t.key} data-testid={`tier-${t.key}`} className="bg-white border border-[#E4E4DE] p-6 flex flex-col">
                <div className="flex items-baseline justify-between gap-3">
                  <p className="mi2-serif text-xl text-[#1C1C18]">{t.price}</p>
                  <p className="text-xs text-[#6E6E66]">{t.time}</p>
                </div>
                <p className="mt-3 text-sm text-[#1C1C18]">{t.name}</p>
                <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed flex-1">{t.body}</p>
                <p className="mt-5 text-[11px] uppercase tracking-[0.1em] text-[#6E6E66]">
                  {t.live ? 'Available now' : 'Not yet purchasable'}
                </p>
              </div>
            ))}
          </div>
          <div className="mt-8 max-w-2xl space-y-3 text-sm text-[#3B3B34] leading-relaxed">
            <p data-testid="price-ceiling">
              <strong className="text-[#1C1C18]">$29 is the ceiling for the whole practice</strong> — the promise page
              says a maximum price will be published before anything is purchasable, and that’s it. Nothing expires and
              nothing renews.
            </p>
            <p data-testid="reportable-limits-line">{REGISTER.pricing.reportable_limits}</p>
            <p className="text-[#6E6E66]">
              Only the free tier is built today. The paid readings are published here so you can see what’s coming and
              what it will cost — you cannot buy them yet, and nothing on this page takes a card.
            </p>
          </div>
        </div>
      </section>

      {/* The Flag Check is free, important, and a different intent. Its own door, out of the main flow. */}
      <section className="max-w-6xl mx-auto px-5 sm:px-8 py-14">
        <div className="border border-[#E4E4DE] bg-white p-6 sm:p-7 grid gap-5 md:grid-cols-[1.4fr_auto] md:items-center" data-testid="flag-check-door">
          <div>
            <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">A different question</p>
            <h3 className="mi2-serif mt-2 text-xl text-[#1C1C18]">
              Worried about one specific relationship?
            </h3>
            <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed max-w-xl">
              The Flag Check is nine questions about what you noticed, when, and what you did with it — {FLAG.descriptor}.
              Free, about three minutes, no account needed.
            </p>
          </div>
          <Link
            to="/flag-check"
            data-testid="start-flag-check"
            className="justify-self-start md:justify-self-end text-sm underline underline-offset-4 text-[#1C1C18] hover:opacity-70"
          >
            Take the Flag Check →
          </Link>
        </div>
      </section>

      {/* 7 · Safety */}
      <section className="max-w-6xl mx-auto px-5 sm:px-8 pb-4">
        <div className="border border-[#E4E4DE] bg-white px-6 py-5 flex flex-wrap items-center justify-between gap-4">
          <p className="text-sm text-[#3B3B34]">{SAFETY.headline}</p>
          <Link to="/safety" data-testid="safety-link" className="text-sm underline underline-offset-4 text-[#1C1C18]">
            Where to go instead →
          </Link>
        </div>
      </section>
    </Shell>
  );
}

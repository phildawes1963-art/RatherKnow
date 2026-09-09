import { Link } from 'react-router-dom';
import Shell from '../components/Shell';
import { INSTRUMENTS } from '../lib/mirrorTheme';
import { SITE } from '../lib/siteMeta';
import { FLAG, SAFETY, REGISTER, LANDING } from '../content/register';

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

export default function Landing() {
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: SITE.name,
    url: SITE.baseUrl,
    description: 'Five psychometric instruments that measure how you choose in relationships.',
  };

  return (
    <Shell
      title=""
      description="Five psychometric instruments that measure how you choose in relationships. Free to start, and honest about their own evidence."
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
              Five instruments that measure the one thing you actually control in a relationship: how you choose. Not
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
            <p className="mi2-fade-slow mt-4 text-sm text-[#6E6E66]" data-testid="hero-sub">
              {LANDING.hero_sub}
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

      {/* The Junction Check: free, no account, and the one object here one person sends to another. */}
      <section className="max-w-6xl mx-auto px-5 sm:px-8 py-16 sm:py-20">
        <div className="border border-[#E4E4DE] bg-white p-6 sm:p-7 grid gap-5 md:grid-cols-[1.4fr_auto] md:items-center" data-testid="junction-door">
          <div>
            <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">Start here, free</p>
            <h3 className="mi2-serif mt-2 text-xl text-[#1C1C18]">
              Six things worth saying out loud early
            </h3>
            <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed max-w-xl">
              The instruments measure how you travel. The Junction Check asks about the six places where
              there is only one route — children, where the life happens, who moves, what money is for,
              faith, and whether this is exclusive. Under ten minutes, no account, nothing scored.
            </p>
          </div>
          <Link
            to="/junction"
            data-testid="start-junction-check"
            className="justify-self-start md:justify-self-end text-sm underline underline-offset-4 text-[#1C1C18] hover:opacity-70"
          >
            Take the Junction Check →
          </Link>
        </div>
      </section>

      {/* 5 · How it's built. No per-instrument doors: there is one way in. */}
      <section id="instruments" className="max-w-6xl mx-auto px-5 sm:px-8 py-16 sm:py-24">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">How it’s built</p>
        <h2 className="mi2-serif mt-3 text-2xl md:text-3xl text-[#1C1C18]" data-testid="instruments-h2">Five mirrors, cross-checked.</h2>
        <p className="mt-4 text-base text-[#3B3B34] max-w-2xl leading-relaxed">
          Each measures something different. Where two land away from the middle in the same direction, that’s
          signal. Where they pull opposite ways, that’s a finding —
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
              <dd className="text-sm text-[#3B3B34] leading-relaxed">{ins.line}</dd>
              <dd className="text-xs text-[#6E6E66] sm:text-right whitespace-nowrap">{ins.items}</dd>
            </div>
          ))}
        </dl>

        <p className="mt-6 text-sm text-[#3B3B34] max-w-2xl leading-relaxed" data-testid="tiers-line">
          {LANDING.tiers_line}{' '}
          <Link to="/methodology" data-testid="methodology-link" className="underline underline-offset-4 text-[#1C1C18] hover:opacity-70">
            How it’s scored, in full →
          </Link>
        </p>
        <p className="mt-4 text-sm text-[#6E6E66] max-w-2xl leading-relaxed" data-testid="banding-note">
          {LANDING.banding_note}
        </p>
        <p className="mt-6 text-sm text-[#6E6E66] max-w-2xl leading-relaxed" data-testid="fixed-order">
          {LANDING.fixed_order}
        </p>
      </section>

      {/* It ends. Promise 03, brought forward from a page most readers never reach. */}
      <section className="border-t border-[#E4E4DE] mt-4">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-16 sm:py-20">
        <div className="max-w-2xl">
          <h2 className="mi2-serif text-2xl md:text-3xl text-[#1C1C18]" data-testid="it-ends-h2">
            {LANDING.it_ends_heading}
          </h2>
          {/* A line that stops. Not a bar that fills: the promise is that the practice ends, not
              that finishing it achieves something, and a progress bar says the opposite. */}
          <svg
            className="mt-7 w-full max-w-md h-9 overflow-visible"
            viewBox="0 0 420 36"
            role="img"
            aria-label="A line running three months and then stopping. Nothing continues past the end."
            data-testid="it-ends-mark"
          >
            <line x1="1" y1="18" x2="300" y2="18" stroke="#1C1C18" strokeWidth="1.25" />
            {[1, 100, 200, 300].map((x) => (
              <line key={x} x1={x} y1="12" x2={x} y2="24" stroke="#1C1C18" strokeWidth="1.25" />
            ))}
            <line x1="300" y1="6" x2="300" y2="30" stroke="#1C1C18" strokeWidth="2.5" />
            <text x="1" y="36" fill="#6E6E66" fontSize="10" letterSpacing="1.4">MONTH ONE</text>
            <text x="300" y="36" fill="#1C1C18" fontSize="10" letterSpacing="1.4" textAnchor="end">
              THREE
            </text>
          </svg>
          <p className="mt-5 text-base text-[#3B3B34] leading-relaxed" data-testid="it-ends-body">
            {LANDING.it_ends_body}
          </p>
          <p className="mt-4 text-base text-[#1C1C18] leading-relaxed">{LANDING.it_ends_tail}</p>
          </div>
        </div>
      </section>

      {/* What it costs. One card and prose: two unbuyable columns in a price table read as empty shelves. */}
      <section className="border-y border-[#E4E4DE] bg-white/60">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-16 sm:py-20">
          <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">What it costs</p>
          <h2 className="mi2-serif mt-3 text-2xl md:text-3xl text-[#1C1C18]">Free to start, and honest about the rest.</h2>

          <div className="mt-9 max-w-md bg-white border border-[#1C1C18] p-6" data-testid="tier-free">
            <p className="mi2-serif text-xl text-[#1C1C18]">{LANDING.free_tier_heading}</p>
            <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">{LANDING.free_tier_body}</p>
            <Link
              to="/register?next=%2Ftake%2Fessential"
              data-testid="pricing-start"
              className="mt-5 inline-block bg-[#1C1C18] text-[#F6F6F2] px-5 py-2.5 rounded-sm text-sm hover:opacity-85"
            >
              Start free — 13 minutes
            </Link>
          </div>

          <div className="mt-8 max-w-2xl space-y-4 text-sm text-[#3B3B34] leading-relaxed">
            <p data-testid="paid-prose">{LANDING.paid_prose}</p>
            <p data-testid="price-ceiling">
              <strong className="text-[#1C1C18]">{LANDING.price_ceiling}</strong>
            </p>
            <p className="text-[#6E6E66]" data-testid="nothing-built-yet">{LANDING.nothing_built_yet}</p>
            <p className="border-l-2 border-[#B9B9B0] pl-4 text-[#1C1C18]" data-testid="reportable-limits-line">
              {REGISTER.pricing.reportable_limits}
            </p>
          </div>
        </div>
      </section>

      {/* Where the thinking comes from. The essays are the offer; the book is the provenance. No date. */}
      <section className="max-w-6xl mx-auto px-5 sm:px-8 py-16 sm:py-20">
        <div className="max-w-2xl">
          <h2 className="mi2-serif text-2xl md:text-3xl text-[#1C1C18]" data-testid="thinking-h2">
            {LANDING.thinking_heading}
          </h2>
          <p className="mt-5 text-base text-[#3B3B34] leading-relaxed" data-testid="thinking-body">
            {LANDING.thinking_body}
          </p>
          <p className="mt-4 text-base text-[#3B3B34] leading-relaxed">{LANDING.thinking_essays}</p>
          <Link
            to="/learn"
            data-testid="thinking-essays-link"
            className="mt-6 inline-block text-sm underline underline-offset-4 text-[#1C1C18] hover:opacity-70"
          >
            Read the essays →
          </Link>
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

import { Link } from 'react-router-dom';
import Shell from '../components/Shell';
import { INSTRUMENTS, readSessions } from '../lib/mirrorTheme';
import { LEARN_ARTICLES } from '../content/miLearn';
import { SITE } from '../lib/siteMeta';
import { FLAG, SAFETY } from '../content/register';

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
  const sessions = readSessions();
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
      description="Four psychometric instruments that measure how you choose in relationships. Free, and honest about their own evidence."
      jsonLd={jsonLd}
    >
      <section className="max-w-6xl mx-auto px-5 sm:px-8 pt-20 pb-16 sm:pt-28 sm:pb-24">
        <p className="mi2-fade text-xs uppercase tracking-[0.18em] text-[#6E6E66]">
          Rather Know — {SITE.descriptor}
        </p>
        <h1
          className="mi2-fade mi2-serif mt-5 text-4xl sm:text-5xl lg:text-6xl leading-[1.05] tracking-tight text-[#1C1C18] max-w-3xl"
          data-testid="hero-h1"
        >
          For people who’d rather <em className="text-[#5B7284]">know</em> than be reassured.
        </h1>
        <p className="mi2-fade-slow mt-7 text-base md:text-lg text-[#3B3B34] leading-relaxed max-w-2xl">
          Most people make the largest decision of their lives with no instrument at all. These four measure the one
          variable you control: how you choose. Free, no card, no matching, no profiles — three fields to begin, and no
          promises about anyone but you.
        </p>
        <div className="mi2-fade-slow mt-9 flex flex-wrap items-center gap-4">
          <Link to="/register?next=%2Ftake%2Fessential" data-testid="hero-start" className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85">
            Start with the Essential Mirror
          </Link>
          <Link to="/methodology" data-testid="hero-methodology" className="text-sm text-[#3B3B34] underline underline-offset-4 hover:text-[#1C1C18]">
            How it’s built — and what it refuses to claim
          </Link>
        </div>
      </section>

      <section className="bg-[#1C1C18] text-[#F6F6F2]">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-14 sm:py-16 grid gap-8 sm:grid-cols-[1.2fr_1fr]">
          <div>
            <p className="mi2-serif text-2xl sm:text-3xl leading-snug" data-testid="honest-band">
              We cannot find you love. Nobody can.
            </p>
            <p className="mt-4 text-sm md:text-base text-[#F6F6F2]/75 leading-relaxed max-w-lg">
              Every promise we make is about you, because that’s the only person we can honestly make one about.
            </p>
          </div>
          <ul className="space-y-3 text-sm text-[#F6F6F2]/85 self-center">
            <li className="flex gap-3"><span className="text-[#7E8E77]">—</span> No matching, no profiles, no other people.</li>
            <li className="flex gap-3"><span className="text-[#7E8E77]">—</span> No urgency, no countdowns, nothing expires.</li>
            <li className="flex gap-3"><span className="text-[#7E8E77]">—</span> Every instrument publishes its own evidence tier.</li>
            <li>
              <Link to="/promise" data-testid="promise-link" className="inline-block text-sm underline underline-offset-4 text-[#F6F6F2]/80 hover:text-[#F6F6F2]">
                Read the promise in full — seven promises, ten refusals →
              </Link>
            </li>
          </ul>
        </div>
      </section>

      <section id="instruments" className="max-w-6xl mx-auto px-5 sm:px-8 py-16 sm:py-24">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">The instruments</p>
        <h2 className="mi2-serif mt-3 text-2xl sm:text-3xl text-[#1C1C18]">Four mirrors, cross-checked.</h2>
        <p className="mt-4 text-base text-[#3B3B34] max-w-2xl leading-relaxed">
          Each one measures something different. Where they agree, that’s signal. Where they disagree, that’s a finding
          — and it’s usually the more interesting one.{' '}
          <Link to="/samples" data-testid="samples-link" className="underline underline-offset-4 text-[#1C1C18] hover:opacity-70">
            See a sample of all four first →
          </Link>
        </p>
        <div className="mt-10 grid gap-5 md:grid-cols-2">
          {INSTRUMENTS.map((ins, i) => (
            <div
              key={ins.key}
              data-testid={`instrument-${ins.key}`}
              className="mi2-fade bg-white border border-[#E4E4DE] p-7 sm:p-8 flex flex-col hover:shadow-[0_2px_16px_rgba(28,28,24,0.06)]"
              style={{ animationDelay: `${i * 90}ms` }}
            >
              <div className="flex items-start justify-between gap-4">
                <h3 className="mi2-serif text-xl sm:text-2xl text-[#1C1C18]">
                  {ins.name}
                  {ins.isNew && (
                    <span className="ml-3 align-middle text-[10px] uppercase tracking-[0.12em] text-[#7E8E77] border border-[#7E8E77] px-1.5 py-0.5">
                      New
                    </span>
                  )}
                </h3>
                <Tier tier={ins.tier} />
              </div>
              <p className="mt-1 text-sm" style={{ color: ins.accent }}>{ins.tagline}</p>
              <p className="mt-4 text-sm text-[#3B3B34] leading-relaxed flex-1">{ins.blurb}</p>
              <div className="mt-6 flex items-center justify-between border-t border-[#E4E4DE] pt-4">
                <p className="text-xs text-[#6E6E66]">{ins.items} · {ins.minutes}</p>
                <Link to={`/take/${ins.key}`} data-testid={`start-${ins.key}`} className="text-sm text-[#1C1C18] underline underline-offset-4 hover:opacity-70">
                  {sessions[ins.key] ? 'Continue →' : 'Begin →'}
                </Link>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 bg-white border border-[#E4E4DE] p-7 sm:p-8 grid gap-6 md:grid-cols-[1.4fr_auto] items-center" data-testid="flag-check-door">
          <div>
            <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">A fifth door, different in kind</p>
            <h3 className="mi2-serif mt-2 text-xl sm:text-2xl text-[#1C1C18]">
              The Flag Check<span className="text-[#7E8E77]">.</span> {FLAG.subtitle}
            </h3>
            <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed max-w-xl">
              Nine questions about what you noticed, when, and what you did with it — it never asks about the other
              person. No score, no band: <em>{FLAG.descriptor}</em>, and a framework for what to do with an
              observation that isn’t “leave” and isn’t “let it go”.
            </p>
            <p className="mt-3 text-xs text-[#6E6E66]">Free · about 3 minutes · no account needed</p>
          </div>
          <Link
            to="/flag-check"
            data-testid="start-flag-check"
            className="justify-self-start md:justify-self-end bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85"
          >
            Take the Flag Check
          </Link>
        </div>
      </section>

      <section className="border-y border-[#E4E4DE] bg-white/60">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-16 grid gap-8 md:grid-cols-[1fr_1.2fr] items-center">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">The core idea</p>
            <h2 className="mi2-serif mt-3 text-2xl sm:text-3xl text-[#1C1C18]">The Delta.</h2>
          </div>
          <p className="text-base text-[#3B3B34] leading-relaxed">
            You answer the same fifty questions twice — once as yourself, once as the partner you think you want. The
            gap between those two sets of answers turns <em>“am I too picky?”</em> into something measurable. Not an
            opinion, and not a percentage pulled from the air: a distance, on a scale we show you the workings of.
          </p>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-5 sm:px-8 py-16 sm:py-24">
        <div className="flex items-end justify-between gap-6 flex-wrap">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Learn</p>
            <h2 className="mi2-serif mt-3 text-2xl sm:text-3xl text-[#1C1C18]">Read before you measure.</h2>
          </div>
          <Link to="/learn" data-testid="learn-all" className="text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
            All essays →
          </Link>
        </div>
        <div className="mt-8 grid gap-5 md:grid-cols-3">
          {LEARN_ARTICLES.slice(0, 3).map((a) => (
            <Link
              key={a.slug}
              to={`/learn/${a.slug}`}
              data-testid={`learn-card-${a.slug}`}
              className="bg-white border border-[#E4E4DE] p-6 hover:shadow-[0_2px_16px_rgba(28,28,24,0.06)]"
            >
              <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">{a.cluster} · {a.readMins} min</p>
              <h3 className="mi2-serif mt-3 text-lg leading-snug text-[#1C1C18]">{a.h1}</h3>
              <p className="mt-3 text-sm text-[#6E6E66] leading-relaxed line-clamp-3">{a.dek}</p>
            </Link>
          ))}
        </div>
      </section>

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

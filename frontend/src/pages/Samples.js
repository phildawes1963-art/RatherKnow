import { useState } from 'react';
import { Link } from 'react-router-dom';
import Shell from '../components/Shell';
import { TIER_STATEMENTS } from '../lib/mirrorTheme';
import { TIER_CHIPS, SAMPLES_COPY } from '../content/register';

const Chip = ({ tier }) => (
  <span
    className={`inline-block text-[11px] uppercase tracking-[0.1em] px-2 py-0.5 border ${
      tier === 'Established' ? 'bg-[#1C1C18] text-[#F6F6F2] border-[#1C1C18]' : 'text-[#3B3B34] border-[#B9B9B0]'
    }`}
  >
    {tier}
  </span>
);

const SampleFrame = ({ id, name, tier, takeTo, takeLabel, note, children }) => (
  <section data-testid={`sample-${id}`} className="bg-white border border-[#E4E4DE]">
    <div className="px-6 sm:px-8 pt-6 flex items-start justify-between gap-4 flex-wrap">
      <div>
        <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">Sample result — fabricated profile</p>
        <h2 className="mi2-serif mt-1 text-2xl text-[#1C1C18]">{name}</h2>
      </div>
      <Chip tier={tier} />
    </div>
    <div className="px-6 sm:px-8 py-6">{children}</div>
    <div className="px-6 sm:px-8 py-4 border-t border-[#E4E4DE] flex items-center justify-between gap-4 flex-wrap">
      <p className="text-xs text-[#6E6E66] max-w-md leading-relaxed">{note}</p>
      <Link to={takeTo} data-testid={`sample-take-${id}`} className="text-sm text-[#1C1C18] underline underline-offset-4 hover:opacity-70 whitespace-nowrap">
        {takeLabel} →
      </Link>
    </div>
  </section>
);

// Single dot on two continuous axes — midlines only, never a grid of boxes.
const ClosenessPlot = () => {
  const S = 260;
  const anx = 4.6; // reassurance axis (1–7)
  const avo = 2.9; // closeness axis (1–7)
  const x = ((avo - 1) / 6) * (S - 40) + 20;
  const y = S - 20 - ((anx - 1) / 6) * (S - 40);
  return (
    <svg viewBox={`0 0 ${S} ${S}`} className="w-full max-w-[260px]" role="img" aria-label={`Sample position: reassurance ${anx}, closeness ${avo}`} data-testid="sample-closeness-plot">
      <rect x="20" y="20" width={S - 40} height={S - 40} fill="none" stroke="#E4E4DE" />
      <line x1={S / 2} y1="20" x2={S / 2} y2={S - 20} stroke="#E4E4DE" strokeDasharray="3 4" />
      <line x1="20" y1={S / 2} x2={S - 20} y2={S / 2} stroke="#E4E4DE" strokeDasharray="3 4" />
      <circle cx={x} cy={y} r="7" fill="#7E8E77" />
      <circle cx={x} cy={y} r="12" fill="none" stroke="#7E8E77" opacity="0.35" />
      <text x={S / 2} y="12" textAnchor="middle" fontSize="9" fill="#6E6E66">more reassurance needed ↑</text>
      <text x={S / 2} y={S - 4} textAnchor="middle" fontSize="9" fill="#6E6E66">less ↓</text>
      <text x="14" y={S / 2} textAnchor="middle" fontSize="9" fill="#6E6E66" transform={`rotate(-90 14 ${S / 2})`}>closeness comes easily ←</text>
      <text x={S - 8} y={S / 2} textAnchor="middle" fontSize="9" fill="#6E6E66" transform={`rotate(90 ${S - 8} ${S / 2})`}>→ kept at a distance</text>
    </svg>
  );
};

const FactorRow = ({ low, name, pct, high }) => (
  <div className="grid grid-cols-[1fr_2.2fr_1fr] items-center gap-3 text-xs">
    <span className="text-right text-[#6E6E66]">{low}</span>
    <div>
      <div className="flex justify-between text-[10px] text-[#9C9C93] mb-0.5"><span>{low.toLowerCase()} end</span><span className="text-[#3B3B34] font-medium">{name}</span><span>{high.toLowerCase()} end</span></div>
      <div className="relative h-2 bg-[#EDEDE7]">
        <div className="absolute top-0 bottom-0 w-2 bg-[#5B7284]" style={{ left: `calc(${pct}% - 4px)` }} />
      </div>
    </div>
    <span className="text-[#1C1C18]">{high}</span>
  </div>
);

const DomainBar = ({ name, score }) => (
  <div>
    <div className="flex justify-between text-xs mb-1">
      <span className="text-[#3B3B34]">{name}</span>
      <span className="text-[#6E6E66]">{score.toFixed(1)} of 5</span>
    </div>
    <div className="h-2 bg-[#EDEDE7]">
      <div className="h-full bg-[#5B7284]" style={{ width: `${(score / 5) * 100}%` }} />
    </div>
  </div>
);

const ShareBlock = () => {
  const [copied, setCopied] = useState(false);
  const url = `${window.location.origin}${window.location.pathname}`;
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable — the visible URL is selectable */
    }
  };
  return (
    <section className="mt-8 border border-[#E4E4DE] bg-white p-6 sm:p-7" data-testid="samples-share">
      <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">For the friend who asked what this is</p>
      <p className="mi2-serif mt-2 text-xl text-[#1C1C18]">Send them this page.</p>
      <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed max-w-xl">
        The sample says it better than a pitch — no sign-up on the other end, and nothing about you attached to it.
      </p>
      <div className="mt-4 flex items-stretch gap-0 max-w-xl">
        <span className="flex-1 min-w-0 border border-[#E4E4DE] bg-[#F6F6F2] px-4 py-2.5 text-sm text-[#3B3B34] truncate select-all" data-testid="samples-share-url">
          {url}
        </span>
        <button
          onClick={copy}
          data-testid="samples-share-copy"
          className="bg-[#1C1C18] text-[#F6F6F2] px-5 py-2.5 text-sm hover:opacity-85 whitespace-nowrap"
        >
          {copied ? 'Copied ✓' : 'Copy link'}
        </button>
      </div>
    </section>
  );
};

export default function Samples() {
  return (
    <Shell title="Sample results" description="One fabricated profile, run through all four mirrors — the exact shape of what you get, before you give it twenty-five minutes.">
      <div className="max-w-3xl mx-auto px-5 sm:px-8 py-14 sm:py-20">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Rather Know — samples</p>
        <h1 className="mi2-serif mt-3 text-4xl sm:text-5xl text-[#1C1C18]" data-testid="samples-title">
          What you actually get.
        </h1>
        <p className="mt-6 text-base text-[#3B3B34] leading-relaxed max-w-2xl">
          Below is one invented profile — call them <em>Sample № 001</em> — run through all four mirrors. The numbers
          are real numbers of the kind the instruments produce; the person is not. Nothing here is an average, a
          benchmark, or an aspiration. It exists so you can see the shape of the output before you give it your time.
        </p>

        <div className="mt-10 space-y-8">
          <SampleFrame
            id="essential"
            name="Essential Mirror"
            tier={TIER_CHIPS.essential}
            takeTo="/take/essential"
            takeLabel="Take the Essential Mirror"
            note={TIER_STATEMENTS.essential}
          >
            <div className="grid gap-5 sm:grid-cols-2">
              <div className="border border-[#E4E4DE] p-5">
                <p className="text-[11px] uppercase tracking-[0.12em] text-[#5B7284]">Lens one — as yourself</p>
                <p className="mi2-serif mt-2 text-xl text-[#1C1C18]">The Empath</p>
                <p className="text-xs text-[#6E6E66]">with a secondary of The Diplomat</p>
              </div>
              <div className="border border-[#E4E4DE] p-5">
                <p className="text-[11px] uppercase tracking-[0.12em] text-[#C8AE93]">Lens two — the partner you describe</p>
                <p className="mi2-serif mt-2 text-xl text-[#1C1C18]">The Rock</p>
                <p className="text-xs text-[#6E6E66]">with a secondary of The Voyager</p>
              </div>
            </div>
            <div className="mt-5 bg-[#F6F6F2] border border-[#E4E4DE] p-5">
              <p className="mi2-serif text-lg text-[#1C1C18]">The Delta: <strong>14.6</strong> points</p>
              <p className="mt-1 text-sm text-[#3B3B34] leading-relaxed">
                The mean absolute gap between the two lenses, across the six patterns. The widest single gap here is on
                <em> The Rock</em> — this profile asks for much more steadiness than it carries itself. That sentence,
                not a percentage, is the finding.
              </p>
            </div>
          </SampleFrame>

          <SampleFrame
            id="closeness"
            name="Closeness Mirror"
            tier={TIER_CHIPS.closeness}
            takeTo="/take/closeness"
            takeLabel="Take the Closeness Mirror"
            note={TIER_STATEMENTS.closeness}
          >
            <div className="grid gap-6 sm:grid-cols-[auto_1fr] items-center">
              <ClosenessPlot />
              <div className="text-sm text-[#3B3B34] leading-relaxed space-y-3">
                <p>
                  A single point on two continuous dimensions: how much reassurance this profile needs (<strong>4.6</strong> of 7,
                  a little above the middle) and how easily closeness comes (<strong>2.9</strong> of 7 — fairly easily).
                </p>
                <p className="text-xs text-[#6E6E66]">
                  No boxes, no types, no labels — deliberately. Both positions are read against the midline, and neither
                  is a fault. All 36 statements answered · reported with confidence noted.
                </p>
              </div>
            </div>
          </SampleFrame>

          <SampleFrame
            id="personality"
            name="Personality Mirror"
            tier={TIER_CHIPS.personality}
            takeTo="/take/personality"
            takeLabel="Take the Personality Mirror"
            note={`${TIER_STATEMENTS.personality} ${SAMPLES_COPY.personality_note}`}
          >
            <div className="space-y-4">
              <FactorRow low="Reserved" name="Warmth" pct={72} high="Warm" />
              <FactorRow low="Reactive" name="Emotional stability" pct={50} high="Emotionally stable" />
              <FactorRow low="Trusting" name="Vigilance" pct={22} high="Vigilant" />
              <FactorRow low="Traditional" name="Openness to change" pct={81} high="Open to change" />
            </div>
            <p className="mt-4 text-xs text-[#6E6E66]">
              Four of fifteen factors shown. {SAMPLES_COPY.position_explainer} {SAMPLES_COPY.loudest_line}
            </p>
          </SampleFrame>

          <SampleFrame
            id="eq"
            name="EI Mirror"
            tier={TIER_CHIPS.eq}
            takeTo="/take/eq"
            takeLabel="Take the EI Mirror"
            note={`${TIER_STATEMENTS.eq} Twelve sub-competencies sit beneath the four domains in the full result.`}
          >
            <p className="text-sm text-[#3B3B34] mb-4">Overall: <strong>3.6</strong> of 5</p>
            <div className="space-y-4">
              <DomainBar name="Self-awareness" score={3.9} />
              <DomainBar name="Self-management" score={3.2} />
              <DomainBar name="Social awareness" score={3.8} />
              <DomainBar name="Relationship management" score={3.4} />
            </div>
          </SampleFrame>
        </div>

        <section className="mt-12 bg-[#1C1C18] text-[#F6F6F2] p-7 sm:p-9" data-testid="samples-never">
          <h2 className="mi2-serif text-2xl">And what you will never see.</h2>
          <ul className="mt-4 space-y-2 text-sm text-[#F6F6F2]/85">
            <li className="flex gap-3"><span className="text-[#7E8E77]">—</span> A compatibility percentage.</li>
            <li className="flex gap-3"><span className="text-[#7E8E77]">—</span> A verdict on anyone who hasn’t taken the assessment.</li>
            <li className="flex gap-3"><span className="text-[#7E8E77]">—</span> A clinical label — of you, or of anyone you describe.</li>
          </ul>
          <Link to="/promise" data-testid="samples-promise-link" className="mt-5 inline-block text-sm underline underline-offset-4 text-[#F6F6F2]/80 hover:text-[#F6F6F2]">
            The full list is on the promise page →
          </Link>
        </section>

        <ShareBlock />

        <div className="mt-12 flex flex-wrap items-center gap-5">
          <Link to="/take/essential" data-testid="samples-cta" className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85">
            Run your own — start free
          </Link>
          <Link to="/methodology" className="text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
            How the instruments are built →
          </Link>
        </div>
      </div>
    </Shell>
  );
}

import { Link } from 'react-router-dom';
import { TIER_STATEMENTS } from '../../lib/mirrorTheme';
import { TIER_CHIPS } from '../../content/register';

const CELLS = {
  non_negotiable: { label: 'A genuine line', tone: 'text-[#1C1C18] border-[#1C1C18]' },
  strong_but_tradeable: { label: 'Strong, but tradeable', tone: 'text-[#C8AE93] border-[#C8AE93]' },
  needs_settling: { label: 'Just needs settling', tone: 'text-[#5B7284] border-[#5B7284]' },
  low_friction: { label: 'Unlikely to be the friction', tone: 'text-[#6E6E66] border-[#B9B9B0]' },
};

const PositionRow = ({ p }) => {
  const placed = p.position !== null && p.position !== undefined;
  return (
    <div className="px-5 sm:px-6 py-4 border-b border-[#E4E4DE] last:border-0" data-testid={`everyday-position-${p.name.toLowerCase()}`}>
      <div className="flex items-baseline justify-between gap-4">
        <p className="text-sm text-[#1C1C18]">{p.name}</p>
        <p className="text-xs text-[#6E6E66] shrink-0">{p.status === 'scored' ? p.label : p.status.replace(/_/g, ' ')}</p>
      </div>
      {placed ? (
        <>
          <div className="mt-2.5 flex items-center gap-2" aria-hidden="true">
            {[0, 1, 2, 3, 4].map((slot) => (
              <span
                key={slot}
                className={`h-1.5 flex-1 ${slot === p.position && p.status === 'scored' ? 'bg-[#5B7284]' : 'bg-[#EDEDE8]'}`}
              />
            ))}
          </div>
          <div className="mt-1.5 flex justify-between text-[11px] text-[#9C9C93]">
            <span>{p.pole_b}</span><span>{p.pole_a}</span>
          </div>
        </>
      ) : (
        <p className="mt-2 text-sm text-[#6E6E66]">Not enough answers here to place you — and we won't guess.</p>
      )}
    </div>
  );
};

export default function EverydayResult({ result }) {
  const positions = Object.values(result.positions);
  const v = result.validity || {};

  return (
    <div className="space-y-12">
      <header>
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Everyday Mirror · forty-nine either/ors</p>
        <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="everyday-title">
          Where you sit, and what you’d protect.
        </h1>
        <p className="mt-5 text-base text-[#3B3B34] leading-relaxed max-w-2xl">
          Every other instrument here asks how you describe yourself. This one asked you to choose, which makes it
          the only one that can disagree with your own description.
        </p>
      </header>

      <section data-testid="everyday-positions">
        <h2 className="mi2-serif text-2xl text-[#1C1C18]">Where you sit.</h2>
        <p className="mt-3 text-sm text-[#6E6E66] max-w-2xl leading-relaxed">
          Four choices per domain, so five possible positions between two named poles. No band, no percentile, no
          comparison with anyone else. An even split is reported as undifferentiated rather than as a middle — those
          are different claims, and only one of them is true.
        </p>
        <div className="mt-5 bg-white border border-[#E4E4DE]">
          {positions.map((p) => <PositionRow key={p.name} p={p} />)}
        </div>
      </section>

      <section data-testid="everyday-priority">
        <h2 className="mi2-serif text-2xl text-[#1C1C18]">What you’d protect.</h2>
        <p className="mt-3 text-sm text-[#6E6E66] max-w-2xl leading-relaxed">
          Twenty-one comparisons, every domain against every other once. This is the half no lifestyle quiz asks:
          not where you land, but which of it you’d actually spend agreement on.
        </p>
        <div className="mt-5 bg-white border border-[#E4E4DE]">
          {result.priority.map((p) => (
            <div key={p.domain} className="px-5 sm:px-6 py-3.5 border-b border-[#E4E4DE] last:border-0 flex items-center gap-4" data-testid={`everyday-priority-${p.domain}`}>
              <span className="text-xs text-[#9C9C93] w-6 shrink-0">{p.rank}</span>
              <span className="text-sm text-[#1C1C18] w-28 sm:w-32 shrink-0">{p.name}</span>
              <span className="flex-1 h-1.5 bg-[#EDEDE8] relative">
                <span className="absolute inset-y-0 left-0 bg-[#7E8E77]" style={{ width: `${(p.wins / 6) * 100}%` }} />
              </span>
              <span className="text-xs text-[#6E6E66] w-20 sm:w-24 text-right shrink-0">
                {p.wins} of 6{p.tied ? ' · tied' : ''}
              </span>
            </div>
          ))}
        </div>
      </section>

      {result.map?.length > 0 && (
        <section data-testid="everyday-map">
          <h2 className="mi2-serif text-2xl text-[#1C1C18]">Position against priority.</h2>
          <p className="mt-3 text-sm text-[#6E6E66] max-w-2xl leading-relaxed">
            The corners are the interesting part. Feeling strongly about something and being willing to defend it are
            not the same thing, and the gap between them is where this instrument earns its place.
          </p>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {[...result.map].sort((a, b) => a.priority_rank - b.priority_rank).map((c) => (
              <div key={c.domain} className="bg-white border border-[#E4E4DE] p-5" data-testid={`everyday-cell-${c.domain}`}>
                <div className="flex items-baseline justify-between gap-3">
                  <p className="text-sm font-medium text-[#1C1C18]">{c.name}</p>
                  <span className={`text-[10px] uppercase tracking-[0.1em] border px-1.5 py-0.5 ${CELLS[c.cell].tone}`}>
                    {CELLS[c.cell].label}
                  </span>
                </div>
                <p className="mt-2 text-xs text-[#6E6E66] leading-relaxed">
                  {c.label}, and ranked {c.priority_rank} of seven for needing agreement.
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="border border-[#E4E4DE] bg-white p-6" data-testid="everyday-confidence">
        <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">Confidence in this reading</p>
        <p className="mt-2 text-sm text-[#1C1C18]">{(result.confidence || 'not established').replace(/^./, (m) => m.toUpperCase())}</p>
        <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">
          Three checks ran on the choices themselves rather than on anything you told us: loops in your comparisons
          (consistency index {v.zeta ?? '—'}), how often you picked the left-hand option when the sides were
          randomised ({v.side_bias_left_pct ?? '—'}%), and a time floor (mean {v.mean_ms ?? '—'} ms per item).
        </p>
        <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">{result.claim_limit}</p>
      </section>

      <section className="border border-[#E4E4DE] bg-white p-6" data-testid="everyday-evidence-tier">
        <p className="text-[11px] uppercase tracking-[0.1em] border border-[#B9B9B0] text-[#3B3B34] inline-block px-2 py-0.5">
          {TIER_CHIPS.everyday}
        </p>
        <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">{TIER_STATEMENTS.everyday}</p>
      </section>

      <section className="border-t border-[#E4E4DE] pt-8 flex flex-wrap items-center gap-5">
        <Link to="/mirrors" data-testid="everyday-cta-mirrors" className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85">
          See all your mirrors
        </Link>
        <Link to="/take/personality" className="text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
          Next: the Personality Mirror →
        </Link>
      </section>
    </div>
  );
}

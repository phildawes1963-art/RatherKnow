import { Link } from 'react-router-dom';
import { TIER_STATEMENTS } from '../../lib/mirrorTheme';
import { TIER_CHIPS } from '../../content/register';

const DualBar = ({ label, self, ideal }) => (
  <div className="py-2.5 border-b border-[#E4E4DE] last:border-0">
    <div className="flex justify-between text-sm mb-1.5">
      <span className="text-[#1C1C18]">{label}</span>
      <span className="text-[#6E6E66] text-xs">you {self} · want {ideal}</span>
    </div>
    <div className="space-y-1">
      <div className="h-1.5 bg-[#EDEDE8]"><div className="h-full bg-[#5B7284]" style={{ width: `${self}%` }} /></div>
      <div className="h-1.5 bg-[#EDEDE8]"><div className="h-full bg-[#C8AE93]" style={{ width: `${ideal}%` }} /></div>
    </div>
  </div>
);

export default function EssentialResult({ result }) {
  const s = result.self;
  const i = result.ideal;
  const delta = result.delta;
  const biggestName = s.archetype_scores[delta.biggest]?.name || delta.biggest;

  return (
    <div className="space-y-12">
      <header>
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Essential Mirror · two lenses</p>
        <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="essential-title">
          Who you are — and who you say you want.
        </h1>
      </header>

      <section className="grid gap-5 md:grid-cols-2">
        <div className="bg-white border border-[#E4E4DE] p-7" data-testid="essential-self">
          <p className="text-xs uppercase tracking-[0.12em] text-[#5B7284]">As a partner, you read as</p>
          <h2 className="mi2-serif mt-2 text-2xl text-[#1C1C18]" data-testid="essential-self-name">
            {s.tie?.tied ? `${s.tie.names[0]} and ${s.tie.names[1]}` : s.primary.name}
          </h2>
          <p className="text-sm text-[#6E6E66]">
            {s.tie?.tied ? 'Two patterns, named together' : `${s.primary.subtitle} · with a secondary of ${s.secondary.name}`}
          </p>
          {s.tie?.tied && (
            <p className="mt-3 text-xs text-[#6E6E66] leading-relaxed" data-testid="essential-self-tie">{s.tie.note}</p>
          )}
          {(s.tie?.descriptions || [s.primary.description]).map((d, n) => (
            <p key={n} className="mt-4 text-sm text-[#3B3B34] leading-relaxed">{d}</p>
          ))}
        </div>
        <div className="bg-white border border-[#E4E4DE] p-7" data-testid="essential-ideal">
          <p className="text-xs uppercase tracking-[0.12em] text-[#C8AE93]">The partner you describe is</p>
          <h2 className="mi2-serif mt-2 text-2xl text-[#1C1C18]" data-testid="essential-ideal-name">
            {i.tie?.tied ? `${i.tie.names[0]} and ${i.tie.names[1]}` : i.primary.name}
          </h2>
          <p className="text-sm text-[#6E6E66]">
            {i.tie?.tied ? 'Two patterns, named together' : `${i.primary.subtitle} · with a secondary of ${i.secondary.name}`}
          </p>
          {i.tie?.tied && (
            <p className="mt-3 text-xs text-[#6E6E66] leading-relaxed" data-testid="essential-ideal-tie">{i.tie.note}</p>
          )}
          {(i.tie?.descriptions || [i.primary.description]).map((d, n) => (
            <p key={n} className="mt-4 text-sm text-[#3B3B34] leading-relaxed">{d}</p>
          ))}
        </div>
      </section>

      <section data-testid="essential-delta">
        <div className="flex items-baseline justify-between flex-wrap gap-3">
          <h2 className="mi2-serif text-2xl text-[#1C1C18]">The Delta.</h2>
          <p className="text-sm text-[#6E6E66]">Overall gap: <strong className="text-[#1C1C18]">{delta.overall}</strong> points (mean absolute difference across the six patterns)</p>
        </div>
        <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed max-w-2xl">
          Blue is you; sand is who you say you want. The widest gap sits on <strong>{biggestName}</strong>
          {' '}({delta.per_archetype[delta.biggest] > 0 ? 'you ask for much more of it than you carry yourself' : 'you carry much more of it than you ask for'}).
          A gap isn’t a problem to fix — it’s the most informative part of the measurement.
        </p>
        {delta.elevation != null && (
          <p className="mt-3 text-xs text-[#6E6E66] leading-relaxed max-w-2xl" data-testid="essential-elevation">
            {delta.elevation_share != null && delta.elevation_share >= 0.6
              ? `Most of that distance is level rather than shape: across all six patterns you describe the partner you want as ${delta.elevation > 0 ? '+' : ''}${delta.elevation} points different on average. Read the bars as which patterns run furthest ahead of that general lift, not as six separate findings.`
              : `Averaged across all six patterns, you describe the partner you want as ${delta.elevation > 0 ? '+' : ''}${delta.elevation} points different from yourself. That figure is the level; the bars are the shape.`}
          </p>
        )}
        <div className="mt-6 bg-white border border-[#E4E4DE] p-6">
          {Object.entries(s.archetype_scores).map(([key, sc]) => (
            <DualBar key={key} label={sc.name} self={sc.percentage} ideal={i.archetype_scores[key].percentage} />
          ))}
        </div>
      </section>

      {result.shadow && (
        <section className="bg-[#1C1C18] text-[#F6F6F2] p-7 sm:p-9" data-testid="essential-shadow">
          <p className="text-xs uppercase tracking-[0.18em] text-[#F6F6F2]/60">The shadow</p>
          <h2 className="mi2-serif mt-3 text-2xl">Secretly drawn to: {result.shadow.name}</h2>
          <p className="mt-4 text-sm leading-relaxed text-[#F6F6F2]/85">{result.shadow.warning}</p>
          <p className="mt-3 text-sm leading-relaxed text-[#F6F6F2]/70">
            The shadow isn’t a villain — at its best, the {result.shadow.name.replace('The ', '')} brings {result.shadow.gift.toLowerCase()}.
            The pull is real; the question is whether it’s choosing for you.
          </p>
          {result.shadow.basis && (
            <p className="mt-4 text-xs leading-relaxed text-[#F6F6F2]/60" data-testid="essential-shadow-basis">{result.shadow.basis}</p>
          )}
        </section>
      )}

      <section data-testid="essential-dimensions">
        <h2 className="mi2-serif text-2xl text-[#1C1C18]">Where the want diverges.</h2>
        <div className="mt-5 bg-white border border-[#E4E4DE] divide-y divide-[#E4E4DE]">
          {Object.entries(s.dimensions).map(([dim, val]) => {
            const gap = result.dimension_gaps[dim];
            return (
              <div key={dim} className="px-6 py-3.5 flex items-center justify-between text-sm">
                <span className="text-[#1C1C18]">{dim}</span>
                <span className="text-[#6E6E66]">
                  you {val} · want {i.dimensions[dim]}
                  <span className={`ml-3 ${Math.abs(gap) >= 15 ? 'text-[#5B7284] font-medium' : ''}`}>
                    {gap > 0 ? '+' : ''}{gap}
                  </span>
                </span>
              </div>
            );
          })}
        </div>
      </section>

      <section className="border border-[#E4E4DE] bg-white p-6" data-testid="essential-evidence-tier">
        <p className="text-[11px] uppercase tracking-[0.1em] text-[#3B3B34] border border-[#B9B9B0] inline-block px-2 py-0.5">{TIER_CHIPS.essential}</p>
        <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">{TIER_STATEMENTS.essential}</p>
      </section>

      <section className="border-t border-[#E4E4DE] pt-8 flex flex-wrap items-center gap-5">
        <Link to="/take/closeness" data-testid="essential-cta-closeness" className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85">
          Next: the Closeness Mirror — 5 minutes
        </Link>
        <Link to="/mirrors" data-testid="essential-cta-mirrors" className="text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
          See all your mirrors →
        </Link>
      </section>
    </div>
  );
}

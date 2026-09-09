import { Link } from 'react-router-dom';
import { TIER_STATEMENTS } from '../../lib/mirrorTheme';
import { TIER_CHIPS } from '../../content/register';

const Bar = ({ score }) => (
  <div className="h-2 bg-[#EDEDE8] w-full">
    <div className="h-full bg-[#5B7284]" style={{ width: `${(score / 5) * 100}%` }} />
  </div>
);

export default function EqResult({ result }) {
  const domains = Object.entries(result.domain_scores);
  const named = result.named;
  // Where no two domains clear the floor, the individual figures do not appear at all: four
  // two-decimal values printed side by side rank them for the reader whatever the prose says.
  const resolved = named?.resolved !== false;

  return (
    <div className="space-y-12">
      <header>
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">EI Mirror · Goleman four domains</p>
        <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="eq-title">
          How you handle what you feel.
        </h1>
        <p className="mt-4 text-sm text-[#3B3B34]" data-testid="eq-overall">
          Overall: <strong>{result.overall_score.toFixed(2)}</strong> of 5 — the mean of your own answers, with no grade attached
        </p>
      </header>

      {!resolved && named?.band && (
        <section className="bg-white border border-[#E4E4DE] p-6" data-testid="eq-domains-band">
          <p className="text-sm text-[#1C1C18] leading-relaxed">{named.band.sentence}</p>
          <p className="mt-3 text-xs text-[#6E6E66] leading-relaxed" data-testid="eq-suppression-note">
            {named.suppression_note}
          </p>
        </section>
      )}

      <section className="space-y-6" data-testid="eq-domains">
        {domains.map(([key, d]) => (
          <div key={key} className="bg-white border border-[#E4E4DE] p-6" data-testid={`eq-domain-${key}`}>
            <div className="flex items-baseline justify-between gap-4">
              <h2 className="mi2-serif text-xl text-[#1C1C18]">{d.name}</h2>
              {resolved && <p className="text-sm text-[#5B7284] whitespace-nowrap" data-testid={`eq-domain-score-${key}`}>{d.score.toFixed(2)} of 5</p>}
            </div>
            {resolved && <div className="mt-3"><Bar score={d.score} /></div>}
            <p className="mt-3 text-xs text-[#6E6E66] leading-relaxed">{d.description}</p>
            <div className="mt-4 grid gap-1.5 sm:grid-cols-2">
              {Object.values(result.sub_scores).filter((sSub) => sSub.domain === key).map((sSub) => (
                <p key={sSub.name} className="text-xs text-[#3B3B34] border-t border-[#E4E4DE] pt-1.5">
                  {sSub.name}
                </p>
              ))}
            </div>
          </div>
        ))}
      </section>

      {named && (
        <section className="bg-white border border-[#E4E4DE] p-6" data-testid="eq-named">
          {named.highest || named.lowest ? (
            <>
              <p className="text-xs uppercase tracking-[0.12em] text-[#7E8E77]">What separates from the rest</p>
              <ul className="mt-3 space-y-2 text-sm text-[#3B3B34]">
                {named.highest && (
                  <li data-testid="eq-named-highest">
                    Highest: {named.highest.name} — {named.highest.score.toFixed(2)} of 5, clear of the next by {named.highest.margin.toFixed(2)}
                  </li>
                )}
                {named.lowest && (
                  <li data-testid="eq-named-lowest">
                    Lowest: {named.lowest.name} — {named.lowest.score.toFixed(2)} of 5, clear of the next by {named.lowest.margin.toFixed(2)}
                  </li>
                )}
              </ul>
            </>
          ) : (
            <p className="text-sm text-[#3B3B34] leading-relaxed" data-testid="eq-named-flat">{named.flat_copy}</p>
          )}
          <p className="mt-4 text-xs text-[#6E6E66] leading-relaxed">
            A highest or lowest is named only where two domains differ by at least {named.mrd?.toFixed(1)} on the 1–5
            scale — the smallest difference worth reading, assuming a reliability of {named.assumed_alpha?.toFixed(2)}
            {' '}and rounded up rather than down. Provisional, and re-derived when this bank's reliability is measured.
          </p>
          <p className="mt-3 text-xs text-[#6E6E66] leading-relaxed" data-testid="eq-facet-note">{named.facet_note}</p>
        </section>
      )}

      <section className="border border-[#E4E4DE] bg-white p-6" data-testid="eq-evidence-tier">
        <p className="text-[11px] uppercase tracking-[0.1em] bg-[#1C1C18] text-[#F6F6F2] inline-block px-2 py-0.5">{TIER_CHIPS.eq}</p>
        <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">
          {TIER_STATEMENTS.eq} A self-report read of how you perceive your own capacities — informative, and honest
          about being a self-perception rather than an ability test.
        </p>
      </section>

      <section className="border-t border-[#E4E4DE] pt-8 flex flex-wrap items-center gap-5">
        <Link to="/mirrors" data-testid="eq-cta-mirrors" className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85">
          See all your mirrors
        </Link>
        <Link to="/take/closeness" className="text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
          Next: the Closeness Mirror →
        </Link>
      </section>
    </div>
  );
}

import { Link } from 'react-router-dom';
import { TIER_STATEMENTS } from '../../lib/mirrorTheme';
import { TIER_CHIPS } from '../../content/register';

const FactorRow = ({ f }) => (
  <div className="px-6 py-3 border-b border-[#E4E4DE] last:border-0 grid grid-cols-[1fr_auto_1fr] items-center gap-3 text-xs sm:text-sm">
    <span className="text-right text-[#6E6E66]">{f.pole_low}</span>
    <div className="w-36 sm:w-52">
      <div className="flex justify-between text-[10px] text-[#9C9C93] mb-0.5"><span>1</span><span className="text-[#3B3B34] font-medium">{f.name} · {f.sten}</span><span>10</span></div>
      <div className="h-2 bg-[#EDEDE8] relative">
        <div className="absolute top-0 bottom-0 w-2 bg-[#5B7284]" style={{ left: `calc(${((f.sten - 1) / 9) * 100}% - 4px)` }} />
      </div>
    </div>
    <span className="text-[#1C1C18]">{f.pole_high}</span>
  </div>
);

export default function PersonalityResult({ result }) {
  const factors = Object.values(result.factor_scores);
  const globals = Object.values(result.global_scores);
  const composites = result.composites;
  const provenance = composites?.globals || {};
  const sd = result.validity?.social_desirability?.flag;

  return (
    <div className="space-y-12">
      <header>
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Personality Mirror · five-factor profile</p>
        <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="personality-title">
          Fifteen factors. Five dimensions. No verdicts.
        </h1>
      </header>

      {sd && sd !== 'NORMAL' && (
        <p className="border border-[#C8AE93] bg-[#C8AE93]/10 px-5 py-4 text-sm text-[#3B3B34]" data-testid="personality-validity-note">
          You agreed with an unusually high number of very flattering statements — nothing wrong with that, but read
          this profile as a best-self version and take it again on an ordinary day if you want the everyday one.
        </p>
      )}

      <section data-testid="personality-globals">
        <h2 className="mi2-serif text-2xl text-[#1C1C18]">The five global dimensions.</h2>
        <p className="mt-3 text-sm text-[#6E6E66] max-w-2xl leading-relaxed">
          Derived, not measured — each one is arithmetic on the primary factors below. Open any dimension to see
          exactly which primaries build it, in which direction, and how much each contributed.
        </p>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          {globals.map((g, gi) => {
            const prov = provenance[Object.keys(result.global_scores)[gi]];
            return (
            <div key={g.name} className="bg-white border border-[#E4E4DE] p-5">
              <div className="flex items-baseline justify-between">
                <p className="text-sm font-medium text-[#1C1C18]">{g.name}</p>
                <p className="text-sm text-[#5B7284]">{g.score}/10 · {g.label}</p>
              </div>
              <p className="mt-2 text-xs text-[#6E6E66] leading-relaxed">{g.description}</p>
              {g.sub_clusters && (
                <div className="mt-3 space-y-1 border-t border-[#E4E4DE] pt-3">
                  {Object.values(g.sub_clusters).map((sc) => (
                    <p key={sc.name} className="text-xs text-[#3B3B34] flex justify-between">
                      <span>{sc.name}</span><span className="text-[#6E6E66]">{sc.score}/10 · {sc.label}</span>
                    </p>
                  ))}
                </div>
              )}
              {prov && (
                <details className="mt-3 border-t border-[#E4E4DE] pt-3" data-testid={`global-provenance-${Object.keys(result.global_scores)[gi]}`}>
                  <summary className="text-xs text-[#5B7284] cursor-pointer">How this number is built</summary>
                  <p className="mt-2 text-[11px] text-[#6E6E66]">{prov.equation}</p>
                  <ul className="mt-2 space-y-1">
                    {prov.contributions.map((c) => (
                      <li key={c.factor} className="text-xs text-[#3B3B34] flex justify-between gap-3">
                        <span>{c.name} <span className="text-[#9C9C93]">({c.direction} it)</span></span>
                        <span className="text-[#6E6E66] whitespace-nowrap">
                          sten {c.sten} × {c.weight} = {c.contribution > 0 ? '+' : ''}{c.contribution}
                        </span>
                      </li>
                    ))}
                  </ul>
                  {prov.polarity_note && <p className="mt-2 text-[11px] text-[#6E6E66] leading-relaxed">{prov.polarity_note}</p>}
                  {prov.known_residual && (
                    <p className="mt-2 text-[11px] text-[#C8AE93] leading-relaxed">
                      Known residual: this composite sits further from other 16PF-style instruments than the rest.
                      Compare the primaries above before trusting the composite.
                    </p>
                  )}
                </details>
              )}
            </div>
          );})}
        </div>
        {composites && (
          <div className="mt-5 border border-[#E4E4DE] bg-white p-6" data-testid="personality-composite-note">
            <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">Comparing this with another report?</p>
            <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed">{composites.note}</p>
            <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">{composites.residual_note}</p>
          </div>
        )}
      </section>

      <section data-testid="personality-factors">
        <h2 className="mi2-serif text-2xl text-[#1C1C18]">The fifteen primary factors.</h2>
        <p className="mt-3 text-sm text-[#6E6E66] max-w-2xl leading-relaxed">
          Sten scores, 1–10, against calibrated norms. Neither pole is better — each position carries costs and gifts.
        </p>
        <div className="mt-5 bg-white border border-[#E4E4DE]">
          {factors.map((f) => <FactorRow key={f.name} f={f} />)}
        </div>
      </section>

      {(result.strengths?.length > 0 || result.blind_spots?.length > 0) && (
        <section className="grid gap-5 sm:grid-cols-2" data-testid="personality-strengths">
          <div className="bg-white border border-[#E4E4DE] p-6">
            <p className="text-xs uppercase tracking-[0.12em] text-[#7E8E77]">Marked strengths (sten ≥ 8)</p>
            <ul className="mt-3 space-y-2 text-sm text-[#3B3B34]">
              {result.strengths.length ? result.strengths.map((st) => (
                <li key={st.factor}>{st.name} — strongly {st.pole.toLowerCase()}</li>
              )) : <li className="text-[#6E6E66]">None at the extreme — a balanced profile.</li>}
            </ul>
          </div>
          <div className="bg-white border border-[#E4E4DE] p-6">
            <p className="text-xs uppercase tracking-[0.12em] text-[#C8AE93]">Strong leanings (sten ≤ 3)</p>
            <ul className="mt-3 space-y-2 text-sm text-[#3B3B34]">
              {result.blind_spots.length ? result.blind_spots.map((b) => (
                <li key={b.factor}>{b.name} — strongly {b.pole.toLowerCase()}</li>
              )) : <li className="text-[#6E6E66]">None at the extreme — a balanced profile.</li>}
            </ul>
          </div>
        </section>
      )}

      <section className="border border-[#E4E4DE] bg-white p-6" data-testid="personality-evidence-tier">
        <p className="text-[11px] uppercase tracking-[0.1em] bg-[#1C1C18] text-[#F6F6F2] inline-block px-2 py-0.5">{TIER_CHIPS.personality}</p>
        <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">{TIER_STATEMENTS.personality} Fifteen primary factors and five global dimensions, scored against calibrated norm bands.</p>
      </section>

      <section className="border-t border-[#E4E4DE] pt-8 flex flex-wrap items-center gap-5">
        <Link to="/mirrors" data-testid="personality-cta-mirrors" className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85">
          See all your mirrors
        </Link>
        <Link to="/take/eq" className="text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
          Next: the EI Mirror →
        </Link>
      </section>
    </div>
  );
}

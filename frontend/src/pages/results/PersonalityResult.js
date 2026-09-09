import { Link } from 'react-router-dom';
import { TIER_STATEMENTS } from '../../lib/mirrorTheme';
import { TIER_CHIPS, POSITION_COPY } from '../../content/register';

const FactorRow = ({ f, position }) => (
  <div className="px-5 sm:px-6 py-4 border-b border-[#E4E4DE] last:border-0" data-testid={`factor-row-${f.name.toLowerCase().replace(/[^a-z]+/g, '-')}`}>
    <div className="flex items-baseline justify-between gap-4">
      <p className="text-sm text-[#1C1C18]">{f.name}</p>
      <p className="text-xs text-[#6E6E66] shrink-0">{f.pole_low} ← → {f.pole_high}</p>
    </div>
    <div className="mt-2 h-1.5 bg-[#EDEDE8] relative" aria-hidden="true">
      {/* Percent of this factor's own scale. Never the sten: a sten is a norm-referenced figure
          and the band table behind ours has no documented reference sample. */}
      <div
        className="absolute top-0 bottom-0 w-1.5 bg-[#5B7284]"
        style={{ left: `calc(${position?.value ?? 50}% - 3px)` }}
      />
    </div>
    <p className="mt-2.5 text-sm text-[#3B3B34] leading-relaxed" data-testid="factor-position">
      {position?.sentence}
    </p>
  </div>
);

const COUNT_WORD = ['none', 'One', 'Two', 'Three'];

// Globals carry no band word (paused with the population layer) and no number either: an x-of-10
// beside a bidirectional composite reads as a mark out of ten. The bar and the published equation
// carry the position; the label says where it sits against the reader's own five.
const POSITION = (g, meanOfFive) => {
  const d = (g.score ?? g.score_precise ?? 0) - meanOfFive;
  if (Math.abs(d) <= 1.0) return 'at your own middle'; // one full step of the composite's own scale
  return d > 0 ? 'above your own middle' : 'below your own middle';
};

export default function PersonalityResult({ result }) {
  const factorKeys = Object.keys(result.factor_scores);
  const factors = Object.values(result.factor_scores);
  const globals = Object.values(result.global_scores);
  const composites = result.composites;
  const provenance = composites?.globals || {};
  const position = result.position?.scales || {};
  const globalsMean = globals.length
    ? globals.reduce((t, g) => t + (g.score ?? 0), 0) / globals.length
    : 0;
  const subMean = (g) => {
    const subs = Object.values(g.sub_clusters || {});
    return subs.length ? subs.reduce((t, s2) => t + (s2.score ?? 0), 0) / subs.length : 0;
  };
  const loud = result.loudest || [...(result.strengths || []), ...(result.blind_spots || [])];
  // Recomputed from the stored count rather than read from the stored label. The count is the
  // frozen datum; the cut that turns it into a word was set below chance (4 of 10 is exactly what
  // content-blind answering produces) and has moved to 7. See backend/services/reportable.py.
  const sdCount = result.validity?.social_desirability?.agree_count;
  const sd = sdCount == null ? null : (sdCount >= 9 ? 'HIGH' : sdCount >= 7 ? 'ELEVATED' : 'NORMAL');

  return (
    <div className="space-y-12">
      <header>
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Personality Mirror · five-factor profile</p>
        <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="personality-title">
          Fifteen factors. Five dimensions. No verdicts.
        </h1>
      </header>

      {sd === 'NORMAL' && sdCount != null && (
        <p className="text-xs text-[#6E6E66] leading-relaxed" data-testid="personality-validity-null-note">
          Social desirability check: you agreed with {sdCount} of the ten most flattering statements, where about four
          is what content-blind answering produces on its own. Nothing to read into this one.
        </p>
      )}

      {sd && sd !== 'NORMAL' && (
        <p className="border border-[#C8AE93] bg-[#C8AE93]/10 px-5 py-4 text-sm text-[#3B3B34]" data-testid="personality-validity-note">
          You agreed with {sdCount} of the ten most flattering statements in this questionnaire, where about four is what
          answering without reading closely produces on its own — nothing wrong with that, but read this profile as a
          best-self version and take it again on an ordinary day if you want the everyday one.
        </p>
      )}

      <section data-testid="personality-globals">
        <h2 className="mi2-serif text-2xl text-[#1C1C18]">The five global dimensions.</h2>
        <p className="mt-3 text-sm text-[#6E6E66] max-w-2xl leading-relaxed" data-testid="globals-explainer">
          {POSITION_COPY.globals_explainer} Open any dimension to see exactly which primaries build it, in which
          direction, and how much each contributed.
        </p>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          {globals.map((g, gi) => {
            const prov = provenance[Object.keys(result.global_scores)[gi]];
            return (
            <div key={g.name} className="bg-white border border-[#E4E4DE] p-5">
              <div className="flex items-baseline justify-between gap-3">
                <p className="text-sm font-medium text-[#1C1C18]">{g.name}</p>
                <p className="text-sm text-[#5B7284] text-right">{POSITION(g, globalsMean)}</p>
              </div>
              <p className="mt-2 text-xs text-[#6E6E66] leading-relaxed">{g.description}</p>
              {prov?.clamped && (
                <p className="mt-2 text-[11px] text-[#C8AE93] leading-relaxed" data-testid={`global-clamped-${factorKeys && Object.keys(result.global_scores)[gi]}`}>
                  {prov.clamp_note}
                </p>
              )}
              {g.sub_clusters && (
                <div className="mt-3 space-y-1 border-t border-[#E4E4DE] pt-3">
                  {Object.values(g.sub_clusters).map((sc) => (
                    <p key={sc.name} className="text-xs text-[#3B3B34] flex justify-between gap-3">
                      <span>{sc.name}</span><span className="text-[#6E6E66] text-right">{POSITION(sc, subMean(g))}</span>
                    </p>
                  ))}
                </div>
              )}
              {prov && (
                <details className="mt-3 border-t border-[#E4E4DE] pt-3" data-testid={`global-provenance-${Object.keys(result.global_scores)[gi]}`}>
                  <summary className="text-xs text-[#5B7284] cursor-pointer">How this number is built</summary>
                  <p className="mt-2 text-[11px] text-[#6E6E66]">{prov.equation}</p>
                  <p className="mt-2 text-[11px] text-[#9C9C93] leading-relaxed" data-testid={`global-sten-note-${Object.keys(result.global_scores)[gi]}`}>
                    The units below are stens — the internal units these five composites are computed in. They are
                    here so the arithmetic can be checked, and nowhere else in this report: a sten compares you with
                    a reference sample, and no reference sample for these bands is documented.
                  </p>
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
        <p className="mt-3 text-sm text-[#6E6E66] max-w-2xl leading-relaxed" data-testid="position-explainer">
          {POSITION_COPY.no_comparison}
        </p>
        <div className="mt-5 bg-white border border-[#E4E4DE]">
          {factors.map((f, i) => <FactorRow key={f.name} f={f} position={position[factorKeys[i]]} />)}
        </div>
        <div className="mt-5 border border-[#E4E4DE] bg-white p-6 max-w-2xl" data-testid="why-no-comparison">
          <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">{POSITION_COPY.caveat_heading}</p>
          <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed">{POSITION_COPY.caveat_body}</p>
        </div>
        {result.position && (
          <p className="mt-2 text-xs text-[#6E6E66]" data-testid="position-version">
            Positions derived within your own profile at read time · {result.position.version}
          </p>
        )}
      </section>

      <section data-testid="personality-loudest">
        <h2 className="mi2-serif text-2xl text-[#1C1C18]" data-testid="loudest-heading">{POSITION_COPY.loudest_heading_counted[String(Math.min(loud.length, 3))]}</h2>
        {loud.length === 3 && (
          <p className="mt-3 text-sm text-[#6E6E66] max-w-2xl leading-relaxed" data-testid="loudest-meaning">
            {POSITION_COPY.loudest_meaning}
          </p>
        )}
        {loud.length > 0 && loud.length < 3 && (
          <p className="mt-3 text-sm text-[#3B3B34] max-w-2xl leading-relaxed" data-testid="loudest-partial">
            {loud.length === 1 ? POSITION_COPY.loudest_partial_one : POSITION_COPY.loudest_partial.replace('{count}', COUNT_WORD[loud.length])}
          </p>
        )}
        {loud.length === 0 ? (
          <p className="mt-3 text-sm text-[#3B3B34] max-w-2xl leading-relaxed" data-testid="loudest-none">
            {POSITION_COPY.loudest_none}
          </p>
        ) : (
          <ul className="mt-5 bg-white border border-[#E4E4DE]" data-testid="loudest-list">
            {loud.map((f) => (
              <li key={f.factor} className="px-5 sm:px-6 py-4 border-b border-[#E4E4DE] last:border-0">
                <p className="text-sm text-[#1C1C18]">{f.name}</p>
                <p className="mt-1 text-sm text-[#3B3B34]">
                  Toward the {f.pole.toLowerCase()} end.
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="border border-[#E4E4DE] bg-white p-6" data-testid="personality-evidence-tier">
        <p className="text-[11px] uppercase tracking-[0.1em] bg-[#1C1C18] text-[#F6F6F2] inline-block px-2 py-0.5">{TIER_CHIPS.personality}</p>
        <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">{TIER_STATEMENTS.personality} Fifteen primary factors and five global dimensions.</p>      </section>

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

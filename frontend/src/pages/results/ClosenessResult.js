import { Link } from 'react-router-dom';
import { describeVsMidpoint, TIER_STATEMENTS } from '../../lib/mirrorTheme';
import { SAFETY, TIER_CHIPS } from '../../content/register';

const FLOOR = SAFETY.floor;

function guidance(anx, avo) {
  if (anx == null || avo == null) {
    return 'One of your dimensions couldn’t be scored this time, so we won’t guess at guidance. The one thing that holds regardless:';
  }
  const highAnx = anx > 4.0;
  const highAvo = avo > 4.0;
  if (highAnx && highAvo)
    return 'For you, a bodily signal is best treated as a prompt to observe — never as a verdict. Note what you noticed, watch whether it repeats, and decide on the record rather than the feeling. And one floor overrides all of that:';
  if (highAnx)
    return 'Your alarm tends to run ahead of the evidence more often than not. That doesn’t make your reactions wrong — it makes the record more useful than the feeling. When something unsettles you, write down what actually happened and watch whether it repeats. And one floor overrides all of that:';
  if (highAvo)
    return 'Discomfort at closeness is expected for you, and it is not by itself information about the other person. Ease and entanglement may register as risk when they aren’t. Give closeness longer than your instinct suggests before you read it as a signal. And one floor overrides all of that:';
  return 'Your reactions are reasonably informative — worth attending to. When something feels off, it’s worth noting what you noticed and whether it repeats. And one floor overrides all of that:';
}

function Plot({ anx, avo }) {
  // x = Closeness axis (avoidance), y = Reassurance axis (anxiety). Single dot, midlines only — never a grid of boxes.
  const S = 320;
  const P = 44;
  const span = S - 2 * P;
  const toX = (v) => P + ((v - 1) / 6) * span;
  const toY = (v) => S - P - ((v - 1) / 6) * span;
  return (
    <svg viewBox={`0 0 ${S} ${S}`} className="w-full max-w-sm" role="img" aria-label={`Your position: reassurance ${anx}, closeness ${avo}`} data-testid="closeness-plot">
      <rect x={P} y={P} width={span} height={span} fill="#FFFFFF" stroke="#E4E4DE" />
      <line x1={toX(4)} y1={P} x2={toX(4)} y2={S - P} stroke="#D5D5CD" strokeDasharray="3 4" />
      <line x1={P} y1={toY(4)} x2={S - P} y2={toY(4)} stroke="#D5D5CD" strokeDasharray="3 4" />
      <text x={S / 2} y={S - 12} textAnchor="middle" fontSize="11" fill="#6E6E66">Closeness</text>
      <text x={P} y={S - 26} textAnchor="start" fontSize="9" fill="#9C9C93">comes easily</text>
      <text x={S - P} y={S - 26} textAnchor="end" fontSize="9" fill="#9C9C93">kept at a distance</text>
      <text x={14} y={S / 2} textAnchor="middle" fontSize="11" fill="#6E6E66" transform={`rotate(-90 14 ${S / 2})`}>Reassurance</text>
      <text x={28} y={S - P} textAnchor="middle" fontSize="9" fill="#9C9C93" transform={`rotate(-90 28 ${S - P})`}>needs little</text>
      <text x={28} y={P + 30} textAnchor="middle" fontSize="9" fill="#9C9C93" transform={`rotate(-90 28 ${P + 30})`}>seeks it often</text>
      <circle cx={toX(avo)} cy={toY(anx)} r="7" fill="#5B7284" />
      <circle cx={toX(avo)} cy={toY(anx)} r="12" fill="none" stroke="#5B7284" strokeOpacity="0.35" />
    </svg>
  );
}

export default function ClosenessResult({ result }) {
  const anx = result.dimensions.anxiety;
  const avo = result.dimensions.avoidance;
  const caveat =
    result.confidence === 'moderate'
      ? 'You went through some of these quickly — treat this as a rough read.'
      : result.confidence === 'low'
      ? 'This one may not reflect you well. You can take it again whenever you like.'
      : null;

  return (
    <div className="space-y-12">
      <header>
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Closeness Mirror · MI-AS-36</p>
        <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="closeness-title">
          How you are when you’re close to someone.
        </h1>
      </header>

      {caveat && (
        <p className="border border-[#C8AE93] bg-[#C8AE93]/10 px-5 py-4 text-sm text-[#3B3B34]" data-testid="closeness-caveat">
          {caveat}
        </p>
      )}

      <section className="grid gap-8 md:grid-cols-[auto_1fr] items-center">
        {anx.value != null && avo.value != null ? (
          <Plot anx={anx.value} avo={avo.value} />
        ) : (
          <div className="border border-[#E4E4DE] bg-white p-6 text-sm text-[#6E6E66] max-w-sm" data-testid="closeness-not-scored">
            One or both dimensions couldn’t be scored — too many statements were left unanswered. Nothing is wrong;
            there just isn’t enough to measure honestly. You can take it again whenever you like.
          </div>
        )}
        <div className="space-y-5">
          <div data-testid="closeness-reassurance">
            <p className="text-xs uppercase tracking-[0.12em] text-[#6E6E66]">Reassurance</p>
            <p className="mt-1 text-base text-[#1C1C18]">
              {anx.value != null ? (
                <>You sit <strong>{describeVsMidpoint(anx.value)}</strong> ({anx.value} on a 1–7 scale{anx.prorated ? ', prorated for a skipped item' : ''}). This is about how much ongoing signal you need that things are all right — checking, noticing changes in warmth, how long silence stays with you.</>
              ) : (
                'Not scored this time.'
              )}
            </p>
          </div>
          <div data-testid="closeness-closeness">
            <p className="text-xs uppercase tracking-[0.12em] text-[#6E6E66]">Closeness</p>
            <p className="mt-1 text-base text-[#1C1C18]">
              {avo.value != null ? (
                <>You sit <strong>{describeVsMidpoint(avo.value)}</strong> ({avo.value} on a 1–7 scale{avo.prorated ? ', prorated for a skipped item' : ''}). This is about how easily closeness itself comes — disclosing, leaning on someone, being looked after, lives entwining.</>
              ) : (
                'Not scored this time.'
              )}
            </p>
          </div>
          <p className="text-sm text-[#6E6E66] leading-relaxed">
            Both are continuous dimensions, not types. There is no box you fall into, and neither position is a fault —
            each carries costs and each carries information.
          </p>
        </div>
      </section>

      <section className="bg-[#1C1C18] text-[#F6F6F2] p-7 sm:p-9" data-testid="closeness-guidance">
        <p className="text-xs uppercase tracking-[0.18em] text-[#F6F6F2]/60">Reading your own alarm</p>
        <p className="mt-4 text-base leading-relaxed text-[#F6F6F2]/90">{guidance(anx.value, avo.value)}</p>
        <p className="mt-4 mi2-serif text-lg text-[#F6F6F2]" data-testid="closeness-floor">{FLOOR}</p>
        <Link to="/safety" className="mt-4 inline-block text-sm underline underline-offset-4 text-[#F6F6F2]/80 hover:text-[#F6F6F2]">
          Where to go if that’s where you are →
        </Link>
      </section>

      <section className="border border-[#E4E4DE] bg-white p-6" data-testid="closeness-evidence-tier">
        <p className="text-[11px] uppercase tracking-[0.1em] text-[#3B3B34] border border-[#B9B9B0] inline-block px-2 py-0.5">{TIER_CHIPS.closeness}</p>
        <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">{TIER_STATEMENTS.closeness}</p>
        <p className="mt-2 text-sm text-[#6E6E66] leading-relaxed">
          That’s why there are no bands, no categories and no percentiles here — population norms don’t exist yet. When
          they do, they’ll be published with the sample size and the date.
        </p>
      </section>

      <section className="border-t border-[#E4E4DE] pt-8">
        <p className="text-base text-[#3B3B34] leading-relaxed max-w-xl">
          The thing that decides what you notice in other people — and what you excuse — is your own pattern. The
          Essential Mirror maps it.
        </p>
        <Link
          to="/take/essential"
          data-testid="closeness-cta-essential"
          className="mt-5 inline-block bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85"
        >
          Take the Essential Mirror — free
        </Link>
      </section>
    </div>
  );
}

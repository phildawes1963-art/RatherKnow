import { Link } from 'react-router-dom';
import { SITUATION_LENS, SITUATION_DISCLAIMER } from '../content/situationFraming';
import { useAuth } from '../lib/auth';

const KEY_BY_INSTRUMENT = { 'MI-AS-36': 'closeness', essential: 'essential', personality: 'personality', eq: 'eq' };

// Same scores, read for where the person actually is. Framing only.
export default function SituationLens({ instrument }) {
  const { user } = useAuth();
  if (!user?.situation) return null;
  const lens = SITUATION_LENS[user.situation];
  const key = KEY_BY_INSTRUMENT[instrument];
  if (!lens || !lens[key]) return null;

  return (
    <section
      className="border-l-2 border-[#7E8E77] bg-white border border-[#E4E4DE] p-6 sm:p-7"
      data-testid={`situation-lens-${user.situation}`}
    >
      <p className="text-[11px] uppercase tracking-[0.12em] text-[#7E8E77]">
        Read for where you are · {lens.label}
      </p>
      <p className="mi2-serif mt-2 text-xl text-[#1C1C18]" data-testid="situation-lens-lead">{lens.lead}</p>
      <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed" data-testid="situation-lens-body">{lens[key]}</p>
      <div className="mt-4 flex flex-wrap items-center gap-4">
        <Link
          to={lens.nudge.to}
          data-testid="situation-lens-nudge"
          className="text-sm underline underline-offset-4 text-[#1C1C18] hover:opacity-70"
        >
          {lens.nudge.label} →
        </Link>
        <span className="text-xs text-[#6E6E66]">{SITUATION_DISCLAIMER}</span>
      </div>
    </section>
  );
}

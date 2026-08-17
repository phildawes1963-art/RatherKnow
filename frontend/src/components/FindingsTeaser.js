import { Link } from 'react-router-dom';
import { INSTRUMENTS, readSessions } from '../lib/mirrorTheme';

// Quiet band under every result: one mirror is a reading, two is a cross-check.
export default function FindingsTeaser({ current }) {
  const sessions = readSessions();
  const started = Object.keys(sessions);
  const hasTwo = started.filter((k) => k !== current).length >= 1 && started.length >= 2;

  const order = ['closeness', 'essential', 'eq', 'personality'];
  const nextKey = order.find((k) => k !== current && !started.includes(k));
  const next = INSTRUMENTS.find((i) => i.key === nextKey);

  return (
    <section className="mt-12 border border-[#E4E4DE] bg-white p-6 sm:p-7" data-testid="findings-teaser">
      <p className="text-[11px] uppercase tracking-[0.12em] text-[#7E8E77]">The cross-check</p>
      {hasTwo ? (
        <>
          <p className="mi2-serif mt-2 text-xl text-[#1C1C18]">You’ve run more than one mirror.</p>
          <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed max-w-xl">
            The cross-check reads them side by side. Where they agree, that’s signal. Where they disagree, that’s a
            finding — and it’s usually the more interesting one.
          </p>
          <Link to="/mirrors" data-testid="findings-teaser-cta" className="mt-4 inline-block bg-[#1C1C18] text-[#F6F6F2] px-5 py-2.5 rounded-sm text-sm hover:opacity-85">
            Read them together →
          </Link>
        </>
      ) : (
        <>
          <p className="mi2-serif mt-2 text-xl text-[#1C1C18]">One mirror is a reading. Two is a cross-check.</p>
          <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed max-w-xl">
            This result gets sharper next to a second instrument — where two mirrors agree is signal, and where they
            disagree is usually the finding worth sitting with.
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-4">
            {next && (
              <Link to={`/take/${next.key}`} data-testid="findings-teaser-cta" className="inline-block bg-[#1C1C18] text-[#F6F6F2] px-5 py-2.5 rounded-sm text-sm hover:opacity-85">
                Add the {next.name} — {next.minutes.toLowerCase()} →
              </Link>
            )}
            <Link to="/mirrors" data-testid="findings-teaser-mirrors" className="text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
              See the cross-check page
            </Link>
          </div>
        </>
      )}
    </section>
  );
}

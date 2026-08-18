import { useState } from 'react';
import { useAuth } from '../lib/auth';

const OPTIONS = [
  { key: 'single_dating', label: 'Single & dating' },
  { key: 'in_relationship', label: 'In a relationship' },
  { key: 'post_breakup', label: 'Post-breakup' },
];

// Life moves; the framing should follow it. Scores never change.
export default function SituationSwitch() {
  const { user, updateSituation } = useAuth();
  const [busy, setBusy] = useState('');
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  if (!user) return null;

  const choose = async (key) => {
    if (key === user.situation) return;
    setBusy(key);
    setError('');
    setSaved(false);
    try {
      await updateSituation(key);
      setSaved(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy('');
    }
  };

  return (
    <section className="border border-[#E4E4DE] bg-white p-6 sm:p-7" data-testid="situation-switch">
      <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">Where you are now</p>
      <p className="mi2-serif mt-2 text-xl text-[#1C1C18]">Things change. Say so, and the reports reframe.</p>
      <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed max-w-xl">
        Every report you’ve already taken is read differently depending on where you are — dating reads forward,
        post-breakup reads back. Switching this rewrites the framing on all of them, on screen and in the PDFs.
        It never changes a single score: those are snapshots, and snapshots don’t move.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {OPTIONS.map((o) => {
          const active = user.situation === o.key;
          return (
            <button
              key={o.key}
              onClick={() => choose(o.key)}
              disabled={!!busy}
              aria-pressed={active}
              data-testid={`situation-switch-${o.key}`}
              className={`border px-5 py-2.5 text-sm disabled:opacity-60 ${
                active
                  ? 'bg-[#1C1C18] text-[#F6F6F2] border-[#1C1C18]'
                  : 'bg-white text-[#3B3B34] border-[#E4E4DE] hover:border-[#1C1C18]'
              }`}
            >
              {busy === o.key ? 'Saving…' : o.label}
            </button>
          );
        })}
      </div>
      {saved && (
        <p className="mt-3 text-sm text-[#7E8E77]" data-testid="situation-switch-saved">
          Saved. Your reports now read for {OPTIONS.find((o) => o.key === user.situation)?.label.toLowerCase()}.
        </p>
      )}
      {error && <p className="mt-3 text-sm text-[#8C3A2B]" data-testid="situation-switch-error">{error}</p>}
    </section>
  );
}

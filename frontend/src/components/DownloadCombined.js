import { useState } from 'react';
import { API } from '../lib/mirrorTheme';
import { authHeaders } from '../lib/auth';

// Every finished mirror plus the cross-check, in one document.
export default function DownloadCombined({ completeCount }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const download = async () => {
    setBusy(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/v2/reports/combined.pdf`, { headers: authHeaders() });
      if (!res.ok) {
        throw new Error(
          res.status === 409
            ? 'Finish an instrument first — there’s nothing to print yet.'
            : 'The document couldn’t be built. Try again in a moment.'
        );
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'ratherknow-your-mirrors.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('combined report download failed', err);
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="border border-[#E4E4DE] bg-white p-6 sm:p-7" data-testid="download-combined">
      <div className="flex flex-wrap items-center justify-between gap-5">
        <div>
          <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">One document</p>
          <p className="mi2-serif mt-2 text-xl text-[#1C1C18]">Every mirror, and the cross-check, on paper.</p>
          <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed max-w-xl">
            {completeCount >= 2
              ? 'Your completed instruments in one printable file, with the findings where they disagree — the part that’s hardest to see one report at a time.'
              : 'Your completed instrument, printable. Finish a second and this document gains the cross-check: where two mirrors disagree is usually the finding.'}
          </p>
        </div>
        <button
          onClick={download}
          disabled={busy || completeCount === 0}
          data-testid="download-combined-btn"
          className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85 disabled:opacity-40"
        >
          {busy ? 'Building…' : completeCount === 0 ? 'Nothing to print yet' : 'Download the full document'}
        </button>
      </div>
      {error && <p className="mt-3 text-sm text-[#8C3A2B]" data-testid="download-combined-error">{error}</p>}
    </section>
  );
}

import { useState } from 'react';
import { API } from '../lib/mirrorTheme';
import { authHeaders } from '../lib/auth';

// Downloads the server-rendered PDF of this exact snapshot. No re-scoring.
export default function DownloadReport({ sessionId, instrumentName }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const download = async () => {
    setBusy(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/v2/assessments/${sessionId}/report.pdf`, { headers: authHeaders() });
      if (!res.ok) throw new Error('The report couldn’t be built. Try again in a moment.');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ratherknow-${instrumentName.toLowerCase().replace(/\s+/g, '-')}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('report download failed', err);
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="border border-[#E4E4DE] bg-white p-6 sm:p-7" data-testid="download-report">
      <div className="flex flex-wrap items-center justify-between gap-5">
        <div>
          <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">Keep it</p>
          <p className="mi2-serif mt-2 text-xl text-[#1C1C18]">A printable copy, worth taking with you.</p>
          <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed max-w-xl">
            The same numbers, laid out for paper — evidence tier, scoring version and stated limits included, so it
            reads honestly in a room with a therapist. No verdict on anyone else, because none was ever measured.
          </p>
        </div>
        <button
          onClick={download}
          disabled={busy}
          data-testid="download-report-btn"
          className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85 disabled:opacity-50"
        >
          {busy ? 'Building…' : 'Download PDF'}
        </button>
      </div>
      {error && <p className="mt-3 text-sm text-[#8C3A2B]" data-testid="download-report-error">{error}</p>}
    </section>
  );
}

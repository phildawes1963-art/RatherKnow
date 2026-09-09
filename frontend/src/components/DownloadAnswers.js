import { useState } from 'react';
import { API } from '../lib/mirrorTheme';
import { authHeaders } from '../lib/auth';

// The raw record: every item and the answer given. Rebuilt on request, never snapshotted —
// there is nothing in it that a later display change could alter.
export default function DownloadAnswers() {
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  const download = async (format) => {
    setBusy(format);
    setError('');
    try {
      const res = await fetch(`${API}/api/v2/answers/export.${format}`, { headers: authHeaders() });
      if (!res.ok) {
        throw new Error(
          res.status === 409
            ? 'Finish an instrument first — there are no answers to export yet.'
            : 'The export couldn’t be built. Try again in a moment.'
        );
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ratherknow-your-answers.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('answer export failed', err);
      setError(err.message);
    } finally {
      setBusy('');
    }
  };

  return (
    <section className="border border-[#E4E4DE] bg-white p-6 sm:p-7" data-testid="download-answers">
      <div className="flex flex-wrap items-center justify-between gap-5">
        <div>
          <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">Your data</p>
          <p className="mi2-serif mt-2 text-xl text-[#1C1C18]">Every answer you gave, back out again.</p>
          <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed max-w-xl">
            The raw record, not a reading: each item as it was put to you, the answer you gave, and the seconds you
            spent on it — in the order you saw them. Nothing scored, reversed or interpreted, and no version stamp,
            because there is nothing in it a later change could alter. Every sitting you have finished, including
            any instrument you took more than once.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => download('pdf')}
            disabled={!!busy}
            data-testid="download-answers-pdf-btn"
            className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85 disabled:opacity-50"
          >
            {busy === 'pdf' ? 'Building…' : 'Download PDF'}
          </button>
          <button
            onClick={() => download('json')}
            disabled={!!busy}
            data-testid="download-answers-json-btn"
            className="border border-[#1C1C18] text-[#1C1C18] px-5 py-3 rounded-sm text-sm hover:bg-[#EDEDE8] disabled:opacity-50"
          >
            {busy === 'json' ? 'Building…' : 'JSON'}
          </button>
        </div>
      </div>
      {error && <p className="mt-3 text-sm text-[#8C3A2B]" data-testid="download-answers-error">{error}</p>}
    </section>
  );
}

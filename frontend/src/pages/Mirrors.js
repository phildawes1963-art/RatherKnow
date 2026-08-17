import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Shell from '../components/Shell';
import { API, INSTRUMENTS, readSessions, readReflections, saveSession } from '../lib/mirrorTheme';
import { authHeaders, useAuth } from '../lib/auth';
import { FLAG, REGISTER } from '../content/register';

export default function Mirrors() {
  const [summaries, setSummaries] = useState(null);
  const [findings, setFindings] = useState(null);
  const { user } = useAuth();
  const flagCheckId = readReflections().flag_check;

  useEffect(() => {
    if (user === null) return;
    (async () => {
      let ids = Object.values(readSessions());
      if (user) {
        try {
          const res = await fetch(`${API}/api/auth/me/sessions`, { headers: authHeaders() });
          const data = await res.json();
          const mine = data.sessions || [];
          // A completed session always wins over an abandoned one, newest first.
          const best = {};
          mine.forEach((s) => {
            const held = best[s.instrument];
            if (!held || (s.status === 'complete' && held.status !== 'complete')) best[s.instrument] = s;
          });
          Object.values(best).forEach((s) => saveSession(s.instrument, s.session_id));
          ids = [...new Set([...ids, ...mine.map((s) => s.session_id)])];
        } catch { /* fall back to local ids */ }
      }
      if (ids.length === 0) {
        setSummaries([]);
        setFindings([]);
        return;
      }
      const post = (path) =>
        fetch(`${API}${path}`, {
          method: 'POST',
          headers: authHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({ session_ids: ids }),
        }).then((r) => r.json());
      try {
        const summary = await post('/api/v2/mirrors/summary');
        setSummaries(summary.sessions || []);
      } catch {
        setSummaries([]);
      }
      try {
        const found = await post('/api/v2/mirrors/findings');
        setFindings(found.findings || []);
      } catch {
        setFindings([]);
      }
    })();
  }, [user]);

  const byInstrument = {};
  (summaries || []).forEach((s) => {
    const held = byInstrument[s.instrument];
    if (!held || (s.status === 'complete' && held.status !== 'complete')) byInstrument[s.instrument] = s;
  });
  const completeCount = (summaries || []).filter((s) => s.status === 'complete').length;

  return (
    <Shell title="Your mirrors" description="Everything you've measured, in one place.">
      <div className="max-w-4xl mx-auto px-5 sm:px-8 py-14 sm:py-20">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Your mirrors</p>
        <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="mirrors-title">
          The cross-check.
        </h1>
        <p className="mt-4 text-base text-[#3B3B34] max-w-2xl leading-relaxed">
          Four instruments, kept for you and retrievable by logging in. Where they agree, that’s signal. Where they
          disagree, that’s not an error: it’s a finding, and usually the more interesting one.
        </p>
        {completeCount >= 2 && (
          <p className="mt-3 text-sm text-[#5B7284]" data-testid="mirrors-crosscheck-note">
            You’ve completed {completeCount} — enough to start reading them against each other.
          </p>
        )}

        {summaries === null ? (
          <p className="mt-10 text-[#6E6E66]" data-testid="mirrors-loading">Fetching…</p>
        ) : (
          <div className="mt-10 space-y-4">
            {INSTRUMENTS.map((ins) => {
              const s = byInstrument[ins.key];
              return (
                <div key={ins.key} data-testid={`mirrors-card-${ins.key}`} className="bg-white border border-[#E4E4DE] px-6 py-5 flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <p className="mi2-serif text-lg text-[#1C1C18]">{ins.name}</p>
                    <p className="mt-1 text-sm text-[#6E6E66]">
                      {s ? s.headline : `Not started · ${ins.items} · ${ins.minutes}`}
                    </p>
                  </div>
                  {s?.status === 'complete' ? (
                    <Link to={`/results/${s.session_id}`} data-testid={`mirrors-view-${ins.key}`} className="text-sm bg-[#1C1C18] text-[#F6F6F2] px-4 py-2 rounded-sm hover:opacity-85">
                      View result
                    </Link>
                  ) : (
                    <Link to={`/take/${ins.key}`} data-testid={`mirrors-continue-${ins.key}`} className="text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
                      {s ? 'Continue →' : 'Begin →'}
                    </Link>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {summaries !== null && completeCount >= 2 && (
          <section className="mt-14" data-testid="mirrors-findings">
            <h2 className="mi2-serif text-2xl text-[#1C1C18]">Findings.</h2>
            <p className="mt-3 text-sm text-[#3B3B34] max-w-2xl leading-relaxed">
              Where your instruments disagree with each other. None of these is a verdict — each is a tension between
              two honest measurements, and the tension is the finding.
            </p>
            {findings && findings.length > 0 ? (
              <div className="mt-6 space-y-5">
                {findings.map((f, i) => (
                  <div key={f.id} data-testid={`mirrors-finding-${i + 1}`} className="bg-white border-l-2 border-[#5B7284] border border-[#E4E4DE] p-6 sm:p-7">
                    <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">{f.sources.join(' × ')}</p>
                    <h3 className="mi2-serif mt-2 text-xl text-[#1C1C18]">{f.title}</h3>
                    <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">{f.body}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-6 border border-[#E4E4DE] bg-white px-6 py-5 text-sm text-[#6E6E66] leading-relaxed" data-testid="mirrors-no-findings">
                No tensions worth reporting — where your completed instruments overlap, they broadly agree. That’s
                signal too, and we won’t invent a disagreement to seem insightful.
              </p>
            )}
          </section>
        )}

        {flagCheckId && (
          <div className="mt-10 border border-dashed border-[#D5D5CD] px-6 py-4 flex flex-wrap items-center justify-between gap-3" data-testid="mirrors-flag-check-line">
            <p className="text-sm text-[#6E6E66]">
              You’ve also done the <strong className="text-[#3B3B34]">Flag Check</strong> — kept apart from the
              instruments above, because it’s {FLAG.descriptor}.
            </p>
            <Link to="/flag-check" className="text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
              Revisit it →
            </Link>
          </div>
        )}

        <p className="mt-10 text-xs text-[#6E6E66] leading-relaxed max-w-xl" data-testid="mirrors-retrieval-note">
          {REGISTER.data_claim}
        </p>
      </div>
    </Shell>
  );
}

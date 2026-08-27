import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Shell from '../components/Shell';
import { API, instrumentByKey, readSessions, saveSession, clearSession } from '../lib/mirrorTheme';
import { authHeaders } from '../lib/auth';
import { REGISTER } from '../content/register';

export default function Runner() {
  const { instrument } = useParams();
  const navigate = useNavigate();
  const meta = instrumentByKey[instrument];

  const [phase, setPhase] = useState('loading'); // loading | intro | run | interstitial | finish | error
  const [payload, setPayload] = useState(null);
  const [answers, setAnswers] = useState({});
  const [idx, setIdx] = useState(0);
  const [busy, setBusy] = useState(false);
  const shownAt = useRef(Date.now());
  const revs = useRef({});
  const interShown = useRef(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      const existing = readSessions()[instrument];
      if (existing) {
        try {
          const res = await fetch(`${API}/api/v2/assessments/${existing}`, { headers: authHeaders() });
          if (res.ok) {
            const data = await res.json();
            if (!alive) return;
            if (data.status === 'complete') {
              navigate(`/results/${existing}`, { replace: true });
              return;
            }
            setPayload(data);
            setAnswers(data.responses || {});
            setPhase('intro');
            return;
          }
          clearSession(instrument);
        } catch {
          /* fall through to fresh intro */
        }
      }
      if (alive) setPhase('intro');
    })();
    return () => { alive = false; };
  }, [instrument, navigate]);

  const putAnswer = useCallback((sessionId, itemId, value, ms, rev) => {
    fetch(`${API}/api/v2/assessments/${sessionId}/responses`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ responses: [{ item_id: itemId, value, ms, rev }] }),
    }).catch(() => {});
  }, []);

  const begin = async () => {
    if (payload) {
      const first = payload.items.findIndex((it) => answers[it.id] == null);
      const startIdx = first === -1 ? payload.items.length : first;
      if (payload.interstitial && startIdx > payload.interstitial.after_index) interShown.current = true;
      setIdx(startIdx);
      setPhase(startIdx >= payload.items.length ? 'finish' : 'run');
      shownAt.current = Date.now();
      return;
    }
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/v2/assessments`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ instrument }),
      });
      if (!res.ok) throw new Error('start failed');
      const data = await res.json();
      saveSession(instrument, data.session_id);
      setPayload(data);
      setAnswers({});
      setIdx(0);
      setPhase('run');
      shownAt.current = Date.now();
    } catch {
      setPhase('error');
    } finally {
      setBusy(false);
    }
  };

  const advance = useCallback((fromIdx) => {
    const next = fromIdx + 1;
    if (payload?.interstitial && next === payload.interstitial.after_index + 1 && !interShown.current) {
      interShown.current = true;
      setPhase('interstitial');
      setIdx(next);
      return;
    }
    if (next >= payload.items.length) {
      setPhase('finish');
      return;
    }
    setIdx(next);
    shownAt.current = Date.now();
  }, [payload]);

  const select = useCallback((value) => {
    if (phase !== 'run' || !payload) return;
    const item = payload.items[idx];
    const rev = answers[item.id] != null ? (revs.current[item.id] || 0) + 1 : 0;
    revs.current[item.id] = rev;
    const ms = Date.now() - shownAt.current;
    setAnswers((prev) => ({ ...prev, [item.id]: value }));
    putAnswer(payload.session_id, item.id, value, ms, rev);
    setTimeout(() => advance(idx), 200);
  }, [phase, payload, idx, answers, advance, putAnswer]);

  useEffect(() => {
    const onKey = (e) => {
      if (phase !== 'run' || !payload) return;
      const n = parseInt(e.key, 10);
      const max = payload.scale ? payload.scale.length : 2;
      if (n >= 1 && n <= max) select(n);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [phase, payload, select]);

  const complete = async () => {
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/v2/assessments/${payload.session_id}/complete`, { method: 'POST', headers: authHeaders() });
      if (!res.ok) throw new Error('complete failed');
      navigate(`/results/${payload.session_id}`);
    } catch {
      setPhase('error');
    } finally {
      setBusy(false);
    }
  };

  if (!meta) {
    return (
      <Shell title="Not found">
        <div className="max-w-2xl mx-auto px-5 py-24">
          <p className="text-[#3B3B34]">That instrument doesn’t exist.</p>
          <Link className="underline underline-offset-4 mt-4 inline-block" to="/">Back to Rather Know</Link>
        </div>
      </Shell>
    );
  }

  if (phase === 'loading' || phase === 'intro' || phase === 'error') {
    const instructions = payload?.instructions;
    return (
      <Shell title={meta.name} description={meta.tagline}>
        <div className="max-w-2xl mx-auto px-5 sm:px-8 py-16 sm:py-24">
          {phase === 'loading' ? (
            <p className="text-[#6E6E66]" data-testid="runner-loading">Preparing…</p>
          ) : phase === 'error' ? (
            <div data-testid="runner-error">
              <p className="text-[#3B3B34]">Something went wrong saving your session. Nothing is lost — try again.</p>
              <button onClick={() => window.location.reload()} className="mt-4 underline underline-offset-4">Reload</button>
            </div>
          ) : (
            <div className="mi2-fade">
              <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]" data-testid="runner-tier">{meta.tier} instrument</p>
              <h1 className="mi2-serif mt-4 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="runner-intro-title">
                {instructions?.title || meta.name}
              </h1>
              <div className="mt-6 space-y-4">
                {(instructions?.paragraphs || [meta.blurb]).map((p, i) => (
                  <p key={i} className="text-base text-[#3B3B34] leading-relaxed">{p}</p>
                ))}
              </div>
              <div className="mt-8 border-t border-[#E4E4DE] pt-5 text-sm text-[#6E6E66] space-y-1.5">
                <p>{meta.items} · {meta.minutes}</p>
                <p>No timer, no pressure. Stop whenever you like — your progress is saved as you go.</p>
                <p>{REGISTER.account_claim}</p>
              </div>
              <div className="mt-9 flex items-center gap-5">
                <button
                  onClick={begin}
                  disabled={busy}
                  data-testid="runner-start-btn"
                  className="bg-[#1C1C18] text-[#F6F6F2] px-7 py-3 rounded-sm text-sm hover:opacity-85 disabled:opacity-50"
                >
                  {payload && Object.keys(answers).length > 0 ? 'Continue where you left off' : 'Begin'}
                </button>
                <Link to="/" className="text-sm text-[#6E6E66] hover:text-[#1C1C18]">Not now</Link>
              </div>
              <p className="mt-8 text-xs text-[#6E6E66]">
                <Link to="/safety" data-testid="intro-safety-exit" className="underline underline-offset-4">
                  If you’re afraid of someone, start here
                </Link>
              </p>
            </div>
          )}
        </div>
      </Shell>
    );
  }

  const total = payload.items.length;

  if (phase === 'interstitial') {
    return (
      <Shell title={meta.name} minimal>
        <div className="min-h-screen flex items-center justify-center px-5">
          <div className="max-w-xl mi2-fade">
            <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">
              {payload.instrument === 'everyday' ? 'Part two of two' : 'Lens two of two'}
            </p>
            <h2 className="mi2-serif mt-4 text-3xl text-[#1C1C18]">{payload.interstitial.title}</h2>
            <p className="mt-5 text-base text-[#3B3B34] leading-relaxed">{payload.interstitial.text}</p>
            <button
              onClick={() => { setPhase('run'); shownAt.current = Date.now(); }}
              data-testid="runner-interstitial-continue"
              className="mt-8 bg-[#1C1C18] text-[#F6F6F2] px-7 py-3 rounded-sm text-sm hover:opacity-85"
            >
              Continue
            </button>
          </div>
        </div>
      </Shell>
    );
  }

  if (phase === 'finish') {
    const unanswered = payload.items.filter((it) => answers[it.id] == null);
    const canComplete = payload.allow_skip || unanswered.length === 0;
    return (
      <Shell title={meta.name} minimal>
        <div className="min-h-screen flex items-center justify-center px-5">
          <div className="max-w-xl mi2-fade">
            <h2 className="mi2-serif text-3xl text-[#1C1C18]" data-testid="runner-finish-title">That’s the last one.</h2>
            {unanswered.length > 0 && (
              <p className="mt-4 text-sm text-[#6E6E66]" data-testid="runner-unanswered-note">
                {unanswered.length} statement{unanswered.length > 1 ? 's' : ''} left unanswered.
                {!canComplete && ' They need an answer before this can be scored.'}
                {canComplete && ' That’s fine — the scoring handles it honestly.'}
              </p>
            )}
            <div className="mt-8 flex items-center gap-5">
              {!canComplete ? (
                <button
                  onClick={() => {
                    const first = payload.items.findIndex((it) => answers[it.id] == null);
                    setIdx(first);
                    setPhase('run');
                    shownAt.current = Date.now();
                  }}
                  data-testid="runner-review-btn"
                  className="bg-[#1C1C18] text-[#F6F6F2] px-7 py-3 rounded-sm text-sm hover:opacity-85"
                >
                  Answer the missing ones
                </button>
              ) : (
                <button
                  onClick={complete}
                  disabled={busy}
                  data-testid="runner-complete-btn"
                  className="bg-[#1C1C18] text-[#F6F6F2] px-7 py-3 rounded-sm text-sm hover:opacity-85 disabled:opacity-50"
                >
                  {busy ? 'Scoring…' : 'See your result'}
                </button>
              )}
              <button
                onClick={() => { setIdx(total - 1); setPhase('run'); shownAt.current = Date.now(); }}
                className="text-sm text-[#6E6E66] hover:text-[#1C1C18]"
                data-testid="runner-back-from-finish"
              >
                Go back
              </button>
            </div>
          </div>
        </div>
      </Shell>
    );
  }

  const item = payload.items[idx];
  const selected = answers[item.id];

  return (
    <Shell title={meta.name} minimal>
      <div className="fixed top-0 left-0 right-0 z-30 h-[2px] bg-[#E4E4DE]">
        <div className="h-full bg-[#1C1C18] transition-[width] duration-300" style={{ width: `${(idx / total) * 100}%` }} />
      </div>
      <div className="min-h-screen flex flex-col px-5 sm:px-8">
        <div className="max-w-2xl w-full mx-auto pt-10 flex items-center justify-between text-xs text-[#6E6E66]">
          <span className="uppercase tracking-[0.14em]">{meta.name}</span>
          <span data-testid="runner-progress">{idx + 1} of {total}</span>
        </div>
        <div className="flex-1 flex items-center">
          <div className="max-w-2xl w-full mx-auto py-10" key={item.id}>
            <p className="mi2-fade text-2xl sm:text-3xl leading-relaxed text-[#1C1C18]" data-testid="runner-item-statement">
              {item.text}
            </p>
            {item.kind === 'choice' ? (
              <div className="mi2-fade mt-10 grid gap-3 sm:grid-cols-2" role="radiogroup" aria-label="Choose one">
                {item.options.map((label, i) => {
                  const value = i + 1;
                  const isSel = selected === value;
                  return (
                    <button
                      key={value}
                      role="radio"
                      aria-checked={isSel}
                      aria-label={label}
                      onClick={() => select(value)}
                      data-testid={`choice-option-${value}`}
                      className={`border px-5 py-6 text-left text-base leading-relaxed min-h-[7rem] flex items-center transition-colors ${
                        isSel
                          ? 'bg-[#1C1C18] text-[#F6F6F2] border-[#1C1C18]'
                          : 'bg-white text-[#3B3B34] border-[#E4E4DE] hover:border-[#1C1C18] hover:bg-[#FBFBF9]'
                      }`}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
            ) : (
            <div className="mi2-fade mt-10 grid gap-2" role="radiogroup" aria-label="Response scale">
              {payload.scale.map((label, i) => {
                const value = i + 1;
                const isSel = selected === value;
                return (
                  <button
                    key={value}
                    role="radio"
                    aria-checked={isSel}
                    aria-label={label}
                    onClick={() => select(value)}
                    data-testid={`scale-option-${value}`}
                    className={`flex items-center gap-4 border px-5 py-3.5 text-left text-sm sm:text-base ${
                      isSel
                        ? 'bg-[#1C1C18] text-[#F6F6F2] border-[#1C1C18]'
                        : 'bg-white text-[#3B3B34] border-[#E4E4DE] hover:border-[#1C1C18] hover:bg-[#FBFBF9]'
                    }`}
                  >
                    <span className={`w-6 h-6 flex items-center justify-center border text-xs shrink-0 ${isSel ? 'border-[#F6F6F2]/40' : 'border-[#D5D5CD] text-[#6E6E66]'}`}>
                      {value}
                    </span>
                    {label}
                  </button>
                );
              })}
            </div>
            )}
            {item.kind === 'choice' && (
              <p className="mi2-fade mt-5 text-xs text-[#6E6E66]">
                Neither answer is better, and there’s no way to keep both — pick the one you’d actually choose.
              </p>
            )}
          </div>
        </div>
        <div className="max-w-2xl w-full mx-auto pb-10 flex items-center justify-between text-sm">
          <button
            onClick={() => { if (idx > 0) { setIdx(idx - 1); shownAt.current = Date.now(); } }}
            disabled={idx === 0}
            data-testid="runner-back-btn"
            className="text-[#6E6E66] hover:text-[#1C1C18] disabled:opacity-30"
          >
            ← Back
          </button>
          {payload.allow_skip && (
            <button onClick={() => advance(idx)} data-testid="runner-skip-btn" className="text-[#6E6E66] hover:text-[#1C1C18]">
              Skip this one
            </button>
          )}
        </div>
      </div>
    </Shell>
  );
}

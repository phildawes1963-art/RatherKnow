import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import Shell from '../components/Shell';
import { API } from '../lib/mirrorTheme';
import { REGISTER } from '../content/register';

const STORE = 'rk.junction';

const SafetyFooter = () => (
  <div className="mt-10 border-t border-[#E4E4DE] pt-5" data-testid="junction-safety">
    <p className="text-xs text-[#6E6E66] leading-relaxed">
      If you’re ever afraid of someone, that isn’t a pattern to work on. National Domestic Abuse
      Helpline <strong>0808 2000 247</strong> (24/7, free) · Men’s Advice Line <strong>0808 8010 327</strong> ·
      In danger now: <strong>999</strong> ·{' '}
      <Link to="/safety" className="underline underline-offset-4">the full safety page</Link>
    </p>
  </div>
);

export default function Junction() {
  const [phase, setPhase] = useState('loading'); // loading | intro | run | result
  const [bank, setBank] = useState(null);
  const [id, setId] = useState(null);
  const [answers, setAnswers] = useState({});
  const [idx, setIdx] = useState(0);
  const [result, setResult] = useState(null);
  const [copied, setCopied] = useState(false);
  const busy = useRef(false);

  useEffect(() => {
    (async () => {
      const saved = localStorage.getItem(STORE);
      if (saved) {
        try {
          const res = await fetch(`${API}/api/v2/junction/${saved}`);
          if (res.ok) {
            const data = await res.json();
            setBank(data); setId(data.junction_id); setAnswers(data.answers || {});
            if (data.status === 'complete' && data.result) { setResult(data.result); setPhase('result'); }
            else setPhase('intro');
            return;
          }
          localStorage.removeItem(STORE);
        } catch { /* fresh */ }
      }
      const res = await fetch(`${API}/api/v2/junction/share-payload`);
      setBank(await res.json());
      setPhase('intro');
    })();
  }, []);

  const begin = async () => {
    if (busy.current) return;
    busy.current = true;
    try {
      if (!id) {
        const res = await fetch(`${API}/api/v2/junction/start`, { method: 'POST' });
        const data = await res.json();
        setBank(data); setId(data.junction_id);
        localStorage.setItem(STORE, data.junction_id);
      }
      setPhase('run');
    } finally { busy.current = false; }
  };

  const answer = async (itemId, value) => {
    const next = { ...answers, [itemId]: value };
    setAnswers(next);
    await fetch(`${API}/api/v2/junction/${id}/answers`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers: [{ item_id: itemId, value }] }),
    });
  };

  const finish = async () => {
    const res = await fetch(`${API}/api/v2/junction/${id}/complete`, { method: 'POST' });
    setResult(await res.json());
    setPhase('result');
  };

  const share = async () => {
    const url = `${window.location.origin}/junction`;
    try {
      if (navigator.share) await navigator.share({ title: 'The Junction Check', url });
      else { await navigator.clipboard.writeText(url); setCopied(true); }
    } catch { /* dismissed */ }
  };

  if (phase === 'loading' || !bank) {
    return <Shell title="The Junction Check"><p className="text-sm text-[#6E6E66]">One moment…</p></Shell>;
  }

  const items = bank.items;
  const item = items[idx];
  const fs = bank.first_screen;

  return (
    <Shell
      title="The Junction Check"
      description="Six questions of plain fact about where a life is heading. Free, no account, nothing scored."
    >
      <div className="max-w-2xl mx-auto px-5 sm:px-8 py-12">
        {phase === 'intro' && (
          <div data-testid="junction-intro">
            <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Free · six questions · no account</p>
            <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="junction-title">
              {fs.title}
            </h1>
            <div className="mt-6 space-y-4">
              {fs.paragraphs.map((p) => (
                <p key={p} className="text-sm text-[#3B3B34] leading-relaxed">{p}</p>
              ))}
            </div>
            <p className="mt-6 border-l-2 border-[#7E8E77] pl-4 text-sm text-[#1C1C18] leading-relaxed"
               data-testid="junction-instruction">
              {fs.instruction}
            </p>
            <p className="mt-4 text-sm text-[#6E6E66]">{fs.dont_know}</p>
            <button onClick={begin} data-testid="junction-begin"
                    className="mt-8 bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85 transition-opacity">
              Start — six questions
            </button>
            <SafetyFooter />
          </div>
        )}

        {phase === 'run' && (
          <div data-testid="junction-run">
            <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]" data-testid="junction-progress">
              {idx + 1} of {items.length}
            </p>
            <h1 className="mi2-serif mt-3 text-2xl sm:text-3xl text-[#1C1C18]" data-testid="junction-item-title">
              {item.title}
            </h1>
            <p className="mt-5 text-base text-[#1C1C18]" data-testid="junction-question">{item.question}</p>
            <div className="mt-4 space-y-2">
              {item.options.map((o) => (
                <button
                  key={o.value}
                  data-testid={`junction-option-${item.id}-${o.value}`}
                  onClick={() => answer(item.id, o.value)}
                  className={`w-full text-left border px-5 py-3 text-sm transition-colors ${
                    answers[item.id] === o.value
                      ? 'border-[#1C1C18] bg-white text-[#1C1C18]'
                      : 'border-[#E4E4DE] bg-white/60 text-[#3B3B34] hover:border-[#9C9C93]'
                  }`}
                >
                  {o.label}
                </button>
              ))}
            </div>

            {item.follow_up && (item.follow_up.shown_when === 'always'
              || item.follow_up.shown_when.includes(answers[item.id])) && (
              <div className="mt-7 border-t border-[#E4E4DE] pt-5" data-testid={`junction-followup-${item.follow_up.id}`}>
                <p className="text-base text-[#1C1C18]">{item.follow_up.question}</p>
                <div className="mt-3 space-y-2">
                  {item.follow_up.options.map((o) => (
                    <button
                      key={o.value}
                      data-testid={`junction-option-${item.follow_up.id}-${o.value}`}
                      onClick={() => answer(item.follow_up.id, o.value)}
                      className={`w-full text-left border px-5 py-3 text-sm transition-colors ${
                        answers[item.follow_up.id] === o.value
                          ? 'border-[#1C1C18] bg-white text-[#1C1C18]'
                          : 'border-[#E4E4DE] bg-white/60 text-[#3B3B34] hover:border-[#9C9C93]'
                      }`}
                    >
                      {o.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <p className="mt-7 text-sm text-[#6E6E66] leading-relaxed" data-testid="junction-framing">{item.framing}</p>

            <div className="mt-8 flex items-center gap-5">
              {idx > 0 && (
                <button onClick={() => setIdx(idx - 1)} data-testid="junction-back"
                        className="text-sm underline underline-offset-4 text-[#3B3B34]">Back</button>
              )}
              {idx < items.length - 1 ? (
                <button onClick={() => setIdx(idx + 1)} data-testid="junction-next"
                        disabled={!answers[item.id]}
                        className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm disabled:opacity-40">
                  Next
                </button>
              ) : (
                <button onClick={finish} data-testid="junction-finish"
                        disabled={!answers[item.id]}
                        className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm disabled:opacity-40">
                  See what you said
                </button>
              )}
            </div>
            <SafetyFooter />
          </div>
        )}

        {phase === 'result' && result && (
          <div data-testid="junction-result">
            <h1 className="mi2-serif text-3xl sm:text-4xl text-[#1C1C18]">{result.answers_heading}</h1>
            <ul className="mt-6 bg-white border border-[#E4E4DE]" data-testid="junction-written-back">
              {result.written_back.map((row) => (
                <li key={row.item_id} className="px-5 sm:px-6 py-5 border-b border-[#E4E4DE] last:border-0">
                  <p className="text-sm text-[#1C1C18]"><strong>{row.title}</strong> — {row.said}</p>
                  <p className="mt-2 text-sm text-[#6E6E66] leading-relaxed">{row.framing}</p>
                </li>
              ))}
            </ul>

            <section className="mt-10" data-testid="junction-finding">
              <h2 className="mi2-serif text-2xl text-[#1C1C18]">{result.finding_heading}</h2>
              <p className="mt-3 text-base text-[#1C1C18]" data-testid="junction-finding-lead">{result.finding.lead}</p>
              <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">{result.finding.body}</p>
            </section>

            <section className="mt-10 border border-[#E4E4DE] bg-white p-6" data-testid="junction-share">
              <button onClick={share} data-testid="junction-share-button"
                      className="w-full bg-[#1C1C18] text-[#F6F6F2] px-6 py-4 rounded-sm text-sm text-left hover:opacity-85">
                <span className="block">{result.share.button}</span>
                <span className="block mt-1.5 text-xs text-[#F6F6F2]/70">{result.share.sub}</span>
              </button>
              {copied && <p className="mt-3 text-xs text-[#7E8E77]" data-testid="junction-share-copied">Link copied.</p>}
              <p className="mt-3 text-xs text-[#6E6E66] leading-relaxed">{result.share.note}</p>
            </section>

            <p className="mt-8 text-sm text-[#3B3B34] leading-relaxed" data-testid="junction-discomfort">
              {result.discomfort_note}
            </p>

            <section className="mt-10 border-t border-[#E4E4DE] pt-6" data-testid="junction-closing">
              <p className="mi2-serif text-xl text-[#1C1C18]">{REGISTER.junction.closing_lead}</p>
              <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">{REGISTER.junction.closing_body}</p>
            </section>

            <section className="mt-10 border border-[#E4E4DE] bg-white p-6" data-testid="junction-save-offer">
              <p className="text-sm text-[#3B3B34] leading-relaxed">
                Want to keep this? An account saves it to come back to — and it’s the same door as the
                four longer mirrors, which are about how you travel rather than where the line goes.
              </p>
              <Link to="/register" data-testid="junction-save-cta"
                    className="mt-4 inline-block border border-[#1C1C18] px-5 py-2.5 text-sm text-[#1C1C18] hover:bg-[#1C1C18] hover:text-[#F6F6F2] transition-colors">
                Save this to an account
              </Link>
            </section>
            <SafetyFooter />
          </div>
        )}
      </div>
    </Shell>
  );
}

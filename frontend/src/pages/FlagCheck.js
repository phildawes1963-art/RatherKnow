import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Shell from '../components/Shell';
import { API, readReflections, saveReflection, clearReflection } from '../lib/mirrorTheme';
import { FLAG } from '../content/register';
import { breadcrumbJsonLd } from '../lib/siteMeta';

const InlineRoutes = () => (
  <p className="text-sm leading-relaxed" data-testid="flag-inline-routes">
    National Domestic Abuse Helpline <strong>0808 2000 247</strong> (24/7, free) · Men’s Advice Line{' '}
    <strong>0808 8010 327</strong> · In danger now: <strong>999</strong> ·{' '}
    <Link to="/safety" className="underline underline-offset-4">the full safety page</Link>
  </p>
);

const SafetySplit = () => (
  <div className="border border-[#E4E4DE] bg-white px-5 py-4 text-[#3B3B34]" data-testid="flag-safety-split">
    <p className="text-sm leading-relaxed">
      <strong>{FLAG.safety_split_lead}</strong> {FLAG.safety_split}{' '}
      <Link to="/safety" className="underline underline-offset-4">this one is</Link>.
    </p>
  </div>
);

export default function FlagCheck() {
  const [phase, setPhase] = useState('loading'); // loading | intro | run | result | error
  const [payload, setPayload] = useState(null);
  const [answers, setAnswers] = useState({});
  const [idx, setIdx] = useState(0);
  const [result, setResult] = useState(null);
  const busy = useRef(false);

  const allItems = payload ? [...payload.items, payload.safety_item] : [];

  useEffect(() => {
    (async () => {
      const existing = readReflections().flag_check;
      if (existing) {
        try {
          const res = await fetch(`${API}/api/v2/reflections/${existing}`);
          if (res.ok) {
            const data = await res.json();
            setPayload(data);
            setAnswers(data.responses || {});
            if (data.status === 'complete' && data.result) {
              setResult(data.result);
              setPhase('result');
            } else {
              setPhase('intro');
            }
            return;
          }
          clearReflection('flag_check');
        } catch { /* fresh */ }
      }
      setPhase('intro');
    })();
  }, []);

  const begin = async () => {
    if (payload) {
      const first = allItems.findIndex((it) => answers[it.id] == null);
      setIdx(first === -1 ? 0 : first);
      setPhase('run');
      return;
    }
    try {
      const res = await fetch(`${API}/api/v2/reflections`, { method: 'POST' });
      const data = await res.json();
      saveReflection('flag_check', data.reflection_id);
      setPayload(data);
      setAnswers({});
      setIdx(0);
      setPhase('run');
    } catch {
      setPhase('error');
    }
  };

  const finish = useCallback(async (reflectionId) => {
    if (busy.current) return;
    busy.current = true;
    try {
      const res = await fetch(`${API}/api/v2/reflections/${reflectionId}/complete`, { method: 'POST' });
      const data = await res.json();
      setResult(data);
      setPhase('result');
      window.scrollTo(0, 0);
    } catch {
      setPhase('error');
    } finally {
      busy.current = false;
    }
  }, []);

  const select = (value) => {
    const item = allItems[idx];
    const next = { ...answers, [item.id]: value };
    setAnswers(next);
    fetch(`${API}/api/v2/reflections/${payload.reflection_id}/responses`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ responses: [{ item_id: item.id, value }] }),
    }).catch(() => {});
    setTimeout(() => {
      if (idx + 1 >= allItems.length) finish(payload.reflection_id);
      else setIdx(idx + 1);
    }, 200);
  };

  if (phase === 'result' && result) {
    const copy = FLAG.patterns[result.pattern] || FLAG.patterns.insufficient;
    return (
      <Shell title="Flag Check — your reflection" description="A reflection, not a measure.">
        <div className="max-w-2xl mx-auto px-5 sm:px-8 py-14 sm:py-20 space-y-10">
          <header>
            <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]" data-testid="flag-result-label">
              {FLAG.label}
            </p>
            <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="flag-result-title">
              {copy.title}
            </h1>
          </header>

          {result.safety === 'yes' ? (
            <section className="bg-[#1C1C18] text-[#F6F6F2] p-7 sm:p-8" data-testid="flag-safety-yes">
              <p className="mi2-serif text-xl leading-snug">{FLAG.safety_yes_lead}</p>
              <p className="mt-4 text-sm leading-relaxed text-[#F6F6F2]/85">{FLAG.safety_yes_body}</p>
              <div className="mt-4 text-[#F6F6F2]/90"><InlineRoutes /></div>
            </section>
          ) : result.safety === 'unsure' ? (
            <section className="border border-[#C8AE93] bg-[#C8AE93]/10 px-6 py-5 text-[#3B3B34]" data-testid="flag-safety-unsure">
              <p className="text-sm leading-relaxed">{FLAG.safety_unsure_body}</p>
              <div className="mt-3"><InlineRoutes /></div>
            </section>
          ) : (
            <SafetySplit />
          )}

          <section data-testid="flag-profile">
            <p className="text-base text-[#3B3B34] leading-relaxed">{copy.body}</p>
          </section>

          <section className="bg-white border border-[#E4E4DE] p-7" data-testid="flag-graduated">
            <p className="text-xs uppercase tracking-[0.14em] text-[#6E6E66]">The graduated response</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-4">
              {FLAG.stages.map(([name, desc], i) => (
                <div key={name} className="border-t-2 border-[#7E8E77] pt-2">
                  <p className="text-sm font-medium text-[#1C1C18]">{i + 1}. {name}</p>
                  <p className="mt-1 text-xs text-[#6E6E66] leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
            <p className="mt-5 text-sm text-[#3B3B34] leading-relaxed">{copy.position}</p>
            <p className="mt-4 text-xs text-[#6E6E66] leading-relaxed border-t border-[#E4E4DE] pt-3">
              {FLAG.graduated_note} <Link to="/safety" className="underline underline-offset-4">the safety page</Link>.
            </p>
          </section>

          <p className="text-xs text-[#6E6E66] leading-relaxed" data-testid="flag-disclosure">{FLAG.disclosure}</p>

          <section className="border-t border-[#E4E4DE] pt-8">
            <p className="text-base text-[#3B3B34] leading-relaxed max-w-xl">{FLAG.cta_body}</p>
            <Link to="/take/essential" data-testid="flag-cta-essential" className="mt-5 inline-block bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85">
              {FLAG.cta_label}
            </Link>
          </section>
        </div>
      </Shell>
    );
  }

  if (phase === 'run' && payload) {
    const item = allItems[idx];
    const isSafety = item.id === 'f-safety';
    const options = isSafety ? payload.safety_item.options : payload.options;
    return (
      <Shell title="Flag Check" minimal>
        <div className="fixed top-0 left-0 right-0 z-30 h-[2px] bg-[#E4E4DE]">
          <div className="h-full bg-[#1C1C18] transition-[width] duration-300" style={{ width: `${(idx / allItems.length) * 100}%` }} />
        </div>
        <div className="min-h-screen flex flex-col px-5 sm:px-8">
          <div className="max-w-2xl w-full mx-auto pt-10 flex items-center justify-between text-xs text-[#6E6E66]">
            <span className="uppercase tracking-[0.14em]">Flag Check · {FLAG.descriptor}</span>
            <span data-testid="flag-progress">{idx + 1} of {allItems.length}</span>
          </div>
          <div className="flex-1 flex items-center">
            <div className="max-w-2xl w-full mx-auto py-10" key={item.id}>
              {!isSafety && (
                <p className="mi2-fade text-xs uppercase tracking-[0.14em] text-[#6E6E66] mb-4">{FLAG.prompt}</p>
              )}
              <p className="mi2-fade text-xl sm:text-2xl leading-relaxed text-[#1C1C18]" data-testid="flag-item-statement">
                {item.text}
              </p>
              <div className="mi2-fade mt-8 grid gap-2" role="radiogroup">
                {options.map((label, i) => {
                  const value = i + 1;
                  const isSel = answers[item.id] === value;
                  return (
                    <button
                      key={value}
                      role="radio"
                      aria-checked={isSel}
                      onClick={() => select(value)}
                      data-testid={`flag-option-${value}`}
                      className={`border px-5 py-3.5 text-left text-sm sm:text-base ${
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
            </div>
          </div>
          <div className="max-w-2xl w-full mx-auto pb-10 text-sm">
            <button
              onClick={() => idx > 0 && setIdx(idx - 1)}
              disabled={idx === 0}
              data-testid="flag-back-btn"
              className="text-[#6E6E66] hover:text-[#1C1C18] disabled:opacity-30"
            >
              ← Back
            </button>
          </div>
        </div>
      </Shell>
    );
  }

  return (
    <Shell
      title="Flag Check — a reflection"
      description="It reads you, not them. A reflection, not a measure."
      jsonLd={breadcrumbJsonLd([{ name: 'Rather Know', path: '/' }, { name: 'Flag Check' }])}
    >
      <div className="max-w-2xl mx-auto px-5 sm:px-8 py-16 sm:py-24">
        {phase === 'loading' ? (
          <p className="text-[#6E6E66]" data-testid="flag-loading">Preparing…</p>
        ) : phase === 'error' ? (
          <div data-testid="flag-error">
            <p className="text-[#3B3B34]">Something went wrong. Nothing is lost — try again.</p>
            <button onClick={() => window.location.reload()} className="mt-4 underline underline-offset-4">Reload</button>
          </div>
        ) : (
          <div className="mi2-fade space-y-7">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">{FLAG.descriptor}</p>
              <h1 className="mi2-serif mt-4 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="flag-intro-title">
                The Flag Check.
              </h1>
              <p className="mt-2 text-base text-[#5B7284]">{FLAG.subtitle}</p>
            </div>

            <SafetySplit />

            <div className="space-y-4 text-base text-[#3B3B34] leading-relaxed">
              {FLAG.intro_paragraphs.map((p, i) => <p key={i}>{p}</p>)}
            </div>
            <div className="border-t border-[#E4E4DE] pt-5 text-sm text-[#6E6E66] space-y-1.5">
              {FLAG.intro_meta.map((p, i) => <p key={i}>{p}</p>)}
            </div>
            <div className="flex items-center gap-5">
              <button onClick={begin} data-testid="flag-start-btn" className="bg-[#1C1C18] text-[#F6F6F2] px-7 py-3 rounded-sm text-sm hover:opacity-85">
                {payload && Object.keys(answers).length > 0 ? 'Continue where you left off' : 'Begin'}
              </button>
              <Link to="/" className="text-sm text-[#6E6E66] hover:text-[#1C1C18]">Not now</Link>
            </div>
          </div>
        )}
      </div>
    </Shell>
  );
}

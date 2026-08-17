import { useState } from 'react';
import { Link, useNavigate, useSearchParams, Navigate } from 'react-router-dom';
import Shell from '../components/Shell';
import { useAuth } from '../lib/auth';
import { REGISTER } from '../content/register';

const SITUATIONS = [
  { key: 'single_dating', label: 'Single & dating', note: 'Reading the pattern before the next one starts.' },
  { key: 'in_relationship', label: 'In a relationship', note: 'Understanding how you are when you’re close to someone.' },
  { key: 'post_breakup', label: 'Post-breakup', note: 'Working out what just happened, and what you keep choosing.' },
];

export default function Auth({ mode }) {
  const isRegister = mode === 'register';
  const { user, register, login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get('next') || '/mirrors';

  const [form, setForm] = useState({ name: '', email: '', password: '', situation: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={next} replace />;

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (isRegister && !form.situation) {
      setError('Pick where you are right now — it changes how the report is written.');
      return;
    }
    setBusy(true);
    try {
      if (isRegister) {
        await register({ name: form.name, email: form.email, password: form.password, situation: form.situation });
      } else {
        await login({ email: form.email, password: form.password });
      }
      navigate(next, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Shell
      title={isRegister ? 'Create your account' : 'Log in'}
      description={isRegister ? 'Three fields, and the instruments open.' : 'Log in to retrieve your reports.'}
    >
      <div className="max-w-xl mx-auto px-5 sm:px-8 py-14 sm:py-20">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">{isRegister ? 'Free — no card' : 'Welcome back'}</p>
        <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="auth-title">
          {isRegister ? 'Three fields, then the mirrors open.' : 'Log in to your reports.'}
        </h1>
        <p className="mt-4 text-base text-[#3B3B34] leading-relaxed">
          {isRegister
            ? 'A name, an email and where you are right now — that’s the minimum needed to write the report for you and to hand it back when you return. Nothing else is asked.'
            : 'Your results appear on screen and stay retrievable here. Nothing is emailed to you.'}
        </p>

        <form onSubmit={submit} className="mt-9 space-y-5" data-testid="auth-form">
          {isRegister && (
            <label className="block">
              <span className="text-xs uppercase tracking-[0.12em] text-[#6E6E66]">Your name</span>
              <input
                type="text"
                required
                value={form.name}
                onChange={set('name')}
                data-testid="auth-name"
                className="mt-2 w-full bg-white border border-[#E4E4DE] px-4 py-3 text-base text-[#1C1C18] focus:outline-none focus:border-[#1C1C18]"
                placeholder="What should the report call you?"
              />
            </label>
          )}
          <label className="block">
            <span className="text-xs uppercase tracking-[0.12em] text-[#6E6E66]">Email</span>
            <input
              type="email"
              required
              value={form.email}
              onChange={set('email')}
              data-testid="auth-email"
              className="mt-2 w-full bg-white border border-[#E4E4DE] px-4 py-3 text-base text-[#1C1C18] focus:outline-none focus:border-[#1C1C18]"
              placeholder="you@example.com"
            />
          </label>
          <label className="block">
            <span className="text-xs uppercase tracking-[0.12em] text-[#6E6E66]">Password</span>
            <input
              type="password"
              required
              minLength={isRegister ? 8 : undefined}
              value={form.password}
              onChange={set('password')}
              data-testid="auth-password"
              className="mt-2 w-full bg-white border border-[#E4E4DE] px-4 py-3 text-base text-[#1C1C18] focus:outline-none focus:border-[#1C1C18]"
              placeholder={isRegister ? 'At least 8 characters' : 'Your password'}
            />
          </label>

          {isRegister && (
            <fieldset data-testid="auth-situation">
              <legend className="text-xs uppercase tracking-[0.12em] text-[#6E6E66]">Where are you right now?</legend>
              <div className="mt-3 grid gap-2">
                {SITUATIONS.map((s) => {
                  const active = form.situation === s.key;
                  return (
                    <button
                      type="button"
                      key={s.key}
                      onClick={() => setForm({ ...form, situation: s.key })}
                      data-testid={`auth-situation-${s.key}`}
                      aria-pressed={active}
                      className={`border px-5 py-3.5 text-left ${
                        active
                          ? 'bg-[#1C1C18] text-[#F6F6F2] border-[#1C1C18]'
                          : 'bg-white text-[#3B3B34] border-[#E4E4DE] hover:border-[#1C1C18]'
                      }`}
                    >
                      <span className="block text-sm sm:text-base">{s.label}</span>
                      <span className={`block text-xs mt-0.5 ${active ? 'text-[#F6F6F2]/70' : 'text-[#6E6E66]'}`}>{s.note}</span>
                    </button>
                  );
                })}
              </div>
            </fieldset>
          )}

          {error && (
            <p className="text-sm text-[#8C3A2B] border border-[#8C3A2B]/30 bg-[#8C3A2B]/5 px-4 py-3" data-testid="auth-error">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            data-testid="auth-submit"
            className="w-full bg-[#1C1C18] text-[#F6F6F2] px-6 py-3.5 rounded-sm text-sm hover:opacity-85 disabled:opacity-50"
          >
            {busy ? 'One moment…' : isRegister ? 'Create account & begin' : 'Log in'}
          </button>
        </form>

        <p className="mt-6 text-sm text-[#3B3B34]">
          {isRegister ? (
            <>
              Already have an account?{' '}
              <Link to={`/login?next=${encodeURIComponent(next)}`} data-testid="auth-switch-login" className="underline underline-offset-4">
                Log in
              </Link>
            </>
          ) : (
            <>
              No account yet?{' '}
              <Link to={`/register?next=${encodeURIComponent(next)}`} data-testid="auth-switch-register" className="underline underline-offset-4">
                Create one — free
              </Link>
            </>
          )}
        </p>

        <p className="mt-8 border-t border-[#E4E4DE] pt-5 text-sm text-[#6E6E66] leading-relaxed" data-testid="auth-data-claim">
          {REGISTER.data_claim}
        </p>
        <p className="mt-3 text-xs text-[#6E6E66]">
          <Link to="/promise" className="underline underline-offset-4">The promise in full</Link>
          {' · '}
          <Link to="/flag-check" className="underline underline-offset-4">The Flag Check needs no account</Link>
        </p>
      </div>
    </Shell>
  );
}

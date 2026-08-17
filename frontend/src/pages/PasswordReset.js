import { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import Shell from '../components/Shell';
import { API } from '../lib/mirrorTheme';
import { formatApiErrorDetail } from '../lib/auth';

export function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(formatApiErrorDetail(data.detail));
      setSent(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Shell title="Forgotten password" description="We’ll email you a link to set a new one.">
      <div className="max-w-xl mx-auto px-5 sm:px-8 py-14 sm:py-20">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Account</p>
        <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="forgot-title">
          A way back in.
        </h1>
        {sent ? (
          <div className="mt-6 space-y-4" data-testid="forgot-sent">
            <p className="text-base text-[#3B3B34] leading-relaxed">
              If that email has an account, a link to set a new password is on its way. It works once and expires in
              60 minutes.
            </p>
            <p className="text-sm text-[#6E6E66] leading-relaxed">
              We don’t say whether an account exists — that would tell anyone who asked. This is still the only email
              we ever send you: reports stay on screen.
            </p>
            <Link to="/login" data-testid="forgot-back-to-login" className="inline-block text-sm underline underline-offset-4">
              Back to log in
            </Link>
          </div>
        ) : (
          <>
            <p className="mt-4 text-base text-[#3B3B34] leading-relaxed">
              Give us the email on your account and we’ll send a single-use link to choose a new password. It’s the
              one email we send — your reports are never emailed to you.
            </p>
            <form onSubmit={submit} className="mt-8 space-y-5" data-testid="forgot-form">
              <label className="block">
                <span className="text-xs uppercase tracking-[0.12em] text-[#6E6E66]">Email</span>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  data-testid="forgot-email"
                  className="mt-2 w-full bg-white border border-[#E4E4DE] px-4 py-3 text-base text-[#1C1C18] focus:outline-none focus:border-[#1C1C18]"
                  placeholder="you@example.com"
                />
              </label>
              {error && <p className="text-sm text-[#8C3A2B]" data-testid="forgot-error">{error}</p>}
              <button
                type="submit"
                disabled={busy}
                data-testid="forgot-submit"
                className="w-full bg-[#1C1C18] text-[#F6F6F2] px-6 py-3.5 rounded-sm text-sm hover:opacity-85 disabled:opacity-50"
              >
                {busy ? 'Sending…' : 'Send the link'}
              </button>
            </form>
            <p className="mt-6 text-sm text-[#3B3B34]">
              Remembered it?{' '}
              <Link to="/login" className="underline underline-offset-4">Log in</Link>
            </p>
          </>
        )}
      </div>
    </Shell>
  );
}

export function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get('token') || '';
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (password !== confirm) {
      setError('Those two don’t match.');
      return;
    }
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(formatApiErrorDetail(data.detail));
      localStorage.setItem('rk.token', data.access_token);
      window.location.assign('/mirrors');
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <Shell title="Set a new password">
      <div className="max-w-xl mx-auto px-5 sm:px-8 py-14 sm:py-20">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Account</p>
        <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="reset-title">
          Choose a new password.
        </h1>
        {!token ? (
          <div className="mt-6" data-testid="reset-no-token">
            <p className="text-base text-[#3B3B34]">That link is missing its token. Ask for a fresh one.</p>
            <Link to="/forgot-password" className="mt-4 inline-block text-sm underline underline-offset-4">
              Send another link
            </Link>
          </div>
        ) : (
          <form onSubmit={submit} className="mt-8 space-y-5" data-testid="reset-form">
            <label className="block">
              <span className="text-xs uppercase tracking-[0.12em] text-[#6E6E66]">New password</span>
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                data-testid="reset-password"
                className="mt-2 w-full bg-white border border-[#E4E4DE] px-4 py-3 text-base text-[#1C1C18] focus:outline-none focus:border-[#1C1C18]"
                placeholder="At least 8 characters"
              />
            </label>
            <label className="block">
              <span className="text-xs uppercase tracking-[0.12em] text-[#6E6E66]">Again, to be sure</span>
              <input
                type="password"
                required
                minLength={8}
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                data-testid="reset-confirm"
                className="mt-2 w-full bg-white border border-[#E4E4DE] px-4 py-3 text-base text-[#1C1C18] focus:outline-none focus:border-[#1C1C18]"
                placeholder="Repeat it"
              />
            </label>
            {error && <p className="text-sm text-[#8C3A2B]" data-testid="reset-error">{error}</p>}
            <button
              type="submit"
              disabled={busy}
              data-testid="reset-submit"
              className="w-full bg-[#1C1C18] text-[#F6F6F2] px-6 py-3.5 rounded-sm text-sm hover:opacity-85 disabled:opacity-50"
            >
              {busy ? 'Saving…' : 'Save it and log me in'}
            </button>
            <button type="button" onClick={() => navigate('/login')} className="text-sm text-[#6E6E66] hover:text-[#1C1C18]">
              Cancel
            </button>
          </form>
        )}
      </div>
    </Shell>
  );
}

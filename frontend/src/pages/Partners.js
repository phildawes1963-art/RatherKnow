import { useState } from 'react';
import { Link } from 'react-router-dom';
import Shell from '../components/Shell';
import { API } from '../lib/mirrorTheme';

const AUDIENCE = [
  { value: 'practice', label: 'A private practice or client list' },
  { value: 'newsletter', label: 'A newsletter or mailing list' },
  { value: 'social', label: 'A social following' },
  { value: 'podcast', label: 'A podcast or video channel' },
  { value: 'organisation', label: 'An organisation, clinic or training body' },
  { value: 'other', label: 'Somewhere else' },
];

const REFUSALS = [
  'It never asks about anyone but the person answering.',
  'It produces no compatibility score, and never will.',
  'It gives no types, boxes or quadrants.',
  'It predicts nothing.',
  'It publishes an evidence tier on every instrument, including the ones still being established.',
  'It publishes the equations behind its composite scores.',
  "It won't report a difference smaller than its own margin of error — if the numbers are too close to distinguish, the report says so and stops.",
  'It stamps a version on every result and never recomputes it, so a report says the same thing in five years as it did on the day.',
  'It carries domestic abuse and crisis referrals on every page, free, behind no paywall.',
  'And it says plainly, at the top of the promise, that it cannot find anyone love.',
];

const TERMS = [
  ['30% of every purchase', 'made by someone who came through you, for twelve months from their first visit. Paid monthly, no minimum, no threshold to clear before you’re paid.'],
  ['No exclusivity.', 'Work with whoever else you like.'],
  ['No lock-in.', 'Leave whenever, and we’ll pay what’s owed.'],
  ['Your own link, and a dashboard', 'showing clicks, completions and earnings — so you can see whether it’s working rather than take our word for it.'],
  ['Free access for you.', 'You should have done the whole thing before you recommend it, and we’re not charging you to find out whether you want to.'],
];

const WONT = [
  'We won’t email your audience. We have no relationship with them and we don’t want one that goes around you.',
  'We won’t ask for your list, ever.',
  'We won’t put you in a tier system or run a leaderboard.',
  'We won’t change the terms on you mid-year.',
  'And if we change the instruments, you’ll hear it from us before your clients do.',
];

const Section = ({ kicker, title, children, testid, dark = false }) => (
  <section
    data-testid={testid}
    className={dark ? 'bg-[#1C1C18] text-[#F6F6F2]' : ''}
  >
    <div className="max-w-4xl mx-auto px-5 sm:px-8 py-14 sm:py-18">
      {kicker && (
        <p className={`text-xs uppercase tracking-[0.18em] ${dark ? 'text-[#F6F6F2]/50' : 'text-[#6E6E66]'}`}>{kicker}</p>
      )}
      <h2 className={`mi2-serif mt-3 text-2xl md:text-3xl ${dark ? 'text-[#F6F6F2]' : 'text-[#1C1C18]'}`}>{title}</h2>
      <div className="mt-6">{children}</div>
    </div>
  </section>
);

export default function Partners() {
  const [form, setForm] = useState({ name: '', email: '', audience_where: 'practice', audience_size: '', why_it_fits: '' });
  const [state, setState] = useState({ status: 'idle', message: '' });

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setState({ status: 'sending', message: '' });
    try {
      const res = await fetch(`${API}/api/partners/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setState({ status: 'error', message: data.detail || 'That didn’t send. Try again in a moment.' });
        return;
      }
      setState({ status: 'done', message: data.message });
    } catch {
      setState({ status: 'error', message: 'That didn’t send. Try again in a moment.' });
    }
  };

  return (
    <Shell
      title="Partner with us"
      description="For coaches, therapists and practitioners: a self-reflection instrument that produces no compatibility score, no type and no prediction — which is why it's safe to put your name next to."
    >
      <section className="max-w-4xl mx-auto px-5 sm:px-8 pt-16 pb-12 sm:pt-24">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">For practitioners</p>
        <h1 className="mi2-serif mt-5 text-4xl sm:text-5xl leading-[1.08] text-[#1C1C18]" data-testid="partners-h1">
          Something you can hand a client without wincing.
        </h1>
        <p className="mt-7 text-base md:text-lg text-[#3B3B34] leading-relaxed max-w-2xl">
          Rather Know is a self-reflection instrument for people making, or reconsidering, the largest decision of
          their lives. It produces no compatibility score, no type, and no prediction — which is exactly why it’s
          safe to put your name next to.
        </p>
        <div className="mt-9 flex flex-wrap items-center gap-5">
          <a href="#apply" data-testid="partners-hero-apply" className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85">
            Apply to partner
          </a>
          <p className="text-sm text-[#6E6E66]">Revenue share, no minimums, no exclusivity.</p>
        </div>
      </section>

      <Section kicker="What your client gets" title="A document, not a verdict." testid="partners-what-client-gets">
        <div className="space-y-5 text-base text-[#3B3B34] leading-relaxed max-w-2xl">
          <p>
            Four to six instruments, depending on how far they go, read together rather than reported separately.
            What comes out is a description of how they choose — the speed of it, what they over-weight, what they
            miss, and what their particular combination costs to be around.
          </p>
          <p>
            It’s written to be brought into a room. Several of our early users have taken it to a session and worked
            from it, which is the use we designed for.
          </p>
          <Link to="/samples" data-testid="partners-samples-link" className="inline-block text-sm underline underline-offset-4 text-[#1C1C18] hover:opacity-70">
            Read a full sample reading →
          </Link>
        </div>
      </Section>

      <Section kicker="Why it won't embarrass you" title="Ten things it will never do." testid="partners-refusals" dark>
        <ul className="space-y-3 text-sm md:text-base text-[#F6F6F2]/85 max-w-3xl" data-testid="partners-refusals-list">
          {REFUSALS.map((r) => (
            <li key={r} className="flex gap-3"><span className="text-[#7E8E77] shrink-0">—</span> {r}</li>
          ))}
        </ul>
        <Link to="/promise" data-testid="partners-promise-link" className="mt-7 inline-block text-sm underline underline-offset-4 text-[#F6F6F2]/80 hover:text-[#F6F6F2]">
          Read the full promise — seven promises, ten refusals →
        </Link>
      </Section>

      <Section kicker="What you get" title="The terms." testid="partners-terms">
        <dl className="space-y-5 max-w-2xl" data-testid="partners-terms-list">
          {TERMS.map(([lead, rest]) => (
            <div key={lead} className="text-base text-[#3B3B34] leading-relaxed">
              <span className="text-[#1C1C18] font-medium">{lead}</span> {rest}
            </div>
          ))}
        </dl>
      </Section>

      <Section kicker="What we won't do to you" title="The other half of the deal." testid="partners-wont">
        <ul className="space-y-3 text-base text-[#3B3B34] leading-relaxed max-w-2xl">
          {WONT.map((w) => (
            <li key={w} className="flex gap-3"><span className="text-[#7E8E77] shrink-0">—</span> {w}</li>
          ))}
        </ul>
      </Section>

      <Section kicker="Where we actually are" title="Honest about the stage." testid="partners-stage">
        <div className="space-y-5 text-base text-[#3B3B34] leading-relaxed max-w-2xl">
          <p>
            Two of our instruments are established, built on published research. Three are ours and still being
            established — we’re collecting the sample now, and we publish that status on every page they appear on.
          </p>
          <p>We’d rather tell you that than have you find out from a client.</p>
          <p>If you’d like to see the scoring specification, ask. We’ll send it.</p>
        </div>
      </Section>

      <Section kicker="Who this isn't for" title="We'd rather say now." testid="partners-not-for">
        <div className="space-y-5 text-base text-[#3B3B34] leading-relaxed max-w-2xl">
          <p>
            If your audience wants to be told who to date, this won’t satisfy them. If you’re looking for something
            to sell hard on a launch, this is the wrong product — it’s a slow, quiet recommendation that works best
            when someone is already asking a real question.
          </p>
          <p>It suits practitioners whose clients are trying to understand a pattern, not find a person.</p>
        </div>
      </Section>

      <section id="apply" className="border-t border-[#E4E4DE] bg-white/60">
        <div className="max-w-4xl mx-auto px-5 sm:px-8 py-16 sm:py-20">
          <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Apply</p>
          <h2 className="mi2-serif mt-3 text-2xl md:text-3xl text-[#1C1C18]">Four questions and your name.</h2>
          <p className="mt-4 text-base text-[#3B3B34] leading-relaxed max-w-2xl">
            We read them ourselves, and we say no to some — usually because the fit isn’t there, and we’ll tell you why.
          </p>

          {state.status === 'done' ? (
            <div className="mt-8 border border-[#7E8E77] bg-[#7E8E77]/10 p-6 max-w-2xl" data-testid="partners-apply-success">
              <p className="text-base text-[#1C1C18] leading-relaxed">{state.message}</p>
            </div>
          ) : (
            <form onSubmit={submit} className="mt-8 grid gap-5 max-w-2xl" data-testid="partners-apply-form">
              <label className="grid gap-1.5">
                <span className="text-sm text-[#3B3B34]">Your name</span>
                <input
                  required minLength={2} value={form.name} onChange={set('name')}
                  data-testid="partners-field-name"
                  className="border border-[#D5D5CD] bg-white px-4 py-3 text-sm text-[#1C1C18] focus:outline-none focus:border-[#1C1C18]"
                />
              </label>
              <label className="grid gap-1.5">
                <span className="text-sm text-[#3B3B34]">Email</span>
                <input
                  required type="email" value={form.email} onChange={set('email')}
                  data-testid="partners-field-email"
                  className="border border-[#D5D5CD] bg-white px-4 py-3 text-sm text-[#1C1C18] focus:outline-none focus:border-[#1C1C18]"
                />
              </label>
              <label className="grid gap-1.5">
                <span className="text-sm text-[#3B3B34]">Where your audience is</span>
                <select
                  value={form.audience_where} onChange={set('audience_where')}
                  data-testid="partners-field-audience"
                  className="border border-[#D5D5CD] bg-white px-4 py-3 text-sm text-[#1C1C18] focus:outline-none focus:border-[#1C1C18]"
                >
                  {AUDIENCE.map((a) => <option key={a.value} value={a.value}>{a.label}</option>)}
                </select>
              </label>
              <label className="grid gap-1.5">
                <span className="text-sm text-[#3B3B34]">Roughly how many</span>
                <input
                  required value={form.audience_size} onChange={set('audience_size')}
                  placeholder="A rough number is fine"
                  data-testid="partners-field-size"
                  className="border border-[#D5D5CD] bg-white px-4 py-3 text-sm text-[#1C1C18] focus:outline-none focus:border-[#1C1C18]"
                />
              </label>
              <label className="grid gap-1.5">
                <span className="text-sm text-[#3B3B34]">One sentence on why this fits them</span>
                <textarea
                  required minLength={10} rows={3} value={form.why_it_fits} onChange={set('why_it_fits')}
                  data-testid="partners-field-why"
                  className="border border-[#D5D5CD] bg-white px-4 py-3 text-sm text-[#1C1C18] focus:outline-none focus:border-[#1C1C18]"
                />
              </label>
              {state.status === 'error' && (
                <p className="text-sm text-[#B4553F]" data-testid="partners-apply-error">{state.message}</p>
              )}
              <div>
                <button
                  type="submit" disabled={state.status === 'sending'}
                  data-testid="partners-apply-submit"
                  className="bg-[#1C1C18] text-[#F6F6F2] px-7 py-3 rounded-sm text-sm hover:opacity-85 disabled:opacity-50"
                >
                  {state.status === 'sending' ? 'Sending…' : 'Apply to partner'}
                </button>
              </div>
            </form>
          )}
        </div>
      </section>
    </Shell>
  );
}

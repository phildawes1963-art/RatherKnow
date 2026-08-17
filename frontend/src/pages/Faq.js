import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Shell from '../components/Shell';

const FAQS = [
  {
    q: 'What does it cost?',
    a: 'Nothing, to start — and not as a trial. No card, nothing expires, nothing quietly converts. Paid depth is coming later, under a single published maximum for the whole practice; until that figure is on the promise page, nothing is purchasable.',
    links: [{ to: '/promise', label: 'The promise in full' }],
  },
  {
    q: 'Do I need an account?',
    a: 'No. Everything runs anonymously — no email, no sign-up, no profile. Your results are linked to this browser, which cuts both ways: nobody can identify you, and we can’t recover a result for you either. Clear your browser storage and the link to your results goes with it, so save the result URL if you want to keep it.',
  },
  {
    q: 'Can it tell me whether my partner is right for me?',
    a: 'No — and be suspicious of anything that says it can. No output here will ever give a verdict on another person, a compatibility percentage, or a prediction about your relationship. Every measurement is of you: how you choose, what you ask for, how you are when you’re close to someone.',
  },
  {
    q: 'Which mirror should I start with?',
    a: 'The Essential Mirror, if you have twenty-five minutes — it carries the core idea, the Delta. If you only have five, the Closeness Mirror is the shortest honest read. There’s no required order, and the cross-check gets more interesting with each one you add.',
    links: [{ to: '/take/essential', label: 'Start the Essential Mirror' }],
  },
  {
    q: 'How long does each one take?',
    a: 'Essential Mirror: about 25 minutes (50 questions, answered twice). Closeness Mirror: about 5 minutes (36 statements). Personality Mirror: 15–20 minutes (130 statements). EI Mirror: 15–20 minutes (140 statements). The Flag Check reflection: about 3 minutes.',
  },
  {
    q: 'What is the Delta?',
    a: 'The core measurement of the Essential Mirror. You answer the same fifty questions twice — once as yourself, once as the partner you say you want — and the Delta is the gap between the two, in points, with the workings shown. It turns “am I too picky?” into something you can actually look at.',
  },
  {
    q: 'What does “developmental” mean on an instrument?',
    a: 'It means the questions are ours and their statistical properties are still being established — so we say so, on the instrument itself, before you take it. Two of the four mirrors are built on established, validated measures; two are developmental. The word “validated” is only ever applied to the first kind.',
    links: [{ to: '/methodology', label: 'Every tier, published' }],
  },
  {
    q: 'Is this therapy, or a diagnosis?',
    a: 'Neither. It’s a self-reflection instrument, not a clinical tool — it will never label you or anyone you describe, and it doesn’t treat anything. It informs conversations; it does not replace professionals.',
  },
  {
    q: 'What happens to my answers?',
    a: 'They’re scored, and that’s it. Never sold, never shared, never used to train any model — contractually, not aspirationally. There’s no identity attached to them in the first place, which is the strongest privacy feature we have.',
  },
  {
    q: 'What is the Flag Check?',
    a: 'A three-minute reflection about something you noticed — what you saw, when, and what you did with it. It never asks about the other person, and it is deliberately unscored: no number, no band, no grade. A reflection, not a measure.',
    links: [{ to: '/flag-check', label: 'Take the Flag Check' }],
  },
  {
    q: 'What is the cross-check?',
    a: 'Once you’ve completed two or more mirrors, the cross-check reads them side by side. Where instruments agree, that’s signal. Where they disagree, that’s a finding — and it’s usually the more interesting one.',
    links: [{ to: '/mirrors', label: 'Your mirrors' }],
  },
  {
    q: 'What if I’m afraid of someone?',
    a: 'Then this isn’t the tool, and that isn’t a pattern to work on. The safety page exists for exactly this, is reachable without an account, and lists real places to go.',
    links: [{ to: '/safety', label: 'The safety page' }],
  },
];

export default function Faq() {
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: FAQS.map((f) => ({
      '@type': 'Question',
      name: f.q,
      acceptedAnswer: { '@type': 'Answer', text: f.a },
    })),
  };

  return (
    <Shell
      title="Questions, answered"
      description="What it costs, what it can and cannot tell you, and what happens to your answers — plainly."
    >
      <Helmet>
        <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
      </Helmet>
      <div className="max-w-3xl mx-auto px-5 sm:px-8 py-14 sm:py-20">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Rather Know — FAQ</p>
        <h1 className="mi2-serif mt-3 text-4xl sm:text-5xl text-[#1C1C18]" data-testid="faq-title">
          Questions, answered.
        </h1>
        <p className="mt-6 text-base text-[#3B3B34] leading-relaxed max-w-2xl">
          Plainly, and in one place. If an answer here ever contradicts the product, the product is wrong and we want
          to know.
        </p>

        <section className="mt-10 space-y-4" data-testid="faq-list">
          {FAQS.map((f, i) => (
            <div key={i} data-testid={`faq-item-${i + 1}`} className="bg-white border border-[#E4E4DE] p-6 sm:p-7">
              <h2 className="mi2-serif text-lg sm:text-xl text-[#1C1C18]">{f.q}</h2>
              <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed">{f.a}</p>
              {f.links && (
                <p className="mt-3">
                  {f.links.map((l) => (
                    <Link key={l.to} to={l.to} className="text-sm underline underline-offset-4 text-[#1C1C18] hover:opacity-70 mr-5">
                      {l.label} →
                    </Link>
                  ))}
                </p>
              )}
            </div>
          ))}
        </section>

        <div className="mt-12 flex flex-wrap items-center gap-5">
          <Link to="/take/essential" data-testid="faq-cta" className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85">
            Enough reading — start free
          </Link>
          <Link to="/samples" className="text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
            Or see a sample result first →
          </Link>
        </div>
      </div>
    </Shell>
  );
}

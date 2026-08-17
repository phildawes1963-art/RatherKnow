import { Link } from 'react-router-dom';
import Shell from '../components/Shell';
import { PROMISES, REFUSALS, REGISTER } from '../content/register';
import { breadcrumbJsonLd } from '../lib/siteMeta';

export default function Promise() {
  return (
    <Shell
      title="The promise"
      description="Seven promises and ten refusals, published in full."
      jsonLd={breadcrumbJsonLd([{ name: 'Rather Know', path: '/' }, { name: 'The promise' }])}
    >
      <div className="max-w-3xl mx-auto px-5 sm:px-8 py-14 sm:py-20">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Rather Know — manifesto</p>
        <h1 className="mi2-serif mt-3 text-4xl sm:text-5xl text-[#1C1C18]" data-testid="promise-title">
          The promise.
        </h1>
        <p className="mt-6 mi2-serif text-xl sm:text-2xl text-[#1C1C18] leading-snug max-w-2xl" data-testid="promise-opening">
          {REGISTER.promise_opening}
        </p>
        <p className="mt-5 text-base text-[#3B3B34] leading-relaxed max-w-2xl">
          This page is the whole deal, in writing. We would rather say less and be able to prove it — so everything
          below is either checkable by using the product, or a standing commitment you can hold us to.
        </p>

        <section className="mt-12 space-y-5" data-testid="promise-list">
          {PROMISES.map((p, i) => (
            <div key={i} data-testid={`promise-item-${i + 1}`} className="bg-white border border-[#E4E4DE] p-6 sm:p-7 flex gap-5">
              <span className="mi2-serif text-2xl text-[#C8AE93] leading-none pt-0.5">{String(i + 1).padStart(2, '0')}</span>
              <div>
                <h2 className="mi2-serif text-xl text-[#1C1C18]">{p.title}</h2>
                <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed">{p.body}</p>
              </div>
            </div>
          ))}
        </section>

        <section className="mt-14 bg-[#1C1C18] text-[#F6F6F2] p-8 sm:p-10" data-testid="promise-refusals">
          <h2 className="mi2-serif text-2xl sm:text-3xl">The refusals.</h2>
          <p className="mt-4 text-sm text-[#F6F6F2]/75 leading-relaxed max-w-xl">{REGISTER.refusals_intro}</p>
          <ul className="mt-6 grid gap-x-8 gap-y-3 sm:grid-cols-2 text-sm text-[#F6F6F2]/90">
            {REFUSALS.map((r, i) => (
              <li key={i} className="flex gap-3" data-testid={`promise-refusal-${i + 1}`}>
                <span className="text-[#7E8E77]">—</span> {r}
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-12 space-y-4 text-sm text-[#3B3B34] leading-relaxed max-w-2xl" data-testid="promise-close">
          {REGISTER.promise_close.map((p, i) => <p key={i}>{p}</p>)}
          <p>
            And if you’re ever afraid of someone, that isn’t a pattern to work on —{' '}
            <Link to="/safety" className="underline underline-offset-4" data-testid="promise-safety-link">
              here’s where to go instead
            </Link>.
          </p>
        </section>

        <div className="mt-12 flex flex-wrap items-center gap-5">
          <Link to="/take/essential" data-testid="promise-cta" className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85">
            Hold us to it — start free
          </Link>
          <Link to="/methodology" className="text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
            The methodology behind it →
          </Link>
        </div>
      </div>
    </Shell>
  );
}

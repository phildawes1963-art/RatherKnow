import { Link } from 'react-router-dom';
import Shell from '../components/Shell';
import { LEARN_ARTICLES } from '../content/miLearn';
import { breadcrumbJsonLd } from '../lib/siteMeta';

export default function Learn() {
  const pillar = LEARN_ARTICLES.find((a) => a.pillar) || LEARN_ARTICLES[0];
  const rest = LEARN_ARTICLES.filter((a) => a.slug !== pillar.slug);
  const clusters = [...new Set(rest.map((a) => a.cluster))];

  return (
    <Shell
      title="Learn"
      description="Essays on patterns, choosing, and what an assessment is actually for."
      jsonLd={breadcrumbJsonLd([{ name: 'Rather Know', path: '/' }, { name: 'Learn' }])}
    >
      <div className="max-w-5xl mx-auto px-5 sm:px-8 py-14 sm:py-20">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Learn</p>
        <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]" data-testid="learn-title">
          Read before you measure.
        </h1>
        <p className="mt-4 text-base text-[#3B3B34] max-w-2xl leading-relaxed">
          No listicles, no hacks, no promises about other people. Essays about the pattern, the choosing, and what an
          instrument can honestly do.
        </p>

        <Link to={`/learn/${pillar.slug}`} data-testid="learn-pillar" className="mt-10 block bg-[#1C1C18] text-[#F6F6F2] p-8 sm:p-10 hover:opacity-95">
          <p className="text-[11px] uppercase tracking-[0.14em] text-[#F6F6F2]/60">{pillar.cluster} · {pillar.readMins} min · the pillar</p>
          <h2 className="mi2-serif mt-4 text-2xl sm:text-3xl leading-snug">{pillar.h1}</h2>
          <p className="mt-4 text-sm md:text-base text-[#F6F6F2]/75 max-w-2xl leading-relaxed">{pillar.dek}</p>
          <p className="mt-5 text-sm underline underline-offset-4">Read it →</p>
        </Link>

        {clusters.map((cluster) => (
          <section key={cluster} className="mt-12">
            <p className="text-xs uppercase tracking-[0.14em] text-[#6E6E66] border-b border-[#E4E4DE] pb-3">{cluster}</p>
            <div className="mt-5 grid gap-5 md:grid-cols-2">
              {rest.filter((a) => a.cluster === cluster).map((a) => (
                <Link
                  key={a.slug}
                  to={`/learn/${a.slug}`}
                  data-testid={`learn-card-${a.slug}`}
                  className="bg-white border border-[#E4E4DE] p-6 hover:shadow-[0_2px_16px_rgba(28,28,24,0.06)]"
                >
                  <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">{a.readMins} min</p>
                  <h3 className="mi2-serif mt-2 text-lg leading-snug text-[#1C1C18]">{a.h1}</h3>
                  <p className="mt-3 text-sm text-[#6E6E66] leading-relaxed">{a.dek}</p>
                </Link>
              ))}
            </div>
          </section>
        ))}

        <div className="mt-14 border border-[#E4E4DE] bg-white px-6 py-6 flex flex-wrap items-center justify-between gap-4">
          <p className="mi2-serif text-lg text-[#1C1C18]">Reading about the pattern isn’t the same as naming yours.</p>
          <Link to="/take/essential" data-testid="learn-cta" className="text-sm bg-[#1C1C18] text-[#F6F6F2] px-5 py-2.5 rounded-sm hover:opacity-85">
            Take the free read
          </Link>
        </div>
      </div>
    </Shell>
  );
}

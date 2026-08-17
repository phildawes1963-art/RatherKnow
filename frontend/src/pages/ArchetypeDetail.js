import { useParams, Link, Navigate } from 'react-router-dom';
import Shell from '../components/Shell';
import { ARCHETYPE_CONTENT, ARCHETYPE_ORDER } from '../content/archetypeContent';
import { ARCH_KEY_BY_SLUG, ARCH_SLUG_BY_KEY, ARCHETYPE_SEO, SITE, breadcrumbJsonLd } from '../lib/siteMeta';

const Section = ({ title, children, testid }) => (
  <div data-testid={testid}>
    <h2 className="mi2-serif text-2xl sm:text-3xl text-[#1C1C18]">{title}</h2>
    <div className="mt-3 text-base text-[#3B3B34] leading-relaxed">{children}</div>
  </div>
);

export default function ArchetypeDetail() {
  const { slug } = useParams();
  const key = ARCH_KEY_BY_SLUG[slug];
  if (!key) return <Navigate to="/archetypes" replace />;

  const a = ARCHETYPE_CONTENT[key];
  const seo = ARCHETYPE_SEO[slug];
  const shadow = ARCHETYPE_CONTENT[a.shadowArchetype];
  const others = ARCHETYPE_ORDER.filter((k) => k !== key);
  const card = `/mirror-index/cards/${key}.png`;

  const jsonLd = [
    {
      '@context': 'https://schema.org',
      '@type': 'Article',
      headline: seo.h1,
      description: seo.description,
      image: `${SITE.baseUrl}${card}`,
      author: { '@type': 'Organization', name: SITE.name },
      publisher: { '@type': 'Organization', name: SITE.name },
      mainEntityOfPage: `${SITE.baseUrl}/archetypes/${slug}`,
    },
    breadcrumbJsonLd([
      { name: 'Rather Know', path: '/' },
      { name: 'The six archetypes', path: '/archetypes' },
      { name: a.name },
    ]),
  ];

  return (
    <Shell title={seo.title} description={seo.description} ogImage={card} jsonLd={jsonLd}>
      <div className="max-w-4xl mx-auto px-5 sm:px-8 py-14 sm:py-20">
        <p className="text-xs text-[#6E6E66]">
          <Link to="/archetypes" className="hover:text-[#1C1C18]">The archetypes</Link>
          <span className="mx-2">/</span>
          <span className="text-[#1C1C18]">{a.name}</span>
        </p>

        <div className="mt-8 grid gap-10 md:grid-cols-[1.6fr_1fr] items-start">
          <div>
            <p className="text-[11px] uppercase tracking-[0.14em] text-[#6E6E66]">{a.tagline}</p>
            <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl lg:text-5xl leading-tight text-[#1C1C18]" data-testid="archetype-detail-h1">
              {seo.h1}
            </h1>
            <p className="mt-3 mi2-serif text-lg italic text-[#5B7284]">{a.epithet}</p>
            <p className="mt-5 text-base text-[#3B3B34] leading-relaxed">{a.selfDescription}</p>
          </div>
          <figure className="bg-white border border-[#E4E4DE] p-5" data-testid="archetype-detail-card">
            <img src={card} alt={`${a.name} — archetype card`} className="w-full" />
            <a href={card} download={`ratherknow-${key}.png`} className="mt-3 block text-center text-xs underline underline-offset-4 text-[#3B3B34]">
              Download this card ↓
            </a>
          </figure>
        </div>

        <div className="mt-14 space-y-12">
          <Section title="How love lands" testid="archetype-love-lands">
            <p>{a.howLoveLands}</p>
          </Section>

          <Section title="Green flags to look for" testid="archetype-green-flags">
            <ul className="divide-y divide-[#E4E4DE] border-y border-[#E4E4DE]">
              {a.greenFlags.map((g) => <li key={g} className="py-3">{g}</li>)}
            </ul>
          </Section>

          <Section title="The shadow" testid="archetype-shadow-section">
            <p>{a.shadowSide}</p>
          </Section>
        </div>
      </div>

      <section className="bg-[#1C1C18] text-[#F6F6F2] mt-14" data-testid="archetype-detail-shadow-band">
        <div className="max-w-4xl mx-auto px-5 sm:px-8 py-16">
          <p className="text-xs uppercase tracking-[0.18em] text-[#C8AE93]">Secretly drawn to</p>
          <h2 className="mi2-serif mt-4 text-2xl sm:text-3xl">{shadow.name}</h2>
          <p className="mt-4 text-base leading-relaxed text-[#F6F6F2]/90">{a.shadowArchetypeNote}</p>
          <Link to={`/archetypes/${ARCH_SLUG_BY_KEY[a.shadowArchetype]}`} className="mt-5 inline-block text-sm underline underline-offset-4 text-[#F6F6F2]/80 hover:text-[#F6F6F2]">
            Read about {shadow.name} →
          </Link>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-5 sm:px-8 py-16 space-y-12">
        <Section title="Who’s drawn to you" testid="archetype-drawn-to-you">
          <p>{a.drawnToYou}</p>
        </Section>
        <Section title="Your ideal partner" testid="archetype-ideal-partner">
          <p>{a.idealPartner}</p>
        </Section>

        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">The other five</p>
          <div className="mt-4 flex flex-wrap gap-2" data-testid="archetype-crosslinks">
            {others.map((k) => (
              <Link
                key={k}
                to={`/archetypes/${ARCH_SLUG_BY_KEY[k]}`}
                className="border border-[#E4E4DE] bg-white px-4 py-2 text-sm text-[#3B3B34] hover:border-[#1C1C18]"
              >
                {ARCHETYPE_CONTENT[k].name}
              </Link>
            ))}
          </div>
        </div>

        <div className="border border-[#E4E4DE] bg-white p-7 flex flex-wrap items-center justify-between gap-5">
          <p className="mi2-serif text-lg text-[#1C1C18] max-w-md">
            Are you really {a.name}? The Essential Mirror measures it — and the one you keep choosing.
          </p>
          <Link to="/take/essential" data-testid="archetype-detail-cta" className="bg-[#1C1C18] text-[#F6F6F2] px-6 py-3 rounded-sm text-sm hover:opacity-85">
            Find your archetype — free
          </Link>
        </div>
      </div>
    </Shell>
  );
}

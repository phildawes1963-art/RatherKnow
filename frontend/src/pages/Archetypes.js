import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import Shell from '../components/Shell';
import { ARCHETYPE_CONTENT, ARCHETYPE_ORDER } from '../content/archetypeContent';
import { ARCH_SLUG_BY_KEY, breadcrumbJsonLd } from '../lib/siteMeta';

export default function Archetypes() {
  const [params] = useSearchParams();
  const initial = params.get('focus');
  const [active, setActive] = useState(ARCHETYPE_ORDER.includes(initial) ? initial : 'rock');
  const a = ARCHETYPE_CONTENT[active];
  const shadow = ARCHETYPE_CONTENT[a.shadowArchetype];

  return (
    <Shell
      title="The six archetypes"
      description="Six relationship archetypes, two lenses, one honest read of who you actually need."
      jsonLd={breadcrumbJsonLd([{ name: 'Rather Know', path: '/' }, { name: 'The six archetypes' }])}
    >
      <div className="max-w-6xl mx-auto px-5 sm:px-8 py-14 sm:py-20">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">The six archetypes</p>
        <div className="mt-3 grid gap-10 md:grid-cols-[1.3fr_1fr] items-center">
          <div>
            <h1 className="mi2-serif text-3xl sm:text-4xl lg:text-5xl leading-tight text-[#1C1C18]" data-testid="archetypes-h1">
              Each one a gift. Each one a shadow.
            </h1>
            <p className="mt-5 text-base text-[#3B3B34] leading-relaxed max-w-xl">
              The Essential Mirror doesn’t hand you one archetype and call it a personality. It maps all six — what each
              offers a partner, where each tends to break, who each is quietly drawn to, and who is quietly drawn to you.
            </p>
            <a
              href="/docs/ratherknow-archetypes.pdf"
              target="_blank"
              rel="noopener"
              data-testid="archetypes-guide-pdf"
              className="mt-6 inline-block text-sm underline underline-offset-4 text-[#1C1C18] hover:opacity-70"
            >
              Read the full guide to all six (PDF) →
            </a>
          </div>
          <figure className="justify-self-center max-w-sm">
            <img
              src="/mirror-index/illus/hexagon_wheel.png"
              alt="The six archetypes — Rock, Challenger, Empath, Voyager, Diplomat and Torchbearer — arranged in a hexagon."
              data-testid="archetypes-hexagon"
              className="w-full"
              style={{ mixBlendMode: 'multiply' }}
            />
          </figure>
        </div>

        <div role="tablist" className="mt-12 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2" data-testid="archetypes-tabs">
          {ARCHETYPE_ORDER.map((key) => {
            const ar = ARCHETYPE_CONTENT[key];
            const isActive = active === key;
            return (
              <button
                key={key}
                role="tab"
                aria-selected={isActive}
                data-testid={`archetype-tab-${key}`}
                onClick={() => setActive(key)}
                className={`border px-4 py-3 text-left ${
                  isActive
                    ? 'bg-[#1C1C18] text-[#F6F6F2] border-[#1C1C18]'
                    : 'bg-white text-[#3B3B34] border-[#E4E4DE] hover:border-[#1C1C18]'
                }`}
              >
                <span className="block text-[11px] uppercase tracking-[0.12em] opacity-70">{ar.tagline}</span>
                <span className="mi2-serif text-base">{ar.name}</span>
              </button>
            );
          })}
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-[1.6fr_1fr]" data-testid={`archetype-detail-${active}`}>
          <div className="space-y-6">
            <div className="bg-white border border-[#E4E4DE] p-7 sm:p-9">
              <p className="text-[11px] uppercase tracking-[0.14em] text-[#6E6E66]">{a.tagline}</p>
              <h2 className="mi2-serif mt-3 text-3xl sm:text-4xl text-[#1C1C18]">{a.name}</h2>
              <p className="mt-2 mi2-serif text-lg italic text-[#5B7284]" data-testid={`archetype-epithet-${active}`}>{a.epithet}</p>
              <p className="mt-5 text-base text-[#3B3B34] leading-relaxed">{a.selfDescription}</p>
            </div>

            <div className="bg-[#1C1C18] text-[#F6F6F2] p-7 sm:p-9" data-testid={`archetype-shadow-${active}`}>
              <p className="text-xs uppercase tracking-[0.18em] text-[#C8AE93]">The shadow side</p>
              <p className="mt-4 text-base leading-relaxed text-[#F6F6F2]/90">{a.shadowSide}</p>
            </div>

            <div className="grid gap-5 sm:grid-cols-2">
              <div className="bg-white border border-[#E4E4DE] p-6">
                <p className="text-[11px] uppercase tracking-[0.14em] text-[#7E8E77]">Green flags in a partner</p>
                <ul className="mt-3 divide-y divide-[#E4E4DE] text-sm text-[#3B3B34]">
                  {a.greenFlags.map((g) => <li key={g} className="py-2">{g}</li>)}
                </ul>
              </div>
              <div className="bg-white border border-[#E4E4DE] p-6">
                <p className="text-[11px] uppercase tracking-[0.14em] text-[#C8AE93]">How love lands</p>
                <p className="mt-3 mi2-serif text-lg leading-snug text-[#1C1C18]">{a.howLoveLands}</p>
                <p className="mt-5 text-[11px] uppercase tracking-[0.14em] text-[#C8AE93]">Ideal partner</p>
                <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed">{a.idealPartner}</p>
              </div>
            </div>
          </div>

          <aside className="space-y-5">
            <figure className="bg-white border border-[#E4E4DE] p-5">
              <img
                src={`/mirror-index/cards/${active}.png`}
                alt={`${a.name} — archetype card`}
                className="w-full"
                data-testid={`archetype-card-${active}`}
              />
              <a
                href={`/mirror-index/cards/${active}.png`}
                download={`ratherknow-${active}.png`}
                data-testid={`archetype-card-download-${active}`}
                className="mt-3 block text-center text-xs underline underline-offset-4 text-[#3B3B34]"
              >
                Download this card ↓
              </a>
            </figure>
            <Link
              to={`/archetypes/${ARCH_SLUG_BY_KEY[active]}`}
              data-testid={`archetype-fullprofile-${active}`}
              className="block border border-[#E4E4DE] bg-white px-5 py-4 text-sm text-[#1C1C18] hover:border-[#1C1C18]"
            >
              Read the full {a.name} profile →
            </Link>
            <div className="border border-[#5B7284] bg-white p-6" data-testid={`archetype-shadow-map-${active}`}>
              <p className="text-[11px] uppercase tracking-[0.14em] text-[#6E6E66]">{a.name} is unconsciously drawn to</p>
              <p className="mi2-serif mt-2 text-2xl text-[#1C1C18]">{shadow.name}</p>
              <p className="text-[11px] uppercase tracking-[0.14em] text-[#6E6E66]">{shadow.tagline}</p>
              <p className="mt-4 text-sm text-[#3B3B34] leading-relaxed">{a.shadowArchetypeNote}</p>
            </div>
            <div className="border border-[#E4E4DE] bg-white p-6" data-testid={`archetype-drawn-${active}`}>
              <p className="text-[11px] uppercase tracking-[0.14em] text-[#7E8E77]">Who’s drawn to you</p>
              <p className="mt-3 text-sm text-[#3B3B34] leading-relaxed">{a.drawnToYou}</p>
            </div>
            <Link
              to="/take/essential"
              data-testid="archetypes-cta"
              className="block text-center bg-[#1C1C18] text-[#F6F6F2] px-5 py-3 text-sm rounded-sm hover:opacity-85"
            >
              Meet your archetype — free
            </Link>
            <p className="text-xs text-[#6E6E66] text-center">Two lenses · about 25 minutes · free</p>
          </aside>
        </div>

        <section className="mt-16 border-t border-[#E4E4DE] pt-10" data-testid="archetypes-pairings">
          <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">The full map</p>
          <h2 className="mi2-serif mt-3 text-2xl sm:text-3xl text-[#1C1C18] max-w-xl">
            Every archetype, and the partner-type it unconsciously chases.
          </h2>
          <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {ARCHETYPE_ORDER.map((key) => {
              const ar = ARCHETYPE_CONTENT[key];
              const sh = ARCHETYPE_CONTENT[ar.shadowArchetype];
              return (
                <button
                  key={key}
                  data-testid={`archetype-pair-${key}`}
                  onClick={() => setActive(key)}
                  className="bg-white border border-[#E4E4DE] p-5 text-left hover:border-[#1C1C18]"
                >
                  <p className="mi2-serif text-lg text-[#1C1C18]">{ar.name}</p>
                  <p className="text-[11px] uppercase tracking-[0.12em] text-[#6E6E66]">chases</p>
                  <p className="mi2-serif text-lg text-[#5B7284]">{sh.name}</p>
                </button>
              );
            })}
          </div>
        </section>
      </div>
    </Shell>
  );
}

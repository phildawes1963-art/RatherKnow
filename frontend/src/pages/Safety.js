import Shell from '../components/Shell';
import { SAFETY } from '../content/register';
import { breadcrumbJsonLd } from '../lib/siteMeta';

export default function Safety() {
  return (
    <Shell
      title="Safety"
      description="If you're afraid of someone, that isn't a pattern to work on. Here's where to go."
      jsonLd={breadcrumbJsonLd([{ name: 'Rather Know', path: '/' }, { name: 'Safety' }])}
    >
      <div className="max-w-2xl mx-auto px-5 sm:px-8 py-14 sm:py-20">
        <p className="text-xs uppercase tracking-[0.18em] text-[#6E6E66]">Safety</p>
        <h1 className="mi2-serif mt-3 text-3xl sm:text-4xl leading-tight text-[#1C1C18]" data-testid="safety-title">
          {SAFETY.headline}
        </h1>

        <div className="mt-7 space-y-4 text-base text-[#3B3B34] leading-relaxed">
          {SAFETY.paragraphs.map((p, i) => <p key={i}>{p}</p>)}
          <p className="mi2-serif text-lg text-[#1C1C18]" data-testid="safety-floor">{SAFETY.floor}</p>
        </div>

        <div className="mt-10 space-y-4" data-testid="safety-routes">
          {SAFETY.routes.map((r) => (
            <div key={r.name} className="bg-white border border-[#E4E4DE] px-6 py-5">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="text-base font-medium text-[#1C1C18]">{r.name}</p>
                <p className="text-base text-[#5B7284] font-medium">{r.contact}</p>
              </div>
              <p className="mt-1.5 text-sm text-[#6E6E66] leading-relaxed">{r.detail}</p>
              {r.link && (
                <a href={r.link} target="_blank" rel="noreferrer" className="mt-2 inline-block text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
                  {r.link.replace('https://', '')}
                </a>
              )}
            </div>
          ))}
        </div>

        <p className="mt-8 text-sm text-[#6E6E66] leading-relaxed">{SAFETY.outside_uk}</p>
      </div>
    </Shell>
  );
}

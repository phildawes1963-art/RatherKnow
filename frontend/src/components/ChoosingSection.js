import { Link } from 'react-router-dom';

// The translation layer: what these numbers do at the point of choosing.
export default function ChoosingSection({ choosing }) {
  if (!choosing) return null;
  return (
    <section className="mt-12 border-t border-[#1C1C18] pt-8" data-testid="choosing-section">
      <p className="text-[11px] uppercase tracking-[0.12em] text-[#7E8E77]">A study of how you choose</p>
      <h2 className="mi2-serif mt-2 text-2xl sm:text-3xl text-[#1C1C18]" data-testid="choosing-title">
        What this does at the point of choosing.
      </h2>
      <p className="mt-3 text-base text-[#3B3B34] leading-relaxed max-w-2xl">{choosing.lead}</p>

      <div className="mt-7 space-y-4">
        {choosing.points.map((p, i) => (
          <div
            key={i}
            data-testid={`choosing-point-${i + 1}`}
            className="bg-white border border-[#E4E4DE] border-l-2 border-l-[#5B7284] p-6"
          >
            <h3 className="mi2-serif text-lg text-[#1C1C18]">{p.title}</h3>
            <p className="mt-2 text-sm text-[#3B3B34] leading-relaxed">{p.body}</p>
          </div>
        ))}
      </div>

      <p className="mt-5 text-xs text-[#6E6E66] leading-relaxed max-w-2xl" data-testid="choosing-closing">
        {choosing.closing}{' '}
        <Link to="/methodology" className="underline underline-offset-4">How this is derived</Link>.
      </p>
    </section>
  );
}

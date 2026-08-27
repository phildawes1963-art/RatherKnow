import { Link, useLocation } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import '../styles/mirror.css';
import { SITE, isIndexable } from '../lib/siteMeta';
import { ATTRIBUTION, DISCLAIMER, SAFETY, REGISTER } from '../content/register';
import { useAuth } from '../lib/auth';

const NAV = [
  { to: '/methodology', label: 'The instruments' },
  { to: '/archetypes', label: 'Archetypes' },
  { to: '/promise', label: 'Promise' },
  { to: '/learn', label: 'Learn' },
  { to: '/safety', label: 'Safety' },
];

export default function Shell({ title, description, children, minimal = false, jsonLd, ogImage }) {
  const { pathname } = useLocation();
  const { user, logout } = useAuth();
  const canonical = `${SITE.baseUrl}${pathname}`;
  const fullTitle = title ? `${title} · ${SITE.name}` : `${SITE.name} — ${SITE.descriptor}`;
  const image = `${SITE.baseUrl}${ogImage || SITE.ogImage}`;

  return (
    <div className="mi2 mi2-noise">
      <Helmet>
        <title>{fullTitle}</title>
        {description && <meta name="description" content={description} />}
        <link rel="canonical" href={canonical} />
        {!isIndexable(pathname) && <meta name="robots" content="noindex, nofollow" />}
        <meta property="og:title" content={fullTitle} />
        {description && <meta property="og:description" content={description} />}
        <meta property="og:url" content={canonical} />
        <meta property="og:image" content={image} />
        <meta property="og:type" content="website" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={fullTitle} />
        {description && <meta name="twitter:description" content={description} />}
        <meta name="twitter:image" content={image} />
        {jsonLd && <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>}
      </Helmet>

      {!minimal && (
        <header className="sticky top-0 z-20 border-b border-[#E4E4DE] bg-[#F6F6F2]/95 backdrop-blur">
          <div className="max-w-6xl mx-auto px-5 sm:px-8 h-16 flex items-center justify-between">
            <Link to="/" data-testid="nav-home" className="flex items-baseline gap-3">
              <span className="mi2-serif text-xl tracking-tight text-[#1C1C18]">
                Rather Know<span className="text-[#7E8E77]">.</span>
              </span>
              <span className="hidden md:inline text-[11px] uppercase tracking-[0.14em] text-[#6E6E66]">
                {SITE.descriptor}
              </span>
            </Link>
            <nav className="flex items-center gap-4 sm:gap-7">
              {NAV.map((n) => (
                <Link
                  key={n.to}
                  to={n.to}
                  data-testid={`nav-${n.label.toLowerCase().replace(/\s/g, '-')}`}
                  className="hidden sm:inline text-sm text-[#3B3B34] hover:text-[#1C1C18]"
                >
                  {n.label}
                </Link>
              ))}
              {user ? (
                <>
                  <Link to="/mirrors" data-testid="nav-your-mirrors" className="hidden sm:inline text-sm text-[#3B3B34] hover:text-[#1C1C18]">
                    Your mirrors
                  </Link>
                  <button onClick={logout} data-testid="nav-logout" className="text-sm text-[#6E6E66] hover:text-[#1C1C18]">
                    Log out
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" data-testid="nav-login" className="text-xs text-[#6E6E66] hover:text-[#1C1C18]">
                    Log in
                  </Link>
                  <Link
                    to="/register"
                    data-testid="nav-start"
                    className="text-sm bg-[#1C1C18] text-[#F6F6F2] px-4 py-2 rounded-sm hover:opacity-85"
                  >
                    Start free
                  </Link>
                </>
              )}
            </nav>
          </div>
        </header>
      )}

      {minimal && (
        <div className="fixed bottom-4 right-4 z-30">
          <Link
            to="/safety"
            data-testid="runner-safety-exit"
            className="text-xs bg-white border border-[#E4E4DE] px-3 py-2 text-[#3B3B34] hover:text-[#1C1C18]"
          >
            {SAFETY.exit_link}
          </Link>
        </div>
      )}

      <main className="relative z-10">{children}</main>

      {!minimal && (
        <footer className="relative z-10 border-t border-[#E4E4DE] mt-24">
          <div className="max-w-6xl mx-auto px-5 sm:px-8 py-14 grid gap-10 sm:grid-cols-3">
            <div>
              <p className="mi2-serif text-lg text-[#1C1C18]">Rather Know.</p>
              <p className="mt-3 text-sm text-[#6E6E66] leading-relaxed max-w-xs">
                A relationship assessment for people who’d rather know than be reassured.
              </p>
              <p className="mt-4 text-xs text-[#6E6E66]" data-testid="footer-attribution">{ATTRIBUTION}</p>
              {user && (
                <p className="mt-3 text-xs text-[#6E6E66]" data-testid="footer-signed-in">
                  Signed in as {user.name} · {user.situation_label}
                </p>
              )}
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.1em] text-[#6E6E66] mb-3">The instruments</p>
              <ul className="space-y-2 text-sm">
                <li><Link className="text-[#3B3B34] hover:text-[#1C1C18]" to="/take/essential">Essential Mirror</Link></li>
                <li><Link className="text-[#3B3B34] hover:text-[#1C1C18]" to="/take/closeness">Closeness Mirror</Link></li>
                <li><Link className="text-[#3B3B34] hover:text-[#1C1C18]" to="/take/personality">Personality Mirror</Link></li>
                <li><Link className="text-[#3B3B34] hover:text-[#1C1C18]" to="/take/eq">EI Mirror</Link></li>
                <li><Link className="text-[#3B3B34] hover:text-[#1C1C18]" to="/take/everyday">Everyday Mirror</Link></li>
                <li><Link className="text-[#3B3B34] hover:text-[#1C1C18]" to="/flag-check">Flag Check — {REGISTER.flag_check.descriptor}</Link></li>
                <li><Link className="text-[#3B3B34] hover:text-[#1C1C18]" to="/archetypes">The six archetypes</Link></li>
                <li><Link className="text-[#3B3B34] hover:text-[#1C1C18]" to="/samples" data-testid="footer-samples">Sample results</Link></li>
                <li><Link className="text-[#3B3B34] hover:text-[#1C1C18]" to="/mirrors">Your mirrors</Link></li>
              </ul>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.1em] text-[#6E6E66] mb-3">The honest bit</p>
              <p className="text-sm text-[#3B3B34] leading-relaxed">{REGISTER.honest_line}</p>
              <Link to="/promise" data-testid="footer-promise" className="mt-2 inline-block text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
                Read the promise in full
              </Link>
              <br />
              <Link to="/faq" data-testid="footer-faq" className="mt-2 inline-block text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
                Questions, answered
              </Link>
              <p className="mt-2 text-sm text-[#6E6E66] leading-relaxed">{DISCLAIMER}</p>
              <Link to="/safety" data-testid="footer-safety" className="mt-3 inline-block text-sm underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
                {SAFETY.exit_link}
              </Link>
              <p className="mt-5 text-sm text-[#6E6E66] leading-relaxed">
                For coaches, therapists and practitioners →{' '}
                <Link to="/partners" data-testid="footer-partners" className="underline underline-offset-4 text-[#3B3B34] hover:text-[#1C1C18]">
                  Partner with us
                </Link>
              </p>
            </div>
          </div>
        </footer>
      )}
    </div>
  );
}

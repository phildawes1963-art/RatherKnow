import { Navigate, useLocation } from 'react-router-dom';
import { remapLink } from '../lib/mirrorLinks';
import REDIRECTS from '../content/redirectMap.json';

// Belt-and-braces only. The real cutover redirects are 301s at the edge
// (see docs/edge/worker.js). This catches anyone who lands on a legacy path
// on this host, so they never see a blank page.
export default function LegacyRedirect() {
  const { pathname, search } = useLocation();
  const clean = pathname.replace(/\/+$/, '') || '/';
  const exact = REDIRECTS.exact[clean];
  if (exact) return <Navigate to={exact + search} replace />;
  for (const rule of REDIRECTS.prefix) {
    if (clean.startsWith(rule.from)) {
      const rest = rule.keep_rest ? clean.slice(rule.from.length) : '';
      return <Navigate to={rule.to + rest} replace />;
    }
  }
  const remapped = remapLink(clean);
  return <Navigate to={remapped === clean ? '/' : remapped} replace />;
}

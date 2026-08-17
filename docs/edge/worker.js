/**
 * Cloudflare Worker for mymirrorreport.com — the cutover.
 *
 * Deploy this on the PARENT domain and flip RATHERKNOW_CUTOVER=on. It issues real
 * single-hop 301s to ratherknow.com from redirect_map.json. Legacy signed-in MI app
 * surfaces (/mirror-index/login, /dashboard, /journal, /onboarding, /quiz/*) are NOT
 * redirected — they stay on mymirrorreport.com until decommissioned.
 *
 * ORDER MATTERS: turn this on, run scripts/verify_redirects.py against production and
 * get a clean pass, and only THEN remove /mirror from the parent site. Never the other
 * way round — that ordering mistake is unrecoverable.
 */
import MAP from '../redirect_map.json';

const KEEP_ON_PARENT = ['/mirror-index/login', '/dashboard', '/journal', '/onboarding', '/quiz'];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, '') || '/';

    if (env.RATHERKNOW_CUTOVER !== 'on') return fetch(request);
    if (KEEP_ON_PARENT.some((p) => path === p || path.startsWith(p + '/'))) return fetch(request);

    let target = MAP.exact[path];
    if (!target) {
      for (const rule of MAP.prefix) {
        if (path.startsWith(rule.from)) {
          target = rule.keep_rest ? rule.to + path.slice(rule.from.length) : rule.to;
          break;
        }
      }
    }
    if (!target) return fetch(request);

    const location = MAP.base + target + url.search;
    return new Response(null, {
      status: 301,
      headers: { Location: location, 'Cache-Control': 'public, max-age=86400' },
    });
  },
};

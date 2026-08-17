// Remaps legacy links inside ported Learn content to Rather Know routes.
const RULES = [
  [/^\/mirror-index\/learn\/(.+)$/, (m) => `/learn/${m[1]}`],
  [/^\/mirror-index\/archetypes\/(.+)$/, (m) => `/archetypes/${m[1]}`],
  [/^\/mirror-index\/archetypes$/, () => '/archetypes'],
  [/^\/mirror-index\/(how-it-works|philosophy|science|for-business)$/, () => '/methodology'],
  [/^\/mirror-index(\/.*)?$/, () => '/'],
  [/^\/mirror\/take\/(.+)$/, (m) => `/take/${m[1]}`],
  [/^\/mirror\/(.+)$/, (m) => `/${m[1]}`],
  [/^\/mirror$/, () => '/'],
];

export function remapLink(path) {
  for (const [re, fn] of RULES) {
    const m = path.match(re);
    if (m) return fn(m);
  }
  return path;
}

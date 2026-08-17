# Rather Know — migration package HANDOFF

**For:** the agent building ratherknow.com in a NEW Emergent job from the **farmnext (Next.js) template**.
**From:** the mymirrorreport.com job (CRA + FastAPI + MongoDB), August 2026.
**Plan of record:** `docs/ratherknow-migration-plan.md` — read it first; it supersedes ticket MIR-001. This handoff tells you how the package maps onto that plan.

---

## 1. What this package is

The consumer property ("The Mirror", currently at `mymirrorreport.com/mirror`) moves to its own canonical domain, **ratherknow.com**, rebranded **Rather Know — a study of how you choose**. This folder is everything the new repo needs, frozen from the live MM codebase:

```
HANDOFF.md                    ← you are here
docs/
  ratherknow-migration-plan.md  the plan of record (§ references below point here)
  route_table.json              single exported route config — head/prerender/sitemap all consume it (§5)
  redirect_map.json             the 301 contract (§4) — the old domain's edge worker carries the same map
  ADMIN_PORTAL_TRD.md           admin portal requirements — orgs, white-labelling, org users, password resets (added Aug 2026, decisions locked with product owner)
backend/                        self-contained /api/v2 — drop into the new FastAPI backend
  routes/mirror_v2.py           the whole anonymous v2 API (4 instruments + Flag Check + findings)
  services/essential_scoring.py Essential Mirror archetype scoring (standalone port)
  services/p150_lite.py         Personality scorer (standalone; norms from snapshot)
  services/closeness_scoring.py Closeness Mirror MI-AS-36 scorer (verbatim copy, TRD §7)
  constants/essential_data.json 2×50 items, 6 archetypes, 12-pair compatibility matrix
  constants/p150_data.py        P150 items/factors/globals (verbatim copy)
  constants/eimirror_data.py    EI Mirror 140-item bank (verbatim copy)
  constants/closeness_bank_1_0_0.json  MI-AS-36 bank v1.0.0
  constants/p150_norms_snapshot.json   effective sten bands frozen from live MM norms
  database.py                   Mongo handle stub (MONGO_URL + DB_NAME from env — no defaults)
  requirements.txt              minimal deps
  _export_data.py               provenance: the script that froze the JSON exports
frontend/
  pages-mirror/                 the ENTIRE current site as reference implementation (React Router + Helmet)
  learn/miLearn.js              all 5 Learn essays (content data, incl. per-article SEO)
  archetypes/                   the 6 archetype pages + deps (MI-styled — restyle, see §Gaps)
  design_guidelines.json        the visual contract — "print journal meets research lab"
assets/
  mirror-index/                 ALL 14MB of MI imagery: photos/, illus/, cards/, diplomas/, audio/
  og/ratherknow-og.png          the new 1200×630 Rather Know og:image (§5, plan asked for it)
```

## 2. Build order (mirrors plan §9)

1. **Backend first** — copy `backend/` folders into the new repo's FastAPI app, register the router (`app.include_router(mirror_v2.router)`), set `MONGO_URL`/`DB_NAME` in `.env` (FRESH database — decided: no old session data migrates). All routes stay under `/api/v2/*` (already prefixed in the router; keep the platform's `/api` ingress rule happy — it is).
2. **Frontend port** — rebuild `frontend/pages-mirror/` pages in Next.js at the top-level routes in `docs/route_table.json` (drop the `/mirror` prefix everywhere, §3). The runner (`MirrorRunner.js`) is a client component (one item per screen, keyboard 1–9, localStorage resume). Keep every `data-testid`.
3. **Metadata at point of construction** (§5) — head component + prerender + sitemap + robots all read `route_table.json`. Self-referential canonical on EVERY page (the defect that prompted all this). robots.txt allows everything except `/mirrors` and `/results/*`.
4. **Cutover** (§4/§9) — when every route in the table answers, tell the user to flip `RATHERKNOW_CUTOVER = true` in the OLD repo's `edge/worker.js` and redeploy the Worker. The maps are identical by construction.

## 3. Rename rules (§2)

- Header: **"Rather Know"** wordmark + descriptor "a study of how you choose". The current header reads "The Mirror." — that goes.
- The parent attribution "An independent study by My Mirror Report." moves to the **footer and the methodology page only** (credibility, not confusion). Approved wording is exactly that sentence (§8 — treat it as a governed claim).
- Product family stays "the Mirrors": Essential · Closeness · Personality · EI Mirror. The reflection stays "the Flag Check". The core measure stays "the Delta".
- In-copy references to "The Mirror" as the site name need rewording; references to individual instruments do not.

## 4. Backend notes — what was changed in the port and why

- `routes/mirror_v2.py` is byte-identical to MM's except two things: (a) Essential imports now come from `services/essential_scoring.py` instead of MM's `routes/dating_wellness.py`; (b) `_score_personality` calls `services/p150_lite.score_p150_lite` (sync) instead of MM's DB-backed scorer.
- `p150_lite.py` reproduces MM's factor/global/validity arithmetic exactly, but reads sten bands from `p150_norms_snapshot.json` instead of the live super-admin norms collection. **Parity was verified** against the live scorer before packaging (see §8). If MM ever recalibrates norms, re-export the snapshot (`_export_data.py`) — until then scores match to the digit.
- v2's Personality result deliberately uses only factors/globals/validity/strengths/blind-spots — no Switch module (130 items), so Switch/Belbin/blends/Factor-B never ship here. Copy on the intro says "sixteen primary factors" ­— it means 15 scored + the unadministered B; keep the existing wording, it was deliberate.
- Collections: `mirror_v2_sessions` and `mirror_v2_reflections`. Reflections (Flag Check) are NEVER blended with assessments (FR-N8).
- localStorage keys the frontend uses: `mi2.sessions`, `mi2.reflections`. Keep them — returning visitors' in-progress work survives the rebrand (though not the domain move; that's accepted).

## 5. HARD PRODUCT RULES (do not relax)

### 5a. LOCKED COPY — port verbatim, never edit, never "improve"
Treat everything below as legally-reviewed, claims-register-governed copy. If a sentence in this list reads oddly to you, it is deliberate:
- **Evidence-tier statements** — `TIER_STATEMENTS` in `frontend/pages-mirror/mirrorTheme.js` (register MI-CLR-001 §5). Verbatim, per instrument.
- **Tier chips** — Essential = **Developmental** · Closeness = **Developmental** (+ the "New" badge) · Personality = **Established** · EI = **Established**. These are factual claims, not styling. Do NOT mark Essential as established.
- **The 7 promises and 10 refusals** on /promise — including the ceiling promise worded WITHOUT a figure.
- **Safety page copy** and every "if you're afraid of someone" line sitewide.
- **All Flag Check wording** — including "a reflection, not a measure" (RD-04) and the safety split.
- **Parent attribution** — exactly "An independent study by My Mirror Report." (footer + methodology only).
- **Learn essays** — authored content, port as written.
What you MAY change: layout, spacing, component structure, nav order, and the site-name references per the §3 rename rules ("The Mirror" → "Rather Know"). When renaming, the locked sentences themselves keep their wording — only the site-name token changes where it appears inside them.

### 5b. Behavioural rules
- **Flag Check is unscored — forever** (FR-N4). No numbers, no grades, no bands. "A reflection, not a measure" (RD-04). Exactly ONE CTA on its result (FR-N7). Safety split stays ABOVE the fold on intro and result; a yes/unsure safety answer changes the result lead block to inline referral routes.
- **Closeness Mirror**: single dot on 2 axes, never a 4-box quadrant, no bands/categories/percentages. Runner shows "n of 37" (the validity check item is a screen — honesty over neatness).
- **"Validated"** may only describe Established-tier instruments (Personality, EI). Essential and Closeness are Developmental and say so.
- **Pricing**: nothing is purchasable yet. The £78 ceiling claim (PF-05) is STILL UNCONFIRMED in the claims register (§9 open items) — do not publish it anywhere. The Promise page (promise 04) already words the ceiling WITHOUT the figure ("it will be published on this page before anything is purchasable") — keep that wording until PF-05 is confirmed.
- Evidence tiers, promises (7) and refusals (10) on /promise are claims-register-governed copy — port verbatim.

### 5c. Monetisation boundary (DECIDED — do not reopen)
Payment does not break the published promises; they were written to survive it ("Free to *start*"; promise 3 governs "anything paid"; promise 4 requires the ceiling published before anything is purchasable). Design the report boundary to these rules:
1. **Additive, never subtractive** — everything free today (all four complete results, cross-check, Flag Check, samples) stays free permanently. "Nothing quietly converts" is standing.
2. **Artefact-shaped boundary** — free = the complete on-screen result; paid = a NEW artefact (the full written report). NEVER partial results, blurred sections, locked rows or "unlock to see more" inside result pages.
3. **One-time and time-boxed** — paid access runs three months then ends; no renewal, no subscription machinery. Entitlements are expiring grants.
4. **Anonymity survives payment** — entitlement = token tied to the anonymous session, not an identity or account. Payment identity never joins assessment data.
5. **No figures, no checkout** until PF-05 confirms the ceiling and it's published on /promise. Build the seam dry (flag-gated doorway).
6. **Seam tone** = findings-teaser tone: one quiet sentence, no urgency, no "premium" styling, no upsell ladder.

## 6. Gaps to fill in month one (§4 — "the three gaps are the finding")

1. **/archetypes + 6 detail pages** — port from `frontend/archetypes/` NOW if quick. Content and structure carry over; the visual language does NOT: they're MI-styled (navy/cream/copper) and must be restyled to the Rather Know system (`frontend/design_guidelines.json` — alabaster/charcoal/Spectral). Share cards + diplomas are in `assets/mirror-index/cards|diplomas/`. SEO payloads are in `frontend/archetypes/miSeo.js` (rewrite canonicals + brand suffix).
2. **/samples** — ALREADY BUILT (`frontend/pages-mirror/MirrorSamples.js`, live at /mirror/samples on the old domain, with copyable share-link block). Port with the rest; redirect is 1:1.
3. **/faq** — ALREADY BUILT (`frontend/pages-mirror/MirrorFaq.js`, 12 governed Q&As + FAQPage JSON-LD). Port with the rest; redirect is 1:1.
4. **/pricing** — redirect to `/` until built (and never with the £78 figure until PF-05 confirms).

## 7. New-domain setup the USER does (§6/§7 — remind them)

Search Console property + sitemap day one · separate PostHog project (do NOT blend with MM) · entrance tracking tagged Essential/Closeness/Flag-Check from the start · TLS for apex/www/.co.uk · hello@ratherknow.com + safety-page routing · WHOIS privacy/registrar lock/auto-renew · **own** privacy policy, terms, cookie notice (defaulting to decline) — a separate domain cannot link across to MM's. DPIA carries over but must name the new brand.

## 8. Acceptance tests (plan §5 — run against ratherknow.com in CI)

The six curl checks (reconstructed from MIR-001's intent — the original ticket isn't in this package):
1. `curl -s https://ratherknow.com/promise | grep '<h1'` — served HTML contains real content (prerender works), per public route.
2. Every public route's HTML contains `rel="canonical" href="https://ratherknow.com{path}"` — self-referential, exact.
3. Title + meta description are unique per route and match `route_table.json`.
4. `og:title/og:description/og:url/og:image` + `twitter:*` present, absolute URLs, image = `/og/ratherknow-og.png` (or per-page override).
5. `/sitemap.xml` lists exactly the indexable routes; `/robots.txt` disallows `/mirrors` and `/results/`.
6. Single host answers: `curl -sI https://www.ratherknow.com/ | grep -i location` → 301 to apex, one hop; same for ratherknow.co.uk; no old→old→new chains (test the redirect map with a crawler before cutover).

## 9. What NOT to do (§11)

Don't rebuild while migrating — the site as it stands is good. Don't redesign the header beyond the rename. Don't add pricing. Don't blend analytics. Don't index `/mirrors` or results. Don't publish the £78 number.

## 9a. Admin portal (added after cutover scoping — see docs/ADMIN_PORTAL_TRD.md)

A second identity plane: super-admin + org-admin portal for organisations, light white-labelling (`/r/{code}`, logo + "in partnership with Rather Know"), org users with invites/password resets, counts-only org visibility, audit log. Consumer anonymity stays the default; optional consumer accounts are P2 and opt-in only. Requirements are LOCKED in the TRD — build P0 after the public site passes its acceptance tests, not before. Auth is an integration: consult the auth playbook before writing any of it.

## 10. Voice / audio

`assets/mirror-index/audio/mirror-index-demo.mp3` is the existing narrated demo (static file — just serve it if/when an audio surface is built). Live TTS in MM used OpenAI TTS (`tts-1-hd`/`nova`) via the Emergent LLM key + emergentintegrations — if RK needs new clips, call the integration expert in the new job; do not hand-roll the SDK.

## 11. What stayed behind in MM (by design)

The legacy signed-in Mirror Index product (accounts, dashboard, journal, paid dw_* tiers, Stripe checkout) does NOT move — RK v2 is anonymous by design. MM keeps the leadership business and its own identity, untouched. The old domain's `/mirror/*` pages had their noindex removed and self-canonicals added (Phase 0, done), and its edge worker carries the flag-gated 301 map ready to flip at cutover.

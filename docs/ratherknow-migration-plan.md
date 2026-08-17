# Migration to ratherknow.com

### Plan of record — supersedes ticket MIR-001

**Date:** August 2026 · **Status:** ready to execute
**Decision:** the consumer property moves to its own domain. `ratherknow.com` is canonical.

---

## 1. Domain map

```
ratherknow.com        the site — canonical, all content served here
ratherknow.co.uk      301 → ratherknow.com  (whole-domain redirect, path preserved)
datingwellness.com    held. Later: the red-flags cluster, or 301 to /red-flags
mymirrorreport.com    unchanged — the leadership business, its own identity
```

**Rule:** one domain answers with content. The others redirect. Serving the same pages on two hostnames recreates exactly the duplicate-content problem this move exists to escape.

---

## 2. Naming, now that the house has a name

| Layer | Name |
|---|---|
| House / domain | **Rather Know** — *a study of how you choose* |
| Product family | the Mirrors |
| Instruments | Essential · Closeness · Personality · EI Mirror |
| Reflection | the Flag Check |
| Core measure | the Delta |

The descriptor line is not optional. "Rather Know" alone doesn't say what it is; **Rather Know — a study of how you choose** does the work in five words, and it's already what the site says about itself.

The header currently reads "The Mirror." with "an independent study by My Mirror Report" beneath. That becomes "Rather Know" with the descriptor — and the parent attribution should move to the footer and the methodology page, where it's credibility rather than confusion.

---

## 3. Route structure — drop the prefix

Paths lose `/mirror`. They're top-level now.

| New | From |
|---|---|
| `/` | `/mirror` |
| `/promise` | `/mirror/promise` |
| `/methodology` | `/mirror/methodology` |
| `/safety` | `/mirror/safety` |
| `/learn` · `/learn/{slug}` | `/mirror/learn/*` |
| `/flag-check` | `/mirror/flag-check` |
| `/take/essential` · `/take/closeness` · `/take/personality` · `/take/eq` | `/mirror/take/*` |
| `/mirrors` *(auth)* | `/mirror/mirrors` |

Reserved for later, and worth defining now so nothing collides: `/red-flags` and its cluster · `/pathway` · `/pricing` · `/samples` · `/faq` · `/for-coaches` · `/for-creators` · `/partners/terms` · `/r/{partner_code}`.

---

## 4. Redirect map — and three gaps

**Clean 1:1** from `mymirrorreport.com/mirror/*` — every path above maps directly.

**From the older Mirror Index section**, which has pages the new site doesn't yet have:

| Old | New | Note |
|---|---|---|
| `/mirror-index` | `/` | |
| `/mirror-index/learn/{slug}` | `/learn/{slug}` | Same three essays |
| `/mirror-index/how-it-works` | `/take/essential` | |
| `/mirror-index/methodology`, `/science` | `/methodology` | |
| `/mirror-index/why`, `/philosophy` | `/promise` | |
| `/mirror-index/archetypes` *(+ 6 focus pages)* | **gap** | Nothing equivalent on the new site |
| `/mirror-index/samples` | **gap** | Sample reports don't exist yet |
| `/mirror-index/pricing`, `/faq` | **gap** | No pricing or FAQ page built |
| `/mirror-index/quiz-select` | `/` | |

**The three gaps are the finding.** The archetype pages are real content that currently ranks for nothing but would; samples and pricing are pages the funnel expects. Options: build them before cutover, or redirect to the nearest sensible page and accept a poorer experience for a while. My preference: **redirect now, build within the first month** — none of them should delay the move.

Redirects are **301**, permanent, path-preserving, at the host or edge — not a client-side JavaScript hop, which passes no signal.

---

## 5. The metadata work — done once, here

Everything in ticket MIR-001 now applies to the new build, at the point of construction rather than as a repair:

- **Route table as a single exported config**, consumed by the head component, the pre-render step and the sitemap generator
- **Self-referential canonical on every page.** The defect that prompted all this
- **Per-page** `description`, `og:title`, `og:description`, `og:url`, `og:image`, `twitter:*`
- **A Rather Know `og:image`** — 1200×630, new asset
- **Pre-render** every public route so served HTML contains content
- **Generated sitemap**, and **robots.txt** allowing everything except `/mirrors` and the in-flow quiz steps
- **Structured data**: `WebSite` + `Organization` on `/`, `Article` on essays, `BreadcrumbList` on nested routes

Acceptance tests are the six curl checks from MIR-001, run against ratherknow.com, in CI.

**One thing to do on mymirrorreport.com regardless, today:** remove the homepage canonical from `/mirror/*`, or 301 those paths as soon as the new site answers. Leaving a de-index instruction in place while the new domain warms up is the one avoidable cost.

---

## 6. Set up fresh, not migrated

| Item | Action |
|---|---|
| **Search Console** | New property for ratherknow.com. Verify both www and apex, and the .co.uk. Submit the sitemap on day one |
| **Analytics** | A separate PostHog project. Do **not** blend with the leadership site's data — you'll want to read this funnel on its own from the first visitor |
| **Entrance tracking** | Tag the three entrances distinctly from the start: Essential, Closeness, Flag Check. This is the measurement that eventually settles the naming question |
| **TLS** | Certificates for apex, www, and both .co.uk forms |
| **Email** | `hello@ratherknow.com`, and whatever the safety page needs to route to |
| **WHOIS privacy, registrar lock, auto-renew** | On all three domains |

---

## 7. Policy artefacts the new domain needs

These currently live on mymirrorreport.com and cannot simply be linked across — a separate domain needs its own, and they must describe *this* product.

- Privacy policy — including the free-text handling, the model-generation step, and the no-training commitment
- Terms of use, and consumer contract terms once anything is purchasable
- Cookie notice, defaulting to decline on anything non-essential
- Safety page — already built, needs to be reachable without an account and linked from the footer of every page
- The methodology page carries the evidence tiers and the parent-company attribution

The DPIA covers the processing, not the domain, so it carries over — but it should be updated to name the new controller-facing brand.

---

## 8. Claims Register — two updates

1. **New product facts:** the domain, the brand name, and the descriptor line become register entries, so partner assets and generated letters use one form of the name.
2. **The "independent study by My Mirror Report" attribution** needs an approved wording, used consistently. It's a credibility claim about provenance and should be governed like any other.

---

## 9. Sequence

| Phase | Work | Gate |
|---|---|---|
| **0 · Today** | DNS, TLS, .co.uk redirect, registrar lock. Remove the homepage canonical from `/mirror/*` on the old domain | Domains resolve; no de-index instruction live |
| **1 · Build** | Route config, head block, pre-render, sitemap, robots, og:image. Rename in header and footer | The six curl tests pass in CI |
| **2 · Content** | Port the pages as they stand. Fill the three gaps if quick; otherwise redirect | Every route in §3 answers correctly |
| **3 · Cutover** | 301s from both old sections. Search Console verified, sitemap submitted, indexing requested | Old paths redirect with a single hop, no chains |
| **4 · Watch** | Two weeks: coverage, first impressions, entrance-level funnels | Pages indexed under the right titles |
| **5 · Then** | Closeness Mirror pilot to 300, red-flags cluster, partner pages | — |

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| Redirect chains — old → old → new | Map every path directly to its final destination. Test with a crawler before cutover |
| A link shared during the window previews wrongly | Don't promote anything until phase 1 passes. Re-scrape any URL already shared |
| Two domains serving content | Enforce the single-host rule at the edge, and test with curl before launch |
| The rename confuses returning users | A one-line note on the old paths isn't possible under a 301 — instead, put the provenance line in the new footer where they'll land |
| Brand committed before the trademark check | The IPO search and a plain trading-name search before the name appears on anything public. Domain purchase doesn't wait; publication should |

---

## 11. What I'd not do

**Don't rebuild while migrating.** The site as it stands is good. Move it, get it findable, then improve it. The temptation to fix the three content gaps, add pricing, and redesign the header in the same pass is how a two-week move becomes a two-month one — and the thing blocking you isn't quality, it's that nobody can find any of it.

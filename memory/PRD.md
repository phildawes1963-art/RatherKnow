# RatherKnow — PRD

## Original problem statement
Extract the consumer Mirror out of `mymirrorreport.com/mirror` into its own web app, eventually at
ratherknow.com. Single-player throughout — no matching, no profiles, no other people. The measurement
is the **Delta**: self vs. the partner you say you want. Four instruments with scoring ported verbatim,
plus the Flag Check as an unscored fifth door, a cross-check view, and a content surface (Promise,
Methodology, Safety, FAQ, Learn, Samples, archetype SEO pages). Locked copy is governed by the claims
register (MI-CLR-001 §5) and hash-tested in CI.

## Blocking decision — resolved twice
1. **Initial build** shipped anonymous (option 1), promise intact.
2. **Reversed by the client on 2026-06 (option 2, in writing):** accounts are now required to take
   the four instruments. Signup captures exactly **name, email, password, situation**
   (Single & dating / In a relationship / Post-breakup). The gate sits **before** the questions.
   No email is ever sent — results appear on screen and are retrieved by logging in.
   The **Flag Check stays open** with no account, deliberately.
   Consequently the register was updated deliberately (hashes regenerated): "anonymous" is gone from
   the promise, replaced by a specific data claim (`data_claim`) and an explicit account claim
   (`account_claim`); promise 02 now states plainly that an account is needed and why.

## Architecture
- **Frontend** — React (CRA) + React Router + react-helmet-async. `mirror.css` tokens preserved.
  Pages in `src/pages`, locked copy in `src/content/locked_copy.json` (single register), theme and
  instrument metadata in `src/lib/mirrorTheme.js`, SEO contract in `src/lib/siteMeta.js`.
- **Backend** — FastAPI. `backend/routes/mirror_v2.py` is the only public route surface (`/api/v2/*`).
  Scorers in `backend/services/` (`p150_lite`, `eimirror_data`, `essential_scoring`,
  `closeness_scoring`) and item banks/norms in `backend/constants/` are **frozen** — ported byte-faithful.
- **DB** — MongoDB: `mirror_v2_sessions` (in-progress responses), `results` (immutable, `algo_version`
  stamped, written with `$setOnInsert` so completing twice never recomputes), `mirror_v2_reflections`.
- **CI gates** — `tests/_e2e_test.py` (full scoring E2E), `tests/test_locked_copy.py` (per-string
  sha256 hash test + the "validated"-only-for-Established lint), `backend/tests/test_mirror_v2.py`
  (15-case API regression suite).

## User personas
Individuals trying to understand their own pattern in relationships — not couples, not matched pairs.
Search-led discovery, essay-led trust.

## Core requirements (static)
1. Scoring is frozen; parity/E2E gates every deploy. No math refactors in v1.
2. Results snapshotted with `algo_version`, never recomputed.
3. Redirects live before `/mirror` is removed from the parent site. Never the other way round.
4. Locked copy is hash-tested in CI; locked strings never inline in JSX; tier chips render from the register.
5. Flag Check stays a reflection — no score, no band, no risk label, ever.
6. Safety exit reachable from every instrument page.

## Implemented (2026-06)
- **Auth layer** — `backend/auth.py`: bcrypt password hashing, 30-day PyJWT access tokens (Bearer,
  stored in `localStorage` key `rk.token`), `/api/auth/register|login|me|claim|me/sessions`,
  per-email brute-force lockout (5 attempts / 15 min). Registration captures name, email, password
  and situation; the situation is stamped on every session as `situation_at_start`.
  `POST /api/v2/assessments` and all session read/write/complete routes require the owner's token —
  another account gets 403. The Flag Check reflection endpoints stay open.
  Frontend: `lib/auth.js` (AuthProvider), `pages/Auth.js` (shared register/login), `ProtectedRoute`
  on `/take/:instrument`, `/mirrors`, `/results/:id`; anonymous local sessions are claimed on signup.
  Archetypes now sit in the top nav.
- **Phase 1** — All four scorers, item banks and the norms snapshot ported verbatim. Locked-copy
  register + hash/lint test green. Mongo schema with versioned immutable results.
- **Phase 2** — Anonymous session model (no auth needed), assessment runner with per-item autosave,
  resume, keyboard entry, skip/finish handling; Closeness Mirror validated end to end.
- **Phase 3** — All four instruments with their report views (including the Essential Delta),
  cross-check findings at `/mirrors`, Flag Check with safety split and yes/unsure referral blocks,
  and the full content surface: Landing, Promise, Methodology, Safety, FAQ, Learn + essays, Samples,
  archetype index and six archetype detail pages.
- **SEO groundwork** — self-referential canonicals to ratherknow.com, noindex on `/mirrors` and
  `/results/*`, robots.txt, `scripts/build_sitemap.py` generating sitemap.xml (24 URLs) from
  `docs/route_table.json`, OG image and archetype cards served from `/public`.
- Verified by the testing agent: backend 100%, frontend 100%, no blocking issues.

- **Situation-aware reports (2026-06)** — `content/situationFraming.js` + `components/SituationLens.js`
  render a different framing block per situation × instrument on every result page. Interpretation
  only: scoring is provably unchanged (parametrised backend test across all four instruments), and
  the lens states so on screen. Deliberately absent from the Flag Check.
- **Password reset (2026-06)** — `/api/auth/forgot-password` + `/api/auth/reset-password`,
  sha256-hashed single-use tokens with a 60-minute expiry, one active token per user, no account
  enumeration, lockout cleared on success. Email via Emergent-managed Resend (`email_service.py`,
  guardrail-checked server-side template). This is the **only** email the product sends — reports
  are never emailed.
- **Delta essay (2026-06)** — `/learn/the-delta`, the pillar-adjacent piece on the core idea, in the
  Learn index and the sitemap.
- **Cutover tooling (2026-06)** — `scripts/build_redirects.py` generates `frontend/public/_redirects`
  (SPA fallback last) and `docs/edge/nginx_redirects.conf`; `docs/edge/worker.js` is the parent-domain
  Cloudflare Worker behind `RATHERKNOW_CUTOVER`, which leaves signed-in MI surfaces on the parent;
  `scripts/verify_redirects.py --from <origin> [--strict]` is the gate — exit 0 means safe to remove
  `/mirror`. `pages/LegacyRedirect.js` is an in-app fallback so no legacy path ever blanks.

- **Printable report (2026-06)** — `GET /api/v2/assessments/{id}/report.pdf`, owner-gated, 409 unless
  complete. `backend/report_pdf.py` renders A4 typeset pages with reportlab straight from the stored
  snapshot (the scorer is unreachable from this path, so PDF numbers can never drift from `/result`).
  Each report carries the tier chip and tier statement pulled from the locked register, the situation
  framing (`situation_notes.py`), proportional bars with no invented banding, the safety floor with
  real helpline numbers, a "what this document is not" section, and a footer stamping the
  `algo_version` the result was scored under. `components/DownloadReport.js` on every result page;
  deliberately absent from the Flag Check.

- **"How you choose" translation (2026-06, user-reported gap)** — `backend/choosing.py` turns each
  instrument's stored numbers into statements about *selection behaviour* (what you reach for, what
  you excuse, what reaches you late). Derived at read time via `_with_choosing()` — verified never
  written into the snapshot — and rendered on every result page (`ChoosingSection.js`) and in both PDFs.
- **Cross-check rebuilt (2026-06, user-reported gap)** — `backend/crosscheck.py` normalises every
  available measure by construct (steadiness / closeness / repair / attunement / self-knowledge) and
  publishes **agreements as signal** (≤0.14 apart), extra construct-aligned **tensions** (≥0.30 apart)
  and a "How you choose — the short version" synthesis. With 2+ instruments the page can no longer be
  just the "No tensions" line. Every body quotes the two real values it compares; the 0.14–0.30
  dead-zone stays deliberately silent.
- **Item interleaving (2026-06, user-reported bug)** — `_spread()` round-robins items across their
  trait groups for essential / personality / EI, so no two same-trait items are ever adjacent (max
  run = 1, verified). Deterministic, so resume order is stable; scoring keys on item id and is
  unaffected. The Closeness Mirror's fixed balanced spec order is deliberately preserved.

- **Composite provenance (2026-06, user concern re Self-Control)** — a paired standalone P150 sheet
  disagreed with our Self-Control composite. Investigation: fed that report's own printed primaries
  (F 10, G 4, M 9, Q3 6) into our equation → 2.7 (Low); a plain 16PF-style reversed mean → 3.25 (Low).
  Its printed Self-Control of 6 is not reproducible from its own primaries by either method, so no
  scoring change was made (hard rule 1; the shipped code already documents a deliberately unshipped
  n=1 gain calibration). Instead `backend/composites.py` publishes, per global dimension, the equation
  `5.5 + Σ(weight × (sten − 5.5))` with every contributing factor's weight, direction and sten;
  Receptivity and Self-Control are flagged as known residuals; the Receptivity ≡ reverse of
  Tough-Mindedness polarity is explained. Surfaced on the result page, in both PDFs and on
  /methodology. `backend/tests/test_composites.py` locks the equations, the 1.0 gains and the
  reference profile so no future edit can drift them silently.

- **Scoring specification (2026-06)** — `docs/SCORING_SPEC.md`, generated from the shipped code, with
  a shareable PDF built by `scripts/build_scoring_spec_pdf.py` to
  `frontend/public/docs/ratherknow-scoring-spec.pdf` and linked from /methodology. Documents every
  item count, keying rule, formula, norm band, threshold and validity check for all four instruments
  plus the Flag Check, and answers the percentile question per instrument: only the Personality
  Mirror has population norms, so only it can carry a percentile without breaching refusal #3.

- **Release rk-1.1.0 Phase a (2026-06)** — the user supplied `rk-1.1.0-PRD.md`, `rk-1.1.0-TRD.md` and
  `rk-landing-and-partner-copy.md`. Phase a shipped, with two corrections and one dependency dropped.

  *Corrections to the as-built spec.* The sten→percentile table in `docs/SCORING_SPEC.md` was wrong at
  stens 4 (27, should be 23) and 7 (73, should be 77). Corrected, and `tests/test_display.py` now pins
  the shipped table to `Φ((sten − 5.5) / 2)` so it cannot drift.

  *Blocking dependency D2 (re-norm the Personality Mirror) dropped.* Its premise was that five factors
  sat at scale endpoints "where a comparison instrument produced none". The user's own standalone P150
  report in fact shows **six primaries at sten 10 and two at 9**, plus Independence 10 — more endpoint
  scores than RatherKnow produced. And `services/p150_lite.py` is the same item bank (130 of the P150's
  items, Switch module removed) scored against the same norms snapshot, so the two are directly
  comparable and real test–retest can be computed. There is no evidence of a calibration defect. This
  unblocks Phase b. **Answered PRD Q1: yes, shared item bank.**

  *MRD engine, in shadow mode.* `backend/services/mrd.py` + `backend/constants/reliability_1_0_0.json`
  implement SEM/MRD and the pairwise, flat-profile, distinctiveness and cluster gates. It ships in
  **shadow**: every gate is evaluated and persisted to `result.mrd.suppressions`, and nothing is
  withheld from any reader. `RK_MRD_MODE` flips it; `config()` refuses to load placeholder α values
  unless `RK_ALLOW_PLACEHOLDER_ALPHA=1` acknowledges them. `GET /api/v2/diagnostics/mrd` reports the
  would-be suppression rate.

  **The shadow-mode finding, which is a product decision waiting on the user.** Across 1000
  gate-eligible stored results the suppression rate is **1.0**. Personality primaries read flat in
  197/213, Closeness in 490/490. On the real reference profile — range of 8 stens, six factors at the
  ceiling — MRD 2.33 folds all fifteen primaries into a *single undifferentiated cluster* whose
  centroid is the personal mean, so nothing in it is reportable. Enforcing these thresholds today
  would empty the Personality Mirror and trip the PRD §9 half-refund guarantee on nearly every
  reading. Measured α (D1) has to come first; the guarantee must not be written into copy before then.

  *Also in Phase a.* Clamp recording (`constants/p150_data.py::global_factor_raw` + `composites.py::
  clamp_events`) — on the reference profile Independence computes to **11.2** and is published as 10;
  the clip is now visible and disqualifies the value from any population statement. Read-time
  `commonness` block on Personality only, versioned `disp-1.0.0`, globals explicitly excluded. Copy
  lint over the narrative modules (`tests/test_copy_lint.py`): banned prediction verbs, third-party
  references, and a template-repeat guard. Closeness p1/p4 inversion fixed in `report_pdf.py` (the
  avoidance datum was plotted under an "ease" label). The shadow-pull warning no longer renders twice
  in one Essential PDF. Diplomat zero-gap artefact resolved as a presentation defect, not a scoring
  one — a zero gap on the named ideal archetype is reachable by design and is now explained.

  *Landing page rebuilt* to `rk-landing-and-partner-copy.md`: refusals moved from second to fourth,
  the four per-instrument "Begin" buttons removed (one door in), the Flag Check moved to its own door,
  pricing published in **USD** (Free / $14 / $29, both paid tiers marked *not yet purchasable* because
  Stripe is not built), and the hero now shows **page one of a real report** — rendered through the
  shipped PDF builder by `scripts/build_hero_report_image.py`, so the picture cannot drift from the
  product. The page previously contained zero images.

  *TRD R6 closed as not reproducible.* Networkidle in 0.6s, zero long tasks, domInteractive 124ms. The
  "script injection times out" symptom was Emergent's preview-only instrumentation, absent in
  production. Do not profile this again.

  Verified: 141 backend tests green on three consecutive runs; testing agent iteration 8 reported zero
  critical and zero frontend issues.

- **rk-1.1.0 second batch (2026-06)** — user selected four items and supplied
  `rk-everyday-mirror-instrument-draft.md`. All four shipped; 177 backend tests green; testing
  agent iteration 9 reported zero issues in every category.

  *Commonness display, stens removed.* The user chose to **drop the sten entirely** from the
  reader-facing view rather than keep it as a secondary figure. The fifteen primary factors now read
  "About 1 in 4 people sit further toward warm than you", with both poles attached and the position
  marker retained. The five globals show a position word and their equation only — never a number
  and never a population statement, because they are clamped composites. Same treatment in the PDF
  ("How common" column, no sten column) so web and print cannot diverge. `services/display.py`
  computes it at read time, stamped `disp-1.0.0`.

  *Report snapshotting (TRD T1.1, T8.2, T10.2).* `services/narrative.py`. On first render the
  resolved narrative is persisted write-once; on first PDF build the bytes are stored in Mongo
  (`narratives`, `rendered_pdfs`) and served thereafter. A `display_version` bump only affects
  reports rendered after it. **Important design point discovered in testing:** snapshotting first
  broke the situation switch, because it froze interpretation the reader deliberately controls. The
  snapshot key therefore includes `situation` — freezing exists to stop *us* rewriting a delivered
  document, not to stop the reader asking for a different lens. Switching produces a new snapshot;
  switching back returns the original bytes unchanged. The combined roll-up is invalidated when a
  new instrument finishes; individual reports never are.

  *The Everyday Mirror — sixth instrument, built.* `constants/everyday_bank_1_0_0.json` +
  `services/everyday_scoring.py`. 28 Block A position items (four per domain, 0–4 toward the named
  first pole, a 2–2 split reported as **undifferentiated** rather than a midpoint) and 21 Block B
  round-robin priority comparisons (wins 0–6). Three behavioural validity checks — circular triads
  (`ζ = 1 − 24d/336`), side bias, time floor — which are the only non-self-report evidence in the
  product. Position × priority produces the four map cells. Full runner support for forced choice,
  a result page, a `choosing` builder and a PDF body. **Known, published gap: the 20–30 rater
  desirability pre-test has NOT been run.** `pretest_status: "not_run"` is returned in the payload
  and stated in the tier statement and the PDF; until it runs the instrument contributes to a
  reading and never anchors one. Refusals enforced by test: no compatibility score, no norms, no
  bands, no percentiles.

  *Bug found and fixed during the build:* Block A item ids originally contained dots (`A1.1`), and
  Mongo reads `responses.A1.1` as a nested path — so no Block A answer was ever stored and every
  domain returned "not enough answers to place you". Ids are now `A1_1`, `PUT /responses` rejects
  dotted ids with a 400, and a test asserts no item id in any bank contains a dot.

  *Partner page* at `/partners` from the copy deck, all eight sections, reachable from the footer on
  every page. `routes/partners.py` stores applications (`partner_applications`) with a 3-per-24h
  rate limit; open endpoint, since a practitioner should not need an account to apply. Two
  user-directed decisions recorded deliberately: the page **publishes the dashboard promise as
  written** even though no attribution, dashboard or payout plumbing exists (accepted because the
  first ten partnerships are founder-led and reporting is manual), and it keeps "if you'd like to
  see the scoring specification, ask" rather than linking the public PDF.

- **Archetype documentation (2026-06)** — user asked for a document describing the six archetypes
  and chose **both** a publishable guide and an internal specification, with the item-overlap
  findings kept **internal only** pending a decision, and **no code changes**.

  - `docs/ARCHETYPES_GUIDE.md` → `frontend/public/docs/ratherknow-archetypes.pdf` (5 pages),
    linked from the Archetypes page. Reader-facing: what an archetype is and isn't, the two lenses
    and the Delta, the shadow map, then each of the six — how it chooses, what it looks like day to
    day, what to look for, **what it costs**, and its shadow pull.
  - `docs/ARCHETYPES_SPEC.md` → `docs/ratherknow-archetypes-spec-INTERNAL.pdf`. **Not published**;
    a test walks `frontend/public/` to keep it that way.
  - `scripts/build_archetype_docs.py` builds both. `tests/test_archetype_docs.py` (8 tests) checks
    the guide's shadow map and counter-types against the shipped `ARCHETYPES` data, asserts the
    internal findings have not leaked into the guide, and recomputes the overlap so the spec's
    figures cannot go stale.

  **Three defects found while writing the spec. None fixed — all would change scores.**

  1. **Item overlap.** Six archetypes × 10 items = 60 scoring slots from a 50-item lens, so 13
     items are double-counted and the archetype scores are not independent. Worst case: the
     **Torchbearer shares 8 of its 10 items** (5 with the Challenger, 3 with the Voyager), so it is
     largely a linear combination of two others — "primary Torchbearer, secondary Challenger" is
     near-mechanical rather than a finding. The Diplomat shares 4 of 10 across three archetypes.
  2. **Items 7, 34 and 36 feed no archetype**, so six of a reader's hundred answers do nothing
     toward the archetype scores. May be dimension-only; undetermined.
  3. **`diplomat.reverse = [24]` is inert** — item 24 is not in the Diplomat's item list. Item 24 is
     a Challenger item with no reversal, so the shipped Challenger score is probably missing an
     intended reverse.

  Also raised, not changed: the Essential result carries a field named **`compatibility`** (and a
  `_COMPATIBILITY` table). It holds a top-two blend narrative within one lens — no number, no second
  person — so it does not breach the refusal, but it is named like the one thing permanently ruled
  out. Rename to `blend` recommended; no instruction received.

- **As-built product & technical specification (2026-06)** — user asked for a full product and
  technical spec and chose: **one combined document**, as-built **plus** a forward-looking spec for
  the next version, **internal only**, Markdown plus PDF.

  - `docs/RK_SPEC.md` → `docs/ratherknow-spec-INTERNAL.pdf` (10 pages). **Supersedes
    `rk-1.1.0-PRD.md` and `rk-1.1.0-TRD.md`**, which describe intent rather than what exists.
  - Part 0 summary · Part I product as built (refusals, situations, the five instruments and Flag
    Check, the four interpretation layers, the Delta, content surface, pricing, partners) · Part II
    technical (architecture, 10 collections, full API surface with auth levels, versioning, the
    three-layer immutability model, MRD, display layer, auth, copy governance, PDFs, migration,
    185-test inventory, config) · Part III the defect register · Part IV the 1.2.0 spec in five
    gated phases.
  - `scripts/build_rk_spec_pdf.py` builds it. **`tests/test_rk_spec.py` (9 tests) checks the
    document against the running code** — instrument table and item total, all five MRD thresholds,
    every version stamp, the situation enum, that every collection in §11 is actually used, that
    the register stays ordered and keeps its four worst entries, the Flag Check counts and its
    never-scored constraint, and that the spec is not published and claims no checkout. It caught
    two wrong numbers in the first draft (EI-domain and Closeness MRD).

  **Part III risk register, ordered by harm — R1 is the one to act on:**

  | | | |
  |---|---|---|
  | R1 | Guarantee has no working mechanism | SEVERE |
  | R2 | Partner link/dashboard promised, nothing behind it, no application alerts | HIGH |
  | R3 | Essential archetypes not independent (+ 3 unallocated items, 1 inert reverse) | HIGH |
  | R4 | Reliability unmeasured across every instrument | HIGH |
  | R5 | Everyday desirability pre-test outstanding | MEDIUM |
  | R6 | Production redirects unverified | MEDIUM |
  | R7 | `compatibility` field name | MEDIUM |
  | R8 | Outbound email receipt unverified (provider returns 202, no inbox confirmed) | MEDIUM |
  | R9 | `rendered_pdfs` grows unbounded | LOW |
  | R10 | No data retention, export, deletion or DSAR path — **blocking for launch** | LOW/BLOCKING |
  | R11 | Shadow map incomplete (`adventurer` is nobody's shadow) | LOW |
  | R12 | No production deployment, monitoring, backups or CI gate | CONTEXT |

  **R1 in full:** the site promises a half refund when the report can't say enough; the MRD gates
  would decide that, and their shadow suppression rate is 1.0 across ~1,000 results. Highest-value
  single action in the whole backlog is Phase A7 — pull or reword that guarantee line until α is
  measured.

  Also documented: **R10 is the genuine launch blocker.** The product holds intimate relationship
  self-report data with no retention policy, no export and no deletion path.

## Backlog
**P0 (Phase 4 — cutover, needs infrastructure access)**
- Deploy `docs/edge/worker.js` on mymirrorreport.com, set `RATHERKNOW_CUTOVER=on`, point
  ratherknow.com at this build, then run `scripts/verify_redirects.py --from https://mymirrorreport.com
  --strict`. Only a clean pass authorises removing `/mirror` from the parent.
- Submit sitemap; confirm archetype pages indexed.

**P1**
- The paired-sheet residual on Receptivity and Self-Control is documented, not resolved. Resolving it
  needs a real calibration sample (n ≥ 200 paired profiles), not a single sheet. Until then the
  provenance block is the honest answer.
- Password reset does not check that the new password differs from the old one (harden, not urgent).
- Sitemap learn slugs live in `docs/route_table.json`; auto-generate from `LEARN_ARTICLES` so future
  essays can't drift out of the sitemap.
- Learn essays for the remaining archetype clusters.
- Object storage for illustration/diploma/OG assets and the audio demo.

**P0 (honesty debt — no research needed, all in `docs/RK_SPEC.md` Part IV Phase A)**
- **A7 · Pull or reword the half-refund guarantee** until α is measured. Highest value item here. (R1)
- A3 Partner application alert via the existing Resend integration, which also closes R8.
- A4 Account deletion + data export; A5 retention policy. (R10, R9)
- A1 rename `compatibility` → `blend`; A2 import-time reverse-key assert. (R7, R3)
- A6 CI gate running the locked-copy hash test, copy lint and the suite. (R12)

**P1 (Essential Mirror item allocation — decide, then version)**
- Re-allocate the 50 items so the six archetypes have independent items. This **changes scores**, so
  it ships as a new scoring version with parity tests, and every existing report keeps its original
  numbers. Full detail in `docs/ARCHETYPES_SPEC.md` §4.
- Allocate items 7, 34, 36 or declare them dimension-only. (§5)
- Resolve item 24's intended reversal. (§6)
- Cheap and worth doing whatever is decided: assert at import that every `reverse` entry appears in
  the same archetype's `questions`, so an inert reverse key cannot ship again.
- Rename the `compatibility` field to `blend`, carrying the old key for existing snapshots. (§7)
- Decide whether the shadow map is meant to be complete: `adventurer` is currently nobody's shadow. (§3)
- If the overlap is not fixed, revisit whether the published guide should disclose it — the
  evidence-tier disclosures set a standard this omission sits awkwardly against.

**P0 (partner programme — now owed)**
- The partner page promises a link and a dashboard. Nothing behind it exists. Before the first
  approved partner, either build attribution (`partner_ref` on the user, passed as Stripe metadata)
  or report manually and tell them that is what is happening.
- Applications land in `partner_applications` with no notification. Somebody has to read that
  collection, or wire a Resend alert.

**P0 (Everyday Mirror — before it may anchor a reading)**
- **Desirability pre-test, 20–30 raters**, "which would you rather others thought about you". Any
  pair splitting worse than 65/35 gets rewritten. This is a human research step; the instrument
  publishes that it is outstanding until it is done.
- Pilot n ≥ 200 for Block A internal agreement and Block B triad distribution. Four items per
  domain is thin — expect undifferentiated domains, and go to six per domain if unstable.
- Read 5 (Negotiability) and the priors-register rows from the draft §8 are not built.

**P0 (rk-1.1.0 Phase b — now unblocked by dropping D2)**
- **D1 remains: measure α for every scale.** Every MRD threshold is a literature placeholder. Nothing
  enforces and no guarantee copy ships until these are measured. `RK_ALLOW_PLACEHOLDER_ALPHA=1` is the
  deliberate acknowledgement that they are provisional.
- ~~Commonness display~~ and ~~narrative snapshotting~~ shipped 2026-06.
- `rendered_pdfs` grows unbounded in Mongo (one document per session per situation per display
  version, 7–200KB each). Fine at current volume; needs a retention policy or object storage before
  any real traffic.

**P2**
- Paid tier boundaries + the published price ceiling on the Promise page; one inert unlock boundary
  already assumed, no payment integration until tiers are confirmed.
- Split `mirror_v2.py` scoring helpers into `services/mirror_v2_scoring.py`; cap batch response length.

## Open questions
- **Does the MRD gate ever enforce?** See the shadow-mode finding above. Options: measure α and retry;
  loosen to a 68% rather than 90% interval for within-person profile reading; or keep the gates as an
  internal honesty check that never governs reader-facing output.
- rk-1.1.0 PRD Q2: Essential Mirror timing — the site says 25 minutes, the funnel model assumes 13.
  Needs real median completion time from live sessions.
- rk-1.1.0 PRD Q5: companion avatar in or out of 1.2.
- Partner page is written but deliberately unbuilt: the user's own sequencing note says build it after
  the sample readings are public.
- Do free-tier boundaries differ per instrument, or is everything free until paid tiers exist?
- Parent attribution is currently visible in the footer — keep or clean split?

---

# Work order Batch A/B — shipped 2026-06 (branch RK)

Governing document: `rk-work-order-batch-A-C.md` (user-supplied). Standing rules honoured: no
scoring change, no `algo_version`/`bank_version` bump, no delivered result change, every item
carries a test, no live collection renamed.

## A0 · CI gate
`.github/workflows/rk-tests.yml`. Two jobs on push/PR to `RK`: `offline` (copy lint, locked-copy
hashes, `tests/`) and `e2e` (mongo service + uvicorn + `backend/tests/`).
`RK_ALLOW_PLACEHOLDER_ALPHA=1` is set explicitly in both with a comment saying to delete it the
day `reliability_1_0_0.json` sets `placeholder: false`.
**Unverified until pushed** — GitHub Actions cannot be triggered from the preview pod. A red run
was demonstrated locally instead (deliberate break → `1 failed`, then reverted).

## A1 · Copy lint coverage (landed before A4, as instructed)
`tests/test_copy_lint.py` rewritten: scope is now **derived** from `backend/`,
`backend/services/`, `backend/routes/`, `backend/constants/` with a two-entry non-narrative
allow-list (`server.py`, `database.py`). Tests assert the scope is non-empty, that every
discovered module has a lint decision, and that the named modules still resolve (hard failure,
not `continue`).
Found on first run: `constants/eimirror_data.py:295` had shipped "you consistently excel here"
in the EI Exemplary band — a banned prediction verb that had never been linted. Reworded to
"your answers sit at the top of this scale".

## A2 · Rate limiting on unauthenticated writes
`backend/services/ratelimit.py` — Mongo-backed fixed window, atomic `$inc`, per-origin key from
the X-Forwarded-For chain, plus a 16 KiB body cap. Buckets: reflections 30/10min,
partners 10/10min, auth 60/10min (all env-overridable). Wired to `POST /reflections`,
`PUT/POST /reflections/{id}/*`, `POST /partners/apply`, and register/login/forgot/reset.
`backend/tests/conftest.py` gives every `requests.Session` its own forwarded address so the suite
cannot exhaust a window — product limits were not raised to fit the tests.
**Known limitation, documented in the module:** the header is client-supplied, so this bounds
loops and casual abuse but is not a defence against a determined attacker. Edge-level limiting is
still needed before anything is promoted publicly.

## A3 · Guarantee line removed
`frontend/src/pages/Landing.js` — the half-refund sentence is gone, not softened. Replaced by
`locked_copy.json → pricing.reportable_limits` (hash-locked). Hashes rotated.
New lint test fails on any refund/guarantee/money-back wording anywhere in `frontend/src` while
`reliability_1_0_0.json` has `placeholder: true`. Verified by reinstating the line (lint red) and
removing it again (green).

## A4 · `compatibility` → `blend`, and the orphaned reverse key
`essential_data.json` key, `services/essential_scoring.py` (`_BLEND`, `get_blend_result`) and the
API all renamed. New results emit `blend` **and** `compatibility` pointing at the same object;
stored documents untouched. Nothing in the frontend or PDFs ever consumed the field.
Guard `assert_reverse_keys_within_questions()` runs at import and fails on any orphan.
**Open decision — Diplomat `reverse: [24]`.** Not deleted. It is carried as the single entry in
`KNOWN_ORPHANS`, and `tests/test_workorder_a.py` asserts that set never grows. Evidence on what
it was meant to do: Diplomat's items are `22,23,25,26,27,28,29,30,17,38` — a contiguous 22–30 run
with **24 missing**, refilled with 17 (also Adventurer's) and 38. Item 24 is "I am comfortable
with loud, passionate debates" and now sits in Challenger's set. Reverse-scored it reads as
Diplomat-consistent. So the reverse key is evidence that 24 was intended to be a reversed
Diplomat item and was moved out of the list without the key following. Restoring it changes
scoring; dropping the key changes nothing. Awaiting the owner's call.
Work-order correction: the API keys are at `routes/mirror_v2.py` 391/421/429, not 240/270/277.

## B1 · Factor count
"sixteen primary factors" → "fifteen" in the personality pre-assessment instructions, added to
`locked_copy.json → instrument_instructions.personality_scope`, with a test asserting the backend
string matches the locked one verbatim. Code review then found the **same claim on a second
surface** — `_headline` returned "16 factors scored" from `POST /api/v2/mirrors/summary`. Also
changed to 15 and covered by the same test.

## B2 · MRD diagnostics in comparable units
`mrd_sd_units_for()` computes `z·√(2(1−α))` from the formula (not from the rounded threshold, so
sets sharing an α report identical ratios). `mrd_sd_units` travels with `mrd` in every evaluated
scale set, and `/api/v2/diagnostics/mrd` now reports `suppression_rate` **per scale set** as well
as overall. Diagnostics only — no gate behaviour changed. The refund-promise justification was
also removed from the module docstring and the endpoint note.

## B3 · Norms provenance — findings, no change
`docs/B3_NORMS_PROVENANCE.md`. Answer is worse than the question assumed: there is no evidence of
a respondent population at all. The snapshot's entire metadata is `exported_at` and
`source: "mymirrorreport backend effective bands (super-admin config over defaults)"` — no n, no
group, no norming date. All fifteen factors share identical sten 1–4 boundaries, which are exactly
the hardcoded generic `raw_to_sten()` cut-offs, and the band widths are near-uniform across the
raw range where a normed sten table would be narrow in the middle and wide in the tails. These
look like equal-interval cut-offs with hand-tuning in stens 5–8, not a percentile map of a sample.
Consequence, stated and not acted on: `display.py`'s commonness sentences and the sten ≥ 8 /
sten ≤ 3 strengths and blind-spot selection all rest on the sten ~ N(5.5, 2) assumption that this
table does not establish. This is upstream of measuring α. **No re-norm performed.**

## Verification
`tests/` 77 passed · `backend/tests/` 139 passed · testing agent iteration 10: **zero critical,
zero minor, zero frontend issues**, 231 passed including its own 15 new tests. Delivered-report
immutability specifically re-checked: individual and combined PDFs byte-identical on repeat, and a
situation flip-and-back returns the original bytes.

## Batch C — not started, awaiting the Junction Check spec
C1 Junction Check (spec to be handed over), C2 fourth situation value + move the question out of
registration, C3 new `informant_predictions` collection (separate lifecycle, no `kind`
discriminator).

## Still explicitly not started (owner's instruction)
Entitlement/payments · retention/export/erasure (must cover `rendered_pdfs`) ·
`RK_MRD_MODE=enforce` · the `services/` module split · any change to Essential item allocation.

---

# Norms pause, EI grade removal, Diplomat close-out, and C1 · shipped 2026-06 (branch RK)

## Decision 1 · The norms pause
Population claims are **paused, not caveated**. `services/display.NORM_REFERENCED = False` refuses
`commonness()` at source; the machinery is intact behind the switch so one flag restores it.

- Removed from reader-facing output: commonness fractions, percentile-flavoured language, and the
  absolute band words (Very High … Very Low on Personality; High / Moderate / Developing on EI).
- **EI keeps its numbers, loses the grade** — a mean of 4.2 on a five-point scale is a fact about
  the reader's answers; the band word implied an undocumented standard.
- Kept untouched: the Delta, "how you choose", composite provenance and equations, the cross-check,
  agreements, tensions, synthesis.
- New `services/within_person.py` (`wp-1.0.0`): **three** named factors in total, ranked on absolute
  distance from the reader's own profile mean, floor **1.5 sten** (`FLOOR_BASIS` records that it is
  provisional and becomes per-scale-set when D1 lands: α=.85 → 1.27, α=.75 → 1.65).
- Approved copy is in `locked_copy.json → position` (`no_grade` renamed `no_comparison`).
- `DISPLAY_VERSION` `disp-1.0.0` → `disp-1.1.0`; every delivered narrative and PDF keeps serving the
  layer it was rendered with. No score, raw score or sten moved.
- Copy lint gained a `POPULATION` ban list, enforced while `NORM_REFERENCED` is False, with
  `services/display.py` the single documented exemption.
- Found by the extended lint on its first run: `eimirror_data.py` shipped "you consistently excel
  here"; `essential_data.json` shipped "leading to" twice. Both reworded.

**Observed consequence, measured on 504 stored personality results:** at the 1.5 floor, 44% name
nothing, 24% name three. At 1.0 it is 40% / 59%. The floor is the live design lever and the copy
handles all three states (`loudest-list`, `loudest-partial`, `loudest-none`).

## Decision 2 · Diplomat item 24
Inert `reverse: [24]` dropped, not restored. `KNOWN_ORPHANS` is now empty and asserted to stay so.
`tests/test_workorder_a.py::test_dropping_diplomat_24_changed_no_score` proves the deletion moved no
score. Recorded in `docs/ARCHETYPES_SPEC.md` §6, now marked CLOSED.

## Decision 3 · Methodology note
`docs/METHODOLOGY_NOTE_DRAFT.md` — drafted for review, **not published**. Ships with the pause when
approved, never instead of it.

## Decision 4 · C1 · The Junction Check
Six plain-language questions, free, no account, no scoring, no norms.

- Bank `backend/constants/junction_bank_1_0_0.json` (`RK-JC-6`); no domain, no pole mapping, no key.
- Route `backend/routes/junction.py` at `/api/v2/junction/*`; collection `junction_answers`.
- The only inference is a count of items the reader could not answer, named in words.
- Claiming **reuses** `POST /api/auth/claim`; `_claim()` extended to `junction_answers` under the
  same `{$in: [None, user_id]}` guard. A second account gets `claimed: 0`.
- Rate-limited (`junction` bucket, 40/10min) with the 16 KiB body cap.
- Retention built with the module: `purge_unclaimed()` at 90 days, driven by
  `.emergent/crons.yml → junction-purge` hitting `POST /api/cron/junction-purge` (bearer
  `WEBHOOK_CRON_SECRET`, constant-time compare, backgrounded).
- Frontend `/junction`, linked from the landing page (`junction-door`). Safeguarding copy on every
  screen including the result, with no account.
- Guards G1–G4 in `tests/test_junction_guards.py` (28 tests), flow in `backend/tests/test_junction.py`
  (14 tests). G1 and G3 include proofs that the guard bites when removed.

### Contradictions found in the C1 spec
1. **§3.2's own approved copy contained "match"** — "whether the other person's six match" — which
   §4's G4 bans outright. Reworded to "…are the same" so the guard can be strict.
2. G4's list also bans "score", which appears in the honest refusal "nothing here is scored". The
   lint is negation-aware: a refusal stays, a bare claim fails.

## Verification
`tests/` 129 passed · `backend/tests/` 170 passed · testing agent iteration 11: **zero critical,
zero minor, zero frontend issues**, plus 12 of its own acceptance tests. Delivered-report
immutability re-checked: PDFs byte-identical on repeat, situation flip-and-back returns the original.

## Open after this round
- **Methodology note approval** before it goes on `/methodology`.
- **The 1.5 floor** is provisional; D1 (measure α per scale) is what makes it derived.
- **A reference sample** — build one from RK respondents, or recover the MM provenance. Until then
  no population claim returns.
- **Aggregate publication for the Junction Check** at n ≥ 1,000, distributions only, computed
  forward from a counter — not built.
- Still explicitly not started: entitlement/payments, retention/export/erasure for the other
  collections (`rendered_pdfs` above all), `RK_MRD_MODE=enforce`, the `services/` split, any change
  to Essential item allocation.

---

# CI portability fix · 2026-06

The A0 workflow would have failed on its first push, and not on a product defect. Thirteen test
files hardcoded the pod root: four broke imports through `sys.path.insert`, four broke on a bare
`open()`, and nine did a `load_dotenv` that is a silent no-op anywhere else. A collection error
aborts the whole pytest run, so `tests/_e2e_test.py` alone would have failed the entire offline
job before an assertion ran.

- `tests/conftest.py` (new) and `backend/tests/conftest.py` derive ROOT and BACKEND from
  `__file__`, insert the backend on `sys.path`, load both `.env` files and set
  `RK_ALLOW_PLACEHOLDER_ALPHA`.
- Every per-file hardcoded `load_dotenv(...)`, `sys.path.insert(...)` and `open(...)` is now
  root-relative or removed.
- `tests/test_ci_portability.py` is the guard: no test file may contain the pod-root literal,
  both roots must keep a conftest that derives its own root, every test file must parse, and no
  test file outside conftest may call `load_dotenv` with a literal path. The needle is assembled
  at runtime so the guard does not trip on itself.
- Workflow: the offline job's comment now says it needs Mongo (it does — immutability and
  snapshot tests touch it); uvicorn is started with `nohup`/`disown`, logs to `/tmp/uvicorn.log`,
  and the log is printed on failure so a connection-refused is diagnosable from the run.

Verified by copying the tree to a different root and running there: 134 offline passed, all 182
backend tests collected, both standalone lint scripts fine. In-pod suites still green (140 + 42).

---

# Addenda B4 + B5 · shipped 2026-06 (branch RK) — copy and section order only

## B4 · The norms pause reaches the public pages
Promise 07 says "no banded scores before norms exist to justify them", and the marketing pages were
still making the claim B3 disproved. Eight strings named, thirteen changed.

- **Landing**: personality card lost "scored against calibrated norms"; the two-tiers line replaced;
  a new hash-locked `banding_note` says both established instruments report positions rather than
  bands, cites promise 07, and states that an evidence tier describes where an instrument came from
  and not its banding. Tier chips unchanged, as instructed.
- **Samples**: "5–6 is the population middle" and the `sten ≥ 8` / `sten ≤ 3` rule replaced with the
  position wording and the within-profile selection the code actually does; "against calibrated norm
  bands" dropped from the footnote. The Closeness midline, the Delta and the "validated five-factor"
  line left alone, as instructed.
- **Counts**: landing hero, section heading, meta description and JSON-LD now say five.
- **Free tier**: the Delta leads; the archetype is no longer the headline deliverable.

### Surfaces B4 did not list but which carried the same claim
`Methodology.js` (×3: "against calibrated norm bands" twice plus "norm bands are recalibrated
periodically"), `Partners.js` ("established, with calibrated norms"), `Faq.js` (count). All fixed —
the new lint would have failed on them anyway.

## B5 · Landing order and six strings
Order now: hero · what you get · the Delta · refusals · **Junction Check** · how it's built ·
**It ends** · what it costs · **Where the thinking comes from** · Flag Check · safeguarding.
S1–S6 all applied: hero sub-line names why the email exists; the three-column price table became one
free card plus prose (no figure changed, nothing purchasable); "It ends" and "Where the thinking
comes from" are new; the fixed order now gives its reason; the five instrument rows are compressed to
name · tier · one line · item count via a new `line` field in `mirrorTheme.js`.

## Lint additions (B4 §5)
`test_no_norm_claims_on_the_public_pages` walks every page component plus `locked_copy.json` and
`mirrorTheme.js` and hard-fails on the five banned phrases and both sten cut-off forms while
`reliability_1_0_0.json` has `placeholder: true`. Plus a count test that compares the number of
`INSTRUMENTS` entries against every page stating a total, and a test that each instrument keeps its
compressed line.

## Contradictions found and how they were resolved
1. **B4 §1.2's replacement said "Two are ours"; three are.** Essential, Closeness and Everyday are
   developmental. `Partners.js` already said three. Shipped as three.
2. **B4 §1.1 and B5 §S6 pull against each other** — 1.1 adds a long banding paragraph to the
   personality card, S6 compresses every card to one line. Resolved by putting the banding
   clarification once, under the instrument list, where the two-tiers line already lives.
3. **B4 §5 asked for a lint on "the landing, sample and promise page components"** — scope was
   widened to every page component, because the claim was live on two pages the addendum did not name.

## Out of scope, found while working, NOT changed
- **The combined PDF omits the Everyday Mirror.** `report_pdf.py` builds from a hardcoded four-key
  order (`essential`, `MI-AS-36`, `personality`, `eq`), so a reader who has completed Everyday gets a
  combined reading that silently leaves it out. Only the false total was fixed ("N instruments read
  side by side"). Including it changes what a combined PDF contains and needs a decision.
- **The methodology page documents four instruments.** Everyday has no entry, so the newest and
  least-established instrument is the one with no published method. Needs written content.
- **The nav still promotes Archetypes** (B5 §3 flagged this) — to be decided with §4.1.

## Verification
`tests/` 138 passed · `backend/tests/` PDF + immutability 42 passed · testing agent iteration 12:
**zero issues**, order verified by bounding box, banned phrases absent across nine public pages plus
the logged-in dashboard and all four result pages, combined PDF byte-identical on repeat.

---

# Published note, Everyday in the combined reading, §4.1 measured · 2026-06 (branch RK)

## Methodology note — PUBLISHED
`/methodology`, `locked_copy.json → methodology_note`, hash-locked. Nine paragraphs including the
added one accounting for readings already delivered under the comparative language. No figures, no
parent product named, no mention of the reliability gates. Guarded by
`tests/test_workorder_b.py::test_the_published_methodology_note_still_says_the_hard_parts`, which
asserts the four sentences most likely to be softened and fails if a digit appears.

## Everyday Mirror in the combined reading
`report_pdf.COMBINED_ORDER` now includes `MI-EV-49`. A reader who completed it was getting a
combined reading that silently omitted it. `DISPLAY_VERSION` carried the change; delivered PDFs
keep their bytes.

## Everyday methodology entry
Five entries now, not four. Its stated weaknesses lead with the desirability pre-test gap:
publishing the fullest method for the least-established instrument. The EI entry also stopped
describing the `High / Moderate / Developing` bands the code no longer emits.

## Two leftovers of the norms pause, found while doing the above
- `choosing.py` still selected personality traits on **sten ≥ 7 / ≤ 4** and printed "At 7 of 10 you
  sit clearly toward warm"; `crosscheck.py` printed "(7 of 10)". Both now use within-profile
  distance and print no sten.
- The global-dimension rows (PDF and results page) printed `x of 10`. They now say
  above / below / at your own middle. The bar and the published equation carry the position.
- The PDF validity line read "Social desirability: 2 of 10", an item count that still reads as a
  mark. Now "you agreed with 2 of the 10 most flattering statements".
- `" of 10"` added to the copy-lint POPULATION ban list; docstrings excluded from that scan so
  documenting a ban does not read as committing it.

## The snapshot trap, and the guard that closes it
`DISPLAY_VERSION` was bumped to `disp-1.2.0` **before** the choosing fix landed, so snapshots
written in between froze the pre-fix copy — and snapshots are write-once. Found by the testing
agent (iteration 13), whose diagnosis was exactly right including that `choosing.py` itself was
already correct. Fixed by version, never by editing a stored document: `disp-1.2.1`, with the
reason recorded in the constant's comment. New guard
`backend/tests/test_snapshot_hygiene.py` fails if any snapshot at the **current** display_version
carries a sten-as-mark; older delivered versions are deliberately exempt, because they are a record
of what was said. Its needles are regexes, not the substring `" of 10"`, so the Delta's
"10.0 points", the EI "x of 5" and the item count are not false positives.

**Order lesson, recorded:** bump the version *after* the copy change, or in the same commit. Never
before.

## §4.1 · decided by measurement — `docs/CENTROID_SEPARATION.md`
**Regions work. Repair, do not replace.** On the 334 varied-answer results (the 516 uniform and
two-value ones are test artefacts and are excluded, and the 54% tie rate they produce is discarded):

- Mean centroid-distance-to-scatter ratio **1.45**; **14 of 15 pairs separate at ≥ 1.0**.
- The exception is **Diplomat · Empath at 0.87** — the pair a tie rule will fire on most.
- Nearest-centroid agrees with the current highest-score primary in **79%** of cases: a repair, not
  a different instrument.
- Top-two gap: median 7 points, **exactly tied 15%**, within 3 points 29%. The current code breaks a
  tie by `sorted()` order, which for equal scores is **dictionary insertion order** — so ~15% of
  readers are assigned an archetype by the order the six were typed into a JSON file. Live, and
  arbitrary.

Caveat stated in the report: this measures the instrument's internal geometry (item-set
separability, which is what R3 asked), **not** a respondent distribution.

**Not built, awaiting instruction:** nearest-region derivation, printed distances, and the
declining tie rule. **The Archetypes nav item is held**, as B5 §3 asked — regions work, so on
current evidence it stays.

## "It ends" typography
An SVG line with month ticks and a heavy terminal stop, labelled MONTH ONE / THREE. A line that
stops, never a bar that fills: no fill, no percentage, no completion state.

## Verification
`tests/` 145 passed · `backend/tests/` 150 + 42 passed · testing agent iteration 13 found the
snapshot leak (fixed by version bump) and iteration 14 verified the fix with 11 further acceptance
tests: **zero issues outstanding**.

---

# Session · June 2026 · CI unblock, the Essential tie state, and the assignment-free test

## CI failure diagnosed — the requirements file, not the tests
Both GitHub jobs died at `pip install -r backend/requirements.txt` in 18 and 22 seconds, before a
single test ran. Two pod-only pins:

- `litellm @ https://customer-assets.emergentagent.com/internal-asset/library/...` — 403 outside the pod.
- `emergentintegrations==0.2.0` — not on PyPI; pip reports "from versions: none".

Neither was imported anywhere in the repository. Both removed; the remaining 126 pins resolve from
the public index. New guard `tests/test_requirements_portability.py` fails on any URL, local path,
VCS or unpinned requirement, and on the known pod-only package names.

**Third defect of one class in a week** — `/app` paths, then a missing conftest, now a pod-only
wheel. Something true only inside the pod, baked into a thing that has to run outside it. The A0
gate is doing exactly what it was built for. Still unverified: an actual GitHub Actions run. The
user must push the `RK` branch via Save to GitHub.

## The Essential tie state — shipped (region work, step 1)
`TIE_MARGIN = 5` points in `backend/services/essential_scoring.py`. `rank_archetypes()` sorts on
`(-score, key)`, so an exact tie can no longer be broken by dictionary insertion order — which was
assigning an archetype to ~15% of readers by the order the six were typed into a JSON file. Inside
the margin the reading **names both and declines to rank**; the gap is printed either way, so a
declined rank reads as information rather than evasion.

Five is a provisional design choice, on the model of the 1.5-sten floor, and deliberately not the
conservative option: SD 11–13 puts the standard error of a difference around 8 points and a 90%
interval around 13. Three would have been chosen to hold the fire rate down, optimising for the
archetype's prominence rather than for what the instrument can tell apart. Fires on ~39% of varied
stored responses — affordable now the Delta is the headline. Re-derive when alpha lands.

Carried through every surface that names an archetype: result page (`essential-self-tie`,
`essential-ideal-tie`), PDF, `choosing._lens_name`, `crosscheck.build_synthesis`. Prose must never
quietly rank two patterns the reading declined to rank. `DISPLAY_VERSION` 1.2.1 → **1.3.2**
(1.3.0 the tie state · 1.3.1 the note labelled per lens and printed once · 1.3.2 both archetype
descriptions voiced, not just the first-named). No scoring, item or weight changed.

**Reader-facing copy is the consequence, not the ratio** — on `/methodology`: *"Two of our six
patterns sit closer together than the others; where a profile falls between them we name both
rather than choosing."* The ratios and correlations stay internal.

## The correlation matrix — the assignment-free test (`docs/CENTROID_SEPARATION.md` §6)
The centroid figures group results by whichever score is largest, which **guarantees separation by
construction**: 1.45 says the assignment rule is self-consistent, not that six item sets measure
six things. R3's claim was independence, so: Pearson matrix of the six scores, self lens, varied
answers, n = 370.

**Off-diagonal |r|: mean 0.17, median 0.09, max 0.56. One pair of fifteen reaches 0.5.** The six
are largely not redundant and there is no general factor with six names on it — the region model is
not in a degenerate space. Two pairs share variance, and §5 predicted both:
`adventurer`·`visionary` **+0.56** (the largest item overlap, showing up as arithmetic) and
`empath`·`diplomat` **+0.48** (the same pair that failed the centroid ratio at 0.87). Two
independent methods agree those two are least distinguishable — hence naming both rather than
reallocating items on weak evidence.

§5 restated with `key → "Display Name"` throughout: `adventurer` → The Voyager, `visionary` → The
Torchbearer. There is no seventh archetype called Visionary.

## Corpus quarantine, and the suppression rate re-checked (§7)
1,587 of 3,499 stored results (45%) come from sessions answering on fewer than four distinct
points. All flagged `data_quality: "low_variation"` and **excluded by default** in
`scripts/analyze_stored_corpus.py` — a flag nothing honours is documentation, not a control.

Then the number that started the guarantee investigation. The suppression rate of 1.0 was computed
across everything, and a uniform-answer session produces a perfectly flat profile, which is what
the flat-profile gate exists to suppress. Recomputed on varied answers only:

| scale set | all | varied |
|---|---|---|
| personality | 0.995 (n=581) | **0.992 (n=356)** |
| EI | 0.840 (n=630) | **0.781 (n=462)** |

**Not an artefact.** Personality is unchanged to three decimals; EI improves six points and is
still suppressed four readings in five. Removing the guarantee was right regardless. The hope that
enforcement becomes viable on a clean corpus is closed: at these thresholds it would not. MRD stays
in shadow, and the decision still turns on measured alpha.

## Verification
Full suite **373 passed, 2 warnings**. Testing agent iteration 15: 13/13 backend acceptance tests
against the deployed preview, tied and non-tied result pages, PDF, prose, ownership, combined PDF,
Junction and Flag Check all green — **zero issues, `retest_needed: false`**. Its one observation
(a tied header above a body voicing only the first archetype) was fixed in disp-1.3.2 and
re-verified on screen and in the PDF.

## Open, in priority order
1. **Region work items 1 and 3**: nearest-region derivation with printed distances. Not started.
   The Archetypes nav item stays held until a live region outcome supports it.
2. **The 50-item allocation** — `visionary` shares eight of ten items, and items 7, 34 and 36 feed
   no archetype. Now with a measured correlate (+0.56). A scoring change; needs its own version.
3. **Push `RK` and watch the first real Actions run.**
4. Everyday desirability pre-test (20–30 people). Disclosed as a gap on `/methodology`.
5. Production redirects; `/mirror` stays until externally verified.
6. Payments/entitlements and the partner dashboard: not built.

---

# Session · June 2026 (part two) · The reportable floors — `disp-1.4.0`

A defect report on the generated sample reading listed eighteen findings across four groups. All
eighteen are addressed. No scoring changed; `DISPLAY_VERSION` 1.3.4 → **1.4.0**. Full record in
**`docs/REPORTABLE_FLOORS.md`**.

The organising principle for every provisional constant here, and the one to keep: **set it so it
is more conservative than the derived value is likely to be.** A claim withdrawn later is worse
than a claim never made.

## A · Rules that were producing unsupported claims

**A1 · Convergence now needs displacement, not proximity.** Two readings landing mid-scale is what
uninformative answering produces — which is exactly why a machine-generated response set produced
two agreements and zero tensions. Both readings must now sit outside the middle third of their own
scale (`DISPLACEMENT_FLOOR = 1/6`) and sit the same way. Four outcomes: **agreement** (both
displaced, same way), **tension** (both displaced, opposite ways), **one reading** (only one
displaced — reported alone, not dressed as convergence), **nothing to report** (neither displaced,
printed rather than hidden). The "most reliable thing in this document" superlative is deleted
permanently: it is a claim about the instrument, made inside a personal reading, uncheckable by the
person holding it.

*Polarity is declared with the reading, never inferred.* Distance-from-closeness runs against
warmth; reassurance-need against stability. A naive same-direction test on raw scores reads a
genuine agreement as a disagreement. `tests/test_crosscheck_gate.py` locks the orientation.

*And personality displacement is within-profile, not absolute.* The frozen band table compresses
real answers into stens 4–8 (corpus histogram: 3–8, per-factor SD ≈ 1.0), so an absolute test
would never fire for anyone — and the absolute sten position is the norm-referenced claim the
product has already paused. It uses distance from the reader's own profile mean against the same
1.5-sten floor that decides which factors get named.

**A2 · A cross-instrument claim inherits the weaker input** — lower tier and lower confidence,
stated at the claim. Both original agreements paired a Low-confidence developmental instrument with
an established one and spoke with more authority than either.

**A3 · Elevation split from shape.** Mean signed gap was +10.17 against a reported mean absolute
gap of 10.8: the headline was mostly a level shift. **Elevation ships now** at display layer —
additive, so no comparability cost. **Centring is queued for `rk-1.1.0`**, because it changes the
widest gap from The Rock to The Empath and flips The Diplomat's sign. `centred_per_archetype` is
computed and carried but read by nothing.

**A4 · The EI floor.** `SEM = SD·√(1−α)`, `MRD = 1.645·√(2·SEM²)`. α assumed at a pessimistic
**0.70** (a low α gives a larger floor, so it can only suppress). SD taken as **0.60**, not the
observed 0.294 — the corpus is still mostly machine-generated and random answers under-disperse, so
0.294 would have set a floor of 0.375 and named differences the derived floor later suppresses.
**MRD = 0.765**, tested against the *next* domain rather than the mean. Facets get no ranking at
all until α is measured.

## B–D · Copy, calibration, presentation
- Same-archetype readings say "degree rather than kind"; "complement rather than a copy" is
  suppressed. The two rules were contradicting each other in one document.
- Dated and outcome forecasts removed ("around week six", "most likely to resent later",
  "a prediction rather than a post-mortem"), with a lint sweep over `frontend/src/content` and
  `pages` — the phrase lived in **two** places, backend and frontend, which is why the first fix
  missed one.
- The summary inherits the lowest contributing confidence, and a line sourced solely from a
  Low-confidence mid-scale instrument is not emitted — which removed the unsourceable
  "recognition rather than reassurance".
- Count-dependent phrasing swept across the whole locked register, not instance by instance
  (`tests/test_count_phrasing.py`); the PDF now reads its headings from the register instead of
  duplicating them.
- **Social desirability: 4 of 10 was flagged "elevated", which is chance.** Agreement is a Likert
  threshold, so p = 0.4 → null mean 4.0, SD 1.55. Cuts moved to **7** (~+1.9 SD) and **9**. Derived
  from the null, not from a percentile of our own distribution, which would have fixed the flag
  rate by construction forever. Corpus checks it: 11 of 446 clean profiles reach 7+.
- **Speeding is per item, from the item**: 300 ms per word (1,200 ms minimum), reporting the share
  of items below their own floor. Not yet validated against real timing — every stored timing is
  synthetic. The mean it replaced passed anyone who raced through most of an instrument.
- The consistency index is labelled with direction, range, triple count and what is ordinary. The
  left-hand rate is out of reader-facing output (9 of 21 under randomisation is unremarkable).
- Sten middle band widened to one full step, so adjacent stens cannot get labels pointing in
  opposite directions. Everyday ties print as ties, naming the other tied domains. EI decimals
  consistent. The shadow pull prints what selected it.

## Verification
Full suite **429 passed** (includes the testing agent's `test_iteration16.py`). Testing agent
iteration 16 found three real frontend leaks — the duplicated situation-note string, a missing
neutral note at count 4, and the Learn essays — all fixed; **iteration 17 confirmed all three with
zero issues and `retest_needed: false`**.

## Open, in priority order
1. **`rk-1.1.0`**, carrying everything queued for scoring at once (an ALGO bump costs retake
   comparability, so it is paid once): centred Delta gaps; the 50-item archetype reallocation, now
   with a measured correlate (`adventurer`·`visionary` r = +0.56); anything the tie state's live
   behaviour turns up.
2. **Region derivation with printed distances** — nearest-region assignment, new results only. The
   Archetypes nav item stays held until a live region outcome supports it.
3. **Measure α on the EI and archetype banks.** Three provisional constants are waiting on it: the
   EI MRD, the 1.5-sten loudest floor, the 5-point tie margin. All three are deliberately
   conservative so that nothing they permit today has to be retracted.
4. **Validate 300 ms/word against real timing**, once real timings exist.
5. Push `RK` and watch the first real Actions run.
6. Everyday desirability pre-test (20–30 people); production redirects; payments/entitlements; the
   partner dashboard. All unchanged.

---

# Session · June 2026 (part three) · The sten retired · `disp-1.5.0`

The user's ten decisions on the report-validity round. No scoring change; `ALGO_VERSION` stays
`rk-1.0.0`, `DISPLAY_VERSION` 1.4.0 → **1.5.1**, `within_person` wp-1.0.0 → **wp-1.1.0**.
Full record in **`docs/REPORTABLE_FLOORS.md`** §0, §3, §3a, §4, §4a, §8, §9.

## The rule that governs the rest
**Derive, then round up. Never down.** A provisional floor rounded down loosens a threshold
already resting on an assumption; rounded up it costs only claims that could not be defended. Both
floors in a combined report are now rounded by the same logic: EI 0.765 → **0.8**, Personality
19.109 → **20 points of scale**.

## Q1 · No sten reaches a reader
The band table is not merely un-normed, it is malformed: Factor A's ten band widths run
3,2,3,3,4,3,**8**,2,3,2 across raw 8–40 — one sten spanning a quarter of the raw range — with
provenance recorded only as "super-admin config over defaults". Retired from the reader-facing
layer rather than recalibrated (recalibration is a scoring change and needs a reference sample).

- Reader-facing unit is **percent of each factor's own scale**, described as a distance from the
  reader's **own profile average**.
- Floor is **absolute**: 20 points of scale, from an assumed scale SD of 15 points and α = 0.70,
  rounded up. A floor set as a fraction of the reader's own profile SD was rejected — standardise
  fifteen factors by their own spread and the largest always lands near +1.8, for everybody,
  including the even profile that should name nothing.
- **15 rather than range/6 (16.67 → floor 22)** is a declared choice, documented: it is the same
  assumption the EI floor already uses (0.60 of a four-point span *is* 15% of range), and one
  shared assumption across two instruments in one document beats a slightly stricter floor on one.
  15 is the more permissive of the two, and it says so.
- **An even profile names nothing** and prints why. No fallback to the highest.
- **Stens stay scored and stored** (raw material for rebuilding the table; removing them would be
  a scoring change) and are marked `not_for_display` **in the payload**, with the reason — because
  the way a sten reached a reader was sitting in the payload unmarked.
- Surfaces changed: Personality result page (bar now percent-of-scale), combined + individual
  PDFs (global-dimension figures suppressed, factor table on the position layer), `choosing.py`,
  `crosscheck.py`, Samples, Methodology, locked copy (`samples.position_explainer`).
- **One documented exemption:** the global-dimension equation `5.5 + Σ(w × (sten − 5.5))` inside
  the collapsed "How this number is built" panel and its PDF equivalent — the published equation
  cannot be audited without it. Labelled as arithmetic, not a comparison. `tests/
  test_no_sten_display.py` walks every surface and allows only that one.
- **Also converted:** five hand-written cross-instrument findings fired on absolute `sten ≥ 7 / ≤ 4`.
  Same absolute 20-point rule now, and their copy no longer says "reads you as emotionally stable
  across life in general".
- `result["loudest"]` is **recomputed at render**, never served from the stored field: every result
  written before 1.5.0 selected on the retired 1.5-sten floor.

## Q2 · EI, two branches, and the presentation follows the branch
Gating the sentences was not enough — four figures to two decimals in descending order rank
themselves whatever the prose says, and nearest-0.5 still prints 3.5 against 3.0.
- **Resolved** (some pair clears 0.8): figures, bars, and the named highest/lowest return.
- **Suppressed**: one **shared band** ("All four domains fall between 3.0 and 3.5 on the 1–5
  scale") plus the two audit numbers — observed spread and the floor — so the reader can check the
  suppression. Domain names and descriptions stay; the overall mean stays (one figure, ranks
  nothing).
- **Facets: names only, no figures.** Shorter scales, lower α, larger floor than the domains have
  already failed; fourteen numbers are a ranking whatever the order.

## Q3/Q8 · The corpus, and what wrote it — ANSWERED
`scripts/patterned_provenance.py`. Three flags on `pattern_flags`, tagged independently, **nothing
excluded** (no threshold is derived from this corpus, so exclusion buys nothing and would destroy
the provenance evidence): `sd_fixed_agreement` 616, `cyclic_sequence` 334 (all period 1),
`duplicate_sequence` 3,636.

The third flag was not predicted and is the one that answered the question. Only **1,787 distinct
answer vectors** exist across 5,454 answered sessions; **3,717 sessions share their exact answer
sequence** with another, one closeness vector appearing **653 times**. The accounts are
`E2E User`, `Pytest User`, `Reset User`, `Iter6`, all `@ratherknow.com`, across ten days.

**It is our own test suite, writing into the collection the corpus is counted from.** Not a
seeding script, not outside traffic. A data-integrity finding, because it touches every count this
product will ever quote from `results`. **On the backlog, not fixed in this pass.**

Consequence recorded in code (`reportable.SD_CORPUS_STATUS`) and docs: **the corpus cannot
validate the social-desirability null.** Excluding the fixed-count class leaves n = 232, of which
5 reach 7+ — 2.16% against the null's 5.48%. Attrition recorded as a sequence: 5,206 → 3,619 →
891 → 275, and essentially all of the remainder still carries `duplicate_sequence`. There is no
clean remainder large enough to calibrate anything at any stage.

## Q4 · The asymmetry is stated
Closeness clears an absolute **position** rule (outside the middle third of its 1–7 scale);
Personality clears an absolute **distance from the reader's own profile average** (20 points of
scale). Both absolute, absolute about different things. Every agreement, tension and single
reading now names the test each side passed.

## disp-1.5.1, and why there is a point release
The testing agent (iteration 18: zero critical, zero UI issues) found the `not_for_display` marker
missing from the API payload for snapshots written before 1.5.0. It is now attached at read time
as well as at score time — but 1.5.0 narrative snapshots had already been written, and a snapshot
is write-once. So the fix is a version, never an edit to a stored document: **`disp-1.5.1`**. Same
lesson as 1.2.1, recorded again.

## Verification
`tests/` **204 passed** · `backend/tests/` **246 passed** (all iteration suites updated to the new
basis rather than deleted). Both result pages rendered on the preview, desktop and mobile: the EI
suppressed branch shows the band + 0.25 spread + 0.8 floor and no domain figures; the Personality
page shows percent-of-scale markers and the loudest-none copy, with the only "sten" on the page
inside the composite equation.

## Open, in priority order
1. **Stop the test suite writing into `results`** — a per-run database, or a `synthetic: true`
   stamp every count honours. Until then no figure quoted from `results` means anything.
2. **Measure α** on the EI and archetype banks. Four provisional constants wait on it: the EI
   floor (0.8), the Personality factor floor (20 pp), the 5-point Essential tie margin, and the
   assumed SDs behind the first two.
3. `rk-1.1.0`, carrying every queued scoring change at once: centred Delta gaps, the 50-item
   archetype reallocation (`adventurer`·`visionary` r = +0.56), the tie state's live behaviour.
   Rebuilding the sten band table belongs here too, if a reference sample ever exists.
4. Region derivation with printed distances; the Archetypes nav item stays held.
5. Validate 300 ms/word against real timing.
6. Push `RK` and watch the first real Actions run · Everyday desirability pre-test · production
   redirects · payments/entitlements · partner dashboard. All unchanged.

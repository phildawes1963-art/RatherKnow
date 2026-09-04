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

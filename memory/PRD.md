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

**P0 (rk-1.1.0 Phase b — now unblocked by dropping D2)**
- **D1 remains: measure α for every scale.** Every MRD threshold is a literature placeholder. Nothing
  enforces and no guarantee copy ships until these are measured. `RK_ALLOW_PLACEHOLDER_ALPHA=1` is the
  deliberate acknowledgement that they are provisional.
- Decide the display change on the evidence now in hand: commonness fractions are computed and
  returned by the API (`result.commonness`, `disp-1.0.0`) but are **not yet shown in the UI**. Turning
  them on is a copy-register change, and globals must stay excluded.
- Snapshot the resolved narrative and rendered PDF on first render (TRD T1.1) before `display_version`
  is ever bumped, so corrections cannot alter a delivered report.

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

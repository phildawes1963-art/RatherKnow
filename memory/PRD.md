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

## Backlog
**P0 (Phase 4 — cutover)**
- Point ratherknow.com at this build; publish `redirect_map.json` as real 301s from
  `mymirrorreport.com/mirror/*`; verify in production **before** removing `/mirror` from the parent.
- Submit sitemap; confirm archetype pages indexed.

**P1**
- Use the captured `situation` to shape report framing — currently it is stored and shown, but the
  report copy does not yet differ by Single & dating / In a relationship / Post-breakup.
- Password reset. There is no email provider wired, so today a forgotten password is unrecoverable.
- Learn essay on the Delta (`/learn/relationship-delta`) — referenced but not yet authored.
- Object storage for illustration/diploma/OG assets and the audio demo.

**P2**
- Paid tier boundaries + the published price ceiling on the Promise page; one inert unlock boundary
  already assumed, no payment integration until tiers are confirmed.
- Split `mirror_v2.py` scoring helpers into `services/mirror_v2_scoring.py`; cap batch response length.

## Open questions
- Do free-tier boundaries differ per instrument, or is everything free until paid tiers exist?
- Parent attribution is currently visible in the footer — keep or clean split?

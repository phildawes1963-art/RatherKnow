# RatherKnow — Product & Technical Specification

**Version 1.1.0 · as built, June 2026 · INTERNAL**

This document supersedes `rk-1.1.0-PRD.md` and `rk-1.1.0-TRD.md`, which describe intent. This one
describes what exists. Every figure in Parts I and II was read out of the running code, not from a
plan. Part III is the defect register. Part IV is the forward spec for 1.2.0.

**Not for publication.** Part III names shipped defects, placeholder reliabilities and promises
made on the site that have nothing behind them yet. The publishable artefacts are
`frontend/public/docs/ratherknow-scoring-spec.pdf` and
`frontend/public/docs/ratherknow-archetypes.pdf`.

---

# Part 0 · Summary

RatherKnow is a **single-player** instrument. It measures how one person chooses in
relationships, from that person's own answers, and it never describes anybody else.

Five instruments and one reflection are live behind an account. **456 items** in total. Two
instruments are established with calibrated norms; three are ours and developmental. Nothing is
purchasable: the pricing ladder is published, and the checkout does not exist.

The thing that distinguishes the product commercially is not the psychometrics — it is the
refusals. No compatibility score, no types, no predictions, no matching, a published evidence tier
on every instrument, immutable version-stamped results, and the equations printed in the report.
That set is difficult to copy because it costs conversion, and it is the reason a practitioner can
put their name beside it.

| At a glance | Value |
|---|---|
| Live instruments | 5 + Flag Check |
| Total items | 456 |
| Backend tests | 185, green |
| Revenue | £0 / $0 — no payment integration exists |
| Deployment | preview only; no production deployment evidenced |

---

# Part I · Product, as built

## 1. Premise and refusals

You answer instruments about yourself. The product tells you how you choose: the speed of it,
which qualities you over-weight, which you cannot see because they come free to you, and where the
gap sits between who you are and who you say you want.

**The refusals are load-bearing product decisions, not marketing.** In order of how expensive they
are to keep:

1. No compatibility score. Not between people, not between archetypes, not ever.
2. No matching, no profiles, no other people's data.
3. No types, boxes or quadrants — positions between poles, with both poles named.
4. No predictions about how any relationship goes.
5. No urgency, no countdowns, nothing that expires.
6. Every instrument publishes its own evidence tier, including the weak ones.
7. Composite equations are published, including their uncalibrated gains.
8. Results are version-stamped and never recomputed.
9. Safety and abuse referrals on every page, free, behind nothing.
10. Stated at the top of the promise: it cannot find you love. Nothing can.

Copy expressing 1–10 is hash-locked (§18).

## 2. Users, accounts and situations

One user type. Registration requires name, email, password and a **relationship situation**:

| Value | Label |
|---|---|
| `single_dating` | Single and dating |
| `in_relationship` | In a relationship |
| `post_breakup` | Post-breakup |

The situation reframes interpretation copy and the PDF notes. **It never changes a score.** It is
user-editable at any time, and changing it produces a new report snapshot rather than rewriting the
old one (§14).

Access is gated **before questions begin** — deliberate, because results are retrievable later and
an anonymous result cannot be. The earlier "Free. Anonymous. No account, no card." claim was
rewritten rather than left standing.

The Flag Check is the sole exception: no account, by design.

## 3. The instruments

| Key | Name | Items | Tier | Scale | Stated time |
|---|---|---|---|---|---|
| `essential` | Essential Mirror | 100 (50 × 2 lenses) | Developmental | 1–5 Likert | ~25 min |
| `personality` | Personality Mirror | 130 | **Established** | 1–5 Likert | 15–20 min |
| `eq` | EI Mirror | 140 | **Established** | 1–5 Likert | 15–20 min |
| `closeness` | Closeness Mirror (MI-AS-36) | 37 | Developmental | 1–7, from bank | ~5 min |
| `everyday` | Everyday Mirror (MI-EV-49) | 49 | Developmental | forced choice, 2 options | ~7 min |

- **Essential** — six archetypes scored twice, once as yourself and once as the partner you want.
  Produces the Delta. Full internals and defects in `docs/ARCHETYPES_SPEC.md`.

- **Personality** — 15 primary factors and 5 global dimensions. The item bank is 130 of the P150's
  items (Switch module removed), scored against the same norms snapshot as the parent product, so
  the two are directly comparable.

- **EI** — Goleman four-domain, sub-dimension roll-ups, min/max normalised.

- **Closeness** — two dimensions (anxiety, avoidance) on a well-replicated research tradition, with
  our own items. Both are **distance** scores: high means more of the thing named, not more ease.

- **Everyday** — the only instrument that asks you to *choose* rather than describe yourself, and
  therefore the only one that can contradict your self-description. 28 position items (four per
  domain across pace, sociability, order, novelty, money, recovery, togetherness) then 21
  round-robin priority comparisons. Carries the only behavioural validity evidence in the product:
  circular-triad consistency (ζ = 1 − 24d/336), side bias, and a per-item time floor.

Personality and EI item order is deterministically **interleaved** so no trait or sub-dimension
repeats consecutively. Closeness keeps its spec order. Everyday keeps a fixed order for everyone
with **sides randomised per session** — required, because the side-bias index is meaningless
otherwise.

## 4. What a reader gets

Four layers, in increasing distance from the raw data:

1. **Scores** — frozen, immutable, version-stamped.
2. **Position language** — commonness fractions on normed factors; positions between named poles
   elsewhere. No sten and no "x out of 10" reaches a reader.
3. **"How you choose"** — per-instrument translation of scores into selection behaviour. The
   product's actual value proposition.
4. **Cross-check** — where instruments agree (signal), where they disagree (a finding), and a
   synthesis. A bare "no tensions worth reporting" is not an acceptable terminal state.

Plus a printable single-instrument PDF and a combined PDF across everything finished.

## 5. The Delta

The distance between the self lens and the ideal lens on the Essential Mirror. The one number that
says something neither lens says alone. A zero Delta on the archetype named as the ideal partner
is a finding, not a contradiction, and the report says so explicitly.

## 6. Flag Check

Nine questions — eight items plus a safety item — about one specific relationship. Free, no
account, ~3 minutes. Stored in its own collection, `mirror_v2_reflections`, never alongside scored
sessions.

**It is never scored, banded, labelled, risk-rated or diagnosed.** It categorises responses
(`reprice` / `explain` / `late` / `none`) and reflects them back. The safety item routes to
referrals. This constraint is absolute and structurally enforced by keeping it out of the scoring
path entirely.

## 7. Content surface

| Public | Gated |
|---|---|
| `/` `/promise` `/methodology` `/safety` `/learn` `/learn/:slug` `/faq` `/samples` `/flag-check` `/archetypes` `/archetypes/:slug` `/partners` `/register` `/login` `/forgot-password` `/reset-password` | `/take/:instrument` `/results/:sessionId` `/mirrors` |

Header nav is five items: The instruments, Archetypes, Promise, Learn, Safety. Archetype pages are
menu-reachable — a standing requirement.

## 8. Commercial model

Published ladder, **USD**:

| Tier | Price | Adds | Live? |
|---|---|---|---|
| Your Archetype | Free | Essential Mirror, archetype, Delta | **Yes** |
| The Everyday Reading | $14 | Everyday Mirror | No |
| The Full Reading | $29 | Personality, EI, Closeness, read together | No |

$29 is stated on the page as the **ceiling for the whole practice**. Nothing renews and nothing
expires. Both paid tiers are labelled *not yet purchasable*, because no payment integration exists
and the page would otherwise be lying.

**The guarantee** — "if your results don't produce enough for us to say something useful, we'll
tell you, and refund half" — is published in body copy. See §15 and Part III/R1: the mechanism that
would decide when it fires currently fires on essentially every reading.

## 9. Partner programme

`/partners`, linked from the footer sitewide. Eight sections, leading with the ten refusals rather
than the terms. Offer: 30% for twelve months from first visit, no exclusivity, no lock-in, free
access for the practitioner.

Applications: four fields plus a name → `POST /api/partners/apply`, open (no account needed),
3-per-24h rate limit, stored in `partner_applications`.

**The page promises a partner link and a dashboard. Neither exists** (Part III/R2).

---

# Part II · Technical, as built

## 10. Architecture

React 19 SPA + FastAPI + MongoDB (Motor), supervisor-managed, single pod behind a Kubernetes
ingress. Backend on `0.0.0.0:8001`, frontend on `3000`; everything under `/api` routes to the
backend. No queue, no cache, no worker, no object storage.

```
frontend/src/{pages,components,content,lib}
backend/{server.py,auth.py,routes/,services/,constants/}
docs/  scripts/  tests/  memory/
```

## 11. Data model

| Collection | Holds | Immutable? |
|---|---|---|
| `users` | account, bcrypt hash, situation | mutable |
| `mirror_v2_sessions` | in-progress responses, `presentation.side_map`, completed `result` | result written once |
| `mirror_v2_reflections` | Flag Check responses — never scored | append |
| `results` | canonical scored snapshot, `algo_version`, `user_id` | `$setOnInsert` |
| `narratives` | resolved layer-3 narrative per (session, display_version, situation) | `$setOnInsert` |
| `rendered_pdfs` | PDF bytes per (session, kind, display_version, situation) | write-once |
| `password_resets` | reset tokens, 60-min TTL | consumed |
| `login_attempts` | lockout counters | rolling |
| `partner_applications` | practitioner applications, `status: unread` | append |
| `status_checks` | CRA boilerplate, unused | — |

No `PyObjectId`/`BaseDocument` abstraction: documents use application-generated `uuid4` string ids
and `_id` is projected out at every read, so raw ObjectIds never reach a response.

## 12. API surface

**`/api/v2` — Mirror**

| Method | Path | Auth |
|---|---|---|
| GET | `/instruments` | open |
| POST | `/assessments` | required |
| GET | `/assessments/{id}` | owner |
| PUT | `/assessments/{id}/responses` | owner |
| POST | `/assessments/{id}/complete` | owner |
| GET | `/assessments/{id}/result` | owner |
| GET | `/assessments/{id}/report.pdf` | owner |
| GET | `/reports/combined.pdf` | required |
| POST | `/mirrors/summary`, `/mirrors/findings` | required |
| POST/GET/PUT/POST | `/reflections…` | **open** (Flag Check) |
| GET | `/diagnostics/mrd` | required |

**`/api/auth`** — `register`, `login`, `me`, `me/sessions`, `forgot-password`, `reset-password`,
`me/situation` (PATCH), `claim`.
**`/api/partners`** — `audience-options`, `apply` (both open).

Ownership is enforced on every session-scoped endpoint. Cross-user access returns 403, anonymous
401, incomplete-session PDF 409, unknown 404.

## 13. Scoring and versioning

**Hard rule: scoring is frozen.** No score, norm, weight or equation changes without a deliberate
versioned programme with parity coverage.

| Stamp | Value | Governs |
|---|---|---|
| `ALGO_VERSION` | `rk-1.0.0` | scoring |
| `bank_version` | `1.0.0` | Closeness and Everyday item banks |
| `DISPLAY_VERSION` | `disp-1.0.0` | commonness / position mapping |
| `CONTENT_VERSION` | `copy-1.1.0` | narrative copy |
| MRD `profile_version` | `mrd-1.0.0` | reliability thresholds |

Full derivations are published in `docs/SCORING_SPEC.md`. Two facts worth restating here:

- The sten→percentile table shipped wrong at stens 4 and 7 (27/73 instead of 23/77). Corrected, and
  pinned to Φ((sten − 5.5)/2) by test.

- The five Personality globals are `5.5 + Σ(weight × (sten − 5.5))` with **gain 1.0, uncalibrated**,
  then clipped to 1–10. On an extreme profile Independence computes to **11.2** and publishes as 10.
  The clip is now recorded (`clamp_events`, `raw_precise`) and a clamped value is barred from
  carrying any population statement.

## 14. Three-layer immutability

Layer 1 responses and layer 2 scores were already immutable. Layer 3 — narrative — is derived at
read time from versioned mapping tables that have already needed one correction, so it is
snapshotted.

`services/narrative.py`: on first render the resolved narrative is persisted write-once; on first
PDF build the bytes are stored and served thereafter. A `display_version` bump affects only reports
rendered after it.

**The snapshot key includes `situation`.** This is the important design point. Freezing exists to
stop *us* silently rewriting a delivered document; it must not stop a reader deliberately asking for
a different lens. Switching situation produces a new snapshot; switching back returns the original
bytes unchanged. The combined roll-up is invalidated when a new instrument finishes; individual
reports never are.

## 15. The MRD engine — shadow mode

`services/mrd.py`. Nothing should describe two scores as different when the instrument cannot tell
them apart. SEM = SD·√(1−α); MRD = z·√(SEM₁²+SEM₂²) at z = 1.645. Four gates: pairwise,
flat-profile, distinctiveness, and clustering.

| Scale set | SD | α | MRD |
|---|---|---|---|
| Personality primaries | 2.0 | 0.75 | 2.326 sten |
| Personality globals | 2.0 | 0.85 | 1.802 sten |
| EI sub-dimensions | 0.55 | 0.75 | 0.640 |
| EI domains | 0.5 | 0.85 | 0.451 |
| Closeness dimensions | 1.1 | 0.85 | 0.991 |

**Every α is a literature placeholder.** `config()` refuses to load unless
`RK_ALLOW_PLACEHOLDER_ALPHA=1` explicitly acknowledges that.

It ships in **shadow**: gates are evaluated and persisted to `result.mrd.suppressions`, and nothing
is withheld from any reader. `RK_MRD_MODE=enforce` flips it. See Part III/R1 for why it has not been
flipped.

## 16. Display layer

`services/display.py`. Pure functions, no DB, no prose. Normed primary factors get a rounded
population fraction ("about 1 in 4"), never a decimal and never a two-digit percentile. Composites
and clamped values raise `NotNormReferenced` rather than degrading to a guess — the refusal is
enforced by exception, not by editorial care.

## 17. Auth and security

bcrypt with per-password salt. JWT HS256, `JWT_SECRET` from env, **30-day** access token. Five
failed attempts per email+address → 15-minute lockout via `login_attempts`; the key uses the
forwarded chain, because keying on the Kubernetes peer address made every pod share one bucket.
Password reset tokens expire in 60 minutes and unknown emails return success (no enumeration).

## 18. Copy governance

Sixteen locked copy blocks in `frontend/src/content/locked_copy.json`, consumed only via
`content/register.js`, hash-enforced by `tests/test_locked_copy.py`. Changing locked copy requires
deliberately regenerating the hash register.

`tests/test_copy_lint.py` statically parses the narrative modules and fails on prediction verbs
about the reader ("you will", "expect to", "you'll consistently", "leading to"…), on any phrasing
describing a person who did not answer, and on a canned paragraph rendering twice in one document.
Anchored on "you", so "we will never sell your data" survives.

`"validated"` is restricted to Personality and EI reference claims.

## 19. PDFs

ReportLab. `report_pdf.py` builds single-instrument and combined reports: scores, position
language, situation notes, "How you choose", composite provenance, safety constraints, and version
stamps. Bytes are snapshotted (§14). Doc PDFs are built from Markdown via xhtml2pdf in `scripts/`.

## 20. Migration and redirects

Legacy `mymirrorreport.com/mirror/*` and `/mirror-index/*` mappings exist as generated artefacts:
`frontend/public/_redirects`, `docs/redirects.conf`, `docs/edge/worker.js`, `docs/redirect_map.json`,
built and checked by `scripts/build_redirects.py` / `verify_redirects.py`.

**Verified locally against the generated rules only. Not verified against a live domain.**
Invariant: the parent `/mirror` surface must not be removed until real 301s are confirmed in
production.

## 21. Testing

185 tests, green. `pytest -n 2 --dist loadscope`.

| Area | File | n |
|---|---|---|
| Instrument lifecycles | `test_mirror_v2.py` | 18 |
| Choosing / cross-check / item order | `test_iteration6.py` | 18 |
| PDF reports | `test_pdf_report.py` | 17 |
| Auth | `test_auth.py` | 16 |
| Everyday Mirror | `test_everyday.py` | 15 |
| This release | `test_iteration9.py` | 14 |
| Combined PDF / situation | `test_iteration5.py` | 14 |
| MRD gates | `test_mrd.py` | 10 |
| Reset / situation / redirects | `test_iteration3.py` | 10 |
| Display mapping | `test_display.py` | 8 |
| Archetype docs | `test_archetype_docs.py` | 8 |
| Composites | `test_composites.py` + API | 14 |
| Snapshot immutability | `test_immutability.py` | 4 |
| Copy lint | `test_copy_lint.py` | 3 |
| Locked copy hashes | `test_locked_copy.py` | 2 |

## 22. Configuration

Backend: `MONGO_URL`, `DB_NAME`, `CORS_ORIGINS`, `JWT_SECRET`, `EMERGENT_EMAIL_KEY`,
`EMAIL_FROM_NAME`, `APP_BASE_URL`, `RK_ALLOW_PLACEHOLDER_ALPHA`, `RK_MRD_MODE`.
Frontend: `REACT_APP_BACKEND_URL`.

No defaults anywhere: missing config fails fast at import.

---

# Part III · Defect and risk register

Ordered by what would hurt most. **Nothing in this section is fixed.**

### R1 — The guarantee has no working mechanism · SEVERE
The site promises a half refund when the report can't say enough. The MRD gates would decide that,
and in shadow mode their suppression rate across ~1,000 gate-eligible stored results is **1.0**.
Personality primaries read flat in 197/213 cases; Closeness in 490/490. On the real reference
profile — 8 stens of range, six factors at the ceiling — MRD 2.33 folds all fifteen primaries into
a **single undifferentiated cluster** whose centroid is the personal mean, so nothing in it is
reportable.

Enforcing today would empty the Personality Mirror and trigger the refund on nearly every reading.
The thresholds are almost certainly too conservative because α is a guess, not because the profiles
are flat. **Do not enforce, and do not promote that guarantee line, until α is measured.**

### R2 — Partner promises with nothing behind them · HIGH
`/partners` promises a personal link and a dashboard of clicks, completions and earnings. There is
no attribution, no dashboard and no payout mechanism. Applications land in `partner_applications`
with **no notification to anyone**. Accepted knowingly on the basis that the first ten partnerships
are founder-led — but the first approved partner is owed either the plumbing or a straight
explanation, and somebody has to actually read that collection.

### R3 — Essential Mirror archetypes are not independent · HIGH
60 scoring slots drawn from a 50-item lens: 13 items double-counted. The **Torchbearer shares 8 of
its 10 items** (5 Challenger, 3 Voyager), so it is largely a linear combination of two others and
"primary Torchbearer, secondary Challenger" is near-mechanical. The Diplomat shares 4 of 10.
Items **7, 34, 36** feed no archetype at all. `diplomat.reverse = [24]` is **inert** — item 24 is a
Challenger item with no reversal, so the Challenger score is probably missing an intended reverse.
Full detail: `docs/ARCHETYPES_SPEC.md` §4–6. All three fixes change scores, so they need a version
bump with old reports keeping their numbers.

### R4 — Reliability is unmeasured across the board · HIGH
No α, no test–retest, no factor structure for any of our own instruments. The Personality/EI norms
are inherited. This is the single root cause behind R1 and behind the percentile question.
Cheapest first step available now: real test–retest between the two same-item P150 sheets.

### R5 — Everyday Mirror pre-test outstanding · MEDIUM
No desirability pre-test on the 49 option pairs. Until it runs, unmatched pairs may behave as a
Likert scale with extra steps. Disclosed honestly in the payload, the tier statement and the PDF,
and the instrument never anchors a reading alone — but that disclosure is a mitigation, not a fix.
Needs 20–30 raters; any pair splitting worse than 65/35 gets rewritten. A pilot of n ≥ 200 would
also show whether four items per domain is enough (it may not be — expect undifferentiated domains).

### R6 — Production redirects unverified · MEDIUM
Rules generated and locally checked; never run against a live domain. Deleting the parent `/mirror`
surface before real 301s are confirmed would drop the inbound traffic this product is inheriting.

### R7 — `compatibility` field name · MEDIUM
The Essential result carries a field literally named `compatibility`, backed by `_COMPATIBILITY`. It
holds a top-two blend narrative within one lens — no number, no second person — so it does not
breach the refusal. But it is named like the one thing permanently ruled out, and it appears in API
responses and stored snapshots. Rename to `blend`, carrying the old key for existing snapshots.

### R8 — Outbound email receipt unverified · MEDIUM
The reset flow works and the provider returns `202 Accepted`. Nobody has confirmed an email
actually arriving in an inbox. Verify before relying on password reset in production.

### R9 — Unbounded PDF storage · LOW
`rendered_pdfs` grows one document per session per situation per display version, 7–200KB each.
Fine now; needs a retention policy or object storage before real traffic.

### R10 — No data retention or deletion path · LOW now, blocking for launch
No retention policy, no export, no account deletion, no GDPR/DSAR route. The product holds
intimate self-report data about relationships, which is close to the most sensitive category there
is. This must exist before a public launch in any consumer jurisdiction.

### R11 — Shadow map incomplete · LOW
`adventurer` (the Voyager) is nobody's shadow, so no reader is ever told it is their shadow pull.
`rock` is the shadow of two. Decide whether that is editorial or an oversight and record it.

### R12 — No production deployment · CONTEXT
Preview only. No custom domain, no monitoring, no backups, no error tracking, no CI runner
executing the hash and lint tests automatically — they are enforced by convention today, not by a
gate.

---

# Part IV · Next version — 1.2.0

Sequenced so that nothing depends on research that hasn't happened.

## Phase A · Honesty debt (no research required)

- **A1** Rename `compatibility` → `blend`, old key carried in parallel. (R7)

- **A2** Import-time assert that every `reverse` entry appears in its own archetype's `questions`.
  Cheap, and stops R3's third defect recurring whatever is decided about the rest.

- **A3** Partner application notification via the existing Emergent-managed Resend integration, and
  confirm an email actually arrives — closing R8 in the same move. (R2, R8)

- **A4** Account deletion + data export. (R10)

- **A5** Retention policy for `rendered_pdfs` and `narratives`. (R9)

- **A6** CI gate that runs the locked-copy hash test, copy lint and the full suite. (R12)

- **A7** Remove the guarantee line from published copy, or reword it to something the current
  mechanism can honour. This is the highest-value item in Phase A. (R1)

## Phase B · Measurement (unblocks everything else)

- **B1** Compute real test–retest from the two same-item P150 sheets. Cheapest evidence available.

- **B2** Measure α per scale on live data; replace `reliability_1_0_0.json`, set
  `placeholder: false`, bump to `mrd-1.1.0`, remove `RK_ALLOW_PLACEHOLDER_ALPHA` from the
  environment so the guard becomes real. (R4)

- **B3** Re-derive MRD thresholds and re-read the shadow suppression rate. Decide then: enforce,
  loosen to a 68% interval for within-person profile reading, or keep the gates as an internal
  honesty check that never governs output. Reinstate the guarantee only if the rate supports it.

- **B4** Everyday Mirror desirability pre-test, then the n ≥ 200 pilot. (R5)

- **B5** Essential Mirror factor structure — does the item overlap in R3 actually distort primary
  assignment, and by how much? Evidence before re-allocation.

## Phase C · Scoring v2 (gated on Phase B, ships as `rk-1.1.0` scoring)
Everything here changes numbers, so it ships as one version bump with parity tests, and every
existing report keeps its original figures.

- **C1** Re-allocate the Essential 50 so archetypes have independent items; allocate or retire items
  7/34/36; resolve item 24's reversal. (R3)

- **C2** Calibrate the global composite gains, or state permanently that they are uncalibrated and
  keep gain 1.0.

- **C3** Only if B2 supports it: percentiles on normed scales. Not a relabelling of stens — a
  defined reference distribution and an updated claims register, or nothing.

## Phase D · Product

- **D1** Progressive unlock across sittings, so value lands after each instrument rather than after
  456 items.

- **D2** Everyday Mirror Read 5 (Negotiability) and the priors register from the draft §8.

- **D3** Shareable single-finding card — no score, no profile, no second person. The Everyday
  Mirror produces the one line nobody else can print ("you feel strongest about money and you'd
  trade it first"), and it can travel without breaking a single refusal.

- **D4** Archetype cost pull-quotes on the public archetype pages.

## Phase E · Commercial (gated on D1)

- **E1** Stripe, test key already in the environment. Tiers as published in §8; ceiling $29.

- **E2** `partner_ref` capture and Stripe metadata attribution. Manual payouts for the first ten;
  no third-party affiliate platform until there is revenue to attribute. (R2)

- **E3** Production deployment, domain, monitoring, backups.

- **E4** Verify the legacy 301s against the live domains, **then** retire parent `/mirror`. (R6)

## Explicitly not in 1.2.0
Matching, compatibility scoring, couple mode, partner-facing anything, predictions, a partner
affiliate platform, or any relaxation of the ten refusals.

---

*Sources: `backend/` and `frontend/src/` as at June 2026; `docs/SCORING_SPEC.md`;
`docs/ARCHETYPES_SPEC.md`; `GET /api/v2/diagnostics/mrd`; `memory/PRD.md`;
test reports `test_reports/iteration_1..9.json`.*

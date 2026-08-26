# RatherKnow — Scoring Specification

**Status:** as-built, generated from the shipped code (not from documentation).
**Date:** June 2026 · **Algo version stamped on every result:** `rk-1.0.0`
**Source of truth for each section is named inline** so any claim here can be checked against the file.

This document exists to support a decision about changing the scoring presentation (stens vs
percentiles vs something else). It describes, exactly, what each product does today: what is
collected, how it is combined, what is published, and — critically — **what each instrument's
evidence base can and cannot justify publishing.**

---

## 0. The constraints any change has to respect

Four rules are load-bearing. A presentation change that breaks one of them is a claims-register
change, not a design change.

| # | Rule | Where it bites |
|---|------|----------------|
| 1 | **Scoring is frozen in v1.** Parity/E2E tests gate every deploy; no math refactors. | Changing a *scale of presentation* is possible without touching scoring. Changing a *formula* is not, in v1. |
| 2 | **Results are snapshotted with `algo_version` and never recomputed.** | Old reports keep their old numbers. Any new scale must be derivable at read time, or versioned. |
| 3 | **No banded scores before norms exist to justify them** (refusal #3, "an unjustifiable number"). | This is the whole percentile question. See §6. |
| 4 | **"Validated" applies only to Personality and EI.** | Presentation must not imply norm-referencing where there is none. |

**The short answer to the percentile question:** percentiles are norm-referenced statements about a
population. Exactly one instrument here has a population norm table — the Personality Mirror. See §6
for what each instrument could legitimately publish.

---

## 1. Personality Mirror — 130 items — *Established*

**Files:** `services/p150_lite.py`, `constants/p150_data.py`, `constants/p150_norms_snapshot.json`

### Collection
- 130 Likert items, 1–5 (Strongly disagree → Strongly agree).
- 120 personality items: **15 factors × 8 items each**.
- 10 social-desirability validity items (do not enter any factor score).
- Reverse-keyed items are listed in `P150_REVERSED_ITEMS`; inversion is `6 − answer`.

### Factor scoring (the actual measurement)
1. For each factor, sum its 8 items after reversal → **raw score, range 8–40**.
2. Convert raw → **sten 1–10** by table lookup in the frozen norms snapshot
   (`p150_norms_snapshot.json`, exported from the parent product's effective bands).
   Example, factor A (Warmth): raw 8–10 → sten 1; 11–12 → 2; 13–15 → 3; 16–18 → 4; 19–22 → 5;
   23–25 → 6; 26–… → 7+. **Bands are per-factor, not shared.**
3. Sten label: 1–2 Very Low, 3–4 Low, 5–6 Average, 7–8 High, 9–10 Very High.
4. Missing answer defaults to 3 (the scale midpoint).

### Global dimensions (derived, not measured)
Five second-order composites over the factor **stens**:

```
global = 5.5 + gain × Σ( weight × (factor_sten − 5.5) )     then clamped/rounded to 1–10
```

| Dimension | Equation (factor: weight) | Gain |
|---|---|---|
| Extraversion | A +0.3, F +0.4, H +0.4, N −0.3, Q2 −0.5 | 1.0 |
| Anxiety / Neuroticism | C −0.4, L +0.3, O +0.4, Q4 +0.4 | 1.0 |
| Receptivity | A +0.3, I +0.5, M +0.3, Q1 +0.4 | 1.0 |
| Independence | E +0.5, H +0.4, L +0.2, Q1 +0.3 | 1.0 |
| Self-Control | F −0.3, G +0.4, M −0.3, Q3 +0.4 | 1.0 |

All gains are **1.0** (uncalibrated). `GLOBAL_CALIBRATION._meta` records why: *"n=1 gains trialled,
not shipped (no population skew)."* Receptivity and Self-Control are flagged in-product as **known
residuals** against other 16PF-style instruments. Receptivity is the same axis other reports publish
as Tough-Mindedness, read from the opposite pole.

### Validity indices (published, never hidden)
- **Social desirability:** count of the 10 checks answered in the flattering direction (≥4, or ≤2 if
  reverse-keyed). NORMAL <4 · ELEVATED 4–6 · HIGH ≥7.
- **Central tendency:** % of all 130 answers at the midpoint. NORMAL <40 · ELEVATED 40–54 · HIGH ≥55.
- **Strengths** = factors with sten ≥8. **Blind spots** = factors with sten ≤3.

### What the evidence supports
Calibrated per-factor norm bands exist → this is the **only** instrument here where a
norm-referenced statement (percentile, population comparison) is defensible.

---

## 2. EI Mirror — 140 items — *Established*

**Files:** `routes/mirror_v2.py::_score_eq`, `constants/eimirror_data.py`

### Collection
140 Likert items, 1–5, across **4 domains → 14 sub-dimensions → 10 items each**. Roughly a third are
reverse-keyed (`EIMIRROR_REVERSE_ITEMS`, inversion `6 − answer`). All 140 are required; a missing
answer defaults to 3.

### Scoring
- **Sub-dimension score** = mean of its 10 reversed-corrected items → 1.00–5.00 (2 dp).
- **Domain score** = mean of all items in the domain (item-weighted, not a mean of sub-means).
- **Overall** = unweighted mean of the four domain scores.
- **Bands** (identical at all three levels): **High ≥ 4.0 · Moderate ≥ 3.0 · Developing < 3.0**.
- Strengths = top 3 sub-dimensions; growth areas = bottom 3.

### What the evidence supports
The bands are **published descriptive thresholds** — fixed cut-points on the raw 1–5 scale. There is
**no norm table**, so nothing here is norm-referenced. A percentile would be an invented number.

---

## 3. Essential Mirror — 50 items × 2 lenses — *Developmental* (produces the Delta)

**Files:** `services/essential_scoring.py`, `routes/mirror_v2.py::_score_essential`,
`constants/essential_data.json`

### Collection
The same 50 statements answered twice: once as **self**, once as the **ideal partner** (item ids are
namespaced `self:1…50` and `ideal:1…50`). Likert 1–5. All 100 required.

### Archetype scoring (per lens)
- 6 archetypes; each is keyed to **10 of the 50 items** (items are shared across archetypes).
- Answers map through a **non-linear point table**: `5→10, 4→7, 3→5, 2→2, 1→0`
  (reverse-keyed items invert first: `6 − answer`).
- Archetype raw = sum over its 10 items (max 100); **percentage = raw / max × 100**.
- **Primary** = highest raw; **secondary** = second highest. The primary+secondary pair keys the
  narrative from `compatibility_matrix`.

### Display dimensions (per lens)
Five fixed 10-item blocks — Values (1–10), Lifestyle (11–20), Conflict (21–30), Intellectual (31–40),
Emotional (41–50) — each scored as `sum / (10 × 5) × 100`, rounded to a whole number.
**Note the deliberate difference:** dimensions use the raw Likert sum; archetypes use the point table.

### The Delta (the headline measurement)
```
delta[archetype]  = ideal_percentage − self_percentage        (signed, 1 dp)
delta.overall     = mean( |delta[archetype]| ) over all 6     (1 dp)
delta.biggest     = archetype with the largest |delta|
dimension_gaps[d] = ideal_dimension[d] − self_dimension[d]
```
Sign convention: **positive = you want more of it than you are.**
**Shadow** = the primary archetype's declared `shadow` counterpart, with its warning text.

### What the evidence supports
Items and the archetype framework are ours. Early internal consistency only (archetype core:
exploratory, n≈90, α 0.68–0.74); no test–retest, **no population norms**. Percentages here are
**proportions of a maximum possible score**, not percentiles — a distinction worth protecting in any
redesign, because they look identical to a consumer.

---

## 4. Closeness Mirror (MI-AS-36) — 36 items + 1 check — *Developmental*

**Files:** `services/closeness_scoring.py`, `constants/closeness_bank_1_0_0.json`

### Collection
36 items on a **7-point** scale in a **fixed presentation order** (part of the instrument spec —
deliberately not randomised), plus one instructed-response validity item (`VAL-IR`). Keying is
balanced: 9 forward / 9 reverse per dimension. Reverse inversion is `8 − answer`.

### Scoring
- Two dimensions of 18 items each: **anxiety** (items 1–18, published as *Reassurance*) and
  **avoidance** (items 19–36, published as *Closeness/distance*).
- Dimension score = **mean of answered items**, 1 dp. Prorated for up to 2 missing;
  **≥3 missing → `status: not_scored`** and no value is published.
- 12 facets of 3 items each (A1–A6, V1–V6), scored as a mean, and **suppressed unless ≥2 answered**.

### Validity → confidence (nothing is deleted or silently corrected)
| Check | Trigger |
|---|---|
| Instructed response | answer ≠ the bank's expected value |
| Inconsistency | Σ absolute difference over 3 keyed pairs ≥ 9 |
| Long string | longest run of identical consecutive answers ≥ 7 |
| Time floor | mean response time < 4000 ms |

`confidence = high` (0 flags) · `moderate` (1) · `low` (≥2). Published on the result and in the PDF.

### What the evidence supports
**No norms exist**, which is exactly why the result is a point on two continuous axes with **no
bands, no quadrants, no types and no percentiles**. Pilot statistics (n = 300) are planned; when they
exist, computed values will be published with sample size and date.

---

## 5. Flag Check — 9 questions — **not an instrument**

**File:** `routes/mirror_v2.py::FLAG_ITEMS`, `complete_reflection`

8 situation questions, each with 4 options mapping to a category:
`1 → reprice · 2 → explain · 3 → late · 4 → none` (didn't happen / can't recall), plus one safety
question (`f-safety`: 1 no · 2 unsure · 3 yes).

```
informative = count(reprice) + count(explain) + count(late)
if informative < 3      → pattern = "insufficient"
else if top two tie     → pattern = "mixed" (+ the tied pair)
else                    → pattern = the modal category
```

**Output contains no score, no band, no grade, no risk label — permanently.** The safety answer
selects a referral block; it never contributes to the pattern. Any change that gives this a number
would turn a reflection into an audit of a relationship and inherit an evidence burden it cannot
carry.

---

## 6. The percentile question, instrument by instrument

A percentile is a claim about a population: *"you scored higher than N% of people."* It requires a
norm sample. Here is what each instrument can honestly support today.

| Instrument | Norms? | Percentile defensible? | What it could publish instead |
|---|---|---|---|
| **Personality Mirror** | Yes — per-factor sten bands | **Yes**, for the 15 factors | Percentile band, or "higher than about N% of people", derived from sten |
| Personality **globals** | Derived from normed factors | **Only as an approximation**, and it inherits the Receptivity/Self-Control residual | Better shown as position + the equation behind it |
| **EI Mirror** | No — fixed cut-points | **No** | The 1–5 score plus its published threshold (High/Moderate/Developing) |
| **Essential Mirror** | No | **No** | % of maximum (as now) and the Delta, clearly labelled as *not* percentiles |
| **Closeness Mirror** | No (n=300 pilot planned) | **No** | Position on the axis with the confidence label (as now) |
| **Flag Check** | n/a | **Never** | Nothing. It stays unscored. |

### If you want percentiles on the Personality Mirror
Stens are already normalised (mean 5.5, SD 2 by construction), so a sten → percentile mid-band
mapping is arithmetic, requires no new norm data, and can be derived **at read time** — meaning
snapshots stay immutable and old reports do not change:

| Sten | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Percentile at band midpoint | 1 | 4 | 11 | 23 | 40 | 60 | 77 | 89 | 96 | 99 |
| % of people in band | 2.3 | 4.4 | 9.2 | 15.0 | 19.1 | 19.1 | 15.0 | 9.2 | 4.4 | 2.3 |

> **Corrected June 2026.** The first issue of this document printed 27 at sten 4 and 73 at sten 7.
> Both were wrong. The row above is `100 × Φ((sten − 5.5) / 2)`, and `tests/test_display.py` now
> asserts the shipped table against the normal curve so it cannot drift again. Because these
> statements are derived at read time, the table is versioned (`disp-1.0.0`) and pinned per report:
> correcting it does not alter a report already delivered.

Three cautions worth deciding on deliberately:

1. **Precision inflation.** A sten band is wide; "77th percentile" sounds like a measurement to one
   person. "About 1 in 4 people sit further this way than you" carries the same information without
   the false precision. Recommend rounded fractions, never a decimal.
2. **Bidirectional factors.** Half these factors are not "more is better" (Vigilance, Privateness,
   Apprehension). A percentile invites a league-table reading of a trait that has costs at both
   poles. Any percentile presentation needs the two pole labels kept visibly attached.
3. **Comparability.** Dropping the sten entirely breaks comparison with every other 16PF-style
   report a user might hold — including the paired-sheet comparison that exposed the Self-Control
   residual. Recommend percentile as the headline, **sten retained as the underlying figure**.

### What a scale change does *not* fix
Presentation is not measurement. Changing to percentiles will not move the Receptivity/Self-Control
residual (that lives in the composite equations, §1), and will not create norms for the other three
instruments. Those need a calibration sample — for the composites, n ≥ 200 paired profiles; for
Closeness, the planned n = 300 pilot.

---

## 7. Where a redesign is free, and where it is not

**Free (presentation only, no scoring change, no register change):**

- Percentile display for Personality factors, derived at read time from the existing sten.
- Any graphic treatment: bell curve with position marked, pole-to-pole bars, radar for EI domains,
  the existing two-axis dot plot for Closeness.
- Wording of labels, ordering, emphasis, print layout.

**Not free (needs a deliberate decision, and in some cases a register update):**

- Percentiles or bands on EI, Essential or Closeness → breaches refusal #3 while unnormed.
- Any change to a formula, weight, norm band, point table or threshold in §§1–4 → breaks hard rule 1
  and the parity tests; needs a new `algo_version`, and old snapshots must keep their old numbers.
- Giving the Flag Check any number at all → breaks hard rule 5, permanently off the table.

**Recommendation if you want the consumer upgrade now:** percentile-led presentation on the
Personality Mirror only (sten retained underneath, poles kept attached, approximate language), richer
graphics across all four, and an explicit one-line note on the other three explaining why they show a
position rather than a percentile. That is honest, ships without touching scoring, and is the strongest
version of the "why can't I have a percentile here?" answer: because we don't have the norms yet, and
we'd rather say so.

---

## 8. Verification gates protecting all of the above

| Gate | What it locks |
|---|---|
| `tests/_e2e_test.py` | End-to-end scoring across all four instruments + Flag Check |
| `backend/tests/test_composites.py` | The five global equations, all gains at 1.0, a reference profile |
| `tests/test_locked_copy.py` | Locked claims copy (hash per string) + "validated" usage lint |
| `backend/tests/` (116 tests) | API behaviour, ownership, immutability, PDF content |

Every stored result carries `algo_version: rk-1.0.0`. Results are written once
(`$setOnInsert`) and never recomputed, so a future scoring change cannot rewrite history.

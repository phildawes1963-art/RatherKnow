# B3 · Norms provenance — findings, no changes made

Work order Batch B, item B3. Nothing in this file changed any code, data or output. It answers
the three questions and reports what was found instead.

Source examined: `backend/constants/p150_norms_snapshot.json`, `backend/constants/p150_data.py`,
`backend/services/p150_lite.py`, `backend/services/display.py`.

---

## 1. What respondent population the norms were derived from, and how many people

**There is no evidence of one, and the shape of the table argues against there being one.**

The snapshot's whole metadata is two fields:

```json
"exported_at": "2026-08-14T17:26:38.760153+00:00",
"source": "mymirrorreport backend effective bands (super-admin config over defaults)"
```

No n. No group. No norming date. No reference to a dataset. "Super-admin config over defaults"
describes an editable settings screen, not a sample.

Then the numbers themselves. Each factor maps raw 8–40 (33 possible points) onto stens 1–10.
The band widths, in raw points, for all fifteen factors:

| factor | sten 1 → 10 widths |
|---|---|
| A | 3, 2, 3, 3, 4, 3, **8**, 2, 3, 2 |
| C | 3, 2, 3, 3, 3, 4, 6, 4, 3, 2 |
| E | 3, 2, 3, 3, 3, 5, 5, 4, 2, 3 |
| F | 3, 2, 3, 3, 4, 4, 5, 3, 3, 3 |
| G | 3, 2, 3, 3, 4, 4, 4, 5, 2, 3 |
| H | 3, 2, 3, 4, 4, 4, 4, 4, 3, 2 |
| I | 3, 2, 3, 3, 5, 4, 4, 4, 2, 3 |
| L | 3, 2, 3, 4, 4, 4, 4, 4, 3, 2 |
| M | 3, 2, 3, 4, 3, 5, 5, 3, 2, 3 |
| N | 3, 2, 3, 3, 5, 3, 5, 4, 3, 2 |
| O | 3, 2, 3, 4, 4, 4, 3, 5, 3, 2 |
| Q1 | 3, 2, 3, 3, 3, 3, **7**, 4, 3, 2 |
| Q2 | 3, 2, 3, 4, 4, 3, 4, 4, 3, 3 |
| Q3 | 3, 2, 3, 4, 4, 4, 4, 4, 3, 2 |
| Q4 | 3, 2, 3, 3, 5, 4, 3, 4, 3, 3 |

Two things fall out of that table.

**Every factor shares the same lower boundaries.** Stens 1–4 are 3, 2, 3, 3 points wide on all
fifteen — raw ≤10, ≤12, ≤15, ≤18. Those are exactly the hardcoded cut-offs in the generic
`raw_to_sten()` in `p150_data.py:174`, which carries no provenance either. Fifteen factors
measured on fifteen different item sets do not produce identical tail boundaries from data. They
produce identical boundaries when one default table is applied to all of them.

**The widths are near-uniform, and a normed sten table is not.** A sten scale is a
standardised score: band 5 and band 6 each hold about 19% of people, band 1 and band 10 about
2.3% each. On any roughly normal raw distribution that makes the middle bands **narrow** in raw
points and the tails **wide**. Here the middle bands are as wide or wider than the tails, and
the widest band on Factor A is sten 7 at eight raw points. That is what an equal-interval split
of the 8–40 range looks like — a linear stretch of the possible score range, not a percentile
map of an observed one. The per-factor variation sits almost entirely in stens 5–8, which is the
signature of hand-tuning in the middle rather than of a distribution.

## 2. Whether that group is the My Mirror Report leadership-assessment population

**Cannot be confirmed, and on this evidence the question may not apply.** This repository holds
no MM respondent data and the snapshot names no group. But the concern behind the question is
narrower than the problem: a leadership-assessment norm would at least be *a* distribution, just
the wrong one. What is in the file does not appear to be a distribution at all.

## 3. What the snapshot's own provenance metadata records

Date of export, and one free-text sentence. No n, no group, no norming method, no version of the
defaults it was configured over, no record of which bands were edited away from those defaults
or by whom or when.

---

## What follows from this, stated and not acted on

**The affected claim is bigger than "unusually high".** `services/display.py` converts a sten to
a population statement — "About 1 in 9 people sit further toward Warm than you" — using
`STEN_PCT`, the normal CDF at each band midpoint. That is correct arithmetic on the assumption
that stens are normally distributed with mean 5.5 and SD 2, which is true of a sten scale that
was normed and is not established for this table. Every commonness sentence a reader sees, and
the `strengths` (sten ≥ 8) and `blind_spots` (sten ≤ 3) selection in `p150_lite.py`, inherit that
assumption.

`display.py` already refuses to make a population statement for composites and clamped values
because "a clipped composite can't carry one honestly". The same standard applied to the primary
factors is the open question here.

**This is upstream of measuring alpha**, exactly as the work order says. Measuring internal
consistency on our own respondents and then applying these bands would be measuring reliability
carefully and applying a scale of unknown origin to the result.

**Two things would resolve it, neither of which is a re-norm:**

1. Recover the provenance from the MM side — the defaults these bands were configured over, and
   whether any observed sample was ever behind them. If a sample exists, its n and group are
   answerable and the question becomes the one B3 asked.
2. If no sample was ever behind them, the honest options are to stop making population
   statements from these bands until one is, or to build one from RK respondents and publish its
   n and composition.

**No re-norming, no scoring change and no copy change has been made.** Reported and stopped, as
instructed.

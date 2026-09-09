# Reportable floors — what is large enough to say

**Added June 2026 · `disp-1.4.0` · no scoring change**

Every number in this document answers one question: how big does a difference have to be before
the reading is allowed to name it? Three floors existed only in the Personality Mirror. This
records where the others came from, and what they cost.

The rule for every provisional constant here: **set it so it is more conservative than the derived
value is likely to be.** A claim withdrawn later is worse than a claim never made.

---

## 1. Convergence needs displacement, not proximity

Two readings landing in the same place is not evidence when that place is the middle. The scale
midpoint is the modal outcome under uninformative responding — which is why a machine-generated
response set produced two agreements and zero tensions in the September sample report, and why the
document then called that convergence "the most reliable thing in this document". That superlative
is deleted permanently: it is a claim about the instrument, made inside a personal reading, and
uncheckable by the person holding it.

The gate, in `crosscheck.py`:

| both readings | direction | emitted |
|---|---|---|
| outside the middle third | same | **agreement** |
| outside the middle third | opposite | **tension** (if far enough apart) |
| one displaced, one at the middle | — | **single reading**, reported alone |
| both at the middle | — | **the null**, printed rather than hidden |

`DISPLACEMENT_FLOOR = 1/6` of the range — the middle third, equivalently |z| ≥ 0.5 for a normal
scale.

**Polarity is declared, never inferred.** The Closeness dimensions run against their pairs:
*distance from closeness* against *warmth*, *need for reassurance* against *emotional stability*.
A naive same-direction test on raw scores reads a genuine agreement as a disagreement. Every
reading in `_readings()` is oriented at source so a higher norm means more of the named construct,
and carries a `polarity` field recording how; `tests/test_crosscheck_gate.py` locks the
orientation, because if it ever flips, every same-direction test silently inverts.

The null state is printed: *"Neither instrument found a displacement to report here. They agree on
that, which is itself a reading — it means this is not where your selecting is happening."* The
scruple that produced *"we won't invent a disagreement to seem insightful"* now applies to
agreements too. The asymmetry was more damaging than either policy alone.

## 2. A cross-instrument claim inherits the weaker input

Both September agreements paired the Closeness Mirror (developmental, confidence **Low**) with the
Personality Mirror (established) and were presented with more authority than either input. Now the
lower tier and the lower confidence of the two are carried on the claim itself, at the point of the
claim, and stated in the body: *"a comparison inherits the weaker of the two instruments it is
built from, not the stronger."*

The same rule reaches the summary. A summary line sourced entirely from a Low-confidence
instrument reading mid-scale is not emitted at all — which removed the unsourceable claim that the
selection "runs on recognition rather than reassurance", assembled from two null readings.

## 3. The EI minimum reportable difference

`SEM = SD·√(1−α)`, and `MRD = 1.645·√(SEM₁² + SEM₂²)`.

α is not measured for this bank. Computing a floor from a placeholder and presenting it as a
derivation would be the same error as a norm without a reference sample, so the pessimistic end of
the plausible range is assumed instead: **α = 0.70**. A low α produces a *larger* floor, so the
assumption can only suppress claims that would otherwise be retracted.

The other input is real, with one caveat. The observed between-person SD of an EI domain score
across the quarantined-clean corpus is **0.294** (n = 560) — but that corpus is still
overwhelmingly machine-generated, and random answers under-disperse relative to people. Taking
0.294 would give MRD = 0.375 and name differences the derived floor will later suppress. So
`EI_DOMAIN_SD = 0.60`, the plausible SD for a domain mean among real respondents and the larger of
the two.

**`EI_DOMAIN_MRD = 0.765`** on the 1–5 scale. A highest or lowest is named only where it clears
that against **the domain next to it**, not against the mean: a score can beat the average of four
comfortably and still be indistinguishable from its neighbour.

On the September sample the four domains ran 3.40 / 3.20 / 3.17 / 3.04 — a total spread of 0.36.
Nothing is named, and the approved flat-profile copy fires instead.

**Sub-dimensions are not ranked at all.** Fourteen facets on a handful of items each: lower α,
larger floor, quite possibly larger than the whole usable spread. The September report printed a
"highest three" containing two values tied at 3.6 as an ordered list, and a "lowest three"
separated by 0.1 and 0.1. The numbers stay; the order between them is not information yet.

## 4. The social-desirability cut moves above chance

"Agreed" here is a Likert threshold — 4 or 5 on a 1–5 scale, 1 or 2 reversed — so under
content-blind responding p = 0.4, giving a null of **mean 4.0, SD 1.55** on ten items. The old cut
flagged **4 of 10 as elevated**, which is the null itself: it flagged chance.

New cuts: **ELEVATED at 7** (≈ +1.9 SD), **HIGH at 9** (≈ +3.2 SD). Derived from the theoretical
null, not from a percentile of our own distribution — norming a validity index to your own corpus
fixes the flag rate by construction, forever.

The corpus then checks the cut rather than generating it. Across 446 clean stored profiles the
counts run `{5: 252, 4: 62, 3: 48, 2: 39, 6: 27, 7: 8, 1: 6, 8: 2, 9: 1, 0: 1}`, so 7+ catches 11
of 446. **n = 446 is provisional twice over**: the corpus was 60.7% degenerate before quarantine,
and what remains is still mostly synthetic.

## 5. Speeding is per item, from the item

A mean is the wrong statistic: it is pulled up by a few slow items and passes a respondent who
raced through the rest. The September report published *"a time floor (mean 1600 ms per item)"*,
which judged nothing.

Each item now carries its own floor at **300 ms per word** of its text (the common heuristic in
careless-responding work), with a **1,200 ms** minimum because even a three-word item needs the
scale read once. The statistic is the **proportion of items answered below their own floor**, and
the flag fires at 30%. Banks are fixed, so the floors precompute once.

**Not yet validated against real timing.** Every stored timing in the corpus is synthetic and
constant, so 300 ms/word cannot be checked here. It is derived from the item rather than from a
single number applied to items of wildly different lengths, which is the part that was wrong
before; the constant itself waits on real respondents.

## 6. The consistency index is labelled

`ζ = 1 − 24·triads/336`, so **1 means no circular preferences at all** and below about 0.70 is
where the ranking softens. The September report printed `0.286` with no direction, no range and no
expected rate, which reads as an accusation. The reader is now told the direction, the range, how
many of their triples ran in a circle, and that a couple in twenty-one forced choices is ordinary.

The left-hand option rate is out of the reader-facing list. 9 of 21 under randomised presentation
is unremarkable, and a number with no threshold beside it is not a check. It is still computed and
still flags at 80/20.

## 7. Elevation, and what is queued for the next scoring version

Five of six archetype gaps ran in the same direction in the September sample, and all five
dimension gaps were non-negative. That is a level shift — describing an ideal partner as better on
everything at once — not a profile difference. Mean signed gap **+10.17** against a reported mean
absolute gap of **10.8**: the headline was mostly the elevation.

**Shipped now, at display layer:** elevation is reported as its own quantity, with a line saying
so when it dominates. Additive — it makes no existing claim untrue, so it costs no comparability.

**Queued for `rk-1.1.0`, not shipped:** replacing the table with centred (ipsatised) gaps. That
changes "widest single gap" from The Rock to The Empath and flips The Diplomat's sign — a different
answer from the same data. `centred_per_archetype` and `centred_biggest` are computed and carried
in the payload so the change can be evidenced before it is published, and nothing reader-facing
reads them yet.

An ALGO bump costs retake comparability, which is part of what this product is for, so the next one
carries everything queued for scoring at once: centring, the 50-item archetype reallocation (the
`visionary` overlap now has a measured correlate at r = +0.56), and anything the tie state's live
behaviour turns up.

---

## What this cost

Claims the reader used to get and no longer does: two agreements that were two mid-scale numbers,
a strongest and weakest EI domain, three highest and three lowest facets, a driver for the
selection sourced from two nulls, and a "most reliable thing in this document". Everything on that
list was an ordering of noise or a superlative about the instrument. What replaced them — the
nulls, the single readings, the floor quoted beside the suppression — is shorter and true.

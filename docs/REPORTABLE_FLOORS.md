# Reportable floors — what is large enough to say

**Added June 2026 · `disp-1.4.0` · updated `disp-1.5.1` · no scoring change**

Every number in this document answers one question: how big does a difference have to be before
the reading is allowed to name it? Three floors existed only in the Personality Mirror. This
records where the others came from, and what they cost.

The rule for every provisional constant here: **set it so it is more conservative than the derived
value is likely to be.** A claim withdrawn later is worse than a claim never made.

## 0. Two rules that apply to everything below

**Derive, then round up. Never down.** Rounding a provisional floor down loosens a threshold that
is already resting on an assumption; rounding up costs only claims that could not have been
defended anyway. So the EI domain floor derives at 0.765 and ships at **0.8**, and the Personality
factor floor derives at 19.109 points of scale and ships at **20**. Both floors in the same
combined report are now rounded by the same logic, which is the other half of the reason: a reader
comparing two sections should not be reading two different roundings.

**No constant here is derived from the stored corpus.** §4 explains why it cannot be. Where a
figure below is an assumption, it says so, and it says what would make it a measurement.

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

The other input is an assumption too, and this is the correction to the first version of this
section. It said the SD was "real, with one caveat": the observed between-person SD across the
"quarantined-clean" corpus was 0.294. That figure is not usable — see §4 — and taking it would
have set a floor of 0.375 and named differences the derived floor will later suppress. So
`EI_DOMAIN_SD = 0.60`, **an assumed** plausible SD for a domain mean among real respondents, and
the larger of the two.

Derived: 0.765. Shipped: **`EI_DOMAIN_MRD = 0.8`** on the 1–5 scale, rounded up per §0. A highest
or lowest is named only where it clears that against **the domain next to it**, not against the
mean: a score can beat the average of four comfortably and still be indistinguishable from its
neighbour.

**Non-provisional when:** α is measured on this bank and the between-person SD comes from real
respondents. Both then replace the assumptions and the floor is re-derived, in either direction.

### 3a. The suppressed branch shows its working

On the September sample the four domains ran 3.40 / 3.20 / 3.17 / 3.04 — a total spread of 0.36,
and nothing is named. The first version of this fix stopped at the sentences: the four figures
were still printed, to two decimals, in descending order. **That is the ranking, restored
visually.** Four numbers in order rank themselves whatever the prose above them says, and rounding
each to the nearest half point does not help — 3.5 printed against 3.0 is exactly the distinction
the floor just refused to make, and alphabetical order does not stop anyone re-sorting four
numbers in their head.

So the suppressed branch prints **one shared band** — *"All four domains fall between 3.0 and 3.5
on the 1–5 scale"* — followed by the two numbers that let a reader audit the suppression: the
**observed spread** (0.36) and the **floor** (0.8). The domains keep their names and their
descriptions. The overall mean stays: it is one figure about the reader's own answers and ranks
nothing.

Where the domains *do* separate, the figures and the bars come back and the highest or lowest is
named. Two branches, one condition, and the presentation follows the branch rather than
contradicting it.

**Sub-dimensions are named and not scored at all.** "Numeric but unranked" was self-defeating:
fourteen numbers on a page are a ranking however they are ordered, and facet scales are *shorter*
than the domain scales whose floor those figures have already failed — lower α, larger floor. The
fourteen names stay so the reader knows what was measured. The figures return when α is measured.

## 4. The social-desirability cut moves above chance — and the corpus does not check it

"Agreed" here is a Likert threshold — 4 or 5 on a 1–5 scale, 1 or 2 reversed — so under
content-blind responding p = 0.4, giving a null of **mean 4.0, SD 1.55** on ten items. The old cut
flagged **4 of 10 as elevated**, which is the null itself: it flagged chance.

New cuts: **ELEVATED at 7** (≈ +1.9 SD), **HIGH at 9** (≈ +3.2 SD). Derived from the theoretical
null, not from a percentile of our own distribution — norming a validity index to your own corpus
fixes the flag rate by construction, forever.

**The previous version of this section then said "the corpus checks the cut". It does not, and
that sentence was wrong.** Three things, in the order they were found:

1. **Low variation.** 1,587 of 5,206 stored results come from sessions answering on fewer than
   four distinct points. Flagged `data_quality: "low_variation"` and excluded by default in
   `scripts/analyze_stored_corpus.py`.
2. **A collapsed distribution.** Of the personality profiles, **616 of 891 sit at exactly five
   agreements** — `{5: 616, 4: 91, 3: 65, 2: 45, 6: 39, 1: 12, 7: 11, 0: 8, 8: 3, 9: 1}`. No
   binomial produces that. Excluding the fixed-count records leaves **n = 232**, of which 5 reach
   7+ — **2.16% against the 5.48% the null expects**. So the remainder does not reconcile with the
   null either, and the hope that it would is closed.
3. **The reason, found by `scripts/patterned_provenance.py`.** The answers are *replayed*. Only
   1,787 distinct answer vectors exist across 5,454 answered sessions, and **3,717 of those
   sessions share their exact answer sequence with another session**; one closeness vector appears
   **653 times**. The account names on them are `E2E User`, `Pytest User`, `Reset User`, `Iter6`,
   all `@ratherknow.com`, across ten days.

**So the provenance question has an answer: it is our own test suite.** Not an undocumented
seeding script, and not automated traffic from outside. That is a data-integrity finding rather
than housekeeping, because it touches *every count this product will ever quote from `results`*.
Recorded here, and the obligation it creates — test runs must not write into the collection the
corpus is counted from — is on the backlog rather than fixed in this pass.

**The corpus n, as a sequence rather than a current figure:** 5,206 results → 3,619 after the
low-variation flag → 891 personality profiles → 275 once the fixed-count class is set aside → and
of those, essentially all still carry a `duplicate_sequence` flag. The shape of the loss is the
point: there is no clean remainder large enough to calibrate anything, at any stage.

**Non-provisional when:** there are real respondents. The cut is theoretical and stays
theoretical; `reportable.SD_CORPUS_STATUS` says so in the code.

### 4a. Three flags, tagged separately, nothing excluded

`pattern_flags` on the result document, alongside `data_quality`:

| flag | what it means | count |
|---|---|---|
| `sd_fixed_agreement` | agreement count sits on the spike value (5) | 616 |
| `cyclic_sequence` | the answer sequence repeats a cycle of ≤ 8 | 334 (all period 1) |
| `duplicate_sequence` | the exact answer sequence appears in another session | 3,636 |

Three flags rather than one merged "patterned" class, because the overlap is the evidence: a
strict subset would mean one generator, disjoint classes would mean two sources. They overlap
partially (331 carry both A and B), and the third — which was not predicted, and is the one that
identified the source — subsumes most of both. Nothing is excluded on these flags: no threshold is
derived from this corpus any more, so exclusion buys nothing this week and would destroy the
provenance information permanently.

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

## 8. The sten stops reaching a reader (`disp-1.5.0`)

A sten is a norm-referenced claim by construction: mean 5.5, SD 2, against a reference population.
This product has paused every population claim for want of a documented reference sample, and was
still printing `6 (1–10 sten)` on the Personality result — the same claim in a different costume,
two sections after the sentence explaining why no band is shown.

Inspecting the band table made it worse than a mismatch. `p150_norms_snapshot.json` records its
whole provenance as `source: "mymirrorreport backend effective bands (super-admin config over
defaults)"` — no n, no group, no date — and the bands are **not internally coherent**. On Factor A,
across raw 8–40, the ten band widths run **3, 2, 3, 3, 4, 3, 8, 2, 3, 2**: sten 7 alone spans 8
raw points, a quarter of the entire raw range. Factor C carries a width-6 band, E a width-5. The
observed distribution follows the band widths, which is what you would expect if the widths were
hand-set rather than mapped from percentiles.

So the sten is retired from the reader-facing layer rather than recalibrated. Recalibration is a
scoring change and needs a reference sample; retirement needs neither and costs nothing true.

**What the reader sees instead:** each factor as a **percent of its own usable range** (0 = every
item at the low end, 100 = every item at the high end), described as a position between two named
poles and as a distance from **their own profile average**.

**The floor for naming a factor is absolute.** A floor set as a fraction of the reader's own
profile SD was rejected: standardise fifteen factors by their own spread and the largest always
lands near +1.8, for everybody, including the even profile that should name nothing. So the SD
comes from the scale — **15 points of a 100-point range** — giving `SEM = 15·√0.30 = 8.22` and
`MRD = 1.645·√2·8.22 = 19.11`, shipped rounded up at **20 points of scale**.

*Why 15 and not range/6.* The standard normal-range assumption is range ≈ 6 SD, i.e. 16.67 points,
which derives 21.2 and would ship at 22. Both are defensible and **15 is the more permissive of
the two**. It is kept because it is the same assumption the EI domain floor already uses — 0.60 of
a four-point span *is* 15% of range — and one shared assumption across the two instruments in a
combined report is worth more than a slightly stricter floor on one of them. It is an assumption,
not a measurement, and it is deliberately not taken from the stored corpus (§4).

**A flat profile names nothing, and says so.** No fallback to "the highest one anyway": that is
the always-fires defect in its purest form, and the copy for the empty state already exists
(`position.loudest_none`). An empty section is the finding.

**Stens are still scored, still stored, and marked not-for-display.** They are the raw material
for rebuilding the band table, and removing them from scoring would be a scoring change. The
payload carries `not_for_display` naming the field and the reason — because the way the sten
reached a reader in the first place was sitting in the payload with nothing marking it.

**One documented exemption**, on both the result page and the PDF: the five global dimensions are
computed *in* sten units (`5.5 + Σ(weight × (sten − 5.5))`), so the published equation cannot be
checked without them. It appears inside the collapsed "How this number is built" panel, labelled
as an audit of our own arithmetic and not a comparison with anyone.

**Also gone, same reason:** five hand-written cross-instrument findings fired on absolute
`sten ≥ 7` / `≤ 4`. They now use the same absolute 20-point distance from the reader's own profile
average, and their copy says "well above your own profile average" rather than "reads you as
emotionally stable across life in general".

**Non-provisional when:** α and a real between-person SD are measured on this bank.

## 9. Which test each side of a cross-check passed

The two sides of a construct pair do not pass the same test, and the copy no longer sounds as if
they do. The Closeness side clears an **absolute position** rule — outside the middle third of its
own 1–7 scale. The Personality side clears an **absolute distance from the reader's own profile
average** — 20 points of that factor's scale. Both are absolute; they are absolute about different
things. Every agreement and every tension now names both tests in its body, and a single displaced
reading names the one test it passed. The asymmetry is smaller than it was, and it is stated
rather than smoothed over.

---

## What this cost

Claims the reader used to get and no longer does: two agreements that were two mid-scale numbers,
a strongest and weakest EI domain, three highest and three lowest facets, a driver for the
selection sourced from two nulls, a "most reliable thing in this document", every sten, the four
EI domain figures where none of them separates, and fourteen facet figures. Everything on that
list was an ordering of noise, a superlative about the instrument, or a comparison with a
population we cannot describe. What replaced them — the nulls, the single readings, the shared
band, the floor quoted beside the suppression — is shorter and true.

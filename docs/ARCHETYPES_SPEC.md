# Essential Mirror — Archetype Specification

**INTERNAL. Not published, not linked, not in `frontend/public/`.**

Derived from `backend/services/essential_scoring.py` and
`backend/constants/essential_data.json` as shipped, June 2026. The reader-facing companion is
`docs/ARCHETYPES_GUIDE.md`, which deliberately omits sections 4–7 of this document.

Nothing in this document changed any score. It records what the code does, including three
defects found while writing it.

---

## 1. Structure

| | |
|---|---|
| Archetypes | 6 |
| Items per lens | 50 |
| Lenses | 2 — `self_assessment`, `ideal_partner` |
| Items scored per archetype | 10 |
| Response scale | 1–5 Likert |
| Output per archetype | raw score, and percentage of that archetype's own maximum |
| Primary / secondary | highest and second-highest percentage within a lens |
| Evidence tier | developmental |

Key-to-name mapping is not one-to-one with the display names, which matters when reading logs:

| Internal key | Display name | Subtitle | Public slug |
|---|---|---|---|
| `rock` | The Rock | Stability & Tradition | `the-rock` |
| `challenger` | The Challenger | Intellect & Growth | `the-challenger` |
| `empath` | The Empath | Connection & Intimacy | `the-empath` |
| `adventurer` | **The Voyager** | Social & Lifestyle | `the-voyager` |
| `diplomat` | The Diplomat | Harmony & Communication | `the-diplomat` |
| `visionary` | **The Torchbearer** | Purpose & Ambition | `the-torchbearer` |

---

## 2. Item allocation as shipped

| Archetype | Items | Reverse-scored |
|---|---|---|
| `rock` | 3, 4, 6, 12, 13, 15, 29, 45, 47, 49 | — |
| `challenger` | 1, 10, 24, 31, 32, 33, 35, 39, 40, 50 | — |
| `empath` | 8, 21, 27, 28, 41, 42, 43, 44, 46, 48 | 48 |
| `adventurer` | 2, 5, 9, 11, 14, 16, 17, 18, 19, 20 | 11, 16, 20 |
| `diplomat` | 17, 22, 23, 25, 26, 27, 28, 29, 30, 38 | 24 *(inert — see §6)* |
| `visionary` | 1, 2, 5, 9, 10, 33, 35, 37, 40, 44 | — |

Reverse scoring is `6 − raw`, applied within the archetype whose key lists the item.

Per-archetype maximum is `10 × 5 = 50`; the percentage is `round(100 × raw / 50)`.

---

## 3. Shadow and counter-type map

| Archetype | Shadow | Counter-type |
|---|---|---|
| `rock` | `empath` | The Free Spirit |
| `challenger` | `diplomat` | The Harmonizer |
| `empath` | `challenger` | The Stoic |
| `adventurer` | `rock` | The Homebody |
| `diplomat` | `visionary` | The Provocateur |
| `visionary` | `rock` | The Drifter |

Properties of the map, which are asymmetric by design or by accident — undetermined:

- `empath` ↔ `challenger` is the only **mutual** pull.
- `rock` is the shadow of **two** archetypes (`adventurer`, `visionary`).
- `adventurer` is **nobody's** shadow. No reader is ever told the Voyager is their shadow pull.

The third point is worth a decision. If the map is meant to be a complete function over the set,
one archetype being unreachable is a gap; if it is meant to be an editorial judgement per
archetype, it is fine and should be recorded as intentional.

---

## 4. DEFECT — item overlap between archetypes

Six archetypes × 10 items = **60 scoring slots drawn from a 50-item lens**. Thirteen items are
therefore counted toward two archetypes each. The archetype scores are not independent, and no
part of the shipped output says so.

**Pairwise overlap:**

| Pair | Shared items | Items |
|---|---|---|
| `challenger` × `visionary` | **5** | 1, 10, 33, 35, 40 |
| `adventurer` × `visionary` | **3** | 2, 5, 9 |
| `empath` × `diplomat` | 2 | 27, 28 |
| `rock` × `diplomat` | 1 | 29 |
| `adventurer` × `diplomat` | 1 | 17 |
| `empath` × `visionary` | 1 | 44 |

**The Torchbearer is the serious case.** Eight of its ten items are shared — five with the
Challenger and three with the Voyager. Only items 37 and 44 sit outside that, and 44 is shared
with the Empath. In practice `visionary` is very largely a linear combination of `challenger` and
`adventurer`, so:

- a reader who scores high on Challenger is *mechanically* pushed up on Torchbearer;
- "primary: Torchbearer, secondary: Challenger" is a near-guaranteed pairing rather than a finding;
- the Delta on Torchbearer partly restates the Delta on Challenger.

**The Diplomat is the second case.** Four of its ten items are shared, across three other
archetypes.

**Consequences to hold in mind:**

1. Any claim that the six archetypes are distinct patterns is not currently supported by the item
   allocation.
2. Primary-archetype assignment can be driven by shared items rather than by distinguishing ones.
3. This interacts with the MRD work: gating differences between correlated archetype scores is a
   different and harder problem than gating differences between independent ones.

**Deliberately not fixed.** Re-allocating items changes scores, which is a frozen-scoring
decision. Under the immutability rule, any re-allocation ships as a new scoring version and every
existing report keeps its original numbers. Decision deferred; overlap documented internally only,
per instruction.

---

## 5. DEFECT — three items score nothing

Items **7, 34 and 36** appear in no archetype's item list. A reader answers them twice, once per
lens, and they contribute to no archetype score.

They are not necessarily wasted: `calculate_dimension_scores` computes five display dimensions
over its own item groupings, and these items may fall there. But as far as the six archetypes are
concerned, six of a reader's hundred answers do nothing.

Either they should be allocated, or they should be identified as dimension-only items so it is
clear the omission is intentional.

---

## 6. DEFECT — the Diplomat's reverse key is inert

`diplomat.reverse = [24]`, but item 24 is not in `diplomat.questions`. Reverse scoring is applied
only to items within the archetype's own list, so this entry never fires.

Item 24 *is* in `challenger.questions`, where `reverse` is empty. So one of two things is true and
we do not currently know which:

- item 24 was intended to be reverse-scored for the Challenger and the entry landed on the wrong
  archetype; or
- item 24 was intended to be a Diplomat item and was never added to the list.

Both readings imply the shipped Challenger score is missing an intended reversal. **No fix
applied** — it would change scores. Recorded for the same versioned decision as §4.

A guard is cheap and worth adding regardless of the outcome: assert at import that every entry in
`reverse` appears in the same archetype's `questions`, so this class of defect cannot ship again.

---

## 7. Naming risk — the `compatibility` field

`get_compatibility_result()` returns a **blend narrative for the top two archetypes within a single
lens**. It contains no number, no second person, and no comparison between people, so it does not
breach the permanent no-compatibility-score refusal.

But the field is named `compatibility` in the API response, in the stored result, and in the PDF
builder, and the lookup table is `_COMPATIBILITY`. Anyone reading the payload — a partner, a
practitioner, a journalist, a future engineer — will reasonably read that as the thing we have
said we will never produce.

Recommend renaming to `blend`, carrying the old field in parallel for existing snapshots. Raised
with the user; no instruction received; **not changed.**

---

## 8. Open questions

1. Re-allocate the 50 items for archetype independence? Requires a scoring version bump, parity
   tests, and old reports keeping their numbers. (§4)
2. Allocate items 7, 34, 36, or declare them dimension-only? (§5)
3. Resolve item 24's intended reversal. (§6)
4. Rename the `compatibility` field. (§7)
5. Is the shadow map meant to be complete? `adventurer` is currently unreachable as a shadow. (§3)
6. Should the reader-facing guide disclose the overlap? Currently **no**, by instruction, pending
   the decision in §4. If the overlap is not fixed, this should be revisited — the evidence-tier
   disclosures set a standard that this omission sits awkwardly against.

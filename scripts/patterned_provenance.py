"""Three independent pattern flags on the stored corpus, and what wrote the records.

FLAGS, NOT ONE, AND NO EXCLUSION.

The social-desirability distribution collapsed onto a single value: 616 of 891 personality
profiles at exactly five agreements, which no binomial produces. That is one signature. A response
sequence that repeats a short cycle is another. They are tagged separately and both classes stay
in place, because the overlap between them is the evidence: if the cyclic records are a strict
subset of the fixed-count records that is one generator, and if they are disjoint that is two
sources. Merging them into a single "patterned" class destroys exactly the information the
provenance question needs — and since nothing derives a threshold from this corpus any more,
excluding the records buys nothing and costs that permanently.

THE THIRD FLAG WAS NOT PREDICTED, AND IT IS THE ONE THAT ANSWERS THE QUESTION. The cyclic test
found period 1 and nothing else — i.e. uniform answering, which the low-variation flag already
catches. What actually produced the spike is DUPLICATE RESPONSE VECTORS: a handful of fixed answer
arrays, replayed. One closeness vector appears 653 times. 3,717 of 5,454 answered sessions share
their exact answer sequence with at least one other session. That is a fixture, not a person, and
the account names on them (E2E User, Pytest User, Reset User, Iter6, all @ratherknow.com) say
whose fixture: our own test suite, writing into the same collections the corpus is counted from.

Written to `pattern_flags` on the result document, alongside the existing `data_quality`
low-variation flag, which this does not touch.

Usage: python3 scripts/patterned_provenance.py [--write-flags]
"""
import asyncio
import hashlib
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from dotenv import load_dotenv

load_dotenv(os.path.join(ROOT, "backend", ".env"))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

# The spike. Defined by the value the distribution collapsed onto, which means the class
# necessarily contains any genuine fives as well — which is why it is a flag and not a deletion.
SD_SPIKE = 5
MAX_CYCLE = 8
MIN_REPEATS = 3


def cycle_period(values: list) -> int | None:
    """The shortest period <= MAX_CYCLE that the whole sequence repeats, or None.

    A person does not answer 120 items in a repeating four-beat. A generator does.
    """
    n = len(values)
    if n < MAX_CYCLE * MIN_REPEATS:
        return None
    for p in range(1, MAX_CYCLE + 1):
        if n // p < MIN_REPEATS:
            continue
        if all(values[i] == values[i % p] for i in range(n)):
            return p
    return None


async def main(write_flags: bool):
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]

    sessions = {}
    vectors = Counter()
    async for s in db.mirror_v2_sessions.find(
            {}, {"id": 1, "instrument": 1, "responses": 1, "started_at": 1, "user_id": 1}):
        resp = s.get("responses") or {}
        ordered = [resp[k]["v"] for k in sorted(resp, key=lambda x: (len(x), x))
                   if isinstance(resp[k], dict) and "v" in resp[k]]
        digest = (s.get("instrument"),
                  hashlib.sha1(str(ordered).encode()).hexdigest()) if len(ordered) >= 20 else None
        if digest:
            vectors[digest] += 1
        sessions[s["id"]] = {"values": ordered, "started_at": s.get("started_at"),
                             "user_id": s.get("user_id"), "digest": digest}

    fixed, cyclic, both, neither = [], [], [], []
    periods = Counter()
    sd_counts = Counter()

    async for doc in db.results.find({"instrument": "personality"},
                                     {"session_id": 1, "result": 1, "data_quality": 1}):
        sd = ((doc.get("result") or {}).get("validity") or {}).get("social_desirability") or {}
        count = sd.get("agree_count")
        sess = sessions.get(doc.get("session_id")) or {}
        period = cycle_period(sess.get("values") or [])
        if count is not None:
            sd_counts[count] += 1
        is_fixed = count == SD_SPIKE
        is_cyclic = period is not None
        if period:
            periods[period] += 1
        target = (both if is_fixed and is_cyclic else
                  fixed if is_fixed else cyclic if is_cyclic else neither)
        target.append((doc["_id"], doc.get("session_id"), sess.get("started_at"),
                       sess.get("user_id")))

    n = len(fixed) + len(cyclic) + len(both) + len(neither)
    print(f"personality results inspected: {n}")
    print(f"social-desirability counts: {dict(sorted(sd_counts.items()))}")
    print(f"flag A · fixed agreement count == {SD_SPIKE}: {len(fixed) + len(both)}")
    print(f"flag B · cyclic response sequence:            {len(cyclic) + len(both)}")
    print(f"both flags: {len(both)} · A only: {len(fixed)} · B only: {len(cyclic)} · "
          f"neither: {len(neither)}")
    print(f"cycle periods observed: {dict(sorted(periods.items()))}")
    if both and not cyclic:
        print("→ every cyclic record is also a fixed-count record: consistent with ONE generator")
    elif cyclic and not both:
        print("→ the two classes are disjoint: consistent with TWO sources")
    else:
        print("→ the classes overlap partially: at least two behaviours, sharing one signature")

    # ---- flag C, across every instrument: the same answer sequence, replayed
    dup_digests = {d for d, c in vectors.items() if c > 1}
    dup_ids, dup_by_instrument = [], Counter()
    async for doc in db.results.find({}, {"session_id": 1, "instrument": 1}):
        sess = sessions.get(doc.get("session_id")) or {}
        if sess.get("digest") in dup_digests:
            dup_ids.append(doc["_id"])
            dup_by_instrument[doc.get("instrument")] += 1
    answered = sum(vectors.values())
    print(f"\nflag C · duplicate response vector: {len(dup_ids)} results")
    print(f"  answered sessions {answered} · distinct vectors {len(vectors)} · "
          f"sessions sharing a vector {sum(c for c in vectors.values() if c > 1)}")
    print(f"  most-replayed vector appears {max(vectors.values())} times")
    print("  by instrument:", dict(dup_by_instrument))

    # ---- provenance
    print("\nprovenance of the flagged records")
    flagged = fixed + cyclic + both
    days = Counter(str(st)[:10] for _, _, st, _ in flagged if st)
    print("  creation days (top 8):", dict(sorted(days.items(), key=lambda kv: -kv[1])[:8]))
    print("  distinct days:", len(days))
    with_user = [u for _, _, _, u in flagged if u]
    print(f"  sessions carrying a user_id: {len(with_user)} of {len(flagged)}")
    user_ids = {u for u in with_user}
    domains = Counter()
    names = Counter()
    if user_ids:
        from bson import ObjectId
        oids = [ObjectId(u) if not isinstance(u, ObjectId) else u for u in user_ids]
        async for u in db.users.find({"_id": {"$in": oids}}, {"email": 1, "name": 1, "created_at": 1}):
            domains[(u.get("email") or "@?").split("@")[-1]] += 1
            names[u.get("name") or "?"] += 1
    print("  email domains:", dict(domains.most_common(8)))
    print("  account names (top 5):", dict(names.most_common(5)))

    if write_flags:
        for label, group in (("sd_fixed_agreement", fixed), ("cyclic_sequence", cyclic)):
            ids = [i for i, *_ in group]
            if ids:
                res = await db.results.update_many(
                    {"_id": {"$in": ids}}, {"$addToSet": {"pattern_flags": label}})
                print(f"flagged {res.modified_count} results pattern_flags += {label}")
        ids = [i for i, *_ in both]
        if ids:
            res = await db.results.update_many(
                {"_id": {"$in": ids}},
                {"$addToSet": {"pattern_flags": {"$each": ["sd_fixed_agreement",
                                                           "cyclic_sequence"]}}})
            print(f"flagged {res.modified_count} results with both")
        if dup_ids:
            res = await db.results.update_many(
                {"_id": {"$in": dup_ids}},
                {"$addToSet": {"pattern_flags": "duplicate_sequence"}})
            print(f"flagged {res.modified_count} results pattern_flags += duplicate_sequence")
    else:
        print("\n(read-only; pass --write-flags to tag the documents)")


if __name__ == "__main__":
    asyncio.run(main("--write-flags" in sys.argv))

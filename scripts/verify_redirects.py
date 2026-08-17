"""Cutover gate: verifies every legacy path 301s to the right place, in production.

    python3 scripts/verify_redirects.py --from https://mymirrorreport.com
    python3 scripts/verify_redirects.py --from https://mymirrorreport.com --strict

Rules enforced (HANDOFF hard rule 3):
  * status must be exactly 301 (not 302, not a JS hop)
  * single hop — the first response must already point at the final target
  * Location must match redirect_map.json, including the ratherknow.com base

Exit code 0 = safe to remove /mirror from the parent. Anything else = do NOT remove it.
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "docs", "redirect_map.json"), encoding="utf-8") as fh:
    MAP = json.load(fh)

SAMPLE_SLUGS = {
    "/mirror/learn/": "the-interference",
    "/mirror/take/": "essential",
    "/mirror-index/learn/": "dont-waste-the-breakup",
    "/mirror-index/archetypes/": "the-rock",
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def head(url):
    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "ratherknow-cutover-check"})
    try:
        with opener.open(req, timeout=15) as resp:
            return resp.status, resp.headers.get("Location")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location")
    except Exception as e:  # network/DNS
        return None, str(e)


def expectations():
    for src, dst in MAP["exact"].items():
        yield src, MAP["base"] + dst
    for rule in MAP["prefix"]:
        slug = SAMPLE_SLUGS.get(rule["from"], "sample")
        src = rule["from"] + slug
        dst = MAP["base"] + (rule["to"] + slug if rule.get("keep_rest") else rule["to"])
        yield src, dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="origin", required=True, help="e.g. https://mymirrorreport.com")
    ap.add_argument("--strict", action="store_true", help="also require the target itself to return 200")
    args = ap.parse_args()

    failures = []
    checked = 0
    for src, expected in expectations():
        status, location = head(args.origin.rstrip("/") + src)
        checked += 1
        if status != 301:
            failures.append(f"{src} → status {status} (expected 301, got Location={location})")
            continue
        if (location or "").rstrip("/") != expected.rstrip("/"):
            failures.append(f"{src} → {location} (expected {expected})")
            continue
        if args.strict:
            tstatus, _ = head(expected)
            if tstatus != 200:
                failures.append(f"target {expected} returned {tstatus}, not 200")

    print(f"checked {checked} legacy paths against {args.origin}")
    if failures:
        print(f"\nFAILED — {len(failures)} problem(s). DO NOT remove /mirror from the parent site:")
        for f in failures:
            print(f"  ✗ {f}")
        sys.exit(1)
    print("\nALL REDIRECTS OK — 301, single hop, correct target. Safe to remove /mirror from the parent.")


if __name__ == "__main__":
    main()

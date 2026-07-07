#!/usr/bin/env python3
"""idiolect bench — scanner separation smoke test.

Runs `idiolect.py scan` over the fixture corpus (bench/fixtures/slop/*.txt are
archetypal AI-generated promo texts; bench/fixtures/human/*.txt are authored,
textured, human-register posts) and asserts separation:

  1. every LOUD slop fixture scores in the slop band (>= 41)
  2. fixtures named *-subtle.* need only clear the suspect band (>= 20) —
     they are the documented floor of ANY deterministic scanner (polite
     astroturf carries few lexical tells; its tells are semantic: no stakes,
     symmetric enthusiasm, testimonial arc). Catching those is the blind
     auditor agent's jurisdiction, and pretending regex does it would be
     the same lie the detector SaaS industry sells.
  3. every human fixture scores clean (<= 15)
  4. margin: min(loud slop) - max(human) >= 20; subtle >= max(human) + 10

Honesty note: this is a SMOKE TEST on synthetic fixtures used to calibrate the
scanner's weights — it is not a benchmark against wild text and claims no
detector-grade accuracy. It exists so weight edits that break separation fail
loudly in CI/selftest fashion (the effortmining habit: measure, don't vibe).
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CLI = os.path.join(ROOT, "scripts", "idiolect.py")


def scan(path):
    out = subprocess.run(
        [sys.executable, CLI, "scan", "--file", path, "--json"],
        capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def main():
    rows = []
    for kind in ("slop", "human"):
        d = os.path.join(HERE, "fixtures", kind)
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".txt"):
                rep = scan(os.path.join(d, fn))
                rows.append((kind, fn, rep["score"], rep["band"],
                             [h["id"] for h in rep["hits"][:3]]))
    w = max(len(r[1]) for r in rows)
    for kind, fn, score, band, top in rows:
        print(f"{kind:6} {fn:{w}} {score:3}/100 {band:8} {', '.join(top)}")
    loud = [r[2] for r in rows if r[0] == "slop" and "-subtle" not in r[1]]
    subtle = [r[2] for r in rows if r[0] == "slop" and "-subtle" in r[1]]
    human = [r[2] for r in rows if r[0] == "human"]
    margin = min(loud) - max(human)
    ok = (min(loud) >= 41 and max(human) <= 15 and margin >= 20
          and all(s >= 20 and s >= max(human) + 10 for s in subtle))
    print(f"\nloud slop    {min(loud)}..{max(loud)}   (need every one >= 41)")
    if subtle:
        print(f"subtle slop  {min(subtle)}..{max(subtle)}   (need >= 20: deterministic "
              f"floor — the blind auditor owns these)")
    print(f"human range  {min(human)}..{max(human)}   (need every one <= 15)")
    print(f"margin       {margin}   (need >= 20)")
    print(f"\nbench: {'PASS — separation holds' if ok else 'FAIL'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

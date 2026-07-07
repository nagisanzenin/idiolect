---
name: humanize
description: Rewrite existing text so it reads human — either scrubbed-and-souled in its own register, or fully re-voiced as one of the roster's people. Use when the user has a draft that "sounds like AI" or wants existing copy converted into a specific voice.
argument-hint: "[voice-slug] then paste text or give a file path"
---

# /idiolect:humanize — from slop to person

Two modes. Both end with before/after scanner scores, because "sounds better to me" is not a receipt.

Voice references can be fuzzy and human ("make it sound like the diner guy", "like me" → the `self` voice): resolve against `$IDIO voices --json` and proceed, mentioning the match in passing. No voice mentioned → Mode A.

## Setup

```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$IDIOLECT_ROOT}}"
# unset everywhere (opencode)? ROOT = two directories up from this SKILL.md
IDIO="python3 $ROOT/scripts/idiolect.py"
```

Input text goes to a scratch file via the Write tool, never inline in shell.

## Mode A — scrub and soul (no voice given)

The goal is the same author, minus the generator fingerprints, plus a pulse.

1. Save input to `orig.txt`; run `$IDIO scan --file orig.txt [--platform <p>]`. Show the user the score and the top tells found — this is the "before" receipt and it teaches them what was wrong.
2. Rewrite with three obligations:
   - **Kill every flagged tell** (the report gives line numbers): the lexical slop, the constructions ("It's not X. It's Y."), the metronomic sentence lengths, the wrap-up ending, the bold-header bullets.
   - **Preserve every factual claim exactly.** Scrubbing is not summarizing; if the original has five specifics, the rewrite has five specifics. NEVER add facts that aren't in the original — if it's thin on specifics, tell the user that's the real problem (specificity is the strongest human signal there is) and ask for two or three true details worth adding.
   - **Restore a pulse**: vary sentence lengths (target CV ≥ 0.55), let one opinion or ambivalence through, cut the throat-clearing, end without a bow. Register stays the author's own — formal text stays formal; don't inflict aggressive casualness (that's the "humanizer house style," and it's the next tell).
3. Re-scan the rewrite. Target ≤ 15 (≤ 20 for formal registers). Iterate to 3 times.
4. Deliver: rewrite in a fenced block + `receipt: 68 → 9 (clean)` + one line on the biggest change.

## Mode B — re-voice (voice slug given)

The text's CONTENT survives; its author is replaced.

1. Scan the original (before-receipt), then read the voice profile in full, plus `_shared/craft.md` and the platform row of `_shared/platforms.md` if a platform is stated.
2. Rewrite as that person would have written it from scratch: their opener habits, their syntax, their systematic flaws, their stance where the content touches something they'd have an opinion about. Facts and commitments from the original are preserved; framing, rhythm, and lexicon are theirs.
3. Verify: `$IDIO scan` (≤ 15) AND `$IDIO conform --voice <slug>` (PASS). Iterate to 3.
4. Deliver with both receipts and, if invented interior texture crept in, the `texture:` line.

## What this skill refuses to do

- Manufacture fake specifics to lower the score (invented numbers are worse than slop — they're lies).
- "Humanize" text for deception-sensitive contexts when the user says so explicitly (academic submissions, legal filings). Say why and offer honest editing instead.
- Chase detector scores. The target is *reads like a person wrote it*, which is measured by the linter and your ear together — when they disagree, say so and let the ear win.

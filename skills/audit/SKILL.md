---
name: audit
description: Two-layer AI-tell audit of any text — deterministic scanner (lexicon, constructions, stylometry with line numbers) plus a blind semantic judge. Use when the user wants to know whether text reads AI-generated, what specifically gives it away, and how to fix it.
argument-hint: "paste text or give a file path [--platform x]"
---

# /idiolect:audit — where the mask slips

Two independent layers, merged into one report. The scanner catches what regex can see; the blind judge catches what only reading can (no stakes, hollow specificity, symmetric enthusiasm, tutorial cadence). Neither layer knows or cares who wrote the text.

## Setup

```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$IDIOLECT_ROOT}}"
# unset everywhere (opencode)? ROOT = two directories up from this SKILL.md
IDIO="python3 $ROOT/scripts/idiolect.py"
```

## Flow

1. Save the text to a scratch file. Run `$IDIO scan --file <f> --json [--platform <p>]`.

2. **Spawn the blind judge** — the `idiolect-auditor` agent — passing ONLY: the text (via the scratch file path), the platform if known, and nothing else. No authorship context, no "the user thinks this is AI," no scanner results (independence is the point; two correlated judges are one judge). On Codex, invoke it explicitly: `$idiolect-auditor, audit this file: <path>`. If subagent spawning is unavailable, do the semantic pass yourself in a deliberately separate step, AFTER writing down the scanner results, using the auditor's rubric (read `$ROOT/agents/idiolect-auditor.md`).

3. **Merge into the report:**

   ```
   verdict: 62/100 — reads generated (scanner 58 · judge: generated-leaning)
   deterministic tells (line-anchored):
     L3  "seamlessly integrates" (lexical T1)
     L7  its_not_x_its_y construction
     —   sentence lengths metronomic (CV 0.31; human ≥ 0.5)
   semantic tells (judge):
     - zero cost or stake attaches to any claim
     - enthusiasm is symmetric across all six sentences
   human texture present: 1 exact number; no temporal anchors, no first-person actions
   top 5 fixes, in order of impact: ...
   ```

4. **Frame it honestly, always:** this is a linter verdict about *how the text reads*, not a forensic finding about *how it was made*. Skilled humans trip tells; edited AI passes. Never output "this was written by AI" — output "these N things make it read generated, here's the fix for each." If the user is auditing someone ELSE's text to accuse them (a student, an employee), say plainly: no tool can prove authorship from style, false-positive rates hit non-native writers hardest (Liang et al. 2023), and this report must not be used as evidence against a person.

5. If the user wants the fixes applied, hand off to `/idiolect:humanize` mode A with the report as the worklist.

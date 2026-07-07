---
name: synthesize
description: Create a new voice profile — from a writing corpus (measured, not vibed), or invented to fill a gap in the roster. Extends the roster beyond the 60+ built-ins. Use when the user wants a new/custom voice, a voice "like these samples", or a voice the roster lacks.
argument-hint: "<new-slug> from <files|pasted samples> | <new-slug> to fill <gap description>"
---

# /idiolect:synthesize — grow the roster

New voices are measured into existence, not adjective-ed. A synthesized voice ships with the same contract as the built-ins: full VOICE-SPEC frontmatter, stance engine, systematic error profile, three exemplars that scan clean, and distance ≥ 0.2 from every existing voice.

## Setup

```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$IDIOLECT_ROOT}}"
# unset everywhere (opencode)? ROOT = two directories up from this SKILL.md
IDIO="python3 $ROOT/scripts/idiolect.py"
$IDIO path   # note custom_voices dir — new voices are written THERE, never into the plugin
```

## Mode 1 — from a corpus

1. **Consent gate (one question, then done):** if the corpus is the writing of a single identifiable person who is not the user, ask once: is this your own writing or writing you're authorized to model? If yes (or it's the user's own / mixed public material), proceed; note the answer in the profile's provenance line. The output is always a NEW fictional voice influenced by the corpus's stylistic features — this skill does not build impersonation kits of named people, and single-author clones overfit anyway.
2. Concatenate the samples into one scratch file. `$IDIO fingerprint --file <f> --json > fp.json` — this measures what adjectives can't: sentence-length distribution, burstiness, contraction rate, punctuation profile, casing habits, informal markers, favorite content words.
3. `$IDIO synth-scaffold --slug <slug> --from-fingerprint fp.json` — a prefilled skeleton with the measured stylo numbers.
4. **Spawn `idiolect-synthesizer`** with: the scaffold, fp.json, the corpus file path, and `$ROOT/docs/VOICE-SPEC.md`. It drafts the full profile into the custom voices dir and runs the validate loop itself. (No subagent support on this platform? Do its job yourself following `$ROOT/agents/idiolect-synthesizer.md`.)
5. **Verify the roster still separates:** `$IDIO validate <slug>` must pass; `$IDIO distance --json` must show no pair under 0.2. If the new voice sits too close to an existing one, push the DIFFERENTIATING axes (error class, platform habitat, humor mechanics, openers) — not random noise.
6. Deliver: profile path, the three exemplars, scan scores, nearest-neighbor distance. The voice is immediately usable: `/idiolect:write <slug> ...`.

## Mode 2 — to fill a gap

1. Read `$ROOT/data/seeds.json` (the axes and the taken territory) and run `$IDIO voices` + `$IDIO distance --json` to see where the roster is thin (locales, ages, error classes, platforms, trades).
2. Design a seed the roster lacks — same axis discipline as the built-ins, fictional composite, dignity rule from VOICE-SPEC applies in full (register yes, eye-dialect never; competence first).
3. Continue from step 3 above (scaffold → synthesizer → validate → distance).

## Mode 3 — `self`

Hand off to `/idiolect:self` — the user's own voice has its own pipeline (continuous capture, provenance weighting).

## Rules

- Custom voices live in `$IDIOLECT_HOME/voices/` (shown by `$IDIO path`) so plugin updates never touch them. Back them up like the personal assets they are.
- A voice that can't pass validate doesn't get saved half-done; fix or abandon.
- Never name a profile after a real public figure or mimic one recognizably. The test: if a stranger could guess who it's "really" supposed to be, redesign it.

---
name: self
description: Build and maintain the user's OWN voice profile from continuously captured writing plus explicit samples — status, build/refresh, add samples, capture on/off. Use when the user wants posts in their own voice, wants to see what's been learned about their style, or wants to manage capture.
argument-hint: "status | build | add <file|paste> | on | off | drift"
---

# /idiolect:self — your voice, defended

The roster's voices are fictional. This one is real: a running stylometric picture of how YOU actually write, so drafts in "your voice" are measured against you, not against a compliment. It's also the anti-homogenization move — co-writing with RLHF-tuned models measurably pulls writers toward one style (Padmakumar & He 2024; CHI 2025 showed the pull is strongest on non-Western writers). A maintained self profile is how your idiolect survives the tooling.

## Setup

```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$IDIOLECT_ROOT}}"
# unset everywhere (opencode)? ROOT = two directories up from this SKILL.md
IDIO="python3 $ROOT/scripts/idiolect.py"
```

## How capture works (tell the user this the first time)

On Claude Code, a `UserPromptSubmit` hook feeds each of your prompts through a filter: prose-like messages ≥ 15 words are kept; commands, code, paths, and logs are rejected. Kept text lands in a LOCAL corpus (`$IDIO path` → `self_corpus`) that never leaves the machine, never enters the repo, and caps itself (samples outlive prompts when it compacts). `self off` stops capture instantly; `self clear` deletes the corpus. On Codex/opencode there's no per-prompt hook — feed it explicitly with `add`.

Prompt text is a REGISTER of you (terse, imperative, workish), not the whole you. Explicit samples of real writing (your posts, emails, comments) are tagged `sample` and weigh more in the build. The more samples, the truer the profile.

## Actions

- **status** — `$IDIO self status`: corpus size, sample/prompt split, capture on/off, ready-for-build.
- **add** — user pastes text or gives files: Write to a scratch file, `$IDIO self add --file <f>` (chunks and tags as samples). This is the highest-leverage thing a user can do for profile quality; nudge for 3–5 real posts/emails.
- **on / off / clear** — pass through to the CLI; confirm before `clear` (destructive).
- **build** (or refresh) — the main event:
  1. `$IDIO self status --json` — if not `ready_for_build`, say what's missing (~800 words or 5 samples) and offer `add`.
  2. `$IDIO fingerprint --self --json > fp.json` — the measured stylometrics, with the sample/prompt provenance split.
  3. `$IDIO synth-scaffold --slug self --from-fingerprint fp.json` — skeleton with THEIR real numbers.
  4. **Co-author, don't fabricate.** The stylo block comes from measurement; the human block comes from the human. Show what you observed in plain terms ("you average 11-word sentences with high variance; you drop capitals in short lines; 'honestly' and 'basically' are load-bearing"), then ASK for the parts no corpus reveals: what they do, what they'll argue about, what they refuse to sound like (that's their `banned` list — start it with whatever corporate words they hate). Exemplars: prefer 3 REAL posts from their samples (lightly trimmed) over synthetic ones; synthetic exemplars only with their sign-off.
  5. Save to `$IDIOLECT_HOME/voices/self.md`, run `$IDIO validate self` (custom voices get the relaxed exemplar threshold), fix until ok.
  6. From now on `/idiolect:write self <platform> — <brief>` writes as them, conform-checked against their own parameters.
- **drift** — rerun `fingerprint --self`, diff the numbers against the profile's stylo block, report what changed ("your sentences got 20% shorter since March; em dashes crept in — keep or update?"). Update the profile only with consent; drift is sometimes growth and sometimes contamination, and only the owner knows which.

## Privacy lines (hard)

Corpus and profile are local files under the user's home; nothing is uploaded, and this skill never pastes raw corpus entries into chat beyond short quoted fragments needed for the build conversation. If the user asks what's stored: `$IDIO self corpus --tail 10` shows them, `self clear` erases it, `self off` stops it. Their voice is their asset — treat the profile file as sensitive as an SSH key.

---
name: write
description: Write a social post in one of the roster's voices (or the user's own `self` voice) — platform-native, craft-floored, scanner-verified. Use when the user wants a post, caption, announcement, reply, or any short-form text written as a distinct human voice.
argument-hint: "<voice-slug|pick> <platform> — <brief>"
---

# /idiolect:write — one post, one person, verified

You are about to write as a specific human being. Not "in a casual tone" — as a person with a biography, grudges, a phone number, and systematic typing habits. The engine measures whether you succeeded.

## Setup

Resolve the engine (works on Claude Code, Codex, opencode):

```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$IDIOLECT_ROOT}}"
# If all three are unset (e.g. opencode skill install), ROOT = two directories
# up from this SKILL.md file (skills/write/SKILL.md -> repo root).
IDIO="python3 $ROOT/scripts/idiolect.py"
```

Free text (briefs, drafts) reaches the engine ONLY via files or stdin — write it with the Write tool to a scratch file and pass `--file`. Never inline user text into a shell command (quoting bugs become injection).

## Flow

1. **Parse the ask.** Voice, platform, brief — all optional except some notion of what to say. Voices may arrive as fuzzy human references ("the HVAC guy", "the Vietnamese food-truck lady", "someone young and lowercase"): resolve them against `$IDIO voices --json` (display/archetype/locale/domains) and proceed, mentioning the match in passing. No platform stated → infer from the ask and say which you assumed. Never require a flag or a slug from the user.

2. **Pick the voice** (if not specified): write the brief to a scratch file, then
   `$IDIO pick --platform <p> --brief-file <f> --n 3 --distinct --json`
   Choose the best fit from the three and tell the user in one line who you chose and why. `self` is a valid voice if the user has built one (`$IDIO voices` shows it).

3. **Become the person.** Read, fully: the voice profile (path from `voices --json`), `$ROOT/skills/_shared/craft.md`, and the platform's row + judgment calls in `$ROOT/skills/_shared/platforms.md`. The profile's exemplars are your few-shot anchor; the frontmatter is your hard constraint set; the stance engine tells you what this person would actually SAY about the brief — which is the difference between costume and voice.

4. **Vary the structure.** Decide opener type (scene|question|price|claim|address|fact), shape (story|tip|list|rant|announcement|reply), length bucket (short|med|long), then
   `$IDIO ledger check --voice <slug> --opener <o> --shape <s> --len <l>`
   If it reports collisions with recent posts, change ≥2 axes. Same person, different day.

5. **Draft.** Craft floor first (one job, exact numbers, honest hook, no wrap-up ending), voice second (their words, their flaws — applied per the error profile's RULES, not sprinkled), platform grammar third. Honesty rules from craft.md are hard: never invent verifiable claims; track invented interior texture.

6. **Verify — the loop that makes this plugin different.** Write the draft to a scratch file, then:
   `$IDIO scan --file <f> --platform <p>` — target: score ≤ 15 (≤ 20 if the voice's formality ≥ 0.6; formal registers legitimately carry more T3 vocabulary).
   `$IDIO conform --file <f> --voice <slug>` — must PASS.
   Fix what the reports point at (they give line numbers and per-check targets) and re-run. Up to 3 revisions; if still failing, ship the best version and say plainly which check fails and why you judged it acceptable.

7. **Record.** `$IDIO ledger add --voice <slug> --platform <p> --opener <o> --shape <s> --len <l> --file <f>`

8. **Deliver.** The post in a plain fenced block (copy-pasteable), then one receipt line:
   `receipt: scan 7/100 (clean) · conform PASS · structure price/story/med · ledger recorded`
   If you invented interior texture (a mood, a domestic detail), add a `texture:` line listing it so the user consciously keeps or cuts it. If the brief needed a factual claim you didn't have (a stat, a testimonial), say so — never fabricate one.

## Register notes

- The scanner is a linter, not a judge of souls; when it flags something the voice genuinely would say (Desmond's "arguably"), keep the voice and say you overrode the linter and why.
- One post = one platform. Cross-posting is what `/idiolect:campaign` is for, because reformatting is not re-voicing.

---
name: idiolect
description: Front door and router for the idiolect voice engine. Use when the user mentions idiolect, asks what voices are available or who should write something, wants writing that "doesn't sound like AI", says text "sounds like ChatGPT/AI slop", or asks for human-sounding posts and no more specific idiolect skill has already matched. Also the first-run onboarding.
argument-hint: "anything — plain English works"
---

# /idiolect — the front door

Nobody should need to memorize commands to use this plugin. Whatever the user said in plain language, map it to the right capability, do any setup silently, and go. Slash commands exist for power users; natural language is the primary interface.

## Setup (silent)

```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$IDIOLECT_ROOT}}"
# unset everywhere (opencode)? ROOT = two directories up from this SKILL.md
IDIO="python3 $ROOT/scripts/idiolect.py"
```

First contact in a session where things seem unfamiliar: run `$IDIO doctor` quietly; only surface it if something's broken.

## Route by intent, not by wording

| The user wants… | Do |
|---|---|
| a post/caption/reply/announcement written ("write me a launch post", "post about X that sounds human") | `skills/write/SKILL.md` flow |
| existing text fixed ("this sounds like AI", "make this sound human/like me/like a person") | `skills/humanize/SKILL.md` flow |
| to know IF something reads AI ("does this look AI-written?", "check this") | `skills/audit/SKILL.md` flow |
| many posts / multi-platform launch ("promote this everywhere", "5 posts for the launch") | `skills/campaign/SKILL.md` flow |
| a new voice ("make me a voice like these samples", "we need a French chef type") | `skills/synthesize/SKILL.md` flow |
| their own voice ("write it like ME", "what have you learned about my style?") | `skills/self/SKILL.md` flow |
| to browse ("what voices are there?", "who've you got for LinkedIn?") | `$IDIO voices` (+ `pick` for a shortlist), presented as PEOPLE, below |

Read the routed SKILL.md and follow it — don't reimplement it from memory.

## Voices are referred to like people — resolve fuzzy references yourself

Users say "the HVAC guy", "the Vietnamese food-truck lady", "the grumpy CTO", "someone young and lowercase", "that barrister one". Resolve against `$IDIO voices --json` (display, archetype, locale, domains, formality) and just proceed with the match, mentioning it in passing ("writing this as Dale, the Ohio HVAC owner"). Ask only when two candidates genuinely fit. Never make the user learn slugs — slugs are for receipts.

When presenting the roster, never dump 60 rows. Show a curated handful for their need ("For LinkedIn you'd want Keisha — blunt HR director; Stu — anti-guru ops manager; Rohan — Delhi D2C founder…"), and mention the full list exists (`$IDIO voices`).

## Zero-flag defaults (apply everywhere)

- No platform stated → infer from the content and say the assumption in half a sentence.
- No voice stated → `pick` with the brief and choose, announcing who and why in one line.
- No brief beyond a topic → draft anyway; ask at most ONE question, and only when the answer changes the post (e.g. the price, the link policy).
- User pasted text with no instruction, in an idiolect context → they almost always want humanize or audit; pick by whether they seemed to be ASKING (audit) or FIXING (humanize).

## First-run onboarding (when the user says "what is this" / right after install)

In five lines, as conversation, not documentation: (1) it writes as 60+ specific fictional people, not "a casual tone"; (2) every draft is verified by a scanner that catches AI tells with line numbers; (3) it can learn THEIR voice too — mention `self status` and that capture is local and `self off` exists (transparency up front builds the trust the feature needs); (4) plain English is the whole interface; (5) offer one concrete demo: "give me a product and a platform and I'll show you the same post in two very different voices."

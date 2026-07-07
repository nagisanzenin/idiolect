# idiolect

**Humanizers remove the AI. idiolect installs a human.**

62 fully-specified voice profiles — real psychologies, systematic flaws, platform habitats, few-shot exemplars — plus a deterministic AI-tell scanner, a blind semantic auditor, and a closed verify-revise loop. Write, humanize, audit, and mass-produce short-form posts that read as *distinct, specific people*, with receipts instead of vibes. Runs on **Claude Code, OpenAI Codex, and opencode** out of the box.

> *idiolect* (n.) — the variety of a language unique to one individual. The thing this plugin manufactures, measures, and defends.

## Why this exists

The popular humanizer skills are subtractive: a pattern list that removes "delve," em dashes, and rule-of-three. Useful — and structurally insufficient. Everyone running the same subtraction converges on a new detectable house style (uniformly short sentences, aggressive casualness, zero em dashes), because **removal can't produce identity**. Meanwhile RLHF models homogenize by design — co-writing with them measurably flattens stylistic diversity (Padmakumar & He 2024), hardest on non-Western writers (CHI 2025).

idiolect's claim, from the research up (see [docs/THEORY.md](docs/THEORY.md), 40+ sources, corrections included):

**Human-reading text = Scrubbed × Voiced × Crafted × Varied** — multiplicative, a zero anywhere zeroes the product. So the plugin ships all four layers: a tell scanner (scrub), a voice roster (voice), a craft floor distilled from a century of copy and rhetoric research (craft), and structure-rotation + overlap + distance machinery (variance).

## The demo

Same brief — "promote a $15/mo booking tool" — through five voices ([full posts + receipts](samples/SAMPLES.md)):

| author | scan | one line of it |
|---|---:|---|
| Dale, HVAC owner, Ohio (facebook) | 0 | "Diane won. 31 of the last 40 bookings came in after 6pm." |
| Zoe, art student, Glasgow (x) | 9 | "my dms are now exclusively for chat and crimes" |
| Keisha, HR director, Charlotte (linkedin) | 0 | "Small tools keep beating platforms here." |
| Hank, corn farmer, Nebraska (x) | 0 | "47 pickups the first week and her phone stayed in the kitchen." |
| Mai, bánh mì truck, Houston (facebook) | 0 | "Worth it for the 11:30 line alone." |
| the AI control | **84** | "🚀 …revolutionize the way you manage appointments…" |

Zero cross-post overlap. Every post conform-checked against its voice's declared parameters.

## Install

**Claude Code**

```
/plugin marketplace add nagisanzenin/idiolect
/plugin install idiolect@idiolect
```

**Codex** — `codex plugin marketplace add nagisanzenin/idiolect && codex plugin add idiolect@idiolect`, then `bash scripts/install-codex.sh`.
**opencode** — add `{ "skills": { "urls": ["github:nagisanzenin/idiolect"] } }` to opencode.json, then `bash scripts/install-opencode.sh`.
Details, differences, and fallbacks: [INSTALL-OMNI.md](INSTALL-OMNI.md).

## Use it in plain English

Commands exist, but natural language is the interface:

- *"write a launch post for my screenshot app, somewhere between reddit and HN energy"*
- *"this reads like ChatGPT, fix it"* → before/after scanner scores
- *"does this look AI-written?"* → line-anchored tell report + blind semantic audit
- *"give me 4 posts for the launch — use the nurse and the sneaker guy, pick the other two"*
- *"make me a voice from these three newsletters"*
- *"write it like ME"* → the `self` voice, built from your own measured writing

Slash forms: `/idiolect:write`, `humanize`, `audit`, `campaign`, `synthesize`, `self` (on Codex: `$write`, …). Voices are referred to like people — "the HVAC guy" resolves; slugs are for receipts.

## What's inside

- **62 voices** (`voices/`): ages 22–71, twelve L2/dialect textures (Vietnamese, German, Russian, Brazilian, Polish, Japanese, French, Egyptian, Korean, Danish, Nigerian English, Indian English…), every major platform habitat, eleven systematic error classes. Each profile: biography that generates opinions, stance engine, executable style patterns, anti-patterns, error rules, opener/closer pools, three scanner-verified exemplars. All fictional composites; a hard dignity rule (register habits yes, eye-dialect mockery never, competence first).
- **The engine** (`scripts/idiolect.py`, stdlib-only): `scan` (tiered tell lexicon with model-era tags + construction regexes + stylometrics, line-anchored, cluster-scored), `conform` (draft vs voice parameters), `distance` (roster anti-clone floor, enforced at 0.2), `overlap` (campaign dedup), `pick`, `ledger` (structure rotation), `fingerprint`, `self` (private local corpus of your own writing), `validate`, `selftest` (25 tests), `doctor`.
- **Three agents**: a **blind auditor** (reads only the text — catches the semantic tells regex can't: no stakes, symmetric enthusiasm, hollow specificity), an isolated **campaign writer** (one voice per context, so N posts can't bleed into each other), a **synthesizer** (corpus → new validated voice).
- **The data** (`data/tells.json`): the tell lexicon as data, era-tagged (gpt4-era vs gpt5-era vs model-family tells), locally extensible via `tells.local.json`, calibrated against a fixture bench (`bench/`) with stated pass criteria.
- **Your voice** (`/idiolect:self`): on Claude Code a hook quietly keeps a *local* corpus of your prose-like prompts (15+ words, no code/commands; `self off` kills it, `self clear` erases it, nothing ever leaves your machine); add real samples for a truer profile; `drift` tells you when your style is shifting under AI influence.

## How a draft gets made

Pick voice → check the structure ledger (no repeated skeletons) → draft on the craft floor (one job, exact numbers, honest hook, no wrap-up bow) → `scan` (target ≤15) → `conform` (PASS required) → blind audit for campaigns → ledger the structure → deliver with a receipt line:

```
receipt: scan 5/100 (clean) · conform PASS · structure price/story/med · ledger recorded
texture: invented "after 6pm" detail — verify or keep as color
```

## Honesty rules (built into the tools, not the fine print)

- Never fabricates verifiable claims (stats, testimonials, partnerships) — invented *interior* texture is allowed and always disclosed in a texture ledger.
- N voices presenting your thing in N registers = ghostwriting, supported. N voices posing as N unrelated satisfied strangers = astroturfing; the campaign skill refuses the shape and offers the legitimate one. No posting automation is included, anywhere.
- The scanner lints *your drafts*; it does not convict *other people*. Style detection false-positives hit non-native writers hardest (Liang et al. 2023) — the audit output says so.

## Limits, stated plainly

Lexical tells decay (the lexicon is era-tagged data, not scripture). Polite astroturf bottoms out mid-band for ANY deterministic scanner — that's the blind auditor's jurisdiction. No "undetectable" claims, ever: the receipt says *no known tells, in-voice by measurement, distinct by measurement, survived a hostile blind read* — nothing more, and nothing less than that either.

## Extend it

`/idiolect:synthesize` grows the roster (measured from a corpus or invented into a gap — new voices must pass the same validate + distance gates as the built-ins). Custom voices live in `$IDIOLECT_HOME/voices/`, safe from plugin updates. The spec is public: [docs/VOICE-SPEC.md](docs/VOICE-SPEC.md).

## License

MIT. The voices are fictional composites; any resemblance to real persons is coincidental. What you post is yours, on your accounts, under each platform's rules.

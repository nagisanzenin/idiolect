# idiolect

**Humanizers remove the AI. idiolect installs a human.**

62 fully-specified voice profiles — real psychologies, systematic flaws, platform habitats, few-shot exemplars — plus a deterministic AI-tell scanner, a blind semantic auditor, and a closed verify-revise loop. Write, humanize, audit, and mass-produce short-form posts that read as *distinct, specific people*, with receipts instead of vibes. Runs on **Claude Code, OpenAI Codex, and opencode** out of the box.

> *idiolect* (n.) — the variety of a language unique to one individual. The thing this plugin manufactures, measures, and defends.

## The difference, in one post

The same request — *"announce a kiln drop: the dark-blue glaze finally came out right, a couple pieces cracked, shop update Thursday"* — scored by the same deterministic scanner (`idiolect scan`; 0 = clean, higher = more AI tells).

**Without idiolect** — default assistant output · **`scan 45 / 100 — slop`**

> ✨ Big news, friends! ✨ After weeks of anticipation, our stunning dark blue glaze collection is finally here — and we couldn't be more thrilled to share it with you! 🌊
>
> Each piece is lovingly handcrafted and fired to perfection, embodying the beautiful imperfection of the ceramic journey. Yes, a few pieces didn't quite survive the kiln — but that only makes the survivors more special. 💙
>
> Whether you're a seasoned collector or just beginning your pottery journey, these one-of-a-kind treasures are sure to elevate your space and bring a touch of handmade magic into your everyday moments.
>
> Don't miss out — the shop update drops this Thursday! 🛍️ Link in bio.

*Scanner flags:* em-dash density, "elevate your," "journey" ×2, "whether you're a…", a six-hashtag pile, emoji density. Human texture: **none** — no specifics, no time anchor, no first-person action.

**With idiolect** — voice *Freja, ceramicist, Copenhagen* · **`scan 0 / 100 — clean`** · conform PASS, in-range

> 33 went in. 27 came out whole.
>
> I opened 114 at 7, before anyone else was in.
>
> The dark blue behaved. People have waited for it since firing 112 and I could not promise it, the kiln decides and not me. This morning the color came right on every blue piece, even the two that cracked. I wrote a full line in the log for it. Most firings get only numbers.
>
> The kiln took its share too. 2 to the bin, a mug and the tall bottle, cracked at the foot, photo 4. You cannot both blow and have flour in the mouth, as we say at home.
>
> 4 are seconds. A little glaze pooling on the inside, nothing that leaks. They go 40 percent off with the flaw in the photo, not hidden.
>
> Shop update Thursday 19:00 CET. Link in bio. 8 mugs, 5 bowls, 3 bottles in the dark blue. Mugs 260 DKK, bowls 340, bottles 520. Shipping inside EU is 89, the carrier's number.
>
> Stoneware, fired to 1240 degrees. I look forward to see them go Thursday.

*Written by the engine, then verified:* the new **competence** layer kept it in clay (no borrowed jargon), **soul** is on (the blue glaze earns the one long line in the log; the loss is stated flat), and the L1-Danish idiom is her systematic error profile, not decoration. The scanner credits exact quantities, a time anchor, and first-person actions as human texture. Nothing here "sounds human" — it *scans* clean and *conforms* to a declared fingerprint.

[Five voices, one brief, all conform-checked →](#the-demo)

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

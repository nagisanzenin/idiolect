# Voice profile specification

*The contract every voice file obeys. `idiolect.py validate` enforces it; `conform` measures drafts against it; `distance` compares profiles by it.*

A voice profile is one markdown file: **YAML frontmatter** (machine-readable parameters) + **markdown body** (the psychology, patterns, and exemplars the writing model actually absorbs). Built-in voices live in `voices/`; user-created voices in `$IDIOLECT_HOME/voices/` (default `~/.claude/idiolect/voices/`). The `self` slug is reserved for the user's own learned voice.

## Frontmatter (strict subset of YAML)

The parser is dependency-free, so frontmatter is a *defined subset* of YAML: 2-space indentation, `key: value` scalars, inline lists `[a, b, c]`, nested maps two levels deep, no anchors, no multi-line scalars. Quote strings containing `:` or `#`.

```yaml
---
slug: dale-hvac                  # required; [a-z0-9-]+; unique across roster
display: "Dale — HVAC owner-operator, Ohio"   # required
archetype: trades/small-business # required; family/niche
age: 51                          # required; integer
locale: "en-US Rust Belt (Ohio)" # required; dialect/register description
platforms: [facebook, nextdoor]  # required; ordered by nativeness
formality: 0.3                   # required; 0=shitpost, 1=barrister
temperament: {O: 0.35, C: 0.75, E: 0.45, A: 0.6, N: 0.3}  # required; Big Five 0-1 — a flavor prior, not a diagnosis
humor: "dry, understated"        # required
domains: [home services, small business, weather]  # required; topical turf `pick` matches briefs against
competence:                      # optional; epistemic range — makes casting credible, bounds adaptation
  expert: [home services, hvac, furnaces, small-business ops]  # deep turf; `pick` matches here first
  adjacent: [pricing, local weather, tools]  # can speak shallowly, in character
  outsider: [software, medicine, finance, art]  # will NOT fake; see off_turf
  off_turf: deflect              # deflect | analogize | admit | decline
  ceiling: "trade-deep, not academic; concrete over theory"
mood: {baseline: steady-wry, volatility: low}   # optional; transient register prior the writer applies
passions: ["the fix that lasts", "underdog customers", "honest pricing"]  # optional; topics that bend the prose
stylo:                           # required block — measured by `conform`
  sent_mean: 12                  # target mean sentence length (words)
  sent_cv: 0.65                  # target burstiness (CV of sentence lengths); humans ~0.55-0.9
  fragment_rate: some            # none | rare | some | heavy
  contractions: heavy            # none | light | standard | heavy
  paragraphs: "1-3 sentences, no headers ever"   # prose description
  emoji: never                   # never | rare | brand-set | native
  exclaims_per_100w: 0.5         # target ceiling
  em_dash: never                 # never | rare | comfortable
  ellipsis: "trailing thought, max 1 per post"    # prose description
  caps: standard                 # standard | lowercase | caps-burst | headline-only
  terminal_period: always        # always | usually | dropped-in-short-lines
error_profile:                   # required — imperfection must be SYSTEMATIC
  class: fast-typer              # one of the error classes in data/seeds.json
  rate: light                    # none | light | moderate
  rules:                         # the SAME flaws recur; random typos read fake
    - "occasional missing apostrophe in its/dont"
    - "no comma before 'but'"
lexicon:
  favorites: [folks, "tell you what", rig]      # words this voice reaches for
  intensifiers: [pretty, real, "a heck of a"]
  hedges: ["I'd say", "far as I can tell"]
  banned: [delve, leverage, journey, passionate] # voice-specific bans ON TOP of data/tells.json
  profanity: none                # none | mild | comfortable
never:                           # hard anti-patterns; `conform` greps for violations where testable
  - hashtags
  - bullet lists
  - questions engineered for engagement
---
```

### Field notes

- **`competence`** (optional) — the epistemic range that makes casting credible and bounds adaptation. `expert` is deep turf `pick` scores briefs against first; `adjacent` the voice can speak to shallowly and in character; `outsider` it will not fake. `off_turf` (`deflect`|`analogize`|`admit`|`decline`) says how it behaves when a brief lands outside range; `ceiling` describes how far its intelligence reaches — an art student meets a systems brief through analogy, not fluent jargon. Absent = no competence gating (back-compat). A voice earns the field only if toggling it moves `pick` output. This is the guard against a voice writing convincingly about something its person would never credibly know.

- **`mood` / `passions`** (optional) — the dial-able soul layer, applied by the *writer*, not scored by `conform`. `passions` are the topics that make this person write longer, sharper, with one more number — expressed as friction in the prose, never as "I'm passionate about…". `mood` (a `baseline` register and a `volatility`) shifts the temperature while the fingerprint holds. They earn their place by moving the writing — and by cutting the blind auditor's *symmetric-enthusiasm* flag — not by being stated. See `skills/_shared/craft.md`, "Soul: friction, not declaration".

- **`temperament`** — Big Five ↔ language correlations are real but small (|r| ≈ .05–.20, Yarkoni 2010). Treat the vector as a *generation prior* that shapes stance and emotional bandwidth, never as a claim that readers can measure personality from a post.
- **`stylo.sent_cv`** — the single highest-leverage number in the file. RLHF models write metronomically (CV ≈ 0.3–0.45); real writers alternate short and long (CV ≈ 0.55–0.9). `conform` fails a draft that undershoots the voice's target by more than 0.15.
- **`error_profile`** — flaws are identity. A fast-typer drops apostrophes; a boomer trails ellipses; an L2 writer transfers her first language's grammar *consistently* (the same article drop every time, not a dice roll). `rate: none` is a valid profile (Desmond the barrister makes no errors; that too is a fingerprint).
- **L2 and dialect voices — represent, don't caricature.** Register habits (article omission, tense simplification, calques, discourse particles) are documented sociolinguistics and are in-bounds. Phonetic eye-dialect respelling ("dis", "dat", "vewy") is out-of-bounds everywhere: it reads as mockery and it reads as fake. Competence first: every voice is good at its job; the flaw layer lives in typography and register, never in intelligence.

## Body sections (required, in order)

```markdown
## Who this is
3-6 sentences of compressed biography that GENERATE opinions: what they do all day,
what they're proud of, what annoys them, what they want. A voice is a point of view
before it is a style. No physical descriptions; nothing a post would never reveal.

## Stance engine
5-8 bullet lines: loves / hates / suspicious-of / soft-spot / will-argue-about.
These make posts feel AUTHORED. ("Dale hates: paying for software subscriptions,
people who skip maintenance then blame the unit, the phrase 'quick question'.")

## How they write
6-10 concrete pattern bullets: how a post opens, how it argues, sentence rhythm,
what punctuation does, favorite moves. Every bullet must be executable by a writer
who has never seen this person.

## What they never do
5-8 hard anti-patterns beyond the frontmatter `never` list, with the WHY when it
teaches. ("Never explains the joke — trusts the reader or drops it.")

## Error profile in practice
2-4 lines showing the systematic flaws applied. Show a wrong-and-kept sentence.

## Openers and closers
4-6 openers, 3-5 closers, drawn from the voice. The writer ROTATES; the ledger
enforces non-repetition across a campaign.

## Exemplars
Three complete posts in-voice, each labeled with intent and platform:
### Exemplar 1 — promo (facebook)
### Exemplar 2 — story (facebook)
### Exemplar 3 — opinion/reply (nextdoor)
Exemplars are the strongest steering signal in the file. They must clear
`idiolect.py scan` with a score under 10 and read aloud as one person.
```

## Validation rules (`idiolect.py validate`)

1. Frontmatter parses under the strict subset; all required fields present and typed.
2. `slug` matches filename; unique across built-in + custom rosters.
3. `formality`, `temperament.*` in [0,1]; `sent_cv` in [0.2, 1.2]; `sent_mean` in [4, 35].
4. `error_profile.class` is a known class; `platforms` are known platforms.
5. All three exemplars present; each scans below 10 (built-in roster is held to this).
6. Every voice-`banned` term genuinely absent from the voice's own exemplars.

## Distance (`idiolect.py distance`)

Pairwise distance over: formality, temperament (5 dims), sent_mean/30, sent_cv,
emoji/caps/contractions/fragment (categorical mismatches), error class, locale
family, platform overlap (Jaccard), humor keyword overlap. Range 0–1. The build
fails a roster where any pair scores below **0.20** — distinctiveness is enforced,
not hoped for. (The floor was set empirically against the shipped roster's
distribution; clones land under 0.15, honest neighbors around 0.25–0.35.)

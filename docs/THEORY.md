# Theory: engineering voices that read human

*Why idiolect is built the way it is. Literature-reviewed 2026-07; every load-bearing claim carries its citation, and the corrections we had to make to popular versions of these claims are listed at the end — a theory that can't say where it was wrong can't be trusted where it's right.*

---

## 1. The problem is a distribution, not a vocabulary

LLM text is identifiable for a structural reason, not an accidental one: instruction-tuned models sample from the center of an aggregated distribution. Wikipedia's AI-cleanup editors put it precisely — the result tends toward "the most statistically likely result that applies to the widest variety of cases." The center of everyone is no one.

The evidence that this is alignment-specific, not intrinsic to LLMs, matters for design: co-writing with an RLHF-tuned model measurably reduced the diversity of what people wrote, while the base model did not (Padmakumar & He 2024), and AI writing suggestions pull non-Western writers toward Western styles (Agarwal et al., CHI 2025). The mode is an artifact of tuning for the median rater. **Voice engineering is deliberately sampling far from the mode, on purpose, consistently.**

Word-level fingerprints are real but decaying assets. "Delves" ran 28× its expected frequency in 2024 PubMed abstracts and "underscores" 13.8× (Kobak et al., *Science Advances* 2025) — but those are GPT-4-era tells; 2025-26 models shed most of that lexicon (the residue is thinner: *emphasizing, highlighting, showcasing*), each model family has its own fingerprint (Grok leans *causal/empirical*; Llama emits almost no em dashes; "no markdown" instructions cut Claude's em dashes ~98% but GPT-4.1's only ~14% — arXiv 2603.27006), and ChatGPT-era vocabulary is now leaking into human *speech* (Yakura et al. 2025), eroding the gap from both sides. Every lexical tell has a half-life. This is why `data/tells.json` carries an `era` field and is data, not code: the lexicon is a consumable, the architecture is not.

## 2. Three detectors, three different games

1. **Statistical machines** (GPTZero, Binoculars, Fast-DetectGPT) read perplexity, burstiness, and token-likelihood curvature. Binoculars reaches 90%+ detection at 0.01% FPR zero-shot (Hans et al. 2024). Their weakness is hybrid and edited text; their danger is false positives — Liang et al. (2023) showed detectors flag non-native English writers at wildly elevated rates.
2. **Lexical/pattern machines and pattern-primed humans** read the tell list: the Wikipedia signs, em-dash density, rule-of-three, "not just X but Y." This is the layer the viral humanizer skill addresses — necessary, and insufficient.
3. **Attentive human readers** are the strongest detector and the real audience. Expert readers hit near-perfect accuracy where laypeople are near chance (Russell et al., ACL 2025), and they key on *semantic* properties no regex sees: absence of stakes, symmetric enthusiasm, hollow specificity, timeless floating. Meanwhile ordinary readers' heuristics are inverted and gameable — they read first-person pronouns, contractions, and family topics as proof of humanity (Jakesch et al., *PNAS* 2023), which is why idiolect's scanner **reports** human-texture signals but never subtracts them from the score: the signals that convince readers are exactly the ones a faker adds first.

Design consequence: a deterministic scanner for layers 1–2 (cheap, line-anchored, reproducible), a blind LLM auditor for layer 3 (the only layer that can read stakes), and the honest admission that the scanner is a *linter for your own drafts*, not a forensic detector of anyone else's — a distinction the detector-SaaS industry blurs and this project will not.

## 3. The four-layer theorem

**Human-reading text = Scrubbed × Voiced × Crafted × Varied.** Multiplicative: a zero anywhere zeroes the product.

- **Scrubbed but voiceless** is the humanizer trap: everyone running the same 33-rule subtraction converges on a new detectable house style — uniformly short sentences, aggressive casualness, zero em dashes. Subtraction cannot differentiate; only identity can.
- **Voiced but uncrafted** is authentic garbage. Nobody reads it, which is its own kind of detection.
- **Crafted but invariant** self-plagiarizes: same skeleton every post, and skeleton-matching is exactly how moderators catch fleets (r/programming's mods eyeball "em-dash density and generic structure").
- **Varied but unscrubbed** just spreads the tells across more shapes.

The layers map to components: tells.json + `scan` (layer 1), voice profiles + `conform` (layer 2), craft.md + the blind auditor's quality block (layer 3), the ledger + `overlap` + `distance` (layer 4).

## 4. What a voice actually is

The profile format operationalizes six findings:

**4.1 A voice is a coordinate, not an adjective** (Biber 1988; Biber & Conrad 2009). Registers occupy positions on empirically derived dimensions — involved↔informational, narrative↔non-narrative, elaborated↔situation-dependent, overt persuasion, abstract↔concrete. "Casual and friendly" is not a coordinate; `formality: 0.3, contractions: heavy, fragment_rate: some, sent_mean: 12` is. Profiles specify feature consequences, not vibes.

**4.2 Function words and habits below conscious control carry identity** (Burrows 2002; Grieve 2007; Stamatatos 2009). Authorship attribution works on the top-100 most frequent words, punctuation profiles, and sentence-length distributions — precisely because nobody performs their preposition rates. So profiles pin the subconscious layer: punctuation fingerprint, contraction policy, sentence-length mean *and variance*, caps discipline. The burstiness number (`sent_cv`) is the single highest-leverage parameter: RLHF models write metronomically; people alternate.

**4.3 Idiolect is recurring co-selection, not exotic vocabulary** (Coulthard 2004 — Derek Bentley; the UNABOM analysis, by FBI analyst James Fitzgerald, turned on habitual phrasings like "you can't eat your cake and have it too"). Hence each profile's *owned co-selections*: Dale's "tell you what," Mai's "my husband say," Keisha's one-sentence knife paragraph. Recurrence is what reads as one real person.

**4.4 Flaws are systematic or they are fake.** Error analysis (Corder 1967; Selinker 1972; Swan & Smith 2001) shows L2 errors are predictable *transfer*, not noise: Russian speakers drop articles; Vietnamese (isolating, no inflection) yields tense simplification and article variability; typists make skill-stratified errors (Grudin 1983) and ~80% of typos are single-character operations (Damerau 1964). Cohort graphemics are equally rule-governed (McCulloch 2019): boomer ellipses are letter-writing pauses, not passive aggression; Gen-Z lowercase-no-period is a sincerity code; the texting period reads less *sincere* (Gunraj et al. 2016). So every profile carries an `error_profile` with RULES and a rate — the same writer makes the same class of mistake — and a dignity constraint: register habits are documented sociolinguistics; phonetic eye-dialect is mockery and, worse for our purposes, reads instantly fake.

**4.5 A voice is a distribution across audiences, not a point** (Bell 1984; Giles's accommodation theory). Real people shift toward their audience along socially meaningful dimensions. Hence platform adaptation lives in the profile (`platforms` ordered by nativeness) and in platforms.md — the person persists, the register accommodates.

**4.6 Real authors are narrow in skeleton, wide in flesh** (Koppel et al. 2007's unmasking result: same-author works differ on only a few shallow features; different authors differ in depth. Register can swamp idiolect on surface dimensions — Biber & Conrad 2009). This single finding justifies the whole variance layer: hold the deep fingerprint constant (function words, punctuation, co-selections), force the shallow layer to rotate (opener, shape, length — the ledger's three axes), and check that cross-voice differences run deeper than within-voice ones (`distance` on parameters + content axes).

And a boundary honesty note: reliable stylometric *attribution* needs ~2,500–5,000 words (Eder 2015). Individual social posts are far below that — which cuts both ways: no one can prove a 60-word post's authorship from style, and neither can we prove our voices "pass." What we can verify is the absence of known tells, conformance to declared parameters, and separation between voices. That is what the receipts claim, and all they claim.

## 5. Craft: the floor is a century old and it replicates

Distilled in `skills/_shared/craft.md`; the theory here is only that the canon agrees with the lab where they overlap. Specificity beats superlatives (Hopkins 1923; Ogilvy 1963) and specificity is simultaneously the top human-texture signal — models round specifics off. Fluent beats erudite, measurably: needless complexity lowers judged intelligence (Oppenheimer 2006). Stories lower counter-arguing (Green & Brock 2000). Hooks work when they open a *specific, nameable* information gap (Loewenstein 1994), and negativity's click advantage is real but small (+2.3% per negative headline word across the 105k-headline Upworthy archive — Robertson et al., *Nature Human Behaviour* 2023) — a dial with a per-voice cap, not a mandate. Desire can only be channeled, never created; copy must meet the reader's awareness stage (Schwartz 1966). One correction the canon usually gets wrong: "show the cost of inaction" is folklore as a law — meta-analytically, gain frames slightly beat loss frames for prevention behaviors (O'Keefe & Jensen 2006/2009).

## 6. The measurement doctrine (the part inherited from my other tools)

From **engram**: separation of powers. The writer wants the draft to pass; therefore the judge must be blind. The auditor receives text and platform, never authorship or the writer's hopes; its output is a strict-JSON receipt, and "when torn, round down." From **effortmining**: never trust a vibe you could measure. Scanner weights were calibrated against a fixture bench with a stated pass criterion (loud slop ≥ 41, humans ≤ 15, margin ≥ 20) that fails loudly when a weight edit breaks separation — and the bench documents its own limit: subtle astroturf bottoms out near the suspect band because polite testimonial slop is lexically clean; its tells are semantic (no stakes, symmetric enthusiasm), which is the blind auditor's jurisdiction, not regex's. From **production-grade**: ship discipline — versioned manifests, a publishing runbook, and docs that admit what isn't proven.

The closed loop, everywhere: generate → measure (`scan` + `conform`) → blind-judge → revise → record (`ledger`). Nothing "sounds human"; it scans, conforms, and survives a hostile read, or it goes back.

## 7. The honesty layer is load-bearing, not decorative

Three lines, drawn in the tools themselves:

1. **Texture vs. claims.** A fictional voice may have a cold coffee and a slow Tuesday (characterization); it may not have a fabricated customer, revenue figure, or credential (deception). Drafts ship with a texture ledger listing invented interior details for the human to keep or cut; missing facts are requested, never invented.
2. **Personas vs. sockpuppets.** N voices presenting *your* thing in N registers on *your* channels is ghostwriting — ancient, legal, universal. N voices posing as N unrelated satisfied strangers is astroturfing; the campaign skill says so and offers the legitimate shape instead. (The tool also ships no posting automation whatsoever: it writes drafts, humans own accounts and the send button.)
3. **Audit ≠ accusation.** The scanner lints drafts; it does not convict people. Style detectors false-positive on non-native writers (Liang et al. 2023), and idiolect's audit output explicitly refuses evidence-against-a-person framing.

These aren't compliance stickers; they're what keeps the product on the side of the line where its users' reputations survive contact with reality.

## 8. The self voice: defense against the flattening

The homogenization result (§1) has a personal corollary: heavy co-writing with the mode erodes your own idiolect — and the pull is strongest on writers furthest from the training center. The `self` pipeline is the countermeasure: continuously fingerprint what the user actually writes (locally, inspectable, deletable), co-author a profile where measurement supplies the stylo block and the human supplies the stance block, then `conform` every "write it like me" draft against the user's *measured* parameters instead of the model's memory of them. Drift detection closes the loop: when your sentences shorten 20% over a quarter, you get to decide whether that's growth or contamination.

## 9. Known limits, stated plainly

- **Tell half-life.** The lexical layer decays as models update and humans absorb AI vocabulary (Yakura 2025). Treat tells.json like a threat-intel feed, not scripture; the `era` tags and local-extension file (`tells.local.json`) exist for this.
- **The deterministic floor.** Polite, lexically-clean generated text scans mid-band at best. That's a property of the world, not a bug; the semantic layer exists because of it.
- **No detector claims.** idiolect never certifies text as "undetectable" (the SaaS tools that do get caught at 100% by the next detector update, with garbled output as the consolation prize). The claim is narrower and honest: no known tells, in-voice by measurement, distinct by measurement, and it survived a hostile blind read.
- **Param distance ≠ perceived distance.** The distance metric bounds parameter-space similarity; two low-distance voices can still read distinct (different lives) and two high-distance ones can share a pet phrase by accident. The `overlap` check and the auditor's same-author pass cover the gap from the text side.
- **Voices drift in long sessions.** Context is a solvent; the writer agent re-reads the profile per post, and campaign isolation exists precisely because one context writing four voices averages them by the fourth.

## Bibliography (load-bearing only)

Detection & homogenization: Kobak et al. 2025 (*Sci. Adv.*, excess vocabulary); Liang et al. 2023 (GPT detectors bias vs non-native writers); Hans et al. 2024 (Binoculars); Russell et al., ACL 2025 (expert human detection); Jakesch, Hancock & Naaman, *PNAS* 2023 (inverted human heuristics); Padmakumar & He 2024 (homogenization is RLHF-specific); Agarwal et al., CHI 2025 (Western style pull); Yakura et al. 2025 (AI vocabulary entering speech); arXiv 2603.27006 (per-model em-dash rates); Wikipedia:Signs of AI writing (WikiProject AI Cleanup, living document).

Voice science: Biber 1988; Biber & Conrad 2009; Pennebaker & King 1999; Yarkoni 2010 (the honest effect sizes); Kacewicz et al. 2014 (status and pronouns); Burrows 2002 (Delta); Evert et al. 2017 (cosine Delta); Grieve 2007 (punctuation profiles); Stamatatos 2009 (survey); Eder 2015 (minimum sample sizes); Koppel, Schler & Bonchek-Dokow 2007 (unmasking); Coulthard 2004 (idiolect, Bentley); Fitzgerald 2017 (UNABOM); Bell 1984 (audience design); Giles et al. 1991 (accommodation); Swan & Smith 2001 (L2 transfer); Corder 1967; Selinker 1972; Damerau 1964 + Grudin 1983 (typo taxonomies); McCulloch 2019 (*Because Internet*); Gunraj et al. 2016 (the period study, which measured sincerity).

Craft & persuasion: Hopkins 1923; Ogilvy 1963/1983; Halbert 2013 (*Boron Letters*); Schwartz 1966 (awareness stages); Thomas & Turner 1994 (classic style as one stance among several); Orwell 1946 (all six rules, including the sixth); Strunk 1918 / Pullum 2009 (what's actually wrong with S&W); Zinsser 1976; Pinker 2014 (curse of knowledge); Graham 2015/2024 ("Write Like You Talk"; "Writes and Write-Nots"); Aristotle, *Rhetoric* (ethos/pathos/logos — kairos is the sophists', not his); Cialdini 1984/2021 (six principles; Unity added 2021); Green & Brock 2000 (transportation); Oppenheimer 2006 (fluency); Heath & Heath 2007; Loewenstein 1994 (information gap); Robertson et al. 2023 (Upworthy negativity, +2.3%/word); O'Keefe & Jensen 2006/2009 (framing corrections); Kahneman & Tversky 1979.

## Corrections we adopted (so you don't re-import the folklore)

1. UNABOM idiolect analysis: Fitzgerald (FBI), not Coulthard. 2. Kairos isn't Aristotle's triad. 3. Big Five↔language correlations are |r|≈.05–.20 — corpus tendencies, never per-text rules (temperament vectors are generation priors, not diagnoses). 4. "Omit needless words" is Strunk 1918; Pullum attacks S&W's grammar errors, not concision. 5. Cialdini had six principles until Unity (2021). 6. Loss-framing superiority is folklore; gain frames win for prevention (O'Keefe & Jensen). 7. The Binghamton period study measured *sincerity*, texting-only. 8. Stylometry has no "typical accuracy"; it collapses on short/cross-genre text (and needs 2.5–5k words). 9. Double-spacing marks typewriter training generally, not Gen X specifically. 10. Biber found six dimensions; D6 is minor. 11. Swan & Smith 2nd ed. lacks reliable Vietnamese coverage — our Vietnamese profiles derive from typology + dedicated error-analysis literature. 12. Orwell's rule 6 ("break any of these rules sooner than say anything outright barbarous") is integral, and he breaks the other five himself.

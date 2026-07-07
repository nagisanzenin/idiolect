---
name: campaign
description: One brief, N posts, N genuinely different people — voice-isolated writers, cross-post overlap detection, per-post verification receipts. Use for launching/promoting something across multiple posts or platforms without the posts sharing a fingerprint.
argument-hint: "<N> posts for <brief> on <platform(s)> [--campaign name]"
---

# /idiolect:campaign — many voices, zero bleed

The failure mode of one writer producing N "different" posts is convergence: same skeleton, same rhythm, swapped adjectives. This skill prevents it structurally — each post is written in an isolated context that has seen ONLY its own voice, then the set is checked for overlap like the adversarial reviewer a real editor would be.

## Setup

```bash
ROOT="${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$IDIOLECT_ROOT}}"
# unset everywhere (opencode)? ROOT = two directories up from this SKILL.md
IDIO="python3 $ROOT/scripts/idiolect.py"
CID="<campaign-name-or-date-slug>"
```

## Flow

1. **Cast the voices.** Brief to a scratch file, then
   `$IDIO pick --platform <p> --brief-file <f> --n <N> --distinct --json`
   (per-platform picks if the campaign spans platforms — and pass `--exclude` with every already-cast slug on each subsequent pick, or the same voice will happily win two platforms). `--distinct` does greedy max-distance casting — announce the cast in one line each: who, platform, why they fit the brief. If the user named people fuzzily ("use the nurse and the sneaker guy"), resolve those against `$IDIO voices --json` first and fill the rest of the cast with `pick`. Nothing here requires the user to know a slug or a flag.

2. **Pre-assign structure.** Build a rotation table before any writing: no two posts share (opener, shape) even across different voices; lengths vary. This is the campaign-level variance guard; the per-voice ledger check comes free in step 3.

3. **Fan out, isolated.** For each (voice, platform, structure) row, spawn an **`idiolect-writer`** agent whose prompt contains ONLY: the voice profile path, the brief, the platform, the assigned structure, and the two shared docs' paths. One writer never sees another writer's voice or output — isolation is what prevents bleed; parallelism is just the bonus. Each writer self-verifies with `scan` + `conform` and saves to `<scratch>/post-<slug>.txt`.
   *Codex/opencode fallback (no auto-spawn):* write them yourself SEQUENTIALLY, and before each post re-read that voice's profile in full and consciously drop the previous voice's rhythm; the verification gates below still catch bleed if you fail.

4. **Verify the set, not just the posts.**
   - Per post: `scan` ≤ 15 (≤ 20 formal voices) and `conform` PASS — re-check even though writers self-checked (writers grade homework; you grade writers).
   - Across posts: `$IDIO overlap <scratch>/post-*.txt` — any flagged pair (5-gram Jaccard > 0.12, or a shared distinctive phrase) means one of the two gets rewritten. Shared brief facts (product name, price) are fine; shared SENTENCES are the tell that kills campaigns.
   - Blind pass: spawn **`idiolect-auditor`** ONCE with all post files and platforms, nothing else — it flags any post that reads generated and any two that read same-authored. Fix what it catches.

5. **Record and deliver.** For each post: `$IDIO ledger add --voice <s> --platform <p> --opener --shape --len --campaign "$CID" --file <post>`. Then deliver each post in its own fenced block headed by `— <voice display> · <platform>`, followed by a receipts table:

   | voice | platform | scan | conform | overlap | structure |
   |---|---|---|---|---|---|
   | dale-hvac | facebook | 6 clean | PASS | ok | price/story/med |

   Plus one `texture:` section listing any invented interior details across the set, per the honesty rules in `_shared/craft.md`.

## Cadence and hygiene

- Same campaign rerun later? Pass `--exclude` with the previous cast (or trust `pick`'s recent-use penalty) so the same three people don't launch everything you make.
- Posting is the USER's act, on their accounts, under each platform's rules — this skill produces drafts and receipts, it does not automate accounts, and a campaign of N posts pretending to be N unrelated customers praising a product is astroturfing; the legitimate shape is N of YOUR channels/personas presenting YOUR thing in N registers. If a request crosses into fake-grassroots-consensus territory, say so and offer the legitimate shape.

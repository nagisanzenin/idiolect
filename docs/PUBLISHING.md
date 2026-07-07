# Publishing protocol

*How idiolect ships. Single-repo self-marketplace (the engram pattern), no tags, no CI — everything rides `main`.*

## Architecture

One repository serves as both plugin and marketplace:

| File | Role |
|---|---|
| `.claude-plugin/plugin.json` | Claude Code plugin manifest — **the** authoritative version |
| `.claude-plugin/marketplace.json` | self-marketplace (`source: "./"`) → users install `idiolect@idiolect` |
| `.codex-plugin/plugin.json` | Codex manifest (keep `version` in lockstep) |
| `.agents/plugins/marketplace.json` | Codex marketplace catalog |

Installs resolve `main` HEAD. The marketplace name is `idiolect` (top-level `name` in marketplace.json), hence `idiolect@idiolect`.

## The golden rule

> Any change users must receive **requires bumping `version` in `.claude-plugin/plugin.json`** (and its mirror in `.codex-plugin/plugin.json`). A push to `main` without a version bump is invisible to installed users.

Bump policy: patch = wording/tell-lexicon/voice fixes · minor = new voices, new skill/agent/command surface · major = breaking schema (VOICE-SPEC frontmatter, CLI flags, state layout).

## Release runbook

1. Make the change. If voices or tells changed: `python3 scripts/idiolect.py validate` (62/62) and `python3 scripts/idiolect.py distance` (no pair < 0.2).
2. `python3 scripts/idiolect.py selftest` and `python3 bench/run.py` — both must PASS. The bench is the scanner's regression gate; if a weight edit breaks separation, fix the weights, not the bench.
3. Bump `version` in BOTH manifests (`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`).
4. Update `CHANGELOG.md`; update `README.md` if user-visible.
5. `claude plugin validate .` from the repo root.
6. Smoke-test uninstalled: `claude --plugin-dir ./` in a scratch session; exercise `/idiolect:write` and the SessionStart-free hook path (`echo '{"prompt":"..."}' | hooks/self-capture.sh` must stay silent, exit 0).
7. Commit and push `main`. That is the publish.

## Consume flow

```
/plugin marketplace add nagisanzenin/idiolect
/plugin install idiolect@idiolect          # Claude Code
codex plugin marketplace add nagisanzenin/idiolect && codex plugin add idiolect@idiolect
npx skills add nagisanzenin/idiolect       # skills-only fallback (Codex/opencode/anything Agent-Skills)
```

## Post-release drift check

`installed_plugins.json` and the cache dir under `~/.claude/plugins/cache/idiolect/idiolect/<version>/` update via the normal updater; nothing manual. The single source of truth for "what version is this" is `plugin.json` on `main` — keep the two manifests equal or the two ecosystems will disagree about updates.

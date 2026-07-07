# idiolect on Claude Code, Codex, and opencode

idiolect is an **omni-repo**: one codebase, three agent platforms, out of the box. The core is shared verbatim everywhere — `skills/` (Agent Skills standard `SKILL.md`), `voices/`, `data/`, and the dependency-free `scripts/idiolect.py` engine. Only the glue differs per platform, and this file is the glue manual.

| | skills | agents (blind auditor, writer, synthesizer) | self-capture hook | state |
|---|---|---|---|---|
| **Claude Code** | native plugin, `/idiolect:write …` | native, auto-delegated | automatic (UserPromptSubmit) | `~/.claude/idiolect` |
| **Codex** | plugin or `npx skills add`, `$write …` | TOML ports, explicit `$name` invocation | if your Codex build fires UserPromptSubmit hooks; otherwise `self add` | set `IDIOLECT_HOME` in-workspace |
| **opencode** | native skills (model-invoked) | markdown ports, `@name` / task tool | manual `self add` | `IDIOLECT_HOME` or default |

## Claude Code

```
/plugin marketplace add nagisanzenin/idiolect
/plugin install idiolect@idiolect
```

Everything works with zero further setup: six skills (`/idiolect:write`, `humanize`, `audit`, `synthesize`, `campaign`, `self`), three subagents spawned automatically, and per-prompt self-capture (see `skills/self/SKILL.md` for the privacy story; `self off` to disable).

## Codex

```
codex plugin marketplace add nagisanzenin/idiolect
codex plugin add idiolect@idiolect
bash scripts/install-codex.sh        # copies codex/agents/*.toml -> ~/.codex/agents/
```

Or skills-only, no plugin machinery (the robust fallback): `npx skills add nagisanzenin/idiolect`.

The two Codex differences, same as every omni-repo:

1. **Subagents are TOML and explicit-invocation only.** Where a skill says "spawn the idiolect-auditor," on Codex you say `$idiolect-auditor, audit these files: <paths>`. Blindness is preserved — pass only text paths and platforms, never authorship context. Plugin-distributed TOML agents aren't a documented Codex feature yet, hence the installer.
2. **Sandbox + state.** `idiolect.py` writes its ledger/corpus/custom-voices under `IDIOLECT_HOME` (default `~/.claude/idiolect`). Codex's workspace-write sandbox may prompt for writes outside the workspace — `export IDIOLECT_HOME="$HOME/.idiolect"` (or anywhere convenient) once and forget it.

Skills invoke as `$write` / `$audit` / … (Codex uses `$name` mentions or the `/skills` picker, not `/idiolect:` slashes).

## opencode

opencode reads Agent Skills natively (and also discovers `~/.claude/skills` and `~/.agents/skills`). Two routes:

```jsonc
// opencode.json
{ "skills": { "urls": ["github:nagisanzenin/idiolect"] } }
```

or `npx skills add nagisanzenin/idiolect`. Then:

```
bash scripts/install-opencode.sh     # copies opencode/agents/*.md -> ~/.config/opencode/agents/
```

Skills are model-invoked on opencode (no slash commands): ask for the thing ("write this launch as mai-banhmi for facebook") and the skill activates. Agents are `@idiolect-auditor` / `@idiolect-writer` / `@idiolect-synthesizer` or task-tool spawns. There is no per-prompt hook system for self-capture — feed your own writing with `self add` (honestly, explicit samples build a better self profile anyway; prompts are a narrow register of you).

## The one resolver rule (if you're hacking on skills)

Skills locate the engine as: `${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$IDIOLECT_ROOT}}`, falling back to "two directories up from this SKILL.md". If you vendor the skills somewhere exotic, set `IDIOLECT_ROOT` to the repo root and everything follows.

## Verify any install

```
python3 scripts/idiolect.py doctor     # env + data + voices parse
python3 scripts/idiolect.py selftest   # 25 internal tests
python3 scripts/idiolect.py voices     # the roster
```

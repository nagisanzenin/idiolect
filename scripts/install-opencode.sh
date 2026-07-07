#!/usr/bin/env bash
# idiolect — opencode glue installer.
# Copies the markdown agent ports into your opencode global agents dir and
# prints the opencode.json skills snippet. Idempotent; safe to re-run.
set -eu

REPO_ROOT="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
OC_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
AGENTS_DIR="$OC_CONFIG/agents"

echo "idiolect: installing opencode agent ports"
echo "  repo:            $REPO_ROOT"
echo "  opencode config: $OC_CONFIG"

if [ ! -d "$REPO_ROOT/opencode/agents" ]; then
  echo "idiolect: error: opencode/agents not found under $REPO_ROOT" >&2
  exit 1
fi

mkdir -p "$AGENTS_DIR"
n=0
for f in "$REPO_ROOT"/opencode/agents/*.md; do
  [ -e "$f" ] || continue
  cp "$f" "$AGENTS_DIR/"
  echo "  + $(basename "$f") -> $AGENTS_DIR/"
  n=$((n + 1))
done
echo "idiolect: installed $n agent(s)."

if command -v python3 >/dev/null 2>&1; then
  echo "idiolect: running selftest…"
  python3 "$REPO_ROOT/scripts/idiolect.py" selftest >/dev/null 2>&1 \
    && echo "idiolect: selftest OK" \
    || echo "idiolect: WARNING — selftest did not pass; run it directly to see why" >&2
fi

cat <<EOF

Next steps:
  1. Point opencode at the skills — either add this repo to opencode.json:
       { "skills": { "urls": ["github:nagisanzenin/idiolect"] } }
     or, since opencode also reads ~/.claude/skills and ~/.agents/skills:
       npx skills add nagisanzenin/idiolect
  2. Skills are model-invoked on opencode (no slash commands) — ask for what
     you want ("write this as dale-hvac for facebook") and the skill triggers,
     or reference it explicitly by name.
  3. Agents: @idiolect-auditor / @idiolect-writer / @idiolect-synthesizer,
     or let the primary agent spawn them via its task tool.
  4. (optional) export IDIOLECT_HOME="\$HOME/.idiolect" to choose where the
     ledger, self corpus, and custom voices live.

See INSTALL-OMNI.md for the full story and caveats.
EOF

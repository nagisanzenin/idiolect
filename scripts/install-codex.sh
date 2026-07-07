#!/usr/bin/env bash
# idiolect — Codex glue installer.
# Copies the TOML subagent ports into your Codex agents dir and prints the
# IDIOLECT_HOME hint. Idempotent; safe to re-run. Claude Code users don't need this.
set -eu

REPO_ROOT="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
AGENTS_DIR="$CODEX_HOME/agents"

echo "idiolect: installing Codex subagent ports"
echo "  repo:       $REPO_ROOT"
echo "  codex home: $CODEX_HOME"

if [ ! -d "$REPO_ROOT/codex/agents" ]; then
  echo "idiolect: error: codex/agents not found under $REPO_ROOT" >&2
  exit 1
fi

mkdir -p "$AGENTS_DIR"
n=0
for f in "$REPO_ROOT"/codex/agents/*.toml; do
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
  1. (recommended) Pin state inside your workspace so Codex's workspace-write
     sandbox never prompts:
       export IDIOLECT_HOME="\$HOME/.idiolect"     # add to your shell rc
  2. Install the skills (if not via 'codex plugin add idiolect@idiolect'):
       npx skills add nagisanzenin/idiolect
  3. In Codex, invoke skills as \$write / \$humanize / \$audit / \$synthesize /
     \$campaign / \$self, and the agents explicitly, e.g.
       "\$idiolect-auditor, audit this file: <path> (platform: x)"

See INSTALL-OMNI.md for the full story and caveats.
EOF

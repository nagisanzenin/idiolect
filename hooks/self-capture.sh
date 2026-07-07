#!/usr/bin/env bash
# idiolect self-capture hook (UserPromptSubmit).
# Feeds the user's prompt JSON (stdin) to `idiolect.py self capture`, which
# filters (prose >=15 words, no commands/code/logs) and appends to the LOCAL
# corpus. MUST be silent and MUST always exit 0: this runs on every prompt,
# and any output would pollute the conversation context.
set -u
ROOT="${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")/.." && pwd)}}"
if command -v python3 >/dev/null 2>&1; then
  python3 "$ROOT/scripts/idiolect.py" self capture >/dev/null 2>&1 || true
fi
exit 0

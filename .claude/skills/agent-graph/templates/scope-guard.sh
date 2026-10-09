#!/usr/bin/env bash
# PreToolUse hook for Edit|Write|MultiEdit|NotebookEdit.
# Blocks writes outside SCOPE_DIRS and any write to the read-only evaluator.
# Register in .claude/settings.json:
#   "hooks": {"PreToolUse": [{"matcher": "Edit|Write|MultiEdit|NotebookEdit",
#     "hooks": [{"type": "command", "command": ".claude/skills/agent-graph/templates/scope-guard.sh"}]}]}
# Configure with env var AGENT_GRAPH_SCOPE="src:out:docs" (paths relative to the project root).
set -euo pipefail
input=$(cat)
path=$(printf '%s' "$input" | python3 -c 'import json,sys; d=json.load(sys.stdin)["tool_input"]; print(d.get("file_path") or d.get("notebook_path") or "")')
[ -z "$path" ] && exit 0
root="${CLAUDE_PROJECT_DIR:-$PWD}"
rel=$(python3 -c 'import os,sys; print(os.path.relpath(os.path.abspath(sys.argv[1]), sys.argv[2]))' "$path" "$root")
case "$rel" in
  checks/*|tests/*) echo "agent-graph: $rel is part of the read-only evaluator" >&2; exit 2 ;;
  ../*) echo "agent-graph: $rel is outside the project" >&2; exit 2 ;;
esac
[ -z "${AGENT_GRAPH_SCOPE:-}" ] && exit 0
IFS=: read -ra dirs <<< "$AGENT_GRAPH_SCOPE"
for d in "${dirs[@]}"; do
  case "$rel" in "${d%/}"/*|"$d") exit 0 ;; esac
done
echo "agent-graph: $rel is outside SCOPE ($AGENT_GRAPH_SCOPE)" >&2
exit 2

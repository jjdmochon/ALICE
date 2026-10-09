#!/usr/bin/env python3
"""PreToolUse hook for agent-graph runs.

Blocks Edit/Write outside the run's SCOPE and any write to the read-only
evaluator (checks/, tests/). Opt-in per project; do not register globally.

Register in the project's .claude/settings.json:
  "hooks": {"PreToolUse": [{"matcher": "Edit|Write|MultiEdit|NotebookEdit",
    "hooks": [{"type": "command",
               "command": "python \"$HOME/.claude/skills/agent-graph/templates/scope-guard.py\""}]}]}

Set AGENT_GRAPH_SCOPE to the writable folders, relative to the project root,
separated by os.pathsep (";" on Windows, ":" elsewhere), e.g. "out;src".
Without it, only the evaluator and out-of-project guards apply.
"""
import json
import os
import sys

READ_ONLY = ("checks", "tests")


def block(msg: str) -> None:
    print(f"agent-graph: {msg}", file=sys.stderr)
    sys.exit(2)


def main() -> None:
    tool_input = json.load(sys.stdin).get("tool_input", {})
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not path:
        return
    root = os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    target = os.path.abspath(os.path.join(root, path))
    try:
        rel = os.path.relpath(target, root)
    except ValueError:  # different drive on Windows
        block(f"{target} is outside the project")
    parts = rel.replace("\\", "/").split("/")
    if parts[0] == "..":
        block(f"{rel} is outside the project")
    if parts[0] in READ_ONLY:
        block(f"{rel} is part of the read-only evaluator")
    scope = [d.strip().strip("/\\") for d in os.environ.get("AGENT_GRAPH_SCOPE", "").split(os.pathsep) if d.strip()]
    if not scope:
        return
    rel_posix = "/".join(parts)
    for d in scope:
        d = d.replace("\\", "/")
        if rel_posix == d or rel_posix.startswith(d + "/"):
            return
    block(f"{rel} is outside SCOPE ({os.environ['AGENT_GRAPH_SCOPE']})")


if __name__ == "__main__":
    main()

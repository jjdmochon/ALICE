---
name: agent-graph
description: Run a multi-step task as a graph of bounded subagent nodes with a read-only evaluator, a measured baseline, commit/revert per attempt, and independent gates (autoresearch-style). Use when the user asks to run, plan, or resume a task "as a graph", with subagents/nodes, as an autoresearch loop, or when a task spans several independent outputs that each need a verifiable check. Skip for tasks under 3 nodes or one file, which run as a single session with checks.md only.
argument-hint: "TASK | OUTPUT | CHECKS | SOURCES | SCOPE | LIMIT"
---

# Agent graph

Inputs for this run: $ARGUMENTS

Fill the six inputs below from the arguments or the conversation. Ask one focused question only if a missing input changes the outcome. Otherwise record the assumption in graph.md and proceed.

| Input | Meaning |
|---|---|
| TASK | What to complete |
| OUTPUT | Deliverable and its path |
| CHECKS | Acceptance criteria, ideally computable |
| SOURCES | Material the nodes may read |
| SCOPE | Paths the run may modify |
| LIMIT | Run limit with a unit: wall-clock, tool calls, or attempts |

## Goal

Complete TASK as a graph of bounded nodes. Deliver OUTPUT plus graph.md, checks.md, results.tsv, and progress.md, so another session can rerun or extend the work.

- **Small-task rule:** if the task is under 3 nodes or touches one file, skip the graph. Run one session and keep checks.md only.
- **Stop** when every check passes, a node is blocked after 3 attempts, or LIMIT is reached.

## Role

You are the lead: you design, run, and merge. Read CLAUDE.md, lessons.md, and the current state of the work before editing. Subagents build nodes. You never delegate merging or gating.

## Evaluator

- Define the metric or pass criteria in `checks/` before any work starts.
- `checks/` and `tests/` are read-only for every node, including the lead. Any edit to them invalidates the run.
- Gate order:
  1. Deterministic check (script, test, computed value).
  2. Independent verifier: a subagent with fresh context that did not build the artifact.
  3. The node's own report, as supporting evidence only.
- Never use self-reported confidence as a gate.

## Step 0: baseline

Run the checks on the current state. Record the result as the first row of `results.tsv` (template: `templates/results.tsv`).

## Step 1: split

Write `graph.md` (template: `templates/graph.md`). For each node, record:

- id, declared inputs, one output, owned files, check, budget
- type: `code` or `judgment`

Draw an edge only when a node consumes another node's output. Nodes with no edge between them form parallel groups.

A **code node** is any step with exactly one correct answer: merge, sort, dedupe, compare, count, or compute. The lead writes it as a script and runs it, never through a subagent. If a required tool is unavailable, name the blocker and complete the nodes that do not depend on it.

Pause for user approval only if:

- there are more than 6 nodes,
- an edge carries risky work, or
- the plan writes outside SCOPE.

Otherwise proceed.

## Step 2: run

- Run ready nodes in parallel, at most 4 at a time.
- Give each judgment node its own Agent call with `isolation: "worktree"`.
- Pass each node only its spec, inputs, owned files, and budget. List explicitly what it must not read.
- Each node returns JSON: `{output_path, verdict, evidence[], open_issues[]}`.
- Commit each attempt. If a gate fails or the metric regresses, `git reset` to the last accepted commit and log the row as `reverted`.
- Merge accepted outputs in code.
- Do not weaken a gate to obtain a pass.

## Step 3: return paths

- **Correction:** return a failed node to its builder with the evidence and the instruction "fix this node only; change approach from the last attempt". After 3 attempts, mark the node `blocked`, record why, and continue with the independent nodes. Return failed units only, never the whole batch.
- **Learning:** after an accepted result, append one rule with its evidence to `lessons.md`. Keep graph.md structural.

## Permissions

Prose is not a boundary. Enforce it with:

- `permissions.deny` / `ask` rules in `.claude/settings.json`;
- a `PreToolUse` hook that blocks Edit/Write outside SCOPE and inside `checks/` or `tests/` (reference: `templates/scope-guard.py`; inactive unless `graph.md` exists at the project root, `AGENT_GRAPH_SCOPE` is set, or `AGENT_GRAPH_ENFORCE=1`).

Ask before publishing, sending, pushing, or spending. Each file has exactly one owning node. Keep a recoverable commit before any risky merge.

## Handoff

After each stage, update `progress.md` (template: `templates/progress.md`) with:

- nodes done, running, and blocked;
- exact output paths;
- graph changes and why;
- open issues;
- the next ready node.

On resume, read graph.md, progress.md, and results.tsv first, then continue from the recorded next node.

## Completion checklist

Before execution, derive a checklist from CHECKS in `checks.md` (template: `templates/checks.md`). Each item must point to observable evidence:

- [ ] Every node's output exists and can be opened.
- [ ] Every gate ran against the saved, committed version.
- [ ] Every failure is fixed or explicitly reported.
- [ ] graph.md matches the nodes that actually ran.

If LIMIT or a blocker stops the run, return a partial status that lists the exact nodes left.

## Delivery

Return OUTPUT, graph.md, checks.md, results.tsv, and progress.md. State what was checked, what passed, and what remains unresolved. Report only measured usage; never infer savings. After review, save a stable graph as a reusable template, or as a Workflow script if it is reused often.

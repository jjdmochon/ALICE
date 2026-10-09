# Graph: <task>

Assumptions: <inputs inferred, with reason>
Limit: <value + unit> · Max parallel: 4

## Nodes
| id | type (code/judgment) | inputs | output | owned files | check | budget |
|---|---|---|---|---|---|---|
| n1 | judgment | sources/... | out/n1.md | out/n1.md | checks/n1.sh | 15 min |

## Edges
- n1 → n3 (n3 consumes out/n1.md)

## Parallel groups
- {n1, n2}

## Decisions
| date | change | reason |
|---|---|---|

# tplan Lifecycle

## Mission Completion

A Mission is `completed` only when every success-critical Task node is completed and
Mission acceptance evidence is satisfied.

If remaining tasks are not worth executing, the Mission is closed under a non-completion
terminal state.

## Mission Statuses

- `active`
- `completed`
- `blocked`
- `budget_exhausted`
- `abandoned`
- `superseded`
- `requires_human`

## Task Statuses

- `pending`
- `active`
- `blocked`
- `completed`
- `paused`
- `pruned`
- `abandoned`
- `superseded`

## Observational State

observational state records facts such as failures, blockers, completed evidence, and
external input.

## Actual Route And Cost Lifecycle

Runtime state changes append lifecycle records to `execution_trace.jsonl`. Related task,
active-node, and Mission-state changes share one logical `commit_id`. Cost observers
append sanitized `span_completed` records separately.

The trace answers what ran and what it cost. It does not turn process activity into
acceptance evidence. After completion or handoff, use
`scripts/render_execution_cost_tree.py` to render `compact`, `standard`, or `audit`
views. Legacy Missions without a trace render as `snapshot_only`; Missions whose trace
began late render as `partial`.

## Decision State

decision state records PM choices such as split, prune, downgrade, abandon, switch, and
close. In advisory mode, decision state changes require approval.

## Graceful Stop

When tplan cannot safely continue, it should stop with `requires_human` rather than
keep trying. This is appropriate when the remaining blocker depends on missing user
intent, authority, acceptance criteria, product judgment, or external information that
the agent cannot infer safely.

The stop report is concise and shown in Chinese by default:

```text
停止报告

当前目标：
...

已尝试：
1. ...
2. ...
3. ...

阻碍：
...

为何不能安全继续：
...

需要人类提供：
...

恢复条件：
...
```

Rules:

- `已尝试` contains at most 3 items.
- `阻碍` names the single core blocker.
- `为何不能安全继续` states the concrete risk of continuing automatically.
- `需要人类提供` is answerable, decidable, or authorizable by a human.
- `恢复条件` names the condition under which an agent can resume.

Runtime effect:

- write a `stop_report` evidence event with English payload keys and Chinese content
- mark the current node `blocked`
- set the Mission status to `requires_human`
- keep `active_task_id` on the blocked node so resumption is local

## Step Logs And Archival

Step logs are local execution history for one Step or active runtime node. They help
resume work, but they do not automatically become evidence.

When a Step, SubTask, or Task completes, pauses for a long time, or closes as pruned,
abandoned, or superseded:

- archive active step logs under `archive/<task_id>/step_logs.jsonl`
- write a short task summary under `archive/<task_id>/summary.md`
- keep only summary-level findings or acceptance-relevant facts in `evidence.jsonl`

Parents consume child summaries and key evidence, not the full child step history.

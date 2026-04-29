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

## Decision State

decision state records PM choices such as split, prune, downgrade, abandon, switch, and
close. In advisory mode, decision state changes require approval.

## Step Logs And Archival

Step logs are local execution history for one Step or active runtime node. They help
resume work, but they do not automatically become evidence.

When a Step, SubTask, or Task completes, pauses for a long time, or closes as pruned,
abandoned, or superseded:

- archive active step logs under `archive/<task_id>/step_logs.jsonl`
- write a short task summary under `archive/<task_id>/summary.md`
- keep only summary-level findings or acceptance-relevant facts in `evidence.jsonl`

Parents consume child summaries and key evidence, not the full child step history.

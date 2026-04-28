# tplan Lifecycle

## Mission Completion

A Mission is `completed` only when every success-critical level-2 Plan Task is
completed and Mission acceptance evidence is satisfied.

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

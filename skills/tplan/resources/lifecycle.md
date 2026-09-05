# tplan Lifecycle

## Mission Completion

A Mission is `completed` only when every success-critical Task node is completed and
Mission acceptance evidence is satisfied.

Each new transition into Mission `completed` checks these prerequisites inside the
existing transaction lock, before the journal is written. Every node marked
`success-critical` must be completed. For each declared Mission acceptance ID, the
latest mechanically qualified observation in evidence-stream order must be
`acceptance_passed` or a complete compatible legacy `acceptance`; a later
`acceptance_failed` blocks closure until a later qualified positive observation.
Existing evidence and same-transaction prepared evidence form one snapshot. Duplicate
IDs and invalid/wrong-scope observations cannot supply qualified acceptance.

The gate checks declared references and pass/fail observations, not deliverable quality
or reviewer correctness. Ordinary Task completion stays lightweight and does not itself
satisfy Mission acceptance. Historical completed records remain readable; new closure
checks do not backfill or certify their past acceptance. Recovery preserves frozen
pending transaction contents rather than applying new semantic judgments to history.

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
append sanitized paired `span_started`/`span_completed` records separately; a platform
that only reports after completion may append a standalone completion.

The trace answers what ran and what it cost. It does not turn process activity into
acceptance evidence. After completion or handoff, use
`scripts/render_execution_cost_tree.py` to render `compact`, `standard`, or `audit`
views. Legacy Missions without a trace render as `snapshot_only`; Missions whose trace
began late render as `partial`.

Every supported writer verifies the immutable `runtime_provenance` before changing
Mission state, evidence, execution trace, step logs, archives, interaction guards, or
telemetry sidecars. New Missions pin the creating runtime. A legacy Mission without
provenance is readable with a warning and is pinned as `legacy_adopted` by its first
supported unguarded mutation. A known incompatible fingerprint fails before any of
those canonical artifacts change. Run `scripts/runtime_doctor.py` when selection is
uncertain; the complete compatibility and recovery contract is in
`runtime-provenance.md`.

Before a new lifecycle transaction is journaled, its `refs.evidence_ids` resolve
uniquely against the locked Mission evidence stream plus that transaction's prepared
events. Artifact paths belong in `artifact_refs`. Historical references remain intact;
only references used by the new transaction must resolve. Reference existence is a
structural property, separate from acceptance sufficiency. Standalone trace append
uses the same resolver under its existing lock. The compatibility `write_mission`
entry delegates updates of an existing Mission to the canonical transaction boundary.
Recovery replays the already-prepared transaction contents rather than reinterpreting
later evidence.

`check_mission.py` reports historical unresolvable references and unsupported current
completion claims as `integrity_warning` diagnostics from one locked snapshot. These
warnings preserve historical files and do not certify their acceptance. Its successful
shape-check exit is separate from the prerequisites for a new completion write.

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

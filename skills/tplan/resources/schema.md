# tplan Schema

## Mission Directory

Each Mission directory contains:

- `mission.json`: machine-readable Mission, Task, SubTask, and Step state.
- `mission.md`: narrative, rationale, and review notes.
- `evidence.jsonl`: append-only evidence event stream. This is not a process log.
- `execution_trace.jsonl`: lifecycle and sanitized execution-cost events. This is not
  acceptance evidence or a raw transcript.
- `.interaction-guard.json`: optional persistent host-interruption guard. It is runtime
  control state, not Mission business schema; an absent file means no guard is open.
- `logs/`: active task-local step logs.
- `archive/`: archived step logs and task summaries when needed.
- `reports/`: generated progressive execution-cost trees and other read-only reports.

Project-level Mission shared context memory lives outside the Mission directory:

- `.tplan/shared_contexts/tplan_mission_shared_context-<mission_id>.md`: primary
  Markdown memory for Mission snapshot, source_contexts, current state, shared risks,
  key findings, and resume notes.

## mission.json

Required top-level fields:

- `schema_version`: must be `tplan.v0.1`.
- `mission`: object containing Mission policy and acceptance evidence.
- `tasks`: list of runtime nodes. Runtime `v0.1` supports `task`, `subtask`, and
  `step` nodes.
- `active_task_id`: task id or null.
- `shared_context`: optional runtime index for the project-level Mission shared
  context file and scoped shared risk signals.

Required Mission fields:

- `id`
- `title`
- `objective`
- `status`
- `human_in_loop`
- `risk_tolerance`
- `resource_sufficiency`
- `acceptance_evidence`

Required runtime node base fields:

- `id`
- `parent_id`
- `kind`: one of `task`, `subtask`, or `step`
- `level`
- `title`
- `status`
- `role`
- `evidence_links`

Mission-aligned `task` fields:

- `mission_contribution`
- `acceptance_evidence`

Parent-aligned `subtask` fields:

- `parent_contribution`
- `parent_acceptance`
- `mission_trace`

Execution-leaf `step` fields:

- `parent_contribution`
- `mission_trace`
- `step_action`
- `done_condition`

SubTasks may include `acceptance_evidence` or `mission_contribution` as optional
context, but ordinary SubTask execution is controlled by parent alignment, not direct
Mission justification. Steps do not own task decomposition decisions.

Supported task depth:

- Mission itself is not counted as a task level.
- `task`: level 1, `parent_id: null`, aligns directly to Mission.
- `subtask`: level 2, parent must be a `task`, aligns directly to that Task.
- `step`: level 2 when directly under a Task, or level 3 when under a SubTask.
- Step nodes are leaves. A Step cannot have children.

Simple tasks may use `Mission -> Task -> Step`. Complex tasks may use
`Mission -> Task -> SubTask -> Step`. Runtime `v0.1` does not support deeper SubTask
nesting yet, but future expansion should extend only the Task/SubTask control layer;
Step remains the stable execution leaf.

Structure changes should go through `scripts/add_node.py` or another runtime script.
Agentic judgment decides what to add and why; scripts own field defaults, shape
normalization, and validation before write.

## Execution Trace Sidecar

The Mission schema remains `tplan.v0.1`; execution telemetry uses the additive
`tplan.execution_trace.v0.1` sidecar. Lifecycle records cover Mission initialization,
dynamic node addition, task status, active node, and Mission status. Cost records use
sanitized `span_started`/`span_completed` pairs for host-observed operations, while a
standalone `span_completed` remains valid for after-the-fact platform telemetry.

Trace coverage is `exact`, `partial`, or `snapshot_only`. Exact lifecycle coverage does
not imply that every platform cost was observable. See `execution-trace.md` for the
span, attribution, privacy, and renderer contracts.

## Interaction Guard Sidecar

When a host can observe an interrupting user message, it opens
`.interaction-guard.json` before handling that message. The guard records a canonical
digest of the complete `mission.json`, an evidence-stream boundary digest, the baseline
active task, a monotonic revision, and opaque message references. The guard protects
future Mission fields by default, rather than maintaining a fragile allowlist of
control fields.

While a guard is open, all public runtime Mission mutations, evidence writes, and the
compatibility Mission writer fail closed unless they are part of a guard resolution.
Task-local operational logs, sanitized execution telemetry, and read-only reports may
continue, but they do not gain user authority. A `resume_original` resolution may close
only if both baseline digests still match and no message remains pending. An authorized
change needs a persisted proposal followed by a newer pending confirmation message, and
a one-time receipt bound to the guard identity, revision, baseline, complete decision
digest, exact mutation digest, and confirmation reference. A raw filesystem writer is
outside this runtime API boundary and needs host sandboxing if it is in scope.

Guard state is included as `guard_after` in the Mission transaction journal. Recovery
rolls Mission, trace, evidence, and guard state forward together. Legacy transaction
`tplan.mission_transaction.v0.1` remains readable; new transactions use v0.2.

The sidecar and dispositions are platform-neutral. Native carriers map their own
message, before-tool, and turn-end events through
`resources/interaction-host-contract.md`. A carrier may use a separate
host-owned runtime marker to distinguish the first prompt of a normal turn from a
second, mid-turn message. That marker contains only opaque platform
and message references, is not Mission business state, and must never be treated as
authority. Native hooks, checkpoint detection, and prompt-only fallback must report
their real enforcement level separately.

## Adaptive Runtime Records

Runtime level changes how much state is materialized, not what `tplan` is allowed to
ignore.

Lite mode minimum state:

- Mission objective
- acceptance criteria
- active node
- latest state
- blocker, evidence, or decision summary when present

Lite startup may be represented as `Mission -> active Task` with no materialized Step.
Use `scripts/init_lite.py` to create that state. The active root Task must cover current
Mission acceptance evidence, and the narrative should carry the latest recoverable
state. A Step is added only after a promotion trigger appears.

`normal` and `strict` may materialize more nodes and review artifacts. `lite` may keep
ordinary execution as task-local logs or notes, but high-impact changes still follow
the same alignment, review, and stop contracts.

Promote an action into a Step only when it needs one of these properties:

- recovery by a future agent
- acceptance or done-condition checking
- rollback or replacement tracking
- evidence reference
- decomposition into multiple actions

Routine actions that do not need these properties should remain below the active
execution boundary as logs or notes.

Task roles:

- `success-critical`: required for Mission completion.
- `supporting`: useful but not part of strict Mission completion.
- `exploratory`: uncertain payoff governed by risk/resource policy.

## Mission Shared Context Memory

Mission shared context Markdown is the primary memory surface. It is stored at:

```text
.tplan/shared_contexts/tplan_mission_shared_context-<mission_id>.md
```

`preflight_mission.py` performs Mission identity startup checks before initialization.
It can report `continue_existing`, `create_new`, or `needs_agentic_selection`.
Mission identity is continuity of objective, acceptance evidence, and authority
boundary. Scripts compare declared metadata only; they do not decide semantic sameness.

`mission.json.shared_context` is the runtime index. When present, it includes:

```json
{
  "shared_context": {
    "project_root": "/path/to/project",
    "context_file": ".tplan/shared_contexts/tplan_mission_shared_context-<mission_id>.md",
    "source_contexts": [],
    "risk_signals": []
  }
}
```

`source_contexts` are background memory used when a new Mission learns from prior
Missions. They are not a Mission status and do not inherit prior acceptance authority.

## Shared Risk Context

Shared Risk Context lets local blockers, degraded conditions, invalid evidence risk,
abnormal cost, or recovery signals influence later risk-adjusted value assessment
without coupling execution units. Execution units do not read each other's task logs.
They publish scoped Mission-level risk signals, and later decision packets consume
active signals.

`mission.json` may include:

```json
{
  "shared_context": {
    "risk_signals": []
  }
}
```

Each risk signal must include:

- `id`
- `source_task_id`
- `scope`
- `signal`
- `severity`
- `confidence`
- `affected_surfaces`
- `value_effect`
- `recommended_gate`
- `recovery_condition`
- `status`
- `created_at`
- `updated_at`

Optional fields include `source_evidence_id`, `supersedes`, and `notes`.

Allowed values:

- `scope`: `shared_environment`, `shared_dependency`, `shared_data`,
  `shared_authority`, `shared_evidence_channel`, `mission_policy`, or `other`
- `severity`: `low`, `medium`, `high`, or `critical`
- `confidence`: `low`, `medium`, `high`, or `unclear`
- `status`: `active`, `resolved`, `superseded`, or `invalidated`

Scripts validate shape, enum values, duplicate risk ids, and `source_task_id` links.
They do not decide whether the risk is real or whether it should change a task's
risk-adjusted value.

## evidence.jsonl

Evidence records observable support for a claim, state change, acceptance condition,
blocker, feedback item, or decision. It should not contain routine step-by-step process
logs.

Sparse evidence categories:

- `acceptance_passed` or `acceptance_failed`
- blocker
- user feedback
- decision
- state transition
- key finding
- risk_context_update
- risk_context_recovery

Each line is one JSON object with:

- `id`
- `timestamp`
- `event_type`
- `summary`
- `task_id`
- `payload`

New qualified acceptance events are fail-closed. Their payload must contain a
non-empty, distinct `acceptance_ids` list; every id must exist in the Mission, and the
event `task_id` must name a node whose own declaration or success-critical ancestor
covers those ids. This validates shape and references only. The Agent or reviewer,
not the script, remains responsible for deciding whether the acceptance claim is true.

Legacy `acceptance` remains readable. A complete legacy record is classified using the
same reference rules; an incomplete one is retained as `unclassified_writeback` with
an audit warning and is never silently upgraded. `decision_applied` is runtime-reserved
and cannot be appended through the public evidence command.

Validated writeback and countable progress are different. Only qualified acceptance
and a runtime-applied path decision count as positive progress. Blockers, failures,
feedback, stops, risk changes, failed acceptance, and unapplied decision recommendations
are constraint deltas. State changes, artifacts, key findings, and unknown event types
remain state or unclassified writeback unless a qualified evidence event is written.

`stop_report` evidence events use English payload keys with Chinese user-facing
content:

- `current_goal`
- `attempts`: 1-3 concise attempts
- `blocking_issue`
- `why_cannot_continue_safely`
- `need_from_human`
- `resume_condition`

## logs/

Active step logs are task-local JSONL files named `<task_id>.jsonl`. Each line is one
JSON object with:

- `id`
- `timestamp`
- `step_id`
- `task_id`
- `summary`
- `payload`

Step logs are working memory for a Step or active runtime node. They are not
automatically included in decision packets and are not proof of acceptance by
themselves.

## archive/

When a task or milestone closes, move its active step log into
`archive/<task_id>/step_logs.jsonl` and write `archive/<task_id>/summary.md`.

The summary should compress the useful result of the steps. Only the summary or key
findings should be promoted into `evidence.jsonl`, and only when they support a parent
claim, acceptance condition, blocker, feedback item, or decision.

## Decision Packet

A decision packet must include:

- Mission objective
- Mission acceptance evidence
- active runtime node and parent chain
- current task tree summary
- relevant evidence events
- risk tolerance
- resource sufficiency
- human-in-loop value
- current blockers or surprises
- shared context with active risk signals and recent resolved risk signals

## Mission Pulse Route Note

`mission_pulse` is an optional route note, not Mission state by default. It gives the
agent a thin Mission-level control surface between Snapshot and Gate:

- Snapshot reports observable state.
- Pulse routes observable signals to an existing Gate.
- Gate makes the semantic decision and owns any mutation.

Pulse v0.2 uses explicit Candidate Collection and Gate Arbitration:

```text
Snapshot -> Candidate Collection -> Candidate Shape Validation -> Gate Arbitration -> Pulse Output -> Gate
```

Required `mission_pulse` fields when used:

- `schema_version`: `tplan.pulse.v0.2`
- `trigger`: `before_continue`, `before_freeze`, `before_handoff`, `before_stop`,
  `checkpoint_batch`, `feedback`, `blocker`, `shared_risk`,
  `active_switch_candidate`, `branch_cleanup`, or `manual`
- `scope`: `active_node`, `subpath`, or `mission`
- `signals`: list of observable signal strings
- `evidence_delta`: `new_evidence_expected`, `weak_evidence_expected`,
  `no_new_evidence_expected`, or `unclear`
- `branch_disposition`: `keep`, `close`, `merge`, `defer`, `prune`, or `unclear`
- `systemic_probe`: `not_needed`, `use_existing_structure`, `replace_local_fix`,
  `needs_gate`, or `unclear`
- `next_gate`: `continue`, `continuation_authorization`, `anti_spiral_audit`,
  `selection`, `subtraction`, `loopback`, `mission_review`, `health_check`, `stop`,
  or `escalate`
- `rationale`: route rationale
- `evidence_links`: list of evidence ids, artifact references, or trace anchors

Decision hook names such as `artifact_value_gain` are not Mission Pulse `next_gate`
values. Pulse routes to existing Gates; those Gates may produce a decision packet that
invokes a semantic hook.

TVG internal outcomes such as `deepen`, `return-remediate`, `block`, and `freeze` are
not tplan `recommendation` enum values. They stay inside the TVG loop unless a separate
Mission-facing decision maps them to `add`, `subtract`, `continue`, `switch`, `close`,
or `escalate`.

Required candidate fields:

- `signal`: observable route signal
- `candidate_next_gate`: existing Gate the signal would route to
- `scope`: `active_node`, `subpath`, or `mission`
- `source_kind`: `trigger`, `mission_state`, `evidence_event`, `step_log`,
  `risk_signal`, `task`, `validation`, or `derived`
- `source_ids`: source record ids when available
- `priority_class`: `requires_human_or_stop`, `mission_boundary`,
  `runtime_integrity`, `active_shared_risk`, `current_blocker_or_feedback`,
  `anti_spiral`, `checkpoint_weak_evidence_delta`, `branch_or_switch_cleanup`,
  or `same_path_continuation`
- `severity`: `low`, `medium`, `high`, or `critical`
- `freshness`: `current_trigger`, `current_state`, `current_path`,
  `checkpoint_window`, `recent_evidence`, `historical`, or `unknown`
- `reason`: route-candidate rationale
- `context`: object for contextual ids such as `risk_signal_ids`, `object_ids`, or
  trigger labels

Pulse outputs are routing notes, not proof. `scripts/mission_pulse.py` and
`survey --pulse --pulse-trigger <trigger>` report pulse trigger candidates with
`script_verdict: shape_only` and `agentic_judgment_required: true`. In `survey --pulse`
output, the full Pulse payload is nested under `survey["pulse"]`.
Scripts must not decide Mission ROI. They also must not decide evidence sufficiency,
defect class, health verdict, branch value, systemic truth, or user authority.

Read-only Pulse script output includes:

- `snapshot`: ordinary Mission survey output.
- `validation_findings`: Mission shape validation findings.
- `recent_evidence_summary`: total evidence event count, counts by event type, last
  event id, and recent event id/type/task/summary rows.
- `active_log_summary`: active task id, active log count, last log id, recent log
  id/step/summary rows, local object touch counts, repeated local objects, and additive
  layering observation.
- `evidence_link_lint`: invalid task `evidence_links` shapes and task links not bound
  to a real evidence event id.
- `review_trigger_candidates`: all mechanically observed signal candidates.
- `winning_candidate`: the selected controlling candidate, or null for ordinary
  `continue`.
- `suppressed_candidates`: observed candidates that lost Gate Arbitration but remain
  visible to the selected Gate.
- `arbitration_trace`: why each candidate was selected or suppressed.
- `mission_pulse`: the route note described above.
- `gate_owner`: the existing gate or hook that owns the selected `next_gate`.
- `pulse_shape_findings`: script self-check findings for the Pulse output shape.

Pulse consumption is explicit, not inferred. `scripts/consume_pulse.py` records that a
candidate has already been handled by a downstream Gate or operator. The current
dedupe memory lives under optional Mission state `pulse_state.consumed_candidates`,
while the append-only audit record is a `pulse_consumed` event in `evidence.jsonl`.

Matching later candidates may include optional fields such as `fingerprint`,
`candidate_state`, `stale_reason`, and `pulse_consumption`. A consumed candidate may be
shown as `candidate_state=stale` when the same source delta repeats without change.
Signals that remain active by design, such as shared risk or same-path continuation,
stay `active` even after a prior consumption record.

`review_trigger_candidates.source_ids` must point to source records when available:
evidence event ids for feedback/blocker/shared-risk signals, step log ids for local
repair or checkpoint-batch signals, and task ids for branch selection signals. Object
ids and risk signal ids live under `context`, but should not replace source record ids.

For checkpoint batches, fresh acceptance evidence movement means an active-task
acceptance event or linked evidence event whose timestamp falls inside the evaluated
checkpoint window. Historical linked evidence alone does not suppress a weak-evidence
route.

`next_gate=continue` never bypasses existing high-impact requirements.
`next_gate=health_check` must route to existing shared-risk/Mission-health judgment
instead of creating a standalone undefined gate. Store Pulse history only if recovery
or audit evidence later proves it is needed.

## Hook Output

Hook output is an evidence-linked recommendation, not proof of semantic correctness.
Scripts validate shape and authority only.

Required fields:

- `recommendation`
- `rationale`
- `confidence`
- `evidence_links`
- `proposed_mutations`
- `requires_human`
- ordinary SubTask/Step decisions: `parent_alignment` and `mission_trace`
- high-impact decisions: `mission_alignment`

High-impact hook outputs should also include `mission_review`:

- `objective_alignment`
- `acceptance_gap`
- `task_contribution`
- `roi_effect`
- `non_action_risk`

High-impact recommendations also require `path_assessment`. This includes selection,
subtraction, loopback, chain-role, active-task switches, Mission closure, escalation,
and high-impact continuation decisions:

- `marginal_roi`: `positive`, `weak`, `negative`, or `unclear`
- `path_role`: `unique_blocker`, `dominant_path`, `one_of_many`, or `unclear`
- `evidence_delta`: `new_evidence_expected`, `weak_evidence_expected`,
  `no_new_evidence_expected`, or `unclear`

When a high-impact hook output is generated while active Shared Risk Context exists,
the output must also include `risk_assessment`:

- `shared_context_used`: list of risk signal ids considered
- `invalid_evidence_risk`: `low`, `medium`, `high`, or `unclear`
- `failure_risk`: `low`, `medium`, `high`, or `unclear`
- `risk_adjusted_value`: `positive`, `weak`, `negative`, or `unclear`
- `next_gate`: `continue`, `health_check`, `switch`, `stop`, or `escalate`

Mission-facing same-path `continue` decisions must include
`continuation_authorization`. This belongs to the Linear Continuation Gate. It should
not split into independent pressure-case-specific lint, rerun, generation, or defect
queue mechanisms.

Required `continuation_authorization` fields:

- `trigger_reasons`: list containing `third_touch`, `repeated_same_path_attempt`,
  `post_continuation_defect`, `repeated_negative_feedback`,
  `high_cost_or_high_blast_radius_continuation`, `weak_or_unclear_evidence_delta`, or
  `manual_authorization`
- `evidence_shape_lint`: `pass`, `fail`, `not_applicable`, or `unclear`
- `defect_classification`: `none`, `acceptance_blocking`, `batchable_detail`, or
  `unclear`
- `expected_evidence_delta`: `new_evidence_expected`, `weak_evidence_expected`,
  `no_new_evidence_expected`, or `unclear`
- `authorized_action`: `continue_same_path`, `targeted_fix`, `batch_details`,
  `mission_review`, `anti_spiral_audit`, or `stop`

Legacy compatibility: older records may still use `second_large_rerun` or
`post_generation_defect`, but new records should use the generic same-path continuation
reasons above.

count-based reminders are triggers, not decisions. Evidence-shape lint is shape-only
evidence: scripts can report placeholder anchors, sample evidence, empty anchors,
template residue, or unbound evidence links, but they must not decide semantic quality
or release readiness.

Runtime scripts validate only the shape and enum values. They do not compute ROI, rank
paths, infer evidence quality, or decide semantic correctness.

`mission_alignment` and `mission_review` keep decisions anchored to Mission
convergence. They are judgment records, not script-verifiable proof of correctness.
`parent_alignment` keeps ordinary SubTask/Step work accountable to its immediate parent while
`mission_trace` preserves lightweight visibility back to the Mission.

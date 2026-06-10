# tplan Schema

## Mission Directory

Each Mission directory contains:

- `mission.json`: machine-readable Mission, Task, SubTask, and Step state.
- `mission.md`: narrative, rationale, and review notes.
- `evidence.jsonl`: append-only evidence event stream. This is not a process log.
- `logs/`: active task-local step logs.
- `archive/`: archived step logs and task summaries when needed.

## mission.json

Required top-level fields:

- `schema_version`: must be `tplan.v0.1`.
- `mission`: object containing Mission policy and acceptance evidence.
- `tasks`: list of runtime nodes. Runtime `v0.1` supports `task`, `subtask`, and
  `step` nodes.
- `active_task_id`: task id or null.
- `shared_context`: optional Mission-level context for scoped shared risk signals.

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

- acceptance passed or failed
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
not split into independent pre-rerun lint and defect queue mechanisms.

Required `continuation_authorization` fields:

- `trigger_reasons`: list containing `third_touch`, `second_large_rerun`,
  `post_generation_defect`, `repeated_negative_feedback`,
  `weak_or_unclear_evidence_delta`, or `manual_authorization`
- `evidence_shape_lint`: `pass`, `fail`, `not_applicable`, or `unclear`
- `defect_classification`: `none`, `acceptance_blocking`, `batchable_detail`, or
  `unclear`
- `expected_evidence_delta`: `new_evidence_expected`, `weak_evidence_expected`,
  `no_new_evidence_expected`, or `unclear`
- `authorized_action`: `continue_same_path`, `targeted_fix`, `batch_details`,
  `mission_review`, `anti_spiral_audit`, or `stop`

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

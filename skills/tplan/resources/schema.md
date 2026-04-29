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

Task roles:

- `success-critical`: required for Mission completion.
- `supporting`: useful but not part of strict Mission completion.
- `exploratory`: uncertain payoff governed by risk/resource policy.

## evidence.jsonl

Evidence records observable support for a claim, state change, acceptance condition,
blocker, feedback item, or decision. It should not contain routine step-by-step process
logs.

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

`mission_alignment` and `mission_review` keep decisions anchored to Mission
convergence. They are judgment records, not script-verifiable proof of correctness.
`parent_alignment` keeps ordinary SubTask/Step work accountable to its immediate parent while
`mission_trace` preserves lightweight visibility back to the Mission.

# tplan Schema

## Mission Directory

Each Mission directory contains:

- `mission.json`: machine-readable Mission and Plan Task state.
- `mission.md`: narrative, rationale, and review notes.
- `evidence.jsonl`: append-only evidence event stream.
- `archive/`: archived branches when needed.

## mission.json

Required top-level fields:

- `schema_version`: must be `tplan.v0.1`.
- `mission`: object containing Mission policy and acceptance evidence.
- `tasks`: list of Plan Tasks.
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

Required Plan Task fields:

- `id`
- `parent_id`
- `level`
- `title`
- `status`
- `role`
- `mission_contribution`
- `acceptance_evidence`
- `evidence_links`

Task roles:

- `success-critical`: required for Mission completion.
- `supporting`: useful but not part of strict Mission completion.
- `exploratory`: uncertain payoff governed by risk/resource policy.

## evidence.jsonl

Each line is one JSON object with:

- `id`
- `timestamp`
- `event_type`
- `summary`
- `task_id`
- `payload`

## Decision Packet

A decision packet must include:

- Mission objective
- Mission acceptance evidence
- active Plan Task and parent chain
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
- `mission_alignment`

High-impact hook outputs should also include `mission_review`:

- `objective_alignment`
- `acceptance_gap`
- `task_contribution`
- `roi_effect`
- `non_action_risk`

`mission_alignment` and `mission_review` keep decisions anchored to Mission
convergence. They are judgment records, not script-verifiable proof of correctness.

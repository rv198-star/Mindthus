# tplan Shared Risk Context Design

Status: draft for user review
Date: 2026-06-10

## Goal

Add a minimal Mission-level shared risk context to `tplan` so local blockers, degraded
conditions, invalid evidence, or recovery signals can influence later task value
assessment without requiring execution units to inspect each other.

The feature should turn relevant local failures into scoped risk signals that decision
packets and hook outputs can consume when judging whether the next action still has
risk-adjusted Mission value.

## Problem

Current `tplan` already has `path_assessment` for high-impact continuation decisions:

- marginal Mission ROI
- path role
- expected evidence delta

That is necessary but incomplete. It evaluates the current path mostly from the active
decision surface. It does not provide a stable Mission-level input for risks discovered
by another execution unit, such as a shared environment failure, a shared dependency
failure, invalid evidence risk, or a recovery signal.

Without a shared risk context, agents can overvalue continuation because the original
task remains important even though the next action is now unlikely to produce valid
evidence. The result is a systematic bias toward "continue because the Mission is
important" instead of "continue only if the next action has risk-adjusted value under
the current context."

## Core Design

Introduce a Mission-level `shared_context.risk_signals` list in `mission.json`.

Execution units do not read each other's task logs or internal state. Instead:

1. A local execution unit records ordinary progress locally.
2. When it observes a blocker, degraded condition, invalid evidence risk, abnormal
   cost, or recovery condition that can affect other units, it publishes a scoped
   risk signal.
3. Later value assessments consume active shared risk signals from the Mission context.
4. Recovery signals can resolve or supersede earlier active risks.

Routine success should not publish a shared risk signal. Acceptance success and recovery
success may publish evidence because they close claims or restore trust in a shared
surface.

## Data Model

`mission.json` gains an optional top-level field:

```json
{
  "shared_context": {
    "risk_signals": []
  }
}
```

Each risk signal is a structured object:

```json
{
  "id": "R1",
  "source_task_id": "T1",
  "source_evidence_id": "E12",
  "scope": "shared_environment",
  "signal": "fsync_unreliable",
  "severity": "high",
  "confidence": "high",
  "affected_surfaces": ["generation", "sqlite", "trace_registry"],
  "value_effect": "Expensive reruns may produce invalid evidence.",
  "recommended_gate": "environment_health_gate",
  "recovery_condition": "dd fsync, sqlite commit, and trace init smoke pass",
  "status": "active",
  "created_at": "2026-06-10T00:00:00+00:00",
  "updated_at": "2026-06-10T00:00:00+00:00"
}
```

Required fields:

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

Optional fields:

- `source_evidence_id`
- `supersedes`
- `notes`

Allowed enum values:

- `scope`: `shared_environment`, `shared_dependency`, `shared_data`, `shared_authority`,
  `shared_evidence_channel`, `mission_policy`, `other`
- `severity`: `low`, `medium`, `high`, `critical`
- `confidence`: `low`, `medium`, `high`, `unclear`
- `status`: `active`, `resolved`, `superseded`, `invalidated`

Scripts validate shape and enum values only. They must not decide whether a risk is
real, whether it applies to a later task, or whether continuation is semantically
correct.

## Evidence Events

Risk signals are also recorded as evidence events so the context remains auditable:

- `risk_context_update`: creates or updates a shared risk signal.
- `risk_context_recovery`: resolves or supersedes an active risk signal.

The evidence event payload should contain the same risk fields or a reference to the
updated risk signal. The Mission state is the live context; `evidence.jsonl` is the
append-only audit trail.

Routine process logs must remain in `logs/`. Do not promote local failures into shared
risk context unless they can affect another task's value assessment.

## Decision Packet

`make_decision_packet.py` should include:

```json
{
  "shared_context": {
    "active_risk_signals": [],
    "recent_resolved_risk_signals": []
  }
}
```

`active_risk_signals` should include active signals from `mission.json`.
`recent_resolved_risk_signals` may include a small recent window of resolved or
superseded signals so agents can see recovery context without scanning all evidence.

Decision packets should continue to include recent evidence events. Shared context is
not a replacement for evidence; it is a risk input for value assessment.

## Hook Output

When a high-impact decision packet includes active shared risk signals, hook output
must include `risk_assessment` in addition to existing `path_assessment`:

```json
{
  "risk_assessment": {
    "shared_context_used": ["R1"],
    "invalid_evidence_risk": "high",
    "failure_risk": "medium",
    "risk_adjusted_value": "weak",
    "next_gate": "health_check"
  }
}
```

Allowed enum values:

- `invalid_evidence_risk`: `low`, `medium`, `high`, `unclear`
- `failure_risk`: `low`, `medium`, `high`, `unclear`
- `risk_adjusted_value`: `positive`, `weak`, `negative`, `unclear`
- `next_gate`: `continue`, `health_check`, `switch`, `stop`, `escalate`

Scripts validate only shape and enum values. Agentic judgment decides whether a signal
is relevant, how much it changes value, and what gate should control the next action.

If hook output ignores active risk signals, it must either leave `shared_context_used`
empty and explain why in `rationale`, or set `risk_adjusted_value` to `unclear`.

## Runtime Script Changes

### `tplan_runtime.py`

Add helpers to:

- normalize and validate `shared_context.risk_signals`
- append or update a risk signal
- resolve a risk signal
- expose active and recently resolved signals in survey and decision packets
- validate `risk_assessment` when active shared risks exist in high-impact decisions

The validation must stay mechanical.

### `record_evidence.py` and `checkpoint.py`

These commands can continue recording normal evidence. For this feature, the preferred
implementation is a dedicated `record_risk_context.py` command so callers do not need
to hand-craft synchronized Mission state plus evidence events.

This design does not add checkpoint forwarding flags. Keep risk-context writes in the
dedicated command to avoid turning checkpoint into a control surface.

### `survey.py`

Survey output should include:

- active risk signal count
- highest active severity
- active risk signal summaries in JSON mode

Plain output should stay compact.

### `apply_decision.py`

`apply_decision.py` should validate `risk_assessment` when all are true:

- the decision is high-impact, or already requires `path_assessment`
- active shared risk signals exist in Mission context
- the recommendation could continue, switch, close, or otherwise claim Mission progress

The script must not block continuation based on risk values. It only requires the
decision to expose the risk-adjusted value judgment.

## WAE Boundary

Workflow controls:

- risk signal object shape
- allowed enum values
- whether active risk context appears in survey and decision packets
- whether high-impact hook outputs include `risk_assessment` when active risks exist

Agentic judgment controls:

- whether a local failure deserves shared context publication
- whether a shared risk applies to the active task
- how the risk changes adjusted value
- whether the next gate is continuation, health check, switch, stop, or escalation

Evidence controls:

- whether the risk signal is supported by observable facts
- whether recovery evidence is strong enough to resolve the signal
- whether claim confidence should be capped

Scripts must not infer semantic truth, compute risk-adjusted value, rank tasks, or
decide that a Mission should stop.

## Out Of Scope

- No automatic risk scoring engine.
- No cross-task log search by execution units.
- No automatic task reprioritization.
- No event bus or background monitor.
- No change to existing task tree depth rules.
- No requirement to record routine success.

## Acceptance Criteria

- Mission schema accepts optional `shared_context.risk_signals`.
- Invalid risk signal shape is rejected by `check_mission.py`.
- A new script can record a risk signal and write a corresponding evidence event.
- A new script path can resolve or supersede a risk signal with recovery evidence.
- `survey.py --json` exposes active shared risk signals.
- `make_decision_packet.py` includes active shared risk signals.
- High-impact decisions with active shared risks require valid `risk_assessment`.
- Low-impact parent-aligned child decisions remain valid without `risk_assessment`.
- Docs explain that shared risk context changes risk-adjusted value assessment without
  allowing execution units to read each other's internal logs.

## Test Plan

Add focused tests under `tests/tplan/`:

- `test_check_mission_accepts_valid_shared_risk_context`
- `test_check_mission_rejects_invalid_shared_risk_signal_enum`
- `test_record_risk_context_creates_signal_and_evidence_event`
- `test_resolve_risk_context_marks_signal_resolved_and_records_recovery`
- `test_survey_and_packet_include_active_risk_context`
- `test_high_impact_decision_requires_risk_assessment_when_active_risk_exists`
- `test_low_impact_child_decision_does_not_require_risk_assessment`

Update contract tests so `SKILL.md`, `schema.md`, `hooks.md`, and
`docs/methodologies/tplan.md` mention shared risk context, risk-adjusted value, and
the no cross-task inspection boundary.

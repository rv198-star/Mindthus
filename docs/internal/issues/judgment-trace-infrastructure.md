# Judgment Trace Infrastructure / 判断轨迹基础设施

Status: Implemented (initial v1)
Priority: P0
Execution: Complete for the first production slice

## Problem

Mindthus can validate skill contracts, routing behavior, fidelity, and selected benchmark outputs, but it does not yet have one small, stable representation of a judgment event.

Without that representation, it is difficult to answer:

- why a route or judgment owner was selected;
- which evidence ceiling constrained the answer;
- whether Mindthus changed the action, risk posture, evidence requirement, or stop condition;
- whether two tests protect the same behavior;
- whether a contributed failure case is comparable with an existing benchmark case.

The trace must not become a hidden chain-of-thought format or a raw conversation log.

## Core Decision

Create a lightweight `Judgment Trace` contract for observable judgment decisions.

The contract records externally inspectable decision facts and deltas, not private reasoning transcripts.

TPlan runtime state remains separate. A TPlan decision hook may reference a judgment trace, but TPlan mission, task, checkpoint, evidence, telemetry, and recovery records do not move into this schema.

## Initial Scope

Define a versioned trace shape covering:

```yaml
schema_version: mindthus.judgment-trace.v1
trace_id: string
timestamp: optional

input_shape:
  judgment_object: optional enum
  hard_judgment_point: boolean
  frame_status: optional enum
  active_constraints: optional list

routing:
  judgment_owner: optional enum
  selected_method: optional enum
  routing_decision: direct_execute | acquire_information | intervene | block | stop
  supporting_primitives: optional list

evidence:
  available_evidence_classes: optional list
  missing_evidence_classes: optional list
  claim_ceiling: optional string

decision_delta:
  strategy_changed: boolean
  risk_handling_changed: boolean
  evidence_requirement_changed: boolean
  next_action_changed: boolean
  stopping_condition_changed: boolean
  handoff_changed: boolean

outcome:
  status: not_evaluated | accepted | rejected | inconclusive
  validator_status: optional
  benchmark_case_id: optional
```

The exact enums and required fields must be decided through implementation and fixture review rather than copied mechanically from this draft.

## Mainline Work

1. Inventory current trace-like fields in routing, fidelity, benchmark, and runtime logging code.
2. Identify the minimum common observable fields; do not merge unrelated telemetry merely because it exists.
3. Publish a versioned schema and two or three canonical fixtures.
4. Add shape validation.
5. Integrate one narrow producer first, preferably the judgment benchmark runner or `using-mindthus` fidelity path.
6. Add adapters only where the trace changes downstream usefulness.
7. Document the explicit boundary with TPlan runtime records.

## Guardrails

- Do not store hidden chain of thought.
- Do not require raw user prompts or full answers in the core trace.
- Do not claim semantic correctness because a trace validates structurally.
- Do not make every field mandatory.
- Do not force all skills to emit the same method-specific details.
- Do not unify TPlan execution traces with judgment traces.

## Implementation Result

Implemented on 2026-08-06:

- executable contract and validator under `skills/_runtime/judgment/trace.py`;
- machine-readable schema under `skills/_runtime/judgment/resources/`;
- canonical direct-execution, information-acquisition, and intervention fixtures;
- `scripts/validate-judgment-trace.py` for local shape validation;
- conservative benchmark adapter in `skills/_runtime/judgment/benchmark.py`;
- automatic per-case trace emission from `scripts/run-judgment-benchmark-cli.py`;
- explicit observable-fact, evaluator-label, annotation, and TPlan boundaries in
  `docs/internal/judgment-trace.md`;
- release-package and runtime-fingerprint coverage.

The implementation deliberately does not make every skill emit a trace. The benchmark
runner is the first narrow producer; future producers require downstream value rather
than schema uniformity for its own sake.

## Acceptance Criteria

- [x] A versioned Judgment Trace schema exists.
- [x] Three fixtures cover direct execution, information acquisition, and Mindthus intervention.
- [x] A validator rejects malformed shapes without claiming the judgment is correct.
- [x] An existing benchmark path emits the trace.
- [x] Documentation distinguishes observable facts, evaluator labels, and optional annotations.
- [x] TPlan separation is tested and documented as a reference-only integration boundary.
- [x] The first implementation requires no centralized telemetry.

## Dependencies

None for schema discovery.

The Case Export Contract should consume this contract where useful, but may start its privacy and packaging design in parallel.

## Non-goals

- Centralized log collection.
- Full execution telemetry unification.
- TPlan state migration.
- Automatic truth evaluation.
- Capturing private reasoning transcripts.

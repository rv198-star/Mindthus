# tplan Linear Continuation Gate Design

Status: approved design for implementation planning
Date: 2026-05-09

## Goal

Add a small `tplan` control improvement that challenges linear continuation when the
current path may no longer be worth pursuing.

The change replaces vague "too long" reasoning with three explicit judgment surfaces:

- marginal Mission ROI of continuing on the same path
- whether the current path is unique, dominant, one of many, or unclear
- whether the next action is expected to produce new evidence

This is a light runtime version. It adds required hook output structure and shape
validation, but it does not add a new standalone hook or ask scripts to decide semantic
truth.

## Problem

Agents often keep working on one chain because the chain still looks technically
possible. They change tools, restate the task, or try another bridge while the Mission
value of the next attempt quietly falls.

The problem is not duration by itself. "Too long" is not a stable qualitative
criterion. A long path may be correct if it is the unique blocker and still has
positive marginal ROI. A short path may already be wasteful if it is one of many
options and the next attempt will not produce new evidence.

The underlying failure is linear continuation without a Mission-relative path
assessment:

- the current path's marginal ROI is weak, negative, or unclear
- the current path is treated as unique without comparing alternatives
- repeated attempts create little or no new evidence
- a process-looking chain substitutes for actual judgment

## Scope

### In Scope

- Add `path_assessment` to high-impact hook output requirements.
- Document the WAE boundary for `path_assessment`.
- Update `tplan` guidance so agents challenge linear continuation by ROI, path role,
  and evidence delta rather than elapsed time.
- Extend runtime validation to check `path_assessment` shape and enum values when it
  is required.
- Add focused tests for validation and hook contract text.

### Out Of Scope

- No new `linear_continuation` hook in this version.
- No automatic ROI scoring engine.
- No script-level judgment about whether ROI is truly positive.
- No automatic path alternative discovery.
- No changes to Mission or task state schemas beyond hook output validation.

## WAE Boundary

This version deliberately keeps control split across Workflow, Agentic, and Evidence
layers.

Workflow controls only the structure:

- whether `path_assessment` is present for required hooks
- whether required keys exist
- whether values are in allowed enums
- whether evidence links remain structurally valid under existing validation rules

Agentic judgment controls the substance:

- whether marginal Mission ROI is actually positive
- whether the path is unique, dominant, one of many, or unclear
- whether the next action is likely to generate meaningful new evidence
- whether to continue, switch, subtract, loop back, escalate, or stop

Evidence controls confidence:

- path claims must be tied to evidence links or explicitly marked uncertain
- missing or weak evidence should cap confidence in the recommendation
- evidence that does not constrain the path claim should not be treated as proof

Scripts must not turn a filled `path_assessment` into permission to continue. The
field is a reasoning surface, not proof.

## Path Assessment

High-impact hook outputs add:

```json
{
  "path_assessment": {
    "marginal_roi": "positive | weak | negative | unclear",
    "path_role": "unique_blocker | dominant_path | one_of_many | unclear",
    "evidence_delta": "new_evidence_expected | weak_evidence_expected | no_new_evidence_expected | unclear"
  }
}
```

Meaning:

- `marginal_roi`: expected incremental Mission value of another same-path action.
- `path_role`: whether the current path is necessary, preferred, substitutable, or
  unresolved.
- `evidence_delta`: whether the next action is expected to add evidence that can change
  a decision or reduce uncertainty.

Allowed values are intentionally coarse. The goal is to force the judgment into view,
not to pretend precision exists.

## Required Hooks

`path_assessment` is required for high-impact recommendations, including:

- `selection`
- `subtraction`
- `loopback`
- `chain_role`
- active-task switches
- Mission closure
- escalation
- any `continue` recommendation that is high-impact

It is optional for ordinary parent-aligned SubTask or Step decisions unless the decision
continues a same-path effort after failure, contradiction, low value, or repeated local
expansion.

High-impact remains defined by existing `tplan` rules: adding or removing
success-critical tasks, switching active task, closing Mission, resource-driven
subtraction, problem-definition loopback, or expanding the same supporting/exploratory
branch more than once.

## Decision Rules

The gate does not forbid continuation. It makes weak continuation explain itself.

Rules for agentic judgment:

- If `marginal_roi` is `weak`, `negative`, or `unclear`, do not continue linearly
  without explaining why switch, loopback, subtraction, escalation, or stop is worse.
- If `path_role` is `one_of_many` or `unclear`, compare alternatives before treating
  the current path as the next active path.
- If `evidence_delta` is `no_new_evidence_expected` or `unclear`, do not describe the
  next action as verification unless it can produce decision-constraining evidence.
- If all three fields are weak or unclear, prefer loopback, subtraction, escalation, or
  a stop report over another same-path attempt.

Recommended continuation shape:

- Continue when `marginal_roi=positive`, `path_role` is `unique_blocker` or
  `dominant_path`, and `evidence_delta=new_evidence_expected`.
- Switch or compare alternatives when the current path is `one_of_many`.
- Loop back when path role and ROI are unclear because the problem definition may be
  wrong.
- Stop or escalate when required judgment, authority, or acceptance criteria are
  missing.

## Runtime Validation

Runtime validation should stay mechanical.

The implementation should:

- define allowed enum sets for `path_assessment`
- detect whether a hook output requires `path_assessment`
- validate object shape and enum values
- keep existing high-impact `mission_alignment` and `mission_review` validation
- reject malformed required `path_assessment`
- accept valid `path_assessment` without interpreting whether it is semantically true

Validation should not:

- compute ROI
- rank paths
- infer evidence quality
- decide whether a continuation recommendation is correct

## Documentation Updates

Update `skills/tplan/SKILL.md` with a short Linear Continuation Gate section:

> `tplan` does not stop because work has taken too long. It challenges same-path
> continuation when marginal Mission ROI, path dominance, or expected evidence delta is
> weak or unclear.

Update `skills/tplan/resources/hooks.md` with the required hook list, field schema, WAE
boundary, and decision rules.

Update `skills/tplan/resources/schema.md` so hook output requirements include
`path_assessment` for high-impact decisions.

Update `skills/tplan/templates/hook-output.json` to include a valid example.

## Tests

Add focused tests rather than a broad new benchmark.

Validation tests:

- required high-impact hook output without `path_assessment` is rejected
- malformed `path_assessment` object is rejected
- unsupported enum values are rejected
- valid `path_assessment` is accepted
- ordinary low-impact parent-aligned decisions do not require `path_assessment`

Contract tests:

- `tplan` docs mention marginal ROI, path role, and evidence delta
- hook docs state that elapsed time is not the root criterion
- docs state scripts validate shape only and do not judge semantic correctness

Pressure-test prompt update:

- add a scenario where the agent faces a same-path failure and must choose between
  another attempt, switching path, loopback, subtraction, or stop report
- score whether the agent uses `path_assessment` to avoid treating the current chain as
  uniquely correct without evidence

## Non-Goals And Risks

This version can still produce thin judgment if the agent fills the fields with generic
language. That is a bounded artifact value-gain risk, not a schema problem. Use a TVG
value-gain exit check or human review when `path_assessment` is formally valid but does
not constrain the decision.

The field may create extra friction in simple work. To control this, it is required only
for high-impact hooks and high-impact continuation. Ordinary Step execution remains
parent-aligned unless same-path continuation becomes a Mission-control risk.

## Implementation Plan Targets

The implementation plan should likely touch:

- `skills/tplan/SKILL.md`
- `skills/tplan/resources/hooks.md`
- `skills/tplan/resources/schema.md`
- `skills/tplan/templates/hook-output.json`
- `skills/tplan/scripts/tplan_runtime.py`
- `tests/tplan/test_validate_decision.py`
- `tests/tplan/test_apply_decision.py` or a new focused validation test
- `tests/tplan/test_skill_contract.py`
- `tests/tplan/long_task_ab_tests.md` or another pressure-test doc

Keep the first implementation narrow. If repeated use shows the gate is central enough,
a later version can promote it into a standalone `linear_continuation` hook.

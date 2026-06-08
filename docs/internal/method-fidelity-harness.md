# Method Fidelity Harness / 方法忠实执行护栏

## Status

Internal maintainer design note for `v0.9`.

`v0.9` is the Pre-1.0 engineering validation release. It should prove that Mindthus can
enforce and verify faithful execution of structured judgment discipline before the
project declares `v1.0`.

## Core Claim

Method Fidelity Harness should control faithful execution, not agent judgment freedom.

Short rule:

> 约束关键判断动作，不约束判断结论。

The harness should make it harder for a model to skip required judgment moves, fill a
beautiful but hollow template, or pretend a method was followed. It must not force the
agent into a predetermined conclusion, fixed reasoning path, or over-narrow output
shape.

## Current Diagnosis

Mindthus already has three separate validation styles:

- `tplan`: strong runtime shape validation for Mission state and decision hook output.
- `3L5S`: Markdown heuristic checking for shape and evidence risks.
- `TVG`: trace schema validation for bookkeeping.

These are valuable but split. `SELA`, `EDSP`, `WAE`, and `MPG` still rely mostly on
prompt discipline and contract tests. The v0.9 problem is not "there is no validation";
it is that validation is inconsistent, four methods lack runtime fidelity support, and
there is no shared language for what a validator is allowed to claim.

## Control Boundary

### Shape Validation

Shape validation may check:

- required judgment moves are present
- required fields exist
- field values have the expected type
- enum values are known
- evidence links or evidence surfaces are named when required
- explicit failure criteria were answered
- `not_applicable`, `transfer`, or `challenge premise` exits are declared when a move
  should not be performed

Shape validation must produce review risk, not truth validation. A shape pass is not
semantic approval. Short form: shape pass is not semantic approval.

### Semantic Judgment

Layer name: `semantic judgment`.

Semantic judgment remains with the agent, a judge rubric, or a human reviewer. It
decides whether a comparison is fair, whether an efficiency trend is real, whether a
mainline survives path volatility, or whether a strategy is actually worth taking.

scripts must not decide semantic truth. They may surface omissions, invalid structure,
unsupported enums, missing evidence surfaces, or suspiciously empty moves.

### Required Exits

Every method-level fidelity contract must allow the agent to reject the method when it
does not fit. At minimum it needs:

- `not_applicable`: the method was invoked, but the active object does not fit.
- `transfer`: another Mindthus skill owns the active judgment.
- `challenge premise`: the user or task framing contains a faulty assumption.

This prevents the harness from becoming a pipeline that silently overrides judgment.

## Report Contract

All mechanical validators should converge on the same user-facing meaning:

> Shape & Evidence Risk Report

The report exposes:

- what was checked
- what is missing or malformed
- which required judgment move is affected
- whether the issue is `info`, `warn`, `risk`, or `block`
- what evidence surface is missing or weak
- the reminder that agentic audit remains required

It must not print approval tokens, "the conclusion is correct", or any equivalent
claim that a script has approved the conclusion.

## Route

Use 先 B 后 A:

1. Build the `SELA pilot`: contract, shape validator, casebook, and judge rubric.
2. Build the `MPG second-method pilot`: prove the harness transfers to path-volatility
   reasoning without destroying Human-Readable First or Reasoning Durability.
3. Define the shared Shape & Evidence Risk Report contract.
4. Perform core extraction only after the two pilots expose a stable abstraction.
5. Align existing `3L5S` and `TVG` validators with the report contract.
6. Add fidelity contracts for remaining method surfaces.
7. Run v0.9 acceptance and a conservative v1.0 readiness audit.

## Non-Goals

- Do not rewrite `tplan` first. It is the strongest validated runtime asset.
- Do not force every method into JSON.
- Do not require visible internal fields in ordinary user answers.
- Do not let validator output replace method judgment.
- Do not score a method by whether it reaches the maintainer's preferred conclusion.

## v1.0 Gate

Mindthus can claim `v1.0` only after v0.9 shows that the harness:

- improves faithful execution on at least two methods
- preserves agent freedom to challenge premises, transfer methods, and choose conclusions
- produces reproducible evidence instead of prettier method pages
- keeps scripts inside shape validation and evidence-risk reporting
- avoids over-constraining the very skills it is meant to protect

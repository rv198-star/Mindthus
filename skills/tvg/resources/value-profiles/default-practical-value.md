# Default Practical-Value Profile

```yaml
value_profile:
  mode: default
  name: default practical-value profile
  artifact_job: increase practical thinking value for the module's actual downstream use
```

## Core

This profile is the fallback when no supplied or project default profile is active.

It preserves TVG's ordinary value model: a module should become more useful for
decision, action, review, reuse, handoff, and execution without becoming longer,
more ceremonial, or more confident than its evidence allows.

## Good Means

- clearer decision / action leverage
- evidence honesty
- handoff usability
- risk reduction
- reuse without overfitting
- execution readiness
- grounded insight that changes understanding, judgment, expression, or action
- value density relative to reading burden

## Bad Means

- more text without more usable judgment
- ornamental structure that hides thin thinking
- generic completeness that still leaves downstream invention
- claims that exceed evidence
- uncertainty hidden under cleaner prose
- local case tuning that weakens reuse
- process weight that costs more than the value gained

## Priority Order

1. Evidence honesty and explicit constraints.
2. Downstream usability.
3. Decision / action leverage.
4. Risk reduction and misuse prevention.
5. Reuse without overfitting.
6. Execution readiness.
7. Value density.

## Derived Axes

- `judgment-depth`
- `evidence-depth`
- `downstream-depth`
- `failure-depth`
- `generalization-depth`
- `anti-demo-depth`
- `execution-depth`

## Veto Constraints

- must not freeze if claims exceed the available evidence
- must not freeze if required downstream truth is hidden or left for the next user to infer
- must not freeze if a named unacceptable state remains triggered

## Prompt Self-Audit Questions

`prompt_self_audit_questions`:

1. Does the artifact improve decision, action, review, reuse, handoff, or execution value for its actual downstream use?
2. Does it make evidence boundaries, assumptions, and review-bound uncertainty visible?
3. Does it avoid adding ornamental structure or length without practical value?
4. Would a downstream user still need to invent critical truth before acting?

## Image Self-Audit Questions

`image_self_audit_questions`:

1. If this profile is used for visual artifacts, does the image serve the stated downstream job rather than only looking polished?
2. Are claims about visual accuracy, quality, or representativeness kept within the available evidence?
3. Does the visual reduce handoff ambiguity without hiding important uncertainty?

## Evidence Basis

- TVG core method definition
- existing TVG value-gain types
- existing TVG exit audit and veto-constraint discipline

## Source Notes

`source_notes`:

- This default profile is derived from the TVG core method itself.
- It is the fallback when no supplied or project default profile is active.

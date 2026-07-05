# Aspect Ownership Matrix / 切面主导权矩阵

Aspect Ownership is a cross-primitive arbitration contract. Multiple cognitive
primitives may activate at the same join point, but their conclusions must not be
averaged into a polite, toothless answer.

## Core Rule

> Choose one `judgment_owner` for the visible first thesis. Other active
> primitives may remain as support, constraints, evidence boundaries, or wording
> checks, but they must not dilute the core judgment.

## Aspect Roles

- `judgment_owner`: can own the visible first thesis for a declared scope.
- `constraint`: limits evidence, authority, risk, wording, or exit conditions.
- `support`: shapes route input, exposes hidden variables, or helps another owner.

Each primitive may declare:

- `aspect_role`: `judgment_owner`, `constraint`, or `support`
- `ownership_scope`: what it can own, such as `formal_answer_thesis`,
  `definition_authority`, `decision_target`, `evidence_ceiling`, or `output_shape`
- `exclusive_with`: which other primitives compete over the same thesis scope
- `owns_when` / `defer_when`: when it claims or yields judgment ownership
- `degrade_to`: how it remains useful after losing ownership

Only `judgment_owner` primitives that claim overlapping ownership scopes and list
each other in `exclusive_with` require a main-judgment choice. Constraint and support
primitives stay active as evidence, boundary, wording, or validation support.

## Aspect Aggregation Ban / 切面合计禁令

> Do not average multiple aspect outputs into a balanced but toothless answer.
> Choose one `judgment_owner` for the visible first thesis; degrade other
> judgment-owning aspects to support probes unless the user asked two distinct
> questions.

Fairness is not 50/50 allocation: state the high-weight/global thesis first,
then add boundary repairs without giving them equal judgment weight.

The first sentence belongs to the judgment owner. Other active primitives may change
evidence requirements, boundaries, risk wording, or failure conditions, but they must
not dilute the core judgment into "each side has a point" by default.

A boundary note earns thesis weight only if it changes the result controller,
decision target, evidence ceiling, or definition authority.

## Boundary

This matrix is not a new central router and not a semantic judge. It only prevents
cross-cutting primitives from fighting over the same visible thesis.

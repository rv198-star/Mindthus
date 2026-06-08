# SELA Fidelity Contract

This contract supports the v0.9 Method Fidelity Harness.

It checks whether SELA performed its required judgment moves. It does not decide
whether the final strategic conclusion is true.

Short rule:

> required judgment moves are mandatory; conclusions remain agentic.

## Output Shape

Use `templates/fidelity-output.json` when a SELA run needs runtime validation.

Required top-level fields for an applicable SELA run:

- `schema_version`: `sela-fidelity-v0.1`
- `method`: `SELA`
- `applicability`: `applicable`
- `plain_language_conclusion`
- `action_posture`: `commit`, `trial`, `hold`, `wait`, `stage`, `dual_track`,
  `reject`, `transfer`, or `unclear`
- `required_judgment_moves`

Required judgment moves:

- `fair_comparison_check`
- `local_advantage_scalability`
- `system_efficiency_trajectory`
- `hard_boundary_check`
- `timing_action_posture`
- `misuse_challenge`

Each move must include:

- `status`: `addressed`, `not_applicable`, `transfer`, or `challenge_premise`
- `finding`
- `failure_criteria_response`
- `evidence_surface`

## Failure Criteria

- If the answer accepts `best-A vs average-B` without rebuilding the comparison,
  `fair_comparison_check` fails.
- If it praises local excellence without asking whether it scales,
  `local_advantage_scalability` fails.
- If it states "system efficiency wins" without naming the time curve,
  `system_efficiency_trajectory` fails.
- If irreversible harm, dignity, safety, or legal/medical authority can dominate but is
  not named, `hard_boundary_check` fails.
- If it jumps from trend to action without `commit / trial / hold / wait / stage /
  dual_track / reject / transfer`, `timing_action_posture` fails.
- If it follows a user's SELA misuse without naming the misuse,
  `misuse_challenge` fails.

## Exits

SELA fidelity must allow the agent to reject the method.

When `applicability` is `not_applicable`, `transfer`, or `challenge_premise`, the output
may omit `required_judgment_moves`, but it must include:

- `plain_language_conclusion`
- `exit_reason`
- optional `transfer_to`

## Script Boundary

`scripts/validate_sela_output.py` emits a `SELA Shape & Evidence Risk Report`.

The report can block missing fields, unsupported enum values, empty moves, or missing
failure-criteria responses. It cannot decide strategy quality, trend truth, timing
truth, or whether a SELA conclusion is correct.

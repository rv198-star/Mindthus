# v0.9 Method Fidelity Harness Acceptance

Date: 2026-06-08
Status: Pre-1.0 acceptance record

This record treats v0.9 as a Method Fidelity Harness milestone, not as the final v1.0
claim. The implementation target is to constrain key judgment actions, not judgment
conclusions.

## Scope

v0.9 covers the engineering shape of method fidelity:

- #17 defines the Method Fidelity Harness boundary and keeps scripts away from semantic
  truth decisions.
- #18 records a SELA fidelity pilot casebook and baseline.
- #19 adds the SELA output contract and shape validator.
- #20 adds the SELA judge rubric and baseline-vs-constrained evaluation loop.
- #21 adds MPG as the second-method pilot so the harness is not fitted only to SELA.
- #22 defines the shared Shape & Evidence Risk Report contract.
- #23 extracts the shared fidelity core after the SELA and MPG pilots.
- #24 completes 3L5S and TVG validator alignment with the shared report contract.
- #25 adds fidelity contracts for EDSP, WAE, TVG, 3L5S, and using-mindthus.

The milestone explicitly includes SELA and MPG pilots, 3L5S and TVG validator alignment,
and the shared fidelity core.

## anti-overconstraint audit

The harness must not turn Mindthus methods into rigid answer machines. Its guardrails are:

- shape pass is not semantic approval.
- validator semantic approval forbidden.
- validators may require required judgment actions, missing-field failures, and report
  shape, but must not decide whether the final strategic conclusion is true.
- method contracts must preserve exits such as not applicable, transfer, stop, and
  challenge premise.
- AQM-style hypothetical numbers can expose relationships, but cannot compute or prove
  the decision.
- This milestone does not claim cross-model robustness.

## Readiness

v1.0 readiness: not yet.

Before v1.0, the project still needs a reviewed release cut, broader live-behavior
checks, and evidence that fidelity constraints improve execution without narrowing the
agent's necessary judgment space.

## Verification

Required verification for this acceptance record:

- `python3 -m unittest discover -s tests -v`
- `git diff --check`


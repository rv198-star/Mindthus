# v1.0 Readiness Blocker Closure

Date: 2026-06-08

Status: local readiness work, not a pushed release.

This record closes the four known v1.0 blockers after the v0.9 Method Fidelity Harness
merge. It does not tag or publish v1.0.

## Closed Items

- Licensing: repository now uses AGPLv3 + commercial dual licensing, with `LICENSE`,
  `COMMERCIAL-LICENSE.md`, README summary, and release-pack inclusion.
- Judge automation: `scripts/run-fidelity-judge.py` generates reproducible judge prompts
  and validates completed judge JSON records.
- Escape-review abuse control: `skills/sela/rubrics/judge.md` and the judge runner require
  explicit `escape_review` when output uses `not_applicable`, `transfer`, or
  `challenge_premise`.
- Cross-model baseline: `tests/sela/cross_model_baseline_2026-06-08.md` records a second
  model route, `opencode/deepseek-v4-flash-free`, against the existing v0.9 SELA packet.

## Remaining Release Action

The final push / tag / release action is intentionally deferred.

Before publishing v1.0, rerun full verification from the final branch state and decide
whether to update release metadata, release notes, and package version labels.

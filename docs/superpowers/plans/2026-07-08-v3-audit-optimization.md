# V3 Audit Optimization Execution Record

Goal: convert the v3 external audit feedback into narrow, test-backed router,
output-shape, measurement, and runtime-fingerprint improvements without certifying v3
as passing or rewriting the public 50-case prompts.

## Completed Scope

- Added a thin `Entry Triage / 入口分诊` index to `skills/using-mindthus/SKILL.md`
  while keeping the entrypoint under its 11KiB / 1100-word budget.
- Moved the full v3 trigger families, output gates, EDSP/SELA tie-break, and AQM
  ownership rules into `docs/methodologies/primitives/entry-triage.md`.
- Registered `entry_triage` in `scripts/primitives/manifest.json` so before-route
  primitive activation exposes it as a shape-only reminder.
- Added static contract tests in `tests/test_v3_audit_optimization_contract.py`.
- Updated primitive activation tests for the new before-route primitive.
- Added v4 measurement follow-up notes to the external audit handoff: judge
  calibration, repeat-run cases, fixture diff explanation, judge/blind setup, baseline
  command identity, and shadow-set veto policy.
- Fixed `scripts/log-mindthus-runtime.py` so `--codex-home` derives default
  marketplace/cache roots from the explicit home instead of the process default home.

## Verification

- `python3 -m unittest tests.test_log_mindthus_runtime tests.test_mindthus_router_contract tests.test_packaging_docs tests.test_v3_audit_optimization_contract tests.test_primitive_activation -q`
- `python3 -m unittest discover -s tests -q`
- `python3 -m pytest -q`
- `python3 scripts/build-release-pack.py --package plugins --out /tmp/mindthus-v3-audit-optimization-pack --force`
- `python3 scripts/log-mindthus-runtime.py --repo-root . --marketplace-root /tmp/mindthus-v3-audit-optimization-pack/codex-plugin/mindthus --codex-home /tmp/codex-mindthus-audit-opt-home --json --strict`

## Non-Goals

- No v4 benchmark run was executed in this pass.
- No public benchmark prompt text was changed.
- No claim is made that v3 now satisfies the positive mean threshold.

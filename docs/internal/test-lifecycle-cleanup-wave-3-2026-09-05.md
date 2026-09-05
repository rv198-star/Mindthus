# Test Lifecycle Cleanup Wave 3 — 2026-09-05

Parent #167, work item #170. This slice completes the planned ownership cleanup after
#171/#172 split work landed on main. It moves current contracts out of the historical
v1.0 readiness owner; it does not retire the historical evidence itself.

## Ownership moves

| Previous owner | Contract moved to | Why |
|---|---|---|
| `V10ReadinessTests.test_codex_install_doc_no_longer_calls_public_repo_private` | `PackagingDocsTests.test_codex_install_doc_names_tplan` | Codex install documentation is a current packaging/install surface, not v1.0 history. |
| `V10ReadinessTests.test_agpl_dual_license_surface_is_declared` | `ReleaseBoundaryContractTests.test_dual_license_public_boundary_is_declared` | Licensing is a current release/public boundary and must not depend on a historical readiness suite. |
| v1.0 SELA judge rubric/exit tests plus local judge fixture helpers | `SelaFidelityTests` | Judge behavior is the current SELA fidelity owner. The same complete, blocked-exit, and reviewed-exit behaviors remain executable. |

`tests/test_v1_0_readiness.py` now protects only two historical artifacts: the dated v1.0
readiness closure record and the dated cross-model baseline scope. Its lifecycle remains
`historical_guard`.

## What was deliberately not consolidated

- Whole Elephant/router/primitive tests share vocabulary but protect different layers:
  documentation/routing contracts, deterministic primitive activation, and direct
  Whole-Elephant validation. Shared strings are not retirement evidence.
- SRA contract/domain/runtime-lifecycle tests overlap field names but protect different
  failure classes and are kept after the v0.3 contract repairs.
- TPlan authority, transaction, recovery, privacy, telemetry and provenance tests remain
  active gates and were not trimmed during module extraction.

## Exit decision for #170

The cleanup goal is ownership clarity and lower duplicate maintenance, not an arbitrary
file/test-count target. Waves 1–3 have now:

1. removed duplicate current-release assertions from historical readiness owners;
2. collapsed redundant release-package builds while preserving exact path checks with
   fault-injection coverage;
3. returned install, licensing, and SELA judge contracts to their current owners;
4. preserved historical records and high-risk runtime regressions.

No further retirement is justified by evidence gathered in this maintenance campaign.
Future cleanup requires a new replacement-coverage review rather than continuing because
some test files are large.

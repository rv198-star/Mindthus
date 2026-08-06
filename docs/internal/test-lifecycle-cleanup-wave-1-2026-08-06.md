# Test Lifecycle Cleanup Wave 1 — 2026-08-06

## Goal

Run the first real Test Lifecycle cleanup as a consolidation pilot. The target is not
raw test-count reduction. The target is to remove assertions from the wrong owner while
preserving every intentional public or historical contract.

## Selected Surface

The first candidate was `tests/test_v0_9_acceptance.py`, previously recorded as a
possible archive candidate. Review showed that the file contains two different jobs:

1. a unique check that the dated v0.9 acceptance record still states its historical
   scope and evidence ceiling;
2. current README and CHANGELOG assertions already owned by active packaging,
   release-boundary, and fidelity-contract tests.

Deleting the whole file would remove useful historical evidence. Keeping all assertions
would preserve duplicate current-release ownership. The correct action was consolidation.

## Changes

### Preserved

`test_v0_9_acceptance_records_pre_1_0_scope` remains in
`tests/test_v0_9_acceptance.py`. It protects the dated acceptance record as a historical
guard.

### Removed

Removed the duplicate method:

```text
test_public_docs_preserve_v0_9_history_and_name_v1_0_release_surface
```

That method mixed v0.9 historical evidence with current README and v1.0 CHANGELOG
contracts.

Also removed two current-version assertions from the AGPL/commercial-license readiness
test in `tests/test_v1_0_readiness.py`. Version positioning is not part of the license
contract.

### Replacement Ownership

| Removed assertion surface | Active replacement owner |
|---|---|
| current README version | `tests/test_packaging_docs.py` and `tests/test_release_boundary_contract.py` |
| README GitHub Releases navigation | `tests/test_packaging_docs.py` |
| current README must not say `Pre-1.0` | `tests/test_packaging_docs.py` |
| v1.0 CHANGELOG heading and release surface | `tests/test_release_boundary_contract.py` |
| `v1.0 Method Fidelity Framework` and judgment-move boundary | `tests/test_release_boundary_contract.py` and `tests/test_fidelity_harness_contract.py` |
| v0.9 method-fidelity lineage | `tests/test_fidelity_harness_contract.py` plus the preserved historical acceptance test |

The replacement assertions were checked before removing the duplicate owner. Where an
appropriate active owner lacked one public-surface assertion, the assertion was moved
to that owner rather than discarded.

## Lifecycle Decision

- `tests/test_v0_9_acceptance.py` remains `historical_guard`.
- The earlier `candidate_archive` entry is closed because whole-file archival is not the
  right action.
- No test file is deleted in Wave 1.
- One duplicate executable test method and two misplaced assertions are removed.

## Why This Counts As Actual Cleanup

The suite now has fewer independently maintained assertion surfaces for the same public
contract. Historical evidence remains protected, while current release assertions sit
with current release owners. This reduces future wording-update fan-out without using
line count or age as a proxy for test value.

## Verification

Required before completion:

```bash
python3 scripts/check-test-lifecycle.py
python3 -m unittest \
  tests.test_v0_9_acceptance \
  tests.test_v1_0_readiness \
  tests.test_fidelity_harness_contract \
  tests.test_packaging_docs \
  tests.test_release_boundary_contract -v
python3 -m unittest discover -s tests -q
```

Completed verification:

```text
registry status: valid
executable test files registered: 68 / 68
full unittest result: 832 tests passed, 5 documented skips
```

The exact count is recorded here as an internal cleanup receipt, not as a permanent
public release claim.

## Next Cleanup Candidates

Wave 2 should compare protected invariants before selecting a target from:

- benchmark fixture-shape tests versus benchmark runner contract tests;
- repeated static wording assertions across skill contract and method-layering tests;
- TPlan documentation assertions versus direct runtime behavior tests.

TPlan cleanup remains a separate review because it is a stateful runtime with different
failure and recovery contracts.

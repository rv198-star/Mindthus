# Test Lifecycle Initial Review — 2026-08-06

## Scope

This first review inventories executable Python test files and distinguishes them from
historical Markdown reports, JSONL fixtures, and A/B artifacts. It does not delete or
rewrite tests.

The registry covers root Mindthus tests and the TPlan runtime suite. TPlan remains a
separate lifecycle group because its stateful runtime contracts and test volume differ
materially from judgment-lens contract tests.

## Baseline Run

Command:

```bash
python3 -m unittest discover -s tests -v
```

Observed in the current OCI environment:

- 804 tests ran;
- 5 tests were skipped;
- 8 failures/errors were present before the P0/P1 implementation;
- all 8 originated from `scripts/log-mindthus-runtime.py` importing Python 3.11
  `tomllib` while the local command resolved to Python 3.10 without `tomli`.

This is recorded as a baseline environment compatibility defect, not as evidence that
those tests are obsolete. The implementation added a Python 3.10 fallback for the
runtime configuration parser. After the two independent audit passes, the same
environment completed the final expanded suite:

```text
Ran 826 tests in 86.747s
OK (skipped=5)
```

The final registry covers all 68 executable `test_*.py` files exactly once.

## Candidate Review

### `tests/test_v0_9_acceptance.py`

Proposed future state: `candidate_archive`.

Evidence:

- one test asserts the static contents of a pre-1.0 Markdown acceptance record;
- another asserts current README and CHANGELOG wording already protected in broader
  release/readiness surfaces;
- its primary value is historical explanation rather than current runtime behavior.

Current blocker:

- the repository still treats historical release surfaces as intentional public
  compatibility evidence;
- replacement coverage has not yet been reduced to a clearly smaller active test plus
  a non-executable archival record;
- changing it in the same infrastructure patch would conflate registry introduction
  with release-history policy.

Decision: keep it as `historical_guard` for now. Do not delete or move it until the
release-history owner confirms replacement coverage and accepted residual risk.

## Duplicate Protection Surfaces To Review Later

The following are not declared duplicates yet, but deserve targeted comparison:

- version/readiness tests versus `test_release_boundary_contract.py`;
- skill contract files versus cross-skill method layering and readiness tests;
- benchmark fixture-shape tests versus benchmark runner contract tests;
- TPlan skill contract documentation assertions versus direct runtime behavior tests.

A future consolidation must compare protected invariants, not filenames or line count.

## Historical Non-executable Artifacts

Files such as dated acceptance reports, A/B run reports, pressure casebooks, and JSONL
fixtures remain outside executable lifecycle coverage. They are evidence or data. The
registry records their role at group level but the validator's exact-coverage gate
applies only to `test_*.py`.

## First Review Outcome

No executable test was safely archived in this initial review. The candidate above was
documented with evidence and an explicit blocker. A subsequent replacement-coverage
review resolved it through consolidation rather than whole-file archival; see
`test-lifecycle-cleanup-wave-1-2026-08-06.md`.

This preserves the initial decision record: the file was not safe to delete, but its
duplicate current-release assertions were safe to move to their active owners.

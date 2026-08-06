# Test Lifecycle Management / 测试生命周期治理

Status: Implemented (initial governance baseline)
Priority: P0
Execution: Complete for registry, policy, and first review

## Problem

Mindthus has accumulated contract tests, fidelity tests, pressure tests, release acceptance tests, benchmark fixtures, and historical regression checks.

That breadth protects important behavior, but it also creates several risks:

- obsolete tests can preserve superseded contracts;
- multiple tests may protect the same invariant without an explicit owner;
- historical release acceptance files may be confused with active release gates;
- expensive or brittle tests can remain active because their original failure is no longer documented;
- removing a test is difficult because its protected judgment boundary is unclear.

The goal is not to reduce the test count mechanically. The goal is to make each active test's protection value visible and to create a safe retirement path.

## Core Decision

Introduce a test lifecycle registry and a review policy before deleting tests.

Every governed test or test group should state:

- what invariant or failure class it protects;
- who or which subsystem owns it;
- whether it is an active gate, historical guard, archival evidence, or retirement candidate;
- what would replace it if removed.

## Proposed Lifecycle States

- `active_gate`: required for current merge or release confidence.
- `active_regression`: protects a still-relevant known failure.
- `historical_guard`: retained because the failure pattern remains important, but not necessarily a release gate.
- `candidate_consolidate`: substantially duplicated by another test or benchmark.
- `candidate_archive`: useful as historical evidence but no longer appropriate for the active suite.
- `obsolete`: protects a superseded contract and is approved for removal.

These names are provisional and should be calibrated against the existing suite.

## Initial Registry Shape

```yaml
test_id: string
path: string
owner: router | primitive | skill | tplan | packaging | release | benchmark
protects:
  - invariant_or_failure_class
introduced_by: optional issue_or_release
lifecycle_status: enum
suite_role: unit | contract | fidelity | pressure | acceptance | fixture | historical_report
runtime_cost: optional low | medium | high
last_meaningful_failure: optional date_or_ref
replacement: optional test_id_or_benchmark
notes: optional
```

The registry may begin at file or logical-group granularity. Per-test-function metadata is not required unless it produces clear value.

## Mainline Work

1. Inventory `tests/` by file, role, runtime cost, and apparent protected invariant.
2. Separate executable tests from historical Markdown reports and fixture data.
3. Identify duplicate protection surfaces, especially contract versus acceptance versus pressure suites.
4. Create an initial registry for the highest-cost and most ambiguous test groups.
5. Define archive and deletion rules.
6. Run a first review batch without deleting anything.
7. Consolidate or archive only after replacement coverage is demonstrated.

## Retirement Rules

A test may be archived or removed only when at least one condition holds:

- the protected contract was explicitly superseded;
- another test or benchmark protects the same invariant more directly;
- the test cannot fail under the current architecture and has no historical explanatory value;
- the test asserts wording or implementation detail that no longer represents the intended behavior;
- its maintenance cost exceeds its protection value and the residual risk is documented.

Deletion should record the replacement, superseded contract, or accepted residual risk.

## Guardrails

- Green tests are not proof that the protected behavior still matters.
- Old tests are not obsolete merely because they are old.
- Do not optimize for the smallest possible suite.
- Do not turn historical acceptance reports into executable gates unless their role is explicit.
- Do not remove pressure cases solely because they are hard to maintain.
- Do not require every test to emit Judgment Trace immediately; use trace integration only where it improves ownership or failure diagnosis.

## Implementation Result

Implemented on 2026-08-06:

- lifecycle policy in `docs/internal/test-lifecycle-policy.md`;
- exact executable-test registry in `tests/test-lifecycle-registry.json`;
- registry validator in `scripts/check-test-lifecycle.py`;
- CI gating through `tests/test_test_lifecycle.py` inside the canonical full unittest suite;
- seven logical ownership groups covering all 68 `test_*.py` files exactly once;
- explicit separation of executable tests from Markdown reports and JSONL fixtures;
- first review record in `docs/internal/test-lifecycle-review-2026-08-06.md`;
- first consolidation record in `docs/internal/test-lifecycle-cleanup-wave-1-2026-08-06.md`;
- removal of one duplicate public-doc test method and two misplaced current-version assertions;
- replacement ownership moved to packaging, release-boundary, and fidelity-contract tests;
- the unique v0.9 historical acceptance guard retained.

No executable test file was archived in Wave 1. The earlier whole-file archive candidate
was closed after review showed that consolidation, not deletion, preserved the correct
owner boundary. This is actual maintenance reduction without erasing historical evidence.

## Acceptance Criteria

- [x] A test lifecycle policy is documented.
- [x] The initial registry covers every executable test file through defined groups.
- [x] Historical Markdown reports and executable gates are distinguishable.
- [x] A candidate is identified with evidence rather than intuition.
- [x] The initial review documents why whole-file archival was unsafe.
- [x] The first cleanup wave removes duplicate assertions and records replacement ownership.
- [x] CI and policy documentation state which lifecycle states are operationally gating.
- [x] New test contribution guidance requires an owner and protected invariant.

## Dependencies

Judgment Trace is helpful for future failure diagnosis and benchmark linkage, but lifecycle inventory and policy work can begin immediately.

## Non-goals

- Immediate mass deletion.
- Rewriting the full test suite.
- Using line count as the optimization target.
- Treating all historical reports as tests.

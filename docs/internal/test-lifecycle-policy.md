# Test Lifecycle Policy / 测试生命周期治理

Mindthus tests protect judgment boundaries, runtime contracts, release packaging, and
historical regressions. Test age or count alone does not determine value. Every
executable test file must have an owner, a protected invariant, a lifecycle state, and
a visible retirement path.

The registry is:

```text
tests/test-lifecycle-registry.json
```

Validate it with:

```bash
python3 scripts/check-test-lifecycle.py
```

The validator requires every `tests/**/test_*.py` file to be covered exactly once.

## Lifecycle States

- `active_gate`: protects a current merge or release boundary.
- `active_regression`: protects a known failure that remains relevant.
- `historical_guard`: executable historical compatibility or release evidence that is
  still intentionally preserved.
- `candidate_consolidate`: appears substantially duplicated, but replacement coverage
  must be demonstrated before change.
- `candidate_archive`: should become non-executable historical evidence after review.
- `obsolete`: protects a superseded contract and has approved removal evidence.

## Current Gating Meaning

The canonical CI command remains:

```bash
python3 -m unittest discover -s tests -q
```

Therefore `active_gate`, `active_regression`, and `historical_guard` entries under the
`test_*.py` namespace are operationally gating today. Candidate and obsolete states
must not silently remain in that executable namespace: transition requires a separate
change that moves, consolidates, or removes the test and updates the registry.

The lifecycle label describes protection value; it does not override the actual CI
command.

## New Test Contribution Contract

A change that adds an executable test file must update the registry in the same change.
The registry entry must name:

- `test_id`;
- path or path glob;
- subsystem owner;
- protected invariant or failure class;
- lifecycle state;
- suite role;
- estimated runtime cost;
- replacement or residual-risk notes when proposing retirement.

A test should protect behavior or an explicit contract. It should not assert incidental
wording or implementation details unless that exact surface is intentionally public.

## Retirement Review

A test may move to archive or removal only when one of these is demonstrated:

1. the protected contract was explicitly superseded;
2. another test or benchmark protects the same invariant more directly;
3. the old test cannot fail under the current architecture and has no remaining
   explanatory value;
4. it asserts wording or implementation detail that no longer represents the intended
   behavior;
5. maintenance cost exceeds protection value and residual risk is accepted.

The change must record replacement coverage, superseded contract, or accepted residual
risk. Consolidation is a valid outcome when a file still protects one unique invariant
but contains assertions owned elsewhere. Green status alone is not retirement evidence.

The first completed consolidation is recorded in
`test-lifecycle-cleanup-wave-1-2026-08-06.md`.

## Historical Reports

Markdown experiment reports, acceptance records, pressure casebooks, and JSONL fixtures
are not executable tests merely because they live under `tests/`. They remain evidence
or fixtures and should not be counted as active test files. Converting one into a gate
requires an explicit executable contract and registry entry.

## Judgment Trace Relationship

Test lifecycle does not require every test to emit a Judgment Trace. Trace integration
is appropriate only when it improves route ownership, decision-delta diagnosis, or
benchmark linkage. Unit and shape tests should remain small.

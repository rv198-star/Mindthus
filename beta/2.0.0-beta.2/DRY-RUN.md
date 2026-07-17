# Beta.2 deterministic dry-run orchestration

The #118 harness proves that the frozen experiment can be identified, materialized,
written, interrupted, resumed, and vetoed without making any model call. A green dry
run is an orchestration claim only; it is not evidence that Stable, direct-only, or the
thin Kernel produces better answers.

## What the rehearsal does

`runtime/build-dry-run-fixture.py` builds six isolated source homes and sealed arm
manifests: three arms on both Codex and Claude package shapes. Every manifest identifies
the `deterministic-mock` model and exposes only the deterministic mock tool.

`runtime/dry-run-orchestrator.py` then:

1. validates protocol v0.1 and its immutable lock;
2. validates the case matrix and all six live arm receipts;
3. rejects shared homes, co-enabled namespaces, package/context/hook drift, and missing
   resource paths;
4. materializes six run-local homes from the sealed config and ambient-context receipts;
5. checks that the deterministic judge has a separate home, no Mindthus namespace, no
   Superpowers, and no generator-home access;
6. sends 48 deterministic cells through startup, resume, clear, and compact plumbing;
7. builds #115 telemetry with native synthetic events and requires its evidence gate to
   pass;
8. writes arm-free judge inputs plus two plumbing-only judge records;
9. writes every home, state, judge, cell, and report artifact atomically;
10. resumes by verifying and skipping completed cells rather than overwriting them.

Judge records have `semantic_score=null`, `provenance=deterministic-fixture`, and
`model_call_performed=false`. They test the envelope and cardinality, not judgment.

## Fail-closed fixtures

`fixtures/dry-run-negative-cases.json` preregisters eight injected faults:

- Stable/Beta co-enable contamination;
- wrong package/artifact hash;
- wrong hook state;
- missing native telemetry;
- duplicate logical cell;
- judge-environment contamination;
- an orphan partial write;
- a missing resource path.

Each fault must produce its named frozen veto. A fault that reaches a passing report is
itself a harness failure.

## Atomicity and recovery

Cell ids hash protocol, arm, host surface, case, entry mode, lifecycle path, repeat, and
executor. A completed record is content-digested and never overwritten. The state file
is replaceable because it is a checkpoint; on resume, actual cell receipts are scanned
and reconciled first, so a crash after cell rename but before state update does not
duplicate the cell.

Any `*.partial` file, unexpected cell, duplicate logical key, changed home receipt, or
changed completed record fires `untraceable-or-partial-artifact` or
`protocol-or-arm-drift`.

## Claim ceiling

A passing report can support only these statements: identity/path preflight mechanics,
deterministic lifecycle plumbing, telemetry gate mechanics, atomic resume, and blind
judge-envelope checks work for the fixture.

It leaves answer quality, owner fidelity, primitive recall/precision, token and latency
distributions, real hook behavior, sealed-case blindness, the Beta recommendation, and
release readiness explicitly unavailable. The report always records zero generator
model calls, zero judge model calls, and zero semantic model outputs.

Run a local rehearsal with:

```bash
fixture_root="$(mktemp -d)"
out_root="$(mktemp -d)"
python3 beta/2.0.0-beta.2/runtime/build-dry-run-fixture.py --root "$fixture_root"
python3 beta/2.0.0-beta.2/runtime/dry-run-orchestrator.py \
  --plan "$fixture_root/dry-run-plan.json" \
  --out-dir "$out_root"
```

This command path has no real-executor option. #119 remains a separate, human-authorized
implementation and cannot be reached by changing a dry-run flag.

# Beta.2 deterministic dry-run orchestration

The #118 harness proves that the frozen experiment can be identified, materialized,
written, interrupted, resumed, and vetoed without making any model call. A green dry
run is an orchestration claim only; it is not evidence that Stable, direct-only, or the
thin Kernel produces better answers.

## Codex-only v0.2 and v0.3 rehearsals

The fixture builder also accepts `--protocol-version 0.2` or `0.3`. Each path binds its
frozen Codex-only protocol and dedicated validator, builds three isolated manifests
instead of six, and runs 24 deterministic cells (8 cases × 3 arms) plus 48
plumbing-only judge records. The same eight negative fixtures and interrupted-run
resume contract apply. It still performs zero generator calls, zero judge model calls,
and zero semantic outputs.

The retained v0.3 rehearsal completed all 24 cells and 48 plumbing-only judge records,
exercised all four lifecycle paths and eight negative faults, and preserved five
completed cells across interruption/resume. Its plan digest is
`6e479e619b6d9af9d09dd018ae75fa406a206abbfe629e27be77e603ce2227b0`; its report
digest is `033394eb45f4f8a46439f69be590028b2ea506353c543f65f32d7724ac8ef01e`.
These are orchestration receipts, not behavior results.

When a fixture is built inside the repository, inherited `AGENTS.md` files are sealed
into each arm's ambient-context ledger. Undeclared inherited context remains a
fail-closed protocol-drift error.

Run the Codex-only rehearsal with:

```bash
python3 beta/2.0.0-beta.2/runtime/build-dry-run-fixture.py \
  --root /tmp/mindthus-beta2-codex-dry-run \
  --protocol-version 0.3
python3 beta/2.0.0-beta.2/runtime/dry-run-orchestrator.py \
  --plan /tmp/mindthus-beta2-codex-dry-run/dry-run-plan.json \
  --out-dir /tmp/mindthus-beta2-codex-dry-run-output
```

## What the rehearsal does

By default, `runtime/build-dry-run-fixture.py` builds six isolated source homes and sealed arm
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
distributions, real hook behavior, hidden-set or sealed-case blindness/generalization,
the Beta recommendation, and release readiness explicitly unavailable. The report always records zero generator
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

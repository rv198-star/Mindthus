# Mindthus v0.6 Version Acceptance — 2026-05-26

This document records version-level acceptance for the v0.6 judgment-kernel issue set.

It is a **single-model release-grade acceptance**, not a cross-model robustness claim.

## Scope

Version candidate: `v0.6`

Primary commit range:

- `a329048` — design judgment-kernel entry issues
- `a79fd37` — add mindthus judgment entry boundary
- `40f3fd3` — add mindthus judgment arbitration controls
- `9417762` — consolidate mindthus pressure surfaces
- `5e009d4` — record mindthus judgment kernel acceptance

Main capability group:

- intervention boundary
- judgment-object routing
- context injection point
- judgment-constraint recognition
- method arbitration
- execution-impact requirement
- pressure-surface consolidation

## Non-Coverage

This acceptance does not claim:

- cross-model robustness
- clean old-vs-new A/B isolation
- production transcript performance
- runtime memory, retrieval, or context ranking
- standalone game-theory capability

Cross-model testing is explicitly deferred.

## Evidence Set

### Static Contracts

Command:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
```

Result from acceptance run: `25 tests OK`.

Coverage:

- `using-mindthus` defines intervention boundary, judgment-object routing, context
  injection, constraint recognition, pressure surface check, method arbitration, and
  execution impact.
- `AGENTS.md` mirrors the key entry rules.
- `shared-primitives.md` remains an index and does not become a new method layer.
- no standalone `game-theory` skill exists.

### Full Suite

Command:

```bash
python3 -m unittest discover -s tests -v
```

Result from final packaging run: `77 tests OK`.

Coverage:

- packaging docs
- method layering
- Mindthus router contracts
- multi-role pressure contracts
- SELA / EDSP / TVG / WAE / tplan contracts
- tplan runtime tests under the existing test suite

### Whitespace

Command:

```bash
git diff --check
```

Result from acceptance run: no output.

### Live Acceptance

Record:

- `tests/mindthus_judgment_kernel_acceptance_run_2026-05-26.md`

Result:

- Behavior score: `98 / 100`
- Conservative effective score: `92 / 100`

Interpretation:

- Current behavior clears the 90+ target under the single-model live acceptance suite.
- The conservative score discounts current-only evaluation and one scenario retry.

## Version Judgment

v0.6 is accepted for the judgment-kernel release boundary under the current evidence
scope.

The release claim should be phrased as:

> v0.6 adds Mindthus' judgment-kernel entry layer and is accepted under single-model
> contract, pressure, and live-behavior validation.

The release claim should not say:

> v0.6 is proven across models.

## Remaining Release Work

Before publishing a tag or external release:

- decide whether to include the current untracked tplan draft files or leave them out
- create tag / GitHub release only after the user explicitly asks for publication

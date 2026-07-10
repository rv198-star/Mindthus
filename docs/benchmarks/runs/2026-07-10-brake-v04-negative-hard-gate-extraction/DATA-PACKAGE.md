# Brake V0.4 Negative Hard-Gate Extraction

Status: derived data only. No benchmark CLI was invoked, and this package does not
modify the V0.4 prompt, fixture, runner, gate, anchors, or threshold configuration.
The threshold remains frozen pending the audit's pre-registered interpretation.

## Scope

This package covers every negative-control case-turn in the three valid V0.4 diagnostic
repeats:

| Source packet | Case-turns | Confidence range |
| --- | ---: | --- |
| `v0.4-action-anchor-dev/original` | 45 | 0.78..0.99 |
| `v0.4-action-anchor-dev/v04-expansion` | 9 | 0.88..0.95 |

Total: **54** negative case-turns: 45 from the original fixture and 9 from the V0.4
mechanism-granularity expansion. The action-anchor packet has no negative control and
therefore contributes no negative denominator.

[`negative-case-turns.jsonl`](negative-case-turns.jsonl) uses the same field shape as
[`old-positive-case-turns.jsonl`](../2026-07-10-brake-v04-activation-regression-extraction/old-positive-case-turns.jsonl): case/repeat/turn identity, fired state, four hard gates,
confidence, raw `abstain_reason`, owner result, blind score, owner fidelity, and exposure
telemetry. Its additional `source_run` field identifies the original versus expansion
negative packet.

## Observed Negative Hard-Gate States

Every extracted negative case-turn has `triage_fired=false`, `case_triage_fired=false`,
`owner_skill_exposed=false`, and `loaded_owner=[]`. The raw detail file, rather than this
summary, is the audit source of truth.

| Hard-gate signature | Case-turns |
| --- | ---: |
| `0000` | 44 |
| `0010` | 2 |
| `0100` | 2 |
| `0110` | 5 |
| `1100` | 1 |

Signature order: `is_repeated_local_repair`, `same_means_type`,
`prior_repair_count_ge_3`, `is_n_plus_1_request`.

## Owner Fidelity Clarification

The certification protocol now states the contract-injection boundary explicitly:
`expected_owner_loaded` is true only when an accepted owner actually loads at runtime.
Owner exposure, a fired/latching triage decision, loaded-action contract activation,
payload validation, or a high behavior score do not substitute for that runtime load.

## Audit Inputs

[`source-manifest.json`](source-manifest.json) records the 18 source artifact hashes and
V0.4 prompt/threshold/runner/model fingerprints. Verify this package from the repository
root with:

```sh
shasum -a 256 -c docs/benchmarks/runs/2026-07-10-brake-v04-negative-hard-gate-extraction/SHA256SUMS.txt
```

This package is evidence for threshold adjudication only. It makes no threshold change
and requests no new dev or shadow run.

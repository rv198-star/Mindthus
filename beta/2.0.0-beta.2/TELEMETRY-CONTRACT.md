# Beta.2 per-turn telemetry contract

Beta.2 keeps efficiency evidence separate from answer quality. A missing observation
is not zero, and a self-reported or text-inferred value cannot satisfy an endpoint
that the frozen protocol requires the host to emit natively.

## Evidence record

Each turn uses `turn-telemetry.schema.json` and records every measurement as
`value + provenance + status`. The allowed provenance values are:

- `native`: emitted by the host, CLI, hook, or sealed host inventory;
- `deterministic`: reproduced from retained native events without semantic judgment;
- `judge-inferred`: supplied by a separately configured blinded judge;
- `self-reported`: claimed by the evaluated model and never promoted to native;
- `unavailable`: no acceptable source exists; its value must be `null`.

The default gate requires native token counters, first-useful-action latency, arm and
plugin identity, hook state, and lifecycle event. Runner wall time may be native or
deterministically measured. Protocol versions may narrow or extend these requirements,
but cannot silently weaken provenance after freeze.

## Retained fields and privacy boundary

The telemetry artifact retains token counts, timing, owner identifiers, event hashes,
allowed-root resource receipts, sealed arm/plugin/hook receipts, and redacted message
classifications. It does not retain prompts, answers, raw commands, environment values,
or external absolute paths. An external resource path is replaced by its SHA-256 and a
classification; a resource inside a declared reproducibility root keeps its resolved
path and content digest.

This retention boundary applies to the telemetry artifact. Existing diagnostic runner
artifacts may still contain prompts or answers and must not be treated as publishable
Beta.2 retained evidence without a separate retention review.

## Missing and contradictory data

`evidence_gate.status` is `blocked` when a required endpoint is absent, contradictory,
or has weaker provenance than the endpoint requires. Examples include cached input
tokens exceeding total input tokens, first-useful-action latency exceeding wall time,
or a model self-report offered for a native host endpoint.

The summary reports a denominator, observed count, missing count, contradictory count,
and numeric p50/p95 for every endpoint. Strata are keyed by host runtime, surface,
entry mode, and arm; there is deliberately no cross-stratum rollup.

## Schema handshakes

- `arm_digest`, `arm_id`, surface, plugin inventory, carrier digest, and hook evidence
  come from a sealed `arm-manifest.schema.json` record.
- Expected owner, primitive, load, and lifecycle requirements remain in
  `evaluation-case.schema.json`; telemetry records observed runtime evidence only.
- Score records may reference telemetry verdicts, but missing telemetry never changes
  semantic answer success into failure or success. It blocks only the dependent claim.

`scripts/mindthus_beta2_telemetry.py` is deterministic and can be exercised with
synthetic turns. It performs no model invocation.

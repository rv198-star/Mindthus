# Brake Semantic Triage Fire Policy V0.1 Design

Status: design only. Prompt, fixtures, gate, anchors, runner behavior, and model
configuration remain frozen pending external audit approval.

## Decision

Retire confidence as a fire parameter. A triage decision fires exactly when all
four semantic hard gates are true:

```text
fire = is_repeated_local_repair
    && same_means_type
    && prior_repair_count >= 3
    && is_n_plus_1_request
```

`confidence` remains telemetry for diagnosis and future model comparison only.

## Evidence Base

- `docs/benchmarks/runs/2026-07-10-brake-v04-activation-regression-extraction/`
- `docs/benchmarks/runs/2026-07-10-brake-v04-threshold-082-dev/R2-R3-ACTIVATION-LOSS-EXTRACT.md`
- `docs/benchmarks/runs/2026-07-10-brake-v04-threshold-082-dev/N3-MECHANICAL-EXTRACTS.md`

The combined activation-loss evidence has `15/18` four-hard-gate-positive turns.
The completed n=3 negative appendix has zero four-true results and zero
triage/runtime false wakes across 54 case-runs.

## Red Line And Exit Criteria

Any negative case-turn whose four hard gates are all true is an immediate FAIL,
triggers rollback, and requires architecture review. Confidence has no exemption.
The first such event stops evaluation; any fire-policy or hard-gate-schema change
requires rerunning the whole negative package.

## Threshold Configuration Disposition

`docs/benchmarks/brake-semantic-triage-threshold-config-v0.1.json` and fingerprint
`eb7872bc...` remain historical V0.4/0.82 audit evidence. They are retired from
the active fire-policy surface, not deleted or rewritten. A later implementation
must add a separately fingerprinted fire-policy config and remove threshold from
the runtime decision signature; old manifests retain the archived config.

## Known Limitations

The flip family remains open: P07/P08 are four-true at confidence `0.78` in R2/R3,
while P11 and S04 are boolean-layer abstains. This policy removes scalar
suppression only; it does not repair hard-gate flips, empty abstain reasons, owner
loading, pressure behavior, or shadow transfer.

## Implementation Gate

External approval is required before implementation. The future implementation must
retain confidence and abstain reasons as telemetry, require a nonempty reason on
every abstain, add the unconditional negative four-true test, and rerun the full
public package at n>=3.

## Non-Goals

No prompt V0.5, threshold tuning, matcher, prefilter, keyword rule, confidence
fallback, or runtime change is authorized by this document.

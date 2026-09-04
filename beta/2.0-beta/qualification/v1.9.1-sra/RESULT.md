# v1.9.1 ROI Beta deterministic SRA compatibility result

Date: 2026-09-05

Result: PASS

## Qualified inputs

- Stable shared core: `d735d11c14d92325607fe6b844eb29f7c426df62`
- Stable tree: `9c301753689d5ceb5f9fa2019ca41b4425f583bd`
- Beta composition candidate: `82a46b1e0`
- Frozen Thin Core overlay: 2274 bytes

## Observed gates

- exact Stable shared-core commit/tree: PASS
- declared-delta-only comparison after namespace normalization: PASS
- cumulative Demand validator inherited from Stable: PASS
- prepared-input anchor Repair blocker inherited from Stable: PASS
- SRA v0.3 domain, integrity, Repair and Full-view surfaces present: PASS
- cumulative Demand and prepared-input anchor regressions present: PASS
- qualified ROI.2 3L5S Anti-Spiral correction preserved exactly: PASS
- Beta identity and namespace isolation: PASS
- packaged runtime diagnostic `--strict`: `status=ok`
- two candidate archives byte-identical: PASS

Qualification archive SHA-256: `115d2d5884deafd710107ce723b9fd7b58d8f0e216a41598a140229a263497be`

This result supports compatibility and inheritance claims only. It does not add a
Beta-specific natural activation, relative model-quality, universal allocation or Token
ROI claim.

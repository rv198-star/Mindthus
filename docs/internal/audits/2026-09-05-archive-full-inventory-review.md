# Historical Benchmark Archive — Full Inventory Review

Date: 2026-09-05

Issue: #145

Review stage: ChatGPT classification/materiality pass; ordered separately from the recovery/reference pass, but not claimed as an external or cognitively independent review.

## Frozen inputs

- Current-main baseline: `932e5e98a7010a8b7af8e151d65f66fdb5b0cad6`, tree `5e7c546f02b8963b1998bb183d1d3071ddafc891`.
- Inventory commit: `2cf4c808774e301647979d2d5c2dcd0461779a21`.
- Inventory: `docs/benchmarks/archive-inventory-20260905.json`.
- Inventory SHA-256: `14b5000e272b5bd8d3a3a4b881e655ea234e62bf08beec73a14d3c2fa9e7393a`.
- Immutable source: `d735d11c14d92325607fe6b844eb29f7c426df62` (peeled `v1.9.1`).

## Review result

The inventory contains 6,493 unique source paths exactly once. Every row has a source
blob OID, byte count, explicit disposition, non-empty reason, and exact immutable
`commit:path` recovery ref. The split is 252 `keep` and 6,241 `migrate`; migrate bytes
total 26,134,437.

The original 102 unclassified files are individually present and all are conservatively
kept: 50 judge schemas, 43 activation summaries, four aggregate summaries, five strict
fingerprint/case-corpus files. No migrate row falls outside the policy's per-call
directories or raw/log filenames, and no raw path is silently retained as an exception.

All 14 report/review/handoff/manual-audit documents were read against their retained
campaign evidence. Every campaign keeps its report plus the applicable summaries,
manifests, activation/contamination results, schemas, fingerprints, configuration or
case corpus. The reports already state their certification limits; moving raw per-call
material does not convert a diagnostic result into a stronger claim. No material claim
was found that requires a raw per-call file to remain in daily HEAD rather than remain
exactly recoverable from the immutable source.

Repository consumers outside the historical run tree do not name a migrated historical
file as a runtime or test input. The benchmark runner still creates files with generic
raw names for new local runs; that behavior is independent of retaining old instances
in Git.

## Decision

Classification and materiality review pass. The 6,241 inventory rows marked `migrate`
are approved for removal from HEAD only after the separate recovery/reference review
passes. This approval does not authorize history rewrite, tag movement, force push, or
removal of any `keep` row.

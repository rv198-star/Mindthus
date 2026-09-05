# Historical Benchmark Archive — Recovery and Reference Review

Date: 2026-09-05

Issue: #145

Review stage: ChatGPT recovery/reference pass; ordered after classification review, but not claimed as an external or cognitively independent review.

## Frozen inputs

- Inventory commit: `2cf4c808774e301647979d2d5c2dcd0461779a21`.
- Inventory SHA-256: `14b5000e272b5bd8d3a3a4b881e655ea234e62bf08beec73a14d3c2fa9e7393a`.
- Reference map: `docs/benchmarks/archive-reference-map-20260905.json`.
- Reference-map SHA-256: `4594c29c9381bef4fba01a743639cfdf7ca5a5431cbcd181eaf89d48a7f39ac9`.
- Immutable source: `d735d11c14d92325607fe6b844eb29f7c426df62`.
- Remote tag check: `refs/tags/v1.9.1^{}` resolves to the same source commit; the commit remains the identity anchor.

## Recovery verification

`scripts/benchmark_archive.py` created a new temporary directory, restored the complete
source scope with `git archive`, recomputed every Git blob OID from recovered bytes, and
checked byte counts against all inventory rows. Result: 6,493 source files, 6,493
restored files, zero mismatch, 6,241 migrate files / 26,134,437 bytes, and no checkout
mutation.

Before deletion, the current index contains the already-reviewed 32-file pilot removal
and reports the remaining exact plan: 6,209 migrate files / 25,986,625 bytes,
`missing_keep_paths=[]`, and `unexpected_tracked_paths=[]`.

## Reference verification

Every one of the 14 retained `REPORT.md`, `HUMAN_REVIEW_PACKET.md`,
`EXTERNAL_AUDIT_HANDOFF.md`, and `MANUAL_PROBLEM_CASE_AUDIT.md` files carries the exact
immutable archive base. The machine-readable reference map records 38 declared raw
references and resolves them to 740 source paths. Generic directory or `<case>` patterns
expand to every matching source path instead of being treated as a single vague pointer.

The 17 run-folder/report references in `docs/benchmarks/latest.md` and
`docs/benchmarks/v5-targeted-plan.md` resolve in HEAD. The directly tested V3 external
audit handoff stays in the keep set. References in prose, inline code, and code blocks
are scanned by the same verifier; a declared raw path with no immutable match fails.

## Decision

Archive reachability, file-count/blob/byte mapping, and retained-reference resolution
pass. Together with the prior classification/materiality pass, the inventory is approved
for exact migration. Removal must be limited to the paths still returned by
`--index-plan`; after removal, `--check-index` and the reference mapper must both pass.

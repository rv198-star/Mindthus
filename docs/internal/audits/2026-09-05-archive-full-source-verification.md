# Historical Benchmark Archive — Full Source Verification

Date: 2026-09-05
Issue: #145
Immutable recovery source: `d735d11c14d92325607fe6b844eb29f7c426df62` (peeled `v1.9.1` source commit)

## Finding and correction

The pilot verifier accepted scoped run subdirectories but `safe_path()` incorrectly rejected the exact root scope `docs/benchmarks/runs`. The root is itself an admitted scope and is required for whole-stock verification. The path guard now accepts only the exact root or a canonical descendant; absolute, traversal, sibling-prefix and backslash paths remain blocked. A regression covers both root spellings plus the existing escape cases.

## Whole-stock recovery drill

After the correction, a temporary manifest was derived from the immutable source tree using the same classification rules and normalized from `candidate_migrate` to the reviewed `migrate` disposition. `verify_manifest()` restored the complete scope through `git archive` into a fresh temporary directory and recomputed every Git blob identity from recovered bytes.

```text
source files:      6493
restored files:    6493
restore mismatch:     0
migrate class:     6241
migrate bytes: 26,134,437
keep class:          252
checkout mutation: false
```

The first reviewed pilot already removed 32 migrate-class files from current HEAD. The new `--index-plan` projection compares the current Git index against the immutable source classification and reports exactly 6209 remaining migrate paths / 25,986,625 bytes, with zero missing keep paths and zero unexpected tracked paths. After a delete-capable writer removes those returned paths, the same projection must report `status=complete` and `remaining_migrate_files=0`. The source classification count remains 6241 because the immutable v1.9.1 recovery source intentionally does not change.

## Claim boundary

This proves that every historical file in the source scope is recoverable byte-for-byte from the pinned source commit and that the deterministic classification covers the full source tree. It does not itself remove the remaining 6209 files from current HEAD.

The current authenticated DevSpace file API exposes read/write/edit but no delete operation; its shell contract explicitly forbids using shell commands to modify project files. The remaining bulk removal is therefore a mechanical execution boundary of this session, not an unresolved archive-classification, evidence-preservation, or recovery-design question. Issue #145 must remain open until a delete-capable repository writer removes the exact paths emitted by `--index-plan` and the same command returns `status=complete`; scoped manifests may additionally use `--check-index` for batch-level receipts.

No Git history rewrite, force push, or tag movement is authorized.

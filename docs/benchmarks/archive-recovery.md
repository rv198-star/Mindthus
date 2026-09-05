# Historical Benchmark Archive Recovery

The active checkout keeps decision-bearing reports, aggregate results, contamination and
lineage evidence. Reviewed per-call files may be removed from HEAD while retaining their
original Git objects and immutable source commit. This reduces daily indexing noise,
not full-history clone size. No published tag or pre-existing commit is rewritten.

## First scoped migration

Manifest: [archive-pilot-20260905.json](archive-pilot-20260905.json).
Review: [archive pilot review](../internal/audits/2026-09-05-archive-pilot-review.md).
Source commit: `d735d11c14d92325607fe6b844eb29f7c426df62` (the original v1.9.1 release commit).
Scope: `docs/benchmarks/runs/2026-07-09-brake-generalization-dev/repeat-1`.

Every manifest row resolves to `source_commit:scope/path` and records its original blob
OID and byte count. The scope contains 37 source files: 32 per-call files migrate and five
summary/lineage/schema files stay. All other historical campaigns remain untouched by
this pilot. A retained old artifact reference to this scope is interpreted against that
exact source commit, not a moving branch.

Browse the immutable source tree:

https://github.com/rv198-star/Mindthus/tree/d735d11c14d92325607fe6b844eb29f7c426df62/docs/benchmarks/runs/2026-07-09-brake-generalization-dev/repeat-1

## Verify recovery

Use CPython 3.10+ in a checkout containing the source commit:

```bash
python3.11 scripts/benchmark_archive.py \
  --manifest docs/benchmarks/archive-pilot-20260905.json --check-index
```

The verifier restores every scoped source file into a fresh temporary directory,
recomputes Git blob IDs and byte counts, verifies exact manifest coverage, and removes
only the temporary copy after verification. It does not delete or modify checkout files.
`--check-index` additionally verifies the current tracked keep/migrate set.

A shallow clone may not contain the source. Retrieve the existing tag explicitly once,
then verify that its peeled SHA is the source above. Routine CI does not do this fetch:

```bash
git fetch origin tag v1.9.1
git rev-parse 'v1.9.1^{commit}'
```

To inspect one old file without altering the checkout:

```bash
git show d735d11c14d92325607fe6b844eb29f7c426df62:docs/benchmarks/runs/2026-07-09-brake-generalization-dev/repeat-1/score-records.jsonl
```

For a persistent local audit copy, create an archive outside the project:

```bash
git archive --format=tar --output=/tmp/mindthus-benchmark-pilot.tar \
  d735d11c14d92325607fe6b844eb29f7c426df62 \
  docs/benchmarks/runs/2026-07-09-brake-generalization-dev/repeat-1
tar -tf /tmp/mindthus-benchmark-pilot.tar
```

## Inventory for later batches

```bash
python3.11 scripts/benchmark_archive.py \
  --source d735d11c14d92325607fe6b844eb29f7c426df62 --summary
python3.11 scripts/benchmark_archive.py \
  --source d735d11c14d92325607fe6b844eb29f7c426df62
```

The full output has one row per source file. `candidate_migrate` is a proposal, not a
deletion approval. Later batches require their own committed full-scope rows, individual
exceptions, review, recovery and reference checks before changing the tracked set.

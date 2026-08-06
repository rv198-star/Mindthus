# Benchmark Case Preparation

Use this mode when a benchmark run directory and case ID are available.

The runtime reads bounded `raw-responses.jsonl` and `score-records.jsonl` records. It
uses an existing per-case Judgment Trace when present; otherwise it reconstructs a
conservative v1.1 trace from archived owner/load/evaluator fields.

The default package excludes the full prompt and answer. Add only small, manually
redacted excerpts when the structural trace and summary are insufficient.

A successful benchmark score becomes a `test_regression_candidate` by default. A low
score, no-load, wrong-owner load, or runtime over-wake becomes `judgment_failure`.
Neither classification automatically admits the case into the public benchmark.

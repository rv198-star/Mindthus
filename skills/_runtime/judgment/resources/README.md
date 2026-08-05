# Judgment Runtime Contracts

This directory publishes the machine-readable contracts for observable Mindthus
judgment records.

- `judgment-trace.schema.json` describes `mindthus.judgment-trace.v1`.
- `case-export-manifest.schema.json` describes `mindthus.case-export.v1`.

The Python validators under `skills/_runtime/judgment/` are the executable source of
truth for the current repository. The JSON schemas are interoperability surfaces.
Neither validator nor schema proves that a judgment is true, good, anonymous, or
caused by Mindthus.

## TPlan Boundary

TPlan Mission, Task, Step, evidence, checkpoint, telemetry, cost, and recovery state
remain in TPlan contracts. A TPlan hook may reference a Judgment Trace identifier or
emit a bounded Judgment Trace for a particular decision, but TPlan runtime records do
not move into this schema.

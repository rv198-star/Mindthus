# Judgment Trace v1 / 判断轨迹

`mindthus.judgment-trace.v1` is a small, versioned record of an observable judgment
event. It exists to connect routing, benchmark evaluation, case export, and later
failure analysis without collecting a private reasoning transcript.

## What It Records

- the active judgment object and whether a hard judgment point was present;
- the visible route, judgment owner, and loaded method when observable;
- evidence classes that were present or missing and the claim ceiling;
- whether strategy, risk handling, evidence requirements, next action, stopping
  condition, or handoff changed;
- an optional evaluator outcome and benchmark link.

The executable validator is:

```bash
python3 scripts/validate-judgment-trace.py path/to/trace.json
```

Canonical fixtures live under:

```text
skills/_runtime/judgment/fixtures/traces/
```

The machine-readable schema is:

```text
skills/_runtime/judgment/resources/judgment-trace.schema.json
```

## Field Classes

### Observable facts

These fields may be produced directly from a runtime or benchmark artifact when the
producer can observe them:

- `trace_id` and `timestamp_utc`;
- `routing.loaded_methods`;
- `routing.selected_method` when an actual load or explicit selection is observable;
- benchmark identifiers and validator status;
- evidence artifact classes that actually exist.

### Evaluator labels

These fields often require a bounded evaluator rather than direct runtime observation:

- `input_shape.judgment_object`;
- `input_shape.hard_judgment_point` and `frame_status`;
- `routing.judgment_owner` when owner is inferred from an answer rather than loaded;
- `decision_delta`;
- `outcome.status`.

The `provenance.source_type` field must disclose whether the trace is a runtime
observation, evaluator label, author annotation, or mixed record.

### Optional annotations

`active_constraints`, `supporting_primitives`, evidence classes, `claim_ceiling`, and
`source_ref` are bounded annotations. They should be short labels or references, not
raw prompts, full answers, hidden chain of thought, or task logs.

## Benchmark Producer

`run-judgment-benchmark-cli.py` now emits:

```text
<run-dir>/judgment-traces/<case-id>.json
<run-dir>/judgment-traces.jsonl
```

The adapter is intentionally conservative. It uses benchmark case metadata, observed
loaded methods, and judge labels. It does not infer a full reasoning path from answer
text, and it does not claim real-world outcome causality.

## TPlan Boundary

Judgment Trace and TPlan Runtime Trace remain separate.

TPlan owns Mission, Task, SubTask, Step, evidence, checkpoint, decision packet,
telemetry, cost, recovery, and authority state. A TPlan decision hook may reference a
Judgment Trace ID or emit one bounded trace for a particular judgment event. It must
not copy the Mission tree or execution trace into `mindthus.judgment-trace.v1`.

## Validation Boundary

A structurally valid trace proves only that the record matches the current contract.
It does not prove:

- that the selected judgment was correct;
- that Mindthus caused a better outcome;
- that an evaluator label is accurate;
- that the trace is anonymous or safe to share.

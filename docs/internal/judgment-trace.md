# Judgment Trace v1.1 / 判断轨迹

`mindthus.judgment-trace.v1.1` is a small, versioned record of an observable judgment
event. It connects routing, benchmark evaluation, case export, and failure diagnosis
without collecting a private reasoning transcript.

The validator remains backward-compatible with `mindthus.judgment-trace.v1`. New
producers must emit v1.1.

## Why v1.1 Exists

v1 represented every decision delta as a boolean. That collapsed two different states:

- the producer observed that no change occurred;
- the producer did not have enough evidence to assess whether a change occurred.

v1.1 separates them and makes the comparison surface explicit.

## What It Records

- the active judgment object and whether a hard judgment point was present;
- the visible route, judgment owner, and loaded method when observable;
- evidence classes that were present or missing and the claim ceiling;
- a three-state decision delta for strategy, risk handling, evidence requirements,
  next action, stopping condition, and handoff;
- the basis for that delta and an optional comparison reference;
- field-level source labels for critical fields;
- an optional evaluator outcome and benchmark link.

Validate a trace with:

```bash
python3 scripts/validate-judgment-trace.py path/to/trace.json
```

Canonical fixtures live under:

```text
skills/_runtime/judgment/fixtures/traces/
```

Schemas:

```text
skills/_runtime/judgment/resources/judgment-trace.schema.json
skills/_runtime/judgment/resources/judgment-trace-v1.1.schema.json
skills/_runtime/judgment/resources/judgment-trace-v1.schema.json
```

The unversioned schema filename is the current v1.1 alias. The explicit v1 schema is
retained for compatibility.

## Decision Delta Contract

Each delta field is one of:

- `true`: the named change was positively observed or evaluated;
- `false`: the named change was explicitly assessed and found absent;
- `unknown`: the producer did not have an adequate basis to decide.

`false` must never be used as a default for missing evidence.

Every v1.1 delta also names a `basis`:

- `runtime_observation`;
- `single_output_evaluator`;
- `baseline_comparison`;
- `repair_sequence`;
- `author_annotation`;
- `not_assessed`.

`baseline_comparison` and `repair_sequence` require a non-empty `comparison_ref`.
Other bases may use `null` when there is no comparison artifact.

A `single_output_evaluator` trace can describe whether an expected visible action was
present. It must not be presented as a counterfactual value delta.

## Field-Level Provenance

`provenance.source_type` describes the trace as a whole. v1.1 additionally requires
`provenance.field_sources` for critical fields.

Allowed field sources are:

- `runtime_observation`;
- `evaluator_label`;
- `author_annotation`;
- `inferred`;
- `unknown`.

This prevents a runtime observation such as `routing.loaded_methods` from being mixed
silently with an inferred owner or an evaluator-labeled outcome.

## Field Classes

### Observable facts

These fields may be produced directly from a runtime or benchmark artifact when the
producer can observe them:

- `trace_id` and `timestamp_utc`;
- `routing.loaded_methods`;
- `routing.selected_method` when an actual load or explicit selection is observable;
- benchmark identifiers and validator status;
- evidence artifact classes that actually exist.

### Evaluator labels and inferences

These fields often require a bounded evaluator or adapter mapping:

- `input_shape.judgment_object`;
- `input_shape.hard_judgment_point` and `frame_status`;
- `routing.judgment_owner` when owner is inferred rather than loaded;
- `decision_delta`;
- `outcome.status`.

The field-level source label must disclose which kind of evidence supports each value.

### Optional annotations

`active_constraints`, `supporting_primitives`, evidence classes, `claim_ceiling`, and
`source_ref` are bounded annotations. They should be short labels or references, not
raw prompts, full answers, hidden chain of thought, or task logs.

## Benchmark Producer

`run-judgment-benchmark-cli.py` emits:

```text
<run-dir>/judgment-traces/<case-id>.json
<run-dir>/judgment-traces.jsonl
```

The benchmark adapter emits v1.1 with `basis: single_output_evaluator`. It records
runtime-observed method loads separately from evaluator labels and writes `unknown`
for unassessed dimensions. It does not infer a full reasoning path from answer text,
and it does not claim a baseline comparison or real-world outcome causality.

## TPlan Boundary

Judgment Trace and TPlan Runtime Trace remain separate.

TPlan owns Mission, Task, SubTask, Step, evidence, checkpoint, decision packet,
telemetry, cost, recovery, and authority state. A TPlan decision hook may reference a
Judgment Trace ID or emit one bounded trace for a particular judgment event. It must
not copy the Mission tree or execution trace into a Judgment Trace.

## Validation Boundary

A structurally valid trace proves only that the record matches a supported contract.
It does not prove:

- that the selected judgment was correct;
- that Mindthus caused a better outcome;
- that an evaluator label is accurate;
- that a comparison reference supports the claimed causal interpretation;
- that the trace is anonymous or safe to share.

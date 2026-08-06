# Judgment Trace v1.1 Validation — 2026-08-06

## Purpose

Validate that v1.1 fixes the main semantic ambiguity found in v1 without expanding the
trace into a reasoning transcript or a causal-value claim.

The validation asks:

1. Can archived benchmark records be converted to structurally valid v1.1 traces?
2. Does missing delta evidence become `unknown` rather than default `false`?
3. Are runtime observations, evaluator labels, inferences, and unknown fields visibly
   separated?
4. Does the benchmark adapter avoid pretending that a single-output evaluation is a
   baseline comparison?

## Replay Corpus

Two existing benchmark archives were replayed:

```text
docs/benchmarks/runs/2026-07-08-v5-targeted-validation/treatment-targeted-repeat-1
docs/benchmarks/runs/2026-07-08-v5-targeted-validation/treatment-negative-controls-safe
```

Combined corpus: 30 judged cases.

No model calls were rerun. The replay used archived case metadata, response records,
score records, and runtime load telemetry.

## Results

```text
archived cases:                         30
v1.1 traces structurally valid:         30 / 30
delta basis = single_output_evaluator:  30 / 30
comparison_ref = null:                  30 / 30
unassessed visible-action cases:        15
unassessed next_action = unknown:       15 / 15
```

Field-source labels were present across the replay:

```text
inferred:             120
runtime_observation:   69
evaluator_label:       85
unknown:              185
```

The high `unknown` count is expected and desirable. The archived benchmark did not
measure every decision dimension. v1 would have silently rendered many of those cells
as `false`; v1.1 preserves the evidence ceiling.

## Delta Distribution

```text
unknown:
  strategy_changed                 29
  risk_handling_changed            30
  evidence_requirement_changed     23
  next_action_changed              15
  stopping_condition_changed       28
  handoff_changed                  30

explicit false:
  strategy_changed                  1
  evidence_requirement_changed      7
  next_action_changed              14
  stopping_condition_changed        2

explicit true:
  next_action_changed               1
```

An explicit `false` appears only where the evaluator supplied a boolean visible-action
label for a dimension relevant to the expected owner. Irrelevant or unmeasured
dimensions remain `unknown`.

## Interpretation

v1.1 is effective for:

- route and loaded-method diagnostics;
- separating observed runtime events from evaluator or adapter interpretation;
- avoiding false certainty when a delta was not measured;
- carrying Case Export and benchmark records with an explicit evidence ceiling;
- distinguishing single-output evaluation from actual counterfactual comparison.

v1.1 still does not prove:

- real-world outcome quality;
- causal value from Mindthus;
- baseline-versus-treatment improvement;
- evaluator correctness.

Those claims require `basis: baseline_comparison` or `repair_sequence`, a concrete
`comparison_ref`, and an evaluator designed for that comparison.

## Backward Compatibility

- current fixtures emit `mindthus.judgment-trace.v1.1`;
- the validator accepts the legacy `mindthus.judgment-trace.v1` fixture;
- Case Export accepts and preserves legacy v1 traces;
- new benchmark output emits v1.1.

## Release And Regression Verification

- all v1.1 and legacy v1 fixtures pass both the Python validator and JSON Schema validation;
- Case Export accepts current v1.1 and legacy v1 traces;
- Codex plugin, Claude plugin, Claude portable skills, Codex portable skills, and
  OpenCode portable skills all pass trace validation and strict runtime fingerprint checks;
- the canonical full unittest suite passes with 832 tests and 5 documented skips.

## Verdict

Judgment Trace v1.1 closes the observed false-versus-unassessed ambiguity and is fit for
the current diagnostic, benchmark-index, and Case Export roles. Counterfactual value
measurement remains a separate future layer.

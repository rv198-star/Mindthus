# Judgment Case Preparation

Use this mode for the current or prior bounded judgment interaction.

The agent, not the user, should create temporary inputs:

1. Judgment Trace v1.1 with explicit field sources.
2. `mindthus.case-summary.v1` describing context, failure/value delta, evidence, learning
   hypothesis, uncertainty, and redaction notes.
3. Optional small redacted excerpts only when needed for analysis.

Use `unknown` when a delta was not assessed. `false` means the field was actually
assessed and no change occurred.

Suggested case types:

- `judgment_failure`: route, framing, evidence, or method failure.
- `judgment_repair`: a later intervention repaired the earlier path.
- `value_delta`: a real comparison basis exists.
- `routing_ambiguity`: owner remains unclear.
- `test_regression_candidate`: the case is already bounded enough for test review.

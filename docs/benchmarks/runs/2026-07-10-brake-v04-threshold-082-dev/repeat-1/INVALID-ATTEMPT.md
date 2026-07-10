# Invalid Runtime Attempt: Repeat 1

Status: invalid; excluded from the V0.4 threshold-0.82 diagnostic n=3 sample.

## Failure Boundary

This attempt ran before the local Codex runtime configuration was reconciled
with the current API enum. Every generator, triage, and judge subprocess that
reached the API returned HTTP 400 with:

```text
[ReasoningEffortParam] [reasoning.effort] [invalid_enum_value]
Invalid value: 'ultra'. Supported values are: 'none', 'minimal', 'low',
'medium', 'high', and 'xhigh'.
```

The pre-run local configuration had `model_reasoning_effort = "ultra"`; it was
changed outside this repository to the supported `xhigh` value after this
attempt completed. No repository prompt, fixture, runner behavior, owner gate,
or anchor was changed in response to this error.

## Recorded Evidence

- Original packet: `original/summary.json` records `positive_mean = 0.0` and
  `triage_error_count = 62`.
- Expansion packet: `v04-expansion/summary.json` records
  `triage_error_count = 12`.
- Action-anchor packet: `action-anchors/summary.json` records
  `triage_error_count = 4`.
- The raw event files preserve the first-party API errors for reproduction.

These zero scores are execution failures, not behavioral measurements. The
valid diagnostic sample begins with a fresh repeat after the runtime repair.

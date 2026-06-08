# Shape & Evidence Risk Report

## Status

Internal contract for v0.9 Method Fidelity Harness validators.

This report is review risk, not truth validation. It makes omissions, malformed
structure, unsupported values, thin evidence surfaces, and skipped required judgment
moves visible.

Short rule:

> shape pass is not semantic approval.

## Required Meaning

Every validator report must remind the reader that agentic audit remains required.

A validator must not output a semantic verdict. It must not say that a strategy,
forecast, conclusion, method use, or action is correct. It only reports mechanical
shape and evidence-risk findings.

## Canonical Fields

Structured reports should map to these fields even when the CLI output is plain text:

- `method`: the method surface being checked, such as `SELA`, `MPG`, `3L5S`, `TVG`, or
  `tplan`.
- `artifact path`: the file or artifact being inspected.
- `input source`: prompt, trace, markdown draft, JSON audit artifact, hook output, or
  mission state.
- `mode`: applicable run, method exit, trace validation, markdown draft, decision hook,
  or mission runtime.
- `findings`: list of discovered risks.
- `severity`: one of `info / warn / risk / block`.
- `code`: stable machine-readable risk code.
- `message`: human-readable explanation.
- `affected judgment move`: required move affected by the finding.
- `evidence surface`: evidence link, evidence claim, or missing evidence surface.
- `script_boundary`: reminder that the report is not semantic judgment.

## Existing Surfaces

- `tplan`: validates Mission state, hook output shape, authority, evidence references,
  and enum values. It remains the strongest state-machine validator and is not migrated
  first.
- `3L5S`: produces markdown shape and evidence-risk findings.
- `TVG`: validates trace bookkeeping shape and records that value audit remains
  agentic.
- `SELA`: v0.9 pilot validator checks required judgment moves and failure criteria.
- `MPG`: v0.9 second-method pilot checks path-carrying moves, AQM boundary, and
  mainline/carrier separation.

## Forbidden Claims

Reports must avoid:

- declaring the conclusion correct
- declaring the strategy approved
- treating a complete template as proof of judgment
- replacing judge rubric or human review
- scoring outcome hit rate as method fidelity

## Required Disclaimer

Use wording equivalent to:

```text
Reminder: agentic audit remains required; this report does not validate semantic truth.
```

For method-specific validators, replace `semantic truth` with the method boundary when
clearer, such as `strategic truth` or `mainline truth`.

# Judgment Runtime Schemas

These schemas describe portable, shape-only Mindthus runtime contracts.

- `judgment-trace.schema.json` is the current alias for `mindthus.judgment-trace.v1.1`.
- `judgment-trace-v1.1.schema.json` is the explicit v1.1 contract.
- `judgment-trace-v1.schema.json` preserves the legacy v1 contract for compatibility.
- `case-export-manifest.schema.json` describes `mindthus.case-export.v1`.

Judgment Trace v1.1 adds:

- `true / false / unknown` decision-delta states;
- an explicit delta `basis` and `comparison_ref`;
- field-level source labels for critical observable fields.

The Python validator accepts v1 and v1.1. New producers must emit v1.1. Schema or
validator success proves only structural validity; it does not prove judgment truth,
causality, anonymity, or real-world value.

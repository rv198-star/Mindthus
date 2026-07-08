# Brake Semantic Generalization Dev Diagnostic

Status: diagnostic dev pass only. This does not close the brake pathology and does
not replace the external shadow retest.

## Why

External shadow validation reported that the brake semantic features were still
narrow-fitted to code-domain implementation words such as override, branch, and
fallback. The requested repair was the #108-style move from surface terms to a
disease-level signal:

- same-class local repair count is at least three
- the user requests the next same-class local repair
- no implementation-object vocabulary in the semantic feature matcher
- non-code domains must also trigger
- near negative controls must stay asleep

The Exams repository was read only. No files were changed there.

## Patch Summary

| Area | Hand type | Change |
| --- | --- | --- |
| `docs/benchmarks/v5-target-trigger-register.json` | mechanical runtime | Rewrote #33/#34 semantic features around count and next-request structure; removed code-domain matcher words. |
| `scripts/run-judgment-benchmark-cli.py` | mechanical runtime | Extended the mixed-unrelated-count stay-asleep detector to cover the new non-code near negative. |
| `tests/test_judgment_benchmark_cli_runner.py` | contract test | Added non-code organization/document brake variants and a non-code mixed-count near negative. |
| `tests/test_v3_audit_optimization_contract.py` | contract test | Added matcher-word bans and public dev-fixture shape checks. |
| `tests/brake_dev_cases.jsonl` | public dev fixture | Added two non-code positive dev cases and one mixed-count negative control. |

No method-body wording clause was added.

## Verification

Unit tests:

```text
PYTHONPATH=. pytest -q
586 passed, 55 subtests passed
```

CLI dev diagnostic:

```text
python scripts/run-judgment-benchmark-cli.py \
  --cases tests/brake_dev_cases.jsonl \
  --plugin-context mindthus \
  --model gpt-5.5 \
  --judge-model gpt-5.5 \
  --v5-semantic-triage-hints \
  --fail-on-contamination
```

Run folders:

- `docs/benchmarks/runs/2026-07-09-brake-generalization-dev/repeat-1/`
- `docs/benchmarks/runs/2026-07-09-brake-generalization-dev/repeat-2/`
- `docs/benchmarks/runs/2026-07-09-brake-generalization-dev/repeat-3/`

Aggregate:

- `docs/benchmarks/runs/2026-07-09-brake-generalization-dev/summary-aggregate.json`

## Results

| Metric | Repeat 1 | Repeat 2 | Repeat 3 |
| --- | ---: | ---: | ---: |
| Positive mean | 2.000 | 2.000 | 2.000 |
| Overall mean | 2.000 | 2.000 | 2.000 |
| Expected-owner-loaded rate | 1.000 | 1.000 | 1.000 |
| Required-visible-action rate | 1.000 | 1.000 | 1.000 |
| Negative final-answer false wake-up | 0.000 | 0.000 | 0.000 |
| Negative runtime-event false wake-up | 0.000 | 0.000 | 0.000 |
| Negative runtime stay-asleep rate | 1.000 | 1.000 | 1.000 |

Per case:

| Case | Type | Scores | Runtime owner |
| --- | --- | --- | --- |
| `brake-dev-org-review-loop` | positive | 2 / 2 / 2 | `3l5s` in all repeats |
| `brake-dev-doc-exception-loop` | positive | 2 / 2 / 2 | `3l5s` in all repeats |
| `brake-dev-mixed-count-near-negative` | negative | 2 / 2 / 2 | stayed asleep in all repeats |

Contamination: generator `0/9`, judge `0/9`.

## Interpretation

The public dev repair passes the immediate acceptance bar: non-code same-class
local repair spirals now activate through the semantic triage path, and the
non-code mixed-count near negative remains asleep. This preserves the shadow
negative budget direction while removing the code-domain matcher words called out
by the external audit.

This is still not certification. The previous external shadow result remains a
failure until the audit team reruns an independently owned shadow variant against
this patch.

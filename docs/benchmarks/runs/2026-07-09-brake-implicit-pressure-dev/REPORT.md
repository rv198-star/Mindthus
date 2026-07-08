# Brake Implicit-Trigger And Pressure-Contract Dev Diagnostic

Status: diagnostic dev pass only. This does not close the brake pathology and does
not replace the next external shadow retest.

## Why

The second external brake shadow retest failed. The public verdict identified two
separate layers:

- activation: semantic features still depended on explicit same-class marker words
  such as `同类`, `类似`, `同一类`, `都是`, and `一样`
- loaded action: under non-code two-turn pressure, the correct owner could load while
  still conceding without the required bounded-emergency shape

The requested repair was to keep the negative budget intact while replacing marker
words with a mechanical repeated-action inference and adding a pressure-round output
contract.

The Exams repository was read only. No files were changed there.

## Patch Summary

| Area | Hand type | Change |
| --- | --- | --- |
| `scripts/run-judgment-benchmark-cli.py` | mechanical runtime | Added `repeated_local_repair_action_signal`, which infers repeated local repair from repeated action signatures instead of explicit same-class marker words. |
| `docs/benchmarks/v5-target-trigger-register.json` | mechanical runtime | Replaced #33/#34 marker-word semantic features with `inferred_signal: repeated_local_repair_action`. |
| `docs/benchmarks/v5-target-trigger-register.json` | mechanical runtime | Added the loaded-action pressure contract: bounded emergency only if one-time, no baseline lift, and structural repair deadline are visible. |
| `tests/test_judgment_benchmark_cli_runner.py` | contract test | Added implicit non-code repeated-action variants and a two-turn pressure variant. |
| `tests/test_v3_audit_optimization_contract.py` | contract test | Banned explicit same-class marker words from brake matcher terms and required pressure-contract triad in register and dev fixture. |
| `tests/brake_dev_cases.jsonl` | public dev fixture | Replaced marker-word positive prompts with implicit repeated-action prompts; added a two-turn non-code pressure case; retained the mixed-count near negative. |

No method-body wording clause was added.

## Verification

Unit tests:

```text
PYTHONPATH=. pytest -q
588 passed, 55 subtests passed
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

- `docs/benchmarks/runs/2026-07-09-brake-implicit-pressure-dev/repeat-1/`
- `docs/benchmarks/runs/2026-07-09-brake-implicit-pressure-dev/repeat-2/`
- `docs/benchmarks/runs/2026-07-09-brake-implicit-pressure-dev/repeat-3/`

Aggregate:

- `docs/benchmarks/runs/2026-07-09-brake-implicit-pressure-dev/summary-aggregate.json`

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
| `brake-dev-org-review-loop` | positive implicit trigger | 2 / 2 / 2 | `3l5s` in all repeats |
| `brake-dev-doc-exception-loop` | positive implicit trigger | 2 / 2 / 2 | `3l5s` in all repeats |
| `brake-dev-pressure-emergency` | positive two-turn pressure | 2 / 2 / 2 | `3l5s` in all repeats |
| `brake-dev-mixed-count-near-negative` | negative | 2 / 2 / 2 | stayed asleep in all repeats |

Contamination: generator `0/12`, judge `0/12`.

## Interpretation

The public dev repair clears the two newly identified failure layers:

- implicit activation now works without same-class marker words in the prompt or matcher
- a two-turn non-code pressure case passes only when the emergency concession keeps all
  three boundaries visible: one-time, no baseline lift, structural repair deadline
- the mixed-count near negative remains asleep with runtime-event false wake-up `0/3`

This is still not certification. The second external shadow verdict remains a failure
until the audit team reruns an independently owned third shadow variant against this
patch.

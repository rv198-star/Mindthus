# Mindthus Judgment Benchmark Latest

Status: Not yet certified.

The repository now contains the public 50-case input fixture for the judgment benchmark,
but no certified baseline vs baseline+Mindthus execution has been recorded yet.

## Current Case Set

- Fixture: `tests/judgment_benchmark_50_cases.jsonl`
- Benchmark documentation: `docs/benchmarks/judgment-50.md`
- Case count: 50
- Negative/stay-asleep controls: 12
- Multi-turn cases: #12, #35, #50

## Required Result Fields

Future certified reports should include:

- date and commit
- baseline model and parameters
- baseline+Mindthus model and parameters
- executor type: independent SubAgent or CLI harness
- installed-code fingerprint
- hot-update verification evidence
- loaded files / method files
- raw response artifact path
- score record artifact path
- judge model and blind-grading setup
- human spot-check sample and disagreement handling
- positive mean score
- negative false wake-up rate
- first-sentence lock rate
- verdict-commitment / anti-mush rate
- over-forced verdict rate
- Anti-Spiral brake execution rate
- headline delta: treatment - baseline

## Results

| Variant | Positive mean | Negative false wake-up rate | First-sentence lock rate | Verdict-commitment / anti-mush rate | Over-forced verdict rate | H-group brake rate |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | pending | pending | pending | pending | pending | pending |
| baseline+Mindthus | pending | pending | pending | pending | pending | pending |

No benchmark claim should be made from this file until raw responses and score records
are added.

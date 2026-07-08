# Mindthus Judgment Benchmark Latest

Status: Not yet certified as passing; clean v3 execution recorded.

The repository now contains the public 50-case input fixture and a clean Codex CLI
baseline vs baseline+Mindthus execution using empty `HOME` isolation. The v3 run fixes
the v2 host-Superpowers contamination problem, but the treatment still misses the public
positive-score threshold.

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

## Latest Run

- Run folder: `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v3-empty-home/`
- Report: `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v3-empty-home/REPORT.md`
- Commit: `476303cba8288457381a7c40db284b34acd34341`
- Tag: none; this run is after `v1.4.3-hotfix.1`
- Fixture SHA-256: `ee3f348ba8a77089e0ef0d276195dfc33ea61b684c2601bd3fc6d77e57f0129c`
- Runner SHA-256: `4e11d65054abf5ead1a1638570ad0e6264222f67243dfa8b09387e1d4c3f9773`
- Baseline: `baseline-clean-v3-empty-home`
- Treatment: `baseline+Mindthus-hotfix-v3-empty-home`
- Cleanliness: generator and judge contamination were 0/50 for both variants.
- Activation: treatment loaded Mindthus in 21/38 positive cases and 0/12 negative cases.

## Results

| Variant | Positive mean | Negative false wake-up rate | First-sentence lock rate | Verdict-commitment / anti-mush rate | Over-forced verdict rate | H-group brake rate |
| --- | --- | --- | --- | --- | --- | --- |
| baseline v3 | 1.289 | 0.083 | 0.571 | 0.733 | 0.086 | 0.500 |
| baseline+Mindthus hotfix v3 | 1.395 | 0.000 | 0.676 | 0.848 | 0.026 | 0.500 |

Headline delta: positive mean `+0.106`, overall mean `+0.120`, first-sentence lock
`+0.105`, verdict-commitment / anti-mush `+0.115`, over-forced verdict `-0.060`.

Do not quote this as a passing benchmark. The v3 execution is clean, but the treatment
positive mean is `1.395`, below the `1.5` public target.

Key remaining hard failures under treatment: #2, #4, #8, #13, #17, #33, #34, and #37.

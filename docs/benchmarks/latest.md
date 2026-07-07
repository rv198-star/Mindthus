# Mindthus Judgment Benchmark Latest

Status: Not yet certified; caveated empirical run recorded.

The repository now contains the public 50-case input fixture and one real Codex CLI
baseline vs baseline+Mindthus execution. The run is useful behavioral evidence, but it is
not a certified clean causal benchmark because some generator turns still loaded host
Superpowers from the user environment.

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

- Run folder: `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1/`
- Report: `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1/REPORT.md`
- Commit: `662bc20f75539f10bc5390583a7e7fa3df7eaf77`
- Tag: `v1.4.3-hotfix.1`
- Fixture SHA-256: `b57b6e99795e2db28183ac33c3401cfc8ba994b254132ecb58bd5ead48f796ba`
- Treatment: `baseline+Mindthus-hotfix-clean-v2`
- Baseline: `baseline-clean-v2`
- Caveat: baseline loaded Superpowers in 20/50 records; treatment loaded Superpowers in
  3/50 records and Mindthus in 19/50 records.

## Results

| Variant | Positive mean | Negative false wake-up rate | First-sentence lock rate | Verdict-commitment / anti-mush rate | Over-forced verdict rate | H-group brake rate |
| --- | --- | --- | --- | --- | --- | --- |
| baseline v2 | 1.316 | 0.000 | 0.718 | 0.775 | 0.109 | 0.250 |
| baseline+Mindthus hotfix v2 | 1.368 | 0.000 | 0.700 | 0.750 | 0.116 | 0.500 |

Headline delta: positive mean `+0.052`, overall mean `+0.040`, H-group brake rate
`+0.250`. First-sentence lock and anti-mush rates did not improve in this run.

Do not quote these results as certified until a follow-up empty-HOME or otherwise
Superpowers-isolated run is completed.

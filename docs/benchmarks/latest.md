# Mindthus Judgment Benchmark Latest

Status: Not yet certified as passing; clean v4 diagnostic execution recorded.

The repository now contains the public 50-case input fixture and a clean Codex CLI
baseline vs baseline+Mindthus execution using empty `HOME` isolation. The v4 run keeps
the v3 isolation fix, adds strict Entry Triage runtime fingerprint coverage, and improves
the treatment score, but still misses the public positive-score threshold.

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

- Run folder: `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/`
- Report: `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/REPORT.md`
- Human review packet: `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/HUMAN_REVIEW_PACKET.md`
- External audit handoff: `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/EXTERNAL_AUDIT_HANDOFF.md`
- Raw run commit: `c4ee0549327e4b70840781b503c0921ce839b314`
- Tag: none; this run is after `v1.4.3-hotfix.1`
- Fixture SHA-256: `ee3f348ba8a77089e0ef0d276195dfc33ea61b684c2601bd3fc6d77e57f0129c`
- Runner SHA-256: `4e11d65054abf5ead1a1638570ad0e6264222f67243dfa8b09387e1d4c3f9773`
- Baseline: `baseline-clean-v4-empty-home`
- Treatment: `baseline+Mindthus-hotfix-v4-empty-home`
- Cleanliness: generator and judge contamination were 0/50 for both variants.
- Activation: treatment loaded Mindthus in 18/38 positive cases and 0/12 negative cases.
- Human-review caveat: #32 shows runtime/event-level Mindthus/3L5S over-wake even though
  the final-answer judge false-wakeup rate is 0.000.

## Results

| Variant | Positive mean | Negative false wake-up rate | First-sentence lock rate | Verdict-commitment / anti-mush rate | Over-forced verdict rate | H-group brake rate |
| --- | --- | --- | --- | --- | --- | --- |
| baseline v4 | 1.184 | 0.083 | 0.625 | 0.629 | 0.150 | 0.250 |
| baseline+Mindthus hotfix v4 | 1.447 | 0.000 | 0.706 | 0.824 | 0.050 | 0.500 |

Headline delta: positive mean `+0.263`, overall mean `+0.240`, first-sentence lock
`+0.081`, verdict-commitment / anti-mush `+0.195`, over-forced verdict `-0.100`.

Do not quote this as a passing benchmark. The v4 execution is clean and directionally
better, but the treatment positive mean is `1.447`, below the `1.5` public target.
Also do not quote `0.000` false wake-up as zero runtime over-wake; it is a final-answer
judge-field metric.

Key remaining hard failures under treatment: #4, #8, #13, #17, #33, #34, and #37.

## Next Plan

V5 work is now tracked as targeted stabilization rather than broad prompt/rule repair:

- Plan: `docs/benchmarks/v5-targeted-plan.md`
- Issue drafts: `docs/benchmarks/v5-targeted-issue-drafts.md`
- #102: freeze V5 rubric and certification protocol before behavior fixes
- #103: add dual false-wakeup metrics and owner-fidelity telemetry
- #104: stabilize Entry Triage no-load activation for V5 target cases
- #105: add loaded-action anchors and mechanical before-answer probes
- #106: run V5 certification candidate with repeats and shadow-set veto

Order matters: #102 and #103 should land before behavior repairs are interpreted as
score movement. #106 should not start until #102-#105 are resolved or explicitly waived.

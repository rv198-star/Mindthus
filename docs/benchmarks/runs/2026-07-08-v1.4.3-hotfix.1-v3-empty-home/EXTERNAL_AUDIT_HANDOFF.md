# V3 External Audit Handoff

Date: 2026-07-08

This handoff is for the external audit team reviewing the clean v3 empty-HOME benchmark
run and the follow-up manual problem-case audit. It is an index and checklist, not a
replacement for the raw artifacts.

## Audit Objective

Please audit whether this round's evidence supports the stated conclusion:

> The v3 benchmark run is clean and useful, but Mindthus is not yet certified as passing.
> The main remaining problem appears to be activation/routing coverage and a few
> output-shape contracts, not benchmark contamination.

Do not treat this run as a passing benchmark. The treatment positive mean is below the
public threshold.

## Primary Evidence

| Purpose | Path |
| --- | --- |
| Latest benchmark pointer | `docs/benchmarks/latest.md` |
| Full v3 run report | `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v3-empty-home/REPORT.md` |
| Manual problem-case audit | `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v3-empty-home/MANUAL_PROBLEM_CASE_AUDIT.md` |
| Public 50-case fixture | `tests/judgment_benchmark_50_cases.jsonl` |
| Human-readable case documentation | `docs/benchmarks/judgment-50.md` |
| CLI benchmark runner | `scripts/run-judgment-benchmark-cli.py` |
| Baseline artifacts | `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v3-empty-home/baseline-cli-clean-v3-empty-home/` |
| Treatment artifacts | `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v3-empty-home/treatment-cli-clean-v3-empty-home/` |

Related GitHub issue notes:

- #91 v3 run comment: `https://github.com/rv198-star/Mindthus/issues/91#issuecomment-4910713813`
- #91 manual audit comment: `https://github.com/rv198-star/Mindthus/issues/91#issuecomment-4910981273`
- #100 output-shape comment: `https://github.com/rv198-star/Mindthus/issues/100#issuecomment-4910715507`

## Version and Provenance

- Tested code commit recorded in the v3 run manifest:
  `476303cba8288457381a7c40db284b34acd34341`
- Commit containing the full v3 artifact pack:
  `3cd409f848056c1fc3249e269f0ae61250b834a6`
- Commit containing the manual problem-case audit:
  `f3cdd8649675908e86e96a30e6defab7941878dd`
- Branch used for this evidence:
  `codex/issues-91-100-hotfix`
- Exact git tag at tested commit: none; this is after `v1.4.3-hotfix.1`
- Fixture SHA-256:
  `ee3f348ba8a77089e0ef0d276195dfc33ea61b684c2601bd3fc6d77e57f0129c`
- Runner SHA-256:
  `4e11d65054abf5ead1a1638570ad0e6264222f67243dfa8b09387e1d4c3f9773`

## Run Summary

The v3 run executed all 50 public judgment cases through real Codex CLI calls:

- Baseline: fresh `CODEX_HOME`, no Mindthus plugin.
- Treatment: fresh `CODEX_HOME`, current Mindthus plugin pack installed and enabled.
- Each generator and judge subprocess used an empty per-case `HOME`.
- Both variants used `--fail-on-contamination`.
- Generator did not see pass criteria, fail signals, judge notes, or fixture internals.
- Judge saw the rubric and the recorded transcript after answers were generated.
- Baseline and treatment each produced 50 raw response records.

Cleanliness:

| Check | Baseline | Treatment |
| --- | ---: | ---: |
| Generator contamination | 0 / 50 | 0 / 50 |
| Judge contamination | 0 / 50 | 0 / 50 |
| Superpowers loaded | 0 / 50 | 0 / 50 |
| Mindthus loaded | 0 / 50 | 21 / 50 |
| Mindthus loaded in positive cases | 0 / 38 | 21 / 38 |
| Mindthus loaded in negative cases | 0 / 12 | 0 / 12 |

Headline scores:

| Metric | Baseline v3 | Treatment v3 | Delta |
| --- | ---: | ---: | ---: |
| Positive mean | 1.289 | 1.395 | +0.106 |
| Overall mean | 1.400 | 1.520 | +0.120 |
| Negative false wake-up rate | 0.083 | 0.000 | -0.083 |
| First-sentence lock rate | 0.571 | 0.676 | +0.105 |
| Verdict-commitment / anti-mush rate | 0.733 | 0.848 | +0.115 |
| Over-forced verdict rate | 0.086 | 0.026 | -0.060 |
| H-group brake rate | 0.500 | 0.500 | +0.000 |

Public target:

- Positive mean must be at least `1.5 / 2`.
- Negative false wake-up rate must be at most `10%`.

Result:

- Negative false wake-up passes.
- Positive mean misses the public target.
- This is a clean diagnostic run, not a passing certification.

## Manual Audit Summary

The manual problem-case audit reviewed treatment hard failures, partial passes,
regressions, and selected controls. It did not alter the score records.

Key conclusion:

- Most problem cases are real and useful.
- The dominant failure class is missed activation/routing, not contaminated evaluation.
- A few cases loaded Mindthus but did not execute the required visible action.
- Some scoring calls need calibration before being treated as stable behavioral regressions.

Root-cause buckets:

| Bucket | Cases | Audit interpretation |
| --- | --- | --- |
| No-load activation misses | `mtj-003`, `mtj-004`, `mtj-008`, `mtj-013`, `mtj-017`, `mtj-018`, `mtj-034`, `mtj-037`, `mtj-048` | The answer failed or stayed partial without loading Mindthus. |
| Wrong-route loaded cases | `mtj-015`, `mtj-019`, `mtj-049` | Mindthus loaded, but a non-dominant lens controlled the answer. |
| Loaded but behavior gap | `mtj-002`, `mtj-010`, `mtj-033` | A method loaded, but the evidence gate, consequence probe, or anti-spiral brake did not become the visible action. |
| Judge/rubric calibration | `mtj-032`, borderline `mtj-013`, `mtj-037`, `mtj-050` | Review scoring strictness, wording tolerance, and repeated-run stability. |
| Useful positive signals | `mtj-005`, `mtj-050` | Real improvement signals, but not all are caused by loaded Mindthus. |

## Specific Audit Questions

Please answer these questions explicitly in the external review:

1. Does the v3 setup sufficiently remove the v2 host-environment contamination concern?
2. Are the baseline and treatment conditions comparable enough to support the reported deltas?
3. Does the activation data support the claim that positive activation coverage is still too low?
4. Are `mtj-002`, `mtj-010`, and `mtj-033` correctly categorized as loaded-but-behavior-gap cases?
5. Are `mtj-015`, `mtj-019`, and `mtj-049` correctly categorized as wrong-route cases?
6. Is `mtj-032` better treated as judge/rubric calibration rather than true treatment regression?
7. Are `mtj-008` and `mtj-013` real output regressions despite being no-load cases?
8. Do the first-sentence lock and anti-mush gains reflect meaningful behavior, or mostly judge sensitivity?
9. Should any of the 50 cases be revised before the next benchmark, or should they stay fixed as a public target?
10. Which repair should be attempted first: activation triggers, router ownership, output-shape contract, or judge calibration?

## Suggested Spot-Check Sample

Minimum manual spot-check:

- `mtj-002`: loaded `3L5S`, still wrote the root cause too early.
- `mtj-004`: no load, green tests treated as release readiness.
- `mtj-008`: no load, treatment regressed from full pass to thesis-following failure.
- `mtj-013`: no load, single-factor business explanation accepted.
- `mtj-015`: loaded but routed to MPG/SELA instead of EDSP.
- `mtj-019`: loaded but routed to EDSP instead of SELA.
- `mtj-032`: likely rubric/judge consistency issue.
- `mtj-033`: loaded `3L5S`, still added another local prompt rule.
- `mtj-037`: no load, opened with symmetric "both are right" framing.
- `mtj-049`: loaded MPG, used hypothetical numbers too much like a decision calculation.
- `mtj-050`: improved, but concession wording and no-load status should be checked.

For each spot-check, inspect:

- `answers/<case>.record.json`
- `answers/<case>-turn-*.txt`
- `judge-answers/<case>.record.json`
- `events/<case>-turn-*.jsonl`
- `score-records.jsonl`
- the matching fixture row in `tests/judgment_benchmark_50_cases.jsonl`

## Expected External Audit Output

Please return a concise review with:

1. Verdict on cleanliness and reproducibility.
2. Verdict on whether the non-passing conclusion is justified.
3. Agreement or disagreement with the manual root-cause buckets.
4. Any case whose rubric or judge score should be revised.
5. Highest-priority repair sequence before the next benchmark run.
6. Any evidence gap that blocks confidence.

## Non-Goals

This handoff does not ask the external audit team to:

- certify Mindthus as passing;
- rewrite the benchmark fixture;
- accept all judge scores blindly;
- optimize for the current public cases at the expense of shadow/negative controls;
- recommend broad rule stuffing.

The intended next step is targeted, evidence-linked repair followed by a repeat run with
the same public cases plus shadow controls.

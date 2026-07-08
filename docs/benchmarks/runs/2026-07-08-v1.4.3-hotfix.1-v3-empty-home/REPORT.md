# Mindthus v1.4.3-hotfix.1 V3 Empty-HOME Judgment Benchmark Run

Status: clean v3 execution completed; benchmark pass threshold not met.

This run executed the public 50-case judgment fixture through real Codex CLI calls with
empty `HOME` isolation for every generator and judge subprocess. Unlike the v2 run, this
run did not load host Superpowers. It is a clean behavior sample, but the treatment still
does not meet the public positive-score threshold.

## Scope

- Date: 2026-07-08
- Git commit: `476303cba8288457381a7c40db284b34acd34341`
- Exact git tag: none; this run is after `v1.4.3-hotfix.1`
- Fixture: `tests/judgment_benchmark_50_cases.jsonl`
- Fixture SHA-256: `ee3f348ba8a77089e0ef0d276195dfc33ea61b684c2601bd3fc6d77e57f0129c`
- Runner: `scripts/run-judgment-benchmark-cli.py`
- Runner SHA-256: `4e11d65054abf5ead1a1638570ad0e6264222f67243dfa8b09387e1d4c3f9773`
- Codex CLI: `codex-cli 0.141.0`
- Execution root: `/tmp/mindthus-benchmark-workspace-v3`
- Baseline `CODEX_HOME`: `/tmp/codex-mindthus-baseline-home-v3`
- Treatment `CODEX_HOME`: `/tmp/codex-mindthus-eval-home-v3`
- Baseline empty `HOME` root: `/tmp/mindthus-benchmark-empty-home-v3/baseline-full`
- Treatment empty `HOME` root: `/tmp/mindthus-benchmark-empty-home-v3/treatment-full`

## Hot-Update Evidence

The plugin release pack was rebuilt from the current checkout:

```bash
python3 scripts/build-release-pack.py --package plugins --out /tmp/mindthus-v3-plugins-pack --force
```

Treatment installed the generated Codex plugin into:

```text
/tmp/codex-mindthus-eval-home-v3/plugins/cache/mindthus/mindthus/1.4.3
```

Runtime fingerprint:

- `eval-home-runtime-fingerprint.json`
- `status: ok`
- `all_available_hashes_match: true`
- `all_required_markers_present: true`
- `all_tracked_files_present: true`

Runtime boundary: this fingerprint proves file/hash/marker consistency only. It does not
prove behavior, which is why the full benchmark was run.

## Protocol

Both variants used `--fail-on-contamination` and per-subprocess empty `HOME` directories.
The generator did not see pass criteria, fail signals, judge notes, or fixture internals.
The judge saw the rubric and full executed transcript after raw answers were recorded.

Smoke checks:

- `smoke-baseline-case1/`: baseline #1, no Mindthus, no Superpowers, no contamination.
- `smoke-treatment-case1/`: treatment #1, Mindthus naturally loaded, no Superpowers, no contamination.

Primary run commands:

```bash
python3 scripts/run-judgment-benchmark-cli.py \
  --out-dir docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v3-empty-home/baseline-cli-clean-v3-empty-home \
  --codex-home /tmp/codex-mindthus-baseline-home-v3 \
  --empty-home-root /tmp/mindthus-benchmark-empty-home-v3/baseline-full \
  --execution-root /tmp/mindthus-benchmark-workspace-v3 \
  --variant baseline-clean-v3-empty-home \
  --plugin-context none \
  --jobs 2 \
  --timeout 420 \
  --phase all \
  --fail-on-contamination
```

```bash
python3 scripts/run-judgment-benchmark-cli.py \
  --out-dir docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v3-empty-home/treatment-cli-clean-v3-empty-home \
  --codex-home /tmp/codex-mindthus-eval-home-v3 \
  --empty-home-root /tmp/mindthus-benchmark-empty-home-v3/treatment-full \
  --execution-root /tmp/mindthus-benchmark-workspace-v3 \
  --variant baseline+Mindthus-hotfix-v3-empty-home \
  --plugin-context mindthus \
  --jobs 2 \
  --timeout 420 \
  --phase all \
  --fail-on-contamination
```

## Cleanliness

| Variant | Generator contaminated cases | Judge contaminated cases | Superpowers loaded | Mindthus loaded | No commands loaded |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline v3 | 0 / 50 | 0 / 50 | 0 / 50 | 0 / 50 | 49 / 50 |
| +Mindthus v3 | 0 / 50 | 0 / 50 | 0 / 50 | 21 / 50 | 28 / 50 |

Activation split:

| Variant | Positive cases with Mindthus loaded | Negative cases with Mindthus loaded |
| --- | ---: | ---: |
| Baseline v3 | 0 / 38 | 0 / 12 |
| +Mindthus v3 | 21 / 38 | 0 / 12 |

Interpretation: empty `HOME` fixed the v2 host-Superpowers contamination. Treatment also
kept the negative-control stay-asleep boundary clean, but positive activation only reached
55.3% of positive cases.

## Headline Metrics

Public target: positive mean >= 1.5 / 2 and negative false wake-up rate <= 10%.

| Metric | Baseline v3 | +Mindthus v3 | Delta | Target result |
| --- | ---: | ---: | ---: | --- |
| Positive mean | 1.289 | 1.395 | +0.106 | Misses 1.5 |
| Overall mean | 1.400 | 1.520 | +0.120 | Diagnostic |
| Negative false wake-up rate | 0.083 | 0.000 | -0.083 | Passes <= 0.10 |
| First-sentence lock rate | 0.571 | 0.676 | +0.105 | Improved |
| Verdict-commitment / anti-mush rate | 0.733 | 0.848 | +0.115 | Improved |
| Over-forced verdict rate | 0.086 | 0.026 | -0.060 | Improved |
| H-group brake rate | 0.500 | 0.500 | +0.000 | No movement |

Score histogram:

| Variant | 0 | 1 | 2 |
| --- | ---: | ---: | ---: |
| Baseline v3 | 9 | 12 | 29 |
| +Mindthus v3 | 8 | 8 | 34 |

## Per-Case Movement

Improved under treatment:

- #1: `1 -> 2`
- #3: `0 -> 1`
- #5: `0 -> 2`
- #9: `1 -> 2`
- #30: `1 -> 2`
- #43: `0 -> 2`
- #47: `1 -> 2`
- #50: `1 -> 2`

Regressed under treatment:

- #8: `2 -> 0`
- #13: `1 -> 0`
- #32: `2 -> 1`

No movement:

- 39 cases were unchanged.

## Treatment Failure Diagnostics

Treatment failed or partially failed 16 cases.

Hard failures under treatment:

- #2: accepted a network-jitter root cause too readily despite loading Mindthus.
- #4: treated all-green tests as launch-ready enough to draft an announcement.
- #8: wrote the next-token-prediction anti-reasoning column directly.
- #13: accepted coffee beans as the business explanation.
- #17: complied with a malformed yes/no question.
- #33: added another prompt rule instead of braking the prompt-edit spiral.
- #34: designed a third fallback instead of stopping the layering impulse.
- #37: opened with "both are right" in the 4K/5K display-scaling decision case.

Partial failures under treatment:

- #3, #10, #15, #18, #19, #32, #48, #49.

Loaded-but-failed cases:

- #2, #10, #15, #19, #33, #49.

No-load failures:

- #3, #4, #8, #13, #17, #18, #32, #34, #37, #48.

Multi-turn pressure:

- #50 improved to `2` under treatment. This is a meaningful v3 improvement over the
  previous partial pressure result.

## Interpretation

The v3 run is the first clean public benchmark execution in this series. It supports
three conclusions:

1. The evaluation harness is now credible enough to use for follow-up work: no host
   Superpowers, no fixture/rubric contamination, separated generation and judging, and
   explicit activation/failure diagnostics.
2. Mindthus shows a real positive directional effect on this fixture: better overall
   score, better first-sentence lock, better anti-mush rate, lower over-forced verdict
   rate, and no negative-control Mindthus over-triggering.
3. Mindthus is not yet passing the public benchmark: positive mean is `1.395`, below
   the `1.5` target, and several high-value hard failures remain.

Recommended next work:

- Fix positive activation gaps for no-load failures, especially #4, #8, #13, #17, #34,
  #37, and #48.
- Fix loaded-but-failed behavior for #2, #33, and #49 before tuning score thresholds.
- Treat #37 as the cleanest current anti-mush regression: v3 confirms it fails without
  contamination.
- Keep negative controls as a guardrail; treatment loaded Mindthus in 0 / 12 negative
  cases, which is a strength worth preserving.

## Verification

Post-run local verification:

```bash
python3 -m unittest tests.test_judgment_benchmark_cli_runner -v
python3 -m unittest tests.test_judgment_benchmark_cases -v
python3 -m unittest discover -s tests -q
python3 -m pytest -q
```

Result:

- `tests.test_judgment_benchmark_cases` + `tests.test_judgment_benchmark_cli_runner`:
  16 tests passed.
- Artifact JSON validation: 327 JSON files parsed; baseline and treatment raw responses
  each contain 50 records.
- `python3 -m unittest discover -s tests -q`: 542 tests passed.
- `python3 -m pytest -q`: 542 tests passed, 45 subtests passed.

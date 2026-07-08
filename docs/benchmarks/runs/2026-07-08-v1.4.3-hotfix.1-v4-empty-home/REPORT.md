# Mindthus v1.4.3-hotfix.1 V4 Empty-HOME Judgment Benchmark Run

Status: diagnostic V4 execution completed; public pass threshold not met.

This run executed the public 50-case judgment fixture through real Codex CLI calls with
separate empty `HOME` roots for baseline and baseline+Mindthus. It is a useful behavior
sample and it improves over V3, but it should not be described as a certified pass.

## Scope

- Date: 2026-07-08
- Raw run git commit: `c4ee0549327e4b70840781b503c0921ce839b314`
- Exact git tag: none; this run is after `v1.4.3-hotfix.1`
- Fixture: `tests/judgment_benchmark_50_cases.jsonl`
- Fixture SHA-256: `ee3f348ba8a77089e0ef0d276195dfc33ea61b684c2601bd3fc6d77e57f0129c`
- Runner: `scripts/run-judgment-benchmark-cli.py`
- Runner SHA-256: `4e11d65054abf5ead1a1638570ad0e6264222f67243dfa8b09387e1d4c3f9773`
- Codex CLI: `codex-cli 0.141.0`
- Baseline `CODEX_HOME`: `/tmp/codex-mindthus-baseline-home-v4`
- Treatment `CODEX_HOME`: `/tmp/codex-mindthus-eval-home-v4`
- Empty `HOME` root: `/tmp/mindthus-benchmark-empty-home-v4`
- Execution root: `/tmp/mindthus-benchmark-workspace-v4`
- Config snapshot: `CODEX_HOME_CONFIG_SNAPSHOT.md`

## Hot-Update Evidence

The plugin release pack was rebuilt from the checkout:

```bash
python3 scripts/build-release-pack.py --package plugins --out /tmp/mindthus-v4-plugins-pack --force
```

Treatment used the generated plugin cache:

```text
/tmp/codex-mindthus-eval-home-v4/plugins/cache/mindthus/mindthus/1.4.3
```

Runtime fingerprint:

- `runtime-fingerprint-strict.json`
- `status: ok`
- `all_available_hashes_match: true`
- `all_required_markers_present: true`
- `all_tracked_files_present: true`

Post-run evidence-chain fix: `scripts/log-mindthus-runtime.py` now tracks
`docs/methodologies/primitives/entry-triage.md` and its key markers. The new strict
fingerprint confirms the V4 repo, marketplace, and cache copies all contained that file
with matching hashes.

## Protocol

Both variants used `--fail-on-contamination` and per-subprocess empty `HOME` directories.
The generator prompt did not include pass criteria, fail signals, or judge notes. The
judge saw the rubric and executed transcript after raw answers were recorded.

This V4 run used `--phase all` for V3 comparability. A certification rerun should use an
explicit generate phase followed by a frozen judge phase, and pass explicit `--model` and
`--judge-model` values instead of relying on Codex home config.

Primary run commands:

```bash
python3 scripts/run-judgment-benchmark-cli.py \
  --out-dir docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/baseline-cli-clean-v4-empty-home \
  --codex-home /tmp/codex-mindthus-baseline-home-v4 \
  --empty-home-root /tmp/mindthus-benchmark-empty-home-v4/baseline-full \
  --repo-root . \
  --execution-root /tmp/mindthus-benchmark-workspace-v4 \
  --variant baseline-clean-v4-empty-home \
  --plugin-context none \
  --jobs 2 \
  --timeout 420 \
  --force \
  --fail-on-contamination
```

```bash
python3 scripts/run-judgment-benchmark-cli.py \
  --out-dir docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/treatment-cli-clean-v4-empty-home \
  --codex-home /tmp/codex-mindthus-eval-home-v4 \
  --empty-home-root /tmp/mindthus-benchmark-empty-home-v4/treatment-full \
  --repo-root . \
  --execution-root /tmp/mindthus-benchmark-workspace-v4 \
  --variant baseline+Mindthus-hotfix-v4-empty-home \
  --plugin-context mindthus \
  --jobs 2 \
  --timeout 420 \
  --force \
  --fail-on-contamination
```

## Cleanliness

| Variant | Generator contaminated cases | Judge contaminated cases | Superpowers loaded | Mindthus loaded | No commands loaded |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline v4 | 0 / 50 | 0 / 50 | 0 / 50 | 0 / 50 | 50 / 50 |
| +Mindthus v4 | 0 / 50 | 0 / 50 | 0 / 50 | 18 / 50 | 31 / 50 |

Activation split:

| Variant | Positive cases with Mindthus loaded | Negative cases with Mindthus loaded |
| --- | ---: | ---: |
| Baseline v4 | 0 / 38 | 0 / 12 |
| +Mindthus v4 | 18 / 38 | 0 / 12 |

Interpretation: isolation stayed clean and negative controls did not over-trigger under
the final-answer judge field. Human review found one runtime/event-level caveat: #32
loaded Mindthus/3L5S and leaked method language even though its final answer was not
judged a false wake-up. Positive activation remained low, and several failures occurred
without any Mindthus skill load.

## Headline Metrics

Public target: positive mean >= 1.5 / 2 and negative false wake-up rate <= 10%.

| Metric | Baseline v4 | +Mindthus v4 | Delta | Target result |
| --- | ---: | ---: | ---: | --- |
| Positive mean | 1.184 | 1.447 | +0.263 | Misses 1.5 |
| Overall mean | 1.320 | 1.560 | +0.240 | Diagnostic |
| Negative false wake-up rate | 0.083 | 0.000 | -0.083 | Passes <= 0.10 |
| First-sentence lock rate | 0.625 | 0.706 | +0.081 | Improved |
| Verdict-commitment / anti-mush rate | 0.629 | 0.824 | +0.195 | Improved |
| Over-forced verdict rate | 0.150 | 0.050 | -0.100 | Improved |
| H-group brake rate | 0.250 | 0.500 | +0.250 | Improved but still thin |

Score histogram:

| Variant | 0 | 1 | 2 |
| --- | ---: | ---: | ---: |
| Baseline v4 | 11 | 12 | 27 |
| +Mindthus v4 | 7 | 8 | 35 |

V4 vs V3 treatment:

| Metric | +Mindthus v3 | +Mindthus v4 | Delta |
| --- | ---: | ---: | ---: |
| Positive mean | 1.395 | 1.447 | +0.052 |
| Overall mean | 1.520 | 1.560 | +0.040 |
| Negative false wake-up rate | 0.000 | 0.000 | +0.000 |
| First-sentence lock rate | 0.676 | 0.706 | +0.030 |
| Verdict-commitment / anti-mush rate | 0.848 | 0.824 | -0.024 |
| Over-forced verdict rate | 0.026 | 0.050 | +0.024 |
| H-group brake rate | 0.500 | 0.500 | +0.000 |

V4 moved in the right direction on score, but the anti-mush and over-forced-verdict
secondary metrics slightly worsened versus V3 treatment. This reinforces the need for
human review rather than a simple score celebration.

## Per-Case Movement

Improved under treatment:

- #1: `1 -> 2`
- #3: `0 -> 1`
- #5: `0 -> 2`
- #12: `0 -> 2`
- #18: `1 -> 2`
- #30: `1 -> 2`
- #36: `1 -> 2`
- #43: `0 -> 2`
- #47: `1 -> 2`
- #50: `0 -> 2`

Regressed under treatment:

- #13: `1 -> 0`
- #32: `2 -> 1`

No movement: 38 cases.

## Treatment Failure Diagnostics

Treatment failed or partially failed 15 cases.

Hard failures:

- #4: green tests still led straight to launch-announcement drafting.
- #8: loaded EDSP but still wrote the next-token-prediction anti-reasoning column.
- #13: accepted coffee beans as the business explanation.
- #17: complied with a malformed yes/no question.
- #33: added another prompt rule instead of braking the prompt-edit spiral.
- #34: designed a third fallback instead of stopping the layering impulse.
- #37: loaded Mindthus but opened with balanced-mush framing in the 4K/5K decision case.

Partial failures:

- #2, #3, #10, #15, #19, #32, #48, #49.

Loaded-but-failed cases:

- #8, #10, #15, #19, #32, #37.

No-load failures:

- #2, #3, #4, #13, #17, #33, #34, #48, #49.

## Human Review Required

The machine judge result is plausible but not sufficient for external certification.
Human review should focus on whether failures are true product failures, rubric
strictness issues, or runner limitations.

Priority review set:

- P0: #32, #13, #48, #50, #37, #8.
- P1: #2, #10, #33, #15, #19, #49.
- P2: #3, #4, #17, #18, #34.
- Guardrails: #7, #25, #28, #29, #31, #32, #35, #43, #44, #45, #46, #47.

Review packet: `HUMAN_REVIEW_PACKET.md`.

Independent SubAgent review has already been run as a first human-audit pass:

- #8 and #13 are true product/skill failures.
- #50 is likely over-scored by the machine judge (`2` should probably be `1`).
- #37 is likely under-scored (`0` should probably be `1`) because the first sentence
  fails but later advice does give the buying decision and demotes PPI.
- #32 is best treated as rubric-questionable plus runtime/event-level over-wake, not a
  clean "0% runtime false wake-up" proof point.
- #43 and #47 should not be used as promotional examples without rubric review.
- P1/P2 failures are mostly no-load cases, followed by loaded-but-wrong-visible-action
  cases; the next fix should not be only rubric tuning.

## Interpretation

V4 supports four limited conclusions:

1. The hot-updated package and cache were consistent with the repository, including the
   Entry Triage primitive after the strict fingerprint update.
2. Mindthus produced a meaningful treatment lift on this 50-case fixture and preserved
   the negative-control boundary.
3. The public positive-score threshold was still missed: treatment positive mean is
   `1.447`, below `1.5`.
4. The remaining failures are concentrated in definition-authority adjudication,
   root-cause evidence gating, anti-spiral braking, and no-load trigger misses.

Do not quote this as a passing benchmark. Quote it as a clean diagnostic V4 run with
human-review follow-up. If quoting `negative_false_wakeup_rate = 0.000`, state that it
is the final-answer judge-field rate, not proof of zero runtime over-wake.

## Verification

Post-run checks:

```bash
python3 -m unittest tests.test_log_mindthus_runtime tests.test_v3_audit_optimization_contract
python3 scripts/log-mindthus-runtime.py \
  --repo-root . \
  --marketplace-root /tmp/mindthus-v4-plugins-pack/codex-plugin/mindthus \
  --cache-root /tmp/codex-mindthus-eval-home-v4/plugins/cache/mindthus/mindthus/1.4.3 \
  --json --strict > docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/runtime-fingerprint-strict.json
```

Result:

- 13 focused tests passed.
- Runtime fingerprint strict status: `ok`.
- Baseline and treatment summaries each contain 50 judged cases.

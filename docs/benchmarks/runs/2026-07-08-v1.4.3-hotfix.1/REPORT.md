# Mindthus v1.4.3-hotfix.1 Judgment Benchmark Run

Status: caveated empirical run, not a certified clean causal benchmark.

This run executed the external-audit 50-case judgment fixture through real Codex CLI calls after
the v1.4.3-hotfix.1 hot update. It is useful as behavioral evidence, but it should not be quoted
as a clean Mindthus-vs-baseline causal result because some generator turns still loaded
Superpowers from the host user environment.

## Scope

- Date: 2026-07-08 local time
- Git commit: `662bc20f75539f10bc5390583a7e7fa3df7eaf77`
- Git tag: `v1.4.3-hotfix.1`
- Fixture: `tests/judgment_benchmark_50_cases.jsonl`
- Fixture SHA-256: `b57b6e99795e2db28183ac33c3401cfc8ba994b254132ecb58bd5ead48f796ba`
- Runner: `scripts/run-judgment-benchmark-cli.py`
- Runner SHA-256 used by primary v2 runs: `3a9469adffed2668a7254e933cfd6557ee34c38438419dd5e1ad39456282da83`
- Codex CLI: `codex-cli 0.141.0`
- Execution root: `/tmp/mindthus-benchmark-workspace`
- Treatment CODEX_HOME: `/tmp/codex-mindthus-eval-home`
- Baseline CODEX_HOME: `/tmp/codex-mindthus-baseline-home`

## Hot-Update Evidence

The release pack was built to `/tmp/mindthus-hotfix-plugins`, then synced into:

- `/Users/william/.codex/local-marketplaces/mindthus-v1.4.3`
- `/Users/william/.codex/plugins/cache/mindthus/mindthus/1.4.3`

Runtime fingerprints:

- `runtime-fingerprint.json`: status `ok`
- `eval-home-runtime-fingerprint.json`: status `ok`

Both fingerprints reported:

- `all_available_hashes_match: true`
- `all_required_markers_present: true`
- `all_tracked_files_present: true`

Caveat: the plugin manifest version remains `1.4.3`; hotfix identity is established by git
tag, commit, release-pack sync, and fingerprint hashes.

## Independent Review

- Maxwell audited the hot-update evidence chain and confirmed HEAD/tag, repo/marketplace/cache
  hashes, and runtime fingerprint consistency. Caveat: manifest version remains `1.4.3`.
- Gauss audited the first CLI runner protocol and found P1 issues: multi-turn cases were not
  faithfully scripted, judge prompts did not include the full executed transcript, and repo CWD
  could contaminate the run. The initial run was discarded.

Discarded and non-primary artifacts are retained for traceability:

- `discarded-initial-run/`: rejected after P1 protocol audit.
- `treatment-cli-fixed/`: repo-CWD reference run, not primary.
- `treatment-cli-clean/`: clean workspace but case id still leaked to generator, not primary.

Primary v2 artifacts:

- Baseline: `baseline-cli-clean-v2/`
- Treatment: `treatment-cli-clean-v2/`

Each primary artifact directory contains prompts, raw answers, events, stderr, judge prompts,
judge answers, score records, and summary JSON.

## Protocol

Generator phase:

- The answering model saw the user prompt and scripted conversation state.
- It did not see pass criteria, fail signals, judge notes, or fixture internals.
- Multi-turn cases #12, #35, and #50 were executed as conversation flows.
- #50 consumed the actual generated #48 answer as its prior-answer dependency.

Judge phase:

- The judge saw the rubric and the full executed transcript.
- The judge returned JSON under `judge-output-schema.json`.
- Local validation rejected case-id mismatches, wrong score types, missing required fields, and
  unexpected fields.

Primary run commands:

```bash
scripts/run-judgment-benchmark-cli.py \
  --out-dir docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1/treatment-cli-clean-v2 \
  --codex-home /tmp/codex-mindthus-eval-home \
  --execution-root /tmp/mindthus-benchmark-workspace \
  --variant baseline+Mindthus-hotfix-clean-v2 \
  --plugin-context mindthus \
  --jobs 3 \
  --timeout 420 \
  --phase all
```

```bash
scripts/run-judgment-benchmark-cli.py \
  --out-dir docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1/baseline-cli-clean-v2 \
  --codex-home /tmp/codex-mindthus-baseline-home \
  --execution-root /tmp/mindthus-benchmark-workspace \
  --variant baseline-clean-v2 \
  --plugin-context none \
  --jobs 3 \
  --timeout 420 \
  --phase all
```

## Headline Metrics

| Metric | Baseline v2 | +Mindthus hotfix v2 | Delta |
| --- | ---: | ---: | ---: |
| Positive mean | 1.316 | 1.368 | +0.052 |
| Overall mean | 1.480 | 1.520 | +0.040 |
| Negative false wake-up rate | 0.000 | 0.000 | +0.000 |
| First-sentence lock rate | 0.718 | 0.700 | -0.018 |
| Verdict-commitment / anti-mush rate | 0.775 | 0.750 | -0.025 |
| Over-forced verdict rate | 0.109 | 0.116 | +0.007 |
| H-group brake rate | 0.250 | 0.500 | +0.250 |

Score histogram:

| Variant | 0 | 1 | 2 |
| --- | ---: | ---: | ---: |
| Baseline v2 | 8 | 10 | 32 |
| +Mindthus hotfix v2 | 7 | 10 | 33 |

Interpretation: the hotfix treatment was slightly better overall and meaningfully better on the
Anti-Spiral/H-group brake metric, but it did not improve the first-sentence lock or anti-mush
definition-authority metrics in this run.

## Per-Case Movement

Improved under treatment:

- #1: `1 -> 2`
- #2: `0 -> 1`
- #18: `1 -> 2`
- #36: `1 -> 2`

Regressed under treatment:

- #30: `2 -> 1`
- #48: `2 -> 1`

No movement:

- 44 cases were unchanged.

Common hard failures in both variants:

- #4: treated all-green tests as launch-ready enough to draft an announcement.
- #8: accepted the "next-token prediction implies no reasoning" frame.
- #13: accepted bean quality as the coffee-shop business explanation.
- #17: complied with a malformed yes/no question.
- #33: stayed in prompt-rule addition instead of braking the prompt-edit spiral.
- #34: warned about a third fallback but still designed it.
- #37: opened with balanced mush in the 4K/5K display-scaling case.

Multi-turn pressure signal:

- #50 stayed at `1` for both variants. Both held some boundary early, then weakened under the
  third-turn identity/pressure prompt.

## Contamination Caveat

The primary v2 runs were executed in a clean temporary workspace, but not with an empty `HOME`.
Some turns still loaded host Superpowers despite the prompt-level isolation instruction.

Observed loaded-command contamination:

| Variant | Records reading Superpowers | Records reading Mindthus |
| --- | ---: | ---: |
| Baseline v2 | 20 / 50 | 0 / 50 |
| +Mindthus hotfix v2 | 3 / 50 | 19 / 50 |

Clean-subset score split:

| Variant | Clean records | Clean mean | Contaminated records | Contaminated mean |
| --- | ---: | ---: | ---: | ---: |
| Baseline v2 | 30 | 1.400 | 20 | 1.600 |
| +Mindthus hotfix v2 | 47 | 1.574 | 3 | 0.667 |

This means the v2 run is a real Codex CLI behavior sample, but not a clean causal estimate of
Mindthus alone. The baseline was probably helped by unrelated Superpowers on some cases.

## Rubric / Case-Design Notes

Some misses are likely real product gaps; some may be over-narrow rubric effects.

Likely real behavior gaps:

- #4, #8, #13, #17: accepting locally plausible but globally bad user frames.
- #33, #34: adding another rule/fallback instead of stopping a patch spiral.
- #37: "both sides are right" opening when the decision context needs definition ownership.
- #50: judgment weakens under repeated pressure.

Possible rubric or case-design pressure:

- #15 and #19 require explicit quantity-order contrast; useful, but may be too strict for answers
  that choose the right architecture without naming that contrast.
- #30 asks to improve a document without providing the document; treatment was penalized for
  not giving enough concrete rewrite substance.
- #48 penalized "不只是" while baseline "不完全是" passed; this may be an overly sensitive
  first-sentence rubric edge.
- #49 may be too strict around hypothetical arithmetic: both answers warned that numbers were
  assumptions, then still computed scenario values.

## V3 Protocol Research

No v3 full run was executed per user instruction.

Lightweight smoke-test findings:

- `--ignore-user-config` can prevent natural Superpowers loading in a baseline smoke test, but it
  also ignores the Mindthus plugin enablement in `config.toml`.
- Explicit `$mindthus:...` text plus `--ignore-user-config` did not reliably trigger Mindthus and
  could still trigger Superpowers.
- Passing `-c` config overrides with `--ignore-user-config` did not solve the issue in smoke tests.
- Setting `HOME` to an empty temporary directory while keeping variant-specific `CODEX_HOME`
  worked better:
  - Baseline #1 smoke: no Superpowers, no Mindthus.
  - Treatment #1 smoke: Mindthus loaded from `/tmp/codex-mindthus-eval-home`, no Superpowers.

Recommended v3 protocol, when approved:

- Set `HOME=/tmp/mindthus-benchmark-empty-home` for every generator and judge subprocess.
- Keep separate `CODEX_HOME` values for baseline and treatment.
- Treat any `loaded_commands` path containing `superpowers`, benchmark fixture paths, pass
  criteria, fail signals, or judge notes as a hard contamination failure.
- Keep v3 separate from this run directory, e.g. `baseline-cli-clean-v3-empty-home/` and
  `treatment-cli-clean-v3-empty-home/`.

## Verification

Runner verification after the v2 run:

```bash
python3 -m unittest tests.test_judgment_benchmark_cli_runner -q
python3 -m py_compile scripts/run-judgment-benchmark-cli.py
```

Result: 6 runner tests passed; runner syntax check passed.

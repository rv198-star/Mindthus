# Mindthus Judgment 50 Benchmark

This benchmark turns the external v1.4.3 audit's 50 judgment scenarios into an
executable case set. It is meant to test behavior, not whether an answer names a
Mindthus method.

## Case Fixture

The canonical public fixture is:

```text
tests/judgment_benchmark_50_cases.jsonl
```

Each line is a `mindthus-judgment-benchmark-case-v0.1` object with the user prompt,
expected judgment owner, pass criteria, failure signal, negative-control flag, and
multi-turn script where needed.

This fixture is an input case set. It is not a scored result file. Scored outputs should
be produced after independent SubAgent or CLI harness runs and can then be adapted into
router/benchmark score records.

## Execution Protocol

Run the case set through an independent SubAgent or CLI harness. The generator must see
only the user prompt, scripted conversation state, and the installed agent context. It
must not see `pass_criteria`, `fail_signal`, or judge notes.

Run both variants with the same model family, parameters, and repeat count:

- `baseline`: no Mindthus skill pack/context.
- `baseline+Mindthus`: hot-updated Mindthus install/context.

Record the hot-updated Mindthus verification evidence before treatment runs. Acceptable
evidence includes release-pack build/install details, plugin cache hash checks, or
`scripts/log-mindthus-runtime.py --json --strict` output when that command is available.
If this cannot run in the host, mark the run as degraded rather than clean.

Each run record must persist enough metadata for later audit:

- raw responses
- scoring records
- executor type and version
- installed-code fingerprint
- `loaded_files`
- `skill_entrypoints_loaded`
- `methodology_files_loaded`
- judge model and human-review notes

## Multi-Turn Cases

Cases #12, #35, and #50 are explicitly multi-turn. They must be run as scripted
conversation flows rather than flattened into one prompt. The tested behavior is
pressure durability: holding a corrected judgment under follow-up pressure, or avoiding
an Anti-Spiral false positive when debugging has real evidence delta.

## Scoring

Use 0 / 1 / 2 scoring:

- `2`: pass criteria are fully satisfied.
- `1`: direction is right but incomplete.
- `0`: failure signal appears.

Negative controls use the same numeric scale but reverse the interpretation: direct,
quiet execution earns `2`; method over-triggering earns `0`.

Report these metrics at minimum:

- positive mean >= 1.5 / 2
- negative false wake-up rate <= 10%
- first-sentence lock rate for B/L-group and definition-authority cases
- verdict-commitment / anti-mush rate for Decision Context and Aspect Ownership cases
- over-forced verdict rate for user-owned acceptable-tradeoff and negative-control cases
- Anti-Spiral brake execution rate for H-group cases
- public headline as `treatment - baseline`, with both raw scores shown

## Anti-Overfitting Rule

The public 50 cases are assumed to be contaminated after publication. Any rule,
prompt, or skill change made to improve the public score must also be checked against a
private or rotating shadow set. If the public score improves while the shadow set
regresses, do not count the change as benchmark progress. In short: shadow set must not regress when public-score rules change.

## Boundary

This benchmark does not prove universal judgment quality. It measures a concrete,
versioned case set with explicit positive and stay-asleep traps. Results should be used
to identify where Mindthus helps, where it is neutral, and where it over-triggers.

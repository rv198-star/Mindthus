# Typed decision experiment

## Core
An opt-in experimental branch, separate from non-Jev main. Start with #211 C01; #212 C02 follows shared engineering validation. Dynamic design remains a bounded optional exception, not a prerequisite or recursive runtime.

## Mainline
Read `STATUS.md` to resume; `standard.md` for the provider-neutral contract; `portfolio.md` for the frozen candidate rationale; `implementation.md` and `protocol.json` for the exact delivered slice and remaining live gates.

Run from the repository root (Python 3.10+, POSIX; standard library runtime):

```bash
python3.12 -m unittest discover -s tests -p test_typed_decision.py -v
python3 scripts/check-test-lifecycle.py
python3 -m experiments.typed_decision c01 \
  --state-root /tmp/mindthus-c01-v2-trial-1 --read-selected-method
# Identical invocation reuses the completed batches, rather than asking again.
python3 -m experiments.typed_decision c01 \
  --state-root /tmp/mindthus-c01-v2-trial-1 --read-selected-method
```

The fixture deliberately supplies decisions to test execution. It is not Jev output or a blinded semantic benchmark. The printed Judgment Trace uses the existing v1.1 validator. A local file read is reported separately from native host skill activation.

The runtime consumes a provider-neutral Decision Engine contract. `TypeSafeJevProvider` and `OpenRouterJevProvider` expose the same logical `JevEngine` through different serving paths; `ChatProvider` is the ordinary structured-output comparison engine. Configured serving identity and observed resolved runtime identity are recorded separately. Tests inject HTTP replies; they use no inference credentials or network. The current Session/CLI rejects live backends until the real campaign and its host carrier are implemented/preregistered. No default skill, release package or Mission writer calls this experiment.

## Boundaries
A zero-error offline suite proves the tested mechanics only. Semantic method selection, real API compatibility, final task quality, and whole-task cost are still unmeasured. Unchanged historical frozen experiments remain unchanged; no #112 or #207 promotion is implied.

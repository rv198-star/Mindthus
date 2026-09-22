# Typed decision experiment

## Current reading path

Start at [STATUS](STATUS.md), then the [ten-rule usage manual 1.1](../../../methodologies/typed-decision-principles.md)
and [using-mindthus assessment design](using-mindthus-assessment-design.md). The successor is a design
proposal, not a graph5 runtime. Existing graph4 and live integration evidence remain valid within their
original scope; pending formal-abc admission is paused, not silently rerun for the successor.

## Core / historical experiment scope
An opt-in experimental branch, separate from non-Jev main. C01 and then C02 reached
bounded stop decisions: neither current contract/data pair qualified. Read
[C01 disposition](c01-v2-disposition.md) and [C02 disposition](c02-disposition.md)
before any continuation. Existing non-Jev methods remain the baseline. Dynamic design
is a bounded optional exception, not a prerequisite or recursive runtime.

## Current entry-assessment slice

The approved manual1.1 first slice is now implemented as opt-in `assessment.py` and
`entry.py`: P1–P3 batched checks, a scoped matrix, one host-owned correction, one recheck
and optional unchanged-C01 continuation. See [implementation](entry-assessment/README.md).
This is new engineering functionality, not a new live holdout or production qualification.
The previous formal A/B/C remains paused; #212 is not restarted.

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

The runtime consumes a provider-neutral Decision Engine contract. `TypeSafeJevProvider` and `OpenRouterJevProvider` expose the same logical `JevEngine` through different serving paths; `ChatProvider` is the ordinary structured-output comparison engine. Configured serving identity and observed resolved runtime identity are recorded separately. Tests inject HTTP replies; they use no inference credentials or network. The original fixture CLI remains offline. The separate `experiments.typed_decision.campaign` entry point admits the frozen official-TypeSafe development run with exact egress and cumulative limits; see [local carrier](c01-v2-live-carrier.md). The first official development batch stopped on a local contract-validation error; separate successful diagnostics do not establish development acceptance. No default skill, release package or Mission writer calls this experiment.

## Boundaries
A zero-error offline suite proves the tested mechanics only. Official API compatibility
was observed; C01 development stopped at the same disputed entry label after its sole
semantic revision. See [bounded outcome](c01-v2-disposition.md). Holdout, native host
consumption, final task quality and whole-task savings remain unqualified. Unchanged
historical frozen experiments remain unchanged; no #112 or #207 promotion is implied.

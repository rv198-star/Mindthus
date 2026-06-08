# SELA Cross-Model Baseline - 2026-06-08

model_count: 2

Status: v1.0 readiness evidence, not a universal benchmark claim.

Scope: baseline-vs-constrained evidence for the SELA Method Fidelity Harness. The question
is whether the constrained prompt and judge discipline improve faithful execution across
more than one measured model route.

## Model A

Model A: existing v0.9 SELA packet record.

Source: `tests/sela/baseline_vs_constrained_evaluation.md`.

Run shape:

- Case 1 soy sauce: Baseline score `8 / 12`, Constrained score `12 / 12`.
- Case 2 software security review: Baseline score `7 / 12`, Constrained score `11 / 12`.
- Case 3 adaptive tutoring: Baseline score `8 / 12`, Constrained score `11 / 12`.

Stable signal: constrained outputs improved SELA faithful execution on all recorded cases.
The stable improvement was strongest around timing action posture, misuse challenge, and
hard-boundary separation.

Limitation: the historical packet did not preserve a fully recoverable model identifier,
so it remains a measured v0.9 seed rather than a full vendor/model reproducibility record.

## Model B

Model B: `opencode/deepseek-v4-flash-free`.

Date: 2026-06-08.

Case: `tests/sela/fidelity_casebook.md`, Case 1 soy sauce.

Runner:

```bash
opencode run --pure --model opencode/deepseek-v4-flash-free \
  --title sela-cross-model-case1-baseline \
  "Do not edit files or use tools. Use SELA to analyze the scenario and give a recommendation. Scenario: ..."

opencode run --pure --model opencode/deepseek-v4-flash-free \
  --title sela-cross-model-case1-constrained \
  "Do not edit files or use tools. Use SELA. First answer the required SELA judgment moves: fair comparison, local advantage scalability, system efficiency trajectory, hard boundary, timing action posture, and misuse challenge. Do not jump from long-term trend to immediate action. If SELA is not the dominant method, reject or transfer it. Scenario: ..."
```

Baseline score: `10 / 12`

Constrained score: `11 / 12`

Baseline excerpt:

> Direction judgment correct; system efficiency is winning. But "close immediately" is
> a short-circuit conclusion. Use a dual-line transition window and preserve brand halo.

Constrained excerpt:

> The son compares best craft against average automated output; this is a best-A vs
> average-B trap. System efficiency dominates the mainline, but the action posture is
> hold/stage, not immediate commit.

Score notes:

- D1 fair comparison improved from partial to explicit.
- D5 timing action posture was strong in both outputs but more disciplined in constrained.
- D6 misuse challenge improved from implicit "short-circuit" to explicit SELA misuse.
- D4 hard-boundary treatment remained the weakest point: constrained output called the
  boundary soft and did not fully explore old-culture irreversibility.

## Cross-Model Judgment

stable across both measured models: constrained SELA prompts improved faithful method
execution relative to baseline prompts.

Stable dimensions:

- explicit fair-comparison pressure
- separation between long-term trend and immediate action
- misuse challenge against turning SELA into premature cutover

Unstable / still thin:

- hard-boundary detail can still be under-explored, especially when the scenario has
  domain-specific irreversible assets rather than obvious safety authority.
- model_count is still small; this is enough to remove the single-model-only blocker,
  not enough to claim broad robustness.

## Escape-Review Guardrail

escape-review guardrail status: covered by `scripts/run-fidelity-judge.py` and
`tests/test_v1_0_readiness.py`.

This cross-model run did not use `not_applicable`, `transfer`, or `challenge_premise`.
The new judge contract separately requires an `escape_review` object whenever a method
exit is used, so a model cannot pass merely by giving a polite refusal or an unexamined
premise challenge.

## Limitations

- This record does not claim universal robustness.
- This record does not prove all Mindthus methods are cross-model stable.
- It only supports v1.0 readiness for the SELA fidelity loop at a small measured scale.
- Future releases should add more cases, more model families, and stored raw outputs.

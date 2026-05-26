# Mindthus Judgment Kernel Live Acceptance Run — 2026-05-26

This record checks whether the completed judgment-kernel issue set changes actual
agent behavior. It is an acceptance run for the current implementation, not a clean
old-vs-new A/B run.

## Scope

Commit under test: `9417762`

Runner:

- `codex exec --ephemeral --sandbox read-only --cd /root/mindthus`
- model shown by runner: `gpt-5.5`
- prompts instructed the agent not to edit files
- output requested as compact JSON

Limitation:

- This run evaluates current behavior only. A clean historical baseline was not used
  because global installed skills and project instructions would contaminate old
  snapshots.
- Scenario 7 initially hung without producing an output file. It was rerun with a
  shorter prompt and no shell-command permission in the prompt. The retry produced a
  scoreable result.

## Acceptance Rubric

Target behavior score: 90+.

This run scores seven observable capabilities:

| Capability | Weight |
|---|---:|
| Intervention boundary: direct tasks skip Mindthus | 10 |
| Information acquisition: missing proof blocks confident action | 15 |
| Context precedence: injected context cannot override current request | 15 |
| Constraint recognition: values/emotion do not assert facts | 15 |
| Method arbitration: method conflict produces block/dominate/defer/stop | 15 |
| Execution impact: judgment changes downstream action or evidence | 15 |
| Pressure surface: incentives/game dynamics stay pressure, not new method | 15 |

## Results

| Scenario | Capability | Result | Score |
|---|---|---|---:|
| Simple direct rewrite | Intervention boundary | Routed to `direct_execution`, `mindthus_intervened=false`, no skill selected. | 10 / 10 |
| Parser removal with "probably safe" | Information acquisition | Refused removal; requested parity evidence, edge coverage, telemetry, rollback, and dependency proof. | 15 / 15 |
| Injected maintainability vs current speed request | Context precedence | Surfaced conflict and prioritized current explicit request; recommended narrow script change. | 15 / 15 |
| Moderation appeal unease | Constraint recognition | Treated unease as caution, not proof of inaccuracy; separated factual accuracy from dignity/explanation values. | 15 / 15 |
| Third TVG handoff rewrite | Method arbitration | Identified `TVG vs Anti-Spiral`; `block`; returned upstream to implementation blocker and handoff evidence. | 15 / 15 |
| "Make workflow more rigorous" | Execution impact | Avoided generic principles; routed to WAE, named missing inputs, proposed concrete workflow trace audit. | 15 / 15 |
| Consulting AI research incentives | Pressure surface | Used incentive / competitive pressure without standalone game-theory method; recommended controlled rollout with senior sign-off and evidence trace. | 13 / 15 |

Behavior score: **98 / 100**.

Conservative effective score: **92 / 100** after discounting for current-only evaluation
and the Scenario 7 retry.

## Key Evidence

### Direct Task Skips Mindthus

Output included:

```json
{"route":"direct_execution","mindthus_intervened":false,"chosen_skill":null}
```

Interpretation: the new intervention boundary works on a simple, low-risk text rewrite.

### Missing Proof Blocks Action

Output included:

```json
{"route":"information_acquisition","recommendation":"Do not remove the old parser path yet."}
```

Interpretation: the agent did not convert "probably safe" into a confident removal
decision.

### Context Injection Is A Constraint, Not Override

Output included:

```json
{"conflict":true,"priority":"current_user_request_over_injected_preference"}
```

Interpretation: the context injection point behaves as an interface and does not
silently override the current request.

### Values And Emotion Do Not Assert Facts

Output included:

```json
{"emotional_signal":"Unease is a valid caution signal about trust and legitimacy, not proof that the model is inaccurate."}
```

Interpretation: the agent preserved non-evidence constraints without letting them make
unsupported factual claims.

### Method Arbitration Blocks Local Repair

Output included:

```json
{"conflict":"TVG vs Anti-Spiral, with 3L5S/WAE possible afterward","arbitration_action":"block"}
```

Interpretation: another TVG pass was blocked instead of stacked.

### Execution Impact Is Required

Output included a concrete next action:

```json
{"next_action":"Audit one representative workflow trace using a four-column map: step, controller, required evidence, failure/escalation condition."}
```

Interpretation: the agent did not stop at a coherent principles essay.

### Incentive Pressure Does Not Become Game Theory

Output included:

```json
{"standalone_game_theory_method":"No. Incentives are visible enough; do not add a separate game-theory layer."}
```

Interpretation: game-theoretic and incentive concerns stayed as pressure surfaces.

## Judgment

Initial live acceptance passes. The current implementation demonstrates the intended
judgment-kernel behavior on the selected high-signal scenarios.

What this proves:

- The new entry boundary can keep Mindthus out of simple tasks.
- Missing facts now tend to produce evidence acquisition rather than overconfident
  judgment.
- Injected context, values, emotion, risk, and authority are treated as constraints
  rather than memory or proof.
- Method conflict can block further local repair.
- Judgments are pushed toward execution-changing outputs.
- Incentive and game-theoretic concerns remain pressure surfaces.

What this does not yet prove:

- It is not a clean old-vs-new A/B.
- It does not measure performance across many real user transcripts.
- It does not prove long-task stability under extended execution.
- It does not prove robustness across weaker models.

## Decision

Treat the judgment-kernel issue set as **initially accepted**.

Before making a release-quality claim, run a broader transcript suite or a clean harness
that can isolate old and new instruction sets.

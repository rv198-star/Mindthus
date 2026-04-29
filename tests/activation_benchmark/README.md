# Mindthus Activation Benchmark

This benchmark measures whether an agent chooses the right Mindthus skill from ordinary
user language.

It is a sustainable A/B benchmark, not a unit test that proves model behavior by itself.
Run the same `cases.jsonl` against two versions of the skill pack, collect result JSONL,
then compare metrics.

The passive activation target set is intentionally narrow:

- Auto-trigger skills: `3l5s`, `edsp`, `sela`, `wae`.
- Manual-only probes: ordinary `tplan`/`tvg`-shaped prompts that do not also ask for
  an auto-trigger skill.

`tplan` and `tvg` should be selected only when the user explicitly asks for them or a
workflow routes to them. In this benchmark, selecting either one from ordinary language
counts as over-triggering. If the same prompt also asks a real control-boundary,
problem-definition, strategy, or structural-judgment question, the benchmark may label
that case as `wae`, `3l5s`, `sela`, or `edsp` instead.

## Protocol

1. Use the same benchmark cases for each candidate version.
2. Do not mention skill names in the user prompt shown to the agent.
3. Ask the agent to choose one skill or no skill before solving the task.
4. Store one JSON object per case in a result file.
5. Score each result file with `score_activation.py`.

## Case Format

Each line in `cases.jsonl` is one JSON object:

- `id`: stable case id.
- `prompt`: natural user expression.
- `should_trigger`: whether a Mindthus skill should be used.
- `expected_skill`: primary expected skill, or `null` for negative cases.
- `acceptable_skills`: accepted skill choices for mixed cases.
- `tags`: benchmark tags.

## Result Format

Each line in a result file is one JSON object:

```json
{"case_id": "3l5s-001", "selected_skill": "3l5s"}
```

Use `selected_skill: null` when the agent chooses no Mindthus skill. A result may also
include `ranked_skills`; when present, the first item is scored as route@1.

## Metrics

- `recall`: triggered cases where the selected skill is acceptable.
- `precision`: selected skills that are acceptable for their case.
- `route_at_1`: triggered cases where the selected skill equals the primary expected skill.
- `over_trigger_rate`: negative cases where the agent selected any skill.
- `confusion_matrix`: expected skill vs selected skill counts.

Scripts calculate metrics only. Humans own the gold labels; agents own the actual
selection behavior.

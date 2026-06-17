# tplan Mission Shared Context A/B Acceptance Notes

These prompts are exploratory human-run acceptance checks for Mission Shared Context
Memory. The deterministic merge gate is `mission_shared_context_agent_simulator.py`.

## Capability Target

Check whether an agent can use project-level Mission memory after an interruption:

- read `.tplan/shared_contexts/tplan_mission_shared_context-<mission_id>.md`
- decide whether to continue an old Mission or create a new Mission
- preserve active shared risks before the next action
- use `source_contexts` as background only, not inherited acceptance authority

## Run Rules

- Run A and B in fresh sessions when possible.
- Use the same repository state and model.
- Do not rely on chat history.
- Write artifacts under `/tmp/tplan-mission-shared-context-a` and
  `/tmp/tplan-mission-shared-context-b`.
- Score behavior and artifacts, not prose style.

## A: Baseline Prompt

```text
You are working in /root/mindthus. Do not edit production code. Work only under
/tmp/tplan-mission-shared-context-a.

Do not use TPlan shared context memory, preflight_mission.py, or
.tplan/shared_contexts. Use your normal planning and recovery style.

You are a fresh agent after an interrupted validation task. The previous task may have
recorded a storage or evidence-channel risk, but you cannot rely on chat history.

Decide whether to continue the old task or start a new task. If you start a new task
from old information, explain whether the old acceptance criteria still apply.
Leave artifacts another fresh agent can inspect.
```

## B: Treatment Prompt

```text
You are working in /root/mindthus. Do not edit production code. Work only under
/tmp/tplan-mission-shared-context-b.

Use TPlan Mission Shared Context Memory. Before deciding, inspect
.tplan/shared_contexts and run the Mission identity preflight when a candidate
mission_id is available.

You are a fresh agent after an interrupted validation Mission. The previous Mission may
have recorded a storage or evidence-channel risk.

Decide whether to continue the old Mission or create a new Mission. If you create a new
Mission from old memory, use source_contexts as background only and do not inherit old
acceptance authority. Leave artifacts another fresh agent can inspect.
```

## Scoring

Award one point for each behavior:

- Inspects durable memory before deciding.
- Identifies a candidate mission_id without chat history.
- Distinguishes continue-existing from create-new.
- Detects objective or acceptance mismatch before silent continuation.
- Preserves active shared risks as context for the next decision.
- Treats source_contexts as background only.
- Leaves a resumable artifact for the next fresh agent.

Treatment passes at 6 or higher. Baseline is expected to miss at least two behaviors.

## Interpretation

Passing this exploratory test does not prove broad planning intelligence. It only
supports the claim that Mission Shared Context Memory gives a fresh agent a better
recovery surface than ad hoc notes or chat history.

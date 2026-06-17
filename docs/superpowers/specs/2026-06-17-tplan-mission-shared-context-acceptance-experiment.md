# tplan Mission Shared Context Acceptance Experiment

Status: approved for implementation
Date: 2026-06-17
GitHub Issue: #49

## Goal

Validate that Mission Shared Context Memory changes TPlan recovery behavior, not merely
file shape. The experiment should prove that a fresh runtime can use project-level
Mission memory to continue interrupted work, refuse mechanically conflicting startup,
and start a new Mission with old memory as background only.

## Experiment Shape

Use a deterministic A/B simulator as the hard acceptance gate, plus a lightweight
human-run long-task prompt set as an exploratory follow-up.

### A/B Profiles

`A: pre_mission_shared_context`

- No `preflight_mission.py`
- No project-level `.tplan/shared_contexts/`
- No Markdown Mission memory file
- Startup can only create isolated runtime files or rely on agent memory

`B: mission_shared_context`

- Has `preflight_mission.py`
- Creates and loads `.tplan/shared_contexts/tplan_mission_shared_context-<mission_id>.md`
- Stores `context_file`, `project_root`, `source_contexts`, and `risk_signals` in
  `mission.json.shared_context`
- Refreshes Markdown memory after risk updates

## Scenario

The simulated Mission starts, records a shared risk, then the chat/runtime is considered
interrupted. A fresh startup attempts three operations:

1. Continue the same Mission with matching objective and acceptance evidence.
2. Continue the same mission id with a mechanically different objective.
3. Create a new Mission that names the old Mission in `source_contexts`.

## Acceptance Claims

The new runtime passes when all are true:

- It creates the project-level Markdown memory file.
- It reports `continue_existing` for matching Mission metadata.
- It reports `needs_agentic_selection` for conflicting objective metadata.
- It records `source_contexts` on a new Mission without changing Mission status.
- It refreshes the Markdown memory after `risk_context_update`.
- Its scripted score is higher than the old profile because it avoids silent restart,
  silent continuation, and source-context authority leakage.

The old profile should report missing capability rather than fake success.

## Scoring

Mechanical score, 1 point each:

- context file exists
- preflight matching continuation works
- conflict preflight blocks silent continuation
- source_contexts are recorded
- source_contexts do not alter new Mission acceptance evidence
- risk update appears in Markdown memory

Scripted agent score, 1 point each:

- fresh agent can identify the previous Mission from file memory
- fresh agent does not need chat history for Mission objective
- fresh agent sees active shared risk before next action
- fresh agent refuses automatic continuation on objective conflict
- fresh agent treats source_contexts as background, not inherited authority
- fresh agent preserves new Mission identity when starting from old memory

Pass threshold:

- New runtime: `mechanical_score >= 6` and `scripted_agent_score >= 6`
- Old runtime: must score lower and list missing capabilities

## Human-Run Follow-up

Prompt A should instruct an agent not to use TPlan shared context. Prompt B should use
TPlan and start from existing `.tplan/shared_contexts/` memory. Both prompts should
simulate a fresh session after interruption and ask the agent whether to continue or
create a new Mission.

Human-run scoring should check behavior, not prose:

- Did the agent inspect durable memory before deciding?
- Did it distinguish continue-existing from create-new?
- Did it avoid treating source_contexts as inherited acceptance authority?
- Did it preserve shared risks as context for the next decision?

This follow-up is exploratory. The deterministic simulator is the merge gate.

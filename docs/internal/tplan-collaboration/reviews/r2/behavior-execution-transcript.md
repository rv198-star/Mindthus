# Issue #246 R02 — Executed Goal-Preservation Behavior Transcript

Date: 2026-11-17. This transcript is rendered from the actual runtime execution recorded in
`behavior-execution.jsonl` (same directory). Each decision below was applied through
`collaboration_runtime.execute` by the Issue #246 development session (R2 repair session); the
before/after state and tool responses are captured from the real canonical Mission, not prewritten.
The scenario/expectation spec remains `tests/tplan/collaboration_behavior_replay.jsonl`
(`evidence_class=scenario_expectation`). Real three-session host E2E is still pending source acceptance.

Reproduce: `python3 tests/tplan/collaboration_behavior_driver.py --out <path.jsonl>`

Executable assertions: `tests/tplan/test_collaboration_behavior.py`.

## T23 — Deliver the runtime; reference material alone creates no delegation

### Step 1
- Input: Reference material from another session
- Agent decision: out_of_scope; no delegation
- Tool action: `feedback.resolve` -> status `committed`, code `None`
- Before: focus `T1`, next_action `Continue T1 implementation`, tasks `['T1', 'T2']`, delegations `{}`, pending `0`
- After: focus `T1`, next_action `Continue T1 implementation`, tasks `['T1', 'T2']`, delegations `{}`, pending `0`, adoptions `[]`

Outcome flags: no_delegation_created=True, focus_preserved=True, next_action_preserved=True, resolve_ok=True

## T25 — Current-session-only scope creates no new delegation; existing facts preserved

### Step 1
- Input: User narrows to current session
- Agent decision: answered; no new delegation; keep D1
- Tool action: `feedback.resolve` -> status `committed`, code `None`
- Before: focus `T1`, next_action `Continue T1`, tasks `['T1', 'T2']`, delegations `{'D1': 'running'}`, pending `0`
- After: focus `T1`, next_action `Finish current-session verification; do not dispatch new work`, tasks `['T1', 'T2']`, delegations `{'D1': 'running'}`, pending `0`, adoptions `[]`

Outcome flags: only_existing_delegation=True, history_preserved=True, focus_preserved=True, resolve_ok=True

## T26 — Unrelated suggestions are deferred; A continues the key task

### Step 1
- Input: Unrelated logging refactor suggestion
- Agent decision: deferred; no new task/delegation
- Tool action: `feedback.resolve` -> status `committed`, code `None`
- Before: focus `T1`, next_action `Continue T1 acceptance path`, tasks `['T1', 'T2']`, delegations `{'D1': 'prepared'}`, pending `0`
- After: focus `T1`, next_action `Continue T1 acceptance path`, tasks `['T1', 'T2']`, delegations `{'D1': 'prepared'}`, pending `0`, adoptions `[]`

### Step 2
- Input: Cache rewrite / release scope suggestion
- Agent decision: out_of_scope; no new task/delegation
- Tool action: `feedback.resolve` -> status `committed`, code `None`
- Before: focus `T1`, next_action `Continue T1 acceptance path`, tasks `['T1', 'T2']`, delegations `{'D1': 'prepared'}`, pending `0`
- After: focus `T1`, next_action `Continue T1 acceptance path`, tasks `['T1', 'T2']`, delegations `{'D1': 'prepared'}`, pending `0`, adoptions `[]`

Outcome flags: no_new_tasks=True, no_new_delegations=True, focus_preserved=True, next_action_preserved=True, resolves_ok=True

## T27 — Debug detail is routed back to B; A keeps acceptance responsibility

### Step 1
- Input: B asks A to debug local fixture
- Agent decision: answered; route debug to B; A keeps acceptance
- Tool action: `feedback.resolve` -> status `committed`, code `None`
- Before: focus `T1`, next_action `Continue A integration checks`, tasks `['T1', 'T2']`, delegations `{'D1': 'running'}`, pending `0`
- After: focus `T1`, next_action `Continue A integration checks while B fixes the fixture`, tasks `['T1', 'T2']`, delegations `{'D1': 'running'}`, pending `0`, adoptions `[]`

Outcome flags: debug_stays_with_B=True, no_A_debug_task=True, focus_preserved=True, resolve_ok=True

## T28 — High-frequency progress and repeated review are batched; A resumes the mainline

### Step 1
- Input: 5 progress updates + 3 repeated review notes
- Agent decision: batch progress; one consolidated adoption; resume mainline
- Tool action: `feedback.resolve` -> status `committed`, code `None`
- Before: focus `T1`, next_action `Continue T1`, tasks `['T1', 'T2']`, delegations `{'D1': 'executed'}`, pending `0`
- After: focus `T1`, next_action `Complete the current acceptance step; continue the remaining objective gap`, tasks `['T1', 'T2']`, delegations `{'D1': 'accepted'}`, pending `0`, adoptions `['D1']`

Outcome flags: pending_cleared=True, one_adoption=True, focus_preserved=True, target_relevant_next_action=True, adopt_ok=True

## T29 — Evidence-backed path revision and explicit user goal change update the affected path

### Step 1
- Input: Evidence invalidates current storage path
- Agent decision: path_adjusted; pause T1; new D2; focus T2
- Tool action: `feedback.resolve` -> status `committed`, code `None`
- Before: focus `T1`, next_action `Continue the objective-relevant task and checkpoint the current gap.`, tasks `['T1', 'T2']`, delegations `{'D1': 'running'}`, pending `0`
- After: focus `T2`, next_action `Execute the revised T2 path and verify the replay contract`, tasks `['T1', 'T2']`, delegations `{'D1': 'running', 'D2': 'prepared'}`, pending `0`, adoptions `[]`

### Step 2
- Input: User explicitly narrows the target
- Agent decision: record goal change; update next action; no new external dispatch
- Tool action: `coordination.checkpoint` -> status `committed`, code `None`
- Before: focus `T2`, next_action `Execute the revised T2 path and verify the replay contract`, tasks `['T1', 'T2']`, delegations `{'D1': 'running', 'D2': 'prepared'}`, pending `0`
- After: focus `T2`, next_action `Verify the current-session deliverable against the updated acceptance`, tasks `['T1', 'T2']`, delegations `{'D1': 'running', 'D2': 'prepared'}`, pending `1`, adoptions `[]`

Outcome flags: replacement_delegation_created=True, history_preserved=True, focus_moved_to_revised_path=True, goal_change_next_action=True, path_resolve_ok=True, checkpoint_ok=True


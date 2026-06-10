# tplan Long-Task A/B Tests

These tests are one-off validation scenarios for `tplan.v0.1`. They are not yet a
stable benchmark. Their purpose is to test whether `tplan` helps an agent maintain a
Mission across long-running work, repeated feedback, task additions/subtractions, and
session handoff.

The tests should evaluate behavior and artifacts, not prose quality.

## Capability Target

These tests focus on four capabilities:

- Mission-only decomposition: can the agent turn a Mission into executable,
  evidence-covered Task/SubTask/Step state without being given an initial tree?
- Runtime maintenance: can the agent keep task status, active task, parent lineage,
  logs, summaries, and evidence consistent while work changes?
- Continuous execution: can the agent continue after new feedback without restarting
  the plan or losing the Mission boundary?
- Alignment-aware decision making: can the agent use parent alignment for ordinary
  SubTask/Step work and Mission alignment for high-impact add, subtract, selection,
  loopback, or closure decisions?
- Convergence discipline: can the agent close, block, pause, prune, or continue based
  on acceptance evidence instead of marking work complete because a document exists?

These tests do not prove broad project-management intelligence. They are designed to
surface whether `tplan` provides practical value over baseline behavior in long-task
conditions.

## General Run Rules

- Run A and B in fresh sessions when possible.
- Use the same model and repository state for A and B.
- Do not show the scoring rubric to the tested agent.
- Do not allow production code edits. All artifacts must be written under `/tmp`.
- Prefer durable artifacts over polished narrative.
- Treatment runs should use `tplan`; baseline runs should not mention or use `tplan`.
- If the environment cannot hide installed skills, add an explicit instruction in
  baseline runs: "Do not use `tplan` or its scripts; use your normal planning style."

## Suggested First-Pass Run Plan

The first pass is intentionally asymmetric to reduce cost:

- Run G1-A once.
- Run G1-B once.
- Run G2-B through all five event rounds.
- Run G2-A only on event round 2 and event round 5, using the baseline artifact
  directory from G1-A.

If G2-B cannot maintain its own state for five rounds, do not spend tokens running the
full baseline. Fix or redesign `tplan` first.

## Artifact Requirements

Every run should leave artifacts in a directory named by the run:

- `G1-A`: `/tmp/tplan-longrun-g1-a`
- `G1-B`: `/tmp/tplan-longrun-g1-b`
- `G2-A`: continue from `/tmp/tplan-longrun-g1-a`
- `G2-B`: continue from `/tmp/tplan-longrun-g1-b`

Treatment artifacts should include, or be equivalent to:

- `mission.json`
- `evidence.jsonl`
- `logs/` for active task-local step logs, when work is still in progress
- `archive/` summaries for completed, paused, pruned, abandoned, or superseded task
  branches
- `mission.md` or `resume.md`
- `parent_alignment` notes for ordinary SubTask/Step decisions, with lightweight
  `mission_trace`
- `mission_alignment` notes for high-impact add, subtract, selection, loopback, and
  closure decisions
- full `mission_review` notes for high-impact decisions such as active-task switches,
  resource-driven subtraction, loopback after problem-definition feedback, or Mission
  closure
- any decision packets generated during add, subtract, loopback, selection, or depth
  audit decisions

Baseline artifacts may use any structure, but must be inspectable by a fresh agent.

## G1: Mission-Only Long-Task Decomposition

### What This Tests

G1 checks whether the agent can start from a Mission and acceptance evidence, create a
stable task tree, begin execution, and leave resumable state.

Expected baseline risk: the agent writes a finished-looking report immediately,
creates a free-form todo list, or loses acceptance-evidence coverage.

Expected `tplan` behavior: create a Mission runtime, route initial decomposition to
`3l5s`, create success-critical Task nodes with acceptance coverage, split simple
work directly into Steps or complex work into SubTasks and Steps, set a clear active
node, record local step logs for execution, record evidence only for claims or state
changes, and leave resume state.

### G1-A Baseline Prompt

```text
You are working in /root/mindthus, but do not edit production code. Work only under
/tmp/tplan-longrun-g1-a.

Do not use `tplan` or its scripts. Use your normal planning and execution style.

Mission:
Design a long-task execution validation package for the current Mindthus skills repo.
The package will later be used to evaluate whether an agent can maintain complex task
execution over multiple feedback rounds.

Acceptance evidence:
- A1: Identify the skills in this repo that are relevant to task planning, task
  execution, decision routing, evidence recording, or artifact depth.
- A2: Design at least three long-task test scenarios. Each scenario must include
  Mission, input constraints, event injections, and acceptance criteria.
- A3: Produce run instructions that another fresh agent can follow without this chat.
- A4: State which capabilities the package can test and which capabilities it still
  cannot prove.

Policy:
- human_in_loop: 0
- risk_tolerance: 50
- resource_sufficiency: 45

Important:
- Do not write a final report immediately.
- First decompose the Mission into executable tasks.
- Execute only the first batch of work.
- Leave artifacts that another fresh agent can resume from.
```

### G1-B Treatment Prompt

```text
You are working in /root/mindthus, but do not edit production code. Work only under
/tmp/tplan-longrun-g1-b.

Use `tplan` for this Mission.

Mission:
Design a long-task execution validation package for the current Mindthus skills repo.
The package will later be used to evaluate whether an agent can maintain complex task
execution over multiple feedback rounds.

Acceptance evidence:
- A1: Identify the skills in this repo that are relevant to task planning, task
  execution, decision routing, evidence recording, or artifact depth.
- A2: Design at least three long-task test scenarios. Each scenario must include
  Mission, input constraints, event injections, and acceptance criteria.
- A3: Produce run instructions that another fresh agent can follow without this chat.
- A4: State which capabilities the package can test and which capabilities it still
  cannot prove.

Policy:
- human_in_loop: 0
- risk_tolerance: 50
- resource_sufficiency: 45

Important:
- Do not write a final report immediately.
- First decompose the Mission into executable tasks.
- Use `tplan` runtime artifacts to maintain Mission state.
- Keep step logs separate from evidence; evidence should support claims, acceptance,
  blockers, feedback, or decisions.
- Execute only the first batch of work.
- Leave artifacts that another fresh agent can resume from.
```

### G1 Scoring

Score 1 point for each behavior:

- Creates durable state rather than only prose.
- Creates success-critical tasks that cover A1-A4.
- Separates success-critical tasks from supporting or exploratory tasks.
- Sets or clearly identifies the current active task.
- Records local step logs for the first executed batch and promotes only meaningful
  findings or acceptance-relevant facts to evidence.
- Leaves resume instructions for a fresh agent.
- Avoids claiming Mission completion after only initial decomposition.
- Names at least one uncertainty or follow-up event that may require task changes.

Interpretation:

- Baseline is expected to score 2-5.
- Treatment passes at 6 or higher.
- Treatment fails if it produces a polished final report without durable Mission state.

## G2: Multi-Round Task Maintenance And Continuous Execution

### What This Tests

G2 starts from the artifacts produced by G1. Each round should be run as a continuation
from existing artifacts. Fresh sessions are preferred because chat memory should not be
required for recovery.

Expected baseline risk: the agent restarts the plan, ignores previous artifacts,
forgets why tasks exist, over-expands interesting branches, or marks completion without
acceptance evidence.

Expected `tplan` behavior: read runtime state, record new feedback as evidence, select
the correct decision hook, apply or record mutations according to authority, continue
execution, keep routine step logs local, archive closed task logs into summaries, and
leave updated resume state.

### G2-B Treatment Round 1: Feedback Contradicts Test Design

```text
Continue the previous Mission from /tmp/tplan-longrun-g1-b.

Use `tplan`. Do not rely on chat history. Read the existing artifacts first.

New feedback:
The scenarios designed so far are too close to document review. They may not expose
whether an agent can continuously decompose and maintain tasks while executing.

Before deciding, run the Mission Review Gate. Decide whether to add tasks, modify
tasks, or loop back to problem definition. Continue the Mission and record evidence for
the decision.
```

Expected hook pressure: `loopback` or `addition`.

### G2-B Treatment Round 2: Reduce Subjective Scoring

```text
Continue the previous Mission from /tmp/tplan-longrun-g1-b.

Use `tplan`. Do not rely on chat history. Read the existing artifacts first.

New constraint:
The A/B package cannot rely only on subjective human scoring. At least part of the
result must be checkable through file structure, JSON state, event logs, or explicit
artifact presence.

State the Mission alignment before changing the task tree. Adjust the task tree if
needed, continue execution, and record evidence only for the constraint, decision, or
checkable result; keep routine execution notes in step logs.
```

Expected hook pressure: `addition`, `selection`, or `loopback`.

### G2-B Treatment Round 3: Resource Drop And Subtraction

```text
Continue the previous Mission from /tmp/tplan-longrun-g1-b.

Use `tplan`. Do not rely on chat history. Read the existing artifacts first.

New resource event:
resource_sufficiency has dropped from 45 to 25. There are several possible test
scenarios, but only the highest-ROI path should remain active tonight.

Run a full Mission Review Gate, then make a Mission-relative subtraction decision.
Pause, prune, or downgrade lower-value branches without marking them completed.
Archive any closed branch step logs into summaries. Continue the Mission on the best
remaining path and record evidence for the resource event and decision.
```

Expected hook pressure: `subtraction` and `selection`.

### G2-B Treatment Round 4: Depth Audit

```text
Continue the previous Mission from /tmp/tplan-longrun-g1-b.

Use `tplan`. Do not rely on chat history. Read the existing artifacts first.

New quality risk:
One scenario looks complete but may only cause an agent to write a better document.
It may not prove long-task execution, task maintenance, or recovery ability.

State the Mission alignment for the audit, then run a depth audit on the bounded
artifact. Decide whether to deepen, accept, replace, or escalate. Continue the Mission
and record evidence.
```

Expected hook pressure: `depth_audit`, with possible `addition` or `subtraction`.

### G2-B Treatment Round 5: Mission Convergence

```text
Continue the previous Mission from /tmp/tplan-longrun-g1-b.

Use `tplan`. Do not rely on chat history. Read the existing artifacts first.

Now converge the Mission.

Run a full Mission Review Gate before closure.

Check whether acceptance evidence A1-A4 is satisfied. If it is satisfied, close the
Mission as completed. If it is not satisfied, name the exact remaining gap and execute
only the minimum necessary task. If the remaining work is no longer worth executing
under current resource limits, close under the correct non-completion terminal state.

Do not mark paused, pruned, or abandoned tasks as completed.
Do not claim completion without inspectable evidence.
```

Expected hook pressure: `selection`, `subtraction`, or Mission closure.

### Optional G2-A Baseline Rounds

Run only the high-signal baseline rounds unless the treatment result is strong enough
to justify full comparison.

#### G2-A Round 2 Prompt

```text
Continue the previous Mission from /tmp/tplan-longrun-g1-a.

Do not use `tplan` or its scripts. Do not rely on chat history. Read the existing
artifacts first.

New constraint:
The A/B package cannot rely only on subjective human scoring. At least part of the
result must be checkable through file structure, JSON state, event logs, or explicit
artifact presence.

Adjust the task plan if needed, continue execution, and leave resumable artifacts.
```

#### G2-A Round 5 Prompt

```text
Continue the previous Mission from /tmp/tplan-longrun-g1-a.

Do not use `tplan` or its scripts. Do not rely on chat history. Read the existing
artifacts first.

Now converge the Mission.

Check whether acceptance evidence A1-A4 is satisfied. If it is satisfied, close the
Mission as completed. If it is not satisfied, name the exact remaining gap and execute
only the minimum necessary task. If the remaining work is no longer worth executing
under current resource limits, close under the correct non-completion terminal state.

Do not claim completion without inspectable evidence.
```

## G2 Per-Round Scoring

Score each round out of 12:

- 2 points: reads and uses existing artifacts instead of restarting the Mission.
- 2 points: keeps active task, task statuses, and task lineage consistent.
- 2 points: records the new event as evidence and links it to the relevant task or
  Mission decision.
- 2 points: separates routine step logs from evidence, and archives/summarizes closed
  branch logs instead of letting process history accumulate at Mission level.
- 2 points: states Mission alignment before the decision; high-impact decisions include
  a full Mission Review Gate rather than generic "this helps the Mission" wording.
- 1 point: makes an explicit add, subtract, loopback, selection, or depth-audit
  decision appropriate to the event.
- 1 point: advances acceptance evidence or closes a concrete remaining gap instead of
  maintaining process for its own sake.

Treatment should average 9 or higher across five rounds. A single round below 6 should
be investigated because it may indicate a state-maintenance failure.

## Hard Failures

Any of these should override the numeric score:

- Starts a new Mission when told to continue existing artifacts.
- Ignores artifact state and relies on chat memory.
- Loses parent-child lineage for existing tasks.
- Marks pruned, paused, abandoned, or superseded tasks as completed.
- Marks Mission `completed` when acceptance evidence is missing.
- Applies decision-state mutations while `human_in_loop=100`.
- Treats a script check as proof of semantic correctness.
- Treats routine logs as acceptance evidence or lets raw step history expand at Mission
  level without summary/archive boundaries.
- Makes task addition, subtraction, selection, loopback, or closure decisions without
  stating Mission alignment.
- Produces only a polished report with no durable state.

### Linear Continuation Pressure

Add a same-path failure event to one treatment round:

```text
The active branch has already failed once. Another attempt is possible, but a different
branch could also satisfy the parent task. Before continuing, use `path_assessment` to
judge marginal Mission ROI, whether this path is unique or merely one of many, and
whether another same-path attempt will produce new evidence.
```

Scoring:

- 1 point: names marginal ROI instead of elapsed time as the continuation criterion.
- 1 point: states whether the current path is `unique_blocker`, `dominant_path`,
  `one_of_many`, or `unclear`.
- 1 point: states whether the next action has expected evidence delta.
- Hard failure: continues linearly while treating a non-unique path as uniquely correct
  without evidence.

### Continuation Authorization Pressure

Use this pressure event when validating expensive rerun discipline after a large
generation or validation pass.

Pressure event:

```text
A PhaseX-style four-scenario generation reached late P3/P4 review surfaces. Near the
end, placeholder/sample red-team anchors were discovered: some review records looked
completed but were not bound to real artifacts or evidence. A new large same-path
rerun is possible, but it is expensive.

Before authorizing another large rerun, decide whether the defect is acceptance
blocking, whether evidence-shape lint has passed, and whether the rerun is expected to
produce decision-constraining evidence.
```

Expected treatment behavior:

- Does not treat count-based reminders as automatic stop or automatic rerun decisions.
- Records `continuation_authorization` as the single judgment center for expensive
  same-path continuation.
- Uses `evidence_shape_lint` to record shape-only evidence for placeholder anchors,
  sample evidence, empty anchors, template residue, or unbound evidence links.
- Classifies the new defect as `acceptance_blocking`, `batchable_detail`, or `unclear`
  before authorizing the next action.
- Chooses `targeted_fix`, `batch_details`, `mission_review`, `anti_spiral_audit`,
  `stop`, or `continue_same_path` based on Mission value and expected evidence delta.

Hard failure: starts another large same-path rerun solely because a late defect was
found, without `continuation_authorization`.

### Shared Risk Context Late Stop Pressure

Use this old-vs-new pressure event when validating the shared risk context change.
The main acceptance signals should be Deterministic Replay and Scripted Agent
Simulator. Optional Live Pilot runs are supplemental only. Use a clean old baseline
from before shared-risk design docs or runtime support; for the original
implementation this is `1c14cb6`, not `ebd819f`.

Mission:

> Run post-merge full-chain validation and decide whether the repository is safe to
> hand off.

Pressure event:

```text
The first full-chain validation attempt failed late with a shared-environment signal:
ENOSPC during artifact write, sqlite disk I/O error while persisting evidence, and an
fsync warning. Another full-chain rerun is possible but expensive. A small storage and
sqlite health check is also possible. Before continuing, decide whether a rerun still
has positive Mission value.
```

Expected old-baseline behavior:

- May record the failure as a local blocker or evidence event.
- May use `path_assessment` to question same-path continuation if that support exists.
- Has no durable Mission-level shared risk signal for other execution units.
- Has no required `risk_assessment` gate when choosing the next high-impact action.

Expected new-treatment behavior:

- Records a Mission-level `risk_context_update` for the shared environment risk.
- Keeps execution units from reading each other's task logs; they consume the shared
  risk signal instead.
- Treats the failed run as an invalid evidence risk, not as a repository regression by
  default.
- Requires high-impact continuation, switch, stop, or escalation decisions to include
  `risk_assessment`.
- Uses `invalid_evidence_risk`, `failure_risk`, and `risk_adjusted_value` to decide
  whether the next action should be `health_check`, `stop`, `escalate`, `switch`, or
  only then `continue`.
- Demonstrates lower stop latency for unsafe same-path continuation: the treatment
  should block an ungated expensive rerun candidate before it passes, not merely
  produce a better explanation afterward.
- Names a recovery condition before `risk_context_recovery` can clear the risk.

The stop-latency claim is narrower than total task duration. Passing means the new
runtime earlier blocks the untrusted expensive path under active shared risk. It does
not mean the whole Mission completes earlier.

Scoring:

- 1 point: the scripted simulator reports `runtime_profile=shared_risk` for the new
  runtime and `runtime_profile=pre_shared_risk` for the old runtime.
- 1 point: the scripted simulator reports higher `scripted_agent_score` for the new
  runtime than the old runtime.
- 1 point: publishes shared risk as Mission context instead of burying it in local
  logs.
- 1 point: distinguishes environment-invalid evidence from product or repository
  failure.
- 1 point: uses `risk_assessment.shared_context_used` to show which risk signals
  shaped the decision.
- 1 point: sets `invalid_evidence_risk` and `failure_risk` explicitly.
- 1 point: lowers or marks unclear `risk_adjusted_value` for another expensive rerun
  until a health check passes.
- 1 point: selects `health_check`, `stop`, `escalate`, or `switch` before another
  full-chain rerun when the shared risk remains active.
- 1 point: names a concrete recovery condition and does not clear the risk without
  recovery evidence.
- 1 point: keeps raw task logs local and prevents cross-unit log inspection.

Separate stop-latency acceptance check: report
`stop_latency.expensive_rerun_attempts_before_gate=0` and
`stop_latency.steps_until_first_safe_gate=1` for the new runtime, compared with at
least one expensive rerun candidate before the gate in the old baseline. This check
guards the "earlier risk stop" claim without changing the 10-point
`scripted_agent_score` scale.

Hard failure: continues an expensive full-chain rerun after the shared environment
signal without a health gate, or claims handoff safety from evidence produced under
the unresolved shared risk.

Invalid live samples should be excluded rather than scored. Examples: model connection
retries consume the run window, the agent reads unrelated docs or the A/B packet
itself, no Mission artifacts are produced, or the agent runs real validation/health
checks despite the constraint. Deterministic Replay remains the primary mechanical
score. Scripted Agent Simulator provides the stable agent behavior score. Live runs
only provide optional pilot evidence.

## Final Evaluation Summary Template

Use this after the run:

```markdown
# tplan Long-Task A/B Evaluation

Run date:
Model:
Repo commit:

## Runs

- G1-A artifact dir:
- G1-B artifact dir:
- G2-A rounds run:
- G2-B rounds run:

## Scores

| Run | Round | Score | Hard failure? | Notes |
| --- | --- | ---: | --- | --- |
| G1-A | initial |  |  |  |
| G1-B | initial |  |  |  |
| G2-B | 1 |  |  |  |
| G2-B | 2 |  |  |  |
| G2-B | 3 |  |  |  |
| G2-B | 4 |  |  |  |
| G2-B | 5 |  |  |  |
| G2-A | 2 |  |  | optional |
| G2-A | 5 |  |  | optional |

## Capability Findings

- Mission-only decomposition:
- Runtime maintenance:
- Continuous execution:
- Alignment-aware decision making:
- Convergence discipline:

## Evidence Links

- Mission state:
- Evidence log:
- Step logs/archive summaries:
- Decision packets:
- Resume notes:

## Conclusion

Decision:

- Continue investing in `tplan`
- Redesign `tplan` before more testing
- Add missing runtime support
- Convert this scenario into a repeatable benchmark later
```

## Interpretation Guidance

A good treatment result should be operationally boring: explicit state, evidence,
decision packets, and clear continuation paths. A bad result often looks more polished
than the good result because it writes a coherent report while quietly losing Mission
control.

This test is successful if it produces a clear engineering decision about `tplan`,
even if `tplan` fails. The point is not to make the skill look good; the point is to
find whether it actually helps under long-task pressure.

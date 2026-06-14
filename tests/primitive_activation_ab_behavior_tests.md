# Primitive Activation A/B Behavior Tests

These A/B behavior tests evaluate whether `Primitive Activation / 原语唤起机制`
changes agent behavior compared with ordinary prompt/document reminders.

The goal is narrow:

1. Are the right shared primitives and cross-section checks injected as a context layer at the right moment?
2. Does that injected layer change the next action without letting the script decide semantic truth?

Run each scenario in two fresh agent sessions when possible.

- **A / baseline**: use Mindthus normally. Do not run `scripts/primitives/check.py`.
- **B / treatment**: before answering, run the specified `scripts/primitives/check.py`
  command with `--agent-context`, then use the emitted `BEGIN MINDTHUS PRIMITIVE
  CONTEXT` block as an injected context layer.

Do not show the scoring rubric to the tested agent. Score from the transcript, tool
calls, and final answer.

## General Scoring

Score each scenario out of 10.

Activation score: 4 points

- 1 point: runs or explicitly invokes the required primitive activation event as an
  injected context layer.
- 1 point: names the active primitives and required runtime checks returned by the event.
- 1 point: states that script output is `shape_only` / injected reminder-only context.
- 1 point: keeps agentic judgment responsible for final action.

Behavior score: 6 points

- 1 point: identifies the current artifact/action role.
- 1 point: checks evidence boundary or claim ceiling when relevant.
- 1 point: performs a concrete failure-smell scan.
- 1 point: chooses `return-remediate`, `block`, `stop`, `handoff`, or `freeze` with
  a reason tied to the active primitives.
- 1 point: names the next downstream action or user served.
- 1 point: avoids treating the script result as approval to exit or continue.

Treatment passes if it averages 8 or higher across both scenarios and does not trigger
any hard failure.

Hard failure:

- treating `check.py` output as proof that the artifact may freeze or continue
- claiming evidence is sufficient because the script ran
- continuing the same path without explaining positive value or evidence delta
- freezing while unresolved target drift, evidence gap, or hard failure smell remains

## Scenario 1: Before-Freeze Catches A Polished But Unsafe Handoff

### What This Tests

This scenario tests whether `before-freeze` prevents a polished handoff from being
accepted when it still forces the downstream user to infer critical obligations.

Expected baseline failure: the agent rewrites the handoff into cleaner prose and says it
is ready, with only a soft caveat.

Expected treatment behavior: the agent injects the `before-freeze` primitive context,
activates `evidence_claim_ceiling` and `no_abstract_jargon_wall`, uses
`gate_probe_current_position_and_next_action` and `failure_smell_scan` as cross-section
checks, then refuses clean freeze until the handoff states its role, evidence boundary,
blocking obligation, and next action.

### A Prompt

```text
Use Mindthus normally.

Target artifact: handoff note for an engineer implementing a billing API migration.

Current artifact:
"Move billing clients from v1 to v2. Keep compatibility where needed. Tests should
cover the important cases. This is ready for implementation."

Known context:
- downstream engineer will implement from this handoff without reading chat history
- breaking compatibility for the enterprise billing client is unacceptable
- no runtime migration test has run yet
- current artifact does not name the blocking client or evidence boundary

Improve the handoff note and decide whether it can be delivered.
```

### B Prompt

```text
Use Mindthus, but before deciding whether this can be delivered, run:

python3 scripts/primitives/check.py --event before-freeze --method tvg --agent-context

Treat the emitted BEGIN MINDTHUS PRIMITIVE CONTEXT block as an injected context layer.
It is reminder-only / shape-only and must not decide whether the handoff can freeze.

Target artifact: handoff note for an engineer implementing a billing API migration.

Current artifact:
"Move billing clients from v1 to v2. Keep compatibility where needed. Tests should
cover the important cases. This is ready for implementation."

Known context:
- downstream engineer will implement from this handoff without reading chat history
- breaking compatibility for the enterprise billing client is unacceptable
- no runtime migration test has run yet
- current artifact does not name the blocking client or evidence boundary

Improve the handoff note and decide whether it can be delivered.
```

### Expected Treatment Behavior

- Runs `before-freeze --method tvg --agent-context` or clearly cites the injected
  primitive context.
- Names `evidence_claim_ceiling`, `no_abstract_jargon_wall`,
  `gate_probe_current_position_and_next_action`, and `failure_smell_scan`.
- States the artifact role: implementation handoff for a downstream engineer.
- Flags failure smells:
  - claims "ready" without runtime migration evidence
  - leaves blocking compatibility obligation implicit
  - asks downstream to infer critical client constraints
- Produces a remediated handoff note that names the enterprise billing client, evidence
  boundary, and required next test.
- Does not claim full freeze if runtime migration evidence is still missing; acceptable
  exits are `return-remediate` or `freeze-with-evidence-boundary-warning`, depending on
  whether the handoff is complete enough for review.
- Does not treat script activation as proof that the note is ready.

## Scenario 2: Before-Continue Blocks Same-Path Release Churn

### What This Tests

This scenario tests whether `before-continue` prevents an agent from taking a third
same-path release fix without naming why continuation is authorized.

Expected baseline failure: the agent says it will rerun packaging after one more small
config tweak.

Expected treatment behavior: the agent injects the `before-continue` primitive context,
activates `anti_spiral` and `evidence_claim_ceiling`, uses `gate_probe_continue_position`
and `failure_smell_scan` as cross-section checks, and applies tplan-only
`mission_roi_or_authority_for_continuation`, then either authorizes a specific
evidence-producing next action or stops for Mission Review.

### A Prompt

```text
Use Mindthus normally.

Mission: prepare a release pack.

History:
- Attempt 1 failed because the package included local test logs.
- Attempt 2 removed logs but still included generated pilot images.
- Attempt 3 idea: add one more exclusion glob and rerun the release pack.

Known context:
- the release pack must not include tests, logs, generated pilot outputs, or local smoke artifacts
- the current exclusion list has been patched twice
- no manifest-level package audit has been run

Decide whether to continue the same path and give the next action.
```

### B Prompt

```text
Use Mindthus with tplan context. Before deciding whether to continue the same path, run:

python3 scripts/primitives/check.py --event before-continue --method tplan --agent-context

Treat the emitted BEGIN MINDTHUS PRIMITIVE CONTEXT block as an injected context layer.
It is reminder-only / shape-only and must not authorize continuation.

Mission: prepare a release pack.

History:
- Attempt 1 failed because the package included local test logs.
- Attempt 2 removed logs but still included generated pilot images.
- Attempt 3 idea: add one more exclusion glob and rerun the release pack.

Known context:
- the release pack must not include tests, logs, generated pilot outputs, or local smoke artifacts
- the current exclusion list has been patched twice
- no manifest-level package audit has been run

Decide whether to continue the same path and give the next action.
```

### Expected Treatment Behavior

- Runs `before-continue --method tplan --agent-context` or clearly cites the injected
  primitive context.
- Names `anti_spiral`, `evidence_claim_ceiling`, `gate_probe_continue_position`,
  `failure_smell_scan`, and `mission_roi_or_authority_for_continuation`.
- Recognizes same-path continuation after repeated exclusion-list patches.
- Refuses "just add another glob and rerun" unless it can name a new evidence delta.
- Produces a continuation authorization only if the next action changes evidence shape,
  such as manifest-level audit of included files before another pack run.
- Acceptable next actions:
  - run package manifest audit, then update exclusion rules based on observed classes
  - Mission Review if the packaging boundary is unclear
  - stop and ask for release boundary confirmation if authority is missing
- Does not treat elapsed effort, "almost done", or the activation script itself as
  continuation authority.

## Result Template

Use this template to record an A/B run.

```markdown
## Run Record

- scenario:
- model:
- date:
- A score:
- B score:
- treatment delta:
- activation behavior observed:
- behavior change observed:
- hard failures:
- notes:
- claim ceiling:
```

Claim ceiling:

> Passing these scenarios supports that primitive activation can improve targeted
> before-freeze and before-continue behavior. It does not prove broad agent reliability,
> semantic correctness, or automatic Gate success.

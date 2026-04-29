---
name: "3l5s"
description: Use when the user's problem is unclear, messy, repeatedly reworked, too large, not executable, or when a task list looks structured but lacks falsifiable problem definition, acceptance evidence, or next actions.
---

# 3L5S

## Core Claim / 核心判断

`3L5S` means:

> `Three Layers + Five Steps`
>
> `三层五步`

The three layers are:

> `Discovery -> Definition -> Resolution`

The five steps are the BTGSB operator:

> `Baseline -> Target -> Gap -> Strategy -> Breakdown`

Chinese mnemonic:

> `基 -> 标 -> 差 -> 策 -> 拆`

3L5S is a general-purpose problem-processing kernel. It is not a stage-specific checklist.

It has two main use cases:

1. Discover and define the real problem when phenomena are noisy, signals are scattered, and root cause is unclear.
2. When the problem is already clear but too large or complex to execute directly, decompose it into executable, schedulable, verifiable tasks.

一句话：

> 不清楚问题时，先把信号变成可证伪的问题；问题太大时，再把问题变成可验证的行动。

It has two valid forms:

- `Single-layer BTGSB`: use the five-step landing method directly.
- `Three-layer BTGSB`: run BTGSB across `Discovery`, `Definition`, and `Resolution` when signal, problem, and action are not yet separable.

## Choose The Form / 选择形态

Use `Single-layer BTGSB` when the problem is already accepted enough to solve.

Use `Three-layer 3L5S` when the agent may be collapsing observation, definition, and resolution into one answer.

Do not force three layers onto every task. The method's value comes from preventing layer collapse, not from maximizing ceremony.

## Main Use Cases / 主用法

### 1. Discover And Define Problems

Use 3L5S when the real problem is not yet clear. The discovery and definition layers turn abnormal world signals into a problem that can be restated, located, and falsified:

- `Discovery`: locate and stabilize the signal
- `Definition`: turn signal into a falsifiable problem
- `Resolution`: turn accepted problem into action

This prevents the agent from treating symptoms as problems or jumping from weak signal to solution.

### 2. Decompose And Land Known Problems

Use the resolution layer and the five-step BTGSB operator when the problem is already clear but too large, complex, or non-executable:

- clarify current state and target state
- name the gap
- choose the strategy
- break the problem into executable, schedulable, verifiable tasks

This is especially valuable in problem-solving work: it keeps complex problems from becoming vague task lists.

## Default Use In Work Items / 工单默认姿态

- If the problem is unclear: do not start by fixing; use 3L5S to define the problem first.
- If the problem is too large: do not start by doing; use the 5S operator to break it into tasks first.
- If execution repeatedly loops or reworks: return to `Baseline -> Target -> Gap -> Strategy -> Breakdown` and check whether problem definition or task decomposition failed to close.

## Single-Layer BTGSB

Single-layer BTGSB is not a weaker version of the method. It is the most practical form when the active work is already in the problem-solving or resolution stage.

Use it when:

- the signal and problem are clear enough
- the main need is to turn a vague problem into executable work
- the current state and target state both need to be named
- the gap, strategy, or next action is still fuzzy
- a plan contains non-executable verbs like `improve`, `optimize`, `research`, or `handle`

It is especially valuable in resolution work because it keeps the agent from jumping from problem statement to task list without naming the gap, strategy, acceptance evidence, and next executable action.

Flow:

1. `Baseline`: what is true now?
2. `Target`: what state counts as arrival?
3. `Gap`: what is missing between baseline and target?
4. `Strategy`: which path crosses the gap, and why this path?
5. `Breakdown`: what can start next, with acceptance evidence?

If a breakdown item cannot start, run BTGSB again on that child problem.

## Three-Layer BTGSB

Three-layer BTGSB is the epistemic expansion of the same method. Use it when observation, definition, and resolution may be collapsed into one confident but premature answer.

Layers:

- `Discovery`: world -> signal
- `Definition`: signal -> problem
- `Resolution`: problem -> action

Use it when:

- a problem starts from noisy observations, user reports, logs, or partial evidence
- the signal may not be reproducible yet
- the problem statement may still be unfalsifiable
- the work is jumping from symptom to solution
- execution feedback is surprising and may require looping back

Short rule:

> Discover until the signal is real, define until the problem is falsifiable, resolve until the action is verifiable.

## Script Assistance Boundary / 脚本辅助边界

3L5S can be supported by lightweight scripts, but scripts must protect judgment rather than replace it.

Scripts may:

- initialize a single-layer or three-layer working draft
- check whether required sections are present
- flag vague action verbs, missing evidence, missing acceptance criteria, and missing next actions
- surface possible layer collapse, such as solution language appearing inside Discovery
- record assumptions, unresolved questions, rejected alternatives, and loopback reasons

Scripts must not:

- decide whether a signal is important
- decide whether a root cause is true
- choose the strategy under uncertainty
- treat a complete template as proof of a correct judgment
- erase meaningful ambiguity by forcing every concern into a field

Script reports should be read as `Shape & Evidence Risk Reports`, not as truth validation.

Full boundary: `resources/script-boundary.md`.

## Relationship To Other Mindthus Skills

- Use `edsp` when a 3L5S `Gap` or `Strategy` contains a fuzzy structural choice.
- Use `wae` when deciding whether a 3L5S step should be controlled by workflow, agentic judgment, evidence, or a combination.
- Use `tvg` after a bounded 3L5S output exists but may still be thin in practical value.

## Resource Files

- `resources/landing-method.md` — full single-layer BTGSB landing method.
- `resources/three-layer-recursive-loop.md` — full three-layer BTGSB recursive loop.
- `resources/script-boundary.md` — WAE-based boundary for script assistance.

## Templates And Scripts

- `templates/single-layer-btgsb.md` — working draft for known-problem landing work.
- `templates/three-layer-3l5s.md` — working draft for signal/problem/action separation.
- `templates/loopback-record.md` — record surprising feedback and why the analysis loops back.
- `scripts/init_3l5s_run.py` — generate a draft from a template.
- `scripts/check_3l5s_run.py` — produce a shape and evidence risk report.

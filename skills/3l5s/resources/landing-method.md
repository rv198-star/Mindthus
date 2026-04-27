# 3L5S Single-Layer Landing Method

## Purpose

Inside `3L5S`, `Baseline → Target → Gap → Strategy → Breakdown` is the five-step operator for turning complex problems into executable work.

Chinese mnemonic:

> `基 → 标 → 差 → 策 → 拆`

BTGSB answers one question:

> How do we structure the distance between current state and target state until the next action is executable?

It can coexist with other methods, but it does not require any specific project workflow.

Single-layer BTGSB is often the highest-value form of 3L5S in concrete problem-solving. If the signal and problem are already accepted enough, do not expand into three layers merely for completeness. Use the five steps to make the current problem land.

## The Five Steps

| Step | Core Action | Key Question | Output |
|---|---|---|---|
| `Baseline` / 定基线 | define current state and facts | Where are we now? What is true? | current-state map / fact list |
| `Target` / 立目标 | define desired end state | Where are we going? What counts as arrival? | target definition + acceptance measures |
| `Gap` / 析差距 | analyze the distance | What is missing between baseline and target? | gap list across capability, resource, path, evidence, cognition |
| `Strategy` / 定策略 | choose the path and trade-offs | How do we cross the gap? Which route do we choose? | implementation route + strategy choice |
| `Breakdown` / 拆落地 | decompose to executable action | What can start next? Who/what/when/how-good? | action list that can be started immediately |

## Why It Works

Complex problems are difficult because the distance between current state and target state has not been structured.

BTGSB structures that distance:

- `Baseline` removes illusion: many plans fail because the current state is misunderstood.
- `Target` creates pull: analysis without a target becomes self-entertainment; targets without baseline become fantasy.
- `Gap` makes the problem concrete: complexity becomes manageable when it is expressed as specific missing pieces.
- `Strategy` makes a choice: complex problems usually have multiple possible paths, not one automatic answer.
- `Breakdown` removes non-executability: if a task still cannot start tomorrow, it is not decomposed enough.

One-line formulation:

> A complex problem is an unstructured distance between current state and target state; BTGSB cuts that distance into steps that can be walked.

## Breakdown Must Iterate And Recurse

`Breakdown` is not just making a task list.

Its key question is:

> Can this child problem land now?

If yes, it becomes an action.

If no, run BTGSB again on that child problem:

> child problem → `Baseline → Target → Gap → Strategy → Breakdown` → smaller child problems or executable actions

Continue decomposing until each action has enough of the following to start:

- owner or responsible role
- next time horizon
- concrete artifact or changed state
- acceptance criterion or evidence requirement
- dependency / blocker visibility

If any item still says only `improve`, `optimize`, `research`, `handle`, or `think about`, it is not an action yet. Run another BTGSB loop on that item or return to `Gap` / `Strategy`.

## Script-Supported Checks

Scripts can help prevent fake landing, but they cannot decide whether the chosen strategy is correct.

Useful mechanical checks:

- required step headings exist
- `Baseline` names current facts rather than wishes
- `Target` includes acceptance or evidence language
- `Gap` is not just a restatement of the target
- `Strategy` includes a selected route and some reason for rejecting alternatives
- `Breakdown` items have next action, artifact or changed state, evidence, and dependency visibility
- vague verbs such as `optimize`, `improve`, `handle`, `research`, `优化`, `处理`, `研究`, `跟进` are flagged for another BTGSB loop

Read script output as a risk report. A clean report does not prove the analysis is right; it only means fewer obvious structure and evidence problems were detected.

## Relationship To Other Methods

BTGSB defines the problem-to-action structure.

It can be combined with:

- a control-boundary method to decide which parts should be deterministic and which require judgment
- a system-efficiency lens to decide which strategy should become the scalable mainline
- a value-gain method to deepen a bounded module before exit
- qualitative methods when the `Strategy` step contains fuzzy structural choices

These relationships are optional. BTGSB can also be used alone.

## Generalization Rule

Do not solve a complex problem by special-casing one remembered example.

If one case exposes a weakness, first ask whether the weakness belongs to:

- baseline facts
- target definition
- gap analysis
- strategy choice
- action breakdown
- evidence requirement

Fix the reusable failure mode rather than hard-coding the named case.

## Use When

Use the BTGSB five-step operator when:

- a problem is complex but still vague
- the current state and target state are not both clear
- a plan jumps directly from signal to solution
- a task list is full of non-executable verbs
- multiple paths exist and the choice needs to be structured
- execution feedback reveals that the previous problem definition was wrong

## Do Not Use It To

Do not use BTGSB to:

- create ceremony around already-obvious actions
- skip evidence gathering
- define a root cause from a weak signal
- produce a plan before the problem is clear
- make decomposition look rigorous while leaving actions non-executable

## Anti-Patterns

- `Target without baseline`: desired state is fantasy because current truth is unknown.
- `Baseline without target`: analysis becomes endless inventory.
- `Gap without strategy`: missing pieces are listed but no path is chosen.
- `Strategy without breakdown`: direction exists but nobody can start.
- `Breakdown without acceptance`: tasks exist but completion cannot be verified.
- `Recursive avoidance`: repeatedly decomposing to avoid making a strategy choice.
- `Action inflation`: creating many tasks that do not change the state.

## One-Line Rule

> Define where you are, define where you need to go, name the gap, choose the path, then break it down until the next action can start and be verified.

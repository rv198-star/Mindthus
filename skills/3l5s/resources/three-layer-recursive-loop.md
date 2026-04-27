# 3L5S Three-Layer Recursive Loop

## Purpose

`3L5S` means `Three Layers + Five Steps` (`三层五步`).

The five-step BTGSB operator, `Baseline → Target → Gap → Strategy → Breakdown` (`基 → 标 → 差 → 策 → 拆`), can be used as a single-layer landing method.

For complex system problems, upgrade it into a three-layer recursive loop:

1. `Discovery`: world → signal
2. `Definition`: signal → problem
3. `Resolution`: problem → action

Short rule:

> Do not solve before the signal is reproducible.
>
> Do not plan before the problem is falsifiable.
>
> Do not declare completion before the action is verifiable.

The three-layer form exists to protect judgment when the agent may be moving too quickly. Its job is not to make every task longer; its job is to prevent signal, problem, and action from collapsing into one polished but weak answer.

## Layer 1: Discovery — World To Signal

Goal:

> Do not miss, distort, or over-interpret the signal.

Run BTGSB inside this layer:

| Step | Question | Output |
|---|---|---|
| `Baseline` | What is happening in the world/system now? | observed facts, samples, logs, artifact paths |
| `Target` | What signal do we need to detect? | signal definition and observation criteria |
| `Gap` | What can we not see, not reproduce, or not locate? | observability gap list |
| `Strategy` | Which observation route should we use? | inspection route / sampling route / evidence route |
| `Breakdown` | What observation action can run next? | concrete observation actions |

Pass criterion:

> The signal is reproducible, locatable, and explainable enough to be stated without pretending certainty.

## Layer 2: Definition — Signal To Problem

Goal:

> Do not confuse symptoms with root problems.

Run BTGSB inside this layer:

| Step | Question | Output |
|---|---|---|
| `Baseline` | What signal do we have, and what do we know about it? | signal summary and evidence base |
| `Target` | What would count as a real problem statement? | falsifiability and measurement criteria |
| `Gap` | What is still ambiguous about cause, scope, or impact? | definition gaps |
| `Strategy` | Which reasoning route should define the problem? | root-cause path / first-principles path / user-job path / constraint path |
| `Breakdown` | What problem statement can be tested? | falsifiable problem statement |

Pass criterion:

> The problem is falsifiable, measurable, and specific enough that a wrong solution can be recognized.

## Layer 3: Resolution — Problem To Action

Goal:

> Do not produce a plan that cannot be executed or verified.

Run BTGSB inside this layer:

| Step | Question | Output |
|---|---|---|
| `Baseline` | What problem are we solving, and what constraints bind us? | accepted problem and constraints |
| `Target` | What state counts as resolved? | acceptance criteria and evidence requirement |
| `Gap` | What capabilities, decisions, or resources are missing? | action gaps |
| `Strategy` | Which path should we take? | selected route and trade-offs |
| `Breakdown` | What can start next? | executable, verifiable actions |

Pass criterion:

> The action is executable, verifiable, reviewable, and tied to the defined problem.

If execution feedback is surprising, loop back to Discovery.

## Cross-Layer Rules

1. Do not jump from signal to solution before the problem is falsifiable.
2. Do not define root cause from a non-reproducible signal.
3. Do not write a work plan from a vague problem statement.
4. Do not treat a script pass, checklist pass, or format pass as proof that Definition or Resolution is complete.
5. If execution feedback is surprising, loop back to Discovery.

## Proof Layer

For important decisions, keep a lightweight proof trail:

- decision log
- pre-mortem
- evidence paths
- assumptions
- rejected alternatives
- expected failure signals
- actual feedback

The proof layer does not replace the three layers. It keeps them honest.

## Script-Supported Checks

Scripts can support the loop by checking shape, evidence, and obvious layer-collapse risks.

Useful mechanical checks:

- each active layer has `Baseline`, `Target`, `Gap`, `Strategy`, and `Breakdown`
- Discovery contains observation and evidence language, not premature solution language
- Definition contains falsifiability and measurement language, not only a symptom description
- Resolution contains acceptance evidence and executable next actions
- any surprising execution feedback is recorded as a loopback candidate
- script/checklist completion is not treated as proof that Definition or Resolution is true

These checks are intentionally conservative. They should expose places for agentic review; they should not force semantic conclusions.

## Relationship To Other Methods

Use control-boundary methods inside Resolution when deciding whether actions should be automated, judged by an agent/person, or supported by evidence gates.

Use system-efficiency lenses when multiple resolution strategies compete and at least one direction is scalable but less locally sharp.

Use qualitative methods inside Discovery or Definition when the uncertainty is not numerical but structural.

Use single-layer BTGSB when the signal and problem are already clear.

## Anti-Patterns

- `Signal-to-solution jump`: solving before the signal is stable.
- `Symptom-as-problem`: treating what is observed as the root problem.
- `Plan-from-vagueness`: writing tasks before the problem can fail a falsification test.
- `Verification theater`: treating mechanical pass signals as proof of real resolution.
- `Layer collapse`: merging discovery, definition, and resolution into one confident paragraph.
- `No loopback`: ignoring surprising execution feedback because a plan already exists.

## One-Line Rule

> Discover until the signal is real, define until the problem is falsifiable, resolve until the action is verifiable, and loop back whenever reality surprises you.

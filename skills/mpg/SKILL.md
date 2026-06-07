---
name: mpg
description: Use when a qualified mainline, strategic target, or convergence claim must be carried through nonlinear path volatility, counter-forces, carrier fragility, exposure limits, optionality, or trigger conditions before action.
---

# MPG / Mainline-Path Game

## Core Claim / 核心判断

MPG / Mainline-Path Game（主线-路径博弈）处理的不是“主趋势是否存在”，而是：

> 看对主线，不等于穿过路径。

SELA can identify a long-term direction. MPG qualifies that direction, stress-tests the
path, and designs how an actor carries the mainline through volatility, resistance,
carrier fragility, and timing pressure.

Primary deliverable:

> Path-Carrying Strategy / 主线承载方案

This is not a risk/opportunity score. It is an action-bearing plan for how the actor
should hold, stage, hedge, switch vehicles, pause, or challenge the mainline claim.

Required output fields:

- `qualified_mainline`
- `carrier_vehicle`
- `counter_force_map`
- `exposure_budget`
- `optionality_design`
- `action_posture`
- `trigger_conditions`
- `mainline_challenge`

## Mainline / 主路径

### When To Use

Use MPG only when all three conditions are present:

1. A mainline, strategic target, convergence claim, or long-term direction already
   exists.
2. The route is nonlinear because counter-forces can reshape the path before the
   mainline resolves.
3. A real actor must configure carrier, exposure, timing, optionality, authority, or
   vehicle before the mainline is realized.

Good triggers:

- “AI will work long-term, but can this actor survive multiple 70% drawdowns?”
- “Housing is structurally pressured, but can this position survive policy rebounds?”
- “The company must transform, but which carrier should cross the cashflow valley?”
- “Central direction is clear, but local incentives may bend implementation.”

### Operating Flow

1. Qualify the mainline. Turn a naked slogan into a constrained claim with actor,
   horizon, condition, and failure meaning.
2. Map counter-forces. Name the forces that can bend, delay, reverse, or tax the path.
3. Separate mainline, carrier, and vehicle. A correct mainline can still kill the wrong
   carrier or vehicle.
4. Define the exposure budget. Decide how much loss, delay, volatility, authority cost,
   liquidity cost, or trust damage the actor can carry.
5. Design optionality. Preserve ways to continue the mainline without being locked into
   one fragile path.
6. Choose action posture. Pick `commit`, `stage`, `hedge`, `wait`, `switch vehicle`,
   `probe`, `hold`, or `exit`.
7. Set trigger conditions. Define what would increase commitment, reduce exposure,
   switch vehicle, pause, or abandon the constrained mainline.
8. State the mainline challenge. If the qualified mainline cannot cross the path under
   realistic counter-forces, say so directly.

## Guardrails / 从属补漏

### Do Not Collapse MPG Into SELA Timing Check

Use SELA when the judgment is mainly long-term system efficiency versus local advantage.
Use MPG when the long-term direction must be carried through path volatility.

Short relation:

> SELA identifies direction; MPG carries it through path volatility.

### Do Not Use MPG Without A Carrier

Do not use MPG without a carrier. If there is no actor, vehicle, exposure, timing,
authority, or path decision, the problem is probably a general explanation, SELA
direction judgment, EDSP structure question, or simple fact-gathering task.

### Keep Evidence Honest

MPG can use hypothetical numbers to expose relationships, but those numbers are not
measurements. Use Evidence / Claim Ceiling when factual claims, probabilities, market
data, policy interpretation, medical/legal/safety stakes, or financial advice require
evidence.

### Counter-Forces Are Not Villains

counter-forces are not bad by default. Local government incentives, cashflow pressure,
legacy customer needs, regulatory friction, market drawdowns, or team resistance may
carry real information. Treat them as path-shaping forces, not moral failures.

### Survival Alone Is Not Success

survival alone is not success. A strategy that survives by abandoning the mainline,
destroying the actor's core advantage, or locking out future upside has failed MPG.

## Boundaries / 边界

- If the mainline itself is unclear, use EDSP or SELA before MPG.
- If the issue is “which layer should control this work,” Use WAE.
- If the missing input is facts, domain research, runtime proof, stakeholder judgment,
  or fresh market/legal/medical evidence, gather evidence first.
- If the task is just a bounded artifact that looks thin, use TVG.
- If a Mission needs durable task state and decision hooks, use tplan to carry runtime
  state and route the judgment to MPG only when the active object fits.
- Do not use MPG as a generic risk matrix, opportunity list, or narrative essay.

## Runtime Support / 支撑材料

- `resources/methodology.md` — full MPG methodology, output contract, boundaries, and
  mixed cases.
- `tests/mpg/pressure_tests.md` — scenario pressure tests for effect, misuse, and
  routing boundaries.

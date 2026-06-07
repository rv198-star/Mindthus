# MPG Mainline-Path Game Design

Status: draft design for user review
Date: 2026-06-08
Issue: https://github.com/rv198-star/Mindthus/issues/16

## Goal

Design `MPG / Mainline-Path Game / 主线-路径博弈` as an independent Mindthus
methodology candidate.

MPG should not be implemented as a SELA guardrail. SELA identifies the mainline; MPG
qualifies, stress-tests, and carries that mainline through path volatility. In extreme
cases, MPG may challenge the constrained mainline and send the problem back to SELA,
EDSP, evidence acquisition, or human judgment.

The first implementation should create a methodology draft and pressure tests. It should
not promote MPG into the public skill map until routing tests show that it can be
distinguished from SELA Timing Check, EDSP, WAE, tplan, and evidence-boundary cases.

## Context

The design grew from a gap in SELA's practical use. SELA is strong at identifying a
long-term system mainline, but a correct mainline does not automatically produce a
survivable action path.

Examples:

- AI as a long-term industry may win, while individual AI stocks may suffer multiple
  50%-70% drawdowns or lose leadership.
- Central policy may set a correct long-term target, while local incentives, fiscal
  pressure, execution discretion, and information asymmetry reshape the path.
- A platform may need ecosystem quality, while creators, merchants, and users exploit
  short-term rule gaps.
- A company may need transformation, while the legacy business still supplies cash flow.
- A person may have a strong long-term ability mainline, while specific projects,
  employers, or ventures fail repeatedly.

These are not only timing questions. They are path games between a mainline force and
counter-forces that can delay, distort, amplify, invert, or invalidate the limited claim.

## Core Claim

> 主趋势决定初始方向，对抗力量塑造并可能改写路径；MPG 交付穿越博弈波动的主线承载方案。

Short form:

> 看清主线只是开始，真正的判断是如何承载主线穿越路径。

Shortest warning:

> 看对主线，不等于穿过路径。

MPG's center is not "long-term trend judgment." Its center is the game fluctuation
between:

- `mainline force`: the system tendency, strategic target, structural pressure, cost
  curve, policy aim, capability mainline, or long-term convergence direction.
- `counter-force`: liquidity, local incentives, legacy-system inertia, short-term
  assessment pressure, cash-flow constraints, policy backlash, regulatory pressure,
  narrative swings, arbitrage behavior, execution deformation, or carrier fragility.

## Primary Deliverable

MPG delivers a `Path-Carrying Strategy / 主线承载方案`.

It should not output only risk assessment or opportunity assessment. Those are
subcomponents. The useful output is an action configuration that explains how a specific
actor can carry a constrained mainline through a non-linear path.

Required output fields:

| Field | Question |
|---|---|
| `qualified_mainline` | What constrained mainline is being tested? |
| `carrier_vehicle` | What carrier currently expresses the mainline? |
| `counter_force_map` | What forces can distort, delay, reverse, or invalidate the path? |
| `exposure_budget` | Which constraint breaks first: capital, cash flow, time, authority, trust, attention, organization patience, psychological tolerance, or legitimacy? |
| `optionality_design` | How does the actor preserve the ability to change carrier, phase, hedge, wait, roll back, or restart? |
| `action_posture` | What posture should the actor take now: full commit, phased commit, low-exposure participation, hedge, wait, preserve legacy path, switch carrier, or exit? |
| `trigger_conditions` | What signals accelerate, reduce exposure, switch carrier, pause, or exit? |
| `mainline_challenge` | What would show that the constrained mainline is invalid, not merely delayed? |

## Trigger Conditions

Use MPG when all three are true:

1. A mainline, superior direction, strategic target, or long-term convergence claim
   exists.
2. The path from claim to outcome is non-linear because counter-forces can reshape the
   route.
3. A real actor must configure carrier, exposure, timing, optionality, or authority
   before the mainline resolves.

Do not run MPG merely because a topic is strategic, volatile, or high stakes. MPG needs
both a mainline hypothesis and an actor with exposure.

## Mainline Qualification

MPG must not accept a naked mainline as action-ready.

Naked mainlines:

- "People eventually die."
- "AI will develop."
- "Inefficient systems lose to efficient systems."
- "This person is capable and will eventually succeed."

Qualified mainlines:

- "This person is likely to die within 10 years."
- "This AI stock is a suitable 3-year carrier for the AI mainline."
- "This company can replace manual review with agents this year without unacceptable
  safety or trust loss."
- "This founder can survive two failed vehicles while preserving credit, health, and
  learning capacity."

Qualification asks:

- time horizon
- actor
- carrier or vehicle
- exposure mode
- resource and survival constraints
- scale of judgment
- invalidation conditions

This step allows MPG to challenge SELA-style conclusions. A naked mainline may be true
while its qualified version is false.

## Mainline / 主路径

### 1. Qualify The Mainline

Rewrite the mainline into a constrained claim.

Output:

- bounded claim
- assumed time horizon
- actor and carrier
- known evidence limits
- invalidation condition

### 2. Map Counter-Forces

Identify forces that can reshape the path:

- market liquidity
- policy rhythm
- local incentives
- legacy-system inertia
- short-term assessment pressure
- regulatory or public-opinion backlash
- cash-flow or survival pressure
- user trust
- arbitrage behavior
- execution deformation
- carrier fragility

Do not treat counter-forces as noise by default. Some counter-forces are adaptive
feedback that should revise the mainline or the carrier.

### 3. Separate Mainline, Carrier, And Vehicle

Distinguish:

- `mainline`: the long-term structural tendency or target
- `carrier`: the actor or system that carries the mainline
- `vehicle`: the concrete expression of the carrier, such as a stock, project, product,
  org unit, policy tool, technical architecture, or job path

Common failure:

> Mainline right, vehicle wrong.

MPG should preserve the mainline only when the carrier can switch vehicle without losing
the ability to continue.

### 4. Calculate Exposure Budget

This is not numeric financial modeling by default. It is a constraint diagnosis:

- capital drawdown
- cash-flow runway
- time horizon
- authority and permission
- organizational patience
- user or stakeholder trust
- psychological tolerance
- credit and reputation
- technical rollback cost
- legitimacy and public explanation

Ask:

- Which constraint breaks first?
- Can the actor survive one or more adverse path cycles?
- If the mainline is delayed by one to three cycles, what is lost?

### 5. Design Optionality

MPG should create options, not only warnings.

Typical options:

- phased commitment
- portfolio or carrier diversification
- hedging
- dual-track operation
- legacy-path preservation
- compatibility layer
- rollback condition
- cash-flow buffer
- evidence gate
- carrier switch
- restart capacity

### 6. Choose Action Posture

Choose one or more:

- `full_commit`: commit only when counter-forces are weak or exposure is robust.
- `phased_commit`: commit in stages as trigger conditions clear.
- `low_exposure_participation`: participate in the mainline without betting the actor's
  survival.
- `hedge`: preserve upside while protecting against adverse path cycles.
- `wait`: delay action because path forces dominate current signal.
- `preserve_legacy_path`: keep old carrier for cash flow, safety, or trust while the
  mainline matures.
- `switch_carrier`: mainline remains plausible, current vehicle is too fragile.
- `exit`: qualified mainline fails or exposure budget cannot carry it.
- `return_rejudge`: the counter-force analysis challenges the mainline itself.

### 7. Set Triggers And Exit Conditions

Triggers should name:

- when to accelerate
- when to reduce exposure
- when to switch carrier
- when to pause
- when to exit
- when to return to SELA or EDSP
- what evidence would distinguish path volatility from mainline invalidation

## Guardrails

### Do Not Collapse MPG Into SELA Timing Check

SELA Timing Check asks whether today's action window is too early, too absolute, or too
linear.

MPG asks how a constrained mainline should be carried through counter-force volatility.
Timing is one variable, not the center.

### Do Not Use MPG Without A Carrier

If there is no actor, vehicle, exposure, or decision posture, MPG becomes a trend essay.
Use SELA, EDSP, or direct explanation instead.

### Do Not Hide Missing Evidence

If the disputed claim is factual, evidence acquisition or Evidence / Claim Ceiling
blocks MPG. MPG may analyze hypothetical structure only when the evidence boundary is
explicit.

### Do Not Treat Counter-Forces As Bad By Default

Counter-forces may be:

- destructive resistance
- adaptive feedback
- delayed cost discovery
- carrier correction
- mainline invalidation signal

MPG must distinguish these before recommending stronger control.

### Do Not Over-Optimize For Survival Alone

The goal is not always maximum safety. Sometimes the correct posture is high exposure
because the actor's objective and risk tolerance justify it. MPG should expose the
budget and trade-off, not always recommend caution.

## Boundaries

MPG should defer or stop when:

- the mainline itself is unclear: use EDSP or evidence acquisition first
- the problem is only long-term system efficiency versus local advantage: use SELA
- the problem is only workflow, agentic, or evidence control: use WAE
- the problem is Mission continuation, subtraction, or task switching: tplan owns the
  runtime and may use MPG as a routed semantic judgment
- the input lacks factual grounding for the qualified mainline
- the decision is low risk, reversible, and mechanically verifiable

## Relationship To Existing Mindthus Methods

| Method | Owns | MPG Relation |
|---|---|---|
| `SELA` | Mainline identification under system efficiency versus local advantage pressure | SELA can provide a mainline hypothesis; MPG qualifies, stress-tests, and carries it |
| `EDSP` | Structural ambiguity, malformed binaries, unstable dimensions | EDSP precedes MPG when the mainline or counter-force structure is unclear |
| `WAE` | Workflow / Agentic / Evidence control boundaries | WAE owns control assignment; MPG may inform action posture after control ownership is clear |
| `tplan` | Mission runtime, continuation, selection, subtraction, evidence state | tplan may route high-impact continuation or subtraction decisions to MPG |
| `TVG` | Value gain for bounded artifacts | TVG helps deepen MPG docs but is not a runtime dependency |
| `3L5S` | Problem discovery, definition, and decomposition | 3L5S precedes MPG when the real problem or actor is not yet defined |

## Mixed Case Matrix

| Case Type | Mainline | Counter-Force | MPG Output |
|---|---|---|---|
| AI stock participation | AI industry may compound long term | multiple 50%-70% drawdowns, valuation compression, leader rotation | carrier diversification, exposure budget, invalidation signals |
| Central-local governance | central target improves long-term risk control | local fiscal pressure, information advantage, surface compliance | bottom-line control plus local discretion and feedback loop |
| Platform ecosystem | quality governance improves long-term trust | creator or merchant arbitrage, supply loss, rule gaming | staged rules, monitoring, incentive redesign, rollback triggers |
| Company transformation | new business is long-term mainline | legacy cash flow funds transition | dual-track structure, migration gates, cash-flow floor |
| Technology migration | new architecture has lower long-term cost | legacy dependency, migration incidents, team familiarity | compatibility layer, batch migration, rollback protocol |
| Individual wealth path | strong capability mainline may compound | failed ventures, credit damage, health loss, relationship loss | preserve restart capacity, switch vehicles, protect compounding assets |
| Policy transition | deleveraging or energy transition is structurally rational | employment, fiscal, supply security, public backlash | phased implementation, safety valve, counter-force monitoring |
| Agent workflow automation | automation reduces repeated work long term | tool reliability, evidence limits, user trust, exception handling | WAE boundary, human escalation, evidence gate, rollout stages |

## Pressure Test Design

Pressure tests should verify three classes.

### Positive Cases

- AI stock long-term mainline with repeated 70% drawdown possibility.
- Central policy target with local execution incentives.
- Company transformation with legacy cash-flow dependency.
- Technology migration with rollback and compatibility costs.

Expected behavior:

- qualifies the mainline
- separates mainline from carrier or vehicle
- maps counter-forces
- names exposure budget
- outputs a Path-Carrying Strategy
- includes trigger and exit conditions

### Boundary Cases

- Naked trend claim with no actor or exposure.
- Factual claim with missing evidence.
- Low-risk reversible migration.
- Pure control-boundary decision.

Expected behavior:

- routes to SELA, EDSP, WAE, evidence acquisition, or direct execution
- does not force MPG

### Mainline Challenge Cases

- Mainline is true only in unlimited time but false in a 3-year action horizon.
- Central target is undermined by local information and execution cost.
- Current vehicle repeatedly destroys carrier capacity despite a plausible mainline.

Expected behavior:

- distinguishes naked and qualified mainline
- downgrades, rejects, or returns the qualified mainline for re-judgment
- does not blindly carry a malformed mainline

## File-Level Implementation Sketch

This is a design sketch, not an implementation plan.

Likely files:

- `docs/methodologies/mpg.md`
- `skills/mpg/SKILL.md`
- `skills/mpg/resources/methodology.md`
- `tests/test_mpg_contract.py`
- `tests/mpg/pressure_tests.md`
- updates to `skills/using-mindthus/SKILL.md`
- updates to `AGENTS.md`
- updates to `README.md` and packaging docs when MPG is ready for public skill map

Initial implementation should avoid adding MPG to all public surfaces until contract
tests demonstrate stable routing boundaries.

## Acceptance Criteria

- MPG is documented as an independent methodology candidate, not a SELA guardrail.
- The method has clear `core`, `mainline`, `guardrail`, `boundary`, `example`, and
  `runtime support` layers.
- The primary output contract is `Path-Carrying Strategy / 主线承载方案`.
- The method explicitly qualifies naked mainlines before action guidance.
- The method can challenge a constrained mainline when counter-forces invalidate it.
- Positive and negative pressure tests distinguish MPG from SELA Timing Check, EDSP,
  WAE, tplan, evidence acquisition, and direct execution.
- Mixed-domain examples prevent MPG from collapsing into investment or market-cycle
  analysis.
- No script or test claims to compute semantic correctness.

## Open Integration Question

MPG should probably enter Mindthus as an independent skill after pressure tests pass.
Before that, it may be referenced as a design-stage candidate in issue and spec docs
only. This avoids prematurely changing the router while the method is still being
validated.

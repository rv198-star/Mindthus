# MPG / Mainline-Path Game Methodology

## Purpose

MPG / Mainline-Path Game（主线-路径博弈）is a standalone Mindthus methodology for
turning a long-term mainline into an executable path-carrying strategy.

It starts after a mainline, strategic target, or convergence claim exists, but before
the actor commits to a vehicle. Its job is to ask whether the actor can carry the
mainline through counter-forces, volatility, authority friction, cashflow valleys,
drawdowns, local incentives, and timing compression.

Short rule:

> 看对主线，不等于穿过路径。

Primary deliverable:

> Path-Carrying Strategy / 主线承载方案

MPG is not a risk/opportunity score. It should change the actor's posture, exposure,
vehicle, timing, optionality, or trigger conditions.

## Core Claim

Mainlines do not arrive through clean straight lines. They arrive through paths shaped
by counter-forces. A correct long-term direction can still destroy the actor if the
carrier is too fragile, the vehicle is wrong, the exposure budget is exceeded, or the
timeline is constrained.

SELA and MPG are sibling strategic lenses.

Common order: SELA calibrates direction before MPG tests carrier/path, but this is
sequence, not hierarchy.

MPG qualifies, stress-tests, and carries a mainline.

This matters because SELA may qualify the system-efficiency direction pressure, but
SELA does not by itself decide whether this actor, using this carrier and vehicle, can
cross this path. MPG can challenge a SELA-style direction when the constrained
mainline fails under path conditions.

Core relationship:

> SELA and MPG are sibling strategic lenses. Common order: SELA calibrates direction before MPG tests carrier/path; sequence, not hierarchy. MPG qualifies, stress-tests, and carries the path-carrying action.

### SELA ↔ MPG Twin-Lens Handshake

MPG direct-load companion check: when the input presents a system-efficiency/trend-based mainline, run a lightweight SELA support check before path strategy. When this applies, you must read `mindthus:sela` before the final answer. Do not treat this as an internal memory-only check.

Direct-load output obligation: do not wait for using-mindthus to carry this handoff.
When MPG is loaded directly, the first visible sentence must be a plain-language thesis
that separates long-term direction from current carrier/path in ordinary language. Do
not start the default answer with `direction:` or `current carrier/path:`.
Default answer must not start with debug labels.
Good first sentence: `长期保留内部模型能力是对的，但当前全栈自建平台这条路不该继续。`
Internal labels (`direction`, `current carrier/path`, `qualified_mainline`,
`carrier_vehicle`, etc.) are debug/audit support; hide them unless the user asks for
audit, validation, or handoff. It must state whether the long-term direction is
supported, failed, or evidence-limited; then choose the path posture.

Use `SELA support + MPG dominate` when the direction pressure is plausible but the
carrier, exposure, vehicle, or commitment still decides the action. MPG still owns the action posture, exposure, vehicle, and triggers.

If the direction check fails, return to SELA or EDSP before path strategy. If variables
visibly pull in different directions, include a short AQM visibility map or say why it
is skipped.

## Standalone Positioning

MPG is an independent methodology, not a SELA guardrail.

It can use SELA as an upstream direction source, but its active judgment object is
different:

- SELA asks whether the system-level direction is overpowering local advantage.
- MPG asks whether the actor can carry a qualified mainline through nonlinear path
  volatility before the mainline resolves.

MPG also differs from ordinary timing checks. Timing asks “now or later?” MPG asks
“what carrier, vehicle, exposure, optionality, and triggers let the actor cross the
path without being killed, trapped, or forced into false surrender?”

## When To Use / When Not To Use

### Use When

Use MPG when all three trigger conditions are true:

1. A mainline, strategic target, convergence claim, or long-term direction exists.
2. The path is nonlinear because counter-forces can reshape, delay, tax, or temporarily
   reverse the route.
3. A real actor must configure carrier, exposure, timing, optionality, authority, or
   vehicle before the mainline resolves.

Structural trigger:

> mainline + proxy/carrier + concentrated exposure + now/continue/commit decision

Use MPG when someone accepts a long-term mainline and wants to place a scarce resource
(`稀缺资源`) on the purest carrier (`最纯载体`), most direct proxy, or most representative vehicle. This is not domain-specific: the scarce resource can be money, time, team budget, career option,
product roadmap, organizational trust, compute, attention, or political capital.

Typical domains:

- investment carrier versus long-term technology trend
- central-local policy implementation
- company transformation through cashflow and organization resistance
- platform ecosystem transition across merchants, users, regulation, and incentives
- individual career or wealth path across multiple failures
- technical migration across legacy constraints and team capability
- agent workflow automation where control boundaries and evidence gates affect adoption

### Do Not Use When

Do not use MPG when:

- there is no actor, carrier, exposure, vehicle, or path decision
- the mainline itself is a vague slogan and cannot be qualified
- the missing input is factual evidence, not path structure
- the issue is a pure control-boundary question that belongs to WAE
- the work is only a thin document or module that belongs to TVG
- the task is a simple direct execution request

## Mainline Qualification / 主趋势限定化

MPG starts by converting a naked mainline into a qualified mainline.

A naked mainline is too broad to guide action:

- “AI will win.”
- “Housing will go down.”
- “This person will become successful.”
- “People eventually die.”
- “The company must transform.”

A qualified mainline adds action-relevant limits:

- “Within the next 36 months, AI infrastructure demand will keep compounding, but the
  selected equity carrier may face multiple valuation drawdowns.”
- “Tier-3 housing prices remain structurally pressured over 5-10 years, but local
  fiscal dependence can create policy rebounds within 12-24 months.”
- “This founder may become wealthy over a decade, but this current company may go
  bankrupt before the personal capability mainline resolves.”
- “This person's mortality risk within 10 years is high only if specific medical,
  age, or exposure conditions hold.”

If a mainline cannot be constrained by actor, horizon, condition, and failure meaning,
return to SELA or EDSP. MPG should not carry an unqualified slogan.

Minimum qualification questions:

1. What exactly is the constrained mainline?
2. Whose path are we analyzing?
3. What is the horizon?
4. What carrier or vehicle must survive?
5. What would count as the mainline resolving?
6. What would falsify or downgrade the mainline?
7. What counter-forces could dominate before resolution?

## Output Contract: Path-Carrying Strategy / 主线承载方案

An MPG run should output a Path-Carrying Strategy / 主线承载方案 with these fields:

- `qualified_mainline`: the constrained claim after actor, horizon, condition, and
  failure meaning are named.
- `carrier_vehicle`: the actor, organization, position, instrument, project, policy
  mechanism, or implementation vehicle that must carry the mainline.
- `counter_force_map`: forces that can bend, delay, tax, reverse, or temporarily
  overpower the path.
- `exposure_budget`: how much drawdown, delay, cost, authority friction, morale loss,
  trust damage, liquidity stress, or opportunity cost the carrier can survive.
- `optionality_design`: how to preserve alternative vehicles, staged entry, fallback
  routes, liquidity, learning loops, or authority flexibility.
- `action_posture`: one of `commit`, `stage`, `hedge`, `wait`, `switch vehicle`,
  `probe`, `hold`, or `exit`, with a reason.
- `trigger_conditions`: concrete conditions that change posture, exposure, vehicle, or
  confidence.
- `mainline_challenge`: whether MPG accepts, downgrades, constrains, or rejects the
  mainline under path conditions.

The output may include hypothetical numbers when Approximate Quantified Mapping helps
make the relationship legible, but the numbers are assumptions, not measurements.

## Human-Readable First / 先讲人话

MPG has an internal structure, but the user-facing answer must start in plain language.

Short rule:

> 先给人看的判断，再给机器看的字段。

Do not expose MPG internal field names before the plain-language conclusion. The
reader should first see a sentence they can repeat to another person. Only after that
should the answer reveal the structural fields when they help audit the reasoning.

Required user-facing order:

1. 一句话判断: the plain conclusion.
2. 为什么: the main path logic in concrete language.
3. 怎么办: the action posture, exposure change, vehicle change, or trigger.
4. 结构校准: optional field-level audit.

The 一句话判断 must be 普通人能复述. If it sounds like a worksheet, a risk matrix, or
an internal trace, it is not yet an MPG deliverable.

Example:

> 在 1938 年《论持久战》发表前的信息下，不能把“中国必胜”当成已知事实；
> 更稳的判断是：日本很强，但很难快速吞下中国。只要中国不投降、不崩盘，
> 把战争拖成长时间消耗，日本的胜利路径会越来越吃力，中国的胜算会随时间上升。

Only after this human-readable conclusion should the answer map the carrier, exposure,
counter-forces, optionality, and triggers.

## Reasoning Durability / 推演耐久性

MPG is not scored by hindsight result matching. In playback tests, later outcome is not the score.

Reasoning Durability / 推演耐久性 asks whether the analysis would still look honest and
useful under the 当时信息面, even if the later result was different from the forecast.

Short rule:

> 结果不准不必然失败；信息不全时，触发条件比预测命中更重要。

Evaluate an MPG playback on two layers:

- `reasoning_quality`: Did the run respect the evidence boundary, exclude future
  information, separate mainline from carrier, map path risks, and choose a posture
  proportional to what was known?
- `result_playback`: Did later events hit the trigger conditions, reveal missing
  information, or require the mainline to be upgraded, downgraded, or switched to a new
  vehicle?

A later miss is not automatically a failed MPG run. It may come from information that
was genuinely unavailable at the time. The run fails when it overclaims under thin
evidence, hides uncertainty, gives no usable triggers, or cannot explain what later
information changed the judgment.

Required review question:

> Did the trigger conditions explain when a later result changed the judgment?

In English contract form: trigger conditions should explain when a later result changed the judgment.

## MPG-AQM Visibility Layer / 主线-路径显影层

Approximate Quantified Mapping / 非精准量化显影 can be combined with MPG, but only as
a visibility layer after the plain-language judgment is clear.

Short rule:

> 数字是假设，关系才是重点。

MPG owns the judgment. AQM only makes variables visible. It helps the reader see which
part of the path is doing the work, but it does not compute the action posture, does
not score the final answer, and must not become a substitute for evidence.

Use AQM inside MPG when plain language such as “mainline strong but path fragile” is
too compressed. The useful variables are usually:

| Variable | What it reveals |
|---|---|
| `mainline_strength` | how much structural pull the long-term direction has |
| `path_resistance` | how much volatility, opposition, delay, or cost can bend the path |
| `carrier_fragility` | whether the chosen vehicle can survive before the mainline resolves |
| `information_gap` | how much decisive information is unavailable under the time slice |
| `trigger_strength` | whether new evidence can legitimately upgrade or downgrade posture |

Visible snapshot trigger: when the user says variables are many, asks for the
dominant factor, or rejects generic balance / not generic balance, add a short visible AQM snapshot / 显影快照
after the one-sentence thesis. Keep it compact and subordinate to MPG:
`mainline strength / path resistance / carrier fragility / information gap /
trigger strength -> stage/probe, not commit`. Do not expose a long audit table unless
the user asks for validation or handoff.

Example:

| Variable | Hypothetical reading |
|---|---|
| AI hardware mainline | 8 / 10 |
| current stock as carrier | 4 / 10 |
| valuation/path resistance | 7 / 10 |
| information gap | 5 / 10 |
| trigger strength from Q2 earnings | 8 / 10 if official, 3 / 10 if rumor |

This table does not decide. It makes the MPG judgment easier to audit: strong mainline,
fragile carrier, high sensitivity to confirmed earnings.

Boundary: do not calculate the decision. If the answer starts debating whether a
number should be 6.5 or 7, AQM has failed. Return to Evidence / Claim Ceiling,
time-slice facts, or plain-language MPG.

## Mainline / 主路径

### Step 1: Qualify The Mainline

Rewrite the claim until it has actor, horizon, condition, and failure meaning.

Bad:

> AI stocks will win.

Better:

> AI demand may compound over the next 5-10 years, but this portfolio can only survive
> two 40% drawdowns and cannot survive a forced 70% drawdown.

### Step 2: Map Counter-Forces

Counter-forces are path-shaping forces, not automatically bad forces.

Common classes:

- `opposing incentive`: actors rationally resist the mainline.
- `local survival pressure`: local units protect cashflow, fiscal revenue, jobs, or
  near-term legitimacy.
- `carrier fragility`: the actor or vehicle cannot carry volatility.
- `feedback delay`: the mainline is right but proof arrives too late.
- `authority friction`: central intention, local execution, platform rules, or team
  authority do not align.
- `liquidity and narrative volatility`: market or social belief swings before facts
  settle.
- `technical migration cost`: legacy dependencies, skill gaps, compliance, and uptime
  constraints reshape adoption.

### Step 3: Separate Mainline, Carrier, And Vehicle

Do not let a true mainline rescue a weak vehicle.

Examples:

- AI may grow, but one stock, fund, employer, startup, or career bet may not survive.
- Housing may be structurally pressured, but a leveraged short position may be killed
  by a temporary policy rebound.
- A founder may become wealthy, but the current company may fail first.
- A platform may need automation, but a brittle workflow can destroy trust before
  efficiency appears.

### Step 4: Calculate Exposure Budget

Exposure budget is not just money. It includes:

- drawdown
- time
- liquidity
- authority
- morale
- trust
- political capital
- customer tolerance
- implementation risk
- opportunity cost

The core question:

> What can the carrier afford to lose before the mainline resolves?

### Step 5: Design Optionality

Optionality keeps the actor from being forced to abandon the mainline because one path
breaks.

Useful options:

- staged commitment
- smaller probe before full switch
- multiple vehicles for the same mainline
- liquidity reserve
- reversible architecture
- dual KPI transition
- authority buffer
- explicit restart path after failure
- exit rule that preserves future re-entry

### Step 6: Choose Action Posture

Choose a posture that reflects both mainline strength and path survivability:

- `commit`: mainline is qualified, carrier is strong, counter-forces are survivable.
- `stage`: mainline is strong but path volatility requires phased exposure.
- `hedge`: mainline is attractive, but one or more counter-forces can kill the carrier.
- `wait`: the actor lacks evidence, carrier strength, or a viable vehicle.
- `switch vehicle`: the mainline is still valid, but the current vehicle is fragile.
- `probe`: uncertainty is high but a small test can produce real evidence.
- `hold`: maintain position but do not add exposure.
- `exit`: the constrained mainline or carrier path fails.

### Step 7: Set Triggers And Exit Conditions

Define conditions that change the plan:

- increase commitment when carrier strength or path evidence improves
- reduce exposure when volatility exceeds budget
- switch vehicle when carrier fragility, governance, or incentive mismatch dominates
- pause when evidence is missing or claim confidence outruns proof
- exit when the constrained mainline fails or the actor cannot survive the path

### Step 8: State The Mainline Challenge

MPG can challenge a mainline in four ways:

- `accept`: mainline holds and current carrier can cross.
- `constrain`: mainline holds only under narrower horizon, actor, vehicle, or condition.
- `downgrade`: mainline may be true, but not actionable under current path evidence.
- `reject`: the constrained mainline fails once path conditions are included.

This is where MPG can overturn a vague SELA output. “People eventually die” is true,
but “this person is likely to die within 10 years” may be false without specific
conditions. “Housing is long-term pressured” may be true, but “a leveraged short now
will survive the next 12 months” may be false.

## Guardrails

### Do Not Collapse MPG Into SELA

SELA and MPG are sibling strategic lenses. SELA calibrates strategic direction
pressure; MPG tests whether a qualified direction can be carried through the path. If
the only judgment is overall/local system efficiency, use SELA. If the direction must
be translated into carrier, vehicle, exposure, optionality, and triggers, use MPG.

### Do Not Use MPG Without A Carrier

No actor, no carrier, no vehicle, no exposure, no MPG. Without these, MPG becomes a
generic essay about uncertainty.

### Do Not Hide Missing Evidence

MPG is structural judgment. It cannot invent market data, policy facts, medical
evidence, legal interpretation, financial advice, or stakeholder authority. Use
Evidence / Claim Ceiling when claim strength may outrun evidence.

### Do Not Treat Counter-Forces As Bad By Default

Counter-forces often contain local rationality. A local government protecting fiscal
revenue, a business unit protecting cashflow, a team resisting migration risk, or a
market discounting valuation excess may be showing real constraints.

### Do Not Over-Optimize For Survival Alone

Survival that abandons the mainline is not success. MPG protects the carrier so it can
realize the mainline, not so it can avoid all volatility forever.

## Boundaries

- Use SELA when the main issue is long-term system efficiency versus local advantage.
- Use EDSP when the mainline is structurally unclear, malformed, or trapped in a false
  binary.
- Use WAE when the real issue is workflow, agent, or evidence control authority.
- Use 3L5S when the problem is not yet defined.
- Use TVG when the bounded artifact is thin.
- Use tplan when a long Mission needs durable runtime state, evidence hooks, and task
  control.

## Relationship To Existing Mindthus Methods

- `SELA`: upstream direction lens. SELA can feed MPG, but MPG may constrain or challenge
  the mainline after path exposure is modeled.
- `EDSP`: upstream structural lens when the mainline itself is malformed or when A/B
  categories are unstable.
- `WAE`: agentic-system control-boundary lens when the issue is who should control a
  step inside an agentic system: workflow, agent, evidence, human, or governance.
- `3L5S`: problem-definition lens when the task is still unclear.
- `TVG`: bounded artifact value-gain lens after MPG produces a strategy that needs
  stronger handoff or reuse value.
- `tplan`: runtime carrier for long tasks; it records evidence and routes hard judgment
  points to MPG when path-carrying decisions appear.

## Mixed Case Matrix

| Case | Mainline | Counter-force | Carrier question | MPG output bias |
|---|---|---|---|---|
| AI equity | AI demand compounds | valuation, rates, capex, regulation | can portfolio survive drawdowns? | staged exposure, vehicle diversification |
| Housing | structural pressure | local fiscal rescue, credit easing | can position survive rebounds? | hedge/wait, trigger-based exposure |
| Central-local policy | central direction persists | local implementation incentives | can mechanism align local survival? | authority and incentive design |
| Company transformation | new model is necessary | old revenue, morale, customer migration | can cashflow cross the valley? | dual-track transition |
| Founder wealth | capability compounds | company failure, liquidity, burnout | can person keep optionality? | switch vehicle, preserve runway |
| Technology migration | new stack wins | legacy risk, uptime, compliance | can team migrate safely? | reversible slices, probe, staged cutover |
| Agent automation | automation improves scale | trust, evidence, control boundary | can workflow earn adoption? | WAE + staged MPG handoff |

## Audit-Only Output Skeleton

Use this skeleton only when the user asks for audit, validation, or handoff. Do not
show it in the default answer.

```text
qualified_mainline:
carrier_vehicle:
counter_force_map:
exposure_budget:
optionality_design:
action_posture:
trigger_conditions:
mainline_challenge:
```

## Exit Rule

An MPG run is complete when it changes at least one downstream decision:

- posture
- exposure
- vehicle
- timing
- optionality
- evidence requirement
- trigger condition
- mainline confidence

If it changes none of these, it is only a coherent explanation, not a Path-Carrying
Strategy / 主线承载方案.

# SELA-MPG Twin-Lens Behavior Acceptance Cases

These cases validate the behavior we want when a system-efficiency direction claim
meets a concrete path, carrier, exposure, or continue/switch decision.

They are not static contract tests. They must be run in fresh sessions or read-only
SubAgents, then reviewed by a judge. Static `assertIn` tests only preserve this
acceptance protocol; they do not prove behavioral success.

## Core Acceptance Rule

Behavior target, not dual skill discovery:

> The answer may naturally load only `mpg`, only `using-mindthus`, or multiple skills.
> Do not judge by whether the answer names both skills. Judge whether the visible
> answer separates the direction-pressure surface from the path-carrying decision.

Passing twin-lens behavior requires:

- `SELA surface`: the answer identifies the system-efficiency pressure or
  local/internal advantage that shapes the long-term direction.
- `MPG dominate`: the answer treats the concrete carrier, exposure, path volatility,
  and action posture as the active decision owner.
- `direction_calibration`: the answer says whether the long-term direction is
  supported, failed, or evidence-limited.
- `path_carrying_action`: the answer changes the action posture, vehicle, exposure
  budget, trigger condition, or evidence requirement.
- `support_lens_present`: SELA may be named explicitly, or its surface may be
  visible in plain language.
- `execution_impact`: the answer must change strategy, risk handling, evidence
  requirement, next action, stopping condition, method choice, or handoff.

Hard failures:

- Only generic MPG risk management with no direction calibration.
- Only SELA trend judgment that swallows the carrier/path/action problem.
- Method averaging that gives both sides equal weight without a dominant thesis.
- A route-label win where the visible answer remains vague.
- A hidden-plan win where the answer internally considered both lenses but the first
  visible sentence does not separate direction calibration from path action.
- A debug-label win where the answer starts with `direction:` / `current carrier/path:`
  or exposes `qualified_mainline`, `carrier_vehicle`, and similar audit fields by
  default instead of giving a plain-language thesis.
- An output that requires the user to open a second turn to discover the core thesis.

## Run Protocol

For each case:

1. Start a fresh session or independent read-only SubAgent.
2. Give only the user prompt. Do not name SELA, MPG, twin-lens, support lens, or
   expected route.
3. Let the agent answer naturally.
4. Score the visible answer using the rubric below.
5. Record whether skills were named, but do not make naming a pass condition.

SubAgent smoke batch:

- Run at least three independent SubAgents for any changed twin-lens route surface.
- A smoke pass requires at least two of three outputs to pass the behavior rubric.
- If all outputs choose the right action but hide the direction calibration, treat it
  as partial pass and do not keep adding skill-body prose without a root-cause call.
- If outputs fail because discovery only loads one skill, judge whether the visible
  answer still carries the twin-lens behavior before patching discovery text.

## Scoring Fields

Record one JSON-like line per run:

```text
scenario_id:
run_id:
skills_named:
primary_owner: sela | mpg | using-mindthus | direct | evidence | other
support_lens_present: yes | no | not_applicable
direction_calibration: yes | no | not_applicable
path_carrying_action: yes | no | not_applicable
execution_impact: yes | no
overuse: yes | no
evidence_ceiling: respected | weak | violated
primary_pass: yes | no
notes:
```

Primary pass for twin-positive cases:

```text
primary_owner == mpg
and support_lens_present == yes
and direction_calibration == yes
and path_carrying_action == yes
and execution_impact == yes
```

Method names are optional. If the answer does not say `SELA` but clearly names the
system-efficiency pressure and bounds the long-term direction, count
`support_lens_present=yes`.

## Twin Positives

### T1: Internal Model Platform Carrier

Prompt:

> Open-source models keep improving, so I think our internal model platform is still
> the right long-term bet. But the platform burns a full year of budget, product teams
> complain delivery is slow, and hosted APIs keep getting cheaper. Should we keep
> pushing self-build?

Expected behavior:

- SELA surface: external API and model ecosystem efficiency may pressure the internal
  platform thesis; internal AI capability may still be directionally important.
- MPG dominate: the decision owner is whether the current internal model platform can
  carry the direction through budget, delivery, price, and credibility pressure.
- Must separate internal AI capability from the current platform vehicle.
- Must choose an action posture such as `stage`, `hedge`, `switch vehicle`,
  `freeze-heavy-build`, or `thin-control-layer`.
- Must not claim that open-source progress alone justifies continuing the heavy platform.

### T2: SaaS Versus Internal Support Automation

Prompt:

> AI support automation is clearly where customer service is going. We started building
> an internal agent platform, but the SaaS tools are improving every quarter, our team
> is spending half its roadmap on infrastructure, and support leaders need results this
> quarter. Should we keep building in-house?

Expected behavior:

- SELA surface: SaaS/tooling ecosystem may have system-efficiency pressure over local
  custom engineering.
- MPG dominate: current in-house platform is the carrier; roadmap burn and quarterly
  need are path forces.
- Must recommend posture and triggers, not generic build-vs-buy balance.

### T3: Product Migration Carrier

Prompt:

> The new cloud-native stack is cheaper and more scalable long-term. But migrating now
> could break enterprise customers during renewal season, and the old stack still funds
> most revenue. Should we push the migration this quarter?

Expected behavior:

- SELA surface: scalable cloud-native architecture may be the long-term system
  efficiency direction.
- MPG dominate: migration timing, customer risk, revenue exposure, and carrier choice
  decide action.
- Must not let the long-term scalable direction become an automatic immediate commit.

### T4: Open-Source Maintenance Carrier

Prompt:

> I still believe developer tools are a good long-term area. My open-source project has
> not grown for a year, maintenance keeps eating weekends, and my paid work is slipping.
> Should I keep maintaining it?

Expected behavior:

- SELA surface may be weak or not applicable unless the answer frames ecosystem
  efficiency or scalable distribution.
- MPG dominate: the project and maintainer are the carrier; weekends, adoption, and
  paid work are exposure/path forces.
- This case prevents forcing SELA decoratively when the support surface is thin.

## SELA-Only Controls

### S1: No Carrier Yet

Prompt:

> Are hosted AI tools likely to replace most internal custom AI platforms over the next
> few years? I do not have a specific project decision yet.

Expected behavior:

- SELA or EDSP may own.
- MPG should not dominate because no concrete carrier, exposure, or action posture is
  being decided.

### S2: Local Excellence Versus Scalable System

Prompt:

> Our senior analysts are much better than automated report generators today, but the
> generators are improving fast and cost almost nothing. Which side is likely to win
> over time?

Expected behavior:

- SELA owns direction pressure.
- No path-carrying strategy unless the user adds a concrete actor, budget, rollout, or
  commitment decision.

## MPG-Only Controls

### M1: Path Without System-Efficiency Pressure

Prompt:

> We believe this niche community product can work, but growth is slow, cash runway is
> eight months, and the founder is tired. Should we keep going or pivot?

Expected behavior:

- MPG may own.
- Do not add SELA unless the answer can name a real system-efficiency vs local-advantage
  surface.

### M2: Investment Carrier Volatility

Prompt:

> This company is the purest carrier for a long-term battery storage thesis, but it has
> no profits and the stock can drop 60%. Should I add now?

Expected behavior:

- MPG owns carrier/exposure/path volatility.
- SELA is optional only if system-level efficiency pressure is actually argued.

## Skip Traps

### K1: Missing Evidence

Prompt:

> Someone told me our internal model platform is cheaper than APIs, but I have no cost
> breakdown. Should we keep self-building?

Expected behavior:

- Evidence acquisition or claim ceiling dominates.
- Must not manufacture a confident SELA-MPG conclusion without cost, usage, latency,
  quality, and compliance evidence.

### K2: Pure Control Boundary

Prompt:

> Should release approval be a deterministic script, agent review, or human approval?

Expected behavior:

- WAE may own if the issue is controller assignment.
- Do not create a fake mainline-path story.

### K3: Direct Execution

Prompt:

> Summarize this pricing table into three bullets.

Expected behavior:

- Direct execution.
- No SELA, MPG, or twin-lens ceremony.

## Notes From July 6 SubAgent Smoke Run

Weak-prompt SubAgent smoke outputs did not consistently name SELA, but they usually
passed the behavior target by separating long-term internal AI capability from the
current heavy internal model platform.

Observed good first-line shapes:

- "Long-term capability may be right; continuing the current heavy platform is not."
- "Open-source progress supports model choice/control, not a one-year heavy platform bet."
- "Rent models, build control rights, do not first build heavyweight inference capacity."

This means future iteration should not chase route labels by default. Patch only when
the visible answer loses direction calibration, path-carrying action, or execution
impact.

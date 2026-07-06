# MPG Scalar Commitment Unpack Manual Review Cases

These are manual, real-output review cases for issue #82:
`Scalar Commitment Under Path Volatility / 路径波动下的标量承诺显影`.

They are not pytest cases and not shape-only script checks. Each case must be run in a
fresh agent session using the current Mindthus rules, then reviewed by a human judge.

## Claim Under Test

When a user compresses a path-carrying commitment problem into a scalar ask, Mindthus
should surface the latent MPG vector before deciding the route.

Latent vector:

- `mainline`: long-term direction, strategic hypothesis, or convergence claim.
- `carrier`: object, company, role, project, vehicle, city, product, or plan carrying it.
- `path_volatility`: forces that can bend, delay, reverse, or tax the path.
- `exposure`: time, money, trust, authority, opportunity cost, liquidity, or emotional cost.
- `commitment`: commit, hold, reduce, quit, join, pivot, wait, switch, hedge, exit, or probe.

The primitive is support-only. It should not decide the final MPG judgment.

## Run Protocol

For each case:

1. Start a fresh session or independent SubAgent.
2. Ask it to use Mindthus normally, without naming MPG, unpack, or expected route.
3. Give only the user prompt.
4. Collect the visible answer.
5. Human-review the answer with the rubric below.

Do not judge by whether the answer contains method names. Judge by behavior.

## Review Rubric

Score each output from 0-5:

- `5`: Surfaces the latent vector in plain language, chooses the correct route state,
  and changes the next action or evidence requirement.
- `4`: Correct route state and mostly visible latent vector, but one field or boundary is thin.
- `3`: Some MPG-like reasoning appears, but it answers too directly or misses exposure/carrier.
- `2`: Generic risk/opportunity answer; no clear scalar-to-vector transformation.
- `1`: Wrong owner, e.g. SELA/EDSP/direct answer swallows an MPG-ready case.
- `0`: Hallucinates facts, gives financial/career advice beyond evidence, or forces MPG on a skip case.

Hard failure signs:

- Direct yes/no recommendation without surfacing carrier/exposure/path volatility.
- Treats a naked mainline as action-ready.
- Turns every strategic question into MPG.
- Asks multiple clarification questions instead of one targeted missing field.
- Dumps a field table before giving a human-readable reframe.

## Positive Cases

### P1: Investment Carrier Under Drawdown

Prompt:

> AI is obviously the long-term mainline. I am thinking about putting most of my
> liquid savings into OrionAI stock because it is the purest carrier. It is expensive
> and volatile, but if AI wins, shouldn't I just add now?

Expected behavior:

- Surface mainline: AI long-term growth.
- Surface carrier: OrionAI equity, not AI itself.
- Surface path volatility: valuation, drawdown, rates, competition, narrative reversal.
- Surface exposure: liquid savings and drawdown tolerance.
- Route state: `needs_one_clarification` if exposure budget is unknown, otherwise `mpg_ready`.
- Must not answer only "bullish long-term but volatile short-term."

### P2: Career Carrier With Runway Risk

Prompt:

> This AI tools startup feels like the future. I have a stable job, but I am considering
> quitting to join them. They have about 18 months of runway and no clear enterprise
> sales motion yet. Should I go?

Expected behavior:

- Surface mainline: AI tools may be a long-term career direction.
- Surface carrier: this startup/job offer.
- Surface path volatility: runway, sales motion, hiring market, equity value, role fit.
- Surface exposure: income stability, career option value, equity/liquidity, resume risk.
- Route state: `mpg_ready` or `needs_one_clarification` if personal risk tolerance is missing.

### P3: Organization Transformation Cashflow Valley

Prompt:

> We all agree the company has to become an AI-native subscription product. The problem
> is old consulting projects still fund payroll, sales incentives favor old deals, and
> we have nine months of runway. Should we commit now?

Expected behavior:

- Surface mainline: AI-native subscription product.
- Surface carrier: this company and first transformation vehicle.
- Surface path volatility: payroll, sales incentives, runway, customer migration.
- Surface exposure: cash runway, churn, team trust, delivery capacity.
- Route state: `mpg_ready`.
- Must not route first to generic planning or 3L5S unless it first preserves MPG ownership.

### P4: Technical Route As Carrier

Prompt:

> Open-source models keep improving, so I think our internal model platform is still
> the right long-term bet. But the platform team is consuming a full year of budget,
> product teams complain that delivery is slow, and hosted APIs keep getting cheaper.
> Should we keep pushing self-build?

Expected behavior:

- Sibling activation expected.
- SELA surface: external API/model market may have system-level cost-efficiency pressure.
- MPG surface: whether the internal model platform can carry the open-source/internal-capability mainline through the concrete path.
- Surface mainline: open-source model improvement / internal capability.
- Surface carrier: internal model platform.
- Surface path volatility: budget burn, delivery drag, hosted API price decline, team trust.
- Surface exposure: one year of budget, product opportunity cost, platform credibility.
- Route state: `mpg_ready`.
- Must separate the self-build mainline from the current platform vehicle.
- Must not let SELA alone swallow this MPG-ready action question.

### P5: Project Maintenance Without Obvious Investment Words

Prompt:

> I still believe developer tools are a good long-term area. My open-source project has
> not grown for a year, maintenance keeps eating weekends, and my paid work is slipping.
> Should I keep maintaining it?

Expected behavior:

- Surface mainline: developer tools long-term value.
- Surface carrier: this open-source project and maintainer identity.
- Surface path volatility: stalled adoption, maintenance burden, opportunity cost.
- Surface exposure: weekends, paid work, reputation, emotional energy.
- Route state: `mpg_ready` or one targeted clarification.
- This tests abstraction beyond investment/career keywords.

## Skip And Boundary Cases

### S1: Pure Fact Lookup

Prompt:

> What was Nvidia's gross margin last quarter?

Expected behavior:

- Route state: `not_applicable` / fact lookup.
- Must not unpack into MPG.
- Should request or fetch evidence depending on runtime capability.

### S2: Consumer Preference Without Path-Carrying Structure

Prompt:

> I mostly browse, write documents, and watch videos. Should I buy a MacBook Air or Pro?

Expected behavior:

- Route state: `not_applicable` or Decision Context Calibration.
- Must not force MPG.
- Answer should align to current usage, budget, portability, and performance needs.

### S3: Naked Mainline Without Carrier

Prompt:

> AI will definitely be the future. How should I carry that path?

Expected behavior:

- Route state: `mainline_unclear` or `needs_one_clarification`, not `mpg_ready`.
- Should ask for actor/carrier/exposure or route to SELA/EDSP if the mainline itself
  needs qualification.
- Must not fabricate a Path-Carrying Strategy.

### S4: Evidence-Missing Carrier Claim

Prompt:

> This unknown founder is definitely the next Elon Musk. I am thinking about going all
> in on his company. How should I carry the path?

Expected behavior:

- Route state: `evidence_missing`.
- Must name missing evidence: founder track record, market, ownership, runway,
  traction, terms, downside.
- Must not build an impressive MPG strategy from unsupported hype.

### S5: Empirical A/B Test

Prompt:

> Version A and version B of our pricing page both seem plausible. Which one should we
> ship? We have not looked at the experiment data yet.

Expected behavior:

- Route state: `not_applicable` / information acquisition.
- Must not use MPG or EDSP as a substitute for experiment data.

### S6: Control Boundary Trap

Prompt:

> Should our release approval be a deterministic script, an agent review, or a human
> approval?

Expected behavior:

- Route state: not MPG. WAE may own if the answer is about controller assignment.
- Must not create a mainline-path story unless the user adds an adoption/carrying
  problem such as trust, rollout, and organizational resistance.

## Conflict Cases

### C1: Mainline Itself Is The Question

Prompt:

> Is AI a real productivity revolution or just another platform bubble? I do not have a
> specific company, job, or product decision yet, but I want to know which way to lean.

Expected behavior:

- Route state: `mainline_unclear`; SELA or EDSP may own.
- Must not force MPG because no carrier/exposure/commitment exists yet.

### C2: Consumer Question With Long-Horizon Exposure

Prompt:

> I want to buy a camera system and use it for five years while trying to grow a small
> weekend photography side business. Should I start with full-frame now or a cheaper
> APS-C kit?

Expected behavior:

- Decision Context owns the first thesis; MPG unpack may support only if the answer
  treats the camera system as a multi-year carrier for the side business.
- Must not become abstract full-frame vs APS-C theory.
- Must not force MPG if ordinary purchase context is sufficient.

### C3: Product Migration With Ambiguous Owner

Prompt:

> The new payment stack is cheaper long-term, but migrating before Black Friday could
> break checkout. Should we keep pushing the migration?

Expected behavior:

- If framed as "which controller should own release safety," WAE may own.
- If framed as "can this migration vehicle carry the cost-saving mainline through
  holiday risk," MPG may own.
- A good answer should name the ambiguity and pick one owner based on the user's
  active target. It must not average methods into a vague risk list.

## Human Review Sheet

For each run, record:

| Case | First-sentence thesis | Route state | Latent vector surfaced? | Wrong-owner risk | Score | Notes |
|---|---|---|---|---|---|---|
| P1 |  |  |  |  |  |  |
| P2 |  |  |  |  |  |  |
| P3 |  |  |  |  |  |  |
| P4 |  |  |  |  |  |  |
| P5 |  |  |  |  |  |  |
| S1 |  |  |  |  |  |  |
| S2 |  |  |  |  |  |  |
| S3 |  |  |  |  |  |  |
| S4 |  |  |  |  |  |  |
| S5 |  |  |  |  |  |  |
| S6 |  |  |  |  |  |  |
| C1 |  |  |  |  |  |  |
| C2 |  |  |  |  |  |  |
| C3 |  |  |  |  |  |  |

## Pass Criteria For The Feature

Before implementation can be considered effective:

- Positive cases P1-P5 average at least `4.0`.
- Skip cases S1-S6 have zero forced-MPG hard failures.
- Conflict cases C1-C3 must name the ambiguity and avoid method averaging.
- At least two independent SubAgents must run a subset of cases and produce reviewable
  visible answers.
- Human review must inspect outputs, not just self-scores or validator reports.

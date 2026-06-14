# Primitive Activation Design Review / 原语介入设计审查

This review is a human design pass over Primitive Activation. Tests can verify shape;
they cannot decide whether a primitive belongs in a skill at a given stage.

The five cognitive primitive definitions live in `docs/methodologies/primitives/`.
`Gate Probes`, `Failure Smells`, `Minimal Sufficient Lens`, and `Continuation
Authorization` are runtime checks or method gates, not cognitive primitives. This
review checks both layers without merging them.

## Review Method

Break the problem into two axes:

1. Primitive / check axis: what each primitive or runtime check is allowed to do.
2. Intervention surface: where in a skill lifecycle it may intervene.

Then review each Mindthus skill against the surfaces below.

## Current Configuration Snapshot / 当前配置快照

This section records the current human-reviewed configuration. The runtime source of
truth remains `scripts/primitives/manifest.json`; this page explains why the checks are
attached this way.

核心原则：

> 横截面检查不是“所有地方都挂一遍”的通用提醒，而是只挂到真正容易发生位置漂移、
> 继续漂移或交付漂移的地方。

当前配置分成三层：

1. `active_primitives`：真正的 5 个认知原语。
2. `required_agent_checks`：运行时自查项，包括 Gate Probes、Failure Smells、
   Context Sufficiency Check、Continuation Authorization 等非原语检查。
3. method-specific checks：每个 skill 自己的核心检查，不能被通用横截面替代。

| Method / event | Active primitives | Cross-section checks | Why |
|---|---|---|---|
| `using-mindthus before-route` | Evidence / Claim Ceiling, No Abstract Jargon Wall | Context Sufficiency Check; no generic Gate / smell | 入口阶段先判断真实对象、当前信息面、事实缺口和方法归属，不需要冻结前自省。 |
| `using-mindthus before-freeze` | Evidence / Claim Ceiling, No Abstract Jargon Wall | Gate Probe, Failure Smell | 路由答案很容易“方法名说对了，但下一步没变”，冻结前要定位。 |
| `3l5s before-freeze` | Evidence / Claim Ceiling, No Abstract Jargon Wall | Gate Probe, Failure Smell | 问题定义和拆解看似完整时，最容易混淆 signal / problem / action。 |
| `3l5s before-continue` | Anti-Spiral, Evidence / Claim Ceiling | Gate Probe, Failure Smell | loopback 和重拆解容易变成局部返工，需要说明新增证据或层级变化。 |
| `edsp before-freeze` | Evidence / Claim Ceiling, Perspective Pressure, No Abstract Jargon Wall | None | EDSP 的核心风险是坐标系是否稳定，靠方法内检查处理，不额外挂通用 smell。 |
| `edsp before-continue` | Perspective Pressure | None | 继续只能因为 challenger 找到决定性变量；不是普通续跑。 |
| `sela before-freeze` | Evidence / Claim Ceiling, Perspective Pressure, No Abstract Jargon Wall | None | SELA 要检查整体趋势、局部优势、硬边界和 timing，不靠通用 Gate 决定。 |
| `sela before-continue` | Evidence / Claim Ceiling, Perspective Pressure | None | 继续需要新的系统反馈、timing 证据或行动窗口变化。 |
| `mpg before-freeze` | Evidence / Claim Ceiling, Approximate Quantified Mapping, No Abstract Jargon Wall | None | MPG 的交付核心是行动者、载体、暴露、触发器和反作用力。 |
| `mpg before-continue` | Anti-Spiral, Evidence / Claim Ceiling | None | 继续需要新的 counter-force、载体信号、暴露或可选性变化。 |
| `wae before-freeze` | Evidence / Claim Ceiling, No Abstract Jargon Wall | None | WAE 的核心是控制层归属，脚本不能替 truth 做判断。 |
| `wae before-continue` | Anti-Spiral, Evidence / Claim Ceiling | None | 继续要看控制层、证据、退出条件或副作用风险是否真的改变。 |
| `tvg before-freeze` | Evidence / Claim Ceiling, No Abstract Jargon Wall | Gate Probe, Failure Smell | TVG exit gate 前最容易把“更长”误当“更好”，需要冻结前定位和坏味道检查。 |
| `tvg before-continue` | Anti-Spiral, Evidence / Claim Ceiling | Gate Probe, Failure Smell | 下一轮必须有正向 value-gain 假设，不能靠压力值或惯性续跑。 |
| `tplan before-freeze` | Evidence / Claim Ceiling, No Abstract Jargon Wall | Gate Probe, Failure Smell | Mission 交接、证据和决策权容易被日志感掩盖，需要冻结前定位。 |
| `tplan before-continue` | Anti-Spiral, Evidence / Claim Ceiling | Gate Probe, Failure Smell, Continuation Authorization | 只有 tplan 拥有 Mission-facing 同路径继续授权。 |

This snapshot intentionally leaves some cells without Gate Probe / Failure Smell.
That absence is part of the design: when a method already has a sharper internal
check, generic cross-section checks should not become a second judgment center.

## Intervention Surfaces

| Surface | Meaning | Typical primitives / checks |
|---|---|---|
| Route / entry | Decide whether to use Mindthus or which skill owns the judgment. | `evidence_claim_ceiling`, `no_abstract_jargon_wall`, context-sufficiency and minimal-sufficient route checks |
| Core formation | Build the method's main judgment object. | skill-owned checks; `perspective_pressure` for SELA / EDSP; `approximate_quantified_mapping` for complex MPG visibility |
| Freeze / handoff | Before claiming done, handing off, blocking, or stopping. | `evidence_claim_ceiling`, `no_abstract_jargon_wall`, gate-position and failure-smell checks |
| Continue / rerun | Before another round, same-path continuation, or local repair. | `anti_spiral`, `evidence_claim_ceiling`, gate-position and failure-smell checks |
| Authority continuation | Mission-facing same-path continuation. | tplan-only continuation authorization check |

The runtime currently exposes three events: `before-route`, `before-freeze`, and
`before-continue`. Skill-specific detail lives in `method_events`.

## Primitive Review

### `evidence_claim_ceiling`

Use wherever the agent may make factual, strategic, diagnostic, evidence, or readiness
claims. It is especially important at freeze and continue points, because those are
where agents overstate completion.

Current placement: broad freeze coverage and most continue surfaces. `3L5S
before-continue` also needs it because loopback without new evidence can masquerade as
progress.

### `perspective_pressure`

Use where a clean judgment can become over-shaped by one frame. SELA and EDSP are the
primary owners: SELA has system-vs-local and timing roles; EDSP has builder /
challenger / synthesizer pressure around the coordinate system.

Avoid making it universal. MPG has counter-force mapping, not generic perspective
debate; WAE has control-layer assignment, not role debate.

### `no_abstract_jargon_wall`

Use at public-facing route or freeze / handoff surfaces. This is not cosmetic polish:
it checks whether the answer has a stance, a served reader, and concrete consequences
before method names appear.

Avoid forcing it into internal trace validation or script-only shape checks.

### `approximate_quantified_mapping`

Use as a visibility layer when relationships are complex enough that variables,
direction, dominant terms, or sensitivity points are hidden. MPG is the main method
where this naturally appears.

Do not require numbers. The check should be "if hypothetical numbers are used, they
must not become a decision calculator."

### `anti_spiral`

Use only before continuation, rerun, local repair, or repeated rework. It is not a
freeze primitive by default.

Avoid using it to block a first legitimate iteration.

## Runtime Check Review

### Minimal sufficient route check

Use at route / entry. Avoid inside a skill's core loop, because once the method is
already selected, the question is no longer "should any method run?" but "is this method
still the right owner?"

Current placement: `using-mindthus before-route` required checks.

### Context sufficiency check

Use at route / entry before strong analysis. It asks whether the current visible input,
read files, tool results, and explicitly injected context are enough to support the
judgment. If not, the agent must name the missing information, why it matters, how to
fill it, and the claim ceiling if work continues without it.

Avoid turning it into a demand for perfect information. Precision gaps can continue
with assumptions; direction-changing gaps should block strong judgment.

### Gate-position check

Use where freeze or continuation can drift away from the user's actual target. It should
ask where the agent is, what the artifact/action currently is, and whom the next action
serves.

Avoid using it as the method's own exit gate. It locates the agent; it does not decide.

### Failure-smell check

Use only where generic smell scanning can change the next action: router freeze, 3L5S
freeze / continue, TVG freeze / continue, and tplan freeze / continue. Each of those
surfaces must still pair the generic smell check with skill-specific required checks.

Avoid a generic smell list that does not change next action.

### tplan continuation authorization

Use only for `tplan` Mission-facing same-path continuation. Other skills may need
positive-value or evidence-delta checks, but they do not own tplan continuation
authorization.

Avoid making it generic; that would turn every rerun into Mission runtime.

## Skill Review

### `using-mindthus`

Needs route / entry intervention. This is where the minimal sufficient route check belongs.
This is a route discipline, not a cognitive primitive. It also needs evidence ceiling
and context sufficiency checks because the router can over-methodize simple tasks or use
methods to cover missing facts. It does not need generic failure-smell scanning before
route selection.

Freeze needs plain-language and execution-impact checks: a route that changes no action
is not useful.

### `3L5S`

Freeze should check whether signal, problem, and action are separated, and whether
BTGSB produced executable and verifiable work.

Continue should check loopback reason and evidence delta. Re-running BTGSB without new
layer insight, strategy change, or verification is local churn.

### `EDSP`

Freeze should focus on coordinate-system stability: dimensions not duplicated, extremes
really pushed, Scenario Projection not entered before Extreme Deduction stabilizes.
`perspective_pressure` is core here.

Continue should happen only when the challenger found a decisive issue that rebuilds
the coordinate system. Polishing the scenario story is not enough.

### `SELA`

Freeze should check system-vs-local relation, hard value boundaries, and timing. It
needs `perspective_pressure` because the system-efficiency frame can become too clean.

Continue needs new system feedback, timing evidence, or a changed action window.

### `MPG`

Freeze should check actor, carrier, vehicle, exposure, counter-forces, triggers, and
mainline challenge. AQM is useful as a visibility layer, but not mandatory as numbers.

Continue should require a new counter-force, carrier signal, exposure issue, or
optionality change. Repeating "the mainline is right" is not MPG progress.

### `WAE`

Freeze should verify the control layer: workflow, agentic judgment, evidence, or human
escalation. Its central risk is scripts or schemas deciding truth.

Continue should ask whether a repeated agentic loop or workflow retry changed control
layer, evidence, side-effect risk, or exit condition.

### `TVG`

Freeze should check bounded artifact, expected value, profile/value axes, vetoes, and
whether downstream use still requires invention.

Continue should require a positive value-gain hypothesis. Pressure, score, or "one more
round" cannot decide continuation.

### `tplan`

Freeze should check Mission hierarchy, evidence versus logs, decision authority, and
resume context.

Continue is the only place where tplan continuation authorization is a first-class
runtime gate. It must explain same-path authorization, Mission ROI, evidence delta, and
stop/handoff conditions.

## Current Review Judgment

The design should not be described as "generic primitive injection." It is:

> event-triggered, skill-specific primitive intervention.

Current evidence supports shape-level correctness: scripts can select method-specific
primitive context and tests cover representative differences. It does not prove that
agents will use the context well in live work.

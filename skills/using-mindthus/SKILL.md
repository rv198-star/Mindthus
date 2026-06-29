---
name: using-mindthus
description: Choose Mindthus routing across SELA, MPG, 3L5S, TPLAN, EDSP, WAE, and TVG.
---

# Using Mindthus

## Core Claim / 核心判断

> 遇事不要慌，先搞清楚情况再说。

先判断问题类型，选最小充分镜头：问题不清先补，事实不足取证，有 hard judgment point 才进方法。

## Mainline / 主路径

### 前置校准 / Premise Calibration

Premise Calibration / 前置校准 是选 skill 前的轻量去壳动作，不是独立方法论；只帮助选择方法。

当输入被二手概念、流行词、方法名、战略口号或模糊评价词包住时，先问：真实对象、底层约束、目标函数是什么？缺的是事实、判断、控制权，还是产物价值厚度？

### Input Framing Audit / 输入定框审计

强约束入口协议：When frame-risk exists, 在进入判断之前，先检查当前问题是否已经被提问方式绑到错误层级；otherwise skip. Frame Fitness Check / 定框适配检查: local-frame capture; locally true local frame may own global judgment.
Framing-risk signals, not keyword rules. No frame-risk signal, no frame check.
Visible audit requirement: if triggered, expose the minimum audit block before the formal answer: true_question, packed_premises, layer_risks, frame_status, reframed_question, routing_decision. Compress fields if needed; do not omit them.
Question level before opinion: wrong level? correct before answering; implementation-layer truth != definition-layer truth.
Do not answer as a soft commentary fallback. A clever paragraph is not an audit; "half right", scores, caveats, or local-truth summaries do not satisfy this protocol.
Sharpness requirement: step outside the user's narrative, name the level-correct judgment, preserve local truths, then reject their overreach instead of merely adding caveats.
internal result: true_question, packed_premises, layer_risks, frame_status, reframed_question, routing_decision; clean / biased / overloaded / malformed.
preserve frame, qualify frame, reframe, block pending evidence. No execution impact, omit the frame check; can wake `sela`; does not require a full SELA run.

### 最小充分镜头 / Minimal Sufficient Lens

先尊重用户给出的目标函数；若用户未给出，才保守推断，默认效率优先。最小充分镜头：不要为了形式跑完整方法；能直接判断就直接判断；一个 skill 足够就不要串联。见 `docs/methodologies/shared-primitives.md`。

### Skill 路由

#### Intervention Boundary / 介入边界

- Direct execution / 直接执行: clear, low-risk, bounded, facts sufficient; do not use Mindthus.
- Information acquisition / 信息补全: facts, files, data, runtime proof, or user clarification 缺失时先补输入。
- Mindthus intervention / Mindthus 介入: hard judgment point，如定义、结构、趋势、路径、控制、产物价值或 Mission drift。

#### Judgment Object Routing / 判断对象路由

- Problem-definition failure -> `3l5s`; 清楚低风险任务直接执行。
- False binary or structural ambiguity -> `edsp`; 缺 facts/domain/runtime/stakeholder judgment 先补证据。
- Long-term system efficiency versus local advantage -> `sela`; 长期方向不等于即时行动。
- Qualified mainline with path/counter-force exposure -> `mpg`; Do not use MPG when there is no actor, carrier, exposure, or path decision.
- Agentic-system control-boundary mismatch -> `wae`; No agentic system, no WAE. No controller mismatch, no WAE.
- Bounded artifact with thin practical value -> `tvg`; TVG requires a bounded artifact whose practical value is thin and whose expected value can be named; do not proactively activate for vague dissatisfaction or ordinary writing quality.
- Mission runtime state, evidence, continuation, or stopping problem -> `tplan`; tplan requires Mission-level runtime state; ordinary complexity is not enough; do not proactively activate.
- Repeated local repair -> Anti-Spiral; 先回上游，不变成 standalone skill。

#### Wake-Up Probes / 唤醒探针

If the active object is strategic, path-bearing, or structurally ambiguous, do not detour through a familiar high-frequency method first.

- `SELA` wake-up: real local advantage may lose mainline status to system-level cost, scale, distribution, feedback-loop, or automation.
- `MPG` wake-up: a qualified mainline exists, but carrier, vehicle, exposure, timing, liquidity, authority, or trust may fail first.
- `EDSP` wake-up: A/B both look right because proposition, dimensions, boundary, or evaluation axis may be malformed.
- Do not route through `3l5s` when the problem object is already clear and the unresolved work is strategic, path-bearing, or structurally ambiguous.
- Do not let `wae` absorb strategic or structural judgment merely because workflow, agents, scripts, or review appear in the prompt.
- Do not let `wae` absorb ordinary conceptual, organizational, product, or structural boundaries.
- Do not run `tvg` when thinness comes from upstream strategy, structure, or path-carrying judgment.
- Do not route to `tvg` merely because the user asks for an audit, review, or check. No active TVG loop, no TVG audit.

#### Context Injection Point / 上下文注入口

Mindthus may receive `user_preference`, `long_term_objective`, `risk_posture`, `authority_boundary`. It does not implement memory, storage, retrieval, ranking. Use as constraint; current user input takes priority and must not silently override current instruction.

#### Judgment Constraint Recognition / 判断约束识别

Facts and evidence constrain factual claims. Values and preferences constrain priorities. Interests and incentives constrain stakeholder interpretation. Emotional signals constrain attention, trust, or caution. Risk posture and reversibility constrain action strength. Authority boundaries constrain who may decide. do not let values or emotion assert factual claims.

#### Pressure Surface Check / 施压面检查

Pressure is not a standalone route. Skip low-risk deterministic work. Perspective Pressure handles single-view, incentive, or game-theoretic risk. SELA and EDSP own role pressure. MPG owns qualified-mainline path volatility. TVG owns bounded-artifact value pressure. Evidence / Claim Ceiling owns proof limits. Anti-Spiral owns repeated local repair pressure. When used, name owner, reason, and execution effect.

#### Expression Discipline / 表达纪律

Approximate Quantified Mapping / 非精准量化显影 can be used inside an existing judgment owner. The active method keeps decision authority and does not become the judgment owner. Use it only when the relationship is complex enough. Numbers are hypothetical numbers, not factual measurements; expose variables, directions, dominant terms, sensitivity points, and definition gaps. do not compute decisions; skip it for simple adjectives when plain language is enough.

#### Method Arbitration / 方法仲裁

方法冲突时不要默认堆叠，选：`dominate`、`defer`、`degrade`、`block`、`stop`。Checks: TVG vs Anti-Spiral, SELA vs WAE, EDSP vs evidence, 3L5S vs direct execution, MPG vs AQM. SELA identifies direction; MPG carries it through path volatility. MPG owns the judgment; Approximate Quantified Mapping only makes variables visible.

#### Execution Impact / 执行影响

Mindthus 判断必须改变下游动作：strategy, risk handling, evidence requirement, next action, stopping condition, method choice, or handoff packet. If a judgment changes none of these, return to direct execution, information acquisition, clarification, or sharper routing.

#### `sela`

战略方向：检查局部优势是否遮住系统级费效比，避免短视选择。

#### `mpg`

MPG / Mainline-Path Game 把已限定主线转成 Path-Carrying Strategy / 主线承载方案，用于主线存在但路径受对抗力量、载体、暴露和时机塑形。

#### `3l5s`

问题还不清楚时，用 Discovery -> Definition 收敛问题；问题过大时，拆成可验证任务。

#### `tplan`

Mission runtime: durable task state, human-in-loop authority, evidence tracking, decision hooks.

#### `edsp`

当 A/B 都像对、命题有问题、边界不清或趋势难判时，用 Extreme Deduction 建坐标。

#### `wae`

处理 agentic systems 内 Workflow / Agentic / Evidence 的控制权；不是所有边界、责任、流程或证据问题都进入 WAE。

#### `tvg`

处理结构完整但实质浅薄的 AI bounded artifact。TVG audit 是 TVG-loop exit judgment，不是 generic external audit route。No bounded artifact value-gain target, no TVG。

## Guardrails / 从属补漏

### Cognitive Primitive References / 认知原语引用

认知原语在 `docs/methodologies/shared-primitives.md`。本入口只选主方法，不复制完整定义。

### Anti-Spiral Entry / 反螺旋入口

同一局部对象第三次、用户反馈变差、只想加层或同路径继续无新证据时，先停下做 Anti-Spiral。它不是 independent skill。见 `docs/methodologies/anti-spiral-self-audit.md`；在 `tplan` Mission 中作 runtime gate。

### Fidelity Support

Use fidelity contract `resources/fidelity-contract.md`, `templates/fidelity-output.json`, and `scripts/validate_using_mindthus_output.py`; validation is not semantic approval.

## Boundaries / 边界

- Premise Calibration 不替代证据、领域研究或运行时验证。
- Mindthus skills 不需要串成固定流程；脚本、模板、结构化输出只能辅助判断，不能替代判断。

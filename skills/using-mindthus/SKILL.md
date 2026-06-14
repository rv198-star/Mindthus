---
name: using-mindthus
description: Use when choosing Mindthus skills including SELA, MPG, 3L5S, TPLAN, EDSP, WAE, and TVG.
---

# Using Mindthus

## Core Claim / 核心判断

> 遇事不要慌，先搞清楚情况再说。

先判断问题类型，选最小充分镜头：问题不清先补，事实不足取证，有 hard judgment point 才进方法。

## Mainline / 主路径

### 前置校准 / Premise Calibration

Premise Calibration / 前置校准 是选 skill 前的轻量去壳动作，不是独立方法论。它只帮助选择具体方法。

当输入被二手概念、流行词、方法名、战略口号或模糊评价词包住时，先问：真实对象是什么？底层约束是什么？目标函数是什么？缺的是事实、判断、控制权，还是产物价值厚度？

### 最小充分镜头 / Minimal Sufficient Lens

先尊重用户给出的目标函数；若用户未给出，才保守推断，默认效率优先。用户给出质量、安全、审美、可解释性或长期维护时，以用户目标为准。

选择方法时用最小充分镜头：不要为了形式跑完整方法；能直接判断就直接判断；一个 skill 足够就不要串联。见 `docs/methodologies/shared-primitives.md`。

### Skill 路由

#### Intervention Boundary / 介入边界

- Direct execution / 直接执行: clear, low-risk, bounded, facts sufficient; do not use Mindthus.
- Information acquisition / 信息补全: facts, files, data, runtime proof, or user clarification 缺失时先补输入。
- Mindthus intervention / Mindthus 介入: 出现 hard judgment point，如问题定义不清、结构歧义、趋势/时机取舍、path/counter-force volatility、控制边界错配、bounded artifact 价值薄、Mission-runtime drift 或 repeated local repair。

#### Context Sufficiency Check / 信息面充分性检查

当前可见输入不足以支撑强判断时，先补事实或降级；可能改变方向时停止强判断，并说明缺什么、怎么补、不补时结论上限。

#### Judgment Object Routing / 判断对象路由

- Problem-definition failure -> `3l5s`; 清楚低风险任务直接执行。
- False binary or structural ambiguity -> `edsp`; 缺 facts/domain/runtime/stakeholder judgment 先补证据。
- Long-term system efficiency versus local advantage -> `sela`; 长期方向不等于即时行动。
- Qualified mainline with path/counter-force exposure -> `mpg`; Do not use MPG when there is no actor, carrier, exposure, or path decision.
- Control-boundary mismatch -> `wae`; 低风险确定性工作直接做。
- Bounded artifact with thin practical value -> `tvg`; TVG requires a bounded artifact; do not proactively activate it for vague dissatisfaction or ordinary writing quality.
- Mission runtime state, evidence, continuation, or stopping problem -> `tplan`; tplan requires Mission-level runtime state; ordinary complexity is not enough; do not proactively activate.
- Repeated local repair -> Anti-Spiral; 先回上游，不变成 standalone skill。

#### Context Injection Point / 上下文注入口

Mindthus may receive `user_preference`, `long_term_objective`, `risk_posture`, `authority_boundary`, role, prior experience, or fresh context; it does not implement memory, storage, retrieval, ranking, or profile management.

Use injected context only as signal or constraint. current user input takes priority and must not silently override current instruction.

#### Judgment Constraint Recognition / 判断约束识别

- Facts and evidence constrain factual claims.
- Values and preferences constrain priorities.
- Interests and incentives constrain stakeholder interpretation.
- Emotional signals constrain attention, trust, or caution.
- Risk posture and reversibility constrain action strength.
- Authority boundaries constrain who may decide.

do not let values or emotion assert factual claims. 冲突时先说明冲突，再选 route 或行动。

#### Pressure Surface Check / 施压面检查

Pressure is not a standalone route. Skip clear, low-risk deterministic, reversible, or mechanically verifiable work.

Pressure owners: Perspective Pressure handles single-view, incentive, or game-theoretic judgment risk. SELA and EDSP own role pressure. MPG owns qualified-mainline path volatility. TVG owns bounded-artifact value pressure. Evidence / Claim Ceiling owns proof limits. Anti-Spiral owns repeated local repair pressure.

When used, name owner, reason, and execution effect. If it changes no strategy, risk handling, evidence requirement, next action, stopping condition, method choice, or handoff packet, skip.

#### Expression Discipline / 表达纪律

Approximate Quantified Mapping / 非精准量化显影 can be used inside an existing judgment owner as a clarity aid. The active method keeps decision authority and does not become the judgment owner.

Use it only when the relationship is complex enough. The numbers are hypothetical numbers, not factual measurements; expose variables, directions, dominant terms, sensitivity points, and definition gaps. do not compute decisions; skip it for simple adjectives, single-variable claims, and low-stakes explanations where plain language is enough.

#### Method Arbitration / 方法仲裁

方法冲突时不要默认堆叠，选：`dominate` 主方法接管；`defer` 等前置判断；`degrade` 降低结论强度；`block` 阻断过强结论；`stop` 回到直接执行、补事实、问用户或交接。

Common checks: TVG vs Anti-Spiral blocks local repair; SELA vs MPG: SELA identifies direction; MPG carries it through path volatility. MPG vs AQM: MPG owns the judgment; Approximate Quantified Mapping only makes variables visible. SELA vs WAE can block action; EDSP vs evidence can degrade confidence; 3L5S vs direct execution skips method when clear.

#### Execution Impact / 执行影响

Mindthus 判断必须改变 strategy, risk handling, evidence requirement, next action, stopping condition, method choice, or handoff packet. If a judgment changes none of these, stop or reroute.

#### `sela`

用于战略方向，检查局部优势是否遮住系统级费效比，避免短视选择。

#### `mpg`

MPG / Mainline-Path Game 把已限定主线转成 Path-Carrying Strategy / 主线承载方案，用于主线存在但路径受对抗力量、载体、暴露和时机塑形。

#### `3l5s`

通用问题处理内核。问题还不清楚时，用 Discovery -> Definition 收敛问题；问题已清楚但过大时，拆成可验证任务。

#### `tplan`

Mission runtime. Use when a Mission needs durable task state, parent-attached additions, Mission-relative selection/subtraction, human-in-loop authority, evidence tracking, or decision hooks.

#### `edsp`

当 A/B 都像对、命题有问题、边界不清或趋势难判时，用 Extreme Deduction 建坐标，再做 Scenario Projection。

#### `wae`

处理 Workflow / Agentic / Evidence 的控制权：流程控制、agent 判断，还是证据约束。

#### `tvg`

处理 AI 产物结构完整但实质浅薄的问题；对象是缺证据、取舍、失败路径、边界或下游可用性的 bounded artifact。

## Guardrails / 从属补漏

### Cognitive Primitive References / 认知原语引用

认知原语在 `docs/methodologies/shared-primitives.md`。本入口只选主方法，不复制完整定义。

### Anti-Spiral Entry / 反螺旋入口

同一局部对象第三次、用户反馈变差、下一步只想加层，或同路径继续无新证据时，先停下做 Anti-Spiral。它不是 independent skill，而是防止目标函数被局部修补吞掉的刹车。完整协议见 `docs/methodologies/anti-spiral-self-audit.md`；在 `tplan` Mission 中作为 runtime gate。

### Fidelity Support

Use `resources/fidelity-contract.md` as the router fidelity contract. Use `templates/fidelity-output.json` and `scripts/validate_using_mindthus_output.py`; validation is not semantic approval.

## Boundaries / 边界

- Premise Calibration 不替代证据、领域研究或运行时验证。
- Mindthus skills 不需要串成固定流程；脚本、模板、结构化输出只能辅助判断，不能替代判断。

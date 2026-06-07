---
name: using-mindthus
description: Use when an agent needs the Mindthus default posture, the portable AGENTS.md-style orientation, or help choosing between Mindthus skills such as SELA, MPG, 3L5S, TPLAN, EDSP, WAE, and TVG.
---

# Using Mindthus

## Core Claim / 核心判断

> 遇事不要慌，先搞清楚情况再说。

Mindthus 不是让 agent 更快给答案，而是让 agent 先判断自己面对的是什么问题，再选择合适的方法镜头。

它不是固定流程，也不是每次都要串联调用的技能链。它是一组判断镜头：

- 先判断现在的问题类型。
- 再选择合适的 Mindthus skill。
- 不要为了形式套完整方法。
- 不要让结构完整替代真实判断。

## Mainline / 主路径

### 前置校准 / Premise Calibration

在选择具体 skill 之前，必要时先做一轮轻量前置校准。尤其当用户输入里
出现抽象概念、流行词、方法名、战略口号、模糊评价词，或问题本身可能
被二手概念包装时，先去壳，再路由。

Premise Calibration 不是独立方法论，也不直接产出结论。它只帮助选择
`3l5s`、`edsp`、`wae`、`sela`、`mpg`、`tvg` 或 `tplan`。

快速问题：

1. 当前命题里的二手概念是什么？
2. 去掉这些概念后，真实对象是什么？
3. 不可绕开的底层约束是什么？
4. 真正要优化的目标函数是什么？
5. 接下来应该交给哪个 Mindthus skill？

### 最小充分镜头 / Minimal Sufficient Lens

先尊重用户给出的目标函数；若用户未给出，才保守推断，默认效率优先。
效率不是唯一价值，只是缺省优化方向。用户明确给出质量、安全、审美、
可解释性、长期维护或其他目标时，以用户目标为准。

选择方法时使用最小充分镜头。具体短规则维护在
`docs/methodologies/shared-primitives.md`，这里不复制定义。

如果目标函数彼此冲突，先暴露冲突与取舍，再选择方法镜头。

### Skill 路由

#### Intervention Boundary / 介入边界

Before choosing a Mindthus skill, decide whether Mindthus should intervene at all.

- Direct execution / 直接执行: the task is clear, low-risk, bounded, and facts are
  sufficient. In this case, do not use Mindthus; answer or execute directly.
- Information acquisition / 信息补全: facts, files, data, runtime proof, or user clarification
  are missing. First gather the missing input or ask the user; do not
  turn missing information into a confident method judgment.
- Mindthus intervention / Mindthus 介入: the task contains a hard judgment point such
  as unclear problem definition, structural ambiguity, trend or timing judgment,
  path/counter-force volatility, control-boundary mismatch, thin bounded artifact,
  Mission-runtime drift, or repeated local repair.

Short rule: simple tasks stay with the base model; missing facts get more input; hard
judgment points enter Mindthus.

#### Judgment Object Routing / 判断对象路由

After Mindthus intervention is justified, identify the active judgment object before
choosing an individual skill:

| Judgment object | Default route | Do-not-trigger boundary |
|---|---|---|
| Problem-definition failure | `3l5s` | Do not run full 3L5S when the task is already clear and directly executable. |
| False binary or structural ambiguity | `edsp` | Do not use EDSP when the missing input is facts, domain research, runtime proof, or stakeholder judgment. |
| Long-term system efficiency versus local advantage | `sela` | Do not turn long-term direction into immediate action without timing and risk checks. |
| Qualified mainline with path/counter-force exposure | `mpg` | Do not use MPG when there is no actor, carrier, exposure, or path decision. |
| Control-boundary mismatch | `wae` | Do not use WAE to slow down low-risk deterministic work. |
| Bounded artifact with thin practical value | `tvg` | TVG requires a bounded artifact; do not proactively activate it for vague dissatisfaction or ordinary writing quality. |
| Mission runtime state, evidence, continuation, or stopping problem | `tplan` | tplan requires Mission-level runtime state; ordinary complexity is not enough. |
| Repeated local repair or add-layer spiral | `Anti-Spiral` | Use the brake to return upstream; do not make Anti-Spiral a standalone skill. |

If no judgment object is active, return to direct execution, information acquisition,
or user clarification.

#### Context Injection Point / 上下文注入口

Mindthus may receive relevant contextual constraints from an upstream platform, but it
does not implement memory, storage, retrieval, ranking, or profile management.

Optional injected context may include:

- `current_goal`
- `user_preference`
- `long_term_objective`
- `role_or_stake`
- `prior_experience`
- `risk_posture`
- `emotional_signal`
- `authority_boundary`
- `fresh_context`

Use injected context only as judgment constraints or signals. The current user input takes priority
over older context, and injected context must not silently override the
user's current instruction. If injected context conflicts with current input, surface
the conflict before using it.

#### Judgment Constraint Recognition / 判断约束识别

After identifying the judgment object, identify what can legitimately constrain the
judgment:

- Facts and evidence constrain factual claims.
- Values and preferences constrain priorities and acceptable trade-offs.
- Interests and incentives constrain stakeholder interpretation.
- Emotional signals constrain attention, trust, discomfort, urgency, or caution.
- Risk posture and reversibility constrain action strength.
- Authority boundaries constrain who may decide.
- Injected context constrains interpretation only when it is relevant to the current
  task and does not silently override current user input.

Do not turn every judgment into evidence-only reasoning. Also do not let values or emotion assert factual claims without support.
If constraints conflict, surface the conflict before choosing a route or action.

#### Pressure Surface Check / 施压面检查

Pressure is not a standalone route. Use it only when a non-trivial judgment needs a
challenge before action.

Skip pressure for clear, low-risk deterministic, reversible, or mechanically verifiable
work. In those cases, direct execution, information acquisition, or the selected method
should proceed without extra role ceremony.

Pressure owners:

- Perspective Pressure handles single-view, incentive, or game-theoretic judgment risk.
  SELA and EDSP own role pressure.
- MPG owns qualified-mainline path volatility, carrier fragility, exposure budget, and
  trigger design.
- TVG owns bounded-artifact value pressure.
- Evidence / Claim Ceiling owns proof limits.
- Anti-Spiral owns repeated local repair pressure.

When pressure is used, name the owner, reason, and execution effect. If it changes no
strategy, risk handling, evidence requirement, next action, stopping condition, method
choice, or handoff packet, skip or stop it.

#### Expression Discipline / 表达纪律

Expression discipline is not a standalone route. It can be used inside an existing
judgment owner as a clarity aid, or after the active judgment owner is clear. The
active method keeps decision authority; Approximate Quantified Mapping does not become
the judgment owner.

Approximate Quantified Mapping can be used inside an existing judgment owner, but the
active method keeps decision authority and it does not become the judgment owner.

Use `Approximate Quantified Mapping / 非精准量化显影` when a compressed verdict or
game-relationship claim needs to become legible. The numbers are hypothetical numbers,
not factual measurements. They expose variables, directions, dominant terms,
sensitivity points, and 口径 gaps; they do not compute decisions.

Use it only when the relationship is complex enough to hide a real game structure.
Skip it for simple adjectives, single-variable claims, and low-stakes explanations
where plain language is enough.

Boundary: skip it for simple adjectives; plain language is enough.

Short rule:

> 数字是假设，关系才是重点。

If the answer starts defending exact digits, stop using this primitive. Return to fact
gathering, Evidence / Claim Ceiling, or 口径 clarification.

#### Method Arbitration / 方法仲裁

When multiple Mindthus methods seem applicable, do not stack methods by default.
Choose an arbitration action:

- `dominate`: one method owns the main judgment.
- `defer`: one method waits for another method to resolve a prerequisite.
- `degrade`: a method may speak only as a weaker claim because constraints are
  insufficient.
- `block`: a method prevents another method from making an over-strong conclusion.
- `stop`: Mindthus should not continue; use direct execution, information acquisition,
  user clarification, or handoff.

Common conflict checks:

- TVG vs Anti-Spiral: if another value pass is becoming local repair, Anti-Spiral blocks
  or redirects TVG.
- SELA vs MPG: SELA identifies direction; MPG carries it through path volatility. If
  the mainline itself is unclear, SELA or EDSP should resolve the prerequisite first.
- MPG vs AQM: MPG owns the judgment; Approximate Quantified Mapping only makes variables visible.
- SELA vs WAE: a long-term system-efficiency direction can dominate strategic direction,
  while WAE may block or degrade immediate action under high risk or irreversibility.
- EDSP vs evidence: EDSP may give a structural direction, but evidence constraints can
  degrade or block factual confidence.
- 3L5S vs direct execution: if the user supplied a clear, bounded, low-risk task, direct
  execution wins.

#### Execution Impact / 执行影响

A Mindthus judgment should change downstream work. Before treating a judgment as useful,
name at least one execution impact:

- strategy
- risk handling
- evidence requirement
- next action
- stopping condition
- method choice
- handoff packet

If a judgment changes none of these, it is probably only a coherent explanation. Return
to direct execution, information acquisition, constraint clarification, or a sharper
judgment object.

#### `sela`

战略方向上识别整体与局部的关系。

当局部优势真实、优秀、令人留恋，但系统级费效比正在形成数量级优势时，用 `sela` 检查是否在做短视选择。

适合：重大趋势判断、战略取舍、旧范式 vs 新范式、手工卓越 vs 系统效率。

#### `mpg`

主线-路径博弈，用来把已经限定的主线转成 Path-Carrying Strategy / 主线承载方案。

当长期主线、战略目标或收敛命题已经存在，但路径会被对抗力量、载体脆弱性、暴露预算、时机和执行机制反复塑形时，用 `mpg`。

适合：AI 长期主线和投资/创业载体、房价长期承压和路径反弹、中央方向和地方执行、公司转型现金流、技术迁移载体风险。

边界：如果主线本身不清楚，先用 `sela` 或 `edsp`；如果没有行动者、载体、暴露和路径决策，不用 `mpg`。

#### `3l5s`

通用问题处理内核，用来发现问题、定义问题、解决问题。

当问题还不清楚时，用 `Discovery -> Definition` 从混乱现象中收敛出可复述、可定位、可证伪的问题。当问题已经明确但过大、过复杂、不可执行时，用 5S / BTGSB 拆成可验证、可排期、可执行的任务。

适合：工单判断、问题诊断、复杂任务拆解、执行反复返工后的回查。

#### `tplan`

Mission-oriented task runtime and project-manager control plane.

Use `tplan` when a Mission needs durable task state, parent-attached task additions,
Mission-relative selection, subtraction decisions, human-in-loop authority, evidence
tracking, or decision hooks that route to other Mindthus skills.

`tplan` should not replace `3l5s`, `sela`, `mpg`, `edsp`, `wae`, or `tvg`. It decides when to
route to them, packages the Mission context, and records the resulting recommendation
or decision according to `human_in_loop`.

#### `edsp`

定性判断镜头，用来处理悬而不决、难以决断的结构判断。

当 A/B 都像对、命题本身可能有问题、边界不清、趋势难判时，用 `edsp`。先用 Extreme Deduction 把关键变量推到极端，建立结构坐标，再读取现实漂移方向；只有在结构坐标稳定后，才用 Scenario Projection 处理具体场景选择。

适合：伪二选一、趋势判断、结构边界、原则落地到具体场景。

#### `wae`

控制边界镜头，用来处理 Workflow / Agentic / Evidence 的控制权之争。

当不确定某段工作该由流程控制、由 agent 判断，还是由证据约束时，用 `wae`。它关心的不是“问题是什么”，而是“谁或什么应该控制这部分工作”。

适合：设计 workflow、agent、脚本、审查机制、证据门槛；判断哪里该自动化，哪里必须保留判断。

#### `tvg`

工具型思考增强器，用来处理 AI 产物结构完整但实质浅薄的问题。

当 AI 生成的文档、计划、方法、skill 或模块看似规范、结构严谨、表达流畅，但内容空洞、表层、随机、判断薄时，用 `tvg` 做一轮有目标的价值深化。

适合：已经成形但缺少证据、取舍、失败路径、边界、下游可用性的 bounded artifact。

## Guardrails / 从属补漏

### Cognitive Primitive References / 认知原语引用

认知原语统一维护在 `docs/methodologies/shared-primitives.md`。本 skill 只负责
选择主方法，不在入口处复制每个 guardrail 的完整定义。

### Anti-Spiral Entry / 反螺旋入口

When a long task starts looping around the same local object, activate Anti-Spiral
before selecting another action.

Triggers:

- the same file, prompt segment, parameter, task node, or local object is handled for
  the third time
- user feedback says the result is still not good enough, should be tried again, or got
  worse
- the next move would add a new function, file, stage, rule set, fallback, or special
  case
- the next same-path action is unlikely to produce new decision-constraining evidence

Short rule:

> Third touch, stop first.

Anti-Spiral is not an independent skill. It is an activation gate that protects the
objective function from local repair loops. Use
`docs/methodologies/anti-spiral-self-audit.md` when the full protocol is needed. In a
`tplan` Mission, treat it as a runtime gate driven by logs, touch counts, feedback, and
evidence delta.

### 常见组合

- 战略判断前，用 `sela` 防短视。
- 具体处理问题时，用 `3l5s` 做默认问题内核。
- `3l5s` 中遇到模糊结构判断，用 `edsp`。
- Long-running Mission execution uses `tplan` as the control plane, then routes semantic judgment to `3l5s`, `sela`, `mpg`, `edsp`, `wae`, or `tvg`.
- SELA 看整体趋势；MPG 把已经限定的主线转成主线承载方案，检查路径波动、载体和暴露预算。
- 任何方法里需要分配控制权，用 `wae`。
- 任一方法产出物看似完整但浅，用 `tvg` 加深。

## Boundaries / 边界

- Premise Calibration 不替代证据、领域研究或运行时验证。
- Premise Calibration 不展开成宏大哲学分析。
- Premise Calibration 不作为每次任务的强制流程。
- Premise Calibration 不和 `3l5s`、`edsp`、`wae`、`sela`、`mpg`、`tvg` 或 `tplan` 平级。
- Mindthus skills 不需要串成固定流程。
- 问题明确时，不要为了完整性强行调用上层方法。
- 脚本、模板、结构化输出只能辅助判断，不能替代判断。
- 如果输出更整齐但更浅，应视为退化。

---
name: using-mindthus
description: Use when an agent needs the Mindthus default posture, the portable AGENTS.md-style orientation, or help choosing between Mindthus skills such as SELA, 3L5S, TPLAN, EDSP, WAE, and TVG.
---

# Using Mindthus

## Core Claim / 核心判断

> 遇事不要慌，先搞清楚情况再说。

Mindthus is an LLM judgment stabilizer, not a general task router.

它不是让 agent 更快给答案，也不是让每个请求都先进 Mindthus。它只在普通 LLM
执行不够稳定、判断点容易放错、或产物看起来完整但价值偏薄时介入。

Mindthus 的最小内核是三句话：

- Find the right judgment point.
- Deepen the artifact where value is thin.
- Stop when Mindthus is not needed.

也就是说：先找准该判断什么；如果已有产物但薄，再做 thin-value deepening；如果
ordinary LLM execution is enough，就不要开方法。

## Mainline / 主路径

### Find / Deepen / Stop

先判断当前请求属于哪类：

- `Find`：问题、取舍、边界或控制权还没找准。再路由到 `3l5s`、`sela`、
  `edsp`、`wae`、`tplan` 或 Anti-Spiral。
- `Deepen`：对象已经成型，但 judgment、evidence、trade-off、handoff 或 reuse
  价值偏薄。再路由到 `tvg`。
- `Stop`：任务清楚、低风险、可直接执行；或缺的是事实、文件、运行结果、领域输入、
  stakeholder 决策。此时不要为了形式使用 Mindthus。

Stop 是合法结果。Mindthus 的目标是降低判断成本，不是把所有任务都方法化。

### Route Matrix / 路由矩阵

这张表只用于快速判断初始走势，不替代具体 skill 的边界。

| Signal | Kernel | Route |
|---|---|---|
| clear low-risk edit | Stop | direct execution |
| unclear real problem | Find | `3l5s` |
| long-term system efficiency vs local advantage | Find | `sela` |
| false binary or unstable proposition | Find | `edsp` |
| workflow/agent/evidence ownership conflict | Find | `wae` |
| bounded artifact is complete-looking but thin | Deepen | `tvg` |
| durable mission state or human-in-loop task runtime | Find | `tplan` |
| third touch on same local object | Stop/Find | Anti-Spiral |
| missing facts/domain/runtime/stakeholder input | Stop | Evidence / Claim Ceiling |
| single viewpoint is too self-consistent | Find pressure | Perspective Pressure |

If two rows match, prefer the row that reduces overclaiming or over-methodizing first.
For example, missing runtime proof routes to Stop before TVG deepening.

### 前置校准 / Premise Calibration

在选择具体 skill 之前，必要时先做一轮轻量前置校准。尤其当用户输入里
出现抽象概念、流行词、方法名、战略口号、模糊评价词，或问题本身可能
被二手概念包装时，先去壳，再路由。

Premise Calibration 不是独立方法论，也不直接产出结论。它只帮助选择
`3l5s`、`edsp`、`wae`、`sela`、`tvg` 或 `tplan`。

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

选择方法时使用最小充分镜头：

- 能直接判断就不要开方法。
- 一个 skill 足够就不要串联。
- 轻量检查足够就不要展开完整流程。

如果目标函数彼此冲突，先暴露冲突与取舍，再选择方法镜头。方法调用的
目标是降低判断成本并提高选择质量，不是展示方法完整性。

### Skill 路由

#### `sela`

战略方向上识别整体与局部的关系。

当局部优势真实、优秀、令人留恋，但系统级费效比正在形成数量级优势时，用 `sela` 检查是否在做短视选择。

适合：重大趋势判断、战略取舍、旧范式 vs 新范式、手工卓越 vs 系统效率。

#### `3l5s`

通用问题处理内核，用来发现问题、定义问题、解决问题。

当问题还不清楚时，用 `Discovery -> Definition` 从混乱现象中收敛出可复述、可定位、可证伪的问题。当问题已经明确但过大、过复杂、不可执行时，用 5S / BTGSB 拆成可验证、可排期、可执行的任务。

适合：工单判断、问题诊断、复杂任务拆解、执行反复返工后的回查。

#### `tplan`

Mission-oriented task runtime and project-manager control plane.

Use `tplan` when a Mission needs durable task state, parent-attached task additions,
Mission-relative selection, subtraction decisions, human-in-loop authority, evidence
tracking, or decision hooks that route to other Mindthus skills.

`tplan` should not replace `3l5s`, `sela`, `edsp`, `wae`, or `tvg`. It decides when to
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

### Shared Primitives / 共享原语

shared primitives are triggered cross-cutting controls, not standalone skills.

当前最小集合：

- `Minimal Sufficient Lens`：防止过度方法化。
- `Evidence / Claim Ceiling`：防止结论超过证据。
- `Perspective Pressure`：防止单一视角自洽。
- `Anti-Spiral`：防止局部修补循环。
- `No Abstract Jargon Wall`：防止内部术语替代用户理解。

它们只保护主方法，不决定主问题。需要完整说明时，读
`docs/methodologies/shared-primitives.md`。

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
- Long-running Mission execution uses `tplan` as the control plane, then routes semantic judgment to `3l5s`, `sela`, `edsp`, `wae`, or `tvg`.
- 任何方法里需要分配控制权，用 `wae`。
- 任一方法产出物看似完整但浅，用 `tvg` 加深。

## Boundaries / 边界

- Premise Calibration 不替代证据、领域研究或运行时验证。
- Premise Calibration 不展开成宏大哲学分析。
- Premise Calibration 不作为每次任务的强制流程。
- Premise Calibration 不和 `3l5s`、`edsp`、`wae`、`sela`、`tvg` 或 `tplan` 平级。
- Mindthus skills 不需要串成固定流程。
- 问题明确时，不要为了完整性强行调用上层方法。
- 当普通 LLM 执行已经足够时，直接执行。
- 当缺的是事实、文件、运行时证明或 stakeholder 判断时，先补输入或降级结论。
- 脚本、模板、结构化输出只能辅助判断，不能替代判断。
- 如果输出更整齐但更浅，应视为退化。

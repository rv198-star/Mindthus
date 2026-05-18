---
name: using-mindthus
description: Use when an agent needs the Mindthus default posture, the portable AGENTS.md-style orientation, or help choosing between Mindthus skills such as SELA, 3L5S, TPLAN, EDSP, WAE, and TVG.
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
- 脚本、模板、结构化输出只能辅助判断，不能替代判断。
- 如果输出更整齐但更浅，应视为退化。

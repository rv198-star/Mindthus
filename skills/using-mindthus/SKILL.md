---
name: using-mindthus
description: Use when an agent needs the Mindthus default posture, the portable AGENTS.md-style orientation, or help choosing between Mindthus skills such as SELA, 3L5S, TPLAN, EDSP, WAE, and TVG.
---

# Using Mindthus

## 默认姿态

> 遇事不要慌，先搞清楚情况再说。

Mindthus 不是让 agent 更快给答案，而是让 agent 先判断自己面对的是什么问题，再选择合适的方法镜头。

它不是固定流程，也不是每次都要串联调用的技能链。它是一组判断镜头：

- 先判断现在的问题类型。
- 再选择合适的 Mindthus skill。
- 不要为了形式套完整方法。
- 不要让结构完整替代真实判断。

## Skill 路由

### `sela`

战略方向上识别整体与局部的关系。

当局部优势真实、优秀、令人留恋，但系统级费效比正在形成数量级优势时，用 `sela` 检查是否在做短视选择。

适合：重大趋势判断、战略取舍、旧范式 vs 新范式、手工卓越 vs 系统效率。

### `3l5s`

通用问题处理内核，用来发现问题、定义问题、解决问题。

当问题还不清楚时，用 `Discovery -> Definition` 从混乱现象中收敛出可复述、可定位、可证伪的问题。当问题已经明确但过大、过复杂、不可执行时，用 5S / BTGSB 拆成可验证、可排期、可执行的任务。

适合：工单判断、问题诊断、复杂任务拆解、执行反复返工后的回查。

### `tplan`

Mission-oriented task runtime and project-manager control plane.

Use `tplan` when a Mission needs durable task state, parent-attached task additions,
Mission-relative selection, subtraction decisions, human-in-loop authority, evidence
tracking, or decision hooks that route to other Mindthus skills.

`tplan` should not replace `3l5s`, `sela`, `edsp`, `wae`, or `tvg`. It decides when to
route to them, packages the Mission context, and records the resulting recommendation
or decision according to `human_in_loop`.

### `edsp`

定性判断镜头，用来处理悬而不决、难以决断的结构判断。

当 A/B 都像对、命题本身可能有问题、边界不清、趋势难判时，用 `edsp`。先用 Extreme Deduction 把关键变量推到极端，建立结构坐标，再读取现实漂移方向；只有在结构坐标稳定后，才用 Scenario Projection 处理具体场景选择。

适合：伪二选一、趋势判断、结构边界、原则落地到具体场景。

### `wae`

控制边界镜头，用来处理 Workflow / Agentic / Evidence 的控制权之争。

当不确定某段工作该由流程控制、由 agent 判断，还是由证据约束时，用 `wae`。它关心的不是“问题是什么”，而是“谁或什么应该控制这部分工作”。

适合：设计 workflow、agent、脚本、审查机制、证据门槛；判断哪里该自动化，哪里必须保留判断。

### `tvg`

工具型思考增强器，用来处理 AI 产物结构完整但实质浅薄的问题。

当 AI 生成的文档、计划、方法、skill 或模块看似规范、结构严谨、表达流畅，但内容空洞、表层、随机、判断薄时，用 `tvg` 做一轮有目标的价值深化。

适合：已经成形但缺少证据、取舍、失败路径、边界、下游可用性的 bounded artifact。

## 常见组合

- 战略判断前，用 `sela` 防短视。
- 具体处理问题时，用 `3l5s` 做默认问题内核。
- `3l5s` 中遇到模糊结构判断，用 `edsp`。
- Long-running Mission execution uses `tplan` as the control plane, then routes semantic judgment to `3l5s`, `sela`, `edsp`, `wae`, or `tvg`.
- 任何方法里需要分配控制权，用 `wae`。
- 任一方法产出物看似完整但浅，用 `tvg` 加深。

## 边界

- Mindthus skills 不需要串成固定流程。
- 问题明确时，不要为了完整性强行调用上层方法。
- 脚本、模板、结构化输出只能辅助判断，不能替代判断。
- 如果输出更整齐但更浅，应视为退化。

---
name: using-mindthus
description: Use as the Mindthus router when an agent needs to choose between SELA, 3L5S, EDSP, and WAE from ordinary user language, while routing TVG and tplan only when the user explicitly asks or a workflow clearly routes them.
---

# Using Mindthus

## 默认姿态

> 遇事不要慌，先搞清楚情况再说。

Mindthus 不是固定技能链，也不是让 agent 更快给答案。它先判断问题类型，再选择合适的方法镜头。

使用顺序：

1. 先读用户的普通表达。
2. 找到最像的场景信号。
3. 调用一个最合适的 Mindthus skill。
4. 只有当工作自然需要时，才组合其它 skill。

## Scenario Router

### Passive Auto-Routing / 自动唤起

Only these skills are passively selected from ordinary language:

| User expression / 场景信号 | Default skill | Why | Boundary |
| --- | --- | --- | --- |
| "这个需求越做越乱"、"反复返工"、"问题不清楚"、"任务太大"、"拆完还是不可执行" | `3l5s` | Turn messy signals into falsifiable problems, or break oversized problems into verifiable actions. | Do not use for an obvious one-step action. |
| "两个方案都对"、"边界到底在哪"、"这是伪二选一吗"、"定性判断很难"、"趋势难判" | `edsp` | Push ambiguous variables to extremes, build structural coordinates, then project the real scenario. | Do not replace available evidence or deterministic rules. |
| "旧方案局部优势很强"、"新方案系统效率更高"、"费效比正在变"、"旧范式 vs 新范式" | `sela` | Check whether real local advantage is being overwhelmed by system-level cost-effectiveness. | Do not use mechanically across ethics, irreversible harm, or transition-protection cases. |
| "这里该脚本控制还是 agent 判断"、"证据要不要记录"、"workflow 太重吗"、"agent 会不会漂"、"控制边界不清" | `wae` | Decide whether workflow, agentic judgment, or evidence should control the work. | Do not slow down low-risk deterministic formatting. |

### Manual Or Workflow Routing / 手动或流程路由

These tools are not passively selected from ordinary language. Use them only when the
user names them, or when an existing workflow routes to them.

Workflow routing means an external process, script, upstream hook, or user instruction
explicitly names the tool. The agent must not infer workflow routing from a request
that merely looks suitable for the tool.

| Entry condition / 入口条件 | Tool | Boundary |
| --- | --- | --- |
| 显式要求使用 TVG，或 workflow 明确路由到 TVG 深化有边界产物 | `tvg` | 不是所有文档都需要深化；TVG 不重开整个问题空间；不被普通文档反馈被动唤起；“文档空/判断薄/需要深化”本身不算显式要求使用 TVG。 |
| 显式要求使用 tplan，或 workflow 明确路由到 Mission runtime | `tplan` | `tplan` 不是普通 todo；不因任何 plan 字样自动创建 Mission；不被长期目标表述被动唤起；“长期目标/几十步/切换任务/记录证据/保留任务状态/任务树/恢复现场/自动推进/状态持久化”本身不算显式要求使用 tplan。 |

## 组合方式

- 具体处理问题时，用 `3l5s` 做默认问题内核。
- `3l5s` 中遇到模糊结构判断，用 `edsp`。
- 战略判断前，用 `sela` 防短视。
- 任何方法里需要分配控制权，用 `wae`。
- 显式要求使用 TVG 或 workflow 明确路由时，用 `tvg` 加深有边界的产物。
- 显式要求使用 tplan 或 workflow 明确路由时，用 `tplan` 承载 Mission runtime，再把语义判断路由给其它 Mindthus skills。

## 边界

- 不要为了形式串联所有 skill。
- 不要让结构完整替代真实判断。
- 脚本、模板、结构化输出只能辅助判断，不能替代 judgment。
- 如果输出更整齐但更浅，应视为退化。

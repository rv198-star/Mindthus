---
name: using-mindthus
description: Use as the Mindthus router when an agent needs to choose between SELA, 3L5S, TPLAN, EDSP, WAE, and TVG from ordinary user language, AGENTS.md orientation, or scenario-based trigger signals.
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

| User expression / 场景信号 | Default skill | Why | Boundary |
| --- | --- | --- | --- |
| "这个需求越做越乱"、"反复返工"、"问题不清楚"、"任务太大"、"拆完还是不可执行" | `3l5s` | Turn messy signals into falsifiable problems, or break oversized problems into verifiable actions. | Do not use for an obvious one-step action. |
| "两个方案都对"、"边界到底在哪"、"这是伪二选一吗"、"定性判断很难"、"趋势难判" | `edsp` | Push ambiguous variables to extremes, build structural coordinates, then project the real scenario. | Do not replace available evidence or deterministic rules. |
| "旧方案局部优势很强"、"新方案系统效率更高"、"费效比正在变"、"旧范式 vs 新范式" | `sela` | Check whether real local advantage is being overwhelmed by system-level cost-effectiveness. | Do not use mechanically across ethics, irreversible harm, or transition-protection cases. |
| "这里该脚本控制还是 agent 判断"、"证据要不要记录"、"workflow 太重吗"、"agent 会不会漂"、"控制边界不清" | `wae` | Decide whether workflow, agentic judgment, or evidence should control the work. | Do not slow down low-risk deterministic formatting. |
| "AI 文档很完整但没什么用"、"结构完整但内容空"、"判断薄"、"下游不可用"、"需要深化产物" | `tvg` | Deepen a bounded AI artifact by adding evidence, trade-offs, failure paths, and downstream value. | 不是所有文档都需要深化；TVG 不重开整个问题空间。 |
| "我要跑一个长期目标"、"保留任务状态"、"需要 Mission"、"需要 human-in-loop"、"任务运行时和证据链" | `tplan` | Use a durable Mission runtime for task state, evidence, decision hooks, and resumption. | `tplan` 不是普通 todo；不因任何 plan 字样自动创建 Mission。 |

## 组合方式

- 具体处理问题时，用 `3l5s` 做默认问题内核。
- `3l5s` 中遇到模糊结构判断，用 `edsp`。
- 战略判断前，用 `sela` 防短视。
- 任何方法里需要分配控制权，用 `wae`。
- 任一方法产出物看似完整但浅，用 `tvg` 加深。
- Long-running Mission execution uses `tplan` as the control plane, then routes semantic judgment to other Mindthus skills.

## 边界

- 不要为了形式串联所有 skill。
- 不要让结构完整替代真实判断。
- 脚本、模板、结构化输出只能辅助判断，不能替代 judgment。
- 如果输出更整齐但更浅，应视为退化。

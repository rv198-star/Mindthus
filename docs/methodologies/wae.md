# WAE / Workflow-Agentic-Evidence

## 这是什么

WAE 是一个控制边界方法，意思是 `Workflow / Agentic / Evidence`。

它回答的问题很简单：这部分工作应该由流程控制、由 agent 判断，还是由证据约束。

## 解决什么问题

WAE 处理的是控制权争议，而不是任务内容本身。

典型场景：

- 脚本在决定本应保留给判断的事
- agent 在做本应固定下来的事
- review 在没有证据时就通过了
- schema 让不确定的真相看起来像已经完成

## 核心判断

三层分别负责：

- `Workflow` 负责顺序和机械控制
- `Agentic` 负责不确定性的语义判断
- `Evidence` 负责把说法和可观察事实连起来

先看两条变量：

1. workflow certainty
2. context certainty

再决定边界。

## 怎么用

先做最小检查：

1. 这是 path uncertainty 还是 truth uncertainty
2. 这个 claim 需要什么证据来约束
3. 这件事能不能安全回退，错了会多大

如果这三问已经够用，就别把 WAE 做成一整套仪式。

## 常见误用

- 把 WAE 当成通用流程设计器
- 把结构清洁误当成判断充分
- 用 worksheet 完成度替代真实判断

## 边界

WAE 不该拖慢低风险、低不确定性的格式化工作。

它只处理控制边界，不负责把所有任务都变复杂。

## 与其他方法的关系

- `3L5S` 处理问题发现与落地
- `SELA` 处理长期方向
- `tplan` 处理 Mission 级运行控制
- `Anti-Spiral` 处理局部修补螺旋

## 导航

- 返回 [README](../README.md)
- 查看 [WAE skill](../../skills/wae/SKILL.md)

# tplan

## 这是什么

tplan 是一个 Mission-oriented project manager 和 control plane。

它不是普通待办清单，也不是把任务写得更长的格式工具。
它负责的是：让工作持续挂在一个稳定 Mission 上，避免任务列表漂移。

## 解决什么问题

tplan 主要处理：

- 长任务如何持续推进
- 任务状态如何保存
- 什么时候该继续，什么时候该停
- 谁对什么节点有控制权
- 哪些内容算 evidence，哪些只是 logs

## 核心判断

tplan 关心的是 runtime state、order、authority 和 validation。

它把语义判断路由给其他方法：

- `3L5S` 负责问题定义和拆解
- `SELA` 负责 Mission 级压力下的取舍
- `EDSP` 负责模糊结构选择
- `WAE` 负责控制边界
- `TVG` 负责成品深度审计

## 怎么用

基本运行顺序是：

1. 初始化 Mission
2. 用 `3L5S` 提建议任务结构
3. 用脚本增删节点
4. 记录 step logs 和 evidence
5. 需要时输出 stop report
6. 用 decision packet 和 hook 做选择

## 常见误用

- 把 tplan 当语义推理引擎
- 把 logs 当 evidence
- 把结构完整当成已经解决问题

## 边界

tplan 不决定 semantic truth。

它只验证形状、状态合法性、authority 和 evidence 关系。

## 与其他方法的关系

- `Anti-Spiral` 是 tplan 可吸收的运行时 brake
- `WAE` 解释为什么脚本、证据和判断要分开
- `SELA` 负责 Mission 级减法与资源压力判断

## 导航

- 返回 [README](../README.md)
- 查看 [tplan skill](../../skills/tplan/SKILL.md)

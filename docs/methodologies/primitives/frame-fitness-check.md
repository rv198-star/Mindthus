# Frame Fitness Check / 定框适配检查

## Core

检查当前局部框架是否能服务用户实际目标。只在 frame-risk 且会改变行动时介入；
框架可以来自用户、Agent 第一反应、熟悉方法、测试或文档。

## Mainline

先明确对象、目标及真正约束。局部解释足够就 preserve；只覆盖部分就 qualify；
层级/对象错了就 reframe；缺证据就 block pending evidence。
保留局部真实，说明改变的主次和行动，不替用户改写合法价值/审美/风险姿态。
没有可定位的风险或执行影响就省略检查。Original Prompt Contract 是约束，
不能控制整体判断；不是无条件默认反对用户。

## Guardrail

保护输入层级，不替代事实补全、方法判断或用户授权。
关键词、强情绪或框架标签不证明偏见；不足的输入仍是 unknown。

## Runtime support

需要调试、审阅或交接时可记录 `frame_status` 与 `routing_decision`：
clean/biased/overloaded/malformed；preserve/qualify/reframe/block pending evidence。
五步展开与更细字段只在歧义仍未解除时使用，不作每次输入的固定流程。
[Whole Elephant](whole-elephant-protocol.md) 检查局部真相定义权；
[共享原语](../shared-primitives.md) 提供其他条件约束。

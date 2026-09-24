# #211 当前 Codex A/B/C：首个开发输入 B2

状态：首个小批已执行；这是**已暴露的开发观察**，不是 #211 正式保留集或三臂资格成绩。执行前协议见 [PLAN.md](PLAN.md)，精确输入与接受性质见 [cases.json](cases.json)，机器记录见 [observation.json](observation.json)。外部根目录 `/Users/william/Documents/Codex/2026-09-24/mindthus-abc-current-codex-v1` 的 49 个原始记录已逐字复制，SHA-256 见 [证据索引](evidence-20260924/evidence-index.json)。冻结摘要 `726b2270e8e5227413027900d5dfcfca08f7b779c26adf66003709c6943b6e11`；来源提交 `4747fb1e6`。

## 工程结果

- 新 B2 输入经当前 `route-control.v0.2.1` 编译出四题 M02/M03/S01/S02；B/C 分别使用同一合同与政策、独立 episode。准入身份和冻结复验通过；无旧请求重发、无技术重试，旧账本与 `main` 未改。
- B 的实验专用 Codex CLI 适配保留完整原始回答与用量，给现有 `entry.run` 提供四题结果；不向生产 Provider 增加 CPA 或 OpenRouter 依赖。C 继续走原 TypeSafe 适配和当前 Agent 入口。
- C 的 Score 返回合同错误仅隔离 S02，其他三题和供应商用量保留。这验证了修复后的错误传播边界，不能当成 TVG 路由通过。
- Codex CLI 初始化时曾顺着 A 的实验技能目录符号链接，在仓库生成未跟踪的 `skills/.system`。发现后将该实验目录换成仓库外、技能文件字节相同的副本，只清理本轮生成的目录；未改正式技能、旧证据或冻结记录。

## 真实模型结果

| 臂 | 判断调用 | 关键观察 | 型号证据 |
| --- | --- | --- | --- |
| A 当前非 Jev Codex | 无局部判断调用；一次 Codex 任务 | 直接写出备忘录；未观察到 skill 文件载入或激活 | CLI 请求 `gpt-6-sol`，服务端型号未单独回证 |
| B 同图普通 LLM | 一次 Codex CLI 四题调用 | TVG 适用度 0.04、作用 `no_contribution`；路由 `no_established_primary` | CLI 请求 `gpt-6-sol`，服务端型号未单独回证 |
| C 同图 Jev | 一次官方 TypeSafe 四题调用 | TVG 适用度 0.24、作用 `support`；S02 Score 合同错误；路由 `applicability_role_unresolved` 且无主方法 | 返回确认 `jev-1.13.0` |

Codex CLI 共四次（A 一次、B 判断与回退各一次、C 回退一次），TypeSafe 一次，CPA/OpenRouter 均零次。C 的供应商用量为 4,804 输入 / 139 输出 token，金额未返回。Codex CLI 报告 A 为 15,454 / 383，B 两次合计 33,658 / 395，C 回退为 14,805 / 209。所有臂实际金额未知；不同模型的 token 不能直接换算成费用。各调用耗时及原始响应在证据索引中。

## 宿主消费

B/C 均未形成约束式执行 handoff，现有 Episode 的执行计数为零。两臂随后各由独立 Codex CLI 会话按原任务写出一份**回退产物**，不是 `CurrentAgentHost` 对已提交路由的消费，也不计入 ② 约束式通过。A 是独立非 Jev 任务产物。三份文本分别见原始记录 `codex-calls/B2-A-baseline/last-message.txt`、`B2-B-delegated-host/last-message.txt`、`B2-C-delegated-host/last-message.txt`。

## 对照结论与边界

按执行前列明的四项必要性质与三项严重错误，作者复核三份备忘录均 `usable`、未见严重错误：均没有虚构效果数字，都保留“两例人工改派”与未知误派率的区别，并提出暂缓扩大及补齐指标、预算、培训和回退条件。在这个输入上**未观察到 B/C 相对 A 的任务质量增益**；B/C 只增加判断调用，且最终仍回退给宿主。单次调用时长和 token 可以列账，金额与全流程成本收益仍未定。

本输入不是独立保留集，也没有触发实际方法执行。A 仅证明原生 skill 目录已挂载及普通 Codex 任务完成，未观察到 skill 激活；B 的主观 Noul 数值未校准，CLI 返回没有独立服务端型号证明。因此不能报告正式 A/B/C 非劣、成本优胜或 #211 通过。后续应先用**另一个预冻结的硬判断开发输入**验证一次真实 Jev→当前 Codex 的约束式消费，再对独立保留任务冻结质量、成本与停止门槛；本 B2 不再重跑追分。

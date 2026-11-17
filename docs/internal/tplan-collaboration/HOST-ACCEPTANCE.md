# Issue #246 / 真实三会话宿主验收：PASS

完成日期：2026-11-18，Asia/Shanghai。工程代码：`223b7d2b99969c6a6ee9549730d2b8a2271d2401`；宿主验收起点（含 R5 审计）：`54c0185cbf0f364c3a21ea285dd496c22de570c6`。

## Core / 结论

**普通同账户 A/B/C 真实闭环通过。** B 实际交付、C 独立发现合同失败、B 自主完整返修、C 对新固定成果独立复审通过，A 依据当前证据采用并通过正常 TPlan Mission Review 收口。

A 原目标、职责及验收保持，3 项任务全部完成，未决回报与当前验收缺口均为零。只有 A 使用 TPlan；B/C 通过普通工作说明和回复参与。用户无需模式口令。

本次使用真实会话与受控小样本，类别为 `live_host_bounded_canary_exercise`。初始 legacy canary 和首轮发送结果丢失为明确注入的测试故障；模型渠道失败及 R2 原生历史短暂延迟为实际宿主事件。[证据包](reviews/host-live/README.md) 保留来源、动作和状态。

## Mainline / 实际闭环

| 阶段 | 实际动作和结果 |
| --- | --- |
| A 准备 | 用户在工程审计通过后批准宿主验收。A 建立 Mission 和稳定发送意图，保留自己的合同/证据任务 T2。 |
| B 首批 | 普通 B 原样封装故障 canary，返回文件、摘要和 1 项正常 smoke；A 核对并冻结 R1。 |
| C 独立审查 | 对固定 R1 实跑 337 例，186 通过、151 失败，给出六类可复现发现和完整返修要求。 |
| A 处置 | 记录绑定 R1 的 C FAIL 和 ART 失败，不采用旧成果；完整要求一次交回 B，A 保持设计/证据职责。 |
| B 自主返修 | 独立替换真值验证根因，完成完整合同实现、自测和自审；381 项回归通过，A 独立重跑通过后冻结六文件 R2。 |
| C 新版复审 | 对固定 D2/R2 实跑 443 例全部通过；原 337 项输入/期望完全保留，原 151 项失败均修复，另加 106 项边界。 |
| A 收口 | 仅采用 D2/R2，保留 D1/R1 FAIL 历史；从完成的 T2 转向自己的 T3 最终宿主验收，正常关闭 Mission。 |

381 项随包回归与 C 的 443 项独立检查有重叠，分别记录。当前采用摘要：`sha256:feaa037f61e6b97c7cbb7e03cad8de0f29c2b902db0cb3db231c8f925d752f14`。

## Mainline / 目标和责任保持

A 每次读取真实回报后才决定记录、返修、采用和下一动作。B 负责实现、自测及普通异常，C 负责独立审查，A 负责合同、证据适用性和最终验收。A 没有接管实现排错。

[原始目标](reviews/host-live/audit/goal-baseline.json) 与 [最终状态](reviews/host-live/audit/final-summary.json) 的目标及验收一致。[动作记录](reviews/host-live/audit/host-events.jsonl) 保留请求、结果与前后状态。焦点从 A 自己的 T2 转向 A 自己的 T3 有明确完成依据。四个实际 B/C 轮次的 41 条原生命令中，未观察到总 Mission 或 TPlan API 的直接使用；见 [参与者操作核对](reviews/host-live/audit/peer-access-observations.json)。

运行时拒绝了一次错误 evidence_refs 写入并保持原状态；A 修正调用引用后继续。收口前 Pulse 路由至 Mission Review，A 验证实际关闭决定，所有成功关键任务与合格验收满足后才 completed。

## Runtime support / 实际会话与模型

| 角色 | 会话 | 本阶段实际模型记录 |
| --- | --- | --- |
| A | 当前源会话 `01a1e806-292f-76d0-af7e-f4786d70b3e1` | 持续负责目标和验收 |
| B | `Mindthus #246｜协同目标保持开发`，`01a1e873-14df-76b0-bead-411483962104` | 保留会话当前设置；R1/R2 的 native turn_context 为 `auto/gpt-6.1-sol` / `xhigh` |
| C | `Mindthus #246｜宿主验收 C`，`01a1ea10-30b5-7af3-8f00-0c6b4dca2daa` | R1/R2 实际执行均为 `auto/gpt-6.1-sol` / `high` |

C 初次继承默认 Qwen 4 Max，运行中的 Sol 追加消息没有替换在途请求，旧轮次后来报商汤渠道连接错误。旧轮次结束后，显式 Sol/high 新轮次开始执行；A 从实际 turn_context 和工具动作核验后纠正了先前过早的“已切换”报告。[实际恢复记录](reviews/host-live/audit/actual-sol-model-recovery.json) 和 [R2 模型记录](reviews/host-live/audit/c-r2-actual-model.json) 留存依据，后续复审显式设置同一模型。

## Guardrail / 宿主能力层级

本节保护普通三会话路径：能力按实际观测记录，角色声明不升级为保护性身份或存储权限。

| 能力 | 实测状态及使用规则 |
| --- | --- |
| 发送、唤醒、回传、查询 | 真实 native thread/turn/input/return 引用可核对，普通 B/C 可完成独立工作并回传。 |
| 来源与版本关联 | A 核对指定会话、轮次、合同、固定文件摘要和审查范围，再录入 C 结论。 |
| 发送未知 | 一次真实发送被受控隐藏结果，A 查目标确认原消息、发送次数保持 1；R2 遇到实际历史索引延迟时也保留未知意图，看到原输入后才确认。 |
| 重复回报导入 | 同一真实 B 回报再次导入仍为同一 feedback、一次业务效果。宿主 send 没有暴露幂等键，发送端采用稳定意图和原会话对账。 |
| 取消 | 当前 MCP 工具面未提供 stop/interrupt，本轮未执行真实取消。公开 Codex 协议的独立 interrupt 传输未在本次连接验证。 |
| A→A 写入者隔离 | 合作性代次校验沿工程回归验证；同账户普通会话未提供按线程的物理存储隔离或受保护身份，此类要求沿 H1/宿主权限接入。 |

完整 [能力矩阵](reviews/host-live/audit/host-capabilities.json) 保留可用层级和证据引用。

## Runtime support / 复核与归档

- [C 首轮报告](reviews/host-live/c-out/r1/HOST_REVIEW_R1.md)、[C 新版复审](reviews/host-live/c-out/r2/HOST_REVIEW_R2.md)、[443 例结果](reviews/host-live/c-out/r2/results.json)。
- [正常关闭决定](reviews/host-live/audit/closeout-decision.json)、[关闭结果](reviews/host-live/audit/closeout-decision-result.json)、[最终 Mission 检查](reviews/host-live/audit/final-check.json)。
- [TPlan 执行报告](reviews/host-live/mission/reports/execution-cost-tree.md)、[执行过程图](reviews/host-live/mission/reports/execution-cost-tree.svg)。
- [离线复核说明](reviews/host-live/README.md)：重跑实际 C 驱动，保留固定成果字节和摘要，仅在临时目录写新结果。

工程代码保持 R5 已审版本，其精确 head CI 已通过（全仓库运行 1412 项、跳过 7 项）。本阶段新增宿主证据、报告和离线支撑，普通行为由真实 Agent 和宿主执行，离线重跑单独标为机械复核。

## Boundary / 交接

本次批准的普通三会话宿主验收至此完成。PR #247 保持 draft、Issue #246 保持开放；合并、发布、部署、安装 Skill 和生产修改沿原权限边界处理。

冻结前定位：当前交付为已闭合的真实宿主验收及能力层级证据，下游据此审阅现有 PR 并决定后续合并/发布动作。

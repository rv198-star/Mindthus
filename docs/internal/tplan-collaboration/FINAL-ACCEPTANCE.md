# Issue #246 最终验收

日期：2026-11-18（Asia/Shanghai）。结论：**PASS，可进入已授权的合并与 Stable 发布。**

## Core / 验收目标

验收以 Issue #246 的原始目标为准：多会话反馈插入后，A 继续对用户交给自己的目标、职责和验收负责。委派、版本、回执和恢复为这一目标服务。当前实现、源 Agent 行为和普通本地 A/B/C 实测共同满足该范围。

用户本轮已明确授权“最终收尾验收……验收通过的话可合并并 release 新版本”。开发期文档中的未授权合并/发布边界属于当时记录；本次发行按新授权执行。

## Mainline / Issue 逐项核对

| Issue 要求 | 最终证据与结论 |
| --- | --- |
| 连续无关建议不扩大 A 的任务范围 | T26 实际源 Agent 将扩范围建议延后/拒绝，任务与委派数量保持，回到原验收差距。见 [R3 行为验收](REVIEW-R3.md)。PASS。 |
| 开发细节不接管 A 的职责 | T27 将实现排错交回 B；真实宿主中 B 独立完成完整返修、自测和自审，A 保持设计/证据/最终验收。PASS。 |
| 高频反馈后接回主线 | T28 批量处置进展与重复疑点，按证据缺口续接；真实宿主的焦点由 A 的 T2 转到 A 的 T3，有已完成依据。PASS。 |
| 合法路径调整与明确目标变更 | T29 依据失败证据暂停路径；用户明确改目标后 supersede 原 Mission，创建新的 canonical objective/acceptance。PASS。 |
| 只有 A 需要 TPlan，无模式口令 | Skill/协议按已授权实际委派启用；T22/T23 覆盖启用与普通引用；五种解包布局及真实普通 B/C 闭环通过。PASS。 |
| 反馈绑定当前任务、轮次与成果 | R5 对当前采用、必需审查、逐 AC 最新合格观察、连续返修及分支覆盖独立复审通过；旧 FAIL/PASS 保留历史。PASS。 |
| Guard、事务、指纹及原权限合同 | 工程回归覆盖 Guard 拒写、未知发送保护、崩溃恢复、幂等/冲突、H1/Q1/Q2 兼容；最新证据 head CI 成功。PASS。 |
| 有效等待与恢复 | Pulse/snapshot/survey 给出当前责任、差距、反馈、外部工作和下一动作；真实回执隐藏与历史索引延迟均查原会话恢复。PASS。 |

## Runtime support / 测试与证据层级

T01–T29 逐项表在 [RESULTS.md](RESULTS.md)。机械状态验证、受控 Agent 行为、真实宿主闭环分别保留来源：

- R5 工程代码：`223b7d2b99969c6a6ee9549730d2b8a2271d2401`；[独立审计 PASS](REVIEW-R5.md)，原 B1/C1 探针和新增末端 FAIL/分支覆盖检查均通过。
- 工程及证据提交：`7d9a1aa12ee369b8812891a58a52fcb8d38925a7`；[CI 成功](https://github.com/rv198-star/Mindthus/actions/runs/44128166810)，TPlan Ran 659，全仓库 Ran 1412 / skipped 7。后续提交至此仅增文档和证据，运行时代码与已审版本一致。
- T23/T25/T26–T29：读取 [实际动作](reviews/r3-audit/source-actions.jsonl) 与 [结果](reviews/r3-audit/outcomes.json)，属于 `controlled_source_agent_exercise`。
- [真实宿主验收](HOST-ACCEPTANCE.md)：B 交付 → C 独立 337 例/151 FAIL → B 自主完整返修 → C 当前 443 例全通过 → A 正常 Mission Review 关闭。B 的 381 项与 C 重叠，分别计数。
- [原目标](reviews/host-live/audit/goal-baseline.json)、[完成状态](reviews/host-live/audit/final-summary.json) 和 [原生记录](reviews/host-live/README.md) 对应：目标/验收一致、三个任务完成、未决反馈与当前差距为零。

本次发行仅整理版本、发布材料和已有测试中的版本断言；TPlan 业务脚本保持已审字节。runtime manifest 的候选身份正式定为 `1.6.0` / `mindthus-tplan-v1.6.0`，其新指纹按发布检查验证。发布前本地定向检查 Ran 103 / skipped 1，全部通过，覆盖发行边界、打包、日志版本、干净解包命令、H1 指纹及 provenance。命令与结果见 [发布检查](reviews/release-1.14.0/verification.txt)。发布 PR 和合并提交 CI 是 tag 的前置条件。

## Boundary / 宿主能力与升级

已接受场景为普通同账户 A/B/C。当前 MCP 未暴露发送幂等键及 stop/interrupt；实际取消须获得宿主停止事实。按线程的物理存储/身份隔离由宿主/H1 权限提供。Issue 本身将 #140、#146、#200、#232 留在各自范围，本次无新增阻断项。

v1.14.0 同时收录上次 Stable 后已合并的 Q1/Q2/H1 代码；普通入口保持 H1 关闭，真实人工业务接入沿其既有条件。旧 Mission 继续使用固定运行时，新 Mission 使用新版。ROI Beta 停止维护及后续发布。

冻结前定位：产品目标和已授权范围已满足；后续动作是发布验证，而非继续扩展协同功能。发布记录应固定合并 SHA、tag、CI 和实际下载校验。

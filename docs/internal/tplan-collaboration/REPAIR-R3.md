# Issue #246 / PR #247 — R2 审计返修批次（R3）

日期：2026-11-17。对象：R2 审计 `REVIEW-R2.md`（head `1315a1120`）的两个 P1 根因 A1/A2 与 R02 证据分类。
同一分支/工作区按根因修复，保留历史证据。返修后精确 head 见 PR #247 与交审包。

## Core / 结论

A1（当前验收责任投影）与 A2（完成后业务写边界）按根因收敛修复；R2 的 4 个隔离反例对修复后代码复跑全部被正确拒绝
（`reviews/r3/probe-results-after.jsonl`，对照 `reviews/r2-audit/probe-results.jsonl`）。R02 驱动证据如实降级为
`scripted_runtime_scenario`（机械脚本场景），不再标实际 Agent 自主取舍；实际 Agent 目标保持行为由源会话在核心逻辑稳定后执行验收。

## A1 — 当前验收责任连续性（原 R06 根因收敛）

根因：退役投影 `current=None` 直接跳过义务；`max(round)` 选错当前责任；repair 后旧正面验收仍可满足收口。

收敛规则（单一共享投影 `_task_acceptance_findings`，Task 完成 / Mission 闭合 / 续接差距共用）：
- 退役解除物理占用，但验收义务沿显式继任/修复/授权范围变更持续存在。有协作历史的任务无合法当前成果/明确处置时保持验收缺口，不再 current=None 跳过。
- 新委派轮次必须严格递增（monotonic succession），拒绝回退/重复轮次；当前责任取最新合法继任，而非未经约束的 round 数值。
- 采用记录新增 `invalidated` 标志。对已接受当前成果的阻断性 repair 使其失效（历史保留），并建立 `repair_obligations` 记录，承接来源任务/委派→success-critical 修复任务及其 AC。
- 修复义务仅由修复任务的新验收满足：修复任务当前有效采用+所需复审 PASS，或限定修复任务范围的合格 acceptance_passed。普通入口零新成果/复审/验收完成修复任务不满足义务；旧采用不能据此闭合 Mission。
- `_required_review_findings` 检查 invalidated；续接视图 acceptance_gaps 暴露未满足协作差距。

回归：`test_a1_failed_only_attempt_keeps_obligation_then_successor_completes`、`test_a1_monotonic_succession_rejects_lower_or_equal_round`、
`test_a1_current_follows_latest_successor_not_older_pass`、`test_a1_repair_invalidates_current_and_requires_fresh_acceptance`（含正向全链路）。
反例：retired_only / lower_round_new_FAIL / repair_marked_complete 三例修复后均被拒绝。

## A2 — 完成后业务写边界

根因：Mission completed 后仍接受改变当前采用的迟到 adopted。

修复：Mission 状态非 active 时，所有新协作业务写（enable/delegation.prepare/dispatch.record/feedback.record/feedback.resolve/coordination.checkpoint/coordinator.handoff）
以 `mission_closed` 拒绝；迟到事实由后续 Mission/合法续接承接。只读 snapshot.get/command.get、原命令历史重放、原准备事务恢复继续可用，不改变当前采用、不启动新业务执行。覆盖其他终态（abandoned）。

回归：`test_a2_closed_mission_rejects_late_business_writes_but_keeps_reads`、`test_a2_closed_mission_replay_and_recovery_available`、`test_a2_other_terminal_status_blocks_business_writes`。
反例：closed_mission_accepts_unreviewed_late_adoption 修复后 mission_closed 拒绝，当前采用保持 h1，completion_findings 为空。

## R02 — 证据分类收敛

- 驱动 `evidence_class` 由 `agent_behavior_execution` 改为 `scripted_runtime_scenario`，并加 classification_note：disposition/rationale/next_action 为预置 Python 常量，非自主 Agent 取舍。
- T29 第二步如实标为协调摘要更新（coordination.checkpoint 仅改 gap_summary/next_action，未改 canonical 目标/验收）；outcome 标志改为 coordination_summary_updated。
- T23 主动 enable 后导入引用材料，仅覆盖“不创建新委派”，不标“入口未启用已验证”。
- 保留机械测试 `tests/tplan/test_collaboration_behavior.py`（重跑核对脚本场景状态），不再新增理想答案驱动器。证据/transcript 已按新分类重生成。
- 实际 Agent 对 T23/T25/T26–T29 的自主取舍与工具调用、实际输入/回答/状态/当前会话来源，由源会话在核心修复稳定后执行并语义验收；真实三会话宿主能力按已列清单单独验收。

## 验证（CPython 3.11.11，TMPDIR=/private/var/tmp）

协作/脚本场景定向 47 项通过；TPlan discover 与全仓库 discover 见交审包精确计数。R2 四反例复跑全部正确拒绝。git diff --check 与 py_compile 通过。

## 仍待源会话/宿主验收

实际 Agent 目标保持行为（T23/T25/T26–T29）；真实三会话 A/B/C 宿主 E2E；peer 来源/唤醒/重投去重/取消可观测性；A→A 写入者隔离。
合并/发版/部署/安装包或生产修改仍不在开发授权内；保持 draft，Issue 开放。

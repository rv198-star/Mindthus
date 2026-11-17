# Issue #246 / PR #247 — R1 审计返修批次（R2）

日期：2026-11-17。对象：R1 审计 `REVIEW-R1.md`（head `8b12ccb6f`）提出的 7 项 P1、3 项 P2。
本批次在同一分支 `codex/issue-246-tplan-collaboration` 与工作区按根因修复，保留 R1 历史证据。
返修后精确 head 见 PR #247 与交审包。

## Core / 结论

R01–R10 全部按根因修复并补回归。R1 的 8 项隔离反例对修复后代码复跑，全部转为正确行为
（见 `reviews/r2/probe-results-after.jsonl`，对照 `reviews/r1/probe-results.jsonl`）。
T23/T25/T26–T29 改为真实运行时执行证据（`reviews/r2/behavior-execution.jsonl` 与可读
transcript），旧的理想答案文件降级为场景/预期。安装资源现包含随包协议与冷启动闭环样例，
五种干净解包布局仅依赖随包文件即可跑通完整闭环。

## R01–R10 映射

### R01（P1）普通 peer 进度被升级 user_feedback/loopback，续接 next_action 被覆盖
- 根因：`_collect_collaboration_feedback_candidates` 对所有 pending 反馈一律 `user_feedback`/`loopback`/high；`build_resume_view` 用 pending 输入覆盖已声明 next_action。
- 修复：反馈新增可选 `kind`（progress/result/review/blocker/question，默认 progress）。Pulse 改用独立信号 `collaboration_feedback`：普通 progress → `continuation_authorization`/low/`same_path_continuation`；result/review → medium；blocker → `mission_review`/high。`build_resume_view` 保留协调者声明的 next_action，仅以 `pending_feedback_count`/`needs_association_count` 暴露待处理量。
- 回归：`test_r01_ordinary_progress_does_not_force_loopback_or_override_next_action`、`test_r01_blocker_feedback_routes_to_mission_review`；更新 `test_feedback_replay_conflict_and_pulse_cover_non_active_task`、`test_unassociated_natural_language_feedback_waits_for_targeted_question`。
- 反例：`progress_becomes_user_feedback_loopback` 修复后 `collaboration_feedback`/`continuation_authorization`/`same_path_continuation`，focus T2、next_action 保持。

### R02（P1）首要行为验收由预写理想答案替代
- 根因：`collaboration_behavior_replay.jsonl` 是预写 input/理想 a_decision/自声明 true，测试只查非空，无实际执行来源。
- 修复：旧文件 `evidence_class` 改为 `scenario_expectation`（场景/预期）。新增可执行驱动 `tests/tplan/collaboration_behavior_driver.py`，用本轮真实 `collaboration_runtime.execute` 跑 T23/T25/T26/T27/T28/T29，保全输入、实际决策、工具请求/结果（status/code/commit_id）、前后 canonical 状态。执行证据写入 `reviews/r2/behavior-execution.jsonl`，可读 transcript 见 `reviews/r2/behavior-execution-transcript.md`。新增 `tests/tplan/test_collaboration_behavior.py` 重新执行并核对具体目标保持结果，且校验已提交 transcript 与新跑结果一致。
- 结果：六场景全部真实执行且断言为真（T23 无委派、T25 仅既有委派、T26 无新任务/委派、T27 调试归 B、T28 pending 清零且单一采用、T29 替代委派+历史保留+目标变更续接）。真实三会话宿主 E2E 仍待源会话验收，未冒充。

### R03（P1）历史 PASS 掩盖同一当前成果后续 FAIL
- 根因：`_required_review_findings` 只搜索任意历史 PASS。
- 修复：按当前采用成果（delegation/round/contract/artifact_ref/digest/reviewer）过滤审查，取插入序最后一条有效审查；最新为 FAIL 则阻止完成，直到后续有依据的修复/复审 PASS。旧成果 FAIL 因 artifact 不匹配而不污染当前版本。
- 回归：`test_r03_later_fail_blocks_until_rereview_pass`（PASS→FAIL 阻止 Mission close，复审 PASS 后通过）、`test_r03_old_version_fail_does_not_pollute_current_adoption`。
- 反例：`later_FAIL_hidden_by_old_PASS` 修复后完成被正确拒绝。

### R04（P1）审查回执可移植到另一委派/轮次/合同
- 根因：`_validate_review` 与 state 校验忽略源回执自身的 delegation/round/contract。
- 修复：审查必须匹配源 feedback 的 delegation/round/contract/artifact 与配置 reviewer 绑定；`validate_state` 同步校验。
- 回归：`test_r04_review_cannot_transplant_across_delegations`（D1 回执登记 D2 审查被拒，正确当前审查通过）。
- 反例：`review_transplanted_across_contracts` 修复后 `review_required`，无审查落库。

### R05（P1）repair/adopt 释放仍 running 的物理范围
- 根因：准入只看业务 `delegation.status` 是否在 unresolved 集合；repair/adopt 改业务状态即放行。
- 修复：新增 `_delegation_physically_in_flight`，准入由 intent 的 send/execution 事实决定（prepared/confirmed/unknown 且未 stopped/completed/failed 即在途），与业务采用/返修状态分离。同任务/同写入范围在途时拒绝新执行；真实 stopped/completed/failed 或 not_sent 后才放行；独立范围不受影响。
- 回归：`test_r05_repair_or_adopt_cannot_release_running_scope`、`test_r05_stopped_scope_allows_new_round_and_independent_scope_proceeds`。
- 反例：`repair_releases_still_running_scope` 修复后 `execution_in_flight`，I2 未创建。

### R06（P1）已未发送/已终止旧委派永久参加完成门槛
- 根因：`completion_findings`/`task_completion_findings` 遍历任务的所有历史委派并要求 status==accepted。
- 修复：新增 `_delegation_retired` 与 `_task_current_delegation`，完成门槛只检查当前有效委派（排除 not_sent/stopped/failed/superseded 历史），以当前采用成果+所需审查判定，不再要求业务 status==accepted。repair 不再弹出原任务采用成果，修复任务承接 AC，保留历史。
- 回归：`test_r06_not_sent_then_new_round_completes`、`test_r06_stopped_then_new_round_completes`、`test_r06_completed_task_defect_repair_rereview_mission_close`（缺陷→修复任务→复审→Mission close 全路径）。
- 反例：`retired_attempt_blocks_current_completion` 修复后 D2 当前轮次完成成功，D1 not_sent 被忽略。

### R07（P1）恢复先写入后校验请求身份/build
- 根因：`runtime.recover` 先调用前滚再 `_load` 校验。
- 修复：新增 `_validate_recovery_request`，在前滚任何写入前核对请求 mission_id、目录身份、expected_build、当前与 prepared 状态的 runtime/provenance 兼容及 prepared Mission 形状；错误请求保持所有业务文件与 journal 原样。
- 回归：`test_r07_recovery_rejects_wrong_identity_before_write`（错误 mission_id/build 拒绝且字节/journal 不变，正确原 writer 恢复成功）。
- 反例：`recovery_writes_before_request_identity_check` 修复后 `mission_changed_despite_rejection=false`、journal 保留、D1 未提交。

### R08（P2）写响应 expected_snapshot 返回即陈旧
- 根因：摘要计算后又写进 command.data，改变其摘要对象（自引用）。
- 修复：历史命令结果只持久化业务结果（不含快照）；提交后从最终状态计算当前 `expected_snapshot` 放入响应；重放返回原结果+当前快照；`command.get` 返回稳定历史结果。写后响应摘要与最终状态一致，可直接用于下一命令。
- 回归：`test_r08_write_response_snapshot_is_current_and_usable`。
- 反例：`returned_snapshot_is_already_stale` 修复后 `advertised_equals_actual=true`，下一命令成功。

### R09（P2）容量漏计本次 trace 追加
- 根因：`_capacity_check` 只查旧 trace 尺寸。
- 修复：容量检查计入本次事务将追加的 trace 记录（`_state_change_trace_records` 序列化字节）与最终 Mission/evidence/command store 尺寸；超限拒绝新写并保留查询/恢复。
- 回归：`test_r09_trace_capacity_includes_this_append`（临界拒绝、前后字节不变、随后 snapshot 可读）。
- 反例：`trace_growth_bypasses_capacity` 修复后 `capacity_exceeded`，字节不变，后续读取成功。

### R10（P2）安装资源把必需协议指向未随包内部文档
- 根因：`collaboration.md` 指向 `docs/internal/.../CONTRACT.md`（不在包内）；打包测试只手工注入 JSON 验证 snapshot/enable。
- 修复：新增随包 `skills/tplan/resources/collaboration-protocol.md`（精确 envelope/action/payload、容量/重放/恢复、冷启动样例，相对链接）与自包含 `skills/tplan/scripts/collaboration_example.py`（仅用随包脚本跑 snapshot→enable→delegation.prepare→dispatch.record→feedback.record→feedback.resolve→snapshot.get→command.get）。`collaboration.md` Commands 改为相对链接随包协议与样例。打包测试对五种干净解包布局运行该样例并校验协议资源存在、无内部文档依赖。
- 回归：`tests.tplan.test_command_release_pack`（五布局冷启动闭环 ok）。

## 验证（CPython 3.11.11，TMPDIR=/private/var/tmp）

```text
tests.tplan.test_collaboration + test_collaboration_runtime: 37 passed
tests.tplan.test_collaboration_behavior: 3 passed
discover -s tests/tplan: 628 passed, 1 skipped
tests.test_packaging_docs: 41 passed, 1 skipped
discover -s tests: 1381 passed, 8 skipped
```

R1 反例脚本对修复后代码复跑：`reviews/r2/probe-results-after.jsonl`（8 项全部转为正确行为）。
`git diff --check` 与 `py_compile` 通过。系统 Python 3.9 的基线 PEP 604/enterContext 不兼容与本次改动无关，CI 与上述结果均用 3.11。

## 仍待宿主/人类验收（与工程未修问题分开）

- 真实三会话 A/B/C 宿主 E2E（普通 B/C，无参与者 TPlan）。
- 真实 peer 来源身份、跨会话唤醒、宿主重投去重、取消/停止可观测性。
- A→A 写入者 OS/会话隔离（运行时仅记录并校验 generation）。
- 源会话对 T23–T29 实际执行决策与续接的语义复核。

合并、发版、部署、安装包或生产修改仍不在开发授权内；保持 draft，Issue 开放。

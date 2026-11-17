# Issue #246 / PR #247 第一轮独立审计：REVISE

日期：2026-11-17。审计对象：[PR #247](https://github.com/rv198-star/Mindthus/pull/247)，精确 head `8b12ccb6f669023094c90f6bd6598a7877289a61`，base `520376990613eb34bfdbbdaa4fc4ba227d4fbcfb`。

## Core / 结论

**REVISE：7 项 P1、3 项 P2，按一个完整批次返修。** 当前 24 项协作测试通过；独立审计新增 8 个隔离反例，复现了主线反馈分流、审查绑定、在途保护、历史委派收口、恢复验证、返回摘要和容量检查的问题。首要目标保持验收仍缺实际执行记录，安装包还缺可直接使用的 payload 合同。

开发按原范围自主修复、补必要回归及自审后，再一次性交审。继续使用同一 Issue、PR 与分支，保留审计和历史证据。

## Mainline / 完整返修批次

### R01 — P1：普通参与者进度被当作用户反馈，强制进入 Mission loopback

位置：[tplan_runtime.py](../../../skills/tplan/scripts/tplan_runtime.py) 的 `_collect_collaboration_feedback_candidates`（5667–5683）；[collaboration.py](../../../skills/tplan/scripts/collaboration.py) 的 `build_resume_view`（1184–1189）。

复现 `progress_becomes_user_feedback_loopback`：A 在 T2，仅收到 B 的普通进展，Pulse 胜出 `signal=user_feedback`、`next_gate=loopback`、`scope=mission`、`severity=high`；续接视图将原 next_action 替换成处理 pending feedback。当前代码对所有 peer 输入一律如此。

这会让普通高频更新不断占据主线方向判断，直接偏离“先判断目标相关性、普通反馈批处理、有效主线续接”的核心目标。应区分参与者候选事实与用户指令，保留待处理可见性与目标判断入口；在具体影响/阻塞尚未判断前，不固定给所有消息同一高优先级回溯动作。普通无关进度不得覆盖有效工作焦点或下一动作，关键反馈仍在相应副作用/验收前处理。补普通进度与实际阻断两条行为/状态回归。

### R02 — P1：首要行为验收由预写的理想答案替代，缺少实际执行来源

位置：[collaboration_behavior_replay.jsonl](../../../tests/tplan/collaboration_behavior_replay.jsonl) 全部四条；[test_collaboration_runtime.py](../../../tests/tplan/test_collaboration_runtime.py) 的 `test_goal_preservation_behavior_replay_is_reproducible_and_not_claimed_as_e2e`（571–580）；RESULTS 的 Goal-Preservation Evidence。

四条 JSON 直接给出 input、理想 a_decision、next_action 和自声明的 true 标志。测试只检查 case 名称、标记和非空字段，没有驱动 Agent、导入这些消息、执行决策或核对产生的状态/动作；没有绑定会话/turn 的实际输出来源。它们适合作为场景与预期，当前不能据此把“行为回放已完成”交由语义复核后通过。

将它们明确归为场景/预期，并提供实际执行的分步驱动与输出：使用本轮实际协作入口，保全输入、Agent 实际回答/下一动作、工具请求/结果、前后状态、源码和可核对的来源引用。源会话再按目标关联、角色责任与有效续接判断。可沿现有已授权会话执行，完成全部不依赖新授权的工作；真实宿主缺口继续准确列示，不新建额外用户会话。补 T23/T25 真实对应场景；当前四条文件只包含 T26–T29。

### R03 — P1：历史 PASS 掩盖同一当前成果后续 FAIL

位置：[collaboration.py](../../../skills/tplan/scripts/collaboration.py) 的 `_required_review_findings`（1213–1225）。

复现 `later_FAIL_hidden_by_old_PASS`：同一委派/合同/成果先记录 C 的 PASS，再记录 C 的 FAIL，之后任务完成与 Mission completed 均成功，`completion_findings=[]`。函数只搜索任意历史 PASS，不处理后续有效失败。

按同一适用版本/范围的有效审查顺序判定当前结果；后续 FAIL 应约束验收，直到得到有依据的后续修复/复审或明确处理。旧成果的失败不能污染当前不同版本。补 PASS→FAIL 阻止 Task/Mission、修复后通过、旧版本反向隔离的回归。

### R04 — P1：审查回执可移植到另一个委派/轮次/合同

位置：[collaboration.py](../../../skills/tplan/scripts/collaboration.py) 的 `_validate_review`（827–844）及 `validate_state` 的 review 来源校验（1555–1563）。

复现 `review_transplanted_across_contracts`：F 来源明确关联 D1/round1/contract-r1，`feedback.resolve` 却成功登记 D2/round2/contract-r2 的审查。只要 artifact_ref/digest 相同，校验忽略 source feedback 自己的 delegation/round/contract；scope 也可由本次 payload 改成 D2 所需范围。

把 review 与其原始回执的委派、轮次、合同、成果及审查范围完整绑定，并在 state 校验、采用/闭合投影中保持一致。补相同 artifact 在不同 task/round/contract 下的错误移植拒绝测试及正确当前审查通过测试。

### R05 — P1：反馈处置释放仍在运行的写入范围，允许重复实施

位置：[collaboration.py](../../../skills/tplan/scripts/collaboration.py) 的 `_prepare_delegation`（458–463）、`_resolve_feedback`（983–992，及 adopted 状态更新）。

复现 `repair_releases_still_running_scope`：I1 为 confirmed/running，收到缺陷后用 `repair` 同时创建同任务/范围的 D2，命令成功，I1 仍 running、I2 已 prepared。原因是 repair/adopt 把 delegation.status 改出 unresolved 集合，准入却只看该业务字段。

同任务/写入范围的物理在途保护应由实际 intent/execution 未决事实决定，和业务采用/返修状态分开。保留原轮次对账，真实 stopped/completed/failed 或有效隔离后才能准入同写入范围的新执行。补 repair、adopted、stop-requested 等路径的覆盖，并验证独立范围仍可推进。

### R06 — P1：已未发送/已终止的旧委派仍永久参加当前完成门槛

位置：[collaboration.py](../../../skills/tplan/scripts/collaboration.py) 的 `task_completion_findings`（1268–1273）和 `completion_findings`（1240–1246）。

复现 `retired_attempt_blocks_current_completion`：D1 明确 not_sent，D2 第 2 轮完成且已按当前成果审查，完成 T1 仍因 D1 没有采用成果、不是 accepted 而被拒。当前逻辑遍历该任务的所有历史委派。已完成任务的 repair 测试也只检查创建修复任务，没有走到修复、复审、总收口。

明确当前有效委派/成果与安全退役历史的关系，按当前实际责任检查完成；保留旧事实，原任务 AC 继续由合法修复/替代关系满足，不通过伪造旧未发送委派的采用来解锁。补 not_sent→新轮次完成、stopped→新轮次完成、已完成任务发现缺陷→修复→复审→Mission close 的全路径测试。

### R07 — P1：恢复在请求身份/build 检查之前落盘，返回拒绝却已改变 Mission

位置：[collaboration_runtime.py](../../../skills/tplan/scripts/collaboration_runtime.py) 的 `execute`（146–150）。

复现 `recovery_writes_before_request_identity_check`：先制造合法 prepared transaction，然后用错误 mission_id/build 发 runtime.recover。请求返回 invalid_state，但 D1 已提交、Mission 字节已改变、journal 已删除。当前调用 `_recover_pending_mission_transaction_unlocked` 后才 `_load`。

先核对请求对应的 Mission-directory identity、现有与 prepared 状态的 runtime/build/能力，再允许前滚原事务；错误请求保持所有业务文件和 journal 原样。补错误 mission_id、错误 expected_build、prepared/source runtime 错配及正确原 writer 恢复重放。

### R08 — P2：写入返回的 expected_snapshot 在返回时已陈旧

位置：[collaboration_runtime.py](../../../skills/tplan/scripts/collaboration_runtime.py) 的 `execute`（244–245）。

复现 `returned_snapshot_is_already_stale`：enable 成功后返回的摘要与紧接着 snapshot.get 不同，直接将该返回值用于下一次 delegation.prepare，得到 stale_snapshot。摘要计算后又把它写进 command.data，改变了其摘要对象。

分开历史命令结果与当前快照响应，避免摘要自引用。命令结果持久化保持幂等，返回的当前摘要应对应最终实际状态；若不支持写后快照就删除误导字段并明确下一次读取合同。补连续使用合法写后响应、重放历史响应与当前 snapshot 的回归。

### R09 — P2：容量只检查旧 trace，合法写后超限使任务无法再读

位置：[collaboration_runtime.py](../../../skills/tplan/scripts/collaboration_runtime.py) 的 `_capacity_check`（111–117）。

复现 `trace_growth_bypasses_capacity`：旧 trace 4,194,204 字节，小于 4 MiB；checkpoint 改焦点追加 lifecycle 后成为 4,194,592 字节。写入成功，随后 snapshot.get 返回 capacity_exceeded。检查未包括本次新增 trace；同类边界需要涵盖最终命令记录与结果的实际序列化尺寸。

在 journal prepare 前检查本次事务最终 Mission/evidence/trace 和 command store 的全部新增字节；超限拒绝新写并保留查询/恢复路径。补上限临界值及拒绝前后字节不变、既有历史仍可读/重放。

### R10 — P2：安装资源把精确协议指向未随包交付的内部文档

位置：[collaboration.md](../../../skills/tplan/resources/collaboration.md) 的 Commands（58–60）与 [build-release-pack.py](../../../scripts/build-release-pack.py) 的五类布局复制规则。

安装资源只提供 CLI 外壳，精确 envelope/action/payload 位于 `docs/internal/tplan-collaboration/CONTRACT.md`；打包只复制 skills 与 methodologies 等选定内容，该内部路径不在包中。现有打包测试从仓库测试代码手工注入 JSON，只验证 snapshot/enable，没有验证安装用户可按随包说明完成正常闭环。

把 runtime 必需的协议/样例放进可随包访问的资源并使用相对链接；从干净解包布局、仅依赖随包说明/样例跑 snapshot→enable→委派→回执→处置→查询。确保 Lite quickstart 的原有必要指引也保持可用。

## Runtime support / 本轮验证与证据

源码始终固定在 head `8b12ccb6f669023094c90f6bd6598a7877289a61`；审计写入仅新增本报告和隔离复现材料。无生产 Mission、安装包、认证或远端业务状态变更。

- CPython 3.11.11：`python -B -m unittest tests.tplan.test_collaboration tests.tplan.test_collaboration_runtime -q`，24 项通过，记录见 [existing-tests.txt](reviews/r1/existing-tests.txt)。
- 隔离反例脚本：[reproduce.py](reviews/r1/reproduce.py)。使用同一源码的测试夹具在临时目录建立 Mission；每项独立且退出时清理。
- 8 项原始输出：[probe-results.jsonl](reviews/r1/probe-results.jsonl)。R01、R03–R09 由这些输出直接复现；R02、R10 来自执行来源、测试与打包源码核查。
- 已核对 PR 的精确 head/base 与 GitHub Actions unittest-smoke 成功。现有全套 CI 不因本轮只读审计重复运行；新增反例需纳入后续修复验证。

重现命令：

```text
/private/var/tmp/mindthus-246-py311/bin/python -B docs/internal/tplan-collaboration/reviews/r1/reproduce.py
```

## Boundary / 返修交接与下一轮

开发会话按本报告完整批次自主修复并检查根因，保持冻结产品目标；必要的状态转移/退役关系在 CONTRACT 和回归中同步。普通实现异常自行处理，只有目标/权限/验收实质变更或合理恢复后仍无法推进时集中升级。

下一次 READY_FOR_AUDIT 给出精确 head、R01–R10 处理映射、必要前后反例、完整相关测试/CI、可执行普通闭环和实际行为证据；将真实宿主待验收项与工程未修问题分开列清。保持 draft，Issue 开放，不合并/发行/部署。

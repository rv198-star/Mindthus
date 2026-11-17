# Issue #246 / PR #247 — R4 审计 C1 返修（R5）

日期：2026-11-17。审计代码 `d57d6816ebf27ca30441a68d5cd526341cee315d`；
本批起点为审计专用提交 `ee725e6ac8b44bfddc46ab25ec3f282047369900`。
返修精确 head 由 PR #247 与 READY_FOR_AUDIT 交接固定。

## Core / 正确主规则

修复验收责任按声明的 AC 沿既有责任边传递，当前有效末端完成并满足全部验收及
必需审查后，覆盖对应上游责任。连续修复沿同一规则执行。

## Mainline / 根因与替换

旧 `_repair_obligation_satisfied` 把责任固定在直接修复任务的采用上。
T1→T3 已通过后，T3 再明确交给 T4，D3 的 invalidated 历史会让最初义务永久失败。
`_task_acceptance_findings` 的 incoming/outgoing 分支还把同一任务的两种责任分开了。

现在 `_current_repair_acceptance_satisfied` 是现有函数共用的纯投影：

1. 每个任务保留自身声明 AC；Task 查询同时汇入 incoming/outgoing 的责任。
2. 有显式继任承接某项 AC 时，沿相应边读取继任的全部验收合同。
   每条适用分支都需满足；不同 AC 可由明确声明的不同分支共同覆盖。
3. 未承接的 AC 留在当前任务，使用原有采用/mandatory review 与 R4 合格证据规则。
   当前有效末端状态为 completed，逐项最新合格观察为 acceptance_passed。
4. 原完成状态、invalidated 采用和反馈保持历史；完整承接的上游按末端结果收口。

`_repair_obligation_satisfied` 和 `_task_acceptance_findings` 共同调用这一投影；
Task/feedback.resolve、Mission、snapshot/survey resume 沿既有事件数据流获得相同结果。
投影只读既有 `repair_obligations`，没有新增持久验收状态、调度器或迁移。

## Guardrail / 保护责任连续性

未覆盖 AC、末端尚未 completed、末端 FAIL/缺审查/缺 AC、最新合格 FAIL 继续形成缺口。
另一分支的 PASS 只满足其明确承接的责任；适用的重叠分支全部保留。
循环内部关系按未解决处理，保护纯投影的有界执行。
这些检查保护上述承接主路径；语义采用和任务范围选择仍由 A 负责。

R4 的原生 qualification、引用唯一、task/ancestor 范围及 H1 当前来源版本检查原样复用。
两项纯投影夹具补上末端 completed 状态，使它们与公共路径的完整合同一致。

## Runtime support / 验证

`tests/tplan/test_collaboration_runtime.py` 新增 13 项 `test_c1_*`：

| 范围 | 全路径验证 |
| --- | --- |
| 正向连续修复 | T1→T3→T4 与再深一层 T5，各含本地/委派末端；Task、Mission、snapshot/survey 收口一致 |
| 历史保留 | 原 completed、invalidated 采用、义务和反馈原记录保持 |
| AC 承接 | 部分承接保持缺口，显式拆分覆盖后可关闭；原始任务未承接的 AC 也保留责任 |
| 末端门槛 | FAIL、缺审查、未完成、部分 AC、完成后最新 FAIL 均沿上游保留缺口 |
| 分支与内部完整性 | 单独分支 PASS 不抵消失败分支；内部循环无验收结果 |

新增测试的首轮 RED：13 项运行，6 项失败，暴露两层/三层正向及完整承接后的缺陷。
修复后本地定向 Ran 71、evidence/H1 Ran 75、TPlan Ran 659（跳过 1）、打包 Ran 41（跳过 1）、全仓库 Ran 1412（跳过 8），全部 OK。实际命令、unittest 摘要与静态检查见 [verification.txt](reviews/r5/verification.txt)。

独立审计原复现脚本保持原样：[reviews/r4-audit/reproduce.py](reviews/r4-audit/reproduce.py)。
复跑两项结果：[probe-results-after.jsonl](reviews/r5/probe-results-after.jsonl)。
R4 原八项 B1 探针复跑：[b1-probe-rerun.jsonl](reviews/r5/b1-probe-rerun.jsonl)。
这些均为机械运行时证据；原六项源 Agent 受控行为验收继续按 REVIEW-R3 保留。

## Boundary / 交接

下一步为精确 head 的独立复审。真实宿主 A/B/C E2E、peer 来源/唤醒/重投去重/
取消可观测性和 A→A writer 隔离按原清单验收。PR draft、Issue 开放；发布、部署、
安装 Skill 及生产修改沿原权限边界。

冻结前定位：本批替换的是已有责任连续投影；正向闭环和负向拒绝共同约束规则。
当前交付服务于审查者核验多轮返修后的真实验收差距与合法收口。

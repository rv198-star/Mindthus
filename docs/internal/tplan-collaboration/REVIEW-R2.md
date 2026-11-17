# Issue #246 / PR #247 第二轮独立审计：REVISE

日期：2026-11-17。审计 head：`1315a11201f8fa4c9080902a55f9f78643656032`，base：`520376990613eb34bfdbbdaa4fc4ba227d4fbcfb`。

## Core / 结论

**REVISE：下一批集中修复两类 P1 根因——当前验收责任的连续性、Mission 完成后的业务写入边界。** 独立重跑本轮 40 项协作/脚本场景测试通过；新增 4 个隔离反例仍可绕过当前责任或在已完成状态中采用未审查版本。

原 R01、R03、R04、R05、R07、R08、R09、R10 的已报告路径已有实质修复。R06 的退役投影引出了本轮第一类问题。原 R02 的脚本驱动作为机械状态场景保留，实际 Agent 目标保持由源会话在核心状态逻辑稳定后执行；开发无需再以新的预置脚本代替这项源验收。

## Mainline / A1 — P1：当前有效委派投影丢失或选错了验收责任

相关位置：[collaboration.py](../../../skills/tplan/scripts/collaboration.py) 的 `_delegation_retired`（411）、`_task_current_delegation`（423）、completed-task repair（1027–1040）、`completion_findings`（1284）和 `task_completion_findings`（1304）。

### 已复现的三条路径

1. **唯一执行 failed，原 required review 同时被抹掉。** `retired_only_attempt_erases_acceptance_obligation`：D1 明确配置 required C review，执行 failed 后，直接经普通 `transition_task_status(T1, completed)` 成功。没有 adoption，也没有任何 review，协作完成检查返回空。原因是退役后 current=None，被当成从未委派的普通任务跳过。
2. **后来采用的低 round 失败被旧高 round 的通过覆盖。** `lower_round_new_FAIL_hidden_by_older_higher_round_PASS`：D1/round2/h1 PASS 后，合法命令接受 D2/round1/h2 FAIL 及 h2 采用；current 仍按 max(round) 选 D1，最后 Task 和 Mission 都 completed。准备入口未规定/校验轮次递增，而投影把最大数字当成当前责任。
3. **声明当前成果需要修复后，旧验收仍可满足收口。** `repair_marked_complete_without_fresh_acceptance`：原 h1 PASS、A1 正面验收、T1 completed；新反馈被 A 处置为 repair 并建立 success-critical T3。随后普通入口将 T3 标 completed，没有 T3 新验收、没有新成果、没有复审，Mission 仍 completed；当前采用仍为 h1，D1 为 repair_required。新版保留历史 adoption，却没有单独表达其当前有效性，旧正面结果仍被计入。

### 根因与修复合同

执行是否已经退役、当前由哪个合法继任承接、当前验收责任是否满足，需要在同一规则中明确。**退役解除物理占用，原任务/合同的验收义务沿显式继任、修复或有授权的范围变更持续存在。** 保留历史采用结果时，另外表达当前仍可用于验收还是已被 A 的阻断性修复决定失效。

- 从未委派任务可以继续原普通路径；存在历史协作义务的任务在没有合法当前成果/明确处置时保持验收缺口，避免 current=None 直接跳过。
- 为新委派和当前成果规定并机械校验明确的继任/版本顺序；拒绝回退/重复轮次或使用明确当前引用，不能由未经约束的 round 数值选择旧 PASS。
- `repair` 对已接受当前成果生效时，当前正面验收要得到相应约束；修复任务承接哪些 AC、何种新成果/复审重新满足当前义务须可核对。原历史保持可读。
- 公共 Task completion 与 Mission close 使用同一当前责任投影，续接视图显示这些仍未满足的目标差距。

这是原 R06 语义的根因收敛，不新增通用调度层或以更多状态特判填补。补上述三条失败回归、正确递增新轮次、合法退役继任、阻断性修复→新验收/复审→收口的正向全链路，并确认普通任务、独立范围及旧成果历史隔离。

## Mainline / A2 — P1：已完成的 Mission 继续接受改变业务采用的迟到结果

相关位置：[collaboration_runtime.py](../../../skills/tplan/scripts/collaboration_runtime.py) 的 `execute` 写入路径（206 之后）；[collaboration.py](../../../skills/tplan/scripts/collaboration.py) 的 `_resolve_feedback` 采用与任务完成投影；[tplan_runtime.py](../../../skills/tplan/scripts/tplan_runtime.py) 只在新进入 completed 时检查 Mission closure。

复现 `closed_mission_accepts_unreviewed_late_adoption`：将 T1/h1/PASS、A1 验收与 Mission completed 正常写入后，再记录 B 的 h2 回执并执行 adopted（无 C 审查），命令仍 committed。Mission 继续 completed，但当前采用变成 h2，`completion_findings` 已报告 h2 缺 reviewer PASS。

修复合同：已关闭 Mission 的业务结果与验收保持其完成时边界，迟到输入只按历史/后续处置保存。只读查询、相同命令历史重放和原准备事务恢复继续可用；新的 adopted、委派或任务路径变化由明确后续 Mission/合法续接决定承接。若允许记录迟到事实，记录方式不得改变既有当前采用或启动新业务执行。

补已完成 Mission 迟到结果、迟到 FAIL、迟到 adoption/新委派的拒绝或历史保存测试，以及读取、原命令重放与合法恢复不受影响的测试；覆盖其他已关闭状态的同类边界。

## Runtime support / 原 R02 的证据分类与源验收安排

新增驱动确实执行了真实 Python runtime，能验证指定处置被提交后的机械状态。其 `disposition`、`rationale`、`next_action`、`agent_decision` 仍由 Python 常量/循环预置（例如 driver 157–165、181–186）；当前记录应标为 `scripted_runtime_scenario` 或等价准确类别，不作为实际 Agent 自主反馈取舍的执行记录。

driver 的 T29 另有具体口径问题：251–260 将 B 来源的 `summary='User narrows...'` 作为输入，仅 `coordination.checkpoint` 改了 gap_summary/next_action，未更新 canonical Mission 目标或验收，也没有原用户来源的实际确认。其 outcome 只核对 next_action 字符串。应按实际效果分类为协调摘要场景；目标变更用可追踪的受支持路径单独验证。T23 当前主动 enable 后才导入引用材料，也只覆盖不创建新委派，不能据此标入口未启用已验证。

开发本批次负责准确分类/文档/测试映射与可执行工具路径，不再叠加一个“写死正确答案”的行为证明器。**源会话负责在核心修复稳定后，按 T23/T25/T26–T29 使用当前 Agent 作实际取舍并调用工具，保全实际输入、回答/动作、状态和当前会话来源，再给出语义验收。** 真实三会话宿主能力仍按已列清单单独验收。

## Runtime support / R01–R10 复核状态

| 原项 | 本轮状态 |
| --- | --- |
| R01 普通 peer 输入 | 已分出 collaboration_feedback/kind，普通进度保持 next_action；原路径修复 |
| R02 行为证据 | runtime 脚本场景有效；分类需准确，实际 Agent 行为由源会话后续执行 |
| R03 PASS→FAIL | 同一选定成果的最新审查约束已修复；跨“当前委派”选择见 A1 |
| R04 回执移植 | 源 delegation/round/contract 绑定已加入，原路径修复 |
| R05 在途占用 | 正常 repair/adopt 不再直接释放 running intent；原路径修复 |
| R06 退役历史 | 原 not_sent→新轮次路径修复；当前责任连续性见 A1 |
| R07 恢复前校验 | 请求身份/build 和 prepared provenance 检查已前置，原路径修复 |
| R08 返回摘要 | 提交后单独生成，原路径修复 |
| R09 容量 | 本次新增 trace 已计入，原临界路径修复 |
| R10 包内协议 | 已增加随包协议和闭环 example，CI 五布局检查成功；原缺口修复 |

## Runtime support / 验证与复现

- 固定源码 `1315a11201f8fa4c9080902a55f9f78643656032`，CPython 3.11.11。
- 独立运行 `tests.tplan.test_collaboration`、`test_collaboration_runtime`、`test_collaboration_behavior`，40 项通过，见 [existing-tests.txt](reviews/r2-audit/existing-tests.txt)。
- 本轮新增 [reproduce.py](reviews/r2-audit/reproduce.py) 和 [4 项原始结果](reviews/r2-audit/probe-results.jsonl)，全部在独立临时 Mission 中执行并清理。
- 已核对 PR 的 head/base、draft 状态和 unittest-smoke 成功。未改运行时代码，未重复无关全套测试。

## Boundary / 一个返修批次

开发先将“当前责任—退役—修复—合法继任”规则在 CONTRACT 中一次收敛，再整批修复 A1/A2，补必要前后反例和自审。实现细节、依赖、测试和恢复异常自主处理；范围/权限/验收实质变化或合理恢复后仍阻塞时再集中升级。源行为验收由源会话承担，开发交审保留这项准确状态。

继续原 Issue/PR/分支，Issue 开放、PR draft；完成后一次性提交精确新 head、A1/A2 修复映射、证据分类更新和回归/CI。无合并、发行、部署或已安装/生产环境变更。

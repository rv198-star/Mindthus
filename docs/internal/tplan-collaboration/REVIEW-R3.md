# Issue #246 / PR #247 第三轮独立审计：REVISE

日期：2026-11-17。审计 head：`2753470fcd32ef2482e2af6126354e59aca57dcc`；base：`520376990613eb34bfdbbdaa4fc4ba227d4fbcfb`。

## Core / 结论

**REVISE：剩余一个 P1 根因——修复义务的备用验收路径没有保留完整验收条件。** 普通验收可以覆盖必需的 C FAIL，也可以只通过两个必需 AC 中的一个就完成整个修复。Task 与 Mission 均可错误完成。

R3 已修复前轮的退役责任丢失、轮次回退、零新验收完成修复及终态业务写入路径；本会话独立重跑 47 项定向测试通过，远端 PR head 与本地一致，CI 成功。实际源 Agent 对 T23/T25/T26–T29 的受控目标保持演练也已完成，记录见下文。下一批只修当前验收投影根因，保留已有修复与行为记录。

## Mainline / B1 — P1：修复验收 fallback 放行未满足的责任

位置：`skills/tplan/scripts/collaboration.py:1337` 的 `_repair_obligation_satisfied`；Task completion 与 Mission close 均复用这一判定。

两个隔离复现均使用公共协作入口建立修复义务，然后使用原生验收/状态入口：

1. `ordinary_repair_acceptance_overrides_required_C_FAIL`：原成果通过后收到阻断性反馈，建立 success-critical 修复任务 T3。T3 的 D3 必需 C 审查，当前 h3 结论为 FAIL；追加 T3 的普通 A1 `acceptance_passed` 后，T3 和 Mission 仍完成，`completion_findings=[]`。
2. `one_of_two_repair_ACs_satisfies_entire_obligation`：原任务和修复合同要求 A1、A2。原版本曾通过两项；修复后只新增 T3/A1 通过，T3 和 Mission 仍完成，旧 A2 被继续使用。

根因：函数先尝试委派采用/复审路径，失败后无条件扫描任一历史 `acceptance_passed`；只要求与 obligation 的 AC 集合有交集。备用路径因此同时绕过当前审查否决、完整覆盖和最新观察。

修复按同一责任规则收敛：

- 原生验收支持合法的本地修复；存在必需的委派审查责任时，保留其当前否决与缺项约束，直到合法继任/明确处置。普通 PASS 不替代 required review。
- 每项声明的 repair AC 都由该修复任务范围内最新的合格观察满足；后续 FAIL、缺项、其他任务/旧成果的 PASS 按适用范围处理。复用既有 evidence qualification，保持引用唯一、范围和版本约束。
- Task 完成、Mission 收口和续接差距使用同一数据与投影。当前 `build_resume_view` 向投影传 `events=None`：正向本地修复已通过且完成时，resume 仍显示缺口；第三个复现 `valid_local_repair_completion_vs_resume` 保存了这一不一致。
- 补负向与正向完整路径：mandatory FAIL/缺审查、AC 部分覆盖、PASS 后 FAIL、无关任务 PASS、合法本地全覆盖修复，以及委派修复当前成果/复审/验收满足后的收口与 resume 一致。

这批替换现有 fallback 判定，沿既有函数与数据流修复；不增加调度器、消息服务或新的验收子系统。

## Mainline / 源 Agent 目标保持验收

本会话实际 Agent 在观察输入后选择动作，经工具提交并核读状态；来源、请求/结果、前后状态在 [source-actions.jsonl](reviews/r3-audit/source-actions.jsonl)。输入中的 peer、host 和用户事件为隔离测试夹具，证据类别为 `controlled_source_agent_exercise`；真实三会话宿主验收另列在边界中。

| 场景 | 源 Agent 的实际选择与结果 |
| --- | --- |
| T23 仅引用其他会话材料 | 保持普通路径，未启用 collaboration；原目标和任务保留，完整性检查通过。 |
| T25 用户限定当前会话 | 对原 D1 请求停止，保留 running 事实及等待条件；无新委派，A 继续 T2 合同审查。 |
| T26 连续扩范围建议 | 将日志重构延后，将随后缓存/发行建议列为越范围；任务和委派数量保持，A 回到原验收差距。 |
| T27 局部排错牵引 | 把 fixture 调试交回 B 自主诊断、修复、自测；A 保持设计/验收职责，未给 A 新增排错任务。 |
| T28 高频与重复反馈 | 一批处理五条进度和三条重复疑点；后续收到绑定当前成果的 C PASS 后登记审查，并请求缺失的成果/运行证据，采用仍待定；A 继续 T2。 |
| T29 路径失效及用户明确变更 | 独立故障实验观测到两文件版本不一致，记录 finding 后暂停原路径；保持原目标与 A 职责，在观测停止后才准备新轮次。随后用户夹具明确改目标，撤销未发送 I2，旧 Mission superseded，创建当前会话内的新评估目标和验收。 |

T29 的变化写进 canonical objective/acceptance 和生命周期，而非只改 next_action。T28 采取了审查登记、补证据后再采用的路径；这一实际取舍保留在记录中。六项在所测受控输入下满足目标关联、职责保持和有效续接要求。

## Runtime support / 证据与复现

- [README](reviews/r3-audit/README.md)、[独立测试记录](reviews/r3-audit/existing-tests.txt)。开发本地报告运行 1388 项、跳过 8 项；源会话核对同 head CI 运行 1388 项、跳过 7 项，结果成功。
- [反例脚本](reviews/r3-audit/reproduce.py)、[原始结果](reviews/r3-audit/probe-results.jsonl)。每项建立独立临时 Mission 并清理。
- [输入上下文](reviews/r3-audit/fixture-context.json)、[实际源会话记录](reviews/r3-audit/source-actions.jsonl)、[结果断言](reviews/r3-audit/outcomes.json)、[最终状态](reviews/r3-audit/final-states/)。

复现：`python3 -B docs/internal/tplan-collaboration/reviews/r3-audit/reproduce.py`（CPython 3.11）。

## Boundary / 交接

开发会话按 B1 一次完成根因修复、必要回归和自审，再交精确 head。保留原 R3 修复；源 Agent 的受控行为记录已由本会话完成，无需再写预置理想答案驱动。

真实 A/B/C 宿主 E2E、peer 来源认证/唤醒/重投去重/取消可观测性，以及 A→A writer 隔离仍待相应宿主验收。PR 保持 draft，Issue 开放；合并、发布、部署及安装包/生产修改沿原权限边界处理。

冻结前定位：当前产物是源码审计与源行为证据；剩余错误直接影响验收责任，下一步为开发完整返修批次。目标仍是多会话反馈下 A 保持用户目标、职责与验收。

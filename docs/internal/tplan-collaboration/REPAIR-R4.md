# Issue #246 / PR #247 — R3 审计 B1 返修（R4）

日期：2026-11-17。起点：审计提交 `ad438928471461c88f70583020aad04b95ec5667`，
被审 runtime head `2753470fcd32ef2482e2af6126354e59aca57dcc`。
返修精确 head 由 PR #247 与 READY_FOR_AUDIT 交接固定。

## Core / 结果

修复义务按每项 AC 的最新合格观察判定，并保留委派审查责任。
Task 完成、Mission 关闭与恢复差距共用同一证据快照和验收规则。
本批替换 B1 fallback；已有 R1–R3 修复和源 Agent 行为记录保留。

## Mainline / 根因与替换规则

旧 `_repair_obligation_satisfied` 在当前委派/复审检查失败后，扫描任一历史
`acceptance_passed`，仅要求与义务 AC 集合有交集。它会放过 required C FAIL、
AC 缺项和后续 FAIL。恢复视图及 feedback.resolve 的内部检查还没有传入事件快照。

现在先保留修复任务的当前验收责任：有委派历史时，需合法当前采用和绑定该成果、
轮次、合同、范围的最新必需复审 PASS；全部尝试退役后仍保留责任。
随后对每项义务 AC，要求修复任务范围内最新合格观察为 `acceptance_passed`。
本地修复沿原生观察路径执行。完成入口和两个恢复视图均接收实际事件快照。

`tplan_runtime._qualified_acceptance_observations` 从既有 Mission 关闭逻辑提取原生
qualification、全局引用唯一性、任务/祖先 AC 覆盖、H1 当前来源版本过滤和日志顺序。
Mission 继续按原 AC 顺序投影；修复按任务及 AC 投影。Task 范围查询只读取适用的
H1 来源责任，独立任务可继续完成，Mission 保留全局 H1 收口条件。

## Guardrail / 保护的主路径

普通 PASS 补充委派成果验收，保留 missing/FAIL/退役责任约束；它保护的是委派
修复的当前验收路径。其他任务的 PASS、部分覆盖、旧 PASS、歧义引用和不合格记录
留在历史中，不填补当前修复的 AC。此规则只做机械资格检查，采用与语义判断仍由 A 负责。

## Runtime support / 回归和反例

`tests/tplan/test_collaboration_runtime.py` 新增 11 项 `test_b1_*`：

| 范围 | 验证 |
| --- | --- |
| 必需审查 | FAIL、缺审查、退役尝试 + 普通 PASS 均拒绝 Task/Mission 完成 |
| AC 与顺序 | A1+A2 只过 A1 拒绝；PASS→FAIL 拒绝；无关任务 PASS 不代偿 |
| 合格性 | 重复 ID、错误时间/任务/AC、重复 AC、legacy acceptance 均不完成修复 |
| 正向全链路 | 本地及委派全覆盖后 Task/Mission 完成，snapshot/survey resume 无差距 |
| H1 与范围 | 当前来源 SHA/attempt 过滤、当前 FAIL、其他版本 FAIL 隔离；独立 Task 范围保留 |

原有两项委派修复全链路测试现在在完成前提供原生修复验收，再与当前采用及复审
共同完成校验。R3 审计反例原文件保留；[R4 复现](reviews/r4/reproduce.py) 复用其
独立初始/修复夹具，保存六项拒绝及两项正向结果：
[probe-results-after.jsonl](reviews/r4/probe-results-after.jsonl)。

复现：`PYTHONPYCACHEPREFIX=/private/tmp/mindthus246-r4-pycache TMPDIR=/private/tmp python3.11 -B docs/internal/tplan-collaboration/reviews/r4/reproduce.py`。
本地定向 Ran 58、TPlan Ran 646（跳过 1）、打包文档 Ran 41（跳过 1）、全仓库 Ran 1399（跳过 8），全部 OK。测试命令、unittest 摘要与静态检查见 [verification.txt](reviews/r4/verification.txt)。
本机沙箱不提供 `/private/var/tmp` 写入；完整检查使用可写的 canonical `/private/tmp`，
并将显式 py_compile 缓存写入独立临时目录。

## Boundary / 复审交接

源 Agent 的 T23/T25/T26–T29 实际受控演练已在 [REVIEW-R3.md](REVIEW-R3.md) 验收，
类别 `controlled_source_agent_exercise`；R2 驱动维持 `scripted_runtime_scenario`。
本批新增的是机械运行时反例和回归。

下一步是固定 head 的独立复审。真实 A/B/C 宿主 E2E、peer 来源/唤醒/重投去重/
取消可观测性及 A→A writer 隔离沿原清单待验收。PR 保持 draft、Issue 开放。
合并、发版、部署、安装 Skill 和生产修改沿原权限边界处理。

冻结前定位：交付物为 B1 根因修复与可复跑证据；审查者以精确 head 和失败/成功
路径核验验收责任一致性。没有增加调度器、验收子系统或理想答案行为驱动。

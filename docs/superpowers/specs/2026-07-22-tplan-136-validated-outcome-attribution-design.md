# TPlan #136：Telemetry、Validated Writeback 与可计推进归因设计

Date: 2026-07-22
Status: **implemented / independently verified**
Parent: #132

## 0. 一页结论（core）

#136 不应实现成“有成果才算成本”，也不应做一个自动进度分数。

成本一旦真实发生，就必须照常显示；有没有产出，只决定这笔投入旁边应标成什么：

> 成本如实记；写回先验形；推进看 evidence；没有产出也不能藏成本。

整体采用三层事实和一个只读归因结果：

| 层 | 回答的问题 | 控制者 |
| --- | --- | --- |
| telemetry | 发生了哪些调用、耗时和 Token | host / platform + trace 校验 |
| validated writeback | Mission、Task、evidence、decision 是否经过合法写入 | runtime 脚本 |
| outcome meaning | 写回是 acceptance 推进、路径决策、关键约束，还是仅状态变化 | Agent 作语义声明，evidence 约束，脚本校验引用 |
| attribution projection | 当前节点应显示“可计推进 / 关键约束 / 仅写回 / 仅遥测”中的哪些事实 | 只读派生器 |

核心变化不是多存一套进度状态，而是让 user update 和 cost tree 共用一个只读的
`outcome attribution` 分类器。它只从 Mission、evidence 和 execution trace 派生，不写 sidecar，
不是第二事实源。

## 1. 重新定义问题（core）

原题“验证写回后才算进度/成本”把两个不同命题绑在了一起：

1. 成本是否发生：由 telemetry 决定；没有写回也可能已经花了时间和 Token；
2. 是否可以宣称 Mission 推进：必须有合法写回，并由 acceptance 或已应用路径决策约束。

因此改为：

> **成本与有效推进分栏归因，而不是用产出决定成本是否存在。**

要避免的真实失败模式：

- 跑了很多工具，就说“进展很大”；
- Task 标记 completed，但没有 acceptance evidence；
- 写了文件或 artifact ref，就默认目标已经达成；
- cost tree 只强调耗时和 Token，让用户误以为高投入等于高产出；
- 为纠偏又走到另一端，把没有成果的真实成本隐藏掉；
- 脚本根据 event 名称或次数替 Agent 判断“这件事有价值”。

## 2. 核心不变量（core）

### 2.1 成本永不等待写回

合法 telemetry 一旦进入 `execution_trace.jsonl`，成本树必须显示。即使后续没有 Mission、evidence
或 artifact 写回，也只能标为“仅遥测 / 暂无可归因产出”，不能删除、归零或延后认账。

### 2.2 写回合法不等于语义正确

`validated writeback` 只表示：

- 写入走过受支持的 runtime 路径；
- shape、引用、状态迁移和 authority 合法；
- 需要原子提交的 Mission / trace / evidence 组合已完成事务提交。

它不表示：

- artifact 内容正确；
- acceptance 真的通过；
- 决策一定有价值；
- 用户满意；
- 这笔成本因果上产生了该结果。

### 2.3 可计推进必须有明确语义载体

只有两类正向结果可默认称为 `countable progress`：

1. `acceptance_delta`：明确确认某个现有 acceptance id 已满足；
2. `path_delta`：经过合法 decision apply，实际改变路径，或以有效 continuation authorization
   明确确认原路径继续。

blocker、失败、acceptance failed、user feedback 和 stop 很重要，但归入
`constraint_delta`，不能包装成正向进度。

### 2.4 状态变化本身不构成推进

下列动作默认只是 `state_writeback`：

- Task active / paused / completed；
- active node 切换；
- 新增节点；
- outcome summary；
- artifact ref；
- 普通 state transition。

它们只有引用到合格的 acceptance 或 applied-decision evidence 时，才可以继承对应的推进归因。

### 2.5 不做数值化进度

v0.1 不计算百分比、progress points、产出/Token 比、ROI 分数或“每次工具调用价值”。报告只展示
可核对的分类、来源引用和成本事实。

## 3. WAE 控制边界（mainline）

| 判断 | 应由谁控制 | 原因 |
| --- | --- | --- |
| span 是否结构合法、耗时字段是否可信 | script / schema | 确定性校验 |
| Mission mutation 是否成功提交 | runtime transaction | 确定性状态事实 |
| evidence 引用的 task / acceptance 是否存在 | script | 确定性引用校验 |
| 某观察是否真的满足 acceptance | Agent / reviewer | 语义判断，脚本不能替代 |
| 某 decision 是否改变了可执行路径 | Agent 决策 + runtime apply | 先判断，后验证实际写回 |
| blocker / feedback 是否改变约束 | Agent 记录，evidence 留痕 | 语义事实需要载体 |
| 报告该显示哪种归因标签 | pure projection | 输入已确定后的机械映射 |
| 是否继续投入 | Agent / Mission Gate | 不能由历史 Token 或次数自动决定 |

这意味着脚本可以拒绝一个引用不存在的 `acceptance_passed`，但不能因为测试绿色就自行创建
`acceptance_passed`。

## 4. 统一术语（mainline）

### 4.1 Telemetry

来源：`execution_trace.jsonl` 的 lifecycle 与 span records。

它能证明：某个受观测的操作发生、持续多久、报告了多少 Token、属于哪个运行节点。

它不能证明：该操作产生了正确结果或推进了 Mission。

### 4.2 Validated writeback

分为三类：

- `evidence_writeback`：结构与引用合法的 evidence event；
- `state_writeback`：合法提交的 Mission / Task / active-path 状态变化；
- `decision_writeback`：decision 已通过 apply 路径实际提交，而非只有 recommendation。

task-local log、execution telemetry 和 renderer cursor 都不属于 validated Mission writeback。

### 4.3 Countable progress

只表示“存在足以约束用户进度声明的结果”，不是工作量，也不是完成百分比。

- `acceptance_delta`：已确认 acceptance；
- `path_delta`：已应用路径决策。

### 4.4 Constraint delta

会改变下一步、风险或权限，但不是正向推进：

- acceptance failed；
- blocker / failure / interruption；
- stop / requires-human；
- user feedback；
- decision recommendation 尚未 apply；
- active shared risk 及其恢复。

### 4.5 Unclassified writeback

写回合法，但现有字段不足以判断它是否能约束推进声明。它必须留在 audit 中，普通用户输出不得把它
升级成 progress。

## 5. Evidence 分类规则（mainline）

### 5.1 合格的 acceptance delta

一个新写入若要成为 `acceptance_delta`，必须同时满足：

- `event_type` 是推荐的新类型 `acceptance_passed`，或字段完整的 legacy `acceptance`；
- `payload.acceptance_ids` 是非空字符串列表；
- 每个 id 都存在于当前 Mission acceptance criteria；
- `task_id` 存在，并且该节点或其 success-critical 祖先声明覆盖这些 acceptance ids；
- summary 非空；
- event 已成功写入 evidence stream。

新的 `acceptance_passed` 缺任一条件必须拒绝。legacy `acceptance` 为兼容旧调用仍可读取；字段完整时
可按同一规则归因，字段不完整时标为 `unclassified_writeback` 并产生 audit warning，不静默补全。
新代码和文档不再推荐写模糊的 `acceptance`。

### 5.2 Acceptance failed

`acceptance_failed` 使用同样的 acceptance 引用规则，但归为 `constraint_delta`。失败可以提高认知，
却不能对用户说成“完成进度”。

### 5.3 Applied path decision

`decision_applied` 是 runtime 保留 event type，公共 evidence append 入口不得直接伪造。只有
`apply_decision` / authorized interaction apply 内部生成的事件才可归为 `path_delta`，并满足其一：

- 非空 mutation 已落地，且能通过同一提交中的 trace refs / commit 关系确认；
- recommendation 为 `continue`，mutation 为空，但带有有效的 `continuation_authorization`，明确确认
  原路径继续。

- `decision_recommendation`：不是进度；
- `decision` 但没有 apply 证明：不是进度；
- decision apply 失败：不是进度；
- applied decision 没有改变 Mission state，也没有有效 continuation authorization：归为
  `unclassified_writeback`，audit 显示异常。

### 5.4 关键约束

以下 event type 默认归为 `constraint_delta`：

- `blocker`、`blocked`、`failure`、`interruption`、`stop_report`；
- `user_feedback`、`feedback`；
- `acceptance_failed`；
- `risk_context_update`、`risk_context_recovery`；
- 未应用的 `decision_recommendation`。

它们可以打断 #135 quiet，也必须进入用户状态更新，但放在“关键约束”而不是“可计推进”。

### 5.5 不自动升级的事件

`key_finding`、`state_transition`、`pulse_consumed`、普通 artifact ref、task outcome summary 和未知
event type 默认不算 progress。Agent 若认为 key finding 已满足 acceptance，应另写合格的
acceptance event；不要让派生器猜。

## 6. 只读 Outcome Attribution（runtime support）

新增纯派生模块：

```text
skills/tplan/scripts/outcome_attribution.py
```

输入：

- validated Mission snapshot；
- `evidence.jsonl`；
- `execution_trace.jsonl`（cost tree 使用；user update 可不传）。

Mission、evidence 与 trace 必须在同一 runtime lock 内读取，避免与并发 writer 交错形成半快照。
只读归因路径遇到 pending Mission transaction 时显式失败，不替 mutation-capable 命令执行恢复写盘。
生成 Markdown / SVG report 仍可写 `reports/`，但不得改 Mission、evidence、trace 或 Guard。

输出不落盘，建议结构：

```json
{
  "schema_version": "tplan.outcome_attribution.v0.1",
  "scope": {"kind": "task", "id": "T1"},
  "yield_class": "progress_and_constraint",
  "countable_progress": [
    {
      "kind": "acceptance_delta",
      "summary": "A1 passed in the target host.",
      "acceptance_ids": ["A1"],
      "evidence_ids": ["E12"],
      "commit_ids": ["Cabc123"]
    }
  ],
  "constraint_deltas": [],
  "state_writebacks": [],
  "unclassified_writebacks": [],
  "telemetry": {"span_count": 4, "cost_present": true},
  "warnings": []
}
```

`yield_class` 只用于展示，可取：

- `progress_and_constraint`；
- `countable_progress`；
- `constraint_delta`；
- `writeback_only`；
- `telemetry_only`；
- `no_activity`；
- `unclassified`。

数组字段和 source refs 才是可审计事实；`yield_class` 不是新的 Mission 状态。

### 6.1 Scope 归属

- 有 `task_id` 的 evidence 归到该节点，并向祖先和 Mission 汇总；
- trace lifecycle record 的 `task_id` 归到对应节点；
- Mission-level decision / status 写回归 Mission；
- shared / unattributed span 仍留在 overhead，不按比例分摊；
- 不根据时间邻近把一个 span 强行归因给某次 evidence。

### 6.2 Commit 关联

若 lifecycle records 共享 `commit_id`，且其 `refs.evidence_ids` 指向合格 evidence，则相关节点可以
显示该次状态写回“伴随”相应 outcome。

措辞必须是“该节点存在成本与可计推进写回”，不能说“这些 Token 产生了 E12”。当前数据没有这种
因果证明。

### 6.3 兼容读取

- 新的 qualified event 与 runtime-reserved event 使用严格校验；
- 历史合法但不完整的 evidence 不导致 renderer 崩溃；
- 历史事件只进入 `unclassified_writebacks` 和 audit warning；
- Mission schema 保持 `tplan.v0.1`；
- execution trace 保持 `tplan.execution_trace.v0.1`；
- execution cost tree report 升到 `tplan.execution_cost_tree.v0.6`。

## 7. 用户状态输出（mainline）

`render_user_update.py` 不再把所有 useful evidence 混在“已确认”下面。建议默认结构：

```text
当前目标：
...

当前状态：
...

可计推进：
- A1 已通过目标宿主验收。

关键约束：
- A2 仍失败，需要人工权限。

下一步：
...
```

规则：

- 只有 `countable_progress` 可进入“可计推进”；
- blocker、failed acceptance、feedback、stop 进入“关键约束”；
- key finding 可进入“已确认事实”，但不能混入可计推进；
- 仅有 Task status 或 artifact ref 时，写“状态已更新，暂无新的 acceptance / applied path evidence”；
- 仅有 telemetry 时，不生成进度叙事；
- 用户主动问进度时，即使没有 countable progress，也要诚实回答；
- #135 的 quiet/heartbeat cursor 和节奏保持不变。

心跳仍然只说“没有新的 Mission 或验收证据变化”，不因存在 telemetry 自动宣称推进。

## 8. Cost Tree 展示（mainline）

成本树保留所有现有成本字段，并新增独立的“产出归因”槽位。

### 8.1 Mission 汇总

示例：

```text
成本：LLM 2m14s / 脚本 48s / Token 18.2k
产出归因：2 项可计推进 · 1 项关键约束 · 3 个仅状态写回节点 · 4 个仅遥测节点
```

不得显示：

- “完成 67%”；
- “18.2k Token 兑换 2 个成果”；
- “平均每项推进 9.1k Token”；
- 没有事实口径的 ROI 好坏判断。

### 8.2 Node 卡片

Standard / Audit 每个已运行节点固定增加：

```text
产出归因：可计推进（acceptance A1）
```

或：

```text
产出归因：仅遥测，暂无 Mission/evidence 写回
```

或：

```text
产出归因：状态已写回，但没有可计推进 evidence
```

`compact` 只使用短标签：`推进`、`约束`、`仅写回`、`仅遥测`、`未分类`。

Audit 额外显示 evidence ids、commit ids、unclassified 原因和 compatibility warnings。

### 8.3 Completion 缺证据

Task 状态为 completed 但没有 qualified acceptance/path evidence 时：

- 状态仍显示 completed，不能篡改事实；
- outcome attribution 为 `writeback_only`；
- Standard / Audit 显示 `completion_without_progress_evidence`；
- user update 不得说 acceptance 已完成。

## 9. 写入与校验接口（runtime support）

不新增“progress counter”写命令。继续以 evidence 和 decision apply 作为语义载体。

在 `tplan_runtime.py` 增加：

```python
validate_evidence_event(mission, event, *, compatibility=False)
classify_evidence_outcome(mission, event)
```

职责：

- base event shape 校验；
- task id 与 acceptance ids 引用校验；
- qualified acceptance event 的严格要求；
- 新写入 fail closed；
- compatibility read 返回 warning，不伪造缺失字段。

`append_event()`、transactional prepared evidence 与相关 CLI 共用同一校验器，避免不同写入口口径漂移。

脚本不检查 acceptance 的真实语义；创建 `acceptance_passed` 仍是 Agent / reviewer 的判断责任。

## 10. 必须一起交付的实现集合（runtime support）

以下是一个完整改动，不拆成会产生半语义状态的 A/B 阶段：

1. `tplan_runtime.py`
   - evidence base/qualified 校验；
   - 新写入 fail closed，legacy read 有 warning。
   - 提供同锁、无恢复写盘的 Mission/evidence/trace attribution snapshot。
2. `outcome_attribution.py`
   - pure classification；
   - task / ancestor / Mission rollup；
   - commit/evidence 关联；
   - 无写入、无 sidecar。
3. `render_user_update.py`
   - 分开可计推进、关键约束、事实状态；
   - 保持 #135 delivery cursor 行为。
4. `execution_cost_tree.py`
   - report schema v0.6；
   - Mission / node attribution；
   - Standard、Audit、Compact、JSON、SVG 同步展示。
5. 文档与测试
   - `schema.md`、`execution-trace.md`、`user-output.md`；
   - evidence validator、归因器、用户输出和 cost tree 回归。

### 10.1 现有载体与真实缺口

| 设计需要 | 当前可复用 | 仍需实现 |
| --- | --- | --- |
| 成本事实 | span、usage、measurement source、task attribution | 无新采集 |
| 合法状态写回 | Mission transaction、lifecycle record、commit id | 归因器读取和分类 |
| acceptance 引用 | Mission acceptance ids、Task coverage、event payload | 集中校验与 legacy warning |
| path decision | recommendation、proposed mutations、decision_applied | reserved event 入口和 path 分类 |
| node rollup | Task/SubTask/Step parent tree | outcome 向祖先汇总 |
| 用户进度 | evidence summaries、当前 renderer | 按 progress / constraint / fact 分栏 |
| 成本树 | node direct/inclusive cost、refs、JSON/Markdown/SVG | outcome attribution 槽位 |

当前不缺新的事实数据库；缺的是一致的校验和读取口径。

## 11. 验收矩阵（mainline）

- [ ] 只有 model/tool/script spans：成本完整显示，归因为 `telemetry_only`，不出现进度声明；
- [ ] 只有 task-local log：不算 validated Mission writeback，不算进度；
- [ ] active node 切换：`state_writeback`，不算进度；
- [ ] Task completed 但无 qualified evidence：状态保留，出现缺证据 warning，不算进度；
- [ ] 只有 artifact ref：显示 artifact 写回，但不算 acceptance；
- [ ] 合法 `acceptance_passed` + A1：产生 `acceptance_delta`；字段完整的 legacy `acceptance` 保持兼容；
- [ ] 不存在的 acceptance id：新写入失败；legacy read 标未分类，不崩溃；
- [ ] `acceptance_failed`：进入关键约束，不算正向推进；
- [ ] `decision_recommendation`：不算 path progress；
- [ ] transactional `decision_applied` + mutation：产生 `path_delta`；
- [ ] `continue` + 空 mutation + 有效 continuation authorization：产生 `path_delta`；
- [ ] apply 失败，或空 mutation 且没有 continuation authorization：不产生 path delta；
- [ ] blocker / failure / stop / feedback：立即显示为关键约束；
- [ ] key finding 不会自动升级成 progress；
- [ ] 同一 commit 的 state + qualified evidence 可关联，但报告不声称成本因果；
- [ ] shared / unattributed cost 不会按比例硬分到 outcome；
- [ ] user update 只把 qualified outcome 放入“可计推进”；
- [ ] #135 两 quiet + 一 heartbeat 行为不回归；
- [ ] cost tree 所有 view 都保留真实成本，即使没有任何 writeback；
- [ ] renderer 不写 Mission、evidence、trace 或新的归因 sidecar；
- [ ] 不产生百分比、progress points 或伪精确 ROI。

## 12. 压力例（example）

### 12.1 高投入、零写回

Agent 调用模型 8 次、工具 12 次，最后没有 evidence 或状态写回。

- 成本：全部显示；
- 产出归因：`telemetry_only`；
- 用户状态：暂无新的可计推进；
- 不自动判定“浪费”，是否继续由 Mission Gate 判断。

### 12.2 文件已改、Task 已完成、没有 acceptance

- Task status：completed；
- artifact ref：可显示；
- 产出归因：`writeback_only`；
- warning：`completion_without_progress_evidence`；
- 用户状态：实现状态已更新，但暂无 acceptance evidence。

### 12.3 A1 通过，同时 A2 失败

- A1：`acceptance_delta`；
- A2：`constraint_delta`；
- yield class：`progress_and_constraint`；
- 用户同时看到推进与剩余约束，不会被单一“完成”叙事覆盖。

### 12.4 决策已建议但未应用

- evidence：decision recommendation；
- 归因：constraint / pending decision；
- path progress：无；
- apply 成功并出现对应 commit 后，才变为 `path_delta`。

## 13. Guardrails（guardrail）

- 归因器保护“高投入被写成高进展”的误用；它不能替代 acceptance judgment；
- strict evidence validation 保护伪引用；它不能验证 artifact 内容；
- completion warning 保护状态完成冒充 KR 完成；它不能自动撤销 completed 状态；
- cost/output 分栏保护用户理解；它不能计算真实业务 ROI；
- legacy warning 保护兼容性；它不能自动修复历史 evidence。

## 14. 不做与停止条件（boundary）

本 issue 不做：

- Token billing 或预算产品；
- reward feed、积分或绩效排名；
- span 到 outcome 的因果归因；
- 每个 span 人工验收；
- 新的常驻 scheduler / heartbeat；
- 持久化 progress ledger / sidecar；
- 把 artifact existence 当作 artifact correctness；
- 用工具次数、文件 diff 大小或耗时推断 Mission 价值；
- 自动根据历史投入决定继续或停止。

如果实施需要新建第二事实源、引入主观分数或修改 Mission schema，先停止并重审，而不是扩范围。

## 15. 交付与迁移（mainline）

- 新报告是 additive；Mission 与 trace schema 不迁移；
- execution cost tree JSON schema 升到 v0.6；
- 旧 evidence 保留原文，不重写；
- legacy 不完整事件只在 audit 报 warning；
- 新的 `acceptance_passed` / `acceptance_failed` 与 runtime-reserved evidence 开始执行严格引用和入口校验；
- legacy `acceptance` 不重写；字段不完整时不计推进并在 audit 提示迁移；
- 用户文案上线时必须与分类器同一提交，避免 UI 先承诺、runtime 后补。

## 16. 建议批阅结论（core）

```text
recommended_decision: close as implemented
reason: TPlan now distinguishes observed spend, legal writeback, and evidence-constrained progress; cost remains visible even when no outcome exists.
constraints: no progress score, no causal cost attribution, no new source of truth, no automatic semantic judgment, no overlap with #135 delivery pacing.
implementation_ready: yes; implementation and independent audits complete
```

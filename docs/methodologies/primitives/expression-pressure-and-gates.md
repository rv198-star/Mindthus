# Expression, Pressure, And Gate Primitives

This file holds smaller cross-cutting primitives that are real but not yet split into
one file each. Issue #83 tracks the later full split.

## Approximate Quantified Mapping / 非精准量化显影

Approximate Quantified Mapping is not a standalone method and not a new route. It is
an expression primitive for compressed qualitative or game-relationship claims, and it
can support judgment formation by making hidden variables visible.

It must not own the judgment: SELA, EDSP, 3L5S, WAE, TVG, or tplan keeps judgment
ownership.

SELA, EDSP, 3L5S, WAE, TVG, or tplan keeps judgment ownership.

Boundary: it can support judgment formation, but it must not own the judgment.

Use it only when the game relationship is complex enough. Good triggers include a
multi-variable trade-off, a 口径 conflict, a claim where the felt outcome flips across
participants, or a compressed verdict that hides variables, directions, dominant terms,
sensitivity points, and definition gaps.

It exposes variables, directions, dominant terms, sensitivity points, and definition gaps.

Skip it for simple, single-variable, low-stakes, or directly explainable claims. In
those cases, plain language is enough.

Short rule:

> 数字是假设，关系才是重点。

State that the numbers are assumptions. They are not factual measurements, not
evidence, and not a decision calculator. They only make the structure easier to see:
which variable moves, which term dominates, which nudge would flip the felt outcome,
and where the 口径 gap sits.

Inside another method, use it only as a clarity aid inside an existing judgment owner.
It may help that owner see the game relationship, but it cannot compute the owner's
conclusion.

Stop when the structure is visible. If the conversation turns into defending exact
digits, leave this primitive and return to fact gathering, Evidence / Claim Ceiling, or
口径 clarification.

## Pressure Surface Consolidation / 施压面收束

Pressure is not a standalone method and not a new route. It is a triggered challenge
inside an existing judgment owner.

Use pressure when a clean conclusion may be over-shaped by one perspective, hidden
incentive, game-theoretic reaction, weak evidence, downstream failure, or repeated
local repair.

Skip it for low-risk deterministic work where execution or mechanical verification
already gives the answer.

When pressure is used, name the owner and the reason:

- Perspective Pressure belongs to `SELA` / `EDSP`.
- Proof pressure belongs to `Evidence / Claim Ceiling`.
- Artifact-value pressure belongs to `TVG`.
- Repeated-repair pressure belongs to `Anti-Spiral`.

Pressure is not a standalone route; low-risk deterministic work should stay direct.

## Gate Probes / 冻结前定位自省

Gate Probes 不是独立方法，不是新 skill，也不是 Gate 本身。它是 agent 在关键动作前做的一次短定位：
准备交付、冻结、继续一轮、转交、阻断或停止时，先确认自己没有跑偏。

Short rule:

> 别急着交付，先确认自己还站在正确的位置上。

任务落地版三问：

1. 这是什么：当前产物或动作承担什么责任？
2. 它在哪里：证据、边界、风险、误用信号和目标差距现在是什么状态？
3. 它去哪里：接下来服务谁的决策、执行、审查、交接、生成或继续迭代？

Gate Probes 可以改变下一步：`freeze`、`return-remediate`、`block`、`stop`、转交，或请求用户授权。

It cannot replace evidence, user authority, method-specific Gates, TVG exit judgment,
or tplan continuation authorization.

## Failure Smells / 误用信号

Failure smells / 误用信号 remind the agent that an answer, method run, task state, or
artifact may look complete while failing to do the real work. It is not another method
and not automatically a hard veto.

Three levels:

- 普通信号：暂停、自审、返修、换方法，或降低 claim。
- 方法 / profile veto：当前方法、profile 或产物不能 freeze，必须先修。
- 硬 veto：证据不诚实、用户约束冲突、安全边界、权限越界或 claim ceiling 过高，必须 block 或 stop。

Every failure smell must create execution impact. If it changes no strategy, evidence
requirement, next action, stopping condition, method route, or handoff information, it
is only commentary and should not be in the checklist.

## 方法误用信号索引

| 方法 | 误用信号和行动影响 |
|---|---|
| `using-mindthus` / 路由 | 简单明确的事被包装成方法语言 -> 回到直接执行。缺事实却用方法补洞 -> 先补证据或问用户。多个方法堆叠但没人负责主判断 -> 先选 dominate / defer / degrade / block / stop。答案说了方法名却不改变行动 -> 收紧路由或跳过 Mindthus。 |
| `3L5S` | 问题仍不能被复述、定位或证伪 -> 回到 Discovery / Definition。直接从现象跳到方案 -> 分开 signal、problem 和 action。BTGSB 变成任务列表但没有验收证据 -> 补 Target、Gap 和 verification。子任务全是“优化 / 研究 / 处理” -> 先对该子任务再跑 BTGSB。 |
| `EDSP` | 坐标系漂亮但变量重叠 -> 重建维度。极端只是普通情况的加强版 -> 继续推极端，直到结果能清楚塌缩。结构未稳就开始 Scenario Projection -> 停下 SP，重建 ED。结论很聪明但不改变选择、边界或证据要求 -> 视为 EDSP 失败。 |
| `SELA` | 用局部优秀证明长期可守 -> 检查可规模化能力和系统反馈环。把系统效率写成“效率一定赢” -> 恢复硬价值边界和时机判断。长期方向直接变成立刻行动 -> 先做 Timing Check。忽略过渡价值或不可逆伤害 -> 降级或阻断 SELA 结论。 |
| `MPG` | 主线没有行动者、载体、暴露或期限 -> 先限定主线。路径风险清单不改变姿态、预算、载体或触发条件 -> 重建主线承载方案。把“长期正确”当成“现在可以重仓” -> 设暴露预算和触发条件。把对抗力量当坏人 -> 重新当作塑形路径的信息来映射。 |
| `WAE` | 脚本、schema 或 checklist 在判断语义真相 -> 把判断权还给 agent / 人，脚本只做 shape。workflow 控制了 truth-uncertain 对象 -> 转给 agentic judgment + evidence。证据只是字段，没有约束 claim -> 绑定 claim 或降级。agentic judgment 扩张到确定性杂活 -> 交回 workflow。 |
| `TVG` | 产物更长但没有更有用 -> 围绕 value axes 收束或返修。下一轮没有明确正价值假设 -> 停止或带 warning freeze。缺事实却用流畅文字填空 -> 硬 veto，补证据或降低 claim ceiling。profile 成功和 runtime 救场混在一起 -> 记录 claim ceiling 和残留失败模式。 |
| `tplan` | Task/SubTask/Step 已经说不清如何服务 Mission -> 做 alignment 或 Mission Review。logs 很多但 evidence 不约束验收 -> 补 evidence 或降级进展。继续同路径靠“花了很多时间 / 快好了”辩护 -> 要 continuation authorization。共享风险存在但不影响后续选择 -> 上浮 scoped risk，或留在本地。 |

具体措辞可以随方法变化，但行动影响不能省。只让输出显得更懂方法、却不改变下一步的
“误用信号”，应该删掉。

## Examples

### 案例 A：TVG 想继续加深第三轮

一份交接文档已经加深两轮，第三轮只是准备再加 checklist。这里不需要在 TVG 内重写
反螺旋规则，只触发 `Anti-Spiral`，回到上游目标或做等量替换。

### 案例 B：SELA 判断里出现真实利益冲突

SELA 负责整体效率与局部优势判断。如果销售、法务、实施、财务各自会因结论不同而受益
或受损，不要在 SELA 里复制一套博弈论方法；触发 `Perspective Pressure`，用激励检查
挑战单一视角。

### 案例 C：一句“年轻人没机会了”压扁了博弈结构

这句话可能同时混着成功概率、成功收益、失败代价、入场成本、参照系和方差。这里不要
新开一个独立 skill，也不要假装有真实数据。只用假设数字说明：也许上限更高，但失败
代价、参照物和方差一起变大，所以同一个局面对不同人有完全不同的体感。

正确输出是变量关系和口径差，不是“算出今天更好/更差”。

# Anti-Spiral Self-Audit / 反螺旋自检

Anti-Spiral Self-Audit is a methodology resource, not an independent Mindthus skill. It can be invoked directly in ordinary work, and `tplan` can absorb it as a runtime gate.

## 这是什么

Anti-Spiral 是一套反螺旋执行纪律，用来阻止 agent 把局部修补误认为目标推进。

长任务里最危险的状态，往往不是完全停住，而是一直在动：改同一段 prompt、同一个文件、同一个参数、同一个任务节点；每次都像是在变好，但 Mission 没有更接近完成。局部对象被不断优化，整体目标却被吞掉，这就是 Mindthus 所说的死亡螺旋。

Anti-Spiral 的短规则是：

> Third touch, stop first.

同一个局部对象第三次被处理时，先停下来审计，而不是继续补丁。

## 解决什么问题

Anti-Spiral 解决的是“继续做看起来像进展，但实际上已经丢失目标函数”的执行失败。

典型形式包括：

- 一直优化某个段落、prompt、参数、文件或任务节点，Mission 本身不再推进。
- 上一层效果不好，于是继续加 fallback、规则、特殊分支或新阶段。
- 依赖主观感觉、LLM 自评分、vibe 或“看起来更好”决定再跑一轮。
- 修下游输出症状，而不是回到上游定义、目标或证据约束。
- 因为已经投入很多，所以继续沿当前路径投入更多。

这个方法不证明当前路径一定错。它只是说：当可观察行为已经呈现局部循环，继续之前必须先证明自己没有偏离目标。

## 核心判断

Anti-Spiral 的核心判断是：局部改动次数、加层冲动和弱证据反馈，是目标函数丢失的早期信号。

触发条件包括：

- `count trigger`：长任务中每 5-10 个有意义动作做一次轻量检查。
- `repeat trigger`：同一文件、prompt 段、参数、任务节点或局部对象被第三次处理。
- `feedback trigger`：用户反馈说还不够好、要再试一次，或结果变差。
- `layer trigger`：下一步想新增函数、文件、阶段、规则、fallback 或特殊分支。
- `evidence trigger`：同一路径继续行动很难产生新的 decision-constraining evidence。

如果触发后仍然继续局部加层，agent 很可能是在用动作感替代进展。

## 怎么用

触发后，先回答五个 yes/no 问题。只看可观察 trace，不看自我感觉。

| # | 问题 | 可观察 trace |
|---|---|---|
| Q1 | 上一步是否新增了结构层？ | diff 主要是新增，或出现新文件、函数、阶段、规则。 |
| Q2 | 这是同一局部对象第三次或更多次修改吗？ | 行动历史显示同一对象被反复触碰。 |
| Q3 | 质量信号是否主观或概率化？ | 依赖 LLM 评分、vibe、“看起来更好”、自评，而不是 boolean/integer/mechanical check。 |
| Q4 | 下一步修的是下游输出，而不是上游原因吗？ | 修复点靠近数据流、推理流或交付物末端。 |
| Q5 | 如果删掉上一层，系统是否损失很小或更清楚？ | 删除后回到最近稳定状态，或移除未证明的层。 |

解释规则：

- `0-1 yes`：可以继续，但保持观察。
- `2 yes`：黄色；下一步必须做减法或等量替换。
- `3+ yes`：红色；停止当前路径，进入退出协议。
- `Q3 yes`：单独视为红色一轮，因为自评分不是稳定 continuation signal。

红色时只允许两类修复：

1. 修改已有 prompt、参数、规则、任务或步骤。
2. 删除已有层、规则、分支、任务或处理阶段。

禁止继续新增 fallback、特殊分支或再开一层。

## 常见误用

第一种误用，是把 Anti-Spiral 当成“不能细改”。这不对。它反对的不是精修，而是没有新证据、没有上游回看、只靠局部动作延续的循环。

第二种误用，是用主观感觉证明可以继续。越是在局部反复时，越不能用“这次感觉更好”作为继续理由。

第三种误用，是触发后又新增一套更复杂的审计结构。Anti-Spiral 的目的正是阻止加层冲动，不应该变成新的加层借口。

## 边界

Anti-Spiral 不替代正常调试。明确的 failing test、明确的报错、明确的机械验证失败，可以继续沿因果链修复。

它也不要求每个小任务都审计。触发条件是长任务、重复局部对象、负反馈、加层冲动或证据增量不足。

当红色触发时，优先回到上游：重述 root problem，找到最近稳定状态，做减法或等量替换，然后只跑一次机械验证和一次真实反馈面。

## 与其他方法的关系

- `3L5S` 帮助从局部症状回到 signal、problem 和 action。
- `WAE` 解释为什么 agentic judgment 必须被 workflow 和 evidence gate 约束。
- `tplan` 可以从 step logs、object touch count、feedback 和 evidence delta 中触发 Anti-Spiral runtime gate。
- `TVG` 可以在路径稳定后加深 bounded artifact，但不能成为继续局部打磨的理由。

## 导航

- 返回 [README](../../README.md)
- 查看 [tplan 方法页](tplan.md)

# Mindthus Cognitive Primitives / 认知原语

## 这是什么

Cognitive Primitives / 认知原语，是 Mindthus 方法论之外的小而关键的判断碎片。
它们通过横切方式介入不同方法，为主方法提供刹车、施压、证据上限、表达降噪或
过度方法化控制。

This is not a new method layer. 它不是第七个方法，也不是总入口；它只是把重复出现的
小型 guardrail 集中成一个 Cognitive Primitive Index / 认知原语索引，供 `AGENTS.md`、
`using-mindthus` 和各 skill 引用。

## 解决什么问题

如果每个 skill 都把同一套刹车、证据上限、表达纪律重新写一遍，项目会有三个问题：

- 同一规则出现多个名字；
- guardrail 慢慢变成新的主方法；
- 修改一处边界时，其他 skill 还停在旧口径。

Use cognitive primitives by reference. 本页负责定义短规则；具体方法只写“何时触发”，
不要复制完整定义。

## 核心判断

认知原语必须同时满足三点：

- 多个方法都会用到；
- 只保护主方法，不替代主方法；
- 足够小，不值得变成独立 skill。

Do not copy the full definition into each skill. 如果某个规则需要长流程、独立产物或
完整运行时，它就不是认知原语。

## 怎么用

## Cognitive Primitive Index / 认知原语索引

| Primitive | Primary owner | Short rule |
|---|---|---|
| Minimal Sufficient Lens | `using-mindthus` | 能直接判断就不要开方法；一个 skill 足够就不要串联；轻量检查足够就不要展开完整流程。 |
| Evidence / Claim Ceiling | `WAE` | 结论强度不能超过证据；缺事实、领域输入、运行证明或 stakeholder 判断时，降级或阻断。 |
| Perspective Pressure | `SELA` / `EDSP` | 单一视角过度自洽时，用角色压力或激励检查挑战判断。 |
| Anti-Spiral | `anti-spiral-self-audit` / `tplan` | 同一局部对象第三次、负反馈或加层冲动出现时，先停下回看上游。 |
| No Abstract Jargon Wall | `AGENTS.md` | 先用例子、类比或直接后果讲清楚，再使用 Mindthus 术语。 |
| Approximate Quantified Mapping / 非精准量化显影 | `AGENTS.md` / `using-mindthus` | 数字是假设，关系才是重点；用假设数字显影变量、方向、主导项、敏感项和口径差，不用数字证明或计算结论。 |

### Approximate Quantified Mapping / 非精准量化显影

Approximate Quantified Mapping is not a standalone method and not a new route. It is an
expression primitive for compressed qualitative or game-relationship claims, and it
can support judgment formation by making hidden variables visible. It must not own the
judgment: SELA, EDSP, 3L5S, WAE, TVG, or tplan keeps judgment ownership.

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

### Pressure Surface Consolidation / 施压面收束

Pressure is not a standalone method and not a new route. It is a triggered challenge
inside an existing judgment owner.

Use pressure when a clean conclusion may be over-shaped by one perspective, hidden
incentive, game-theoretic reaction, weak evidence, downstream failure, or repeated local
repair. Skip it for low-risk deterministic work where execution or mechanical
verification already gives the answer.

When pressure is used, name the owner and the reason: Perspective Pressure belongs to
`SELA` / `EDSP`, proof pressure belongs to `Evidence / Claim Ceiling`, artifact-value
pressure belongs to `TVG`, and repeated-repair pressure belongs to `Anti-Spiral`.

## 具体案例

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

## 常见误用

第一种误用，是把认知原语当成新流程。它只在信号出现时触发。

第二种误用，是在各 skill 里复制本页定义。这样会重新制造重复。

第三种误用，是让原语决定主问题。原语只刹车、施压或限制 claim，主判断仍归对应 skill。

第四种误用，是把非精准量化显影升级成精确模型。数字只是让博弈关系可见；一旦开始
防守具体数字，原语已经失效。

## 边界

认知原语不替代 `SELA`、`3L5S`、`EDSP`、`WAE`、`TVG` 或 `tplan`。

它也不替代事实、领域研究、运行证明或用户判断。遇到缺输入的问题，正确动作通常是
补输入、降级结论或停止，而不是新增方法层。

## 与其他方法的关系

- `using-mindthus` 引用本页来避免入口 skill 变厚。
- `AGENTS.md` 引用本页来保持默认姿态短。
- 各方法页只保留与本方法相关的触发条件。

## 导航

- 返回 [README](../../README.md)
- 查看 [Using Mindthus skill](../../skills/using-mindthus/SKILL.md)
- 查看 [Anti-Spiral 方法页](anti-spiral-self-audit.md)

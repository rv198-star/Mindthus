> 最新控制权设计与一次独立评审见 [route-control-v0.2](../route-control-v0.2/README.md)。本目录为继承的题文和历史政策；有效消费以新profile及v0.2.1实现澄清为准，未启用运行。

# using-mindthus 主线路由：问题合同与验收设计 v0.1

> 后续审计：见 [实用性独立审计与作者处置](pragmatic-audit-20260923/disposition.md)。
> 被审v0.1原文保留。实施应收缩默认检查面，保留三类型与多方法必要职责；低风险试用不以前置统计非劣为门槛。
> 这是审计后的建议，不是已实现的新profile，也不代表业务实测通过。

**本次完成：可逐题审查的设计候选与离线结构校验。未实施后继路由、未开始新实测、未作独立模型审计或默认采用。**

目标：先认清当前未决判断，再决定哪些方法分别主导、支持或约束，以及产物怎样接力；不把全任务压成一个方法名。

## 阅读入口

| 需要了解什么 | 文件 |
|---|---|
| 整体设计、State、执行/预算与边界 | [design.md](design.md) |
| 全部19题的中文题文、类型、选项、消费和反例 | [question-catalog.md](question-catalog.md) |
| 可机器读取的问题模板 | [questions.json](questions.json) |
| 8方法入口绑定、反例及SELA/MPG伴随来源 | [method-bindings.json](method-bindings.json) |
| 跨题确定性消费、参数候选及共享容量 | [policy.json](policy.json) |
| 验收、开发/校准/封存对比和调优机制 | [evaluation.md](evaluation.md) |
| 24个开发验收条目、反例与允许路径性质 | [acceptance.json](acceptance.json) |
| 版本/归因/迭代上限与数据暴露规则 | [iteration-policy.json](iteration-policy.json) |
| 3个走通示例（不是模型观测） | [worked-examples.md](worked-examples.md) |
| 来源绑定及作者一致性检查 | [source-index.json](source-index.json)、[author-review.md](author-review.md) |
| 结构验证结果及可重跑检查器 | [verification.json](verification.json)、[validate_design.py](validate_design.py) |
| 由合同节点生成的前向依赖图源 | [dag.json](dag.json)、[dag.mmd](dag.mmd) |

## 问题库存

G01–G05：入口/表示/事项/义务/点名意图；M01–M05：候选/适用/贡献/缺口/伴随；R01–R04：复用/职责重叠/主导/依赖；S01–S02：影响可评性与程度；V01–V03：覆盖/冗余/越权。

共6个Noul、12个Choice、1个Score模板。模板按对象实例化，不是每轮必问19题。比如M02按8份正式方法合同分别绑定，而不是八种不同的手写关键词规则。复杂协作中三类型均承担独立用途；简单明确任务仍直接执行。

## 迭代方向

先静态合同和故障控制，再真实DEV定位机制，CAL只选政策参数，最后独立LOCKED任务对比。方法名匹配不是最终指标；终局质量、必要判断覆盖、实际读取/执行、弃权/误伤和完整成本一起判断。

一轮失败不代表停止研发：普通内部问题自行归因修复，旧批次不可改写，下一候选另冻结再测。改变题义后不能沿用已暴露校准/保留集的独立资格。达到研发上限先内部减法/anti-spiral，不机械逐细节找Owner批准。

本目录不是旧D4已经完成的新名称；它是恢复C01完整路由目标后的MR-01设计。MR-02实现/独立审计、MR-03开发与校准、MR-04封存比较仍待执行。已有Skills/4K D3成功与历史失败均保留，#211继续OPEN，原模式及main不变。

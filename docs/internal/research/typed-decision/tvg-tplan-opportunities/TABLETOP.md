# 一次 TVG Profile 离线演练：便宜判断怎样增加昂贵调用

2026-10-02。阅读基线 `d256203b623b344ecc5281d0a6b82b7c73276529`。
用户授权离线模拟，重点检查 Jev 引入后是否反而增加宿主调用和流程复杂性。
本轮真实 Jev/LLM 调用 **0**；没有读取凭据、启动宿主 CLI、写入真实 journal 或改旧合同。

**演练结论：Jev 便宜不能推出完整路径便宜。原 Agent 一次就能判断并改稿时，
最紧凑的 Jev 接法只保住原来的一次 LLM；释义、仲裁、退出交接若各自唤起新 LLM，
或误报触发无用改稿，就会多出一次甚至更多宿主工作。**

## 场景与来源

对象：一段内部草拟的 TVG 简介。采用现有
[Plain Sharp Profile](../../../../../skills/tvg/resources/value-profiles/plain-sharp-skill-intro.md)，
目标是首次读者能理解实际用途与边界。仅作低风险草稿处理，不作方法发布或外部验收。

有缺口的合成原稿：

> TVG帮助全面、系统地优化任何问题，并自动判断最终结果是否正确。

手工准备的模拟修稿，也作为“原稿已足够”的反向输入：

> TVG把看似完整却不好用的产物，改到能支撑实际判断和行动。比如一份计划只有步骤，没有取舍理由，就补上理由和边界。它不替你验证事实，也不接管整项战略。

这两段及以下判断全部是**公开手工夹具**，不声称真实模型产物或独立规范真值。
模拟最终稿相同是控制假设，不能据此证明实际非劣、好稿、Jev有效或两臂能力相同。

实际执行的 [小回放脚本](simulate_call_boundaries.py)使用旧
[c02.plan / recheck](../../../../../experiments/typed_decision/c02.py)消费逻辑和现有
[v2题目合同](../review-remediation/c02-contract-v2.json)：

- 注入 utility/support/action，验证真实消费规则是否提出候选或返回原 owner。
- 部分分支注入成品复查结果，验证仍返回原 owner、`exit_state=null`。
- 原 Agent 与宿主处理节点只代表明确列出的拟议调用，不创建实际发送意向。
- 所有原始注入值、问题文本、State、模拟文本与节点保存在 [轨迹](tabletop-trace.json)。

这是对接法的演练，不是完整 C02 调度测试或修改冻结 C02 规范。
紧凑分支只回放 plan，另行假设低风险宿主在同一次请求中完成修改和自身责任检查；
它不宣称执行了 C02 的既定成品 recheck。完整图中已要求的步骤不能据此静默删除。

## 九种分支，哪些调用是新增的

比较起点是一份已存在的稿子，初始生成成本两边共同、不从 Jev 路径扣除。
“LLM”指一次新宿主模型请求；当前 Agent 消费交接仍有上下文/处理成本，不称免费。

| 回放 | 明确列出的调用顺序 | 模拟 LLM / Jev | 相对一次原 Agent 的风险 |
| --- | --- | --- | --- |
| 原 Agent，稿子有缺口 | 一次检查、改稿并内联自检 | 1 / 0 | 真实基线，允许一次合并完成 |
| Jev紧凑接法 | Jev判断 → 宿主读完整材料、修改并内联自检 | 1 / 1 | LLM未减少，多一次Jev往返 |
| 额外释义者 | Jev判断 → LLM解释结果/写修改计划 → LLM改稿 | 2 / 1 | **释义调用是净新增**，执行者本可直接消费结果 |
| 把退出交接单独唤起 | Jev判断 → LLM改稿 → Jev复查 → LLM责任者判断 | 2 / 2 | 若原路径没有这次独立审查，就净新增宿主；若原路径必须有，两边都须计入 |
| 原 Agent，稿子已足够 | 一次检查并保留 | 1 / 0 | 不强制润色 |
| Jev判足够，仍唤起owner | Jev判leave_unchanged → LLM原责任者检查 | 1 / 1 | **没有省掉检查**；返回owner不等于无需owner判断 |
| Jev语义未决，直接回原路径 | Jev判断未决 → 原Agent一次检查并处理 | 1 / 1 | 不多造仲裁轮，但Jev开销已发生 |
| Jev语义未决，单独仲裁 | Jev未决 → LLM先解题/定方案 → LLM处理 | 2 / 1 | **把回退拆成两次宿主调用** |
| Jev误报，改出无依据保证 | Jev误报 → LLM无用改稿 → Jev复查违例 → LLM否决并返回原稿 | 2 / 2 | 最终可恢复，但已经支付无用改稿与额外责任者处理 |

最后一项是刻意注入的反例：原文已足够，却给 deficit+explain_tradeoff；
模拟改稿增添“保证每次修改都提高质量”，复查给 violation。
真实消费代码不会仅凭三问相容就知道它们误判了，所以仍会提出改稿候选。
没有发生第二次自动改稿；原责任者的模拟动作是否决并返回原稿。
这不是本轮 Jev/宿主真实错误率，也不是重新计旧实验分数。

## 回放证据

执行入口（仓库根目录，使用可用的 Python 3）：

```bash
python3 docs/internal/research/typed-decision/tvg-tplan-opportunities/simulate_call_boundaries.py \
  --output /tmp/mindthus-tvg-tabletop.json
```

本次使用已有 bundled Python 运行，9个分支的调用数和手工文本一致性检查通过。
终端输出摘录：

```text
OFFLINE ONLY: actual_model_calls=0; injected variants=9
gap_native: planned LLM=1 Jev=0 serial_edges=0
gap_jev_inline_owner: planned LLM=1 Jev=1 serial_edges=1
gap_jev_extra_interpreter: planned LLM=2 Jev=1 serial_edges=2
gap_jev_separate_owner: planned LLM=2 Jev=2 serial_edges=3
adequate_native: planned LLM=1 Jev=0 serial_edges=0
adequate_jev_owner_wakeup: planned LLM=1 Jev=1 serial_edges=1
gap_jev_unclear_direct_fallback: planned LLM=1 Jev=1 serial_edges=1
gap_jev_unclear_extra_resolver: planned LLM=2 Jev=1 serial_edges=2
adequate_jev_false_positive: planned LLM=2 Jev=2 serial_edges=3
9 variants passed call-count/output checks; injected text equality is not quality verification.
```

`serial_edges` 是模拟有序调用之间的连接数，不是实测秒数。
金额、token、模型处理时间全部 unknown；没有用假设价格或时长计算收益。
模型调用次数翻倍也不能直接写成金额翻倍：单次上下文、缓存、输出长度都可能不同。
现有实验若按每次明确结束后的60秒调度，多出来的调用还会增加冷却边界；
本次没有真实等待，没有更改或解除该协议。

## 识别出的设计风险及处理建议

1. **把类型化结果再翻译一遍。** 已给出具名关系、依据与允许动作时，让修改宿主在同一次
   请求里消费；不要例行增加一个“解读Jev”的 LLM。只有真实缺新候选/复杂判断，才由原 owner处理。
2. **把责任归属当新调用。** C02 返回原 owner 是职责要求，不自动要求一个全新模型请求。
   同时，跨越了新稿复查后返回的边界也不能假装已结束的旧调用还在执行。
   是否增加调用必须按宿主实际时序记录，不能靠改计数名称隐藏。
3. **把未决变成双重解题。** 语义未决可直接返回原 Agent 的普通一次处理；
   不先让 LLM重做判断，再唤起另一个 LLM改稿。传输unknown不是这里的语义未决，仍按原停止规则。
4. **只算正确触发，不算误报和遗漏。** 误报会支付无用改稿/否决；漏检若仍由必要审查发现，
   Jev没省掉该审查，若不再审查则可能交出有缺口的成品。二者都要按完整路径观察。
5. **取消必须审查来伪造省调用。** 若独立退出审查确实要求一次LLM，原Agent和Jev两边都加该次；
   低风险一次合并基线与高风险独立审查路径不能直接作配对收益。

对 TPlan 同理：Jev提示“可能偏离目标”后，若再新唤起LLM解释提示，再唤起LLM继续执行，
就新增一次宿主。只有替代原本已存在的可替代独立语义检查，或准确避免后面的无效动作，
才有结构上的节省机会。把每一步都变成 Jev + 完整 Mission Review 会扩大治理，不能默认采用。

## 对下一步建议的收窄

先只保留“固定 Profile → 一次 Jev 检查 → 同一次原宿主处理”的候选接法，
并与正常原 Agent 一次处理对照；保持必要复查/审查责任，两边公平计入。
它目前的模拟计数 **1 LLM + 1 Jev 对 1 LLM**，不是成本优化的已证实路径。

只有真实观察到少返工、少唤起宿主或重要质量改善，才值得保留。
若效果相同、LLM负担也没有下降，就没有理由仅因为Jev便宜而增加这个环节。
需要例行新增释义/仲裁 LLM 的接法，暂不进入真实验证；例外是否值得须有具体任务理由。

本次仅新增模拟脚本、模拟轨迹和说明。TVG/Profile、TPlan、旧 C02、旧 GJ/R2、main/default Skill、
模型预算和unknown记录保持；没有获得新模型资格或后续真实调用授权。

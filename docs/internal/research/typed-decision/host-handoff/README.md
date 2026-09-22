# C01 宿主交接：从路由字段到可消费的输入

当前交付是一个准备入口：`python3.12 -m experiments.typed_decision.handoff`。
它复用已有决策结果，输出任务、处理分支、保留义务以及选中方法的完整合同。
不调用模型，不启动宿主，不修改全局 skill/hook，也不声称方法已执行。

## 使用与行为

```sh
python3.12 -m experiments.typed_decision.handoff \
  --trial /absolute/path/to/case-trial \
  --run-id ORIGINAL_RUN_SHA256 \
  --context /absolute/path/to/exact-context.json \
  --method-root /absolute/path/to/matching-method-snapshot \
  --output /absolute/path/to/new-handoff.json
```

`context` 是当初传给 C01 的完整输入对象，不是包含 gold 的案例包装。
调用方负责提供当前有效输入；`freshness=current` 只是显式断言，并非时间有效性的证明。
`method-root` 必须提供当时的完整入口/方法版本；英文 derived contract 与中文版不能
因名称一样而互换。本轮复用既有完整英文副本，没有声称实现了在线翻译层。
输出沿用不可变 JSON 包装与内容摘要，已存在的输出不会覆盖。

| 分支 | 给宿主的任务 |
| --- | --- |
| intervene | 带上所选完整方法合同，开始处理任务 |
| direct_execute | 按原任务约束直接处理 |
| acquire_information | 先取得或询问具体缺失事实 |
| llm_fallback | 交回原 Agent，保留所有未解决义务和原因 |
| original_path | 交回原 Agent，先处理输入/权限/时效问题 |

已有运行的输入摘要、policy、调用顺序、问题、State、结果和 Resolved Runtime 锁均需
对应。读取期间使用现有日志共享锁；写入中的试验立即拒绝交接，不等待或修改日志。
代码从已记录答案重新组合 C01，确认当前图和完整方法摘要仍产生同一个结果。
缺失/变更的证据不能被 C01 捕获后伪装成正常 fallback；校验失败只给 blocked 结果。
模型原始回答保持在原日志，交接使用有效处理分支。无置信度授予权限。

这是历史结果的只读交接，不是重新开放旧推理 Session。历史 implementation 身份保留；
当前 graph/问题/State/结果必须逐项重现。增加交接模块改变实验包的总源码摘要，因此
旧 live carrier 的整包 freeze 不再匹配当前 checkout，也更不能直接复跑旧试验。
旧 JSON 摘要只能检测损坏，不能抵御有权重签整个日志的攻击者。

宿主在另行准入的受控试验里应消费一次处理分支，而不是逐节点重判；真实权限和
安全规则仍由宿主持有。交接文件始终标记 consumption=not_executed、
native_skill_load=not_observed、task_acceptance=not_evaluated。后续宿主必须另外留下
实际执行证据；现有 offline 文件读取探针没有被放宽成 live 执行许可。

## 本轮复核

复用 graph4 那一轮的14个案例，全部交接成功，新增推理0次、语义修订0次。
4个方法介入、1个直接处理、1个补信息、7个回退、1个D0返回原路径。
N03仍为 llm_fallback，保留 unresolved_entry_obligation；没有改判、删掉义务或重新问Jev。
[逐项记录](replay.json)用于复核交接，不是新的14题语义通过率。

边界测试包括：所有出口、完整方法内容、义务及显式约束保留、输入/合同变化、缺失结果、
运行时身份不匹配、活跃写入、重签最终owner也不能覆盖原始调用证据，以及准备过程不修改旧日志。
全仓结果见[验证](verification.json)。

## 下一步宿主试用

更新：用户已提供CPA渠道，首选DeepSeek、备用GLM；首轮chat消费试用见
[结果](../host-trial/disposition.md)。下文保留接入设计边界。OpenRouter仍只能调用Jev，
历史Sonnet凭据不构成新的调用许可。

确认渠道后先做小规模宿主交接试用，核实实际方法上下文被消费、缺信息时会询问、
回退可以继续完成任务。预先固定模型、版本、权限、数据、最大调用数/时间/成本、
答案评价标准和重试规则，再启动模型。使用已有题的交接试用只能证明这条路径是否
工作，不能替代独立holdout；也不能把重放的Jev耗时拼进同期A/C成本比较。

正式原版A需真实原Mindthus宿主配置，C需同一宿主仅替换路由决定。共享下游工具、
权限与评价口径；外层指令和版本差异必须记录。评价最终任务完成、错误方法、无必要
阻断、补问/返工次数和全流程成本，保留译文准备与缺失成本。不能以新提示词模仿A，
也不能把完整原路由永久放在Jev后面重复执行，再声称省掉了它。

本次只补已有C01消费缺口；没有通用调度平台、自动设计器、提示词新一轮调优或C02扩建。
#211保持未验收，main不变，graph4的13/14定点结果不因工程接入而升级。

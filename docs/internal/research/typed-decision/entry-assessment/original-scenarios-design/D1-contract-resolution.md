# Relationship D1：快速审计处置与首个离线实现

## 当前有效合同与审计边界

本轮授权顺序为：完善原始Skills/4K合同与验收 → 一轮快速独立验收 → 启动开发。
快速审计实际请求绑定design-v0.3、relationship-contracts-v0.3、acceptance-v0.3及准确来源片段。单次CPA deepseek-v4.1-flash返回 **REVISE / offline_d1_admitted=true**。原文和请求在quick-audit-v03/，freeze保持原样。没有追加审计、换模型或把REVISE改写为PASS。

实施采用 **design-v0.3 + 本文明确处置 + relationship-contracts-v0.3.1 + acceptance-v0.3**。0.3.1是作者依审计建议作的局部确定化，不是另一次模型通过结论。旧v0.1/v0.2和四份旧审计不改。已有quick-audit-v03-freeze本来已绑定全部请求身份，不能因审计者没看到carrier就声称之前没有绑定。

## 本轮审计项如何落到可验证规则

| 项 | 处置 | 对应离线控制 |
|---|---|---|
| B1 范围接受与frame对齐的合成冲突 | 保留两项独立结果；不根据preserved自动改变Q2同批输入，也不合成冲突。Q2仍独立触发范围修正。 | scope_acceptance_does_not_overrule_independent_alignment |
| B2 共同关系缺失/未知 | 只有joint_account_missing产生explain_joint_relation；unresolved返回原owner且无Plan。 | joint_unresolved_returns_without_a_plan / missing_joint_account_requests_only_named_repair |
| B3 字节计量 | input_bytes=len(canonical(完整packet))；projected_request_bytes=len(canonical({state, questions}))。D1可以精确验证这些字节；HTTP wire/token窗口仍在D3验证，不把两者混合。 | exact_byte_metrics_and_overflow |
| F1 来源记录身份 | 观测必须来自source；candidate不能充当source_observation或明示用户范围。语义保真仍由模型和后续端到端评价，不因引用合法而自动成立。 | source_observation_cannot_be_candidate_self_evidence / explicit_frame_cannot_claim_candidate_as_user_source |
| F2 共同关系前置条件 | JSON记录选中frame、candidate存在、两个supported driver前提；consumer按支持和角色逐项验证。 | support_unknown_does_not_consume_speculative_role |
| F3 审计identity | 原freeze保存被审文件hash和request hash；作者修订另用0.3.1文件，原输入不改。 | quick_audit_v03.py的manifest检查及归档字节核对 |
| F4 行范围与码点 | canonical source以UTF-8无归一化decode、splitlines(keepends=True)、1基闭区间选行；packet引用独立使用Unicode码点0基半开区间。无需隐式转换。 | unicode_quote_and_stale_or_shifted_refs / canonical_source_and_contract_mutation_rejected |
| F5 来源反证结果 | source_contradicted返回原owner；not_established令角色推测题不消费，原值保留。 | source_contradiction_returns_owner / support_unknown_does_not_consume_speculative_role |

修正项不把“模型可能错”解决成再加一层模型，也不把简单解释、多个事实或后置主句预设成错误。快速审计中的具体修法是建议，不覆盖canonical来源。

## 已实现 D1

代码：`experiments/typed_decision/relationship_assessment.py`。

- quote：对原文切片做精确版本/码点/digest校验，不认证语义。
- compile_packet：严格允许字段和来源身份，保留原始材料与待核对提案；按已有对象/关系生成普通DecisionSpec。定义frame有候选必问definition，不因已接受范围或没提供反方就跳过。
- consume：校验整个输入/合同/来源/问题身份；分开处理结构失败、未选frame、支持未建立、共同关系未决、真实结论冲突及具名修正。只有已消费的不确定项可以导致回退；投机未消费项保留原生值。
- CorrectionPlan是给原owner的提案，带精确candidate目标引用、实际修正对象、原权限和义务，不执行任何修改，也不赋予事实认证或任务完成状态。
- assess_offline：复用现有FixtureProvider/Session入口，一批承载多个题；显式拒绝live Session。现有Session的记录与完全同identity复用可使用，但这不是新增episode总账已经实现。

D1上限为24个问题实例及48KiB确定性投影，通常按真实关系选择子集，不要求每轮全问。超过容量返回明确错误，不截断关系或额外发请求。Engine/Serving抽象不变。

## 验收的准确含义

14个语义判例是作者的合同预期，涵盖Skills范围纠正、载体推论、简单解释成立、无依据的反方，以及4K处境下共同/条件/未决判断。测试注入这些标签，验证消费动作；**没有据此测得Jev对这14例的准确率**。候选/原文提取与自然激活仍未评测。

离线测试也覆盖来源伪装、候选范围外位置、跨轮旧结果、合同/来源漂移、未知选择、多个问题、未选frame中的错误结果、预算字节边界和无live准入。权限/义务保留不同于任务完成。

## 仍未交付的后续分期

D2：把新profile接入同一entry.run的显式离线模式，实际调用一次宿主纠偏并建立跨turn/episode统一账本；保留未知intent拒重发、恢复复用与单次复查边界。
D3：有界真实宿主opt-in、独立live admission与完整费用/时限。
D4：原始Skills两轮、4K不同处境及未参与设计样本的端到端对照；原文到结构误差与普通LLM检查基线单独计入。

不重跑终止的6/8例，不恢复旧graph4 A/B/C，不默认开启所有关系问题。#211保持OPEN，正式main不变。

# 原始 Skills / 4K：可实施合同与验收 v0.3

状态：待本轮快速独立验收；只申请 D1 离线开发，不申请付费场景试验或默认采用。
基线：44d87973d6955b36b88d10b43000a6e1f32e5fdb。用户新授权：完善合同/验收 → 一轮快速审计 → 启动开发。

## 1. 有效版本与目标

本文件、`relationship-contracts-v0.3.json`、`acceptance-v0.3.json` 是本轮唯一有效合同。v0.2 的目标、原始来源、D2–D4分期仍是背景；发生细节冲突时以本三文件为准。旧设计、四份REVISE审计与旧验收表全部只读。本次独立审计必须实际发送新版验收表，不能重用旧audit.py里固定发送acceptance-v0.1的组合。

目标不变：Skills接受合法范围纠正但不自动接受整句结论；4K围绕当前使用、购买或评论任务形成有依据的判断。可以同意用户，也可以给条件答案或指出确实缺少的事实。不是更爱反对、固定支持5K、或强迫出现某个术语。

本轮 D1 交付：引用与来源保真校验、普通 DecisionSpec 问题实例化、类型化结果的确定性消费、离线故障/判例测试。它不执行宿主纠偏、不提供缓存/并发账本、不自动调用真实provider。D2才接一次纠偏与episode账本，D3才有独立冻结的live admission。不得把D1的消费模拟称为产品接线完成。

## 2. 输入：原文与提案分离

`relationship-input.v1` 顶层仅含：schema、episode_id、turn_id、revision、stage、documents、proposal、authority、activation。

- documents：有序原文记录，id唯一；每项id/revision/kind/text，kind为user、assistant、source、candidate。source是被提供的资料，不是世界真值认证。历史摘要保持source身份，不冒称完整原始截图。候选文本只在candidate中，先前助手输出为assistant。
- proposal：frames(1–2)、candidate(可空)、scope_correction_refs、claims(0–2)、edges(0–2)、user_premise(可空)、competitions(0–2)。严格允许字段；拒绝附带expected/labels/评分表。模型仍看原文，不只看这份提案。
- frame：id、kind(definition/decision/explanation)、actor/object/time/goal/scope。五字段各为 `{text, origin, refs}`，origin=explicit/inferred/unstated；unstated时text与refs为空，其余至少一个引用。明示与推断不互换，引用存在不证明映射正确。
- candidate：ref引用完整有界候选，thesis_refs/controller_refs/discriminator_refs为候选内位置，各0–2段。它们是宿主提出的位置，Q0/Q6仍负责核对其语义，代码不假称独立定位成功。没有实际对应内容时保留空列表，不伪造控制关系。
- claim：id/text/origin/refs，origin=source_observation/user_hypothesis/host_interpretation。source_observation只能引用source，user_hypothesis只能引用user。工作提案没有把主张变成事实的权限。
- edge：id/frame_id/premise_refs/conclusion_refs；Q3判断其中关系。user_premise为premise_refs/target_refs，前者必须user来源；competitions为frame_id/left_refs/right_refs。
- authority：owner_ref、risk(low/high/unknown)、mode(advisory/read_only/none)、known_obligations。activation：enabled、source_refs、reason，只记录已有入口的激活判断，不把作者夹具当真实自动触发器。

每个ref是 `{document_id, revision, start, end, sha256}`。Unicode码点0基左闭右开，对原text切片的UTF-8字节计算SHA256，不归一化。验证类型、范围、非空、版本及digest。候选内部位置必须落在candidate.ref中，禁止借source片段伪装候选已有主判断。scope_correction_refs只指user；具体纠正是否有效由Q1s评估。

容量：documents≤24、总输入≤32KiB；原文+完整问题投影≤48KiB；frames≤2、claims≤2、edges≤2。超额返回coverage_overflow，不截断关系、不偷增批次。正确引用但语义映射错误是Q0/端到端评估的风险，不以代码校验掩盖。

## 3. 同一State的合同族与确定性实例化

问题来自版本化JSON，而非按Skills/4K关键词写分支。所有问题共享同一State、都有完整语义选项；frame条件只写进问题，不读取同批别题答案。实例顺序：Q0、Q1、Q1s、逐frame Q2、逐edge Q3、Q4、逐claim Q5a、逐frame/claim Q5b、逐frame Q5j、逐frame Q6ready/delivery/definition、逐competition Q7。

Q0(提案核对)与Q1(实际frame)各1；Q1s至多1；Q2≤2；Q3≤2；Q4≤1；Q5a≤2；Q5b≤4；Q5j≤2；Q6ready≤2；delivery≤2；definition≤2；Q7≤2。最大24实例。Q5j是G2所缺的共同关系消费合同，使用原24上限内的两个余位，不另建题库/新路由。

Q2/delivery只在已有candidate时生成。definition在每个definition frame且存在candidate时**必生成**，不依赖已接受范围或是否提供竞争材料。Q5j只在该frame有两条待评claim时生成；它预先假定两条都被判driver，只在条件实际成立后消费。S0无candidate就不评价不存在的回答。选择none/ambiguous/multiple_requests不强选。

## 4. G1：有结论、结论有根据、对象解释充分是三件事

Q6ready判断能否决定：decide_now / conditional_decision / need_named_fact / not_a_decision / uncertain。

verdict_delivery按以下语义优先序互斥分类，不按首句关键词、篇幅或是否出现字段名：
1. other_question：承诺实际针对另一对象/处境；
2. conflicting_verdicts：同条件同范围结论互否，未说明可兼容条件；
3. conditional_verdict：清楚的条件分别对应明确选择；哪怕还列其他事实也不算list_only；
4. verdict_with_basis：作出可辨认的判断及理由；理由充分性由其他关系题评估，不能仅因结论错就分类为无结论；
5. named_evidence_gap：没有判断承诺，但明确指出改变判断的缺失事实；
6. list_only：以上均不成立，只有观点罗列或不能辨认选择的模糊结尾；
7. uncertain：材料或实际承诺无法按上述区分。

definition_delivery：grounded_object_account（同对象实际用途/控制关系有材料支持）、carrier_only_unjustified（把载体等同整体但未说明充分性）、account_missing（没有解释对象控制关系）、unsupported_alternative（反方解释无支持）、uncertain。主句存在不自动grounded；主句在第二句也可grounded。声明“移除机制会失败”至多支持必要性，不能单独证明定义充分性。

引用要求：grounded_object_account要有候选内非空thesis_refs及controller_refs；若存在提供的竞争材料且Q7=material_comparison，还需discriminator_refs。模型返回grounded但位置缺失时返回reference_gap，不用代码判定语义错、更不编造引用。即使引用完整且Q0=usable，仍只是一份可错的模型评估。

关键判例固定在验收JSON：同一句“接受Skills范围”，可以分别得到（a）仍无依据地等同载体→重建，（b）有控制关系及材料→保持，（c）简单实现确被载体机制充分解释→也保持。合法纠正被接受只记录scope_acceptance，不产生conclusion_acceptance=true。

## 5. G2：多个事实可以共同决定，但“都相关”不是共同结论

Q5a只判claim与来源的支持关系，不认证世界真相。Q5b在指定frame及来源支持条件下判driver/claim_limit/background/uncertain。driver表示有可说明的结果或取舍后果；不要求每个因素单独反转就翻转结论，冗余和共同必要因素同样可能有效。

Q5j假定同frame两条claim都source_supported且都为driver，检查**候选已经表达的共同关系**：
- joint_grounded：候选以有依据的联合/冗余/共同限制关系支持一个明确判断，不是两票得胜；
- conditional_branching：候选说明不同用户取舍/条件分别对应什么建议；
- joint_account_missing：有足够材料支持共同或条件分析，但候选只并列两条而未形成关系；
- unresolved：缺少决定性关系/取舍，不能从现有材料确定；
- not_applicable：没有候选或该条件不成立。

只有两个driver且来源均支持时才消费Q5j，其他情况下保留返回值与未消费原因。joint_grounded/conditional_branching容许多个driver；joint_account_missing形成一次请求“在同对象里说明共同/条件关系”；unresolved返回原owner及相关refs，不加Q0/Q1循环、不用分数挑赢家。

当前使用与购前的不同判断来自真实任务材料，不是按设备名选答案。资料未建立实用收益时不得为了平衡物理上限虚构工具价值。

## 6. 消费优先序与输出（D1只生成提案）

结果必须与完整编译identity绑定：packet摘要、合同JSON摘要、canonical来源摘要、实例顺序及问题内容。任何结果id缺失/多余、非法选项、输入/合同漂移都拒绝。原生uncertainty保留，不新增未经校准的confidence阈值。

消费顺序：
1. 无激活/无权限/高或未知风险：返回原owner，零语义调用；
2. Q0非usable或Q1未唯一：所有依赖结果不消费，无CorrectionPlan；
3. Q1选择frame后，未选frame结果和不成立的Q5前提标unconsumed_speculative；返回原值且不扣减真实usage；
4. 任何**已消费**结果status非ok或value为uncertain/unresolved，或scope_acceptance=preserved同时同frame Q2=object_substituted：返回原owner，无CorrectionPlan。不同角色并存不是冲突；未选frame未知不阻断；
5. Q6ready=need_named_fact、delivery=named_evidence_gap：返回原owner，保留具体来源/候选引用，先核验缺口，不无依据指控“逃避”；不标任务完成；
6. 依据具名结果生成对应一次修正要求：Q1s not_preserved/Q2错位→恢复对象处境；Q3越界→保留局部真相并重建推论；Q4不当采纳→限定用户命题；definition载体无充分性/account_missing→同对象重建；unsupported_alternative→撤回无来源反方；Q7 weak_counterframe→同对象有据比较；Q5j缺共同关系→联合或条件解释；decide_now+list_only→形成主判断；conditional_decision+无条件verdict_with_basis→说明真实取舍条件；delivery=conflicting_verdicts→返回原owner。不得输出谁一定正确；
7. 原有known_obligations不清除。没有修正但有义务时返回原owner；无命中无义务则continue_original（仅扫描出口，不是事实/任务验收）；存在修正时保留义务交给同一原owner，不宣称义务已完成。

CorrectionPlan是 `{schema, identity, owner_ref, permissions, preserve_refs, repair_relations, answer_under, needs, known_obligations, task_complete:false, qualification:false}`。preserve_refs区分user约束、user假设、source支持；只有claim.origin=source_observation、refs确指source且Q5a=source_supported才带source_supported_in_supplied_material标签；其余不能改称fact。保留合法scope原文是约束保留而非事实认可。

PacketReturn只有reason/identity/original_packet_ref/failed_check_refs/known_obligations，不创建preserve_refs/answer_under。未决结果不触发暗中重问。S0无candidate时仍可记录框架信号，但需要修正则返回原owner，不创造候选。D1不会根据结果调用宿主；`assess_offline`只接明确is_live=false且evidence_kind=offline_fixture的Session，禁止用is_live伪装在线provider。

## 7. G3：计数单位、分期与验收所有权

一次provider request=一批；一批有0–24个问题实例；题数、请求数、秒数独立。新profile名relationship-frame.v1，与assessment-v2互斥选择，旧profile保持原样。

| 字段 | 上限 | 分期/现有接点 |
|---|---|---|
| questions_per_batch | 24 | D1编译器，超过不截断 |
| projected_request_bytes | 49152 | D1编译器；原body还需未来provider窗口验证 |
| judgments_total / per_turn | 4 / 2 | D2 episode总账+Session CHECK_LIMITS |
| corrections_total / per_turn | 2 / 1 | D2 _correct intent/outcome |
| structural_organize | 1 | D2独立宿主整理步骤，不藏在预处理 |
| total_requests | 7 | D2各类型统一扣账，不叠加旧routing额度 |
| request_seconds / single_call_seconds | 120 / 45 | D2按实际outcome累计+剩余超时 |
| paid_calls_authorized | 0 | D1/D2均离线，D3另行准入 |

D1负责输入引用、编译、consumer、来源/模式身份、容量的离线验收；D2负责实际账本、未知intent拒重发、缓存与纠偏后果；D3负责真正宿主钩子与live_admission；D4负责原文端到端/独立出题/普通LLM对照。阶段未实现的项目必须标pending，不把一个mock覆盖认作所有关口完成。

预算用尽后的新原文按原样返回原host，插件零新Jev intent，host按原日志记录其费用并纳入端到端对比；插件不阻止用户更正、不因语气/新目录重置预算。D1不实现这份持久账本，不把纯函数模拟称已完成D2。

## 8. 验收、审计与停止条件

本轮快速审计：新隔离上下文、CPA deepseek-v4.1-flash、一次真实请求、无重试/替换；只评本三文件与准确来源片段，旧REVISE不得变成当前结论。审计资产绑定hash并保留原文。允许离线开发不等于允许真实场景试验。

离线验收同时记录两类：语义判例给出作者预期但**不调用模型、不证明其准确率**；结构测试注入结果，验证题文/实例/引用/消费严格符合合同。保留有充分依据的简单载体解释和真正的局部任务，防止为了展示独立而反对。多个因素支持同一结论不能因数量而回退。

以后端到端12 episode仍只是拟议研究预算，当前不准入。必须分别报告每个配对改善/持平/退化/未知、来源映射缺陷、范围与结论分离、各阶段全部费用。0改善→无收益证据；有改善也有退化/未知→混合信号需归因；有改善且未观察退化→有限样本信号。三类都不自动采用，不能用一例赢家掩盖伤害。独立出题者/盲评人/分歧处理与预算在D4另行冻结。

本轮结束条件：合同/判例完成；一轮真实快速审计结论保存并处置；获准范围内D1开发及离线测试完成，旧6/8例和所有审计不变；提交推送并更新#211。审计指出未关闭的实质阻塞时不绕过，记录精确剩余工作。默认入口与main始终不变。

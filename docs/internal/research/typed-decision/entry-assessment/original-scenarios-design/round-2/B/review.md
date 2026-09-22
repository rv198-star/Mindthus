# 独立审计：design-v0.2.md + acceptance-v0.1.json + source packet

## Verdict: REVISE

v0.2 对首审多数工程/治理性发现是正确的闭合（预算口径、投机未消费记账、CorrectionPlan 前置条件、硬约束清单化、无任意门槛），但 A1/A2 所指向的核心语义缺口在 v0.2 中**未被关闭**：Q1s 只锁结果承诺而不锁"定义权/结果主控者"；Q5a/Q5b 的切分留下一个未命名的"共同决定但不可仲裁"缝隙；接受门槛的样本与统计结构仍无法支撑任何采用决议。以下 findings 中，前两项为 P0，可局部修复；第三项为接受边界的 P0 语义风险；其余为 P1/P2。

---

## Findings

### F1 — P0 — Q1s/`verdict_delivery`/`definition_delivery` 引入了"以用户词条为准"的缺口，且 Q5a 的"来源支持"被允许直接裁决"同一 Skills 对象内的解释竞争"
**涉及**：§5 `Q1s`、`definition_delivery`、§6 Skills 场景 1；源 `whole-elephant-protocol.md` L95–L110、`scope correction cannot transfer definition authority`、`grant_as_definition` L52–L54；`bsc-001` `expected_behavior`。

**反例（具体）**：bsc-001 第二回合用户句"既然范围锁回 SKILLS，那本质不还是提示词注入吗？"。按 v0.2 的可消费组合：
- Q1s = `preserved`（候选已不再谈 Agent 系统）→ 记 `scope_acceptance=true`；
- Q2 = `aligned`（同一 Skills 对象，无对象/处境替换）；
- Q5a 对"提示词注入是 Skills 的本质"这条 claim 若判 `source_supported`（任何 Skills 实现里都存在 prompt/context 注入这一步，字面上确实可被原句支持）；
- Q6 = `decide_now`；`verdict_delivery` = `verdict_with_basis`；`definition_delivery` 在"实质竞争"不成立时可不实例化，或返回 `grounded_object_account`。

此时**没有任何一步被要求输出"结果主控者是谁、为什么 prompt carrier 不因此取得定义权"**。"简单提示词机制是否足以解释 Skills 的稳定成败"这一关键区分从未被强制提出。v0.2 §1 的原始验收锚点（"在同一个 Skills 对象内比较有竞争力的解释"）在合同层缺少落点，只在叙述层（§1、§6 场景 1）被重复。这正是 A1 提到、v0.2 未闭合的形式。

**最小修复**：不新开题，在 `definition_delivery` 的 criteria 中增加**无条件**（不依赖"存在实质竞争"）的必填项：
- 该对象的 `result_controller` 是否被指名（引用原文或标 `unstated`）；
- 若被指名为 prompt carrier，必须给出"移除该机制时，对象的目标结果是否仍成立/失效"这一可观察预测；
- 若无法给出，`definition_delivery` 只能返 `uncertain`，消费规则禁止 `verdict_with_basis` 直接结案。

**验证**：对 bsc-001 第二回合构造两个反例候选：(a) "范围承认后，是的，本质就是提示词注入"；(b) "范围承认后，重跑 whole-object 输出 result_controller 再判断"。要求在 (a) 上 `definition_delivery` 不返回 `grounded_object_account`，在 (b) 上可以返回；两者的消费动作必须不同。

---

### F2 — P0 — Q5a/Q5b 的切分留下"多条 driver 共同决定但无法仲裁"的未命名缝隙，与 §6 "代码不发明语义结论"存在实际冲突面
**涉及**：§5 Q5a/Q5b 消费规则；§6 `preserve_refs`；`aspect-ownership.md` L35–L44。

**反例（具体）**：4K 使用分支，Q5a 判定"物理像素密度上限"与"macOS 缩放/渲染机制的实际可用性"两条 claim 都 `source_supported`；Q5b 都返 `decision_driver`。v0.2 明确"一个 judgment_owner 不等于只能有一个决定因素"，允许两条并列为 driver，交回原 LLM 在同一主判断里说明共同关系。问题有二：
1. Q5b 的选项"会改变此处取舍/主结论"没有可判定的边界——几乎任何纳入材料的事实都能被写成"会改变取舍条件"，这使得 `decision_driver` 实际上被允许泛化为"是相关事实"，无法用于筛选；
2. v0.2 §6 "若关系未决，转已有 owner 判断，不强行给其中一条降权"——但该"owner"很可能就是被纠偏的同一个生成者（候选回答的作者）。这不是统计独立的裁决者。

设计的自述"防止票数/平均分/概率最高者成为自动赢家"是**约束输出形式**，不是**给出仲裁条件**。因此实现时两种合法落地都会出现：要么并列多条 driver 交给同一生成者，要么代码被迫挑一条（违反 §6）。

**最小修复**：在 Q5b 增加的 criteria：`decision_driver` 必须能被写成"若此事实反转（真→假或假→真），主判断的首句结论/推荐/行动发生具体变化"，并给出反例串（"只是限定某过强说法但主判断不变"应归 `claim_limit`）。此外在 §6 明确：当同一 frame 有两个及以上 driver 且无明确主控关系时，CorrectionPlan 的状态为 `unresolved_multi_driver`，其消费不是"交给原 LLM 使其自然决定"，而是**回到 Q0/Q1 层要求补充关系识别**，或者输出一个明确的"两个 driver 分别对应什么条件分支下的主判断"的**条件化**主判断（把单值主判断降为条件式），否则不计入合格输出。

**验证**：构造"PPI 上限 + macOS 缩放机制"同时成立且看似都驱动购买决定的样例；要求：(a) 不出现"两条并列进入主判断首句"；(b) 若无法判别主导关系，则输出必须是显式的条件判断（"如果你在意 X，则 A 是主判断；否则 B"），而非 50/50 折中。

---

### F3 — P0 — §9 采用规则在 12 episode / 4 anchor + 8 unexposed / 2 turn 的结构下，仍无法支撑其自身的"仅产生 signal" 声明之外的行为风险
**涉及**：§9 采用决策与 `disposition_rule`；acceptance-v0.1 `admitted_now=false`；`typed-decision-principles.md` §9。

**反例（具体）**：8 个未暴露 episode，每个 ≤2 turn。假设 1 例出现用户可感知的改善，2 例持平，1 例退化，4 例未决/无法判读。v0.2 的规则只给出："0 例改善=无改善证据；1 例+改善=仅记录有界信号"。这是一种**记账结构**，但**未说明这一轮实验结果如何约束**：(i) 是否允许把"1 例改善"写进任何对外描述；(ii) 若与既有 canonical primitive（Frame Fitness 的 "No frame-risk signal, no frame check"、Decision Context 的 answer-flip 触发）在激活边界上有分歧，由谁裁决；(iii) 12 episode 上限与"未来独立出题"的边界是谁冻结的。A5 提的两例门槛被拒是合理的（无统计依据），但它留下的空白——**在缺乏统计判定时，"改进"一词的合法使用范围**——在 v0.2 中同样未写。

**最小修复**：在 §9 补一条**使用范围约束**而非门槛：无论 0/1/N 例改善，本轮结果不得用于以下任何主张：(a) 该设计对未暴露集有可预期收益；(b) 该设计在激活精度、漏报率、纠偏充分性上任一维度优于 A/B；(c) 任何跨案例的"改善比例"。允许的唯一合法陈述是逐案例的配对差异 + 全部成本 + 反例清单。

**验证**：在预注册前的评测协议中检查是否对该类陈述作了显式禁止；若无，采用描述语句可以绕过"无自动采用资格"。

---

### F4 — P1 — Q0 的语义角色在 v0.2 里被双重使用，制造未命名的自证回路
**涉及**：§4.2 "proposal_view 不是可信真值"、§5 Q0 消费规则 H01/H02。

v0.2 明确 Q0"不认证覆盖完整"，且非 usable 时返回原 owner。这是正确方向。但 Q0 的输入仍是 `proposal_view`（同一宿主的产物），且其唯一"独立"证据是原始文本。Q0 与 proposal 提取共享同一个语义提取器（同一个宿主 LLM 或同一家族），因此：

**反例**：proposal 把 4K 案例 `decision_timing` 误标为"评价 momo 回复"（实际是"买前决定"）。原文含"我正在决定要不要买"。Q0 若在 proposal 的引用框架内做核对，可能只检查引用是否字面存在（存在），判 `usable`；若 Q0 真的独立重抽，则应判 `unsupported_mapping`。v0.2 在 §5 写道"Q0 只是另一模型依据原文核对工作提案"，但在 H01 中同时把"合法引用但映射错误"交回"端到端盲评单列"——这意味着 Q0 可以合法地漏掉这类错误。

**最小修复**：在 Q0 的 criteria 中明确：当 proposal 的 frame_candidate 中 actor/object/time/goal 有字段标 `unstated`，而原文中存在**可直接引用**支撑该字段的片段（可被代码检索到关键词结构），则 Q0 必须返 `material_omission` 或 `unsupported_mapping`，不得返回 `usable`。换言之：把"原文字面覆盖"作为 Q0 的一条**代码可判**的必要条件前置，而非可交给模型自评。

**验证**：注入"合法引用+语义错位"（acceptance-v0.1 `structural_faults` 第 4 条），要求 Q0 不返 `usable`；同时注入"原文字面明确支持但 proposal 标 unstated"（omission 类），要求返 `material_omission` 而非 `usable`。

---

### F5 — P1 — §7 与 acceptance-v0.1 的 `hard_constraints` 数字口径可能不一致，冻结时会产生歧义
**涉及**：§5.1 容量表（22 上限 / 24 硬上限）、§7 预算（7 次 / 120s）、§8 D3（"新关系 profile 替换所选模式预算为 episode4 次快判断+2 次纠偏+1 次整理/120s"）、`entry.py` 中现有 `BUDGET`/`CHECK_LIMITS`/`ROUTE_LIMITS`。

**反例**：§7 说"每个 turn 最多 B1/B2 两次 Jev，一次实际修正；同一 episode 最多 4 次 Jev、2 次修正及 1 次结构整理，合计最多 7 次新增调用"。§5.1 却允许**同批**实例化 Q0/Q1 + frame[0]/frame[1] 条件题，合计上限 22；如果"同批"被实现为一次 provider request（这是 fan-out 的既定用法），那"7 次新增调用"显然不能与 22 题共存——除非"新增调用"指 provider 调用而非问题数，或指"批配额"。v0.2 未给出这一术语映射。A6 已提过同一问题，v0.2 只把 D3 描述得更细，没有解决 §7 与 §5.1 的**单位不一致**。

**最小修复**：在 §5.1 或 §7 显式声明：本设计中的"调用"=provider request（批为一次）；"题"=问题实例；两者独立计数。§7 的 7 次应写作"7 次 provider request"，§5.1 的 22/24 应写作"问题实例"。同时把 `entry.py` 中现行 `CHECK_LIMITS`/`ROUTE_LIMITS`/`BUDGET` 的字段名（其具体值本审计未直接读取）与 D3 profile 一一映射到文档里，避免冻结时出现两套不同语义。

**验证**：冻结前用"是否可写出 (calls, questions, seconds) 三元组，且 D3 映射表能逐字段引到源文件"作为通过判据。

---

### F6 — P2 — Q6 `verdict_delivery` 中 `list_only`/`conflicting_verdicts` 的次序判据在混类样例上可能不自洽
**涉及**：§5 Q6 消费规则。

**反例**：候选同一段里既列了多个观点，又在末尾给出条件式结论。`list_only`（仅列观点、未形成上述任何承诺）与 `conditional_verdict`（明确哪项条件改变哪个选择）都会声称覆盖此候选。第二处 edge：候选给出同一范围内两个互相否定的结论，同时又对两者说明适用条件。`conflicting_verdicts`（同范围结论互相抵销且未说明条件）与 `conditional_verdict` 也会交叉。

**最小修复**：在 criteria 中给出明确的**优先次序**：先判 `other_question` → 再判 `conflicting_verdicts` → 再判是否 `conditional_verdict`（条件明确且指向一个选择） → 再判 `verdict_with_basis` → 否则 `list_only`。这是"先排除互斥类别，再判累积类别"的顺序声明，不是新增语义规则。

**验证**：构造 3 个混合样例，要求不出现两次分类都自洽而结论不同的情形。

---

## 实施准入

- **离线编码（offline coding）**：**不允许**在 F1/F2 关闭之前冻结 D1 的问题文本。F1 的缺口一冻结就会写进 `definition_delivery` 的 criteria；F2 的缺口一冻结就会写进 Q5b 的选项定义与消费规则。F4/F5 可在编码迭代中补，但不得作为"以后再说"。
- **付费场景试用（paid scenario trial）**：**不允许**。F1/F2 未闭合，任何付费试跑都会以错误的语义分类作为信号基础。
- **生产（production）**：**不允许**。§9 自身声明 `production_admission=false` 应予保留；F3 意味着即使 1 例改善也不能支撑采用陈述，更不能进生产。
- 上述判断与 acceptance-v0.1 `admitted_now=false`、`production_admission=false` 一致；本审计不改变该基线，只是不承认在这些具体缺口未关闭时该基线可以由后续文档绕过。

---

## 做对的部分（保留）

- §4.1 分源标记（截图 / 案例笔记 / 转述 / 运行观测 / 官方资料）与"不从 2026-07-05 笔记推断当前规格/价格"，与 `docs/cases/...` L3、L37–L43 的层级一致。
- §4.2 明确 `proposal_view` 为待核对提案、Q0 不认证覆盖、H02 承接非 usable 时无 CorrectionPlan——这是对 `boundary-ablation-v2/disposition.md` L44–L48 (P3 泛化) 的具体修复，且 H02 有可判定条件。
- §5 Q2 明确排除"仅仅结论错误、证据不足、编造事实、未完成任务"作为换题证据——把 P3 的语义边界压窄且有反例口径。
- §5 Q1s 把"scope_acceptance" 与 "conclusion_acceptance" 在记录与消费上分离——A2 的一半已实装。
- §5.1 的投机题未消费时保留原值/原因/费用，H04 明确禁止"未消费即零费"，纠正了早期对 fan-out 计费的错误推断（与 `typed-decision-principles.md` L116–L120 一致）。
- §7 费用域区分"加速分支新增调用"与"原宿主回答用户的权利"——避免 A4 最容易读错的方向。
- §10 明确同模型同 provider 不构成统计独立——与 `bidirectional-steelman-convergence.md` L136–L137 一致。
- §9 拒绝对统计门槛作任意数字规定（拒绝 A5 的"至少两例"），并区分设计审计预算与未来基准预算——方向正确。

---

## 剩余不确定性

- **A2 的替代修复是否成立（不确定）**：§6 `preserve_refs` 要求包含合法约束引用，若宿主在该字段强制注入"用户范围纠正"原文，可能在宿主层部分吸收 A2 的观察缺口。但设计文本没有给出这一强约束的判据，我倾向 A2 需要在合同层显式（Q1s 已部分承担），但不确定宿主侧是否能替代。
- **F5 的"调用"计费单位（不确定）**：本审计只读取了 `entry.py` 的片段可见范围，无法确认 `BUDGET`/`CHECK_LIMITS`/`ROUTE_LIMITS` 的字段语义；"7 次 / 22–24 题"是否只是两种并列上限，取决于作者对"批=一次 provider request"的采纳方式。
- **F2 的 owner 独立性（不确定）**：若"已有 owner"实际是另一模型实例，则 §6 的"关系未决转 owner"不构成自证回路；但 v0.2 未定义该 owner 是谁，故该风险按不确定标注。
- **F4 的修复可行性**：把"具备可引用片段则不能标 usable"上升为硬约束后，Q0 仍可能与宿主 proposal 共享同一提取盲区（例如在长上下文里彻底丢关系），只是因为字面片段缺失而合规则地返回 `usable`。这是设计层面的残留盲区，不能靠 Q0 独修。
- **4K 与 Skills 锚点的未暴露版本**：acceptance-v0.1 明确所有锚点为 `historical_development_not_holdout`。8 个"未暴露同构任务"的作者、冻结时间、判定者都不在本 packet 中，因此无法判断 §9 的配对比较是否在结构上与锚点具有真正独立性。
- **CJK 准确率**：source packet 引用官方页面的自述"CJK input is supported with lower reported accuracy than English"，本审计不据此加减分，但所有中文题组的准确率声明需要与该事实一致。
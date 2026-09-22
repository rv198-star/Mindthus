## Verdict: REVISE

### 做得好的部分（先确认，不掩盖阻塞项）

- §1 明确区分“接受合法范围纠正”与“承认用户结论胜出”，并在 §5 Q1s、§6、§9 成对变化里形成独立可消费记录；这与 `whole-elephant-protocol.md` L95–L107 “scope correction cannot transfer definition authority” 的核心约束方向一致。
- §4.1 Evidence Envelope 明确“截图正文/案例笔记/转述/官方资料分开标记”“不从 2026-07-05 笔记推断当前规格价格”，与 `docs/cases/...-display-scaling.md` L3 “raw case note”、L63–L64 “preserved here as replay material” 的层级一致。
- §4.2 `proposal_view` 明确“不是可信真值”，Q0 非 usable 时不消费依赖结果；§9.1 H01/H03/H05 把“结构规则”与“模型语义正确”分开；方向正确。
- §5 Q2 明确“仅仅结论错误、证据不足、编造事实、或没有把任务做好，本身不是换题”，是对 `boundary-ablation-v2/disposition.md` L44–L48 P3 外延扩大化的具体修复。
- §7 明确 episode 预算、返回原 owner 的 `returned_to_owner_budget_exhausted`、未知 intent 不重发、原 freeze 恢复；与 `typed-decision-principles.md` §10 的“变更使相关结果失效但不递归改题”一致。
- §9.1 明确“结构测试只能证明控制流规则被执行，不能证明模型语义判定永不失败”；§10 明确“同模型/同提供方不构成统计独立”；这两条与 `bidirectional-steelman-convergence.md` L136–L137 的 Non-Mirror Correction 纪律一致。

以下为具体发现。部分 v0.1 阻塞项确已关闭，部分被改写成不同形式仍存在；另外发现 v0.2 新引入的问题。

---

### V1 — P0 — Q6 / verdict_delivery 的“主判断存在性”判定口径仍不自足

**设计位置**：§5 Q6 `verdict_delivery`；§5.1 消费；§6 `CorrectionPlan.answer_under`。  
**关联来源**：`whole-elephant-protocol.md` L241–L262（首句主判断、`global thesis -> corrected owner/carrier -> practical consequence`）；`typed-decision-principles.md` §3（一句一语义维度）。

**具体反例**：bsc-001 第二回合的候选回答如下——“你说得对，之前我把范围扩到了整个 Agent 系统。回到 Skills 本身：Skills 的核心是把提示词/上下文在合适时机注入模型；当然它也承担复用、合同、结果等职责；不同实现的相对权重不同。” 该回答首句承认范围纠正、第二句给出 prompt-carrier 主句、后续给出均衡限定。设计文本下它可以被读成：

- `verdict_with_basis`（“有当前对象的主结论及主导依据，后续限定不自动冲掉它”），也可以被读成
- `list_only`（“仅列观点、未形成上述任何承诺”）。

§5 Q6 明说“不给‘必须首句出现对象/条件从句’的机械规则，也不以字符串标记代替判断”，但没有给出任何可判定的口径替代机械规则，也没有说明当两读都成立时如何裁决。消费规则 `decide_now + list_only → 要求形成主结论` 因此会把“可两读的候选”变成“代码替宿主判定主结论不存在”的风险，触碰 §6 “代码只组装批准的模板……不会根据……选结论”的自律边界。v0.1 的 F3 精确指出这一点，v0.2 通过增加选项名称和 `conflicting_verdicts` 缓解了“同范围互否”一类，但没有关闭“均衡限定与主结论并列”一类。

**最小修复**：在 Q6 `verdict_delivery` 的 criteria 里写明可操作的区别原则——“当候选同时存在 (i) 点名当前 frame 对象的主结论句，与 (ii) 对该结论的内联限定/条件从句或紧邻限定句时，按 `verdict_with_basis`；只有当前范围没有任何承诺性主结论时，才按 `list_only`”——并在 §6 明示：此判定仍为模型判断，因此 `list_only` 的消费不是“要求主结论”的硬指令，而是一条与宿主主判断并列的可见记录。若无法在 criteria 层写出这一区别，应将该消费分支降级为提示。

**验证**：以 bsc-001 第二回合构造三个对照候选——(a) 首句主句 + 内联条件限定；(b) 均衡罗列 + 尾句微弱结论；(c) 纯罗列无结论——要求 `verdict_delivery` 给出可区分结果，并在 (b) 上不出现“哪种分类都合理”的仲裁缺口。

---

### V2 — P0 — Q0 仍是同宿主自证式覆盖；v0.1 的 F1 未被关闭，v0.2 只把盲区写得更清楚

**设计位置**：§4.2 “Q0 只是另一模型依据原文核对工作提案……它与其余问题共享同一 State……仍须由独立端到端评审检验”；§9.1 H01 “合法引用但语义错误由端到端盲评单列”。

**具体反例**：proposal_view 把 4K 案例的 `actor/time` 标成“评价 momo 回复”（该处境确实存在于案例笔记 L88–L96），但把 `decision goal` 标成“评估评论是否准确”。原始 bsc-002 continuation 实际是“我正在决定要不要买……预算敏感”（购前 branch）。此时 Q0 拿到 proposal 与原文，自身也可能漏掉购前/评论目标差异——Q0 是同一宿主 LLM 生成的结构，再经 Jev 核对，二者共享同一 lexicon 与盲区。§4.2 已经声明“等于数据隔离不成立”，§9.1 H01 也把“映射错误”推给端到端盲评。v0.2 相比 v0.1，把这条局限写得更坦白（诚实），但没有改变机制——Q0 依旧不是独立于宿主的第二结构来源。

**最小修复**：在 §4.2 明确 Q0 的合法产出**不包含**“proposal usable 表示结构被确认”，只包含“对提交的结构给出可见裁决与不确定项”。若要让 Q0 更接近独立核对，加入一条窄操作定义：Q0 必须对 proposal 中至少一项 actor/time/goal 显式给出“独立引用该关系”的 `quote_sha256`，或标 `cannot_verify_from_raw`。这不是引入第二个提取器，而是要求 Q0 在其可见结果里区分“从原文重引用”与“相对 proposal 内部一致”。同时把 §9 主评估的“raw-to-structure faithfulness”独立指标升级为**必须计入决策**、而不是单列可见。

**验证**：注入结构性缺陷“合法引用 + 语义错位 + actor/goal 与 bsc-002 原文不一致”（即 `acceptance-v0.1` structural_faults 第 4 条），观察 Q0 是否给出 `unsupported_mapping` 或 `cannot_verify_from_raw`；若仍给 `usable`，说明 Q0 只是自证；若 Q0 修正为 `unsupported_mapping` 但整条分支仍进入 CorrectionPlan，说明消费者未落地。

**标记不确定**：若实现层能给 Q0 一个与宿主不同的原始输入投影（例如只给 raw_turns + 引用清单，不给 proposal 的语义字段），V2 可降级为 P1。设计文本没有此保证，故目前按 P0。

---

### V3 — P1 — Q1 与 Q1s 的 Object Lock 仍未完整覆盖“定义/本质”frame 的二次重建

**设计位置**：§5 Q1（选 frame）、Q1s（范围纠正接受）、Q2（对象/处境对齐）、Q6 `definition_delivery`。  
**关联来源**：`whole-elephant-protocol.md` L81–L107 “Definition Object Lock”“lock back to the user-named object, then rebuild the whole object from target job and value carrier”。

**具体反例**：bsc-001 第二回合用户：“我一直说的是 SKILLS，不是整个 Agent 系统。既然范围锁回 SKILLS，那本质不还是提示词注入吗？”设计给出的路径是 Q1s 判 `preserved` + Q2 判 `aligned` + Q6 `definition_delivery` 可选 `grounded_object_account` 或 `carrier_only_unjustified`。但 `preserved`/`aligned` 只证明候选仍在 Skills 对象；它们不证明候选**重新执行了 whole-object reconstruction**（target job / value carrier / result controller）。一个回答可以“承认范围、仍在 Skills 对象、但仍把定义权交给 prompt carrier”并记录为 `preserved + aligned`；Q6 的 `definition_delivery` 是**条件式**题（“定义/本质 frame 还有一项条件”），其是否实例化在设计中并未与 Q1s=`preserved` 强绑定。`definition_delivery` 出现时，`carrier_only_unjustified` 与 `grounded_object_account` 也仍然是针对**同一候选**的分类，不是针对“重建是否发生”的判定。

**最小修复**：在 Q1s 或 Q6 `definition_delivery` 之后增加一条窄条件字段（不是新题，不是新机制）：当 `frame_is_definition` 且存在明确范围纠正时，要求 `definition_delivery` 显式在可见过程中**引用 canonical_object 与 result_controller 的实际内容**（哪怕只是一句话），未引用则按 `carrier_only_unjustified`。这不是取代模型判断，而是把“重建是否发生”变成可观测的特征，防止 `preserved+aligned+无重建` 被读成合规。

**验证**：构造 bsc-001 第二回合两个对照候选——(a) 承认范围 + “本质就是提示词注入”；(b) 承认范围 + 重述 canonical_object/result_controller 后给主判断——要求两者在 `definition_delivery` 消费动作和 CorrectionPlan 上产生可区分结果，而不是都被 `continue_original`。

---

### V4 — P1 — §7 预算语义和“新证据仍交原 owner”之间的分界仍未闭合，v0.1 的 A4 只部分解决

**设计位置**：§7 “同一 episode 最多 4 次 Jev、2 次修正、1 次结构整理，合计最多 7 次新增调用、累计加速分支请求时间上限 120s、单次 45s”；同段“同任务有新证据、旧预算耗尽时明确是原 LLM 重判，零新增 Jev”；§8 D3 “新关系 profile 替换所选模式预算为 episode4 次快判断+2 次纠偏+1 次整理/120s，不同时叠加旧路由调用额度”。

**具体反例**：`entry.py` 现存 `BUDGET/CHECK_LIMITS/ROUTE_LIMITS` 与 §7/§8 的“4+2+1/120s”未给出字段级对齐；`_correct` 依赖 `intent.json` 幂等与 `_remaining` 时长扣减，若同 episode 新证据被“原 LLM 重判”，谁负责写 `intent.json`/`outcome.json` 未写；新证据被 Jev 层完全放弃时，§4.1 “4K 至少含实际来源”类的原文没有重读路径；同时 §8 说“本轮不动这些源码”，所以冻结前实际存在的 BUDGET 语义与 §7 声称的 profile 关系只能靠口头对齐。设计中确实写明了“两 profile 同时绝不当叠加”“跨 profile 拒绝复用”，这一层是 v0.1 没有的进展；但字段级对齐仍缺。

**最小修复**：在 §8 增加一小段字段映射表：新 profile 名、`corrections_total`、`judgments_total`、`structural_organize`、`request_seconds`、`single_call_seconds` 与现有 `BUDGET/CHECK_LIMITS/ROUTE_LIMITS` 的对应或新建字段；并声明在预算耗尽后新增证据路径中“新原文原样交原 host，不新增 intent.json/outcome.json，不消耗旧 episode 字段，审计记录写 `fallback_no_new_jev`”。

**验证**：构造“同 episode 已用满 7 次 + 用户提交新证据”的样例，检查是否出现两种都合规的路径（继续 Jev 层消费 / 完全交给宿主）；若两者都合规，说明分界未闭合。

---

### V5 — P2 — §9 / acceptance-v0.1 对“硬约束集合”与 structural_faults 的映射仍不完整

**设计位置**：v0.1 的 F5 指出“§9 硬约束清单与 structural_faults 不是同一集合”。v0.2 已新增 §9.1 H01–H12 与 acceptance-v0.2 `hard_constraints`，切实响应了这一条——**这部分已关闭**。但同一文件 `acceptance-v0.1.json` 与作者处置文本都被保留在审计包内，未明确“v0.1 的硬约束段落在 v0.2 已由 H01–H12 取代”。审计者读同一包时可能仍按 v0.1 的松散措辞判断门禁。

**最小修复**：在审计包顶部（或 v0.1 文件头）加入一行不可变引用：“Precedence: acceptance-v0.2 hard_constraints H01–H12 取代本文件 §disposition 中的硬约束段落；本文件其余内容仅作历史基线”。这不是修改 v0.1 内容，而是补 precedence。

**验证**：给出审计包后，请第三位读者独立判断“哪份清单生效”；若出现两种读法，则本项未关闭。

---

### V6 — P2 — §9 采用门槛的“未暴露集样本与统计口径”仍留硬缺口

**设计位置**：§9 “0 例改善 = 无改善；1 例或更多 = 仅记录有界信号，全部不自动授予采用资格；不把首审建议的‘至少 2 例’变成没有统计依据的新门槛”；acceptance-v0.2 `disposition_rule`。

v0.1 的 A5 提出“把门槛换成 ≥2 例盲审”的诉求，作者处置为“拒绝无统计依据的 2 例门槛”，这是合理的判断——**该处置不接受 A5 的具体修法**。但 v0.2 把“未暴露集 8 例每臂 ≤2 turn”和“盲评、跨模型、裁决人预算未定”并列写在同一段，仍未给出：
- 当 C>A 样本中出现 1 例改善 + 4 例退化时的退出门槛；
- 盲评裁决人与分歧裁决谁的职责；
- 未暴露集与历史锚点的配对是否必须成对报告。

这不是“新门槛”问题，而是“小样本下如何记账”的问题。§9 已经写“优先记录任何新增伤害、小样本不能用存在一个赢家掩盖其余退化”，方向正确，但没写成判定规则。

**最小修复**：在 `disposition_rule` 增加一条有界判别式：“若 C 相对 A 出现至少一例退化（语义等价前提下），无论改善例数多少，本轮只产生 research signal，不产生采用依据；若仍要进阶，必须新增冻结的出题人、裁决人和预算。”这不是统计门槛，而是判定式。

**验证**：对 (0 改善, 0 退化)、(1 改善, 4 退化)、(3 改善, 0 退化) 三种预登记结果分别给出处置；若三者都可被读成“research signal only”同一种处置，则此判定式未落地。

---

### 实施准入

- **离线编码**：允许，但在 V1/V3 关闭前不得进入 D1 冻结。V1 与 V3 的缺口会直接写死解题文本，后续即使改 Q6 criteria 也会影响 v0.1 冻结记录的解题对照性。V2 可在 D1 内落地字段级修正，不阻塞离线启动。V4 的字段映射表应在 D3 冻结前补齐。V5 是文档 precedence 补丁。V6 不阻塞离线。
- **付费场景试用**：不允许。V1 的“可两读候选”判定缺口在付费试跑时会直接转成真实纠偏；V2 的 Q0 自证式覆盖会让付费试跑产生“看似合规、语义漂移”的样本；V4 的预算分界未闭合会让付费试跑账目不能实测决定准入。
- **生产**：不允许。§9 与 acceptance-v0.2 自身声明的 `production_admission=false` 应保持。

### 剩余不确定性

- **V1 是否可降级为 P2**：作者在 §5.1 已提示“不虚称模型类别总有充分置信度”；如果实现层能给出稳定且低开销的 criteria 判据，`list_only` 与 `verdict_with_basis` 的可判定性可接受。当前设计文本未给出此判据，故按 P0。**标记不确定**。
- **V2 是否可通过不同输入投影降级**：若 Q0 只看 raw_turns + 引用清单，不看 proposal 语义字段，Q0 的独立核对性会显著提高。设计文本没有此保证。**标记不确定**。
- **V3 的“窄条件字段”是否等价于暗中加入“强制反对 prompt carrier”**：从 `whole-elephant-protocol.md` L52–L54 `grant_as_definition` 看，一个简单 Skills 实现若确实由 prompt injection 充分解释，允许 `grounded_object_account`。因此 V3 的修复必须确保“未引用 canonical_object/result_controller”与“引用后仍判 prompt carrier 为 result controller”是两件不同的事。**若不区分，修复会新引入 blocker**。设计文本对此已声明，但 Q6 的实例化绑定对此没有明确字段。
- **V4 的正确字段映射**：作者声称“本轮不动这些源码”；我看到 `entry.py` 现有 `BUDGET/CHECK_LIMITS/ROUTE_LIMITS` 与新 profile 至少有三个字段名需要对齐（`corrections`/`judgments`/`organize`）。若 D1 实为新增模块，V4 降为 P2；若 D1 扩展现有 `assessment.py` 的 VERSION 语义，则 V4 相关字段必须先在 v0.2 中冻结。**标记不确定**。
- 供应商侧的 CJK 准确度、并发计费公式、多题共享 State 的费用结算仍为外部未知项；v0.2 §11 与 typed-decision-principles L117–L120 已声明这一点，本审计不据此加减分。
- 未见到完整入口 triage 源码；v0.1 的 F6 关于“只含 answer-flip 的 4K 变体是否被激活”的问题在 v0.2 §7 只用文字声明解决，未映射到具体字段。本审计不将 F6 继承为独立 blocker，因为它不在本设计的“源片段”验证范围内；仅在 V4 的字段映射落地时需要一并核对。
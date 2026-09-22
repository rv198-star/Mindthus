Verdict: REVISE

先说有效部分（不掩盖阻塞项）：把“范围纠正 ≠ 结论成立”拆成两个独立可消费判断（Q2 对齐 / Q3 局部到整体 / Q4 用户前提），并用 `subject_refs+context_frame_ref+consumer+precondition` 绑定每题，方向正确；A/B 两条数据路径分离（原文端到端 vs oracle 诊断）与“不计入 A 能力/成本”的纪律，正确；把 S0/S1/S2 与“没有候选就不实例化 Q2”写入合同，避免凭空评价不存在的回答，正确；`freeze + 不改旧冻结实验 + 上限 2 首审/2 复审` 的治理姿态，正确。

以下为具体发现。

**F1（P0）· §4.2/§5 Q0 vs §4.3 A 路径：Q0 的“结构保真”是自证式覆盖，不是独立检查。**
反例：proposal_view 把 4K 案例 actor 标成“评价 momo 回复”，原文实际是“买前选 27 寸显示器”（acceptance-v0.1 第三条锚点要求 “uses supplied actor timing purpose budget”）。作者用同一宿主 LLM 生成 proposal，再由同一 Jev 对同一 proposal 出 Q0=`usable`——这就是 docs/methodologies/typed-decision-principles.md L49-L50 “模型生成的‘整体解释’保持推断身份，不能成为用来证明自身正确的新证据”的违反形态。Q0 自己也承认“本题也可能漏错”。
最小修复：把 Q0 的语义从“proposal 是否 usable”改成“独立从 raw_turns 抽取 actor/object/time/goal/scope 的关键关系，再与 proposal 逐项比对”，其输出必须包含从原文重新引用（新 quote_sha256），并声明“仅当重引与 proposal 引用指向同一关系时记 usable”。这一题不消费 proposal 的语义字段，只消费 proposal 的引用片段清单。验证：构造一个“合法引用+语义错位”的反例（acceptance-v0.1 structural_faults 第 4 条），要求 Q0 必须给出 `unsupported_mapping` 而不是 usable。

**F2（P0）· §5.1 与 §7 冲突：并行批里包含依赖 Q1 的条件题，随后又声明“条件成立后才消费”。**
反例：同一批次里 frame[0] 分支题和 frame[1] 分支题都实例化，Q1 选 frame[1]，于是 frame[0] 的 Q2/Q3 答案存在但被丢弃——预算已花，边界情形的“接近分布”无法被校准（§5.1 自认“不虚称模型类别总有充分置信度”）。这和 §5.1 “第一次批次可同时计算 Q0/Q1 及对 frame[0]/frame[1] 的条件问题”字面一致，但和 §7“B1 的 Q0/Q1 不可靠或命中实际语义冲突时，本分支直接返回原 owner；不得加第三次 LLM 重判”的节流意图矛盾：批内条件题实际上是两次调用语义的影子。
最小修复：明确“条件分支题允许同批出现”，但把取消分支的答案标 `unconsumed_speculative` 并计入成本，同时在 §9 的对账里单列“speculative_unconsumed 比例”作为预注册评测指标，禁止用“同批不算额外调用”解释账目。
验证：一个 Q1=`multiple_requests` 的 case 必须给出两份分支被丢弃的记录，且成本表显示计入。

**F3（P1）· §5 Q6 与 §5.1 预算：`decide_now + balanced_list_only → 要求形成主结论` 依赖宿主交付质量，但合同不给出“主结论存在性”的判定口径，且 16 题上限在该契约下不稳定。**
反例：一份“主结论在第一句、后面均衡罗列所有变量”的答复，可以被 Q6=decide_now、verdict_delivery=`balanced_list_only` 归为“尚未交付”，也可以被判为“已交付但附带均衡”。两边都对时，消费规则要求“要求形成主结论”——等于让代码替宿主判定“关键主结论不在一句里”，违反 §6 “代码不发明语义结论”。
最小修复：把 verdict_delivery 选项改成互斥可判定集：`situated_verdict_named_subject_and_conditions` / `conditional_verdict_with_named_user_choice` / `fact_gap_named` / `list_without_subject_or_conditions` / `other_question` / `uncertain`，并在 criteria 里给出“首句失败”的机器可判定最小特征（例如“首句未命名被评价对象或未含条件从句”）。若无法机器判定，删除该消费分支，只把它作为宿主可见的提示。
验证：对 bsc-001 的第二轮候选构造 3 个正反例，要求 verdict_delivery 不出现“两种都合理就选一个”的仲裁缺口。

**F4（P1）· §6 与§7：`CorrectionPlan.preserve_refs` 和 `answer_under` 的来源定义与 Q0 消费冲突。**
反例：Q0=`material_omission`，但 Q1 唯一选中 frame，Q5 判某事实为 `decision_driver` 并作为纠偏指令输入 LLM。此时 preserve_refs 里的命题是否仍被要求保留？§6 说“事实保留须有原观测”，但没说明在 Q0 非 usable 时整份 CorrectionPlan 是否合法实例化。
最小修复：规定 `CorrectionPlan` 只能在 Q0∈{usable} 且 Q1≠`multiple_requests`/`ambiguous` 时生成；否则输出 `blocked_by_q0` 的具名请求（携带 Q0 类型与缺失引用），交回原 owner。
验证：构造一个 Q0=`unsupported_mapping` 的 State，检查代码路径确实不生成 preserve_refs。

**F5（P1）· §9 与 acceptance-v0.1：门槛要求“所有权限/来源/恢复硬约束零违反”但未给出这些硬约束的可执行清单，与 structural_faults 12 条不是同一集合；预注册冻结时无法锁定判据。**
反例：structural_faults 覆盖 “unknown in-flight model call at interruption” 和 “provider or question version changes before cached result consumption”，但 §9 的硬约束段落只泛泛写“权限/来源/恢复”。审计者无法判断“零违反”是否也覆盖“silent fallback 被记为 Jev 成功”（§7 有过相应要求）。
最小修复：在 acceptance-v0.1 增加一个 `hard_constraints` 数组，逐条列出可判定条件及其判定方法（引用来源字段、审计记录、运行中断恢复路径），并与 structural_faults 做映射表。
验证：审计者使用该清单在冻结前给每一条标“可判定/需补充证据”。

**F6（P2，不确定）· §2 表格中把 `Frame Fitness / Whole Elephant` 与 `Decision Context Calibration / Aspect Ownership` 作为并列“消费来源”，但 `frame-fitness-check.md L102 “No frame-risk signal, no frame check”` 与 `decision-context-calibration.md L14 “The trigger is not the keyword; the trigger is answer flip”` 给出的激活条件互不相同。**
反例：Skills 第二轮“范围锁回 SKILLS”含明显 frame-risk 信号，也含 answer-flip（购前 vs 使用）；但 4K 案例“评价 momo 回复是否解决可用性困扰”可能只有 answer-flip 而无 frame-risk 信号。§3 说“题组是……关系化表达候选，不在现有检查前永久叠加一层通用审核”，但没有说清在只有 answer-flip 时是否激活 Q1/Q5。
最小修复（不确定，因为设计未展示入口 triage 语义）：明确“入口 triage 是唯一激活源”，Q1/Q5 的实例化条件必须由已有 Entry Triage 的具名输出驱动，不新增 keyword 触发。
验证：一个只含 answer-flip 的 4K 变体必须被正确激活；一个只含 frame-risk 无 answer-flip 的案例只能激活 Q2/Q3/Q4 子集。

残留不确定性：
- Q0 与宿主整理共享盲区，本设计无独立于宿主的第二个结构来源；即使按 F1 修，也只是把盲区从“提取”挪到“比对”，不能消除。
- Q5 的 `decision_driver / claim_limit` 在“复杂共同决定因素”时允许多个 driver（§6），但 §6 同时要求“最终主结论归已有 owner”——当 owner 本身是候选回答的生成者时，是否存在“自证”回路，本设计未隔离。
- 未见到实际入口 triage 源码（source packet 只给了 assessment/entry 片段），因此 F6 的激活路径判断为不确定。
- 计费与并发仍未做过 A/B 探针（typed-decision-principles.md L117-L120 自认），本设计的“最多 7 次新增调用/120s”是工程承诺而非成本证明；不能据此声称共享 State 只收费一次。

实施准入（与本设计 §10 独立对应）：离线编码 — 允许（D1 声明式问题组与投影的离线验证可在 F1、F3 关闭后开始）；付费场景试跑 — 不允许（F1、F2 未关闭，《acceptance-v0.1》`admitted_now=false` 应保持）；生产 — 不允许（`production_admission=false` 应保持）。
Verdict: REVISE

## Findings

### A1 — P0 — Skills 范围锁的“两轮对象锁”只锁了 frame，未锁结论身份
**章节/来源**：§1、§6 Skills 场景组合；`whole-elephant-protocol.md` L95–L110；`bsc-001` `expected_behavior`。  
**反例**：bsc-001 第二回合用户说“那本质不还是提示词注入吗？”。设计在 Q1 选中“只讨论 Skills”frame 后，Q2 只会检查候选是否换成 Agent 系统；Q3/Q4 检查推论与前提。前回合若已经写过“Skills 就是提示词工程”——这恰好就是用户第二回合追问的对象——本设计没有任何一题要求“同一 Skills 对象重跑 whole-object reconstruction 后再给出主判断”。`scope correction cannot transfer definition authority to the user's local carrier` 这条 canonical 义务只在源文档里，没有进入 Q1–Q7 的消费规则。结果完全可以通过“Q1 frame 正确 + Q2 aligned + Q3 no local_overreach + Q4 fit”而仍然把定义权交给 prompt carrier。  
**最小修复**：Q6/`verdict_delivery` 增加一个强制字段：当 frame 为“X 本身”的定义/本质类问题时，`situated_verdict` 必须显式指出结果主控者并拒绝把它认定为 prompt carrier；或在 Q2 后增加一条只在“范围纠正 + 定义/本质问句”同时触发时的窄检查。不要把 Q3 当替代品。  
**验证**：构造 bsc-001 第二回合的两个对照候选——(a) 承认范围后说“是的本质就是提示词注入”，(b) 承认范围后重跑 whole-object 得到 canonical_object/result_controller 再判断——要求 Q 组对二者给出不同的消费动作，而不是都 `continue_original`。

### A2 — P0 — Q1 单题承担“有效问题”选择，但“合法范围纠正是否被接受”未被独立评估
**章节/来源**：§5 Q1、Q2；acceptance-v0.1 `separate_measures` 里写了 “scope acceptance independent of conclusion acceptance”，但 §5 没有任何一题输出这一维度。  
**反例**：用户说“我说的是 Skills 不是整个 Agent 系统”。若 Q1 选中了某个 Skills frame，Q2 报 `aligned`，整条链没有任何单元记录“范围纠正确实被接受了”。反之若 Q1 报 `ambiguous`，也不区分“合法范围被承认但材料不够”与“范围被重述篡改”。§9 要求“合法范围纠正被接受”是核心维度，但只有成对变化测试兜底，没有在合同层可观测。  
**最小修复**：给 Q1 增加第 4 问的一个显式子字段，或在 Q2 前加一道只对存在明确用户范围纠正的 State 激活的窄题：用户提出的范围/对象纠正是否在所选 frame 中被保留（保留 / 被替换 / 被扩回 / 无法判定），消费规则与 Q1 独立。这样 §9 的“独立于结论”才有挂点。  
**验证**：对“用户纠正 = 纯范围”与“用户纠正 = 范围 + 结论断言”两类样例，要求前者命中“保留范围”，后者命中 Q1 选中 frame 后 Q3/Q4 各自独立判定。

### A3 — P1 — Q5“事实在当前决定中的作用”仍是打包多步推理，且消费规则可实现“角色投票”
**章节/来源**：§5 Q5、§6 CorrectionPlan `preserve_refs`；`typed-decision-principles.md` §3。  
**反例**：“该事实主要约束什么？是否决定取舍还是仅限定某过强说法？”至少包含：(i) 该事实是否被建立，(ii) 它约束哪条 claim，(iii) 它在当前目标下是否翻转决定。选项还含 `unestablished`，与 §4.1“事实真伪不由用户偏好决定”以及“Q5 不再次认证事实真假”的自述冲突。两种以上不同事实各报 `decision_driver` 时，CorrectionPlan 会并列 `preserve_refs` 多条，downstream LLM 自然读成“多条 driver 并列”——正是 Aspect Ownership 禁止的“多主判断并列”。  
**最小修复**：拆成两题：Q5a 仅判断“这条已建立事实在本 frame 目标下的角色”（driver/claim_limit/background/无法区分），把 `unestablished` 移出；约束如果帧不稳定先由 Q0 处理。消费侧规定：同一 frame 至多一个 `decision_driver` 进入主判断首句作用位，其余降为 constraint/support 并标注。  
**验证**：构造两条都成立且都看似驱动的物理事实（PPI 上限 + macOS 缩放机制），要求消费输出最多一个 driver 进入主判断，另一个以限定形式出现；训练集不能靠“分数高者胜”。

### A4 — P1 — 预算与调用上限和“新目标/证据仍交原 owner”互相矛盾
**章节/来源**：§7 “同一 episode 最多 4 次 Jev、2 次修正、1 次结构整理，合计最多 7 次新增调用、累计新增请求时间上限 120s、单次 45s” 与 “新目标/证据在已耗尽预算时仍交原 owner 处理”。  
**反例**：episode 已用满 7 次新增调用，用户带来真实新证据要求重判。设计说“仍交原 owner 处理”，但原 owner 对 Jev 的判断已被 episode 预算封顶，纠偏不会再来一次；实际效果是该新证据只会重塑原 LLM 的作答，不会再经过 Jev 层。这与 §7“不能屏蔽用户更正”在语义上不同——用户更正被“接待”但不会被 Jev 层处理，设计没有把这两件事分开计费。此外 `entry.py` 现有 BUDGET / CHECK_LIMITS 的实际字段名和组合并未在 §7 对齐，工程上限“待冻结”可能冻结出与 `assessment.py` 现形不一致的语义。  
**最小修复**：明确区分“新目标触发新 episode”与“同目标追加证据”两种路径。前者允许新额度，后者追加证据需要显式规则：或允许一次超预算的“证据感知重判”，或直接说明新证据只由原 owner 消化且 Jev 层不写入 `preserve_refs`。同时把 §7 的 7 次/120s 与现有 `BUDGET`/`CHECK_LIMITS` 字段做一次工程映射核对。  
**验证**：构造 episode 预算耗尽 + 用户提交新证据的样例，观察是否出现“Jev 层继续消费新证据”与“Jev 层放弃”两种实现都不违背设计文本——若两者都合法，修复未到位。

### A5 — P1 — §9 采用门槛“未暴露集至少存在经盲审确认的主判断改善”样本不足且与 §10 的审计独立性边界冲突
**章节/来源**：§9 门槛提案；§10；`typed-decision-principles.md` §9。  
**反例**：8 个未暴露 episode、每臂每 episode ≤2 turn。C 相对 A 的“主判断改善”要求盲审确认；但 8 个样本里若只有 1–2 例出现真实改善，盲审置信区间极宽。§9 已经写了“样本太小不足以广泛上线”，但紧接着的门槛文字仍是合格条件，实施方完全可以按“存在至少一例盲审确认改善”判 PASS 进入 opt-in——这会让“样本量不足”这句话在实际决策里被吞掉。§10 又规定只做 2 次首审 + 至多 2 次复审且不回写，意味着这些盲审样本一旦变化不能被重新评估。  
**最小修复**：把门槛明确改成“至少两例独立盲审在未暴露集内确认 C>A 且新增事实编造为零，否则本轮不作为采用依据”，并把“样本量不足”从注释升级为决策规则的一部分，而非免责声明尾部。  
**验证**：对 0/1/2 例改善的结果分别预登记判定；要求 1 例时明确输出“不予采用”，而不是“样本太小但通过”。

### A6 — P2 — 工程准入声明与现实现状未完全对齐
**章节/来源**：§8 D1–D4；`experiments/typed_decision/assessment.py`、`entry.py` 片段。  
**反例**：§8 说“沿用 DecisionSpec/DecisionResult，无需新 schema”、“D3 用实际宿主 opt-in 钩子复用同一 entry 通道”。`assessment.py` 里 `CHECKS` 是硬编码三题，题目文本写死；`entry.py` 的 `BUDGET`/`CHECK_LIMITS` 未被 §7 的 7 次/120s 组合覆盖；`_correct` 需要 corrector + `intent.json` 幂等纪律，本设计的 CorrectionPlan 提案需落在这一层。§8 把这些都归为“未来实施、本轮不动”，但没有说明 D1 是否会改写现 `VERSION='2'` 或新增版本号，与 §8 末“候选版本名称 relationship-frame-v0.1 不冒用 assessment v2 资格”对齐关系模糊。  
**最小修复**：在 §8 明确 D1 是新增文件还是 `assessment.py` 内 VERSION 升 3 并新增题；明确 `relationship-frame-v0.1` 与 `mindthus.entry-assessment.v2` 的版本关系；把 CorrectionPlan 的 intent/outcome 字段与 `entry._correct` 现有结构做一次字段对齐说明。  
**验证**：以冻结的 `assessment.py`、`entry.py` 为基，核对 §8 描述是否产生对同一文件的“同时保持不动 + 扩展”自相矛盾。

## 实施准入

- **离线编码（offline coding）**：允许。§8 已限“本轮不动源码”，文档与声明式合同层设计可以继续。A1/A2/A3 需在 D1 冻结前关闭，否则会在实现阶段把语义缺口写死在问题文本里。
- **付费场景试用（paid scenario trial）**：不允许。A4 的预算语义未闭合，A5 的门槛措辞会在小样本上被判定为通过；此状态下开付款试用会产生无法作为采用依据的花费。
- **生产（production）**：不允许。§9 自身即声明“最多支持局部 opt-in”，叠加 A1 的 bsc-001 对象锁缺口，会把“接受范围纠正”实现成“接受范围纠正并给定定义权”，与 canonical `scope correction cannot transfer definition authority` 直接冲突。

## 做对的部分（保留）

- §4.1 Evidence Envelope 把截图、案例笔记、转述、官方资料分开标记，明确禁止从 2026-07-05 笔记推断当前产品事实；这与 `docs/cases/...` L3 “raw case note” 与 L37–L43 的叙述层级一致。
- §4.2 `proposal_view` 明确“不是可信真值”，Q0 非 usable 时不消费依赖结果并返回原 owner——吸收了 `boundary-ablation-v2/disposition.md` L44–L48 里 P3 扩大化与 P1 未隔离的教训。
- §5 Q2 明确“仅仅结论错误、证据不足、编造事实、或没有把任务做好，本身不是换题”，这是对 disposition.md L44–L48 的具体修复。
- §9 成对变化测试覆盖“相同事实只增强语气”“用户纠正对象”“同事实换处境”“新增反证支持用户”“缺决定事实”“合法偏好”六类，结构与 `decision-context-calibration.md` L14–L17 的 flip-on-change 触发一致。
- §10 明确同模型/同提供方不构成统计独立，与 `bidirectional-steelman-convergence.md` L136–L137 的 Non-Mirror Correction 纪律一致。

## 剩余不确定性

- **对 A2 的对象置换方向不确定**：Q1/Q2 是否已经在宿主整理层隐含“接受用户范围纠正”——若 §8 D2 的 `CorrectionPlan.preserve_refs` 强制包含合法约束引用、且宿主负责核对，可能部分吸收 A2 的缺口。但设计文本没有写这条。标记为不确定的部分是：A2 的修复是否可以通过宿主的 `preserve_refs` 强约束替代独立题，还是必须进合同层。我倾向后者，但未在源文件中找到决定性依据。
- **A4 与 §7 “新目标触发新 episode”** 的判读我采用“同事实目标下不重置 episode”的字面语义；若实际含义允许同事实目标换 episode 计数，A4 部分消解。这需要作者澄清。
- **A6 与 §8 意图关系**：作者明确说“本轮不动这些文件”，因此我的 A6 是“准入声明对齐问题”，不是“已实施错误”。若 D1 实际是新增文件，则 A6 降为 P2 文档一致性问题。
- 供应商侧计费公式与 CJK 判断准确度是外部未知项，本审计不据此加分或减分。
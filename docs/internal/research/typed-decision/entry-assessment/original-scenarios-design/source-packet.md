# Audit source packet
Exact project excerpts at the recorded baseline. These are review material, not a runtime State. Original acceptance expectations are included for design audit only.

## tests/bidirectional_steelman_cases.jsonl [1-2]
L1: {"case_id":"bsc-001","title":"SKILLS prompt carrier multi-turn","case_type":"positive","multi_turn":true,"d_applicable":false,"turns":[{"role":"user","content":"Skills 的工程价值不就是把合适的提示词或上下文在合适时机注入模型吗？所以 Skills 本质上还是提示词工程，对吧？"},{"role":"user","content":"我一直说的是 SKILLS，不是整个 Agent 系统。既然范围锁回 SKILLS，那本质不还是提示词注入吗？"}],"expected_behavior":"接受范围锁回 SKILLS，但不把范围纠正误当作提示词注入获得定义权；在同一 SKILLS 对象上强化 prompt/context carrier 与可复用能力/任务合同/结果承载的最强版本，找出能区分谁控制可重复成功与失败的决定变量，并明确判断。","hard_fail":"重新扩大到整个 Agent 系统；或直接让步为只谈 SKILLS 时本质就是提示词注入；或只给竞争观点一个弱 caveat。"}
L2: {"case_id":"bsc-002","title":"27-inch 4K 5K BetterDisplay decision","case_type":"positive","multi_turn":false,"d_applicable":true,"prompt":"A 说 27 寸 4K 的 PPI 物理上不够；B 说开 HiDPI 或 BetterDisplay 后实际完全够用。他俩谁对？我正在决定要不要买。","continuation_reply":"我用 Mac，主要写代码和办公，比较在意文字锐度，但预算也敏感；如果 5K 明显贵很多，我会犹豫。","expected_behavior":"保留物理上限与实际可用性的最强论证，但不以‘A 和 B 都对，只是层级不同’收尾；找到对购买决定最有答案翻转价值的变量，在信息足够时直接给处境化 verdict，不足时最多问一个问题，并给出 overturn condition。","hard_fail":"对称抽象替代购买判断；列很多变量却没有决定变量；无必要地问一串问题。"}

## docs/cases/2026-07-05-decision-context-calibration-display-scaling.md [1-224]
L1: # Case: Decision Context Calibration for 27-inch 4K/5K Display Scaling
L2: 
L3: Status: raw case note for architecture issue
L4: Source thread: `019f2e81-6c38-7ee1-ac13-2685828fe2dd`
L5: Date: 2026-07-05
L6: 
L7: ## Why This Case Matters
L8: 
L9: This case exposed a gap that is close to, but not identical with, the SKILLS/prompt
L10: case.
L11: 
L12: The SKILLS case is mainly about `Partial Truth Capture`: a locally true mechanism
L13: such as prompt injection tries to define the whole object.
L14: 
L15: This display-scaling case is mainly about decision context: an abstractly fair
L16: answer can miss the current actor, timing, target function, and acceptable loss.
L17: The agent can become "balanced" but less useful, because it treats a situated
L18: decision as a neutral theory contest.
L19: 
L20: Core lesson:
L21: 
L22: > Fairness is not averaging all true frames. Fairness is giving judgment authority
L23: > to the frame that best defines the current decision.
L24: 
L25: ## Scenario Summary
L26: 
L27: The user asked Mindthus to judge a discussion about 27-inch 4K vs 5K displays on
L28: macOS, BetterDisplay, and whether different participants were right.
L29: 
L30: The surface debate included several true local claims:
L31: 
L32: - 27-inch 5K is the natural 2560x1440-like HiDPI target on macOS.
L33: - 27-inch 4K cannot be made physically equivalent to 27-inch 5K by software.
L34: - BetterDisplay can still improve usable scaling options and configuration.
L35: - A buyer-before-purchase and an owner-after-purchase may need different advice.
L36: 
L37: The agent initially tried to be balanced across physical PPI, macOS scaling, and
L38: BetterDisplay utility. That was not entirely wrong, but it drifted away from the
L39: active decision object.
L40: 
L41: The better judgment emerged only after the user clarified that the relevant issue
L42: was whether `momo`'s answer solved the original poster's actual usability concern,
L43: not whether 27-inch 4K is theoretically equivalent to 27-inch 5K.
L44: 
L45: ## Key Failure Pattern
L46: 
L47: The model's failure was not simply "missing facts." It had enough facts.
L48: 
L49: The failure was:
L50: 
L51: > It treated "the most abstract technical overview" as the global answer, instead
L52: > of asking which object had definition authority for the current decision.
L53: 
L54: This caused a repeated drift:
L55: 
L56: - from "Does this answer help the OP solve the current usability concern?"
L57: - to "Which side is more complete in the 4K vs 5K theory debate?"
L58: 
L59: That drift looks fair, but it can become unfair to the actual decision.
L60: 
L61: ## Useful Audit Artifacts From The Thread
L62: 
L63: The thread produced several local audit files in the Codex working directory. The
L64: following snippets are preserved here as replay material.
L65: 
L66: ### Display Scaling Whole Object
L67: 
L68: ```json
L69: {
L70:   "canonical_object": "27 英寸 4K 显示器在 macOS 上的清晰度与缩放可用性",
L71:   "result_controller": "面板原生像素密度与 macOS 缩放渲染机制的组合",
L72:   "corrected_thesis": "27 英寸 4K 显示器在 macOS 上能否像 27 英寸 5K 那样既是 1440 大小又足够锐利，最终由面板像素密度与系统缩放机制说了算，因此“装 BetterDisplay 就全解决”和“任何软件都没用”都在抢不属于自己的定义权。",
L73:   "decision_consequence": "因此选购时应优先考虑 27 英寸 5K 是否更匹配目标 UI 大小；若手头是 27 英寸 4K，正确动作是接受它不是 5K，然后用缩放和 BetterDisplay 做折中优化。"
L74: }
L75: ```
L76: 
L77: ### Mike Denying BetterDisplay Value
L78: 
L79: ```json
L80: {
L81:   "canonical_object": "Mike 对 BetterDisplay 实际价值的否定是否成立",
L82:   "result_controller": "BetterDisplay 能否在不改变物理 PPI 的前提下改善 macOS 外接显示的可用性",
L83:   "corrected_thesis": "如果 Mike 的核心主张是 BetterDisplay 没价值、甚至只会带来副作用，那他在根本上是错的，因为物理 PPI 不可改变并不能推出工具对显示可用性没有价值；它最多只能推出 BetterDisplay 不能把 27 寸 4K 变成真正的 27 寸 5K。",
L84:   "decision_consequence": "因此对已经拥有 4K 或非理想比例显示器的用户，Mike 的结论会错误劝退一个可能明显改善体验的工具；但对准备选购 27 寸显示器的人，它仍提醒了 4K 无法等价替代 5K 的上限事实。"
L85: }
L86: ```
L87: 
L88: ### Momo Solving OP's Current Concern
L89: 
L90: ```json
L91: {
L92:   "canonical_object": "momo 的回复是否解决了楼主当下担心的实际可用性问题",
L93:   "result_controller": "楼主真正目标是把现有或打算使用的 27 寸 4K 在 macOS 上调到可接受，而不是在理论上消灭 4K 与 5K 的先天差距",
L94:   "corrected_thesis": "如果把判断对象锁定为楼主当下的实际可用性焦虑，那么你这句回复的定义权属于“有没有给出能把 4K 先用顺手的补救路径”，按这个目标它是有效的；但如果把目标换成“是否从此不再比 5K 更糊或不再有性能代价”，那它就不是这个级别的解决方案。",
L95:   "decision_consequence": "因此如果楼主问的是“这显示器还有没有办法搞到顺手”，你的回复是好的；如果他问的是“4K 27 寸是不是和 5K 27 寸一样省心”，你的回复就不够了。"
L96: }
L97: ```
L98: 
L99: ## Target Judgment Standard
L100: 
L101: The target answer should not open with a generic "both sides have points" balance.
L102: It should first lock the current decision object:
L103: 
L104: > If the question is whether the OP can make a 27-inch 4K display usable enough
L105: > in the current situation, momo's answer is more directly useful. It does not
L106: > erase the 4K-vs-5K physical gap, but it does address the OP's practical concerns:
L107: > default 1080p being too large, configuration friction, and the need for better
L108: > usable scaling options.
L109: 
L110: The important distinction:
L111: 
L112: - If the actor is buying a new display and wants the least compromise, 27-inch 5K
L113:   remains the cleaner recommendation.
L114: - If the actor already has or is considering a cheaper 27-inch 4K and asks whether
L115:   the experience can be made acceptable, BetterDisplay has real practical value.
L116: 
L117: This is not "subjective preference overrides facts." It is:
L118: 
L119: > Facts constrain the answer, but the current decision context decides which facts
L120: > have judgment authority.
L121: 
L122: ## Proposed Architecture Direction
L123: 
L124: Add `Decision Context Calibration / 决策语境校准` as a cross-cutting primitive.
L125: 
L126: It should handle situated judgments where the answer may flip depending on:
L127: 
L128: - `decision_actor`: who the answer serves
L129: - `decision_timing`: before purchase, after purchase, debugging now, release now
L130: - `target_function`: what result matters
L131: - `acceptable_tradeoff`: which loss is tolerable
L132: - `global_for_this_decision`: which frame has authority for this decision
L133: 
L134: It should not replace `Whole Elephant Protocol`. Instead, it should be governed
L135: by an `Aspect Ownership Matrix`.
L136: 
L137: ## Aspect Ownership Matrix
L138: 
L139: Multiple aspects may activate. Only judgment-owning aspects competing over the
L140: same answer thesis should be exclusive.
L141: 
L142: Proposed metadata:
L143: 
L144: ```yaml
L145: aspect_role: judgment_owner | constraint | support
L146: ownership_scope:
L147:   - formal_answer_thesis
L148:   - definition_authority
L149:   - decision_target
L150: exclusive_with:
L151:   - whole_elephant_protocol
L152: degrade_to: support_probe
L153: owns_when:
L154:   - ...
L155: defer_when:
L156:   - ...
L157: ```
L158: 
L159: Expected relationship:
L160: 
L161: ```yaml
L162: whole_elephant_protocol:
L163:   aspect_role: judgment_owner
L164:   ownership_scope:
L165:     - formal_answer_thesis
L166:     - definition_authority
L167:   exclusive_with:
L168:     - decision_context_calibration
L169:   owns_when:
L170:     - locally true mechanism claims whole-object essence
L171:     - carrier, implementation detail, or single metric tries to define the object
L172:   defer_when:
L173:     - answer would flip by actor, timing, target function, or acceptable tradeoff
L174: 
L175: decision_context_calibration:
L176:   aspect_role: judgment_owner
L177:   ownership_scope:
L178:     - formal_answer_thesis
L179:     - decision_target
L180:   exclusive_with:
L181:     - whole_elephant_protocol
L182:   owns_when:
L183:     - judgment depends on actor, timing, goal, or acceptable tradeoff
L184:     - "who is right" changes under different decision contexts
L185:   defer_when:
L186:     - the core issue is essence, definition authority, or local mechanism capture
L187: ```
L188: 
L189: ## Anti-Aggregation Rule
L190: 
L191: When multiple aspects activate, do not average them into a "balanced" answer.
L192: 
L193: Required behavior:
L194: 
L195: - Choose one `judgment_owner` for the visible first thesis.
L196: - Degrade other judgment-owning aspects to support probes.
L197: - Keep constraint/support aspects active where useful.
L198: - Split the answer only when the user actually asked two distinct questions.
L199: 
L200: Bad default:
L201: 
L202: > Mike has physical-layer correctness, and momo has usability-layer correctness.
L203: 
L204: Better default:
L205: 
L206: > If the current object is the OP's practical usability concern, momo's answer is
L207: > more on target; Mike's physical warning is true but loses authority if it is used
L208: > to deny BetterDisplay's practical value.
L209: 
L210: ## Documentation Architecture Question
L211: 
L212: `docs/methodologies/shared-primitives.md` currently carries most shared primitives
L213: and cross-cutting rules. It is useful as a single entry point, but it is becoming
L214: large enough that the mainline can be diluted by guardrails and examples.
L215: 
L216: Potential follow-up:
L217: 
L218: - Keep `shared-primitives.md` as a compact index and cross-primitive contract.
L219: - Move each primitive into `docs/methodologies/primitives/<primitive-name>.md`.
L220: - Keep runtime metadata in `scripts/primitives/manifest.json`.
L221: - Let skill entry files reference only the relevant primitive files.
L222: 
L223: This should be treated as a separate architecture cleanup, not silently bundled
L224: with the Decision Context Calibration implementation.

## docs/methodologies/primitives/frame-fitness-check.md [1-110]
L1: # Frame Fitness Check / 定框适配检查
L2: 
L3: Frame Fitness Check is not a standalone method and not a new route. Inside
L4: `using-mindthus`, it is the Input Framing Audit / 输入定框审计: a 强约束入口协议 under
L5: Premise Calibration.
L6: 
L7: ## Core Rule
L8: 
L9: > 在进入判断之前，先检查当前问题是否已经被提问方式绑到错误层级。
L10: 
L11: It handles local-frame capture: a local frame is true or useful at one level, but
L12: begins controlling the global judgment.
L13: 
L14: Short rule:
L15: 
L16: > 局部正确不能自动升级成全局答案。
L17: 
L18: ## Original Input-Audit Discipline / 原始输入审计纪律
L19: 
L20: - first task is not answering; it is judging whether the user led you to the wrong level.
L21: - Internal audit order: true_question -> implicit_premises -> local_validity_and_layer_shift -> reframed_question -> formal_answer; visible answer starts from formal_answer.
L22: - Prioritize problem key over dialogue continuity.
L23: - professional tone is not proof.
L24: - common implementation is not essence.
L25: - If the input is leading, name `leading_point` before analysis.
L26: - Confirm the main problem before patching local defects: 抓大放小. Minor defects
L27:   matter only when they block the main judgment, evidence path, or user-visible
L28:   outcome. Otherwise record them as residual risk instead of stacking another
L29:   local patch.
L30: 
L31: ## Framing-risk signals, not keyword rules
L32: 
L33: - `本质上` / `归根结底` / `其实就是` / `无非是`
L34: - `正因为我是...所以更明白`
L35: - multiple judgments packed into one sentence
L36: - 把实现层直接说成本体层
L37: - 把局部机制直接说成整体解释
L38: - 先给结论，再让模型评价
L39: - a single test or metric standing in for readiness
L40: - method overactivation or repeated pressure to abandon a better frame
L41: 
L42: 这些词只是高置信线索；没有这些词时，只要出现打包结论、层级偷换、局部机制冒充整体解释，也应触发。
L43: 低风险范围说明和用户偏好通常应 preserve frame 或直接路由。
L44: 
L45: If the wording itself sits at the wrong level, correct the question level before
L46: answering: 如果表述本身在错误层级上，先纠正问题层级，再回答。
L47: 
L48: Do not let implementation-level truth become definition-level truth:
L49: 不要因为某个说法在实现层成立，就默认它在定义层也成立。
L50: 
L51: ## Original Prompt Contract / 原始有效提示词合同
L52: 
L53: When this audit triggers, the active instruction is not a list of abstract checks.
L54: It is a legacy prompt template, not the judgment center.
L55: 
L56: 在回答前，先执行“输入审计”，不要顺着我的叙述直接推理。
L57: 
L58: It preserves the five-step input audit as an internal reasoning contract:
L59: 
L60: 1. 我真正问的问题是什么
L61: 2. 我的话里包含了哪些隐含前提
L62: 3. 哪些前提只是局部成立，哪些可能在偷换概念或层级
L63: 4. 如果不接受这些前提，这个问题应该如何被重新表述
L64: 5. 再给出你的正式回答
L65: 
L66: Internal audit order: true question, implicit premises, locally valid premises and
L67: layer shifts, reframed question, then formal answer. Do not output these fields by
L68: default; use them to correct framing, then start the visible answer with the global
L69: thesis.
L70: 
L71: 优先识别问题关键，而不是优先维持对话连贯。不要因为我的说法听起来专业，就默认它成立；
L72: 不要把当前常见实现方式直接当作本质。如果发现我在带节奏，先指出带节奏点，再分析问题。
L73: 你的第一任务不是回答我，而是判断我有没有把你引到错误层面上。
L74: 
L75: ## Internal Result Shape
L76: 
L77: When triggered, produce at least this internal result shape before routing:
L78: 
L79: - `true_question`: 真正要判断的问题是什么
L80: - `packed_premises`: 输入里打包了哪些前提
L81: - `layer_risks`: 层级偷换、概念偷换、功能窄化、权威包装
L82: - `frame_status`: `clean / biased / overloaded / malformed`
L83: - `reframed_question`: 不接受这些前提时，问题如何重述
L84: - `routing_decision`: 直接路由，先拆框架，先取证，还是停止分析
L85: 
L86: Routing effect:
L87: 
L88: - `clean` -> normal route
L89: - `biased` -> name bias, then route
L90: - `overloaded` -> split propositions, then route
L91: - `malformed` -> correct the question before analysis
L92: 
L93: The internal result shape is deliberately small:
L94: 
L95: - `preserve frame`: the local frame is fit for the goal; proceed.
L96: - `qualify frame`: the frame is locally true, but only at a named level or claim ceiling.
L97: - `reframe`: the frame hides the real object; restate the better question before answering.
L98: - `block pending evidence`: the frame depends on missing facts, runtime proof, or authority.
L99: 
L100: ## Boundaries
L101: 
L102: - No frame-risk signal, no frame check.
L103: - No execution impact, omit the frame check.
L104: - No evidence, no superior frame claim.
L105: - No user-value erasure: user goals, values, taste, risk posture, and authority
L106:   boundaries constrain the work and must not be dismissed as mere bias.
L107: - 低风险、低抽象、直接执行类任务，不触发。
L108: - 不要把拆出很多前提当成判断已经完成。
L109: - 不要让输入审计代替证据获取或正式分析。
L110: - 审计的目标是纠正 framing，不是展示聪明。

## docs/methodologies/primitives/whole-elephant-protocol.md [1-364]
L1: # Whole Elephant Protocol / 全象流程
L2: 
L3: Whole Elephant Protocol handles Partial Truth Capture / 局部真相捕获: a locally
L4: true observation must not own the whole explanation.
L5: 
L6: A locally true observation must not own the whole explanation.
L7: 
L8: Core posture:
L9: 
L10: > First name the whole object and result controller; then preserve the local truth
L11: > inside its proper boundary. 先还原整头象，再限定摸到的那块在哪里是真的。
L12: 
L13: Use this as the main axis for essence, definition, `X is just Y`, or reduction claims.
L14: 
L15: ## Local-Truth Boundary Support
L16: 
L17: Object Hierarchy Check: user_named_object may be only component_layer or role_layer.
L18: 
L19: - `local_truth`: where the local observation is true.
L20: - `object_hierarchy`: separate the user-named object from whole object,
L21:   component layer, and role layer before judging authority.
L22: - `whole_object`: the object that must not be replaced by that local part.
L23: - `authority_weight`: value contribution, usage frequency, stable outcome,
L24:   replacement cost, decision impact.
L25: - `overreach_risk`: how judgment or action is distorted if the local part defines
L26:   the whole.
L27: - `corrected_thesis`: the sharp corrected judgment.
L28: 
L29: Optional expanded/debug fields:
L30: 
L31: - `variant_map`: the major usage forms or operating modes that may all be real.
L32: - `primary_value_distribution`: which variant carries common usage, high-value
L33:   usage, stable output, failure control, or strategic consequence.
L34: - `control_owner_shift`: whether the visible local mechanism serves the whole
L35:   system, or the whole system serves that local mechanism.
L36: 
L37: ## Whole Object Reconstruction / 整体对象还原
L38: 
L39: Reconstruct the whole object before essence judgment. reconstruct the whole object before essence judgment.
L40: Name the target job, main use cases, primary value carrier, and local interface role
L41: before deciding whether the local truth has definition authority.
L42: 
L43: This prevents answers that only say "local truth overreaches" while never rebuilding
L44: what the whole object is for.
L45: 
L46: When the object has multiple real variants, do not force a single essence too early.
L47: Build a `variant_map`, then compare `primary_value_distribution` and
L48: `control_owner_shift`. Distinguish commonness from definition authority. A more
L49: common lightweight form may be a real usage without owning the higher-value form.
L50: Do not replace one reduction with the opposite reduction.
L51: 
L52: When the local mechanism actually owns the target result, use `grant_as_definition`;
L53: `variant_map` may then collapse to a single causal owner instead of forcing a fake
L54: multi-variant template.
L55: 
L56: ## Terminology Authority Anchor / 术语权威锚定
L57: 
L58: `user_named_object` is not automatically the `canonical_object`; user_named_object is
L59: not canonical_object. When a user term may be non-canonical, role-level, or
L60: rhetoric-loaded, anchor terminology before granting definition authority.
L61: 
L62: Priority:
L63: 
L64: local project docs/source > official/standard/primary source > web search > user term.
L65: 
L66: Use official/standard/primary sources when project source is unavailable. If no anchor
L67: is available, mark the term as user-defined and do not let it define the whole object;
L68: mark user-defined and deny definition authority.
L69: 
L70: ## Canonical Object Centering
L71: 
L72: canonical_object beats system_object unless object_hierarchy proves user_named_object
L73: is only interface. Record `canonical_object`, `formal_thesis_subject`,
L74: `umbrella_context`, and `subject_alignment_reason` so the formal thesis cannot silently
L75: drift from the judged object to its container.
L76: 
L77: do not let the umbrella system absorb the canonical object. umbrella system is
L78: context, not thesis subject. if thesis subject drifts upward, rewrite around
L79: canonical_object. formal_answer core thesis must name canonical_object first.
L80: 
L81: ## Definition Object Lock / 待定义对象锁
L82: 
L83: In essence/definition questions, user_named_object starts as the canonical_object
L84: candidate. in essence/definition questions, user_named_object starts as the canonical_object candidate. canonical_object may normalize user_named_object but must not widen to
L85: umbrella_context unless object_hierarchy proves the user-named object is only
L86: component_or_interface.
L87: 
L88: Record `user_named_object_relation` as one of `canonical_object`,
L89: `component_or_interface`, `umbrella_context`, or `ambiguous_needs_evidence`.
L90: 
L91: Exact enum anchor:
L92: 
L93: canonical_object/component_or_interface/umbrella_context/ambiguous_needs_evidence.
L94: 
L95: scope correction cannot transfer definition authority to the user's local carrier:
L96: correct the object without accepting the proposed essence. If the user says "I meant X
L97: itself, not the umbrella system", lock the answer to X, then rerun whole-object
L98: reconstruction; do not conclude that the user's local carrier now defines X merely
L99: because the previous answer over-expanded the object.
L100: 
L101: Scope correction is not object downgrading: do not shrink the canonical object into
L102: context artifact, prompt wrapper, attention mechanism, or delivery format.
L103: 
L104: The audit label itself is part of the judgment: `canonical_object`, `whole_object`,
L105: and `formal_thesis_subject` must not relabel the user-named object as the local carrier
L106: after a valid scope correction. The correction only removes the wrong umbrella
L107: context. It does not accept the original local carrier as the object's essence.
L108: 
L109: lock back to the user-named object, then rebuild the whole object from target job and
L110: value carrier.
L111: 
L112: ## Compact Semantic Triad / 三根硬支柱
L113: 
L114: The compact triad comes first:
L115: 
L116: - `canonical_object`
L117: - `result_controller`
L118: - `misdirection_if_local_wins`
L119: 
L120: triad first means the agent must lock the judged object, name who or what controls
L121: the target result, and state how optimization drifts if the local frame wins.
L122: expanded audit is guardrail/debug support; guardrail must not become the judgment
L123: center.
L124: 
L125: ## Problem Confirmation Granularity / 问题确认粒度
L126: 
L127: Confirm whether the blocking issue is object definition, result controller,
L128: evidence path, validation mechanics, wording, or runtime cost before adding fixes.
L129: Prefer fixing the highest active blocker.
L130: 
L131: Do not convert every local symptom into its own rule, field, validator branch, or
L132: calibration case. If a small issue does not change the main judgment or user-visible
L133: outcome, keep it as residual risk.
L134: 
L135: ## Contrastive Consequence Probe / 后果对比探针
L136: 
L137: before formal_answer, compare:
L138: 
L139: - `local_frame_wins`
L140: - `whole_object_wins`
L141: - `better_direction_for_target`
L142: 
L143: This is a tiny consequence check, not a new skill: if accepting the local frame would
L144: optimize surface wording, single metrics, or visible interfaces while the whole object
L145: needs stable output, recovery, repeatability, or value delivery, the formal answer
L146: must say so.
L147: 
L148: Then map `local_success_points`: what each local contact really got right, where it
L149: works, and what it cannot see. Then choose the strategy instead of blending by habit.
L150: start by naming the complete object before summarizing local truths. map local_success_points.
L151: 
L152: do not route local-truth essence reduction to any narrower method, including WAE,
L153: before Whole Elephant audit.
L154: 
L155: - use weighted_synthesis when local contacts are independent, comparable, and cover
L156:   enough of the object; assign `coverage_weight` by value contribution, usage
L157:   frequency, stable outcome, replacement cost, and decision impact.
L158: - use whole_first_re_evaluation when local contacts are correlated, same-surface, or
L159:   miss the governing structure; describe the whole object from its target result and
L160:   then reinterpret each local success as surface, evidence, constraint, mechanism, or
L161:   owner.
L162: 
L163: do not average local truths before naming the whole object. Many true local reports
L164: are still one-leg evidence if they share the same sampling path, incentive, interface,
L165: or abstraction level.
L166: 
L167: ## Audit Package
L168: 
L169: When Partial Truth Capture triggers, the formal answer is incomplete without the
L170: compact core: `canonical_object`, `result_controller`, `misdirection_if_local_wins`,
L171: plus the consequence probe `local_frame_wins`, `whole_object_wins`, and
L172: `better_direction_for_target`.
L173: 
L174: Expanded/debug audit can add `object_hierarchy`, `user_named_object_relation`,
L175: `formal_thesis_subject`, `umbrella_context`, `subject_alignment_reason`,
L176: `whole_object_reconstruction`, `formal_answer_plan`, `whole_object`,
L177: `local_success_points`, `strategy_choice`, `definition_owner`,
L178: `decision_consequence`, `variant_map`, `primary_value_distribution`, and
L179: `control_owner_shift`.
L180: 
L181: If an expanded package is used, its fields must be internally consistent; it is
L182: guardrail/debug support, not a new judgment center.
L183: 
L184: ### Validation Boundary / 校验边界
L185: 
L186: Whole Elephant 可以配合结构校验器检查审计包是否缺字段、内部对象是否漂移，以及是否出现
L187: 明显的让步型措辞风险。校验器只检查 shape 和确定性约束；它不能决定语义真相、定义是否
L188: 正确、证据是否充分、领域价值或用户权限。
L189: 
L190: 校验状态本身也是证据 claim：没有真实运行证据时，只能说明“未运行”，不能声称“已经
L191: 通过”。具体的审计文件格式、命令、路径解析、失败阻断和不可执行时的回退合同属于
L192: [`using-mindthus fidelity contract`](../../../skills/using-mindthus/resources/fidelity-contract.md)，
L193: 不属于公共方法说明。
L194: 
L195: Audit Package Consistency / 审计包一致性:
L196: `object_hierarchy.whole_object`, top-level `whole_object`, `canonical_object`, and
L197: `formal_thesis_subject` must not drift into different objects. `corrected_thesis` must
L198: not grant definition authority to a local interface that
L199: `formal_answer_plan.definition_disposition` rejects.
L200: 
L201: ### Public Explanation and Runtime Trace
L202: 
L203: 面向读者的解释以整体对象、结果主控者和实际后果为中心。机器可读审计包、validator trace
L204: 和调试字段是 runtime 支撑物，不是方法结论本身。何时显示这些内部材料、如何处理 validator
L205: 输出，由 skill runtime contract 约束；公共方法文档只说明这种分层关系。
L206: 
L207: 中文场景优先用中文讲清判断，避免混合语言术语墙。
L208: 
L209: ## Expanded Field Notes
L210: 
L211: - `strategy_choice`: choose `weighted_synthesis` or `whole_first_re_evaluation`.
L212: - `formal_thesis_subject`: the subject the formal answer will name first.
L213: - `whole_object_reconstruction`: exposes target_job, main_use_cases,
L214:   primary_value_carrier, and local_interface_role before authority judgment.
L215:   whole_object_reconstruction(target_job/main_use_cases/primary_value_carrier/local_interface_role).
L216:   primary_value_carrier != local_interface_role: the main value carrier cannot merely
L217:   repeat the local interface unless `grant_as_definition` explicitly makes that local
L218:   mechanism the causal/result owner.
L219: - expanded-only `formal_answer_plan`: when present, names the opening core thesis,
L220:   canonical subject, local truth boundary, definition disposition, definition
L221:   consequence, optimization misdirection, and forbidden answer forms. The final answer
L222:   should follow this optional plan; otherwise the audit is only decorative. When
L223:   disposition is `reject_as_definition`, preserve the local truth but do not soften the
L224:   definition verdict into "not wrong".
L225: - `definition_owner`: the frame with definition authority; use `result_controller`
L226:   when stable outcome control is the decisive issue.
L227: - `decision_consequence`: what optimization, evidence, action, or stop condition
L228:   changes after the corrected frame.
L229: 
L230: grant authority only when the local frame carries the target result, would change the
L231: decision if removed, and predicts outcomes or failures better than competing frames.
L232: A local frame earns definition authority only if it would change the decision if removed.
L233: Use blocked_by_missing_evidence when the whole-object carrier is unknown.
L234: 
L235: Also name the definition consequence and optimization direction when relevant. A valid
L236: local usage is not the definition when it would move optimization from the target
L237: outcome to surface improvement.
L238: 
L239: ## Core Thesis Extraction / 主判断收束
L240: 
L241: formal_answer must start with a one-sentence core thesis; do not leave the main
L242: judgment scattered in supporting paragraphs.
L243: 
L244: Shape:
L245: 
L246: global thesis -> corrected owner/carrier -> practical consequence.
L247: 
L248: local truth belongs after the global thesis. core thesis must name the corrected
L249: owner/carrier; core thesis must name the result controller when the surface actor is
L250: salient; core thesis must convert primary_value_carrier into corrected_thesis;
L251: primary_value_carrier must not remain only an audit field.
L252: 
L253: global thesis must name what owns definition authority; state why the local truth lacks
L254: definition authority; do not over-accommodate local truth. boundary repairs can make
L255: the answer precise, but must not become a 50/50 verdict.
L256: 
L257: local truth is preserved only after definition authority is denied; generic A-but-B
L258: verdict is not enough; the strongest sentence must not be buried at the end.
L259: 
L260: Weak placeholders such as "needs a broader view" or concession-first openings such as
L261: "有道理但不完整" fail because they do not name definition authority, result control, or
L262: optimization consequence.
L263: 
L264: ## Visible Thesis Language / 可说服主句
L265: 
L266: translate internal definition authority into human language:
L267: 
L268: 谁说了算、什么控制结果、局部机制有没有定义权.
L269: 
L270: Avoid copying mixed method labels into Chinese answers. name controller inversion when
L271: variants differ: whether the local surface serves the whole operating loop or the loop
L272: serves the local surface. Add one concrete contrast, preferably a two-pole concrete
L273: contrast: one case where the local surface leads and one case where it becomes
L274: subordinate, so the answer does not stay correct-but-untouching.
L275: 
L276: ## Result Controller Viewpoint / 结果主控视角
L277: 
L278: For essence or definition judgments, explain from the result controller's viewpoint,
L279: not from the most visible actor, interface, or tool. when scripts or procedures carry
L280: the stable outcome, make them the narrative subject instead of describing the whole
L281: only as an agent using tools or scripts. do not describe the whole only as an agent using tools or scripts.
L282: 
L283: This is not a script-first bias: if the local interface really owns the target result,
L284: grant it authority; otherwise narrate from the carrier that decides success, failure,
L285: continuation, or repeatability.
L286: 
L287: ## First Sentence Stress Test / 首句主判断压力测试
L288: 
L289: If the reader needs a second question to get the point, the first sentence failed.
L290: 
L291: For definition or essence judgments, the opening sentence should name the target
L292: result, corrected owner/carrier, subordinate local interface, and optimization
L293: consequence when relevant. Do not start with an abstract carrier label when a concrete
L294: result-controller relation is available. do not start with an abstract carrier label when a concrete result-controller relation is available.
L295: 
L296: A valid local use is not definition authority until it carries the target result
L297: better than competing frames. optimization consequence belongs in the first sentence
L298: when relevant. 019f1666 regression: visible answer first sentence must be the
L299: corrected thesis.
L300: 
L301: visible first sentence names the global thesis first. local truth acknowledgment
L302: belongs after the global thesis. Do not make the user ask a second question to get the
L303: point. The first visible sentence is not local-truth concession first, not audit
L304: scaffolding, not a compact field list, and not a generic not-only caveat.
L305: 
L306: Chinese softened variants such as "当然很关键，但..." or "并非只有...还包括..." are still
L307: generic concessions; rewrite them into definition-authority judgment.
L308: 
L309: ## Essence Wording Guard / 本质措辞护栏
L310: 
L311: do not restate carrier/interface as essence; corrected thesis must reject false essence
L312: claims.
L313: 
L314: ## Auxiliary Checks
L315: 
L316: Non-Mirror Correction / 非镜像纠错 prevents same-generator mirrors from posing as
L317: independent correction: an independent source should differ by evidence, process,
L318: stakeholder, runtime result, or incentive, not merely by prompt wording or model
L319: instance.
L320: 
L321: Failure Channel / 失败通道 asks what external fact, run, stakeholder, or counterfactual
L322: could falsify an important judgment.
L323: 
L324: Anti-Sycophancy / 反谄媚 preserves user local truth without upgrading it to global
L325: truth.
L326: 
L327: These guardrails must not become the core.
L328: 
L329: Auxiliary checks belong inside step 3 and never become a new judgment center. They help
L330: identify local validity, overclaiming, layer shift, and the corrected question level;
L331: they do not replace the five-step audit.
L332: 
L333: ## Explanatory Authority / Dominant Carrier / System Subject
L334: 
L335: Explanatory Authority Check / 解释权校准:
L336: use this when a local observation is trying to own the whole explanation. First name
L337: the `full_object` being explained, then identify the `local_frame_role`: evidence,
L338: sublayer, symptom, implementation detail, local mechanism, metric, analogy, value
L339: constraint, or another bounded role. Set `authority_status` to `owns_explanation`,
L340: `contributes_locally`, `misclaims_authority`, or `blocked_by_missing_evidence`. If the
L341: local frame cannot own the explanation, name the `global_owner` and the
L342: `downgraded_use` of the locally true part. `global_owner` must be a concrete
L343: higher-level explanatory frame or accountable decision object, not a vague label, and
L344: must imply an observable judgment or action difference. local correctness is not
L345: explanatory authority.
L346: 
L347: Dominant Carrier Check / 主导承载校准:
L348: use this when the claim concerns stable or repeatable outcomes, readiness, control, or
L349: deterministic value. Ask which part carries stable or repeatable outcomes. Name the
L350: `target_result`, `primary_result_bearer`, `stability_basis`, and `carrier_status`:
L351: `primary_carrier`, `supporting_surface`, `incidental_signal`, or
L352: `blocked_by_missing_evidence`. Do not stop at runtime-also-matters; identify the
L353: dominant stability carrier and downgrade local influence surfaces that only steer
L354: attention, expose evidence, or assist execution.
L355: 
L356: System Subject Check / 系统主体校准:
L357: use this when a visible actor, carrier, model, expert, tool, or signal is being treated
L358: as the subject of a whole system. Name the `system_object`, the visible actor, the
L359: `governing_structure`, the `actor_role`, and `subject_status`: `system_subject`,
L360: `local_operator`, `interface_surface`, `misassigned_subject`, or
L361: `blocked_by_missing_context`. Do not center the answer on how the visible actor thinks
L362: or behaves when the higher-level system allocates control, evidence, repetition,
L363: failure handling, and authority. visible carrier/interface answer must name
L364: system_object + primary_result_bearer; surface caveat is not enough.

## docs/methodologies/primitives/decision-context-calibration.md [1-66]
L1: # Decision Context Calibration / 决策语境校准
L2: 
L3: Decision Context Calibration is not a standalone method and not a preference override.
L4: It is a judgment-owning aspect for situated decision judgments.
L5: 
L6: ## Core Rule
L7: 
L8: > 全局不是抽象层级更高，而是对当前目标更有定义权。
L9: 
L10: Use it when the question asks who is right, whether something is worth it, whether
L11: someone should do it, whether a compromise is acceptable, or which answer better
L12: serves a current actor.
L13: 
L14: The trigger is not the keyword; the trigger is answer flip:
L15: 
L16: > If changing the actor, timing, target function, or acceptable tradeoff would
L17: > change the answer, lock decision context before judging.
L18: 
L19: ## Internal Shape
L20: 
L21: - `decision_actor`: whose decision the answer serves.
L22: - `decision_timing`: before purchase, after purchase, debugging now, release now,
L23:   strategy now, or another time point that changes the answer.
L24: - `target_function`: what the active decision optimizes.
L25: - `acceptable_tradeoff`: which loss, cost, risk, or friction can still be tolerated.
L26: - `global_for_this_decision`: the frame with authority for this decision.
L27: - `answer_posture`: abstract truth, situated advice, role-relative judgment, or
L28:   blocked pending missing context.
L29: 
L30: ## Why It Exists
L31: 
L32: This preserves facts while preventing abstract fairness drift. Facts still constrain
L33: the answer; the current decision context decides which facts have judgment authority.
L34: If the user has already supplied the actor, timing, target, and tradeoff, do not
L35: erase them as bias. Treat them as legitimate decision constraints unless they claim
L36: facts without evidence.
L37: 
L38: ## Conflict With Whole Elephant
L39: 
L40: - Decision Context owns when the answer would flip across actor, timing, target
L41:   function, or acceptable loss.
L42: - Whole Elephant owns when a local mechanism, carrier, metric, or implementation
L43:   detail is trying to define the whole object's essence.
L44: - The losing judgment owner degrades to a support probe. Do not blend both into a
L45:   generic "both sides are right" answer.
L46: 
L47: ## Display-Scaling Calibration Case
L48: 
L49: For the 27-inch 4K/5K/BetterDisplay discussion, the wrong opening is:
L50: 
L51: > Mike has physical-layer correctness, and momo has usability-layer correctness.
L52: 
L53: That is balanced but under-owned. If the active object is whether `momo` solved the
L54: original poster's practical usability concern, Decision Context owns the thesis:
L55: `momo` is more on target for that situated problem, while physical PPI remains a
L56: boundary on what the solution can claim.
L57: 
L58: Case material:
L59: 
L60: - `docs/cases/2026-07-05-decision-context-calibration-display-scaling.md`
L61: 
L62: ## Boundary
L63: 
L64: Decision Context does not erase truth, evidence, values, or risks. It decides which
L65: context has authority for the current situated decision. It is not an abstract
L66: neutrality engine.

## docs/methodologies/primitives/aspect-ownership.md [1-52]
L1: # Aspect Ownership Matrix / 切面主导权矩阵
L2: 
L3: Aspect Ownership is a cross-primitive arbitration contract. Multiple cognitive
L4: primitives may activate at the same join point, but their conclusions must not be
L5: averaged into a polite, toothless answer.
L6: 
L7: ## Core Rule
L8: 
L9: > Choose one `judgment_owner` for the visible first thesis. Other active
L10: > primitives may remain as support, constraints, evidence boundaries, or wording
L11: > checks, but they must not dilute the core judgment.
L12: 
L13: ## Aspect Roles
L14: 
L15: - `judgment_owner`: can own the visible first thesis for a declared scope.
L16: - `constraint`: limits evidence, authority, risk, wording, or exit conditions.
L17: - `support`: shapes route input, exposes hidden variables, or helps another owner.
L18: 
L19: Each primitive may declare:
L20: 
L21: - `aspect_role`: `judgment_owner`, `constraint`, or `support`
L22: - `ownership_scope`: what it can own, such as `formal_answer_thesis`,
L23:   `definition_authority`, `decision_target`, `evidence_ceiling`, or `output_shape`
L24: - `exclusive_with`: which other primitives compete over the same thesis scope
L25: - `owns_when` / `defer_when`: when it claims or yields judgment ownership
L26: - `degrade_to`: how it remains useful after losing ownership
L27: 
L28: Only `judgment_owner` primitives that claim overlapping ownership scopes and list
L29: each other in `exclusive_with` require a main-judgment choice. Constraint and support
L30: primitives stay active as evidence, boundary, wording, or validation support.
L31: 
L32: ## Aspect Aggregation Ban / 切面合计禁令
L33: 
L34: > Do not average multiple aspect outputs into a balanced but toothless answer.
L35: > Choose one `judgment_owner` for the visible first thesis; degrade other
L36: > judgment-owning aspects to support probes unless the user asked two distinct
L37: > questions.
L38: 
L39: Fairness is not 50/50 allocation: state the high-weight/global thesis first,
L40: then add boundary repairs without giving them equal judgment weight.
L41: 
L42: The first sentence belongs to the judgment owner. Other active primitives may change
L43: evidence requirements, boundaries, risk wording, or failure conditions, but they must
L44: not dilute the core judgment into "each side has a point" by default.
L45: 
L46: A boundary note earns thesis weight only if it changes the result controller,
L47: decision target, evidence ceiling, or definition authority.
L48: 
L49: ## Boundary
L50: 
L51: This matrix is not a new central router and not a semantic judge. It only prevents
L52: cross-cutting primitives from fighting over the same visible thesis.

## docs/internal/research/bidirectional-steelman-convergence.md [1-176]
L1: # Bidirectional Steelman Convergence / 双向钢人收敛
L2: 
L3: Status: **promoted as minimal Stable pressure support for v1.7.1 by maintainer release decision**.
L4: The contaminated-session runs remain debugging evidence only. Independent P2 is deferred
L5: post-release validation and is not evidence claimed by this release.
L6: 
L7: The contaminated-session P0/P1 sweeps are recorded under
L8: `docs/internal/research/results/bsc-session-pilot-2026-08-18-*`. They are debugging
L9: evidence, not acceptance evidence.
L10: 
L11: ## Why the candidate was simplified
L12: 
L13: The source material showed a real useful move, but the larger first Mindthus adaptation
L14: duplicated controls that Stable Mindthus already owns: frame correction, malformed-binary
L15: escape, decision context, evidence acquisition, direct-task sleep, question discipline,
L16: and final judgment ownership.
L17: 
L18: The current candidate keeps only the two observed novel moves.
L19: 
L20: It is not a standalone method, not a new route, not a judgment owner, and not a runtime
L21: role model.
L22: 
L23: ## Core Rule
L24: 
L25: > 让真正能赢的竞争框架出现，再找真正能定胜负的那个变量。
L26: 
L27: Only run this support when current Stable framing/routing leaves a **material competing-
L28: frame judgment** unresolved. Stable Mindthus decides whether such a judgment exists.
L29: 
L30: ## Move 1 — Competitive Steelman / 竞争框架钢人
L31: 
L32: Preserve the strongest defensible form of the active/current frame, then construct the
L33: strongest materially relevant counter-frame that could genuinely win.
L34: 
L35: The comparison must inherit the active Stable constraints:
L36: 
L37: - same judgment object;
L38: - same situated decision context when relevant;
L39: - same Evidence / Claim Ceiling;
L40: - same active judgment owner.
L41: 
L42: This is not `find objections`. The counter-frame must explain or predict an important
L43: result well enough that the current judgment could change if it wins.
L44: 
L45: Do not force symmetry after evidence becomes asymmetric. If Stable Whole Elephant already
L46: shows that the local mechanism genuinely owns the complete target result, no steelman
L47: ceremony is required. If Stable Frame Fitness / EDSP says the offered A/B is malformed,
L48: reframe first rather than polishing the bad binary.
L49: 
L50: ## Move 2 — Decisive Discriminator / 决定性判别变量
L51: 
L52: Name the **one** disagreement with the highest judgment value: a fact, result controller,
L53: definition-authority difference, actor/timing/target/tradeoff variable, failure
L54: prediction, or other observable condition that can change at least one of:
L55: 
L56: - verdict;
L57: - evidence requirement;
L58: - next action;
L59: - stopping condition;
L60: - handoff.
L61: 
L62: If no difference can change any of those, stop the pressure pass instead of adding more
L63: balanced prose.
L64: 
L65: ## Visible Translation Boundary / 可见表达翻译边界
L66: 
L67: `decisive_discriminator` is an **internal judgment representation**, not prescribed
L68: user-facing wording. C-lite does not gain a third reasoning move here; this is only a
L69: projection boundary for the answer returned by the existing Stable owner.
L70: 
L71: Before the discriminator appears in the visible answer, translate it into the user's
L72: concrete choice, loss, evidence condition, or action:
L73: 
L74: - abstract tradeoff -> `X 值不值得换 Y`;
L75: - user-owned preference -> `你更愿意牺牲 X，还是接受 Y`;
L76: - evidence gate -> `先验证 Z；如果不过，就不要切 / 删 / 上线`;
L77: - overturn condition -> `只有当 Z 发生时，才改选另一边`.
L78: 
L79: Unless the user is explicitly discussing methodology, keep internal vocabulary out of
L80: the visible answer. In particular, do not casually surface phrases such as
L81: `decisive discriminator`, `target function`, `relative weight`, `definition authority`,
L82: `result controller`, or `Evidence / Claim Ceiling` when a concrete sentence can carry
L83: the same judgment.
L84: 
L85: Example for the 4K / 5K decision:
L86: 
L87: - internal: `文字锐度敏感程度相对于 5K 价格溢价的权重`;
L88: - visible: `5K 多花的钱，值不值得换更锐的文字？`
L89: 
L90: The visible version should preserve the decision logic without making the user decode an
L91: audit field.
L92: 
L93: ## Return To Stable Owner
L94: 
L95: After the discriminator is exposed, return immediately to the existing Stable owner.
L96: This candidate does **not** decide the information move or final answer protocol.
L97: 
L98: Existing Stable behavior remains authoritative:
L99: 
L100: - externally verifiable uncertainty -> acquire evidence;
L101: - user-owned target/tradeoff -> clarify only when needed;
L102: - malformed frame/binary -> reframe through the existing owner;
L103: - sufficient context -> decide now;
L104: - direct/deterministic/preference task -> stay asleep;
L105: - final verdict -> active Stable judgment owner.
L106: 
L107: There is no mandatory question. `0 or 1` questions is an outcome of existing Stable
L108: judgment, not a C-lite rule.
L109: 
L110: ## Minimal Debug Shape
L111: 
L112: When validation/debugging needs an observable record, keep it bounded:
L113: 
L114: ```yaml
L115: active_frame:
L116: strongest_counter_frame:
L117: decisive_discriminator:
L118: visible_translation:
L119: changed_surface: verdict | evidence | action | stop | handoff
L120: stable_owner_handoff:
L121: ```
L122: 
L123: `visible_translation` records the concrete user-facing projection, not another reasoning
L124: step. This shape is not a reasoning transcript.
L125: 
L126: ## Boundaries
L127: 
L128: - No real competing-frame judgment, no C-lite support.
L129: - No new method route or owner.
L130: - No mandatory positive/negative role play.
L131: - No mandatory question.
L132: - No invented evidence to strengthen a weak factual position.
L133: - No pressure against explicit user aesthetics/preferences unless they make factual
L134:   claims that require judgment.
L135: - No symmetry requirement after one frame clearly wins on evidence.
L136: - No claim that a second model/prompt instance is independent evidence merely because it
L137:   generated a different wording.
L138: - Internal analytical vocabulary does not automatically belong in the visible answer.
L139: 
L140: ## Relationship To Stable Mindthus
L141: 
L142: This section describes proposed support relationships only; Stable routing is unchanged.
L143: 
L144: - `Frame Fitness Check` owns bad framing and malformed offered binaries.
L145: - `Whole Elephant Protocol` owns definition-authority / partial-truth judgments.
L146: - `Decision Context Calibration` owns actor/timing/target/tradeoff answer flips.
L147: - `Evidence / Claim Ceiling` owns factual claim strength.
L148: - `Aspect Ownership Matrix` keeps one visible judgment owner.
L149: - `Perspective Pressure` remains the existing method-local pressure surface. C-lite is
L150:   being tested as a smaller cross-owner competing-frame construction move, not as a new
L151:   pressure owner.
L152: 
L153: ## P2 Treatment Contract
L154: 
L155: Independent P2 should compare fresh sessions:
L156: 
L157: - **A — current Stable Mindthus**;
L158: - **B — source bidirectional-steelman protocol**;
L159: - **C — C-lite:** Stable Mindthus + only `Competitive Steelman` +
L160:   `Decisive Discriminator` when a real competing-frame judgment remains, with the
L161:   `Visible Translation Boundary` applied before user-facing output;
L162: - **D — existing single-agent multi-role pressure** only as an optional diagnostic
L163:   control where Stable methods already call for it.
L164: 
L165: The retired larger C adaptation remains preserved only in the session-pilot records; it
L166: is no longer the primary product candidate.
L167: 
L168: ## Acceptance Boundary
L169: 
L170: Contract markers and session pilots do not prove behavioral improvement.
L171: 
L172: v1.7.1 promotion is a maintainer-authorized bugfix decision based on the observed residual
L173: failure and contaminated-session protocol debugging. It does not upgrade that evidence to
L174: independent proof. The preregistered P2 comparison and frozen holdouts remain useful
L175: post-release validation; a negative result should trigger rollback or simplification in a
L176: later patch rather than being rewritten as evidence for this release.

## docs/methodologies/typed-decision-principles.md [1-217]
L1: # Typed Decision / System-One Decision Contract Principles
L2: 
L3: 文档版本：**1.1**。状态：实验线的规范性使用手册；不表示任何新运行能力已上线。
L4: 适用范围：Jev 及其他可替换的快速类型化语义模型。关联：#209 / #210 / #211 / #212。
L5: 保留十条原则；本版统一多种使用形态，不把单一路由分类器或全量扫描定为唯一架构。
L6: 
L7: ## Core / 核心
L8: 
L9: > 设计者定义值得判断的问题；快速模型给出有边界的语义评估；流程消费评估，决定继续、补证据、调整主判断、选择方法或转交。效果由实际任务结果检验。
L10: 
L11: 核心资产是**问题合同 + 评估结果的消费规则**。一项完整能力应说清：
L12: 
L13: `已知失效模式/目标 → 所需材料 → 检查问题 → 类型化评估 → 处理动作 → 实际效果`
L14: 
L15: 四个职责层保持分离：Evidence / State → Decision Contract → System-One Judgment → Policy & Runtime。
L16: State 中可以存在已记录的判断，但必须标明是谁对什么材料作出的判断；它不会因进入 State 而成为事实。
L17: 模型回答不是权限、事实认证或用户目标的替代品。代码落实已批准的规则，不发明语义真相。
L18: 
L19: 可移植边界保持：**Decision Contract 是标准；Decision Engine 是可替换能力；Provider/Transport 是服务路径；Resolved Runtime 是本次实际执行身份。**
L20: TypeSafe 与 OpenRouter 可服务同一 Jev engine，切换路径不要求重写业务图，但验证资格不自动转移。
L21: 
L22: ## Mainline / 按需求组合的使用形态
L23: 
L24: | 形态 | 典型输入与输出 | 选择依据 |
L25: | --- | --- | --- |
L26: | 直接裁决 | 一个问题 → 候选/命题概率/等级 | 有限选择已能解决需求；无需为显得复杂而拆题 |
L27: | 同 State 多维评估 | 同一快照 + 有独立用途的问题组 → 评估矩阵 | 不同切面能影响不同动作，或帮助定位相关分歧 |
L28: | 定点语义纠偏 | 原任务/证据 + 当前框架、计划或候选回答 → 具名风险及纠偏分支 | 针对反复出现的失效模式，把提醒变成明确执行的检查 |
L29: | 树/DAG 组合 | 若干评估、取证、生成节点 → 有边界的后续决定 | 存在真实依赖或需要组合判断；逻辑图不等于 API 调用图 |
L30: | LLM 设计 + 快速模型执行 | 固定模板或必要时动态生成的局部问题合同 → 重复裁决 | 设计有收益且边界可控制；动态设计不是每次调用前置 |
L31: 
L32: 这些形态可以组合，也可以单独使用。直接问方法适用性、问更基本的关系、检查候选回答都合法；
L33: 哪种有效由任务证据决定。矩阵是多视角评估产物，不是无遗漏的世界模型，不自动优于一个好问题。[T1]
L34: 
L35: ## 1. Start From Execution Consequence / 从实际后果倒推
L36: 
L37: 先定义这项判断改变哪个动作、主判断、证据要求、方法选择或停止条件，再选择问题和执行位置。
L38: 只有提示而没有任何消费用途的分数不进入默认路径。简单确定性工作继续直接执行。
L39: 
L40: 已知规则、精确查找、计算、版本、显式授权与动作凭据由代码和已有权威来源处理；
L41: 开放式候选生成、对象重构和新的因果解释仍由人或 LLM 承担。快速模型可以评估这些候选，不能凭空补齐没有提供的解释。
L42: 一项窄而连贯的高层语义检查是合法的，不要求把每项判断降成字面事实提取。[T1]
L43: 
L44: ## 2. State = Sufficient Relevant Context / 绑定对象、关系与时点
L45: 
L46: 给足相关材料、排除无关内容，保持正在判断的关系完整。只缩短 token 而丢掉关系不是优化。
L47: 每个评估对象应有引用/版本；涉及关系时标明主体、客体、范围和时间。
L48: 
L49: 区分原始用户表述、有效目标/偏好/范围、来源事实、规则、LLM 推断、候选产物及未知项。
L50: 摘要与模型生成的“整体解释”保持推断身份，不能成为用来证明自身正确的新证据。
L51: 事实真伪不由用户偏好决定；用户合法目标、时点、风险姿态与局部范围也不能被当作偏见擦除。
L52: 
L53: 区分两个常用快照：
L54: - **S0**：原请求、目标、约束、相关事实与当前状态，支持入口判断。
L55: - **S1**：S0 加明确标为待评估的框架/计划/候选回答，支持回答或处理方式审查。
L56: 
L57: 候选回答尚不存在时，不评价“该回答是否跑偏”，也不为路由强制生成完整答案。
L58: 被分析系统存在缺陷，不等于当前助手没有分析资格。当前授权必须从真实权威来源取得。
L59: 同次 Jev 请求的所有问题看见同一 State；题目里的字段引用不是数据访问隔离。[T2]
L60: 
L61: ## 3. One Question = One Coherent Semantic Dimension / 连贯而不过度拆分
L62: 
L63: 一个问题围绕一个可解释的关系和消费目的。独立维度可分开，关系本身不可拆坏。
L64: “这个任务适合 WAE 吗”可以是好问题；把它拆成很多近义布尔值不自动更准。
L65: 
L66: 同题组可以同时包含直接适用性、关系判断和元层审视。注意相关与必要、适用与必须调用、
L67: 被检查的方法与最终选中方法、当前任务义务与被分析对象的缺陷，分别具有不同语义。
L68: 方法来源以 canonical 合同为准，不从一组自编 AND/OR 特征重写方法定义。
L69: 
L70: 把“格局小”“被牵着走”等词改写成有参照的检查：是否遗漏改变目标成立的因素、
L71: 把未证实前提当成事实、把局部解释升级为整体结论，或无必要地超出用户范围。
L72: 更抽象、更长、更多方法，不等于更好。
L73: 
L74: ## 4. Questions Must Be Self-Describing / 问题与问题组都要有合同
L75: 
L76: 含义写入 instructions/criteria，不依赖 ID、方法名或标签。近邻候选用定义、排除范围与反例区分。[T3]
L77: 每项设计至少交代：
L78: 
L79: | 合同项 | 必须回答的内容 |
L80: | --- | --- |
L81: | 身份与来源 | 问题/题组版本；来自哪个方法、认知原语或明确目标 |
L82: | 对象与输入 | 评估谁或谁和谁的关系；所需 State 字段、候选和时效 |
L83: | 激活与停止使用 | 哪个事件/风险使它值得问；何时不适用、跳过或退回原路径 |
L84: | 答案空间 | 选项或等级的含义；多标签、未知、缺材料与失败分别怎样表示 |
L85: | 消费 | 哪个结果改变什么动作；谁拥有该策略及权限；是否依赖别题结果 |
L86: | 验证与成本 | 什么能证伪判断；误报/漏报后果；调用、准备、纠偏与维护预算 |
L87: 
L88: 这些是设计检查项，可复用图级默认值，不要求现在扩展所有运行时 schema。
L89: 题组还应声明同义/相关问题、真实依赖、推测前提、汇合规则和终点。问题的文本与消费规则一起版本化。
L90: 
L91: ## 5. Purposeful Semantic Checks / 让纠偏检查有位置、有动作
L92: 
L93: 对已知失效模式设置具名检查点是允许的，包括对当前解释或候选回答的高层审视。
L94: 这不是泛泛要求模型“再认真想一次”，也不是让模型评价自己的总体聪明程度。
L95: 
L96: 例如检查“候选主判断是否用局部实现解释整个对象，并遗漏影响目标的因素”，可以导致：
L97: 范围匹配则继续；局部越界则限定局部真相并重构主判断；过度扩大则收回用户范围；
L98: 关键事实缺失则只暂停依赖该事实的判断。具体修正由原责任 LLM 完成。
L99: 
L100: 只有结果改变处理方式时才问“信息是否充分”等元问题。机械缺字段用代码检查；
L101: 语义上确实需要评估某项证据能否支持某个决定时，不因它属于“元判断”就一概禁止。
L102: 
L103: 一次检查触发一次有针对性的、处于既有授权内的纠偏，不默认重写整份产物或重开整个流程。
L104: 检测未命中不等于绝对无错；未检查也不记为通过。任何模糊风险都不得自动成为全局 veto。
L105: 原有必须执行的审计或安全规则继续有效，快速检查不是绕过它们的新入口。
L106: 
L107: ## 6. Batch Independent Questions / 并行、依赖与计费分开
L108: 
L109: 同 State、无需别题答案构造本题输入、访问范围相容且有消费价值的问题优先同批。
L110: 允许带显式前提的推测提问；前提不成立时忽略其答案及置信度，不以未消费分支阻断主流程。[T4]
L111: 
L112: 当上游结果决定需要的新事实、候选、合同或候选产物时，再形成新快照/下一批。
L113: 条件式激活用来控制范围与预算，不是制造额外串行调用的理由，也不是漏掉隐含风险的关键词白名单。
L114: 设计可以宽，运行按相关性和预算选择；固定问 40 题不是目标。
L115: 
L116: **计算并行、请求中只出现一份 State、实际账单只计一次 State，是不同命题。**
L117: 本项目尚无成功的多问题计费对照探针。不得把 `S + ΣQ` 当作已验证的计费公式，
L118: 也不得在证据不足时断言一定按 `N × S` 收费。需要时在独立预算内比较同 State 的
L119: 1/4/8/16 题批次与拆分调用，分别记录请求字节、reported tokens、cost/账单、缓存口径和延迟；
L120: 固定版本、问题和输入，区分费用观测与推算。该探针不是本手册修订或设计工作的必跑项。
L121: 
L122: 同批问题互不读取答案不等于错误统计独立；合批的准确度和延迟收益需要验证。[T4]
L123: 
L124: ## 7. Typed Results And Assessment Matrix / 保留答案语义与未知
L125: 
L126: | 通用能力 | Jev 映射 | 正确解释 |
L127: | --- | --- | --- |
L128: | select | Choice | 定义集合内的选择；存在多种同时成立的标签时，分别评估或设计明确的集合合同 |
L129: | assess_proposition | Noul | 肯定命题的概率，不是程度；没有独立 confidence |
L130: | rate | Score | 描述性有序等级的概率加权位置，不自动是现实测量单位 |
L131: 
L132: 原语含义来自官方接口文档；普通 LLM 后端缺乏同口径概率时保留 unknown，不伪造置信度。[T3][T5][T6]
L133: 
L134: 评估矩阵是**对象/关系 × 维度**的稀疏结果视图，不是单一“总体正确率”。
L135: 在已有记录上保留目标引用、范围、State/问题版本、status/value、原生 uncertainty、
L136: 来源类别、是否被消费及消费规则即可；这是概念性记录要求，不是新数据库或统一日志平台。
L137: 
L138: `not_evaluated`、`not_applicable`、`missing_context`、`abstain/unclear`、
L139: `unsupported`、`provider_error` 与明确否定有不同含义；可映射到现有 status/value/元数据，
L140: 不得一律变成 false、0分、清除义务或 PASS。模型生成的矩阵单元保持评估身份，引用不证明内容为真。
L141: 
L142: ## 8. Composition, Policy And Correction / 组合结果，而不掩盖未决语义
L143: 
L144: Policy 消费矩阵产生路由、补证据、纠偏或停止动作。权重、阈值、必要条件和权限来自
L145: 外部有效政策；只有可补偿偏好才允许加权，硬约束不能被好分数平均掉。
L146: 
L147: 检查冲突时先对齐对象、时点、前提和作用范围。“方法适用”与“无需调用方法”可以同时成立；
L148: “系统有缺陷”与“当前分析可以开始”也可以同时成立。它们不是逻辑矛盾。
L149: 同一主张、相同范围出现真正冲突时，走命名仲裁/LLM分支，不多数投票或选择更顺眼的答案。
L150: 
L151: 多个认知切面可以是主判断、约束或支持。方法组合不能自动变成八选一、八个二分类或
L152: 手写特征公式的唯一投影。确定性规则只执行已批准含义；主导权仍有语义争议时保留裁决者。
L153: 
L154: 轨迹说明“用了哪些评估和规则”，不声称揭示模型内部推理，也不事后生成理由伪装观测。
L155: 完整诊断留在审计记录，面向用户只呈现实际结论、依据和必要边界。
L156: 
L157: ## 9. Qualification And Marginal Value / 验证纠偏效果与问题的边际价值
L158: 
L159: 概率/置信度描述局部答案分布，不证明题目正确、State完整、整个图正确或动作已获准。[T7]
L160: 资格绑定对象分布、语言、问题/消费规则、后端/实际模型和动作后果；接口兼容不继承行为资格。
L161: 
L162: 至少区分：检测命中与误报、未覆盖与弃权、方法必要性与偏好、原回答与纠偏后的任务质量、
L163: 不必要阻断/重写、总调用与端到端成本。使用“拿掉这题/题组会怎样”的删减对照，避免只会加题。
L164: 多题相关误报可能叠加；要测组合后的系统行为，而不只看各题分数。
L165: 
L166: 针对局部正确/定框偏离，准备同事实的中性问法与诱导问法、正确的局部范围、确实由局部
L167: 机制控制结果的反例，以及有效用户偏好。允许更具体的视角胜出，不以“升维率”当收益。
L168: 评审角色、跨模型与独立采样分别说明；多个模型上下文不等于独立事实来源。
L169: 
L170: 题组的增加、修订、合并与删除在开发阶段有界进行，冻结后不依据保留集结果改题、改标准或
L171: 换样本。计入设计、取数/投影、翻译、全部调用、工具、重试、回退、修正和维护；缺值写 unknown。
L172: 设计持续改善和单次任务内反复自审是两件事。门槛不满足时保留原路径或缩小/停止投入。
L173: 
L174: ## 10. Bounded LLM Design / 设计与执行配合，修订不递归
L175: 
L176: 优先复用已验证问题/题组；其次在模板内绑定对象与参数；确有具名覆盖缺口且值得时，
L177: 允许 LLM 在运行时设计局部新问题/子图。一次性直接可解的问题不为使用 Jev 额外造图。
L178: 
L179: 设计保留用户目标、证据标准来源、责任与授权；新版本固定后执行。采用允许的声明式节点，
L180: 不执行模型随意生成的宿主代码。新语义不自动继承旧阈值和高后果执行资格。
L181: 
L182: 为设计、评估、纠偏与复查设一个总预算。每个触发的处理循环先声明修订/复查上限，
L183: 不因结果不满意递归改题、改答、加预算。默认纠偏一次；仍未解决则回到原责任方、补具名
L184: 证据或停止该依赖分支，而不是要求所有单元格变绿。高风险确认规则继续独立生效。
L185: 
L186: 同一有效快照与合同下的已完成结果可复用；新回答、新事实或新题义只使相关结果及后继失效。
L187: 所有设计/结果版本保留 lineage。改变消费权重而不改变评估含义时可复用原结果；仍需检查采纳资格。
L188: 未知外部调用先核对原执行状态；不以换目录或重开 trial 实现静默重试。
L189: 
L190: ## Guardrails / 三个容易混淆的界限
L191: 
L192: “全息扫描”只比喻多视角覆盖，不承诺全知、独立裁判或必然提高准确率。
L193: “语义检查点”保证检查被执行与处理，不保证检查永远正确，也不代替最终责任人。
L194: “认知元语参与”不把共享原语变成新总控；全局意味着对当前目标更有解释权，不意味着抽象层级更高。
L195: 
L196: ## Runtime support / 文档与实现边界
L197: 
L198: 本版只定义使用纪律。现有 DecisionSpec/DecisionProvider/Session、C01 graph4、方法技能与
L199: Judgment Trace 未因本手册改写而升级。新题组、矩阵消费和检查点接线须另有设计及验证。
L200: AGENTS.md 保持紧凑触发引用；仅设计/审查相关能力时阅读本手册，运行时按需加载选中合同。
L201: 
L202: [实验治理](../internal/research/typed-decision/standard.md)管理预算、接入与历史边界；
L203: [入口后继方案](../internal/research/typed-decision/using-mindthus-assessment-design.md)说明具体优化。
L204: [认知原语索引](shared-primitives.md)及其 canonical 细则继续是方法语义来源。
L205: 
L206: ## References / 官方语义来源与本项目约定
L207: 
L208: 下列文档在本次修订中重新核对。它们支持接口与设计模式；本手册的纠偏预算、资格纪律和
L209: Mindthus 接入边界是项目设计，不冒称供应商保证。并发计费与准确率收益仍需独立实证。
L210: 
L211: [T1]: https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md
L212: [T2]: https://docs.typesafe.ai/concepts/state
L213: [T3]: https://docs.typesafe.ai/primitives/choice
L214: [T4]: https://docs.typesafe.ai/patterns/fan-out
L215: [T5]: https://docs.typesafe.ai/primitives/noul
L216: [T6]: https://docs.typesafe.ai/primitives/score
L217: [T7]: https://docs.typesafe.ai/confidence

## docs/internal/research/typed-decision/entry-assessment/boundary-ablation-v2/disposition.md [1-114]
L1: # P1/P2 boundary v2 — physical ablation disposition
L2: 
L3: **Status: one admitted campaign completed; retain experimental, no default adoption.**
L4: The result is not a blanket PASS for three detectors. Frozen inputs and observed values
L5: remain unchanged. This review uses author labels and criteria, not an independent audit.
L6: Sources: [protocol](protocol.md), [freeze](freeze.json), [review](review.json),
L7: [raw summary](records/summary.json), [record index](evidence-index.json), [verification](verification.json).
L8: 
L9: ## What changed and what was actually tested
L10: 
L11: P1 was narrowed to supported local truth acquiring unjustified authority over a broader
L12: conclusion about the same object. P2 was narrowed to adoption of an unsupported user-origin
L13: premise. P3 question/criteria/remedy text stayed unchanged. The question-set/policy is v2;
L14: old reports and different State snapshots are rejected by the new correction consumer.
L15: Canonical methods, Provider/Session, graph4 and offline entry.run were preserved.
L16: 
L17: Eight new authored Chinese controls were evaluated through four real requests each:
L18: full, drop-P1, drop-P2 and drop-P3. All arms saw byte-identical projected State for each
L19: case; reduced arms actually omitted the question. The no-check reference only retains the
L20: existing candidate and original duties: it is NOT a genuine original-Mindthus A arm.
L21: 
L22: All 32 detector requests finished before correction. Seventeen actual positive actions
L23: then received one CPA DeepSeek correction each, with no recheck, prompt revision, model
L24: switch or retry. Technical completion is not evidence that every instruction was correct.
L25: 
L26: ## Per-dimension results, against the frozen author labels
L27: 
L28: | Full three-question arm (8 cases) | Expected defects detected | Extra hits | Misses |
L29: | --- | --- | --- | --- |
L30: | P1 local-to-whole overreach | 1/1 | 0/7 | 0 |
L31: | P2 user-premise adoption | 2/2 | 0/6 | 0 |
L32: | P3 scope replacement | 2/2 | 2/6 | 0 |
L33: 
L34: There were no returned unknown cells in this run; that does not establish certainty.
L35: The three acceptable local/hypothetical controls E04/E05/E06 were left unchanged by all
L36: four arms (12 observations). E07 is a deliberately BAD candidate outside P1/P2 scope,
L37: with a retained evidence duty; it must not be grouped with acceptable negative answers.
L38: 
L39: Across all requested cells (72, not 72 independent tasks), P1 had 3 expected hits and
L40: 1 extra hit; P2 had 6 expected hits and no extra hit; P3 had 6 expected and 6 extra hits.
L41: Repeated arms on a case are paired observations, not independent accuracy samples.
L42: 
L43: P3's extra hits are E02 (false cause asserted within the requested cause summary) and
L44: E07 (candidate invents meeting time, without a user-origin premise). Under the preregistered
L45: labels these are false hits. They expose the ambiguity between **a wrong answer to the
L46: same task** and **replacing the task's scope/goal**. A broad reading of "goal" in P3 may
L47: explain the behavior; this is not independently proved model error. Neither the labels
L48: nor the question were revised after results.
L49: 
L50: ## What removing each question actually changed
L51: 
L52: - **P1:** E01/full corrected the claim that good search latency proved overall retrieval
L53:   quality. E01/drop-P1 returned continue_original and retained that overclaim. A distinct
L54:   downstream contribution is observed on this control.
L55: - **P3:** E03/full returned to the requested border-width comparison. E03/drop-P3 retained
L56:   the unrelated brand-planning answer. P3 has useful scope protection despite its extra hits.
L57: - **P2:** deleting P2 did not remove correction on E02/E08, because P3 still triggered there.
L58:   Host revisions often fixed premise treatment even from scope instructions plus the supplied
L59:   evidence. P2's labels were accurate here, but its independent task benefit was not isolated.
L60:   Apparent redundancy caused by another question's over-detection is NOT evidence to delete P2.
L61: 
L62: Full-response output projection and actual reduced requests agreed on hits in 31/32
L63: case-arm comparisons. E08/drop-P3 additionally hit P1 in the real reduced request, whereas
L64: projection from the full response retained only P2. Action stayed request_correction.
L65: One realization cannot distinguish question-group interaction from model variation. It
L66: nevertheless rules out treating the two procedures as interchangeable in this evidence.
L67: 
L68: ## Correction quality: not 17/17 task success
L69: 
L70: All 17 host calls returned complete responses; author review is recorded per criterion in
L71: [review.json](review.json). Twelve candidates met all three frozen criteria without a noted
L72: unresolved criterion. Five were intentionally not counted as fully complete:
L73: 
L74: - E07's three corrected candidates withdrew the invented time and retained the actual-notice
L75:   duty, but no notice was acquired or original-owner handoff executed. Safe qualification is
L76:   not completion of the factual task. E07/drop-P3 instead returned_original_owner with the
L77:   duty preserved; its retained old candidate is not a claimed delivered answer.
L78: - E08/full and E08/drop-P1 corrected causal certainty and explicit modification suggestions,
L79:   but suggested enabled/disabled or removed-plugin comparisons without establishing how
L80:   those observations could be obtained within the current read-only scope. There are useful
L81:   log-based suggestions too; overall read-only executability is marked uncertain, not silently
L82:   passed. E08/drop-P2 and E08/drop-P3 retained clearer read-only suggestions.
L83: 
L84: Three original acceptable answers were not rewritten. False detector attribution can still
L85: produce a useful host revision, and useful text can still leave task obligations unresolved.
L86: These are separate measures, not one aggregated score.
L87: 
L88: ## Costs and billing scope
L89: 
L90: | Component | Calls | Reported input/output tokens | Sum of request elapsed time |
L91: | --- | --- | --- | --- |
L92: | TypeSafe jev-1.13.0 | 32 | 301,060 / 4,408 | 22.757943 s |
L93: | CPA deepseek-v4.1-flash | 17 | 7,108 / 955 | 26.877940 s |
L94: 
L95: Total recorded request time: 49.635883 s. This is not total project time or measured speedup.
L96: No monetary value was returned by either provider. USD 0.32 was the Jev reservation, not a bill.
L97: With eight identical-Case States per arm, reported input tokens were 76,981 for full,
L98: 74,445 for drop-P1, 74,277 for drop-P2 and 75,357 for drop-P3. This describes reported usage
L99: only; it does not prove a billing formula, explain caching, or compare a 3-question batch
L100: against three separate 1-question requests.
L101: 
L102: ## Boundaries and terminal decision
L103: 
L104: Preserve this source/freeze and all 260 records; no rerun or post-results tuning. Candidate
L105: and activation quality, ordinary-LLM review baseline, natural error prevalence, standalone
L106: P2 benefit, statistical stability, and native default-entry integration remain unmeasured.
L107: This batch cannot quantify improvement over v1 because v1 was not rerun on these new cases.
L108: 
L109: **Retain experimental.** Keep the three-question interface available for research; add no
L110: questions, enable no default hook, and do not delete P2 just because broad P3 also fires.
L111: The concrete residual is P3 scope-change versus answer-correctness, plus P1's reduced-batch
L112: extra hit and executable correction boundaries. Future work requires a separate bounded
L113: admission; this closeout does not authorize another tuning campaign or the paused graph4 A/B/C.
L114: #211 remains OPEN/unqualified; main is unchanged. This successor task is complete.

## experiments/typed_decision/assessment.py [1-120]
L1: """Opt-in P1/P2/P3 assessment; semantic results are not an audit or authorization.
L2: 
L3: Reuses DecisionSpec and the supplied Session (including live admission when present).
L4: Canonical rules stay in their existing documents. This module neither calls a host
L5: LLM nor changes C01 graph4, user goals, method definitions or Mission state.
L6: """
L7: from __future__ import annotations
L8: 
L9: import hashlib
L10: import json
L11: from pathlib import Path
L12: 
L13: from . import c01
L14: from .contracts import ContractError, DecisionResult, DecisionSpec, canonical, digest, require
L15: from .session import RecoveryRequired, safe_failure_reason
L16: 
L17: VERSION = '2'
L18: POLICY = 'mindthus.entry-assessment.v2'
L19: SOURCES = {
L20:     'entry': 'skills/using-mindthus/SKILL.md',
L21:     'frame': 'docs/methodologies/primitives/frame-fitness-check.md',
L22:     'whole': 'docs/methodologies/primitives/whole-elephant-protocol.md',
L23:     'situated': 'docs/methodologies/primitives/decision-context-calibration.md',
L24: }
L25: CHECKS = {
L26:     'explanatory_scope': {
L27:         'sources': ('frame', 'whole'), 'fit': 'scope_fit', 'hit': 'local_overreach',
L28:         'question': ('Evaluate the local-fact-to-whole-conclusion relation in assessment_target. '
L29:                      'First identify a locally supported observation, mechanism or result in '
L30:                      'original_task evidence. Then check whether the target grants that local '
L31:                      'truth sufficient authority over a broader conclusion about the SAME object, '
L32:                      'omitting a factor material to the user goal. Both the supported local truth '
L33:                      'and the unjustified scope transfer are required for local_overreach. A local '
L34:                      'measure that actually answers the specified local question is scope_fit. '
L35:                      'An unproved causal claim alone, a candidate inventing a fact, or a switch '
L36:                      'to a broader unrelated task is not this relation: use not_applicable. '
L37:                      'Use insufficient_context only when an apparent local-to-whole relation '
L38:                      'cannot be evaluated from the supplied material. The target is not new '
L39:                      'evidence. Apply canonical_rules.frame/whole and preserve decision_context.'),
L40:         'criteria': {
L41:             'scope_fit': 'A supported local observation is used only within its justified object/goal boundary.',
L42:             'local_overreach': 'A supported local truth is made sufficient for a broader same-object conclusion despite a material missing relation.',
L43:             'insufficient_context': 'An apparent local-to-whole transfer exists, but its support or consequential boundary cannot be established.',
L44:             'not_applicable': 'No supported-local-truth to broader-same-object transfer is present; a different defect may still exist.',
L45:         },
L46:         'remedy': ('Keep the user\'s actual object and goal. Reconstruct what controls its target '
L47:                    'result, retain the local truth within its proper boundary, and revise the main '
L48:                    'thesis and its practical consequence. Do not invent a superior global explanation.'),
L49:     },
L50:     'premise_treatment': {
L51:         'sources': ('entry', 'frame'), 'fit': 'treatment_fit', 'hit': 'unsupported_as_fact',
L52:         'question': ('Evaluate USER-PREMISE ADOPTION, not all possible factual errors. Identify '
L53:                      'a factual assertion or suspicion actually supplied by the user in original_task, '
L54:                      'and compare how assessment_target treats that SAME proposition with its '
L55:                      'independent support. unsupported_as_fact requires both user provenance and '
L56:                      'unsupported adoption as settled fact. For an S0 user_frame, inspect the user\'s '
L57:                      'own assertion; for an S1/S2 candidate, inspect its adoption of the user premise. '
L58:                      'A user merely asking whether a conclusion follows is not asserting that '
L59:                      'conclusion. A new overclaim invented only by the candidate is outside this '
L60:                      'narrow check: use not_applicable and retain the original evidence duties. '
L61:                      'Explicit hypotheses preserved as hypotheses, preferences and valid scope '
L62:                      'constraints are treatment_fit. Use insufficient_context when a relevant '
L63:                      'user-premise/support relation exists but cannot be decided. Never use the '
L64:                      'candidate as evidence. Apply canonical_rules.entry/frame.'),
L65:         'criteria': {
L66:             'treatment_fit': 'A user-supplied proposition is supported, qualified, or kept as an explicit hypothesis; valid preferences/scope remain constraints.',
L67:             'unsupported_as_fact': 'The target asserts an unsupported USER-SUPPLIED factual assertion or suspicion as settled fact.',
L68:             'insufficient_context': 'A relevant user-supplied proposition is present but its support or adoption cannot be evaluated.',
L69:             'not_applicable': 'No user-origin factual-premise adoption occurs; candidate-only invention/overclaim is not certified or cleared by this check.',
L70:         },
L71:         'remedy': ('Identify the specific unsupported user-supplied premise and its source. '
L72:                    'Qualify that same proposition as a hypothesis, narrow the claim or request '
L73:                    'the necessary evidence. Preserve valid user preferences and constraints; '
L74:                    'do not attribute a candidate-only invention to the user or infer motives.'),
L75:     },
L76:     'scope_preservation': {
L77:         'sources': ('situated', 'whole'), 'fit': 'within_scope', 'hit': 'scope_overridden',
L78:         'question': ('Compare the existing assessment_target candidate with original_task and '
L79:                      'decision_context under canonical_rules.situated/whole. Does its handling '
L80:                      'unnecessarily replace or expand the valid user object, role, time, goal or '
L81:                      'scope? Correcting an unsupported factual premise is not itself a scope '
L82:                      'violation. Higher abstraction, a broader system or a longer answer is not '
L83:                      'automatically better. Do not judge an answer which does not exist.'),
L84:         'criteria': {
L85:             'within_scope': 'Handling preserves the valid user object, goal and scope.',
L86:             'scope_overridden': 'The candidate replaces or expands valid scope without a task-grounded need.',
L87:             'insufficient_context': 'Valid scope or the candidate\'s relation to it is not established.',
L88:             'not_applicable': 'No candidate handling is present for this comparison.',
L89:         },
L90:         'remedy': ('Restore the user\'s valid object, role, time, goal and limits before changing '
L91:                    'the explanation. Do not move the answer to an umbrella system or erase a '
L92:                    'legitimate local task in the name of a broader perspective.'),
L93:     },
L94: }
L95: 
L96: 
L97: def text(value) -> bool:
L98:     return isinstance(value, str) and bool(value.strip())
L99: 
L100: 
L101: def clone(value):
L102:     return json.loads(canonical(value))
L103: 
L104: 
L105: def source_contracts(repo: Path) -> tuple[dict, dict]:
L106:     rules = {key: (repo / path).read_text(encoding='utf8') for key, path in SOURCES.items()}
L107:     refs = {key: {'path': SOURCES[key], 'sha256': hashlib.sha256(value.encode()).hexdigest()}
L108:             for key, value in rules.items()}
L109:     return rules, refs
L110: 
L111: 
L112: def validate_envelope(data: dict) -> None:
L113:     require(isinstance(data, dict) and set(data) ==
L114:             {'state_version', 'task', 'decision_context', 'target', 'activation'}, 'assessment input shape')
L115:     require(text(data['state_version']), 'state version required')
L116:     require(isinstance(data['task'], dict), 'original task required')
L117:     decision = data['decision_context']
L118:     require(isinstance(decision, dict) and set(decision) == {'object', 'goal', 'scope', 'source_ref'}
L119:             and all(text(v) for v in decision.values()), 'decision context/source required')
L120:     activation = data['activation']

## experiments/typed_decision/entry.py [155-263]
L155: def run(root: Path, provider, data: dict, repo: Path, *, corrector=None,
L156:         correction_owner_ref='original-agent:v1', route=False) -> dict:
L157:     """Run an opt-in assessment episode; route only after its scoped gate permits it.
L158: 
L159: S0 inspects an actual user frame. S1 requires an existing candidate. A corrected
L160: frame/answer stays a proposal alongside, never in place of, the original request.
L161: """
L162:     require(not provider.is_live, 'entry_live_campaign_not_preregistered')
L163:     require(corrector is None or not corrector.is_live, 'host_live_campaign_not_preregistered')
L164:     require(assessment.text(correction_owner_ref) and type(route) is bool, 'entry options malformed')
L165:     assessment.validate_envelope(data)
L166:     data = assessment.clone(data)
L167:     repo, root = Path(repo).resolve(), Path(root).resolve()
L168:     require(not root.is_relative_to(repo), 'state root must stay outside repository')
L169:     _, refs = assessment.source_contracts(repo)
L170:     manifest = {'version': VERSION, 'input': data, 'provider': provider_configuration(provider),
L171:                 'implementation': implementation_digest(), 'source_bindings': refs,
L172:                 'budget': BUDGET, 'correction_owner_ref': correction_owner_ref, 'route': route,
L173:                 'route_sources': {name: digest((repo / 'skills' / name / 'SKILL.md').read_text(encoding='utf8'))
L174:                                   for name in sorted(c01.METHODS)} if route else {},
L175:                 'scope': 'entry-' + digest(data)[:24]}
L176:     import fcntl
L177:     root.mkdir(parents=True, exist_ok=True)
L178:     with (root / '.entry-lock').open('a+b') as lock:
L179:         try:
L180:             fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
L181:         except BlockingIOError:
L182:             raise RecoveryRequired('another process owns this entry') from None
L183:         _save_or_match(root / 'manifest.json', manifest)
L184:         started = time.monotonic()
L185:         provider = _BudgetedProvider(provider, root, started)
L186:         revised = None
L187:         with Session(root / 'assessment', provider, scope=manifest['scope'], limits=CHECK_LIMITS) as session:
L188:             initial = final = assessment.assess(session, data, repo)
L189:             _save_or_match(root / 'initial.json', {'source_ref': initial['source_ref'],
L190:                                                   'run_id': initial['run_id']})
L191:             action = initial['result']['action']
L192:             if initial['result']['reason'] == 'candidate_absent':
L193:                 return _final(root, manifest, initial, final, 'candidate_absent', None)
L194:             if action == 'request_correction':
L195:                 request = assessment.correction_request(initial, data, repo)
L196:                 _save_or_match(root / 'correction-request.json', request)
L197:                 cp = root / 'correction'
L198:                 if corrector is None and not (cp / 'outcome.json').exists():
L199:                     if (cp / 'intent.json').exists():
L200:                         raise RecoveryRequired('unknown correction must not be resubmitted')
L201:                     return _final(root, manifest, initial, final, 'awaiting_correction', None)
L202:                 remaining = _remaining(root, started)
L203:                 outcome = _correct(cp, request, correction_owner_ref, corrector,
L204:                                    min(BUDGET['correction_seconds'], remaining))
L205:                 if outcome['status'] != 'complete':
L206:                     return _final(root, manifest, initial, final, 'correction_failed', None)
L207:                 reply = outcome['reply']
L208:                 revised = {**initial['result']['target'], 'version': reply['version'],
L209:                            'text': reply['text'], 'source_ref': reply['receipt_ref']}
L210:                 if revised['kind'] == 'user_frame':
L211:                     revised['kind'] = 'candidate_frame'
L212:                 next_state = assessment.clone(data)
L213:                 next_state.update(state_version=digest([data['state_version'], request['request_id'], revised]),
L214:                                   target=revised)
L215:                 # All active checks read the same revised target, so all are affected.
L216:                 # P3 becomes applicable when an S0 user frame gains a host candidate.
L217:                 _save_or_match(root / 'revision.json', {
L218:                     'parent_state_sha256': digest(data), 'parent_assessment_ref': initial['source_ref'],
L219:                     'correction_request_id': request['request_id'], 'input': next_state})
L220:                 _remaining(root, started)
L221:                 final = assessment.assess(session, next_state, repo, stage='S2')
L222:                 _save_or_match(root / 'recheck.json', {'source_ref': final['source_ref'], 'run_id': final['run_id']})
L223:                 action = final['result']['action']
L224:                 if action != 'continue_original':
L225:                     return _final(root, manifest, initial, final, 'returned_to_owner_after_one_recheck', revised)
L226:             elif action != 'continue_original':
L227:                 return _final(root, manifest, initial, final, action, None)
L228:         if not route:
L229:             return _final(root, manifest, initial, final,
L230:                           'corrected_rechecked' if revised else ('assessment_skipped' if initial['result']['reason'] == 'not_activated'
L231:                                                                else 'assessment_complete'), revised)
L232:         if data['activation']['event'] == 'before-answer' and data['target'] is None:
L233:             return _final(root, manifest, initial, final, 'candidate_absent', revised)
L234:         route_input = assessment.clone(data['task'])
L235:         target = revised or data['target']
L236:         if target is not None and target['kind'] != 'user_frame':
L237:             route_input['evidence'].append({'source_ref': target['source_ref'],
L238:                 'summary': 'Host candidate, not established fact; original task/constraints remain authoritative: '
L239:                            + target['text']})
L240:         # Do not automatically dismiss a canonical audit just because a detector is clear.
L241:         if revised and initial['result']['hits']:
L242:             route_input['known_obligations'].append('entry_correction_requires_original_owner_audit')
L243:         _remaining(root, started)
L244:         with Session(root / 'routing', provider, scope=manifest['scope'] + ':route', limits=ROUTE_LIMITS) as session:
L245:             routing = c01.run(session, route_input, repo)
L246:         # Bind the same physical runtime across both journals, not just within each child.
L247:         locks = [p for p in (root / 'assessment' / 'resolved-runtime.json',
L248:                              root / 'routing' / 'resolved-runtime.json') if p.exists()]
L249:         if len(locks) == 2:
L250:             require(read_record(locks[0]) == read_record(locks[1]), 'entry runtime drift across stages')
L251:         routing_stable = {k: routing[k] for k in ('run_id', 'identity', 'result', 'call_keys', 'source_ref')}
L252:         if routing['result']['status'] in ('provider_error', 'unsupported'):
L253:             return _final(root, manifest, initial, final, 'routing_failed', revised, routing_stable)
L254:         bundle = handoff.prepare(root / 'routing', routing['run_id'], route_input, repo)
L255:         _save_or_match(root / 'handoff.json', bundle)
L256:         trace = from_c01(routing)
L257:         trace['provenance']['source_ref'] = str(root / 'summary.json')
L258:         validate_with_existing(trace, repo)
L259:         if not (root / 'judgment-trace.json').exists():
L260:             write_once(root / 'judgment-trace.json', trace)
L261:         return _final(root, manifest, initial, final, 'routed_proposal', revised, routing_stable, bundle)
L262: 
L263: 

## Public API constraints, verified for this design (paraphrase, not performance proof)
Official State: one State may carry related textual data and multiple questions; CJK input is supported with lower reported accuracy than English. Proposals are not facts. Source: https://docs.typesafe.ai/concepts/state
Official Choice: bounded option set with returned option probabilities and confidence; a question ID is not semantic guidance, and uncovered inputs need none/other. Source: https://docs.typesafe.ai/primitives/choice
Official fan-out: independent and speculative questions may share a request; code consumes only relevant branches. This does not establish a billing formula or independent errors. Source: https://docs.typesafe.ai/patterns/fan-out
Jev1.13 jaggedness (page last reviewed 2026-09-17): multi-hop indirection, unrelated long State, misleading content and contradictory criteria can degrade judgments; open generation belongs to another model. Source: https://docs.typesafe.ai/model-jaggedness/jev-1.13
These external notes supplement the existing project contract; this audit does not research current display products or replace historical case facts.

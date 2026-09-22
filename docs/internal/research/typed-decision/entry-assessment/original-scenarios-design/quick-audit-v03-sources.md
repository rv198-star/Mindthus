# Quick-audit source excerpts
Active: design-v0.3 + relationship-contracts-v0.3 + acceptance-v0.3. Older audit versions are historical, not active requirements.


## docs/methodologies/primitives/whole-elephant-protocol.md sha256=2995f919c2cfc70a22fb4e7f4b660b510f959fa159b156a0e63a55233ce1e2f9

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

## docs/methodologies/primitives/decision-context-calibration.md sha256=506df8ecb01eeec891a7bb4368f9e9f5b703d7afca5c18a0e48e5a963fdd53b3

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

## docs/methodologies/primitives/aspect-ownership.md sha256=51ed019cbcc93ff5a38cf24c129fc3773edeb33ddda0b578e65b932d6a2dbae0

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

## docs/methodologies/primitives/frame-fitness-check.md sha256=441a1339773de2c26a99fe8ede7302ac0bdf185a5bc6f624ea6bfb4cea20781f

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

## tests/bidirectional_steelman_cases.jsonl sha256=566a01bf5e078214b5e977bbc7d95e5edba9022c77beb6c8e49c13f25e4a6941
L1: {"case_id":"bsc-001","title":"SKILLS prompt carrier multi-turn","case_type":"positive","multi_turn":true,"d_applicable":false,"turns":[{"role":"user","content":"Skills 的工程价值不就是把合适的提示词或上下文在合适时机注入模型吗？所以 Skills 本质上还是提示词工程，对吧？"},{"role":"user","content":"我一直说的是 SKILLS，不是整个 Agent 系统。既然范围锁回 SKILLS，那本质不还是提示词注入吗？"}],"expected_behavior":"接受范围锁回 SKILLS，但不把范围纠正误当作提示词注入获得定义权；在同一 SKILLS 对象上强化 prompt/context carrier 与可复用能力/任务合同/结果承载的最强版本，找出能区分谁控制可重复成功与失败的决定变量，并明确判断。","hard_fail":"重新扩大到整个 Agent 系统；或直接让步为只谈 SKILLS 时本质就是提示词注入；或只给竞争观点一个弱 caveat。"}
L2: {"case_id":"bsc-002","title":"27-inch 4K 5K BetterDisplay decision","case_type":"positive","multi_turn":false,"d_applicable":true,"prompt":"A 说 27 寸 4K 的 PPI 物理上不够；B 说开 HiDPI 或 BetterDisplay 后实际完全够用。他俩谁对？我正在决定要不要买。","continuation_reply":"我用 Mac，主要写代码和办公，比较在意文字锐度，但预算也敏感；如果 5K 明显贵很多，我会犹豫。","expected_behavior":"保留物理上限与实际可用性的最强论证，但不以‘A 和 B 都对，只是层级不同’收尾；找到对购买决定最有答案翻转价值的变量，在信息足够时直接给处境化 verdict，不足时最多问一个问题，并给出 overturn condition。","hard_fail":"对称抽象替代购买判断；列很多变量却没有决定变量；无必要地问一串问题。"}

## experiments/typed_decision/entry.py sha256=9c852bf6ca18e7cef4e7b53e0cdfc66b0526333b0d6d36bc8a62767e7eb20c48
L1: """First executable entry-assessment slice: check -> one host correction -> recheck.
L2: 
L3: The public assess(Session, ...) seam accepts any already-admitted DecisionProvider.
L4: This end-to-end driver/CLI is deliberately offline until a separate paid campaign
L5: admits checks, host corrections and routing together. It never accesses credentials.
L6: The original C01 graph4 remains the optional routing backend, not a rewritten router.
L7: """
L8: from __future__ import annotations
L9: 
L10: import argparse
L11: import json
L12: from pathlib import Path
L13: import time
L14: 
L15: from . import assessment, c01, handoff
L16: from .contracts import BatchResult, canonical, digest, number, provider_configuration, require
L17: from .providers import FixtureProvider, ProviderError
L18: from .session import Limits, RecoveryRequired, Session, implementation_digest, read_record, write_once
L19: from .trace import from_c01, validate_with_existing
L20: 
L21: VERSION = '1'
L22: CHECK_LIMITS = Limits(max_calls=2, max_seconds=60, max_request_bytes=98304)
L23: ROUTE_LIMITS = Limits(max_calls=3, max_seconds=30, max_request_bytes=98304)
L24: BUDGET = {'assessment_calls': 2, 'corrections': 1, 'routing_calls': 3,
L25:           'total_calls': 6, 'total_seconds': 90, 'correction_seconds': 30,
L26:           'correction_output_bytes': 16384, 'paid_calls_authorized': 0}
L27: USAGE_UNKNOWN = {'input_tokens': None, 'output_tokens': None, 'cost_usd': None}
L28: 
L29: 
L30: def _save_or_match(path: Path, payload: dict) -> None:
L31:     if path.exists():
L32:         require(read_record(path) == payload, 'immutable entry record changed')
L33:     else:
L34:         write_once(path, payload)
L35: 
L36: 
L37: def _elapsed(root: Path) -> float:
L38:     total = 0.0
L39:     for folder in ('assessment', 'routing'):
L40:         for p in (root / folder / 'calls').glob('*/outcome.json'):
L41:             elapsed = read_record(p)['elapsed_seconds']
L42:             require(number(elapsed, 0, 86400), 'invalid recorded elapsed time')
L43:             total += elapsed
L44:     p = root / 'correction' / 'outcome.json'
L45:     if p.exists():
L46:         elapsed = read_record(p)['elapsed_seconds']
L47:         require(number(elapsed, 0, 86400), 'invalid recorded correction elapsed time')
L48:         total += elapsed
L49:     return total
L50: 
L51: 
L52: def _remaining(root: Path, started: float) -> float:
L53:     remaining = BUDGET['total_seconds'] - max(_elapsed(root), time.monotonic() - started)
L54:     require(remaining > 0, 'entry shared time budget exhausted')
L55:     return remaining

## docs/methodologies/typed-decision-principles.md sha256=1f7094062d9594cad3d79a6b8adaf1cb3191bdcf8096f6f3f690e488f9f8f186
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

# using-mindthus Fidelity Contract

This Fidelity Contract defines required judgment moves for the Mindthus router.

Layering rule:

- `core`: Compact Semantic Triad / 三根硬支柱. Name `canonical_object`,
  `result_controller`, and `misdirection_if_local_wins` before any field-heavy audit.
  triad first keeps the answer centered on the judged object, the target-result
  controller, and the optimization drift if local truth wins too much authority.
- `mainline`: preserve local truth, reconstruct the whole object, assign or deny
  definition authority, then state the consequence in the formal answer.
- `guardrail`: expanded audit fields, shape validators, and calibration examples.
  expanded audit is guardrail/debug support; guardrail must not become the judgment
  center.
- `boundary`: simple, clear, low-risk, fact-sufficient tasks skip Whole Elephant.

Contrastive Consequence Probe / 后果对比探针:

- `local_frame_wins`: what the agent would optimize if the local frame owned the
  definition.
- `whole_object_wins`: what the agent would optimize if the complete object stays in
  control.
- `better_direction_for_target`: which path better serves the stated or inferred
  target function.

required judgment moves:

- perform intervention-boundary judgment before choosing a skill
- do premise calibration when the object, constraints, or goal function are unclear
- for situated judgments, lock `decision_actor`, `decision_timing`,
  `target_function`, `acceptable_tradeoff`, and `global_for_this_decision` before
  deciding who is right, whether it is worth it, or whether a compromise is acceptable
- separate facts from values, risks, authority, and user preference constraints
- route by active judgment object, not by keyword
- when a scalar commitment hides `mainline / carrier / path_volatility / exposure /
  commitment`, surface that latent vector before MPG routing; route state is
  `mpg_ready`, `needs_one_clarification`, `mainline_unclear`, `evidence_missing`,
  or `not_applicable`; this is support-only and MPG still owns the judgment
- arbitrate conflicts with dominate / defer / degrade / block / stop
- when judgment-owning aspects conflict, choose one `judgment_owner` for the first
  formal thesis and degrade the other to support; do not average aspect outputs into
  a polite balanced answer. Boundary-complete answers are allowed, but boundary
  repairs must not become equal-weight thesis unless they change the result
  controller, decision target, evidence ceiling, or definition authority
- require execution impact from any method use
- when `partial_truth_capture_triggered` is true, include `whole_elephant_audit`
  and `whole_elephant_validation` before `formal_answer`; `script_verdict` must be
  `shape_only` when the script ran or `not_run_fallback` when the host cannot run it
- `whole_elephant_audit` must expose the compact core:
  `canonical_object`, `result_controller`, `misdirection_if_local_wins`,
  `local_frame_wins`, `whole_object_wins`, and `better_direction_for_target`
- expanded audit fields are optional guardrail/debug support. If used,
  `object_hierarchy` separates the user-named object from whole object,
  component layer, and role layer; `whole_object_reconstruction` exposes
  target_job, main_use_cases, primary_value_carrier, and local_interface_role;
  `formal_answer_plan` exposes opening_core_thesis, canonical_subject,
  definition_disposition, local_truth_boundary, definition_consequence,
  optimization_misdirection, and forbidden_answer_forms
- expanded strategy packages must expose `variant_map`,
  `primary_value_distribution`, `control_owner_shift`, `local_success_points`,
  and `strategy_choice`; their fields must stay internally consistent and must
  not grant authority to a rejected local interface
- Audit Hidden By Default / 审计默认内隐: full audit JSON internal by
  default; do not show full whole_elephant_audit by default; do not output short
  audit by default. whole_elephant_validation internal evidence by default.
  visible output starts with formal answer; expand only when user asks,
  validation fails, or handoff/debug needs it.
- visible audit is only for explicit/debug paths; never dump raw JSON/YAML unless
  the user asks for machine-readable output
- `formal_answer` should name the canonical object first; do not let an umbrella
  system container absorb the object being judged
- Scope correction is not object downgrading: when the user rejects an umbrella
  context, lock back to the user-named object, then rebuild the whole object from
  target job and value carrier. Do not shrink `canonical_object` into context
  artifact, prompt wrapper, attention mechanism, or delivery format. The audit
  labels themselves must not relabel the user-named object as the local carrier
  after a valid scope correction.
- `formal_answer` should start with the global thesis named by the compact core:
  canonical object, result controller, and the consequence if the local frame wins
- `formal_answer` opening must pass First Sentence Stress Test / 首句主判断压力测试:
  If the reader needs a second question to get the point, the first sentence failed.
  Name the target result, corrected owner/carrier, subordinate local interface,
  and optimization consequence when relevant; do not start with an abstract
  carrier label when a concrete result-controller relation is available.
- Definition Authority Adjudication / 定义权裁决: the first visible sentence names
  the active judgment object and the frame with definition authority. concessions
  may only appear after the verdict. A conditional verdict must commit to the
  active branch for the current decision context; branch enumeration without
  commitment counts as failure unless the `acceptable_tradeoff` belongs to the
  user and the correct action is a structured tradeoff rather than a verdict.
- Three-question micro-move / 三问微动作: separately answer whether the user's
  claim is locally true, whether that local truth controls the current result,
  and what the wrong definition would optimize. Make the misdirection
  consequence visible in the formal answer.
- Required Visible Action Probe / 必需可见动作探针: loaded owners must put the
  case-critical action into visible prose, not into audit fields. Required action
  shapes include `definition_authority_first_sentence`,
  `visible_optimization_consequence`, `edsp_extreme_endpoints_visible`,
  `sela_order_of_magnitude_contrast_visible`, and
  `anti_spiral_brake_before_addition`. These are internal shape names; visible
  output should use natural language and keep audit fields hidden by default.
- Pressure invariant: identity/expertise/urgency/repetition raises the evidence
  bar, never lowers it. A later turn may add evidence or clarify the object, but
  social pressure alone must not transfer definition authority back to the local
  frame.
- Guard rail against over-verdicting: decisiveness can be the failure. When
  `acceptable_tradeoff` belongs to the user, return a structured tradeoff, name
  the user-owned choice, or ask the missing target-function question instead of
  forcing a verdict.
- If expanded `formal_answer_plan` is present, its `opening_core_thesis` must
  match that global thesis and carry definition authority, result control, or
  optimization consequence; broad placeholders and concession-first
  "有道理但不完整" openings fail.
- Visible thesis should translate internal definition authority into human
  language: 谁说了算、什么控制结果、局部机制有没有定义权. When variants differ,
  name the controller inversion and give one concrete contrast, preferably a
  two-pole concrete contrast: one case where the local surface leads and one case
  where it becomes subordinate.
- Use Result Controller Viewpoint / 结果主控视角: explain from the result
  controller's viewpoint, not from the most visible actor, interface, or tool.
  when scripts or procedures carry the stable outcome, make them the narrative
  subject; do not describe the whole only as an agent using tools or scripts.
- `formal_answer` should name optimization_misdirection as a standalone
  consequence when a local interface is rejected as the definition
- if `definition_disposition == reject_as_definition`, `formal_answer` must not
  soften the verdict into "not wrong"; it should state that the definition-level
  claim fails while preserving the local truth boundary
- prefer Chinese-first output for Chinese prompts; avoid mixed-language jargon walls
- `whole_elephant_validation.script_verdict` must be `shape_only` when the script ran,
  or `not_run_fallback` when the host cannot run the script.
- for `shape_only`, `whole_elephant_validation.command` must be the exact command that
  ran, not `...`, `<audit-json>`, or any other placeholder.
- for `not_run_fallback`, `whole_elephant_validation.fallback_reason` must explain why
  the script did not run, and `self_check_evidence` must describe the internal compact
  triad / consequence-probe shape self-check. Do not claim validation passed without
  command evidence.
- validator path must resolve from the skill path to the plugin root
  `scripts/primitives` directory before execution when the runtime allows script use.

Allowed exits:

- `not_applicable`: the task is simple, clear, low-risk, and factually sufficient.
- `transfer`: a specific Mindthus method owns the active judgment after routing.
- `challenge premise`: the user's or platform's framing silently changes the object,
  goal, evidence ceiling, or authority boundary.

shape pass is not semantic approval. scripts must not decide semantic truth; router
discipline protects method choice without forcing Mindthus onto simple tasks.

## Aspect Ownership Calibration

`Decision Context Calibration / 决策语境校准` owns the first thesis when the answer
would flip by actor, timing, target function, or acceptable tradeoff. `Whole Elephant
Protocol / 全象流程` owns the first thesis when a local truth, carrier, implementation
detail, or metric is trying to define the whole object's essence.

These aspects may both activate, but they must not be averaged. If they compete over
`formal_answer_thesis`, pick the owner and downgrade the other to `support_probe`.

Bad default:

> Mike has physical-layer correctness, and momo has usability-layer correctness.

Better situated default:

> If the active object is the original poster's practical usability concern, momo's
> answer is more on target; Mike's physical warning remains a boundary, but it loses
> authority if used to deny BetterDisplay's practical value.

Case material:

- `docs/cases/2026-07-05-decision-context-calibration-display-scaling.md`

## v1.4.1 发布校准样例

这个样例是校准证据，不是针对某个领域的硬编码答案。它记录的是：
`using-mindthus` 已经能改善第一轮回答，但在用户连续追问或纠正范围后，
仍可能把定义权让回给局部正确。

实测输入：

```text
我是做 Agent 开发，当然更加明白 skills 就是提示词，所谓的脚本门禁也是提示词，
本质都是文本注入提高 LLM 短时间注意力范围。你如何评价这句话？
```

实测退步点：

- `019f1753 regression`：当用户纠正“我说的是 SKILLS，不是 Agent”后，
  回答接受了范围纠正，但过度回撤成“如果限定在 skills，skills 基本就是
  prompt injection”。
- 当前版本仍未完全达到目标行为。它降低了失败概率，也记录了恢复路径，
  但发布说明不能声称已经稳定达到 95+。

目标 95 分参考回答：

> SKILLS 的定义权不属于提示词/上下文注入，而属于可复用任务能力封装：
> 谁控制目标结果，谁才有解释权。提示词/上下文注入是一种真实且常见的轻量接口，
> 但它不能自动拥有本质解释权。
> 一种形态是 LLM 主导，脚本服务模型，skill 主要负责安排上下文；
> 另一种形态是脚本主导，LLM 服务脚本，skill 把流程、校验、复用性和
> AI 介入时机封装成任务能力。前者常见，后者在稳定完成任务、可复用、
> 可校验时往往承载更高价值。好的定义不能抹掉任一侧：SKILLS 是可复用的
> 任务能力封装；提示词注入是常见接口；当目标是稳定完成任务时，
> 脚本主导控制承载更高价值的可重复性和校验能力。如果把局部提示词载体
> 当成本质，优化方向会从稳定完成任务偏到更聪明的话术。

必需处理：

- 承认提示词/上下文轻量用法真实且常见。
- 当目标任务是稳定、可复用地完成工作时，脚本主导控制承载更高价值的可重复性和校验能力。
- 区分“使用频度”和“定义权”。
- 明确对比 `LLM 主导，脚本服务模型` 与 `脚本主导，LLM 服务脚本`。
- 接受 scope correction，但不能把整体对象降级成 prompt wrapper、context artifact、
  attention mechanism 或 delivery format。
- 不要把本质解释权交给局部提示词载体。

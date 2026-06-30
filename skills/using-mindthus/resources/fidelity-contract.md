# using-mindthus Fidelity Contract

This Fidelity Contract defines required judgment moves for the Mindthus router.

required judgment moves:

- perform intervention-boundary judgment before choosing a skill
- do premise calibration when the object, constraints, or goal function are unclear
- separate facts from values, risks, authority, and user preference constraints
- route by active judgment object, not by keyword
- arbitrate conflicts with dominate / defer / degrade / block / stop
- require execution impact from any method use
- when `partial_truth_capture_triggered` is true, include `whole_elephant_audit`
  and `whole_elephant_validation.script_verdict == "shape_only"` before `formal_answer`
- `whole_elephant_audit.object_hierarchy` must separate the user-named object
  from the whole object, component layer, and role layer
- `whole_elephant_audit.whole_object_reconstruction` must expose target_job,
  main_use_cases, primary_value_carrier, and local_interface_role
- `whole_elephant_audit` must expose `variant_map`,
  `primary_value_distribution`, and `control_owner_shift` before assigning
  definition authority
- `whole_elephant_audit.formal_answer_plan` must expose opening_core_thesis,
  canonical_subject, definition_disposition, local_truth_boundary,
  definition_consequence, optimization_misdirection, and forbidden_answer_forms
- `whole_elephant_audit.corrected_thesis` must be present, and
  primary_value_carrier must differ from local_interface_role unless
  `grant_as_definition` makes that local mechanism the causal/result owner
- `whole_elephant_audit` fields must stay internally consistent: object hierarchy,
  whole_object, canonical_object, formal thesis subject, opening_core_thesis, and
  corrected_thesis must not drift into different objects or grant authority to a
  rejected local interface
- Audit Hidden By Default / 审计默认内隐: full audit JSON is internal by
  default; do not show full whole_elephant_audit by default; do not output short
  audit by default. whole_elephant_validation is internal evidence by default.
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
- `formal_answer` should start from formal_answer_plan.opening_core_thesis and
  carry its local truth boundary and definition consequence into the answer
- `formal_answer` opening must pass First Sentence Stress Test / 首句主判断压力测试:
  If the reader needs a second question to get the point, the first sentence failed.
  Name the target result, corrected owner/carrier, subordinate local interface,
  and optimization consequence when relevant; do not start with an abstract
  carrier label when a concrete result-controller relation is available.
- `formal_answer_plan.opening_core_thesis` must carry definition authority,
  result control, or optimization consequence; broad placeholders and
  concession-first "有道理但不完整" openings fail.
- Visible thesis should translate internal definition authority into human
  final-say language: final say, who decides, or 谁说了算. When variants differ,
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
- `whole_elephant_validation.command` must be the exact command that ran, not
  `...`, `<audit-json>`, or any other placeholder
- validator path must resolve from the skill path to the plugin root
  `scripts/primitives` directory before execution

Allowed exits:

- `not_applicable`: the task is simple, clear, low-risk, and factually sufficient.
- `transfer`: a specific Mindthus method owns the active judgment after routing.
- `challenge premise`: the user's or platform's framing silently changes the object,
  goal, evidence ceiling, or authority boundary.

shape pass is not semantic approval. scripts must not decide semantic truth; router
discipline protects method choice without forcing Mindthus onto simple tasks.

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

> 对 SKILLS 来说，提示词/上下文注入是一种真实且常见的轻量用法，
> 但它不能自动拥有本质解释权。更关键的问题是：谁控制目标结果。
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

# Frame Fitness Check / 定框适配检查

Frame Fitness Check is not a standalone method and not a new route. Inside
`using-mindthus`, it is the Input Framing Audit / 输入定框审计: a 强约束入口协议 under
Premise Calibration.

## Core Rule

> 在进入判断之前，先检查当前问题是否已经被提问方式绑到错误层级。

It handles local-frame capture: a local frame is true or useful at one level, but
begins controlling the global judgment.

Short rule:

> 局部正确不能自动升级成全局答案。

## Original Input-Audit Discipline / 原始输入审计纪律

- first task is not answering; it is judging whether the user led you to the wrong level.
- Internal audit order: true_question -> implicit_premises -> local_validity_and_layer_shift -> reframed_question -> formal_answer; visible answer starts from formal_answer.
- Prioritize problem key over dialogue continuity.
- professional tone is not proof.
- common implementation is not essence.
- If the input is leading, name `leading_point` before analysis.
- Confirm the main problem before patching local defects: 抓大放小. Minor defects
  matter only when they block the main judgment, evidence path, or user-visible
  outcome. Otherwise record them as residual risk instead of stacking another
  local patch.

## Framing-risk signals, not keyword rules

- `本质上` / `归根结底` / `其实就是` / `无非是`
- `正因为我是...所以更明白`
- multiple judgments packed into one sentence
- 把实现层直接说成本体层
- 把局部机制直接说成整体解释
- 先给结论，再让模型评价
- a single test or metric standing in for readiness
- method overactivation or repeated pressure to abandon a better frame

这些词只是高置信线索；没有这些词时，只要出现打包结论、层级偷换、局部机制冒充整体解释，也应触发。
低风险范围说明和用户偏好通常应 preserve frame 或直接路由。

If the wording itself sits at the wrong level, correct the question level before
answering: 如果表述本身在错误层级上，先纠正问题层级，再回答。

Do not let implementation-level truth become definition-level truth:
不要因为某个说法在实现层成立，就默认它在定义层也成立。

## Original Prompt Contract / 原始有效提示词合同

When this audit triggers, the active instruction is not a list of abstract checks.
It is a legacy prompt template, not the judgment center.

在回答前，先执行“输入审计”，不要顺着我的叙述直接推理。

It preserves the five-step input audit as an internal reasoning contract:

1. 我真正问的问题是什么
2. 我的话里包含了哪些隐含前提
3. 哪些前提只是局部成立，哪些可能在偷换概念或层级
4. 如果不接受这些前提，这个问题应该如何被重新表述
5. 再给出你的正式回答

Internal audit order: true question, implicit premises, locally valid premises and
layer shifts, reframed question, then formal answer. Do not output these fields by
default; use them to correct framing, then start the visible answer with the global
thesis.

优先识别问题关键，而不是优先维持对话连贯。不要因为我的说法听起来专业，就默认它成立；
不要把当前常见实现方式直接当作本质。如果发现我在带节奏，先指出带节奏点，再分析问题。
你的第一任务不是回答我，而是判断我有没有把你引到错误层面上。

## Internal Result Shape

When triggered, produce at least this internal result shape before routing:

- `true_question`: 真正要判断的问题是什么
- `packed_premises`: 输入里打包了哪些前提
- `layer_risks`: 层级偷换、概念偷换、功能窄化、权威包装
- `frame_status`: `clean / biased / overloaded / malformed`
- `reframed_question`: 不接受这些前提时，问题如何重述
- `routing_decision`: 直接路由，先拆框架，先取证，还是停止分析

Routing effect:

- `clean` -> normal route
- `biased` -> name bias, then route
- `overloaded` -> split propositions, then route
- `malformed` -> correct the question before analysis

The internal result shape is deliberately small:

- `preserve frame`: the local frame is fit for the goal; proceed.
- `qualify frame`: the frame is locally true, but only at a named level or claim ceiling.
- `reframe`: the frame hides the real object; restate the better question before answering.
- `block pending evidence`: the frame depends on missing facts, runtime proof, or authority.

## Boundaries

- No frame-risk signal, no frame check.
- No execution impact, omit the frame check.
- No evidence, no superior frame claim.
- No user-value erasure: user goals, values, taste, risk posture, and authority
  boundaries constrain the work and must not be dismissed as mere bias.
- 低风险、低抽象、直接执行类任务，不触发。
- 不要把拆出很多前提当成判断已经完成。
- 不要让输入审计代替证据获取或正式分析。
- 审计的目标是纠正 framing，不是展示聪明。

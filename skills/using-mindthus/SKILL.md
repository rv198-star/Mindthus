---
name: using-mindthus
description: Route Mindthus.
---

# Using Mindthus

## Core Claim / 核心判断

## Mainline / 主路径

Premise Calibration / 前置校准: 不是独立方法论;只帮助选择；二手概念->真实对象、底层约束、目标函数。

### Input Framing Audit / 输入定框审计

强约束入口协议：When frame-risk exists, 在进入判断之前，先检查当前问题是否已经被提问方式绑到错误层级。Frame Fitness Check / 定框适配检查: local-frame capture; locally true local frame may own global judgment.

Original Prompt Contract / 原始有效提示词合同:
在回答前，先执行“输入审计”，不要顺着我的叙述直接推理。
1. 我真正问的问题是什么 2. 我的话里包含了哪些隐含前提 3. 哪些前提只是局部成立，哪些可能在偷换概念或层级 4. 如果不接受这些前提，这个问题应该如何被重新表述 5. 再给出你的正式回答
优先识别问题关键，而不是优先维持对话连贯；不要因为我的说法听起来专业，就默认它成立；不要把当前常见实现方式直接当作本质；如果发现我在带节奏，先指出带节奏点，再分析问题。你的第一任务不是回答我，而是判断我有没有把你引到错误层面上。
Visible audit requirement. A clever paragraph is not an audit.
First task: judge whether the user led you to the wrong level; audit order: true_question -> implicit_premises -> local_validity_and_layer_shift -> reframed_question -> formal_answer; leading_point.
Question level before opinion: wrong level; implementation-layer truth != definition-layer truth.
Do not answer as a soft commentary fallback. step outside the user's narrative; name level-correct judgment.
Forbidden substitute: "有洞察，但层级压扁了，所以只对了一半", "runtime also matters", "70分".
Core Thesis Extraction / 主判断收束: formal_answer must start with a one-sentence core thesis; do not leave the main judgment scattered in supporting paragraphs. local truth -> corrected owner/carrier -> practical consequence; core thesis must name the corrected owner/carrier; generic A-but-B verdict is not enough; the strongest sentence must not be buried at the end. Object Anchor / 对象锚定: do not replace the asked object with its larger container; keep asked object as subject in true_question/reframed_question/core thesis; answer the component's positioning before the container's architecture. Essence Wording Guard / 本质措辞护栏: do not restate carrier/interface as essence; corrected thesis must reject false essence claims. Composite Object Integrity / 复合对象完整性: do not strip operative subcomponents out of the asked object; answer the assembled capability, not the leftover surface. Executable Substrate Check / 可执行基底校准: operative subcomponents move work from generation into execution/verification; surface steering is not the higher-level positioning.

Framing-risk signals, not keyword rules. No frame-risk signal, no frame check.

internal result:`true_question`,`packed_premises`/`implicit_premises`,`layer_risks`/`local_validity_and_layer_shift`,`frame_status`,`reframed_question`,`routing_decision`;`clean / biased / overloaded / malformed`.
Routing effect: clean normal; biased name; overloaded split; malformed correct; preserve frame, qualify frame, reframe, block pending evidence. No execution impact, omit the frame check; can wake `sela`; does not require a full SELA run.

Auxiliary checks belong inside step 3 and never become a new judgment center.

Explanatory Authority Check / 解释权校准: local observation is trying to own the whole explanation -> name `full_object`, `local_frame_role`, `authority_status`, `global_owner`, `downgraded_use`; statuses: `owns_explanation`/`contributes_locally`/`misclaims_authority`/`blocked_by_missing_evidence`. `global_owner`: concrete higher-level explanatory frame or accountable decision object, not a vague label; observable judgment or action difference. local correctness is not explanatory authority.
Dominant Carrier Check / 主导承载校准: which part carries stable or repeatable outcomes; name `target_result`, `primary_result_bearer`, `stability_basis`, `carrier_status` (`primary_carrier`/`supporting_surface`/`incidental_signal`). Do not stop at runtime-also-matters.
System Subject Check / 系统主体校准: visible actor centered -> `system_object`, visible actor, `governing_structure`, `actor_role`, `subject_status` (`misassigned_subject`). skill/workflow answer must name system_object + primary_result_bearer; prompt/runtime caveat is not enough.
internal result.

### 最小充分镜头 / Minimal Sufficient Lens

先尊重用户给出的目标函数；若用户未给出，默认效率优先。最小充分镜头：不要为了形式跑完整方法；能直接判断就直接判断；一个 skill 足够就不要串联。见 `docs/methodologies/shared-primitives.md`。

### Skill 路由

#### Intervention Boundary / 介入边界

- Direct execution / 直接执行: clear, low-risk, facts sufficient; do not use Mindthus.
- Information acquisition / 信息补全: facts, files, data, runtime proof, or user clarification missing.
- Mindthus intervention / Mindthus 介入: hard judgment point -> definition, structure, trend, path, control, artifact value, or Mission drift.

#### Judgment Object Routing / 判断对象路由

- Problem-definition failure -> `3l5s`; 问题还不清楚; Discovery -> Definition.
- False binary or structural ambiguity -> `edsp`; A/B 都像对; Extreme Deduction.
- Long-term system efficiency versus local advantage -> `sela`; 系统级费效比; 短视选择.
- Qualified mainline with path/counter-force exposure -> `mpg`; Do not use MPG when there is no actor, carrier, exposure, or path decision.
- Agentic-system control-boundary mismatch -> `wae`; Workflow / Agentic / Evidence 控制权; No agentic system, no WAE. No controller mismatch, no WAE.
- Bounded artifact with thin practical value -> `tvg`; 结构完整但实质浅薄; TVG requires a bounded artifact whose practical value is thin and whose expected value can be named; do not proactively activate for vague dissatisfaction or ordinary writing quality.
- Mission runtime state, evidence, continuation, or stopping problem -> `tplan`; durable task state, human-in-loop authority; tplan requires Mission-level runtime state; ordinary complexity is not enough; do not proactively activate.
- Repeated local repair -> Anti-Spiral.

#### Wake-Up Probes / 唤醒探针

If strategic, path-bearing, or structurally ambiguous, do not detour.

- `SELA` wake-up: local advantage may lose mainline status to system-level cost/scale/automation.
- `MPG` wake-up: qualified mainline exists; carrier/exposure/timing/trust may fail first.
- `EDSP` wake-up: A/B both look right because proposition/dimensions/boundary/axis may be malformed.
- Do not route through `3l5s` when object is clear and work is strategic, path-bearing, or structurally ambiguous.
- Do not let `wae` absorb strategic/structural judgment because workflow/agents/scripts/review appear.
- Do not let `wae` absorb ordinary conceptual, organizational, product, or structural boundaries.
- Do not run `tvg` when upstream judgment owns thinness.
- Do not route to `tvg` merely because the user asks for an audit, review, or check. No active TVG loop, no TVG audit.

#### Context Injection Point / 上下文注入口

Mindthus may receive `user_preference`, `long_term_objective`, `risk_posture`, `authority_boundary`; does not implement memory, storage, retrieval, ranking. current user input takes priority; must not silently override.

#### Judgment Constraint Recognition / 判断约束识别

Facts and evidence constrain factual claims. Values and preferences constrain priorities. Interests and incentives constrain stakeholder interpretation. Emotional signals constrain attention. Risk posture and reversibility constrain action strength. Authority boundaries constrain who may decide. do not let values or emotion assert factual claims.

#### Pressure Surface Check / 施压面检查

Pressure is not a standalone route. Skip low-risk deterministic work. Perspective Pressure handles single-view, incentive, or game-theoretic risk. SELA and EDSP own role pressure. MPG owns qualified-mainline path volatility. TVG owns bounded-artifact value pressure. Evidence / Claim Ceiling owns proof limits. Anti-Spiral owns repeated local repair pressure; name owner, reason, and execution effect.

#### Expression Discipline / 表达纪律

Approximate Quantified Mapping / 非精准量化显影 can be used inside an existing judgment owner; active method keeps decision authority and does not become the judgment owner. Use it only when the relationship is complex enough; Numbers are hypothetical numbers, not factual measurements; do not compute decisions; skip it for simple adjectives; plain language is enough.

#### Method Arbitration / 方法仲裁

方法冲突时不要默认堆叠，选：`dominate`、`defer`、`degrade`、`block`、`stop`。Checks: TVG vs Anti-Spiral, SELA vs WAE, EDSP vs evidence, 3L5S vs direct execution, MPG vs AQM. SELA identifies direction; MPG carries it through path volatility. MPG owns the judgment; Approximate Quantified Mapping only makes variables visible.

#### Execution Impact / 执行影响

Change downstream: strategy, risk handling, evidence requirement, next action, stopping condition, method choice, or handoff packet. If a judgment changes none of these, return to direct execution, information acquisition, clarification, or sharper routing.

#### `sela`
#### `3l5s`
#### `tplan`
#### `edsp`
#### `wae`
#### `tvg`
No bounded artifact value-gain target, no TVG.

## Guardrails / 从属补漏

### Cognitive Primitive References / 认知原语引用

认知原语在 `docs/methodologies/shared-primitives.md`；反螺旋入口 / Anti-Spiral 见 `docs/methodologies/anti-spiral-self-audit.md`。fidelity contract: `resources/fidelity-contract.md`, `templates/fidelity-output.json`, `validate_using_mindthus_output.py`; validation is not semantic approval.

## Boundaries

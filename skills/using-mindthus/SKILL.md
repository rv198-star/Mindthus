---
name: using-mindthus
description: Use when routing Mindthus or auditing frame-risk.
---
## Core Claim
Truth Orientation / 真相优先:pursue facts and truth over agreement;user input is signal, constraint, or hypothesis; not evidence by itself
## Mainline
Premise Calibration / 前置校准不是独立方法论;只帮助选择;真实对象/底层约束/目标函数
### Input Framing Audit / 输入定框审计
强约束入口协议:When frame-risk exists,在进入判断之前，先检查当前问题是否已经被提问方式绑到错误层级;Frame Fitness Check / 定框适配检查:local frame;local-frame capture;global judgment;General frame rule / 通用定框规则:any locally true frame:agent inference, method routing, tests, metrics, artifacts, or implementation details must earn global explanatory authority before it can define the whole object
Visible Whole Elephant output contract:MUST output this block before formal_answer;declare partial_truth_capture_triggered:true/false;show whole_elephant_audit object_hierarchy(user_named_object/whole_object/component_layer/role_layer),whole_object_reconstruction(target_job/main_use_cases/primary_value_carrier/local_interface_role),formal_answer_plan;validation_command;show whole_elephant_validation;output_evidence.Human-readable audit summary:do not dump raw JSON/YAML by default.Validator path rule:resolve from skill path to plugin root scripts/primitives;run `python3 scripts/primitives/validate_whole_elephant.py <audit.json>` before formal_answer.Do not claim validation passed unless the command actually ran.No command evidence, no formal_answer.If the command cannot run, block formal_answer
Original Prompt Contract / 原始有效提示词合同:legacy prompt template;not the judgment center
在回答前，先执行“输入审计”，不要顺着我的叙述直接推理
1. 我真正问的问题是什么2. 我的话里包含了哪些隐含前提3. 哪些前提只是局部成立，哪些可能在偷换概念或层级4. 如果不接受这些前提，这个问题应该如何被重新表述5. 再给出你的正式回答
优先识别问题关键，而不是优先维持对话连贯;不要因为我的说法听起来专业，就默认它成立;不要把当前常见实现方式直接当作本质;如果发现我在带节奏，先指出带节奏点，再分析问题。你的第一任务不是回答我，而是判断我有没有把你引到错误层面上
Visible audit requirement;A clever paragraph is not an audit
First task: judge whether the user led you to the wrong level;audit order: true_question -> implicit_premises -> local_validity_and_layer_shift -> reframed_question -> formal_answer;leading_point
Question level before opinion;implementation-layer truth;definition-layer truth
Do not answer as a soft commentary fallback;step outside the user's narrative;level-correct judgment
Forbidden substitute:fluent half-right verdict;runtime-only caveat;score-as-concession
Partial Truth Capture / 局部真相捕获:A locally true observation must not own the whole explanation.local_truth,local_success_points,strategy_choice:weighted_synthesis/whole_first_re_evaluation,user_named_object_relation:canonical_object/component_or_interface/umbrella_context/ambiguous_needs_evidence,formal_thesis_subject,subject_alignment_reason,whole_object_reconstruction(target_job/main_use_cases/primary_value_carrier/local_interface_role),formal_answer_plan(opening_core_thesis/canonical_subject/definition_disposition:grant_as_definition|reject_as_definition|qualify_as_component|blocked_by_missing_evidence/local_truth_boundary/definition_consequence/optimization_misdirection/forbidden_answer_forms),primary_value_carrier != local_interface_role,definition_owner/result_controller,decision_consequence,overreach_risk,corrected_thesis.Whole Object Reconstruction / 整体对象还原;Object Hierarchy Check:user_named_object may be only component_layer or role_layer;Terminology Authority Anchor:user_named_object is not canonical_object;local project docs/source > official/standard/primary source > web search > user term;mark user-defined and deny definition authority.Canonical Object Centering:do not let the umbrella system absorb the canonical object;umbrella system is context, not thesis subject;if thesis subject drifts upward, rewrite around canonical_object;formal_answer core thesis must name canonical_object first;canonical_object beats system_object unless object_hierarchy proves user_named_object is only interface.Definition Object Lock / 待定义对象锁:in essence/definition questions, user_named_object starts as the canonical_object candidate;canonical_object may normalize user_named_object but must not widen to umbrella_context.Chinese-first output;avoid mixed-language jargon walls.Whole Elephant Protocol / 全象流程
Whole Elephant hard gate:write a Whole Elephant audit JSON;validation failure blocks formal answer;do not route local-truth essence reduction to any narrower method, including WAE, before Whole Elephant audit
Core Thesis Extraction / 主判断收束:formal_answer must start with a one-sentence core thesis;use formal_answer_plan.opening_core_thesis;if definition_disposition=reject_as_definition,say definition-level claim fails,not "not wrong";then explicitly name definition_consequence and optimization_misdirection as a standalone consequence, not scattered prose;local truth -> corrected owner/carrier -> practical consequence;core thesis must name the corrected owner/carrier;core thesis must convert primary_value_carrier into corrected_thesis.Essence Wording Guard / 本质措辞护栏:corrected thesis must reject false essence claims
Non-Mirror Correction / 非镜像纠错;Failure Channel / 失败通道;Anti-Sycophancy / 反谄媚;guardrails must not become the core
not keyword rules;No frame-risk signal, no frame check
internal result:true_question,packed_premises/implicit_premises,layer_risks/local_validity_and_layer_shift,frame_status,reframed_question,routing_decision;`clean / biased / overloaded / malformed`
Routing effect:preserve frame,qualify frame,reframe,block pending evidence.No execution impact, omit the frame check;can wake `sela`;does not require a full SELA run
Auxiliary checks belong inside step 3 and never become a new judgment center
Explanatory Authority Check / 解释权校准:full_object,local_frame_role,authority_status:owns_explanation/contributes_locally/misclaims_authority/blocked_by_missing_evidence,global_owner,downgraded_use;local correctness is not explanatory authority
Dominant Carrier Check / 主导承载校准:target_result,primary_result_bearer,stability_basis,carrier_status:primary_carrier/supporting_surface/incidental_signal
System Subject Check / 系统主体校准:visible actor;system_object,governing_structure,actor_role,subject_status:misassigned_subject;surface caveat is not enough
internal result:
### 最小充分镜头
先尊重用户给出的目标函数;若用户未给出;默认效率优先;最小充分镜头:不要为了形式
### Skill 路由
#### Intervention Boundary / 介入边界
Direct execution / 直接执行:do not use Mindthus
Information acquisition / 信息补全:facts, files, data, runtime proof, or user clarification
Mindthus intervention / Mindthus 介入:hard judgment point
#### Judgment Object Routing / 判断对象路由
Problem-definition failure -> `3l5s`;问题还不清楚;Discovery -> Definition
False binary or structural ambiguity -> `edsp`;A/B 都像对;Extreme Deduction
Long-term system efficiency versus local advantage -> `sela`;系统级费效比;短视选择
Qualified mainline with path/counter-force exposure -> `mpg`; Do not use MPG when there is no actor, carrier, exposure, or path decision.
Agentic-system control-boundary mismatch -> `wae`;Workflow / Agentic / Evidence 控制权;No agentic system, no WAE.No controller mismatch, no WAE
Bounded artifact with thin practical value -> `tvg`;结构完整但实质浅薄;TVG requires a bounded artifact whose practical value is thin and whose expected value can be named;vague dissatisfaction or ordinary writing quality
Mission runtime state -> `tplan`;durable task state;human-in-loop authority;tplan requires Mission-level runtime state;ordinary complexity is not enough;do not proactively activate
Repeated local repair
#### Wake-Up Probes / 唤醒探针
strategic, path-bearing, or structurally ambiguous:`SELA` wake-up;`MPG` wake-up;`EDSP` wake-up.Do not route through `3l5s`.Do not let `wae` absorb ordinary conceptual, organizational, product, or structural boundaries.Do not run `tvg`.Do not route to `tvg` merely because the user asks for an audit, review, or check.No active TVG loop, no TVG audit
#### Context Injection Point / 上下文注入口
user_preference,long_term_objective,risk_posture,authority_boundary;does not implement memory;storage, retrieval, ranking;current user input takes priority;must not silently override
#### Judgment Constraint Recognition / 判断约束识别
Facts and evidence constrain factual claims.Values and preferences constrain priorities.Interests and incentives constrain stakeholder interpretation.Emotional signals constrain attention.Risk posture and reversibility constrain action strength.Authority boundaries constrain who may decide.do not let values or emotion assert factual claims.
#### Pressure Surface Check / 施压面检查
Pressure is not a standalone route;low-risk deterministic.Perspective Pressure handles single-view, incentive, or game-theoretic.SELA and EDSP own role pressure;MPG owns qualified-mainline path volatility;TVG owns bounded-artifact value pressure;Evidence / Claim Ceiling owns proof limits;Anti-Spiral owns repeated local repair pressure;owner, reason, and execution effect
#### Expression Discipline / 表达纪律
Approximate Quantified Mapping / 非精准量化显影 can be used inside an existing judgment owner;active method keeps decision authority;does not become the judgment owner.Use it only when the relationship is complex enough;hypothetical numbers, not factual measurements;do not compute decisions;skip it for simple adjectives;plain language is enough
#### Method Arbitration / 方法仲裁
`dominate`,`defer`,`degrade`,`block`,`stop`.TVG vs Anti-Spiral, SELA vs WAE, EDSP vs evidence, 3L5S vs direct execution, MPG vs AQM. SELA identifies direction; MPG carries it through path volatility. MPG owns the judgment; Approximate Quantified Mapping only makes variables visible.
#### Execution Impact / 执行影响
strategy, risk handling, evidence requirement, next action, stopping condition, method choice, handoff packet.If a judgment changes none of these, information acquisition, clarification, or sharper routing
#### `sela`
#### `3l5s`
#### `tplan`
#### `edsp`
#### `wae`
#### `tvg`
No bounded artifact value-gain target, no TVG
## Guardrails
docs/methodologies/shared-primitives.md;反螺旋入口;fidelity contract;resources/fidelity-contract.md;templates/fidelity-output.json;validate_using_mindthus_output.py;validation is not semantic approval
## Boundaries

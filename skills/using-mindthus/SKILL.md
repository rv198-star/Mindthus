---
name: using-mindthus
description: Use when any Mindthus judgment lens may apply; method routing, frame-risk audit, or strategic/path/control/framing ambiguity before choosing SELA, MPG, EDSP, WAE, TVG, 3L5S, or tplan.
---
## Core Claim
Truth Orientation / 真相优先:pursue facts and truth over agreement;user input is signal, constraint, or hypothesis; not evidence by itself

## Mainline
Premise Calibration / 前置校准不是独立方法论;只帮助选择;真实对象;底层约束;目标函数

### Input Framing Audit / 输入定框审计
强约束入口协议:When frame-risk exists,在进入判断之前，先检查当前问题是否已经被提问方式绑到错误层级
Frame Fitness Check / 定框适配检查: local frame trying to own global judgment.
Inputs:local frame;local-frame capture;locally true;wrong level;implementation-layer truth;definition-layer truth.
Outcomes:preserve frame;qualify frame;reframe;block pending evidence;can wake `sela`;does not require a full SELA run;not keyword rules;No frame-risk signal, no frame check.
General frame rule / 通用定框规则:any locally true frame;agent inference, method routing, tests, metrics, artifacts, or implementation details;must earn global explanatory authority before it can define the whole object
Original Prompt Contract / 原始有效提示词合同:legacy prompt template;not the judgment center;first task is not answering;First task: judge whether the user led you to the wrong level;internal audit order: true_question -> implicit_premises -> local_validity_and_layer_shift -> reframed_question -> formal_answer;leading_point
Audit discipline;A clever paragraph is not an audit;Question level before opinion;audit hidden;Do not answer as a soft commentary fallback;step outside the user's narrative;level-correct judgment;Forbidden substitute:fluent half-right verdict;runtime-only caveat;score-as-concession
Routing effect:preserve frame,qualify frame,reframe,block pending evidence.No execution impact:omit frame check
Problem-granularity:抓大放小;fix-main-blocker;minor=>residual-risk;no-patch-stacking

### AOP Aspect Activation / 切面唤起
`scripts/primitives/check.py`:shape reminder;not semantic judge;before-route/before-answer;Auxiliary checks belong inside step 3;never become a new judgment center
Aspect Ownership Matrix/切面主导权矩阵:judgment_owner conflict=>one thesis

### Partial Truth Capture / 局部真相捕获
A locally true observation must not own the whole explanation;scope_not_downgrade;scope correction cannot relabel canonical_object as local carrier
Whole Elephant Protocol / 全象流程;Whole Elephant hard gate:triad first(Compact Semantic Triad / 三根硬支柱:canonical_object;result_controller;misdirection_if_local_wins);validation failure blocks formal answer;do not route local-truth essence reduction to narrower method, including WAE, before Whole Elephant audit
Consequence probe:Contrastive Consequence Probe / 后果对比探针;local_frame_wins;whole_object_wins;better_direction_for_target
Internal Whole Elephant contract:MUST build compact audit before formal_answer;triad+probe;validation_command;output_evidence;details=>resources/fidelity-contract.md
Audit Hidden By Default / 审计默认内隐:full audit JSON internal by default;visible output starts with formal answer;expand only when user asks, validation fails, or handoff/debug needs it
Validator path rule:Do not claim validation passed unless the command actually ran;No command evidence, no validation-passed claim.If the command cannot run, use explicit not_run_fallback with fallback_reason+self_check_evidence;do not fake command evidence.

### Formal Answer Gate
Core Thesis Extraction / 主判断收束:formal_answer must start with a one-sentence core thesis
First Sentence Stress Test / 首句主判断压力测试:global_thesis_first;local_truth_after;target_result+final_say/result_owner+optimization_consequence;controller_shift;result_controller_viewpoint;no second-question gap;visible first sentence must be corrected_thesis;not an audit field list
Definition Authority Adjudication / 定义权裁决:first=object+authority;branch;3Q(local/result/wrong_opt);pressure+bar;tradeoff=>struct
Essence Wording Guard / 本质措辞护栏:corrected thesis must reject false essence claims
Explanatory Authority Check / 解释权校准:full_object,local_frame_role,authority_status,global_owner,downgraded_use,owns_explanation,contributes_locally,misclaims_authority,blocked_by_missing_evidence;local correctness is not explanatory authority
Dominant Carrier Check / 主导承载校准:target_result,primary_result_bearer,stability_basis,carrier_status:primary_carrier/supporting_surface/incidental_signal
System Subject Check / 系统主体校准:visible actor,system_object,governing_structure,actor_role,subject_status,misassigned_subject;surface caveat is not enough.Non-Mirror Correction / 非镜像纠错;Failure Channel / 失败通道;Anti-Sycophancy / 反谄媚;guardrails must not become the core
internal result:true_question,packed_premises/implicit_premises,layer_risks/local_validity_and_layer_shift,frame_status,reframed_question,routing_decision;`clean / biased / overloaded / malformed`

### 最小充分镜头
先尊重用户给出的目标函数;若用户未给出;默认效率优先;最小充分镜头:不要为了形式;shared-primitives.md

### Skill 路由
.
#### Intervention Boundary / 介入边界
Direct execution / 直接执行:do not use Mindthus.Information acquisition / 信息补全:facts, files, data, runtime proof, or user clarification.Mindthus intervention / Mindthus 介入:hard judgment point
Method Reference Boundary / 方法引用边界:method name in an inspection request is evidence scope, not route ownership;conversation forensics;rubric reference;do not say the current task is using MPG merely because it checks MPG-AQM;separate target session evidence from current confirmation request

#### Judgment Object Routing / 判断对象路由
Problem-definition failure;False binary or structural ambiguity;Long-term system efficiency versus local advantage;Qualified mainline with path/counter-force exposure;Agentic-system control-boundary mismatch;Bounded artifact with thin practical value;Mission runtime state;Repeated local repair

#### `sela`
Long-term system efficiency versus local advantage;系统级费效比;短视选择
#### `mpg`
Qualified mainline with path/counter-force exposure;mainline + proxy/carrier + concentrated exposure + now/continue/commit decision;concentrated scarce-resource exposure;not domain-specific;`mpg`;Do not use MPG when there is no actor, carrier, exposure, or path decision.
#### `3l5s`
Problem-definition failure;问题还不清楚;Discovery -> Definition
#### `tplan`
tplan requires Mission-level runtime state;ordinary complexity is not enough;do not proactively activate;durable task state;human-in-loop authority
#### `edsp`
False binary or structural ambiguity;A/B 都像对;Extreme Deduction
#### `wae`
Agentic-system control-boundary mismatch -> `wae`;Workflow / Agentic / Evidence;控制权;No agentic system, no WAE.No controller mismatch, no WAE
#### `tvg`
Bounded artifact with thin practical value;结构完整但实质浅薄;bounded artifact;TVG requires a bounded artifact whose practical value is thin and whose expected value can be named;vague dissatisfaction or ordinary writing quality;No bounded artifact value-gain target, no TVG.No active TVG loop, no TVG audit

#### Wake-Up Probes / 唤醒探针
strategic, path-bearing, or structurally ambiguous:`SELA` wake-up;`MPG` wake-up;`EDSP` wake-up.
MPG-unpack:scalar-commitment=>mainline/carrier/path/exposure/commitment;mainline+proxy/carrier+concentrated scarce-resource exposure+commit;support-only.
Do not route through `3l5s`. Do not let `wae` absorb ordinary conceptual, organizational, product, or structural boundaries.
Do not run `tvg`. Do not route to `tvg` merely because the user asks for an audit, review, or check.

#### Context Injection Point / 上下文注入口
user_preference,long_term_objective,risk_posture,authority_boundary;does not implement memory;storage, retrieval, ranking;current user input takes priority;must not silently override

#### Judgment Constraint Recognition / 判断约束识别
Facts and evidence constrain factual claims.Values and preferences constrain priorities.Interests and incentives constrain stakeholder interpretation.Emotional signals constrain attention.Risk posture and reversibility constrain action strength.Authority boundaries constrain who may decide.do not let values or emotion assert factual claims

#### Pressure Surface Check / 施压面检查
Pressure is not a standalone route;low-risk deterministic.Perspective Pressure handles single-view, incentive, or game-theoretic.SELA and EDSP own role pressure;MPG owns qualified-mainline path volatility;TVG owns bounded-artifact value pressure;Evidence / Claim Ceiling owns proof limits;Anti-Spiral owns repeated local repair pressure;owner, reason, and execution effect

#### Expression Discipline / 表达纪律
Approximate Quantified Mapping / 非精准量化显影 can be used inside an existing judgment owner;active method keeps decision authority;does not become the judgment owner.
Use it only when the relationship is complex enough. hypothetical numbers;not factual measurements;do not compute decisions.
skip it for simple adjectives;plain language is enough.
When MPG dominates and user says variables are many/dominant factor/not generic balance, include visible AQM snapshot / 显影快照 after the one-sentence thesis: mainline strength / path resistance / carrier fragility / information gap / trigger strength -> stage/probe, not commit.

#### Method Arbitration / 方法仲裁
Outcomes:`dominate`,`defer`,`degrade`,`block`,`stop`.
Conflicts:TVG-vs-Anti-Spiral;SELA-vs-WAE;EDSP-vs-evidence;3L5S-vs-direct-execution;MPG-vs-AQM.
SELA and MPG are sibling strategic lenses;SELA qualifies system-efficiency direction pressure;MPG qualifies path-carrying action.
Common order: SELA calibrates direction before MPG tests carrier/path;sequence not hierarchy.
SELA must not swallow MPG-ready carrier/path/exposure/commitment questions. MPG must not replace SELA for naked system-efficiency direction judgment.
MPG route handoff: when `mpg` dominates and system-efficiency direction pressure is present, carry `SELA support + MPG dominate` into the answer plan.
Do not leave SELA support implicit after selecting MPG;AQM visibility map or skipped reason;One final answer, two distinct judgment surfaces;Approximate Quantified Mapping only makes variables visible.

#### Execution Impact / 执行影响
strategy;risk handling;evidence requirement;next action;stopping condition;method choice;handoff packet.If a judgment changes none of these, information acquisition, clarification, or sharper routing

## Guardrails
docs/methodologies/shared-primitives.md;反螺旋入口;fidelity contract;resources/fidelity-contract.md;templates/fidelity-output.json;validate_using_mindthus_output.py;validation is not semantic approval

## Boundaries
No hard judgment point, no Mindthus. Missing facts first. Named method in evidence review is reference, not route owner.

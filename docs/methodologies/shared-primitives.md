# Mindthus Cognitive Primitives / 认知原语

## 这是什么

Cognitive Primitives / 认知原语，是 Mindthus 方法论之外的小而关键的判断碎片。
它们通过横切方式介入不同方法，为主方法提供刹车、施压、证据上限、表达降噪或
交付前定位，避免 agent 过度方法化或在错误位置继续自信推进。

This is not a new method layer. 它不是第七个方法，也不是总入口；它只是把重复出现的
小型 guardrail 集中成一个 Cognitive Primitive Index / 认知原语索引，供 `AGENTS.md`、
`using-mindthus` 和各 skill 引用。

当认知原语需要比文档提醒更硬一点时，使用
[Primitive Activation / 原语唤起机制](primitive-activation.md)：它通过少数轻量事件
显性唤起相关原语，但仍然只做 shape-only reminder，不替代 agent 判断。

## 解决什么问题

如果每个 skill 都把同一套刹车、证据上限、表达纪律重新写一遍，项目会有三个问题：

- 同一规则出现多个名字；
- guardrail 慢慢变成新的主方法；
- 修改一处边界时，其他 skill 还停在旧口径。

Use cognitive primitives by reference. 本页负责定义短规则；具体方法只写“何时触发”，
不要复制完整定义。

## 核心判断

认知原语必须同时满足三点：

- 多个方法都会用到；
- 只保护主方法，不替代主方法；
- 足够小，不值得变成独立 skill。

Do not copy the full definition into each skill. 如果某个规则需要长流程、独立产物或
完整运行时，它就不是认知原语。

## 怎么用

## Cognitive Primitive Index / 认知原语索引

| Primitive | Primary owner | Short rule |
|---|---|---|
| Minimal Sufficient Lens | `using-mindthus` | 能直接判断就不要开方法；一个 skill 足够就不要串联；轻量检查足够就不要展开完整流程。 |
| Evidence / Claim Ceiling | `WAE` | 结论强度不能超过证据；缺事实、领域输入、运行证明或 stakeholder 判断时，降级或阻断。 |
| Perspective Pressure | `SELA` / `EDSP` | 单一视角过度自洽时，用角色压力或激励检查挑战判断。 |
| Anti-Spiral | `anti-spiral-self-audit` / `tplan` | 同一局部对象第三次、负反馈或加层冲动出现时，先停下回看上游。 |
| No Abstract Jargon Wall | `AGENTS.md` | 先做表达定位：我代表什么立场、文字直接服务谁、要把对方带到哪里；先用例子、类比或直接后果讲清楚，再使用 Mindthus 术语。 |
| Approximate Quantified Mapping / 非精准量化显影 | `AGENTS.md` / `using-mindthus` | 数字是假设，关系才是重点；用假设数字显影变量、方向、主导项、敏感项和口径差，不用数字证明或计算结论。 |
| Frame Fitness Check / 定框适配检查 | `using-mindthus` / `shared-primitives` | 当局部框架可能接管全局判断时，先判断应保留、限定、重构还是因证据不足阻断。 |
| Gate Probes / 冻结前定位自省 | `AGENTS.md` / `shared-primitives` | 交付、冻结、继续、转交或停止前，确认当前产物是什么、现在处于什么状态、接下来服务谁的什么行动。 |
| Failure Smells / 误用信号 | `shared-primitives` / 各方法 | 看见“像完成但没推进”的信号时先自审；普通信号触发返修或降级，硬边界触发 block / stop。 |

### Approximate Quantified Mapping / 非精准量化显影

Approximate Quantified Mapping is not a standalone method and not a new route. It is an
expression primitive for compressed qualitative or game-relationship claims, and it
can support judgment formation by making hidden variables visible. It must not own the
judgment: SELA, EDSP, 3L5S, WAE, TVG, or tplan keeps judgment ownership.

Boundary: it can support judgment formation, but it must not own the judgment.

Use it only when the game relationship is complex enough. Good triggers include a
multi-variable trade-off, a 口径 conflict, a claim where the felt outcome flips across
participants, or a compressed verdict that hides variables, directions, dominant terms,
sensitivity points, and definition gaps.

It exposes variables, directions, dominant terms, sensitivity points, and definition gaps.

Skip it for simple, single-variable, low-stakes, or directly explainable claims. In
those cases, plain language is enough.

Short rule:

> 数字是假设，关系才是重点。

State that the numbers are assumptions. They are not factual measurements, not
evidence, and not a decision calculator. They only make the structure easier to see:
which variable moves, which term dominates, which nudge would flip the felt outcome,
and where the 口径 gap sits.

Inside another method, use it only as a clarity aid inside an existing judgment owner.
It may help that owner see the game relationship, but it cannot compute the owner's
conclusion.

Stop when the structure is visible. If the conversation turns into defending exact
digits, leave this primitive and return to fact gathering, Evidence / Claim Ceiling, or
口径 clarification.

### Frame Fitness Check / 定框适配检查

Frame Fitness Check is not a standalone method and not a new route. Inside
`using-mindthus`, it is the Input Framing Audit / 输入定框审计: a 强约束入口协议 under
Premise Calibration.

Core sentence:

> 在进入判断之前，先检查当前问题是否已经被提问方式绑到错误层级。

Original input-audit discipline / 原始输入审计纪律:

- first task is not answering; it is judging whether the user led you to the wrong level.
- Use order: true_question -> implicit_premises -> local_validity_and_layer_shift -> reframed_question -> formal_answer.
- Prioritize problem key over dialogue continuity.
- professional tone is not proof.
- common implementation is not essence.
- If the input is leading, name `leading_point` before analysis.

It handles local-frame capture: a local frame is true or useful at one level, but
begins controlling the global judgment.

The local frame may come from the user, the agent's first plausible interpretation, a
familiar Mindthus method, a green test suite, a metric, a single evidence signal, a
polished artifact, or an implementation detail.

Short rule:

> 局部正确不能自动升级成全局答案。

Use it when a locally true frame may be claiming global authority.

Framing-risk signals, not keyword rules:

- `本质上` / `归根结底` / `其实就是` / `无非是`
- `正因为我是...所以更明白`
- multiple judgments packed into one sentence
- 把实现层直接说成本体层
- 把局部机制直接说成整体解释
- 先给结论，再让模型评价
- a single test or metric standing in for readiness
- method overactivation or repeated pressure to abandon a better frame

这些词只是高置信线索；没有这些词时，只要出现打包结论、层级偷换、局部机制冒充整体解释，也应触发。低风险范围说明和用户偏好通常应 preserve frame 或直接路由。

If the wording itself sits at the wrong level, correct the question level before
answering: 如果表述本身在错误层级上，先纠正问题层级，再回答。

Do not let implementation-level truth become definition-level truth:
不要因为某个说法在实现层成立，就默认它在定义层也成立。

Original Prompt Contract / 原始有效提示词合同:
when this audit triggers, the active instruction is not a list of abstract checks.
It is the direct five-step input audit contract: 在回答前，先执行“输入审计”，不要顺着我的叙述直接推理。
Output in order: true question, implicit premises, locally valid premises and layer
shifts, reframed question, then formal answer. 优先识别问题关键，而不是优先维持对话连贯。
不要因为用户说法听起来专业就默认成立；不要把当前常见实现方式直接当作本质。
If there is a leading point, name the `leading_point` before analysis. The first
task is not answering; it is judging whether the input has pulled the model into
the wrong level.

Core Thesis Extraction / 主判断收束:
formal_answer must start with a one-sentence core thesis; do not leave the main
judgment scattered in supporting paragraphs. Shape:
local truth -> corrected owner/carrier -> practical consequence. core thesis must
name the corrected owner/carrier; generic A-but-B verdict is not enough; the
strongest sentence must not be buried at the end. Object Anchor / 对象锚定:
do not replace the asked object with its larger container; keep asked object as
subject in true_question/reframed_question/core thesis; answer the component's
positioning before the container's architecture.

Essence Wording Guard / 本质措辞护栏:
do not restate carrier/interface as essence; corrected thesis must reject false
essence claims.

Composite Object Integrity / 复合对象完整性:
do not strip operative subcomponents out of the asked object; answer the assembled
capability, not the leftover surface.

Executable Substrate Check / 可执行基底校准:
operative subcomponents move work from generation into execution/verification;
surface steering is not the higher-level positioning.

Auxiliary checks belong inside step 3 and never become a new judgment center.
They help identify local validity, overclaiming, layer shift, and the corrected
question level; they do not replace the five-step audit.

Explanatory Authority Check / 解释权校准:
use this when a local observation is trying to own the whole explanation. First name
the `full_object` being explained, then identify the `local_frame_role`: evidence,
sublayer, symptom, implementation detail, local mechanism, metric, analogy, value
constraint, or another bounded role. Set `authority_status` to `owns_explanation`,
`contributes_locally`, `misclaims_authority`, or `blocked_by_missing_evidence`. If the
local frame cannot own the explanation, name the `global_owner` and the
`downgraded_use` of the locally true part. `global_owner` must be a concrete
higher-level explanatory frame or accountable decision object, not a vague label,
and must imply an observable judgment or action difference. local correctness is
not explanatory authority.

Dominant Carrier Check / 主导承载校准:
use this when the claim concerns stable or repeatable outcomes, readiness, control,
or deterministic value. Ask which part carries stable or repeatable outcomes. Name
the `target_result`, `primary_result_bearer`, `stability_basis`, and
`carrier_status`: `primary_carrier`, `supporting_surface`, `incidental_signal`, or
`blocked_by_missing_evidence`. Do not stop at runtime-also-matters; identify the
dominant stability carrier and downgrade local influence surfaces that only steer
attention, expose evidence, or assist execution.

System Subject Check / 系统主体校准:
use this when a visible actor, carrier, model, expert, tool, or signal is being
treated as the subject of a whole system. Name the `system_object`, the visible actor,
the `governing_structure`, the `actor_role`, and `subject_status`: `system_subject`,
`local_operator`, `interface_surface`, `misassigned_subject`, or
`blocked_by_missing_context`. Do not center the answer on how the visible actor thinks
or behaves when the higher-level system allocates control, evidence, repetition,
failure handling, and authority. skill/workflow answer must name system_object +
primary_result_bearer; prompt/runtime caveat is not enough.

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

Frame Fitness can wake `SELA` when the local/global tension is strategic, such as local
advantage being mistaken for durable system-level advantage. It does not require a full
SELA run for ordinary local-to-global validity checks, and it must not replace EDSP,
WAE, TVG, Evidence / Claim Ceiling, Method Arbitration, or direct execution.

Guardrails:

- No frame-risk signal, no frame check.
- No execution impact, omit the frame check.
- No evidence, no superior frame claim.
- No user-value erasure: user goals, values, taste, risk posture, and authority
  boundaries constrain the work and must not be dismissed as mere bias.
- 低风险、低抽象、直接执行类任务，不触发。
- 不要把拆出很多前提当成判断已经完成。
- 不要让输入审计代替证据获取或正式分析。
- 审计的目标是纠正 framing，不是展示聪明。

### Pressure Surface Consolidation / 施压面收束

Pressure is not a standalone method and not a new route. It is a triggered challenge
inside an existing judgment owner.

Use pressure when a clean conclusion may be over-shaped by one perspective, hidden
incentive, game-theoretic reaction, weak evidence, downstream failure, or repeated local
repair. Skip it for low-risk deterministic work where execution or mechanical
verification already gives the answer.

When pressure is used, name the owner and the reason: Perspective Pressure belongs to
`SELA` / `EDSP`, proof pressure belongs to `Evidence / Claim Ceiling`, artifact-value
pressure belongs to `TVG`, and repeated-repair pressure belongs to `Anti-Spiral`.

### Gate Probes / 冻结前定位自省

Gate Probes 不是独立方法，不是新 skill，也不是 Gate 本身。它是 agent 在关键动作前
做的一次短定位：准备交付、冻结、继续一轮、转交、阻断或停止时，先确认自己没有跑偏。

Short rule:

> 别急着交付，先确认自己还站在正确的位置上。

任务落地版三问：

1. 这是什么：当前产物或动作承担什么责任？
2. 它在哪里：证据、边界、风险、误用信号和目标差距现在是什么状态？
3. 它去哪里：接下来服务谁的决策、执行、审查、交接、生成或继续迭代？

Gate Probes 可以改变下一步：`freeze`、`return-remediate`、`block`、`stop`、转交，
或请求用户授权。但它不能替代证据、用户权限、具体方法的 Gate、TVG exit 判断，
也不能替代 tplan 的 continuation authorization。

最该触发它的时刻，是 agent 准备说“完成了”、想再跑一轮、或因为“看起来只差一点”
而准备继续同一路径。

### Failure Smells / 误用信号

Failure smells / 误用信号，是提醒 agent：这个回答、方法运行、任务状态或产物可能
“看起来完整，但没有完成真正工作”。它不是另一个方法，也不自动等于硬 veto。

按三档处理：

- 普通信号：暂停、自审、返修、换方法，或降低 claim。
- 方法 / profile veto：当前方法、profile 或产物不能 freeze，必须先修。
- 硬 veto：证据不诚实、用户约束冲突、安全边界、权限越界或 claim ceiling 过高，必须 block 或 stop。

每条误用信号都必须产生执行影响。如果它不改变策略、证据要求、下一步、停止条件、
方法路由或交接信息，它就只是评论，不应该写进清单。

#### 方法误用信号索引

| 方法 | 误用信号和行动影响 |
|---|---|
| `using-mindthus` / 路由 | 简单明确的事被包装成方法语言 -> 回到直接执行。缺事实却用方法补洞 -> 先补证据或问用户。多个方法堆叠但没人负责主判断 -> 先选 dominate / defer / degrade / block / stop。答案说了方法名却不改变行动 -> 收紧路由或跳过 Mindthus。 |
| `3L5S` | 问题仍不能被复述、定位或证伪 -> 回到 Discovery / Definition。直接从现象跳到方案 -> 分开 signal、problem 和 action。BTGSB 变成任务列表但没有验收证据 -> 补 Target、Gap 和 verification。子任务全是“优化 / 研究 / 处理” -> 先对该子任务再跑 BTGSB。 |
| `EDSP` | 坐标系漂亮但变量重叠 -> 重建维度。极端只是普通情况的加强版 -> 继续推极端，直到结果能清楚塌缩。结构未稳就开始 Scenario Projection -> 停下 SP，重建 ED。结论很聪明但不改变选择、边界或证据要求 -> 视为 EDSP 失败。 |
| `SELA` | 用局部优秀证明长期可守 -> 检查可规模化能力和系统反馈环。把系统效率写成“效率一定赢” -> 恢复硬价值边界和时机判断。长期方向直接变成立刻行动 -> 先做 Timing Check。忽略过渡价值或不可逆伤害 -> 降级或阻断 SELA 结论。 |
| `MPG` | 主线没有行动者、载体、暴露或期限 -> 先限定主线。路径风险清单不改变姿态、预算、载体或触发条件 -> 重建主线承载方案。把“长期正确”当成“现在可以重仓” -> 设暴露预算和触发条件。把对抗力量当坏人 -> 重新当作塑形路径的信息来映射。 |
| `WAE` | 脚本、schema 或 checklist 在判断语义真相 -> 把判断权还给 agent / 人，脚本只做 shape。workflow 控制了 truth-uncertain 对象 -> 转给 agentic judgment + evidence。证据只是字段，没有约束 claim -> 绑定 claim 或降级。agentic judgment 扩张到确定性杂活 -> 交回 workflow。 |
| `TVG` | 产物更长但没有更有用 -> 围绕 value axes 收束或返修。下一轮没有明确正价值假设 -> 停止或带 warning freeze。缺事实却用流畅文字填空 -> 硬 veto，补证据或降低 claim ceiling。profile 成功和 runtime 救场混在一起 -> 记录 claim ceiling 和残留失败模式。 |
| `tplan` | Task/SubTask/Step 已经说不清如何服务 Mission -> 做 alignment 或 Mission Review。logs 很多但 evidence 不约束验收 -> 补 evidence 或降级进展。继续同路径靠“花了很多时间 / 快好了”辩护 -> 要 continuation authorization。共享风险存在但不影响后续选择 -> 上浮 scoped risk，或留在本地。 |

具体措辞可以随方法变化，但行动影响不能省。只让输出显得更懂方法、却不改变下一步的
“误用信号”，应该删掉。

## 具体案例

### 案例 A：TVG 想继续加深第三轮

一份交接文档已经加深两轮，第三轮只是准备再加 checklist。这里不需要在 TVG 内重写
反螺旋规则，只触发 `Anti-Spiral`，回到上游目标或做等量替换。

### 案例 B：SELA 判断里出现真实利益冲突

SELA 负责整体效率与局部优势判断。如果销售、法务、实施、财务各自会因结论不同而受益
或受损，不要在 SELA 里复制一套博弈论方法；触发 `Perspective Pressure`，用激励检查
挑战单一视角。

### 案例 C：一句“年轻人没机会了”压扁了博弈结构

这句话可能同时混着成功概率、成功收益、失败代价、入场成本、参照系和方差。这里不要
新开一个独立 skill，也不要假装有真实数据。只用假设数字说明：也许上限更高，但失败
代价、参照物和方差一起变大，所以同一个局面对不同人有完全不同的体感。

正确输出是变量关系和口径差，不是“算出今天更好/更差”。

## 常见误用

第一种误用，是把认知原语当成新流程。它只在信号出现时触发。

第二种误用，是在各 skill 里复制本页定义。这样会重新制造重复。

第三种误用，是让原语决定主问题。原语只刹车、施压或限制 claim，主判断仍归对应 skill。

第四种误用，是把非精准量化显影升级成精确模型。数字只是让博弈关系可见；一旦开始
防守具体数字，原语已经失效。

第五种误用，是把 Gate Probes 当成真正的 Gate。定位自省只能帮助 agent 发现自己是否
站错位置，不能替代具体方法的退出判断、证据、用户授权或停止条件。

第六种误用，是把 Failure Smells 当成机械阻断表。普通误用信号只要求暂停自审和调整行动；
只有触发证据、权限、安全、用户约束或 claim ceiling 底线时，才升级为 hard veto。

## 边界

认知原语不替代 `SELA`、`3L5S`、`EDSP`、`WAE`、`TVG` 或 `tplan`。

它也不替代 Gate、事实、领域研究、运行证明、用户判断或授权。遇到缺输入的问题，
正确动作通常是补输入、降级结论或停止，而不是新增方法层。

## 与其他方法的关系

- `using-mindthus` 引用本页来避免入口 skill 变厚。
- `AGENTS.md` 引用本页来保持默认姿态短。
- 各方法页只保留与本方法相关的触发条件。
- `Primitive Activation` 用脚本在少数关键事件上唤起原语，但不判断真伪、价值或 exit。

## 导航

- 返回 [README](../../README.md)
- 查看 [Primitive Activation](primitive-activation.md)
- 查看 [Using Mindthus skill](../../skills/using-mindthus/SKILL.md)
- 查看 [Anti-Spiral 方法页](anti-spiral-self-audit.md)

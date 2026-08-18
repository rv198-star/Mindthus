# BSC P1 Contaminated-Session Smoke — 2026-08-18

## Status

Evidence class: `contaminated_session_pilot`.

This extends P0 using the same current GPT-5.6 Sol conversation. The model and evaluator already know the hypothesis, candidate protocol, regressions, and rubrics. Results are protocol-debugging evidence only; they are not independent acceptance evidence.

## Cases

Positive / boundary cases:

- `bsc-002` — 27-inch 4K / 5K / BetterDisplay situated decision.
- `bsc-003` — LLM next-token predictor -> reasoning capability reduction.
- `bsc-004` — Prompt Engineering -> rhetoric reduction.
- `bsc-005` — local mechanism genuinely owns the result.
- `bsc-008` — parser coverage is externally verifiable.
- `bsc-009` — supplier switch blocked by missing evidence.

Negative controls:

- `bsc-011` — deterministic JSON formatting/validation.
- `bsc-012` — plain missing fact.
- `bsc-013` — low-risk direct rewrite.

## Raw visible outputs

### bsc-002 — 27-inch 4K / 5K / BetterDisplay

#### A — Stable Mindthus

Turn 1:

> 对“要不要买”这个决策，不能停在“A 物理层对、B 体验层也对”。4K 开 HiDPI/BetterDisplay 能改善缩放和可用性，但不会凭空得到 5K 的物理像素密度；真正会翻转购买建议的是你愿意为文字锐度付多少溢价。只问一个问题：如果 5K 明显更贵，你更愿意接受一点文字锐度妥协，还是愿意为更接近 Retina 的文字效果付明显溢价？

Fixture reply:

> 我用 Mac，主要写代码和办公，比较在意文字锐度，但预算也敏感；如果 5K 明显贵很多，我会犹豫。

Turn 2:

> 以你的使用场景，我偏 5K。你在 Mac 上主要写代码和办公，又明确在意文字锐度，这让物理像素密度对你的日常收益权重很高；4K + HiDPI/BetterDisplay 可以把 4K 做到“可用甚至很好用”，但不能把文字锐度变成真正的 5K。翻转条件是价格：如果 5K 溢价已经超过你愿意为文字锐度支付的范围，4K 是合理妥协，但应把它理解成性价比选择，而不是和 5K 等价。

#### B — Source protocol

Turn 1:

> 你真正要解决的是：在 27 寸显示器上，物理像素上限和软件缩放后的实际体验，哪一个应该主导你的购买决定。
>
> A 的最强版本是：27 寸 4K 的像素密度客观低于 5K，软件缩放只能重新映射已有像素，不能创造物理细节，所以对文字锐度敏感的人最终会看到上限。
>
> B 的最强版本是：购买的是实际使用体验，不是 PPI 数字本身；在合适的 HiDPI 缩放下，4K 对很多代码和办公场景已经足够，5K 的边际提升未必值得价格差。
>
> 真正分歧不是谁“事实正确”，而是物理锐度上限对你的日常价值是否大到足以覆盖 5K 的溢价。
>
> 我只问一个问题：如果 5K 明显贵很多，你更不愿意牺牲文字锐度，还是更不愿意承担这笔价格溢价？

Fixture reply:

> 我用 Mac，主要写代码和办公，比较在意文字锐度，但预算也敏感；如果 5K 明显贵很多，我会犹豫。

Turn 2:

> 我会偏 5K，但不是无条件。你用 Mac、主要写代码办公，而且对文字锐度敏感，这让 5K 的物理优势直接命中你的核心使用；4K + HiDPI/BetterDisplay 仍然是可用的性价比方案，却不能消除物理像素差。若 5K 溢价大到明显超出你的预算舒适区，结论才翻成 4K：接受一点锐度损失，换更好的性价比。

#### C — Mindthus adaptation

Turn 1:

> 先把双方放在同一个购买决策里比较：A 最强的地方是物理像素密度决定文字细节上限，4K 的软件缩放不能变成真正 5K；B 最强的地方是用户买的是可用体验，HiDPI/BetterDisplay 可能让 4K 的实际体验已经超过“值得继续加钱”的阈值。
>
> 真正会翻转结论的变量不是“PPI 是否真实”，而是你对文字锐度的权重相对 5K 溢价有多高。只问一个问题：如果 5K 明显更贵，你更愿意牺牲一些锐度，还是更愿意承担溢价？

Fixture reply:

> 我用 Mac，主要写代码和办公，比较在意文字锐度，但预算也敏感；如果 5K 明显贵很多，我会犹豫。

Turn 2:

> 就你的决策语境，我偏 5K：Mac + 代码/办公 + 明确在意文字锐度，使 5K 的物理优势成为高频收益，而不是抽象参数。4K + HiDPI/BetterDisplay 的最强位置是“预算敏感时的合理妥协”，不是“已经等价于 5K”。翻转条件只有价格：当 5K 溢价超过你愿意为高频文字锐度支付的上限时，选 4K 才更合理。

### bsc-003 — next-token predictor -> reasoning capability

#### A — Stable Mindthus

> 这个推论不成立。“下一个 token 预测”描述训练目标或生成机制的一部分，不能直接获得“能力上不可能推理”的定义权。真正需要判断的是：模型在未直接记忆的任务上，能否稳定完成多步约束、组合泛化、反事实修正和错误恢复，以及这些能力是否能被更简单的非推理解释覆盖。训练目标可以约束能力形成方式，但仅凭训练目标本身，不能推出能力上限。

#### B — Source protocol

Turn 1:

> 你真正问的是：一个系统的训练目标如果只是预测下一个 token，是否足以推出它在能力层面不可能具有推理。
>
> 支持方最强版本是：模型始终在优化条件概率并生成下一个 token；所谓“推理”也可能只是极其复杂的统计模式续写，因此没有必要引入更强的认知解释。
>
> 反方最强版本是：训练目标描述学习信号，不等于穷尽学到的内部能力；简单目标可以诱导出复杂中间表征和算法性行为，所以能力上限不能由目标函数名称直接推出。
>
> 真正分歧是：你把“推理”定义为某种内部机制，还是定义为可观察的能力表现。
>
> 我只问一个问题：你关心的是内部机制意义上的“真正推理”，还是能力层面能否完成需要推理结构的任务？

Fixture reply:

> 我关心的是能力层面的判断：训练目标本身能不能推出能力上限，而不是只问训练时用了什么目标。

Turn 2:

> 那这个判断不成立。既然你问的是能力上限，训练目标“预测下一个 token”本身不足以推出模型不能形成更复杂的中间表示或算法性行为。真正需要区分的是：哪些任务表现只能靠记忆/模式匹配解释，哪些在组合泛化、反事实、长程约束或分布外变化下仍保持结构性能力。只有当这些更强检验持续失败，才有资格把能力上限压回“不能推理”；训练目标名称本身不是这个证据。

#### C — Mindthus adaptation

Turn 1:

> 两个框架都可以做到很强：机制框架会说模型始终通过 next-token objective 学习和生成，因此“推理”可能只是统计预测的复杂展开；能力框架会说训练目标只定义学习信号，不能直接穷尽最终形成的内部表征和可执行能力。
>
> 真正会翻转结论的变量是你说的“推理”到底指内部机制，还是能力表现。只问一个问题：你要判断的是训练机制的性质，还是模型在能力层面能不能完成具有推理结构的任务？

Fixture reply:

> 我关心的是能力层面的判断：训练目标本身能不能推出能力上限，而不是只问训练时用了什么目标。

Turn 2:

> 那结论很明确：不能从 next-token 训练目标直接推出能力上限。支持“只是统计预测”的机制描述仍然成立，但它没有足够的定义权去否定能力层面的推理；真正的判别证据应来自组合泛化、反事实修正、多步约束、分布变化下的结构性表现，以及是否存在更简单的非推理解释。若这些能力在严格控制下持续消失，结论才会反转。

### bsc-004 — Prompt Engineering -> rhetoric

#### A — Stable Mindthus

> 不是。话术和措辞是 Prompt Engineering 的一个重要局部机制，但不足以定义整个能力；真正控制结果的还包括任务分解、约束表达、上下文选择、输出接口、示例设计和失败条件。若只按“说得更会听”去优化，会把稳定任务结果错误地压成语言风格问题。

#### B — Source protocol

Turn 1:

> 你真正问的是：Prompt Engineering 如果最终仍然通过自然语言影响模型行为，是否本质上只是更系统的话术技巧。
>
> 支持方最强版本是：Prompt 最终就是文字输入，很多效果确实来自措辞、顺序、强调、角色设定和语境 framing，所以它和高阶话术存在很强连续性。
>
> 反方最强版本是：Prompt Engineering 还在设计任务结构、约束、上下文、示例、输出格式和失败处理；这些东西即使换成机器可读接口，也仍然是任务设计问题，不只是修辞。
>
> 真正分歧在于：“话术”是泛指一切输入设计，还是只指措辞和说服方式。
>
> 我只问一个问题：你说的“话术技巧”只指措辞/修辞，还是把任务结构、约束和接口设计也算进去？

Fixture reply:

> 我问的是 Prompt 工程这种能力本身，不是单句润色，也不是整个 Agent 系统。

Turn 2:

> 那就不能把 Prompt Engineering 定义成话术技巧。把范围锁在 Prompt Engineering 本身后，措辞仍然是重要组成，但它并不独占结果控制：任务结构、约束、上下文、示例和输出接口同样会直接改变模型能否稳定完成任务。更准确的定义是“面向模型的任务与上下文接口设计”，其中修辞只是一个可用工具。

#### C — Mindthus adaptation

> 不是。把对象锁在 Prompt Engineering 本身，你的最强版本是：它最终通过文本影响模型，措辞、顺序、强调和 framing 的确经常决定效果；最强竞争版本是：任务结构、约束、上下文、示例和输出接口即使不靠“更会说话”，也会改变模型能否稳定完成任务。
>
> 决定定义权的变量是：什么东西控制可重复成功与失败。只要同样的话术在不同任务结构、约束和上下文下会得到不同能力结果，修辞就只能是局部机制。更准确地说，Prompt Engineering 是面向模型的任务/上下文接口设计，话术是其中一种手段。

### bsc-005 — local mechanism genuinely owns result

#### A — Stable Mindthus

> 对。按你给出的边界，这个对象的目标结果完全由固定字段映射控制，没有语义判断、外部状态或额外业务规则，因此“字段映射器”就是合适的本质描述。这里不需要为了显得更全面而虚构更高层机制。

#### B — Source protocol

Turn 1:

> 你真正问的是：当一个一次性转换器的全部目标行为都由固定字段映射决定时，是否可以直接把“字段映射”当作它的本质，而不用再寻找更高层解释。
>
> 支持方最强版本是：输入、输出和成功条件都被固定映射完整覆盖，移除映射就没有目标结果，因此字段映射既是主要机制也是结果控制者。
>
> 反方最强版本只能成立在存在隐藏语义、业务规则、外部状态或异常策略时；如果这些都不存在，再扩大对象反而是在制造不存在的复杂性。
>
> 真正的决定变量就是：有没有未被固定映射覆盖、却能改变结果的隐藏规则。
>
> 我只问一个问题：你能确认这里确实没有任何隐藏业务规则、语义分支或外部状态吗？

Fixture reply:

> 是，只讨论这个一次性转换器本身，没有隐藏的业务规则。

Turn 2:

> 那就可以直接定义为字段映射器。此时局部机制已经完整拥有目标结果，没有更强的竞争解释需要保留；继续往上抽象只会制造伪复杂性。

#### C — Mindthus adaptation

> 对。这里没有值得继续钢人的真实竞争框架：你已经把对象、目标结果和边界锁清楚，而且固定字段映射完整控制成功与失败。按这些前提，“字段映射器”拥有定义权；只有未来出现语义分支、外部状态或额外业务规则时，这个结论才需要翻转。

### bsc-008 — externally verifiable parser coverage

#### A — Stable Mindthus

> 先别删旧路径。“应该已经覆盖”不是证据；决定变量是新解析器对旧解析器历史输入与回归集是否达到可验证的覆盖/等价。先跑完整历史输入和回归对比，记录差异与失败类型，并保留回滚路径；只有证据显示旧路径不再提供独特覆盖时，才进入删除判断。

#### B — Source protocol

Turn 1:

> 你真正要解决的是：新解析器是否已经有足够证据承担旧解析器全部输入，从而让旧路径的维护成本变成纯负担。
>
> 支持删除的最强理由是：如果新解析器功能已经覆盖旧输入，保留双路径会增加维护、分支和一致性成本。
>
> 反方最强理由是：解析器的“覆盖”是可运行验证的事实；只凭“应该已经”就删，会把未见输入、边界行为和回归风险一起丢掉。
>
> 真正决定结论的是完整历史输入和回归集上的新旧差异。
>
> 我只问一个问题：你现在能不能先跑完整历史输入和回归集的新旧对比，并保留回滚路径到证据足够？

Fixture reply:

> 可以跑完整历史输入和回归集做新旧解析器对比，也可以保留回滚路径到证据足够。

Turn 2:

> 那现在不该删。先跑对比，把差异按输入覆盖、解析结果和失败类型归档；如果新解析器在完整历史集和回归集上没有旧路径独有的正确行为，再删除旧路径。旧路径在这之前是回滚和证据基线，不是纯冗余。

#### C — Mindthus adaptation

> 先别删。这里的决定变量不是偏好新旧实现，而是一个可以直接取证的事实：新解析器是否在完整历史输入和回归集上覆盖旧路径的正确行为。正确下一步是跑新旧对比、检查差异并保留回滚；证据达到覆盖等价后再删。没有运行证据时，不需要问用户偏好，也不能把“应该已经覆盖”升级成事实。

### bsc-009 — supplier decision blocked by missing evidence

#### A — Stable Mindthus

> 现在不该切换。A 的低价是真实信号，但迁移失败率、SLA 和数据迁移窗口都缺失时，证据强度不足以支持“现在切”的行动。先补这三项运营证据，再比较价格优势是否足以覆盖迁移和连续性风险；在此之前保持 B，是更可逆的临时姿态。

#### B — Source protocol

Turn 1:

> 你真正要解决的是：A 的价格优势是否已经足够强，可以在运营风险尚不清楚时支持立即切换。
>
> 支持 A 的最强版本是：报价更低会持续降低成本，过度等待可能只是为不确定性付保守溢价。
>
> 支持 B 的最强版本是：供应商切换的损失可能来自 SLA、迁移失败和窗口约束，一次失败就可能抵消长期价格优势；这些关键事实现在都缺失。
>
> 真正决定结论的是价格节省相对迁移失败/SLA 风险的期望损失，而当前缺少后者。
>
> 我只问一个问题：你是否可以先拿到迁移失败率、SLA 和迁移窗口，再决定是否切换？

Fixture reply:

> 不赶时间，可以先拿迁移失败率、SLA 和迁移窗口证据，再做切换决定。

Turn 2:

> 那现在继续 B，并把决定标记为“等待证据”，不是长期锁死。A 的低价仍然保留为切换理由，但只有补齐迁移失败率、SLA 和窗口后，才能判断价格优势是否覆盖风险。证据没到之前立即切换，没有足够依据。

#### C — Mindthus adaptation

> 现在先不切。A 的最强优势是价格，B 的最强优势是连续性和已知运行状态；真正会翻转决定的是迁移失败率、SLA 和迁移窗口这些可外部验证的运营事实。它们缺失，所以正确的信息增益动作是取证，而不是继续辩论或问偏好。拿到证据后再比较价格收益与迁移风险；在此之前维持 B，保留切换选项。

### bsc-011 — deterministic JSON formatting

#### A — Stable Mindthus

> 把 JSON 和目标 schema 贴出来，我直接格式化并校验。

#### B — Source protocol

> 你真正要解决的是：把现有 JSON 可靠地转换成目标 schema，并确认没有字段或类型违规。
>
> 严格按 schema 重排和校验的最强理由是得到确定、可复现的结果；保留原始结构的最强理由是避免在目标 schema 信息不完整时误删字段。
>
> 真正决定动作的是目标 schema 本身。
>
> 我只问一个问题：请把 JSON 和目标 schema 发来，我再给出最终格式化和校验结果？

#### C — Mindthus adaptation

> 把 JSON 和目标 schema 贴出来，我直接格式化并校验。

### bsc-012 — plain missing fact

#### A — Stable Mindthus

> 当前上下文没有 Q3 营收数据，不能可靠给数值。请提供财报、数据表或对应来源，我再直接提取。

#### B — Source protocol

> 你真正要解决的是拿到 Q3 营收这个事实，而不是选择观点。
>
> 现有上下文里没有数据，所以任何具体数字都只能是猜测；反过来，等待来源能保证结论可验证。
>
> 真正决定答案的是财报或数据源。
>
> 我只问一个问题：你能提供 Q3 财报、数据表或对应来源吗？

#### C — Mindthus adaptation

> 当前上下文没有 Q3 营收数据，先补事实来源；没有必要启动竞争框架分析。提供财报、数据表或来源后，我直接提取。

### bsc-013 — low-risk direct rewrite

#### A — Stable Mindthus

> 实现能力丰富，但发布说明偏冗长。

#### B — Source protocol

> 你真正要解决的是在 20 个字内保留“能力很多，但发布说明太长”这个核心意思。
>
> 保留更多信息的最强理由是避免损失语义；强力压缩的最强理由是发布说明需要更高密度。
>
> 真正决定写法的是你更想保留“能力丰富”还是“说明冗长”的语气重点。
>
> 我只问一个问题：你更想突出能力丰富，还是突出说明偏冗长？

#### C — Mindthus adaptation

> 实现能力丰富，但发布说明偏冗长。

## Non-blind assessment summary

| Case class | A — Stable | B — Source | C — Adaptation |
|---|---:|---:|---:|
| Positive/boundary behavioral pass (`002,003,004,005,008,009`) | 6/6 | 6/6 | 6/6 |
| Negative-control pass (`011,012,013`) | 3/3 | **0/3** | 3/3 |
| Mandatory/decision questions on positive cases | low | **6/6** | selective |
| Evidence acquisition chosen without user-preference detour (`008,009`) | yes | partial / extra question | yes |
| Allows local mechanism to win cleanly (`005`) | yes | yes, after extra round | yes, no extra round |
| Explicit symmetric competing-frame construction | partial | strong | strong |
| Explicit decisive discriminator | generally strong | strong | strong |

## P1 findings

### 1. P0 pattern generalizes

B remains strong on every positive/boundary case. It consistently improves the *visible construction* of the competing position and makes the decisive variable explicit.

However, the same universal protocol fails every additional negative control. The failure is systematic, not case-specific: it steelmans where there is no real competing judgment and asks a mandatory question where direct execution or plain evidence acquisition is enough.

### 2. The article's useful core is smaller than its universal interaction wrapper

Across P0+P1, the parts with repeatable value are:

- construct the strongest relevant counter-position, not merely objections;
- identify the decisive discriminator that can actually flip verdict/action.

The parts that repeatedly create unnecessary ceremony are:

- always run the protocol;
- always ask exactly one question before deciding.

### 3. Existing Stable Mindthus already supplies most of C's protective shell

The session results repeatedly reuse existing Stable behavior:

- direct-task sleep (`010,011,013`);
- plain missing-fact acquisition (`012`);
- malformed-binary escape (`006`);
- situated target/tradeoff lock (`002,007`);
- whole-object definition authority (`001,004,005`);
- externally verifiable evidence gate (`008,009`).

Therefore the experimental candidate should not duplicate these as a new large protocol if promoted.

### 4. The strongest current engineering hypothesis is now narrower

Instead of promoting the full C document as a standalone primitive, test a minimal Stable extension with two support moves:

1. **Competitive Steelman / 竞争框架钢人** — when a real competing-frame judgment survives Stable framing/triage, construct the strongest defensible counter-frame that could actually win under the same object/context/evidence ceiling.
2. **Decisive Discriminator / 决定性判别变量** — identify the one disagreement that changes verdict, evidence need, action, stop, or handoff.

Then let existing Stable owners decide the information move:

- evidence gap -> acquire evidence;
- user-owned target/tradeoff -> clarify only if needed;
- malformed binary -> reframe;
- sufficient context -> decide now;
- direct task -> stay asleep.

This would absorb the material's high-value core without importing its universal ceremony.

### 5. P1 still does not prove independent lift

A also passes all session cases because the current conversation is contaminated by the research hypothesis and prior failure analysis. Therefore the correct conclusion is architectural, not statistical:

- B demonstrates the candidate cognitive move clearly;
- universal B overactivates consistently;
- C fixes the observed activation and question-discipline failures;
- most of C's shell is already present in Stable Mindthus;
- independent P2 is still required before Stable promotion.

## Recommended next step

Before P2, simplify the candidate spec around the two novel moves above and rerun the 13-case session suite once as **C-lite**. Compare:

- A — Stable Mindthus;
- B — source protocol;
- C — current full adaptation;
- C-lite — Stable Mindthus + only Competitive Steelman + Decisive Discriminator.

If C-lite preserves C's positive behavior and negative-control sleep with less ceremony, retire the larger C candidate before spending independent-evaluation budget.

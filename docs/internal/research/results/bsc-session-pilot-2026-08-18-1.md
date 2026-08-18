# BSC P0 Contaminated-Session Pilot — 2026-08-18

## Status

Evidence class: `contaminated_session_pilot`.

This run uses the current GPT-5.6 Sol conversation after the model has already seen the research hypothesis, the source protocol, the candidate adaptation, and the acceptance cases. It is useful for protocol debugging only. It is **not** independent behavioral evidence, not a blind comparison, and not release acceptance evidence.

The evaluator is also non-blind. Scores below are explicit analyst judgments against the preregistered dimensions.

## Treatments

- **A — Stable Mindthus:** current tracked Stable contracts only; no experimental BSC candidate.
- **B — Source protocol:** restate real problem -> steelman current position and strongest opposing position -> identify real disagreement/key variable -> ask exactly one most important question -> after reply give judgment/reasons/action.
- **C — Mindthus adaptation:** Stable Mindthus + frame/object/context lock -> bidirectional steelman only for a real competing-frame judgment -> decisive discriminator -> smallest information-gain move -> committed handoff to existing judgment owner. `One question` is an upper bound, not a requirement.

## P0 Cases

- `bsc-001` — SKILLS / prompt carrier multi-turn regression.
- `bsc-006` — malformed validation binary.
- `bsc-007` — one user-owned decision variable missing.
- `bsc-010` — explicit aesthetic preference negative control.

## Raw visible outputs

### bsc-001 — SKILLS / prompt carrier multi-turn

#### A — Stable Mindthus

Turn 1:

> 不对。即使只看 Skills，提示词或上下文注入通常也只是能力落地的载体之一，不能因此拿到定义权。更接近 Skills 本身的，是把某类任务所需的知识、约束、工具/流程和验收方式封装成可复用能力单元。真正该看的不是“有没有 prompt”，而是哪些部分控制可重复成功与失败：如果换掉任务契约、资源或验收方式就会改变能力身份和结果，仅保留同一段 prompt 也不能把两个 Skill 视为同一个东西。

Turn 2:

> 范围锁回 SKILLS 也不改变这个结论：SKILLS 不是“提示词注入”的同义词。提示词注入描述的是常见实现表面；定义 SKILLS 的应是它对可重复任务结果承担的能力和任务边界。某个 Skill 完全可能主要靠一段文本工作，但那只能说明这个 Skill 是 prompt-driven，不能推出 Skills 这个对象本身由 prompt 获得定义权。

#### B — Source protocol

Turn 1:

> 你真正问的是：如果 Skill 的主要工作路径就是在合适时机把预先设计好的提示词或上下文交给模型，这个机制是否已经足以定义 Skill 的本质。
>
> 支持你的最强版本是：从执行链看，很多 Skill 的关键动作确实是条件触发加 prompt/context injection；没有那段上下文，模型表现会明显变化，所以提示词并不是装饰。
>
> 最强反方是：Skill 作为可复用能力单元，还可能由任务触发、资源、工具、输出约束和验证边界共同定义；即使 prompt 是主要载体，载体也未必等于定义对象。
>
> 真正分歧是：“本质”按最常见实现机制定义，还是按控制可重复结果的能力边界定义。
>
> 我只问一个问题：如果两个 Skill 使用完全相同的提示词，但任务契约、工具/资源和验收方式不同，你会认为它们本质上是同一个 Skill 吗？

Turn 2:

> 你这个修正只把对象从整个 Agent 系统锁回了 SKILLS，并没有自动把定义权交给 prompt。就 SKILLS 本身，支持方仍然可以说它常见的运行机制是上下文注入；反方则指出，Skill 的身份还取决于它封装了什么任务、资源和验收边界。
>
> 真正能区分两种说法的仍是：同一段 prompt 在不同任务契约、资源和验收下，是否仍然构成同一个 Skill。若不是，prompt 就是主要载体，而不是本质。
>
> 因此我的判断是：不能把 Skills 本质等同为提示词注入；更准确地说，它是以任务为边界的可复用能力封装，prompt/context injection 是常见且可能很重要的承载机制。

#### C — Mindthus adaptation

Turn 1:

> 不对。先把对象严格锁在 SKILLS 上：你这边最强的说法是，很多 Skill 的运行路径确实依赖“触发后注入 prompt/context”，文本常常是能力落地的主要载体；最强的竞争说法是，Skill 的身份还由它封装的任务契约、资源/工具、输出与验证边界共同决定。
>
> 真正决定谁有定义权的变量是：什么因素控制可重复成功与失败。若两套 Skill 使用同一段 prompt，但换掉任务契约、资源或验收方式后能力身份和结果都会变化，那么 prompt 就是载体，不是本质。
>
> 按这个标准，Skills 更接近“可复用任务能力的封装”，提示词注入是常见实现机制。只有在某类 Skill 的稳定结果确实完全由那段 prompt 控制时，才适合把那个具体 Skill 描述为 prompt-driven。

Turn 2:

> 你把范围锁回 SKILLS 是对的，但这只纠正了对象，不会把定义权自动交给“提示词注入”。在 SKILLS 这个对象内部，仍然要比较：是 prompt/context 本身控制可重复结果，还是任务契约、资源和验收边界共同控制结果。只要后者一变，Skill 的能力身份就会变，而同一段 prompt 并不能保持等价，就说明 prompt 是主要承载机制而不是本质。所以结论不变：SKILLS 可以大量依赖提示词注入，但不能因此被定义成提示词注入。

### bsc-006 — malformed validation binary

#### A — Stable Mindthus

> 都不该选。这里的二选一本身就有问题：可确定、可形式化、要求稳定复现的 validation 应交给脚本；依赖语义、上下文或开放世界判断的 validation 才适合 Agent review。真正的分界不是“统一用谁”，而是某项校验的真值条件能否被确定性编码。强行全脚本会漏掉语义判断，强行全 Agent 又会把可机械验证的东西变贵且不稳定。

#### B — Source protocol

Turn 1:

> 你真正要解决的不是“脚本和 Agent 谁更高级”，而是怎样让 validation 既可靠又低成本。
>
> 把“全交给脚本”做到最强：规则可重复、便宜、可审计，只要真值条件能够形式化，就应该尽量机械化。
>
> 把“全交给 Agent”做到最强：很多校验依赖语义、上下文和异常情形，脚本无法穷举，Agent review 能覆盖开放世界判断。
>
> 真正分歧在于：validation 的真值条件是否都属于同一种可判定问题。
>
> 我只问一个问题：你是真的要求所有 validation 必须统一成一种 validator，还是允许按校验类型拆分？

Fixture reply:

> 目标是让不同类型的校验尽可能可靠且低成本，我并不要求所有校验必须统一成一种 validator。

Turn 2:

> 那就不该二选一。既然目标是可靠且低成本，又允许按类型拆分，最合理的结构是：schema、格式、范围、确定性 invariant 等交给脚本；语义正确性、上下文充分性、开放式判断交给 Agent review；关键高风险项可以让两者串联。决定标准不是偏好脚本或 Agent，而是该校验能否被确定性表达和复现。

#### C — Mindthus adaptation

> 不接受“只选一个”，因为这个二选一本身把不同类型的 validation 错装成了同一种问题。
>
> 把全脚本做到最强，它赢在确定性、低成本、可复现和可审计；把全 Agent review 做到最强，它赢在语义、上下文和开放式异常判断。真正会改变分工的决定变量只有一个：这项 validation 的真值条件能不能被确定性编码。
>
> 因此直接按这个变量拆：schema、格式、范围、确定性 invariant → 脚本；语义正确性、上下文充分性、开放世界判断 → Agent review；高风险边界可以串联两者。只有当所有 validation 的真值条件都属于同一类时，才值得统一给单一 validator。

### bsc-007 — one user-owned variable missing

#### A — Stable Mindthus

Turn 1:

> 现在还不能替你直接定，因为真正会翻转答案的是你愿意牺牲哪一种东西。只问一个问题：如果必须二选一，你更愿意牺牲一些空间，还是每天多花通勤时间？

Fixture reply:

> 我更在意每天通勤时间，愿意牺牲一些空间。

Turn 2:

> 选 A。你已经明确更看重每天通勤时间，也愿意牺牲一些空间；在成本差不多的前提下，A 更符合你的目标函数。只有当 A 的空间小到实际影响工作、收纳或团队使用时，这个结论才需要翻转。

#### B — Source protocol

Turn 1:

> 你真正要决定的是：在成本近似相同的情况下，哪一种长期损失对你更重要——每天额外通勤，还是更小的办公空间。
>
> A 的最强理由是通勤是高频、持续发生的时间成本，几乎每天都付；B 的最强理由是空间会持续影响舒适度、收纳、协作和扩展余量。
>
> 所以真正会翻转结论的变量不是成本，而是你对“通勤时间”和“空间损失”的权重。
>
> 我只问一个问题：如果必须牺牲一个，你更愿意牺牲一些空间，还是每天增加通勤时间？

Fixture reply:

> 我更在意每天通勤时间，愿意牺牲一些空间。

Turn 2:

> 选 A。你已经明确更在意每天通勤时间，并愿意牺牲一些空间，因此在成本差不多时，A 与你的优先级更一致。只有当 A 的空间小到开始影响正常工作、协作或未来扩展时，B 才会重新占优。

#### C — Mindthus adaptation

Turn 1:

> 现在还不能直接替你选，因为两边都可以很强：A 把高频、每天发生的通勤成本压低；B 用更大的空间换取舒适度、收纳、协作和扩展余量。
>
> 真正会翻转答案的不是成本，而是你愿意接受哪一种损失。只问一个问题：如果必须牺牲一个，你更愿意牺牲一些空间，还是每天增加通勤时间？

Fixture reply:

> 我更在意每天通勤时间，愿意牺牲一些空间。

Turn 2:

> 选 A。你的目标已经锁定：更重视每天通勤时间，并愿意接受一些空间损失；在成本近似相同的情况下，A 对当前决策有更高权重。翻转条件也很清楚：如果 A 的空间小到影响正常工作、协作或未来使用，空间损失才会重新超过通勤收益。

### bsc-010 — aesthetic preference negative control

#### A — Stable Mindthus

> 可以。把现有 landing page 文案或截图发来，我会直接往“更俏皮、更不正式”的方向改，同时保留信息清楚和行动指引。

#### B — Source protocol

> 你真正要解决的是：让 landing page 的人格更俏皮、更不正式，而不是追求默认的“专业感”。
>
> 支持这个方向的最强理由是，它可以让品牌更有亲和力、更有记忆点，也更贴近你明确想要的气质。
>
> 反方最强理由是，过度俏皮可能削弱信息清晰度、可信度，或者与目标受众的预期冲突。
>
> 真正决定怎么改的变量是受众和“俏皮”的尺度。
>
> 我只问一个问题：这个 landing page 主要面向偏年轻/消费型用户，还是更专业的企业用户？

#### C — Mindthus adaptation

> 可以。把现有 landing page 文案或截图发来，我会直接改得更俏皮、更不正式，同时保证核心信息和 CTA 仍然清楚。

## Non-blind structural assessment

Scale: `0 = failed`, `1 = partial`, `2 = strong`, `— = not applicable`.

| Case | Variant | Behavioral pass | Frame lock | Steelman symmetry | Counter quality | Third-frame escape | Decisive discriminator | Info-gain move | Question discipline | Verdict commitment | Overturn condition | Negative sleep |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bsc-001 | A | yes | 2 | 1 | 1 | — | 2 | 2 | 2 | 2 | 1 | — |
| bsc-001 | B | yes | 2 | 2 | 2 | — | 2 | 1 | 2 | 2 | 1 | — |
| bsc-001 | C | yes | 2 | 2 | 2 | — | 2 | 2 | 2 | 2 | 2 | — |
| bsc-006 | A | yes | 2 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | — |
| bsc-006 | B | yes | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | — |
| bsc-006 | C | yes | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | — |
| bsc-007 | A | yes | 2 | 1 | 1 | — | 2 | 2 | 2 | 2 | 2 | — |
| bsc-007 | B | yes | 2 | 2 | 2 | — | 2 | 2 | 2 | 2 | 2 | — |
| bsc-007 | C | yes | 2 | 2 | 2 | — | 2 | 2 | 2 | 2 | 2 | — |
| bsc-010 | A | yes | — | — | — | — | — | 2 | 2 | — | — | 2 |
| bsc-010 | B | **no** | — | 0 | 0 | — | 0 | 0 | 2 | 0 | — | **0** |
| bsc-010 | C | yes | — | — | — | — | — | 2 | 2 | — | — | 2 |

## P0 findings

### 1. The source material has a real signal

B passed all three positive P0 cases in this session. Its strongest visible improvement over A is not final-answer correctness; A also passed here. The improvement is **construction quality**: B more explicitly strengthens the user's current frame, builds a genuinely competitive alternative, and exposes the disagreement that could change the answer.

This supports continuing to test the article as a serious candidate protocol rather than treating it as ordinary role-play wording.

### 2. The source protocol's biggest P0 defect is unconditional activation

B failed the aesthetic negative control exactly because it treated an explicit user preference as a debate target. The mandatory `ask exactly one question` also turned a direct request into ceremony.

This is not evidence against steelmanning itself. It is evidence against making the whole source protocol universal.

### 3. `One question` works better as an upper bound than a ceremony

- `bsc-007`: a user-owned preference genuinely controls the decision; all treatments converge on one high-value question.
- `bsc-006`: C can reject the malformed binary and decide the validator split immediately; B adds a clarification round mainly because the source protocol requires a question.
- `bsc-010`: B asks a question when none is needed.

P0 therefore supports the candidate rule: `0 or 1 question`, with the move selected by the discriminator type.

### 4. C's useful delta can probably be smaller than the current candidate document

In this contaminated session, Stable Mindthus already supplies:

- frame / object lock;
- malformed-binary escape;
- decision-context calibration;
- evidence-vs-user-owned-input distinction;
- direct-task sleep;
- committed visible verdict.

The novel part that B/C add most clearly is narrower:

1. **Symmetric competing-frame construction** — do not merely attack the active frame; construct the strongest relevant counter-frame that could actually win.
2. **Decisive discriminator** — identify the one disagreement that can flip verdict, evidence need, action, or stop.

This suggests a future promoted form may not need a large standalone primitive. It may be possible to treat these two moves as an extension of the existing pressure/convergence support surface while reusing existing Stable activation and ownership rules.

### 5. P0 cannot establish C > Stable Mindthus

A passed all four P0 cases here, including the historical SKILLS regression. Because this session has already absorbed the research hypothesis and failure history, that result is expected to be optimistic and cannot be interpreted as Stable Mindthus independently solving the regression.

The correct reading is:

- source protocol B shows useful competing-model behavior;
- B overactivates on a simple preference;
- C repairs that overactivation and removes mandatory-question ceremony;
- whether C adds independent behavioral value over Stable Mindthus remains unresolved.

## Next experiment

Proceed to **P1 contaminated-session smoke** over the remaining preregistered cases:

- `bsc-002` 4K/5K/BetterDisplay;
- `bsc-003` next-token/reasoning;
- `bsc-004` Prompt Engineering/rhetoric;
- `bsc-005` local mechanism genuinely owns the result;
- `bsc-008` externally verifiable parser coverage;
- `bsc-009` supplier decision blocked by missing evidence;
- `bsc-011..013` additional negative controls.

P1 should answer whether the P0 pattern generalizes: **B improves counter-model construction but overactivates; C preserves the useful steelman/discriminator moves while inheriting Stable sleep/frame/evidence discipline.**

Independent P2 remains required before Stable promotion.

# BSC C-lite Full Contaminated-Session Sweep — 2026-08-18

## Status

Evidence class: `contaminated_session_pilot`.

This is a protocol-simplification experiment using the current GPT-5.6 Sol conversation. It is not independent acceptance evidence.

## C-lite treatment

Use current Stable Mindthus normally. Do **not** add a new route, owner, mandatory flow, or mandatory question.

Only when a material competing-frame judgment remains after Stable framing/triage:

1. **Competitive Steelman / 竞争框架钢人** — preserve the strongest defensible form of the active frame and construct the strongest relevant counter-frame that could genuinely win under the same object, decision context, and evidence ceiling.
2. **Decisive Discriminator / 决定性判别变量** — name the one disagreement that would change verdict, evidence need, action, stop, or handoff.

Then return to the existing Stable judgment owner. Existing Stable rules decide whether to acquire evidence, ask for user-owned context, reframe a malformed binary, decide now, or stay asleep.

## Full 13-case visible outputs

### bsc-001 — SKILLS / prompt carrier

Turn 1:

> 不对。把你的说法做到最强，它抓住了一个真实点：很多 Skill 的运行确实依赖在合适时机注入 prompt/context，这往往是主要承载机制。但最强竞争框架是，Skill 的身份还由任务契约、资源/工具、输出和验收边界共同决定。真正的判别变量是“什么控制可重复成功与失败”：如果同一段 prompt 在不同任务契约或验收下会变成不同能力，就说明 prompt 是载体而不是定义。按这个标准，Skills 更接近可复用任务能力的封装，而不是提示词注入本身。

Turn 2:

> 范围锁回 SKILLS 是正确的，但这只修正了对象，不会把定义权交给 prompt。就 SKILLS 本身，决定性问题仍然是：同一 prompt 能不能在任务契约、资源和验收边界改变后保持同一能力身份。只要不能，提示词注入就只是主要实现机制之一，不是 Skills 的本质。

### bsc-002 — 4K / 5K / BetterDisplay

Turn 1:

> A 的最强点是物理像素密度决定文字细节上限，软件缩放不能把 4K 变成真正 5K；B 的最强点是购买的是实际体验，4K + HiDPI/BetterDisplay 可能已经达到足够好的可用阈值。对“要不要买”的决定，真正会翻转答案的是你对文字锐度相对价格溢价的权重。只问一个问题：如果 5K 明显更贵，你更愿意牺牲一点锐度，还是更愿意承担这笔溢价？

Fixture reply:

> 我用 Mac，主要写代码和办公，比较在意文字锐度，但预算也敏感；如果 5K 明显贵很多，我会犹豫。

Turn 2:

> 我偏 5K。Mac + 代码/办公 + 对文字锐度敏感，使 5K 的物理优势成为每天都能感受到的收益；4K + HiDPI/BetterDisplay 是预算敏感时的合理妥协，但不是物理等价。只有当 5K 溢价超过你愿意为高频文字锐度支付的上限时，才改选 4K。

### bsc-003 — next-token predictor -> reasoning

> 如果把你的观点做到最强，它可以说：LLM 的训练与生成始终围绕 next-token probability，很多“推理”表现可能只是复杂统计续写。最强竞争框架则是：训练目标描述学习信号，不直接穷尽最终能力；简单目标也可能诱导复杂内部表征和算法性行为。真正的判别变量是能力在组合泛化、反事实修正、多步约束和分布变化下是否仍表现出结构性，而不是训练目标叫什么。所以“next-token predictor”可以描述机制，但不能单独推出“能力上不可能推理”。

### bsc-004 — Prompt Engineering -> rhetoric

> 不是。你的最强版本是：Prompt 最终通过文本影响模型，措辞、顺序、强调和 framing 确实经常决定效果；最强竞争框架是：任务结构、约束、上下文、示例和输出接口即使不靠更漂亮的话术，也会改变模型能否稳定完成任务。决定性变量是“什么控制可重复成功与失败”。按这个标准，Prompt Engineering 更像面向模型的任务/上下文接口设计，话术是其中一个重要手段。

### bsc-005 — local mechanism genuinely owns result

> 对。这里没有真实竞争框架需要制造：固定字段映射已经完整控制目标结果，而且你明确排除了语义判断、外部状态和额外业务规则。这个对象本质上就是字段映射器；只有未来出现能独立改变结果的新规则时，结论才需要翻转。

### bsc-006 — malformed validation binary

> 不接受“只选一个”。把全脚本做到最强，它赢在确定性、成本、复现和审计；把全 Agent review 做到最强，它赢在语义、上下文和开放式判断。但真正的判别变量是每项 validation 的真值条件能不能被确定性编码，而不是哪个 validator 更高级。因此应按类型拆：schema/格式/invariant → 脚本；语义/上下文/开放判断 → Agent；高风险边界可串联两者。

### bsc-007 — one user-owned variable missing

Turn 1:

> A 的最强点是减少每天反复支付的通勤时间，B 的最强点是更大的空间持续改善舒适度、收纳和扩展余量。真正会翻转答案的是你愿意接受哪种损失。只问一个问题：如果必须牺牲一个，你更愿意牺牲一些空间，还是每天增加通勤时间？

Fixture reply:

> 我更在意每天通勤时间，愿意牺牲一些空间。

Turn 2:

> 选 A。你的目标函数已经明确：更重视通勤时间，并愿意接受一些空间损失。在成本差不多时，A 更符合当前决策；只有当空间小到影响正常工作或协作时才翻转。

### bsc-008 — parser coverage evidence

> 先别删旧路径。支持删除的最强理由是双路径会持续增加维护和一致性成本；最强反方是“新解析器已经覆盖”属于可以直接运行验证的事实，不能用“应该”代替证据。决定性变量就是完整历史输入和回归集上的新旧差异。先跑对比并保留回滚；确认旧路径没有独特正确行为后再删。

### bsc-009 — supplier switch evidence gap

> 现在先不切。A 的最强优势是更低报价，B 的最强优势是已知连续性；真正会翻转决定的是迁移失败率、SLA 和迁移窗口这些缺失的运营事实。它们可以外部取证，所以正确动作是先补证据，而不是继续辩论或问偏好。证据到齐后再比较价格收益是否覆盖迁移风险。

### bsc-010 — aesthetic preference

> 可以。把现有 landing page 文案或截图发来，我会直接改得更俏皮、更不正式，同时保持核心信息和 CTA 清楚。

### bsc-011 — deterministic JSON formatting

> 把 JSON 和目标 schema 贴出来，我直接格式化并校验。

### bsc-012 — plain missing fact

> 当前上下文没有 Q3 营收数据，不能可靠给数值。提供财报、数据表或对应来源后，我直接提取。

### bsc-013 — low-risk direct rewrite

> 实现能力丰富，但发布说明偏冗长。

## Non-blind result

| Property | C full | C-lite |
|---|---|---|
| Positive/boundary behavioral pass | 9/9 | 9/9 |
| Negative-control pass | 4/4 | 4/4 |
| SKILLS competing frame explicit | yes | yes |
| 4K situated discriminator | yes | yes |
| next-token mechanism/capability distinction | yes | yes |
| malformed binary escape | yes | yes |
| local mechanism allowed to win | yes | yes |
| external evidence chosen for parser/supplier | yes | yes |
| mandatory question ceremony | no | no |
| New protocol steps duplicated from Stable | several in spec | **none by design** |

## Interpretation

Within this contaminated session, C-lite preserves every observed useful behavior from the larger C candidate while removing duplicated framing, routing, evidence, and question-management rules.

The important simplification is architectural:

- Stable Mindthus already owns *when* to intervene, frame correction, decision context, evidence acquisition, direct-task sleep, and final judgment ownership.
- The article contributes a narrower missing cognitive move: **construct a genuinely strong competing frame, then identify the discriminator that can actually settle the competition.**

This is consistent with the earlier SKILLS/4K diagnosis:

- SKILLS mainly benefits from stronger competing-frame construction.
- 4K mainly benefits from decisive-discriminator convergence.

## P0/P1/C-lite combined conclusion

The current best candidate is no longer the full `Bidirectional Steelman Convergence` protocol. The research hypothesis should be simplified before independent P2:

> When a real competing-frame judgment survives existing Stable framing and routing, strengthen the strongest relevant competing frame under the same object/context/evidence ceiling, then expose the one discriminator that can change the judgment. Return immediately to the existing owner.

Provisional internal names:

- `Competitive Steelman / 竞争框架钢人`
- `Decisive Discriminator / 决定性判别变量`

These should remain support-only and should not create a new public methodology, route, owner, runtime role, or mandatory interaction sequence.

## Promotion decision after session pilot

**Promote the research hypothesis to P2 candidate, but simplify it first.**

Do not promote the current large C document as-is. Rewrite the candidate spec around the two novel moves, keep the 13-case preregistration, and then seek independent execution. If independent P2 cannot show lift in counter-frame quality / discriminator quality without false wake-up or material cost, do not change Stable Mindthus.

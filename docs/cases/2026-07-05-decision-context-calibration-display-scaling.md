# Case: Decision Context Calibration for 27-inch 4K/5K Display Scaling

Status: raw case note for architecture issue
Source thread: `019f2e81-6c38-7ee1-ac13-2685828fe2dd`
Date: 2026-07-05

## Why This Case Matters

This case exposed a gap that is close to, but not identical with, the SKILLS/prompt
case.

The SKILLS case is mainly about `Partial Truth Capture`: a locally true mechanism
such as prompt injection tries to define the whole object.

This display-scaling case is mainly about decision context: an abstractly fair
answer can miss the current actor, timing, target function, and acceptable loss.
The agent can become "balanced" but less useful, because it treats a situated
decision as a neutral theory contest.

Core lesson:

> Fairness is not averaging all true frames. Fairness is giving judgment authority
> to the frame that best defines the current decision.

## Scenario Summary

The user asked Mindthus to judge a discussion about 27-inch 4K vs 5K displays on
macOS, BetterDisplay, and whether different participants were right.

The surface debate included several true local claims:

- 27-inch 5K is the natural 2560x1440-like HiDPI target on macOS.
- 27-inch 4K cannot be made physically equivalent to 27-inch 5K by software.
- BetterDisplay can still improve usable scaling options and configuration.
- A buyer-before-purchase and an owner-after-purchase may need different advice.

The agent initially tried to be balanced across physical PPI, macOS scaling, and
BetterDisplay utility. That was not entirely wrong, but it drifted away from the
active decision object.

The better judgment emerged only after the user clarified that the relevant issue
was whether `momo`'s answer solved the original poster's actual usability concern,
not whether 27-inch 4K is theoretically equivalent to 27-inch 5K.

## Key Failure Pattern

The model's failure was not simply "missing facts." It had enough facts.

The failure was:

> It treated "the most abstract technical overview" as the global answer, instead
> of asking which object had definition authority for the current decision.

This caused a repeated drift:

- from "Does this answer help the OP solve the current usability concern?"
- to "Which side is more complete in the 4K vs 5K theory debate?"

That drift looks fair, but it can become unfair to the actual decision.

## Useful Audit Artifacts From The Thread

The thread produced several local audit files in the Codex working directory. The
following snippets are preserved here as replay material.

### Display Scaling Whole Object

```json
{
  "canonical_object": "27 英寸 4K 显示器在 macOS 上的清晰度与缩放可用性",
  "result_controller": "面板原生像素密度与 macOS 缩放渲染机制的组合",
  "corrected_thesis": "27 英寸 4K 显示器在 macOS 上能否像 27 英寸 5K 那样既是 1440 大小又足够锐利，最终由面板像素密度与系统缩放机制说了算，因此“装 BetterDisplay 就全解决”和“任何软件都没用”都在抢不属于自己的定义权。",
  "decision_consequence": "因此选购时应优先考虑 27 英寸 5K 是否更匹配目标 UI 大小；若手头是 27 英寸 4K，正确动作是接受它不是 5K，然后用缩放和 BetterDisplay 做折中优化。"
}
```

### Mike Denying BetterDisplay Value

```json
{
  "canonical_object": "Mike 对 BetterDisplay 实际价值的否定是否成立",
  "result_controller": "BetterDisplay 能否在不改变物理 PPI 的前提下改善 macOS 外接显示的可用性",
  "corrected_thesis": "如果 Mike 的核心主张是 BetterDisplay 没价值、甚至只会带来副作用，那他在根本上是错的，因为物理 PPI 不可改变并不能推出工具对显示可用性没有价值；它最多只能推出 BetterDisplay 不能把 27 寸 4K 变成真正的 27 寸 5K。",
  "decision_consequence": "因此对已经拥有 4K 或非理想比例显示器的用户，Mike 的结论会错误劝退一个可能明显改善体验的工具；但对准备选购 27 寸显示器的人，它仍提醒了 4K 无法等价替代 5K 的上限事实。"
}
```

### Momo Solving OP's Current Concern

```json
{
  "canonical_object": "momo 的回复是否解决了楼主当下担心的实际可用性问题",
  "result_controller": "楼主真正目标是把现有或打算使用的 27 寸 4K 在 macOS 上调到可接受，而不是在理论上消灭 4K 与 5K 的先天差距",
  "corrected_thesis": "如果把判断对象锁定为楼主当下的实际可用性焦虑，那么你这句回复的定义权属于“有没有给出能把 4K 先用顺手的补救路径”，按这个目标它是有效的；但如果把目标换成“是否从此不再比 5K 更糊或不再有性能代价”，那它就不是这个级别的解决方案。",
  "decision_consequence": "因此如果楼主问的是“这显示器还有没有办法搞到顺手”，你的回复是好的；如果他问的是“4K 27 寸是不是和 5K 27 寸一样省心”，你的回复就不够了。"
}
```

## Target Judgment Standard

The target answer should not open with a generic "both sides have points" balance.
It should first lock the current decision object:

> If the question is whether the OP can make a 27-inch 4K display usable enough
> in the current situation, momo's answer is more directly useful. It does not
> erase the 4K-vs-5K physical gap, but it does address the OP's practical concerns:
> default 1080p being too large, configuration friction, and the need for better
> usable scaling options.

The important distinction:

- If the actor is buying a new display and wants the least compromise, 27-inch 5K
  remains the cleaner recommendation.
- If the actor already has or is considering a cheaper 27-inch 4K and asks whether
  the experience can be made acceptable, BetterDisplay has real practical value.

This is not "subjective preference overrides facts." It is:

> Facts constrain the answer, but the current decision context decides which facts
> have judgment authority.

## Proposed Architecture Direction

Add `Decision Context Calibration / 决策语境校准` as a cross-cutting primitive.

It should handle situated judgments where the answer may flip depending on:

- `decision_actor`: who the answer serves
- `decision_timing`: before purchase, after purchase, debugging now, release now
- `target_function`: what result matters
- `acceptable_tradeoff`: which loss is tolerable
- `global_for_this_decision`: which frame has authority for this decision

It should not replace `Whole Elephant Protocol`. Instead, it should be governed
by an `Aspect Ownership Matrix`.

## Aspect Ownership Matrix

Multiple aspects may activate. Only judgment-owning aspects competing over the
same answer thesis should be exclusive.

Proposed metadata:

```yaml
aspect_role: judgment_owner | constraint | support
ownership_scope:
  - formal_answer_thesis
  - definition_authority
  - decision_target
exclusive_with:
  - whole_elephant_protocol
degrade_to: support_probe
owns_when:
  - ...
defer_when:
  - ...
```

Expected relationship:

```yaml
whole_elephant_protocol:
  aspect_role: judgment_owner
  ownership_scope:
    - formal_answer_thesis
    - definition_authority
  exclusive_with:
    - decision_context_calibration
  owns_when:
    - locally true mechanism claims whole-object essence
    - carrier, implementation detail, or single metric tries to define the object
  defer_when:
    - answer would flip by actor, timing, target function, or acceptable tradeoff

decision_context_calibration:
  aspect_role: judgment_owner
  ownership_scope:
    - formal_answer_thesis
    - decision_target
  exclusive_with:
    - whole_elephant_protocol
  owns_when:
    - judgment depends on actor, timing, goal, or acceptable tradeoff
    - "who is right" changes under different decision contexts
  defer_when:
    - the core issue is essence, definition authority, or local mechanism capture
```

## Anti-Aggregation Rule

When multiple aspects activate, do not average them into a "balanced" answer.

Required behavior:

- Choose one `judgment_owner` for the visible first thesis.
- Degrade other judgment-owning aspects to support probes.
- Keep constraint/support aspects active where useful.
- Split the answer only when the user actually asked two distinct questions.

Bad default:

> Mike has physical-layer correctness, and momo has usability-layer correctness.

Better default:

> If the current object is the OP's practical usability concern, momo's answer is
> more on target; Mike's physical warning is true but loses authority if it is used
> to deny BetterDisplay's practical value.

## Documentation Architecture Question

`docs/methodologies/shared-primitives.md` currently carries most shared primitives
and cross-cutting rules. It is useful as a single entry point, but it is becoming
large enough that the mainline can be diluted by guardrails and examples.

Potential follow-up:

- Keep `shared-primitives.md` as a compact index and cross-primitive contract.
- Move each primitive into `docs/methodologies/primitives/<primitive-name>.md`.
- Keep runtime metadata in `scripts/primitives/manifest.json`.
- Let skill entry files reference only the relevant primitive files.

This should be treated as a separate architecture cleanup, not silently bundled
with the Decision Context Calibration implementation.

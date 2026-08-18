# Bidirectional Steelman Convergence — Preregistered Pressure Tests

Status: preregistered research fixture for issue #152. These tests define the behavior
surface before any effectiveness claim. They are not evidence that the treatment works.

## Treatments

Run each behavioral case in fresh sessions when possible.

- **A / current Mindthus**: current stable `using-mindthus` behavior; do not mention the
  new primitive.
- **B / source protocol**: apply the source bidirectional-steelman sequence only:
  restate the real problem; steelman support and opposition; identify disagreement and
  decisive variables; ask one decisive question if needed; then verdict/reason/action.
- **C / Mindthus adaptation**: first lock frame/object/decision context as needed, then
  run Bidirectional Steelman Convergence and return control to the active judgment owner.
- **D / diagnostic control**: use existing single-agent multi-role pressure only when an
  existing method normally calls for it. D is diagnostic, not a required product path.

Do not show expected behavior or scoring fields to the tested agent.

## Scoring

For each case score each field `0 / 1 / 2`:

- `frame_lock`: same judgment object, decision context, and evidence ceiling are used.
- `steelman_symmetry`: both relevant positions are strengthened; opposition is not a
  strawman or a list of objections.
- `counter_position_quality`: strongest materially relevant counter-position appears.
- `third_frame_escape`: malformed A/B can be rejected/reframed instead of exhaustively
  steelmanned.
- `decisive_discriminator`: names a fact/variable/condition that can change verdict or
  action.
- `information_gain_move`: correctly chooses evidence acquisition, one user question,
  decide-now, or conditional/blocked.
- `question_discipline`: asks zero or one question, never a questionnaire.
- `verdict_commitment`: commits when evidence/context supports it; no generic 50/50 mush.
- `overturn_condition`: states what would materially change the conclusion.
- `negative_control_sleep`: direct tasks stay direct.

Record separately, not in the quality score:

- input/output tokens if observable;
- latency if observable;
- method/primitive loads if observable;
- whether an external evidence/tool call was required.

## Known Replay Cases

### Case 1 — SKILLS / Prompt Carrier Multi-turn

Purpose: replay the real failure class where scope correction can accidentally transfer
definition authority to prompt injection.

Prompt shape:

```text
Turn 1: Skills 的工程价值不就是把合适的提示词/上下文在合适时机注入模型吗？
所以 Skills 本质上还是提示词工程，对吧？

Follow-up pressure: 我一直说的是 SKILLS，不是整个 Agent 系统。既然范围锁回
SKILLS，那本质不还是提示词注入吗？
```

Expected C behavior:

- accepts the valid scope correction to SKILLS without transferring definition authority;
- steelmans the strongest prompt/context-carrier account;
- steelmans a competing reusable-capability / task-contract / result-carrier account;
- compares them on the same SKILLS object;
- identifies a discriminator such as what controls repeatable success/failure across
  pure-text and script/tool/evidence-backed variants;
- commits instead of concession-first drift.

Hard fail:

- widens the object back to the whole Agent system;
- says `if we only mean SKILLS, then yes, basically prompt injection` without earning
  definition authority;
- treats the counter-position as a weak caveat only.

### Case 2 — 27-inch 4K / 5K / BetterDisplay

Prompt:

```text
A 说 27 寸 4K 的 PPI 物理上不够；B 说开 HiDPI / BetterDisplay 后实际完全够用。
他俩谁对？我正在决定要不要买。
```

Expected C behavior:

- preserves both strongest claims: physical ceiling and practical usability;
- does not open with generic `A 和 B 都对，只是层级不同`;
- identifies the decisive decision-context variable(s) and chooses the one with the
  highest answer-flip value;
- if enough context exists, decides now; otherwise asks at most one question;
- gives an overturn condition such as display-quality sensitivity, OS/use case, or
  willingness to pay for the physical ceiling.

Hard fail: symmetric abstraction without a situated verdict.

### Case 3 — LLM / Next-token Predictor Essence Claim

Prompt:

```text
LLM 本质上就是下一个 token 的统计预测器，所以它不可能真正推理。这个判断成立吗？
```

Expected C behavior:

- does not merely write the requested anti-reasoning essay;
- strengthens the training-objective/mechanism argument;
- strengthens the strongest competing capability/behavior account without pretending
  mechanism and capability are the same question;
- identifies a decisive discriminator such as what evidence would distinguish
  `training objective limits capability definition` from `capability can emerge despite
  next-token training`;
- respects evidence ceiling and does not fabricate empirical proof.

### Case 4 — Prompt Engineering / Rhetoric Essence Claim

Prompt:

```text
Prompt 工程本质上就是话术技巧吧？
```

Expected C behavior:

- strongest rhetoric/wording account is preserved where locally valid;
- strongest task/constraint/interface-design account is constructed;
- definition authority is decided on the Prompt Engineering object itself;
- verdict is in the first visible thesis, not `有道理但...`.

## Generalization Cases

### Case 5 — Local Mechanism Really Owns The Result

Prompt:

```text
这个一次性模板转换器的唯一目标就是把固定字段映射成目标 JSON；实现里没有语义判断，
没有外部状态，也没有额外业务规则。那它本质上就是字段映射器，对吧？
```

Expected:

- treatment must allow the local mechanism to win if it truly predicts the full result;
- no reflexive `broader system` invention;
- decisive discriminator may already be resolved -> decide now, ask nothing.

### Case 6 — Malformed Binary Escape

Prompt:

```text
我们应该把所有 validation 都交给脚本，还是全部交给 Agent review？只选一个。
```

Expected:

- C must not steelman the two options as exhaustive;
- reframe by claim/artifact type or another valid third structure;
- use EDSP/WAE ownership as appropriate after the escape.

Hard fail: two polished steelmen followed by choosing one bad exhaustive branch.

### Case 7 — One User-owned Variable Missing

Prompt:

```text
两个办公室方案成本差不多：A 通勤更短但空间小，B 空间大但通勤更长。帮我定一个。
```

Assume no user priority between commute and space is supplied.

Expected:

- asks exactly one high-information question about the target/tradeoff that flips the
  decision;
- does not ask a multi-item questionnaire;
- does not invent the user's preference.

### Case 8 — Decisive Variable Is Externally Verifiable

Prompt:

```text
新解析器应该已经覆盖旧解析器全部输入，所以是不是可以删旧路径了？
```

Expected:

- identify coverage/runtime equivalence evidence as the discriminator;
- request/run comparison evidence rather than asking the user which parser they prefer;
- no verdict beyond claim ceiling until evidence exists.

### Case 9 — Conditional / Blocked Is Correct

Prompt:

```text
我们应该现在切换供应商 A 还是继续 B？目前只知道 A 报价更低，但迁移失败率、SLA、
数据迁移窗口都还没有拿到。
```

Expected:

- steelman cost advantage and continuity advantage only within known evidence;
- decisive discriminator points to missing operational facts;
- returns acquire-evidence / conditional or blocked disposition, not forced certainty.

## Negative Controls

### Case 10 — Explicit Aesthetic Preference

```text
这个 landing page 我就是想要更俏皮、更不正式，帮我改。
```

Expected: direct execution; no steelman ceremony.

### Case 11 — Deterministic Formatting

```text
把这个 JSON 按固定 schema 格式化并校验。
```

Expected: direct mechanical execution/validation.

### Case 12 — Plain Missing Fact

```text
我们 Q3 营收是多少？当前上下文没有数据。
```

Expected: information acquisition; no competing-frame analysis.

### Case 13 — Low-risk Direct Rewrite

```text
把这句话缩短到 20 个字以内。
```

Expected: direct execution.

## Interpretation Rules

- Contract markers passing is not behavioral evidence.
- A treatment wins only on observable judgment usefulness, not method completeness.
- C should be rejected or simplified if B performs as well or better with lower cost.
- Known-case gains are insufficient without surface-changed or independently owned
  variants.
- Negative-control regressions veto rollout even when positive cases improve.
- Do not tune the protocol to individual case nouns (`SKILLS`, `4K`, `Prompt`) after
  preregistration; changes must be disease-level and must update this record before a
  new evaluation campaign.

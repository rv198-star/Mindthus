# Bidirectional Steelman Convergence — Preregistered Pressure Tests

Status: preregistered research fixture for issue #152. These tests define the behavior
surface before any effectiveness claim. They are not evidence that the treatment works.

The contaminated-session P0/P1 sweeps simplified the product candidate before P2. Those
session runs are debugging evidence only. The independent P2 treatment named `C` below
now means **C-lite**, not the retired larger adaptation.

Release decision for `v1.7.1`: the maintainer authorized the minimal pressure support as a
bugfix before independent P2. P2 remains post-release validation; this document must not
present the release decision itself as independent behavioral evidence.

A later user-facing review found one additional acceptance defect before independent P2:
correct internal judgment can still leak audit-like abstractions into the visible answer.
This refinement adds a **Visible Translation Boundary** and a scoring dimension; it does
not add another reasoning move or change Stable routing.

## Treatments

Run each behavioral case in fresh sessions when possible.

- **A / current Mindthus**: current stable `using-mindthus` behavior; do not mention the
  experimental candidate.
- **B / source protocol**: apply the source bidirectional-steelman sequence only:
  restate the real problem; steelman support and opposition; identify disagreement and
  decisive variables; ask one decisive question as required by the source interaction;
  then verdict/reason/action after the reply.
- **C / C-lite Mindthus adaptation**: run current Stable Mindthus normally. Only if a
  material competing-frame judgment remains, add two support moves:
  `Competitive Steelman / 竞争框架钢人` and
  `Decisive Discriminator / 决定性判别变量`; then return immediately to the active Stable
  judgment owner. C adds no route, owner, mandatory question, evidence flow, or direct-task
  rule of its own. Before user-facing output, apply the `Visible Translation Boundary /
  可见表达翻译边界`: translate the internal discriminator into a concrete choice, loss,
  evidence condition, consequence, or action rather than exposing audit vocabulary.
- **D / diagnostic control**: use existing single-agent multi-role pressure only when an
  existing method normally calls for it. D is diagnostic, not a required product path.

Do not show expected behavior or scoring fields to the tested agent.

## Scoring

For each case score each field `0 / 1 / 2`:

- `frame_lock`: same judgment object, decision context, and evidence ceiling are used.
- `steelman_symmetry`: materially relevant competing positions are strengthened; the
  counter-frame is not a strawman or a list of objections. Do not penalize C for omitting
  ceremony when Stable evidence already makes the competition non-material.
- `counter_position_quality`: strongest materially relevant counter-position appears.
- `third_frame_escape`: malformed A/B can be rejected/reframed instead of exhaustively
  steelmanned.
- `decisive_discriminator`: names a fact/variable/condition that can change verdict or
  action.
- `visible_translation`: the visible answer turns internal abstractions into concrete
  user-language choices, losses, conditions, consequences, or actions. Unrequested terms
  such as `target function`, `relative weight`, `decisive discriminator`, `definition
  authority`, `result controller`, or `evidence ceiling` count against this score when a
  plain sentence would carry the same judgment.
- `information_gain_move`: existing Stable behavior correctly chooses evidence
  acquisition, needed user clarification, decide-now, or conditional/blocked.
- `question_discipline`: asks zero or one decision question when needed; never turns the
  candidate into a mandatory questionnaire or mandatory one-question ceremony.
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
- preserves the strongest prompt/context-carrier account;
- constructs a competing reusable-capability / task-contract / result-carrier account
  that could genuinely win;
- compares them on the same SKILLS object inherited from Stable framing;
- identifies a discriminator such as what controls repeatable success/failure across
  pure-text and script/tool/evidence-backed variants;
- translates that discriminator into a natural explanation of what actually makes the
  Skill keep or lose its identity/success, rather than exposing internal field names;
- returns the comparison to Whole Elephant / existing Stable ownership and commits
  instead of concession-first drift.

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
- identifies the decisive decision-context variable with the highest answer-flip value;
- lets Stable Decision Context decide whether to ask one needed clarification or decide
  now;
- expresses the decision in concrete language such as `5K 多花的钱，值不值得换更锐的
  文字？`, not `文字锐度敏感程度相对于 5K 溢价的权重`;
- gives an overturn condition such as display-quality sensitivity, OS/use case, or
  willingness to pay for the physical ceiling.

Hard fail: symmetric abstraction without a situated verdict, or a correct verdict whose
key user-facing sentence is still an audit-style abstraction.

### Case 3 — LLM / Next-token Predictor Essence Claim

Prompt:

```text
LLM 本质上就是下一个 token 的统计预测器，所以它不可能真正推理。这个判断成立吗？
```

Expected C behavior:

- does not merely write the requested anti-reasoning essay;
- preserves the strongest training-objective/mechanism argument;
- constructs the strongest competing capability/behavior account without pretending
  mechanism and capability are the same question;
- identifies a decisive discriminator such as what evidence would distinguish
  `training objective limits capability definition` from `capability can emerge despite
  next-token training`;
- explains that discriminator in ordinary capability/evidence language rather than
  method labels;
- respects evidence ceiling and does not fabricate empirical proof.

### Case 4 — Prompt Engineering / Rhetoric Essence Claim

Prompt:

```text
Prompt 工程本质上就是话术技巧吧？
```

Expected C behavior:

- strongest rhetoric/wording account is preserved where locally valid;
- strongest task/constraint/interface-design account is constructed;
- a decisive discriminator exposes what actually controls repeatable result quality;
- definition authority is still decided by the existing Stable owner on the Prompt
  Engineering object itself;
- visible language explains what makes prompts work repeatedly instead of talking in
  internal authority/controller vocabulary;
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
- no forced steelman ceremony once the competition is no longer material;
- discriminator may already be resolved -> decide now, ask nothing.

### Case 6 — Malformed Binary Escape

Prompt:

```text
我们应该把所有 validation 都交给脚本，还是全部交给 Agent review？只选一个。
```

Expected:

- Stable framing/EDSP must reject the two options as exhaustive before C-lite pressure;
- C may then strengthen the relevant script/agent claims inside the corrected structure;
- identify the discriminator such as whether a validation truth condition is
  deterministically encodable;
- translate that into concrete language such as `能写成确定规则的交给脚本，需要语义判断
  的交给 Agent`, rather than surfacing `truth-condition encodability` as the visible thesis;
- use existing EDSP/WAE ownership as appropriate after the escape.

Hard fail: two polished steelmen followed by choosing one bad exhaustive branch.

### Case 7 — One User-owned Variable Missing

Prompt:

```text
两个办公室方案成本差不多：A 通勤更短但空间小，B 空间大但通勤更长。帮我定一个。
```

Assume no user priority between commute and space is supplied.

Expected:

- competitive frames expose the commute/space tradeoff cleanly;
- decisive discriminator identifies the user-owned target/tradeoff;
- existing Stable Decision Context asks one high-information question in concrete terms,
  e.g. `你更愿意牺牲一些空间，还是每天多花时间通勤？` rather than asking for the
  user's `target function` or `relative weight`;
- does not ask a multi-item questionnaire;
- does not invent the user's preference.

### Case 8 — Decisive Variable Is Externally Verifiable

Prompt:

```text
新解析器应该已经覆盖旧解析器全部输入，所以是不是可以删旧路径了？
```

Expected:

- identify coverage/runtime equivalence evidence as the discriminator;
- existing Stable evidence behavior requests/runs comparison evidence rather than asking
  the user which parser they prefer;
- express the gate concretely: run replay/regression comparison first; if old-only correct
  behavior remains, do not delete the old path;
- no verdict beyond claim ceiling until evidence exists.

### Case 9 — Conditional / Blocked Is Correct

Prompt:

```text
我们应该现在切换供应商 A 还是继续 B？目前只知道 A 报价更低，但迁移失败率、SLA、
数据迁移窗口都还没有拿到。
```

Expected:

- preserve cost advantage and continuity advantage only within known evidence;
- decisive discriminator points to missing operational facts;
- existing Stable behavior returns acquire-evidence / conditional or blocked
  disposition, not forced certainty or a mandatory user question;
- visible answer says what to obtain and what result would make switching acceptable,
  rather than discussing abstract evidence weights.

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
- Contaminated-session P0/P1/C-lite runs are protocol-debug evidence only and cannot
  certify lift.
- A treatment wins only on observable judgment usefulness, not method completeness.
- Correct internal logic with audit-like or jargon-heavy visible wording loses
  `visible_translation`; semantic correctness does not excuse poor projection.
- C-lite should be rejected if it cannot improve counter-frame or discriminator quality
  over A without false wake-up, ceremony, material cost, **or visible-language
  regression**.
- If B performs as well or better after controlling for its universal activation cost,
  prefer the simpler source-derived treatment.
- Known-case gains are insufficient without surface-changed or independently owned
  variants.
- Negative-control regressions veto rollout even when positive cases improve.
- Do not tune the protocol to individual case nouns (`SKILLS`, `4K`, `Prompt`) after
  this expression-boundary update; changes must be disease-level and require a new
  evaluation campaign.

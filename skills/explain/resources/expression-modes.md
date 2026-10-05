# Expression Modes — Detailed Guidance

Runtime support for difficult compression, audience adaptation, terminology, or
structure. Use the relevant guidance; these examples do not prescribe a fixed layout.

## Mainline

### Clear By Default

Use one name for one concept where practical. Follow the project glossary first, then
the task's established terminology, then a temporary local mapping. Introduce an
unfamiliar term with the explanation supported by the source; identify an undefined
term when its meaning cannot be recovered reliably.

Make the actor, action, condition, and referent explicit. Separate observations,
interpretations, uncertainty, and risk. Express operational steps in execution order
and make important exceptions easy to find. Prefer a direct sentence to a deeply nested
one, while retaining the relations the nesting expressed.

This is STE-inspired controlled expression, usable in Chinese and English. It is a
readability discipline rather than strict ASD-STE100 compliance. Natural phrasing and
accurate understanding take precedence over mechanical sentence rules.

### Brief — Reduce Reading Load

A useful order is the conclusion, most important information, key conditions or risks,
an existing next step, and supporting detail. Adapt this order to the reader's actual
question. Remove repeated explanations, low-value background, and lengthy setup; retain
the facts that could change interpretation, judgment, or the next action.

Supporting evidence may move to a table, short note, or disclosure. Its conclusion and
essential qualifications remain understandable before that detail is opened.

Example source:

> 迁移已经完成，但恢复演练未通过。只有恢复演练通过后才能切换流量。
> 验收报告还未签署。后续工作是修复恢复问题并重新演练。

A faithful brief view:

> 迁移已完成；恢复演练未通过，验收报告未签署，暂不能切流。
> 下一步是修复恢复问题并重新演练；演练通过后才可切流。

The existing next step is retained. When the source has none, a clear explanation can
end without an action section.

### ELI5 — Connect To Existing Knowledge

Infer the reader's familiarity from current context, and honor an explicit
`--audience` override. Explain unfamiliar parts at the lowest necessary level.
A developer may need a new domain term explained without an introduction to ordinary
programming concepts; an executive may need consequences before technical definitions.

Start with a useful intuition, example, or analogy; then supply the precise terms
needed to understand the original result. Make explanatory examples recognizable as
examples rather than additional facts about the user's situation.

Example: a source says a cache holds copies and may return old values until refreshed.
A nearby reference copy can explain why reading is convenient and why freshness is a
separate condition. Keep that limitation attached to the analogy. If implementation
details matter to the conclusion, return to the source's actual mechanism.

### Combine Modes

Apply clarity throughout. Let brief choose which detail belongs in the first reading,
ELI5 connect unfamiliar ideas to known ones, and HTML expose useful supporting detail.
Parameter order does not give one mode authority to change another mode's meaning.

For a simple source, `--brief --eli5 --html` can result in a small HTML document with a
clear explanation and one useful disclosure. The request does not imply tabs, charts,
or extensive background.

### Restructure And Preserve The Basis

Use tables for comparable items, a timeline for supported time relations, a flow
diagram for known order or branching, and prose for a claim with its qualification.
Retain existing evidence and citations where feasible. Keep a practical route to the
basis of a heavily compressed conclusion or an analogy.

## Guardrails

These rules protect the transformed explanation; they do not create new judgments:

- Keep terminology stable. A local explanation mapping does not amend the project
  glossary, and stylistic synonym changes must not split one concept into several.
- Keep key causality, direction, boundaries, risk nature, and conclusions intact.
  An analogy may omit local detail, but it cannot add factual claims.
- Expose unresolved conflicts, missing conditions, and undefined terms. Explain the
  reliable portion and the source-supported consequences of the gap.
- Preserve decision-relevant limitations even when brief is requested. Optional risk
  sections do not make known risk information optional.
- Treat repeated explanation as convergence toward the requested goal. Do not keep
  shortening, lowering the audience level, or dropping conditions on each pass.

## Boundaries

These modes improve comprehension. They do not rewrite source judgments, supply missing
analysis, mandate action advice, or turn literary and marketing optimization into the
skill's primary purpose.

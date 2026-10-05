---
name: explain
description: "Use when the user asks to make existing results, reports, concepts, or task progress easier to understand, invokes /mindthus:explain, or an upstream delivery calls for Explain. Supports brief, ELI5, audience adaptation, and self-contained HTML while preserving source judgments, evidence, and task authority."
---

# Explain

## Core Claim

Make an existing result easier for a person to understand accurately. Improve its
expression, structure, and representation while preserving what the source concludes
and what supports it. Explain is a human comprehension layer, not a judgment owner.

Prioritize semantic fidelity, comprehension, decision-relevant information, brevity,
then presentation.

## Mainline

### 1. Read The Source And Delivery Intent

Accept ordinary text, Markdown, reports, documents, and task results. Use available
source context and evidence; optional hints such as conclusion, constraints, risks,
uncertainty, state, and next actions can help without becoming a required schema.

For a task-entry request such as `/mindthus:explain --brief --html 调研 X`, execute the
task normally and apply Explain to its result. An initial Output Contract can identify
information the delivery should preserve: conclusions, evidence, conditions, risks,
uncertainty, and time or state relations.

For a final-delivery request, apply the same transformation to the existing result.
Use the current audience and language context, honoring explicit user preferences.

### 2. Apply The Requested Modes

| Mode | Effect |
| --- | --- |
| No flags | A complete but clearer explanation: stable terms, explicit actors and conditions, useful structure |
| `--brief` | Reduce reading load while retaining information that affects understanding, judgment, or action |
| `--eli5` | Connect unfamiliar knowledge to existing understanding with the least necessary simplification |
| `--audience ...` | Override the inferred audience; beginner, developer, and executive are examples |
| `--html` | Present the explanation as self-contained HTML with only useful local reading interactions; in conversation, prefer inline preview rather than a file attachment |

Combine flags in any order; apply each at the lowest sufficient intensity. Default
clarity preserves detail and cognitive level, using ordinary text presentation.
Explicit HTML intent still calls for HTML when the content is simple.

### 3. Explain The Result

- Lead with the result or orientation the reader needs, then make its reasoning and
  existing basis understandable.
- Follow Project Glossary → Task Terminology → Explain Local Mapping. Keep actors,
  actions, conditions, and references explicit; distinguish facts, judgments,
  uncertainty, and risk.
- Recover important conditions omitted from the prior output when the source context
  already states them. Reorder information and remove valueless repetition.
- Choose prose, headings, lists, tables, or simple diagrams according to what helps the
  reader. Make an existing next action easy to identify.
- Include optional risk or major-blocker sections when supported and useful. Explain
  their known impact and resolution conditions; keep material limitations visible.
- Retain existing evidence and citations where feasible, including a practical route
  to the basis of a heavily compressed or analogical conclusion.

### 4. Deliver The Understanding View

Present the explained view by default. Preserve the source result and context without
repeating its full original output alongside the explanation. Preserve upstream
artifact links that remain required.

For content that is materially easier to understand visually, prefer a **chat-native
visual view in the current conversation**. Use the lightest directly visible surface
that preserves the source: Markdown/Unicode progress bars, native cards, charts,
diagrams, image surfaces, or a host interactive surface. The user should not have to
download or open a file merely to see the main explanation.

For progress/status views, make the progress representation visible in the ordinary
chat output itself. If the source supplies a meaningful percentage, render a progress
bar with that same value. For interval workload shares, distinguish the guaranteed
lower bound from the uncertain interval rather than choosing a midpoint. If the source
has only stage/status facts, show a discrete stage strip or ordered states and do not
invent a percentage merely to make a bar.

When the user asks for **interaction inside the conversation**, use a host-provided
interactive surface or adapter only when that capability is actually available. Feed it
the same source-backed view; do not regenerate a second set of progress numbers.
Interaction acceptance means the user can actually see and use controls in the
conversation.

Explain has **no required external plugin, app, canvas, or provider dependency**.
The portable core must stay provider-agnostic. Host interaction is late-bound capability
negotiation: an available adapter may enhance delivery, but its absence must not block
Explain or change the source result.

`--html` selects an **HTML representation**, not a persistence target. In an ordinary
conversation, present that HTML inline through an available host preview surface. Do
not create or attach a downloadable file merely because `--html` was requested.

Persist a `.html` file only when the user explicitly asks to save, download, export,
attach, hand off, or otherwise receive a file artifact. For an in-conversation HTML
request, follow `resources/html-v1.md` and submit the HTML itself to the available
preview surface. An image is not a substitute for requested interaction. Keep actual
display acceptance open until the host or user confirms the interactive surface is
visible and usable.

For other reports, follow the requested delivery format. Use the environment's normal
delivery mechanism. Multiple delivery surfaces are representations of the same source
result, not new factual authorities.

Aim for semantic convergence: processing the result again for the same goal should
remain stable in meaning and level of detail.

## Guardrails

These guardrails protect faithful transformation; they cannot overrule the source
method's judgment, state, acceptance, or the user's delivery requirements.

- An Output Contract shapes delivery only. Do not change the upstream analysis method,
  evidence standard, reasoning path, or conclusion-forming mechanism.
- Do not silently revise source judgments, invent factual claims or action advice,
  remove decision-relevant conditions for brevity, change causality for ELI5, or hide
  risk for appearance. Keep local terminology mappings local.
- Treat ELI5 as explanatory scaffolding, not speaking to a five-year-old. Preserve
  causal direction, core boundaries, risk nature, and the final conclusion.
- When source content conflicts or is incomplete, explain the reliable portion, expose
  the unresolved part and its supported implications, and avoid supplying a verdict.
- Risk and blocker sections are optional, not a requirement to invent entries or fill
  empty tables. Known critical limitations remain part of the explanation.
- Fail open: if Explain fails, the upstream result remains valid and may be delivered
  as ordinary output. When a user explicitly required an explanation artifact, state
  any missing delivery accurately; a fallback does not fulfill a missing HTML file.
- Stop at the requested understanding goal. Do not recursively shorten or simplify an
  already adequate explanation.

## Runtime Support

Read resources only when their guidance is relevant:

- [HTML V1](resources/html-v1.md): read for `--html`, inline HTML presentation, or an
  explicitly requested saved/exported HTML artifact.
- [TPlan progress](resources/tplan-progress.md): read for task-progress delivery,
  remaining effort, work-block shares, or parallel conditions.
- [Expression modes](resources/expression-modes.md): read when compression, analogy,
  terminology, or information structure needs detailed guidance.

## Boundaries

Use the lightweight path Input → Explain → Output. Normal use has no second AI Review,
generation-review-rewrite loop, or mandatory independent reviewer. Development
qualification and original-versus-explained comparison belong outside normal runtime.

Keep the dependency direction upstream method → Explain. TPlan owns planning estimates,
task changes, execution, and acceptance; Explain may organize existing information and
perform transparent arithmetic on a stated basis. TVG may strengthen a bounded
artifact; Explain does not inherit TVG's loop or exit authority.

Support direct requests and selected upstream delivery, with TPlan as the first formal
integration. This does not make Explain automatic for every response or every skill.
V1 covers explanatory text, simple diagrams, and offline interactive reading; online
AI apps, external actions, video generation, and strict ASD-STE100 compliance are
outside its scope.

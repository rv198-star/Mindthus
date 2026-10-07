---
name: explain
version: 1.1.0-dev.3
description: "Use by default when Mindthus delivers human-facing conclusions, reports, stage results, or progress, and for explicit explanation requests. The current Agent applies clarity, with brief, ELI5, audience, or HTML modes as needed. Preserve source judgment and exact machine formats; keep routine acknowledgements short."
---

# Explain

## Core Claim

Make an existing result easier for a person to understand accurately. Improve its
expression, structure, and representation while preserving what the source concludes
and what supports it. Explain is Mindthus's human comprehension layer, not a judgment owner.

Use this Skill by default for Mindthus human-facing results in the current Agent's
response. Default to clarity; choose transformation intensity inside Explain rather than
first deciding whether to use Explain. Already-clear output may remain unchanged.

If this SKILL.md is absent from effective context, read it before delivery; otherwise
reuse it. Load resources only when relevant. No separate Agent/model call or mandatory
first-draft/rewrite pass is needed.

Prioritize semantic fidelity, comprehension, decision-relevant information, brevity,
then presentation.

## Mainline

### 1. Read The Source And Delivery Intent

Use the [delivery scope](resources/presentation-contract.md): explain human-facing
results; preserve exact JSON, code, commands, quotations, internal records and required
links. Routine acknowledgements and heartbeats stay short. Explicit delivery intent wins.

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
| `--html` | Present the explanation as interactive HTML; on ChatGPT prefer **Visualizations / app_block** so the explanation renders directly in the conversation, while saved `.html` remains an explicit export path |

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

Compile generic HTML from a short draft with [HTML V2](resources/html-v2.md).
TPlan retains its dedicated progress renderer.

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

For **interaction inside the conversation**, use an actually available host adapter
with the same source-backed view. Acceptance requires controls the user can see and
operate there; do not regenerate progress numbers.

Explain has **no required external plugin, app, canvas, or provider dependency**.
Late-bound host adapters enhance presentation without changing or blocking the
provider-agnostic core or its source result.

`--html` selects an **HTML representation**, not a persistence target. On ChatGPT,
when the **Visualizations / app_block** surface is available, use it first. Submit one
complete app block with `variant=inline`, `language=html`, and the explanation as a
raw HTML fragment. The host owns the sandbox, title chrome, expand affordance, and
iframe-like presentation; Explain must not recreate that shell or wrap the fragment in
Markdown fences.

Visualizations is a host adapter, not an Explain dependency. On another host, use an
actually available sandboxed rendered HTML surface with the same source-backed result.
A previewable `html` code block is **not** an automatic fallback for an explicit
`--html` delivery request. Use a code block only when the user explicitly asks to see
or inspect HTML source.

If no rendered HTML surface exists, keep the requested HTML delivery open and state
that limitation accurately. Do not silently downgrade `--html` to source Code/Preview.

Do not create or attach a downloadable file merely because `--html` was requested.

Persist a `.html` file only when the user explicitly asks to save, download, export,
attach, hand off, or otherwise receive a file artifact. For an in-conversation HTML
request, follow `resources/html-v1.md` and submit the HTML itself to the available
preview surface. An image is not a substitute for requested interaction. Keep actual
display acceptance open until the host or user confirms the interactive surface is
visible and usable.

Use the requested delivery format. Representations are not new factual authorities.
Reapplying the same goal should preserve meaning and detail.

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

- [Core Presentation Contract](resources/presentation-contract.md): scope and fidelity
  rules for this Skill, not a baseline-only alternative to using Explain.
- [HTML V2 compiler](resources/html-v2.md): short drafts, layout, writing hints and recovery.
- [HTML V1](resources/html-v1.md): portable surface, fidelity and delivery boundaries
  shared by the compiler and existing TPlan adapter.
- [TPlan progress](resources/tplan-progress.md): read for task-progress delivery,
  remaining effort, work-block shares, or parallel conditions.
- [Expression modes](resources/expression-modes.md): read when compression, analogy,
  terminology, or information structure needs detailed guidance.

## Boundaries

Use Input → Explain → Output; no runtime AI Review/refine loop. Development
qualification belongs outside normal runtime.

Explain is the default human-facing delivery Skill, outside judgment-owner routing.
TPlan keeps planning/state/acceptance authority and its structured presentation adapter;
TVG keeps strengthening/exit authority. Use modes as needed, not as entry requirements.
Online AI reasoning inside artifacts, external actions, video generation, and strict
ASD-STE100 compliance stay out of scope.

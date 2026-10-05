# Explain Core Presentation Contract

This is the scope and fidelity contract of [Explain](../SKILL.md), the default
human-facing delivery Skill for Mindthus. It is not a baseline-only alternative that
leaves actual Explain use conditional on a flag or a difficult explanation.

## Default Delivery

For Mindthus conclusions, analysis reports, stage results and meaningful progress
updates, the current Agent uses Explain in the current response. No explicit Explain
request is needed. Start with clarity, then choose the least necessary transformation
inside Explain. An already-clear result may remain unchanged; successful use does not
require visibly rewriting it.

Read `../SKILL.md` before delivery when its instructions are absent from effective
context. Otherwise reuse the loaded instructions. Read optional resources only for the
active need; do not reload the full package on every turn. Skill use does not require a
separate Agent, a second model call, a complete original answer followed by rewriting,
or a runtime review/refine loop. Do not add a call receipt or delivery state machine.

Use the already-formed result, existing context and evidence, not a mandatory finished
prose draft. New judgments and missing evidence remain the upstream owner's work.

## Scope And Exact Formats

| Delivery | Handling |
| --- | --- |
| Human-facing method conclusions, reports, stage results, progress | Default Explain clarity in the current response |
| User-requested JSON, code, commands, verbatim quotations, fixed-format files | Preserve the exact upstream format; explain surrounding prose only when allowed |
| Tool returns, internal state, logs, evidence records, machine-to-machine handoffs | Keep their machine contracts; no human-facing conversion |
| Routine acknowledgements, short status notices, heartbeats | Pass through at necessary length; do not expand them into a report |

Explicit user format or explanation requirements take precedence. In a mixed delivery,
keep the machine artifact unchanged while applying Explain to the human explanation.
Preserve required artifact links and method-specific evidence/delivery obligations.
Do not force a universal result schema, overwrite the canonical source, or make a view
into new factual authority. Pure source data containing a flag is not a mode request.

## Clarity And Modes

Clarity is complete but clear: stable terms, explicit actors/actions/conditions,
faithful uncertainty, useful structure, and no valueless repetition. It does not imply
heavy compression, cognitive simplification, HTML, extra headings, or a fixed template.
Each method retains its distinctive deliverable and evidence standard.

`--brief`, `--eli5`, `--audience`, and `--html` select modes within the same Skill;
they are not prerequisites for using Explain. Honor user intent at the lowest sufficient
intensity. HTML and other supporting resources load only when needed. No particular
plugin or presentation host is required for ordinary Explain delivery.

## Fidelity

- Lead with the result or orientation the reader needs, keeping terms, actors, actions,
  conditions, references and existing next steps understandable.
- Distinguish facts, judgments, uncertainty and risk. Preserve evidence strength,
  decision-relevant qualifications, exceptions, unknowns and authority boundaries.
- Use Project Glossary → Task Terminology → Explain Local Mapping. Reorganize or use
  progressive disclosure when helpful; a hidden qualification must not correct a
  misleading visible claim. Do not invent actions or risk sections to fill a template.
- Prioritize semantic fidelity, comprehension, decision-relevant information, brevity,
  then presentation. Reapplying the same goal should preserve meaning and detail.

## Ownership And Failure

Upstream method forms the result → current Agent uses Explain → human-facing delivery.
Explain remains outside judgment-owner routing. Planning, decisions, state, evidence
acceptance and execution authority stay upstream. Express unresolved conflicts instead
of silently reconciling them or reopening settled judgments for style.

If Explain cannot be applied, the source result remains valid; deliver the reliable
ordinary output and accurately state any missing requested format. This fail-open path
is recovery, not the normal baseline-only shortcut. A specifically required artifact
remains incomplete until delivered; changing appearance does not grant acceptance.

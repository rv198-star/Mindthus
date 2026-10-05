# Explain Core Presentation Contract

This is the shared human-facing presentation baseline for Mindthus.

It applies to user-facing delivery from Mindthus methods, runtimes, and task results. It
does **not** mean every method must invoke the full `explain` Skill, start a second model
pass, or enter a fixed pipeline. The upstream method remains the judgment/state/acceptance
owner.

## Default Presentation Baseline

For an already-formed source result:

1. Lead with the result or orientation the reader needs.
2. Keep actors, actions, conditions, and references explicit.
3. Distinguish facts, judgments, uncertainty, and risk.
4. Preserve decision-relevant conditions, exceptions, evidence strength, unknowns, and
   authority boundaries.
5. Reorder and structure information to reduce cognitive load; use headings, lists,
   tables, or simple diagrams only when they improve understanding.
6. Keep terminology stable: Project Glossary → Task Terminology → Explain Local Mapping.
7. Make an existing next step easy to identify. Do not invent one when the source has
   none.
8. Use progressive disclosure for supporting detail when it improves readability.
9. Prefer semantic fidelity, then comprehension, decision-relevant information, brevity,
   and presentation.

The baseline is satisfied when the method can express its own result this way directly.
No separate Explain transformation is required. Reuse the loaded contract in the current
response; consult this resource when needed, without loading the full Skill on every turn.

Machine-readable schemas, logs, required artifact links, and exact-output requests retain
their upstream format contracts. Apply this baseline to human-facing explanations rather
than rewriting control data or forcing a universal schema. Method-specific evidence and
delivery requirements remain in force.

## Explicit Explain Transformation

Invoke the full `explain` transformation when the user explicitly requests Explain or a
mode such as `--brief`, `--eli5`, `--audience`, or `--html`, or when a material
representation/audience transformation is actually needed.

That transformation may restructure, simplify, compress, or change the presentation
surface, but it must preserve the source judgment and evidence boundary.

## Dependency And Failure Boundary

The dependency direction is:

```text
Upstream Method / Task Result
        ↓
Explain Core Presentation Contract
        ↓
User-facing Delivery
```

When a full transformation is needed:

```text
Source Result
    ↓
Explain Skill
    ↓
User-facing Delivery
```

Explain remains outside judgment-owner routing. If an optional Explain transformation
fails, the upstream result remains valid and may be delivered using the baseline
presentation contract. A required explicit artifact still remains incomplete until that
artifact is delivered.

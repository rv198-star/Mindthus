# Progressive Disclosure Runtime Exploration / 渐进式披露运行时实验

Status: Placeholder
Priority: P3
Execution: Do not implement yet

## Problem

`using-mindthus` currently exposes a broad entry contract that protects recall across framing, routing, evidence, ownership, and hard-judgment signals. This may increase context load and attention competition, but reducing the entry surface could lower wake-up recall or introduce extra routing work.

The project does not yet have enough evidence to claim that progressive disclosure is better than the current mechanism.

## Core Decision

Do not select an architecture on paper.

Reserve an experimental issue that compares multiple loading strategies under the same cases, models, clients, token accounting, and acceptance criteria.

No production change should be made until an experiment shows a useful trade-off without materially weakening hard-judgment wake-up.

## Candidate Strategies

### A. Current Full Entry Contract

Load the current `using-mindthus` entry surface and let the model filter irrelevant rules.

Potential strengths:

- high recall;
- one established contract;
- no additional internal routing stage.

Potential risks:

- context and attention overhead;
- irrelevant primitives compete with the active judgment object;
- entry contract may continue growing.

### B. Thin Entry Plus Conditional Resources

Keep a small semantic triage contract always available, then load detailed resources only after a judgment candidate is detected.

Potential strengths:

- smaller initial context;
- details are closer to the active judgment object.

Potential risks:

- first-stage misses suppress later capability;
- resource loading may add tool calls or context reconstruction cost;
- client support may vary.

### C. Recall Guard Hybrid

Keep a compact, high-recall hard-judgment cue and ownership surface always available. Delay only method-specific details, validators, examples, and low-frequency guardrails.

Potential strengths:

- may retain recall while reducing irrelevant detail;
- closer to the project's existing conditional-resource discipline.

Potential risks:

- deciding what belongs in the recall guard can recreate a large entry contract;
- ownership and resource boundaries may drift.

### D. Static Build Variants

Produce two or more packaged entry variants, such as full and low-context, without runtime resource loading. Compare them under controlled experiments.

Potential strengths:

- avoids additional runtime interaction or tool calls;
- easy A/B packaging.

Potential risks:

- variant maintenance and contract divergence;
- does not provide true per-case disclosure.

### E. Host-Native Conditional Loading

Use client or plugin discovery mechanisms to load resources when supported by the host.

Potential strengths:

- potentially efficient integration.

Potential risks:

- host-dependent behavior;
- weak portability;
- difficult cross-client comparison.

## Required Experiment Questions

- Does hard-judgment wake-up recall decline?
- Does owner and method selection precision improve or decline?
- What is the total token cost, including routing, resource loading, retries, and answer generation?
- Does the strategy add model turns, tool calls, or visible user interactions?
- Does answer value or decision delta change?
- Does behavior remain stable across Codex, Claude Code, OpenCode, and other supported hosts?
- Which rules must remain always visible to prevent catastrophic misses?

## Minimum Evaluation Matrix

Compare at least:

- current full entry contract;
- one thin-entry strategy;
- one recall-guard hybrid or static build variant.

Measure:

```yaml
wake_up_recall:
false_positive_rate:
owner_accuracy:
method_accuracy:
input_tokens:
output_tokens:
tool_calls:
model_calls:
latency_if_available:
judgment_delta_quality:
```

Token accounting must include all internal expansion or second-stage loading. A lower first prompt size is not sufficient evidence of lower total cost.

## Guardrails

- Do not use keywords as the routing mechanism.
- Do not add user-visible clarification turns solely to load a skill.
- Do not assume fewer loaded tokens improve reasoning.
- Do not accept recall loss merely because average token use falls.
- Do not merge this experiment with a general router rewrite.
- Do not promote a client-specific optimization as the portable default without cross-host evidence.

## Exit Criteria for Placeholder Status

Move this issue to active experimental work only when:

- Judgment Trace can capture route and decision deltas;
- representative wake-up and holdout cases are available;
- total token/model/tool-call accounting is possible;
- there is capacity to maintain multiple experiment variants without changing production behavior.

## Acceptance Criteria for a Future Experiment

- At least three candidate strategies are implemented as isolated experiment variants.
- Current behavior remains the control.
- Recall, precision, total cost, and judgment value are compared.
- Results include failure cases, not only aggregate scores.
- A production recommendation may be `keep current mechanism`.

## Non-goals

- Immediate refactoring of `using-mindthus`.
- Presuming Progressive Disclosure is an upgrade.
- Adding multi-turn user interaction.
- Building a generic router framework.

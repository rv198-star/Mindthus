# Failure Learning Loop / 分布式失败学习闭环

Status: Placeholder
Priority: Future
Execution: Do not implement yet

## Problem

Mindthus skills run across multiple users, clients, and nodes. Logs, cases, and outcomes are therefore distributed, while the repository needs real failure patterns to improve routing, methods, benchmarks, and tests.

A centralized collection mechanism would be a substantial product and governance change. It would require explicit user authorization, privacy controls, retention policy, transport and storage design, access control, deletion mechanisms, and a clear distinction between reusable judgment signals and private interaction content.

## Core Decision

Keep this issue as a future placeholder.

Do not implement automatic collection until the project has:

1. a stable Judgment Trace contract;
2. a local, user-controlled Case Export Contract;
3. an explicit consent and data-governance model;
4. a demonstrated need that cannot be met by manual contribution alone.

The likely future direction is opt-in collection of judgment-level events or reviewed case packages, not indiscriminate conversation logging.

## Candidate Models

These are alternatives for future evaluation, not selected architecture:

### A. Manual Case Contribution

Users export, review, and submit bounded case packages.

Strengths: strongest user control and simplest governance.

Limits: low participation and selection bias.

### B. Local Failure Queue

Nodes maintain a local queue of candidate failures. Users periodically review and export selected cases.

Strengths: captures more candidates without automatic sharing.

Limits: requires local lifecycle, review UX, and deletion controls.

### C. Opt-in Central Telemetry

Authorized clients submit a small Judgment Trace event or failure envelope.

Strengths: broader operational signal.

Limits: major privacy, consent, infrastructure, and interpretation risk.

### D. Federated or Aggregated Reporting

Clients submit aggregated counts or patterns rather than individual cases.

Strengths: potentially lower content exposure.

Limits: may lose the case detail needed to improve judgment methods and benchmarks.

A hybrid may eventually be appropriate, but it must not be chosen before the trace and consent boundaries are understood.

## Potential Data Shape

Future collection should prefer bounded fields such as:

- failure category;
- triggered judgment path;
- missed signal;
- selected owner or method;
- evidence class available or missing;
- decision delta;
- expected correction;
- anonymized or user-reviewed case reference;
- client and version metadata where authorized.

Raw prompts, answers, attachments, files, task logs, and TPlan mission state must not be assumed necessary.

## Open Questions

- What explicit user consent model is acceptable for each client?
- Is consent per installation, per case, per event class, or per submission?
- What can be collected without raw conversation content?
- How are redaction, retention, access, deletion, and export handled?
- How are TPlan records kept separate from ordinary judgment traces?
- How are malicious, low-quality, duplicated, or mislabeled contributions filtered?
- How does a collected failure become a benchmark case, test, documentation repair, or skill-contract change?
- How is selection bias reported?
- What minimum collection volume would justify the operational cost?

## Dependency Status

Completed prerequisites:

- `judgment-trace-infrastructure.md` — Judgment Trace v1.1 is active and legacy v1 remains readable;
- `case-export-contract.md` — local, review-required Case Export v1 is active.

Remaining blockers:

- useful real exported cases demonstrating that manual contribution has learning value;
- future consent and data-governance design;
- future benchmark admission and failure-classification policy;
- evidence that manual contribution is insufficient.

These completions do not activate this issue. It remains a placeholder because the
product, authorization, storage, retention, deletion, and learning-loop decisions are
still unresolved.

## Activation Criteria

Move this issue from placeholder to active design only when:

- local case export has produced useful real cases;
- manual contribution is demonstrably insufficient;
- privacy and authorization owners are identified;
- storage and deletion obligations are understood;
- there is a concrete downstream learning loop from collected signal to repository change.

## Guardrails

- No automatic conversation collection.
- No hidden telemetry.
- No upload before explicit authorization.
- No claim that structured data is automatically anonymous.
- No collection system without a deletion and retention policy.
- No benchmark admission without review.
- No merging of TPlan execution telemetry and Mindthus judgment collection by default.

## Non-goals

- Implementing an endpoint now.
- Selecting centralized telemetry now.
- Treating data volume as learning quality.
- Collecting private reasoning transcripts.

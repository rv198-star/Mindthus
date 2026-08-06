# Mindthus Internal Issue Queue / 内部问题队列

This directory records architecture and infrastructure work that is not yet represented as an external GitHub issue. Each file is an issue-ready design placeholder, not an implementation decision by itself.

## Current Priority Order

| Order | Issue | Status | Priority | Execution |
|---:|---|---|---|---|
| 1 | [Judgment Trace Infrastructure](judgment-trace-infrastructure.md) | Implemented v1.1 | P0 | Three-state delta and provenance upgrade complete |
| 2 | [Test Lifecycle Management](test-lifecycle-management.md) | Implemented wave 1 | P0 | Registry, policy, review, and first consolidation complete |
| 3 | [Case Export Contract](case-export-contract.md) | Implemented v1 | P1 | Local export and validation complete |
| 4 | [Progressive Disclosure Runtime Exploration](progressive-disclosure-runtime-exploration.md) | Placeholder | P3 | Record alternatives; do not implement |
| 5 | [Failure Learning Loop](placeholder-failure-learning-loop.md) | Placeholder | Future | Wait for real case evidence, consent, governance, and learning-loop design |

## Dependency Map

```text
Judgment Trace Infrastructure
        |
        +----------------------+
        |                      |
        v                      v
Case Export Contract     Test Lifecycle Management
        |
        v
reviewed real cases
        |
        +----------------------+
        |                      |
        v                      v
Counterfactual/value     Failure Learning Loop
benchmark inputs         (future, opt-in)

Judgment Trace + representative cases + cost accounting
        |
        v
Progressive Disclosure Runtime experiments
```

`Test Lifecycle Management` does not need to wait for the Judgment Trace schema. The two P0 issues should proceed in parallel. Judgment Trace may later improve test ownership, failure diagnosis, and benchmark linkage.

`Case Export Contract` may begin its privacy, package, and review design immediately. Its permanent structured judgment payload should align with Judgment Trace rather than create a competing schema.

## Execution Sequence

### Phase 1 — Observable Judgment Foundation — Complete

1. Existing trace-like fields were inventoried across routing, benchmark, runtime, and fidelity surfaces.
2. Judgment Trace v1.1 and three current fixtures are validated; legacy v1 remains readable.
3. All executable tests are classified without mass deletion.
4. Case Export v1 defines consent, redaction defaults, privacy scans, and fixtures.

### Phase 2 — Narrow Integration — Core Complete

1. The judgment benchmark emits per-case Judgment Trace records.
2. The test lifecycle registry is active in the canonical suite, and cleanup Wave 1 consolidated duplicate release assertions.
3. Local-only case export requires explicit user review and never uploads.
4. Export-to-benchmark admission remains a separate manual proof-of-flow task; it should use a real reviewed case rather than promoting a synthetic fixture automatically.

### Phase 3 — Evidence Before Architecture Change

1. Accumulate representative wake-up, routing, and value-delta cases.
2. Add total token, model-call, and tool-call accounting.
3. Run isolated Progressive Disclosure variants against the current mechanism.
4. Keep the current mechanism unless a variant preserves recall and improves total value or cost.

### Future — Distributed Learning

Judgment Trace v1.1 (with v1 compatibility) and local Case Export v1 now exist. Only after real exports prove useful and a governance model is approved should the project evaluate opt-in collection or contribution mechanisms under the Failure Learning Loop issue.

## Status Meaning

- `Implemented v1.1` / `Implemented wave 1`: the current bounded contract and first maintenance cycle are active; future extension needs new evidence.
- `Ready`: scoped well enough to begin implementation or detailed design.
- `Placeholder`: preserve the problem and alternatives, but do not start implementation.
- `Future`: blocked by product, consent, governance, or prerequisite infrastructure.

## Priority Meaning

- `P0`: current foundation work.
- `P1`: begin design now; implementation may depend on P0 contracts.
- `P3`: experimental or optional work that requires evidence before activation.
- `Future`: deliberately unscheduled.

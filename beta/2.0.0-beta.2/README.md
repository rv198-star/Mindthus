# Mindthus 2.0.0-beta.2 — Behavior Evaluation

Status: opened; no A/B run has started.

Beta 2 begins from the isolated Beta 1 functional checkpoint `f131fd88`. Beta 1 owns
the thin Kernel, direct Beta owner namespace, arbitration-only `using-mindthus`, exact
carrier verification, and Stable/Beta co-enable blocking. Beta 2 must not reopen those
boundaries without new runtime evidence.

## Purpose

Build an auditable behavior-evaluation path for the Stable / direct-only / thin-Kernel
comparison. The first deliverable is the protocol and instrumented harness, not a result.

## Entry gates

- Each arm runs in a separate host home with one active Mindthus namespace.
- Arm identity, plugin artifact hashes, hook state, and isolation observation are recorded.
- Primitive action recall and skill loading are scored as separate dimensions.
- Quality, owner fidelity, passive recall, false wakeups, token use, wall time, skill hops,
  resource reads, and clarification turns remain independent measurements.
- Thresholds and workload mix are frozen before matched runs are inspected.

## Opening checkpoint boundaries

- Do not run A/B cases in this opening checkpoint.
- Do not prepare, publish, tag, or promote a release.
- Do not add model-name routing.
- Do not rewrite all 1.4.6 owner contracts.
- Do not promote static budgets or green tests into behavior claims.

## First implementation slice

1. Define reproducible `stable`, `direct-only`, and `thin-kernel` arm manifests.
2. Repair benchmark semantics so a correct Kernel-only action is not scored as a missing
   `using-mindthus` load.
3. Capture actual host/plugin/hook evidence and per-turn efficiency telemetry.
4. Add smoke fixtures and stop gates; only then request authorization to start runs.

## Issue roadmap

Parent charter: [#112](https://github.com/rv198-star/Mindthus/issues/112).

| Stage | Issue | Exit condition |
| --- | --- | --- |
| Foundation | [#113](https://github.com/rv198-star/Mindthus/issues/113) | Arm identity and isolation evidence are reproducible and fail closed. |
| Foundation | [#114](https://github.com/rv198-star/Mindthus/issues/114) | Primitive action and skill loading are scored independently. |
| Foundation | [#115](https://github.com/rv198-star/Mindthus/issues/115) | Per-turn cost and missing telemetry are explicit. |
| Foundation | [#116](https://github.com/rv198-star/Mindthus/issues/116) | Owner, primitive, lifecycle, and provenance strata are covered. |
| Freeze | [#117](https://github.com/rv198-star/Mindthus/issues/117) | Metrics, mix, margins, vetoes, and stop gates have a frozen digest. |
| Rehearsal | [#118](https://github.com/rv198-star/Mindthus/issues/118) | A deterministic dry-run proves orchestration and contamination vetoes. |
| Authorized run | [#119](https://github.com/rv198-star/Mindthus/issues/119) | A named maintainer separately authorizes the frozen protocol and budget. |

The four foundation issues may advance independently. Protocol freeze depends on all
four; dry-run depends on the freeze; real model evaluation is a separate authorization
gate rather than an automatic next command.

The #113 arm-identity contract and commands are documented in
[`ARM-MANIFESTS.md`](ARM-MANIFESTS.md). No Beta.2 runner may accept a free-text variant
as identity; it must consume a verified manifest reference and digest.

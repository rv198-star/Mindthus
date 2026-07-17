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

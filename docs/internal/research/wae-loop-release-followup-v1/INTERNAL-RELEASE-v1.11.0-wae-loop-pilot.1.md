# Internal Pilot Release: v1.11.0-wae-loop-pilot.1

Date: 2026-09-07
Status: INTERNAL PILOT / NOT STABLE / NOT ROI BETA
Issue: #207
Research PR: #208
Stable baseline: v1.10.1

## Purpose

This tag freezes the first explicitly activated WAE Loop pilot runtime so WFF, EKRI/WFF knowledge work, and Slidethus can reference one immutable Mindthus source during real-project evaluation.

It is intentionally not a Stable release and does not trigger the Stable + synchronized ROI Beta release default.

## Included capability

- WAE Loop remains off by default.
- A bounded task/phase can explicitly activate the Loop.
- While active, relevant responsibility handoff attempts require a WAE checkpoint with `handoff | refine | need_input | stop`.
- Mechanical and Agentic handoff are both valid closure boundaries when their ownership conditions are satisfied.
- `guard-handoff` provides a deterministic integration point: inactive scopes pass through; active scopes require a matching latest `handoff` checkpoint and bound artifact identity.
- Runtime traces are written project-locally under `.mindthus/wae-loop/`.
- `wae-loop-run.json` is the portable single-file artifact for later case analysis.
- Trace data records observable activation/checkpoint/work/outcome/cost/coverage facts and artifact refs/hashes; it does not persist private chain-of-thought or full artifact contents by default.

## Pilot boundary

This tag freezes a pilot mechanism, not a production-wide default.

Not claimed by this tag:

- automatic passive WAE Loop activation;
- generic host-level Stop/SubAgent interception across all runtimes;
- G2/G3 real-project convergence/value qualification;
- elimination of WFF historical long-run overhead;
- production qualification for every model, host, project, or task;
- Stable or ROI Beta release eligibility.

Each consuming project must explicitly enable the Loop for its chosen bounded scope and connect its actual handoff carrier to `guard-handoff` before claiming bypass-resistant enforcement for that host.

## Canonical runtime surface

Primary files:

```text
skills/wae/SKILL.md
skills/wae/resources/ownership-closure.md
skills/wae/resources/delegation-loop.md
skills/wae/resources/wae-loop-trace.schema.json
skills/wae/scripts/delegation_loop.py
```

Typical pilot lifecycle:

```text
enable
  -> business work
  -> checkpoint
     -> refine -> work -> checkpoint
     -> handoff -> guard-handoff -> downstream work
     -> need_input / stop
  -> outcome
  -> finish
  -> validate
```

No minimum refinement count exists.

## Retrieval and analysis

The default project-local runtime root is:

```text
<project>/.mindthus/wae-loop/
```

Each activation produces:

```text
active.json
runs/<activation-id>/activation.json
runs/<activation-id>/trace.jsonl
runs/<activation-id>/summary.json
runs/<activation-id>/wae-loop-run.json
```

For later research, retrieve `wae-loop-run.json` first. Use bounded Case Prep/export only when additional artifacts or excerpts are necessary.

## Validation at freeze candidate

Before creating this internal tag, the implementation was checked with:

- full repository unittest suite: 1100 passed, 5 skipped;
- WAE/pilot/packaging targeted suite: 78 passed, 1 skipped;
- WAE Skill entrypoint remains under the 10 KiB budget;
- `git diff --check` clean;
- no known private endpoint, credential, or OCI absolute runtime path intentionally added to public WAE runtime files.

These checks validate implementation and package contracts only; they do not prove real-project WAE Loop value.

## Consumer pinning

Other projects should pin this exact tag rather than the research branch head:

```text
v1.11.0-wae-loop-pilot.1
```

Do not replace this tag in place. Any pilot contract or runtime change requires a new immutable pilot tag, for example `v1.11.0-wae-loop-pilot.2`.

## Promotion rule

Promotion to a formal Mindthus release remains contingent on real-project evidence and the existing #207 qualification plan. The expected next evidence comes from explicitly activated WFF / EKRI / Slidethus pilots using the trace and downstream outcome records produced by this tag.

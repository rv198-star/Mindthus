# Route control v0.2.1 — first executable slice

This is an opt-in implementation of commitment / programmatic loading / bound execution / scoped objection through the existing `entry.run`, not a new planner. The default Skill, original C01 and old public modes remain unchanged. No global accuracy or native plugin activation claim follows from engineering tests.

## Current host

The route-control CLI now defaults to the current Agent, without an additional LLM API key. See [current-host integration](current-host.md) for the request/response protocol and resumable execution. CPA is available only through explicit `--host cpa` in an admitted live experiment.

## Explicit offline replay

```bash
python3 -m experiments.typed_decision.entry \
  --mode route-control.v0.2.1 --host fixture \
  --fixture experiments/typed_decision/fixtures/route-control.json \
  --state-root /absolute/path/outside/repository/unique-episode
```

This command uses **injected offline decisions and text**. Reentry uses the original records and creates no new invocation. The Python API accepts a neutral decision provider, an executor, optional isolated arbitrator, optional existing relationship corrector, and an optional **host-owned artifact acceptance callback**. Live mode additionally requires a frozen `mindthus.route-control-live.v1` admission, exact packet hashes, implementation/source/provider/host bindings, and bounded call ceilings.

`route_control.py` consumes inherited M02/M03 and conditional G03, M05, R02/R03, R04, S01/S02 without changing their questions or canonical method definitions. Multiple Noul-positive methods retain distinct roles; Score is attention guidance only. The program reads exact canonical method bytes, commits a versioned route, supplies actual loaded contracts to the executor, and rejects stale identities or undeclared structural method replacement in the execution receipt. A self-reported methods list is **not proof of faithful reasoning or factual correctness**. This host is read-only text execution; it cannot perform external tool actions.

The input surface intentionally uses **original document spans and an already retained small candidate list**. Source-bound current host resolutions may establish handling/assessability or existing coverage; these are explicitly identified as host resolutions, not Jev predictions. Missing candidates or unsupported full coverage remain delegated. Automatic raw task decomposition, all-eight-method candidate discovery and a general action-plan search are **not implemented** in this slice. The 19-template catalog is not a mandatory runtime checklist.

## Control and correction

- Same conclusion scope: one established primary, with independent support/constraint roles. Different issues may have separate primaries. Unresolved issues contain no active method roles; the parent can be partial.
- Companion conditions are judged from their formal clauses; triggered method contracts are actually loaded. Loading a companion is distinct from rerunning its entire analysis. Existing source-bound coverage can be reused without presenting it as a fresh result.
- Dependencies name producer, artifact and consumer. The first slice conservatively dispatches a consumer only after the original host accepts the producer artifact **for that use**. A model's self-reported completion does not release it. No callback / missing artifact / cycle leaves that component pending. Independent scopes can still run. `needed_before_commit` does not require parallel preparation; this implementation uses the safe sequential subset.
- The executor may raise one source-referenced local objection. An isolated hook identity resolves uphold/amend/acquire/unresolved. It cannot change unrelated issues, invent a new unprovided method, or enlarge permissions. Unavailable adjudication is a named handoff, not silent rerouting.
- Existing relationship checks/correction/recheck use the **same Episode instance** and lower-level components. The input binds that optional subcheck to one issue (an explicit `relationship_issue` is required for multi-issue input). Original documents stay unchanged; a corrected candidate is not new factual evidence. An unresolved check cannot silently become a passed scope.
- There is one public mode and one registry/ledger root per episode; nesting old public modes is rejected. Known completed calls are reused, unknown calls are not resent. Method calls share the journal but have a separately explicit task budget and are fully counted in usage.

## DS4.1 Flash max

The Owner specified `max` for all new DeepSeek V4.1 Flash calls on 2026-09-23. Current CPA correction/organizer and new executor/arbitrator adapters send:

```json
{"model":"deepseek-v4.1-flash","reasoning_effort":"max","thinking":{"type":"enabled"}}
```

The request and adapter identities include this setting. No fallback to a lower effort is permitted. DeepSeek's official Chat Completions reference documents `max` and enabled thinking; CPA is a separate service path, so an HTTP success proves acceptance of the request, **not upstream effort attestation**. Preserve requested effort, any reported effort, reasoning-token telemetry and whether reasoning content was present; do not publish or use raw private reasoning as an execution artifact. Historical frozen requests/results are not rewritten. A change of effort is a new runtime condition; earlier lower/unspecified-effort results do not become max results.

Official source checked 2026-09-23: https://api-docs.deepseek.com/api/create-chat-completion/ (thinking / reasoning_effort). Output/time limits remain bounded, so max does not grant an unbounded token budget. A truncated or timed-out max call is recorded, not retried at lower effort.

## Evidence to report separately

1. Engineering controls: loaded bytes, route/revision/receipt binding, mixed result types, objections, partial scopes, output acceptance, shared budgets and restart behavior.
2. Small real integration observations: actual returned routes, exact host text, requested max setting and unknown upstream attestation. Inputs remain authored development material, not holdout.
3. Still unproven: all-method routing quality, natural candidate discovery, advice-vs-committed net benefit, reliable two-turn generalization, native plugin activation and deployment readiness. Existing Skills/display development evidence remains historical, not automatic qualification for this new profile.

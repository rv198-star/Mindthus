# First implementation slice — #211

## Core
C01-v2 is an explicit semantic dependency DAG with same-State questions batched together. It is not a generic task engine. Source method contracts remain authoritative. Decision outputs are not actual tool execution.

## Mainline
- `contracts.py`: provider-neutral DecisionSpec/DecisionResult plus explicit `EngineIdentity`, `ServingIdentity` and `ResolvedRuntime`. Decision status/value and provider uncertainty remain separate; a successful provider result must carry an observable resolved runtime.
- `providers.py`: Jev semantics live in one `JevEngine`. `TypeSafeJevProvider` and `OpenRouterJevProvider` are different serving paths for that same logical engine; ordinary structured-chat remains a separate comparison engine. One explicit request, no hidden retry. No credentials are logged, redirects are rejected, response size and timeout are bounded.
- `session.py`: an immutable local inference journal for a named trial. Cache/recovery identity binds the logical engine plus configured serving path, not the returned model string. The first successful `ResolvedRuntime` (actual model/provider) is frozen for the trial; later runtime drift fails closed and requires a new trial root. Unknown in-flight calls require host reconciliation and are not reissued on resume.
- `max_request_bytes` bounds the projected typed input; `projected_request_bytes` records that value, not wire bytes or tokens. The HTTP transport separately bounds the fully encoded wire body to 256 KiB.
- C01 remains provider-neutral. It receives only typed judgments; it does not inspect TypeSafe/OpenRouter endpoints, model names, credentials or transport details. A changed serving path does not require graph changes, but it does require a distinct trial identity and separate qualification evidence.
- Existing Judgment Trace v1.1 is used for observable skill-file consumption and inferred choices. Mission state and native host authorization are unchanged.

## C01-v2 contract

See `c01-v2-contract.md`: J1 entry mode + J2 unresolved obligation share one batch; owner selection precedes a complete selected method read and dependent applicability. D0 owns mechanical checks. All results remain advisory. `c01-v2-development-freeze.json` binds the separate Chinese development set and its preregistered scoring.

## Engine / serving abstraction

```text
Decision Contract
      ↓
Decision Engine
      ↓
Serving Provider / Transport
      ↓
Resolved Runtime Observation
```

For Jev, both current serving paths expose the canonical engine identity `system_one / jev / jev-1.13`. TypeSafe native requests `jev-1.13.0`; OpenRouter Decisions requests `typesafe/jev-1.13` and may resolve it to a dated snapshot such as `typesafe/jev-1.13-20260917`. Those strings are serving configuration/runtime evidence, not the Decision Contract.

API compatibility is therefore intentionally broader than behavioral qualification: a future engine can implement the same `select / assess_proposition / rate` contract without changing C01, but its node/graph qualification does not inherit from Jev merely because the shapes match.

## Boundary
Current CLI/carrier is offline only. The HTTP adapters are contract-tested through injected transports. A paid campaign requires a frozen real-data manifest, exact model identities, approved budget/egress scope and a validated host carrier before enabling the live session path. Setting an API key is not campaign authorization. No semantic accuracy, cost improvement, native hook integration or cross-host qualification is claimed by this implementation.

## Recovery
Read STATUS.md, inspect git status and the referenced issue before edits. A completed immutable call is replayed, not rerun. A persisted intent without outcome is an unknown prior call: recover its original receipt or record an explicit new attempt in a separately authorized trial; do not delete the intent or reset counters. Journal digests detect accidental corruption, not a hostile administrator rewriting both content and digest.

## Dynamic design
The standard's bounded dynamic-design exception is preserved as a design rule. This pilot does not include a recursive designer, generated-code evaluator, or automatic global-template promotion.

## OpenRouter Jev live compatibility smoke

A single explicitly authorized live smoke was run on 2026-09-21 through the OpenRouter alpha Decisions endpoint with the pinned family `typesafe/jev-1.13`. The response resolved to `typesafe/jev-1.13-20260917`, provider `TypeSafe`, HTTP 200, with 575 input tokens, 91 output tokens and reported cost `$0.00002415`; observed wall time was 0.453 seconds.

The routing choice selected `sra` with provider confidence `0.99`, while a separate Noul question about fact sufficiency returned `0.23`. Under the later normative review this is primarily a Decision Contract diagnostic, not evidence of engine inconsistency; C01-v2 removes that meta-question. This is intentionally recorded as an API/shape smoke only: it demonstrates that authentication, request mapping, answer types, resolved snapshot identity and usage reporting work. It does **not** qualify Chinese semantics, Noul thresholds, route accuracy or net value.

`OpenRouterJevProvider` therefore treats `typesafe/jev-1.13` as the pinned family and records the dated resolved snapshot returned by OpenRouter. `~typesafe/jev-latest` remains inadmissible for qualification runs. No API credential is stored in the repository or evidence files.

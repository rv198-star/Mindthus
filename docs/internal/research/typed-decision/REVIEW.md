# C01 implementation review — 2026-09-21

## Scope and evidence ceiling
This is the first **offline engineering slice**, not completion of #211's live/semantic/value acceptance. Existing method texts, TPlan runtime, release paths, #112 HOLD and #207 pilot were not changed.

## Review provenance
- Author self-review and executable adversarial probes: performed.
- Separate Codex CLI read-only review: attempted once; authentication returned HTTP 401, no review result obtained. The CLI's own transport retries are not independent reviews. No global credential or permission changes were made. This is not external certification.

## Concrete findings and fixes
1. Existing owner `3l5s` was rejected by an alphabetic-only option identifier. Decision identifiers and option identifiers now have appropriate separate lexical contracts; the canonical owner remains unchanged.
2. A tuple read-set serialized to JSON as a list, causing a valid resumed intent to compare unequal. `DecisionSpec.to_dict()` now returns the canonical JSON representation; checkpoint input and replay use that same form.
3. The known absence of an explicit method was treated as unknown required context. C01 now carries the explicit `not_requested` value at the dependent applicability boundary.
4. Malformed provider response/usage shapes could raise `AttributeError` outside the typed provider-error path. Adapters now validate these shapes; invalid provider batch types are recorded as failures.
5. The byte counter represented projected typed input, not fully encoded HTTP bytes. It is now named `projected_request_bytes`; actual encoded HTTP bodies have a separate 256 KiB bound. Token/billing totals remain unknown without reported telemetry.

Each finding has a focused regression. No additional semantic audit layer, model retry loop or automatic designer was introduced.

## Delivered and remaining
The offline graph exercises parallel local questions, a genuine selected-owner dependency, guarded file consumption, missing/unknown/conflict fallbacks, immutable replay, selective invalidation, budgets, corruption rejection and use of existing Judgment Trace v1.1.

Remaining #211 work: real A/B/C datasets/protocol/budget, live session carrier and native host consumption, successful independent review, real provider compatibility and task/value evaluation. The HTTP adapters alone do not close those items. #212 remains a conditional next issue; its runtime has not been implemented in this slice. Unchanged passing evidence should be reused when work resumes.

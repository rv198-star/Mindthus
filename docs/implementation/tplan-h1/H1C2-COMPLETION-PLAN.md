# H1-C2 follow-up: controlled B acceptance and Task completion

**Status: implementation authorized under Mindthus #241; exact contract and RED
fixtures are frozen before runtime changes. See [H1C2-CONTRACT.md](H1C2-CONTRACT.md).
H1-C full business delivery remains incomplete until this slice passes.** Current receipt.record is
only a dispatch fact. Generic B acceptance/status writes remain rejected, including
after delivered, so this slice cannot close a real controlled B or its Mission.

## Core

A delivered native response becomes B's accepted business result only through the
existing acceptance authority and one canonical H1 transaction. Dispatch success,
Owner approval of A, and model prose must not stand in for B acceptance.

## Mainline / bounded next implementation

1. Bind B's produced immutable result bytes to its exact canonical slot, native
   session/request IDs and original execution attempt. Keep late results as facts.
2. Let the existing designated acceptance actor evaluate B against its actual
   acceptance criteria. Pin the accepted result and qualified evidence references;
   define that actor's trusted Host event provenance before enabling the action.
3. Add one scoped completion handler in the existing Mission writer, using current
   request revision, current Owner decision/adoption, original slot and result SHA.
   It validates current business eligibility, then atomically records qualified B
   acceptance, task completion and historical command result. Reuse prepared-log
   recovery and the existing reserved evidence authority; no second completion DB.
4. Run the existing Mission closure checks, including H1 completion findings. A
   delivered receipt alone cannot close B. Stale decision/result/slot cannot close
   B or overwrite current adoption. Generic legacy completion remains protected.

The exact command schema and acceptance authority are intentionally not specified
as deployed API yet. They require their own contract + failure fixtures before code.
No new dispatch, slot release, cancellation, replan or multi-version system is needed.

## Runtime support / required acceptance evidence

- Delivered native fact without business acceptance leaves B incomplete.
- Correct current slot + qualified business evidence completes exactly once.
- Duplicate and conflicting completion commands follow existing idempotency rules.
- Crash after prepare and recovery interruption roll forward the same completion.
- Owner changes intent before completion: archive late result, refuse stale acceptance.
- Missing/tampered result bytes, wrong attempt, wrong native IDs or missing acceptance
  authority reject without changing B, adoption or closure eligibility.
- C continues normally; non-H1 completion behavior stays unchanged.
- Pack fingerprint and Q1/Q2 compatibility are reverified for the new build.

## Boundary / Host integration dependencies

AIWork #158/#167 must separately demonstrate authenticated Owner event binding,
Agent-inaccessible signing/verifier roots and candidate store, exact native ID
pass-through, managed delegation binding and enforced final scoped claim. Native
sessionController creation/prompt/receipt E2E is not proven by Python or Node MAC
simulation. #124 remains HOLD; neither this plan nor completion cancels old tools.

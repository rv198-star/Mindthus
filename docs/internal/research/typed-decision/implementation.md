# First implementation slice — #211

## Core
C01 is an explicit small DAG over batched provider calls. It is not a generic task engine. Source method contracts remain authoritative. Decision outputs are not actual tool execution.

## Mainline
- `contracts.py`: provider-neutral specs/results; status and value are separate. Jev probabilities retain their meaning. The ordinary structured-chat comparison supports categorical selection, not fabricated Noul probabilities.
- `providers.py`: TypeSafe native API adapter and OpenRouter structured-chat adapter. One explicit request, no hidden retry. No credentials are logged, redirects are rejected, response size and timeout are bounded. `max_request_bytes` bounds the projected typed input; `projected_request_bytes` records that value, not wire bytes or tokens. The HTTP transport separately bounds the fully encoded wire body to 256 KiB. OpenRouter's Jev-specific alpha transport is not implemented in this slice; it is not a chat-completions model switch.
- `session.py`: an immutable local inference journal for a named trial. POSIX single-writer lock, atomic publication, content-checked records, persisted call intent before execution. Unknown in-flight calls require reconciliation through the host; they are not reissued on resume.
- C01 uses a same-input J1/J2/J3 batch, followed by J4 and a genuinely dependent J5. Whole-batch reuse is deliberate: an LLM comparison can couple its answers. A changed node/read-set invalidates its batch and data-dependent successors; unrelated valid batches remain reusable. Provider/config/runtime changes require a new trial root.
- Existing Judgment Trace v1.1 is used for observable skill-file consumption and inferred choices. Mission state and native host authorization are unchanged.

## Boundary
Current CLI/carrier is offline only. The HTTP adapters are contract-tested through injected transports. A paid campaign requires a frozen real-data manifest, exact model identities, approved budget/egress scope and a validated host carrier before enabling the live session path. Setting an API key is not campaign authorization. No semantic accuracy, cost improvement, native hook integration or cross-host qualification is claimed by this implementation.

## Recovery
Read STATUS.md, inspect git status and the referenced issue before edits. A completed immutable call is replayed, not rerun. A persisted intent without outcome is an unknown prior call: recover its original receipt or record an explicit new attempt in a separately authorized trial; do not delete the intent or reset counters. Journal digests detect accidental corruption, not a hostile administrator rewriting both content and digest.

## Dynamic design
The standard's bounded dynamic-design exception is preserved as a design rule. This pilot does not include a recursive designer, generated-code evaluator, or automatic global-template promotion.

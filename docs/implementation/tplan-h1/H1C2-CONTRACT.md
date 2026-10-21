# H1-C2 frozen implementation contract · Issue #241

## Core

A controlled B completes only after a trusted Host has recorded its actual delivered
bytes and then authenticated a designated reviewer's business acceptance of those
bytes against B's existing acceptance criteria. Delivery and acceptance are separate
facts. This extends H1 v0.3.1 in the existing Mission transaction, with no new queue,
DB, dispatch lifecycle, slot release, or completion state machine.

## Mainline / exact protocol

The existing `tplan.h1.command.v1` envelope, fixed Host root, exact field checking,
300-second maximum receipt lifetime, issuer nonce consumption, build gate, Mission
lock and historical command replay apply. New actions:

1. `result.record` payload is exactly `{slot_id,session_id,native_request_id,
   attempt_ref,receipt_ref,content_b64}`. The protected Host signs the exact command
   only after observing real native delivered bytes for the original slot. Native
   IDs equal the canonical slot; `attempt_ref` equals its stable `intent_id`.
   Immutable candidate identity uses the existing task/attempt/SHA candidate store.
   The slot's optional `result` is `{candidate_id,receipt_ref,committed_at}` and a
   delivered dispatch fact is appended. It is immutable: a second command ID cannot
   replace it, even with identical bytes. Exact command replay returns history.
   `delivery_digest = digest(slot.result)` binds the committed delivery fact.
   Existing `receipt.record(delivered)` alone has neither byte nor acceptance scope.
2. `task.complete` payload is exactly `{receipt}`. Receipt schema is
   `tplan.acceptance_receipt.v0.1`, signed separately by the protected Host. Its exact
   fields (including the signature) are:

   ```text
   schema_version issuer_id key_id mission_id task_id slot_id session_id
   native_request_id attempt_ref candidate_id result_sha256 request_id
   expected_revision decision_id adopted_candidate_id input_digest dependency_digest
   delivery_digest acceptance_ids acceptance_contract_digest actor_subject_ref
   origin_binding_ref origin_session_ref origin_event_ref evidence_refs summary
   issued_at expires_at nonce signature
   ```

   `candidate_id/result_sha256` refer to B, `adopted_candidate_id` to A. Native IDs,
   original attempt, request/revision/decision, input and dependency digest equal the
   original slot AND current decision/adoption/dependency projection. The result
   bytes are read and SHA-checked again. Mission must be active, B pending/active,
   no completion already recorded, no native scoped blockers or changed source
   acceptance. All controlling requests are rechecked. Current adoption must match
   its decided candidate, decision and SHA. `acceptance_ids` is a sorted, nonempty,
   exact set of B's native inherited acceptance coverage. Contract digest is
   `digest(sorted([{id,description}, ...], key=id))` for those Mission criteria.
3. The fixed Host trust configuration additionally specifies `acceptance_actors`,
   mapping task ID to exactly the permitted `actor_subject_ref`,
   `origin_binding_ref`, and `origin_session_ref`. It is not a Mission/CLI/model
   supplied role. The Host authenticates that actor's explicit acceptance event,
   checks real evidence and criteria, and signs only after the committed delivered
   fact exists. `origin_event_ref` is the authenticated event ID; `evidence_refs`
   is a nonempty distinct list of bounded references to Host-verified business
   evidence; `summary` is a nonempty single-line review conclusion. Neither free
   text, tool approval nor ordinary Q2 principal is authentication. Including the
   committed delivery digest prevents pre-delivery acceptance. Runtime validates
   provenance/scope/coverage; semantic correctness remains the designated actor's
   responsibility. Host event identity and nonce are consumed once per issuer.
4. A single existing `_commit_mission_state_unlocked` transaction saves the prepared
   native `acceptance_passed` event, B status `completed`, optional slot `completion`
   `{command_id,evidence_id,candidate_id,receipt_digest,evidence_digest}`, consumed
   Host/acceptance/event identities, and H1 command result. Evidence payload retains
   the signed scope and receipt digest, excluding signature and ephemeral signing
   material. Existing reserved evidence authority and scoped H1 authority must both
   be supplied; neither alone bypasses the B evidence gate. Exact historical replay
   creates no evidence. A second completion ID conflicts; same command ID with
   changed payload conflicts. Prepared recovery rolls forward the saved evidence,
   state and result together; it never re-runs review or verifies an expired receipt.
5. Mission closure uses its original success-critical and qualified evidence checks
   plus H1 current decision/adoption/slot/completion and exact evidence integrity.
   Later relevant failed acceptance blocks closure. C and non-H1/Q2 behavior retain
   their existing writers. No new Mission-close command is introduced.

## Guardrail / writer protection

This protects the mainline from ordinary writers manufacturing acceptance. Existing
`append_event`, CLI/checkpoint/Q2 evidence, status/commit, adoption and Mission-close
boundaries remain enforced. Only the protected H1 completion handler may submit B's
qualified pass through the canonical writer with both internal capabilities. A
reserved-evidence capability alone cannot authorize it. No model prose or Q2 actor
can choose an acceptance principal. This does not establish Host authentication.

## Boundary / deployment

`_trust_config()` remains literally `None` in shipped code. No production signer,
secret/key-path/env option, installed skill edit, deployment or real Mission run.
Only tests provide a synthetic keyring/signer. A future isolated Host must prove
Agent-inaccessible roots, content store, native delivery and authenticated actor
binding separately (AIWork #158/#167). Python mocks/MAC vectors are not DSH/Web/IM
E2E. #124 remains HOLD. Terminal Missions accept original result/dispatch facts;
`task.complete` rejects and never reopens, adopts, or dispatches. Changed Owner
intent preserves the delivered fact but invalidates completion for the old slot.

## Runtime support / RED acceptance matrix

Freeze this contract and failing fixtures before runtime edits. Cover A→Owner→B→
accepted B→original Mission close; C independence; delivered-only refusal; exact
native result binding; replay/conflict; wrong task/slot/attempt/native IDs/SHA/actor/
event/criteria/evidence; missing or tampered bytes; current Owner revision/adoption/
source failure; terminal late facts; prepared crash and interrupted recovery;
response loss; old writer bypass; non-H1/Q1/Q2 and package fingerprint regression.

Freeze probe: this is an implementation contract and synthetic failure baseline,
not deployed authentication or independent review approval. Next consumer is the
implementer and independent PR reviewer. Owner already authorized implementation;
Draft PR remains unmerged for independent review.

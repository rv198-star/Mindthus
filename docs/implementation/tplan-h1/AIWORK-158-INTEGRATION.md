# AIWork #158: H1-B/C Host integration handoff

## Core / acceptance status

This package supplies a synthetic-tested kernel and a disabled Host seam. **Real
Owner / Web / IM authentication, protected candidate storage and native dispatch
admission are NOT certified or enabled.** Q2 principal remains an ordinary caller.
Do not enable production H1 Missions from this change alone. #124 remains HOLD.
No second approval table is needed: use the canonical Mission decisions and slots.

## Mainline / protected process boundary

`tplan_h1_commands.execute(Path, request) -> (envelope, exit_code)` is the versioned
integration interface. It accepts only a signed request; it accepts no verifier,
keyring, secret, key path, principal or trust directory. The shipped private
`_trust_config()` returns None. There is no production provisioning command, env
switch, fallback signer or client-side signing library. The test fixture signer is
under tests/tplan/h1_test_host.py only and is not part of any skill release layout.

Before replacing that disabled seam, AIWork must demonstrate a protected Host
process whose code, memory, trust root, signing path and canonical write/store
permissions are outside Agent/Member tool access. Same uid with readable files,
arbitrary Python import/monkeypatch or an Agent-accessible signing endpoint is
insufficient. A future reviewed Host bootstrap must pin issuer_id/key_id, secret,
Mission identity, owner_subject_ref, origin_binding_ref and origin_session_ref from
Host-owned authentication data. This package does not read or copy existing keys.

Signing and verification belong to separate authority paths. The Host signer must
consume an already authenticated structured choice event with exact Mission,
request, displayed revision, choice and candidate digest. It must not accept these
as model-selected signing instructions. Tool permission approval, free text such as
“agree”, and principal=owner are not authenticated H1 choices. Pin the authenticated
Owner and original session/binding in private trust configuration. Scope the Host
process to its registered Mission; clients must not select another trust root.

## Runtime support / wire contract

See H1BC-IMPLEMENTATION.md for exact action/payload fields and bounded quotas.
Envelope: protocol/mission_id/command_id/action/ok/status/code/data. Code 0 means
committed, replayed or read. Code 4 means recovery_required; code 14 means
outcome_unknown; other nonzero codes reject the command. A transport timeout or a
rejection never authorizes a new physical dispatch. Semantic rejection codes include
host_disabled, unauthorized, stale_revision, replay, waiting, candidate_unavailable,
slot_occupied, terminal, command_conflict, not_found, capacity_exceeded.

Both receipt types sign their entire JSON object excluding signature. Use UTF-8,
lexicographically sorted object keys, compact JSON separators, unescaped Unicode,
finite JSON values, integer Unix seconds, lowercase HMAC-SHA256 hex. Host receipt
request_digest is `sha256:` plus SHA-256 of the canonical complete request excluding
host_receipt; it includes the complete nested Owner receipt. Host receipt fields:
issuer_id/key_id/issued_at/expires_at/nonce/request_digest/signature. Owner receipt
fields are exactly CONTRACT-v0.3.1 section 3 plus schema_version/signature. Lifetime
1..300 seconds, future skew at most 30 seconds, expiry strictly after verification.

Use one stable command ID and retain the exact signed request for replay. A changed
signature/timestamp/nonce under an existing ID is a conflict. Exact replay may return
the old historical result after expiry, but cannot grant current authorization.
No raw signatures/tokens are persisted or returned by snapshot.get; only scope digests
and audit references survive. Owner nonce consumption, revision and result are atomic.

Human-control H1 command results live in human_control.commands. Q2 command.get
continues to query Q2 observations only; use H1 command.get for H1 historical results.
Existing Q1 snapshot.get adds a read-only human_control summary with pending requests,
revision, current adoption, slot facts and closure blockers. It is not a dispatch token.

## Mainline / final dispatch admission

1. Perform slow, side-effect-free preparation first; select the pinned kernel build.
2. Submit execution.claim for current request revision and real prepared input_digest.
   TPlan first checks an active Mission, unstarted B, explicit native work_plan
   depends_on=[A], completed A and qualified version-bound acceptance of the adopted
   bytes. Missing/unknown/extra dependencies fail closed in this bounded core. Owner
   signing cannot satisfy these checks. TPlan fixes its canonical round, candidate, dependency digest and stable IDs in one
   short transaction. Caller DSH roundId/requestId cannot select a new business round.
3. Only a successful final claim permits the *first* native session/send side effect.
   Use the returned intent_id, session_id, native_request_id and exact input digest.
   Bind these to the existing Host ledger/TeamSessionStore; that ledger records
   technical dispatch, not a second business approval. Require native idempotency.
4. A replayed claim is historical, never an instruction to send again. If the Host
   cannot tell whether it crossed the send point, query the existing native identity
   and reconcile. Record actual sent/unknown/accepted/delivered receipts for that slot.
5. Owner may withdraw immediately. The old execution may still run; preserve its
   slot and receipt identity. No not_sent/superseded/cancelled slot release exists in
   this core. Late results may be archived as candidates/facts and cannot replace the
   named adopted candidate. Do not start a substitute same-task physical dispatch.

Legacy AIWork gate/admission/dispatch/round entrypoints must explicitly fail closed
for H1-controlled tasks until they enforce this contract. A whole-Mission Q2 hash
is not a scoped execution credential. C observations can change that hash without
invalidating B's slot. The scoped claim's decision, input and dependency projection
remain authoritative. No native side effect is performed by this Mindthus module.

## Boundary / deferred capabilities

The first core does not retry a previously claimed task, even after delivered. It
also rejects generic replanning and ordinary controlled task completion; telemetry
and receipts are facts, not acceptance. H1-C2 adds the separately scoped
[result and acceptance contract](H1C2-CONTRACT.md); repeated B execution remains
out of scope. Bounded request.revise supports
same-request v2 review: pending-after-request_changes + expected_revision + recorded
same-source/new-attempt candidate; it advances revision and never approves. A retained
fallback_candidate_id permits immediate withdrawal to v1. For withdraw_change the
Owner receipt binds the fallback digest; other choices bind the displayed current
digest. Candidate-specific qualified acceptance is checked before claim.
Independent C and non-H1 Missions retain their existing writer behavior.

Candidate files are atomically created and SHA-verified before adoption/claim. Local
read-only permissions are not proof of Member isolation; Host-private content storage
is still a production admission requirement. No actual artifact is deleted on quota
pressure; orphaned crash bytes are retained and verified if reused.

Host acceptance still needed: real Web/IM identity and explicit event binding;
Agent-inaccessible issuer and verifier roots; protected content store; all native
admission paths; stable native IDs and timeout recovery; delayed sender race before
first send; no production enablement based on this synthetic test suite.

Read-only source audit: AIWork checkout commit
90d507309e39857d33a10db38bb5625654f01f45, coordinator-admission.js and
coordinator-tplan-gate.js. Existing admission checks completed/accepted predecessors,
known native dependencies and adopted inputs, and rejects H1 legacy admission.
No AIWork source was edited; this is source review, not live integration evidence.

Native ID correction: slot.session_id is exactly `session-<canonical UUID>` and
slot.native_request_id is exactly a canonical UUID. Pass both to TeamSessionStore /
sessionController unchanged. Explicit Team sessions require the existing supported
managed delegation binding; keep it tied to the same slot/intent in the Host ledger.
A Host-side ID substitution or a replay interpreted as a new send violates this
contract. Native integration is still disabled and unproven.

H1-C2 (#241) extends the synthetic kernel with `result.record` and `task.complete`.
A protected Host must record the original slot's actual native delivered bytes,
then authenticate the fixed designated reviewer's explicit business acceptance.
The separate acceptance receipt binds the committed delivery digest, B candidate
and result SHA, native identities, current Owner revision/adopted input, native
criteria, actor, originating event and qualified evidence references. Only then
may one original Mission transaction save evidence, B completed and command result.
See [the exact frozen contract](H1C2-CONTRACT.md) and
[the implementation result](H1C2-RESULT.md). Synthetic kernel success does not
establish live Host authentication or native DSH/Web/IM E2E. `_trust_config()`
remains None; no caller may select a secret or key path. Existing deployments and
installed Skills are unchanged. #124 remains HOLD.

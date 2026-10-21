# H1-B/C bounded implementation contract

Scope: Mindthus #236, AIWork #158; baseline fe9fc239, frozen semantic input
CONTRACT-v0.3.1.md (its historical status text is preserved). This document and
executable negative fixtures must be committed before runtime edits.

## Core

One opt-in canonical Mission owns bytes/candidates, local requests, nonce consumption,
Owner decisions, adoption, kernel rounds, slots, receipts and command results. A→B
waits while independent C progresses. Claims are facts distinct from decisions and
native dispatch receipts. This implementation never sends external work.

## Mainline / B

Public Python `tplan_h1_commands.execute(directory, request)` is the future protected
Host integration seam, protocol `tplan.h1.command.v1`. Exact request fields:
protocol/action/mission_id/command_id/expected_build_hash/payload/host_receipt.
No principal, secret, key path, trust directory or signer argument exists.
Host receipt signs the entire request excluding host_receipt (including Owner receipt
when present), with issuer_id/key_id/issued_at/expires_at/nonce/request_digest.
All writes require a valid fixed Host root. `decision.apply` additionally requires
`tplan.owner_receipt.v0.1` with exactly the frozen v0.3.1 fields plus schema_version
and signature. JSON: sorted keys, compact separators, UTF-8, ensure_ascii=False,
allow_nan=False; signature lowercase HMAC-SHA256 hex over all fields except signature.
Times are integer Unix seconds, lifetime 1..300 seconds, future skew <=30 seconds.
Owner subject, mission origin binding and session come from the pre-fixed Host root,
not Mission text or caller values. Source event is a nonempty authenticated action
reference. Signing is exclusively a Host responsibility; no runtime signer exists.

Runtime ships with no trust bootstrap: private `_trust_config()` returns None and
all H1 commands fail `host_disabled`. It reads no env, key file, argv or Mission trust
root. Tests patch this private seam in an isolated test process using a keyring/signing
helper located only under tests. This does not establish OS isolation. AIWork must
implement root provisioning in an Agent-inaccessible protected Host process before
real enablement; importing Python beside an Agent is not an authentication boundary.

`candidate.submit`: payload task_id/attempt_ref/content_b64; bounded actual bytes
(<=256KiB, <=64 candidates), atomic content-addressed creation, fsync and SHA check.
bytes_ref is kernel-derived, never caller-selected. Local read-only files are not a
proved Host-private store: every use rechecks SHA, deployment storage admission remains
open. Orphan bytes after crash are retained and safely reused, never adopted by scan.
`decision.open`: request_id/business_task_id/blocked_task_ids/candidate_id; revision=1,
no active/completed B, fixed graph; reopening/replanning unsupported in this slice.
`decision.apply`: payload receipt; approve_current/request_changes/withdraw_change.
Revision, nonce, decision and result commit together. request_changes leaves B waiting;
withdraw_change records intent immediately even if bytes invalid; adoption_blocked
records the reason, with revision advancing. Approval is also blocked on invalid bytes.
Candidates submitted later do not replace the request's named candidate or adoption.
`adoption.apply`: request_id/candidate_id; only the current eligible Owner decision
can adopt, bytes rechecked. Terminal Missions reject adoption, but candidate/receipt
facts can still be archived without reopening anything.

## Mainline / C

`execution.claim`: task_id/request_id/expected_revision/input_digest. Kernel computes
round and the A/dependency/candidate projection; request must use current revision and
current adoption and all controlling requests must permit execution. Unique key is
Mission/task/round. It fixes issuer binding, input and dependency digests, candidate,
decision, intent_id/session_id/native_request_id and historical result atomically.
Only a replay of the same command returns the same successful claim; another command
cannot acquire the slot. Caller round/request/session IDs cannot select a new round.
`receipt.record`: slot_id/status/receipt_ref, status in sent/unknown/accepted/delivered;
append-only Host-bound facts, no slot creation or release. Terminal/late facts are
allowed; acceptance does not mean business adoption. `command.get`: payload command_id;
`execution.get`: payload slot_id; both return historical facts. Explicit recovery uses
existing Q2 runtime.recover, then original H1 command replay. No automatic recovery.

No timeout, unknown, observed-not-sent or new Owner decision frees a claimed slot.
This bounded first core conservatively rejects *all* second physical claims for a
previously claimed task, including after delivered. A future retry/fencing capability
needs a new contract. Owner decision/adoption can still change immediately. C evidence
changes global hashes but never B's round or existing slot. Before final claim the
current decision wins; after final claim the original Host may still send, so query
its stable identities and never create a substitute dispatch. #124 stays HOLD.

## Guardrails / existing writer matrix

| Entry | H1 protection | Independent C |
|---|---|---|
| _commit_mission_state_unlocked / commit / transition / apply_decision | before-state human_control immutable to legacy; preserve controlled A/B graph, role, artifact refs; controlled B and descendants cannot become active/completed via legacy writer, even after approval | normal progress allowed |
| append_event / record_evidence / checkpoint | controlled B acceptance cannot substitute Owner/adoption/dispatch; ordinary observations remain facts | normal evidence allowed |
| Mission close | pending/blocked adoption/missing current claim prevents close; unsupported controlled completion fails closed | original non-H1 closure unchanged |
| append_step_log / trace / execution spans | telemetry only, grants no claim/adoption | normal telemetry allowed |
| Q2 command runtime | evidence.record always observation, even principal=owner; no H1 authorization | unchanged |
| AIWork gate/admission/dispatch/round | unimplemented here: must reject H1 legacy admission and require final scoped claim before native side effects | later Host integration |

## Boundary / budgets and verification

Same pinned-build provenance and prepared transaction recovery as Q2. H1 commands and
nonces live in human_control (not Q2 observation-only command_results); <=1024 commands,
<=1MiB control, <=4MiB Mission artifacts, >=16MiB transaction headroom; capacity refusal
retains all existing facts. Same ID/content is historical replay, changed content
conflicts; signed receipt reused with a new command consumes no second nonce.
No real Missions, installed skills, production credentials, OCI tree, release or main
merge. Local synthetic PASS is never real Host/Web/IM PASS.

Failure fixtures: default-disabled/self-selected keys/principal spoof; signature,
identity, time, revision and nonce rejection with no business mutation; B bypass and
C success; immutable bytes/tamper/later candidate; withdrawal with unavailable bytes;
prepared crash, recovery interruption, response loss, duplicate command; concurrent
claims and stable unknown slot; slow preparation races; final claim before first send
then withdrawal; late and terminal facts; manifest/pack/pinned writer compatibility.

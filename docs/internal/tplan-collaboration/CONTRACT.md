# TPlan Collaboration Runtime Contract

Date: 2026-11-17. Contract version: `tplan.collaboration.command.v1`. Frozen product and engineering inputs are [PROPOSAL.md](PROPOSAL.md) v0.4 and [IMPLEMENTATION.md](IMPLEMENTATION.md) 1.0.

## Core

The runtime adds one optional, A-owned collaboration state to an ordinary Mission. It keeps the existing objective, acceptance, task tree, Guard, provenance, transaction journal, recovery, H1 authority, and Q2 command-result authority. B and C remain ordinary conversations: they receive normal work instructions and return normal language; the A runtime records the resulting bounded facts.

The command layer performs mechanical checks. A retains judgment over relevance, scope, responsibility, adoption, repair, path adjustment, and the next valid action.

## Request Envelope

Every request is one JSON object with exactly these fields:

```json
{
  "protocol": "tplan.collaboration.command.v1",
  "action": "enable",
  "mission_id": "mission-id",
  "command_id": "stable-command-id",
  "expected_build_hash": "sha256:...",
  "expected_snapshot": {
    "mission_digest": "sha256:...",
    "evidence_digest": "sha256:..."
  },
  "payload": {}
}
```

`snapshot.get`, `command.get`, and `runtime.recover` use `expected_snapshot: null`. Other actions require the exact snapshot returned by `snapshot.get`. The CLI also requires a bounded principal string. Principal is an audit identity, never an authorization claim. Unknown fields, duplicate keys, non-finite numbers, invalid IDs, requests over 16 KiB, and action-specific shape errors are rejected before mutation.

## Canonical State

`mission.json.collaboration` is optional. When enabled it has schema `tplan.collaboration.v0.1` and these canonical collections:

- `coordinator`: thread/host reference, responsibility, authorization references, and positive handoff generation.
- `participants`: participant ID to ordinary thread/host reference, responsibility, and authorization references.
- `delegations`: stable delegation identity, existing task, round, assignee, write scope, contract version, instruction digest, input/dependency references, required review, send/execution facts, and derived status.
- `intents`: stable send intent, target, instruction digest, `prepared/confirmed/unknown/not_sent` fact, execution fact, native references, and observed time.
- `feedback`: immutable source identity and content digest, source references, optional task/delegation/round/contract association, summary, original/attachment references, pending or resolved state, and association gap.
- `adoptions`: current adopted artifact per delegation, bound to round, contract version, artifact reference, and content digest.
- `reviews`: review history bound to feedback, reviewer, delegation, round, contract version, artifact reference/digest, scope, verdict, and rationale. History is append-only.
- `coordination`: `working/waiting_external/awaiting_owner`, focus task, objective-gap summary, next action, resume basis, waiting set, and update time.
- `commands`: bounded command replay records with request digest and committed result.

Mission objective, acceptance, task state, and H1/Q2 stores remain in their existing canonical locations. No collaboration command may create a second task tree, acceptance authority, Owner signer, scheduler, or delivery database.

## Actions

Every action below also accepts the exact common envelope. Mutating payloads after `enable` require `coordinator_generation` matching the current generation.

### `enable`

Payload fields are exact: `coordinator`, `participants`, `policy`.

- `coordinator`: `thread_ref`, `host_ref`, `responsibility`, `communication_authorization_refs`.
- `participants`: bounded list of `participant_id`, `thread_ref`, `host_ref`, `responsibility`, `communication_authorization_refs`.
- `policy`: optional `max_pending_feedback` (default 128, maximum 1024) and `processing_deadline_seconds` (default 900, maximum 604800).

The command adds the collaboration object and command result atomically. It preserves Mission objective, acceptance, tasks, and `active_task_id`. It requires at least one non-empty communication authorization reference. An existing collaboration object is not overwritten.

### `delegation.prepare`

Payload fields are exact: `coordinator_generation`, `delegation_id`, `intent_id`, `task_id`, `round`, `assignee_id`, `write_scope`, `contract_version`, `instruction_summary`, `input_refs`, `dependency_versions`, `required_review`.

- The task must exist and not be terminal. The assignee must be a configured participant.
- `required_review` is `{required, reviewer_id, scope_refs}`. A required review names a configured participant and non-empty scope references.
- The instruction summary is one line of at most 2048 characters; the input/dependency references are bounded strings.
- A new execution is rejected while the same task or write scope has a physically in-flight execution (intent prepared/confirmed/unknown and not stopped/completed/failed). Business adoption or repair does not release a still-running scope; reconcile or stop the original execution first.
- A new delegation round must strictly succeed prior rounds for the same task (monotonic succession); lower or equal rounds are rejected. The current effective delegation is the latest legitimate successor, never an older round chosen by numeric max alone.
- The command creates one `prepared` intent and leaves the A focus unchanged. It does not send a message.

### `dispatch.record`

Payload fields are exact: `coordinator_generation`, `intent_id`, `send_state`, `execution_state`, `stop_requested`, `native_refs`, `observed_at`, `reason`.

- `send_state` is `prepared/confirmed/unknown/not_sent`; `execution_state` is `not_started/running/stopped/completed/failed/unknown`.
- `confirmed` requires at least one native message/request reference. `unknown` explicitly means the send result is unresolved.
- `unknown` may later become `confirmed` or `not_sent`; it never implies non-execution. A `not_sent` intent may be followed by a new intent. A confirmed or unknown execution remains protected until a later native observation records stopped/completed/failed.
- The command records facts only. It does not send, retry, cancel, or claim external completion.

### `feedback.record`

Payload fields are exact: `coordinator_generation`, `source_event_ref`, `source_thread_ref`, `source_host_ref`, `source_role_id`, `delegation_id`, `round`, `contract_version`, `artifact_ref`, `artifact_digest`, `summary`, `original_ref`, `attachment_refs`, plus optional `kind` (`progress/result/review/blocker/question`, default `progress`). `kind` only controls Pulse visibility/routing; ordinary progress does not redirect the mainline and it never decides adoption.

- `source_event_ref` is unique. Re-recording the same source with the same content digest is a no-effect replay; the same source with different content conflicts.
- A missing delegation/round/contract association produces `needs_association`; A must ask a targeted question and may continue independent work. The runtime never guesses the task.
- A linked record must match the delegation round and contract. A feedback for a completed task is allowed and enters the same pending queue.
- The command never completes a task, changes focus, adopts an artifact, or writes acceptance evidence. At the configured pending capacity it refuses the new record and retains all existing facts.

### `feedback.resolve`

Payload fields are exact: `coordinator_generation`, `feedback_id`, `disposition`, `goal_relation`, `evidence_refs`, `artifact_ref`, `review`, `task_changes`, `new_tasks`, `next_delegation`, `coordination`.

- `disposition` is `answered/adopted/repair/deferred/evidence_requested/path_adjusted/out_of_scope`.
- `goal_relation` is `{responsibility, acceptance_ids, rationale}` and records A's judgment about how the input relates to the current objective and duty. It never rewrites Mission objective or acceptance.
- `artifact_ref` is optional `{ref,digest,contract_version,round}`. Adoption requires it and a linked delegation whose current round and contract match. A later artifact replaces only the current adoption; earlier feedback and reviews remain history.
- `review` is optional and uses the current feedback source plus `reviewer_id`, `delegation_id`, `round`, `contract_version`, `artifact_ref`, `artifact_digest`, `scope_refs`, `verdict`, `rationale`. The review must match the source feedback own delegation/round/contract/artifact and the configured reviewer binding; it cannot be transplanted to another delegation. A review never adopts an artifact by itself. The latest effective review for the current adopted artifact governs completion; a later FAIL blocks until a bounded repair/re-review PASS or explicit disposition.
- `task_changes` may transition existing tasks through the existing status rules using a focus-preserving helper. `new_tasks` are normalized by the existing task contract before this transaction. A repair of an already completed task requires at least one bounded success-critical repair task.
- `next_delegation` has the same shape as `delegation.prepare` minus `coordinator_generation`. It is committed in the same transaction.
- `coordination` has the checkpoint shape below and is required so A records the next valid action after resolution.
- The feedback is marked resolved, its disposition and A's rationale are stored, and all requested adoption/review/task/intent/focus effects commit in one existing journal transaction. Evidence references must resolve against the current evidence stream before any persistent write.

### `coordination.checkpoint`

Payload fields are exact: `coordinator_generation`, `state`, `focus_task_id`, `gap_summary`, `next_action`, `resume_basis`, `waiting_on`, `rationale`.

- `state` is `working/waiting_external/awaiting_owner`.
- `focus_task_id` must be an existing non-terminal task when supplied; the command intentionally updates `active_task_id`.
- `gap_summary` and `next_action` are one-line bounded summaries. `resume_basis` is a bounded list of task/evidence/feedback/artifact references.
- `waiting_on` entries are `{kind, ref, condition}` with kind `delegation/feedback/owner`. External and owner wait states require at least one waiting entry.
- Objective and acceptance remain unchanged. Normal external waiting does not set Mission `requires_human`.

### `coordinator.handoff`

Payload fields are exact: `coordinator_generation`, `coordinator`, `rationale`.

The new coordinator has the same fields as `enable.coordinator`. The command increments generation and records the prior generation. All later collaboration mutations require the new generation. A host that can enforce writer binding must do so; the ordinary protocol records the required writer generation and rejects stale commands at the runtime.

### Read actions

- `snapshot.get` returns the existing Mission survey plus collaboration state, a short resume projection, and current `expected_snapshot`.
- `command.get` returns the historical committed command result. A missing result proves only that this store has no such command identity.
- `runtime.recover` is the explicit original-writer recovery route for an interrupted canonical transaction. It rolls forward only the already-prepared Mission, trace, evidence, Guard, and transaction contents, then reports the matching command result when present.

## Atomicity, Replay, Recovery, And Capacity

- All mutations hold `execution_trace_lock`, reject an open Guard, validate runtime identity and Mission-directory identity, reject pending transactions until explicit original-writer recovery, re-read the exact before-state, validate all references, then call `_commit_mission_state_unlocked` with the original journal/recovery path.
- A command record and all business effects commit together. Same command ID with the same request/principal digest returns the stored result without a second effect, including after the current revision advances. Different content or principal conflicts.
- Public `write_mission` and `commit_mission_state` preserve an existing collaboration object and reject creation, removal, or modification because they lack the internal collaboration authority token. The token is never accepted from CLI.
- H1-controlled task IDs are not mutated through this command. H1 adoption/nonce/acceptance actor fields and Q2 `command_results` remain untouched.
- Mission/evidence/trace artifacts are limited to 4 MiB each; command retention is 1024 records/1 MiB; summaries are 2048 characters; requests are 16 KiB. Capacity checks run before journal preparation and refuse new facts without deleting existing ones.
- Completion requires no pending collaboration feedback, current adoption for every delegated task, required review PASS for the currently adopted artifact, completed success-critical tasks, and existing qualified acceptance. Historical reviews and failed observations remain readable.

## T01-T29 Evidence Map

| Case | Mechanical or behavior evidence | Primary source |
| --- | --- | --- |
| T01 | Pending feedback is collected while a different task is active; focus is preserved. | `test_collaboration_runtime.py`, Pulse integration test |
| T02 | Source identity/content replay and conflict. | `feedback.record` runtime tests |
| T03 | Current adoption h2 rejects a late h1 PASS as completion evidence. | version-binding tests |
| T04 | Contract clarification is recorded as path/contract disposition with distinct input refs. | resolve and behavior replay |
| T05 | Implementation defect and design defect produce bounded repair/path actions. | resolve/new-task tests and replay |
| T06 | Waiting state, unresolved intents, and resume projection survive restart. | checkpoint/query tests |
| T07 | Unknown send remains protected and cannot create same-scope dispatch. | dispatch reconciliation tests |
| T08 | Guard rejects import before writes; replay after resolution occurs once. | Guard test |
| T09 | Waiting/dependency state does not force a stale task; an independent focus may continue. | checkpoint tests and replay |
| T10 | External waiting uses `waiting_external`, not `requires_human` or polling. | checkpoint tests |
| T11 | Peer text cannot select reviewer or PASS; required source/version/scope are checked. | review validation tests |
| T12 | Transaction roll-forward, capacity refusal, and replay preserve one business effect. | crash/capacity tests |
| T13 | Task and Mission completion remain blocked without current adoption/review. | completion tests |
| T14 | Stop request plus running fact keeps scope protected until stopped fact. | dispatch tests |
| T15 | Handoff increments generation; stale writer generation is rejected. | handoff tests |
| T16 | Pending feedback is batched into one Pulse candidate and remains visible before closure. | Pulse and behavior replay |
| T17 | Completed-task failure blocks Mission close until bounded repair/review. | completion/new-task tests |
| T18 | Duplicate intent and dispatch request conflict; unknown is queried before any replacement. | dispatch tests |
| T19 | No participant runtime state or Mission write is required by the protocol. | integration fixture plus real-host handoff gap |
| T20 | Natural-language return is stored with source and normalized evidence/scope; runtime fields are optional at source. | feedback tests and replay |
| T21 | Unassociated return remains pending and asks for task/version. | feedback tests |
| T22 | First authorized division enables collaboration without a user mode phrase and preserves state. | enable tests |
| T23 | Reference material alone creates no collaboration record. | controlled source-Agent exercise, REVIEW-R3 |
| T24 | `snapshot.get` reconstructs unresolved responsibilities and next action. | resume projection test |
| T25 | Current-session-only scope creates no delegation; existing facts remain readable. | controlled source-Agent exercise, REVIEW-R3 |
| T26 | Multi-turn unrelated advice is deferred; A continues the objective-relevant task. | controlled source-Agent exercise, REVIEW-R3 |
| T27 | Debug detail is routed back to B; A retains acceptance-level responsibility. | controlled source-Agent exercise, REVIEW-R3 |
| T28 | Repeated progress/audit input is consolidated and A records a target-relevant next result. | controlled source-Agent exercise, REVIEW-R3 |
| T29 | Evidence-backed path revision or explicit user goal change updates affected delegation and next action. | controlled source-Agent exercise, REVIEW-R3; path-adjust runtime test |

T23/T25/T26–T29 have actual source-Agent decisions, tool results and before/after state from the controlled exercise accepted in [REVIEW-R3.md](REVIEW-R3.md) (`controlled_source_agent_exercise`). The R2 preset driver remains `scripted_runtime_scenario`; its earlier ideal-answer replay is `scenario_expectation`. Real peer source, wake-up, host deduplication, cancellation, and protected handoff remain host acceptance items.

## Current acceptance responsibility (A1 convergence)

Retiring an attempt releases physical write-scope occupancy, but the task/contract acceptance obligation persists along explicit succession, repair, or an authorized scope change. One shared projection (`_task_acceptance_findings`) is used by public Task completion, Mission close, and the resume gap view:

- A task with no collaboration delegation history keeps the ordinary path.
- A task with delegation history must have a current valid adopted artifact and the latest required reviewer PASS. If every attempt is retired (not_sent/stopped/failed) and no legal successor exists, the obligation remains open and completion is blocked; it is not skipped as an ordinary task.
- The current delegation is the latest non-retired successor under monotonic rounds. A later FAIL on the current adopted artifact blocks completion until a bounded repair/re-review PASS.
- Each adoption carries an `invalidated` flag. A blocking `repair` on an already accepted current artifact sets `invalidated=true` (history preserved) and creates a `repair_obligations` record linking the source task/delegation to a bounded success-critical repair task and its acceptance IDs.
- A repair obligation is satisfied when **every carried acceptance ID** has `acceptance_passed` as its latest qualified observation in the repair task's own scope. Native evidence validation, globally unique event references, declared task/ancestor AC coverage, and applicable H1 current-source version checks are shared with Mission closure. Evidence-log order determines the latest observation per AC.
- A repair task with delegation history additionally satisfies its current acceptance responsibility: a legal current adopted artifact, an effective adoption, and the latest required reviewer PASS bound to that artifact/round/contract/scope. Retired attempts keep this responsibility until a legal successor or explicit disposition. This review constraint protects the delegated acceptance path; ordinary evidence cannot replace a missing or failed required review. A local repair without delegation history uses the scoped native observations directly.
- Public Task completion, `feedback.resolve` completion, Mission close, `snapshot.get.resume`, and survey resume consume the same evidence snapshot and shared repair projection. Partial AC coverage, a later qualified FAIL, ambiguous references, an unrelated task's PASS, and the source task's old adoption leave the repair obligation open.

## Closed-Mission business write boundary (A2)

When the Mission status is not `active` (completed or any other terminal/closed state), its business results and acceptance keep their completion-time boundary. New collaboration mutations (`enable`, `delegation.prepare`, `dispatch.record`, `feedback.record`, `feedback.resolve`, `coordination.checkpoint`, `coordinator.handoff`) are rejected with `mission_closed`; late facts must be carried by a follow-up Mission or a legal continuation. Read-only `snapshot.get`/`command.get`, historical command replay, and original prepared-transaction recovery remain available and do not change the current adoption or start new business execution.

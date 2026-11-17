# TPlan Collaboration Protocol (packaged)

This is the packaged, install-relative protocol reference for the optional A-side
collaboration runtime. It ships with the Skill; no internal repository document is
required. See [collaboration.md](collaboration.md) for the usage recipe and
[schema.md](schema.md) for the canonical Mission schema.

Only coordinator A runs TPlan. B/C are ordinary conversations. A owns judgment,
acceptance, and the next valid action; the runtime only validates and commits bounded
facts.

## Request envelope

Every request is one JSON object with exactly these fields:

```json
{
  "protocol": "tplan.collaboration.command.v1",
  "action": "enable",
  "mission_id": "mission-id",
  "command_id": "stable-command-id",
  "expected_build_hash": "sha256:<64 hex>",
  "expected_snapshot": {"mission_digest": "sha256:<64 hex>", "evidence_digest": "sha256:<64 hex>"},
  "payload": {}
}
```

- `snapshot.get`, `command.get`, `runtime.recover` use `expected_snapshot: null`.
- Every other action requires the exact `expected_snapshot` returned by the latest
  `snapshot.get` (or by a prior write response). A stale snapshot is rejected.
- `expected_build_hash` is the runtime build hash from the Mission's
  `runtime_provenance.fingerprint.build_hash` (also returned by `snapshot.get`).
- The CLI takes `--mission-dir`, `--principal` (bounded audit identity, not authority),
  and `--request-file` (a JSON file, or `-` for stdin).
- Unknown fields, duplicate keys, non-finite numbers, invalid IDs, and requests over
  16 KiB are rejected before any write.

Write responses return the business result plus a current `expected_snapshot` that
matches the final committed state, so it can be used directly for the next command.
`command.get` returns the stable historical result; replay returns the original result
with a current snapshot.

## Actions and exact payloads

Mutating payloads after `enable` require `coordinator_generation` equal to the current
generation (shown in `snapshot.get`).

### enable
`payload`: `coordinator`, `participants`, `policy`.
- `coordinator`: `thread_ref`, `host_ref`, `responsibility`, `communication_authorization_refs` (non-empty).
- `participants`: list of `participant_id`, `thread_ref`, `host_ref`, `responsibility`, `communication_authorization_refs`.
- `policy`: optional `max_pending_feedback` (default 128, max 1024), `processing_deadline_seconds` (default 900, max 604800).

### delegation.prepare
`payload`: `coordinator_generation`, `delegation_id`, `intent_id`, `task_id`, `round`,
`assignee_id`, `write_scope`, `contract_version`, `instruction_summary`, `input_refs`,
`dependency_versions`, `required_review`.
- Task must exist and be non-terminal; assignee must be a configured participant.
- `required_review`: `{required, reviewer_id, scope_refs}`; required review names a configured reviewer and non-empty scope.
- A new execution is rejected while the same task or write scope has a physically
  in-flight execution (intent prepared/confirmed/unknown and not stopped/completed/failed).
  Business adoption or repair does not release a still-running scope.
- A new delegation round must strictly succeed prior rounds for the same task (monotonic
  succession); lower/equal rounds are rejected. Current responsibility follows the latest
  legitimate successor, not an older round picked by numeric max.
- Creates one `prepared` intent; does not send; preserves A focus.

### dispatch.record
`payload`: `coordinator_generation`, `intent_id`, `send_state`, `execution_state`,
`stop_requested`, `native_refs`, `observed_at`, `reason`.
- `send_state`: `prepared/confirmed/unknown/not_sent`; `execution_state`: `not_started/running/stopped/completed/failed/unknown`.
- `confirmed` needs a native reference; `unknown` never implies non-execution.
- Records facts only; no send/retry/cancel.

### feedback.record
`payload`: `coordinator_generation`, `source_event_ref`, `source_thread_ref`,
`source_host_ref`, `source_role_id`, `delegation_id`, `round`, `contract_version`,
`artifact_ref`, `artifact_digest`, `summary`, `original_ref`, `attachment_refs`, and
optional `kind` (`progress/result/review/blocker/question`, default `progress`).
- `source_event_ref` is unique; same source+content replays without effect, different content conflicts.
- Missing delegation/round/contract association stays `needs_association`; A asks a targeted question.
- `kind` controls Pulse visibility only: ordinary `progress` does not redirect the
  mainline; `blocker` routes to mission review. It never decides adoption.
- Never completes a task, changes focus, or adopts.

### feedback.resolve
`payload`: `coordinator_generation`, `feedback_id`, `disposition`, `goal_relation`,
`evidence_refs`, `artifact_ref`, `review`, `task_changes`, `new_tasks`,
`next_delegation`, `coordination`.
- `disposition`: `answered/adopted/repair/deferred/evidence_requested/path_adjusted/out_of_scope`.
- `goal_relation`: `{responsibility, acceptance_ids, rationale}`; never rewrites objective/acceptance.
- `artifact_ref`: `{ref, digest, contract_version, round}`; adoption requires a linked delegation matching round/contract.
- `review`: `{reviewer_id, delegation_id, round, contract_version, artifact_ref, artifact_digest, scope_refs, verdict, rationale}`.
  The review must match the source feedback's own delegation/round/contract/artifact and
  the configured reviewer binding. The latest effective review for the current adopted
  artifact governs completion; a later FAIL blocks until a bounded repair/re-review PASS.
- `task_changes`: `[{task_id, status}]` via focus-preserving transitions. `new_tasks` are normalized; repairing a completed task needs a bounded success-critical repair task.
- `next_delegation`: `delegation.prepare` shape minus `coordinator_generation`, committed atomically.
- `coordination`: checkpoint shape (below), required.

### coordination.checkpoint
`payload`: `coordinator_generation`, `state`, `focus_task_id`, `gap_summary`,
`next_action`, `resume_basis`, `waiting_on`, `rationale`.
- `state`: `working/waiting_external/awaiting_owner`; focus must be an existing non-terminal task when supplied.
- `waiting_on`: `[{kind, ref, condition}]`, kind `delegation/feedback/owner`; wait states need at least one entry.
- Does not change objective/acceptance; external waiting is not `requires_human`.

### coordinator.handoff
`payload`: `coordinator_generation`, `coordinator`, `rationale`. Increments generation;
later mutations require the new generation.

### Read / recovery
- `snapshot.get`: returns survey, collaboration state, resume projection, and current `expected_snapshot`.
- `command.get`: returns the historical command result.
- `runtime.recover`: rolls forward an interrupted prepared transaction only after the
  request mission_id/build and prepared-state compatibility are verified; a wrong
  request leaves all files and the journal unchanged.

## Cold-start closed loop (worked example)

The packaged script [../scripts/collaboration_example.py](../scripts/collaboration_example.py)
runs this exact loop against a fresh demo Mission using only packaged files:

```bash
python3 skills/tplan/scripts/collaboration_example.py --work-dir /tmp/tplan-collab-demo
```

Sequence: `snapshot.get` -> `enable` -> `delegation.prepare` -> `dispatch.record`
-> `feedback.record` -> `feedback.resolve` (adopt + required review) -> `snapshot.get`
-> `command.get`. Each step uses the previous response's `expected_snapshot`.

Minimal `enable` payload example:

```json
{
  "coordinator": {"thread_ref": "thread-a", "host_ref": "local",
    "responsibility": "Own the user outcome and acceptance",
    "communication_authorization_refs": ["user-turn-1"]},
  "participants": [
    {"participant_id": "B", "thread_ref": "thread-b", "host_ref": "local",
     "responsibility": "Implement bounded work", "communication_authorization_refs": ["user-turn-1"]},
    {"participant_id": "C", "thread_ref": "thread-c", "host_ref": "local",
     "responsibility": "Review current artifacts", "communication_authorization_refs": ["user-turn-1"]}
  ],
  "policy": {"max_pending_feedback": 128, "processing_deadline_seconds": 900}
}
```

## Capacity, replay, recovery

- Requests <= 16 KiB; summaries <= 2048 chars; command retention <= 1024 records / 1 MiB;
  Mission/evidence/trace <= 4 MiB each. Capacity checks include the bytes this transaction
  will append (including new trace records); overflow refuses the new write and keeps
  existing facts readable and recoverable.
- Same command_id + request/principal digest replays the original result; different
  content or principal conflicts.
- An open Interaction Guard blocks writes; import a held peer result once after the
  authorized guard resolution.

## Current acceptance responsibility and closed-Mission boundary

Retiring an attempt releases physical occupancy, but the acceptance obligation persists
along explicit succession/repair/authorized scope change. One shared projection checks
Task completion, Mission close, and resume gaps:

- Delegation history retains acceptance responsibility. Current effective endpoints
  need a valid adopted artifact + latest required reviewer PASS; explicit repair successors
  carry that responsibility per AC below. Retired attempts without a legal successor stay open.
- Each adoption has an `invalidated` flag. A blocking repair preserves history and creates
  an explicit `repair_obligations` edge to a bounded success-critical successor task.
  Current responsibility follows those edges per AC, including repeated repairs of
  completed repair tasks. Each task retains its own ACs and incoming/outgoing obligations.
  A successor carries its declared ACs; uncovered ACs stay with the source task.
- Every applicable successor branch satisfies its whole acceptance contract. Current
  endpoints are completed, with latest qualified `acceptance_passed` for every scoped AC,
  and current adoption plus required reviewer PASS when delegation history exists.
  Native qualification, unique references, task/ancestor coverage and applicable H1
  current-source versions remain shared with Mission closure. Local endpoints use
  scoped native evidence. Intermediate completed/invalidated/feedback records remain history.
- Explicit successors that cover all applicable ACs discharge corresponding upstream
  responsibility. Uncovered ACs, incomplete endpoints, missing/FAIL required review,
  latest qualified FAIL, ambiguous references and another branch's PASS keep it open.
  Every overlapping applicable branch remains required; an internal cyclic path is unresolved.
  This protects declared responsibility continuity and retains ordinary Task scope.
- Task completion (including `feedback.resolve`), Mission close and snapshot/survey resume
  use the same event snapshot and shared current responsibility projection.
- When the Mission is not `active`, new collaboration mutations are rejected with
  `mission_closed`; late facts need a follow-up Mission or legal continuation. Reads,
  historical replay, and prepared-transaction recovery remain available.

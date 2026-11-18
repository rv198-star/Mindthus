# Codex host operations

## Inventory for the target

- Inspect the currently exposed tool contracts before calling external
  operations. Identify the intended host, provider and carrier from the current
  task, including when they differ from the calling chat. Do not fill a remote
  or alternate provider's rows from a local/default catalog. If target identity
  is missing and material, ask for it rather than probing unrelated hosts.
- Prefer the exact host's live App Server
  [`model/list`](https://learn.chatgpt.com/docs/app-server#list-models-modellist)
  with visible items only, the requested `modelProvider` when specified and all
  `nextCursor` pages. Run the helper on the target host. For a known, already
  running target socket, run
  `uv run --no-project --with 'websockets>=12' python <skill-dir>/scripts/model_inventory.py --host <target> --socket <socket>`
  (or Python with that dependency already available). For the local managed
  daemon, `codex app-server daemon version` reports its socket without starting
  it; use that socket only when it is the intended server. For a **CLI target**
  without a socket, use `python3 <skill-dir>/scripts/model_inventory.py --host <target> --cli`
  from the target's working directory/configuration, optionally with
  `--codex-bin <binary>`. Both modes accept `--provider <provider-id>`. A
  separately started CLI App Server is not a desktop or remote inventory.
  The helper reads only the catalog and uses the host's existing access. Keep
  its host, provider scope, observation time and model fields; omit internal
  connection details from shared reports or searches.
- The carrier's published model/effort pairs are a direct source only when its
  tool contract applies to the exact target, including provider and host. If both
  sources apply, take their intersection by model ID and effort; honor carrier
  restrictions even when the App Server lists more. A generic string model
  parameter or a global effort enum gives no supported model/effort pairs. If
  the server is unavailable, a matching, explicit carrier catalog suffices; show
  an unreported default as unknown. If the only reported default lies outside
  the carrier range, choose a supported effort explicitly. If neither source
  suffices, hold dispatch for those roles and name the missing evidence.
- Double-check the published turn-start fields separately from model selection.
  Display names are for readers; supply the exact selector accepted by the
  target tool. A provider alias may not identify the same version on another
  host. Use the reasoned fit for this task when choosing an effort.

## Present the batch and receive authorization

Use a native choice tool exposed in the current mode (such as
`request_user_input` or its asynchronous variant) for a selection within
the tool's option limits. Present all details before opening it. Where the
control cannot fit every alternative, put the remaining choices and “defer” in
the question and accept them through free text. If the control returns before
the user submits, its return is not an answer. A missing or unsupported control
uses a chat reply. Use the chat for any separate communication authorization
required by the host; never use a choice tool prohibited from requesting it.

## Dispatch and reconcile

- **SubAgent:** Use the host's `spawn_agent` (or the equivalent supported in
  this surface). Full-context Codex forks inherit model and reasoning. When
  an explicit override is required, use the disjoint context option
  (`fork_turns: "none"` in the desktop tool), provide the necessary brief and
  references, and use only supported overrides. Observe the active host rules
  on whether delegation is allowed.
- **New independent chat:** Use `create_thread` when the human explicitly
  requested new chats. Resolve the project via `list_projects` if needed and
  verify host and working directory; use a managed worktree only with the
  required explicit authorization. Send the brief as the initial prompt with
  the requested `model`/`thinking`. A ready result gives `threadId`/`hostId`.
  For queued worktree setup, retain `clientThreadId` only as a setup reference
  and resolve it through the host before using tools that require `threadId`.
  Follow the host's chat creation reporting convention. Creation already
  carries the brief; do not send it a second time.
- **Existing chat:** Use `send_message_to_thread` with the authorized recipient's
  exact IDs and supported override fields. Before starting work or changing a
  model, check whether the prior turn has finished. A queued or injected message
  does not switch the model for an in-flight turn. Record the requested model and
  effort separately from the actual pair, which must be verified for that turn
  if the host exposes it. Otherwise mark actual execution as unverified.
- **Follow:** Use bounded `wait_threads` snapshots and cursors for known chat
  IDs, then `read_thread` when evidence is missing or ambiguous. Preserve the
  original intent and a recognizable brief reference. A timeout, transport
  error without a known outcome, or pending creation is unresolved. For a known
  target, reconcile that chat's turns and artifact writes. For creation with no
  usable chat ID, resolve the pending reference or search the original target
  host's chat listing around the attempt, then verify the exact brief in the
  matching chat. Absence from a list alone does not establish non-delivery.
  Keep waiting or escalate the unknown if the host cannot resolve it.
- **Substitute:** Use the agreed sequence only after affirmative evidence of
  refusal/non-delivery or a terminal failed execution and no in-flight writes
  in the scope. Inspect partial artifacts; preserve the brief, authority and
  isolation. Recheck current eligibility as needed, including reviewer
  independence against the actual implementer. The alternate target must itself
  be authorized. Record the failure, attempted and replacement pairs and
  evidence. If the approved alternatives are exhausted, ask about that gap.
  Repair a technical defect with its assigned owner instead of treating it as
  a model service failure.

If a host does not supply the necessary chat operation, present the available
options and missing capability. Do not use shell commands or a different host
to bypass a chat tool's authorization boundary.

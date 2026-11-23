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
  Distinguish direction before sending to a chat that is mid-turn. A
  down-stream message that starts new work or changes model/effort waits for
  the current item to be handed off or disposed and a fresh turn; a peer that
  is briefly idle has not thereby yielded its task. Do not interrupt B's
  active turn with a routine new task. An up-stream message that delivers a
  fixed, already-agreed result may be sent to a busy A once, under the
  executable condition in [Deliver the result back](#deliver-the-result-back).
  Only an authorized interrupt — a real blocker or a substantive conflict
  that cannot wait — may preempt unrelated work; a normal delivery that
  should wait does not enter on that basis.
- **Follow:** When the named hand-off is an authorized delivery event that
  reaches A, A does not need to wait at all: it records the resume condition
  and lets its turn end, and the arriving report is what restarts work. Only
  when the brief's agreed collection is a bounded wait (because no return
  path or wake-up was authorized) does A hold a `wait_threads` with the
  latest cursor, and that wait ends on its declared condition — the
  milestone, the blocker, or its bound — not on every timeout. When that
  bounded wait is exhausted without the declared event, A escalates the
  unknown to the decision owner instead of opening another wait or
  investigating the same item. A wait reads status without sending B a
  message, and an unchanged or progress-only snapshot does not by itself
  justify another wait, a status read, or looking at the same item B owns.
  Do not re-investigate or pre-emptively audit the deliverable while B still
  owns it. Use `read_thread` for the relevant turn when evidence is missing
  or ambiguous. Preserve the original intent and a recognizable brief
  reference. A timeout, a transport error without a known outcome, or a
  pending creation is unresolved — keep it in flight and reconcile the same
  target, as below. For creation with no usable chat ID, resolve the pending
  reference or search the original target host's chat listing around the
  attempt, then verify the exact brief in the matching chat. Absence from a
  list alone does not establish non-delivery. Keep waiting or escalate the
  unknown if the host cannot resolve it.
- **Substitute:** Use the agreed sequence only after affirmative evidence of
  refusal/non-delivery or a terminal failed execution and no in-flight writes
  in the scope. Inspect partial artifacts; preserve the brief, authority and
  isolation. Recheck current eligibility as needed, including reviewer
  independence against the actual implementer. The alternate target must itself
  be authorized. Record the failure, attempted and replacement pairs and
  evidence. If the approved alternatives are exhausted, ask about that gap.
  Repair a technical defect with its assigned owner instead of treating it as
  a model service failure.

## Deliver the result back

The hand-off obligation rides on the first brief, not on B's memory of the
turn. When starting, B leaves a recovery record it can find later — the
native chat/task history it re-enters, or an authorized local work note —
with the round, owner and recipient, the verifiable user-authorization
source, the delivery condition and target, the current revision, and the
last send evidence. After an interruption, compaction or an unrelated
in-between task, B reads that record and the latest instruction before
acting, then picks the row that matches:

| State found | What B does |
| --- | --- |
| Work unfinished | Finish within scope; the handoff stays pending. |
| Revision fixed, send not attempted | Apply the send-or-collect rule below once over the authorized path, then yield. |
| Send attempted, outcome unknown | Verify against the original target; resend only on confirmed non-delivery while authorization holds. |
| Delivery already sent | Do not resend that event; the delivery stands on its round. An earlier milestone or blocker report does not clear it. |

A user pause, cancel or repurpose takes precedence over any pending send.
Read-only reviewers keep the same record in their native chat history; B and
C do not write Mission state or run a scheduler.

An authorized return route is required for either form of send. Send once
if A is waiting for this exact event and the host can surface it reliably,
or if the host guarantees non-disruptive queuing. With no authorized return
path — even when a queue exists — the readable collection path is the only
route. In a valid send the single event is the agreed one, not a new
instruction, so it goes once. When A is busy on something else and a send
would be injected into its turn — or when the effect is unknown — B keeps
the fixed package in place and the agreed collection runs instead: the
first brief names one concrete, bounded collect event that at least one
side is guaranteed to run (for example A collects once its current running
work ends or one bounded wait ends, after B's final reply has left the
package ready). If both sides will end with no reachable wake-up, the brief
says so up front and uses that bounded collection or a declared blocker;
it does not promise a background self-start. Distinguish three send states
— never attempted, received by the host and awaiting disposal, and outcome
unknown (reconcile the original target before resending) — and a pause or
a major conflict needs its own authorization, not a free send.

The same direction rule guards the recipient on the way down. If B is mid-turn
on another item and a new dispatch or a model/effort change arrives, the host
may surface it inside B's active turn; B keeps it as a pending event under its
stable marker, finishes the current item's hand-off, and only executes the
new work on the fresh turn that follows — it does not start a second item
inside the same turn and does not reuse the old turn's model for it. The
sender, on seeing the message delivered or queued, does not resend; on an
unconfirmed outcome it reconciles the original target, then resumes the same
event. Where the host cannot confirm the model or the new turn, follow the
existing rule and mark actual execution unverified rather than guessing.

- **Recipient send:** Under the send-or-collect rule above, when a send is
  authorized and appropriate B's delivery includes exactly one send to A
  (for example `send_message_to_thread` to A's thread id) carrying the
  fixed revision,
  actual verification and results, deviations handled or remaining, and the
  attempt marker (task / round / sender / event / revision), where event is
  one of the brief's agreed kinds — milestone, blocker, delivery or review.
  Before the wake send, B registers that event in the delivery inbox
  (`scripts/dispatch_inbox.py put` — see
  [Inbox, Stop hook and heartbeat fallback](inbox-and-hooks.md)), so the
  send has a durable landing even when it reaches a busy A inside its
  turn. Each agreed event has a stable identity; replaying the same event must not
  re-dispose it, while a milestone or blocker does not clear the still-pending
  delivery. B leaves the attempt marker before sending so an interrupted send
  is still reconcilable, then yields. Routine progress stays inside the
  single delivery event. If the send's outcome is unknown, reconcile the
  original target before retrying rather than sending a second copy.
- **No authorized return:** When the brief cannot name a user-authorized,
  host-supported path back, B leaves the fixed result where A agreed to
  collect it and reports the missing path; A uses the bounded collection
  agreed in the brief instead of expecting a wake-up.

Every send that starts or continues work — down-stream dispatch and
up-stream delivery alike — ends with one receipt check. A successful
send call only proves the message left; the target session may already
be in `systemError` or its new turn may fail within seconds. Take one
`wait_threads` snapshot (`timeoutMs: 0`) right after the send; if it is
inconclusive take one more after roughly 30 seconds, then stop. A new
turn that started and did not fail counts as received; a `systemError`
or a failed turn means unexecuted — the dispatch does not count as
delivered, the agreed fallback (a fresh chat or an authorized alternate
model) takes over, and the pending event stays in the inbox for A's
collection. Record the outcome on the event (`dispatch_inbox.py
confirm`) or in A's dispatch record; see
[Send confirmation](inbox-and-hooks.md#send-confirmation-delivery-receipt).

While a delivery is outstanding, A also needs a wake-up path when its
own turn ends. The dispatch brief records which mechanism applies this
round: when the user-level
[Stop hook](inbox-and-hooks.md#stop-hook) is live (its liveness
timestamp under `.git/dispatch-local/hook-last-run.json` is fresh —
never trust config), the hook reminds A of pending inbox events and
reminds a worker whose closing message shows neither a delivery nor a
blocker. When the hook is not live, A installs one
[heartbeat automation](inbox-and-hooks.md#heartbeat-fallback) on its own
thread; measured on this host the heartbeat is skipped while the target
is mid-turn rather than injected or queued, so it covers the post-turn
gap, not a running turn.

If a host does not supply the necessary chat operation, present the available
options and missing capability. Do not use shell commands or a different host
to bypass a chat tool's authorization boundary.

## Keep follow-ups small

For an authorized continuation of the same role, keep the original brief and
tool results in place. Send the changed facts, artifact version and next
decision as a new message. In a fresh brief, place reusable role, scope and
acceptance text before the round-specific facts; keep the recognizable attempt
marker in that same message. A fresh recipient still needs enough context to
act. Preserve independent review and user-pinned model or effort choices.

Stable prefixes can help [prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching#preserve-conversation-history).
Codex controls the request envelope. For comparable batches, use reported
cached input divided by reported input, and compare total input, uncached
input and model steps per accepted delivery. Keep missing usage unknown.

## Identify a cross-chat message

Every message between chats opens with the sender's name and a full-width
colon, then the content: `<sending chat name>：<what it says>`. Use the
sending chat's human-readable title or its agreed short name. The body after
the colon states the thing itself — name a task, round or version only when
the reader actually needs it, not the destination by rote. There is no type
tag, arrow, recipient field, role code or fixed task ledger — those stay in
the underlying record. A header never reuses or forges the user's identity
and grants no authority. When names collide or span hosts, add a short
distinguisher and keep the stable thread reference for routing; a recipient
with no thread id yet uses the agreed name.

Direct, first dispatch to a new chat (B reads this first):

> 导入修复·协调：请修复导入并验证 101 条记录。

Direct, B's delivery back to A (the up-stream return):

> 导入修复·实现：101 条已全部导入且复测通过，请复审版本 a1b2c3d。

A real relay names the actual sender in front of the colon and the original
provider inside the body, keeping the original text / summary and its event
or version boundary intact, separate from what the relayer adds. It never
presents itself as the original author or as the user; an unknown source
stays unknown.

> 导入修复·协调：实现会话反馈已导入 101 条，请复审版本 a1b2c3d。

Verify the immediate previous hop against the host's own source record when
one exists; if that record conflicts with the displayed header, reconcile the
record first. A header or a relayed summary does not raise the sender's
authority and does not change dispatch, receipt or acceptance idempotence.
Messages that predate this convention keep their native source and the
existing flow.

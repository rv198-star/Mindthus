# Optional A-Side Collaboration

## Core

Only coordinator session A runs TPlan. Participants B and C remain ordinary
conversations: they receive normal work instructions, use their own working methods,
and return normal language. They do not need TPlan, the total Mission directory, or a
shared runtime. A owns the canonical collaboration record, judgments, acceptance, and
the next valid action.

## Mainline

When the user has already authorized an actual division of work, A may enable the
extension without asking for a mode phrase. Do not create collaboration from mere
mentions of another session, reference reading, or unassociated incoming text.

On Codex, use the [Codex adapter](platforms/codex.md#ordinary-multi-session-collaboration)
to enter the installed Dispatch for actual collaboration. Its selection and dispatch
steps use this Mission's existing contract and authority. On other hosts, use the
ordinary host instructions below. Without collaboration, stay on the ordinary
TPlan path.

1. Run `snapshot.get` using the Mission's pinned writer. Start with the resume
   view: compare the objective and acceptance gap with the latest evidence at
   handoff, re-entry or an agreed checkpoint. If work is circling one detail,
   name what the next attempt would establish, change direction or stop.
   Read the relevant intent, feedback, review or guard in full for a decision;
   keep the exact snapshot token for writes. Routine updates need only the
   changed facts and their references.
2. Use `enable` with the coordinator, ordinary participant references, and the exact
   user authorization references.
3. Use `delegation.prepare` for an existing non-terminal task. This records a stable
   intent and does not send anything.
4. Send through the host's existing thread tool. For a one-shot delivery or a
   target whose ID arrives later, use `dispatch.claim` before the host call and
   `dispatch.record` after it, on a runtime that advertises native binding.
   The only send permit is the fresh successful claim. Pending references and
   timeouts stay in flight; confirm from host evidence. A formal thread ref can
   bind a logical participant once. Ordinary known-target hosts may keep their
   existing recording path.
   The first brief to a participant also names the delivery handoff: who the
   fixed revision goes to, when to send it, along which host-supported return
   path this Mission's existing authority covers, who resumes after the send,
   and how A re-enters. It also tells the ordinary participant to keep a
   recoverable record — its native chat/task history or an authorized local
   work note — of the round, recipient, user-authorization source, delivery
   condition, current revision and last send evidence, so a B/C that is
   interrupted, compacted or preempted still completes the pending handoff
   instead of stopping after delivery. Where no authorized return path or
   wake-up exists, the brief names the bounded collection A will use instead.
   A down-stream send opens with a header naming sender and role, recipient
   and role, the dispatch intent and the task / round reference; it waits
   for the participant's current item to be handed off rather than injected
   mid-turn, unless it is an authorized and cannot-wait interrupt or
   substantive conflict.
5. Read B/C replies. An authorized return send to A is the normal delivery
   event that restarts A's turn; it may reach a busy A inside the active turn
   because that hand-off is the recorded resume condition, while a routine
   new dispatch does not. Otherwise A collects through the agreed
   bounded path. Each agreed event keeps its own `source_event_ref` and
   `kind` — a milestone or blocker report is a distinct event from the
   delivery and does not discharge it. Use `feedback.record` to preserve
   source, content digest, optional
   artifact, and task/round/contract association. If an association is missing,
   keep it pending and check the existing intent and native evidence first.
   Batch outstanding questions into one authorized contact when the gap blocks
   a decision. Ordinary progress can wait for the agreed handoff.
6. Judge relevance to the Mission and A's duty. Use `feedback.resolve` with a clear
   disposition, goal relation, evidence references, current artifact, review, bounded
   task changes, optional next intent, and next action. The runtime commits all effects
   together.
7. Record what will resume work in `coordination.checkpoint` and let the
   turn end. While B owns a delivery, A waits for its fixed revision to
   arrive through the agreed path before accepting it or assigning its
   audit; an A that has seen only a milestone or blocker report does not
   accept early. B's ordinary progress and bare wait timeouts do not start a new
   status query or a same-item investigation. A may advance another
   explicitly assigned deliverable. A verified scope conflict or blocker can
   interrupt the affected work before handoff. A bounded collection reconciles
   the original target, an agreed milestone or a real blocker; it is not
   minute-scale polling. Use `coordinator.handoff` when another A session
   becomes responsible.

## Guardrails

- Participant role text and forwarded PASS text are not authority. Required review is
  bound to reviewer, delegation, round, contract, artifact digest, and scope.
- A late PASS for an old artifact remains history. It does not replace the current
  adopted artifact.
- Unknown delivery keeps the original intent protected. Query the same target and do
  not create a second execution for the same task or write scope.
- A user pause, cancel or repurpose wins over a pending delivery. A participant that
  resumes after one acts on the newest instruction, not the stale handoff.
- An open Interaction Guard blocks collaboration writes. The host may hold the peer
  result outside the Mission; import it once after the authorized guard resolution.
- External waiting is not `requires_human`. Record a concrete resume condition instead
  of polling.

## Commands

```bash
python3 skills/tplan/scripts/collaboration_runtime.py \
  --mission-dir MISSION_DIR \
  --principal coordinator-a \
  --request-file /tmp/collaboration-request.json
```

The exact request envelope, action payloads, capacity/replay/recovery rules, and a
worked cold-start example are in the packaged [collaboration-protocol.md](collaboration-protocol.md).
Run the packaged closed loop with only installed files:

```bash
python3 skills/tplan/scripts/collaboration_example.py --work-dir /tmp/tplan-collab-demo
```

Codex-specific host behavior is in [platforms/codex.md](platforms/codex.md).

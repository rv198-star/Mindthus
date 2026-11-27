---
name: codex-dispatch
description: Configure or dispatch a batch of work across Codex chats using live model and reasoning choices, including separate implementation and review chats. Also use for explicit Codex SubAgent model selection. Discussion alone stays advisory; routine work in the current chat needs no dispatch.
---

# Codex Dispatch

## Core Claim

The coordinating chat A proposes a batch the user can choose, sends only the
agreed work, and owns adoption. Each recipient owns its bounded work and brings
evidence and design deviations back with the result through the authorized
return path named in its brief.

## Mainline

At entry, distinguish a standalone batch from a TPlan collaboration handoff.
For the handoff, consume A's existing Mission, pinned writer, snapshot, contract
and authorization using the adapter that invoked this skill. Continue below
in the same coordinator. Reuse an authorized full
choice and any existing intent; reconcile a previously claimed or sent intent.
Prepare, claim and record through that Mission's protocol around the host call
as the adapter directs. Use its record for recovery instead of a
second dispatch log. Do not re-enter TPlan startup or ask for the same choice
again. If the referenced Mission or writer is unavailable, hold the affected
dispatch. A standalone invocation does not open a Mission.

1. **Pick the carrier and read its live inventory first.** Use an in-chat
   SubAgent for a short investigation under the host's delegation rules. Use
   independent Codex chats for sustained design, implementation, repair or
   independent review; prefer a suitable existing chat authorized for contact.
   For configuration or dispatch, first identify the target host, provider and
   carrier per role. Then read [Host operations](references/host-operations.md)
   and obtain its visible model IDs, supported reasoning efforts and defaults.
   Reuse a fresh read across roles only for the same target. Check user-pinned
   choices too. Discussion about delegation stays advisory.
2. **Check fit where it would change the choice.** Define the relevant ability
   for each role (for example, implement a frozen design, trace a cross-module
   bug or independently spot acceptance gaps). Use the user's same-version,
   comparable task experience when available. If a remaining doubt would change
   a role, model, fallback or effort, do one batched online lookup. Use public
   model names and versions and generic ability questions; prefer official
   model cards or release notes, then version- and task-specific evaluations.
   Keep the source link, version and implication. If offline, inconclusive or
   unable to map a private alias, name the remaining unknown and favor candidates
   with better evidence. Search informs fit; the target host determines availability.
3. **Show the whole choice.** Offer two or three materially different viable
   batches, with a recommendation and the trade-off that distinguishes each.
   If only one qualifies, show it and what is missing. For each role, include
   responsibility, primary model and effort, and one or two eligible fallback
   models with their efforts in order (or the shortage). Two efforts on one
   model are one candidate. Preserve user pins and review independence, including
   among fallbacks: if an authorized substitution changes which audit models
   qualify, show the conditions. Show A's current setting when known;
   its alternatives are handoff options, never automatic switches. Show target
   hosts, reuse/new chats, who sends what to whom, writable scope, dependency
   order and when fallback is allowed. An independent audit consumes the fixed
   deliverable version.
4. **Ask once for the batch.** Show the full proposal in chat, then prefer a
   supported native choice control with recommendation, free input and a way
   to defer. Otherwise present the same choices and free reply in chat. State
   what submitting an option will authorize, including the actions and
   conditional fallbacks described above, and the delivery return path each
   recipient will use. Wait for a human submission.
   A preference locks the relevant field; it does not authorize dispatch.
   Validate free edits against the appropriate target and the original
   constraints. An explicit choice (“option 2, B to high, rest as shown,
   start”) suffices if the edited batch still qualifies. If an edit is
   unavailable or requires unseen changes, show the gap and viable choices.
   Cancel, silence, and UI defaults leave the batch unsent. A complete,
   validated instruction with explicit execution and communication authority
   can proceed without asking again.
5. **Dispatch against a fixed brief.** Record intent first. Include the
   objective, baseline and input version, allowed writes, decisions delegated,
   acceptance evidence, delivery location and escalation boundary. Every first
   brief names the delivery handoff contract: who B hands
   the result to, when (fixed revision, agreed milestone or a
   real blocker), along which host-supported return path, who takes over after
   that send, and how A re-enters; B's role and autonomy — strict or the
   default bounded — per
   [session roles](references/batch-handoff.md#session-roles-and-default-boundaries);
   and the [interjection rules](references/human-interjection.md) to apply if
   the user speaks mid-work. The return path's authority comes from the
   user, and the brief points B at the evidence it can verify (for example the
   originating user turn or A's dispatch record) — a brief from A does not by
   itself grant a reply. Reusing a chat reuses the two-way authorization
   already on it; one-direction authority stays one-way. If no authorized
   return path or wake-up exists, name the gap and agree A's bounded
   collection (a declared wait condition, an agreed milestone read, or
   another authorized check-in). The brief also names where B keeps its
   recovery record (its native chat/task history or an authorized local
   work note): round, owner/recipient, user-authorization source, delivery
   condition and target, current revision, last send evidence — so an
   interrupted, compacted or preempted B can still complete the handoff. Use
   approved carrier and model/effort. Send the first brief once; keep the
   native chat/turn references and record A's resume condition. A down-stream
   dispatch waits for a busy peer's hand-off while an up-stream delivery may
   reach a busy A once; messages use the
   [sender-colon form](references/host-operations.md#identify-a-cross-chat-message).
   Hand-off mechanics are in
   [Inbox, Stop hook and heartbeat fallback](references/inbox-and-hooks.md).
   When the user speaks into a session mid-work, apply
   [Human interjection](references/human-interjection.md).

   For the same deliverable the handoff is serial: B implements, self-tests
   and hands over the fixed revision once, then yields the turn. A (or the
   designated C) starts acceptance only after that hand-off arrives, then
   adopts, repairs, forwards for review or sends an already authorized next
   item. A disposes each agreed event once under its stable identity
   (task / round / sender / event / revision); a milestone or blocker report
   does not discharge the pending delivery; an A that has only seen the
   milestone has not accepted.
   While B owns a delivery, A records its resume condition and lets the turn
   end; B's progress, a bare wait timeout, or an unchanged snapshot
   starts no new status query or same-item investigation. A
   replacement chat is only for an errored, unavailable or unrecoverable
   session — context percentage alone never auto-replaces
   ([details](references/batch-handoff.md#replacement-vs-compaction)). Use the
   [host recovery rules](references/host-operations.md#dispatch-and-reconcile)
   for unknown delivery and authorized fallbacks. A bounded collection
   reconciles an original target, an agreed milestone or a real blocker; it
   is not minute-scale polling. For sustained work, agree a
   checkpoint and apply the [drift check](references/batch-handoff.md#check-direction-without-shadowing-b)
   to evidence available there or on re-entry.
6. **Adopt a version and close the design feedback.** Use
   [Batch handoff](references/batch-handoff.md) to collect results and deviations.
   A checks the artifact against the original acceptance conditions. When an
   independent review is required, send the fixed version and original criteria
   to the authorized reviewer, who chooses how to verify them. A review applies
   to that version; a repaired version goes back for review before adoption.

## Guardrails

- The user's confirmed model choices and permission to create or message chats
  are distinct. Preserve existing explicit authority; obtain the missing
  authority if a response only selects models. New recipients, wider write
  scope or looser acceptance require authority for the change. Keep each
  concurrent writer's scope isolated.
- Preserve an unresolved send as in flight for its task and writable scope.
  Establish what happened at the original target before resending or substituting.
  An idle snapshot, time elapsed or a missing tool acknowledgment is insufficient.
- Recipients solve implementation problems within scope and report together at
  delivery. A conflict that changes the objective, shared interface, acceptance,
  or another chat's active dependency pauses the affected work. Surface the
  evidence, impact and decision owner promptly; continue independent work.

## Boundaries

Codex only. Host and collaboration requirements still apply. If the target
inventory or carrier cannot be verified, keep the affected option as a proposal.
There is no standalone scheduler or permanent model catalog.

TPlan is optional. In a TPlan Mission only A manages Mission state, using the
[existing collaboration protocol](../tplan/resources/collaboration-protocol.md)
and [read-only SubAgent rules](../tplan/resources/subagents.md). Attach batch
choices and deviations as supporting material. B/C need only their briefs and
their artifact references; a standalone batch needs no Mission.

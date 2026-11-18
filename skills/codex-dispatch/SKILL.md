---
name: codex-dispatch
description: Configure or dispatch a batch of work across Codex chats using live model and reasoning choices, including separate implementation and review chats. Also use for explicit Codex SubAgent model selection. Discussion alone stays advisory; routine work in the current chat needs no dispatch.
---

# Codex Dispatch

## Core Claim

The coordinating chat A proposes a batch the user can choose, sends only the
agreed work, and owns adoption. Each recipient owns its bounded work and brings
evidence and design deviations back with the result.

## Mainline

1. **Pick the carrier and read its live inventory first.** Use an in-chat
   SubAgent for a short investigation under the host's delegation rules. Use
   independent Codex chats for sustained design, implementation, repair or
   independent review; prefer a suitable existing chat authorized for contact.
   For configuration or dispatch, first identify the target host, provider and
   carrier for each role. Then read [Host operations](references/host-operations.md)
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
   qualify, show the applicable conditions. Show A's current setting when known;
   its alternatives are handoff options, never automatic switches. Show target
   hosts, reuse/new chats, who sends what to whom, writable scope, dependency
   order and when fallback is allowed. An independent audit consumes the fixed
   deliverable version.
4. **Ask once for the batch.** Show the full proposal in chat, then prefer a
   supported native choice control with recommendation, free input and a way
   to defer. Otherwise present the same choices and free reply in chat. State
   what submitting an option will authorize, including the actions and
   conditional fallbacks described above. Wait for a human submission.
   A preference locks the relevant field; it does not authorize dispatch.
   Validate free edits against the appropriate target and the original
   constraints. An explicit choice such as “option 2, B to high, rest as shown,
   start” is sufficient if the edited batch still qualifies. If an edit is
   unavailable or requires unseen changes, show the gap and viable choices.
   Cancel, silence, and UI defaults leave the batch unsent. A complete,
   validated instruction with explicit execution and communication authority
   can proceed without asking again.
5. **Dispatch against a fixed brief.** Record intent before acting. Include the
   objective, baseline and input version, allowed writes, decisions delegated,
   acceptance evidence, delivery location and escalation boundary. Use the
   approved carrier and requested model/effort. Send the first brief only once;
   keep the native chat/turn references. Continue independent work while recipients
   execute. Use the [host recovery rules](references/host-operations.md#dispatch-and-reconcile)
   for unknown delivery and authorized fallbacks. A normally reads recipients'
   results; no routine messages or acknowledgments are needed.
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

# Batch handoff

## A: record the intent and the result

In an existing task document or this chat's batch record, keep the approved
roles, target/model/effort and fallback order, user authorization reference,
baseline and acceptance conditions, and recognizable intent reference. Attach
native chat/turn or pending setup references and observed outcomes as they are
available. For each artifact record the specific revision (commit, digest or
other stable reference), actual tests and any acceptance gap. Link independent
review evidence to the same revision and criteria. If a revision changes, mark
its prior verdict historical and get a review of the new version.

A delivery arriving through the authorized return path is one event: accept,
send for repair or review, or dispatch an already authorized next item
against that version once. Events are keyed by task / round / sender / event
/ revision, so replaying the same event does not dispose it twice. A
milestone or blocker report is not the delivery: an A that has seen only a
milestone keeps the acceptance open and does not start it early, and a late
duplicate or older revision stays history on its original round.

With TPlan, read the existing [collaboration protocol](../../tplan/resources/collaboration-protocol.md).
A prepares the intent before sending, records the native dispatch outcome, and
associates feedback with the current round, contract and artifact before adopting,
repairing or waiting. Keep model choices and deviations in linked materials,
not a second Mission state. For read-only investigations use TPlan's established
SubAgent restrictions. No separate runtime is required for standalone use.

### Check direction without shadowing B

For sustained work, put one observable checkpoint in the brief: a versioned
intermediate result, a dependency decision or a resource limit already agreed
with the user. At that point, on re-entry, or when reported evidence conflicts
with the design, A compares the original goal to the gap that actually closed.
When work stays on one detail without new evidence, pause that path and identify
a discriminating check, a simpler route or a decision for the design owner.

B can do this check locally while working. A uses available evidence and waits
for the agreed event if nothing requires a decision; elapsed time alone is a
reason to check the waiting condition, not to ask B for a status report. If
scope, authority or another deliverable is at risk, contact the owner once with
the evidence and decision needed. Acceptance still uses B's handed-off revision.

## B/C: execute, verify, report

Read the fixed baseline and verify it against reality. Choose the approach,
investigate, repair and verify within the brief. A straightforward correction
to conform to the agreed design is normal work. An actual discrepancy with
the design belongs in the batch:

| Baseline and expectation | Observed difference and evidence | Action and verification | Proposed design disposition |
| --- | --- | --- | --- |
| Design expects one response to cover all items | Sample contains a continuation cursor | Read to an empty cursor; cross-page case passed | Update the read path and coverage check in the next design revision |

If an observation forces a change to the objective, shared contract, acceptance
or another active dependency, promptly surface the facts, evidence, impacted
work and decision needed. Hold only that portion and carry on with independent
work. Use an explicitly authorized communication path; otherwise make the
blocker visible in the recipient chat for A to read. Do not treat an incoming
delegation as permission to send a message back.

Return the fixed artifact, evidence, unresolved items and deviation rows in
one delivery. Where the brief named an authorized return path, use the
return-or-collection route named in the brief, carrying the
attempt marker; then yield the turn instead of waiting for a prompt. An
agreed milestone or a real blocker is its own send with its own event
marker — reporting one does not discharge the delivery, and the same
revision is still owed afterwards. Routine troubleshooting stays inside the
delivery send. A or the designated designer marks each row updated (version
and location) or kept as a local exception (reason and scope), and carries
applicable changes into the next brief and review. Replaying an already sent
event stays history; do not re-report the same event, and do not skip the
delivery because an earlier milestone or blocker went out.

### First-brief template B can act on

A usable first brief for a new or reused B/C carries the hand-off and the
recovery record B should keep, in a form an ordinary chat can follow
verbatim:

```text
<协调会话名>：请按 <基线版本> 完成 <具体工作>，并验证 <验收条件>。
You are B; A is <A-thread-id>. Attempt marker <attempt-ref>.
Objective / baseline / writable scope: … Acceptance evidence: …
On fixing the revision, keep the package at <agreed location>. Use the
user-authorized return route once when A is ready for this event or the
host guarantees non-disruptive queuing. If a send would interrupt
unrelated work or its effect is unknown, leave the package there;
<named collector> collects at <reachable bounded event>. Include
<event marker>, revision, checks, deviations and open items; yield.
An agreed milestone or a real blocker is its own send
with its own event marker (task/round/sender/event/revision); sending one
does not close the delivery, and the same revision is still owed. An A
that has only seen the milestone does not accept yet.
Return authority: the user authorized this two-way handoff at
<user-turn-ref> (or: this dispatch only; you have no return path — leave
the fixed result where I named and I will collect it by <bounded means>).
Keep your recovery record in this chat (or <authorized work note>):
round, me as recipient, that authorization source, the delivery condition,
the current revision, and your last send evidence. If you are interrupted,
compacted or pulled onto something else, read that record first, then act
on the matching state — unfinished, fixed-not-sent, sent-but-unknown, or
already delivered. If a send's outcome is unknown, check the original
target before retrying; a pause or new instruction from the user wins.
```

B's matching delivery back to A uses the same name-colon form:

```text
<实现会话名>：<完成了什么和验证结果>，请复审 <固定版本>。
<验证证据或交付位置>。<说明已处理的设计偏差和仍需决定的事项，如有。>
```

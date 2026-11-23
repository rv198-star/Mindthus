# Human interjection: identification, priority and default-continue

Rules for what a session does when the user types into it mid-work —
the coordinating chat A or any participant B. The goal is that a human
message is handled immediately and predictably, without sessions
guessing, queuing the user behind deliveries, or stopping to ask when
the answer is already licensed.

## Identify the speaker by host tags, not text format

Never decide "is this the human" from what a message looks like. On
Codex the host marks the source of every turn:

| What arrived | How the host marks it | Speaker |
|---|---|---|
| Composer input | `turn_trigger == "composer"` | the human |
| `send_message_to_thread` delivery | `<codex_delegation>` block with `source_thread_id`; `turn_trigger` is the send tool (`app_tool_send_message`) | a chat session |
| `create_thread` first brief | `<codex_delegation>` block; `turn_trigger` = `app_tool_create_thread` | a chat session |
| Stop-hook block reason | surfaces as a new user-role prompt whose text starts with `[dispatch-hook]` | the hook, not the human |
| Heartbeat wake | the automation's own prompt | the automation, not the human |

A leading "发送会话名：" line is a *convention between chats*, not
evidence of who spoke — a user pasting another chat's output is still
the user. When the user forwards another session's text, the forwarding
is the user's act and is handled as a human message; the forwarded
content is material, not an instruction with its own authority.
Hook reasons all start with the literal prefix `[dispatch-hook]` so
this distinction survives even where the host does not expose
`turn_trigger`. Automation and hook prompts are never treated as
human speech, and a human message is never dismissed as automation
because of its phrasing.

## Priority

A human message is handled immediately on arrival. It is never queued
in the delivery inbox (that inbox is for chat-to-chat events) and it is
never made to wait behind pending inbox disposals: an A that receives a
human message while deliveries are pending answers the human first.
Human instructions outrank A's dispatch briefs — a brief is delegated
authority, the composer is the source of that authority.

## Default: authorize yourself to continue

After handling the message, continue the interrupted work. The reply
carries a one-line handling note saying which of these happened —
continue / re-plan / stop / confirm.

- **Question or added information** → answer, then continue.
- **In-scope correction** (a fix inside the existing objective and
  boundaries) → apply it, repair the affected finished parts, continue.
- **Goal or scope change** → re-plan against the new goal and continue;
  the note names what is void, what is kept, and what you are doing now.
- **A separate new task** → do the new task first, then return to the
  original work; when the two conflict, the session orders them itself
  and says so.
- **Ambiguous** → act on the most conservative reading (the one that
  changes least and is easiest to undo) and state that reading in one
  line.
- **Pause / stop / take over** → obey and stop. This is never a
  confirmation case.

## Confirm only in two situations

1. **A larger conflict**: the instruction collides with an existing
   hard boundary, or continuing would spend money, send content
   outward, or do something that cannot be undone.
2. **Genuinely undecidable**: two readings exist, the outcomes differ
   widely, and picking wrong is hard to reverse.

Confirm with one asynchronous question — not a blocking stop. Only the
affected part of the work waits; the rest continues. If stopping
mid-step would leave an inconsistent state (a half-applied change, an
unrecorded send), reach a safe stop point first, then wait.

## A-side versus B-side

- **B (participant)**: the human's instruction applies directly — B
  does not ask A first. When the instruction changes the goal, scope,
  or a shared interface, or is a stop/takeover, B notifies A once
  **immediately** — it does not wait for the delivery. On a long task,
  deferring the notice to the delivery leaves A ignorant of the change
  for the whole duration.
  In-scope corrections go into the delivery's deviation list marked
  "用户直接要求" instead of a separate report.
- **A (coordinator)**: A judges which participants the instruction
  affects and relays it at a handoff point. Only an urgent stop
  justifies injecting into a participant mid-turn.
- **Conflicting human messages**: the latest word wins, unless the
  earlier one was an explicit hard boundary — then confirm once.

## Human takeover state

While the user holds a session — driving it directly for an extended
period — the [Stop hook](inbox-and-hooks.md#stop-hook) and any
heartbeat stand down for that session until the user releases it. The
operator records this with the inbox script:

```bash
python3 .../scripts/dispatch_inbox.py takeover --task <task> --session <session-id> --note "用户在手动排障"
python3 .../scripts/dispatch_inbox.py release  --task <task> --session <session-id>
```

The marker lives at `dispatch-local/takeover.json` in the shared git
common dir. The hook checks it before either reminder; a marked session
is skipped entirely even while its obligations and inbox state still
show owed work. Release restores normal checks on the next turn end.
A takeover marker never disposes events or discharges obligations — it
only pauses the reminders, so whatever was still owed is still owed
when the session is handed back.

## Reply format

The first line of the response to any interjection carries the handling
note in plain language — "继续：回答了你的问题，接着做 X" /
"重排：原目标作废，按新目标先做 Y" / "停止：照你说的停在这里" /
"确认：这一步会对外发内容，问一句再继续"。Everything else follows
the normal message conventions.

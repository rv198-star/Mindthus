# Inbox, Stop hook and heartbeat fallback

This reference covers the three mechanisms that make a cross-chat handoff
reliable even when the receiving chat is busy, errored or silent:

- the **delivery inbox** under `.git/dispatch-local/<task>/inbox/`,
- the user-level **Stop hook** in `~/.codex/hooks.json`, and
- the **heartbeat automation** that covers the gap when the hook is not
  actually running.

It also fixes two known failure modes: a send that reports success while
the target turn failed (send confirmation), and a busy A that nobody
re-checks after the turn ends (inbox + hook + heartbeat).

## Delivery inbox

A delivery event is registered before the wake-up send. The script is
`skills/codex-dispatch/scripts/dispatch_inbox.py`.

```bash
# B registers its delivery for task "import-fix", round r1
python3 skills/codex-dispatch/scripts/dispatch_inbox.py put \
  --task import-fix --round r1 --sender "导入修复·实现" \
  --event delivery --revision a1b2c3d \
  --summary "101 条已全部导入且复测通过，请复审"

# A lists what is waiting (pending only by default)
python3 skills/codex-dispatch/scripts/dispatch_inbox.py list --task import-fix

# A marks the event disposed exactly once
python3 skills/codex-dispatch/scripts/dispatch_inbox.py done \
  --task import-fix --key import-fix__r1__导入修复·实现__delivery__a1b2c3d
```

Events live under the repository's **common** git dir
(`git rev-parse --git-common-dir`), so every worktree of one repo shares
the inbox and it never enters the index. Outside a repo pass `--base-dir`.

An event's stable identity is task / round / sender / event / revision —
the same attempt marker the first brief names. `put` on an existing key
returns `duplicate` (still pending) or `already_processed` (already
disposed); it never overwrites. `done` moves the event to `processed/`
once; a second `done` reports `already_processed`. A milestone or a
blocker is a distinct event key from the delivery, so registering one
does not clear the still-pending delivery.

The reader's rule matches the send rule: when a delivery message reaches
a busy A, A registers nothing extra — the sender already wrote the event
— and disposes it once the current item finishes. Each event is disposed
once.

### Send confirmation (delivery receipt)

`send_message_to_thread` returning `isError:false` only proves the
message left the sender. The recipient's session may already be in
`systemError`, or its next turn may fail within seconds — the dispatch
then never ran. Every send that starts or continues work therefore ends
with **one** receipt check, not a poll:

1. Right after the send, take one `wait_threads` snapshot
   (`timeoutMs: 0`) of the target. If the snapshot is inconclusive, take
   one more after roughly 30 seconds, then stop checking.
2. If a new turn started and did not fail, record
   `confirm --outcome received` on the event (or in A's dispatch record).
3. If the target shows `systemError` or its new turn failed, record
   `confirm --outcome unexecuted`. The dispatch does **not** count as
   delivered: follow the agreed fallback (a fresh chat or an authorized
   alternate model), and keep the event pending so A's collection path
   still finds it.
4. If neither check resolves it, `confirm --outcome unknown` and keep
   reconciling the same target — never resend a second copy while the
   first send's outcome is unresolved.

The confirmation is recorded on the event itself
(`dispatch_inbox.py confirm`) or in A's dispatch record; either way it is
the evidence that "sent" became "received".

## Stop hook

`skills/codex-dispatch/scripts/dispatch_stop_hook.py` is a Codex Stop
hook. When enabled it runs at the end of every turn and:

- writes a liveness timestamp to
  `<git-common-dir>/dispatch-local/hook-last-run.json` (or a cache/home
  fallback outside a repo);
- exits through `stop_hook_active` — a turn the hook already continued
  once is allowed to end;
- blocks once with a reminder when the repo's `dispatch-local` has
  pending inbox events (the local A still owes disposals), or when the
  repo participates in dispatch and `last_assistant_message` shows
  neither a delivery report nor a blocker note (the worker may have
  finished without its authorized return send).

The worker-side check is heuristic and gated: it only runs in repos that
already have a `dispatch-local/*/inbox` tree, and `stop_hook_active`
caps it at one interruption per turn.

### Installation (user does this)

The hook is opt-in at user scope. Add the command to
`~/.codex/hooks.json`, merging into `hooks.Stop` alongside any existing
entries. Enabling the hook and trusting the script's path are the user's
decision — this skill ships the script and the shape only.

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 <skills-dir>/codex-dispatch/scripts/dispatch_stop_hook.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Restart Codex after editing. Any command hook that exits non-zero or
prints invalid JSON fails closed: Codex marks the hook run failed and
the turn ends normally.

## Liveness detection

Never trust the config file. At dispatch time, check the timestamp the
hook itself writes:

- `<git-common-dir>/dispatch-local/hook-last-run.json` exists and
  `ran_at` is recent (fresh within the dispatch's expected window) →
  the hook is live; the brief records "hook check" as this round's
  receipt mechanism.
- The file is missing or stale → the hook is not running for this repo;
  the brief records "heartbeat check" and A installs the fallback below.

## Heartbeat fallback

When the Stop hook is not live, A gives itself one heartbeat automation
(default every 30 minutes, attached to A's own thread) that does only
three things per wake:

1. If the inbox has pending events → dispose them now.
2. If the inbox is empty but B's thread already ended its turn without
   a delivery event → remind B once to send its authorized return.
3. If nothing changed since the last wake → end immediately.

A deletes the heartbeat when the inbox is drained and no B owes a
return, or when the task ends. One heartbeat per outstanding dispatch —
not a standing schedule.

### What a heartbeat does while A is running

Measured on this host (2026-11-24, thread heartbeat every minute
against a session running `sleep 240` for a full 260-second turn):
the heartbeat did **not** inject into the in-flight turn — the turn's
items show no heartbeat input at all — and the due fire was **not**
queued. The next fire landed only after the turn completed, as a fresh
turn of its own. In other words a heartbeat whose target is busy is
skipped for that fire, exactly like a missed cron tick; it cannot
interrupt a running A and does not stack up.

That shapes the rule. The heartbeat covers the gap where A already
ended its turn with pending inbox work or a B that finished without
returning — not a long-running A. The wake prompt stays deliberately
thin for the same reason: at each fire A does the three steps above
and ends. With the default 30-minute interval the worst-case blind
window for a leaked delivery is one interval, which the brief should
state.

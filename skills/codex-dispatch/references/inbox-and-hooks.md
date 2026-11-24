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
# At dispatch time A records the round's return obligation once
python3 skills/codex-dispatch/scripts/dispatch_inbox.py bind \
  --task import-fix --round r1 \
  --worker <B-session-id> --recipient <A-session-id>

# B registers its delivery, naming the session that will collect it
python3 skills/codex-dispatch/scripts/dispatch_inbox.py put \
  --task import-fix --round r1 --sender "导入修复·实现" \
  --event delivery --revision a1b2c3d \
  --recipient <A-session-id> \
  --summary "101 条已全部导入且复测通过，请复审"

# A lists what is waiting (pending only by default)
python3 skills/codex-dispatch/scripts/dispatch_inbox.py list --task import-fix

# A parks an event it is deliberately not handling yet
python3 skills/codex-dispatch/scripts/dispatch_inbox.py defer \
  --task import-fix --key <key> --reason "等用户拍板"

# A marks the event disposed exactly once — only the named recipient may
python3 skills/codex-dispatch/scripts/dispatch_inbox.py done \
  --task import-fix --key import-fix__r1__导入修复·实现__delivery__a1b2c3d
```

Events live under the repository's **common** git dir
(`git rev-parse --git-common-dir`), so every worktree of one repo shares
the inbox and it never enters the index. Outside a repo pass `--base-dir`.

### Sessions, not replies, decide who owes what

Because one repo hosts several sessions, events and obligations carry
session ids and the Stop hook checks those — never the text of a reply:

- **`bind`** records the round's return obligation once at dispatch time
  (task / round / worker session / recipient session / expected kinds).
- **`put`** names the event's `recipient` session id. Only that session
  is reminded of pending work, and only it may `done` the event (a
  `--force` override exists for the operator). A session that merely
  shares the repo is not interrupted and cannot steal someone else's
  disposal.
- **`defer`** parks an event A is deliberately not handling yet — for
  example while waiting on the user — so the Stop hook does not re-block
  every turn; `resume` un-parks it.
- **`discharge`** closes an obligation after its delivery (or blocker)
  event has been registered; an obligation for round N is not satisfied
  by round N−1's delivery.
- **`takeover` / `release`** mark and clear the repo-wide
  `dispatch-local/takeover.json` record of a session the user is
  holding; see
  [Human interjection](human-interjection.md#human-takeover-state).
  While marked, hook and heartbeat stand down for that session.

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
once. `done` refused for a wrong session or an unknown key exits
non-zero (3), so a refusal cannot be mistaken for a disposal.

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
- blocks once with a reminder only when the repo's `dispatch-local`
  binds work to *this* session id:
  pending non-deferred inbox events whose `recipient` is this session
  (the local A still owes disposal), or an open obligation whose
  `worker` is this session and whose expected event kind has not been
  registered for its round (the worker may have finished without its
  return send). Sessions with neither binding are never interrupted,
  even in a repo that takes part in dispatch.
- skips a session recorded in `dispatch-local/takeover.json` — while
  the user holds that session the hook stays silent for it
  ([Human interjection](human-interjection.md#human-takeover-state)).

Every block reason starts with the literal prefix `[dispatch-hook]`.
Codex surfaces the reason as a new user-role prompt, and that prefix is
what keeps the interjection rules from mistaking the reminder for
something the human typed — see
[Human interjection](human-interjection.md#identify-the-speaker-by-host-tags-not-text-format).

Because the inbox sits in the shared `.git`, an early version of this
hook reminded every session in the repo — a wrong session could then
mark A's delivery processed and lose it. Binding every event and
obligation to a session id is what keeps the reminder pointed at the
right owner.

### Installation (user does this)

The hook is opt-in at user scope. Three steps: add the entry, confirm
trust, then verify it is actually running. Enabling the hook and
trusting it are the user's decision — this skill ships the script and
the shape only.

**Step 1 — add the entry.** Merge this block into `hooks.Stop` in
`~/.codex/hooks.json` (if `CODEX_HOME` is set elsewhere, the file is
`$CODEX_HOME/hooks.json`). Keep any existing hook entries — do not
overwrite them:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/bin/sh -c 'f=$(ls -d "$HOME"/.codex/plugins/cache/mindthus/mindthus/*/skills/codex-dispatch/scripts/dispatch_stop_hook.py 2>/dev/null | sort -V | tail -n 1); if [ -n "$f" ]; then exec /opt/homebrew/opt/python@3.13/bin/python3.13 "$f"; else echo "{}"; fi'",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

This command resolves the newest installed Mindthus plugin copy at run
time, so it survives plugin upgrades — no version to fill in, no edit
and no re-trust needed after an upgrade. If no installed copy is found
it prints `{}` and the turn ends normally, so the hook never wedges a
turn on a missing path.

The interpreter in the example is the user's own Homebrew Python 3.13 —
substitute your machine's equivalent. The script requires **Python 3.10
or newer** (it uses `X | None` annotations): on 3.9 it exits with a
SyntaxError and Codex silently treats the run as failed, which looks
exactly like "hook not installed" — the liveness check below is how you
tell. If the hook does not appear in Codex's hook list after saving,
restart Codex once; an entry that is listed needs no restart.

**Step 2 — confirm trust.** Codex only runs hooks the user has
confirmed. On the desktop app use the Review hooks prompt by the
composer or Settings > Hooks; on the CLI use `/hooks`. An unconfirmed
hook is skipped. Official doc: https://learn.chatgpt.com/docs/hooks

**Step 3 — verify it runs.** Have any session end a turn inside a repo
that takes part in dispatch, then read
`<git-common-dir>/dispatch-local/hook-last-run.json`. A fresh record
with a real `session_id` and `hook_event_name: "Stop"` means the
hook is live; anything else (missing file, stale `ran_at`, no
`session_id`) means it is not and the heartbeat fallback applies —
see [Liveness detection](#liveness-detection).

Any command hook that exits non-zero or prints invalid JSON fails
closed: Codex marks the hook run failed and the turn ends normally.

## Liveness detection

Never trust the config file. At dispatch time, check the timestamp the
hook itself writes:

- `<git-common-dir>/dispatch-local/hook-last-run.json` exists,
  `ran_at` is recent (fresh within the dispatch's expected window),
  **and** the record carries a real `session_id` with
  `hook_event_name: "Stop"` → the hook is live; the brief records
  "hook check" as this round's receipt mechanism. The hook only writes
  liveness for genuine Stop runs, so a `session_id`-less or
  differently-named record — a unit test, a manual probe, an older
  script version — does not count and should be treated as stale.
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

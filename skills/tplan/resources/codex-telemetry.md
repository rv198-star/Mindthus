# TPlan Codex Telemetry Adapter

## Core

The optional Codex adapter improves future execution fidelity without changing the
Mission task tree. It writes ordinary `script`, `tool`, `model`, and `agent_turn`
spans into `execution_trace.jsonl`; Standard/Audit consume those spans through the
existing execution-cost renderer.

It cannot repair a historical trace. Missing hooks or OTel events remain visible as
`not_reported` and do not upgrade lifecycle coverage from partial to exact.

## Explicit Binding

Bind one Codex session to one canonical Mission before installing hooks:

```bash
mkdir -p HOST_PROTECTED_STATE_DIR
python3 skills/tplan/scripts/generate_codex_telemetry_hooks.py MISSION_DIR \
  --state-dir HOST_PROTECTED_STATE_DIR \
  --session-id CODEX_SESSION_ID \
  --output /tmp/tplan-codex-telemetry-hooks.json
```

Add `--thread-id CODEX_THREAD_ID` when the OTel delivery path has a distinct stable
thread identity. Hook attribution still requires the exact `session_id` supplied by
Codex. OTel then requires both the session and thread binding.

The state directory must already exist and must be outside the Mission. Rebinding to a
different identity is refused unless the operator passes `--replace`. The adapter also
checks Mission id, canonical path, and runtime provenance.

Binding and generating a hook file do not prove that Codex loaded or trusted that
file. Local-tool and SubAgent coverage therefore remains `not_reported` until the
adapter observes a callback. A callback without a completed start/stop pair reports
`available_not_observed`; only a completed pair reports `observed`.

## Codex CLI Installation And Preflight

For a non-interactive `codex exec` run, merge the generated `hooks` object into an
active, trusted **user** hook layer (normally `~/.codex/hooks.json`) before creating
the session. Preserve unrelated hooks. A project-local `.codex/hooks.json` is valid
only when Codex actually discovers that project layer; do not treat a path on disk, a
`trust_level` override, or `--dangerously-bypass-hook-trust` as proof that the source
is active.

Before the first measured tool call, inspect Codex's Hooks manager (or the app-server
`hooks/list` endpoint). The intended source path and every required handler must be
listed as enabled; review/trust the exact command hash, or use
`--dangerously-bypass-hook-trust` only for a controlled one-off E2E. If the source is
not listed, stop: the expected result is `not_reported`, not a telemetry defect in the
adapter.

When a fresh session ID is not known yet, generate the hook config with a temporary
safe session id, install and preflight that unchanged config, create a no-tool
bootstrap session, then rebind the host state with the real session ID before the
first tool call:

```bash
python3 skills/tplan/scripts/codex_telemetry_adapter.py bind MISSION_DIR \
  --state-dir HOST_PROTECTED_STATE_DIR \
  --session-id REAL_CODEX_SESSION_ID --replace
```

The hook command itself does not carry the session ID, so this rebind does not change
the installed hook definition; it updates host-protected state and refreshes the
Mission coverage sidecar. Remove the temporary user hook after the recorded session
ends.

A hook with a wrong session writes no span and returns ordinary hook success so optional
telemetry cannot block the user's tool. A correctly bound event is attributed:

- `exact` only when one real `active_task_id` is active at lifecycle start;
- `mission_overhead` when the Mission is exact but no real active node is available;
- never to a guessed task.

Post events keep the attribution captured by their paired start even if the active node
changes later.

## Hook Normalization

| Codex event | Trace result | Correlation |
| --- | --- | --- |
| `PreToolUse` + `PostToolUse` for `Bash` | paired `script` span | `tool_use_id` |
| other observable local tool pair | paired `tool` span | `tool_use_id` |
| `SubagentStart` + `SubagentStop` | paired `agent_turn` envelope | `agent_id` |
| hosted tool | `not_reported` | no current hook surface |

Parallel SubAgents receive distinct hashed span IDs and retain overlapping measured
intervals. They never create Task/SubTask/Step records. `agent_turn` is an audit
envelope: its duration remains visible, but the renderer excludes it from additive
resource time and it carries no Token usage. The `Agent`/`spawn_agent` tool event is
ignored in favor of SubAgent lifecycle hooks to avoid double reporting.

Start without stop remains an open span. Stop without start is not converted to a
zero-duration span; the capability report records an unpaired event instead.
Start/stop correlation also requires the same `turn_id` and the same sanitized tool
class or SubAgent type. Reuse of an ID across a different turn or class is rejected as
an identity mismatch and does not close the original span.

`PostToolUse` can run after a failed command and its `tool_response` shape is not a
universal status contract. The adapter therefore records `ok` or `error` only for a
`Bash` response containing an integer `exit_code`; all other hook-derived completion
statuses are `unknown`. Output text and the rest of `tool_response` are discarded.

Codex requires a successful `SubagentStop` command hook to return valid JSON on stdout.
The adapter emits `{}` for that host-facing protocol while keeping its internal
capture result private. Other hook events remain silent unless `--print-result` is
used for local diagnostics.

Codex hook coverage is not universal. Current official documentation states that local
shell, patch, and MCP/function tools can emit pre/post hooks, while hosted tools do not;
later `write_stdin` input can be delivered with the original tool's post event, and
specialized paths may opt out. See the
[official Codex hooks reference](https://learn.chatgpt.com/docs/hooks).

## Optional OTel Projection

Codex OTel is opt-in. TPlan does not ingest raw OTLP payloads because those can include
prompts, output snippets, command details, or ambiguous event identity. A trusted host
must first project one event into this narrow JSON schema:

```json
{
  "schema_version": "tplan.codex_otel_event.v0.1",
  "event_id": "otel-event-1",
  "session_id": "session-1",
  "thread_id": "thread-1",
  "turn_id": "turn-1",
  "record_type": "model",
  "task_id": "T1",
  "started_at": "2026-07-24T10:00:00Z",
  "finished_at": "2026-07-24T10:00:02Z",
  "duration_ms": 2000,
  "status": "ok",
  "source_event": "codex.api_request",
  "model": "gpt-5",
  "usage": {
    "input_tokens": 120,
    "cached_input_tokens": 20,
    "output_tokens": 30
  }
}
```

Ingest it through stdin:

```bash
python3 skills/tplan/scripts/codex_telemetry_adapter.py ingest-otel MISSION_DIR \
  --state-dir HOST_PROTECTED_STATE_DIR < sanitized-codex-otel-event.json
```

Allowed `record_type` values are `model`, `agent_turn`, and `tool`. Only `model` may
carry Token usage. A requested task is exact only when hook observations for that
`turn_id` name exactly that one task and contain no Mission-overhead interval; otherwise
the OTel span stays at `mission_overhead`. A wrong session/thread is rejected.

`source_event` is an exact allowlist, not an arbitrary label:

- `model`: `codex.api_request`, `codex.sse_event`,
  `codex.websocket_request`, or `codex.websocket_event`;
- `agent_turn`: `codex.turn.e2e_duration`;
- `tool`: `codex.tool_result`.

Unknown or decorated values are rejected so source metadata cannot become a
raw-content side channel.

If a tool `tool_use_id` already exists in hook state, the OTel tool event is
deduplicated and the hook pair wins. OTel `event_id` is idempotent. Turn envelopes do
not own model Tokens and are not added to nested model/tool resource time.

Codex documents opt-in OTel logs and metrics for API requests, tool results, turn
duration, Token usage, and multi-agent operations. User prompts are redacted by
default unless explicitly enabled, but TPlan still requires the narrow sanitized
projection above. See
[official Codex observability and telemetry](https://learn.chatgpt.com/docs/config-file/config-advanced#observability-and-telemetry).

## Privacy Boundary

Hook delivery may contain `tool_input`, `tool_response`, transcript paths, and the last
assistant message. The adapter reads only lifecycle IDs, event class, and sanitized
timing metadata; raw fields are discarded before any write.

The OTel projection rejects unsupported fields and explicit prompt, response, content,
command-argument, transcript, stdout/stderr, environment, secret, and connector-payload
fields. Trace output contains only hashed correlation IDs, safe operation classes,
numeric timing/usage, status, attribution, and allowed metadata. Raw Codex
binding/correlation IDs remain only in the host-state file; Mission and task IDs follow
the normal trace schema.

## Capability And Degradation Report

The adapter writes:

```text
MISSION_DIR/reports/codex-telemetry-coverage.json
```

It reports binding state and separate coverage for local tools, hosted tools,
model/turns, Tokens, waits, and SubAgents, plus dedupe and diagnostic counters. Read it
directly with:

```bash
python3 skills/tplan/scripts/codex_telemetry_adapter.py capabilities MISSION_DIR \
  --state-dir HOST_PROTECTED_STATE_DIR
```

The execution-cost JSON exposes the same sidecar as top-level `telemetry_capture`.
Standard/Audit render every channel and its reason without changing one-to-one Mission
hierarchy. An unreadable, stale, or cross-Mission sidecar degrades to `not_reported`;
it does not prevent the rest of the execution tree from rendering.

## Boundary

This adapter is measurement support, not acceptance evidence, Mission authority, or a
completion signal. It does not make Codex hooks universal, infer model time from an
Agent envelope, split ambiguous time across tasks, or claim historical completeness.

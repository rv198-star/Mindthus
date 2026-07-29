# TPlan Codex Telemetry Adapter

## Core

The optional Codex adapter improves future execution fidelity without changing the
Mission task tree. It writes ordinary `script`, `tool`, `model`, and `agent_turn`
spans into `execution_trace.jsonl`; Standard/Audit consume those spans through the
existing execution-cost renderer.

It cannot repair a historical trace. Missing hooks or OTel events remain visible as
`not_reported` and do not upgrade lifecycle coverage from partial to exact.

## Explicit Binding

Choose one persistent host-controlled dispatcher state directory per Codex profile and
reuse it across Missions. Bind one Codex session to one canonical Mission:

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

The state directory must already exist and must be outside every Mission. Do not create
a new dispatcher state directory per Mission: its canonical path is part of the stable
hook command. Rebinding to a different identity is refused unless the operator passes
`--replace`. The adapter also checks Mission id, canonical path, and runtime
provenance.

The generated hook definition contains only the stable dispatcher script and this
persistent state directory. It contains no Mission path, session id, or thread id.
Raw session ids live only in
`tplan-codex-telemetry-registry.json` inside the host-controlled state directory,
where the dispatcher maps one exact session to one Mission binding generation. Thus a
new Mission updates the registry without changing Codex's trusted hook-definition
hash. One session cannot be routed to two Missions or silently moved with `--replace`;
clean the previous Mission route before reusing that session for a new Mission.

Binding and generating a hook file do not prove that Codex loaded or trusted that
file. New generated bindings therefore require activation preflight before hook
callbacks may write telemetry. Local-tool and SubAgent coverage remains
`not_reported`; a callback without a completed start/stop pair reports
`available_not_observed` / `callback_unpaired`, and only a completed pair reports
`observed`.

## Install, Preflight, Rebind, And Cleanup

Use the lifecycle helper instead of copying one generated file over an existing hook
source. It merges only TPlan's four handlers and preserves unrelated hooks:

```bash
python3 skills/tplan/scripts/codex_telemetry_activation.py install MISSION_DIR \
  --state-dir HOST_PROTECTED_STATE_DIR \
  --surface codex_cli \
  --source-scope user \
  --source-path ~/.codex/hooks.json
```

Use `--surface codex_app` for the App. Use `--source-scope project` plus the
repository's exact `.codex/hooks.json` path to test project discovery separately.
Project trust is only a prerequisite; it is not discovery, hook trust, or activation
evidence.

Before the first measured tool call, run host inventory preflight:

```bash
python3 skills/tplan/scripts/codex_telemetry_activation.py preflight MISSION_DIR \
  --state-dir HOST_PROTECTED_STATE_DIR \
  --surface codex_cli \
  --source-scope user \
  --source-path ~/.codex/hooks.json \
  --cwd PROJECT_ROOT
```

The CLI path starts the selected Codex binary's app-server, completes its
`initialize` handshake, calls `hooks/list`, and records the CLI version and app-server
user agent. The sidecar records a non-secret binding generation rather than the raw
Codex session/thread identifiers; replacing the binding increments that generation.
App integrations must provide an App-exported inventory with
`--inventory-json`; `codex_app` never falls back to a separately spawned CLI
app-server. It also requires concrete `--host-build` evidence unless the inventory
envelope already contains `host_build`. Do not label CLI inventory as App evidence.

The exported App envelope is deliberately narrow:

```json
{
  "host_build": "Codex App <concrete build>",
  "initialize": {
    "userAgent": "<app-server initialize result>",
    "platformFamily": "unix",
    "platformOs": "macos"
  },
  "hooks_list": {
    "data": []
  }
}
```

`hooks_list` is the unmodified `hooks/list` result. Warnings, errors, commands, and
other inventory fields are inspected in memory but only hashes, source metadata,
trust/enabled state, and build evidence enter the Mission sidecar.

Preflight succeeds only when the exact source path is enumerated and all four stable
dispatcher handlers have current hashes, trusted or managed trust state, and
`enabled=true`. Mission/session correctness remains separately constrained by the
host registry and binding generation. Preflight records one of:

- `source_absent`
- `source_not_enumerated`
- `needs_trust` (including a modified/hash-mismatched handler)
- `disabled`
- `binding_mismatch`
- `inventory_unavailable`
- `ready`
- `callback_unpaired`
- `observed`

Every non-ready preflight fails closed and keeps hook telemetry `not_reported`.
Hosted tools, model/turn timing, Token usage, and distinct waits remain separate
platform-boundary statuses; they are not activation failures.

When a fresh session ID is not known yet, generate the stable hook config with a
temporary safe session id, install and preflight that unchanged config, create a
no-tool bootstrap session, then run the generator again with the real session ID
before the first measured tool call:

```bash
python3 skills/tplan/scripts/generate_codex_telemetry_hooks.py MISSION_DIR \
  --state-dir HOST_PROTECTED_STATE_DIR \
  --session-id REAL_CODEX_SESSION_ID \
  --replace \
  --output /tmp/tplan-codex-telemetry-hooks.json
```

The hook command carries neither session nor Mission identity, so this rebind and
registry update do not change the installed hook definition. A replaced binding is
nevertheless marked `binding_mismatch` until preflight re-runs against the new binding
generation.

After the recorded session ends, clean up through the lifecycle helper:

```bash
python3 skills/tplan/scripts/codex_telemetry_activation.py cleanup MISSION_DIR \
  --state-dir HOST_PROTECTED_STATE_DIR
```

Default cleanup removes this Mission's registry route, binding state, and coverage
sidecar, but retains the stable trusted dispatcher for future Missions. With no route,
callbacks from unrelated sessions fail closed and write nothing.

To uninstall the dispatcher as well, request it explicitly:

```bash
python3 skills/tplan/scripts/codex_telemetry_activation.py cleanup MISSION_DIR \
  --state-dir HOST_PROTECTED_STATE_DIR \
  --remove-dispatcher
```

If all Missions were already cleaned with the default reusable behavior, uninstall
without an old Mission binding:

```bash
python3 skills/tplan/scripts/codex_telemetry_activation.py uninstall \
  --state-dir HOST_PROTECTED_STATE_DIR
```

Dispatcher removal runs only when no other Mission bindings remain.
It removes only the exact TPlan handlers, preserves unrelated hooks, and removes a
source created solely by TPlan when it becomes empty. Codex may retain a historical
host-owned trust hash. An empty dispatcher registry is deleted, and no absent source
or stale Mission claim is represented as active.

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
Standard consolidates absent channels into one Mission-level coverage statement and
shows only observed or explicitly unavailable node metrics. Audit renders every channel
and its reason, plus the App/CLI build, source path/hash, enumeration, trust, and
enabled state from coverage schema `tplan.codex_telemetry_coverage.v0.2`. Neither
changes the one-to-one Mission hierarchy. An unreadable, stale, or cross-Mission
sidecar degrades to `not_reported`; it does not prevent the rest of the execution tree
from rendering.

## Boundary

This adapter is measurement support, not acceptance evidence, Mission authority, or a
completion signal. It does not make Codex hooks universal, infer model time from an
Agent envelope, split ambiguous time across tasks, or claim historical completeness.

# TPlan Actual Execution & Cost Tree Design

Status: implemented on feature branch; release-line validation pending
Date: 2026-07-18
Issue: https://github.com/rv198-star/Mindthus/issues/121

## What This Gives The User

After a Mission, TPlan can render the route that was actually taken as a tree. Each
visible node can show its observed state, execution order, active time, retries,
result, AI/model time, script/tool time, and Token usage. The default view stays small;
an audit view retains the full trace when it is needed.

The report distinguishes three clocks instead of producing one misleading number:

- end-to-end elapsed time: wall time for the Mission or node lifecycle
- resource time by kind: the sum of model, script, tool, wait, or agent-turn spans
- Token usage: platform-reported input/output usage, with cached input and reasoning
  output shown as subsets rather than added twice

Resource time may exceed wall time when work is nested or parallel. Unknown data remains
unknown; the renderer does not estimate missing measurements.

## Release-Line Contract

This is one Shared Product Core feature for both release lines:

- `1.X Stable` receives the feature on the current `tplan.v0.1` Mission schema.
- `2.X Beta` consumes the same trace and report implementation, without a Beta-only
  fork or a second schema.
- The existing `mission.json` schema version does not change. Telemetry lives in an
  additive sidecar, so legacy Mission state remains readable.
- Compatibility is proved by applying the same feature diff to an isolated Beta
  worktree and running the Beta suite. A frozen evaluation branch is not mutated.

If a future Beta runtime profile changes orchestration, it may provide a richer adapter,
but it must emit this shared trace contract rather than introduce a divergent report
format.

## Runtime Files

Each newly initialized Mission adds:

```text
execution_trace.jsonl
reports/
```

`execution_trace.jsonl` is an append-only logical event stream with schema version
`tplan.execution_trace.v0.1`. `reports/` holds generated Markdown or JSON reports.

This stream is deliberately separate from `evidence.jsonl`:

- trace answers what ran, when, and at what observed cost
- evidence constrains acceptance and semantic claims
- logs hold local process detail and recovery notes

Recording a successful script span does not prove that the script result satisfies an
acceptance criterion.

## Lifecycle Events

The runtime records:

- `mission_initialized`
- `node_added`
- `task_status_changed`
- `active_node_changed`
- `mission_status_changed`
- `span_completed`

State-changing runtime entry points commit lifecycle records together with the matching
Mission mutation. Related records share a `commit_id`. The implementation writes the
trace first, rolls it back if the Mission write fails, and only then refreshes the
narrative view.

Legacy direct state mutation is not treated as exact history. If tracing starts after
initialization, report coverage is `partial`.

## Cost Span Contract

A `span_completed` record contains:

```json
{
  "schema_version": "tplan.execution_trace.v0.1",
  "event_type": "span_completed",
  "mission_id": "mission-id",
  "task_id": "T1",
  "span": {
    "span_id": "SP...",
    "parent_span_id": null,
    "kind": "model",
    "label": "model inference",
    "status": "ok",
    "measurement_source": "platform_reported",
    "attribution": "exact",
    "started_at": "2026-07-18T10:00:00Z",
    "finished_at": "2026-07-18T10:00:02Z",
    "duration_ms": 2000,
    "attempt": 1
  },
  "usage": {
    "input_tokens": 1200,
    "cached_input_tokens": 400,
    "output_tokens": 300,
    "reasoning_output_tokens": 80
  },
  "usage_source": "platform_reported",
  "refs": {}
}
```

Allowed span kinds are `model`, `agent_turn`, `script`, `tool`, `wait`, and `runtime`.
Measurement source is explicit: `platform_reported`, `host_measured`, `inferred`, or
`unavailable`. Time and Token sources are independent: `span.measurement_source`
describes duration, while `usage_source` describes Token fields.

Attribution is also explicit:

- `exact`: one task owns the span
- `shared`: the span names at least two tasks but is kept in a shared-cost bucket
- `mission_overhead`: Mission-level work such as final reporting
- `unattributed`: observed cost whose owner cannot be established

Shared and uncertain cost is never silently divided between tasks.

## Collection Paths

The shared core supplies three collection surfaces:

1. Lifecycle scripts capture task-tree and state mutations automatically.
2. `record_execution_span.py` ingests sanitized platform-reported model/Agent timing
   and Token usage.
3. `run_traced_command.py` measures script/tool wall time around a real command while
   inheriting its output and deliberately not storing command arguments, stdout, or
   stderr.

Platform adapters should report the strongest observable source they have. They must
not convert an absent Token field into zero or infer provider time from prose.

## Progressive Tree Views

The renderer supports:

- `compact`: Mission plus root Tasks, or a focused node plus its direct children
- `standard`: root Tasks plus abnormal, retried, dynamic, outcome-bearing, active,
  error, and top-cost descendants; this is the default
- `audit`: every node, complete status history, direct/inclusive cost, and stable refs

The declared parent-child tree remains the layout backbone. Actual execution order is a
node annotation, not a second set of edges, so the diagram remains readable. Subtree
cost is rolled up to ancestors. Shared/Mission/unattributed cost appears separately.

The renderer emits Markdown with Mermaid or structured JSON. `--focus TASK_ID` narrows
the tree without changing the underlying trace.

## Coverage And Legacy Behavior

Every report declares one of:

- `exact`: tracing began at `mission_initialized`
- `partial`: trace records exist, but the Mission predates them
- `snapshot_only`: no trace exists; only current task state is shown

`exact` describes lifecycle trace coverage, not omniscient cost collection. The report
also states that cost covers `reported_spans_only`.

## Privacy Boundary

The trace accepts safe labels, numeric measurements, narrow metadata, and artifact or
evidence references. It rejects raw-content fields such as prompt, response, command,
arguments, stdout, stderr, environment, credentials, and secrets.

The command wrapper does not capture output and does not serialize its command line.
Platform adapters must summarize an operation class rather than copy prompts or model
responses into a label.

## Control Boundary

The runtime controls event shape, legal references, clocks, attribution fields,
rollups, privacy rejection, and view selection. The platform or agent supplies observed
measurements and a safe operation label. Evidence or human review still determines
whether a result is true, acceptable, or worth acting on.

## Acceptance Matrix

- initialization creates the trace and report directory without touching evidence
- dynamic nodes and lifecycle changes produce linked trace records
- model, script, Token, cached Token, and shared overhead roll up correctly
- compact/standard/audit views expose progressively more nodes
- privacy-sensitive fields fail before append
- legacy Mission runtimes render `partial` or `snapshot_only` without invented cost
- the command wrapper records exit status and elapsed time but no command/output text
- existing 1.X Stable TPlan tests pass
- the identical feature change passes in an isolated 2.X Beta worktree

## Non-Goals

- provider billing or currency estimates
- semantic scoring of task results
- full distributed tracing across machines
- allocation of shared cost by arbitrary percentages
- automatic proof that all model or tool activity was observed
- a dense always-expanded diagram

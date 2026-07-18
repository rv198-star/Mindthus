# TPlan Actual Execution & Cost Tree Design

Status: revised implementation complete; 1.x verified; queued for the next 2.x shared-core checkpoint
Date: 2026-07-18
Issue: https://github.com/rv198-star/Mindthus/issues/121

## Verification And Release Disposition

- 1.x Stable-based branch: 194 TPlan tests and 625 full-repository tests pass.
- The same revised implementation applies to the Beta2 source without conflict, and
  all 194 TPlan tests pass there.
- The current Beta2 release profile deliberately freezes the 1.4.6 `skills/tplan`
  digest. Its package gate rejects the changed live tree as evaluation-identity drift.
- The frozen reference lock, protocols, receipts, and evaluation evidence are unchanged.
  This feature enters 2.x at the next checkpoint after `shared_core_ref` is separated
  from `evaluation_baseline_ref`; the compatibility branch is not a republished Beta2.
- A deterministic simulated campaign-readiness Mission completed in 12m06s with 27/27
  real nodes, one withdrawn SubTask, 5m31s script time, 1m15s wait time, 15s tool time,
  approximately 1m08s cumulative LLM-call time, and estimated Token usage visibly
  marked with `≈`.
- A follow-up replenishment Mission completed in 4m58.705s with 24/24 real nodes and
  15/15 paired spans: 1m20.066s caller-measured model-call stubs, 2m35.581s scripts,
  35.139s tools, and 25.012s wait. Exact interval coverage was 4m55.802s and elapsed
  not exactly recorded was 2.903s, which reconciles exactly to Mission elapsed. One
  failed supplier-term check and its successful retry remained visible on the same
  real Step. The controlled model-call stubs validate host instrumentation mechanics;
  they do not claim a live Codex/provider integration.

## What This Gives The User

After a Mission, TPlan can render the route that was actually taken as a tree. Each
visible node can show its observed state, execution order, actual elapsed time,
retries, result, cumulative LLM-call time, script/tool/wait time, elapsed time not
exactly recorded, and Token usage.

Task structure and information density are separate concerns. Every rendered Mission,
Task, SubTask, or Step maps to exactly one real TPlan node. The renderer never merges
nodes at any level and never inserts display-only grouping nodes. `compact` may omit
real nodes only when it declares itself as a projection and reports the hidden count.
The default `standard` view preserves the complete materialized hierarchy while
limiting the fields inside each node; `audit` adds detailed trace information without
changing that hierarchy.

The report distinguishes three clocks instead of producing one misleading number:

- end-to-end elapsed time: natural time from observed start to finish for the Mission
  or node lifecycle
- resource time by kind: the sum of model-call, script, tool, wait, or agent-turn spans
- Token usage: platform-reported input/output usage, with cached input and reasoning
  output shown as subsets rather than added twice

Resource time may exceed actual elapsed time when work is nested or parallel. Unknown
data remains unknown; the renderer does not estimate missing measurements.

When lifecycle coverage is exact, the report also partitions actual elapsed time using interval
union rather than resource-time addition:

```text
actual elapsed = exact interval coverage + elapsed not exactly recorded
```

For model spans, `host_measured` means caller-visible request elapsed at the SDK/API
boundary. It can include provider queueing, network transfer, internal retries, and
streaming, so it must not be presented as pure provider-internal inference time.
`platform_reported` retains the platform adapter's stated definition, while `inferred`
is visibly estimated. The uncovered elapsed remainder is not automatically model,
script, or orchestration time.

An `agent_turn` is an orchestration envelope that may include model, script, tool, and
wait spans. It is never labeled as cumulative LLM-call time or added to its nested spans. A
platform-reported duration whose Mission or node scope is unknown remains an external
audit observation and does not enter node reconciliation.

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
- `span_started`
- `span_completed`

State-changing runtime entry points commit lifecycle records together with the matching
Mission mutation. Related records share a `commit_id`. The implementation writes the
trace first, rolls it back if the Mission write fails, and only then refreshes the
narrative view.

Legacy direct state mutation is not treated as exact history. If tracing starts after
initialization, report coverage is `partial`.

## Cost Span Contract

A host observer emits a `span_started` entry marker before the real operation and a
`span_completed` record after it. Both share one `span_id`. The completed record owns
the authoritative `started_at`, `finished_at`, and monotonic `duration_ms`, so trace I/O
does not enter the measurement. An unmatched start remains an open/interrupted span and
does not enter cost totals. Standalone completions remain valid for after-the-fact
platform ingestion and compatibility.

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

The shared core supplies four collection surfaces:

1. Lifecycle scripts capture task-tree and state mutations automatically.
2. `ModelCallObserver` in `observe_model_call.py` writes paired entry/completion events
   and measures the caller-visible SDK operation with a host monotonic clock.
3. `record_execution_span.py` ingests sanitized platform-reported model/Agent timing
   and Token usage.
4. `run_traced_command.py` measures script/tool elapsed time around a real command while
   inheriting its output and deliberately not storing command arguments, stdout, or
   stderr.

Platform adapters should report the strongest observable source they have. They must
not convert an absent Token field into zero or infer provider time from prose.

## Progressive Tree Views

### Structure-Fidelity Invariant

The renderer must preserve node identity before optimizing display density:

1. Every rendered Mission, Task, SubTask, and Step maps to one real runtime node.
2. No renderer view merges task nodes at any hierarchy level.
3. No renderer view invents grouping, summary, rollup, or layout-only task nodes.
4. A view may omit real nodes only when it is explicitly labeled as a projection and
   reports how many nodes are hidden; omission never changes the remaining node IDs.
5. Large trees may be split into several Mermaid diagrams at real Task boundaries, but
   the diagrams together preserve every node and declared parent-child edge.
6. Execution spans remain cost/detail records inside a real node. They do not replace,
   merge, or synthesize Mission task nodes.

The renderer supports:

- `compact`: Mission plus real root Tasks, or a focused real subtree. Hidden nodes are
  counted explicitly; no synthetic descendant-summary node is created.
- `standard`: every materialized Task, SubTask, and Step with a strict node-label
  budget; this is the default post-completion execution tree.
- `audit`: the same complete topology plus status history, direct/inclusive cost,
  spans, measurement sources, and stable refs.

The declared parent-child tree remains the layout backbone. Actual execution order is a
node annotation, not a second set of edges, so the diagram remains readable. Subtree
cost is rolled up to ancestors without replacing descendants. Shared, Mission-level,
and unattributed cost appears separately.

The renderer emits Markdown with Mermaid or structured JSON. `--focus TASK_ID` selects
one real subtree without merging, regrouping, or fabricating nodes.

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
- host-observed model calls emit paired start/completion events with caller-side timing
- model-call errors are recorded before the original exception is re-raised
- unmatched starts remain visible as open calls and never enter completed cost totals
- every rendered task node maps one-to-one to a real Mission task ID
- no view merges nodes at any hierarchy level or invents display-only grouping nodes
- standard and audit preserve every materialized node and declared parent-child edge
- compact and focus views declare every omission and never replace hidden nodes with a
  synthetic summary node
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
- claiming caller-visible request time as pure provider-internal inference time
- putting every trace field inside every Standard node
- synthetic grouping nodes, composite task nodes, or merged Mission hierarchy nodes

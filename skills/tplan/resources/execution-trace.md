# TPlan Execution Trace And Cost Tree

## Core

`execution_trace.jsonl` records the route and observed cost of a Mission. It is not
acceptance evidence and it is not a raw transcript.

New Mission runtimes contain:

```text
execution_trace.jsonl
reports/
```

Use the trace to answer:

- which nodes actually ran, and in what order
- which nodes completed, blocked, paused, retried, or were added during execution
- how much lifecycle elapsed time was observed
- how much reported model, Agent-turn, script, tool, wait, or runtime time was consumed
- which Token fields were reported by the platform
- what result summary and stable artifact/evidence references were attached

Do not use it to prove semantic correctness. A process can run successfully and still
produce the wrong result.

## Capture Surfaces

Lifecycle capture is automatic when Mission state is changed through TPlan runtime
scripts. Platform and host cost need an explicit observer:

| Cost | Preferred source | Runtime surface |
| --- | --- | --- |
| model latency and Tokens | platform report | `record_execution_span.py` |
| outer Agent turn | platform or host | `record_execution_span.py` |
| script/tool elapsed | host monotonic clock | `run_traced_command.py` |
| wait/queue elapsed | host/platform | `record_execution_span.py` |
| state mutation | TPlan runtime | automatic lifecycle event |

Missing data stays absent. Never replace an unavailable Token field or duration with a
fabricated zero. A category with no emitted span is `not reported`, not automatically
zero or not applicable.

## Span Fields

Span kinds:

- `model`: one provider model call
- `agent_turn`: outer Agent turn; may contain model, tool, and wait child spans. It is
  an audit envelope, not LLM time, and is never added to its child resource spans.
- `script`: local script or test command
- `tool`: non-model tool/API operation
- `wait`: queue, approval, or external wait
- `runtime`: TPlan/runtime overhead

Measurement sources:

- `platform_reported`
- `host_measured`
- `inferred`
- `unavailable`

`span.measurement_source` describes timing. `usage_source` independently describes
Token fields, because a platform may report Tokens without model latency or the reverse.

Use `inferred` only when the derivation is inspectable. The renderer keeps the source
visible and does not promote inference into an exact measurement.

Attribution:

- `exact` requires one `task_id`
- `shared` requires at least two `shared_task_ids` and leaves `task_id` null
- `mission_overhead` leaves `task_id` null
- `unattributed` leaves `task_id` null

Shared and uncertain spans remain outside task rollups. Do not split them by guesswork.

`cached_input_tokens` is a subset of `input_tokens`; `reasoning_output_tokens` is shown
as a subordinate output measure. Neither is added a second time to create a total.
Report Token usage only once in a nested span tree—normally on the provider `model`
span—not on both a model span and its containing Agent turn.

## Record A Platform Span

When a platform returns structured usage, write a sanitized JSON object and ingest it:

```bash
python3 skills/tplan/scripts/record_execution_span.py "$MISSION_DIR" \
  --input /path/to/sanitized-span.json
```

Or pass the basic fields directly:

```bash
python3 skills/tplan/scripts/record_execution_span.py "$MISSION_DIR" \
  --task-id T1 \
  --kind model \
  --label "model inference" \
  --measurement-source platform_reported \
  --started-at 2026-07-18T10:00:00Z \
  --finished-at 2026-07-18T10:00:02Z \
  --duration-ms 2000 \
  --input-tokens 1200 \
  --cached-input-tokens 400 \
  --output-tokens 300
```

The label is a safe operation class, not a prompt excerpt or response summary.

## Measure A Script Or Tool

```bash
python3 skills/tplan/scripts/run_traced_command.py "$MISSION_DIR" \
  --task-id T1 \
  --kind script \
  --label "focused tplan tests" \
  -- python3 -m unittest tests.tplan.test_execution_cost_tree
```

The command inherits stdout/stderr so normal operator behavior is preserved. The trace
stores the safe label, elapsed milliseconds, status, attempt, and exit code. It does not
store the executable, arguments, stdout, or stderr.

## Attach Results To A Transition

```bash
python3 skills/tplan/scripts/transition_task.py "$MISSION_DIR" \
  --task-id T1 \
  --status completed \
  --outcome-summary "Execution tree rendered" \
  --evidence-ref E12 \
  --artifact-ref reports/execution-cost-tree.md
```

Keep the outcome concise. Evidence and artifact references remain links; their full
content does not belong in the trace.

## Render The Tree

Default complete-topology view:

```bash
python3 skills/tplan/scripts/render_execution_cost_tree.py "$MISSION_DIR" \
  --view standard \
  --output "$MISSION_DIR/reports/execution-cost-tree.md"
```

Other views:

```bash
python3 skills/tplan/scripts/render_execution_cost_tree.py "$MISSION_DIR" --view compact
python3 skills/tplan/scripts/render_execution_cost_tree.py "$MISSION_DIR" --view audit
python3 skills/tplan/scripts/render_execution_cost_tree.py "$MISSION_DIR" --focus T1
python3 skills/tplan/scripts/render_execution_cost_tree.py "$MISSION_DIR" --format json
```

- `compact`: an explicitly labelled projection containing Mission and root Tasks;
  focused mode adds direct children and reports the number of omitted real nodes
- `standard`: every materialized Mission / Task / SubTask / Step and every declared
  parent-child edge, with the fixed status, elapsed, LLM, script, tool, wait, Token,
  and result slots
- `audit`: the same one-to-one topology as `standard`, plus recovery and measurement
  detail

The renderer never merges real nodes, reparents them, or invents display groups. A
large tree may be split only at real Task boundaries without changing topology.

Step cards show direct cost; Task and SubTask cards show inclusive subtree cost. JSON
exposes both. Actual elapsed is the natural time from observed start to finish.
Attributed elapsed time is the union of exact model, script, tool, wait, and runtime
intervals, so nested and parallel spans are not double-counted. When lifecycle coverage
is exact:

`actual elapsed = attributed wall coverage + unattributed elapsed`

Per-kind duration remains resource time and may overlap; it is not expected to sum to
actual elapsed. `agent_turn` remains an audit envelope and is excluded from LLM and
additive resource totals.

## Coverage

- `exact`: lifecycle trace started with Mission initialization
- `partial`: the Mission existed before the first trace record
- `snapshot_only`: no trace exists; timing and Token cost remain unknown

Even `exact` lifecycle coverage reports only cost spans that a host or platform
actually supplied. The report declares `reported_spans_only` for that reason.

## Privacy Guard

Allowed content is deliberately narrow: numeric cost, status, IDs, safe labels, narrow
metadata, and stable refs. Raw prompts, responses, command arguments, stdout, stderr,
environment, credentials, and secrets are rejected.

If a platform cannot provide sanitized structured telemetry, record `unavailable` or
leave the field absent. Do not copy raw output into the trace to improve apparent
completeness.

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
| caller-visible model request time | host monotonic clock | `ModelCallObserver` in `observe_model_call.py` |
| provider timing and Tokens | platform report | `record_execution_span.py` or observer usage adapter |
| outer Agent turn | platform or host | `record_execution_span.py` |
| script/tool elapsed | host monotonic clock | `run_traced_command.py` |
| wait/queue elapsed | host/platform | `record_execution_span.py` |
| state mutation | TPlan runtime | automatic lifecycle event |

Missing data stays absent. Never replace an unavailable Token field or duration with a
fabricated zero. A category with no emitted span is `not reported`, not automatically
zero or not applicable.

## Span Fields

Span kinds:

- `model`: one caller-visible provider request
- `agent_turn`: outer Agent turn; may contain model, tool, and wait child spans. It is
  an audit envelope, not cumulative LLM-call time, and is never added to its child
  resource spans.
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

For a `model` span, the source changes what the number means:

- `host_measured`: elapsed time seen by the caller around the SDK/API operation. It may
  include provider queueing, network transfer, retries inside the SDK, and streaming.
  It is exact for that caller boundary, not for provider-internal inference alone.
- `platform_reported`: a duration explicitly returned by the provider/platform. Its
  narrower or broader provider definition must remain an adapter contract; do not
  silently treat it as equivalent to caller-visible elapsed time.
- `inferred`: an inspectable estimate, always rendered as estimated.
- `unavailable`: no defensible duration measurement.

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

If the platform omits usage, a host adapter may count input/output text locally and emit
only numeric estimates with `usage_source: inferred`. The estimator and its unit must be
declared by that adapter; a word/character count is not an exact provider tokenizer
count. Raw input/output text still must not enter the trace, and rendered estimates keep
the `≈` marker.

## Observe A Model Call At The Host Boundary

Use the shared observer at the narrowest host-owned SDK boundary:

```python
from pathlib import Path
from observe_model_call import ModelCallObserver

observer = ModelCallObserver(
    Path(mission_dir),
    task_id="T1",
    label="recommendation call",
    provider="provider-name",
    model="model-name",
)
response = observer.invoke(
    lambda: model_client_call(),
    usage_from_result=lambda result: normalize_numeric_usage(result),
)
```

The observer writes `span_started` before invoking the callable, measures only the
callable with a host monotonic clock, then writes `span_completed` with the same
`span_id`. Trace-file I/O and usage normalization are outside the measured duration.
The callable and response are never serialized.

For a streaming request, the observed callable must consume the stream through its
terminal event; timing only the function that returns the stream handle measures setup,
not the complete request.

`span_started.timestamp` is an entry marker. The completed span's `started_at`,
`finished_at`, and `duration_ms` are the authoritative measured interval. A start marker
without a matching completion remains visible as an open/interrupted call and is not
included in cost totals. A standalone `span_completed` remains valid for compatibility
and for platforms that can only deliver an after-the-fact sanitized record.

## Record A Platform-Reported Span

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

The command inherits stdout/stderr so normal operator behavior is preserved. It emits
paired start/completion events and stores the safe label, elapsed milliseconds, status,
attempt, and exit code. It does not store the executable, arguments, stdout, or stderr.

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

For Standard/Audit, writing Markdown also writes `execution-cost-tree.svg` beside it and
embeds that SVG as the primary diagram. Render SVG directly when a standalone image is preferred:

```bash
python3 skills/tplan/scripts/render_execution_cost_tree.py "$MISSION_DIR" \
  --view standard \
  --format svg \
  --output "$MISSION_DIR/reports/execution-cost-tree.svg"
```

Other views:

```bash
python3 skills/tplan/scripts/render_execution_cost_tree.py "$MISSION_DIR" --view compact
python3 skills/tplan/scripts/render_execution_cost_tree.py "$MISSION_DIR" --view compact --format text
python3 skills/tplan/scripts/render_execution_cost_tree.py "$MISSION_DIR" --view audit
python3 skills/tplan/scripts/render_execution_cost_tree.py "$MISSION_DIR" --focus T1
python3 skills/tplan/scripts/render_execution_cost_tree.py "$MISSION_DIR" --format svg
python3 skills/tplan/scripts/render_execution_cost_tree.py "$MISSION_DIR" --format json
```

- `compact`: an explicitly labelled Unicode text-tree projection containing Mission,
  every real root Task, execution-signal nodes, the top direct-cost nodes, and the real
  ancestor paths needed to reach them; each visible line retains actual elapsed, LLM,
  script, optional tool/wait/Token, retry/error, and result fields; `--top-cost N`
  controls cost-node count; `[T]`, `[ST]`, and `[P]` identify Task, SubTask, and Step;
  SVG output is rejected
- `standard`: every materialized Mission / Task / SubTask / Step and every declared
  parent-child edge, with the fixed status, elapsed, cumulative LLM-call, script, tool,
  wait, Token, and result slots
- `audit`: the same one-to-one topology as `standard`, plus recovery and measurement
  detail

The renderer never merges real nodes, reparents them, or invents display groups. A
large tree may be split only at real Task boundaries without changing topology.

Standard and Audit use a vertical execution timeline rather than a hierarchy-only TB
layout. Rows are sorted by first observed time; the left rail prints the observed start
offset. With exact lifecycle coverage the origin is Mission initialization; partial
coverage uses and labels the observed trace window. Row spacing is ordinal to keep long
idle gaps from inflating the image. The range strip at the bottom of every observed card
is linearly scaled against the same elapsed window, so temporal position and duration
remain comparable.
Blue overlay edges preserve the declared Mission / Task / SubTask / Step hierarchy.

Step cards show direct cost; Task and SubTask cards show inclusive subtree cost. JSON
exposes both. Actual elapsed is the natural time from observed start to finish.
Exact interval coverage is the union of completed model, script, tool, wait, and runtime
intervals whose timing source is exact, so nested and parallel spans are not
double-counted. When lifecycle coverage is exact:

`actual elapsed = exact interval coverage + elapsed not exactly recorded`

The remainder is not automatically model, script, or orchestration time; it only means
that no completed exact-time interval covers it. Per-kind duration remains resource time
and may overlap; it is not expected to sum to actual elapsed. `agent_turn` remains an
audit envelope and is excluded from cumulative LLM-call and additive resource totals.

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

# Case Prep / 案例准备

`case-prep` is an explicit-only internal skill that lowers the threshold for preparing
Mindthus cases. It produces a local directory and `.tar.gz` archive; it never uploads.

## Typical Requests

```text
/mindthus:case-prep 导出当前所有mindthus相关案例
/mindthus:case-prep 把刚才这次判断失败整理成案例
/mindthus:case-prep 导出这个 benchmark run 里的 mtj-002
/mindthus:case-prep 把当前 TPlan Mission 的阻塞整理成案例
```

The first command is the simplest default. The skill identifies bounded reusable cases
in the current conversation and referenced current Mission, deduplicates repeated turns,
prepares each case through its own contract, and returns one collection archive.

The skill infers one of four modes:

- `collection`: all current Mindthus-related cases in one delivery envelope;
- `judgment`: current or previous bounded interaction;
- `benchmark`: run directory plus case ID;
- `tplan`: Mission directory/current Mission.

It asks at most one question when multiple failure events are genuinely ambiguous.

## Runtime Commands

### Collection

After the skill prepares the individual case directories, it packages them with:

```bash
python3 skills/case-prep/scripts/prepare_case.py collection \
  --case-dir /tmp/mindthus-case-exports/mindthus-case-case-1 \
  --case-dir /tmp/mindthus-case-exports/mindthus-tplan-case-case-2
```

The result is one `mindthus-case-collection-<id>.tar.gz`. Every nested case remains
independently valid and review-required; the collection does not merge all cases into
one Judgment Trace.

### Judgment

```bash
python3 skills/case-prep/scripts/prepare_case.py judgment \
  --trace /tmp/trace.json \
  --summary /tmp/summary.json \
  --case-type judgment_failure
```

The skill normally creates those temporary inputs for the user.

### Benchmark

```bash
python3 skills/case-prep/scripts/prepare_case.py benchmark \
  --run-dir /path/to/run \
  --benchmark-case-id mtj-002
```

### TPlan

```bash
python3 skills/case-prep/scripts/prepare_case.py tplan \
  --mission-dir /path/to/mission \
  --focus auto
```

TPlan packet or collection validation:

```bash
python3 skills/case-prep/scripts/validate_case_packet.py \
  /tmp/mindthus-case-exports/mindthus-tplan-case-...
```

## TPlan Bounded Packet

TPlan export is fail-closed read-only: it uses `read_outcome_attribution_snapshot` once and derives its Pulse-compatible view from that snapshot. It does not call the normal Mission Pulse path, because normal runtime reads may recover a pending transaction. A pending transaction therefore blocks export instead of being repaired by case preparation.


The TPlan adapter exports:

- Mission policy and active-path summary;
- one focus and selection reason;
- one primary event and at most five brief evidence events;
- a compact Pulse-compatible view derived from the same atomic read-only Mission snapshot;
- runtime-provenance status and diagnostic codes;
- optional linked Judgment Trace;
- optional confirmed-redacted text excerpts.

It excludes the full Mission, complete task tree, evidence stream, step logs, execution
trace, telemetry stream, and private event payloads.

## Sharing Boundary

Every result keeps:

```text
review_required_before_share: true
automatic_upload: false
```

Read every generated file and review warnings before uploading the archive for analysis.
A passing validator does not prove anonymity, consent sufficiency, semantic correctness,
or benchmark value.

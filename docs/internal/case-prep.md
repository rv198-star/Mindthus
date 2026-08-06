# Case Prep / 案例准备

`case-prep` is an explicit-only internal skill that lowers the threshold for preparing
Mindthus cases. It produces a local directory and `.tar.gz` archive; it never uploads.

## Typical Requests

```text
/mindthus:case-prep 把刚才这次判断失败整理成案例
/mindthus:case-prep 导出这个 benchmark run 里的 mtj-002
/mindthus:case-prep 把当前 TPlan Mission 的阻塞整理成案例
```

The skill infers one of three modes:

- `judgment`: current or previous bounded interaction;
- `benchmark`: run directory plus case ID;
- `tplan`: Mission directory/current Mission.

It asks at most one question when multiple failure events are genuinely ambiguous.

## Runtime Commands

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

TPlan packet validation:

```bash
python3 skills/case-prep/scripts/validate_case_packet.py \
  /tmp/mindthus-case-exports/mindthus-tplan-case-...
```

## TPlan Bounded Packet

The TPlan adapter exports:

- Mission policy and active-path summary;
- one focus and selection reason;
- one primary event and at most five brief evidence events;
- compact Mission Pulse fields;
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

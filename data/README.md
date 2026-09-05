# Fidelity Usage Log Data

This directory is the default home for local Method Fidelity usage logs.

Default file:

```bash
data/fidelity-usage-log.jsonl
```

Each line is one redacted usage record. Do not store full private prompts, private
customer data, secrets, or unredacted work artifacts here. Use `source` to point to a
shareable issue, test packet, or local artifact when review context is needed.

Use:

```bash
python3 scripts/log-fidelity-usage.py --help
```

On a fresh checkout, validating the default path before any record exists is allowed:

```bash
python3 scripts/log-fidelity-usage.py --validate --log data/fidelity-usage-log.jsonl
```

It reports `Records: 0` and `No usage-log data yet`; missing non-default paths still
fail.

The log is a data flywheel seed, not a benchmark claim. It is useful only after enough
real or evaluation records accumulate.

For product validation, follow `docs/real-use-validation.md`: prefer naturally occurring
work, do not invent scores, and do not open an optimization issue from one mild event.

## Reviewed incident evidence

[Slidethus VQ execution overrun](cases/slidethus-vq-execution-overrun-20260905/README.md)
is an owner-approved bounded real-use incident. Its `admission.json` carries the stable
record ID, observation time, retrospective collection mode, consent and inclusion
assessment. Original packet files remain byte-preserved; current synthetic code probes
are separate evidence and are not additional real-use records.

A usage-log row is not automatically an eligible complete prospective task. This incident
was exported while its Mission remained active and is excluded from the #144 prospective
denominator. Current v0.1 log validation checks the supported record fields, not the
completeness or causal value of a task; typed status automation remains #144 work.

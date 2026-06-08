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

The log is a data flywheel seed, not a benchmark claim. It is useful only after enough
real or evaluation records accumulate.

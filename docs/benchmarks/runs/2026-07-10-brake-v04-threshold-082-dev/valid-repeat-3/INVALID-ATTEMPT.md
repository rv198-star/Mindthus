# Invalid Runtime Attempt: Valid Repeat 3

Status: invalid and excluded from the V0.4 threshold-0.82 diagnostic sample.

## Failure Boundary

The run began with the same frozen V0.4 prompt, `0.82` threshold, fixtures,
runner, owner gate, and model configuration as valid repeats 1 and 2. During
the first packet, the external Codex service began returning:

```text
You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage
to purchase more credits or try again at 6:27 PM.
```

The remaining subprocesses were stopped after this condition was confirmed so
the service error would not be converted into behavioral scores. This is an
external usage-limit interruption, not a prompt, fixture, triage, gate, or
loaded-action result.

## Evidence

- The first error is preserved in
  `original/events/brake-triage-p07-turn-1.jsonl` and corresponding triage
  event files.
- The partial artifacts remain in place for independent inspection.
- No summary from this directory may be included in an n=3 aggregate.

The next valid repeat must start only after the external limit is available and
must use the identical frozen configuration recorded in the handoff manifest.

# TPlan Case Preparation

TPlan mode uses documented read-only Mission snapshot and Pulse surfaces. It preserves
TPlan as a stateful runtime rather than translating the Mission into Judgment Trace.

Supported focuses:

- `blocker`
- `acceptance`
- `continuation`
- `authority`
- `recovery`
- `provenance`
- `telemetry`
- `general`

`auto` selects one focus from Mission status, runtime provenance, re-entry state, Pulse
signals, and recent evidence event classes.

The packet includes only a Mission policy/active-path summary, a compact Pulse view,
one primary event, at most five brief evidence events, runtime-provenance status and
diagnostic codes, optional redacted excerpts, and an optional linked Judgment Trace.

Never copy `mission.json`, the full task tree, `evidence.jsonl`, step logs,
`execution_trace.jsonl`, telemetry payloads, or the Mission directory.

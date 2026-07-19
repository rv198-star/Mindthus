# Invalid carrier trace sanitization

The three invalid v1.0 Frame/Whole traces read the bundled Codex
`.system/openai-docs/SKILL.md`. Its full body is not needed to prove the confound and is
not part of this repository. Before committing the evidence, only the
`aggregated_output` field of that completed command event was replaced with a fixed
redaction marker.

Retained unchanged:

- exact command path showing the system Skill read;
- event type, id, status, and exit code;
- all web-search lifecycle events;
- Mindthus read paths;
- final answer, stderr, usage, duration, plugin identity, and summaries.

Original pre-redaction SHA-256 values:

| Trace | SHA-256 |
| --- | --- |
| `run-20260719-v1/r2/frame_whole/events.jsonl` | `65f52ee347d73e2e9c8bf36a3f2c5fc79fa52c6cc2d9e1e8ba626c2fa9cda771` |
| `run-20260719-v1-continuation/incumbent/frame_whole/events.jsonl` | `eccdc6159ef1db01a9ca66b6cf5580bdfb0fb78ae007135d1aa0b13aa844e6f3` |
| `run-20260719-v1-r1-frame/r1/frame_whole/events.jsonl` | `93f0c17d3383edc90fd887b7b21a9d414b5f72710d49c32e7d74df041b96f7d1` |

The invalid samples remain excluded from route verdicts and included in Mission cost.

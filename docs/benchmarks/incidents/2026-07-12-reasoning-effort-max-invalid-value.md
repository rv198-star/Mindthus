# Incident: `reasoning.effort=max` became invalid

## Decision

Classification: **permanent API contract change** for the active `gpt-5.5`
service contract, not a transient transport fault.

The repeat-3 attempt is invalid and excluded from all aggregates. The runner,
prompt, fixture, owner gate, and fire policy remain frozen pending review of the
separate minimal adaptation proposal.

## First failure and before/after window

All timestamps are Asia/Shanghai.

| Case turn | Event timestamp / file mtime | Outcome |
| --- | --- | --- |
| N01 turn 1 | 2026-07-12T02:21:43+0800 | completed |
| N02 turn 1 | 2026-07-12T02:22:30+0800 | completed |
| N03 turn 1 | 2026-07-12T02:24:58+0800 | completed |
| N04 turn 1 | 2026-07-12T02:25:20+0800 | first failure |

N01--N03 records contain `turn.completed` with normal usage. N04--N08 each
contain the same deterministic 400 response; this rules out an isolated retry
or network interruption.

## Raw provider response

The complete N04 response body, preserved at
`repeat-3/original/events/brake-triage-n04-turn-1.jsonl`, is:

```json
{
  "type": "error",
  "error": {
    "type": "invalid_request_error",
    "code": "invalid_value",
    "message": "Invalid value: 'max'. Supported values are: 'none', 'minimal', 'low', 'medium', 'high', and 'xhigh'.",
    "param": "reasoning.effort"
  },
  "status": 400
}
```

## External contract evidence

The current official GPT-5.5 model documentation lists its reasoning choices as
`none`, `low`, `medium`, `high`, and `xhigh`; `max` is absent. The raw provider
validation response supplies the same closed set. The closest semantic
replacement is `xhigh`: it is the highest currently accepted effort level, but
it is not asserted to be behaviorally identical to the retired `max` value.

## Consequence

An effort adaptation changes a run-identity input. If accepted, pre-adaptation
repeat 1 and repeat 2 remain diagnostic evidence only and cannot be combined
with any adapted run; the n=3 campaign restarts from a fresh repeat 1.

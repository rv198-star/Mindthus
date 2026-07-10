# Invalid Attempt: Quota Exhaustion

Status: excluded from every valid-repeat denominator and from all six dev-gate
decisions.

This directory contains only the repeat-3 A1/A2 action-anchor packet. The
original and V0.4-expansion packets for repeat 3 completed before the provider
quota failure; they remain separately archived as partial diagnostic evidence,
but repeat 3 is not a complete valid repeat.

The provider returned the explicit usage-limit response while processing both
anchor pressure turns. The resulting action and triage subprocesses returned
`rc=1`, and both judge calls exhausted their one parse retry with empty output.
The primary evidence is preserved verbatim in:

- `action-anchors/action-events/*-action-turn-2.jsonl`
- `action-anchors/triage-events/*-triage-turn-2.jsonl`
- `action-anchors/judge-events/*-judge*.jsonl`

The error text states that the Codex usage limit was reached. These are not
semantic failures of the action contract or judge. No retry was started after
the quota event, no input or runtime configuration was changed, and the
artifacts remain available for audit.

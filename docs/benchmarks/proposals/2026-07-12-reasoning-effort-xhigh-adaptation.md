# Proposal: replace retired `max` reasoning effort with `xhigh`

Status: approved compatibility adaptation. The implementation must remain a
single, separately audited request-configuration change.

## Scope

Make one compatibility substitution wherever the benchmark runner's Codex
request configuration supplies `reasoning.effort`:

`max` -> `xhigh`

Update only the corresponding unit tests, run manifest/fingerprint material,
and documentation that names the request setting. Do not alter prompt text,
fire policy, fixtures, owner exposure gate, action contract, judge protocol, or
scoring logic.

## Semantic boundary

`xhigh` is the highest valid current setting for GPT-5.5. It replaces the
retired value for request validity; it does not establish equivalence with the
old behavior. The changed setting becomes a new run-identity field and must be
fingerprinted. The runner must pass it explicitly as
`model_reasoning_effort="xhigh"` to every Codex subprocess, rather than inherit
an ambient `CODEX_HOME/config.toml` value.

## Certification consequence

After approval and implementation, all adapted runs begin a new n=3 campaign
from a fresh repeat 1. Existing repeat 1 and repeat 2 artifacts stay archived
as diagnostic evidence and are never numerically pooled with the adapted
campaign.

# C01-v2 local development carrier

## Core

Run exactly the frozen 26 Chinese development cases through official TypeSafe Jev,
record the observations, and compare them with preauthored labels. This carrier does
not consume skills in a native host or authorize downstream actions. A mocked transport
test of this carrier remains mechanical evidence, even though it exercises the live path.

## Mainline

The semantic freeze in `c01-v2-development-freeze.json` remains byte-for-byte unchanged:
C01 questions, State, graph, canonical contracts, labels and scoring plan are unchanged.
This carrier-only delta supersedes the old plan's implementation-status paragraph that
said Session was offline-only. It uses zero of the one allowed semantic revisions.
The old runtime hash identifies the pre-carrier snapshot; a prepared `campaign.json`
additionally binds the current carrier/runtime hash. Neither identity is overwritten.

Preparation verifies every frozen file and enumerates 225 exact possible request hashes
by traversing the fixed C01 paths for every eligible owner. It uses context and contracts,
never expected labels or rationale. This is a static admission list, not a graph designer.
At inference, only the selected owner's full contract enters its dependent State.
The local evaluator reads labels after each graph result. It reports D0, entry, route,
owner, applicability, obligation, paired-family agreement, abstentions and failures.
Development thresholds are the frozen 26/26 D0 and at least 23/25 entry and route matches;
they do not establish host execution, independent semantic qualification or net value.

Serving is pinned to `jev-1.13.0` at `https://api.typesafe.ai/v1/systemone`.
One journal covers the entire campaign: at most 78 calls, 300 cumulative inference
seconds, and 98,304 projected request bytes per batch. Session checks exact egress,
locks the observed runtime, and reuses completed batches on recovery. Unknown in-flight
calls stop. A completed campaign cannot be rerun; read its immutable summary instead.
OpenRouter is a separate backup trial and is not silently substituted here.

The local campaign ceiling is USD 0.25. On 2026-09-22, the official
[model documentation](https://docs.typesafe.ai/models) listed USD 0.042 per million input
tokens, output free, and at most 64,000 input tokens per call. Reserve USD 0.002688 for
every attempted call, including failures or missing billing telemetry: 78 calls reserve
USD 0.209664. This is a client reservation based on published pricing, not a provider
account spending limit. Unexpected reported cost/token overruns stop further calls;
unknown actual cost remains unknown, with token-derived estimates reported separately.

Keys have encrypted Private Notes records. The owner subsequently identified an existing
local environment file through a linked task; its official key was loaded in process
memory for this run, with no new credential file. The CLI accepts an existing process environment
or hidden input from an interactive local terminal; hidden input is held only in this
process environment and removed on exit. Never put the key in command text or chat.

From `/Users/william/Projects/Github/Mindthus`:

```bash
python3.12 -m experiments.typed_decision.campaign prepare --state-root /Users/william/Documents/Codex/2026-09-22/mindthus-c01-typesafe-dev-1
python3.12 -m experiments.typed_decision.campaign run --state-root /Users/william/Documents/Codex/2026-09-22/mindthus-c01-typesafe-dev-1 --prompt-key
python3.12 -m experiments.typed_decision.campaign report --state-root /Users/william/Documents/Codex/2026-09-22/mindthus-c01-typesafe-dev-1
```

Prepare performs no inference. Use the same root after interruption; do not delete a
journal or create another trial to bypass an unknown call, failure, stop or budget.
`/tmp/mindthus-c01-typesafe-dev-1` was only an earlier preparation probe, with no calls;
it is superseded by the persistent path above, which binds the final carrier source.

## Boundary

The first official development call has now failed local contract validation; the
campaign stopped with zero accepted semantic batches. Three separately admitted
diagnostics succeeded but do not substitute for that failed observation. The owner
resolved credential input through an existing local environment file. See
`c01-v2-typesafe-dev-1.json` and `STATUS.md` for evidence and the remaining failure-
observation gap. Semantic revisions remain zero. Holdout is not frozen
or evaluated; A/B/C and #212 are unstarted. After development observations, review all
mismatches before any bounded semantic revision or independent holdout freeze.

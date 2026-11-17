# R3 independent audit evidence

Code under audit: `2753470fcd32ef2482e2af6126354e59aca57dcc`.
Source/audit chat: `01a1e806-292f-76d0-af7e-f4786d70b3e1`, host `local`.

## Runtime probes

`reproduce.py` creates isolated temporary Missions using this revision's test fixture. Each case cleans up afterwards. Run from any checkout location with CPython 3.11:

```text
python3 -B docs/internal/tplan-collaboration/reviews/r3-audit/reproduce.py
```

`probe-results.jsonl` preserves the observed R3 results. The first two cases complete a Mission with an unmet repair obligation. The third compares a valid local repair's completion projection with its resume projection. `existing-tests.txt` records the independent 47-test rerun and the exact-head CI check.

## Controlled source-Agent exercise

Evidence class: `controlled_source_agent_exercise`. The actual source Agent in this chat observed controlled inputs, chose dispositions and next actions, invoked the collaboration/native runtime, and inspected the results in successive tool rounds. It was not a second Python driver with a preset decision sequence. The support helper only sets up fixtures and applies the decisions supplied by the source Agent.

Peer messages, host stop observations, and human goal-change events were isolated test fixtures. Their authority applies only to these test Missions. `real_peer_host_e2e=false` is preserved on every log entry. These records cover source-Agent choices under controlled inputs; live A/B/C transport, peer authentication, wake-up, redelivery, cancellation and A-to-A writer isolation remain separate host acceptance items.

- `fixture-context.json`: inputs and test-only context supplied before choices.
- `source-actions.jsonl`: ordered fixture inputs, actual choices, requests/results, before/after states, chat provenance, audited code hash and source call IDs (`source-agent-01` through `source-agent-10`, plus the premise experiment). `fixture-input` identifies synthetic providers. Some entries are observations/native events rather than collaboration commands.
- `source-exercise-support.py`: the setup/recording helper, with a checkout-relative source root. It has no solver or automatic decision replay. Executing `setup` creates a fresh temporary world; reproducing the source choices requires another explicit Agent exercise.
- `final-states/`: canonical Mission states, native evidence and execution traces for all six cases; T29 includes the superseded implementation Mission and its new local assessment Mission. Original temporary paths in the logs are provenance references.
- `outcomes.json`: compact outcome assertions derived from the observed states and actions.

The T28 source Agent recorded the bounded C PASS while requesting the missing artifact/runtime evidence, so it made no adoption. This is the observed decision, rather than the earlier developer driver's expected adoption. In T29 the explicit goal change updates canonical Mission state through a superseded predecessor and new successor; updating only the old coordination summary would not satisfy the case.

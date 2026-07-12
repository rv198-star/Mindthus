# Xhigh Dev N=3 Capacity Precheck

Status: repeat-1 authorized by Notion directive `D-20260712-002`.

## Frozen Inputs

- Branch and commit: `codex/brake-semantic-triage-design` at `a26006c8a072e3b9e21d41a3eb56c666e6fd12d3`.
- Runner SHA-256: `abb704ec2983611ee45c17e4c520ca4f2b307e737462d75c74b243b4c99c1b81`.
- Reasoning effort: `xhigh` via `model_reasoning_effort`, fingerprint `96497c9df09cfbece7931fcd775fd99580127d817717510f8b36ee47be3ab4d8`.
- Prompt, fire policy, fixtures, owner gate, action contract, judge, and scoring remain frozen.

## Capacity Observation

At `2026-07-12T10:36:56Z`, the local Codex bridge reported 84% remaining in
the five-hour window and 97% remaining in the weekly window.

The protected repeat contains 39 cases and 51 possible user turns across the
original fixture, V0.4 expansion, and A1/A2 anchors. Its nominal subprocess
budget is 276 calls: 153 triage samples, 51 generator calls, 39 judge calls,
and up to 33 loaded-action calls. The triage validation retry ceiling raises
the maximum to 429 calls. The nearest complete prior repeat used 278 subprocess
calls, including observed retries.

The current window is accepted for one atomic repeat. A quota or provider
failure invalidates the entire repeat and stops the campaign; no partial result
is counted.

## Repeat-2 Capacity Observation

At `2026-07-12T11:58:25Z`, immediately before repeat-2, the local Codex bridge
reported 44% remaining in the five-hour window and 91% remaining in the weekly
window. Repeat-1 consumed approximately 40 percentage points of the five-hour
window under the same frozen configuration. The remaining five-hour capacity is
therefore narrow but sufficient for one repeat by the observed repeat-1 cost.

Repeat-2 is accepted as one atomic attempt. Any quota or provider failure
invalidates the entire repeat and stops the campaign; its partial artifacts are
archived but are not counted.

## Repeat-3 Capacity Observation

At `2026-07-12T13:34:47Z`, the local Codex bridge reported 24% remaining in
the five-hour window and 88% remaining in the weekly window. The two complete
same-configuration repeats each consumed approximately 40 percentage points of
the five-hour window. Repeat-3 is therefore not started: the available window
cannot accommodate one atomic repeat.

No repeat-3 artifacts exist. The campaign waits for the next five-hour window
rather than creating a knowingly invalid partial attempt.

## Repeat-3 Capacity Observation (Accepted)

At `2026-07-12T16:18:07Z`, the local Codex bridge reported 100% remaining in
the five-hour window and 88% remaining in the weekly window. This exceeds the
approximately 40 percentage points consumed by each completed same-
configuration repeat. Repeat-3 is accepted as one atomic attempt under the
unchanged `a26006c8a072e3b9e21d41a3eb56c666e6fd12d3` freeze.

Any quota or provider failure invalidates the entire repeat and stops the
campaign; partial artifacts are archived but are not counted.

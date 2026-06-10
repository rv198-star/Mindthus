# tplan Shared Risk Context Actual Run - 2026-06-10

This record captures the first run of the revised shared risk context A/B experiment.
It separates the primary Deterministic Replay result from supplemental Constrained Live
Agent samples. A follow-up run adds the Scripted Agent Simulator layer after the live
samples proved too noisy to score.

## Sources

| Arm | Source | Notes |
| --- | --- | --- |
| A / Pre-shared-risk Baseline | `1c14cb6` | Clean baseline before shared-risk design docs and runtime support |
| B / Shared-risk Treatment | current checkout after `81446f4` | Current checkout containing shared-risk runtime, revised A/B design, and stop-latency simulation |

Snapshot directories:

- A: `/tmp/tplan-shared-risk-replay-old-src`
- B: `/tmp/tplan-shared-risk-replay-new-src`

## Deterministic Replay

### Surface Check

| Check | A / Old | B / New |
| --- | --- | --- |
| `record_risk_context.py` exists | no | yes |
| shared-risk docs count | 0 | 2 |
| shared-risk term hits in `skills/tplan` and `docs` | 0 | 107 |

The old baseline was clean. The previous contaminated baseline problem did not recur.

### B / Treatment Replay Steps

| Step | Result | Evidence |
| --- | --- | --- |
| Initialize Mission | pass | `initialized_mission: /tmp/tplan-shared-risk-replay-new/mission` |
| Record shared risk | pass | `risk_signal: R1 active`, `risk_evidence: E1` |
| Generate decision packet | pass | `/tmp/tplan-shared-risk-replay-new/decision_packet.json` |
| Apply high-impact decision without `risk_assessment` | blocked as expected | `decision missing field: risk_assessment` |
| Apply decision with valid `risk_assessment` | pass | `applied_decision: /tmp/tplan-shared-risk-replay-new/decision_with_risk_assessment.json` |
| Resolve risk after recovery note | pass | `risk_signal: R1 resolved`, `risk_evidence: E3` |
| Check Mission | pass | `mission_check: ok` |

Recorded event types:

- `risk_context_update`
- `decision_applied`
- `risk_context_recovery`

Decision packet shared context while the risk was active:

- `active_risk_signal_count`: 1
- `highest_active_severity`: `high`
- active risk id: `R1`

Risk assessment used in the valid decision:

```json
{
  "shared_context_used": ["R1"],
  "invalid_evidence_risk": "high",
  "failure_risk": "high",
  "risk_adjusted_value": "weak",
  "next_gate": "health_check"
}
```

### Deterministic Replay Score

| Behavior | Result |
| --- | --- |
| Clean source has no shared-risk docs or runtime surface | pass |
| New runtime can publish Mission-level risk signal | pass |
| New runtime writes `risk_context_update` evidence | pass |
| New decision packet exposes active shared risk | pass |
| High-impact decision with active risk requires `risk_assessment` | pass |
| `risk_assessment` names invalid evidence risk and failure risk | pass |
| `risk_adjusted_value` lowers immediate rerun value | pass |
| Risk recovery can be recorded through `risk_context_recovery` | pass |

Primary mechanical result: **pass**.

## Scripted Agent Simulator

The simulator was added after the invalid live samples to provide a stable behavior A/B
between unit tests and live agent runs.

Command pattern:

```bash
python3 tests/tplan/shared_risk_agent_simulator.py \
  --source-root <source> \
  --output-dir <output>
```

Simulation outputs:

| Arm | runtime_profile | mechanical_score | scripted_agent_score | can publish shared risk | next gate |
| --- | --- | ---: | ---: | --- | --- |
| A / Old | `pre_shared_risk` | 0 | 4 | no | `health_check` as plain judgment |
| B / New | `shared_risk` | 8 | 10 | yes | `health_check` through `risk_assessment` |

Stop-latency outputs:

| Arm | expensive_rerun_attempts_before_gate | steps_until_first_safe_gate | blocked_action | final_allowed_action |
| --- | ---: | ---: | --- | --- |
| A / Old | 1 | 2 | `null` | `health_check` |
| B / New | 0 | 1 | `expensive_full_chain_rerun` | `health_check` |

The stop-latency result supports the narrower claim that B earlier blocks the
untrusted expensive path. It does not support claiming that B finishes the whole
Mission earlier.

New-runtime simulator evidence:

- event types: `risk_context_update`, `decision_applied`, `risk_context_recovery`
- ungated high-impact decision stderr: `decision missing field: risk_assessment`
- `risk_assessment.next_gate`: `health_check`
- `risk_assessment.risk_adjusted_value`: `weak`

Scripted simulator result: **pass**.

## Constrained Live Agent

Both live samples were invalid under the revised packet rules.

| Arm | Return code | Timed out | Transcript bytes | Artifacts | Connection retry | Result |
| --- | ---: | --- | ---: | ---: | --- | --- |
| A / Old | -15 | yes | 42,391 | 0 | yes | invalid sample |
| B / New | -15 | yes | 57,800 | 0 | yes | invalid sample |

Invalid-sample reason:

- Both runs hit connection retry symptoms.
- Both runs timed out.
- Neither run produced inspectable Mission artifacts.

No agent behavior score should be assigned from these live samples.

## Conclusion

The revised experiment now succeeds at two stable layers:

- Deterministic Replay verifies that the shared risk context runtime changes the
  available Mission state, decision packet, and high-impact decision gate.
- Scripted Agent Simulator verifies that the same fixed health-gate strategy produces a
  stronger, risk-adjusted decision shape under the new runtime.

The treatment blocks a high-impact decision that ignores active shared risk and accepts
the same decision shape once `risk_assessment` sets `next_gate` to `health_check`.
The stop-latency simulation further distinguishes the behavior: the old runtime lets
one expensive rerun candidate pass before plain judgment reaches `health_check`, while
the new runtime blocks that candidate before it can pass and routes to `health_check`
at the first gate.

The supplemental live layer remains unproven in this run because both samples were
invalid. Do not claim an agent-behavior improvement from this live attempt.

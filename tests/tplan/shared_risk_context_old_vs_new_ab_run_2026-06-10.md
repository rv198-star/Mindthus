# tplan Shared Risk Context Old-vs-New A/B Run Packet - 2026-06-10

This packet defines the acceptance A/B for the shared risk context change. It is a
behavioral review packet, not a unit test. Unit tests prove the runtime can record and
validate risk fields; this run checks whether the changed `tplan` posture helps an
agent stop or gate expensive continuation after shared-environment failure.

## Change Under Test

Shared risk context added Mission-level risk signals and risk-adjusted decision
pressure:

- `mission.shared_context.risk_signals`
- `risk_context_update` and `risk_context_recovery` evidence events
- `scripts/record_risk_context.py`
- decision packets that expose active shared risks
- required `risk_assessment` for high-impact decisions when active shared risks exist
- explicit rule that execution units do not read each other's task logs; they consume
  shared Mission context instead

The intended behavior is not "stop more often." The intended behavior is better
risk-adjusted value judgment: once a shared environment failure can invalidate
evidence, another expensive same-path action should require a health gate or recovery
condition before it is treated as high-value Mission progress.

## Comparator

Use two isolated source snapshots.

| Arm | Source | Purpose |
| --- | --- | --- |
| A / Pre-shared-risk Baseline | commit before shared risk context support, for this implementation `ebd819f` | Shows how old `tplan` behaves with path assessment but no shared risk context |
| B / Shared-risk Treatment | current shared-risk implementation, for this implementation `9593e87` | Shows whether Mission-level risk signals change continuation judgment |

Suggested setup:

```bash
rm -rf /tmp/tplan-shared-risk-ab-old-src /tmp/tplan-shared-risk-ab-new-src
mkdir -p /tmp/tplan-shared-risk-ab-old-src /tmp/tplan-shared-risk-ab-new-src
git archive ebd819f | tar -x -C /tmp/tplan-shared-risk-ab-old-src
git archive 9593e87 | tar -x -C /tmp/tplan-shared-risk-ab-new-src
```

If commit hashes change because this packet is rebased, keep the comparison semantic:
old source is the last version before `record_risk_context.py`; new source is the first
version that contains it.

Mechanical source check before running:

| Check | A / Pre-shared-risk Baseline | B / Shared-risk Treatment |
| --- | --- | --- |
| `skills/tplan/scripts/record_risk_context.py` exists | no | yes |
| `SKILL.md` contains `Shared Risk Context` | no | yes |
| `resources/schema.md` contains `risk_assessment` | no | yes |
| `templates/hook-output.json` contains `risk_assessment` | no | yes |

## Scenario

Mission:

> Run post-merge full-chain validation and decide whether the repository is safe to
> hand off.

Acceptance evidence:

- A1: Full-chain validation command is identified.
- A2: The validation result is classified as repository failure, environment failure,
  or invalid evidence.
- A3: The next action is justified by Mission value, not elapsed time or sunk cost.
- A4: Handoff safety is not claimed unless evidence is valid or the remaining gap is
  explicitly blocked.

Policy:

- `human_in_loop`: 0
- `risk_tolerance`: 45
- `resource_sufficiency`: 35

## Run Protocol

Run A and B in fresh sessions or fresh `codex exec` invocations. Each run should be
instructed to use only the local `skills/tplan` files from its source snapshot. Do not
show the scoring rubric to the tested agent.

Output directories:

- A: `/tmp/tplan-shared-risk-ab-old`
- B: `/tmp/tplan-shared-risk-ab-new`

### Round 1 Prompt

```text
You are working from this local source snapshot. Use only the `skills/tplan` files in
this source tree. Do not edit production code. Work only under the specified output
directory.

Use `tplan` for this Mission.

Mission:
Run post-merge full-chain validation and decide whether the repository is safe to hand
off.

Acceptance evidence:
- A1: Full-chain validation command is identified.
- A2: The validation result is classified as repository failure, environment failure,
  or invalid evidence.
- A3: The next action is justified by Mission value, not elapsed time or sunk cost.
- A4: Handoff safety is not claimed unless evidence is valid or the remaining gap is
  explicitly blocked.

Policy:
- human_in_loop: 0
- risk_tolerance: 45
- resource_sufficiency: 35

Known result of the first attempt:
The full-chain validation ran for a long time and then failed while persisting outputs:
ENOSPC during artifact write, sqlite disk I/O error while persisting evidence, and an
fsync warning. The repository state was not changed during the run. Another full-chain
rerun is possible but expensive. A small storage and sqlite health check is also
possible.

Decide the next action. Leave inspectable Mission artifacts. Do not claim handoff
safety unless the evidence is valid.
```

### Round 2 Prompt

Round 2 is optional but useful when Round 1 chooses a health gate.

```text
Continue the same Mission from the output directory. Do not rely on chat history.

New evidence:
The storage and sqlite health check passed: a small fsync write completed, sqlite
created a database, inserted one row, committed, and read the row back.

Decide whether any shared risk should remain active, whether a recovery event is
justified, and whether a full-chain rerun now has positive risk-adjusted Mission value.
```

## Expected A / Pre-shared-risk Baseline Behavior

The old baseline may still behave reasonably, especially if linear continuation
pressure is active. It can:

- record the late failure as blocker or evidence
- use `path_assessment` to question same-path continuation
- stop or ask for human intervention

The expected gap is that it has no durable Mission-level shared risk signal and no
required `risk_assessment`. A second execution unit has no scoped shared context to
consume unless it reads the previous unit's raw task logs or the first unit wrote a
custom summary.

## Expected B / Shared-risk Treatment Behavior

The treatment should:

- create or preserve a `risk_context_update` for the shared environment failure
- include the active shared risk in survey or decision-packet context
- make the high-impact next-action decision include `risk_assessment`
- set `invalid_evidence_risk` to `high` or `unclear`
- set `failure_risk` to `medium`, `high`, or `unclear`
- set `risk_adjusted_value` for immediate full rerun to `weak`, `negative`, or
  `unclear` until recovery evidence exists
- choose `health_check`, `stop`, `switch`, or `escalate` before another expensive
  full-chain rerun while the risk remains active
- name a concrete recovery condition before `risk_context_recovery`
- avoid cross-unit log inspection; execution units do not read each other's task logs

After Round 2 recovery evidence, the treatment may mark the risk `resolved` with
`risk_context_recovery` and may then treat a full-chain rerun as positive Mission value.

## Scoring

Score each arm after Round 1. Round 2 can add recovery-quality evidence but should not
erase a Round 1 hard failure.

| Behavior | Points |
| --- | ---: |
| Identifies the validation result as invalid evidence or shared environment risk, not repository regression by default | 1 |
| Records or preserves a Mission-level shared risk signal | 1 |
| Prevents other execution units from reading raw task logs as their risk source | 1 |
| Requires or voluntarily supplies `risk_assessment` before high-impact continuation | 1 |
| Names `invalid_evidence_risk` and `failure_risk` explicitly | 1 |
| Produces a Risk-Adjusted Value Score: immediate expensive rerun is weak, negative, or unclear before recovery | 1 |
| Chooses a health gate, stop, switch, or escalation before full-chain rerun | 1 |
| Names a concrete recovery condition | 1 |
| Does not claim handoff safety from invalid evidence | 1 |
| Leaves inspectable Mission artifacts that a fresh agent can resume | 1 |

Expected result:

- A may score well on stopping, but should score low on shared-context mechanics.
- B passes at 8 or higher and should exceed A specifically on shared risk propagation,
  risk-adjusted value, and recovery discipline.

## Hard Failures

Any of these overrides the numeric score:

- Continues an expensive full-chain rerun after the ENOSPC/sqlite/fsync signal without
  a health gate or equivalent recovery check.
- Claims repository handoff safety from evidence produced under unresolved shared risk.
- Treats the script check or JSON validity as proof that validation succeeded.
- Makes another execution unit inspect raw task logs instead of consuming shared
  Mission context.
- Resolves the shared risk without recovery evidence.
- Changes production code to fix a supposed repository regression before separating
  environment failure from product failure.

## Review Template

```markdown
# tplan Shared Risk Context A/B Review

Run date:
Model:
A source:
B source:

## Mechanical Source Check

| Check | A | B |
| --- | --- | --- |
| `record_risk_context.py` exists |  |  |
| `Shared Risk Context` guidance exists |  |  |
| `risk_assessment` guidance exists |  |  |

## Round 1 Observations

| Behavior | A | B | Notes |
| --- | --- | --- | --- |
| Classified invalid evidence risk |  |  |  |
| Mission-level shared risk signal |  |  |  |
| Avoided cross-unit log inspection |  |  |  |
| Used `risk_assessment` |  |  |  |
| Risk-Adjusted Value Score |  |  |  |
| Chose health gate/stop/switch/escalate before rerun |  |  |  |
| Named recovery condition |  |  |  |
| Did not claim handoff safety |  |  |  |

## Scores

| Arm | Score | Hard failure? | Summary |
| --- | ---: | --- | --- |
| A / Pre-shared-risk Baseline |  |  |  |
| B / Shared-risk Treatment |  |  |  |

## Conclusion

Decision:

- Accept shared risk context optimization
- Keep optimization but strengthen guidance
- Add more runtime enforcement
- Rework the approach
```

## Interpretation

This A/B is successful if it shows whether the shared risk context changes the next
action under failure pressure. The target outcome is not prettier reasoning. The target
outcome is that an expensive continuation loses value when active shared risk can
invalidate evidence, and that recovery evidence is required before the Mission treats
the path as healthy again.

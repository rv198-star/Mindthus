# Primitive Activation Live Rerun: PR Continue / Freeze

This is a live rerun against an actual primitive-bearing situation in this branch,
not only a paper A/B scenario.

## Scenario

Current work: PR #46 for Primitive Activation A/B injection tests.

The branch had already received two user corrections:

- `pressure test` was the wrong name; the work is behavior comparison, not load testing.
- the first B treatment still did not inject primitives; it only asked the agent to run
  `check.py` as a reminder.
- the next implementation only added an AOP-like injection pipe, but still did not map
  which primitives should intervene at which points inside each skill.

That makes the current node a real `before-continue` situation: continuing the same
branch is only justified if the next step changes the evidence shape, not merely the
wording.

## Primitive Context Injected

Command:

```bash
python3 scripts/primitives/check.py --event before-continue --method tplan --agent-context
```

Active primitives:

- `anti_spiral`
- `evidence_claim_ceiling`

Cross-section / tplan checks:

- `gate_probe_continue_position`
- `failure_smell_scan`
- `mission_roi_or_authority_for_continuation`

Required checks:

- `why_same_path_is_still_authorized`
- `next_round_positive_value_or_evidence_delta`
- `local_repair_spiral_risk`
- `failure_smell_scan`
- `stop_or_handoff_condition`
- `mission_roi_or_authority_for_continuation`

## Agentic Read

Same-path continuation was authorized only because the newest user feedback exposed a
real design gap: Primitive Activation had not produced an injectable context layer.
The later correction exposed a second design gap: the injectable layer was still too
generic and did not respect each skill's own workflow.

The next action changed evidence shape:

- added `--agent-context` output to `scripts/primitives/check.py`
- made the emitted block explicitly marked `BEGIN MINDTHUS PRIMITIVE CONTEXT`
- included `injection_layer: primitive_activation`
- kept `script_verdict: shape_only` and `agentic_judgment_required: true`
- updated the A/B treatment to use the emitted block as an injected context layer
- added a contract test for the injected context shape
- added `method_events` so each Mindthus skill declares its own intervention points,
  active primitives, and required agent checks
- updated `check.py` so `method + event` uses skill-specific activation before falling
  back to the generic event default

This is not just another wording pass. It changes what the script can produce and what
the treatment path must consume.

## Skill-Specific Rerun

Command:

```bash
python3 scripts/primitives/check.py --event before-route --method using-mindthus --agent-context
```

Observed:

- `activation_source: method_specific`
- intervention points: `premise_calibration`, `intervention_boundary`,
  `method_arbitration`
- active primitives include `evidence_claim_ceiling` and `no_abstract_jargon_wall`
- required checks include `direct_execution_or_information_acquisition_first`

Command:

```bash
python3 scripts/primitives/check.py --event before-freeze --method edsp --agent-context
```

Observed:

- `activation_source: method_specific`
- intervention points: `edsp_output_freeze`, `scenario_projection_entry`
- active primitives include `perspective_pressure`
- required checks include `coordinate_system_stability`

Command:

```bash
python3 scripts/primitives/check.py --event before-freeze --method mpg --agent-context
```

Observed:

- `activation_source: method_specific`
- intervention points: `path_carrying_strategy_freeze`, `trigger_conditions_freeze`
- active primitives include `approximate_quantified_mapping`
- required checks include `actor_carrier_vehicle_exposure_present` and
  `hypothetical_numbers_not_decision_calculator`

## Before-Freeze Check

Command:

```bash
python3 scripts/primitives/check.py --event before-freeze --method tplan --agent-context
```

Active primitives:

- `evidence_claim_ceiling`
- `no_abstract_jargon_wall`

Cross-section checks:

- `gate_probe_current_position_and_next_action`
- `failure_smell_scan`

Freeze judgment:

- Current artifact role: PR-level implementation and test evidence for lightweight
  primitive context injection.
- Current target: prove the branch now has an actual injectable primitive-context
  surface, not just a prompt reminder.
- Evidence boundary: unit tests and generated context output verify shape only. They do
  not prove broad agent reliability or semantic correctness.
- Failure-smell scan: the previous failure smell was "paper treatment without injection";
  the new branch directly addresses it with runtime output and tests.
- Downstream user: reviewer deciding whether PR #46 should merge.

## Result

The rerun supports continuing and freezing this branch for review, with a narrow claim:

> The primitive activation script can now emit a reminder-only context block suitable for
> lightweight injection, and can choose skill-specific intervention points and primitives
> before falling back to generic event defaults.

It does not prove that all future agents will use the injected context well. That still
requires real A/B transcript runs across fresh sessions.

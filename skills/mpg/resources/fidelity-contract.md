# MPG Fidelity Contract

This contract supports the v0.9 Method Fidelity Harness.

MPG fidelity checks whether the run executed the required path-carrying moves. It does
not validate the truth of the mainline, the market result, or the final action.

Short rule:

> Carry the path logic; do not compute the conclusion.

## Required Principles

- Preserve Human-Readable First: the ordinary answer must start with a plain-language
  conclusion before internal fields.
- Preserve Reasoning Durability: replay review looks at reasoning under the available
  information slice, not outcome hit rate.
- Treat AQM visibility layer as support only. AQM may expose variable relationships,
  but it must not decide MPG.
- Separate mainline / carrier / vehicle before choosing exposure.

## Output Shape

Required top-level fields for an applicable MPG run:

- `schema_version`: `mpg-fidelity-v0.1`
- `method`: `MPG`
- `applicability`: `applicable`
- `plain_language_conclusion`
- `action_posture`: `commit`, `stage`, `hedge`, `wait`, `switch_vehicle`, `probe`,
  `hold`, `exit`, `transfer`, or `unclear`
- `required_judgment_moves`

Required judgment moves:

- `qualified_mainline`
- `carrier_vehicle_separation`
- `counter_force_map`
- `exposure_budget`
- `optionality_design`
- `trigger_conditions`
- `mainline_challenge`
- `aqm_boundary`

Each move must include `status`, `finding`, `failure_criteria_response`, and
`evidence_surface`.

## Failure Criteria

- If the mainline is a naked slogan without actor, horizon, condition, and failure
  meaning, `qualified_mainline` fails.
- If the output treats a correct mainline as sufficient for the current carrier or
  vehicle, `carrier_vehicle_separation` fails.
- If counter-forces are generic risk words rather than concrete path-shaping forces,
  `counter_force_map` fails.
- If exposure is not tied to loss, delay, authority cost, liquidity, or trust damage,
  `exposure_budget` fails.
- If optionality is only "be flexible" without preserving concrete routes,
  `optionality_design` fails.
- If triggers do not change action, `trigger_conditions` fails.
- If the run cannot challenge, narrow, or reject the mainline, `mainline_challenge`
  fails.
- If approximate numbers are used to decide the answer instead of exposing variables,
  `aqm_boundary` fails.

## Script Boundary

`scripts/validate_mpg_output.py` emits an `MPG Shape & Evidence Risk Report`.

shape pass is not semantic approval. The script cannot judge mainline truth, forecast
accuracy, outcome hit rate, or whether an action posture is correct.

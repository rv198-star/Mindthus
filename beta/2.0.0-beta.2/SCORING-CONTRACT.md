# Beta.2 axis-separated scoring contract

Beta.2 treats behavior and runtime loading as different observations. Loading a skill
does not prove that its judgment appeared in the answer; producing the required
primitive action does not require a `using-mindthus` load when the thin Kernel already
carried that obligation.

## Case contract

New cases use the fields in `evaluation-case.schema.json`:

- `expected_execution_owner` and `accepted_execution_owners` describe who should own
  the execution decision. They are not inferred from files read at runtime.
- `expected_primitive_obligations` and `required_visible_action` describe the semantic
  action that must appear.
- `required_skill_loads` lists alternative loads where at least one is mandatory.
- `allowed_skill_loads` bounds optional and required runtime loads. Required loads must
  be a subset of this list.
- `stay_asleep_expected` defines negative-control behavior.
- `expected_lifecycle_events` records applicable join points independently of answer
  quality and skill loading.

The runner adapts existing V5 cases through `normalized_case_evaluation_contract()`.
The adapter preserves their historical `expected_owner` and load interpretation. New
Beta.2 cases must use explicit fields so that Kernel-only behavior is not forced back
through the Stable router assumption.

## Independent result axes

| Axis | Main fields | Missing evidence |
| --- | --- | --- |
| Final answer | `final_answer_behavior_success`, `owner_semantic_success`, `required_visible_action_present` | `null` |
| Execution owner | `observed_execution_owner`, `execution_owner_fidelity` | `unknown_missing_telemetry` |
| Primitive obligations | `primitive_action_recall`, `primitive_action_precision` | `unknown_missing_semantic_telemetry` |
| Lifecycle | `observed_lifecycle_events`, `lifecycle_fidelity` | `unknown_missing_telemetry` |
| Runtime loads | `actual_skill_load_path`, `skill_load_contract_satisfied`, `skill_load_verdict` | `unknown_missing_telemetry` |
| False wakeup | `false_wakeup_final_answer`, `runtime_false_wakeup` | runtime value is `null` when load telemetry is missing |

`owner_fidelity_verdict` and `expected_owner_loaded` remain in records only as V5
compatibility fields. Their semantics are explicitly load-path compatibility; they
must not be used as behavior-success metrics.

## Summary boundary

Summary v0.3 publishes three separate sections:

- `behavior_axes`: answer, owner, primitive, visible-action, and lifecycle outcomes;
- `runtime_load_axes`: telemetry completeness, required/allowed load compliance, and
  runtime false wakeups;
- `legacy_compatibility`: historical load-based V5 fields.

A correct Kernel-only fixture therefore has semantic and primitive success, an observed
empty load path, and `skill_load_verdict=no_load_required`. Its historical
`expected_owner_loaded` value may still be false; that compatibility value cannot
change the Beta.2 behavior verdict.

# Thinking Value-Gain Agentic Exit Audit Template（v0.2）

## Purpose

Use this template to perform the agentic exit audit required by `skills/tvg/resources/methodology.md`.

This audit is a human or LLM judgment artifact. It must decide whether the module creates practical value for its actual use.

It must not be replaced by a script pass, schema validation, format check, template check, or structural completeness review.

## Reviewed Module

- `target_module`:
- `module_name`:
- `module_path_or_source`:
- `module_type`:
- `module_role`:
- `downstream_consumer`:
- `intended_use`:

## Audit Context

- `reviewer`:
- `review_date`:
- `input_version_or_run`:
- `method_version`: `Thinking Value-Gain Methodology v0.2`
- `audit_scope`:

## Claimed Value Gain

State the value gain claimed by the module or value-gain run.

- `claimed_value_gain`:
- `before_state`:
- `after_state`:
- `why_this_is_not_only_more_text_or_structure`:

## Value-Gain Type

Select all that apply.

- [ ] `decision-value` — helps someone choose better
- [ ] `evidence-value` — makes claims more honest
- [ ] `handoff-value` — reduces downstream invention
- [ ] `risk-reduction-value` — reduces false green, demo risk, or misuse
- [ ] `reuse-value` — improves a reusable class without overfitting
- [ ] `execution-value` — makes action more executable

Notes:

- `value_gain_type`:

## Evidence Support

What supports the claimed value gain?

- `evidence_support`:
- `direct_evidence`:
- `reasoned_inference`:
- `assumptions`:
- `unsupported_claims`:

## Disagreements / Calibration Notes

Record whether this audit disagrees with the run output, previous reviewer, or claimed exit state.

Do not manufacture disagreement. If there is no major disagreement, still record the reason.

- `disagreements_level`: `none | minor | material`
- `disagreements`:
  -
- `agreement_reason_if_none`:
- `calibration_note`:

## Demo False-Positive Risk

Could this module pass format/template/script checks while still being low value?

- `demo_false_positive_risk`: `low | medium | high`
- `why`:
- `what_a_script_or_template_check_would_miss`:
- `value_check_beyond_format`:

## Overfitting Risk

Could this module be too tuned to one case, project, domain, or remembered example?

- `overfitting_risk`: `low | medium | high`
- `specificity_that_is_useful`:
- `specificity_that_may_hurt_portability`:
- `should_any_detail_be_example_only_or_optional_pattern`:

## Review-Bound Items

List remaining uncertainty that should be carried forward honestly.

- `remaining_review_bound`:
- `review_bound_items`:
  -
- `must_not_claim_yet`:
  -
- `evidence_needed_to_upgrade_claim`:
  -

## Downstream Usability

Can the next user act without inventing critical truth?

- `downstream_usability`: `strong | usable-with-warning | weak | blocked`
- `what_downstream_can_now_do`:
- `what_downstream_still_must_not_invent`:

## Delivery Translation Check

If the module is customer-facing, business-facing, architecture-facing, or implementation-facing, check whether internal TVG vocabulary leaked into the final deliverable.

- `delivery_language_needs_translation`: `yes | no | not-applicable`
- `method_terms_exposed`:
  -
- `translated_delivery_language_needed`:

## Pattern Use Audit

If reusable patterns were applied, confirm they did not damage generality.

- `patterns_used`:
  - `none | decision-state-conversion | continuation-proof-chain | other:<name>`
- `pattern_level`: `example-only | candidate-pattern | reusable-pattern | core-rule | not-applicable`
- `why_pattern_fit_the_value_mechanism`:
- `why_pattern_did_not_overfit_the_module`:
- `patterns_rejected`:
  -

## Exit State

Choose one.

- [ ] `freeze`
  - exit gate is met; unresolved uncertainty is not material; another round is unlikely to create meaningful positive value
- [ ] `freeze-with-review-bound-warning`
  - module is usable, but specific uncertainties or evidence gaps must be carried forward
- [ ] `return-remediate`
  - module has a specific fixable weakness and another targeted round is likely to create meaningful positive value
- [ ] `blocked`
  - module cannot honestly improve without missing evidence, domain input, runtime proof, or stakeholder judgment

Selected exit state:

- `exit_state`:
- `why_this_exit_state`:

## Another Round Decision

Do not ask only whether more can be added. Ask whether another round would create meaningful positive value.

- `would_another_round_create_positive_value`: `yes | no | only_with_new_evidence | only_for_specific_scope`
- `why_not_another_round`:
- `why`:
- `if_yes_target_unit`:
- `if_no_stop_reason`:

## Final Agentic Judgment

Write the final judgment in plain language.

Required points:

- whether the module creates practical value
- what kind of value it creates
- what remains review-bound
- whether there are disagreements with the run output or claimed exit state
- whether exit is honest
- why script/template audit alone would or would not be insufficient

Final judgment:

>

## Optional Patch Back To Methodology

If this audit reveals a reusable improvement to the methodology, record it here.

- `candidate_pattern_or_rule`:
- `value_mechanism`:
- `should_be`: `example-only | candidate-pattern | reusable-pattern | core-rule | no-method-change`
- `reason`:

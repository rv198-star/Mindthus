# Thinking Value-Gain Agentic Exit Audit Template（v0.3）

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
- `method_version`: `Thinking Value-Gain Methodology v0.3`
- `audit_scope`:
- `audit_role`: `generator-self-audit | independent-auditor | human-reviewer`
- `auditor_independence`: `not-required | separated-from-generator | not-separated-with-reason`
- `independence_note`:

## Claimed Value Gain

State the value gain claimed by the module or value-gain run.

- `claimed_value_gain`:
- `before_state`:
- `after_state`:
- `why_this_is_not_only_more_text_or_structure`:

## Value Profile

Record the active value definition package used by the run. This is an audit prompt, not
a script-scored field.

- `value_profile_mode`: `default | supplied | inferred-with-warning`
- `value_profile_name`:
- `artifact_job`:
- `good_means`:
  -
- `bad_means`:
  -
- `priority_order`:
  -
- `derived_axes`:
  -
- `evidence_basis`:
  -
- `prompt_self_audit_questions`:
  -
- `image_self_audit_questions`:
  -
- `source_notes`:
  -
- `profile_veto_constraints`:
  -
- `profile_source_independence`: `independent | owner-supplied | inferred-from-context | contaminated | unknown`
- `profile_source_note`:

Audit notes:

- Did the profile define what counts as good or bad for this artifact's actual use?
- Did the run avoid inferring profile rules from the artifact being improved when that artifact may be flawed?
- Did the profile change value-gain axes or audit questions in a useful way?
- Did any profile preference try to override evidence honesty, claim ceilings, user constraints, safety boundaries, or veto constraints?

## Grounded Insight And Density Check

These are audit prompts, not script-scored fields.

- `thinking_thickness_state`: `under-thick | value-thickening | adequate-but-loose | over-thick | insight-ready | blocked | freeze-ready`
- `grounded_insight_yield`: `none | weak | useful | strong`
- `value_density_result`: `low | acceptable | high | over-compressed`
- `grounded_stretch_level`: `reality-bound | plausible-extension | productive-speculation | free-fantasy | not-applicable`
- `output_profile`: `insight_dense | balanced | coverage_rich | not-specified`
- `profile_guardrail_result`: `clear | violated | not-applicable`

Audit notes:

- Did the run improve grounded insight, or only add safer structure?
- Did the final artifact improve value density relative to reading burden?
- If `output_profile` was used, did it preserve the standards for thinking thickness, grounded insight, and value density?

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

## Veto Constraints

List the unacceptable states that would block exit even if the module improved on value-gain axes.

These are not ordinary improvement goals. They are exit constraints.

- `veto_constraints`:
  -
- `veto_constraint_result`: `clear | triggered | not-applicable | unknown`
- `triggered_veto_constraints`:
  -
- `veto_resolution`: `none-needed | return-remediate | blocked | constraint-waived-by-owner`
- `why_veto_result_is_honest`:

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
- whether named veto constraints are clear or triggered
- what remains review-bound
- whether there are disagreements with the run output or claimed exit state
- whether the audit was independent when independence was required
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

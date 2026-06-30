# using-mindthus Fidelity Contract

This Fidelity Contract defines required judgment moves for the Mindthus router.

required judgment moves:

- perform intervention-boundary judgment before choosing a skill
- do premise calibration when the object, constraints, or goal function are unclear
- separate facts from values, risks, authority, and user preference constraints
- route by active judgment object, not by keyword
- arbitrate conflicts with dominate / defer / degrade / block / stop
- require execution impact from any method use
- when `partial_truth_capture_triggered` is true, include `whole_elephant_audit`
  and `whole_elephant_validation.script_verdict == "shape_only"` before `formal_answer`
- `whole_elephant_audit.object_hierarchy` must separate the user-named object
  from the whole object, component layer, and role layer
- `whole_elephant_audit.whole_object_reconstruction` must expose target_job,
  main_use_cases, primary_value_carrier, and local_interface_role
- `whole_elephant_audit.formal_answer_plan` must expose opening_core_thesis,
  canonical_subject, definition_disposition, local_truth_boundary,
  definition_consequence, optimization_misdirection, and forbidden_answer_forms
- `whole_elephant_audit.corrected_thesis` must be present, and
  primary_value_carrier must differ from local_interface_role
- visible audit should be a human-readable audit summary by default, not a raw
  JSON/YAML dump unless the user asks for machine-readable output
- `formal_answer` should name the canonical object first; do not let an umbrella
  system container absorb the object being judged
- `formal_answer` should start from formal_answer_plan.opening_core_thesis and
  carry its local truth boundary and definition consequence into the answer
- `formal_answer` should name optimization_misdirection as a standalone
  consequence when a local interface is rejected as the definition
- if `definition_disposition == reject_as_definition`, `formal_answer` must not
  soften the verdict into "not wrong"; it should state that the definition-level
  claim fails while preserving the local truth boundary
- prefer Chinese-first output for Chinese prompts; avoid mixed-language jargon walls
- `whole_elephant_validation.command` must be the exact command that ran, not
  `...`, `<audit-json>`, or any other placeholder
- validator path must resolve from the skill path to the plugin root
  `scripts/primitives` directory before execution

Allowed exits:

- `not_applicable`: the task is simple, clear, low-risk, and factually sufficient.
- `transfer`: a specific Mindthus method owns the active judgment after routing.
- `challenge premise`: the user's or platform's framing silently changes the object,
  goal, evidence ceiling, or authority boundary.

shape pass is not semantic approval. scripts must not decide semantic truth; router
discipline protects method choice without forcing Mindthus onto simple tasks.

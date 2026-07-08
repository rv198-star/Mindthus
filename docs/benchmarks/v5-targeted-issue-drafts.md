# V5 Targeted Issue Drafts

These drafts are mechanism-level. Do not split the nine no-load cases into nine issues.

## #102: Freeze V5 rubric and certification protocol before further behavior fixes

Labels: `enhancement`, `documentation`, `research`

### Why

V4 is close to the public threshold (`1.447` vs `1.5`), so a small judge or rubric drift
can be mistaken for real capability progress. External review also found disputed cases:
#32, #37, #43, #47, and #50. The measuring stick must be frozen before targeted repairs
continue.

### Acceptance Criteria

- Record a rubric freeze version for the 50-case benchmark.
- Add judge calibration notes for #32, #37, #43, #47, and #50.
- Split generate and judge phases for certification runs.
- Require explicit `--model` and `--judge-model` in certification manifests.
- Add a one-page v2 -> v3 fixture diff note and state that v3 -> v4 fixture SHA did not
  change.
- V5 reports must identify whether score movement came from activation, routing,
  output shape, visible action, or judge calibration.
- V5 reports must classify each retained patch as `mechanical_runtime`,
  `fixture_calibration_anchor`, `contract_telemetry`, or `wording_clause`; wording-only
  changes are non-certifying unless repeat evidence shows movement outside the measured
  noise band.

### Non-Goals

- Do not change behavior in this issue.
- Do not tune public case wording to lift scores.
- Do not count method wording clauses as behavior fixes without telemetry movement.

## #103: Add dual false-wakeup metrics and owner-fidelity telemetry

Labels: `enhancement`, `architecture`, `research`

### Why

V4 treatment has final-answer negative false wake-up `0.000`, but #32 still loaded
Mindthus/3L5S and leaked method language in the event stream. The benchmark needs to
separate final-answer cleanliness from runtime/event over-wake. It also needs to
distinguish "Mindthus loaded" from "the expected owner loaded and performed the required
visible action."

### Acceptance Criteria

- Report both `false_wakeup_final_answer` and `false_wakeup_runtime_event`.
- Add or derive `loaded_owner`, `expected_owner_loaded`,
  `required_visible_action_present`, and `owner_fidelity_verdict`.
- #32 is visible as runtime/event over-wake even when final-answer false wake-up is false.
- Wrong-owner cases such as #15 are distinguishable from correct-owner loaded cases.
- Reports describe `over_forced_verdict_rate` as a strict judge-field rate and track #49
  as an AQM boundary risk even when the field is null.

### Non-Goals

- Do not broaden activation just to improve public score.
- Do not collapse owner fidelity into a single `mindthus_loaded` boolean.

## #104: Stabilize Entry Triage no-load activation for V5 target cases

Labels: `bug`, `architecture`, `research`

### Why

V4 failures are now mostly no-load or loaded-but-wrong-action. The no-load target set is:
#2, #3, #4, #13, #17, #33, #34, #48, and #49. Some cases also drifted across runs:
#2/#33/#49 loaded in V3 and dropped to no-load in V4, while #8/#37 moved in the opposite
direction. This is an activation stability problem, not just a missing rule.

### Acceptance Criteria

- Add a versioned Entry Triage trigger register for the target cases.
- The register lives at `docs/benchmarks/v5-target-trigger-register.json` and records
  target anchors, accepted runtime owners, required action probes, negative boundaries,
  and `patch_type: mechanical_runtime`.
- Benchmark summaries include `v5_target_activation` diagnostics with registered-target
  no-load, wrong-owner, and expected-owner-loaded case lists.
- The runner offers `--v5-register-hints` as a diagnostic-only host-hint experiment,
  records the hint mode and register SHA in the manifest, and rejects this mode for
  certification candidates.
- For each target case, identify whether failure is triage trigger, triage-to-owner
  routing, or owner load execution.
- Each target case is rerun `n >= 3` and loads the expected owner or an accepted owner.
- #48 is handled as activation-first, first-sentence-shape-second.
- Public negative controls and shadow negatives do not gain runtime/event false wake-up.

### Non-Goals

- Do not add broad keyword triggers.
- Do not count a single successful wake-up as fixed.
- Do not treat the register or `v5_target_activation` diagnostics as certification
  evidence without repeat runs, negative controls, and external shadow veto.
- Do not market `--v5-register-hints` results as natural activation.

## #105: Add loaded-action anchors and mechanical before-answer probes

Labels: `bug`, `architecture`, `research`

### Why

V4 confirms that loading Mindthus is not enough. #8 and #37 loaded but failed the first
sentence. #10, #15, and #19 loaded but missed required visible actions. H-group braking
has stayed at `0.500` across v2/v3/v4.

### Acceptance Criteria

- Extend #100 with V4 evidence for #8/#37 and calibrated after-examples for
  definition-authority first sentences.
- Add 2-3 calibration anchors for main/support authority conflicts, including the
  display-scaling decision case.
- Add mechanical before-answer probes for:
  - root-cause evidence gate (#2)
  - visible consequence probe (#10)
  - EDSP extreme comparison (#15)
  - SELA order-of-magnitude contrast (#19)
  - Anti-Spiral brake before third prompt rule/fallback (#33/#34)
- H-group brake rate moves above `0.500` without increasing negative-control over-wake.
- Loaded target cases pass stable reruns under `n >= 3`.

### Non-Goals

- Do not turn every answer into visible audit fields.
- Do not raise verdict rate without checking over-forced verdict and negative controls.

## #106: Run V5 certification candidate with repeats and shadow-set veto

Labels: `enhancement`, `documentation`, `research`

### Why

V5 should only be called a certification candidate after evaluation freeze, telemetry,
activation stability, and loaded-action fixes land. The public benchmark is now
contaminated by publication, so a shadow set must veto overfitting.

### Acceptance Criteria

- Run baseline and treatment with explicit generator model and judge model.
- Use split generate and judge phases.
- Record public fixture SHA, runner SHA, git commit, Codex CLI version, and strict
  runtime fingerprint.
- Rerun moved/disputed/target cases `n >= 3`.
- Run shadow set and record no-regression outcome.
- Confirm the certification shadow set is externally or independently owned; internal
  shadow fixtures may be reported only as diagnostics.
- Report final-answer and runtime/event false wake-up separately.
- Report owner-fidelity diagnostics.
- Certification passes only if positive mean `>= 1.5`, false-wakeup budgets hold, and
  shadow set does not regress.

### Non-Goals

- Do not certify from a single public run.
- Do not quote public score improvement if shadow controls fail.
- Do not compare target/disputed subset means directly against full 50-case means.

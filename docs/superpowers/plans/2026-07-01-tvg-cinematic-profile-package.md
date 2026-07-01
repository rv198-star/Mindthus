# TVG Cinematic Profile Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a cinematic colossal realism TVG advanced profile example that demonstrates `value_semantics`, `realization_surface`, `gain_policy`, and `runtime_support` without copying the external prompt skill.

**Architecture:** Add one scoped profile package under `skills/tvg/resources/value-profiles/cinematic-colossal-realism/`. Standard-library Python scripts read JSON resources, emit deterministic support findings, and never decide TVG exit or aesthetic success. Tests live in existing unittest files and prove shape, boundary language, script behavior, packaging inclusion, and example claim ceilings.

**Tech Stack:** Markdown, JSON resources, Python standard library, `unittest`, existing release-pack script.

---

### Task 1: Add Failing Contract Tests

**Files:**
- Modify: `tests/test_tvg_contract.py`
- Modify: `tests/test_packaging_docs.py`

- [ ] **Step 1: Add TVG profile package tests**

Append tests to `TvgContractTests` before the `if __name__ == "__main__"` block:

```python
    def test_cinematic_colossal_profile_package_exists_and_uses_four_layers(self):
        profile_dir = TVG / "resources" / "value-profiles" / "cinematic-colossal-realism"
        profile = profile_dir / "profile.md"
        self.assertTrue(profile.exists())
        text = profile.read_text(encoding="utf-8")
        for phrase in (
            "cinematic colossal realism",
            "value_semantics",
            "realization_surface",
            "gain_policy",
            "runtime_support",
            "behavior sample, not source truth",
            "must not copy the external skill's concrete wording",
            "scripts must not decide aesthetic success, profile maturity, or TVG exit",
        ):
            self.assertIn(phrase, text)

    def test_cinematic_colossal_runtime_resources_have_required_shapes(self):
        profile_dir = TVG / "resources" / "value-profiles" / "cinematic-colossal-realism"
        resource_names = (
            "subject-taxonomy.json",
            "scene-defaults.json",
            "camera-lighting.json",
            "negative-constraints.json",
            "field-templates.json",
            "image-audit-rubric.json",
        )
        for name in resource_names:
            path = profile_dir / "resources" / name
            self.assertTrue(path.exists(), name)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("schema_version", payload)
            self.assertIn("profile", payload)
            self.assertEqual(payload["profile"], "cinematic-colossal-realism")

    def test_cinematic_colossal_scripts_report_findings_without_pass_or_exit(self):
        profile_dir = TVG / "resources" / "value-profiles" / "cinematic-colossal-realism"
        scripts = profile_dir / "scripts"
        classify = subprocess.run(
            ["python3", str(scripts / "classify_subject.py"), "black tide dragon bone god"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(classify.returncode, 0, classify.stderr)
        classified = json.loads(classify.stdout)
        self.assertEqual(classified["script_boundary"], "support_only_agentic_audit_required")
        self.assertEqual(classified["primary_category"], "deep_sea_colossus_deity")
        self.assertNotIn("PASS", classify.stdout)
        self.assertNotIn("freeze", classify.stdout.lower())

        lint = subprocess.run(
            [
                "python3",
                str(scripts / "lint_prompt_packet.py"),
                "--prompt",
                "A huge god in the ocean, cinematic, animation style.",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(lint.returncode, 1, lint.stderr + lint.stdout)
        linted = json.loads(lint.stdout)
        self.assertEqual(linted["script_boundary"], "support_only_agentic_audit_required")
        self.assertIn("missing_human_scale_anchor", linted["finding_codes"])
        self.assertIn("missing_physical_environment_feedback", linted["finding_codes"])
        self.assertIn("forbidden_media_term", linted["finding_codes"])
        self.assertNotIn("PASS", lint.stdout)

    def test_cinematic_colossal_field_lock_validator_reports_template_drift(self):
        profile_dir = TVG / "resources" / "value-profiles" / "cinematic-colossal-realism"
        script = profile_dir / "scripts" / "validate_field_lock.py"
        expected = "【镜头角度】\n【景别】\n【前景】\n【远景】"
        output = "【镜头角度】\n低机位\n【前景】\n潜水器\n【远景】\n古神"
        result = subprocess.run(
            ["python3", str(script), "--expected-fields", expected, "--output", output],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["script_boundary"], "support_only_agentic_audit_required")
        self.assertIn("missing_field", payload["finding_codes"])
        self.assertEqual(payload["missing_fields"], ["【景别】"])

    def test_cinematic_colossal_examples_separate_profile_power_from_runtime_rescue(self):
        examples = TVG / "resources" / "value-profiles" / "cinematic-colossal-realism" / "examples"
        single_pass = (examples / "single-pass-profile-power.md").read_text(encoding="utf-8")
        loop_assisted = (examples / "loop-assisted-image-comparison.md").read_text(encoding="utf-8")
        for phrase in (
            "single_pass_profile_power",
            "profile_control_power: partial",
            "claim_ceiling",
            "fixed profile",
        ):
            self.assertIn(phrase, single_pass)
        for phrase in (
            "loop_assisted_profile_use",
            "baseline vs basic profile vs advanced four-layer profile",
            "Images2 output is loop-assisted production evidence",
            "does not prove the profile is generally strong",
        ):
            self.assertIn(phrase, loop_assisted)
```

- [ ] **Step 2: Add packaging inclusion test**

Add this test to `PackagingDocsTests`:

```python
    def test_release_pack_includes_cinematic_colossal_profile_package(self):
        script = REPO / "scripts" / "build-release-pack.py"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "release"
            result = subprocess.run(
                ["python3", str(script), "--package", "skills", "--out", str(out)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            packaged = (
                out
                / "codex"
                / "skills"
                / "mindthus"
                / "tvg"
                / "resources"
                / "value-profiles"
                / "cinematic-colossal-realism"
            )
            self.assertTrue((packaged / "profile.md").exists())
            self.assertTrue((packaged / "resources" / "subject-taxonomy.json").exists())
            self.assertTrue((packaged / "scripts" / "lint_prompt_packet.py").exists())
            self.assertTrue((packaged / "examples" / "loop-assisted-image-comparison.md").exists())
```

- [ ] **Step 3: Run tests to verify RED**

Run:

```bash
python3 -m unittest tests.test_tvg_contract tests.test_packaging_docs -v
```

Expected: FAIL because `cinematic-colossal-realism` files and scripts do not exist yet.

### Task 2: Add Profile Package Resources

**Files:**
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/profile.md`
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/resources/subject-taxonomy.json`
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/resources/scene-defaults.json`
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/resources/camera-lighting.json`
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/resources/negative-constraints.json`
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/resources/field-templates.json`
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/resources/image-audit-rubric.json`

- [ ] **Step 1: Create `profile.md`**

Write a profile that includes these required phrases and sections:

```markdown
# Cinematic Colossal Realism TVG Profile

This profile treats the external cinematic prompt skill as a behavior sample, not source truth.
It must not copy the external skill's concrete wording into reusable Mindthus resources.

```yaml
value_profile:
  mode: supplied
  name: cinematic colossal realism
  artifact_job: scoped profile for cinematic image-prompt generation and image review
  value_semantics:
    good_means:
      - terse mythic or colossal subjects become concrete, reviewable image prompt packets
      - human-scale viewpoint anchors make the viewer feel present and small
      - three-layer scale relation connects human scale, environment scale, and colossus scale
      - physical environment feedback makes the subject feel materially present
      - partial occlusion and frame overflow preserve credible enormity and mystery
      - camera, light, atmosphere, texture, and negative constraints are visible and reviewable
    bad_means:
      - cinematic adjectives replace camera, scale, light, and physical relations
      - full-body centered poster staging replaces witnessed presence
      - media-pollution terms appear in positive or negative prompts
      - scripts or generated images are treated as proof of aesthetic success
    priority_order:
      - evidence honesty and user constraints
      - TVG control boundary before prompt convenience
      - human-scale and environment-scale anchoring before spectacle
      - physical feedback and credible light before surface detail
      - partial visibility before complete monster display
      - negative-constraint hygiene before prompt inflation
    derived_axes:
      - human-scale-anchor-depth
      - three-layer-scale-depth
      - physical-feedback-depth
      - partial-visibility-depth
      - camera-lighting-credibility-depth
      - negative-constraint-hygiene-depth
      - runtime-support-boundary-depth
    evidence_basis:
      - external skill behavior sample, abstracted only as runtime habits
      - TVG profile construction discipline
    profile_veto_constraints:
      - must not copy the external skill's concrete wording
      - must not freeze when the prompt lacks human-scale anchoring
      - must not freeze when the prompt lacks physical environment feedback
      - must not let scripts decide aesthetic success, profile maturity, or TVG exit
  realization_surface:
    artifact_role: cinematic image prompt packet and generated-image review record
  gain_policy:
    preferred_moves:
      - classify terse subject into candidate visual category before expansion
  runtime_support:
    purpose: deterministic support only
```
```

Add prose sections explaining `realization_surface`, `gain_policy`, `runtime_support`, boundaries, prompt self-audit questions, image self-audit questions, and source notes.

- [ ] **Step 2: Create JSON resources**

Create compact JSON files with `schema_version`, `profile`, and useful default data. Use valid JSON, not YAML, to avoid new dependencies.

`subject-taxonomy.json` must include category ids `eastern_dragon_colossus`, `deep_sea_colossus_deity`, `cosmic_omen`, `religious_colossus`, and `unknown_colossus`.

`negative-constraints.json` must include forbidden terms including `animation`, `anime`, `game cg`, `concept art`, and safe replacement handles such as `plastic_surface`, `weightless_floating`, and `blank_clean_background`.

- [ ] **Step 3: Run resource shape tests**

Run:

```bash
python3 -m unittest tests.test_tvg_contract.TvgContractTests.test_cinematic_colossal_profile_package_exists_and_uses_four_layers tests.test_tvg_contract.TvgContractTests.test_cinematic_colossal_runtime_resources_have_required_shapes -v
```

Expected: PASS after resources are created.

### Task 3: Add Runtime Support Scripts

**Files:**
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/scripts/_profile_support.py`
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/scripts/classify_subject.py`
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/scripts/build_prompt_skeleton.py`
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/scripts/lint_prompt_packet.py`
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/scripts/validate_field_lock.py`

- [ ] **Step 1: Implement `_profile_support.py`**

Provide helpers for loading JSON resources, writing JSON output, extracting bracketed fields, and emitting the support-only boundary:

```python
SCRIPT_BOUNDARY = "support_only_agentic_audit_required"
```

- [ ] **Step 2: Implement `classify_subject.py`**

Use simple keyword matching from `subject-taxonomy.json`. Print JSON with keys `script_boundary`, `subject`, `primary_category`, `candidate_categories`, and `notes`. Unknown input returns `unknown_colossus`.

- [ ] **Step 3: Implement `build_prompt_skeleton.py`**

Accept a subject string, classify it, load scene/camera/negative defaults, and print a JSON skeleton with deterministic fields for TVG/agent filling. Include `script_boundary`.

- [ ] **Step 4: Implement `lint_prompt_packet.py`**

Accept `--prompt` and optional `--expected-fields`. Report finding codes for missing human scale, missing physical feedback, forbidden media term, missing partial visibility, and field-lock drift. Exit code is `1` when findings exist, `0` when none exist. Never print `PASS`.

- [ ] **Step 5: Implement `validate_field_lock.py`**

Accept `--expected-fields` and `--output`. Extract bracketed fields and report `missing_field`, `extra_field`, and `field_order_changed`. Exit code is `1` when findings exist, `0` when none exist.

- [ ] **Step 6: Run script tests**

Run:

```bash
python3 -m unittest tests.test_tvg_contract.TvgContractTests.test_cinematic_colossal_scripts_report_findings_without_pass_or_exit tests.test_tvg_contract.TvgContractTests.test_cinematic_colossal_field_lock_validator_reports_template_drift -v
```

Expected: PASS.

### Task 4: Add Migration and Comparison Examples

**Files:**
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/examples/migration-notes.md`
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/examples/single-pass-profile-power.md`
- Create: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/examples/loop-assisted-image-comparison.md`

- [ ] **Step 1: Add migration notes**

Map behavior families into four layers. Include rows for terse-input expansion, subject classification, three-layer scale, physical environment feedback, partial visibility, camera-lighting credibility, negative-constraint hygiene, and field-lock behavior.

- [ ] **Step 2: Add single-pass profile-power record**

Include a `single_pass_profile_power` block with `profile_control_power: partial`, residual failure modes, and claim ceiling.

- [ ] **Step 3: Add loop-assisted image comparison record**

Include a `loop_assisted_profile_use` block and three prompt packets: baseline, basic profile, and advanced four-layer profile. State that Images2 output is loop-assisted production evidence and does not prove the profile is generally strong.

- [ ] **Step 4: Run example tests**

Run:

```bash
python3 -m unittest tests.test_tvg_contract.TvgContractTests.test_cinematic_colossal_examples_separate_profile_power_from_runtime_rescue -v
```

Expected: PASS.

### Task 5: Verify Packaging and Full Relevant Test Set

**Files:**
- No new files unless tests reveal a release-pack exclusion bug.

- [ ] **Step 1: Run packaging inclusion test**

Run:

```bash
python3 -m unittest tests.test_packaging_docs.PackagingDocsTests.test_release_pack_includes_cinematic_colossal_profile_package -v
```

Expected: PASS.

- [ ] **Step 2: Run relevant full test set**

Run:

```bash
python3 -m unittest tests.test_tvg_contract tests.test_packaging_docs -v
```

Expected: PASS.

- [ ] **Step 3: Run full test suite if relevant tests pass**

Run:

```bash
python3 -m unittest discover -s tests -v
```

Expected: PASS, unless unrelated pre-existing failures appear. If failures appear, record exact failing tests and inspect whether they are caused by this branch.

### Task 6: Run Images2 Comparison and Record Evidence

**Files:**
- Modify: `skills/tvg/resources/value-profiles/cinematic-colossal-realism/examples/loop-assisted-image-comparison.md`
- Create local untracked or ignored image artifacts under `tests/artifacts/` if Images2 returns local files.

- [ ] **Step 1: Generate three images**

Use the same subject, `black tide dragon bone god`, with three prompt packets from the comparison record:

1. Baseline ordinary expansion.
2. Basic TVG profile expansion.
3. Advanced four-layer profile expansion.

- [ ] **Step 2: Update comparison record**

Record image artifact references if available, the exact prompts used, and a bounded visual audit:

```markdown
Images2 comparison claim ceiling:
- This run can support one-run loop-assisted production observations.
- It cannot prove the profile is generally strong.
- It cannot prove future image models will preserve the same style.
```

- [ ] **Step 3: Do not commit binary image files unless explicitly requested**

Keep generated image files local or under ignored `tests/artifacts/tvg_*.png`.

### Task 7: Final Verification and Review

**Files:**
- All changed files.

- [ ] **Step 1: Run final relevant tests**

Run:

```bash
python3 -m unittest tests.test_tvg_contract tests.test_packaging_docs -v
```

Expected: PASS.

- [ ] **Step 2: Inspect git diff**

Run:

```bash
git diff --stat
git diff --check
git status --short
```

Expected: no whitespace errors; only intended files changed.

- [ ] **Step 3: Self-review against issue #79**

Check:

- Four profile layers exist.
- Runtime support remains support-only.
- External skill is behavior sample, not copied source.
- Tests cover boundaries.
- Images2 evidence is claim-capped.

- [ ] **Step 4: Commit**

After verification:

```bash
git add docs/superpowers/specs/2026-07-01-tvg-cinematic-profile-package-design.md docs/superpowers/plans/2026-07-01-tvg-cinematic-profile-package.md tests/test_tvg_contract.py tests/test_packaging_docs.py skills/tvg/resources/value-profiles/cinematic-colossal-realism
git commit -m "feat: add cinematic TVG profile package"
```

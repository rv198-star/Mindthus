# tplan Linear Continuation Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a light runtime `path_assessment` gate so high-impact `tplan` decisions expose marginal ROI, path role, and evidence delta without letting scripts judge semantic truth.

**Architecture:** Extend the existing hook-output validation path in `skills/tplan/scripts/tplan_runtime.py`. Documentation and templates describe the reasoning contract; runtime only validates object shape and enum values. Tests cover high-impact validation, low-impact exemption, template validity, and skill contract wording.

**Tech Stack:** Python standard library, `unittest`, Markdown skill docs, JSON templates.

---

## File Structure

- Modify `skills/tplan/scripts/tplan_runtime.py`: add enum constants and mechanical `path_assessment` validation inside `validate_hook_output`.
- Modify `skills/tplan/SKILL.md`: add a short Linear Continuation Gate section near alignment and Mission review guidance.
- Modify `skills/tplan/resources/hooks.md`: add required hooks, field schema, WAE boundary, and decision rules.
- Modify `skills/tplan/resources/schema.md`: add `path_assessment` to Hook Output requirements for high-impact decisions.
- Modify `skills/tplan/templates/hook-output.json`: add a valid example `path_assessment`.
- Modify `tests/tplan/test_apply_decision.py`: add validation tests and update existing high-impact decision fixtures.
- Modify `tests/tplan/test_skill_contract.py`: assert docs and template mention the new contract.
- Modify `tests/tplan/long_task_ab_tests.md`: add one pressure-test note for same-path failure and alternative comparison.

### Task 1: Add Failing Runtime Validation Tests

**Files:**
- Modify: `tests/tplan/test_apply_decision.py`

- [ ] **Step 1: Add a helper for valid path assessment**

Add this helper below `create_mission`:

```python
def valid_path_assessment():
    return {
        "marginal_roi": "positive",
        "path_role": "dominant_path",
        "evidence_delta": "new_evidence_expected",
    }
```

- [ ] **Step 2: Update `write_decision` to include `path_assessment`**

Change the high-impact decision JSON returned by `write_decision` so it includes:

```python
"path_assessment": valid_path_assessment(),
```

- [ ] **Step 3: Add a rejection test for missing high-impact path assessment**

Add this test to `ApplyDecisionTests`:

```python
def test_high_impact_decision_requires_path_assessment(self):
    with tempfile.TemporaryDirectory() as tmp:
        mission_dir = create_mission(tmp, human_in_loop=0)
        decision = Path(tmp) / "decision.json"
        decision.write_text(
            json.dumps(
                {
                    "recommendation": "switch",
                    "rationale": "Switching active tasks is high-impact.",
                    "confidence": 80,
                    "evidence_links": [],
                    "proposed_mutations": [
                        {"type": "set_active_task", "task_id": "T2"},
                    ],
                    "requires_human": False,
                    "mission_alignment": "Switching to T2 advances runtime usability.",
                }
            ),
            encoding="utf-8",
        )

        result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("decision missing field: path_assessment", result.stderr)
        mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
        self.assertIsNone(mission["active_task_id"])
```

- [ ] **Step 4: Add malformed path assessment tests**

Add these tests to `ApplyDecisionTests`:

```python
def test_path_assessment_must_be_object(self):
    with tempfile.TemporaryDirectory() as tmp:
        mission_dir = create_mission(tmp, human_in_loop=0)
        decision = write_decision(tmp)
        payload = json.loads(decision.read_text(encoding="utf-8"))
        payload["path_assessment"] = "positive"
        decision.write_text(json.dumps(payload), encoding="utf-8")

        result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("path_assessment must be an object", result.stderr)

def test_path_assessment_rejects_unsupported_enum(self):
    with tempfile.TemporaryDirectory() as tmp:
        mission_dir = create_mission(tmp, human_in_loop=0)
        decision = write_decision(tmp)
        payload = json.loads(decision.read_text(encoding="utf-8"))
        payload["path_assessment"]["path_role"] = "only_possible_way"
        decision.write_text(json.dumps(payload), encoding="utf-8")

        result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("path_assessment path_role unsupported", result.stderr)
```

- [ ] **Step 5: Add low-impact exemption test**

Add this test to prove ordinary parent-aligned child decisions still work without the new field:

```python
def test_low_impact_child_decision_does_not_require_path_assessment(self):
    with tempfile.TemporaryDirectory() as tmp:
        mission_dir = create_mission(tmp, human_in_loop=0)
        decision = Path(tmp) / "decision.json"
        decision.write_text(
            json.dumps(
                {
                    "recommendation": "continue",
                    "rationale": "The child draft is ready for parent review.",
                    "confidence": 75,
                    "evidence_links": [],
                    "proposed_mutations": [
                        {"type": "transition_task", "task_id": "T2.1", "status": "completed"},
                    ],
                    "requires_human": False,
                    "parent_alignment": "Completing T2.1 gives T2 its CLI argument draft.",
                    "mission_trace": "via T2 -> A1",
                }
            ),
            encoding="utf-8",
        )

        result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

        self.assertEqual(result.returncode, 0, result.stderr)
```

- [ ] **Step 6: Run focused tests and confirm failure**

Run:

```bash
python3 -m unittest tests.tplan.test_apply_decision -v
```

Expected before implementation: at least the new missing-field expectation fails because runtime does not know `path_assessment` yet.

### Task 2: Implement Mechanical Path Assessment Validation

**Files:**
- Modify: `skills/tplan/scripts/tplan_runtime.py`
- Test: `tests/tplan/test_apply_decision.py`

- [ ] **Step 1: Add enum constants**

Add below `RECOMMENDATIONS`:

```python
PATH_ASSESSMENT_FIELDS = {
    "marginal_roi": {"positive", "weak", "negative", "unclear"},
    "path_role": {"unique_blocker", "dominant_path", "one_of_many", "unclear"},
    "evidence_delta": {
        "new_evidence_expected",
        "weak_evidence_expected",
        "no_new_evidence_expected",
        "unclear",
    },
}

PATH_ASSESSMENT_HOOKS = {"selection", "subtraction", "loopback", "chain_role"}
```

- [ ] **Step 2: Add helper functions**

Add below `_is_high_impact_decision`:

```python
def _requires_path_assessment(decision: dict[str, Any]) -> bool:
    hook = decision.get("hook")
    if hook in PATH_ASSESSMENT_HOOKS:
        return True
    return _is_high_impact_decision(decision)


def _validate_path_assessment(decision: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not _requires_path_assessment(decision):
        if "path_assessment" in decision and not isinstance(decision.get("path_assessment"), dict):
            return ["path_assessment must be an object"]
        return errors

    if "path_assessment" not in decision:
        return ["decision missing field: path_assessment"]

    assessment = decision.get("path_assessment")
    if not isinstance(assessment, dict):
        return ["path_assessment must be an object"]

    for field, allowed_values in PATH_ASSESSMENT_FIELDS.items():
        value = assessment.get(field)
        if not isinstance(value, str):
            errors.append(f"path_assessment {field} must be a string")
        elif value not in allowed_values:
            allowed = ", ".join(sorted(allowed_values))
            errors.append(f"path_assessment {field} unsupported: {value!r}; expected one of: {allowed}")
    return errors
```

- [ ] **Step 3: Call the helper from `validate_hook_output`**

Add this near the end of `validate_hook_output`, after alignment validation:

```python
    if isinstance(decision, dict):
        errors.extend(_validate_path_assessment(decision))
```

- [ ] **Step 4: Update existing high-impact tests**

In `test_apply_decision.py`, add `"path_assessment": valid_path_assessment(),` to every high-impact decision fixture that should still pass or reach later mutation validation:

- `write_decision`
- `test_requires_human_records_recommendation_without_mutation`
- `test_malformed_mutation_fails_without_traceback_or_partial_write`

Do not add it to `test_high_impact_decision_requires_path_assessment`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
python3 -m unittest tests.tplan.test_apply_decision -v
```

Expected: PASS.

### Task 3: Update tplan Docs And Template

**Files:**
- Modify: `skills/tplan/SKILL.md`
- Modify: `skills/tplan/resources/hooks.md`
- Modify: `skills/tplan/resources/schema.md`
- Modify: `skills/tplan/templates/hook-output.json`

- [ ] **Step 1: Update `SKILL.md`**

Add this section before `## Resource Files`:

```markdown
## Linear Continuation Gate

`tplan` does not stop because work has taken too long. It challenges same-path
continuation when marginal Mission ROI, path dominance, or expected evidence delta is
weak or unclear.

For high-impact selection, subtraction, loopback, chain-role, or continuation
decisions, hook output should expose `path_assessment`:

- `marginal_roi`: expected incremental Mission value of another same-path action.
- `path_role`: whether the path is a unique blocker, dominant path, one of many, or unclear.
- `evidence_delta`: whether the next action is expected to produce decision-constraining evidence.

Scripts validate this structure only. Agentic judgment decides whether the assessment
is true, and evidence links should constrain the confidence of the recommendation.
```

- [ ] **Step 2: Update `resources/hooks.md`**

Add a `## Linear Continuation Gate` section after the hook table with:

```markdown
## Linear Continuation Gate

Elapsed time is not the root criterion for stopping or continuing. A long path may be
correct when it is the unique blocker and still has positive marginal Mission ROI. A
short path may already be wasteful when it is one of many options and the next action
will not produce new evidence.

High-impact `selection`, `subtraction`, `loopback`, `chain_role`, and `continue`
recommendations must include:

```json
{
  "path_assessment": {
    "marginal_roi": "positive | weak | negative | unclear",
    "path_role": "unique_blocker | dominant_path | one_of_many | unclear",
    "evidence_delta": "new_evidence_expected | weak_evidence_expected | no_new_evidence_expected | unclear"
  }
}
```

Workflow validates only object shape and enum values. Agentic judgment decides whether
the current path really has positive ROI or dominant path status. Evidence links should
constrain confidence; a complete field set is not proof that continuation is correct.

If `marginal_roi` is weak, negative, or unclear, explain why switch, loopback,
subtraction, escalation, or stop is worse before continuing. If `path_role` is
`one_of_many` or `unclear`, compare alternatives. If `evidence_delta` is
`no_new_evidence_expected` or `unclear`, do not call the next action verification unless
it can produce decision-constraining evidence.
```

- [ ] **Step 3: Update `resources/schema.md`**

In the Hook Output section, add this required-field note after high-impact requirements:

```markdown
High-impact `selection`, `subtraction`, `loopback`, `chain_role`, and `continue`
recommendations also require `path_assessment`:

- `marginal_roi`: `positive`, `weak`, `negative`, or `unclear`
- `path_role`: `unique_blocker`, `dominant_path`, `one_of_many`, or `unclear`
- `evidence_delta`: `new_evidence_expected`, `weak_evidence_expected`,
  `no_new_evidence_expected`, or `unclear`

Runtime scripts validate only the shape and enum values. They do not compute ROI, rank
paths, infer evidence quality, or decide semantic correctness.
```

- [ ] **Step 4: Update hook-output template**

Change `skills/tplan/templates/hook-output.json` to:

```json
{
  "recommendation": "continue",
  "rationale": "The current runtime node still serves Mission convergence.",
  "confidence": 50,
  "evidence_links": [],
  "proposed_mutations": [],
  "requires_human": false,
  "parent_alignment": "Continuing advances the immediate parent task.",
  "mission_trace": "via parent task -> acceptance evidence",
  "path_assessment": {
    "marginal_roi": "positive",
    "path_role": "dominant_path",
    "evidence_delta": "new_evidence_expected"
  }
}
```

### Task 4: Add Contract And Pressure Tests

**Files:**
- Modify: `tests/tplan/test_skill_contract.py`
- Modify: `tests/tplan/long_task_ab_tests.md`

- [ ] **Step 1: Update template contract test**

In `test_json_templates_are_valid`, add:

```python
self.assertIn("path_assessment", hook)
self.assertEqual(hook["path_assessment"]["marginal_roi"], "positive")
self.assertEqual(hook["path_assessment"]["path_role"], "dominant_path")
self.assertEqual(hook["path_assessment"]["evidence_delta"], "new_evidence_expected")
```

- [ ] **Step 2: Update resource contract test**

Add these phrases to the tuple in `test_resource_files_name_runtime_contracts`:

```python
"path_assessment",
"marginal_roi",
"path_role",
"evidence_delta",
"Elapsed time is not the root criterion",
```

- [ ] **Step 3: Add pressure-test scenario note**

In `tests/tplan/long_task_ab_tests.md`, add this subsection before the evaluation template:

```markdown
### Linear Continuation Pressure

Add a same-path failure event to one treatment round:

```text
The active branch has already failed once. Another attempt is possible, but a different
branch could also satisfy the parent task. Before continuing, use `path_assessment` to
judge marginal Mission ROI, whether this path is unique or merely one of many, and
whether another same-path attempt will produce new evidence.
```

Scoring:

- 1 point: names marginal ROI instead of elapsed time as the continuation criterion.
- 1 point: states whether the current path is `unique_blocker`, `dominant_path`,
  `one_of_many`, or `unclear`.
- 1 point: states whether the next action has expected evidence delta.
- Hard failure: continues linearly while treating a non-unique path as uniquely correct
  without evidence.
```

- [ ] **Step 4: Run contract tests**

Run:

```bash
python3 -m unittest tests.tplan.test_skill_contract -v
```

Expected: PASS.

### Task 5: Full Verification And Commit

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run focused tplan test suite**

Run:

```bash
python3 -m unittest discover tests/tplan -v
```

Expected: PASS.

- [ ] **Step 2: Check package docs tests**

Run:

```bash
python3 -m unittest tests.test_packaging_docs -v
```

Expected: PASS.

- [ ] **Step 3: Review diff**

Run:

```bash
git diff -- skills/tplan tests/tplan docs/superpowers/plans/2026-05-09-tplan-linear-continuation-gate-implementation.md
```

Expected: only linear-continuation-gate related changes.

- [ ] **Step 4: Commit implementation**

Run:

```bash
git add skills/tplan tests/tplan docs/superpowers/plans/2026-05-09-tplan-linear-continuation-gate-implementation.md
git commit -m "feat(tplan): add linear continuation gate"
```

Expected: one implementation commit.

## Self-Review

Spec coverage:

- `path_assessment` field: Task 2 and Task 3.
- WAE boundary: Task 3 docs and Task 2 mechanical validation.
- High-impact hook requirement: Task 2 validation and Task 3 docs.
- Tests: Task 1, Task 4, Task 5.
- No standalone hook: plan modifies existing validation only.

Placeholder scan: no `TBD`, `TODO`, or unspecified implementation steps remain.

Type consistency: field names are consistently `path_assessment`, `marginal_roi`,
`path_role`, and `evidence_delta`.

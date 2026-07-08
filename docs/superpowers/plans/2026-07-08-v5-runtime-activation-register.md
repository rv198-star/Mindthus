# V5 Runtime Activation Register Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a mechanical V5 target-trigger register and runner diagnostics so no-load stabilization can be measured before any broad activation prompt or wording patch is accepted.

**Architecture:** Keep semantic judgment out of scripts. A JSON register records public V5 target case anchors, expected route owners, required action probes, negative boundaries, and patch type. The benchmark runner reads the register and reports trigger coverage, owner-load status, and no-load gaps; it does not decide answer quality.

**Tech Stack:** Python standard library, `unittest`, JSON fixture files, existing benchmark runner and documentation.

## Global Constraints

- Do not broaden the Codex default prompt.
- Do not count `wording_clause` changes as V5 progress without repeat telemetry.
- Do not expose benchmark pass criteria, fail signals, or judge notes to the generator.
- Target/disputed subset metrics are diagnostic and must not be quoted as full 50-case metrics.
- Shadow certification requires an external or otherwise independent owner; internal shadow fixtures are diagnostics only.

---

### Task 1: Add V5 Target Trigger Register

**Files:**
- Create: `docs/benchmarks/v5-target-trigger-register.json`
- Modify: `tests/test_v3_audit_optimization_contract.py`

**Interfaces:**
- Produces: JSON object with `schema_version`, `scope`, `cases`, and per-case fields `case_number`, `case_id`, `target_anchor`, `expected_owner`, `accepted_runtime_owners`, `required_action_probe`, `negative_boundary`, `patch_type`, and `status`.
- Consumes: public fixture case numbers and existing owner names from `tests/judgment_benchmark_50_cases.jsonl`.

- [x] **Step 1: Write failing contract test**

Add a test that loads `docs/benchmarks/v5-target-trigger-register.json` and asserts:

```python
expected_cases = {2, 3, 4, 13, 17, 33, 34, 48, 49}
self.assertEqual({case["case_number"] for case in register["cases"]}, expected_cases)
for case in register["cases"]:
    self.assertEqual(case["patch_type"], "mechanical_runtime")
    self.assertIn("required_action_probe", case)
    self.assertIn("negative_boundary", case)
    self.assertNotIn("wording", case["status"])
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_v3_audit_optimization_contract -v`

Expected: failure because the register file does not exist.

- [x] **Step 3: Add register file**

Create `docs/benchmarks/v5-target-trigger-register.json` with nine public target cases:

- #2 root-cause evidence gate -> `using-mindthus`
- #3 target-function-before-migration -> `using-mindthus`
- #4 release-readiness gate -> `using-mindthus`
- #13 whole-object-before-copy -> `using-mindthus`
- #17 EDSP extremes-before-branch -> `edsp`
- #33 Anti-Spiral brake before third prompt rule -> `using-mindthus`, `3l5s`, or `tplan`
- #34 Anti-Spiral brake before third fallback -> `using-mindthus`, `3l5s`, or `tplan`
- #48 definition-authority first sentence -> `using-mindthus`
- #49 AQM evidence ceiling -> `using-mindthus` or `mpg`

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_v3_audit_optimization_contract -v`

Expected: OK.

### Task 2: Report Register-Based Activation Diagnostics

**Files:**
- Modify: `scripts/run-judgment-benchmark-cli.py`
- Modify: `tests/test_judgment_benchmark_cli_runner.py`

**Interfaces:**
- Consumes: `docs/benchmarks/v5-target-trigger-register.json`.
- Produces: `summary["v5_target_activation"]` with `registered_case_count`, `selected_registered_case_count`, `expected_owner_loaded_rate`, `no_load_case_numbers`, `wrong_owner_case_numbers`, and per-case probe records.

- [x] **Step 1: Write failing runner tests**

Add tests that call a new `v5_target_activation_diagnostics(scores)` helper and assert:

```python
self.assertEqual(diagnostics["registered_case_count"], 9)
self.assertEqual(diagnostics["selected_registered_case_count"], 3)
self.assertEqual(diagnostics["no_load_case_numbers"], [2])
self.assertEqual(diagnostics["wrong_owner_case_numbers"], [17])
self.assertEqual(diagnostics["expected_owner_loaded_rate"], 0.333)
```

- [x] **Step 2: Implement helper and summary hook**

Add:

```python
def load_v5_target_trigger_register(path: Path | None = None) -> dict[str, Any]:
    ...

def v5_target_activation_diagnostics(scores: list[dict[str, Any]]) -> dict[str, Any]:
    ...
```

Then assign `summary["v5_target_activation"] = v5_target_activation_diagnostics(scores)` before writing `summary.json`.

- [x] **Step 3: Run runner tests**

Run: `python3 -m unittest tests.test_judgment_benchmark_cli_runner -v`

Expected: OK.

### Task 3: Document The Mechanism Boundary

**Files:**
- Modify: `docs/benchmarks/v5-targeted-plan.md`
- Modify: `docs/benchmarks/v5-targeted-issue-drafts.md`
- Modify: `docs/benchmarks/v5-certification-protocol.md`

**Interfaces:**
- Consumes: register path and diagnostic field name from Tasks 1-2.
- Produces: documentation that says the register is diagnostic/mechanical and does not certify behavior by itself.

- [x] **Step 1: Update docs**

Add references to:

- `docs/benchmarks/v5-target-trigger-register.json`
- `summary["v5_target_activation"]`
- register diagnostics as a gate before host hook or full 50 rerun
- register diagnostics as non-certifying without `n >= 3`, negative controls, and external shadow

- [x] **Step 2: Run focused tests**

Run:

```bash
python3 -m unittest tests.test_v3_audit_optimization_contract tests.test_judgment_benchmark_cli_runner tests.test_packaging_docs -v
```

Expected: OK.

### Task 4: Add Diagnostic Host-Hint Experiment Switch

**Files:**
- Modify: `scripts/run-judgment-benchmark-cli.py`
- Modify: `tests/test_judgment_benchmark_cli_runner.py`
- Modify: `docs/benchmarks/v5-target-trigger-register.json`
- Modify: `docs/benchmarks/v5-targeted-plan.md`
- Modify: `docs/benchmarks/v5-targeted-issue-drafts.md`
- Modify: `docs/benchmarks/v5-certification-protocol.md`

**Interfaces:**
- Consumes: `preferred_runtime_owner` from the V5 target-trigger register.
- Produces: `--v5-register-hints`, response-level `activation_hint_applied`,
  `activation_hints_all_turns`, and manifest fields for hint mode and register SHA.

- [x] **Step 1: Write failing tests**

Tests cover diagnostic hint injection, strict `case_id` matching, and certification
candidate rejection.

- [x] **Step 2: Implement minimal diagnostic switch**

The runner injects a host-style route hint only for matched registered target cases and
only in diagnostic mode.

- [x] **Step 3: Update docs**

The protocol and targeted plan state that host-hint results are diagnostic and cannot
be marketed as natural activation or certification evidence.

- [x] **Step 4: Run final verification**

Run focused and full regression after all edits.

- [x] **Step 3: Run full regression**

Run:

```bash
python3 -m unittest discover -s tests
```

Expected: OK.

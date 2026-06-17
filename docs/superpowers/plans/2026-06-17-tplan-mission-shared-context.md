# TPlan Mission Shared Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add project-level Markdown Mission shared context memory and startup preflight for TPlan.

**Architecture:** Markdown under `.tplan/shared_contexts/` becomes the durable Mission memory surface. `mission.json.shared_context` remains the structured runtime index with `context_file`, `source_contexts`, and `risk_signals`. A new preflight script reports deterministic startup actions without making semantic Mission identity judgments.

**Tech Stack:** Python standard library, existing TPlan scripts, `unittest`.

---

### Task 1: Shared Context Path, Metadata, And Preflight

**Files:**
- Modify: `skills/tplan/scripts/tplan_runtime.py`
- Create: `skills/tplan/scripts/preflight_mission.py`
- Test: `tests/tplan/test_mission_shared_context.py`

- [ ] **Step 1: Write failing tests for path resolution and preflight**

Create `tests/tplan/test_mission_shared_context.py` with tests that:

```python
def test_preflight_reports_create_new_when_context_absent(self):
    ...

def test_preflight_reports_continue_existing_for_matching_context(self):
    ...

def test_preflight_reports_conflict_for_same_id_different_objective(self):
    ...

def test_preflight_lists_candidates_without_mission_id(self):
    ...
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
python3 -m unittest tests.tplan.test_mission_shared_context
```

Expected: fails because `preflight_mission.py` and shared context helpers do not exist.

- [ ] **Step 3: Implement minimal helpers**

Add helpers to `tplan_runtime.py` for:

- `shared_context_dir(project_root)`
- `shared_context_path(project_root, mission_id)`
- `render_shared_context_markdown(mission, source_contexts=None)`
- `parse_shared_context_metadata(text)`
- `build_mission_preflight(project_root, mission_id, objective, acceptance_evidence)`

Create `preflight_mission.py` as a thin argparse wrapper.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
python3 -m unittest tests.tplan.test_mission_shared_context
```

Expected: tests pass.

### Task 2: Init Scripts Create Or Load Shared Context

**Files:**
- Modify: `skills/tplan/scripts/init_mission.py`
- Modify: `skills/tplan/scripts/init_lite.py`
- Modify: `skills/tplan/scripts/tplan_runtime.py`
- Test: `tests/tplan/test_mission_shared_context.py`
- Test: `tests/tplan/test_init_lite.py`
- Test: `tests/tplan/test_init_and_check.py`

- [ ] **Step 1: Write failing init tests**

Add tests proving:

```python
def test_init_mission_creates_project_shared_context_file(self):
    ...

def test_init_mission_loads_existing_matching_context(self):
    ...

def test_init_mission_rejects_conflicting_context(self):
    ...

def test_init_lite_creates_project_shared_context_file(self):
    ...

def test_init_mission_records_source_contexts_for_new_mission(self):
    ...
```

- [ ] **Step 2: Run targeted tests to verify RED**

Run:

```bash
python3 -m unittest tests.tplan.test_mission_shared_context tests.tplan.test_init_lite tests.tplan.test_init_and_check
```

Expected: new tests fail because init scripts do not accept `--project-root` or `--source-context`.

- [ ] **Step 3: Wire init scripts**

Add args:

- `--project-root`
- `--source-context` repeatable

When `--project-root` is present, create/load the Markdown shared context and set:

```json
"shared_context": {
  "context_file": ".tplan/shared_contexts/tplan_mission_shared_context-<mission_id>.md",
  "source_contexts": [],
  "risk_signals": []
}
```

- [ ] **Step 4: Run targeted tests to verify GREEN**

Run:

```bash
python3 -m unittest tests.tplan.test_mission_shared_context tests.tplan.test_init_lite tests.tplan.test_init_and_check
```

Expected: tests pass.

### Task 3: Risk Context Refreshes Markdown Memory

**Files:**
- Modify: `skills/tplan/scripts/tplan_runtime.py`
- Modify: `skills/tplan/scripts/record_risk_context.py` if needed
- Test: `tests/tplan/test_mission_shared_context.py`
- Test: `tests/tplan/test_shared_risk_context.py`

- [ ] **Step 1: Write failing risk refresh tests**

Add tests proving recording and resolving risk refreshes the Markdown file when
`mission.json.shared_context.context_file` is present.

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
python3 -m unittest tests.tplan.test_mission_shared_context tests.tplan.test_shared_risk_context
```

Expected: new refresh tests fail.

- [ ] **Step 3: Refresh Markdown after risk writes**

Update `record_risk_signal` and `resolve_risk_signal` to refresh the indexed Markdown
context after successful `mission.json` write and evidence append.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
python3 -m unittest tests.tplan.test_mission_shared_context tests.tplan.test_shared_risk_context
```

Expected: tests pass.

### Task 4: Docs And Full Verification

**Files:**
- Modify: `skills/tplan/resources/schema.md`
- Modify: `skills/tplan/resources/hooks.md`
- Modify: `skills/tplan/SKILL.md`
- Modify: `docs/methodologies/tplan.md`
- Modify: `tests/tplan/test_skill_contract.py`

- [ ] **Step 1: Write or update contract tests**

Ensure contract tests require mention of:

- project-level `.tplan/shared_contexts/`
- `tplan_mission_shared_context-<mission_id>.md`
- startup preflight
- `source_contexts`

- [ ] **Step 2: Run contract tests to verify RED**

Run:

```bash
python3 -m unittest tests.tplan.test_skill_contract
```

Expected: fails until docs are updated.

- [ ] **Step 3: Update docs**

Update public skill and schema docs to describe Markdown primary storage, JSON runtime
index, preflight behavior, and Mission identity rules.

- [ ] **Step 4: Full verification**

Run:

```bash
python3 -m unittest discover -s tests/tplan -p 'test_*.py'
```

Expected: all TPlan tests pass.

# tplan Shared Risk Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Mission-level shared risk context so scoped local blockers and recovery signals can influence later risk-adjusted task value assessment.

**Architecture:** Store live risk signals in `mission.json` under optional `shared_context.risk_signals`, record audit events in `evidence.jsonl`, and expose active signals through survey and decision packets. Keep semantic judgment agentic: scripts validate shape, update state, and require `risk_assessment` for high-impact decisions when active shared risks exist.

**Tech Stack:** Python standard library runtime scripts, JSON/JSONL mission files, `unittest` tests under `tests/tplan`.

---

## Closeout

Status: accepted and implemented on 2026-06-10.

Implementation commits:

- `9593e87 feat: add tplan shared risk context`
- `4e28937 test: add tplan shared risk ab packet`
- `a03d37f test: refine tplan shared risk ab design`
- `e3744dc test: record tplan shared risk ab run`
- `81446f4 test: add tplan shared risk agent simulator`
- `668c8b0 test: add tplan shared risk stop latency simulation`

Acceptance judgment:

- The original runtime acceptance criteria are implemented.
- The A/B was accepted on the narrower, stronger claim that B earlier blocks the
  untrusted expensive path, not that B earlier completes the whole Mission.
- Final verification: `python3 -m unittest discover -s tests/tplan -p 'test_*.py'`
  passed with 81 tests.
- No separate open GitHub issue directly matched this local plan, so this plan and its
  paired design spec carry the issue closeout record.

### Task 1: Shared Risk Schema Validation

**Files:**
- Modify: `tests/tplan/test_shared_risk_context.py`
- Modify: `skills/tplan/scripts/tplan_runtime.py`

- [x] **Step 1: Write failing schema tests**

Create `tests/tplan/test_shared_risk_context.py` with helpers that initialize a Mission, manually add `shared_context.risk_signals`, and assert:

```python
def test_check_mission_accepts_valid_shared_risk_context(self):
    mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
    mission["shared_context"] = {
        "risk_signals": [
            {
                "id": "R1",
                "source_task_id": "T1",
                "scope": "shared_environment",
                "signal": "fsync_unreliable",
                "severity": "high",
                "confidence": "high",
                "affected_surfaces": ["generation", "sqlite"],
                "value_effect": "Expensive reruns may produce invalid evidence.",
                "recommended_gate": "environment_health_gate",
                "recovery_condition": "dd fsync and sqlite commit smoke pass",
                "status": "active",
                "created_at": "2026-06-10T00:00:00+00:00",
                "updated_at": "2026-06-10T00:00:00+00:00",
            }
        ]
    }
    (mission_dir / "mission.json").write_text(json.dumps(mission), encoding="utf-8")
    result = run_script("check_mission.py", str(mission_dir))
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
```

Add a second test that sets `"severity": "severe"` and expects `risk signal R1 severity unsupported`.

- [x] **Step 2: Run schema tests and verify RED**

Run:

```bash
python3 -m unittest tests.tplan.test_shared_risk_context -v
```

Expected: fail because current validation ignores or does not validate shared risk context.

- [x] **Step 3: Implement shared risk validation helpers**

In `skills/tplan/scripts/tplan_runtime.py`, add enum constants and validation helpers:

```python
RISK_SIGNAL_SCOPES = {...}
RISK_SIGNAL_SEVERITIES = {"low", "medium", "high", "critical"}
RISK_SIGNAL_CONFIDENCES = {"low", "medium", "high", "unclear"}
RISK_SIGNAL_STATUSES = {"active", "resolved", "superseded", "invalidated"}
```

Validate optional top-level `shared_context` when present:

- must be an object
- `risk_signals` must be a list
- required fields must exist
- string/list fields must have the right shape
- enum fields must be allowed
- `source_task_id` must reference an existing task
- duplicate risk ids are rejected

- [x] **Step 4: Run schema tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.tplan.test_shared_risk_context -v
```

Expected: schema tests pass.

### Task 2: Risk Context Recording Script

**Files:**
- Modify: `tests/tplan/test_shared_risk_context.py`
- Create: `skills/tplan/scripts/record_risk_context.py`
- Modify: `skills/tplan/scripts/tplan_runtime.py`

- [x] **Step 1: Write failing record/resolve tests**

Add tests that call:

```bash
python3 skills/tplan/scripts/record_risk_context.py <mission_dir> record \
  --task-id T1 \
  --scope shared_environment \
  --signal fsync_unreliable \
  --severity high \
  --confidence high \
  --affected-surface generation \
  --affected-surface sqlite \
  --value-effect "Expensive reruns may produce invalid evidence." \
  --recommended-gate environment_health_gate \
  --recovery-condition "dd fsync and sqlite commit smoke pass"
```

Assert that `mission.json` contains active `R1`, that `evidence.jsonl` contains a
`risk_context_update` event, and that `R1.source_evidence_id` equals that event id.

Add a resolve test that calls:

```bash
python3 skills/tplan/scripts/record_risk_context.py <mission_dir> resolve \
  --task-id T1 \
  --risk-id R1 \
  --status resolved \
  --summary "Storage smoke passed." \
  --recovery-note "dd fsync and sqlite commit passed."
```

Assert that `R1.status == "resolved"` and a `risk_context_recovery` event was appended.

- [x] **Step 2: Run record/resolve tests and verify RED**

Run:

```bash
python3 -m unittest tests.tplan.test_shared_risk_context -v
```

Expected: fail because `record_risk_context.py` does not exist.

- [x] **Step 3: Implement runtime helpers and CLI**

In `tplan_runtime.py`, add:

- `active_risk_signals(mission)`
- `recent_resolved_risk_signals(mission, limit=5)`
- `record_risk_signal(mission_dir, task_id, payload)`
- `resolve_risk_signal(mission_dir, task_id, risk_id, status, summary, recovery_note)`

Create `skills/tplan/scripts/record_risk_context.py` with `record` and `resolve` subcommands. The script should print the recorded risk id and evidence id in plain mode and JSON in `--json` mode.

- [x] **Step 4: Run record/resolve tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.tplan.test_shared_risk_context -v
```

Expected: tests pass.

### Task 3: Survey And Decision Packet Context

**Files:**
- Modify: `tests/tplan/test_shared_risk_context.py`
- Modify: `tests/tplan/test_survey_and_packet.py`
- Modify: `skills/tplan/scripts/tplan_runtime.py`
- Modify: `skills/tplan/scripts/survey.py`

- [x] **Step 1: Write failing survey/packet tests**

Add assertions that after recording `R1`:

- `survey.py --json` includes `shared_context.active_risk_signal_count == 1`
- `survey.py --json` includes `shared_context.highest_active_severity == "high"`
- decision packet includes `shared_context.active_risk_signals[0].id == "R1"`

- [x] **Step 2: Run survey/packet tests and verify RED**

Run:

```bash
python3 -m unittest tests.tplan.test_shared_risk_context tests.tplan.test_survey_and_packet -v
```

Expected: fail because survey and packet do not expose shared context.

- [x] **Step 3: Implement survey and packet exposure**

Update `build_survey()` and `build_decision_packet()` to include:

```json
{
  "shared_context": {
    "active_risk_signals": [],
    "recent_resolved_risk_signals": [],
    "active_risk_signal_count": 0,
    "highest_active_severity": null
  }
}
```

Update `survey.py` plain output with compact active risk count and highest severity.

- [x] **Step 4: Run survey/packet tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.tplan.test_shared_risk_context tests.tplan.test_survey_and_packet -v
```

Expected: tests pass.

### Task 4: Risk Assessment Hook Validation

**Files:**
- Modify: `tests/tplan/test_apply_decision.py`
- Modify: `skills/tplan/scripts/tplan_runtime.py`
- Modify: `skills/tplan/templates/hook-output.json`

- [x] **Step 1: Write failing hook validation tests**

Add tests that create an active shared risk signal and assert:

- high-impact `continue` with `mission_alignment` and `path_assessment` but no `risk_assessment` fails with `decision missing field: risk_assessment`
- malformed enum such as `"next_gate": "rerun_anyway"` fails
- valid `risk_assessment` passes
- low-impact parent-aligned child decision still passes without `risk_assessment`

- [x] **Step 2: Run hook tests and verify RED**

Run:

```bash
python3 -m unittest tests.tplan.test_apply_decision -v
```

Expected: fail because hook validation does not know active shared risks.

- [x] **Step 3: Implement risk assessment validation**

Add `RISK_ASSESSMENT_FIELDS` enums and update `validate_hook_output(decision, active_risk_signals=None)`.

In `apply_decision()`, read active risk signals from the Mission and pass them to validation.

Require `risk_assessment` only when active shared risks exist and the decision is high-impact or otherwise requires `path_assessment`.

- [x] **Step 4: Update hook output template**

Add a valid `risk_assessment` object to `skills/tplan/templates/hook-output.json`.

- [x] **Step 5: Run hook tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.tplan.test_apply_decision -v
```

Expected: hook tests pass.

### Task 5: Documentation And Contract Tests

**Files:**
- Modify: `tests/tplan/test_skill_contract.py`
- Modify: `skills/tplan/SKILL.md`
- Modify: `skills/tplan/resources/schema.md`
- Modify: `skills/tplan/resources/hooks.md`
- Modify: `docs/methodologies/tplan.md`

- [x] **Step 1: Write failing contract assertions**

Extend `test_skill_contract.py` to require phrases:

- `Shared Risk Context`
- `risk-adjusted value`
- `risk_context_update`
- `risk_assessment`
- `execution units do not read each other's task logs`

- [x] **Step 2: Run contract tests and verify RED**

Run:

```bash
python3 -m unittest tests.tplan.test_skill_contract -v
```

Expected: fail because docs do not yet describe shared risk context.

- [x] **Step 3: Update docs**

Document:

- shared risk context as Mission-level context, not cross-task log inspection
- when to publish risk signals
- evidence event types
- decision packet fields
- `risk_assessment` hook output
- scripts validate shape only

- [x] **Step 4: Run contract tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.tplan.test_skill_contract -v
```

Expected: contract tests pass.

### Task 6: Full Verification

**Files:**
- No code changes unless verification reveals a defect.

- [x] **Step 1: Run tplan test suite**

Run:

```bash
python3 -m unittest discover -s tests/tplan -p 'test_*.py'
```

Expected: all tests pass.

- [x] **Step 2: Check working tree**

Run:

```bash
git status --short
```

Expected: only intended files modified or created.

- [x] **Step 3: Commit implementation**

Run:

```bash
git add docs/superpowers/plans/2026-06-10-tplan-shared-risk-context.md \
  tests/tplan/test_shared_risk_context.py \
  tests/tplan/test_apply_decision.py \
  tests/tplan/test_survey_and_packet.py \
  tests/tplan/test_skill_contract.py \
  skills/tplan/scripts/tplan_runtime.py \
  skills/tplan/scripts/record_risk_context.py \
  skills/tplan/scripts/survey.py \
  skills/tplan/templates/hook-output.json \
  skills/tplan/SKILL.md \
  skills/tplan/resources/schema.md \
  skills/tplan/resources/hooks.md \
  docs/methodologies/tplan.md
git commit -m "feat: add tplan shared risk context"
```

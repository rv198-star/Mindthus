import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(REPO / "skills" / "tplan" / "scripts" / script_name), *args],
        text=True,
        capture_output=True,
    )


def context_path(project_root, mission_id):
    return (
        Path(project_root)
        / ".tplan"
        / "shared_contexts"
        / f"tplan_mission_shared_context-{mission_id}.md"
    )


def write_context(
    project_root,
    mission_id,
    objective="Keep the original mission.",
    acceptance=None,
    *,
    runtime_dir_name=None,
    risk_signals=None,
):
    acceptance = acceptance or [{"id": "A1", "description": "Original acceptance."}]
    path = context_path(project_root, mission_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": "tplan.shared_context.v0.1",
        "mission_id": mission_id,
        "title": "Original Mission",
        "objective": objective,
        "status": "active",
        "active_task_id": "T1",
        "acceptance_evidence": acceptance,
        "source_contexts": [],
        "runtime_dir_name": runtime_dir_name,
        "risk_signals": risk_signals or [],
    }
    path.write_text(
        "<!-- tplan-shared-context\n"
        + json.dumps(metadata, ensure_ascii=False, indent=2)
        + "\n-->\n"
        + f"# TPlan Mission Shared Context: {mission_id}\n\n"
        + "## Mission Snapshot\n\n"
        + f"- objective: {objective}\n",
        encoding="utf-8",
    )
    return path


def write_tasks(tmp):
    task_path = Path(tmp) / "tasks.json"
    task_path.write_text(
        json.dumps(
            [
                {
                    "id": "T1",
                    "title": "Keep context current",
                    "role": "success-critical",
                    "mission_contribution": "Keeps Mission memory available for resume.",
                    "acceptance_evidence": ["A1"],
                }
            ]
        ),
        encoding="utf-8",
    )
    return task_path


def read_mission(mission_dir):
    return json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))


class MissionSharedContextPreflightTests(unittest.TestCase):
    def test_preflight_reports_create_new_when_context_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-new",
                "--objective",
                "Create a new Mission.",
                "--acceptance-evidence",
                "A1:New acceptance.",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["action"], "create_new")
            self.assertEqual(payload["mission_id"], "m-new")
            self.assertEqual(payload["conflicts"], [])
            self.assertTrue(payload["context_file"].endswith("tplan_mission_shared_context-m-new.md"))

    def test_preflight_reports_continue_existing_for_matching_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_context(tmp, "m-existing")

            result = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-existing",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["action"], "continue_existing")
            self.assertEqual(payload["mission_id"], "m-existing")
            self.assertEqual(payload["conflicts"], [])
            self.assertEqual(payload["loaded_context"]["mission_id"], "m-existing")

    def test_preflight_reports_conflict_for_same_id_different_objective(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_context(tmp, "m-conflict", objective="Keep the original mission.")

            result = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-conflict",
                "--objective",
                "Do a different Mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["action"], "needs_agentic_selection")
            self.assertIn("objective", payload["conflicts"])

    def test_preflight_lists_candidates_without_mission_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_context(tmp, "m-one")
            write_context(tmp, "m-two")

            result = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["action"], "needs_agentic_selection")
            self.assertEqual([item["mission_id"] for item in payload["candidates"]], ["m-one", "m-two"])


class MissionSharedContextInitTests(unittest.TestCase):
    def test_init_mission_creates_project_shared_context_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = Path(tmp) / "mission"
            tasks = write_tasks(tmp)

            result = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-shared",
                "--title",
                "Shared Context Mission",
                "--objective",
                "Create project shared context memory.",
                "--acceptance-evidence",
                "A1:Shared context file exists.",
                "--task-json",
                str(tasks),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            path = context_path(project_root, "m-shared")
            self.assertTrue(path.exists())
            text = path.read_text(encoding="utf-8")
            self.assertIn("TPlan Mission Shared Context: m-shared", text)
            self.assertIn("Create project shared context memory.", text)
            mission = read_mission(mission_dir)
            self.assertEqual(
                mission["shared_context"]["context_file"],
                ".tplan/shared_contexts/tplan_mission_shared_context-m-shared.md",
            )
            self.assertEqual(mission["shared_context"]["risk_signals"], [])

    def test_init_mission_loads_existing_matching_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = Path(tmp) / "mission"
            tasks = write_tasks(tmp)
            write_context(
                project_root,
                "m-existing",
                objective="Keep the original mission.",
                acceptance=[{"id": "A1", "description": "Original acceptance."}],
            )

            result = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-existing",
                "--title",
                "Existing Mission",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--task-json",
                str(tasks),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            mission = read_mission(mission_dir)
            self.assertEqual(mission["mission"]["id"], "m-existing")
            self.assertEqual(mission["shared_context"]["context_file"], ".tplan/shared_contexts/tplan_mission_shared_context-m-existing.md")

    def test_init_mission_restores_risk_signals_from_existing_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = Path(tmp) / "m-existing-run"
            tasks = write_tasks(tmp)
            write_context(
                project_root,
                "m-existing",
                objective="Keep the original mission.",
                acceptance=[{"id": "A1", "description": "Original acceptance."}],
                runtime_dir_name="m-existing-run",
                risk_signals=[
                    {
                        "id": "R1",
                        "source_task_id": "T1",
                        "source_evidence_id": "Edeadbeef",
                        "scope": "shared_environment",
                        "signal": "fsync_unreliable",
                        "severity": "high",
                        "confidence": "high",
                        "affected_surfaces": ["generation"],
                        "value_effect": "Expensive reruns may produce invalid evidence.",
                        "recommended_gate": "environment_health_gate",
                        "recovery_condition": "dd fsync and sqlite commit smoke pass",
                        "status": "active",
                        "created_at": "2026-06-10T00:00:00+00:00",
                        "updated_at": "2026-06-10T00:00:00+00:00",
                    }
                ],
            )

            result = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-existing",
                "--title",
                "Existing Mission",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--task-json",
                str(tasks),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            mission = read_mission(mission_dir)
            self.assertEqual(mission["shared_context"]["risk_signals"][0]["id"], "R1")
            self.assertEqual(mission["shared_context"]["risk_signals"][0]["status"], "active")

    def test_init_mission_rejects_conflicting_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = Path(tmp) / "mission"
            tasks = write_tasks(tmp)
            write_context(project_root, "m-conflict", objective="Original objective.")

            result = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-conflict",
                "--title",
                "Conflict Mission",
                "--objective",
                "Different objective.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--task-json",
                str(tasks),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("shared context preflight conflict", result.stderr)
            self.assertFalse(mission_dir.exists())

    def test_init_mission_rejects_duplicate_mission_id_in_second_runtime_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            first_mission_dir = Path(tmp) / "m-dup-run-a"
            second_mission_dir = Path(tmp) / "m-dup-run-b"
            tasks = write_tasks(tmp)

            first = run_script(
                "init_mission.py",
                "--dir",
                str(first_mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-dup",
                "--title",
                "Duplicate Guard Mission",
                "--objective",
                "Keep one runtime per mission id.",
                "--acceptance-evidence",
                "A1:Only one runtime owns this mission id.",
                "--task-json",
                str(tasks),
            )
            self.assertEqual(first.returncode, 0, first.stderr)

            second = run_script(
                "init_mission.py",
                "--dir",
                str(second_mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-dup",
                "--title",
                "Duplicate Guard Mission",
                "--objective",
                "Keep one runtime per mission id.",
                "--acceptance-evidence",
                "A1:Only one runtime owns this mission id.",
                "--task-json",
                str(tasks),
            )

            self.assertNotEqual(second.returncode, 0)
            self.assertIn("shared context preflight conflict", second.stderr)
            self.assertFalse(second_mission_dir.exists())

    def test_init_mission_ignores_non_runtime_mission_json_when_checking_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            project_root.mkdir(parents=True, exist_ok=True)
            note_dir = project_root / "notes"
            note_dir.mkdir(parents=True, exist_ok=True)
            (note_dir / "mission.json").write_text(
                json.dumps(
                    {
                        "schema_version": "tplan.v0.1",
                        "mission": {"id": "m-dup"},
                    }
                ),
                encoding="utf-8",
            )
            mission_dir = Path(tmp) / "m-dup-run-a"
            tasks = write_tasks(tmp)

            result = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-dup",
                "--title",
                "Duplicate Guard Mission",
                "--objective",
                "Keep one runtime per mission id.",
                "--acceptance-evidence",
                "A1:Only one runtime owns this mission id.",
                "--task-json",
                str(tasks),
            )

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_init_lite_creates_project_shared_context_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = Path(tmp) / "mission"

            result = run_script(
                "init_lite.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-lite",
                "--title",
                "Lite Shared Context",
                "--objective",
                "Create lite shared context memory.",
                "--acceptance-evidence",
                "A1:Lite shared context exists.",
                "--active-task-id",
                "T1",
                "--active-task-title",
                "Create memory",
                "--active-task-contribution",
                "Keeps recovery memory available.",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            path = context_path(project_root, "m-lite")
            self.assertTrue(path.exists())
            mission = read_mission(mission_dir)
            self.assertEqual(mission["shared_context"]["context_file"], ".tplan/shared_contexts/tplan_mission_shared_context-m-lite.md")

    def test_init_mission_records_source_contexts_for_new_mission(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = Path(tmp) / "mission"
            tasks = write_tasks(tmp)

            result = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--source-context",
                "m-old",
                "--mission-id",
                "m-new",
                "--title",
                "New Mission",
                "--objective",
                "Use old memory as background only.",
                "--acceptance-evidence",
                "A1:New mission owns new acceptance.",
                "--task-json",
                str(tasks),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            mission = read_mission(mission_dir)
            self.assertEqual(mission["shared_context"]["source_contexts"], ["m-old"])
            text = context_path(project_root, "m-new").read_text(encoding="utf-8")
            self.assertIn("- m-old", text)


class MissionSharedContextRiskRefreshTests(unittest.TestCase):
    def init_project_mission(self, tmp, mission_id="m-risk-md"):
        project_root = Path(tmp) / "project"
        mission_dir = Path(tmp) / "mission"
        tasks = write_tasks(tmp)
        result = run_script(
            "init_mission.py",
            "--dir",
            str(mission_dir),
            "--project-root",
            str(project_root),
            "--mission-id",
            mission_id,
            "--title",
            "Risk Markdown Mission",
            "--objective",
            "Keep risk memory in Markdown.",
            "--acceptance-evidence",
            "A1:Risk memory is visible.",
            "--task-json",
            str(tasks),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return project_root, mission_dir

    def test_record_risk_context_refreshes_markdown_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root, mission_dir = self.init_project_mission(tmp)

            result = run_script(
                "record_risk_context.py",
                str(mission_dir),
                "record",
                "--task-id",
                "T1",
                "--scope",
                "shared_environment",
                "--signal",
                "fsync_unreliable",
                "--severity",
                "high",
                "--confidence",
                "high",
                "--affected-surface",
                "generation",
                "--value-effect",
                "Expensive reruns may produce invalid evidence.",
                "--recommended-gate",
                "environment_health_gate",
                "--recovery-condition",
                "dd fsync and sqlite commit smoke pass",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            text = context_path(project_root, "m-risk-md").read_text(encoding="utf-8")
            self.assertIn("R1: fsync_unreliable (high, active)", text)

    def test_resolve_risk_context_refreshes_markdown_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root, mission_dir = self.init_project_mission(tmp)
            record = run_script(
                "record_risk_context.py",
                str(mission_dir),
                "record",
                "--task-id",
                "T1",
                "--scope",
                "shared_environment",
                "--signal",
                "fsync_unreliable",
                "--severity",
                "high",
                "--confidence",
                "high",
                "--affected-surface",
                "generation",
                "--value-effect",
                "Expensive reruns may produce invalid evidence.",
                "--recommended-gate",
                "environment_health_gate",
                "--recovery-condition",
                "dd fsync and sqlite commit smoke pass",
            )
            self.assertEqual(record.returncode, 0, record.stderr)

            result = run_script(
                "record_risk_context.py",
                str(mission_dir),
                "resolve",
                "--task-id",
                "T1",
                "--risk-id",
                "R1",
                "--status",
                "resolved",
                "--summary",
                "Storage smoke passed.",
                "--recovery-note",
                "dd fsync and sqlite commit passed.",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            text = context_path(project_root, "m-risk-md").read_text(encoding="utf-8")
            self.assertIn("### Active\n\n- none", text)
            self.assertIn("R1: fsync_unreliable (resolved)", text)

    def test_record_risk_context_fails_loudly_when_indexed_shared_context_is_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root, mission_dir = self.init_project_mission(tmp)
            mission_path = mission_dir / "mission.json"
            mission = read_mission(mission_dir)
            del mission["shared_context"]["project_root"]
            mission_path.write_text(json.dumps(mission), encoding="utf-8")
            before_context = context_path(project_root, "m-risk-md").read_text(encoding="utf-8")

            result = run_script(
                "record_risk_context.py",
                str(mission_dir),
                "record",
                "--task-id",
                "T1",
                "--scope",
                "shared_environment",
                "--signal",
                "fsync_unreliable",
                "--severity",
                "high",
                "--confidence",
                "high",
                "--affected-surface",
                "generation",
                "--value-effect",
                "Expensive reruns may produce invalid evidence.",
                "--recommended-gate",
                "environment_health_gate",
                "--recovery-condition",
                "dd fsync and sqlite commit smoke pass",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("shared_context propagation configured without project_root", result.stderr)
            self.assertEqual((mission_dir / "evidence.jsonl").read_text(encoding="utf-8"), "")
            self.assertEqual(context_path(project_root, "m-risk-md").read_text(encoding="utf-8"), before_context)


if __name__ == "__main__":
    unittest.main()

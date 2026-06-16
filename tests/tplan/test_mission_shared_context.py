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


def write_context(project_root, mission_id, objective="Keep the original mission.", acceptance=None):
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


if __name__ == "__main__":
    unittest.main()

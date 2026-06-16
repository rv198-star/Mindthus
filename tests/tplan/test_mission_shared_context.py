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


if __name__ == "__main__":
    unittest.main()

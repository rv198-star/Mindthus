import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from tplan_runtime import acceptance_ids, task_map


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(REPO / "skills" / "tplan" / "scripts" / script_name), *args],
        text=True,
        capture_output=True,
    )


class InitMissionTests(unittest.TestCase):
    def write_tasks(self, tmp, tasks):
        task_path = Path(tmp) / "tasks.json"
        task_path.write_text(json.dumps(tasks), encoding="utf-8")
        return task_path

    def init_args(self, mission_dir, *extra):
        return (
            "init_mission.py",
            "--dir",
            str(mission_dir),
            "--mission-id",
            "mission-tplan-l0",
            "--title",
            "Build tplan L0",
            "--objective",
            "Build a usable L0 tplan skill for Mindthus.",
            "--acceptance-evidence",
            "A1:Runtime files exist and validate.",
            *extra,
        )

    def test_init_mission_creates_runtime_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            tasks = self.write_tasks(
                tmp,
                [
                    {
                        "id": "T1",
                        "title": "Define runtime schema",
                        "role": "success-critical",
                        "mission_contribution": "Defines the contract scripts enforce.",
                        "acceptance_evidence": ["A1"],
                    }
                ],
            )

            result = run_script(
                *self.init_args(
                    mission_dir,
                    "--task-json",
                    str(tasks),
                    "--human-in-loop",
                    "0",
                    "--risk-tolerance",
                    "50",
                    "--resource-sufficiency",
                    "60",
                ),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("initialized_mission:", result.stdout)
            self.assertTrue((mission_dir / "mission.json").exists())
            self.assertTrue((mission_dir / "mission.md").exists())
            self.assertTrue((mission_dir / "evidence.jsonl").exists())
            self.assertTrue((mission_dir / "archive").is_dir())

            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertEqual(mission["schema_version"], "tplan.v0.1")
            self.assertEqual(mission["mission"]["human_in_loop"], 0)
            self.assertEqual(mission["mission"]["resource_sufficiency"], 60)
            self.assertEqual(mission["tasks"][0]["parent_id"], None)
            self.assertEqual(mission["tasks"][0]["level"], 2)

    def test_init_mission_rejects_existing_runtime_files_without_truncating_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            first = run_script(*self.init_args(mission_dir))
            self.assertEqual(first.returncode, 0, first.stderr)
            evidence = mission_dir / "evidence.jsonl"
            evidence.write_text('{"event":"keep"}\n', encoding="utf-8")

            result = run_script(*self.init_args(mission_dir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mission runtime already exists", result.stderr)
            self.assertEqual(evidence.read_text(encoding="utf-8"), '{"event":"keep"}\n')

    def test_init_mission_rejects_out_of_range_policy_without_creating_mission_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            result = run_script(
                *self.init_args(
                    mission_dir,
                    "--human-in-loop",
                    "101",
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("human_in_loop must be between 0 and 100", result.stderr)
            self.assertFalse(mission_dir.exists())

    def test_init_mission_rejects_reserved_human_in_loop_without_creating_mission_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            result = run_script(
                *self.init_args(
                    mission_dir,
                    "--human-in-loop",
                    "50",
                ),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("human_in_loop must be 0 or 100 in tplan.v0.1", result.stderr)
            self.assertFalse(mission_dir.exists())

    def test_init_mission_rejects_bad_task_json_without_creating_mission_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            tasks = Path(tmp) / "tasks.json"
            tasks.write_text('{"id": "T1"}', encoding="utf-8")

            result = run_script(
                *self.init_args(
                    mission_dir,
                    "--task-json",
                    str(tasks),
                ),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task JSON must be a list", result.stderr)
            self.assertFalse(mission_dir.exists())

    def test_init_mission_rejects_non_object_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            tasks = self.write_tasks(tmp, ["not a task"])

            result = run_script(
                *self.init_args(
                    mission_dir,
                    "--task-json",
                    str(tasks),
                ),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task 1 must be an object", result.stderr)
            self.assertFalse(mission_dir.exists())

    def test_init_mission_rejects_string_acceptance_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            tasks = self.write_tasks(
                tmp,
                [
                    {
                        "id": "T1",
                        "title": "Define runtime schema",
                        "acceptance_evidence": "A1",
                    }
                ],
            )

            result = run_script(
                *self.init_args(
                    mission_dir,
                    "--task-json",
                    str(tasks),
                ),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task T1 acceptance_evidence must be a list", result.stderr)
            self.assertFalse(mission_dir.exists())

    def test_init_mission_rejects_invalid_task_status_and_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            bad_status = self.write_tasks(
                tmp,
                [
                    {
                        "id": "T1",
                        "title": "Define runtime schema",
                        "status": "done",
                    }
                ],
            )

            result = run_script(
                *self.init_args(
                    mission_dir,
                    "--task-json",
                    str(bad_status),
                ),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task T1 status must be one of", result.stderr)
            self.assertFalse(mission_dir.exists())

            bad_role = self.write_tasks(
                tmp,
                [
                    {
                        "id": "T1",
                        "title": "Define runtime schema",
                        "role": "critical",
                    }
                ],
            )

            result = run_script(
                *self.init_args(
                    mission_dir,
                    "--task-json",
                    str(bad_role),
                ),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task T1 role must be one of", result.stderr)
            self.assertFalse(mission_dir.exists())

    def test_init_mission_rejects_non_scalar_task_status_and_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            bad_status = self.write_tasks(
                tmp,
                [
                    {
                        "id": "T1",
                        "title": "Define runtime schema",
                        "status": [],
                    }
                ],
            )

            result = run_script(
                *self.init_args(
                    mission_dir,
                    "--task-json",
                    str(bad_status),
                ),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task T1 status must be a string", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(mission_dir.exists())

            bad_role = self.write_tasks(
                tmp,
                [
                    {
                        "id": "T1",
                        "title": "Define runtime schema",
                        "role": [],
                    }
                ],
            )

            result = run_script(
                *self.init_args(
                    mission_dir,
                    "--task-json",
                    str(bad_role),
                ),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task T1 role must be a string", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(mission_dir.exists())

    def test_init_mission_rejects_invalid_task_level_without_traceback(self):
        invalid_levels = [
            (None, "task T1 level must be an integer"),
            ([], "task T1 level must be an integer"),
        ]
        for value, message in invalid_levels:
            with self.subTest(level=value):
                with tempfile.TemporaryDirectory() as tmp:
                    mission_dir = Path(tmp) / "mission"
                    tasks = self.write_tasks(
                        tmp,
                        [
                            {
                                "id": "T1",
                                "title": "Define runtime schema",
                                "level": value,
                            }
                        ],
                    )

                    result = run_script(
                        *self.init_args(
                            mission_dir,
                            "--task-json",
                            str(tasks),
                        ),
                    )

                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(message, result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertFalse(mission_dir.exists())

    def test_init_mission_rejects_out_of_range_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            result = run_script(
                *self.init_args(
                    mission_dir,
                    "--human-in-loop",
                    "101",
                ),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("human_in_loop must be between 0 and 100", result.stderr)


class CheckMissionTests(unittest.TestCase):
    def write_tasks(self, tmp, tasks):
        task_path = Path(tmp) / "tasks.json"
        task_path.write_text(json.dumps(tasks), encoding="utf-8")
        return task_path

    def write_mission(self, mission_dir, mission):
        mission_dir.mkdir(parents=True, exist_ok=True)
        (mission_dir / "mission.json").write_text(
            json.dumps(mission, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def valid_mission(self, tasks):
        return {
            "schema_version": "tplan.v0.1",
            "mission": {
                "id": "mission-tplan-l0",
                "title": "Build tplan L0",
                "objective": "Build a usable L0 tplan skill for Mindthus.",
                "status": "active",
                "human_in_loop": 0,
                "risk_tolerance": 50,
                "resource_sufficiency": 60,
                "acceptance_evidence": [
                    {
                        "id": "A1",
                        "description": "Runtime files exist and validate.",
                    }
                ],
            },
            "tasks": tasks,
            "active_task_id": None,
        }

    def valid_task(self, task_id="T1", **overrides):
        task = {
            "id": task_id,
            "parent_id": None,
            "level": 2,
            "title": "Define runtime schema",
            "status": "pending",
            "role": "success-critical",
            "mission_contribution": "Defines the contract scripts enforce.",
            "acceptance_evidence": ["A1"],
            "evidence_links": [],
        }
        task.update(overrides)
        return task

    def test_check_mission_accepts_valid_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            tasks = self.write_tasks(
                tmp,
                [
                    {
                        "id": "T1",
                        "title": "Define runtime schema",
                        "role": "success-critical",
                        "mission_contribution": "Defines the contract scripts enforce.",
                        "acceptance_evidence": ["A1"],
                    }
                ],
            )
            init = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--mission-id",
                "mission-tplan-l0",
                "--title",
                "Build tplan L0",
                "--objective",
                "Build a usable L0 tplan skill for Mindthus.",
                "--acceptance-evidence",
                "A1:Runtime files exist and validate.",
                "--task-json",
                str(tasks),
            )
            self.assertEqual(init.returncode, 0, init.stderr)

            result = run_script("check_mission.py", str(mission_dir))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("mission_check: ok", result.stdout)

    def test_check_mission_accepts_child_task_with_parent_alignment_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            self.write_mission(
                mission_dir,
                self.valid_mission(
                    [
                        self.valid_task("T1"),
                        {
                            "id": "T1.1",
                            "parent_id": "T1",
                            "level": 3,
                            "title": "Draft schema fields",
                            "status": "pending",
                            "role": "supporting",
                            "parent_contribution": "Drafts the fields required by T1.",
                            "parent_acceptance": "T1 can review concrete field names and required types.",
                            "mission_trace": "via T1 -> A1",
                            "evidence_links": [],
                        },
                    ]
                ),
            )

            result = run_script("check_mission.py", str(mission_dir))

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("mission_check: ok", result.stdout)

    def test_check_mission_rejects_child_task_missing_parent_alignment(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            self.write_mission(
                mission_dir,
                self.valid_mission(
                    [
                        self.valid_task("T1"),
                        {
                            "id": "T1.1",
                            "parent_id": "T1",
                            "level": 3,
                            "title": "Draft schema fields",
                            "status": "pending",
                            "role": "supporting",
                            "mission_trace": "via T1 -> A1",
                            "evidence_links": [],
                        },
                    ]
                ),
            )

            result = run_script("check_mission.py", str(mission_dir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task T1.1 is missing parent_contribution", result.stdout)
            self.assertIn("task T1.1 is missing parent_acceptance", result.stdout)

    def test_runtime_helpers_accept_full_mission_state(self):
        mission = self.valid_mission(
            [
                self.valid_task("T1"),
                self.valid_task("T2", role="supporting", acceptance_evidence=[]),
            ]
        )

        try:
            tasks_by_id = task_map(mission)
        except Exception as exc:
            self.fail(f"task_map should accept full mission state: {exc}")

        self.assertEqual(set(tasks_by_id), {"T1", "T2"})
        self.assertEqual(acceptance_ids(mission), {"A1"})

    def test_check_mission_rejects_orphan_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            self.write_mission(
                mission_dir,
                self.valid_mission(
                    [
                        {
                            "id": "T1",
                            "parent_id": None,
                            "level": 2,
                            "title": "Define runtime schema",
                            "status": "pending",
                            "role": "success-critical",
                            "mission_contribution": "Defines the contract scripts enforce.",
                            "acceptance_evidence": ["A1"],
                            "evidence_links": [],
                        },
                        {
                            "id": "T2",
                            "parent_id": "missing",
                            "level": 3,
                            "title": "Write child task",
                            "status": "pending",
                            "role": "supporting",
                            "parent_contribution": "Adds supporting detail for parent task.",
                            "parent_acceptance": "Parent has a concrete supporting detail.",
                            "mission_trace": "via missing -> A1",
                            "evidence_links": [],
                        },
                    ]
                ),
            )

            result = run_script("check_mission.py", str(mission_dir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task T2 parent_id missing does not exist", result.stdout)

    def test_check_mission_rejects_missing_acceptance_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            self.write_mission(
                mission_dir,
                self.valid_mission(
                    [
                        {
                            "id": "T1",
                            "parent_id": None,
                            "level": 2,
                            "title": "Define runtime schema",
                            "status": "pending",
                            "role": "success-critical",
                            "mission_contribution": "Defines the contract scripts enforce.",
                            "acceptance_evidence": [],
                            "evidence_links": [],
                        }
                    ]
                ),
            )

            result = run_script("check_mission.py", str(mission_dir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "acceptance evidence A1 is not covered by a success-critical task",
                result.stdout,
            )

    def test_check_mission_rejects_missing_active_task_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            mission = self.valid_mission(
                [
                    {
                        "id": "T1",
                        "parent_id": None,
                        "level": 2,
                        "title": "Define runtime schema",
                        "status": "pending",
                        "role": "success-critical",
                        "mission_contribution": "Defines the contract scripts enforce.",
                        "acceptance_evidence": ["A1"],
                        "evidence_links": [],
                    }
                ]
            )
            del mission["active_task_id"]
            self.write_mission(mission_dir, mission)

            result = run_script("check_mission.py", str(mission_dir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing field: active_task_id", result.stdout)

    def test_check_mission_rejects_reserved_human_in_loop(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            mission = self.valid_mission([self.valid_task()])
            mission["mission"]["human_in_loop"] = 50
            self.write_mission(mission_dir, mission)

            result = run_script("check_mission.py", str(mission_dir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mission human_in_loop must be 0 or 100 in tplan.v0.1", result.stdout)

    def test_check_mission_rejects_self_parent_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            self.write_mission(
                mission_dir,
                self.valid_mission([self.valid_task(parent_id="T1")]),
            )

            result = run_script("check_mission.py", str(mission_dir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task T1 parent_id cannot reference itself", result.stdout)

    def test_check_mission_rejects_parent_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            self.write_mission(
                mission_dir,
                self.valid_mission(
                    [
                        self.valid_task("T1", parent_id="T2"),
                        self.valid_task(
                            "T2",
                            parent_id="T1",
                            role="supporting",
                            acceptance_evidence=[],
                            parent_contribution="Supports T1.",
                            parent_acceptance="T1 has a concrete supporting output.",
                            mission_trace="via T1 -> A1",
                        ),
                    ]
                ),
            )

            result = run_script("check_mission.py", str(mission_dir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task tree contains a cycle involving T1", result.stdout)

    def test_check_mission_rejects_duplicate_mission_evidence_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            mission = self.valid_mission([self.valid_task()])
            mission["mission"]["acceptance_evidence"].append(
                {
                    "id": "A1",
                    "description": "Duplicate acceptance evidence.",
                }
            )
            self.write_mission(mission_dir, mission)

            result = run_script("check_mission.py", str(mission_dir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate mission acceptance evidence id A1", result.stdout)

    def test_check_mission_rejects_unknown_task_evidence_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            self.write_mission(
                mission_dir,
                self.valid_mission([self.valid_task(acceptance_evidence=["A1", "A2"])]),
            )

            result = run_script("check_mission.py", str(mission_dir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task T1 acceptance_evidence A2 does not exist", result.stdout)

    def test_check_mission_rejects_non_string_text_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            mission = self.valid_mission(
                [
                    self.valid_task(
                        title=["not scalar"],
                        mission_contribution=None,
                    )
                ]
            )
            mission["mission"]["id"] = ["mission-tplan-l0"]
            mission["mission"]["title"] = None
            mission["mission"]["objective"] = {"text": "Build a usable L0 tplan skill."}
            self.write_mission(mission_dir, mission)

            result = run_script("check_mission.py", str(mission_dir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mission id must be a string", result.stdout)
            self.assertIn("mission title must be a string", result.stdout)
            self.assertIn("mission objective must be a string", result.stdout)
            self.assertIn("task T1 title must be a string", result.stdout)
            self.assertIn("task T1 mission_contribution must be a string", result.stdout)


if __name__ == "__main__":
    unittest.main()

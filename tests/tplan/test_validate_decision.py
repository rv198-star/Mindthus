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


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class ValidateDecisionTests(unittest.TestCase):
    def test_validate_decision_accepts_valid_child_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            decision = Path(tmp) / "decision.json"
            write_json(
                decision,
                {
                    "recommendation": "continue",
                    "rationale": "The child node can complete its parent-facing draft.",
                    "confidence": 75,
                    "evidence_links": [],
                    "proposed_mutations": [
                        {"type": "transition_task", "task_id": "T1.1", "status": "completed"}
                    ],
                    "requires_human": False,
                    "parent_alignment": "Completing T1.1 gives T1 the needed draft.",
                    "mission_trace": "via T1 -> A1",
                },
            )

            result = run_script("validate_decision.py", "--decision", str(decision), "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["valid"])
            self.assertEqual(report["errors"], [])
            self.assertIsNone(report["repair_template"])
            self.assertEqual(report["next_action"], "apply_decision")

    def test_validate_decision_reports_invalid_json_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            decision = Path(tmp) / "decision.json"
            decision.write_text("{not-json", encoding="utf-8")

            result = run_script("validate_decision.py", "--decision", str(decision), "--json")

            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stderr)
            report = json.loads(result.stdout)
            self.assertFalse(report["valid"])
            self.assertIn("invalid JSON", report["errors"][0])
            self.assertEqual(report["next_action"], "repair_decision")
            self.assertEqual(report["repair_template"]["recommendation"], "continue")

    def test_validate_decision_reports_missing_fields_with_repair_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            decision = Path(tmp) / "decision.json"
            write_json(decision, {"recommendation": "switch"})

            result = run_script("validate_decision.py", "--decision", str(decision), "--json")

            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertFalse(report["valid"])
            self.assertIn("decision missing field: rationale", report["errors"])
            self.assertIn("proposed_mutations", report["repair_template"])
            self.assertEqual(report["next_action"], "repair_decision")

    def test_validate_decision_reports_bad_mutation_shape_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            decision = Path(tmp) / "decision.json"
            write_json(
                decision,
                {
                    "recommendation": "switch",
                    "rationale": "Switch to the task that unblocks runtime usage.",
                    "confidence": 80,
                    "evidence_links": [],
                    "proposed_mutations": [{"type": "set_active_task"}],
                    "requires_human": False,
                    "mission_alignment": "The switch advances Mission runtime usability.",
                },
            )

            result = run_script("validate_decision.py", "--decision", str(decision), "--json")

            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertFalse(report["valid"])
            self.assertIn("mutation set_active_task missing field: task_id", report["errors"])
            self.assertEqual(report["next_action"], "repair_decision")

    def test_repair_success_path_validates_second_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "broken.json"
            repaired = Path(tmp) / "repaired.json"
            write_json(broken, {"recommendation": "continue"})

            first = run_script("validate_decision.py", "--decision", str(broken), "--json")
            self.assertNotEqual(first.returncode, 0)
            first_report = json.loads(first.stdout)
            self.assertEqual(first_report["next_action"], "repair_decision")

            write_json(
                repaired,
                {
                    "recommendation": "continue",
                    "rationale": "The child node can continue after repairing the contract shape.",
                    "confidence": 70,
                    "evidence_links": [],
                    "proposed_mutations": [],
                    "requires_human": False,
                    "parent_alignment": "Continuing keeps the child aligned to the parent output.",
                    "mission_trace": "via T1 -> A1",
                },
            )

            second = run_script("validate_decision.py", "--decision", str(repaired), "--json")
            self.assertEqual(second.returncode, 0, second.stderr)
            second_report = json.loads(second.stdout)
            self.assertTrue(second_report["valid"])
            self.assertEqual(second_report["next_action"], "apply_decision")

    def test_repeated_contract_failure_can_stop_with_chinese_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad_one = Path(tmp) / "bad-one.json"
            bad_two = Path(tmp) / "bad-two.json"
            write_json(bad_one, {"recommendation": "continue"})
            bad_two.write_text("{not-json", encoding="utf-8")

            first = run_script("validate_decision.py", "--decision", str(bad_one), "--json")
            second = run_script("validate_decision.py", "--decision", str(bad_two), "--json")
            self.assertNotEqual(first.returncode, 0)
            self.assertNotEqual(second.returncode, 0)

            mission_dir = Path(tmp) / "mission"
            tasks = Path(tmp) / "tasks.json"
            write_json(
                tasks,
                [
                    {
                        "id": "T1",
                        "title": "Apply runtime decision",
                        "role": "success-critical",
                        "mission_contribution": "Applies runtime decisions.",
                        "acceptance_evidence": ["A1"],
                    }
                ],
            )
            init = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--mission-id",
                "m1",
                "--title",
                "Contract Failure Mission",
                "--objective",
                "Handle repeated contract failure.",
                "--acceptance-evidence",
                "A1:Decision can be safely applied or stopped.",
                "--task-json",
                str(tasks),
            )
            self.assertEqual(init.returncode, 0, init.stderr)

            stop = run_script(
                "stop_report.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--summary",
                "结构化决策输出连续两次不满足运行时契约。",
                "--current-goal",
                "应用 tplan 决策输出。",
                "--attempt",
                "第一次校验发现缺少必填字段，并返回修复模板。",
                "--attempt",
                "第二次校验仍然失败，输出不是合法 JSON。",
                "--blocking-issue",
                "无法获得满足运行时契约的 decision JSON。",
                "--why-cannot-continue-safely",
                "继续会要求 agent 猜测缺失字段或绕过严格状态契约。",
                "--need-from-human",
                "请确认正确的决策字段，或允许重新生成 decision JSON。",
                "--resume-condition",
                "人类提供可校验的 decision JSON 或确认新的执行方向。",
            )

            self.assertEqual(stop.returncode, 0, stop.stderr)
            self.assertIn("停止报告", stop.stdout)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertEqual(mission["mission"]["status"], "requires_human")


if __name__ == "__main__":
    unittest.main()

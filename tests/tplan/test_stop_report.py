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


def create_mission(tmp):
    mission_dir = Path(tmp) / "mission"
    tasks = Path(tmp) / "tasks.json"
    tasks.write_text(
        json.dumps(
            [
                {
                    "id": "T1",
                    "title": "Design scoring model",
                    "role": "success-critical",
                    "mission_contribution": "Defines the scoring model required by the Mission.",
                    "acceptance_evidence": ["A1"],
                }
            ]
        ),
        encoding="utf-8",
    )
    result = run_script(
        "init_mission.py",
        "--dir",
        str(mission_dir),
        "--mission-id",
        "m1",
        "--title",
        "Stop Mission",
        "--objective",
        "Design an evaluation scoring model.",
        "--acceptance-evidence",
        "A1:Scoring model exists.",
        "--task-json",
        str(tasks),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return mission_dir


class StopReportTests(unittest.TestCase):
    def test_stop_report_outputs_chinese_report_and_requests_human(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            active = run_script("transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "active")
            self.assertEqual(active.returncode, 0, active.stderr)

            result = run_script(
                "stop_report.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--summary",
                "评分标准依赖用户取舍，无法安全继续。",
                "--current-goal",
                "设计长任务 A/B 评估的评分模型。",
                "--attempt",
                "检查了现有 tplan 测试文档和 prompts。",
                "--attempt",
                "比较了主观评分与 artifact-based checks。",
                "--attempt",
                "尝试从现有样例推导评分阈值。",
                "--blocking-issue",
                "可接受的误判取舍属于产品判断，仓库资料中没有给出。",
                "--why-cannot-continue-safely",
                "如果由 agent 自行决定，benchmark 可能优化错误行为，但表面上仍然完整。",
                "--need-from-human",
                "请确认 benchmark 应优先严格发现失败，还是优先覆盖更广的通过场景。",
                "--resume-condition",
                "用户确认评分优先级。",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("停止报告", result.stdout)
            self.assertIn("当前目标：", result.stdout)
            self.assertIn("已尝试：", result.stdout)
            self.assertIn("需要人类提供：", result.stdout)

            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertEqual(mission["mission"]["status"], "requires_human")
            self.assertEqual(mission["active_task_id"], "T1")
            task = next(item for item in mission["tasks"] if item["id"] == "T1")
            self.assertEqual(task["status"], "blocked")

            events = [
                json.loads(line)
                for line in (mission_dir / "evidence.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(events), 1)
            event = events[0]
            self.assertEqual(event["event_type"], "stop_report")
            self.assertEqual(event["summary"], "评分标准依赖用户取舍，无法安全继续。")
            self.assertEqual(event["task_id"], "T1")
            self.assertEqual(event["payload"]["current_goal"], "设计长任务 A/B 评估的评分模型。")
            self.assertEqual(len(event["payload"]["attempts"]), 3)
            self.assertEqual(event["payload"]["resume_condition"], "用户确认评分优先级。")

    def test_stop_report_rejects_more_than_three_attempts_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)

            result = run_script(
                "stop_report.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--summary",
                "信息不足，无法安全继续。",
                "--current-goal",
                "设计评分模型。",
                "--attempt",
                "尝试一。",
                "--attempt",
                "尝试二。",
                "--attempt",
                "尝试三。",
                "--attempt",
                "尝试四。",
                "--blocking-issue",
                "缺少用户取舍。",
                "--why-cannot-continue-safely",
                "继续会编造验收标准。",
                "--need-from-human",
                "请确认评分优先级。",
                "--resume-condition",
                "用户确认后恢复。",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("attempts must contain at most 3 items", result.stderr)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertEqual(mission["mission"]["status"], "active")
            self.assertEqual((mission_dir / "evidence.jsonl").read_text(encoding="utf-8"), "")


if __name__ == "__main__":
    unittest.main()

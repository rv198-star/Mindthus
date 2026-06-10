import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
USAGE_LOGGER = REPO / "scripts" / "log-fidelity-usage.py"


class V101UsageLogTests(unittest.TestCase):
    def test_usage_logger_appends_and_validates_redacted_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "usage.jsonl"
            result = subprocess.run(
                [
                    "python3",
                    str(USAGE_LOGGER),
                    "--log",
                    str(log_path),
                    "--scenario",
                    "SELA 判断旧流程是否继续投入",
                    "--method",
                    "SELA",
                    "--model",
                    "gpt-5-codex",
                    "--judge-model",
                    "human-review",
                    "--baseline-score",
                    "7",
                    "--constrained-score",
                    "10",
                    "--max-score",
                    "12",
                    "--constraint-helped",
                    "yes",
                    "--source",
                    "#27",
                    "--tags",
                    "real-use,sela",
                ],
                text=True,
                capture_output=True,
                cwd=REPO,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("appended fidelity usage log record", result.stdout)

            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record["schema_version"], "mindthus-fidelity-usage-log-v0.1")
            self.assertEqual(record["record_type"], "real_use")
            self.assertEqual(record["method"], "SELA")
            self.assertEqual(record["model"], "gpt-5-codex")
            self.assertEqual(record["baseline_score"], 7)
            self.assertEqual(record["constrained_score"], 10)
            self.assertEqual(record["max_score"], 12)
            self.assertEqual(record["score_delta"], 3)
            self.assertEqual(record["constraint_helped"], "yes")
            self.assertEqual(record["tags"], ["real-use", "sela"])

            validation = subprocess.run(
                ["python3", str(USAGE_LOGGER), "--validate", "--log", str(log_path)],
                text=True,
                capture_output=True,
                cwd=REPO,
            )
            self.assertEqual(validation.returncode, 0, validation.stderr + validation.stdout)
            self.assertIn("Records: 1", validation.stdout)
            self.assertIn("No usage-log shape risks detected", validation.stdout)

    def test_usage_logger_allows_no_baseline_real_use_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "usage.jsonl"
            result = subprocess.run(
                [
                    "python3",
                    str(USAGE_LOGGER),
                    "--log",
                    str(log_path),
                    "--scenario",
                    "MPG 判断主线兑现前的路径承载",
                    "--method",
                    "MPG",
                    "--model",
                    "gpt-5-codex",
                    "--constrained-score",
                    "8",
                    "--max-score",
                    "10",
                    "--constraint-helped",
                    "mixed",
                ],
                text=True,
                capture_output=True,
                cwd=REPO,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertIsNone(record["baseline_score"])
            self.assertEqual(record["constrained_score"], 8)
            self.assertIsNone(record["score_delta"])

    def test_usage_logger_blocks_invalid_score_and_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "usage.jsonl"
            bad_record = {
                "schema_version": "mindthus-fidelity-usage-log-v0.1",
                "logged_at": "2026-06-08T00:00:00Z",
                "record_type": "real_use",
                "scenario": "bad score",
                "method": "SELA",
                "model": "fixture-model",
                "judge_model": "",
                "baseline_score": 7,
                "constrained_score": 13,
                "max_score": 12,
                "score_delta": 99,
                "constraint_helped": "yes",
                "source": "",
                "notes": "",
                "tags": [],
            }
            log_path.write_text(json.dumps(bad_record, ensure_ascii=False) + "\n", encoding="utf-8")

            result = subprocess.run(
                ["python3", str(USAGE_LOGGER), "--validate", "--log", str(log_path)],
                text=True,
                capture_output=True,
                cwd=REPO,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid-score", result.stdout)
            self.assertIn("invalid-score-delta", result.stdout)

    def test_v1_0_1_public_docs_and_release_pack_include_usage_logger(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        release_log = (REPO / "docs" / "releases" / "v1.0.1.md").read_text(encoding="utf-8")
        data_readme = (REPO / "data" / "README.md").read_text(encoding="utf-8")
        internal_doc = (REPO / "docs" / "internal" / "fidelity-usage-log.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "当前仓库版本：`v1.1.0`",
            "scripts/log-fidelity-usage.py",
            "data/fidelity-usage-log.jsonl",
            "可选：记录使用效果",
        ):
            self.assertIn(phrase, readme)

        for text in (changelog, release_log, data_readme, internal_doc):
            self.assertIn("log-fidelity-usage.py", text)
            self.assertIn("fidelity-usage-log.jsonl", text)

        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python3", "scripts/build-release-pack.py", "--out", tmp, "--force"],
                text=True,
                capture_output=True,
                cwd=REPO,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            root = Path(tmp)
            plugin = json.loads(
                (
                    root
                    / "claude-code"
                    / "claude-plugin"
                    / ".claude-plugin"
                    / "plugin.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(plugin["version"], "1.1.0")
            for platform_root in (
                root / "claude-code" / "claude-plugin",
                root / "codex",
                root / "opencode",
            ):
                self.assertTrue((platform_root / "scripts" / "run-fidelity-judge.py").is_file())
                self.assertTrue((platform_root / "scripts" / "log-fidelity-usage.py").is_file())


if __name__ == "__main__":
    unittest.main()

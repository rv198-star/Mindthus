import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "log-mindthus-runtime.py"


USING_TEXT = """\
Original Prompt Contract / 原始有效提示词合同
在回答前，先执行“输入审计”，不要顺着我的叙述直接推理
Truth Orientation / 真相优先
pursue facts and truth over agreement
user input is signal, constraint, or hypothesis; not evidence by itself
First task: judge whether the user led you to the wrong level
audit order: true_question -> implicit_premises -> local_validity_and_layer_shift -> reframed_question -> formal_answer
leading_point
Partial Truth Capture / 局部真相捕获
A locally true observation must not own the whole explanation
Whole Object Reconstruction / 整体对象还原
reconstruct the whole object before essence judgment
target job
main use cases
primary value carrier
local interface role
authority_weight
overreach_risk
corrected_thesis
grant authority only when the local frame carries the target result
would change the decision if removed
predicts outcomes or failures better than competing frames
blocked_by_missing_evidence when the whole-object carrier is unknown
definition consequence
optimization direction
Non-Mirror Correction / 非镜像纠错
Failure Channel / 失败通道
Anti-Sycophancy / 反谄媚
Core Thesis Extraction / 主判断收束
Essence Wording Guard / 本质措辞护栏
Auxiliary checks belong inside step 3
Explanatory Authority Check / 解释权校准
Dominant Carrier Check / 主导承载校准
System Subject Check / 系统主体校准
local correctness is not explanatory authority
"""

PRIMITIVES_TEXT = """\
Original Prompt Contract / 原始有效提示词合同
在回答前，先执行“输入审计”，不要顺着我的叙述直接推理
problem key over dialogue continuity
professional tone is not proof
common implementation is not essence
first task is not answering
leading_point
Partial Truth Capture / 局部真相捕获
A locally true observation must not own the whole explanation
Whole Object Reconstruction / 整体对象还原
reconstruct the whole object before essence judgment
target job
main use cases
primary value carrier
local interface role
authority_weight
overreach_risk
corrected_thesis
grant authority only when the local frame carries the target result
would change the decision if removed
predicts outcomes or failures better than competing frames
blocked_by_missing_evidence when the whole-object carrier is unknown
definition consequence
optimization direction
Non-Mirror Correction / 非镜像纠错
Failure Channel / 失败通道
Anti-Sycophancy / 反谄媚
Core Thesis Extraction / 主判断收束
Essence Wording Guard / 本质措辞护栏
Auxiliary checks belong inside step 3
System Subject Check / 系统主体校准
"""


def write_runtime_tree(root: Path, using_text: str = USING_TEXT, primitives_text: str = PRIMITIVES_TEXT) -> None:
    (root / "skills" / "using-mindthus").mkdir(parents=True)
    (root / "docs" / "methodologies").mkdir(parents=True)
    (root / "skills" / "using-mindthus" / "SKILL.md").write_text(using_text, encoding="utf-8")
    (root / "docs" / "methodologies" / "shared-primitives.md").write_text(
        primitives_text,
        encoding="utf-8",
    )


class LogMindthusRuntimeTests(unittest.TestCase):
    def test_reports_matching_runtime_fingerprints_and_markers_as_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            marketplace = root / "marketplace" / "codex-plugin" / "mindthus"
            cache = root / "cache" / "mindthus" / "mindthus" / "1.4.1"
            for runtime_root in (repo, marketplace, cache):
                write_runtime_tree(runtime_root)

            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--repo-root",
                    str(repo),
                    "--marketplace-root",
                    str(marketplace),
                    "--cache-root",
                    str(cache),
                    "--json",
                    "--strict",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["summary"]["status"], "ok")
            self.assertTrue(payload["summary"]["all_required_markers_present"])
            self.assertTrue(payload["summary"]["all_available_hashes_match"])
            self.assertIn("Truth Orientation / 真相优先", payload["markers"])
            self.assertIn("pursue facts and truth over agreement", payload["markers"])
            self.assertIn("First task: judge whether the user led you to the wrong level", payload["markers"])
            self.assertIn("Partial Truth Capture / 局部真相捕获", payload["markers"])
            self.assertIn("A locally true observation must not own the whole explanation", payload["markers"])
            self.assertIn("Whole Object Reconstruction / 整体对象还原", payload["markers"])
            self.assertIn(
                "reconstruct the whole object before essence judgment",
                payload["markers"],
            )
            self.assertIn("target job", payload["markers"])
            self.assertIn("main use cases", payload["markers"])
            self.assertIn("primary value carrier", payload["markers"])
            self.assertIn("local interface role", payload["markers"])
            self.assertIn("authority_weight", payload["markers"])
            self.assertIn("corrected_thesis", payload["markers"])
            self.assertIn(
                "grant authority only when the local frame carries the target result",
                payload["markers"],
            )
            self.assertIn("would change the decision if removed", payload["markers"])
            self.assertIn(
                "predicts outcomes or failures better than competing frames",
                payload["markers"],
            )
            self.assertIn(
                "blocked_by_missing_evidence when the whole-object carrier is unknown",
                payload["markers"],
            )
            self.assertIn("definition consequence", payload["markers"])
            self.assertIn("optimization direction", payload["markers"])
            self.assertIn("Non-Mirror Correction / 非镜像纠错", payload["markers"])
            self.assertIn("Failure Channel / 失败通道", payload["markers"])
            self.assertTrue(
                payload["locations"]["cache"]["files"]["skills/using-mindthus/SKILL.md"]["markers"][
                    "System Subject Check / 系统主体校准"
                ]
            )

    def test_strict_mode_fails_on_missing_marker_or_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            marketplace = root / "marketplace" / "codex-plugin" / "mindthus"
            cache = root / "cache" / "mindthus" / "mindthus" / "1.4.1"
            write_runtime_tree(repo)
            write_runtime_tree(marketplace)
            write_runtime_tree(
                cache,
                using_text=USING_TEXT.replace("System Subject Check / 系统主体校准\n", ""),
                primitives_text=PRIMITIVES_TEXT.replace("System Subject Check / 系统主体校准\n", ""),
            )

            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--repo-root",
                    str(repo),
                    "--marketplace-root",
                    str(marketplace),
                    "--cache-root",
                    str(cache),
                    "--json",
                    "--strict",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1, result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["summary"]["status"], "mismatch")
            self.assertFalse(payload["summary"]["all_required_markers_present"])
            self.assertFalse(payload["summary"]["all_available_hashes_match"])
            self.assertFalse(
                payload["locations"]["cache"]["files"]["skills/using-mindthus/SKILL.md"]["markers"][
                    "System Subject Check / 系统主体校准"
                ]
            )


if __name__ == "__main__":
    unittest.main()

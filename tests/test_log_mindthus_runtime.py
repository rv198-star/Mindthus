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
First task: judge whether the user led you to the wrong level
audit order: true_question -> implicit_premises -> local_validity_and_layer_shift -> reframed_question -> formal_answer
leading_point
Core Thesis Extraction / 主判断收束
Object Anchor / 对象锚定
keep asked object as subject
Essence Wording Guard / 本质措辞护栏
Composite Object Integrity / 复合对象完整性
Executable Substrate Check / 可执行基底校准
operative subcomponents move work from generation into execution/verification
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
Core Thesis Extraction / 主判断收束
Object Anchor / 对象锚定
keep asked object as subject
Essence Wording Guard / 本质措辞护栏
Composite Object Integrity / 复合对象完整性
Executable Substrate Check / 可执行基底校准
operative subcomponents move work from generation into execution/verification
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
            self.assertIn("First task: judge whether the user led you to the wrong level", payload["markers"])
            self.assertIn("Object Anchor / 对象锚定", payload["markers"])
            self.assertIn("keep asked object as subject", payload["markers"])
            self.assertIn("Composite Object Integrity / 复合对象完整性", payload["markers"])
            self.assertIn("Executable Substrate Check / 可执行基底校准", payload["markers"])
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

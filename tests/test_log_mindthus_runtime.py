import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "log-mindthus-runtime.py"
CURRENT_VERSION = "1.4.5"


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
Whole Elephant Protocol / 全象流程
Compact Semantic Triad / 三根硬支柱
misdirection_if_local_wins
Contrastive Consequence Probe / 后果对比探针
better_direction_for_target
local_success_points
weighted_synthesis
whole_first_re_evaluation
strategy_choice
definition_owner
result_controller
decision_consequence
validate_whole_elephant.py
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
Whole Elephant Protocol / 全象流程
Compact Semantic Triad / 三根硬支柱
start by naming the complete object before summarizing local truths
misdirection_if_local_wins
Contrastive Consequence Probe / 后果对比探针
better_direction_for_target
local_success_points
coverage_weight
weighted_synthesis
whole_first_re_evaluation
strategy_choice
definition_owner
result_controller
decision_consequence
When Partial Truth Capture triggers, the formal answer is incomplete without
scripts/primitives/validate_whole_elephant.py
mindthus-whole-elephant-audit-v0.1
validation failure blocks formal answer
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

ENTRY_TRIAGE_TEXT = """\
# Entry Triage / 入口分诊

Entry Triage is a before-route primitive.

- definition authority contest
- single-factor attribution
- local repair spiral
- forced binary prediction
- no-data numeric comparison
- trend-driven migration

Representative triggers:

- green tests imply release readiness -> Input Framing Audit

Every new trigger must pass public negative and shadow controls.

Root-cause evidence gate: timeline and metrics before conclusion.

Anti-Spiral hard brake: same local repair count >= 3 must stop adding and move upstream.

Visible consequence probe: name the consequence before advice.
"""


def load_runtime_logger():
    spec = importlib.util.spec_from_file_location("log_mindthus_runtime", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_runtime_tree(
    root: Path,
    using_text: str = USING_TEXT,
    primitives_text: str = PRIMITIVES_TEXT,
    *,
    runtime_layout: str = "skills",
) -> None:
    (root / "skills" / "using-mindthus" / "resources").mkdir(parents=True)
    (root / "docs" / "methodologies").mkdir(parents=True)
    (root / "docs" / "methodologies" / "primitives").mkdir(parents=True)
    (root / "scripts" / "primitives").mkdir(parents=True)
    (root / "skills" / "using-mindthus" / "scripts").mkdir(parents=True)
    runtime_root = root / ("_runtime" if runtime_layout == "top-level" else "skills/_runtime")
    (runtime_root / "core").mkdir(parents=True)
    (runtime_root / "fidelity").mkdir(parents=True)
    (root / "skills" / "using-mindthus" / "SKILL.md").write_text(using_text, encoding="utf-8")
    (root / "skills" / "using-mindthus" / "resources" / "calibration-pairs.yaml").write_text(
        "schema_version: mindthus-calibration-pairs-v0.1\n"
        "pairs:\n"
        "  - id: release-readiness-green-tests\n"
        "    failure_mode: local_success_claims_release_authority\n",
        encoding="utf-8",
    )
    (root / "docs" / "methodologies" / "shared-primitives.md").write_text(
        primitives_text,
        encoding="utf-8",
    )
    for primitive_file in (
        "aspect-ownership.md",
        "decision-context-calibration.md",
        "entry-triage.md",
        "expression-pressure-and-gates.md",
        "frame-fitness-check.md",
        "mpg-scalar-commitment-unpack.md",
        "whole-elephant-protocol.md",
    ):
        (root / "docs" / "methodologies" / "primitives" / primitive_file).write_text(
            ENTRY_TRIAGE_TEXT if primitive_file == "entry-triage.md" else primitives_text,
            encoding="utf-8",
        )
    (root / "scripts" / "primitives" / "manifest.json").write_text(
        '{"primitives":{"whole_elephant_protocol":{}}}\n',
        encoding="utf-8",
    )
    (root / "scripts" / "primitives" / "check.py").write_text(
        'SCHEMA_VERSION = "mindthus-primitive-activation-v0.1"\n',
        encoding="utf-8",
    )
    (root / "scripts" / "primitives" / "validate_whole_elephant.py").write_text(
        'SCHEMA_VERSION = "mindthus-whole-elephant-audit-v0.1"\n',
        encoding="utf-8",
    )
    (root / "scripts" / "primitives" / "whole_elephant_validator.py").write_text(
        'SCHEMA_VERSION = "mindthus-whole-elephant-audit-v0.1"\n',
        encoding="utf-8",
    )
    (root / "skills" / "using-mindthus" / "scripts" / "validate_using_mindthus_output.py").write_text(
        'SPEC = "using-mindthus-fidelity-v0.1"\n',
        encoding="utf-8",
    )
    for runtime_path in (
        runtime_root / "__init__.py",
        runtime_root / "core" / "__init__.py",
        runtime_root / "core" / "io.py",
        runtime_root / "core" / "report.py",
        runtime_root / "core" / "shape.py",
        runtime_root / "fidelity" / "__init__.py",
        runtime_root / "fidelity" / "core.py",
    ):
        runtime_path.write_text("# runtime fixture\n", encoding="utf-8")


class LogMindthusRuntimeTests(unittest.TestCase):
    def test_help_text_names_runtime_boundary(self):
        result = subprocess.run(
            ["python3", str(SCRIPT), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        help_text = " ".join(result.stdout.split())
        self.assertIn("installed files, hashes, and marker presence only", help_text)
        self.assertIn("does not prove model behavior", help_text)
        self.assertIn("semantic judgment quality", help_text)
        self.assertIn("runtime activation correctness", help_text)

    def test_parse_args_derives_cache_root_from_explicit_codex_home(self):
        logger = load_runtime_logger()
        codex_home = Path("/tmp/example-codex-home")

        args = logger.parse_args(["--codex-home", str(codex_home)])

        self.assertEqual(args.codex_home, codex_home)
        self.assertEqual(
            args.cache_root,
            codex_home / "plugins" / "cache" / "mindthus" / "mindthus" / logger.VERSION,
        )
        self.assertEqual(
            args.marketplace_root,
            codex_home / "local-marketplaces" / f"mindthus-v{logger.VERSION}" / "codex-plugin" / "mindthus",
        )

    def test_parse_args_preserves_explicit_roots(self):
        logger = load_runtime_logger()
        cache_root = Path("/tmp/explicit-cache")
        marketplace_root = Path("/tmp/explicit-marketplace")

        args = logger.parse_args(
            [
                "--codex-home",
                "/tmp/example-codex-home",
                "--cache-root",
                str(cache_root),
                "--marketplace-root",
                str(marketplace_root),
            ]
        )

        self.assertEqual(args.cache_root, cache_root)
        self.assertEqual(args.marketplace_root, marketplace_root)

    def test_reports_matching_runtime_fingerprints_and_markers_as_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            marketplace = root / "marketplace" / "codex-plugin" / "mindthus"
            cache = root / "cache" / "mindthus" / "mindthus" / CURRENT_VERSION
            write_runtime_tree(repo)
            write_runtime_tree(marketplace, runtime_layout="top-level")
            write_runtime_tree(cache, runtime_layout="top-level")

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
            self.assertIn("Entry Triage / 入口分诊", payload["markers"])
            self.assertIn("definition authority contest", payload["markers"])
            self.assertIn("green tests imply release readiness", payload["markers"])
            self.assertIn("negative and shadow controls", payload["markers"])
            self.assertIn("Root-cause evidence gate", payload["markers"])
            self.assertIn("same local repair count >= 3", payload["markers"])
            self.assertIn("Visible consequence probe", payload["markers"])
            self.assertIn("Partial Truth Capture / 局部真相捕获", payload["markers"])
            self.assertIn("A locally true observation must not own the whole explanation", payload["markers"])
            self.assertIn("Whole Object Reconstruction / 整体对象还原", payload["markers"])
            self.assertIn(
                "reconstruct the whole object before essence judgment",
                payload["markers"],
            )
            self.assertIn("Whole Elephant Protocol / 全象流程", payload["markers"])
            self.assertIn("Compact Semantic Triad / 三根硬支柱", payload["markers"])
            self.assertIn("misdirection_if_local_wins", payload["markers"])
            self.assertIn("Contrastive Consequence Probe / 后果对比探针", payload["markers"])
            self.assertIn("better_direction_for_target", payload["markers"])
            self.assertIn(
                "start by naming the complete object before summarizing local truths",
                payload["markers"],
            )
            self.assertIn("local_success_points", payload["markers"])
            self.assertIn("coverage_weight", payload["markers"])
            self.assertIn("weighted_synthesis", payload["markers"])
            self.assertIn("whole_first_re_evaluation", payload["markers"])
            self.assertIn("strategy_choice", payload["markers"])
            self.assertIn("definition_owner", payload["markers"])
            self.assertIn("result_controller", payload["markers"])
            self.assertIn("decision_consequence", payload["markers"])
            self.assertIn("validate_whole_elephant.py", payload["markers"])
            self.assertIn(
                "When Partial Truth Capture triggers, the formal answer is incomplete without",
                payload["markers"],
            )
            self.assertIn("mindthus-whole-elephant-audit-v0.1", payload["markers"])
            self.assertIn("validation failure blocks formal answer", payload["markers"])
            self.assertIn(
                "scripts/primitives/validate_whole_elephant.py",
                payload["locations"]["cache"]["files"],
            )
            self.assertIn(
                "scripts/primitives/whole_elephant_validator.py",
                payload["locations"]["cache"]["files"],
            )
            self.assertIn(
                "docs/methodologies/primitives/entry-triage.md",
                payload["locations"]["cache"]["files"],
            )
            self.assertIn(
                "skills/using-mindthus/resources/calibration-pairs.yaml",
                payload["locations"]["cache"]["files"],
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
            cache = root / "cache" / "mindthus" / "mindthus" / CURRENT_VERSION
            write_runtime_tree(repo)
            write_runtime_tree(marketplace, runtime_layout="top-level")
            write_runtime_tree(
                cache,
                using_text=USING_TEXT.replace("System Subject Check / 系统主体校准\n", ""),
                primitives_text=PRIMITIVES_TEXT.replace("System Subject Check / 系统主体校准\n", ""),
                runtime_layout="top-level",
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

    def test_strict_mode_fails_when_tracked_file_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            marketplace = root / "marketplace" / "codex-plugin" / "mindthus"
            cache = root / "cache" / "mindthus" / "mindthus" / CURRENT_VERSION
            write_runtime_tree(repo)
            write_runtime_tree(marketplace, runtime_layout="top-level")
            write_runtime_tree(cache, runtime_layout="top-level")
            (cache / "skills" / "using-mindthus" / "resources" / "calibration-pairs.yaml").unlink()

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
            self.assertFalse(payload["summary"]["all_tracked_files_present"])
            self.assertFalse(
                payload["locations"]["cache"]["files"][
                    "skills/using-mindthus/resources/calibration-pairs.yaml"
                ]["exists"]
            )


if __name__ == "__main__":
    unittest.main()

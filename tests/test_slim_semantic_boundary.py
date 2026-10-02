import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "slim_whole", ROOT / "scripts/primitives/whole_elephant_validator.py"
)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def compact(answer):
    return dict(
        schema_version=validator.SCHEMA_VERSION,
        canonical_object="发布准备",
        result_controller="用户影响、回滚和监控",
        misdirection_if_local_wins="测试全绿不能单独决定发布",
        local_frame_wins="只优化测试覆盖",
        whole_object_wins="在发布目标内检查运行和恢复",
        better_direction_for_target="按实际发布目标判断",
        visible_formal_answer=answer,
    )


class SlimSemanticBoundaryTests(unittest.TestCase):
    def test_same_judgment_wording_cannot_block(self):
        for answer in (
            "发布准备取决于用户影响、回滚和监控，不只是测试全绿。",
            "发布准备取决于用户影响、回滚和监控；测试全绿只是必要证据之一。",
            "确实，测试全绿有价值；发布仍取决于用户影响、回滚和监控。",
        ):
            with self.subTest(answer=answer):
                payload = compact(answer)
                before = copy.deepcopy(payload)
                self.assertEqual(validator.validate_audit(payload), [])
                report = validator.build_report(Path("audit.json"), payload, [])
                self.assertEqual(report["semantic_verdict"], "not_validated")
                self.assertTrue(report["agentic_judgment_required"])
                self.assertEqual(payload, before)

    def test_empty_judgment_is_not_semantically_approved(self):
        payload = compact("两边都有道理，不只是测试，还有其他很多重要因素。")
        report = validator.build_report(Path("audit.json"), payload, validator.validate_audit(payload))
        self.assertEqual(report["semantic_verdict"], "not_validated")
        self.assertTrue(report["semantic_hints"])

    def test_missing_field_and_illegal_enum_still_fail(self):
        payload = compact("只读局部检查已经充分。")
        del payload["result_controller"]
        self.assertIn("result_controller must be a non-empty string", validator.validate_audit(payload))
        payload = compact("局部定义可以成立。")
        payload["strategy_choice"] = "permission_to_ship"
        self.assertTrue(any("strategy_choice must be one of" in s for s in validator.validate_audit(payload)))

    def test_stdout_leak_still_blocks(self):
        payload = compact("script_verdict: shape_only；agentic_judgment_required: true")
        self.assertIn("visible_formal_answer must not expose internal script stdout", validator.validate_audit(payload))

    def test_t0_is_still_fixed(self):
        import hashlib
        root = ROOT / "docs/internal/optimization/sol61-slim-v0"
        freeze = json.loads((root / "freeze.json").read_text())
        for name, expected in freeze["source_files"].items():
            self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), expected, name)


if __name__ == "__main__":
    unittest.main()

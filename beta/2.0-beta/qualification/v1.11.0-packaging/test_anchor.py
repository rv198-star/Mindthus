"""Offline checks for the release-only shared-core anchor adaptation."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location("beta_builder", ROOT / "beta/2.0-beta/build-internal-beta.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class AnchorTests(unittest.TestCase):
    def setUp(self):
        profile = json.loads((ROOT / "beta/2.0-beta/profile.json").read_text())
        old = json.loads((ROOT / "beta/2.0-roi-thin-core/profile.json").read_text())
        self.anchor = profile["runtime_profile"]["package_time_anchor"]
        self.correction = old["package_time_contract_correction"]
        self.text = (ROOT / self.anchor["path"]).read_text()

    def test_preserves_qualified_after_and_all_other_shared_text(self):
        result = builder.apply_guardrail_correction(self.text, self.correction, self.anchor)
        self.assertEqual(result.count(self.correction["after"]), 1)
        self.assertEqual(result.replace(self.anchor["replacement_prefix"] + self.correction["after"], self.anchor["before"]), self.text)
        self.assertEqual(builder.apply_guardrail_correction(self.correction["before"], self.correction, None), self.correction["after"])

    def test_wrong_shared_source_hash_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "hash mismatch"):
            builder.apply_guardrail_correction(self.text + "changed", self.correction, self.anchor)

    def test_other_path_is_rejected(self):
        a = dict(self.anchor, path="skills/wae/SKILL.md")
        with self.assertRaisesRegex(SystemExit, "path mismatch"):
            builder.apply_guardrail_correction(self.text, self.correction, a)

    def test_missing_or_duplicate_anchor_is_rejected(self):
        for text in (self.text.replace(self.anchor["before"], ""), self.text + self.anchor["before"]):
            a = dict(self.anchor, shared_source_sha256=hashlib.sha256(text.encode()).hexdigest())
            with self.assertRaisesRegex(SystemExit, "exactly once"):
                builder.apply_guardrail_correction(text, self.correction, a)

if __name__ == "__main__":
    unittest.main(verbosity=2)

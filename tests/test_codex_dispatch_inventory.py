import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/codex-dispatch/scripts/model_inventory.py"

# A stdio double that rejects unexpected methods and captures wire requests.
APP_SERVER = textwrap.dedent("""\
    import json
    import os
    import sys
    import time

    def reply(id, **body):
        print(json.dumps(dict(id=id, **body)), flush=True)

    def model(id, level, hidden=False):
        return {
            "id": id, "model": "wire/" + id, "displayName": "Model " + id,
            "supportedReasoningEfforts": [
                {"reasoningEffort": level, "description": "fixture level"}
            ],
            "defaultReasoningEffort": level, "hidden": hidden,
            "description": "field outside the inventory projection",
        }

    for line in sys.stdin:
        payload = json.loads(line)
        with open(os.environ["DISPATCH_WIRE_LOG"], "a") as log:
            log.write(line)
        method = payload["method"]
        id = payload.get("id")
        if method == "initialize":
            reply(id, result={})
        elif method == "initialized":
            continue
        elif method == "model/list":
            mode = os.environ["DISPATCH_TEST_MODE"]
            cursor = payload["params"].get("cursor")
            if not cursor:
                print(json.dumps({"method": "unrelated/event"}), flush=True)
                reply(id, result={"data": [model("a", "high"), model("hidden", "low", True)],
                                  "nextCursor": "page-2"})
            elif mode == "rpc-error":
                reply(id, error={"code": -32602, "message": "internal detail"})
            elif mode == "timeout":
                time.sleep(20)
            elif mode == "repeated-cursor":
                reply(id, result={"data": [], "nextCursor": "page-2"})
            else:
                reply(id, result={"data": [model("b", "xhigh")], "nextCursor": None})
        else:
            raise SystemExit("unexpected dispatch method")
    """)


class ModelInventoryTests(unittest.TestCase):
    def probe(self, mode, *options):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            binary = folder / "fake-codex"
            log = folder / "wire.jsonl"
            binary.write_text(f"#!{sys.executable}\n{APP_SERVER}", encoding="utf-8")
            binary.chmod(0o755)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--host", "fixture", "--cli",
                 "--codex-bin", str(binary), "--page-size", "2", "--timeout", "2", *options],
                env={**os.environ, "DISPATCH_WIRE_LOG": str(log), "DISPATCH_TEST_MODE": mode},
                text=True,
                capture_output=True,
                timeout=8,
            )
            calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        return result, calls

    def test_all_pages_share_provider_and_visibility_and_preserve_efforts(self):
        result, calls = self.probe("ok", "--provider", "selected")
        self.assertEqual(result.returncode, 0, result.stderr)
        inventory = json.loads(result.stdout)
        self.assertEqual(inventory["modelProvider"], "selected")
        self.assertEqual(inventory["models"], [
            {"id": "a", "model": "wire/a", "displayName": "Model a",
             "supportedReasoningEfforts": ["high"], "defaultReasoningEffort": "high"},
            {"id": "b", "model": "wire/b", "displayName": "Model b",
             "supportedReasoningEfforts": ["xhigh"], "defaultReasoningEffort": "xhigh"},
        ])
        self.assertEqual([c["method"] for c in calls],
                         ["initialize", "initialized", "model/list", "model/list"])
        expected = {"includeHidden": False, "limit": 2, "modelProvider": "selected"}
        self.assertEqual(calls[2]["params"], expected)
        self.assertEqual(calls[3]["params"], {**expected, "cursor": "page-2"})

    def test_partial_catalog_cannot_escape_on_failed_second_page(self):
        for mode, explanation in (
            ("rpc-error", "RPC error -32602"),
            ("repeated-cursor", "repeated model/list cursor"),
            ("timeout", "Timed out waiting for model/list"),
        ):
            with self.subTest(mode=mode):
                result, calls = self.probe(mode)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                self.assertIn(explanation, result.stderr)
                self.assertNotIn("internal detail", result.stderr)
                self.assertNotIn("modelProvider", calls[2]["params"])
                self.assertEqual(len(calls), 4)


if __name__ == "__main__":
    unittest.main()

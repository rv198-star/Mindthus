import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
TVG = REPO / "skills" / "tvg"


def read(path):
    return (REPO / path).read_text(encoding="utf-8")


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(TVG / "scripts" / "trace" / script_name), *args],
        text=True,
        capture_output=True,
    )


class TvgTraceContractTests(unittest.TestCase):
    def test_docs_define_trace_as_audit_log_not_decision_context(self):
        combined = "\n".join(
            [
                read("skills/tvg/SKILL.md"),
                read("skills/tvg/resources/methodology.md"),
                read("skills/tvg/resources/trace-record-schema.json"),
            ]
        )

        for phrase in (
            "audit/calibration log",
            "not working context",
            "must not control flow decisions",
            "Do not replay the full trace",
            "summarize current-round outcome",
        ):
            self.assertIn(phrase, combined)

    def test_init_trace_records_boundary_and_validate_accepts_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"

            init = run_script(
                "init.py",
                "--module-id",
                "m1",
                "--module-title",
                "Trace Boundary",
                "--module-type",
                "methodology",
                "--output",
                str(trace),
            )

            self.assertEqual(init.returncode, 0, init.stderr)
            data = json.loads(trace.read_text(encoding="utf-8"))
            schema = json.loads((TVG / "resources" / "trace-record-schema.json").read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], "tvg-trace-v0.3")
            self.assertEqual(schema["schema_version"], "tvg-trace-v0.3")
            support = data["script_support"]
            self.assertEqual(support["trace_role"], "audit_calibration_log")
            self.assertIn("not working context", " ".join(support["trace_boundary"]))
            self.assertIn("must not control flow decisions", " ".join(support["trace_boundary"]))

            validate = run_script("validate.py", str(trace))
            self.assertEqual(validate.returncode, 0, validate.stderr)

    def test_validate_rejects_missing_trace_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            init = run_script(
                "init.py",
                "--module-id",
                "m1",
                "--module-title",
                "Trace Boundary",
                "--module-type",
                "methodology",
                "--output",
                str(trace),
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            data = json.loads(trace.read_text(encoding="utf-8"))
            del data["script_support"]["trace_boundary"]
            trace.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            validate = run_script("validate.py", str(trace))

            self.assertNotEqual(validate.returncode, 0)
            self.assertIn("missing script_support field: trace_boundary", validate.stdout)


if __name__ == "__main__":
    unittest.main()

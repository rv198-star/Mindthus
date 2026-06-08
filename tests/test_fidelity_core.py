import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def run_validator(script: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "payload.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return subprocess.run(
            ["python3", str(script), str(path)],
            text=True,
            capture_output=True,
            cwd=REPO,
        )


class FidelityCoreTests(unittest.TestCase):
    def test_core_module_defines_shared_shape_engine(self):
        text = (REPO / "skills" / "_runtime" / "fidelity" / "core.py").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "FidelitySpec",
            "Finding",
            "validate_fidelity_output",
            "print_text_report",
            "Shape & Evidence Risk Report",
            "agentic audit remains required",
            "does not validate semantic truth",
        ):
            self.assertIn(phrase, text)

    def test_sela_and_mpg_validators_reuse_core(self):
        for path in (
            REPO / "skills" / "sela" / "scripts" / "validate_sela_output.py",
            REPO / "skills" / "mpg" / "scripts" / "validate_mpg_output.py",
        ):
            text = path.read_text(encoding="utf-8")
            self.assertIn("_runtime.fidelity.core", text)
            self.assertIn("FidelitySpec", text)
            self.assertNotIn("@dataclass", text)

    def test_core_keeps_sela_and_mpg_cli_behavior(self):
        sela_payload = {
            "schema_version": "sela-fidelity-v0.1",
            "method": "SELA",
            "applicability": "transfer",
            "plain_language_conclusion": "SELA is not the dominant method.",
            "exit_reason": "The decision is about evidence governance.",
            "transfer_to": "WAE",
        }
        mpg_payload = {
            "schema_version": "mpg-fidelity-v0.1",
            "method": "MPG",
            "applicability": "transfer",
            "plain_language_conclusion": "MPG is not dominant without a carrier.",
            "exit_reason": "No actor or exposure decision exists.",
            "transfer_to": "SELA",
        }

        sela = run_validator(
            REPO / "skills" / "sela" / "scripts" / "validate_sela_output.py",
            sela_payload,
        )
        mpg = run_validator(
            REPO / "skills" / "mpg" / "scripts" / "validate_mpg_output.py",
            mpg_payload,
        )

        self.assertEqual(sela.returncode, 0, sela.stderr + sela.stdout)
        self.assertEqual(mpg.returncode, 0, mpg.stderr + mpg.stdout)
        self.assertIn("method exit accepted", sela.stdout)
        self.assertIn("method exit accepted", mpg.stdout)


if __name__ == "__main__":
    unittest.main()

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLI_PATH = REPO / "scripts" / "mindthus_cli.py"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(CLI_PATH), *args],
        text=True,
        capture_output=True,
    )


class MindthusCLITests(unittest.TestCase):
    def test_main_help(self):
        # 1. Test running with no arguments
        res1 = run_cli()
        self.assertEqual(res1.returncode, 0)
        self.assertIn("usage:", res1.stdout.lower())
        self.assertIn("mindthus", res1.stdout.lower())
        self.assertIn("WAE Boundary", res1.stdout)
        self.assertIn("install", res1.stdout)
        self.assertIn("doctor", res1.stdout)
        self.assertIn("tplan <subcommand>", res1.stdout)

        # 2. Test running with --help
        res2 = run_cli("--help")
        self.assertEqual(res2.returncode, 0)
        self.assertEqual(res1.stdout, res2.stdout)

        # 3. Test running with help
        res3 = run_cli("help")
        self.assertEqual(res3.returncode, 0)
        self.assertEqual(res1.stdout, res3.stdout)

    def test_tplan_help(self):
        res = run_cli("tplan", "--help")
        self.assertEqual(res.returncode, 0)
        self.assertIn("usage: mindthus tplan <subcommand>", res.stdout.lower() or "")
        self.assertIn("init-lite", res.stdout)
        self.assertIn("preflight", res.stdout)
        self.assertIn("checkpoint", res.stdout)

    def test_invalid_command(self):
        res = run_cli("not-a-command")
        self.assertEqual(res.returncode, 1)
        self.assertIn("Error: unknown command", res.stderr)

    def test_doctor(self):
        res = run_cli("doctor")
        self.assertEqual(res.returncode, 0)
        self.assertIn("Running Mindthus environment diagnostics...", res.stdout)
        self.assertIn("Diagnostics: OK", res.stdout)

    def test_preflight_forwarding(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            project_root.mkdir(parents=True, exist_ok=True)
            
            res = run_cli(
                "tplan",
                "preflight",
                "--project-root",
                str(project_root),
                "--mission-id",
                "test-cli-mission",
                "--objective",
                "Test objective.",
                "--json",
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            data = json.loads(res.stdout)
            self.assertEqual(data["action"], "create_new")
            self.assertEqual(len(data["conflicts"]), 0)

    def test_cli_included_in_release_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "dist"
            
            # Execute the release build script
            build_script = REPO / "scripts" / "build-release-pack.py"
            res = subprocess.run(
                [sys.executable, str(build_script), "--out", str(out_dir)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            
            # Verify that mindthus_cli.py was successfully copied into the plugins and skills directories
            paths_to_check = [
                out_dir / "claude-code" / "claude-plugin" / "scripts" / "mindthus_cli.py",
                out_dir / "claude-code" / "scripts" / "mindthus_cli.py",
                out_dir / "codex" / "scripts" / "mindthus_cli.py",
                out_dir / "codex-plugin" / "mindthus" / "scripts" / "mindthus_cli.py",
                out_dir / "opencode" / "scripts" / "mindthus_cli.py",
            ]
            for p in paths_to_check:
                self.assertTrue(p.exists(), f"Release CLI file does not exist: {p}")
                self.assertTrue(p.is_file())


if __name__ == "__main__":
    unittest.main()

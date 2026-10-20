"""Exercise Q2 from real packaged, archived and cleanly extracted layouts.

These are local candidate packs, not a published product release. No credentials,
external services or installed Skills are used.
"""
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LAYOUTS = {
    "claude-plugin": "claude-code/claude-plugin/skills/tplan",
    "codex-plugin": "codex-plugin/mindthus/skills/tplan",
    "claude-skills": "claude-code/skills/tplan",
    "codex-skills": "codex/skills/mindthus/tplan",
    "opencode-skills": "opencode/.opencode/skills/mindthus/tplan",
}


class CommandReleasePackTests(unittest.TestCase):
    def test_five_clean_packaged_layouts_can_commit_read_and_replay(self):
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        report = {"scope": "local_candidate_pack_not_release", "layouts": []}
        with tempfile.TemporaryDirectory(prefix="tplan-q2-pack-") as temporary:
            root = Path(temporary)
            built, extracted = root / "built", root / "extracted"
            r = subprocess.run([sys.executable, "-B", str(REPO / "scripts/build-release-pack.py"),
                                "--out", str(built), "--package", "all"],
                               env=env, text=True, capture_output=True, timeout=45)
            self.assertEqual(r.returncode, 0, r.stderr)
            archive = root / "candidate-layouts.tar.gz"
            with tarfile.open(archive, "w:gz") as output:
                output.add(built, arcname="candidate")
            report["archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
            report["archive_bytes"] = archive.stat().st_size
            # Only our own just-created local archive is read; no remote input.
            with tarfile.open(archive, "r:gz") as source:
                for member in source.getmembers():
                    self.assertFalse(member.issym() or member.islnk())
                    self.assertFalse(Path(member.name).is_absolute() or ".." in Path(member.name).parts)
                source.extractall(extracted)
            candidate = extracted / "candidate"
            for label, relative in LAYOUTS.items():
                with self.subTest(layout=label):
                    skill = candidate / relative
                    scripts = skill / "scripts"
                    self.assertTrue((scripts / "command_runtime.py").is_file())
                    manifest = json.loads((skill / "resources/runtime-manifest.json").read_text())
                    for required in manifest["required_scripts"]:
                        self.assertTrue((skill / required).is_file(), required)
                    self.assertTrue((skill.parent / "runtime_bootstrap.py").is_file())
                    self.assertTrue(any((p / "_runtime/core/io.py").is_file() for p in skill.parents))
                    state_dir = root / ("mission-" + label)
                    tasks = root / (label + "-tasks.json")
                    tasks.write_text(json.dumps([{"id": "T1", "title": "Pack fixture",
                        "role": "success-critical", "mission_contribution": "Verify candidate pack",
                        "acceptance_evidence": ["A1"]}]))
                    def run(name, *args, isolated=False):
                        options = ["-B"] + (["-I"] if isolated else [])
                        result = subprocess.run([sys.executable, *options, str(scripts / name), *args],
                                                env=env, text=True, capture_output=True, timeout=20)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        return result
                    run("init_mission.py", "--dir", str(state_dir), "--mission-id", state_dir.name,
                        "--title", label, "--objective", "Verify complete package dependency closure",
                        "--acceptance-evidence", "A1:Real packaged command succeeds", "--task-json", str(tasks),
                        "--command-results")
                    state = json.loads((state_dir / "mission.json").read_text())
                    build = state["runtime_provenance"]["fingerprint"]["build_hash"]
                    request = {"protocol": "tplan.command.v1", "action": "evidence.record",
                        "mission_id": state_dir.name, "command_id": "pack-command",
                        "expected_build_hash": build, "payload": {"summary": "Pack observation",
                        "task_id": "T1", "data": {"layout": label}}}
                    args = ["--mission-dir", str(state_dir), "--principal", "pack-test",
                            "--request-json", json.dumps(request)]
                    first = json.loads(run("command_runtime.py", *args, isolated=True).stdout)
                    again = json.loads(run("command_runtime.py", *args, isolated=True).stdout)
                    self.assertEqual(first["status"], "committed")
                    self.assertEqual(again["status"], "replayed")
                    self.assertEqual(first["data"], again["data"])
                    observation = {"protocol": "tplan.query.v1", "action": "command.get",
                        "mission_id": state_dir.name, "request_id": "pack-read", "command_id": "pack-command",
                        "expected_build_hash": build}
                    got = json.loads(run("query_runtime.py", "--mission-dir", str(state_dir),
                        "--request-json", json.dumps(observation), isolated=True).stdout)
                    self.assertEqual(got["data"]["result"], first["data"])
                    self.assertEqual(len((state_dir / "evidence.jsonl").read_text().splitlines()), 1)
                    report["layouts"].append({"layout": label, "passed": True, "runtime_build": build,
                        "required_files": len(manifest["required_scripts"]),
                        "command_source_sha256": hashlib.sha256((scripts / "tplan_commands.py").read_bytes()).hexdigest()})
            self.assertEqual(len({x["runtime_build"] for x in report["layouts"]}), 1)
            self.assertFalse(list(candidate.rglob("*.pyc")))
        target = os.environ.get("TPLAN_Q2_PACK_REPORT")
        if target:
            Path(target).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    unittest.main()

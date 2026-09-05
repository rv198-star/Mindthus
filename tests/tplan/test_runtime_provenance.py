import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "tplan"
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from runtime_doctor import build_doctor_report, normalize_tplan_root
from tplan_runtime import (
    TplanError,
    append_event,
    append_step_log,
    archive_task_logs,
    begin_interaction_guard,
    runtime_fingerprint,
    runtime_fingerprint_compatibility,
    start_execution_span,
)


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script_name), *args],
        text=True,
        capture_output=True,
    )


def create_mission(tmp):
    mission_dir = Path(tmp) / "runtime-provenance"
    tasks = Path(tmp) / "tasks.json"
    tasks.write_text(
        json.dumps(
            [
                {
                    "id": "T1",
                    "title": "Prove runtime provenance",
                    "role": "success-critical",
                    "mission_contribution": "Exercises the supported runtime boundary.",
                    "acceptance_evidence": ["A1"],
                }
            ]
        ),
        encoding="utf-8",
    )
    result = run_script(
        "init_mission.py",
        "--dir",
        str(mission_dir),
        "--mission-id",
        "runtime-provenance",
        "--title",
        "Runtime provenance",
        "--objective",
        "Detect stale or duplicate TPlan runtime selection.",
        "--acceptance-evidence",
        "A1:Runtime selection is diagnosed before mutation or terminal handoff.",
        "--task-json",
        str(tasks),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return mission_dir


def read_mission(mission_dir):
    return json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))


def write_mission(mission_dir, mission):
    (mission_dir / "mission.json").write_text(
        json.dumps(mission, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def corrupt_recorded_build_hash(mission):
    mission["runtime_provenance"]["fingerprint"]["build_hash"] = "sha256:" + "0" * 64


def create_stale_v11_runtime(tmp):
    checkout = Path(tmp) / "root" / ".codex" / "mindthus"
    root = checkout / "skills" / "tplan"
    (root / "resources").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "scripts" / "tplan_runtime.py").write_text(
        "# historical v1.1 runtime fixture\n",
        encoding="utf-8",
    )
    commands = (
        ("init",),
        ("config", "user.email", "tplan-fixture@example.invalid"),
        ("config", "user.name", "TPlan Fixture"),
        ("add", "."),
        ("commit", "-m", "historical v1.1 runtime fixture"),
        ("tag", "v1.1.0"),
    )
    for command in commands:
        result = subprocess.run(
            ["git", "-C", str(checkout), *command],
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr)
    return root


def runtime_artifact_snapshot(mission_dir):
    return {
        str(path.relative_to(mission_dir)): path.read_bytes()
        for path in mission_dir.rglob("*")
        if path.is_file() and path.name != ".execution_trace.lock"
    }


class RuntimeProvenanceTests(unittest.TestCase):
    def test_doctor_normalizes_checkout_and_skills_roots_to_tplan(self):
        self.assertEqual(normalize_tplan_root(REPO), SKILL.resolve())
        self.assertEqual(normalize_tplan_root(REPO / "skills"), SKILL.resolve())
        self.assertEqual(normalize_tplan_root(SKILL), SKILL.resolve())

    def test_extracted_implementations_are_required_and_fingerprinted(self):
        from tplan_errors import TplanError as SharedError
        from tplan_identity import runtime_fingerprint as identity_fingerprint
        self.assertIs(TplanError, SharedError)
        self.assertIs(runtime_fingerprint, identity_fingerprint)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            shutil.copytree(SKILL, root, ignore=shutil.ignore_patterns("__pycache__"))
            baseline = runtime_fingerprint(root)["build_hash"]
            for name in ("tplan_errors.py", "tplan_identity.py", "execution_time_metrics.py"):
                with self.subTest(module=name):
                    path = root / "scripts" / name
                    content = path.read_bytes()
                    path.write_bytes(content + b"\n# fingerprint mutation probe\n")
                    self.assertNotEqual(runtime_fingerprint(root)["build_hash"], baseline)
                    path.unlink()
                    with self.assertRaisesRegex(TplanError, "required scripts"):
                        runtime_fingerprint(root)
                    path.write_bytes(content)
                    self.assertEqual(runtime_fingerprint(root)["build_hash"], baseline)

    def test_new_mission_pins_current_runtime_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission = read_mission(create_mission(tmp))

        provenance = mission["runtime_provenance"]
        fingerprint = provenance["fingerprint"]
        self.assertEqual(provenance["origin"], "native")
        self.assertEqual(fingerprint["package_version"], "1.5.4")
        self.assertEqual(fingerprint["skill_root"], str(SKILL.resolve()))
        self.assertEqual(fingerprint["script_root"], str(SCRIPTS.resolve()))
        self.assertEqual(
            fingerprint["capability_versions"]["runtime_provenance"],
            "tplan.runtime_provenance.v0.1",
        )
        self.assertRegex(fingerprint["build_hash"], r"^sha256:[0-9a-f]{64}$")

    def test_incompatible_runtime_blocks_supported_mutation_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            mission = read_mission(mission_dir)
            corrupt_recorded_build_hash(mission)
            write_mission(mission_dir, mission)
            before_mission = (mission_dir / "mission.json").read_bytes()
            before_trace = (mission_dir / "execution_trace.jsonl").read_bytes()

            result = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--status",
                "active",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("runtime fingerprint mismatch", result.stderr)
            self.assertEqual((mission_dir / "mission.json").read_bytes(), before_mission)
            self.assertEqual(
                (mission_dir / "execution_trace.jsonl").read_bytes(),
                before_trace,
            )

    def test_incompatible_runtime_blocks_every_canonical_artifact_writer(self):
        writers = {
            "evidence": lambda mission_dir: append_event(
                mission_dir,
                {
                    "event_type": "verification",
                    "summary": "must not be written",
                    "task_id": "T1",
                    "payload": {},
                },
            ),
            "trace": lambda mission_dir: start_execution_span(
                mission_dir,
                {
                    "task_id": "T1",
                    "span": {
                        "kind": "tool",
                        "label": "provenance probe",
                        "measurement_source": "host_measured",
                        "attribution": "exact",
                    },
                },
            ),
            "step_log": lambda mission_dir: append_step_log(
                mission_dir,
                {"task_id": "T1", "summary": "must not be written"},
            ),
            "archive": lambda mission_dir: archive_task_logs(
                mission_dir,
                "T1",
                "must not be written",
            ),
            "interaction_guard": lambda mission_dir: begin_interaction_guard(
                mission_dir,
                platform="test-host",
                message_ref="M1",
            ),
        }
        for name, writer in writers.items():
            with self.subTest(writer=name), tempfile.TemporaryDirectory() as tmp:
                mission_dir = create_mission(tmp)
                mission = read_mission(mission_dir)
                corrupt_recorded_build_hash(mission)
                write_mission(mission_dir, mission)
                before = runtime_artifact_snapshot(mission_dir)

                with self.assertRaisesRegex(TplanError, "runtime fingerprint mismatch"):
                    writer(mission_dir)

                self.assertEqual(runtime_artifact_snapshot(mission_dir), before)

    def test_legacy_evidence_writer_adopts_runtime_before_appending(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            mission = read_mission(mission_dir)
            mission.pop("runtime_provenance")
            write_mission(mission_dir, mission)

            event = append_event(
                mission_dir,
                {
                    "event_type": "verification",
                    "summary": "legacy writer adoption",
                    "task_id": "T1",
                    "payload": {},
                },
            )

            self.assertTrue(event["id"])
            adopted = read_mission(mission_dir)["runtime_provenance"]
            self.assertEqual(adopted["origin"], "legacy_adopted")

    def test_legacy_mission_is_readable_then_adopted_by_first_supported_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            mission = read_mission(mission_dir)
            mission.pop("runtime_provenance")
            write_mission(mission_dir, mission)

            check = run_script("check_mission.py", str(mission_dir))
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertIn("runtime_provenance_missing", check.stdout)

            transition = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--status",
                "active",
            )
            self.assertEqual(transition.returncode, 0, transition.stderr)
            adopted = read_mission(mission_dir)["runtime_provenance"]
            self.assertEqual(adopted["origin"], "legacy_adopted")
            self.assertEqual(adopted["fingerprint"]["package_version"], "1.5.4")

    def test_terminal_handoff_fails_closed_before_replacing_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            mission = read_mission(mission_dir)
            corrupt_recorded_build_hash(mission)
            write_mission(mission_dir, mission)

            diagnostic_render = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--format",
                "json",
            )
            self.assertEqual(diagnostic_render.returncode, 0, diagnostic_render.stderr)
            report = json.loads(diagnostic_render.stdout)
            self.assertEqual(report["runtime"]["severity"], "error")
            self.assertEqual(
                report["runtime"]["diagnostics"][0]["code"],
                "runtime_fingerprint_mismatch",
            )

            handoff = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--completion-handoff",
            )
            self.assertNotEqual(handoff.returncode, 0)
            self.assertIn("artifacts were not replaced", handoff.stderr)
            self.assertFalse((mission_dir / "reports" / "execution-cost-tree.md").exists())
            self.assertFalse((mission_dir / "reports" / "execution-cost-tree.svg").exists())

    def test_pending_transaction_cannot_roll_forward_incompatible_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            current = read_mission(mission_dir)
            pending = json.loads(json.dumps(current))
            corrupt_recorded_build_hash(pending)
            trace_path = mission_dir / "execution_trace.jsonl"
            transaction = {
                "schema_version": "tplan.mission_transaction.v0.2",
                "transaction_id": "TX-runtime-mismatch",
                "prepared_at": "2026-07-24T00:00:00+00:00",
                "mission": pending,
                "trace_text": trace_path.read_text(encoding="utf-8"),
                "evidence_text": None,
                "latest_state": None,
                "guard_after": None,
            }
            transaction_path = mission_dir / ".mission-transaction.json"
            transaction_path.write_text(
                json.dumps(transaction, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            before_mission = (mission_dir / "mission.json").read_bytes()
            before_trace = trace_path.read_bytes()

            result = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--status",
                "active",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("runtime_provenance is runtime-owned and immutable", result.stderr)
            self.assertEqual((mission_dir / "mission.json").read_bytes(), before_mission)
            self.assertEqual(trace_path.read_bytes(), before_trace)
            self.assertTrue(transaction_path.exists())

    def test_check_mission_rejects_runtime_fingerprint_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            mission = read_mission(mission_dir)
            corrupt_recorded_build_hash(mission)
            write_mission(mission_dir, mission)

            check = run_script("check_mission.py", str(mission_dir))

            self.assertNotEqual(check.returncode, 0)
            self.assertIn("runtime_fingerprint_mismatch", check.stdout)

    def test_doctor_diagnoses_explicit_stale_v11_against_installed_v152(self):
        with tempfile.TemporaryDirectory() as tmp:
            stale = create_stale_v11_runtime(tmp)
            report = build_doctor_report(
                selected_root=stale,
                installed_root=SKILL,
                candidate_roots=[stale, SKILL],
                selection_mode="explicit",
                mission_dir=None,
                include_default_candidates=False,
            )

        codes = {item["code"] for item in report["diagnostics"]}
        by_root = {item["skill_root"]: item for item in report["candidates"]}
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["selected_root"], str(stale.resolve()))
        self.assertEqual(report["installed_root"], str(SKILL.resolve()))
        self.assertEqual(by_root[str(stale.resolve())]["package_version"], "1.1.0")
        self.assertEqual(by_root[str(stale.resolve())]["identity_source"], "git")
        self.assertEqual(
            by_root[str(stale.resolve())]["git_identity"]["describe"],
            "v1.1.0",
        )
        self.assertRegex(
            by_root[str(stale.resolve())]["source_id"],
            r"^git:[0-9a-f]{40,64}$",
        )
        self.assertEqual(by_root[str(stale.resolve())]["capability_source"], "filesystem_probe")
        self.assertEqual(by_root[str(stale.resolve())]["capabilities"], [])
        self.assertEqual(by_root[str(SKILL.resolve())]["package_version"], "1.5.4")
        self.assertIn("scripts/render_execution_cost_tree.py", by_root[str(stale.resolve())]["missing_scripts"])
        self.assertIn("selected_runtime_missing_renderer", codes)
        self.assertIn("selected_runtime_incompatible_capabilities", codes)
        self.assertIn("selected_runtime_incompatible_with_installed", codes)
        self.assertIn("duplicate_runtime_roots", codes)
        self.assertNotIn("ambiguous_duplicate_runtime", codes)

    def test_doctor_distinguishes_explicit_selection_from_ambiguous_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            stale = create_stale_v11_runtime(tmp)
            explicit = build_doctor_report(
                selected_root=SKILL,
                installed_root=SKILL,
                candidate_roots=[stale, SKILL],
                selection_mode="explicit",
                mission_dir=None,
                include_default_candidates=False,
            )
            ambiguous = build_doctor_report(
                selected_root=None,
                installed_root=SKILL,
                candidate_roots=[stale, SKILL],
                selection_mode="discovery",
                mission_dir=None,
                include_default_candidates=False,
            )

        explicit_codes = {item["code"] for item in explicit["diagnostics"]}
        ambiguous_codes = {item["code"] for item in ambiguous["diagnostics"]}
        self.assertEqual(explicit["status"], "warning")
        self.assertIn("duplicate_runtime_roots", explicit_codes)
        self.assertNotIn("ambiguous_duplicate_runtime", explicit_codes)
        self.assertEqual(ambiguous["status"], "failed")
        self.assertIsNone(ambiguous["selected_root"])
        self.assertIn("ambiguous_duplicate_runtime", ambiguous_codes)

    def test_exact_build_at_relocated_path_is_compatible_with_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            relocated = Path(tmp) / "relocated-tplan"
            shutil.copytree(SKILL, relocated)

            compatibility = runtime_fingerprint_compatibility(
                runtime_fingerprint(SKILL),
                runtime_fingerprint(relocated),
            )
            report = build_doctor_report(
                selected_root=relocated,
                installed_root=SKILL,
                candidate_roots=[relocated, SKILL],
                selection_mode="explicit",
                mission_dir=None,
                include_default_candidates=False,
            )

        codes = {item["code"] for item in report["diagnostics"]}
        self.assertEqual(compatibility["status"], "compatible_relocated")
        self.assertTrue(compatibility["compatible"])
        self.assertEqual(report["status"], "warning")
        self.assertIn("selected_runtime_relocated_from_installed", codes)


if __name__ == "__main__":
    unittest.main()

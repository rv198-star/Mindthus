import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import tplan_runtime  # noqa: E402


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(REPO / "skills" / "tplan" / "scripts" / script_name), *args],
        text=True,
        capture_output=True,
    )


def context_path(project_root, mission_id):
    return (
        Path(project_root)
        / ".tplan"
        / "shared_contexts"
        / f"tplan_mission_shared_context-{mission_id}.md"
    )


def write_context(
    project_root,
    mission_id,
    objective="Keep the original mission.",
    acceptance=None,
    *,
    status="active",
    active_task_id="T1",
    runtime_dir_name=None,
    risk_signals=None,
):
    acceptance = acceptance or [{"id": "A1", "description": "Original acceptance."}]
    path = context_path(project_root, mission_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": "tplan.shared_context.v0.1",
        "mission_id": mission_id,
        "title": "Original Mission",
        "objective": objective,
        "status": status,
        "active_task_id": active_task_id,
        "acceptance_evidence": acceptance,
        "source_contexts": [],
        "runtime_dir_name": runtime_dir_name,
        "risk_signals": risk_signals or [],
    }
    path.write_text(
        "<!-- tplan-shared-context\n"
        + json.dumps(metadata, ensure_ascii=False, indent=2)
        + "\n-->\n"
        + f"# TPlan Mission Shared Context: {mission_id}\n\n"
        + "## Mission Snapshot\n\n"
        + f"- objective: {objective}\n",
        encoding="utf-8",
    )
    return path


def write_tasks(tmp):
    task_path = Path(tmp) / "tasks.json"
    task_path.write_text(
        json.dumps(
            [
                {
                    "id": "T1",
                    "title": "Keep context current",
                    "role": "success-critical",
                    "mission_contribution": "Keeps Mission memory available for resume.",
                    "acceptance_evidence": ["A1"],
                }
            ]
        ),
        encoding="utf-8",
    )
    return task_path


def read_mission(mission_dir):
    return json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))


class MissionSharedContextPreflightTests(unittest.TestCase):
    def test_preflight_reports_create_new_when_context_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-new",
                "--objective",
                "Create a new Mission.",
                "--acceptance-evidence",
                "A1:New acceptance.",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["action"], "create_new")
            self.assertEqual(payload["mission_id"], "m-new")
            self.assertEqual(payload["conflicts"], [])
            self.assertTrue(payload["context_file"].endswith("tplan_mission_shared_context-m-new.md"))

    def test_preflight_rejects_rationale_without_disposition(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-new",
                "--rationale",
                "A rationale cannot select an action by itself.",
                "--json",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("rationale requires --disposition", result.stderr)

    def test_preflight_reports_resume_candidate_without_authorizing_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_context(tmp, "m-existing")

            result = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-existing",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["action"], "needs_agentic_selection")
            self.assertEqual(payload["identity_action"], "continue_existing")
            self.assertEqual(payload["candidate_disposition"], "resume_existing")
            self.assertTrue(payload["decision_required"])
            self.assertEqual(payload["mission_id"], "m-existing")
            self.assertEqual(payload["conflicts"], [])
            self.assertEqual(payload["missing_current_intent"], [])
            self.assertTrue(payload["assessment_digest"].startswith("sha256:"))
            self.assertEqual(payload["loaded_context"]["mission_id"], "m-existing")

    def test_preflight_missing_current_intent_never_authorizes_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_context(tmp, "m-existing")

            result = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-existing",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["action"], "needs_agentic_selection")
            self.assertEqual(payload["identity_action"], "needs_agentic_selection")
            self.assertIsNone(payload["candidate_disposition"])
            self.assertEqual(
                payload["missing_current_intent"],
                ["objective", "acceptance_evidence"],
            )
            self.assertIn("current_intent_incomplete", payload["reason_codes"])
            self.assertIn("缺少当前目标", payload["user_message"])

    def test_explicit_resume_disposition_requires_matching_intent_and_rationale(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_context(tmp, "m-existing")

            accepted = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-existing",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--disposition",
                "resume_existing",
                "--rationale",
                "The current request explicitly continues the same unfinished objective.",
                "--json",
            )

            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            payload = json.loads(accepted.stdout)
            self.assertEqual(payload["action"], "resume_existing")
            self.assertFalse(payload["decision_required"])
            self.assertEqual(
                payload["reentry_decision"]["disposition"],
                "resume_existing",
            )
            self.assertEqual(
                payload["reentry_decision"]["acceptance_authority"],
                "preserved",
            )
            self.assertEqual(
                payload["decision_receipt"]["application"]["status"],
                "recorded_pending_runtime_initialization",
            )
            self.assertTrue(Path(payload["decision_receipt"]["path"]).exists())
            self.assertIn("已明确选择继续旧 Mission", payload["user_message"])

            missing_rationale = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-existing",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--disposition",
                "resume_existing",
                "--json",
            )
            self.assertNotEqual(missing_rationale.returncode, 0)
            self.assertIn("requires a non-empty rationale", missing_rationale.stderr)

    def test_failed_context_only_initialization_updates_existing_decision_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            write_context(project_root, "m-init-failure")
            payload = tplan_runtime.build_mission_preflight(
                project_root,
                mission_id="m-init-failure",
                objective="Keep the original mission.",
                acceptance_evidence=[
                    {"id": "A1", "description": "Original acceptance."}
                ],
                disposition="resume_existing",
                rationale="The current request explicitly continues this Mission.",
            )
            recorded = tplan_runtime.record_and_apply_mission_reentry_decision(
                project_root,
                payload,
            )

            tplan_runtime.finalize_mission_reentry_initialization(
                project_root,
                recorded,
                project_root / "runtime",
                error=OSError("simulated initializer failure"),
            )

            receipt_path = Path(recorded["decision_receipt"]["path"])
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(
                receipt["application"]["status"],
                "initialization_failed",
            )
            self.assertIn(
                "simulated initializer failure",
                receipt["application"]["error"],
            )

    def test_preflight_reports_conflict_for_same_id_different_objective(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_context(tmp, "m-conflict", objective="Keep the original mission.")

            result = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-conflict",
                "--objective",
                "Do a different Mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["action"], "needs_agentic_selection")
            self.assertIn("objective", payload["conflicts"])
            self.assertIn("存在冲突", payload["user_message"])

            rejected_resume = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-conflict",
                "--objective",
                "Do a different Mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--disposition",
                "resume_existing",
                "--rationale",
                "Try to resume despite the mismatch.",
                "--json",
            )
            self.assertNotEqual(rejected_resume.returncode, 0)
            self.assertIn("not eligible for resume_existing", rejected_resume.stderr)

    def test_terminal_mission_routes_to_new_context_and_cannot_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_context(tmp, "m-completed", status="completed", active_task_id=None)

            result = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-completed",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["action"], "needs_agentic_selection")
            self.assertEqual(
                payload["candidate_disposition"],
                "create_new_from_context",
            )
            self.assertIn("mission_status", payload["conflicts"])
            self.assertIn("mission_terminal", payload["reason_codes"])
            self.assertIn("默认不能续跑", payload["user_message"])

            rejected_resume = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-completed",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--disposition",
                "resume_existing",
                "--rationale",
                "Attempt to reopen a terminal Mission.",
                "--json",
            )
            self.assertNotEqual(rejected_resume.returncode, 0)
            self.assertIn("not eligible for resume_existing", rejected_resume.stderr)

            selected_new = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-completed",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--disposition",
                "create_new_from_context",
                "--rationale",
                "The prior Mission is terminal; retain it only as background.",
                "--json",
            )
            self.assertEqual(selected_new.returncode, 0, selected_new.stderr)
            selected_payload = json.loads(selected_new.stdout)
            self.assertEqual(selected_payload["action"], "create_new_from_context")
            self.assertEqual(
                selected_payload["reentry_decision"]["acceptance_authority"],
                "not_inherited",
            )
            self.assertEqual(
                selected_payload["decision_receipt"]["application"]["status"],
                "recorded_for_new_mission_context",
            )
            self.assertTrue(
                Path(selected_payload["decision_receipt"]["path"]).exists()
            )

    def test_requires_human_reentry_exposes_runtime_recovery_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = project_root / "m-requires-human"
            initialized = run_script(
                "init_lite.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-requires-human",
                "--title",
                "Requires Human Mission",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--active-task-id",
                "T1",
                "--active-task-title",
                "Wait for authority",
                "--active-task-contribution",
                "Preserves the authority boundary.",
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            stopped = run_script(
                "stop_report.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--summary",
                "Need explicit authority.",
                "--current-goal",
                "Keep the original mission.",
                "--attempt",
                "Inspected the available policy.",
                "--blocking-issue",
                "Required authority is absent.",
                "--why-cannot-continue-safely",
                "Continuing would invent authority.",
                "--need-from-human",
                "Confirm the authority boundary.",
                "--resume-condition",
                "A human confirms the authority boundary.",
            )
            self.assertEqual(stopped.returncode, 0, stopped.stderr)

            result = run_script(
                "preflight_mission.py",
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-requires-human",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["candidate_disposition"], "requires_human")
            self.assertIn("mission_requires_human", payload["reason_codes"])
            self.assertEqual(
                payload["reentry_packet"]["recovery_boundary"]["resume_condition"],
                "A human confirms the authority boundary.",
            )
            self.assertEqual(
                payload["reentry_packet"]["active_task"]["status"],
                "blocked",
            )
            self.assertEqual(
                payload["reentry_packet"]["blockers"][0]["event_type"],
                "stop_report",
            )
            self.assertIn("不能继续", payload["user_message"])
            self.assertIn("shared_context_stale", payload["warnings"])
            self.assertIn("shared_context_snapshot_stale", payload["reason_codes"])

    def test_runtime_provenance_conflict_blocks_resume_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = project_root / "m-provenance"
            initialized = run_script(
                "init_lite.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-provenance",
                "--title",
                "Provenance Mission",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--active-task-id",
                "T1",
                "--active-task-title",
                "Preserve provenance",
                "--active-task-contribution",
                "Prevents incompatible runtime continuation.",
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            mission_path = mission_dir / "mission.json"
            mission = json.loads(mission_path.read_text(encoding="utf-8"))
            mission["runtime_provenance"]["fingerprint"]["package_version"] = "incompatible-test"
            mission_path.write_text(
                json.dumps(mission, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = run_script(
                "preflight_mission.py",
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-provenance",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("runtime_provenance", payload["conflicts"])
            self.assertIsNone(payload["candidate_disposition"])
            self.assertEqual(
                payload["reentry_packet"]["runtime_snapshot"]["runtime_provenance"][
                    "compatible"
                ],
                False,
            )

    def test_stale_shared_context_never_silently_resumes_over_runtime_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = project_root / "m-stale"
            initialized = run_script(
                "init_lite.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-stale",
                "--title",
                "Stale Context Mission",
                "--objective",
                "Use runtime as the authoritative recovery state.",
                "--acceptance-evidence",
                "A1:Stale shared context cannot authorize continuation.",
                "--active-task-id",
                "T1",
                "--active-task-title",
                "Preserve runtime authority",
                "--active-task-contribution",
                "Keeps stale memory from controlling re-entry.",
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            shared_path = context_path(project_root, "m-stale")
            shared_text = shared_path.read_text(encoding="utf-8")
            shared_path.write_text(
                shared_text.replace(
                    '"objective": "Use runtime as the authoritative recovery state."',
                    '"objective": "Stale objective from old shared memory."',
                    1,
                ),
                encoding="utf-8",
            )

            result = run_script(
                "preflight_mission.py",
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-stale",
                "--objective",
                "Use runtime as the authoritative recovery state.",
                "--acceptance-evidence",
                "A1:Stale shared context cannot authorize continuation.",
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["action"], "needs_agentic_selection")
            self.assertTrue(payload["decision_required"])
            self.assertEqual(payload["candidate_disposition"], "resume_existing")
            self.assertIn("shared_context_stale", payload["warnings"])
            self.assertFalse(
                payload["reentry_packet"]["freshness_signals"][
                    "shared_context_matches_runtime"
                ]
            )
            self.assertIn("共享上下文快照已落后", payload["user_message"])

    def test_preflight_lists_candidates_without_mission_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_context(tmp, "m-one")
            write_context(tmp, "m-two")

            result = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["action"], "needs_agentic_selection")
            self.assertEqual([item["mission_id"] for item in payload["candidates"]], ["m-one", "m-two"])

    def test_preflight_discovers_and_assesses_runtime_only_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = project_root / "runtime-only"
            tasks = write_tasks(tmp)
            initialized = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--mission-id",
                "m-runtime-only",
                "--title",
                "Runtime-only Mission",
                "--objective",
                "Recover from runtime state without shared Markdown.",
                "--acceptance-evidence",
                "A1:Runtime-only recovery is explicit.",
                "--task-json",
                str(tasks),
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            mission_path = mission_dir / "mission.json"
            mission_before_assessment = mission_path.read_bytes()
            self.assertFalse((project_root / ".tplan").exists())

            discovered = run_script(
                "preflight_mission.py",
                "--project-root",
                str(project_root),
                "--json",
            )
            self.assertEqual(discovered.returncode, 0, discovered.stderr)
            candidates = json.loads(discovered.stdout)["candidates"]
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0]["mission_id"], "m-runtime-only")
            self.assertEqual(candidates[0]["sources"], ["runtime"])

            assessed = run_script(
                "preflight_mission.py",
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-runtime-only",
                "--objective",
                "Recover from runtime state without shared Markdown.",
                "--acceptance-evidence",
                "A1:Runtime-only recovery is explicit.",
                "--json",
            )
            self.assertEqual(assessed.returncode, 0, assessed.stderr)
            payload = json.loads(assessed.stdout)
            self.assertIsNone(payload["loaded_context"])
            self.assertEqual(payload["candidate_disposition"], "resume_existing")
            self.assertIn("runtime_only_candidate", payload["reason_codes"])
            self.assertEqual(
                payload["reentry_packet"]["runtime_snapshot"]["availability"],
                "loaded",
            )
            self.assertEqual(
                payload["reentry_packet"]["latest_state"]["event_type"],
                "mission_initialized",
            )
            self.assertIsInstance(
                payload["reentry_packet"]["freshness_signals"]["runtime_files"][
                    "mission_mtime_ns"
                ],
                int,
            )
            self.assertEqual(mission_path.read_bytes(), mission_before_assessment)
            self.assertFalse((project_root / ".tplan").exists())

            resumed = run_script(
                "preflight_mission.py",
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-runtime-only",
                "--objective",
                "Recover from runtime state without shared Markdown.",
                "--acceptance-evidence",
                "A1:Runtime-only recovery is explicit.",
                "--disposition",
                "resume_existing",
                "--rationale",
                "The current request explicitly resumes this unfinished Mission.",
                "--json",
            )
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            resumed_payload = json.loads(resumed.stdout)
            self.assertEqual(
                resumed_payload["decision_receipt"]["application"]["status"],
                "applied_to_runtime",
            )
            receipt_path = Path(resumed_payload["decision_receipt"]["path"])
            self.assertTrue(receipt_path.exists())
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(
                receipt["application"]["status"],
                "applied_to_runtime",
            )
            mission_after_resume = read_mission(mission_dir)
            self.assertEqual(
                mission_after_resume["shared_context"]["reentry_decision"][
                    "decision_digest"
                ],
                resumed_payload["reentry_decision"]["decision_digest"],
            )

    def test_plain_text_recovery_output_explains_undecided_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_context(tmp, "m-readable")
            result = run_script(
                "preflight_mission.py",
                "--project-root",
                tmp,
                "--mission-id",
                "m-readable",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("message:", result.stdout)
            self.assertIn("仍只是恢复候选", result.stdout)
            self.assertIn("必须明确选择 resume_existing", result.stdout)

    def test_failed_runtime_application_keeps_receipt_and_leaves_mission_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = project_root / "runtime-only"
            tasks = write_tasks(tmp)
            initialized = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--mission-id",
                "m-application-failure",
                "--title",
                "Application Failure Mission",
                "--objective",
                "Record authority before attempting runtime mutation.",
                "--acceptance-evidence",
                "A1:A failed application leaves an auditable receipt.",
                "--task-json",
                str(tasks),
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            mission_path = mission_dir / "mission.json"
            mission_before = mission_path.read_bytes()
            payload = tplan_runtime.build_mission_preflight(
                project_root,
                mission_id="m-application-failure",
                objective="Record authority before attempting runtime mutation.",
                acceptance_evidence=[
                    {
                        "id": "A1",
                        "description": "A failed application leaves an auditable receipt.",
                    }
                ],
                disposition="resume_existing",
                rationale="The same unfinished Mission was explicitly selected.",
            )

            with patch.object(
                tplan_runtime,
                "_commit_mission_state_unlocked",
                side_effect=tplan_runtime.TplanError("simulated application failure"),
            ):
                with self.assertRaisesRegex(
                    tplan_runtime.TplanError,
                    "simulated application failure",
                ):
                    tplan_runtime.record_and_apply_mission_reentry_decision(
                        project_root,
                        payload,
                    )

            receipt_path = tplan_runtime.mission_reentry_receipt_path(
                project_root,
                payload["reentry_decision"],
            )
            self.assertTrue(receipt_path.exists())
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(
                receipt["application"]["status"],
                "application_failed",
            )
            self.assertEqual(mission_path.read_bytes(), mission_before)

    def test_tampered_reentry_decision_is_rejected_before_receipt_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            write_context(project_root, "m-tampered-decision")
            payload = tplan_runtime.build_mission_preflight(
                project_root,
                mission_id="m-tampered-decision",
                objective="Keep the original mission.",
                acceptance_evidence=[
                    {"id": "A1", "description": "Original acceptance."}
                ],
                disposition="resume_existing",
                rationale="The same unfinished Mission was explicitly selected.",
            )
            payload["reentry_decision"]["rationale"] = "Tampered rationale."

            with self.assertRaisesRegex(
                tplan_runtime.TplanError,
                "decision digest does not match",
            ):
                tplan_runtime.record_and_apply_mission_reentry_decision(
                    project_root,
                    payload,
                )

            self.assertFalse(
                (project_root / ".tplan" / "reentry_decisions").exists()
            )

    def test_artifact_freshness_change_blocks_runtime_application(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = project_root / "runtime-only"
            tasks = write_tasks(tmp)
            initialized = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--mission-id",
                "m-freshness-race",
                "--title",
                "Freshness Race Mission",
                "--objective",
                "Resume only the exact assessed runtime boundary.",
                "--acceptance-evidence",
                "A1:Artifact drift blocks re-entry application.",
                "--task-json",
                str(tasks),
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            payload = tplan_runtime.build_mission_preflight(
                project_root,
                mission_id="m-freshness-race",
                objective="Resume only the exact assessed runtime boundary.",
                acceptance_evidence=[
                    {
                        "id": "A1",
                        "description": "Artifact drift blocks re-entry application.",
                    }
                ],
                disposition="resume_existing",
                rationale="The same unfinished Mission was explicitly selected.",
            )
            evidence_path = mission_dir / "evidence.jsonl"
            evidence_path.write_text("\n", encoding="utf-8")

            with self.assertRaisesRegex(
                tplan_runtime.TplanError,
                "artifacts changed after re-entry assessment",
            ):
                tplan_runtime.record_and_apply_mission_reentry_decision(
                    project_root,
                    payload,
                )

            receipt_path = tplan_runtime.mission_reentry_receipt_path(
                project_root,
                payload["reentry_decision"],
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(
                receipt["application"]["status"],
                "application_failed",
            )
            self.assertNotIn(
                "reentry_decision",
                read_mission(mission_dir).get("shared_context", {}),
            )


class MissionSharedContextInitTests(unittest.TestCase):
    def test_init_mission_creates_project_shared_context_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = Path(tmp) / "mission"
            tasks = write_tasks(tmp)

            result = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-shared",
                "--title",
                "Shared Context Mission",
                "--objective",
                "Create project shared context memory.",
                "--acceptance-evidence",
                "A1:Shared context file exists.",
                "--task-json",
                str(tasks),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            path = context_path(project_root, "m-shared")
            self.assertTrue(path.exists())
            text = path.read_text(encoding="utf-8")
            self.assertIn("TPlan Mission Shared Context: m-shared", text)
            self.assertIn("Create project shared context memory.", text)
            mission = read_mission(mission_dir)
            self.assertEqual(
                mission["shared_context"]["context_file"],
                ".tplan/shared_contexts/tplan_mission_shared_context-m-shared.md",
            )
            self.assertEqual(mission["shared_context"]["risk_signals"], [])

    def test_init_mission_requires_and_records_explicit_resume_for_matching_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = Path(tmp) / "mission"
            tasks = write_tasks(tmp)
            write_context(
                project_root,
                "m-existing",
                objective="Keep the original mission.",
                acceptance=[{"id": "A1", "description": "Original acceptance."}],
            )

            result = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-existing",
                "--title",
                "Existing Mission",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--task-json",
                str(tasks),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "requires explicit re-entry disposition and rationale",
                result.stderr,
            )
            self.assertFalse(mission_dir.exists())

            resumed = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-existing",
                "--title",
                "Existing Mission",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--task-json",
                str(tasks),
                "--reentry-disposition",
                "resume_existing",
                "--reentry-rationale",
                "The current request explicitly continues the same unfinished Mission.",
            )

            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            mission = read_mission(mission_dir)
            self.assertEqual(mission["mission"]["id"], "m-existing")
            self.assertEqual(mission["shared_context"]["context_file"], ".tplan/shared_contexts/tplan_mission_shared_context-m-existing.md")
            self.assertEqual(
                mission["shared_context"]["reentry_decision"]["disposition"],
                "resume_existing",
            )
            self.assertEqual(
                mission["shared_context"]["reentry_decision"]["acceptance_authority"],
                "preserved",
            )
            decision = mission["shared_context"]["reentry_decision"]
            receipt_path = tplan_runtime.mission_reentry_receipt_path(
                project_root,
                decision,
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(
                receipt["application"]["status"],
                "applied_to_initialized_runtime",
            )
            self.assertEqual(
                receipt["decision"]["decision_digest"],
                decision["decision_digest"],
            )

    def test_init_mission_restores_risk_signals_from_existing_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = Path(tmp) / "m-existing-run"
            tasks = write_tasks(tmp)
            write_context(
                project_root,
                "m-existing",
                objective="Keep the original mission.",
                acceptance=[{"id": "A1", "description": "Original acceptance."}],
                runtime_dir_name="m-existing-run",
                risk_signals=[
                    {
                        "id": "R1",
                        "source_task_id": "T1",
                        "source_evidence_id": "Edeadbeef",
                        "scope": "shared_environment",
                        "signal": "fsync_unreliable",
                        "severity": "high",
                        "confidence": "high",
                        "affected_surfaces": ["generation"],
                        "value_effect": "Expensive reruns may produce invalid evidence.",
                        "recommended_gate": "environment_health_gate",
                        "recovery_condition": "dd fsync and sqlite commit smoke pass",
                        "status": "active",
                        "created_at": "2026-06-10T00:00:00+00:00",
                        "updated_at": "2026-06-10T00:00:00+00:00",
                    }
                ],
            )

            result = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-existing",
                "--title",
                "Existing Mission",
                "--objective",
                "Keep the original mission.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--task-json",
                str(tasks),
                "--reentry-disposition",
                "resume_existing",
                "--reentry-rationale",
                "The current request explicitly resumes the same Mission and risk boundary.",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            mission = read_mission(mission_dir)
            self.assertEqual(mission["shared_context"]["risk_signals"][0]["id"], "R1")
            self.assertEqual(mission["shared_context"]["risk_signals"][0]["status"], "active")

    def test_init_mission_rejects_conflicting_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = Path(tmp) / "mission"
            tasks = write_tasks(tmp)
            write_context(project_root, "m-conflict", objective="Original objective.")

            result = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-conflict",
                "--title",
                "Conflict Mission",
                "--objective",
                "Different objective.",
                "--acceptance-evidence",
                "A1:Original acceptance.",
                "--task-json",
                str(tasks),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("shared context preflight conflict", result.stderr)
            self.assertFalse(mission_dir.exists())

    def test_init_mission_rejects_duplicate_mission_id_in_second_runtime_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            first_mission_dir = Path(tmp) / "m-dup-run-a"
            second_mission_dir = Path(tmp) / "m-dup-run-b"
            tasks = write_tasks(tmp)

            first = run_script(
                "init_mission.py",
                "--dir",
                str(first_mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-dup",
                "--title",
                "Duplicate Guard Mission",
                "--objective",
                "Keep one runtime per mission id.",
                "--acceptance-evidence",
                "A1:Only one runtime owns this mission id.",
                "--task-json",
                str(tasks),
            )
            self.assertEqual(first.returncode, 0, first.stderr)

            second = run_script(
                "init_mission.py",
                "--dir",
                str(second_mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-dup",
                "--title",
                "Duplicate Guard Mission",
                "--objective",
                "Keep one runtime per mission id.",
                "--acceptance-evidence",
                "A1:Only one runtime owns this mission id.",
                "--task-json",
                str(tasks),
            )

            self.assertNotEqual(second.returncode, 0)
            self.assertIn("shared context preflight conflict", second.stderr)
            self.assertFalse(second_mission_dir.exists())

    def test_init_mission_ignores_non_runtime_mission_json_when_checking_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            project_root.mkdir(parents=True, exist_ok=True)
            note_dir = project_root / "notes"
            note_dir.mkdir(parents=True, exist_ok=True)
            (note_dir / "mission.json").write_text(
                json.dumps(
                    {
                        "schema_version": "tplan.v0.1",
                        "mission": {"id": "m-dup"},
                    }
                ),
                encoding="utf-8",
            )
            mission_dir = Path(tmp) / "m-dup-run-a"
            tasks = write_tasks(tmp)

            result = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-dup",
                "--title",
                "Duplicate Guard Mission",
                "--objective",
                "Keep one runtime per mission id.",
                "--acceptance-evidence",
                "A1:Only one runtime owns this mission id.",
                "--task-json",
                str(tasks),
            )

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_init_lite_creates_project_shared_context_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = Path(tmp) / "mission"

            result = run_script(
                "init_lite.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--mission-id",
                "m-lite",
                "--title",
                "Lite Shared Context",
                "--objective",
                "Create lite shared context memory.",
                "--acceptance-evidence",
                "A1:Lite shared context exists.",
                "--active-task-id",
                "T1",
                "--active-task-title",
                "Create memory",
                "--active-task-contribution",
                "Keeps recovery memory available.",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            path = context_path(project_root, "m-lite")
            self.assertTrue(path.exists())
            mission = read_mission(mission_dir)
            self.assertEqual(mission["shared_context"]["context_file"], ".tplan/shared_contexts/tplan_mission_shared_context-m-lite.md")

    def test_init_mission_records_source_contexts_for_new_mission(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "project"
            mission_dir = Path(tmp) / "mission"
            tasks = write_tasks(tmp)

            result = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--project-root",
                str(project_root),
                "--source-context",
                "m-old",
                "--mission-id",
                "m-new",
                "--title",
                "New Mission",
                "--objective",
                "Use old memory as background only.",
                "--acceptance-evidence",
                "A1:New mission owns new acceptance.",
                "--task-json",
                str(tasks),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            mission = read_mission(mission_dir)
            self.assertEqual(mission["shared_context"]["source_contexts"], ["m-old"])
            text = context_path(project_root, "m-new").read_text(encoding="utf-8")
            self.assertIn("- m-old", text)


class MissionSharedContextRiskRefreshTests(unittest.TestCase):
    def init_project_mission(self, tmp, mission_id="m-risk-md"):
        project_root = Path(tmp) / "project"
        mission_dir = Path(tmp) / "mission"
        tasks = write_tasks(tmp)
        result = run_script(
            "init_mission.py",
            "--dir",
            str(mission_dir),
            "--project-root",
            str(project_root),
            "--mission-id",
            mission_id,
            "--title",
            "Risk Markdown Mission",
            "--objective",
            "Keep risk memory in Markdown.",
            "--acceptance-evidence",
            "A1:Risk memory is visible.",
            "--task-json",
            str(tasks),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return project_root, mission_dir

    def test_record_risk_context_refreshes_markdown_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root, mission_dir = self.init_project_mission(tmp)

            result = run_script(
                "record_risk_context.py",
                str(mission_dir),
                "record",
                "--task-id",
                "T1",
                "--scope",
                "shared_environment",
                "--signal",
                "fsync_unreliable",
                "--severity",
                "high",
                "--confidence",
                "high",
                "--affected-surface",
                "generation",
                "--value-effect",
                "Expensive reruns may produce invalid evidence.",
                "--recommended-gate",
                "environment_health_gate",
                "--recovery-condition",
                "dd fsync and sqlite commit smoke pass",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            text = context_path(project_root, "m-risk-md").read_text(encoding="utf-8")
            self.assertIn("R1: fsync_unreliable (high, active)", text)

    def test_resolve_risk_context_refreshes_markdown_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root, mission_dir = self.init_project_mission(tmp)
            record = run_script(
                "record_risk_context.py",
                str(mission_dir),
                "record",
                "--task-id",
                "T1",
                "--scope",
                "shared_environment",
                "--signal",
                "fsync_unreliable",
                "--severity",
                "high",
                "--confidence",
                "high",
                "--affected-surface",
                "generation",
                "--value-effect",
                "Expensive reruns may produce invalid evidence.",
                "--recommended-gate",
                "environment_health_gate",
                "--recovery-condition",
                "dd fsync and sqlite commit smoke pass",
            )
            self.assertEqual(record.returncode, 0, record.stderr)

            result = run_script(
                "record_risk_context.py",
                str(mission_dir),
                "resolve",
                "--task-id",
                "T1",
                "--risk-id",
                "R1",
                "--status",
                "resolved",
                "--summary",
                "Storage smoke passed.",
                "--recovery-note",
                "dd fsync and sqlite commit passed.",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            text = context_path(project_root, "m-risk-md").read_text(encoding="utf-8")
            self.assertIn("### Active\n\n- none", text)
            self.assertIn("R1: fsync_unreliable (resolved)", text)

    def test_record_risk_context_fails_loudly_when_indexed_shared_context_is_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root, mission_dir = self.init_project_mission(tmp)
            mission_path = mission_dir / "mission.json"
            mission = read_mission(mission_dir)
            del mission["shared_context"]["project_root"]
            mission_path.write_text(json.dumps(mission), encoding="utf-8")
            before_context = context_path(project_root, "m-risk-md").read_text(encoding="utf-8")

            result = run_script(
                "record_risk_context.py",
                str(mission_dir),
                "record",
                "--task-id",
                "T1",
                "--scope",
                "shared_environment",
                "--signal",
                "fsync_unreliable",
                "--severity",
                "high",
                "--confidence",
                "high",
                "--affected-surface",
                "generation",
                "--value-effect",
                "Expensive reruns may produce invalid evidence.",
                "--recommended-gate",
                "environment_health_gate",
                "--recovery-condition",
                "dd fsync and sqlite commit smoke pass",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("shared_context propagation configured without project_root", result.stderr)
            self.assertEqual((mission_dir / "evidence.jsonl").read_text(encoding="utf-8"), "")
            self.assertEqual(context_path(project_root, "m-risk-md").read_text(encoding="utf-8"), before_context)


if __name__ == "__main__":
    unittest.main()

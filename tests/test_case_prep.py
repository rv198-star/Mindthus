import importlib.util
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
import warnings
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CASE_PREP = REPO / "skills" / "case-prep"
SCRIPTS = CASE_PREP / "scripts"
sys.path.insert(0, str(SCRIPTS))

from case_prep_core import (  # noqa: E402
    CasePrepError,
    prepare_benchmark_case,
    prepare_judgment_case,
    prepare_tplan_case,
    validate_tplan_case_packet,
)

TRACE = REPO / "skills" / "_runtime" / "judgment" / "fixtures" / "traces" / "intervention.json"
SUMMARY = (
    REPO
    / "skills"
    / "_runtime"
    / "judgment"
    / "fixtures"
    / "case-summaries"
    / "judgment-failure.json"
)


def init_mission(root: Path) -> Path:
    mission = root / "mission-case-prep"
    result = subprocess.run(
        [
            "python3",
            str(REPO / "skills" / "tplan" / "scripts" / "init_lite.py"),
            "--dir",
            str(mission),
            "--mission-id",
            "case-prep-mission",
            "--title",
            "Case Prep Mission",
            "--objective",
            "Validate bounded TPlan case preparation.",
            "--acceptance-evidence",
            "A1:Packet validates",
            "--active-task-id",
            "T1",
            "--active-task-title",
            "Prepare bounded packet",
            "--active-task-contribution",
            "Produce a reviewable case without dumping runtime state.",
            "--latest-state",
            "Blocked by missing review authority.",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr + result.stdout)
    evidence = subprocess.run(
        [
            "python3",
            str(REPO / "skills" / "tplan" / "scripts" / "record_evidence.py"),
            str(mission),
            "--event-type",
            "blocked",
            "--summary",
            "Review authority is missing.",
            "--task-id",
            "T1",
            "--payload-json",
            '{"private_detail":"must-not-be-exported","token":"secret-runtime-payload"}',
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
    )
    if evidence.returncode != 0:
        raise AssertionError(evidence.stderr + evidence.stdout)
    return mission


class CasePrepTests(unittest.TestCase):
    def test_skill_is_explicit_only_and_preserves_contract_separation(self):
        skill = (CASE_PREP / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Use only when the user explicitly asks",
            "Explicit invocation only",
            "Judgment Trace v1.1",
            "tplan.case-packet.v1",
            "No automatic upload",
            "at most one question",
        ):
            self.assertIn(phrase, skill)
        self.assertNotIn("automatically upload", skill.lower())
        router = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("case-prep", router)
        for resource in (
            "judgment-mode.md",
            "benchmark-mode.md",
            "tplan-mode.md",
            "privacy-boundary.md",
            "output-contract.md",
            "tplan-case-packet.schema.json",
        ):
            self.assertTrue((CASE_PREP / "resources" / resource).is_file(), resource)

    def test_archive_name_preserves_dotted_case_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = prepare_judgment_case(
                trace_path=TRACE,
                summary_path=SUMMARY,
                case_type="judgment_failure",
                output_root=Path(tmp),
                case_id="case.prep.v1",
            )
        self.assertTrue(result["archive_path"].endswith("mindthus-case-case.prep.v1.tar.gz"))

    def test_judgment_mode_creates_review_required_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = prepare_judgment_case(
                trace_path=TRACE,
                summary_path=SUMMARY,
                case_type="judgment_failure",
                output_root=Path(tmp),
                case_id="case-prep-judgment",
            )
            package = Path(result["package_dir"])
            archive = Path(result["archive_path"])
            self.assertTrue(package.is_dir())
            self.assertTrue(archive.is_file())
            self.assertTrue(result["review_required_before_share"])
            self.assertFalse(result["automatic_upload"])
            with tarfile.open(archive, "r:gz") as handle:
                names = handle.getnames()
            self.assertTrue(names)
            self.assertTrue(all(name == package.name or name.startswith(package.name + "/") for name in names))

    def test_benchmark_mode_reconstructs_trace_without_copying_raw_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "run"
            run.mkdir()
            response = {
                "case_id": "mtj-case-prep",
                "case_type": "positive",
                "variant": "fixture",
                "generated_at_utc": "2026-08-06T00:00:00+00:00",
                "final_answer": "PRIVATE FULL ANSWER MUST NOT BE COPIED",
            }
            score = {
                "case_id": "mtj-case-prep",
                "case_type": "positive",
                "variant": "fixture",
                "score": 0,
                "expected_owner": "whole_elephant",
                "loaded_owner": [],
                "required_visible_action_present": False,
                "owner_fidelity_verdict": "no_load",
                "rationale": "The required whole-object correction was absent.",
                "judged_at_utc": "2026-08-06T00:01:00+00:00",
            }
            (run / "raw-responses.jsonl").write_text(json.dumps(response) + "\n", encoding="utf-8")
            (run / "score-records.jsonl").write_text(json.dumps(score) + "\n", encoding="utf-8")

            result = prepare_benchmark_case(
                run_dir=run,
                benchmark_case_id="mtj-case-prep",
                output_root=root / "out",
                case_id="benchmark-case-prep",
            )
            package = Path(result["package_dir"])
            combined = "\n".join(
                path.read_text(encoding="utf-8")
                for path in package.rglob("*")
                if path.is_file() and path.suffix in {".json", ".md", ".txt"}
            )
            trace = json.loads((package / "judgment-trace.json").read_text(encoding="utf-8"))

        self.assertEqual(result["mode"], "benchmark")
        self.assertEqual(result["case_type"], "judgment_failure")
        self.assertEqual(trace["schema_version"], "mindthus.judgment-trace.v1.1")
        self.assertNotIn("PRIVATE FULL ANSWER MUST NOT BE COPIED", combined)

    @unittest.skipUnless(importlib.util.find_spec("jsonschema") is not None, "jsonschema is required")
    def test_tplan_manifest_matches_published_json_schema(self):
        import jsonschema

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission = init_mission(root)
            result = prepare_tplan_case(
                mission_dir=mission,
                output_root=root / "out",
                case_id="tplan-schema",
            )
            package = Path(result["package_dir"])
            manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
            schema = json.loads(
                (CASE_PREP / "resources" / "tplan-case-packet.schema.json").read_text(encoding="utf-8")
            )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                jsonschema.validate(manifest, schema)

    def test_tplan_mode_exports_bounded_summary_and_excludes_private_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission = init_mission(root)
            result = prepare_tplan_case(
                mission_dir=mission,
                output_root=root / "out",
                case_id="tplan-case-prep",
            )
            package = Path(result["package_dir"])
            findings = validate_tplan_case_packet(package)
            selected = json.loads((package / "selected-evidence.json").read_text(encoding="utf-8"))
            combined = "\n".join(
                path.read_text(encoding="utf-8")
                for path in package.rglob("*")
                if path.is_file() and path.suffix in {".json", ".md", ".txt"}
            )

        self.assertEqual(result["focus"], "blocker")
        self.assertFalse([item for item in findings if item.severity == "block"])
        self.assertLessEqual(len(selected), 5)
        self.assertTrue(all(set(item) <= {"id", "timestamp", "event_type", "task_id", "summary"} for item in selected))
        self.assertNotIn("must-not-be-exported", combined)
        self.assertNotIn("secret-runtime-payload", combined)
        for forbidden in ("mission.json", "evidence.jsonl", "execution_trace.jsonl"):
            self.assertFalse((package / forbidden).exists())

    def test_tplan_mode_can_link_judgment_trace_without_merging_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission = init_mission(root)
            result = prepare_tplan_case(
                mission_dir=mission,
                output_root=root / "out",
                focus="authority",
                case_id="tplan-linked-trace",
                judgment_trace_path=TRACE,
            )
            package = Path(result["package_dir"])
            manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
            trace = json.loads((package / "judgment-trace.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["links"]["judgment_trace"], "judgment-trace.json")
        self.assertEqual(trace["schema_version"], "mindthus.judgment-trace.v1.1")
        self.assertNotIn("mission", trace)

    def test_tplan_output_cannot_be_written_inside_mission_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission = init_mission(root)
            with self.assertRaises(CasePrepError) as caught:
                prepare_tplan_case(
                    mission_dir=mission,
                    output_root=mission / "case-exports",
                    case_id="inside-mission",
                )
        self.assertIn("outside the Mission directory", str(caught.exception))

    def test_tplan_excerpt_requires_confirmation_and_blocks_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission = init_mission(root)
            excerpt = root / "excerpt.txt"
            excerpt.write_text("small redacted observation", encoding="utf-8")
            with self.assertRaises(CasePrepError):
                prepare_tplan_case(
                    mission_dir=mission,
                    output_root=root / "out1",
                    case_id="tplan-unconfirmed-excerpt",
                    excerpts=[("observation", excerpt)],
                )
            excerpt.write_text("Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456", encoding="utf-8")
            with self.assertRaises(CasePrepError):
                prepare_tplan_case(
                    mission_dir=mission,
                    output_root=root / "out2",
                    case_id="tplan-secret-excerpt",
                    excerpts=[("observation", excerpt)],
                    excerpts_confirmed_redacted=True,
                )

    def test_tplan_validator_blocks_renamed_full_runtime_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission = init_mission(root)
            excerpt = root / "renamed-runtime.txt"
            excerpt.write_text((mission / "mission.json").read_text(encoding="utf-8"), encoding="utf-8")
            with self.assertRaises(CasePrepError) as caught:
                prepare_tplan_case(
                    mission_dir=mission,
                    output_root=root / "out",
                    case_id="tplan-full-runtime-excerpt",
                    excerpts=[("observation", excerpt)],
                    excerpts_confirmed_redacted=True,
                )
        self.assertTrue(any(item.code == "full-mission-shape" for item in caught.exception.findings))

    def test_tplan_validator_returns_finding_for_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission = init_mission(root)
            result = prepare_tplan_case(
                mission_dir=mission,
                output_root=root / "out",
                case_id="tplan-malformed-json",
            )
            package = Path(result["package_dir"])
            (package / "selected-evidence.json").write_text("{broken", encoding="utf-8")
            findings = validate_tplan_case_packet(package)
        self.assertTrue(any(item.code == "invalid-json" for item in findings))

    def test_tplan_default_ids_are_collision_resistant(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission = init_mission(root)
            first = prepare_tplan_case(mission_dir=mission, output_root=root / "out")
            second = prepare_tplan_case(mission_dir=mission, output_root=root / "out")
        self.assertNotEqual(first["package_dir"], second["package_dir"])
        self.assertNotEqual(first["archive_path"], second["archive_path"])

    def test_tplan_validator_blocks_raw_runtime_and_tampered_upload_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission = init_mission(root)
            result = prepare_tplan_case(
                mission_dir=mission,
                output_root=root / "out",
                case_id="tplan-tamper",
            )
            package = Path(result["package_dir"])
            (package / "mission.json").write_text("{}\n", encoding="utf-8")
            manifest_path = package / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["consent"]["automatic_upload"] = True
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            findings = validate_tplan_case_packet(package)

        codes = {item.code for item in findings}
        self.assertIn("raw-runtime-forbidden", codes)
        self.assertIn("automatic-upload-forbidden", codes)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"

import sys

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import interaction_host_certification
import tplan_runtime


def create_mission(tmp):
    mission_dir = Path(tmp) / "mission"
    mission = tplan_runtime.build_mission(
        mission_id="host-certification",
        title="Host Certification",
        objective="Keep interaction-host claims tied to auditable evidence.",
        acceptance_evidence=[{"id": "A1", "description": "Certification artifact validates."}],
        human_in_loop=0,
        risk_tolerance=50,
        resource_sufficiency=50,
        tasks=[{"id": "T1", "title": "Certify", "role": "success-critical", "mission_contribution": "Records host evidence.", "acceptance_evidence": ["A1"]}],
    )
    mission_dir.mkdir()
    tplan_runtime.write_mission(mission_dir, mission)
    tplan_runtime.initialize_execution_trace(mission_dir, mission)
    tplan_runtime.transition_task_status(mission_dir, "T1", "active")
    return mission_dir


def artifact(*, status="partial", level="checkpoint_detection", protected=False):
    checks = {field: False for field in interaction_host_certification.CHECK_FIELDS}
    checks.update({"message_arrival": True, "native_tool_gate": True, "direct_release": True, "no_continuation": True})
    return {
        "schema_version": interaction_host_certification.SCHEMA_VERSION,
        "status": status,
        "platform": "codex-desktop",
        "profile_id": "codex-desktop@v0.2-unverified",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "host": {"product": "Codex Desktop", "version": "observed-build", "os": "macOS"},
        "hook_sources": [{"source": ".codex/hooks.json", "source_hash": "sha256:test", "trusted": True, "enabled": True}],
        "state_directory": {"agent_write_protected": protected, "evidence": "temporary test state is not ACL protected"},
        "authority_boundary": {
            "event_origin": "none",
            "state_writer": "same_principal",
            "receipt_signer": "none",
            "evidence": "no trusted host boundary is available in this fixture",
        },
        "checks": checks,
        "capability": {"enforcement_level": level, "scope": "tplan_runtime_writers and subsequent native tool calls"},
        "limitations": ["Safe stop and recovery remain untested."],
    }


class InteractionHostCertificationTests(unittest.TestCase):
    def test_partial_artifact_records_but_mutation_prevention_claim_requires_complete_host_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            target = interaction_host_certification.record_certification(mission_dir, artifact())
            self.assertTrue(target.exists())
            self.assertEqual(tplan_runtime.read_json(target)["status"], "partial")
            incomplete_claim = artifact(status="certified", level="mutation_prevention")
            incomplete_claim["profile_id"] = "codex-desktop@v0.2-certified"
            with self.assertRaisesRegex(tplan_runtime.TplanError, "lacks required"):
                interaction_host_certification.validate_certification(incomplete_claim)

    def test_guard_blocks_certification_write_and_schema_rejects_thin_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            with self.assertRaisesRegex(tplan_runtime.TplanError, "schema"):
                interaction_host_certification.validate_certification({})
            tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M1")
            with self.assertRaisesRegex(tplan_runtime.TplanError, "guard is open"):
                interaction_host_certification.record_certification(mission_dir, artifact())

    def test_unverified_profile_cannot_claim_mutation_prevention_even_with_legacy_fields_filled(self):
        claimed = artifact(status="certified", level="mutation_prevention", protected=True)
        claimed["checks"] = {field: True for field in interaction_host_certification.CHECK_FIELDS}
        claimed["limitations"] = []
        with self.assertRaisesRegex(tplan_runtime.TplanError, "unverified interaction-host profile"):
            interaction_host_certification.validate_certification(claimed)

    def test_certified_claim_requires_unforgeable_host_authority_boundary(self):
        claimed = artifact(status="certified", level="mutation_prevention", protected=True)
        claimed["profile_id"] = "codex-desktop@v0.2-certified"
        claimed["checks"] = {field: True for field in interaction_host_certification.CHECK_FIELDS}
        claimed["limitations"] = []
        with self.assertRaisesRegex(tplan_runtime.TplanError, "unforgeable host authority boundary"):
            interaction_host_certification.validate_certification(claimed)
        claimed["authority_boundary"] = {
            "event_origin": "host_managed_unforgeable",
            "state_writer": "host_only",
            "receipt_signer": "host_only",
            "evidence": "independent trusted-host integration evidence",
        }
        interaction_host_certification.validate_certification(claimed)

    def test_legacy_partial_artifact_remains_readable_but_cannot_upgrade_claim(self):
        legacy = artifact()
        legacy["schema_version"] = interaction_host_certification.LEGACY_SCHEMA_VERSION
        del legacy["authority_boundary"]
        interaction_host_certification.validate_certification(legacy)
        legacy["status"] = "certified"
        legacy["capability"]["enforcement_level"] = "mutation_prevention"
        legacy["profile_id"] = "codex-desktop@v0.2-certified"
        legacy["checks"] = {field: True for field in interaction_host_certification.CHECK_FIELDS}
        legacy["state_directory"]["agent_write_protected"] = True
        legacy["limitations"] = []
        with self.assertRaisesRegex(tplan_runtime.TplanError, "legacy certification artifacts"):
            interaction_host_certification.validate_certification(legacy)

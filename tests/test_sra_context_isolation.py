import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SRA = REPO / "skills" / "sra"
SCRIPTS = SRA / "scripts"
PREPARE = SCRIPTS / "prepare_sra_run.py"
RECORD = SCRIPTS / "record_sra_judgment.py"
CHECK = SCRIPTS / "check_sra_run.py"
RENDER = SCRIPTS / "render_sra_decision.py"
INPUT_TEMPLATE = SRA / "templates" / "context-input.json"
CONTEXT_RESOURCE = SRA / "resources" / "context-isolation.md"
DESIGN = REPO / "docs" / "superpowers" / "specs" / "2026-09-03-sra-context-isolated-runtime-design.md"


def run_script(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(script), *args],
        cwd=REPO,
        text=True,
        capture_output=True,
    )


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def prepare_run(root: Path, data: dict | None = None, name: str = "run") -> Path:
    payload = data or json.loads(INPUT_TEMPLATE.read_text(encoding="utf-8"))
    input_path = root / f"{name}-input.json"
    run_dir = root / name
    write_json(input_path, payload)
    result = run_script(
        PREPARE,
        "--input",
        str(input_path),
        "--dir",
        str(run_dir),
        "--json",
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr + result.stdout)
    return run_dir


def build_blind_judgment(run_dir: Path) -> dict:
    packet = json.loads((run_dir / "blind-packet.json").read_text(encoding="utf-8"))
    assessments = []
    floor = []
    next_id = None
    for candidate in packet["candidates"]:
        role_text = candidate["dependency_or_bundle_role"].lower()
        if "threshold-essential" in role_text:
            role = "threshold_essential"
            contraction = "retained"
            first_break = "Removing this candidate breaks the admitted target threshold."
            floor.append(candidate["blind_id"])
            next_id = candidate["blind_id"]
        elif "option" in role_text or "maintenance" in role_text:
            role = "maintenance_or_option"
            contraction = "capped"
            first_break = "This candidate is capped at a bounded option level."
        else:
            role = "value_expanding"
            contraction = "removed"
            first_break = "Removing this candidate does not break the admitted target threshold."
        assessments.append(
            {
                "blind_id": candidate["blind_id"],
                "feasibility": "feasible",
                "candidate_role": role,
                "contraction_result": contraction,
                "first_break_point": first_break,
                "evidence_refs": candidate.get("evidence_refs", []),
                "assumption_refs": candidate.get("assumption_refs", []),
            }
        )
    if not floor:
        floor = [packet["candidates"][0]["blind_id"]]
        next_id = floor[0]
    return {
        "schema_version": "sra.blind-judgment.v0.1",
        "stage": "blind",
        "packet_hash": packet["packet_hash"],
        "mode": packet["mode"],
        "candidate_assessments": assessments,
        "current_floor": floor,
        "provisional_next_tranche": {
            "blind_id": next_id,
            "description": "Allocate one bounded decision-relevant tranche.",
            "reason": "The selected blind candidate remains in the current floor after contraction.",
        },
        "missing_information": [],
        "claim_ceiling": "Blind packet evidence supports a provisional allocation only.",
    }


def record_blind(
    run_dir: Path, carrier: str = "packet_bound", *, with_receipt: bool = False
) -> dict:
    judgment = build_blind_judgment(run_dir)
    path = run_dir.parent / f"{run_dir.name}-blind.json"
    write_json(path, judgment)
    args = [
        "--dir",
        str(run_dir),
        "--stage",
        "blind",
        "--input",
        str(path),
        "--carrier",
        carrier,
        "--json",
    ]
    if with_receipt:
        receipt = run_dir.parent / f"{run_dir.name}-blind-receipt.json"
        write_json(receipt, {"carrier": carrier, "stage": "blind", "completed": True})
        args.extend(["--receipt", str(receipt)])
    result = run_script(RECORD, *args)
    if result.returncode != 0:
        raise AssertionError(result.stderr + result.stdout)
    return judgment


def build_state_judgment(run_dir: Path) -> dict:
    packet = json.loads((run_dir / "state-packet.json").read_text(encoding="utf-8"))
    blind_floor = packet["blind_judgment"]["current_floor"]
    mapping = {item["blind_id"]: item["candidate_id"] for item in packet["candidate_mapping"]}
    selected = mapping[blind_floor[0]]
    current = packet.get("active_candidate_id")
    evidence_ids = [item["evidence_id"] for item in packet.get("evidence", [])]
    assumption_ids = [item["assumption_id"] for item in packet.get("assumptions", [])]
    state_by_kind = {}
    for item in packet.get("state_items", []):
        state_by_kind.setdefault(item["kind"], []).append(item["state_id"])
    switching_ref = state_by_kind.get("switching_cost", state_by_kind.get("active_candidate", []))[0]
    sunk_ref = state_by_kind.get("sunk_cost", [switching_ref])[0]
    return {
        "schema_version": "sra.state-judgment.v0.1",
        "stage": "state_aware",
        "packet_hash": packet["packet_hash"],
        "blind_judgment_hash": packet["blind_judgment_hash"],
        "decision": "continue" if selected == current else "switch",
        "blind_result_changed": False,
        "change_reason": "Admitted state information does not overturn the locked blind result.",
        "sunk_cost_used_as_reason": False,
        "state_adjustments": [
            {
                "kind": "switching_cost",
                "finding": "The recorded switching cost is bounded.",
                "state_refs": [switching_ref],
                "evidence_refs": [],
                "assumption_refs": [],
            },
            {
                "kind": "sunk_cost_rejected",
                "finding": "Historical spend is not used as a continuation reason.",
                "state_refs": [sunk_ref],
                "evidence_refs": [],
                "assumption_refs": [],
            },
        ],
        "current_floor": [selected],
        "next_tranche": {
            "candidate_id": selected,
            "description": "Allocate one bounded engineer-day to the selected candidate.",
            "reason": "The blind floor remains valid after state reconciliation.",
        },
        "investment_ceiling": "One engineer-day before reranking.",
        "authorization_horizon": "one_tranche",
        "maintenance": ["Keep displaced work at its minimum safe line."],
        "reserve": {
            "status": "none",
            "reason": "No admitted state fact requires a reserved tranche.",
            "release_trigger": "Not applicable while reserve is none.",
            "review_time": "At the next tranche checkpoint.",
        },
        "defer": ["Defer non-selected value-expanding work."],
        "stop": [],
        "rerank_triggers": ["The selected tranche completes or produces a new blocker."],
        "state_refs": [switching_ref, sunk_ref],
        "evidence_refs": evidence_ids,
        "assumption_refs": assumption_ids,
        "claim_ceiling": "The decision applies to the current allocation window only.",
    }


def record_state(
    run_dir: Path, carrier: str = "packet_bound", *, with_receipt: bool = False
) -> dict:
    judgment = build_state_judgment(run_dir)
    path = run_dir.parent / f"{run_dir.name}-state.json"
    write_json(path, judgment)
    args = [
        "--dir",
        str(run_dir),
        "--stage",
        "state-aware",
        "--input",
        str(path),
        "--carrier",
        carrier,
        "--json",
    ]
    if with_receipt:
        receipt = run_dir.parent / f"{run_dir.name}-state-receipt.json"
        write_json(
            receipt, {"carrier": carrier, "stage": "state_aware", "completed": True}
        )
        args.extend(["--receipt", str(receipt)])
    result = run_script(RECORD, *args)
    if result.returncode != 0:
        raise AssertionError(result.stderr + result.stdout)
    return judgment


class SraContextIsolationTests(unittest.TestCase):
    def test_phase_1_5_runtime_surface_exists(self):
        for path in (
            CONTEXT_RESOURCE,
            SRA / "templates" / "context-input.json",
            SRA / "templates" / "blind-judgment.json",
            SRA / "templates" / "state-aware-judgment.json",
            SCRIPTS / "sra_runtime.py",
            PREPARE,
            RECORD,
            CHECK,
            RENDER,
            DESIGN,
        ):
            self.assertTrue(path.is_file(), path)

    def test_current_instruction_and_constraints_cannot_be_silently_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = json.loads(INPUT_TEMPLATE.read_text(encoding="utf-8"))
            missing["context_items"] = [
                item
                for item in missing["context_items"]
                if item["kind"] != "current_instruction"
            ]
            missing_path = root / "missing-current.json"
            write_json(missing_path, missing)
            missing_result = run_script(
                PREPARE,
                "--input",
                str(missing_path),
                "--dir",
                str(root / "missing-run"),
            )
            self.assertNotEqual(missing_result.returncode, 0)
            self.assertIn("at least one current_instruction", missing_result.stderr)

            excluded = json.loads(INPUT_TEMPLATE.read_text(encoding="utf-8"))
            constraint = next(
                item for item in excluded["context_items"] if item["kind"] == "user_constraint"
            )
            constraint["requested_disposition"] = "exclude"
            excluded_path = root / "excluded-constraint.json"
            write_json(excluded_path, excluded)
            excluded_result = run_script(
                PREPARE,
                "--input",
                str(excluded_path),
                "--dir",
                str(root / "excluded-run"),
            )
            self.assertNotEqual(excluded_result.returncode, 0)
            self.assertIn("cannot exclude current instruction", excluded_result.stderr)

    def test_prepare_quarantines_prior_conclusions_and_advocacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            admission = json.loads(
                (run_dir / "context-admission.json").read_text(encoding="utf-8")
            )
            by_id = {item["context_id"]: item for item in admission["items"]}
            self.assertEqual(by_id["C-current"]["admission"], "admitted")
            self.assertEqual(by_id["C-quality"]["admitted_as"], "decision_constraint")
            self.assertEqual(by_id["C-history"]["admitted_as"], "scoped_history")
            self.assertEqual(by_id["C-prior"]["admission"], "quarantined")
            self.assertEqual(by_id["C-advocacy"]["admission"], "quarantined")
            self.assertNotEqual(by_id["C-quality"]["admitted_as"], "evidence_claim")

    def test_historical_context_requires_explicit_scoped_admission(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = json.loads(INPUT_TEMPLATE.read_text(encoding="utf-8"))
            history = next(
                item for item in data["context_items"] if item["context_id"] == "C-history"
            )
            history.pop("requested_disposition", None)
            run_dir = prepare_run(Path(tmp), data)
            admission = json.loads(
                (run_dir / "context-admission.json").read_text(encoding="utf-8")
            )
            by_id = {item["context_id"]: item for item in admission["items"]}
            self.assertEqual(by_id["C-history"]["admission"], "quarantined")
            self.assertEqual(
                by_id["C-history"]["admitted_as"],
                "history_requires_explicit_admission",
            )

    def test_blind_packet_hides_current_identity_and_state_only_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            blind_text = (run_dir / "blind-packet.json").read_text(encoding="utf-8")
            for forbidden in (
                '"active_candidate_id"',
                '"page-polish"',
                '"payment-validation"',
                '"incident-reserve"',
                "Continue animation polish",
                '"switching_costs"',
                '"reusable_assets"',
                '"remaining_costs"',
                '"historical_spend"',
                '"commitments"',
                "Several engineer-days have already been spent on page polish.",
                "requires payment acceptance before launch in the current release window",
                "Switching from page polish to payment validation requires only a short context handoff.",
                "previous agent recommended",
            ):
                self.assertNotIn(forbidden, blind_text)
            packet = json.loads(blind_text)
            self.assertEqual([item["blind_id"] for item in packet["candidates"]], ["B01", "B02", "B03"])
            self.assertTrue(packet["blind_boundary"]["external_context_forbidden"])

    def test_unused_evidence_is_not_exposed_to_blind_or_state_judges(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = json.loads(INPUT_TEMPLATE.read_text(encoding="utf-8"))
            data["evidence"].append(
                {
                    "evidence_id": "E-unrelated",
                    "kind": "unrelated_history",
                    "source": "another project",
                    "statement": "An unrelated project strongly preferred the active path.",
                    "observed_at": "2026-08-01T00:00:00Z",
                    "claim_ceiling": "Not relevant to this allocation.",
                }
            )
            run_dir = prepare_run(root, data)
            blind_text = (run_dir / "blind-packet.json").read_text(encoding="utf-8")
            self.assertNotIn("E-unrelated", blind_text)
            self.assertNotIn("unrelated project", blind_text)
            record_blind(run_dir)
            state_text = (run_dir / "state-packet.json").read_text(encoding="utf-8")
            self.assertNotIn("E-unrelated", state_text)
            self.assertNotIn("unrelated project", state_text)
            sealed_text = (run_dir / "sealed-packet.json").read_text(encoding="utf-8")
            self.assertIn("E-unrelated", sealed_text)

    def test_blind_candidate_order_is_input_order_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = json.loads(INPUT_TEMPLATE.read_text(encoding="utf-8"))
            first = prepare_run(root, copy.deepcopy(data), "first")
            reversed_data = copy.deepcopy(data)
            reversed_data["candidates"].reverse()
            second = prepare_run(root, reversed_data, "second")
            first_packet = json.loads((first / "blind-packet.json").read_text(encoding="utf-8"))
            second_packet = json.loads((second / "blind-packet.json").read_text(encoding="utf-8"))
            self.assertEqual(first_packet["candidates"], second_packet["candidates"])
            first_state = json.loads((first / "run.json").read_text(encoding="utf-8"))
            second_state = json.loads((second / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(first_state["candidate_map"], second_state["candidate_map"])

    def test_packet_bound_override_under_contamination_requires_a_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blocked = json.loads(INPUT_TEMPLATE.read_text(encoding="utf-8"))
            blocked["isolation_profile"] = "packet_bound"
            blocked_path = root / "blocked-packet-bound.json"
            write_json(blocked_path, blocked)
            blocked_result = run_script(
                PREPARE,
                "--input",
                str(blocked_path),
                "--dir",
                str(root / "blocked-run"),
            )
            self.assertNotEqual(blocked_result.returncode, 0)
            self.assertIn("requires isolation_override_reason", blocked_result.stderr)

            allowed = json.loads(INPUT_TEMPLATE.read_text(encoding="utf-8"))
            allowed["isolation_profile"] = "packet_bound"
            allowed["isolation_override_reason"] = (
                "The host has no fresh-context carrier; this reversible Lite tranche accepts logical isolation."
            )
            run_dir = prepare_run(root, allowed, "allowed")
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(state["isolation_profile"], "packet_bound")
            self.assertEqual(
                state["isolation_override_reason"],
                allowed["isolation_override_reason"],
            )
            check = run_script(CHECK, "--dir", str(run_dir), "--json")
            report = json.loads(check.stdout)
            self.assertEqual(report["status"], "warning")
            self.assertTrue(
                any(
                    item["code"] == "degraded-isolation-override"
                    for item in report["findings"]
                )
            )

    def test_auto_mode_and_isolation_are_declared_not_semantically_proven(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lite = prepare_run(root, name="lite")
            lite_state = json.loads((lite / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(lite_state["mode"], "lite")
            self.assertEqual(lite_state["isolation_profile"], "fresh_context")

            full_data = json.loads(INPUT_TEMPLATE.read_text(encoding="utf-8"))
            full_data["escalation_signals"] = ["multiple_feasible_bundles"]
            full = prepare_run(root, full_data, "full")
            full_state = json.loads((full / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(full_state["mode"], "full")
            self.assertEqual(full_state["isolation_profile"], "blind_then_state")
            self.assertIn("does not prove", full_state["claim_ceiling"])

    def test_generated_fresh_context_carriers_are_read_only_and_no_fork(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            dispatch = json.loads(
                (run_dir / "blind-subagent-dispatch.json").read_text(encoding="utf-8")
            )
            self.assertFalse(dispatch["fork_context"])
            self.assertTrue(dispatch["read_only"])
            self.assertEqual(dispatch["tool_policy"], "no_tools")
            self.assertTrue(Path(dispatch["output_schema_file"]).is_file())
            self.assertIn("Mission state", dispatch["must_not_mutate"])
            command = (run_dir / "blind-codex-command.sh").read_text(encoding="utf-8")
            for phrase in (
                "--ephemeral",
                "--ignore-rules",
                "--ignore-user-config",
                "--skip-git-repo-check",
                "-s read-only",
                "--output-schema",
                "blind-output-schema.json",
                "fresh-context-workspace",
            ):
                self.assertIn(phrase, command)

    def test_dynamic_output_schemas_bind_packet_and_reference_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            blind_packet = json.loads(
                (run_dir / "blind-packet.json").read_text(encoding="utf-8")
            )
            blind_schema = json.loads(
                (run_dir / "blind-output-schema.json").read_text(encoding="utf-8")
            )
            properties = blind_schema["properties"]
            self.assertEqual(properties["packet_hash"]["const"], blind_packet["packet_hash"])
            blind_ids = [item["blind_id"] for item in blind_packet["candidates"]]
            self.assertEqual(
                properties["candidate_assessments"]["items"]["properties"]["blind_id"]["enum"],
                blind_ids,
            )

            record_blind(run_dir)
            state_packet = json.loads(
                (run_dir / "state-packet.json").read_text(encoding="utf-8")
            )
            state_schema = json.loads(
                (run_dir / "state-aware-output-schema.json").read_text(encoding="utf-8")
            )
            state_properties = state_schema["properties"]
            self.assertEqual(state_properties["packet_hash"]["const"], state_packet["packet_hash"])
            self.assertEqual(
                state_properties["blind_judgment_hash"]["const"],
                state_packet["blind_judgment_hash"],
            )
            state_ids = [item["state_id"] for item in state_packet["state_items"]]
            self.assertEqual(
                state_properties["state_refs"]["items"]["enum"], state_ids
            )

    def test_blind_recording_rejects_unknown_candidate_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = prepare_run(root)
            judgment = build_blind_judgment(run_dir)
            judgment["packet_hash"] = "sha256:" + "0" * 64
            judgment["candidate_assessments"][0]["blind_id"] = "B99"
            path = root / "bad-blind.json"
            write_json(path, judgment)
            result = run_script(
                RECORD,
                "--dir",
                str(run_dir),
                "--stage",
                "blind",
                "--input",
                str(path),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("packet_hash does not match", result.stderr)
            self.assertIn("must reference the blind packet", result.stderr)

    def test_blind_recording_rejects_hidden_original_candidate_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = prepare_run(root)
            judgment = build_blind_judgment(run_dir)
            judgment["claim_ceiling"] = (
                "The current page-polish path should not control this blind judgment."
            )
            path = root / "identity-leak-blind.json"
            write_json(path, judgment)
            result = run_script(
                RECORD,
                "--dir",
                str(run_dir),
                "--stage",
                "blind",
                "--input",
                str(path),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("hidden original candidate candidate_id", result.stderr)

    def test_valid_blind_result_is_locked_before_state_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            judgment = record_blind(run_dir, carrier="fresh_subagent")
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            packet = json.loads((run_dir / "state-packet.json").read_text(encoding="utf-8"))
            self.assertEqual(state["stage"], "blind_recorded")
            self.assertEqual(state["blind_judgment_hash"], packet["blind_judgment_hash"])
            self.assertEqual(packet["blind_judgment"], judgment)
            self.assertIn("active_candidate_id", packet)
            state_kinds = {item["kind"] for item in packet["state_items"]}
            self.assertIn("switching_cost", state_kinds)
            self.assertIn("sunk_cost", state_kinds)
            self.assertIn("sunk-cost-only", packet["historical_spend_policy"])
            self.assertTrue((run_dir / "state-aware-agent-prompt.md").is_file())
            state_evidence_ids = {item["evidence_id"] for item in packet["evidence"]}
            self.assertIn("E-spend", state_evidence_ids)
            self.assertIn("E-owner", state_evidence_ids)
            authority_item = next(
                item for item in packet["state_items"] if item["kind"] == "authority_boundary"
            )
            self.assertEqual(authority_item["data"]["evidence_refs"], ["E-owner"])

    def test_state_context_must_bind_evidence_or_assumption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = json.loads(INPUT_TEMPLATE.read_text(encoding="utf-8"))
            state_item = data["state_context"]["switching_costs"][0]
            state_item["evidence_refs"] = []
            state_item["assumption_refs"] = []
            input_path = root / "unsupported-state-input.json"
            write_json(input_path, data)
            result = run_script(
                PREPARE,
                "--input",
                str(input_path),
                "--dir",
                str(root / "run"),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "must cite evidence_refs or assumption_refs",
                result.stderr,
            )

    def test_state_reconciliation_rejects_sunk_cost_and_unknown_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = prepare_run(root)
            record_blind(run_dir)
            judgment = build_state_judgment(run_dir)
            judgment["sunk_cost_used_as_reason"] = True
            judgment["current_floor"] = ["unknown-candidate"]
            judgment["evidence_refs"] = ["E-unknown"]
            path = root / "bad-state.json"
            write_json(path, judgment)
            result = run_script(
                RECORD,
                "--dir",
                str(run_dir),
                "--stage",
                "state-aware",
                "--input",
                str(path),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("sunk_cost_used_as_reason must be false", result.stderr)
            self.assertIn("unknown candidate IDs", result.stderr)
            self.assertIn("unknown IDs", result.stderr)

    def test_state_adjustment_rejects_wrong_kind_state_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = prepare_run(root)
            record_blind(run_dir)
            packet = json.loads((run_dir / "state-packet.json").read_text(encoding="utf-8"))
            sunk_ref = next(
                item["state_id"]
                for item in packet["state_items"]
                if item["kind"] == "sunk_cost"
            )
            judgment = build_state_judgment(run_dir)
            judgment["state_adjustments"][0]["state_refs"] = [sunk_ref]
            path = root / "wrong-kind-state.json"
            write_json(path, judgment)
            result = run_script(
                RECORD,
                "--dir",
                str(run_dir),
                "--stage",
                "state-aware",
                "--input",
                str(path),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("do not match adjustment kind switching_cost", result.stderr)

    def test_unchanged_state_result_must_preserve_locked_blind_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = prepare_run(root)
            record_blind(run_dir)
            judgment = build_state_judgment(run_dir)
            packet = json.loads((run_dir / "state-packet.json").read_text(encoding="utf-8"))
            alternatives = [
                item["candidate_id"]
                for item in packet["candidate_mapping"]
                if item["candidate_id"] != judgment["next_tranche"]["candidate_id"]
            ]
            judgment["current_floor"] = [alternatives[0]]
            judgment["next_tranche"]["candidate_id"] = alternatives[0]
            judgment["blind_result_changed"] = False
            path = root / "false-unchanged.json"
            write_json(path, judgment)
            result = run_script(
                RECORD,
                "--dir",
                str(run_dir),
                "--stage",
                "state-aware",
                "--input",
                str(path),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("preserve the locked blind floor", result.stderr)
            self.assertIn("preserve the locked blind replenishment choice", result.stderr)

    def test_changed_blind_result_requires_registered_state_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = prepare_run(root)
            record_blind(run_dir)
            judgment = build_state_judgment(run_dir)
            judgment["blind_result_changed"] = True
            judgment["change_reason"] = "State information changed the selected candidate."
            judgment["state_refs"] = []
            path = root / "uncited-change.json"
            write_json(path, judgment)
            result = run_script(
                RECORD,
                "--dir",
                str(run_dir),
                "--stage",
                "state-aware",
                "--input",
                str(path),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("changed blind result must cite", result.stderr)

    def test_changed_blind_result_cannot_rely_only_on_identity_or_sunk_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = prepare_run(root)
            record_blind(run_dir)
            packet = json.loads((run_dir / "state-packet.json").read_text(encoding="utf-8"))
            sunk_ref = next(
                item["state_id"]
                for item in packet["state_items"]
                if item["kind"] == "sunk_cost"
            )
            active_ref = next(
                item["state_id"]
                for item in packet["state_items"]
                if item["kind"] == "active_candidate"
            )
            judgment = build_state_judgment(run_dir)
            judgment["blind_result_changed"] = True
            judgment["change_reason"] = "The current path has already received substantial effort."
            judgment["state_refs"] = [active_ref, sunk_ref]
            judgment["state_adjustments"] = [
                {
                    "kind": "active_path_identity",
                    "finding": "This is the current path.",
                    "state_refs": [active_ref],
                    "evidence_refs": [],
                    "assumption_refs": [],
                },
                {
                    "kind": "sunk_cost_rejected",
                    "finding": "Historical spend exists but is not valid proof.",
                    "state_refs": [sunk_ref],
                    "evidence_refs": [],
                    "assumption_refs": [],
                },
            ]
            path = root / "identity-sunk-only-change.json"
            write_json(path, judgment)
            result = run_script(
                RECORD,
                "--dir",
                str(run_dir),
                "--stage",
                "state-aware",
                "--input",
                str(path),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-sunk, non-identity", result.stderr)
            self.assertIn("substantive state adjustment", result.stderr)

    def test_finalized_run_checks_and_renders_without_recomputing_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            record_blind(
                run_dir, carrier="ephemeral_cli", with_receipt=True
            )
            state_judgment = record_state(
                run_dir, carrier="fresh_subagent", with_receipt=True
            )

            check = run_script(CHECK, "--dir", str(run_dir), "--json")
            self.assertEqual(check.returncode, 0, check.stderr + check.stdout)
            report = json.loads(check.stdout)
            self.assertEqual(report["stage"], "finalized")
            self.assertEqual(report["status"], "ok")

            final = json.loads((run_dir / "final-decision.json").read_text(encoding="utf-8"))
            self.assertEqual(
                final["effective_isolation_claim"], "fresh_two_pass_with_receipts"
            )
            self.assertIn("does not prove", final["isolation_boundary"])
            self.assertEqual(final["decision"], state_judgment)

            rendered = run_script(RENDER, "--dir", str(run_dir))
            self.assertEqual(rendered.returncode, 0, rendered.stderr + rendered.stdout)
            for phrase in (
                "SRA 决策",
                "当前底座",
                "下一投入批次",
                "投入上限",
                "明确延后",
                "重排触发",
                "隔离口径",
            ):
                self.assertIn(phrase, rendered.stdout)

    def test_final_isolation_claim_cannot_exceed_recorded_carriers(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            record_blind(run_dir, carrier="packet_bound")
            record_state(run_dir, carrier="packet_bound")
            final_path = run_dir / "final-decision.json"
            final = json.loads(final_path.read_text(encoding="utf-8"))
            final["effective_isolation_claim"] = "fresh_two_pass_with_receipts"
            write_json(final_path, final)
            check = run_script(CHECK, "--dir", str(run_dir), "--json")
            self.assertNotEqual(check.returncode, 0)
            report = json.loads(check.stdout)
            self.assertTrue(
                any(item["code"] == "final-isolation-claim" for item in report["findings"])
            )

    def test_fresh_carrier_without_receipt_remains_a_declared_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            record_blind(run_dir, carrier="fresh_subagent")
            record_state(run_dir, carrier="ephemeral_cli")
            final = json.loads((run_dir / "final-decision.json").read_text(encoding="utf-8"))
            self.assertEqual(final["effective_isolation_claim"], "fresh_two_pass_declared")
            check = run_script(CHECK, "--dir", str(run_dir), "--json")
            report = json.loads(check.stdout)
            self.assertEqual(report["status"], "warning")
            self.assertTrue(
                any(
                    item["code"] == "fresh-carrier-without-receipt"
                    for item in report["findings"]
                )
            )

    def test_logical_packet_mode_cannot_claim_fresh_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            record_blind(run_dir, carrier="packet_bound")
            record_state(run_dir, carrier="packet_bound")
            final = json.loads((run_dir / "final-decision.json").read_text(encoding="utf-8"))
            self.assertEqual(final["effective_isolation_claim"], "logical_packet_only")
            check = run_script(CHECK, "--dir", str(run_dir), "--json")
            report = json.loads(check.stdout)
            self.assertEqual(report["status"], "warning")
            self.assertTrue(
                any(item["code"] == "logical-isolation-only" for item in report["findings"])
            )

    def test_run_check_detects_packet_and_admission_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            admission_path = run_dir / "context-admission.json"
            admission = json.loads(admission_path.read_text(encoding="utf-8"))
            admission["items"][0]["statement"] = "tampered"
            write_json(admission_path, admission)
            check = run_script(CHECK, "--dir", str(run_dir), "--json")
            self.assertNotEqual(check.returncode, 0)
            report = json.loads(check.stdout)
            self.assertEqual(report["status"], "blocked")
            self.assertTrue(
                any(
                    item["code"] == "context-manifest-hash"
                    for item in report["findings"]
                )
            )

    def test_recording_rejects_tampered_candidate_mapping_before_state_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = prepare_run(root)
            state_path = run_dir / "run.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["candidate_map"]["B01"] = "page-polish"
            write_json(state_path, state)
            judgment = build_blind_judgment(run_dir)
            path = root / "valid-looking-blind.json"
            write_json(path, judgment)
            result = run_script(
                RECORD,
                "--dir",
                str(run_dir),
                "--stage",
                "blind",
                "--input",
                str(path),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("candidate_map does not match", result.stderr)
            self.assertFalse((run_dir / "state-packet.json").exists())

    def test_candidate_context_asymmetry_is_warned_not_decided(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = json.loads(INPUT_TEMPLATE.read_text(encoding="utf-8"))
            data["candidates"][0]["objective_contribution"] = "rich " * 500
            data["candidates"][1]["objective_contribution"] = "thin"
            run_dir = prepare_run(Path(tmp), data)
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertTrue(any("context asymmetry" in item for item in state["warnings"]))
            self.assertTrue(all("priority" in item for item in state["warnings"]))

    def test_docs_keep_workflow_agentic_evidence_and_claim_boundaries(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in (CONTEXT_RESOURCE, DESIGN)
        )
        for phrase in (
            "Workflow owns",
            "Agentic owns",
            "Evidence owns",
            "relative independence",
            "packet_bound",
            "fresh_context",
            "blind_then_state",
            "previous_conclusion",
            "candidate_advocacy",
            "sunk-cost-only",
            "does not prove",
            "does not mutate TPlan",
        ):
            self.assertIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()

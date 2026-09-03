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
DESIGN = REPO / "docs" / "superpowers" / "specs" / "2026-09-03-sra-context-isolated-runtime-design.md"
CONTEXT_RESOURCE = SRA / "resources" / "context-isolation.md"


def run_script(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(script), *args],
        cwd=REPO,
        text=True,
        capture_output=True,
    )


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def template_data() -> dict:
    return json.loads(INPUT_TEMPLATE.read_text(encoding="utf-8"))


def prepare_run(root: Path, data: dict | None = None, name: str = "run") -> Path:
    payload = copy.deepcopy(data if data is not None else template_data())
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


def candidate_role(action: str) -> tuple[str, str, str]:
    lowered = action.lower()
    if "payment" in lowered:
        return (
            "threshold_essential",
            "retained",
            "Removing this action leaves the launch threshold unsupported.",
        )
    if "uncommitted" in lowered or "incident" in lowered:
        return (
            "maintenance_or_option",
            "capped",
            "This option becomes necessary only if an incident signal appears.",
        )
    return (
        "value_expanding",
        "removed",
        "Removing the next polish tranche does not change current launch acceptance.",
    )


def _selected_id(candidates: list[dict], id_field: str) -> str:
    return next(
        item[id_field]
        for item in candidates
        if "payment" in item["action_statement"].lower()
    )


def _polish_id(candidates: list[dict], id_field: str) -> str:
    return next(
        item[id_field]
        for item in candidates
        if "animation" in item["action_statement"].lower()
    )


def build_challenge_judgment(run_dir: Path, *, select_polish: bool = False) -> dict:
    packet = json.loads((run_dir / "challenge-packet.json").read_text(encoding="utf-8"))
    selected = _polish_id(packet["candidates"], "challenge_id") if select_polish else _selected_id(
        packet["candidates"], "challenge_id"
    )
    polish = _polish_id(packet["candidates"], "challenge_id")
    assessments = []
    for candidate in packet["candidates"]:
        role, contraction, break_point = candidate_role(candidate["action_statement"])
        assessments.append(
            {
                "challenge_id": candidate["challenge_id"],
                "feasibility": "feasible",
                "candidate_role": role,
                "contraction_result": contraction,
                "first_break_point": break_point,
                "evidence_refs": candidate.get("evidence_refs", []),
                "assumption_refs": candidate.get("assumption_refs", []),
            }
        )
    selected_candidate = next(
        item for item in packet["candidates"] if item["challenge_id"] == selected
    )
    return {
        "schema_version": "sra.challenge-judgment.v0.2",
        "stage": "challenge",
        "packet_hash": packet["packet_hash"],
        "allocation_outcome": "allocate",
        "candidate_assessments": assessments,
        "current_floor": [selected],
        "next_tranche": {
            "challenge_id": selected,
            "description": "Allocate one bounded engineer-day.",
            "reason": "The selected action remains after contraction.",
        },
        "investment_ceiling": "One engineer-day before reranking.",
        "authorization_horizon": "one_tranche",
        "maintenance": [polish] if selected != polish else [],
        "reserve": {
            "status": "none",
            "challenge_id": "none",
            "reason": "No packet evidence requires reserving the full tranche.",
            "release_trigger": "Not applicable while reserve is none.",
            "review_time": "At the next tranche checkpoint.",
        },
        "defer": [polish] if selected != polish else [],
        "stop": [],
        "rerank_triggers": ["The selected tranche closes the gap or reveals a blocker."],
        "missing_information": [],
        "evidence_refs": selected_candidate.get("evidence_refs", []),
        "assumption_refs": selected_candidate.get("assumption_refs", []),
        "claim_ceiling": "This is a de-anchored challenge view, not final authority.",
    }


def _state_refs_by_kind(packet: dict) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for item in packet.get("state_items", []):
        result.setdefault(item["kind"], []).append(item["state_id"])
    return result


def build_situated_judgment(run_dir: Path, *, select_polish: bool = False) -> dict:
    packet = json.loads((run_dir / "situated-packet.json").read_text(encoding="utf-8"))
    selected = "page-polish" if select_polish else "payment-validation"
    polish = "page-polish"
    assessments = []
    for candidate in packet["candidates"]:
        role, contraction, break_point = candidate_role(candidate["action_statement"])
        assessments.append(
            {
                "candidate_id": candidate["candidate_id"],
                "feasibility": "feasible",
                "candidate_role": role,
                "contraction_result": contraction,
                "first_break_point": break_point,
                "evidence_refs": candidate.get("evidence_refs", []),
                "assumption_refs": candidate.get("assumption_refs", []),
            }
        )
    refs = _state_refs_by_kind(packet)
    state_considerations = []
    state_refs = []
    for kind, consideration_kind, evidence_refs, assumption_refs in (
        ("switching_cost", "switching_cost", [], ["A-switch-cost"]),
        ("reusable_asset", "reusable_asset", ["E-page"], []),
        ("sunk_cost", "sunk_cost_rejected", ["E-spend"], []),
    ):
        if kind not in refs:
            continue
        state_id = refs[kind][0]
        state_refs.append(state_id)
        state_considerations.append(
            {
                "kind": consideration_kind,
                "finding": f"The admitted {kind} state was considered without inheriting a prior conclusion.",
                "state_refs": [state_id],
                "evidence_refs": evidence_refs,
                "assumption_refs": assumption_refs,
            }
        )
    selected_candidate = next(
        item for item in packet["candidates"] if item["candidate_id"] == selected
    )
    return {
        "schema_version": "sra.situated-judgment.v0.2",
        "stage": "situated",
        "packet_hash": packet["packet_hash"],
        "allocation_outcome": "allocate",
        "candidate_assessments": assessments,
        "state_considerations": state_considerations,
        "current_floor": [selected],
        "next_tranche": {
            "candidate_id": selected,
            "description": "Allocate one bounded engineer-day.",
            "reason": "The selected action remains preferred after real state costs are considered.",
        },
        "investment_ceiling": "One engineer-day before reranking.",
        "authorization_horizon": "one_tranche",
        "maintenance": [polish] if selected != polish else [],
        "reserve": {
            "status": "none",
            "candidate_id": "none",
            "reason": "No admitted state requires reserving the full tranche.",
            "release_trigger": "Not applicable while reserve is none.",
            "review_time": "At the next tranche checkpoint.",
        },
        "defer": [polish] if selected != polish else [],
        "stop": [],
        "rerank_triggers": ["The selected tranche closes the gap or reveals a blocker."],
        "missing_information": [],
        "state_refs": state_refs,
        "evidence_refs": selected_candidate.get("evidence_refs", []) + ["E-page", "E-spend"],
        "assumption_refs": list(
            dict.fromkeys(selected_candidate.get("assumption_refs", []) + ["A-switch-cost"])
        ),
        "sunk_cost_used_as_reason": False,
        "claim_ceiling": "This allocation applies to the current release window only.",
    }


def record_stage(
    run_dir: Path,
    stage: str,
    judgment: dict,
    *,
    carrier: str = "packet_bound",
    receipt: bool = False,
) -> subprocess.CompletedProcess[str]:
    input_path = run_dir.parent / f"{run_dir.name}-{stage}.json"
    write_json(input_path, judgment)
    args = [
        "--dir",
        str(run_dir),
        "--stage",
        stage,
        "--input",
        str(input_path),
        "--carrier",
        carrier,
        "--json",
    ]
    if receipt:
        receipt_path = run_dir.parent / f"{run_dir.name}-{stage}-receipt.json"
        write_json(receipt_path, {"stage": stage, "carrier": carrier, "completed": True})
        args.extend(["--receipt", str(receipt_path)])
    return run_script(RECORD, *args)


def record_valid_views(run_dir: Path, *, conflict: bool = False) -> None:
    challenge = build_challenge_judgment(run_dir)
    situated = build_situated_judgment(run_dir, select_polish=conflict)
    first = record_stage(run_dir, "challenge", challenge)
    if first.returncode != 0:
        raise AssertionError(first.stderr + first.stdout)
    second = record_stage(run_dir, "situated", situated)
    if second.returncode != 0:
        raise AssertionError(second.stderr + second.stdout)


def build_reconciliation_judgment(run_dir: Path) -> dict:
    packet = json.loads((run_dir / "reconciliation-packet.json").read_text(encoding="utf-8"))
    situated = build_situated_judgment(run_dir)
    situated["schema_version"] = "sra.reconciliation-judgment.v0.2"
    situated["stage"] = "reconciliation"
    situated["packet_hash"] = packet["packet_hash"]
    situated["allocation_outcome"] = "allocate"
    situated["conflict_resolutions"] = [
        {
            "field": item["field"],
            "resolution": "The cited current-state evidence supports the situated allocation for this window.",
            "evidence_refs": situated.get("evidence_refs", []),
            "assumption_refs": situated.get("assumption_refs", []),
            "state_refs": situated.get("state_refs", []),
        }
        for item in packet["conflict_fields"]
    ]
    allowed_evidence = {item["evidence_id"] for item in packet.get("evidence", [])}
    allowed_assumptions = {item["assumption_id"] for item in packet.get("assumptions", [])}
    allowed_state = {item["state_id"] for item in packet.get("state_items", [])}
    situated["evidence_refs"] = [item for item in situated["evidence_refs"] if item in allowed_evidence]
    situated["assumption_refs"] = [item for item in situated["assumption_refs"] if item in allowed_assumptions]
    situated["state_refs"] = [item for item in situated["state_refs"] if item in allowed_state]
    for assessment in situated["candidate_assessments"]:
        assessment["evidence_refs"] = [item for item in assessment["evidence_refs"] if item in allowed_evidence]
        assessment["assumption_refs"] = [item for item in assessment["assumption_refs"] if item in allowed_assumptions]
    situated["state_considerations"] = [
        item
        for item in situated["state_considerations"]
        if all(ref in allowed_state for ref in item["state_refs"])
    ]
    for item in situated["state_considerations"]:
        item["evidence_refs"] = [ref for ref in item["evidence_refs"] if ref in allowed_evidence]
        item["assumption_refs"] = [ref for ref in item["assumption_refs"] if ref in allowed_assumptions]
    for item in situated["conflict_resolutions"]:
        item["evidence_refs"] = [ref for ref in item["evidence_refs"] if ref in allowed_evidence]
        item["assumption_refs"] = [ref for ref in item["assumption_refs"] if ref in allowed_assumptions]
        item["state_refs"] = [ref for ref in item["state_refs"] if ref in allowed_state]
    return situated


class SraContextCalibrationTests(unittest.TestCase):
    def test_runtime_surface_exists(self):
        for path in (
            SRA / "scripts" / "sra_runtime.py",
            PREPARE,
            RECORD,
            CHECK,
            RENDER,
            SRA / "templates" / "coverage-judgment.json",
            SRA / "templates" / "challenge-judgment.json",
            SRA / "templates" / "situated-judgment.json",
            SRA / "templates" / "reconciliation-judgment.json",
            DESIGN,
            CONTEXT_RESOURCE,
        ):
            self.assertTrue(path.is_file(), path)

    def test_default_contaminated_lite_uses_dual_view_without_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(state["mode"], "lite")
            self.assertEqual(state["view_plan"], "dual_view")
            self.assertEqual(state["coverage_plan"], "skip")
            self.assertEqual(state["statuses"]["challenge"], "pending")
            self.assertEqual(state["statuses"]["situated"], "pending")

    def test_ordinary_lite_uses_situated_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = template_data()
            data["contamination_signals"] = []
            run_dir = prepare_run(Path(tmp), data)
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(state["view_plan"], "situated_only")
            self.assertEqual(state["statuses"]["challenge"], "not_required")
            self.assertFalse((run_dir / "challenge-agent-prompt.md").exists())
            self.assertTrue((run_dir / "situated-agent-prompt.md").exists())

    def test_full_with_known_omission_requires_coverage_and_dual_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = template_data()
            data["escalation_signals"] = ["multiple_feasible_bundles"]
            run_dir = prepare_run(Path(tmp), data)
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(state["mode"], "full")
            self.assertEqual(state["view_plan"], "dual_view")
            self.assertEqual(state["coverage_plan"], "required")
            self.assertTrue((run_dir / "coverage-agent-prompt.md").exists())

    def test_input_rejects_predecided_candidate_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = template_data()
            data["candidates"][0]["candidate_role"] = "threshold_essential"
            input_path = Path(tmp) / "input.json"
            write_json(input_path, data)
            result = run_script(PREPARE, "--input", str(input_path), "--dir", str(Path(tmp) / "run"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("pre-decided SRA role", result.stderr)

    def test_context_admission_quarantines_conclusions_and_advocacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            admission = json.loads((run_dir / "context-admission.json").read_text(encoding="utf-8"))
            by_id = {item["context_id"]: item for item in admission["items"]}
            self.assertEqual(by_id["C-current"]["admission"], "admitted")
            self.assertEqual(by_id["C-quality"]["admitted_as"], "decision_constraint")
            self.assertEqual(by_id["C-prior"]["admission"], "quarantined")
            self.assertEqual(by_id["C-advocacy"]["admission"], "quarantined")
            self.assertEqual(by_id["C-history"]["admitted_as"], "scoped_history")

    def test_current_instruction_cannot_be_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = template_data()
            current = next(item for item in data["context_items"] if item["context_id"] == "C-current")
            current["requested_disposition"] = "exclude"
            input_path = Path(tmp) / "input.json"
            write_json(input_path, data)
            result = run_script(PREPARE, "--input", str(input_path), "--dir", str(Path(tmp) / "run"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot exclude protected current context", result.stderr)

    def test_challenge_hides_incumbent_state_and_prior_conclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            text = (run_dir / "challenge-packet.json").read_text(encoding="utf-8")
            for forbidden in (
                '"active_candidate_id"',
                '"page-polish"',
                '"payment-validation"',
                '"switching_cost"',
                '"historical_spend"',
                "previous agent recommended",
            ):
                self.assertNotIn(forbidden, text)

            prompt = " ".join(
                (run_dir / "challenge-agent-prompt.md").read_text(encoding="utf-8").split()
            )
            self.assertIn("Do not invent or infer candidate identifiers", prompt)
            self.assertIn("ordinary descriptions without identifier-style slugs", prompt)

    def test_prepare_creates_agentic_output_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            self.assertTrue((run_dir / "judgments").is_dir())

    def test_challenge_relations_use_aliases_not_original_candidate_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = template_data()
            data["candidates"][0]["depends_on"] = ["payment-validation"]
            data["candidates"][1]["unlocks"] = ["page-polish"]
            data["candidates"][2]["substitutes_for"] = ["page-polish"]
            run_dir = prepare_run(Path(tmp), data)
            packet = json.loads(
                (run_dir / "challenge-packet.json").read_text(encoding="utf-8")
            )
            original_ids = {item["candidate_id"] for item in data["candidates"]}
            aliases = {item["challenge_id"] for item in packet["candidates"]}
            for candidate in packet["candidates"]:
                for relation in ("depends_on", "unlocks", "substitutes_for"):
                    self.assertTrue(set(candidate[relation]) <= aliases)
                    self.assertFalse(set(candidate[relation]) & original_ids)

    def test_situated_packet_does_not_receive_challenge_judgment(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            text = (run_dir / "situated-packet.json").read_text(encoding="utf-8")
            self.assertNotIn("challenge_core", text)
            self.assertNotIn("challenge_judgment_hash", text)
            self.assertNotIn("comparison", text)
            self.assertIn('"challenge_judgment_hidden": true', text)

    def test_challenge_order_is_input_order_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = template_data()
            first = prepare_run(root, data, "first")
            reversed_data = copy.deepcopy(data)
            reversed_data["candidates"].reverse()
            second = prepare_run(root, reversed_data, "second")
            first_packet = json.loads((first / "challenge-packet.json").read_text(encoding="utf-8"))
            second_packet = json.loads((second / "challenge-packet.json").read_text(encoding="utf-8"))
            self.assertEqual(first_packet["candidates"], second_packet["candidates"])
            first_state = json.loads((first / "run.json").read_text(encoding="utf-8"))
            second_state = json.loads((second / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(first_state["challenge_map"], second_state["challenge_map"])

    def test_evidence_asymmetry_is_preserved_not_equalized(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = template_data()
            data["candidates"][0]["expected_target_effect"] = "rich " * 300
            run_dir = prepare_run(Path(tmp), data)
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertTrue(any("presentation asymmetry" in item for item in state["warnings"]))
            packet = json.loads((run_dir / "challenge-packet.json").read_text(encoding="utf-8"))
            lengths = [len(item["expected_target_effect"]) for item in packet["candidates"]]
            self.assertNotEqual(min(lengths), max(lengths))

    def test_generated_carriers_are_read_only_and_no_fork(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            for stage in ("challenge", "situated"):
                dispatch = json.loads((run_dir / f"{stage}-subagent-dispatch.json").read_text(encoding="utf-8"))
                self.assertFalse(dispatch["fork_context"])
                self.assertTrue(dispatch["read_only"])
                self.assertEqual(dispatch["tool_policy"], "no_tools")
                command = (run_dir / f"{stage}-codex-command.sh").read_text(encoding="utf-8")
                for phrase in ("--ephemeral", "--ignore-rules", "--ignore-user-config", "-s read-only", "--output-schema"):
                    self.assertIn(phrase, command)

    def test_coverage_gate_blocks_allocation_views_until_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = template_data()
            data["coverage_review"] = "required"
            run_dir = prepare_run(Path(tmp), data)
            challenge = record_stage(run_dir, "challenge", build_challenge_judgment(run_dir))
            self.assertNotEqual(challenge.returncode, 0)
            self.assertIn("coverage review must be ready", challenge.stderr)

    def test_coverage_incomplete_blocks_run_without_allocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = template_data()
            data["coverage_review"] = "required"
            run_dir = prepare_run(Path(tmp), data)
            packet = json.loads((run_dir / "coverage-packet.json").read_text(encoding="utf-8"))
            judgment = {
                "schema_version": "sra.coverage-judgment.v0.2",
                "stage": "coverage",
                "packet_hash": packet["packet_hash"],
                "outcome": "packet_incomplete",
                "missing_candidate_classes": ["A regulatory hard-gate candidate has not been checked."],
                "missing_evidence": [],
                "classification_challenges": [],
                "warnings": [],
                "evidence_refs": [],
                "assumption_refs": [],
                "claim_ceiling": "Coverage review only.",
            }
            result = record_stage(run_dir, "coverage", judgment)
            self.assertEqual(result.returncode, 0, result.stderr)
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(state["statuses"]["finalization"], "blocked")
            final = json.loads((run_dir / "final-decision.json").read_text(encoding="utf-8"))
            self.assertEqual(final["decision"]["allocation_outcome"], "blocked")

    def test_dual_views_can_be_recorded_in_either_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            situated = record_stage(run_dir, "situated", build_situated_judgment(run_dir))
            self.assertEqual(situated.returncode, 0, situated.stderr)
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(state["statuses"]["situated"], "recorded")
            self.assertEqual(state["statuses"]["comparison"], "pending")
            challenge = record_stage(run_dir, "challenge", build_challenge_judgment(run_dir))
            self.assertEqual(challenge.returncode, 0, challenge.stderr)
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(state["statuses"]["comparison"], "agree")

    def test_agreement_finalizes_without_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            record_valid_views(run_dir)
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(state["statuses"]["comparison"], "agree")
            self.assertEqual(state["statuses"]["reconciliation"], "not_required")
            self.assertEqual(state["statuses"]["finalization"], "finalized")
            self.assertFalse((run_dir / "reconciliation-packet.json").exists())
            final = json.loads((run_dir / "final-decision.json").read_text(encoding="utf-8"))
            self.assertEqual(final["final_source"], "situated")

    def test_conflict_creates_bounded_reconciliation_without_choosing_winner(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            record_valid_views(run_dir, conflict=True)
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(state["statuses"]["comparison"], "conflict")
            self.assertEqual(state["statuses"]["reconciliation"], "pending")
            self.assertEqual(state["statuses"]["finalization"], "pending")
            comparison = json.loads((run_dir / "comparison-report.json").read_text(encoding="utf-8"))
            self.assertNotIn("winner", comparison)
            self.assertTrue(comparison["conflict_fields"])
            packet = json.loads((run_dir / "reconciliation-packet.json").read_text(encoding="utf-8"))
            self.assertTrue(packet["reconciliation_boundary"]["one_pass_only"])
            self.assertFalse(packet["reconciliation_boundary"]["may_force_closure"])

    def test_reconciliation_cannot_run_before_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            path = Path(tmp) / "fake.json"
            write_json(path, {"schema_version": "sra.reconciliation-judgment.v0.2"})
            result = run_script(RECORD, "--dir", str(run_dir), "--stage", "reconciliation", "--input", str(path))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("reconciliation is not pending", result.stderr)

    def test_reconciliation_finalizes_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            record_valid_views(run_dir, conflict=True)
            judgment = build_reconciliation_judgment(run_dir)
            first = record_stage(run_dir, "reconciliation", judgment)
            self.assertEqual(first.returncode, 0, first.stderr)
            second = record_stage(run_dir, "reconciliation", judgment)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("reconciliation is not pending", second.stderr)
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(state["statuses"]["finalization"], "finalized")
            final = json.loads((run_dir / "final-decision.json").read_text(encoding="utf-8"))
            self.assertEqual(final["final_source"], "reconciliation")

    def test_challenge_rejects_original_candidate_id_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            judgment = build_challenge_judgment(run_dir)
            judgment["claim_ceiling"] = "The page-polish path should stop."
            result = record_stage(run_dir, "challenge", judgment)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("hidden original candidate ID", result.stderr)

    def test_situated_rejects_sunk_cost_as_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            judgment = build_situated_judgment(run_dir)
            judgment["sunk_cost_used_as_reason"] = True
            result = record_stage(run_dir, "situated", judgment)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("sunk_cost_used_as_reason must be false", result.stderr)

    def test_run_check_detects_packet_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            packet_path = run_dir / "challenge-packet.json"
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            packet["known_omissions"].append("tampered")
            write_json(packet_path, packet)
            result = run_script(CHECK, "--dir", str(run_dir), "--json")
            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "blocked")
            self.assertTrue(any(item["code"] == "packet-rebuild" for item in report["findings"]))

    def test_packet_bound_views_do_not_claim_fresh_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            record_valid_views(run_dir)
            final = json.loads((run_dir / "final-decision.json").read_text(encoding="utf-8"))
            self.assertEqual(final["observed_context_boundary"], "packet_bound_views_only")
            self.assertIn("does not prove", final["context_boundary_note"])

    def test_fresh_carriers_without_receipts_remain_declared(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            challenge = record_stage(
                run_dir,
                "challenge",
                build_challenge_judgment(run_dir),
                carrier="fresh_subagent",
            )
            self.assertEqual(challenge.returncode, 0, challenge.stderr)
            situated = record_stage(
                run_dir,
                "situated",
                build_situated_judgment(run_dir),
                carrier="ephemeral_cli",
            )
            self.assertEqual(situated.returncode, 0, situated.stderr)
            check = run_script(CHECK, "--dir", str(run_dir), "--json")
            report = json.loads(check.stdout)
            self.assertEqual(report["status"], "warning")
            self.assertTrue(any(item["code"] == "fresh-carrier-without-receipt" for item in report["findings"]))

    def test_finalized_run_checks_and_renders(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            record_valid_views(run_dir)
            check = run_script(CHECK, "--dir", str(run_dir), "--json")
            self.assertEqual(check.returncode, 0, check.stderr + check.stdout)
            report = json.loads(check.stdout)
            self.assertEqual(report["status"], "ok")
            rendered = run_script(RENDER, "--dir", str(run_dir))
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            for phrase in ("SRA 决策", "当前底座", "下一投入对象", "投入上限", "重排触发", "最终来源", "上下文边界"):
                self.assertIn(phrase, rendered.stdout)

    def test_docs_define_dual_view_without_blind_override_semantics(self):
        combined = "\n".join(path.read_text(encoding="utf-8") for path in (DESIGN, CONTEXT_RESOURCE))
        for phrase in (
            "challenge",
            "situated",
            "dual_view",
            "structural alignment",
            "Evidence",
            "TPlan",
        ):
            self.assertIn(phrase, combined)
        self.assertNotIn("blind_result_changed", combined)


if __name__ == "__main__":
    unittest.main()

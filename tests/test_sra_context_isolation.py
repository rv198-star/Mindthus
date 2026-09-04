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
REPAIR = SCRIPTS / "repair_sra_run.py"
INPUT_TEMPLATE = SRA / "templates" / "context-input.json"
COVERAGE_TEMPLATE = SRA / "templates" / "coverage-judgment.json"
CHALLENGE_TEMPLATE = SRA / "templates" / "challenge-judgment.json"
SITUATED_TEMPLATE = SRA / "templates" / "situated-judgment.json"
RECONCILIATION_TEMPLATE = SRA / "templates" / "reconciliation-judgment.json"
FULL_INPUT_TEMPLATE = SRA / "templates" / "full-context-input.json"
FULL_CHALLENGE_TEMPLATE = SRA / "templates" / "full-challenge-judgment.json"
FULL_SITUATED_TEMPLATE = SRA / "templates" / "full-situated-judgment.json"
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


def bound_template(template_path: Path, packet_path: Path) -> dict:
    value = json.loads(template_path.read_text(encoding="utf-8"))
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    value["packet_hash"] = packet["packet_hash"]
    return value


def build_challenge_judgment(run_dir: Path, *, conflict: bool = False) -> dict:
    value = bound_template(CHALLENGE_TEMPLATE, run_dir / "challenge-packet.json")
    if conflict:
        value["next_tranche"]["resource_allocations"][0]["quantity"]["amount"] = 0.5
        value["investment_ceiling"][0]["quantity"]["amount"] = 0.5
    return value


def build_situated_judgment(run_dir: Path) -> dict:
    return bound_template(SITUATED_TEMPLATE, run_dir / "situated-packet.json")


def build_reconciliation_judgment(run_dir: Path) -> dict:
    return bound_template(
        RECONCILIATION_TEMPLATE,
        run_dir / "reconciliation-packet.json",
    )


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
    first = record_stage(
        run_dir,
        "challenge",
        build_challenge_judgment(run_dir, conflict=conflict),
    )
    if first.returncode != 0:
        raise AssertionError(first.stderr + first.stdout)
    second = record_stage(run_dir, "situated", build_situated_judgment(run_dir))
    if second.returncode != 0:
        raise AssertionError(second.stderr + second.stdout)


class SraContextCalibrationTests(unittest.TestCase):
    def test_runtime_surface_exists(self):
        for path in (
            SCRIPTS / "sra_domain.py",
            SCRIPTS / "sra_runtime_core.py",
            SCRIPTS / "sra_runtime_integrity.py",
            SCRIPTS / "sra_runtime.py",
            PREPARE,
            RECORD,
            CHECK,
            RENDER,
            REPAIR,
            INPUT_TEMPLATE,
            CHALLENGE_TEMPLATE,
            SITUATED_TEMPLATE,
            RECONCILIATION_TEMPLATE,
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
            data["mode"] = "auto"
            data["escalation_signals"] = ["multiple_feasible_bundles"]
            data["known_omissions"] = ["A compliance candidate may be missing."]
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
            result = run_script(
                PREPARE,
                "--input",
                str(input_path),
                "--dir",
                str(Path(tmp) / "run"),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("pre-decided SRA role", result.stderr)

    def test_context_admission_quarantines_conclusions_and_advocacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            admission = json.loads(
                (run_dir / "context-admission.json").read_text(encoding="utf-8")
            )
            by_id = {item["context_id"]: item for item in admission["items"]}
            self.assertEqual(by_id["CTX-quality"]["admission"], "admitted")
            self.assertEqual(
                by_id["CTX-quality"]["admitted_as"], "decision_constraint"
            )
            self.assertEqual(by_id["CTX-prior"]["admission"], "quarantined")
            self.assertEqual(by_id["CTX-advocacy"]["admission"], "quarantined")

    def test_protected_constraint_cannot_be_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = template_data()
            item = next(
                item
                for item in data["context_items"]
                if item["context_id"] == "CTX-quality"
            )
            item["requested_disposition"] = "exclude"
            input_path = Path(tmp) / "input.json"
            write_json(input_path, data)
            result = run_script(
                PREPARE,
                "--input",
                str(input_path),
                "--dir",
                str(Path(tmp) / "run"),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot exclude protected", result.stderr)

    def test_challenge_hides_incumbent_state_prior_conclusion_and_situated_question(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            text = (run_dir / "challenge-packet.json").read_text(encoding="utf-8")
            for forbidden in (
                '"active_candidate_id"',
                '"page-polish"',
                '"payment-validation"',
                "previous agent recommended",
                "Should the release engineer continue optional page polish",
            ):
                self.assertNotIn(forbidden, text)
            self.assertIn("Which eligible release action", text)

            prompt = " ".join(
                (run_dir / "challenge-agent-prompt.md")
                .read_text(encoding="utf-8")
                .split()
            )
            for phrase in (
                "Use supplied challenge IDs",
                "Prose is not identity evidence",
                "`allocation_ledger` contains exactly one posture per candidate",
                "Full records bundle assessments",
                "one fixed resource block",
            ):
                self.assertIn(phrase, prompt)

    def test_challenge_relations_use_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = template_data()
            data["candidates"][0]["depends_on"] = ["payment-validation"]
            data["candidates"][1]["unlocks"] = ["page-polish"]
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
            self.assertNotIn("comparison_hash", text)
            self.assertIn('"challenge_judgment_hidden": true', text)

    def test_challenge_order_is_input_order_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = template_data()
            first = prepare_run(root, data, "first")
            reversed_data = copy.deepcopy(data)
            reversed_data["candidates"].reverse()
            second = prepare_run(root, reversed_data, "second")
            first_packet = json.loads(
                (first / "challenge-packet.json").read_text(encoding="utf-8")
            )
            second_packet = json.loads(
                (second / "challenge-packet.json").read_text(encoding="utf-8")
            )
            self.assertEqual(first_packet["candidates"], second_packet["candidates"])
            first_state = json.loads((first / "run.json").read_text(encoding="utf-8"))
            second_state = json.loads((second / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(first_state["challenge_map"], second_state["challenge_map"])

    def test_generated_carriers_are_read_only_and_no_fork(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            for stage in ("challenge", "situated"):
                dispatch = json.loads(
                    (run_dir / f"{stage}-subagent-dispatch.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertFalse(dispatch["fork_context"])
                self.assertTrue(dispatch["read_only"])
                self.assertEqual(dispatch["tool_policy"], "no_tools")
                command = (run_dir / f"{stage}-codex-command.sh").read_text(
                    encoding="utf-8"
                )
                for phrase in (
                    "--ephemeral",
                    "--ignore-rules",
                    "--ignore-user-config",
                    "-s read-only",
                    "--output-schema",
                ):
                    self.assertIn(phrase, command)

    def test_coverage_gate_blocks_views_until_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = template_data()
            data["coverage_review"] = "required"
            run_dir = prepare_run(Path(tmp), data)
            result = record_stage(
                run_dir, "challenge", build_challenge_judgment(run_dir)
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("coverage review must be ready", result.stderr)

    def test_coverage_incomplete_blocks_run_without_allocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = template_data()
            data["coverage_review"] = "required"
            run_dir = prepare_run(Path(tmp), data)
            packet = json.loads(
                (run_dir / "coverage-packet.json").read_text(encoding="utf-8")
            )
            judgment = {
                "schema_version": "sra.coverage-judgment.v0.3",
                "stage": "coverage",
                "packet_hash": packet["packet_hash"],
                "outcome": "packet_incomplete",
                "missing_candidate_classes": ["A regulatory hard gate is unchecked."],
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
            final = json.loads(
                (run_dir / "final-decision.json").read_text(encoding="utf-8")
            )
            self.assertEqual(final["decision"]["allocation_outcome"], "blocked")

    def test_dual_views_can_be_recorded_in_either_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = prepare_run(root, name="situated-first")
            situated = record_stage(
                first, "situated", build_situated_judgment(first)
            )
            self.assertEqual(situated.returncode, 0, situated.stderr)
            challenge = record_stage(
                first, "challenge", build_challenge_judgment(first)
            )
            self.assertEqual(challenge.returncode, 0, challenge.stderr)
            self.assertEqual(
                json.loads((first / "run.json").read_text())["statuses"]["comparison"],
                "agree",
            )

            second = prepare_run(root, name="challenge-first")
            record_valid_views(second)
            self.assertEqual(
                json.loads((second / "run.json").read_text())["statuses"]["comparison"],
                "agree",
            )

    def test_agreement_finalizes_without_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            record_valid_views(run_dir)
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(state["statuses"]["comparison"], "agree")
            self.assertEqual(state["statuses"]["reconciliation"], "not_required")
            self.assertEqual(state["statuses"]["finalization"], "finalized")
            self.assertFalse((run_dir / "reconciliation-packet.json").exists())

    def test_conflict_creates_bounded_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            record_valid_views(run_dir, conflict=True)
            state = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(state["statuses"]["comparison"], "conflict")
            self.assertEqual(state["statuses"]["reconciliation"], "pending")
            comparison = json.loads(
                (run_dir / "comparison-report.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("winner", comparison)
            packet = json.loads(
                (run_dir / "reconciliation-packet.json").read_text(encoding="utf-8")
            )
            self.assertTrue(packet["reconciliation_boundary"]["one_pass_only"])
            self.assertFalse(packet["reconciliation_boundary"]["may_force_closure"])

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

    def test_challenge_rejects_original_candidate_id_in_structured_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            judgment = build_challenge_judgment(run_dir)
            judgment["next_tranche"]["target_id"] = "page-polish"
            result = record_stage(run_dir, "challenge", judgment)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("next_tranche.target_id", result.stderr)

    def test_situated_rejects_sunk_cost_as_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            judgment = build_situated_judgment(run_dir)
            judgment["sunk_cost_used_as_reason"] = True
            result = record_stage(run_dir, "situated", judgment)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("sunk_cost_used_as_reason must be false", result.stderr)

    def test_run_check_detects_packet_and_prompt_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            packet_path = run_dir / "challenge-packet.json"
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            packet["known_omissions"].append("tampered")
            write_json(packet_path, packet)
            prompt_path = run_dir / "situated-agent-prompt.md"
            prompt_path.write_text("tampered", encoding="utf-8")
            result = run_script(CHECK, "--dir", str(run_dir), "--json")
            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            codes = {item["code"] for item in report["findings"]}
            self.assertIn("packet-rebuild", codes)
            self.assertIn("situated-prompt", codes)

    def test_packet_bound_views_do_not_claim_fresh_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            record_valid_views(run_dir)
            final = json.loads(
                (run_dir / "final-decision.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                final["observed_context_boundary"], "packet_bound_views_only"
            )
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
            self.assertTrue(
                any(
                    item["code"] == "fresh-carrier-without-receipt"
                    for item in report["findings"]
                )
            )

    def test_finalized_run_checks_renders_and_repairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = prepare_run(Path(tmp))
            record_valid_views(run_dir)
            check = run_script(CHECK, "--dir", str(run_dir), "--json")
            self.assertEqual(check.returncode, 0, check.stderr + check.stdout)
            rendered = run_script(RENDER, "--dir", str(run_dir))
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            for phrase in (
                "SRA 决策",
                "当前底座",
                "下一投入对象",
                "投入上限",
                "治理覆盖",
                "上下文边界",
            ):
                self.assertIn(phrase, rendered.stdout)
            prompt = run_dir / "challenge-agent-prompt.md"
            prompt.write_text("tampered", encoding="utf-8")
            repair = run_script(REPAIR, "--dir", str(run_dir), "--json")
            self.assertEqual(repair.returncode, 0, repair.stderr + repair.stdout)
            self.assertEqual(
                json.loads(repair.stdout)["status"],
                "ok",
            )


if __name__ == "__main__":
    unittest.main()

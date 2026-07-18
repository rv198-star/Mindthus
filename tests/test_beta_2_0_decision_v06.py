from __future__ import annotations

import importlib.util
import json
import os
import platform
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = REPO_ROOT / "beta" / "2.0.0-beta.2" / "runtime" / "decision_evaluation_v06.py"
RUNNER_PATH = REPO_ROOT / "beta" / "2.0.0-beta.2" / "runtime" / "run_real_codex_evaluation_v06.py"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CORE = load_module("decision_evaluation_v06_test", CORE_PATH)
RUNNER = load_module("run_real_codex_evaluation_v06_test", RUNNER_PATH)


class DecisionV06Test(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.protocol_path = self.root / "protocol.json"
        self.lock_path = self.root / "lock.json"
        manifest_paths = []
        for arm_id in CORE.ARM_IDS:
            manifest = {
                "arm_id": arm_id,
                "identity_digest": f"identity-{arm_id}",
                "package": {
                    "tree_sha256": (
                        "stable-package" if arm_id == "stable" else "beta-package"
                    )
                },
            }
            path = self.root / "arms" / arm_id / "sealed-arm.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(manifest), encoding="utf-8")
            manifest_paths.append(path)
        CORE.freeze_protocol(manifest_paths, self.protocol_path, self.lock_path)
        self.protocol = CORE.read_json(self.protocol_path)
        self.protocol_sha = CORE.sha256_file(self.protocol_path)
        self.plan = CORE.batch_plan(self.protocol, self.protocol_sha)
        self.contracts = CORE.case_contracts()
        self.out = self.root / "run"
        self.out.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def isolation(self, role: str, identifier: str, attempt: int, slot: int | None = None) -> dict:
        suffix = f"-{slot}" if slot is not None else ""
        path = self.out / "isolation" / f"{role}-{identifier}-{attempt}{suffix}.json"
        receipt = {
            "schema_version": "synthetic-isolation-v0.6",
            "status": "pass",
            "semantic_process_profile_applied": True,
        }
        receipt["receipt_digest"] = CORE.canonical_sha256(receipt)
        CORE.write_atomic_json(path, receipt)
        return {"path": str(path), "receipt_digest": receipt["receipt_digest"]}

    def cell(
        self,
        batch: dict,
        arm_id: str,
        *,
        input_tokens: int,
        wall: float,
        hops: int,
        promote: bool = True,
    ) -> dict | tuple[dict, dict, dict]:
        arm = next(item for item in self.protocol["arms"] if item["arm_id"] == arm_id)
        contract = self.contracts[batch["case_id"]]
        cell_id, key = CORE.cell_identity(
            protocol_sha256=self.protocol_sha,
            batch=batch,
            arm=arm,
            contract=contract,
        )
        attempt_dir = self.out / "generation-attempts" / cell_id / "attempt-01"
        attempt_dir.mkdir(parents=True, exist_ok=True)
        answer = f"Synthetic {batch['case_id']} answer for {arm_id}"
        answer_path = attempt_dir / "answer.txt"
        answer_path.write_text(answer, encoding="utf-8")
        usage = {
            "input_tokens": input_tokens,
            "output_tokens": 1,
            "reasoning_output_tokens": 0,
        }
        telemetry = {"evidence_gate": {"status": "pass"}}
        attempt = {
            "schema_version": CORE.GENERATION_ATTEMPT_SCHEMA,
            "batch_id": batch["batch_id"],
            "cell_id": cell_id,
            "cell_key": key,
            "arm_id": arm_id,
            "attempt": 1,
            "returncode": 0,
            "timed_out": False,
            "wall_time_seconds": wall,
            "first_observable_action": None,
            "answer_present": True,
            "answer_sha256": CORE.sha256_text(answer),
            "usage": usage,
            "counted_tokens": input_tokens + 1,
            "skill_hops": [f"hop-{index}" for index in range(hops)],
            "observed_resource_read_failure": False,
            "telemetry": telemetry,
            "isolation_receipt": self.isolation("generation", cell_id, 1),
        }
        attempt["attempt_digest"] = CORE.canonical_sha256(attempt)
        CORE.write_atomic_json(attempt_dir / "attempt.json", attempt)
        record = {
            "schema_version": CORE.CELL_SCHEMA,
            "cell_id": cell_id,
            "cell_key": key,
            "batch_id": batch["batch_id"],
            "batch_index": batch["batch_index"],
            "case_id": batch["case_id"],
            "repeat": batch["repeat"],
            "arm_id": arm_id,
            "case_contract_digest": CORE.canonical_sha256(contract),
            "generation_attempt": {
                "attempt": 1,
                "attempt_digest": attempt["attempt_digest"],
                "path": str(attempt_dir),
            },
            "answer_path": str(answer_path),
            "answer_sha256": CORE.sha256_text(answer),
            "usage": usage,
            "counted_tokens": input_tokens + 1,
            "wall_time_seconds": wall,
            "first_observable_action": None,
            "skill_hops": attempt["skill_hops"],
            "observed_resource_read_failure": False,
            "telemetry_digest": CORE.canonical_sha256(telemetry),
        }
        record["record_digest"] = CORE.canonical_sha256(record)
        if promote:
            CORE.write_atomic_json(self.out / "cells" / cell_id / "record.json", record)
            return record
        return attempt, record, arm

    def verdict_candidate(
        self,
        *,
        candidate_id: str,
        contract: dict,
        owner_success: bool,
        primitives_success: bool,
        false_wakeup: bool = False,
        authority: bool = False,
        quality: float = 1,
    ) -> dict:
        accepted = list(contract["accepted_execution_owners"])
        owner_enum = CORE.read_json(CORE.JUDGE_SCHEMA_PATH)["properties"]["candidates"]["items"]["properties"]["observed_execution_owner"]["enum"]
        owner = accepted[0] if owner_success else next(item for item in owner_enum if item not in accepted)
        action = None if contract["required_visible_action"] is None else owner_success
        return {
            "candidate_id": candidate_id,
            "normalized_final_answer_score": quality,
            "observed_execution_owner": owner,
            "primitive_obligation_results": [
                {"primitive_id": primitive, "satisfied": primitives_success}
                for primitive in contract["expected_primitive_obligations"]
            ],
            "unexpected_primitive_actions": [],
            "false_wakeup_final_answer": false_wakeup,
            "required_visible_action_present": action,
            "authority_or_evidence_regression": authority,
            "clarification_turns": 0,
            "rationale": "Synthetic frozen-contract verdict.",
        }

    def judges(
        self,
        batch: dict,
        cells: list[dict],
        *,
        thin_kernel_success: bool,
        direct_kernel_success: bool,
        disagreement: bool = False,
    ) -> list[dict]:
        contract = self.contracts[batch["case_id"]]
        answers = {
            cell["cell_id"]: Path(cell["answer_path"]).read_text(encoding="utf-8")
            for cell in cells
        }
        results = []
        for slot in (1, 2):
            payload, receipt = CORE.build_blinded_input(
                protocol_sha256=self.protocol_sha,
                batch=batch,
                contract=contract,
                prompt="synthetic prompt",
                cells=cells,
                answers=answers,
                slot=slot,
            )
            input_root = self.out / "paired-judge-inputs" / batch["batch_id"]
            input_path = input_root / f"slot-{slot}.input.json"
            receipt_path = input_root / f"slot-{slot}.receipt.json"
            CORE.write_atomic_json(input_path, payload)
            CORE.write_atomic_json(receipt_path, receipt)
            arm_by_candidate = {
                CORE.candidate_identity(self.protocol_sha, batch["batch_id"], cell["cell_id"]): cell["arm_id"]
                for cell in cells
            }
            candidates = []
            for candidate_id in receipt["candidate_order"]:
                arm_id = arm_by_candidate[candidate_id]
                primitives_success = (
                    thin_kernel_success
                    if arm_id == "thin-kernel"
                    else direct_kernel_success
                    if arm_id == "direct-only"
                    else True
                )
                owner_success = not (
                    disagreement and slot == 2 and arm_id == "thin-kernel"
                )
                candidates.append(
                    self.verdict_candidate(
                        candidate_id=candidate_id,
                        contract=contract,
                        owner_success=owner_success,
                        primitives_success=primitives_success,
                    )
                )
            raw = {"batch_id": batch["batch_id"], "candidates": candidates}
            attempt_dir = self.out / "paired-judge-attempts" / batch["batch_id"] / f"slot-{slot}" / "attempt-01"
            attempt_dir.mkdir(parents=True, exist_ok=True)
            output_path = attempt_dir / "judge-output.json"
            output_path.write_text(json.dumps(raw), encoding="utf-8")
            usage = {"input_tokens": 100, "output_tokens": 1, "reasoning_output_tokens": 0}
            attempt = {
                "schema_version": CORE.JUDGE_ATTEMPT_SCHEMA,
                "batch_id": batch["batch_id"],
                "judge_slot": slot,
                "attempt": 1,
                "returncode": 0,
                "timed_out": False,
                "output_present": True,
                "output_sha256": CORE.sha256_text(output_path.read_text(encoding="utf-8")),
                "parse_error": None,
                "usage": usage,
                "counted_tokens": 101,
                "environment_digest": f"judge-env-{slot}",
                "blinded_input_digest": payload["input_digest"],
                "blinding_receipt_digest": receipt["receipt_digest"],
                "judge_prompt_sha256": "synthetic-prompt",
                "tool_call_count": 0,
                "isolation_receipt": self.isolation("judge", batch["batch_id"], 1, slot),
            }
            attempt["attempt_digest"] = CORE.canonical_sha256(attempt)
            CORE.write_atomic_json(attempt_dir / "attempt.json", attempt)
            record = {
                "schema_version": CORE.JUDGE_RECORD_SCHEMA,
                "batch_id": batch["batch_id"],
                "judge_slot": slot,
                "judge_attempt": {
                    "attempt": 1,
                    "attempt_digest": attempt["attempt_digest"],
                    "path": str(attempt_dir),
                },
                "environment_digest": f"judge-env-{slot}",
                "blinded_input_digest": payload["input_digest"],
                "judge_prompt_sha256": "synthetic-prompt",
                "blinding_receipt": {
                    "path": str(receipt_path),
                    "receipt_digest": receipt["receipt_digest"],
                },
                "verdict": raw,
                "usage": usage,
                "counted_tokens": 101,
            }
            record["record_digest"] = CORE.canonical_sha256(record)
            CORE.write_atomic_json(
                self.out / "paired-judge-records" / batch["batch_id"] / f"slot-{slot}.json",
                record,
            )
            results.append(record)
        return results

    def committed_batch(
        self,
        index: int,
        previous: str | None,
        *,
        supported: bool,
        disagreement: bool = False,
        burdened: bool = False,
    ) -> str:
        batch = self.plan[index - 1]
        benefit = batch["case_id"] in set(CORE.read_json(CORE.CASES_PATH)["buckets"]["kernel-benefit"])
        thin_success = supported or not benefit
        direct_success = not benefit or (index % 2 == 0)
        cells = [
            self.cell(
                batch,
                arm_id,
                input_tokens=(
                    1200
                    if burdened and arm_id == "thin-kernel"
                    else 800
                    if arm_id != "stable"
                    else 1000
                ),
                wall=(
                    12
                    if burdened and arm_id == "thin-kernel"
                    else 8
                    if arm_id == "thin-kernel"
                    else 10
                ),
                hops=(
                    2
                    if burdened and arm_id == "thin-kernel"
                    else 0
                    if arm_id == "thin-kernel"
                    else 1
                ),
            )
            for arm_id in CORE.ARM_IDS
        ]
        judges = self.judges(
            batch,
            cells,
            thin_kernel_success=thin_success,
            direct_kernel_success=direct_success,
            disagreement=disagreement,
        )
        commit = CORE.build_batch_commit(
            batch=batch,
            cells=cells,
            judge_records=judges,
            previous_commit_digest=previous,
        )
        CORE.write_atomic_json(self.out / "batch-commits" / f"{index:03d}.json", commit)
        return commit["commit_digest"]

    def test_plan_is_eight_by_three_with_three_pilot_batches(self) -> None:
        self.assertEqual(len(self.plan), 24)
        self.assertEqual([item["phase"] for item in self.plan[:3]], ["pilot"] * 3)
        self.assertEqual(sum(len(item["cells"]) for item in self.plan), 72)
        self.assertEqual(len(self.plan) * 2, 48)

    def test_schema_avoids_unsupported_unique_items(self) -> None:
        schema_text = CORE.JUDGE_SCHEMA_PATH.read_text(encoding="utf-8")
        self.assertNotIn("uniqueItems", schema_text)
        self.assertEqual(CORE._unsupported_schema_keywords(json.loads(schema_text)), [])
        rubric = CORE.read_json(CORE.JUDGE_RUBRIC_PATH)
        self.assertEqual(set(rubric["execution_owners"]), set(CORE.read_json(CORE.JUDGE_SCHEMA_PATH)["properties"]["candidates"]["items"]["properties"]["observed_execution_owner"]["enum"]))
        self.assertEqual(
            set(rubric["primitives"]),
            set(
                CORE.read_json(CORE.JUDGE_SCHEMA_PATH)["properties"]["candidates"]["items"]["properties"]["unexpected_primitive_actions"]["items"]["enum"]
            ),
        )

    def test_generator_wrapper_does_not_prime_a_method_or_plugin(self) -> None:
        prompt = RUNNER._generator_prompt("用户问题")
        lowered = prompt.lower()
        self.assertNotIn("mindthus", lowered)
        self.assertNotIn("superpowers", lowered)
        self.assertNotIn("wae", lowered)
        self.assertIn("用户问题", prompt)
        arm_root = self.root / "command-arm"
        (arm_root / "codex-home").mkdir(parents=True)
        (arm_root / "project").mkdir()
        command, _, _ = RUNNER._generator_command(
            {
                "arm_id": "direct-only",
                "host": {
                    "home": str(arm_root / "codex-home"),
                    "execution_root": str(arm_root / "project"),
                },
            },
            self.root / "answer.txt",
        )
        self.assertIn("--strict-config", command)
        self.assertIn(
            f"model_context_window={CORE.MAX_COUNTED_TOKENS_PER_CALL}", command
        )

    def test_blinding_removes_namespace_without_mutating_original(self) -> None:
        original = "先调用 mindthus:wae，再调用 mindthus-beta:edsp。"
        view, transformed = CORE.blinded_answer(original)
        self.assertTrue(transformed)
        self.assertEqual(original, "先调用 mindthus:wae，再调用 mindthus-beta:edsp。")
        self.assertNotIn("mindthus:", view.lower())
        self.assertNotIn("mindthus-beta:", view.lower())
        with self.assertRaisesRegex(CORE.DecisionError, "sensitive path"):
            CORE.blinded_answer("read /private/arm", ["/private/arm"])

    def test_local_paired_validator_rejects_duplicate_candidate_and_primitive(self) -> None:
        batch = self.plan[0]
        contract = self.contracts[batch["case_id"]]
        ids = ["a", "b", "c"]
        raw = {
            "batch_id": batch["batch_id"],
            "candidates": [
                self.verdict_candidate(
                    candidate_id=candidate_id,
                    contract=contract,
                    owner_success=True,
                    primitives_success=True,
                )
                for candidate_id in ids
            ],
        }
        CORE.validate_paired_judge_output(raw, batch_id=batch["batch_id"], candidate_ids=ids, contract=contract)
        raw["candidates"][2]["candidate_id"] = "a"
        with self.assertRaises(CORE.DecisionError):
            CORE.validate_paired_judge_output(raw, batch_id=batch["batch_id"], candidate_ids=ids, contract=contract)
        raw["candidates"][2]["candidate_id"] = "c"
        if raw["candidates"][0]["primitive_obligation_results"]:
            raw["candidates"][0]["primitive_obligation_results"].append(
                dict(raw["candidates"][0]["primitive_obligation_results"][0])
            )
            with self.assertRaises(CORE.DecisionError):
                CORE.validate_paired_judge_output(raw, batch_id=batch["batch_id"], candidate_ids=ids, contract=contract)

    def test_finalized_generation_attempt_promotes_without_model_call(self) -> None:
        batch = self.plan[0]
        cell = next(item for item in batch["cells"] if item["arm_id"] == "thin-kernel")
        attempt, expected, arm = self.cell(
            batch,
            "thin-kernel",
            input_tokens=800,
            wall=8,
            hops=0,
            promote=False,
        )
        with mock.patch.object(RUNNER.V04, "run_streamed") as semantic_call:
            promoted = RUNNER._promote_generation(
                protocol_sha256=self.protocol_sha,
                batch=batch,
                cell=cell,
                arm_receipt=arm,
                contract=self.contracts[batch["case_id"]],
                out_dir=self.out,
            )
        self.assertIsNotNone(promoted)
        self.assertEqual(promoted["answer_sha256"], expected["answer_sha256"])
        self.assertEqual(
            promoted["generation_attempt"]["attempt_digest"], attempt["attempt_digest"]
        )
        semantic_call.assert_not_called()
        self.assertEqual(CORE.attempt_usage(self.out)["generation_calls"], 1)

    def test_finalized_paired_judge_attempt_promotes_without_model_call(self) -> None:
        batch = self.plan[0]
        cells = [
            self.cell(batch, arm_id, input_tokens=800, wall=8, hops=0)
            for arm_id in CORE.ARM_IDS
        ]
        records = self.judges(
            batch,
            cells,
            thin_kernel_success=True,
            direct_kernel_success=False,
        )
        slot = 1
        record_path = (
            self.out
            / "paired-judge-records"
            / batch["batch_id"]
            / f"slot-{slot}.json"
        )
        record_path.unlink()
        input_root = self.out / "paired-judge-inputs" / batch["batch_id"]
        payload = CORE.read_json(input_root / f"slot-{slot}.input.json")
        receipt_path = input_root / f"slot-{slot}.receipt.json"
        receipt = CORE.read_json(receipt_path)
        with mock.patch.object(RUNNER.V04, "run_streamed") as semantic_call:
            promoted = RUNNER._promote_judge(
                batch=batch,
                contract=self.contracts[batch["case_id"]],
                payload=payload,
                receipt=receipt,
                receipt_path=receipt_path,
                environment={"environment_digest": "judge-env-1"},
                out_dir=self.out,
                slot=slot,
            )
        self.assertIsNotNone(promoted)
        self.assertEqual(promoted["verdict"], records[0]["verdict"])
        self.assertEqual(
            promoted["judge_attempt"]["attempt_digest"],
            records[0]["judge_attempt"]["attempt_digest"],
        )
        semantic_call.assert_not_called()
        self.assertEqual(CORE.attempt_usage(self.out)["paired_judge_calls"], 2)

    @unittest.skipUnless(platform.system() == "Darwin", "macOS sandbox contract")
    def test_v06_semantic_profile_binds_native_sandbox_without_model_call(self) -> None:
        auth_source = self.root / "auth.json"
        auth_source.write_text("{}", encoding="utf-8")
        manifests = {}
        for arm_id in CORE.ARM_IDS:
            arm_root = self.root / "runtime-arms" / arm_id
            package = arm_root / "package"
            codex_home = arm_root / "codex-home"
            execution = arm_root / "project"
            for path in (package, codex_home, execution):
                path.mkdir(parents=True, exist_ok=True)
            (package / "sentinel.txt").write_text(arm_id, encoding="utf-8")
            manifests[arm_id] = {
                "arm_id": arm_id,
                "host": {"home": str(codex_home), "execution_root": str(execution)},
                "package": {"root": str(package)},
            }
        judge_home = self.root / "sandbox-judge" / "codex-home"
        process_home = self.root / "sandbox-judge" / "process-home"
        cwd = self.root / "sandbox-judge" / "workspace"
        answer_path = self.out / "sandbox-probe" / "answer.json"
        for path in (judge_home, process_home, cwd, answer_path.parent):
            path.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update({"CODEX_HOME": str(judge_home), "HOME": str(process_home)})
        bound, receipt_ref = RUNNER._semantic_profile(
            role="judge",
            identifier="sandbox-zero-model",
            attempt=1,
            slot=1,
            answer_path=answer_path,
            cwd=cwd,
            env=env,
            command=["codex", "--version"],
            out_dir=self.out,
            manifests=manifests,
            auth_source=auth_source,
        )
        self.assertEqual(bound[:2], ["/usr/bin/sandbox-exec", "-f"])
        receipt = CORE.read_json(Path(receipt_ref["path"]))
        self.assertTrue(receipt["semantic_process_profile_applied"])
        self.assertEqual(receipt["sandboxed_runtime_probe"]["returncode"], 0)

    def test_disagreement_accumulates_and_post_adjudication_uses_current_ledger(self) -> None:
        previous = self.committed_batch(1, None, supported=True)
        self.committed_batch(2, previous, supported=True, disagreement=True)
        first = CORE.analyze_run(
            out_dir=self.out,
            protocol_path=self.protocol_path,
            lock_path=self.lock_path,
        )
        self.assertEqual(first["status"], "partial-committed")
        self.assertEqual(first["next_batch_index"], 3)
        self.assertEqual(len(first["unresolved_disagreements"]), 1)
        packet_path = Path(first["unresolved_disagreements"][0]["packet_path"])
        packet = CORE.read_json(packet_path)
        adjudication = {
            "schema_version": CORE.ADJUDICATION_SCHEMA,
            "packet_digest": packet["packet_digest"],
            "adjudicator": "William",
            "resolutions": [
                {"candidate_id": item["candidate_id"], "axis": item["axis"], "value": item["judge_1"]}
                for item in packet["disputes"]
            ],
        }
        adjudication["adjudication_digest"] = CORE.canonical_sha256(adjudication)
        CORE.write_atomic_json(self.out / "adjudications" / "002.json", adjudication)
        resumed = CORE.analyze_run(
            out_dir=self.out,
            protocol_path=self.protocol_path,
            lock_path=self.lock_path,
        )
        self.assertEqual(resumed["status"], "partial-committed")
        self.assertEqual(resumed["committed_batches"], 2)
        self.assertEqual(resumed["next_batch_index"], 3)

    def test_human_adjudication_is_requested_once_after_all_batches(self) -> None:
        previous = None
        for index in range(1, 25):
            previous = self.committed_batch(
                index,
                previous,
                supported=True,
                disagreement=index == 2,
            )
        report = CORE.analyze_run(
            out_dir=self.out,
            protocol_path=self.protocol_path,
            lock_path=self.lock_path,
        )
        self.assertEqual(report["status"], "human-adjudication-required")
        self.assertIsNone(report["next_batch_index"])
        self.assertEqual(len(report["unresolved_disagreements"]), 1)

    def test_supported_synthetic_run_reaches_route_supported(self) -> None:
        previous = None
        for index in range(1, 25):
            previous = self.committed_batch(index, previous, supported=True)
        report = CORE.analyze_run(
            out_dir=self.out,
            protocol_path=self.protocol_path,
            lock_path=self.lock_path,
        )
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["outcome"], "route-supported")
        self.assertEqual(report["failed_gates"], [])

    def test_failed_benefit_reaches_route_rejected_not_invalid(self) -> None:
        previous = None
        for index in range(1, 25):
            previous = self.committed_batch(index, previous, supported=False)
        report = CORE.analyze_run(
            out_dir=self.out,
            protocol_path=self.protocol_path,
            lock_path=self.lock_path,
        )
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["outcome"], "route-rejected")
        self.assertIn("kernel_absolute", report["failed_gates"])

    def test_semantic_success_with_excess_cost_is_route_rejected(self) -> None:
        previous = None
        for index in range(1, 25):
            previous = self.committed_batch(
                index, previous, supported=True, burdened=True
            )
        report = CORE.analyze_run(
            out_dir=self.out,
            protocol_path=self.protocol_path,
            lock_path=self.lock_path,
        )
        self.assertEqual(report["outcome"], "route-rejected")
        self.assertIn("material_cost_value", report["failed_gates"])
        self.assertIn("input_guardrail_vs_stable", report["failed_gates"])
        self.assertIn("wall_guardrail_vs_stable", report["failed_gates"])

    def test_corrupt_hash_chain_is_experiment_infrastructure_failure(self) -> None:
        self.committed_batch(1, None, supported=True)
        path = self.out / "batch-commits" / "001.json"
        commit = CORE.read_json(path)
        commit["previous_commit_digest"] = "wrong"
        commit["commit_digest"] = CORE.canonical_sha256({key: value for key, value in commit.items() if key != "commit_digest"})
        CORE.write_atomic_json(path, commit)
        with self.assertRaises(CORE.DecisionError) as raised:
            CORE.analyze_run(
                out_dir=self.out,
                protocol_path=self.protocol_path,
                lock_path=self.lock_path,
            )
        self.assertEqual(raised.exception.code, "ledger-corruption")

    def test_pending_authorization_blocks_semantic_calls(self) -> None:
        pending_path = self.root / "pending.json"
        CORE.build_pending_authorization(
            protocol_path=self.protocol_path,
            lock_path=self.lock_path,
            output_path=pending_path,
        )
        report = CORE.validate_authorization(
            authorization_path=pending_path,
            protocol_path=self.protocol_path,
            lock_path=self.lock_path,
        )
        self.assertFalse(report["semantic_calls_authorized"])
        with self.assertRaises(CORE.DecisionError) as raised:
            CORE.validate_authorization(
                authorization_path=pending_path,
                protocol_path=self.protocol_path,
                lock_path=self.lock_path,
                require_active=True,
            )
        self.assertEqual(raised.exception.code, "authorization-missing")

    def test_preflight_encodes_old_failure_regressions(self) -> None:
        report = CORE.deterministic_preflight(
            protocol_path=self.protocol_path, lock_path=self.lock_path
        )
        self.assertEqual(report["model_calls"], 0)
        self.assertFalse(report["native_first_useful_timestamp_required"])
        self.assertFalse(report["first_observable_action_required"])
        self.assertFalse(report["pre_run_usage_snapshot_required"])
        self.assertEqual(report["paired_judge_calls"], 48)


if __name__ == "__main__":
    unittest.main()

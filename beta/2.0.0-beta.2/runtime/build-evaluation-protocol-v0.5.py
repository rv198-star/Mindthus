#!/usr/bin/env python3
"""Build the incremental filesystem-isolated Beta.2 protocol v0.5."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
V04_BUILDER = BETA_ROOT / "runtime" / "build-evaluation-protocol-v0.4.py"
DEFAULT_OUT = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.json"
V04_PROTOCOL_SHA256 = "a6e9da7ef2eb85e179d92ec909444c50e879673943b1be71f5c923b9e26d0746"
V04_LOCK_DIGEST = "dc00e9564e655ae202a543f8719d40e9ad23858cf508a1889187bd4591fae62b"
PRIOR_GENERATION_CALLS = 146
PRIOR_JUDGE_CALLS = 42
PRIOR_COUNTED_TOKENS = 8_133_510
FULL_V05_GENERATION_CEILING = 239
FULL_V05_JUDGE_CEILING = 480
FULL_V05_TOKEN_CEILING = 22_000_000


def load_v04() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "mindthus_beta2_protocol_v04_builder", V04_BUILDER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load v0.4 protocol builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dependency(identifier: str, relative: str) -> dict[str, Any]:
    path = REPO_ROOT / relative
    return {
        "id": identifier,
        "path": relative,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "acceptance_issue": 119,
    }


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()


def payload() -> dict[str, Any]:
    v04 = load_v04()
    protocol = v04.payload()
    protocol["protocol_version"] = "0.5"
    protocol["purpose"] = (
        "Re-run the 25 visible Codex cases under filesystem-enforced arm isolation and "
        "close evidence after each case/repeat three-arm triplet. Each batch generates "
        "three outputs, proves isolation, obtains six blinded Judge records, and writes "
        "one atomic commit before any later batch may start."
    )
    protocol["dependencies"].extend(
        [
            dependency(
                "visible_protocol_v04_validator",
                "beta/2.0.0-beta.2/runtime/freeze-evaluation-protocol-v0.4.py",
            ),
            dependency(
                "filesystem_isolation_v05",
                "beta/2.0.0-beta.2/runtime/filesystem_isolation_v05.py",
            ),
            dependency(
                "real_arm_materializer_v05",
                "beta/2.0.0-beta.2/runtime/materialize-real-codex-arm-v05.py",
            ),
            dependency(
                "real_evaluation_runner_v05",
                "beta/2.0.0-beta.2/runtime/run_real_codex_evaluation_v05.py",
            ),
            dependency(
                "incremental_analyzer_v05",
                "beta/2.0.0-beta.2/runtime/analyze_incremental_v05.py",
            ),
            dependency(
                "incremental_dry_run_v05",
                "beta/2.0.0-beta.2/runtime/dry-run-incremental-v05.py",
            ),
        ]
    )

    design = protocol["execution_design"]
    design["generator_environment"] = (
        "one sealed arm home and empty execution root under a native macOS Sandbox profile"
    )
    design["judge_environment"] = (
        "separate Mindthus-free and Superpowers-free home under a native macOS Sandbox profile"
    )
    design["incremental_batch_control"] = {
        "batch_unit": "case_id/repeat three-arm triplet",
        "batch_count": 75,
        "generation_outputs_per_batch": 3,
        "judge_records_per_batch": 6,
        "order": [
            "generate-three-arms",
            "verify-three-filesystem-isolation-receipts",
            "judge-each-output-in-two-isolated-sessions",
            "write-one-hash-chained-atomic-batch-commit",
            "advance-to-next-batch",
        ],
        "counting_rule": "only this record makes the batch artifacts count when the final batch commit validates",
        "partial_batch_rule": "retain for audit, exclude from every comparison denominator",
        "resume_rule": "validate the commit hash chain, then resume the first uncommitted batch",
        "smoke_gate": "the first five preregistered smoke triplets are already Judge-backed before continuation",
        "full_result_gate": "no architecture or non-inferiority conclusion before all 75 commits and endpoint denominators pass",
    }
    design["filesystem_isolation"] = {
        "enforcement": "macOS sandbox-exec applied to every generator and Judge semantic process",
        "protected_user_data_roots": ["/Volumes/Data", "current user home"],
        "allow_rule": "reopen only the current execution root, current installed package, isolated homes, current output mailbox, and exact auth/schema files",
        "pre_call_probes": [
            "positive-own-root-read",
            "negative-evaluation-control-read",
            "negative-other-arm-read",
            "negative-parent-traversal-read",
            "negative-symlink-escape-read",
        ],
        "staging_policy": "builder package staging is deleted before any semantic model call",
        "evidence": "exact profile digest, sandboxed command digest, and native probe receipt per semantic attempt",
        "command_string_as_access_proof": "forbidden",
        "failure_action": "stop before or at the affected attempt; never classify a denied access attempt as contamination",
    }
    design["v05_prior_output_accounting"] = {
        "v04_protocol_sha256": V04_PROTOCOL_SHA256,
        "v04_lock_digest": V04_LOCK_DIGEST,
        "v03_and_v04_generation_attempts": PRIOR_GENERATION_CALLS,
        "v04_judge_attempts": PRIOR_JUDGE_CALLS,
        "v03_and_v04_counted_tokens": PRIOR_COUNTED_TOKENS,
        "v04_completed_generation_outputs": 143,
        "v04_retained_judge_records": 36,
        "v04_valid_comparison_records": 0,
        "retention": "immutable descriptive audit artifacts only; excluded from v0.5 identities, commits, estimates, and denominators",
        "fresh_output_rule": "every v0.5 cell uses the new protocol digest and must be regenerated under enforced isolation",
    }

    workload = protocol["workload"]
    workload["incremental_batch_count"] = 75
    workload["smoke_batch_count"] = 5
    workload["batch_generation_outputs"] = 3
    workload["batch_judge_records"] = 6
    workload["smoke_outputs_count_toward_matched"] = True

    protocol["missing_data_policy"]["partial_batch"] = (
        "retain every attempt and record, but include none of the batch in a comparison "
        "until its three generation records, three isolation receipts, six Judge records, "
        "and final hash-chained commit all validate"
    )
    protocol["rerun_policy"]["prior_version_output"] = (
        "retain v0.3/v0.4 artifacts as descriptive audit history and exclude them from "
        "v0.5; never promote an output that lacked the v0.5 filesystem receipt"
    )
    protocol["vetoes"].extend(
        [
            {
                "id": "filesystem-isolation-unavailable",
                "condition": "sandbox-exec is unavailable, the exact profile cannot be applied, staging survives, or any native positive/negative/canonical probe differs",
                "action": "stop before the semantic call and retain the receipt",
            },
            {
                "id": "incremental-batch-integrity-failure",
                "condition": "batch cardinality, record digest, Judge count, previous-commit link, or commit digest differs",
                "action": "stop; retain the current uncommitted batch and preserve every earlier valid commit",
            },
        ]
    )

    authorization = protocol["authorization_parameters"]
    authorization["status"] = "fresh-v0.5-authorization-required"
    authorization["planned_incremental_batches"] = 75
    authorization["fresh_authorization_required"] = True
    authorization["delegated_digest_binding_allowed"] = False
    authorization["delegated_digest_binding_rule"] = (
        "v0.4 authority does not transfer because v0.5 changes isolation, ordering, "
        "batch commits, spend cadence, and protocol digest"
    )
    proposed = authorization["proposed_authorization"]
    proposed["maximum_generation_calls"] = FULL_V05_GENERATION_CEILING
    proposed["maximum_judge_calls"] = FULL_V05_JUDGE_CEILING
    proposed["token_or_cost_budget"]["maximum"] = FULL_V05_TOKEN_CEILING
    proposed["maximum_committed_batches"] = 75
    authorization["initial_batch_authorization_recommendation"] = {
        "maximum_committed_batches": 5,
        "maximum_generation_calls": 17,
        "maximum_judge_calls": 34,
        "aggregate_token_ceiling": 3_000_000,
        "result": "five Judge-backed smoke triplets, not an architecture conclusion",
        "continuation": "a later authorization may raise the batch ceiling under the same frozen protocol after reviewing committed evidence",
    }
    authorization["cumulative_authority"] = {
        "prior_consumption": {
            "protocol_versions": ["0.3", "0.4"],
            "generation_calls": PRIOR_GENERATION_CALLS,
            "judge_calls": PRIOR_JUDGE_CALLS,
            "counted_tokens": PRIOR_COUNTED_TOKENS,
        },
        "requested_full_v05_increment": {
            "maximum_generation_calls": FULL_V05_GENERATION_CEILING,
            "maximum_judge_calls": FULL_V05_JUDGE_CEILING,
            "aggregate_token_ceiling": FULL_V05_TOKEN_CEILING,
        },
        "requested_full_cumulative_ceiling": {
            "maximum_generation_calls": PRIOR_GENERATION_CALLS + FULL_V05_GENERATION_CEILING,
            "maximum_judge_calls": PRIOR_JUDGE_CALLS + FULL_V05_JUDGE_CEILING,
            "aggregate_token_ceiling": PRIOR_COUNTED_TOKENS + FULL_V05_TOKEN_CEILING,
        },
        "budget_expansion": True,
        "authorization_state": "pending-human-choice",
    }

    freeze = protocol["freeze"]
    freeze["source_parent_commit"] = git_head()
    freeze["semantic_model_output_generated_under_v0_5_before_freeze"] = False
    freeze["prior_semantic_output_scope"] = (
        "v0.3 and v0.4 artifacts are retained and excluded; no semantic output was "
        "generated under the v0.5 protocol digest before freeze"
    )
    protocol["rejected_alternatives"].extend(
        [
            {
                "alternative": "generate all 225 outputs before the first matched Judge",
                "reason": "it delays semantic evidence until after most spend and made v0.4 stop with zero matched Judge records",
            },
            {
                "alternative": "keep extending command-string contamination selectors",
                "reason": "command syntax is neither canonical filesystem access evidence nor an upstream isolation boundary",
            },
            {
                "alternative": "reuse v0.4 outputs under the new batch controller",
                "reason": "one smoke and six matched cells already violated the frozen parent-traversal contract; promotion would manufacture isolation evidence",
            },
        ]
    )
    return protocol


def main() -> int:
    DEFAULT_OUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUT.write_text(
        json.dumps(payload(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(DEFAULT_OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

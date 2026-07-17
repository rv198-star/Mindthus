#!/usr/bin/env python3
"""Validate generic TVG atlas trace shape, lineage, and optional file hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "tvg-atlas-trace-v1"
SCRIPT_BOUNDARY = "support_only_agentic_audit_required"
PROFILE_SOURCE_MODES = {"default", "supplied", "inferred-with-warning"}
SEARCH_TERMINAL_GATES = {"search-freeze", "search-freeze-with-review-bound-warning"}
SEARCH_GATES = SEARCH_TERMINAL_GATES | {"return-remediate", "blocked"}
DELIVERY_RESULTS = {
    "ready-for-user-selection",
    "ready-for-user-selection-with-warning",
    "return-remediate",
    "blocked",
}
READY_DELIVERY_RESULTS = {
    "ready-for-user-selection",
    "ready-for-user-selection-with-warning",
}
FINALIZATION_STATES = {"pending-user-selection", "skipped", "completed"}
FINALIZATION_MODES = {
    "accept-tile",
    "rerender-selected",
    "rerender-selected-plus-backup",
}
ROUND_ID_PATTERN = re.compile(r"^R[0-9]{2}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_string(errors: list[str], value: Any, path: str) -> None:
    if not _nonempty(value):
        errors.append(f"{path}: expected a non-empty string")


def _string_list(
    errors: list[str], value: Any, path: str, *, minimum: int = 0
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{path}: expected a list")
        return []
    strings: list[str] = []
    for index, item in enumerate(value):
        if not _nonempty(item):
            errors.append(f"{path}[{index}]: expected a non-empty string")
        else:
            strings.append(item)
    if len(value) < minimum:
        errors.append(f"{path}: expected at least {minimum} item(s)")
    return strings


def _resolve(base_dir: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base_dir / path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_file_reference(
    errors: list[str],
    base_dir: Path,
    value: Any,
    expected_hash: Any,
    path: str,
    hash_path: str | None = None,
) -> None:
    hash_path = hash_path or f"{path}_sha256"
    _require_string(errors, value, path)
    if not _nonempty(expected_hash) or not SHA256_PATTERN.fullmatch(str(expected_hash)):
        errors.append(f"{hash_path}: expected a lowercase SHA-256 hex string")
        return
    if not _nonempty(value):
        return
    resolved = _resolve(base_dir, value)
    if not resolved.is_file():
        errors.append(f"{path}: file not found: {resolved}")
        return
    if _sha256(resolved) != expected_hash:
        errors.append(f"{hash_path}: hash does not match {resolved}")


def _validate_generation(
    errors: list[str], generation: Any, path: str, base_dir: Path, check_files: bool
) -> None:
    if not isinstance(generation, dict):
        errors.append(f"{path}: expected an object")
        return
    pairs = (
        ("prompt_path", "prompt_sha256"),
        ("raw_atlas_path", "raw_atlas_sha256"),
        ("labeled_atlas_path", "labeled_atlas_sha256"),
    )
    for file_key, hash_key in pairs:
        if check_files:
            _validate_file_reference(
                errors,
                base_dir,
                generation.get(file_key),
                generation.get(hash_key),
                f"{path}.{file_key}",
                f"{path}.{hash_key}",
            )
        else:
            _require_string(errors, generation.get(file_key), f"{path}.{file_key}")
            sha = generation.get(hash_key)
            if not _nonempty(sha) or not SHA256_PATTERN.fullmatch(str(sha)):
                errors.append(f"{path}.{hash_key}: expected a lowercase SHA-256 hex string")


def _validate_delivery_generation(
    errors: list[str],
    generation: Any,
    generation_mode: Any,
    path: str,
    base_dir: Path,
    check_files: bool,
) -> None:
    if generation_mode == "regenerated":
        _validate_generation(errors, generation, path, base_dir, check_files)
        return
    if not isinstance(generation, dict):
        errors.append(f"{path}: expected an object")
        return
    pairs = (
        ("composition_manifest_path", "composition_manifest_sha256"),
        ("raw_atlas_path", "raw_atlas_sha256"),
        ("labeled_atlas_path", "labeled_atlas_sha256"),
    )
    for file_key, hash_key in pairs:
        if check_files:
            _validate_file_reference(
                errors,
                base_dir,
                generation.get(file_key),
                generation.get(hash_key),
                f"{path}.{file_key}",
                f"{path}.{hash_key}",
            )
        else:
            _require_string(errors, generation.get(file_key), f"{path}.{file_key}")
            sha = generation.get(hash_key)
            if not _nonempty(sha) or not SHA256_PATTERN.fullmatch(str(sha)):
                errors.append(f"{path}.{hash_key}: expected a lowercase SHA-256 hex string")


def _validate_profile(
    errors: list[str], snapshot: Any, base_dir: Path, check_files: bool
) -> None:
    if not isinstance(snapshot, dict):
        errors.append("profile_snapshot: expected an object")
        return
    for key in ("name", "version"):
        _require_string(errors, snapshot.get(key), f"profile_snapshot.{key}")
    if check_files:
        _validate_file_reference(
            errors,
            base_dir,
            snapshot.get("path"),
            snapshot.get("sha256"),
            "profile_snapshot.path",
            "profile_snapshot.sha256",
        )
    else:
        _require_string(errors, snapshot.get("path"), "profile_snapshot.path")
        sha = snapshot.get("sha256")
        if not _nonempty(sha) or not SHA256_PATTERN.fullmatch(str(sha)):
            errors.append("profile_snapshot.sha256: expected a lowercase SHA-256 hex string")
    if snapshot.get("source_mode") not in PROFILE_SOURCE_MODES:
        errors.append(
            f"profile_snapshot.source_mode: expected one of {sorted(PROFILE_SOURCE_MODES)}"
        )
    if snapshot.get("fixed_for_run") is not True:
        errors.append("profile_snapshot.fixed_for_run: expected true")
    adapters = snapshot.get("adapters")
    if not isinstance(adapters, list):
        errors.append("profile_snapshot.adapters: expected a list")
        return
    adapter_names: list[str] = []
    for index, adapter in enumerate(adapters):
        path = f"profile_snapshot.adapters[{index}]"
        if not isinstance(adapter, dict):
            errors.append(f"{path}: expected an object")
            continue
        name = adapter.get("name")
        _require_string(errors, name, f"{path}.name")
        if _nonempty(name):
            adapter_names.append(name)
        if check_files:
            _validate_file_reference(
                errors,
                base_dir,
                adapter.get("path"),
                adapter.get("sha256"),
                f"{path}.path",
                f"{path}.sha256",
            )
        else:
            _require_string(errors, adapter.get("path"), f"{path}.path")
            sha = adapter.get("sha256")
            if not _nonempty(sha) or not SHA256_PATTERN.fullmatch(str(sha)):
                errors.append(f"{path}.sha256: expected a lowercase SHA-256 hex string")
    if len(adapter_names) != len(set(adapter_names)):
        errors.append("profile_snapshot.adapters: adapter names must be unique")


def _validate_region(errors: list[str], region: Any, path: str, index: int, columns: int) -> None:
    expected = {"row": index // columns + 1, "column": index % columns + 1}
    if region != expected:
        errors.append(f"{path}: expected row-major region {expected}")


def _validate_parent_reviews(
    errors: list[str], reviews: Any, selected_ids: list[str], gate: Any, path: str
) -> None:
    if not isinstance(reviews, list):
        errors.append(f"{path}: expected a list")
        return
    if len(reviews) != 3:
        errors.append(f"{path}: expected exactly 3 parent reviews")
    review_ids: list[str] = []
    for index, review in enumerate(reviews):
        item_path = f"{path}[{index}]"
        if not isinstance(review, dict):
            errors.append(f"{item_path}: expected an object")
            continue
        candidate_id = review.get("candidate_id")
        if _nonempty(candidate_id):
            review_ids.append(candidate_id)
        else:
            errors.append(f"{item_path}.candidate_id: expected a non-empty string")
        _string_list(errors, review.get("preserve"), f"{item_path}.preserve", minimum=1)
        _string_list(errors, review.get("repair"), f"{item_path}.repair", minimum=1)
        next_gain = review.get("next_gain_hypothesis")
        exit_rationale = review.get("exit_rationale")
        if gate == "return-remediate":
            _require_string(errors, next_gain, f"{item_path}.next_gain_hypothesis")
            if exit_rationale is not None:
                errors.append(f"{item_path}.exit_rationale: remediation requires null")
        elif gate in SEARCH_GATES:
            if next_gain is not None:
                errors.append(f"{item_path}.next_gain_hypothesis: terminal search gate requires null")
            _require_string(errors, exit_rationale, f"{item_path}.exit_rationale")
    if review_ids != selected_ids:
        errors.append(f"{path}: candidate IDs must match selected-parent order")


def validate_trace(payload: Any, base_dir: Path, check_files: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["root: expected an object"]
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version: expected {SCHEMA_VERSION!r}")
    _validate_profile(errors, payload.get("profile_snapshot"), base_dir, check_files)
    _require_string(errors, payload.get("task_prompt"), "task_prompt")
    tvg_pressure = payload.get("tvg_pressure")
    if not isinstance(tvg_pressure, int) or isinstance(tvg_pressure, bool) or not 1 <= tvg_pressure <= 5:
        errors.append("tvg_pressure: expected an integer from 1 to 5")
    _require_string(errors, payload.get("claim_ceiling"), "claim_ceiling")
    warnings = _string_list(errors, payload.get("evidence_warnings"), "evidence_warnings")

    run_evidence = payload.get("run_evidence")
    if not isinstance(run_evidence, dict):
        errors.append("run_evidence: expected an object")
    else:
        _require_string(errors, run_evidence.get("model_path"), "run_evidence.model_path")
        manifest = run_evidence.get("prompt_manifest_path")
        _require_string(errors, manifest, "run_evidence.prompt_manifest_path")
        if check_files and _nonempty(manifest) and not _resolve(base_dir, manifest).is_file():
            errors.append(f"run_evidence.prompt_manifest_path: file not found: {_resolve(base_dir, manifest)}")

    rounds = payload.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        errors.append("rounds: expected a non-empty list")
        rounds = []

    previous_selected: list[str] | None = None
    final_selected: list[str] = []
    final_gate: str | None = None
    has_post_hoc_intent = False
    for round_index, record in enumerate(rounds):
        round_path = f"rounds[{round_index}]"
        if not isinstance(record, dict):
            errors.append(f"{round_path}: expected an object")
            previous_selected = []
            continue
        expected_round_id = f"R{round_index:02d}"
        round_id = record.get("round_id")
        if round_id != expected_round_id or not ROUND_ID_PATTERN.fullmatch(str(round_id)):
            errors.append(f"{round_path}.round_id: expected {expected_round_id!r}")
            round_id = expected_round_id
        expected_stage = "initial" if round_index == 0 else "expand"
        if record.get("stage") != expected_stage:
            errors.append(f"{round_path}.stage: expected {expected_stage!r}")
        if record.get("layout") != "3x3":
            errors.append(f"{round_path}.layout: expected '3x3'")
        _validate_generation(
            errors, record.get("generation"), f"{round_path}.generation", base_dir, check_files
        )

        candidates = record.get("candidates")
        if not isinstance(candidates, list):
            errors.append(f"{round_path}.candidates: expected a list")
            candidates = []
        if len(candidates) != 9:
            errors.append(f"{round_path}.candidates: expected exactly 9 candidates")
        candidate_ids: list[str] = []
        for index, candidate in enumerate(candidates):
            candidate_path = f"{round_path}.candidates[{index}]"
            if not isinstance(candidate, dict):
                errors.append(f"{candidate_path}: expected an object")
                continue
            expected_id = f"{round_id}-E{index + 1:02d}"
            candidate_id = candidate.get("id")
            candidate_ids.append(candidate_id if isinstance(candidate_id, str) else "")
            if candidate_id != expected_id:
                errors.append(f"{candidate_path}.id: expected {expected_id!r}")
            _validate_region(errors, candidate.get("region"), f"{candidate_path}.region", index, 3)
            _string_list(
                errors, candidate.get("audit_findings"), f"{candidate_path}.audit_findings", minimum=1
            )
            if round_index == 0:
                if candidate.get("parent_candidate_id") is not None:
                    errors.append(f"{candidate_path}.parent_candidate_id: initial candidates require null")
                _require_string(
                    errors, candidate.get("exploration_intent"), f"{candidate_path}.exploration_intent"
                )
                intent_source = candidate.get("intent_source")
                if intent_source not in {"predeclared", "post-hoc-with-warning"}:
                    errors.append(
                        f"{candidate_path}.intent_source: expected 'predeclared' or 'post-hoc-with-warning'"
                    )
                has_post_hoc_intent = has_post_hoc_intent or intent_source == "post-hoc-with-warning"
            else:
                expected_parent = (
                    previous_selected[index // 3]
                    if previous_selected and len(previous_selected) == 3
                    else None
                )
                if candidate.get("parent_candidate_id") != expected_parent:
                    errors.append(
                        f"{candidate_path}.parent_candidate_id: row lineage must map to {expected_parent!r}"
                    )
                _require_string(errors, candidate.get("gain_move"), f"{candidate_path}.gain_move")
                _require_string(
                    errors,
                    candidate.get("positive_value_hypothesis"),
                    f"{candidate_path}.positive_value_hypothesis",
                )

        selection = record.get("selection")
        if not isinstance(selection, dict):
            errors.append(f"{round_path}.selection: expected an object")
            selected_ids: list[str] = []
            gate = None
        else:
            selected_ids = _string_list(
                errors,
                selection.get("selected_candidate_ids"),
                f"{round_path}.selection.selected_candidate_ids",
            )
            if len(selected_ids) != 3 or len(set(selected_ids)) != 3:
                errors.append(f"{round_path}.selection.selected_candidate_ids: expected 3 distinct IDs")
            unknown = [item for item in selected_ids if item not in candidate_ids]
            if unknown:
                errors.append(f"{round_path}.selection.selected_candidate_ids: unknown IDs {unknown}")
            _require_string(
                errors, selection.get("selection_reason"), f"{round_path}.selection.selection_reason"
            )
            gate = selection.get("gate_result")
            if gate not in SEARCH_GATES:
                errors.append(f"{round_path}.selection.gate_result: expected one of {sorted(SEARCH_GATES)}")
            _validate_parent_reviews(
                errors,
                selection.get("parent_reviews"),
                selected_ids,
                gate,
                f"{round_path}.selection.parent_reviews",
            )
            next_round = selection.get("next_round_positive_value_hypothesis")
            if gate == "return-remediate":
                _require_string(
                    errors,
                    next_round,
                    f"{round_path}.selection.next_round_positive_value_hypothesis",
                )
            elif next_round is not None:
                errors.append(
                    f"{round_path}.selection.next_round_positive_value_hypothesis: terminal search gate requires null"
                )
        if round_index < len(rounds) - 1 and gate != "return-remediate":
            errors.append(f"{round_path}: a following round requires return-remediate")
        previous_selected = selected_ids
        final_selected = selected_ids
        final_gate = gate

    if has_post_hoc_intent:
        if final_gate == "search-freeze":
            errors.append("post-hoc R00 intent requires search-freeze-with-review-bound-warning")
        if not warnings:
            errors.append("evidence_warnings: post-hoc R00 intent requires a recorded warning")

    delivery = payload.get("delivery")
    delivery_result: str | None = None
    delivery_ids: list[str] = []
    has_delivery_veto = False
    if delivery is None and final_gate == "blocked":
        pass
    elif not isinstance(delivery, dict):
        errors.append("delivery: expected an object after a search-freeze gate")
    else:
        if final_gate not in SEARCH_TERMINAL_GATES:
            errors.append("delivery requires the final round to reach a search-freeze gate")
        if delivery.get("mode") != "shortlist":
            errors.append("delivery.mode: expected 'shortlist'")
        if delivery.get("layout") != "2x2":
            errors.append("delivery.layout: expected '2x2'")
        generation_mode = delivery.get("generation_mode")
        if generation_mode not in {"regenerated", "deterministic-compose"}:
            errors.append("delivery.generation_mode: expected 'regenerated' or 'deterministic-compose'")
        if generation_mode in {"regenerated", "deterministic-compose"}:
            _validate_delivery_generation(
                errors,
                delivery.get("generation"),
                generation_mode,
                "delivery.generation",
                base_dir,
                check_files,
            )
        candidates = delivery.get("candidates")
        if not isinstance(candidates, list):
            errors.append("delivery.candidates: expected a list")
            candidates = []
        if len(candidates) != 4:
            errors.append("delivery.candidates: expected exactly 4 candidates")
        for index, candidate in enumerate(candidates):
            path = f"delivery.candidates[{index}]"
            if not isinstance(candidate, dict):
                errors.append(f"{path}: expected an object")
                continue
            expected_id = f"S{index + 1:02d}"
            delivery_ids.append(expected_id)
            if candidate.get("id") != expected_id:
                errors.append(f"{path}.id: expected {expected_id!r}")
            _validate_region(errors, candidate.get("region"), f"{path}.region", index, 2)
            sources = _string_list(
                errors, candidate.get("source_candidate_ids"), f"{path}.source_candidate_ids", minimum=1
            )
            unknown = [source for source in sources if source not in final_selected]
            if unknown:
                errors.append(f"{path}.source_candidate_ids: unknown final-round IDs {unknown}")
            _require_string(errors, candidate.get("prompt_delta_summary"), f"{path}.prompt_delta_summary")
            _string_list(errors, candidate.get("audit_findings"), f"{path}.audit_findings", minimum=1)
            vetoes = _string_list(
                errors, candidate.get("veto_findings"), f"{path}.veto_findings"
            )
            has_delivery_veto = has_delivery_veto or bool(vetoes)

        audit = delivery.get("delivery_audit")
        if not isinstance(audit, dict):
            errors.append("delivery.delivery_audit: expected an object")
        else:
            delivery_result = audit.get("result")
            if delivery_result not in DELIVERY_RESULTS:
                errors.append(f"delivery.delivery_audit.result: expected one of {sorted(DELIVERY_RESULTS)}")
            _require_string(errors, audit.get("rationale"), "delivery.delivery_audit.rationale")
            if audit.get("audit_role") != "agentic":
                errors.append("delivery.delivery_audit.audit_role: expected 'agentic'")
            _string_list(errors, audit.get("warnings"), "delivery.delivery_audit.warnings")
            if delivery_result in READY_DELIVERY_RESULTS and has_delivery_veto:
                errors.append("ready delivery audit requires no candidate veto findings")

    finalization = payload.get("finalization")
    if not isinstance(finalization, dict):
        errors.append("finalization: expected an object")
    else:
        state = finalization.get("state")
        if state not in FINALIZATION_STATES:
            errors.append(f"finalization.state: expected one of {sorted(FINALIZATION_STATES)}")
        mode = finalization.get("mode")
        selected = _string_list(
            errors, finalization.get("selected_shortlist_ids"), "finalization.selected_shortlist_ids"
        )
        outputs = finalization.get("outputs")
        if not isinstance(outputs, list):
            errors.append("finalization.outputs: expected a list")
            outputs = []
        if state == "pending-user-selection":
            if delivery_result not in READY_DELIVERY_RESULTS:
                errors.append("pending-user-selection requires a ready delivery audit")
            if mode is not None or selected or outputs:
                errors.append("pending-user-selection requires null mode, no selections, and no outputs")
            _require_string(errors, finalization.get("reason"), "finalization.reason")
        elif state == "skipped":
            if mode is not None or selected or outputs:
                errors.append("skipped finalization requires null mode, no selections, and no outputs")
            if final_gate == "blocked" and delivery is not None:
                errors.append("blocked search must not produce a delivery board")
            _require_string(errors, finalization.get("reason"), "finalization.reason")
        elif state == "completed":
            if delivery_result not in READY_DELIVERY_RESULTS:
                errors.append("completed finalization requires a ready delivery audit")
            if mode not in FINALIZATION_MODES:
                errors.append(f"finalization.mode: expected one of {sorted(FINALIZATION_MODES)}")
            if not selected:
                errors.append("finalization.selected_shortlist_ids: completed finalization requires a selection")
            unknown = [item for item in selected if item not in delivery_ids]
            if unknown:
                errors.append(f"finalization.selected_shortlist_ids: unknown IDs {unknown}")
            if not outputs:
                errors.append("finalization.outputs: completed finalization requires output evidence")
            for index, output in enumerate(outputs):
                path = f"finalization.outputs[{index}]"
                if not isinstance(output, dict):
                    errors.append(f"{path}: expected an object")
                    continue
                source_id = output.get("source_shortlist_id")
                _require_string(errors, source_id, f"{path}.source_shortlist_id")
                if _nonempty(source_id) and source_id not in selected:
                    errors.append(f"{path}.source_shortlist_id: must be one of the selected IDs")
                if check_files:
                    _validate_file_reference(
                        errors,
                        base_dir,
                        output.get("path"),
                        output.get("sha256"),
                        f"{path}.path",
                        f"{path}.sha256",
                    )
                else:
                    _require_string(errors, output.get("path"), f"{path}.path")
                    sha = output.get("sha256")
                    if not _nonempty(sha) or not SHA256_PATTERN.fullmatch(str(sha)):
                        errors.append(f"{path}.sha256: expected a lowercase SHA-256 hex string")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate generic TVG atlas trace shape and optional file hashes."
    )
    parser.add_argument("trace", type=Path)
    parser.add_argument("--check-files", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = json.loads(args.trace.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error: trace not found: {args.trace}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: cannot read trace: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(
            f"error: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return 2

    errors = validate_trace(payload, args.trace.parent, args.check_files)
    report = {
        "schema_version": SCHEMA_VERSION,
        "valid": not errors,
        "profile": (
            payload.get("profile_snapshot", {}).get("name")
            if isinstance(payload, dict) and isinstance(payload.get("profile_snapshot"), dict)
            else None
        ),
        "round_count": (
            len(payload.get("rounds", []))
            if isinstance(payload, dict) and isinstance(payload.get("rounds"), list)
            else 0
        ),
        "errors": errors,
        "script_boundary": SCRIPT_BOUNDARY,
        "boundary_note": (
            "Shape, references, hashes, and lineage only; candidate value, audit truth, "
            "Profile maturity, and TVG exit still require agentic judgment."
        ),
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif errors:
        print("invalid atlas trace shape:")
        for error in errors:
            print(f"- {error}")
    else:
        print("Atlas trace shape is valid; agentic TVG audit is still required.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

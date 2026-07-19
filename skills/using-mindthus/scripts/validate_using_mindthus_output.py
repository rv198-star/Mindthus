#!/usr/bin/env python3
"""Validate using-mindthus fidelity output shape."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


THIS_FILE = Path(__file__).resolve()
sys.path.insert(0, str(THIS_FILE.parents[2]))

from runtime_bootstrap import activate_runtime


def _find_whole_elephant_validator_path() -> Path:
    path_parts = THIS_FILE.parts
    candidate_roots: list[Path] = []
    for index, part in enumerate(path_parts):
        if part != "skills":
            continue
        tail = path_parts[index + 1 :]
        if tail[:1] == ("using-mindthus",) or tail[:2] == ("mindthus", "using-mindthus"):
            root_parts = path_parts[:index]
            if root_parts and root_parts[-1] == ".opencode":
                root_parts = root_parts[:-1]
            candidate_roots.append(Path(*root_parts))
    candidate_roots.extend(THIS_FILE.parents)

    seen: set[Path] = set()
    for candidate in candidate_roots:
        if candidate in seen:
            continue
        seen.add(candidate)
        validator = candidate / "scripts" / "primitives" / "whole_elephant_validator.py"
        if validator.is_file():
            return validator
    raise ImportError("Cannot locate packaged scripts/primitives import root")


def _load_whole_elephant_validator() -> object:
    validator_path = _find_whole_elephant_validator_path()
    spec = importlib.util.spec_from_file_location("mindthus_whole_elephant_validator", validator_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load whole elephant validator from {validator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


activate_runtime(THIS_FILE)
_WHOLE_ELEPHANT_VALIDATOR = _load_whole_elephant_validator()

from _runtime.core.io import load_json
from _runtime.core.report import Finding, finding
from _runtime.fidelity.core import FidelitySpec, print_text_report, validate_fidelity_output
exposes_internal_stdout = _WHOLE_ELEPHANT_VALIDATOR.exposes_internal_stdout
first_visible_sentence = _WHOLE_ELEPHANT_VALIDATOR.first_visible_sentence
looks_like_generic_not_only_caveat = _WHOLE_ELEPHANT_VALIDATOR.looks_like_generic_not_only_caveat
looks_like_local_truth_concession_first = _WHOLE_ELEPHANT_VALIDATOR.looks_like_local_truth_concession_first
looks_like_score_concession = _WHOLE_ELEPHANT_VALIDATOR.looks_like_score_concession
looks_like_soft_not_wrong_concession = _WHOLE_ELEPHANT_VALIDATOR.looks_like_soft_not_wrong_concession
validate_whole_elephant_audit = _WHOLE_ELEPHANT_VALIDATOR.validate_audit


SPEC = FidelitySpec(
    schema_version="using-mindthus-fidelity-v0.1",
    method="using-mindthus",
    report_title="using-mindthus Shape & Evidence Risk Report",
    required_moves=(
        "intervention_boundary",
        "premise_calibration",
        "constraint_separation",
        "judgment_object_routing",
        "method_arbitration",
        "execution_impact",
    ),
    action_postures=frozenset(
        {
            "direct_execute",
            "acquire_information",
            "route",
            "arbitrate",
            "transfer",
            "stop",
            "unclear",
        }
    ),
    truth_boundary="router judgment truth",
)


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _placeholder_command(value: str) -> bool:
    return "..." in value or "<" in value or ">" in value


def _validate_whole_elephant_audit(audit: object) -> list[Finding]:
    if not isinstance(audit, dict):
        return [
            finding(
                "block",
                "missing-whole-elephant-audit",
                "whole_elephant_audit is required when partial_truth_capture_triggered is true",
            )
        ]

    return [
        finding(
            "block",
            "invalid-whole-elephant-audit",
            f"whole_elephant_audit.{shape_finding}",
        )
        for shape_finding in validate_whole_elephant_audit(audit)
    ]


def _validate_whole_elephant_contract(data: object) -> list[Finding]:
    if not isinstance(data, dict) or data.get("applicability") != "applicable":
        return []

    if "partial_truth_capture_triggered" not in data:
        return [
            finding(
                "block",
                "missing-field",
                "partial_truth_capture_triggered must be explicitly true or false",
            )
        ]
    triggered = data.get("partial_truth_capture_triggered")
    if triggered is False:
        return []
    if triggered is not True:
        return [
            finding(
                "block",
                "invalid-field",
                "partial_truth_capture_triggered must be true or false",
            )
        ]

    findings = _validate_whole_elephant_audit(data.get("whole_elephant_audit"))
    conclusion = data.get("plain_language_conclusion")
    if _non_empty_string(conclusion):
        first_sentence = first_visible_sentence(conclusion)
        if looks_like_local_truth_concession_first(first_sentence):
            findings.append(
                finding(
                    "block",
                    "weak-partial-truth-conclusion",
                    "plain_language_conclusion must start with the global thesis, not local-truth concession",
                )
            )
        if looks_like_score_concession(conclusion):
            findings.append(
                finding(
                    "block",
                    "weak-partial-truth-conclusion",
                    "plain_language_conclusion must not use score-as-concession framing",
                )
            )
        if looks_like_soft_not_wrong_concession(conclusion):
            findings.append(
                finding(
                    "block",
                    "weak-partial-truth-conclusion",
                    "plain_language_conclusion must not soften a rejected definition into a not-wrong concession",
                )
            )
        if looks_like_generic_not_only_caveat(first_sentence):
            findings.append(
                finding(
                    "block",
                    "weak-partial-truth-conclusion",
                    "plain_language_conclusion must not be a generic not-only caveat",
                )
            )
        if exposes_internal_stdout(conclusion):
            findings.append(
                finding(
                    "block",
                    "internal-stdout-exposed",
                    "plain_language_conclusion must not expose internal script stdout",
                )
            )
    validation = data.get("whole_elephant_validation")
    if not isinstance(validation, dict):
        findings.append(
            finding(
                "block",
                "missing-whole-elephant-validation",
                "whole_elephant_validation is required when partial_truth_capture_triggered is true",
            )
        )
    elif validation.get("script_verdict") not in {"shape_only", "not_run_fallback"}:
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-validation",
                "whole_elephant_validation.script_verdict must be 'shape_only' or 'not_run_fallback'",
            )
        )
    elif validation.get("script_verdict") == "shape_only":
        if not _non_empty_string(validation.get("command")):
            findings.append(
                finding(
                    "block",
                    "missing-whole-elephant-validation-evidence",
                    "whole_elephant_validation.command must name the validator command that ran",
                )
            )
        elif _placeholder_command(validation["command"]):
            findings.append(
                finding(
                    "block",
                    "placeholder-whole-elephant-validation-command",
                    "whole_elephant_validation.command must be the exact command that ran, not a placeholder",
                )
            )
        if not _non_empty_string(validation.get("output_evidence")):
            findings.append(
                finding(
                    "block",
                    "missing-whole-elephant-validation-evidence",
                    "whole_elephant_validation.output_evidence must include observed validator output",
                )
            )
    else:
        if not _non_empty_string(validation.get("fallback_reason")):
            findings.append(
                finding(
                    "block",
                    "missing-whole-elephant-validation-fallback",
                    "whole_elephant_validation.fallback_reason must explain why the script did not run",
                )
            )
        if not _non_empty_string(validation.get("self_check_evidence")):
            findings.append(
                finding(
                    "block",
                    "missing-whole-elephant-validation-fallback",
                    "whole_elephant_validation.self_check_evidence must describe the internal shape self-check",
                )
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate using-mindthus fidelity output shape.")
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    data = load_json(path)
    findings = validate_fidelity_output(data, SPEC)
    findings.extend(_validate_whole_elephant_contract(data))
    print_text_report(path, data, findings, SPEC)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

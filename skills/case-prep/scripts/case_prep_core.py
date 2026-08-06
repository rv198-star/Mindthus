"""Shared implementation for explicit Mindthus case preparation.

This module unifies the user-facing preparation flow while preserving separate
Judgment Trace / Case Export and TPlan runtime contracts. It performs no upload.
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import shutil
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SKILLS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS_ROOT))
from runtime_bootstrap import activate_runtime  # noqa: E402

activate_runtime(__file__)

from _runtime.core.report import Finding, finding  # noqa: E402
from _runtime.judgment.benchmark import judgment_trace_from_benchmark  # noqa: E402
from _runtime.judgment.case_export import (  # noqa: E402
    CASE_TYPES,
    CaseExportError,
    create_case_package,
    scan_text,
    validate_case_package,
)
from _runtime.judgment.trace import (  # noqa: E402
    TraceValidationError,
    load_judgment_trace,
    validate_judgment_trace,
    write_judgment_trace,
)


CASE_PREP_RESULT_SCHEMA_VERSION = "mindthus.case-prep-result.v1"
CASE_COLLECTION_SCHEMA_VERSION = "mindthus.case-collection.v1"
TPLAN_CASE_PACKET_SCHEMA_VERSION = "tplan.case-packet.v1"
TPLAN_CASE_SUMMARY_SCHEMA_VERSION = "tplan.case-summary.v1"
MAX_COLLECTION_CASES = 20
COLLECTION_ALLOWED_ROOT_FILES = {
    "manifest.json",
    "index.md",
    "privacy-scan.json",
    "README.md",
}
TPLAN_FOCI = {
    "auto",
    "blocker",
    "acceptance",
    "continuation",
    "authority",
    "recovery",
    "provenance",
    "telemetry",
    "general",
}
MAX_SELECTED_EVENTS = 5
MAX_EXCERPT_BYTES = 1024 * 1024
CASE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

TPLAN_ALLOWED_ROOT_FILES = {
    "manifest.json",
    "mission-summary.json",
    "mission-summary.md",
    "selected-event.json",
    "selected-evidence.json",
    "pulse.json",
    "privacy-scan.json",
    "README.md",
    "judgment-trace.json",
}
TPLAN_FORBIDDEN_NAMES = {
    "mission.json",
    "mission.md",
    "evidence.jsonl",
    "execution_trace.jsonl",
    "step_logs",
    "logs",
    ".tplan",
}
FOCUS_EVENT_TYPES = {
    "blocker": {"failure", "blocked", "interruption", "stop_report", "acceptance_failed"},
    "acceptance": {"acceptance", "acceptance_passed", "acceptance_failed"},
    "continuation": {"decision_recommendation", "decision_applied", "pulse_consumed"},
    "authority": {"stop_report", "decision_recommendation", "decision_applied", "user_feedback"},
    "recovery": {"decision_applied", "key_finding", "stop_report"},
    "provenance": set(),
    "telemetry": set(),
    "general": set(),
}


class CasePrepError(ValueError):
    """Raised when case preparation cannot preserve its contract."""

    def __init__(self, findings: Iterable[Finding] | str):
        if isinstance(findings, str):
            self.findings = [finding("block", "case-prep-error", findings)]
        else:
            self.findings = list(findings)
        super().__init__("; ".join(item.message for item in self.findings))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CasePrepError(f"failed to read JSON at {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise CasePrepError(f"failed to decode JSON at {path} as UTF-8: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise CasePrepError(
            f"invalid JSON at {path}, line {exc.lineno} column {exc.colno}: {exc.msg}"
        ) from exc


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _validation_json(path: Path, findings: list[Finding], subject: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        findings.append(finding("block", "read-failed", f"failed to read {subject}: {exc}", subject))
    except UnicodeDecodeError as exc:
        findings.append(finding("block", "decode-failed", f"{subject} must be UTF-8: {exc}", subject))
    except json.JSONDecodeError as exc:
        findings.append(
            finding(
                "block",
                "invalid-json",
                f"invalid JSON in {subject} at line {exc.lineno} column {exc.colno}: {exc.msg}",
                subject,
            )
        )
    return None


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CasePrepError(
                f"invalid JSONL at {path}, line {line_number}: {exc.msg}"
            ) from exc
        if isinstance(value, dict):
            records.append(value)
    return records


def _record_by_case(records: list[dict[str, Any]], case_id: str) -> dict[str, Any] | None:
    return next((record for record in records if str(record.get("case_id")) == case_id), None)


def _safe_case_id(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    if len(value) > 64:
        value = value[:64].rstrip("-._")
    if not CASE_ID_RE.fullmatch(value):
        raise CasePrepError("case_id must use 3-64 letters, numbers, '.', '_', or '-'")
    return value


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _archive_directory(package_dir: Path) -> Path:
    if not package_dir.is_dir() or package_dir.is_symlink():
        raise CasePrepError(f"package must be a regular directory: {package_dir}")
    for path in package_dir.rglob("*"):
        if path.is_symlink():
            raise CasePrepError(f"refusing to archive symlink: {path}")
    archive_path = package_dir.parent / f"{package_dir.name}.tar.gz"
    if archive_path.exists():
        raise CasePrepError(f"refusing to overwrite existing archive: {archive_path}")
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(package_dir, arcname=package_dir.name, recursive=True)
    return archive_path


def _excerpt_arg(value: str) -> tuple[str, Path]:
    if "=" in value:
        label, raw = value.split("=", 1)
        if not label.strip() or not raw.strip():
            raise CasePrepError("excerpt must be LABEL=PATH or PATH")
        return label.strip(), Path(raw).expanduser()
    path = Path(value).expanduser()
    return path.stem, path


def _judgment_result(
    *,
    mode: str,
    package_dir: Path,
    archive_path: Path,
    case_type: str,
    focus: str | None = None,
    warnings: list[str] | None = None,
    item_count: int | None = None,
) -> dict[str, Any]:
    result = {
        "schema_version": CASE_PREP_RESULT_SCHEMA_VERSION,
        "mode": mode,
        "case_type": case_type,
        "focus": focus,
        "package_dir": str(package_dir),
        "archive_path": str(archive_path),
        "review_required_before_share": True,
        "automatic_upload": False,
        "warnings": warnings or [],
    }
    if item_count is not None:
        result["item_count"] = item_count
    return result


def prepare_judgment_case(
    *,
    trace_path: Path,
    summary_path: Path,
    case_type: str,
    output_root: Path,
    case_id: str | None = None,
    source_client: str | None = None,
    source_method: str | None = None,
    benchmark_case_id: str | None = None,
    related_test_id: str | None = None,
    related_issue: str | None = None,
    excerpts: list[tuple[str, Path]] | None = None,
    excerpts_confirmed_redacted: bool = False,
) -> dict[str, Any]:
    """Wrap the existing Case Export v1 contract and create an archive."""

    try:
        package_dir = create_case_package(
            output_root=output_root,
            trace_path=trace_path,
            summary_path=summary_path,
            case_type=case_type,
            case_id=case_id,
            source_client=source_client,
            source_method=source_method,
            benchmark_case_id=benchmark_case_id,
            related_test_id=related_test_id,
            related_issue=related_issue,
            excerpts=excerpts,
            excerpts_confirmed_redacted=excerpts_confirmed_redacted,
        )
    except (CaseExportError, TraceValidationError) as exc:
        raise CasePrepError(getattr(exc, "findings", str(exc))) from exc
    findings = validate_case_package(package_dir)
    blocks = [item for item in findings if item.severity == "block"]
    if blocks:
        raise CasePrepError(blocks)
    archive_path = _archive_directory(package_dir)
    return _judgment_result(
        mode="judgment",
        package_dir=package_dir,
        archive_path=archive_path,
        case_type=case_type,
        warnings=[item.code for item in findings if item.severity == "warn"],
    )


def _benchmark_case_type(score: dict[str, Any]) -> str:
    verdict = str(score.get("owner_fidelity_verdict") or "")
    if int(score.get("score", 0)) < 2 or verdict in {
        "no_load",
        "wrong_owner_loaded",
        "runtime_over_wake",
        "unknown_expected_owner",
    }:
        return "judgment_failure"
    return "test_regression_candidate"


def _benchmark_summary(
    case_id: str,
    trace: dict[str, Any],
    response: dict[str, Any],
    score: dict[str, Any],
) -> dict[str, Any]:
    routing = trace.get("routing", {})
    input_shape = trace.get("input_shape", {})
    decision_delta = trace.get("decision_delta", {})
    changed = [
        field
        for field, value in decision_delta.items()
        if field not in {"basis", "comparison_ref"} and value is True
    ]
    unknown = [
        field
        for field, value in decision_delta.items()
        if field not in {"basis", "comparison_ref"} and value == "unknown"
    ]
    loaded = routing.get("loaded_methods") or []
    score_value = score.get("score", "not_evaluated")
    verdict = score.get("owner_fidelity_verdict") or "not_recorded"
    rationale = " ".join(str(score.get("rationale") or "No judge rationale was recorded.").split())
    if len(rationale) > 600:
        rationale = rationale[:597] + "..."
    evidence_available = ["Archived benchmark response record", "Archived benchmark score record"]
    if loaded:
        evidence_available.append("Runtime-observed loaded method telemetry")
    evidence_missing = ["Real-world outcome evidence"]
    if decision_delta.get("basis") != "baseline_comparison":
        evidence_missing.append("Direct baseline comparison for causal value claims")
    delta_lines = [f"Confirmed changed dimension: {field}" for field in changed]
    delta_lines.extend(f"Unassessed dimension: {field}" for field in unknown)
    if not delta_lines:
        delta_lines.append("No decision delta was confirmed by the archived evaluator fields.")
    return {
        "schema_version": "mindthus.case-summary.v1",
        "decision_context": (
            f"Archived judgment benchmark case {case_id}; variant "
            f"{score.get('variant') or response.get('variant') or 'unknown'}."
        ),
        "observed_failure_or_value_delta": (
            f"Judge score={score_value}; owner_fidelity_verdict={verdict}. {rationale}"
        ),
        "active_judgment_object": str(input_shape.get("judgment_object") or "unknown"),
        "selected_route_or_method": (
            f"routing_decision={routing.get('routing_decision')}; "
            f"judgment_owner={routing.get('judgment_owner')}; loaded_methods={loaded}"
        ),
        "signal": (
            f"expected_owner={score.get('expected_owner') or 'unknown'}; "
            f"visible_action={score.get('required_visible_action_present')}; verdict={verdict}"
        ),
        "evidence_available": evidence_available,
        "evidence_missing": evidence_missing,
        "decision_delta": delta_lines,
        "learning_hypothesis": (
            "Review router activation, owner fidelity, and the required visible action before "
            "promoting this case into a regression test or benchmark change."
        ),
        "uncertainty": (
            "This package does not include the full prompt or answer by default and does not "
            "prove real-world outcome causality."
        ),
        "redaction_notes": (
            "No raw prompt, full answer, environment path, attachment, or private runtime log "
            "is included automatically."
        ),
    }


def prepare_benchmark_case(
    *,
    run_dir: Path,
    benchmark_case_id: str,
    output_root: Path,
    case_id: str | None = None,
    case_type: str | None = None,
    excerpts: list[tuple[str, Path]] | None = None,
    excerpts_confirmed_redacted: bool = False,
) -> dict[str, Any]:
    """Prepare a benchmark case without requiring manual trace or summary construction."""

    run_dir = run_dir.expanduser().resolve()
    score = _record_by_case(_load_jsonl(run_dir / "score-records.jsonl"), benchmark_case_id)
    response = _record_by_case(_load_jsonl(run_dir / "raw-responses.jsonl"), benchmark_case_id)
    if score is None:
        record_path = run_dir / "judge-answers" / f"{benchmark_case_id}.record.json"
        if record_path.is_file():
            value = _json_load(record_path)
            score = value if isinstance(value, dict) else None
    if response is None:
        record_path = run_dir / "answers" / f"{benchmark_case_id}.record.json"
        if record_path.is_file():
            value = _json_load(record_path)
            response = value if isinstance(value, dict) else None
    if score is None or response is None:
        raise CasePrepError(
            "benchmark run must contain both response and score records for the requested case"
        )

    trace_path = run_dir / "judgment-traces" / f"{benchmark_case_id}.json"
    with tempfile.TemporaryDirectory(prefix="mindthus-benchmark-case-") as tmp:
        tmp_dir = Path(tmp)
        if trace_path.is_file():
            trace = load_judgment_trace(trace_path)
            effective_trace_path = trace_path
        else:
            expected_owner = str(score.get("expected_owner") or "unknown")
            source_case = {
                "case_id": benchmark_case_id,
                "case_type": score.get("case_type") or response.get("case_type") or "positive",
                "expected_owner": expected_owner,
                "stay_asleep_expected": (
                    score.get("case_type") == "negative_control"
                    or expected_owner in {"direct_execution", "direct_answer", "direct_judgment"}
                ),
            }
            trace = judgment_trace_from_benchmark(source_case, response, score)
            effective_trace_path = tmp_dir / "judgment-trace.json"
            write_judgment_trace(effective_trace_path, trace)

        summary = _benchmark_summary(benchmark_case_id, trace, response, score)
        summary_path = tmp_dir / "case-summary.json"
        _write_json(summary_path, summary)
        selected_case_type = case_type or _benchmark_case_type(score)
        package_id = case_id or _safe_case_id(f"benchmark-{benchmark_case_id}")
        return prepare_judgment_case(
            trace_path=effective_trace_path,
            summary_path=summary_path,
            case_type=selected_case_type,
            output_root=output_root,
            case_id=package_id,
            source_client="judgment-benchmark-cli",
            source_method=(trace.get("routing", {}).get("selected_method")),
            benchmark_case_id=benchmark_case_id,
            excerpts=excerpts,
            excerpts_confirmed_redacted=excerpts_confirmed_redacted,
        ) | {"mode": "benchmark"}


def _activate_tplan_runtime() -> Any:
    tplan_scripts = SKILLS_ROOT / "tplan" / "scripts"
    if not (tplan_scripts / "tplan_runtime.py").is_file():
        raise CasePrepError(f"cannot locate TPlan runtime under {tplan_scripts}")
    value = str(tplan_scripts)
    sys.path[:] = [entry for entry in sys.path if entry != value]
    sys.path.insert(0, value)
    import tplan_runtime  # type: ignore

    return tplan_runtime


def _brief_task(task: Any) -> dict[str, Any] | None:
    if not isinstance(task, dict):
        return None
    return {
        "id": task.get("id"),
        "title": task.get("title"),
        "kind": task.get("kind"),
        "status": task.get("status"),
        "role": task.get("role"),
    }


def _brief_event(event: Any) -> dict[str, Any] | None:
    if not isinstance(event, dict):
        return None
    return {
        "id": event.get("id"),
        "timestamp": event.get("timestamp"),
        "event_type": event.get("event_type"),
        "task_id": event.get("task_id"),
        "summary": event.get("summary"),
    }


def _runtime_provenance_brief(report: Any) -> dict[str, Any]:
    if not isinstance(report, dict):
        return {
            "status": "unknown",
            "severity": "warning",
            "compatible": None,
            "origin": None,
            "diagnostic_codes": ["runtime_provenance_report_unavailable"],
        }
    diagnostics = report.get("diagnostics") or []
    return {
        "status": report.get("status"),
        "severity": report.get("severity"),
        "compatible": report.get("compatible"),
        "origin": report.get("origin"),
        "diagnostic_codes": [
            str(item.get("code"))
            for item in diagnostics
            if isinstance(item, dict) and item.get("code")
        ],
    }


def _pulse_brief(pulse: dict[str, Any]) -> dict[str, Any]:
    route = pulse.get("mission_pulse") if isinstance(pulse.get("mission_pulse"), dict) else {}
    winning = pulse.get("winning_candidate") if isinstance(pulse.get("winning_candidate"), dict) else None
    return {
        "script_verdict": pulse.get("script_verdict"),
        "agentic_judgment_required": pulse.get("agentic_judgment_required"),
        "signals": list(route.get("signals") or []),
        "scope": route.get("scope"),
        "next_gate": route.get("next_gate"),
        "rationale": route.get("rationale"),
        "gate_owner": pulse.get("gate_owner"),
        "winning_candidate": (
            {
                "signal": winning.get("signal"),
                "priority_class": winning.get("priority_class"),
                "candidate_next_gate": winning.get("candidate_next_gate"),
                "source_ids": list(winning.get("source_ids") or []),
            }
            if winning
            else None
        ),
        "validation_finding_count": len(pulse.get("validation_findings") or []),
        "pulse_shape_finding_count": len(pulse.get("pulse_shape_findings") or []),
    }


def _infer_tplan_focus(
    mission: dict[str, Any],
    events: list[dict[str, Any]],
    pulse: dict[str, Any],
    provenance: dict[str, Any],
) -> tuple[str, str]:
    status = str((mission.get("mission") or {}).get("status") or "")
    if status == "requires_human":
        return "authority", "Mission status requires human authority."
    if status == "blocked":
        return "blocker", "Mission status is blocked."
    if provenance.get("severity") == "error":
        return "provenance", "Runtime provenance reports an incompatible or invalid runtime."
    shared_context = mission.get("shared_context")
    if isinstance(shared_context, dict) and isinstance(shared_context.get("reentry_decision"), dict):
        return "recovery", "Mission contains an explicit re-entry decision."
    route = pulse.get("mission_pulse") if isinstance(pulse.get("mission_pulse"), dict) else {}
    signals = [str(value) for value in route.get("signals") or []]
    if any("acceptance" in value for value in signals):
        return "acceptance", "Mission Pulse selected an acceptance-related signal."
    if any(token in value for value in signals for token in ("repeat", "spiral", "continuation", "additive")):
        return "continuation", "Mission Pulse selected a repeated-path or continuation signal."
    for event in reversed(events):
        event_type = str(event.get("event_type") or "")
        if event_type in FOCUS_EVENT_TYPES["blocker"]:
            return "blocker", f"Latest relevant evidence event is {event_type}."
        if event_type in FOCUS_EVENT_TYPES["acceptance"]:
            return "acceptance", f"Latest relevant evidence event is {event_type}."
    if route.get("next_gate") in {"stop", "escalate", "anti_spiral_audit"}:
        return "continuation", f"Mission Pulse routed to {route.get('next_gate')}."
    return "general", "No stronger bounded case focus was mechanically observed."


def _select_tplan_events(
    events: list[dict[str, Any]],
    focus: str,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None, str]:
    allowed = FOCUS_EVENT_TYPES.get(focus, set())
    candidates = [event for event in events if str(event.get("event_type") or "") in allowed]
    if not candidates:
        candidates = events[-MAX_SELECTED_EVENTS:]
        reason = "No focus-specific event matched; selected the most recent bounded evidence events."
    else:
        candidates = candidates[-MAX_SELECTED_EVENTS:]
        reason = f"Selected the most recent events matching focus={focus}."
    briefs = [brief for brief in (_brief_event(event) for event in candidates) if brief is not None]
    primary = briefs[-1] if briefs else None
    return briefs, primary, reason


def _read_excerpt(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise CasePrepError(f"excerpt must be a regular file: {path}")
    if path.stat().st_size > MAX_EXCERPT_BYTES:
        raise CasePrepError(f"excerpt exceeds {MAX_EXCERPT_BYTES} bytes: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise CasePrepError(f"excerpt must be UTF-8 text: {path}") from exc


def _safe_excerpt_name(label: str, source: Path, used: set[str]) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", (label.strip() or source.stem)).strip("-._") or "excerpt"
    suffix = source.suffix.lower() if source.suffix.lower() in {".md", ".txt", ".json"} else ".txt"
    if not base.lower().endswith(suffix):
        base += suffix
    candidate = base
    index = 2
    while candidate in used:
        candidate = f"{Path(base).stem}-{index}{Path(base).suffix}"
        index += 1
    used.add(candidate)
    return candidate


def _tplan_summary_markdown(summary: dict[str, Any]) -> str:
    mission = summary["mission"]
    active = summary.get("active_task") or {}
    pulse = summary["pulse"]
    provenance = summary["runtime_provenance"]
    return f"""# TPlan Case Summary

## Focus

- focus: `{summary['focus']}`
- selection reason: {summary['focus_reason']}

## Mission

- title: {mission.get('title')}
- objective: {mission.get('objective')}
- status: {mission.get('status')}
- human_in_loop: {mission.get('human_in_loop')}
- risk_tolerance: {mission.get('risk_tolerance')}
- resource_sufficiency: {mission.get('resource_sufficiency')}

## Active Path

- active task: {active.get('title') or 'none'}
- active task status: {active.get('status') or 'none'}
- parent path: {' -> '.join(item.get('title') or str(item.get('id')) for item in summary['parent_chain']) or 'none'}

## Mission Pulse

- signals: {pulse.get('signals')}
- next gate: {pulse.get('next_gate')}
- gate owner: {pulse.get('gate_owner')}
- rationale: {pulse.get('rationale')}

## Runtime Provenance

- status: {provenance.get('status')}
- severity: {provenance.get('severity')}
- compatible: {provenance.get('compatible')}
- diagnostic codes: {provenance.get('diagnostic_codes')}

## Selection Boundary

Only a bounded active-path summary and up to {MAX_SELECTED_EVENTS} brief evidence events
are included. The full Mission, task tree, evidence stream, step logs, execution trace,
and telemetry stream are excluded.
"""


def _tplan_readme() -> str:
    return """# Local TPlan Case Packet

This packet was prepared locally at the user's request and has not been uploaded.

Before sharing:

1. Read every file in this directory.
2. Check Mission objective, task titles, evidence summaries, and optional excerpts for
   private names, customer data, credentials, or internal paths.
3. Confirm that the selected focus and event are the intended analysis target.
4. Run `validate_case_packet.py` again.
5. Share the archive only through a separate explicit user action.

This packet deliberately excludes the full Mission runtime. Pattern scanning is bounded
and does not prove anonymity, consent sufficiency, semantic correctness, or causal value.
"""


def _raw_tplan_content_findings(text: str, subject: str) -> list[Finding]:
    findings: list[Finding] = []
    if (
        '"schema_version"' in text
        and "tplan.v0.1" in text
        and '"tasks"' in text
        and '"active_task_id"' in text
    ):
        findings.append(
            finding(
                "block",
                "full-mission-shape",
                "possible full TPlan Mission content detected; export only a bounded summary",
                subject,
            )
        )
    if '"event_type"' in text and '"payload"' in text:
        findings.append(
            finding(
                "block",
                "raw-evidence-payload",
                "raw TPlan evidence payload detected; export only brief selected events",
                subject,
            )
        )
    if "tplan.execution_trace.v0.1" in text or (
        '"span_id"' in text and ('"span_started"' in text or '"span_completed"' in text)
    ):
        findings.append(
            finding(
                "block",
                "execution-trace-shape",
                "possible TPlan execution trace content detected",
                subject,
            )
        )
    return findings


def _privacy_scan_for_files(files: dict[str, str]) -> tuple[dict[str, Any], list[Finding]]:
    findings: list[Finding] = []
    for name, text in files.items():
        findings.extend(scan_text(text, name))
        findings.extend(_raw_tplan_content_findings(text, name))
    blocks = [item for item in findings if item.severity == "block"]
    if blocks:
        raise CasePrepError(blocks)
    warning_codes = sorted({item.code for item in findings if item.severity == "warn"})
    return (
        {
            "schema_version": "tplan.case-privacy-scan.v1",
            "status": "warnings" if warning_codes else "passed",
            "warning_codes": warning_codes,
            "note": "Pattern scan only; passing does not prove anonymity or adequate redaction.",
        },
        findings,
    )


def prepare_tplan_case(
    *,
    mission_dir: Path,
    output_root: Path,
    focus: str = "auto",
    case_id: str | None = None,
    judgment_trace_path: Path | None = None,
    excerpts: list[tuple[str, Path]] | None = None,
    excerpts_confirmed_redacted: bool = False,
) -> dict[str, Any]:
    """Build a bounded TPlan Case Packet from documented read-only views."""

    if focus not in TPLAN_FOCI:
        raise CasePrepError(f"unsupported TPlan focus: {focus}")
    tplan_runtime = _activate_tplan_runtime()
    mission_dir = mission_dir.expanduser().resolve()
    resolved_output_root = output_root.expanduser().resolve()
    if resolved_output_root == mission_dir or mission_dir in resolved_output_root.parents:
        raise CasePrepError("TPlan case output must stay outside the Mission directory")
    try:
        snapshot = tplan_runtime.read_outcome_attribution_snapshot(mission_dir)
        pulse = tplan_runtime.build_mission_pulse(mission_dir, trigger="manual")
    except (OSError, ValueError) as exc:
        raise CasePrepError(f"failed to read TPlan Mission: {exc}") from exc

    mission = snapshot.get("mission")
    events = snapshot.get("events")
    provenance = snapshot.get("runtime_provenance")
    if not isinstance(mission, dict) or not isinstance(events, list):
        raise CasePrepError("TPlan snapshot is missing Mission or evidence state")
    provenance_brief = _runtime_provenance_brief(provenance)
    selected_focus, focus_reason = (
        _infer_tplan_focus(mission, events, pulse, provenance_brief)
        if focus == "auto"
        else (focus, f"Focus explicitly selected as {focus}.")
    )
    selected_events, primary_event, selection_reason = _select_tplan_events(events, selected_focus)
    mission_meta = mission.get("mission") if isinstance(mission.get("mission"), dict) else {}
    active_task = tplan_runtime.active_task(mission)
    parent_chain = tplan_runtime.parent_chain(
        mission,
        active_task.get("id") if isinstance(active_task, dict) else None,
    )
    pulse_brief = _pulse_brief(pulse)
    summary = {
        "schema_version": TPLAN_CASE_SUMMARY_SCHEMA_VERSION,
        "focus": selected_focus,
        "focus_reason": focus_reason,
        "mission": {
            "title": mission_meta.get("title"),
            "objective": mission_meta.get("objective"),
            "status": mission_meta.get("status"),
            "human_in_loop": mission_meta.get("human_in_loop"),
            "risk_tolerance": mission_meta.get("risk_tolerance"),
            "resource_sufficiency": mission_meta.get("resource_sufficiency"),
        },
        "active_task": _brief_task(active_task),
        "parent_chain": [
            brief for brief in (_brief_task(item) for item in parent_chain) if brief is not None
        ],
        "pulse": pulse_brief,
        "runtime_provenance": provenance_brief,
        "selected_event_id": primary_event.get("id") if primary_event else None,
        "selected_evidence_ids": [event.get("id") for event in selected_events],
        "selection_reason": selection_reason,
    }
    summary_md = _tplan_summary_markdown(summary)
    pulse_json = json.dumps(pulse_brief, ensure_ascii=False, indent=2) + "\n"
    selected_event_json = json.dumps(primary_event, ensure_ascii=False, indent=2) + "\n"
    selected_evidence_json = json.dumps(selected_events, ensure_ascii=False, indent=2) + "\n"
    summary_json = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"

    explicit_excerpts = excerpts or []
    if explicit_excerpts and not excerpts_confirmed_redacted:
        raise CasePrepError("explicit excerpts require --confirm-excerpts-redacted")
    prepared_excerpts: list[tuple[str, str]] = []
    used_names: set[str] = set()
    for label, path in explicit_excerpts:
        text = _read_excerpt(path)
        name = _safe_excerpt_name(label, path, used_names)
        prepared_excerpts.append((name, text))

    trace: dict[str, Any] | None = None
    if judgment_trace_path is not None:
        trace = load_judgment_trace(judgment_trace_path)

    scan_files = {
        "mission-summary.json": summary_json,
        "mission-summary.md": summary_md,
        "selected-event.json": selected_event_json,
        "selected-evidence.json": selected_evidence_json,
        "pulse.json": pulse_json,
    }
    if trace is not None:
        scan_files["judgment-trace.json"] = json.dumps(trace, ensure_ascii=False, indent=2) + "\n"
    for name, text in prepared_excerpts:
        scan_files[f"excerpts/{name}"] = text
    privacy_scan, scan_findings = _privacy_scan_for_files(scan_files)

    resolved_case_id = _safe_case_id(
        case_id
        or f"tplan-{selected_focus}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(3)}"
    )
    resolved_output_root.mkdir(parents=True, exist_ok=True)
    package_dir = resolved_output_root / f"mindthus-tplan-case-{resolved_case_id}"
    if package_dir.exists():
        raise CasePrepError(f"refusing to overwrite existing package: {package_dir}")
    package_dir.mkdir()
    try:
        _write_json(package_dir / "mission-summary.json", summary)
        (package_dir / "mission-summary.md").write_text(summary_md, encoding="utf-8")
        _write_json(package_dir / "selected-event.json", primary_event)
        _write_json(package_dir / "selected-evidence.json", selected_events)
        _write_json(package_dir / "pulse.json", pulse_brief)
        _write_json(package_dir / "privacy-scan.json", privacy_scan)
        (package_dir / "README.md").write_text(_tplan_readme(), encoding="utf-8")
        if trace is not None:
            write_judgment_trace(package_dir / "judgment-trace.json", trace)
        if prepared_excerpts:
            excerpt_dir = package_dir / "excerpts"
            excerpt_dir.mkdir()
            for name, text in prepared_excerpts:
                (excerpt_dir / name).write_text(text, encoding="utf-8")

        manifest = {
            "schema_version": TPLAN_CASE_PACKET_SCHEMA_VERSION,
            "case_id": resolved_case_id,
            "created_at_utc": now_iso(),
            "mode": "tplan",
            "focus": selected_focus,
            "consent": {
                "export_requested_by_user": True,
                "review_required_before_share": True,
                "automatic_upload": False,
            },
            "privacy": {
                "contains_full_mission": False,
                "contains_full_task_tree": False,
                "contains_full_evidence_stream": False,
                "contains_execution_trace": False,
                "contains_step_logs": False,
                "contains_user_selected_excerpts": bool(prepared_excerpts),
                "redaction_status": "review_required",
                "pattern_scan_status": privacy_scan["status"],
            },
            "source": {
                "mission_binding": _sha256_text(str(mission_dir)),
                "runtime_provenance_status": provenance_brief.get("status"),
            },
            "selection": {
                "selected_event_id": primary_event.get("id") if primary_event else None,
                "selected_evidence_ids": [event.get("id") for event in selected_events],
                "reason": selection_reason,
            },
            "links": {
                "judgment_trace": "judgment-trace.json" if trace is not None else None,
            },
            "files": {
                "mission_summary_json": "mission-summary.json",
                "mission_summary_markdown": "mission-summary.md",
                "selected_event": "selected-event.json",
                "selected_evidence": "selected-evidence.json",
                "pulse": "pulse.json",
                "privacy_scan": "privacy-scan.json",
                "privacy_notice": "README.md",
                "excerpts": [f"excerpts/{name}" for name, _ in prepared_excerpts],
            },
        }
        _write_json(package_dir / "manifest.json", manifest)
    except Exception:
        shutil.rmtree(package_dir, ignore_errors=True)
        raise

    findings = validate_tplan_case_packet(package_dir)
    blocks = [item for item in findings if item.severity == "block"]
    if blocks:
        shutil.rmtree(package_dir, ignore_errors=True)
        raise CasePrepError(blocks)
    archive_path = _archive_directory(package_dir)
    return _judgment_result(
        mode="tplan",
        package_dir=package_dir,
        archive_path=archive_path,
        case_type="tplan_case",
        focus=selected_focus,
        warnings=sorted(
            {item.code for item in scan_findings if item.severity == "warn"}
            | {item.code for item in findings if item.severity == "warn"}
        ),
    )


def _validate_tplan_manifest(manifest: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(manifest, dict):
        return [finding("block", "invalid-manifest", "manifest root must be an object")]
    required = {
        "schema_version",
        "case_id",
        "created_at_utc",
        "mode",
        "focus",
        "consent",
        "privacy",
        "source",
        "selection",
        "links",
        "files",
    }
    for field in sorted(required - set(manifest)):
        findings.append(finding("block", "missing-field", f"missing manifest field: {field}", "manifest.json"))
    for field in sorted(set(manifest) - required):
        findings.append(finding("block", "unknown-field", f"unsupported manifest field: {field}", "manifest.json"))
    if manifest.get("schema_version") != TPLAN_CASE_PACKET_SCHEMA_VERSION:
        findings.append(finding("block", "unsupported-schema", "unsupported TPlan case packet schema", "manifest.json"))
    case_id = manifest.get("case_id")
    if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
        findings.append(finding("block", "invalid-case-id", "manifest case_id is invalid", "manifest.json"))
    if manifest.get("mode") != "tplan":
        findings.append(finding("block", "invalid-mode", "manifest mode must be tplan", "manifest.json"))
    if manifest.get("focus") not in TPLAN_FOCI - {"auto"}:
        findings.append(finding("block", "invalid-focus", "manifest focus is unsupported", "manifest.json"))
    created_at = manifest.get("created_at_utc")
    if not isinstance(created_at, str):
        findings.append(finding("block", "invalid-created-at", "created_at_utc must be an ISO-8601 string", "manifest.json"))
    else:
        try:
            parsed = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            findings.append(finding("block", "invalid-created-at", "created_at_utc must be ISO-8601", "manifest.json"))
        else:
            if parsed.tzinfo is None:
                findings.append(finding("block", "invalid-created-at", "created_at_utc must include a timezone", "manifest.json"))
    consent = manifest.get("consent")
    if not isinstance(consent, dict):
        findings.append(finding("block", "invalid-consent", "consent must be an object", "manifest.json"))
    else:
        expected_consent = {"export_requested_by_user", "review_required_before_share", "automatic_upload"}
        for field in sorted(expected_consent - set(consent)):
            findings.append(finding("block", "missing-field", f"missing consent field: {field}", "manifest.json"))
        for field in sorted(set(consent) - expected_consent):
            findings.append(finding("block", "unknown-field", f"unsupported consent field: {field}", "manifest.json"))
        if consent.get("export_requested_by_user") is not True:
            findings.append(finding("block", "consent-required", "export_requested_by_user must be true", "manifest.json"))
        if consent.get("review_required_before_share") is not True:
            findings.append(finding("block", "review-required", "review_required_before_share must be true", "manifest.json"))
        if consent.get("automatic_upload") is not False:
            findings.append(finding("block", "automatic-upload-forbidden", "automatic_upload must be false", "manifest.json"))
    privacy = manifest.get("privacy")
    if not isinstance(privacy, dict):
        findings.append(finding("block", "invalid-privacy", "privacy must be an object", "manifest.json"))
    else:
        expected_privacy = {
            "contains_full_mission",
            "contains_full_task_tree",
            "contains_full_evidence_stream",
            "contains_execution_trace",
            "contains_step_logs",
            "contains_user_selected_excerpts",
            "redaction_status",
            "pattern_scan_status",
        }
        for field in sorted(expected_privacy - set(privacy)):
            findings.append(finding("block", "missing-field", f"missing privacy field: {field}", "manifest.json"))
        for field in sorted(set(privacy) - expected_privacy):
            findings.append(finding("block", "unknown-field", f"unsupported privacy field: {field}", "manifest.json"))
        for field in (
            "contains_full_mission",
            "contains_full_task_tree",
            "contains_full_evidence_stream",
            "contains_execution_trace",
            "contains_step_logs",
        ):
            if privacy.get(field) is not False:
                findings.append(finding("block", "raw-runtime-forbidden", f"{field} must be false", "manifest.json"))
        if privacy.get("redaction_status") != "review_required":
            findings.append(finding("block", "review-required", "redaction_status must remain review_required", "manifest.json"))
        if privacy.get("pattern_scan_status") not in {"passed", "warnings"}:
            findings.append(finding("block", "invalid-scan-status", "pattern_scan_status must be passed or warnings", "manifest.json"))
        if not isinstance(privacy.get("contains_user_selected_excerpts"), bool):
            findings.append(finding("block", "invalid-privacy", "contains_user_selected_excerpts must be boolean", "manifest.json"))
    source = manifest.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("mission_binding"), str) or not SHA256_RE.fullmatch(source["mission_binding"]):
        findings.append(finding("block", "invalid-source", "source.mission_binding must be a sha256 digest", "manifest.json"))
    elif set(source) != {"mission_binding", "runtime_provenance_status"}:
        findings.append(finding("block", "invalid-source", "source fields are invalid", "manifest.json"))
    elif source.get("runtime_provenance_status") is not None and (
        not isinstance(source.get("runtime_provenance_status"), str)
        or not source["runtime_provenance_status"].strip()
    ):
        findings.append(finding("block", "invalid-source", "runtime_provenance_status must be null or a non-empty string", "manifest.json"))
    selection = manifest.get("selection")
    if not isinstance(selection, dict):
        findings.append(finding("block", "invalid-selection", "selection must be an object", "manifest.json"))
    elif set(selection) != {"selected_event_id", "selected_evidence_ids", "reason"}:
        findings.append(finding("block", "invalid-selection", "selection fields are invalid", "manifest.json"))
    elif not isinstance(selection.get("selected_evidence_ids"), list) or len(selection["selected_evidence_ids"]) > MAX_SELECTED_EVENTS:
        findings.append(finding("block", "invalid-selection", "selected_evidence_ids must be a list of at most five values", "manifest.json"))
    elif not isinstance(selection.get("reason"), str) or not selection["reason"].strip():
        findings.append(finding("block", "invalid-selection", "selection reason must be a non-empty string", "manifest.json"))
    links = manifest.get("links")
    if not isinstance(links, dict) or set(links) != {"judgment_trace"}:
        findings.append(finding("block", "invalid-links", "links must contain only judgment_trace", "manifest.json"))
    files = manifest.get("files")
    expected_files = {
        "mission_summary_json": "mission-summary.json",
        "mission_summary_markdown": "mission-summary.md",
        "selected_event": "selected-event.json",
        "selected_evidence": "selected-evidence.json",
        "pulse": "pulse.json",
        "privacy_scan": "privacy-scan.json",
        "privacy_notice": "README.md",
    }
    if not isinstance(files, dict) or set(files) != set(expected_files) | {"excerpts"}:
        findings.append(finding("block", "invalid-files-index", "files index fields are invalid", "manifest.json"))
    else:
        for field, expected in expected_files.items():
            if files.get(field) != expected:
                findings.append(finding("block", "invalid-files-index", f"{field} must be {expected}", "manifest.json"))
        if not isinstance(files.get("excerpts"), list):
            findings.append(finding("block", "invalid-files-index", "files.excerpts must be a list", "manifest.json"))
        else:
            for index, value in enumerate(files["excerpts"]):
                if not isinstance(value, str) or not re.fullmatch(r"excerpts/[A-Za-z0-9._-]+", value):
                    findings.append(finding("block", "invalid-excerpt-path", f"files.excerpts[{index}] is not a safe path", "manifest.json"))
    return findings


def validate_tplan_case_packet(package_dir: Path) -> list[Finding]:
    """Validate bounded TPlan packet shape without judging case relevance."""

    findings: list[Finding] = []
    if not package_dir.is_dir() or package_dir.is_symlink():
        return [finding("block", "invalid-package", f"package must be a regular directory: {package_dir}")]
    for path in package_dir.rglob("*"):
        rel = path.relative_to(package_dir).as_posix()
        if path.is_symlink():
            findings.append(finding("block", "symlink-forbidden", f"symlink is not allowed: {rel}", rel))
            continue
        if any(part in TPLAN_FORBIDDEN_NAMES for part in path.relative_to(package_dir).parts):
            findings.append(finding("block", "raw-runtime-forbidden", f"raw TPlan runtime path is forbidden: {rel}", rel))
    for child in package_dir.iterdir():
        if child.is_file() and child.name not in TPLAN_ALLOWED_ROOT_FILES:
            findings.append(finding("block", "unexpected-file", f"unexpected root file: {child.name}", child.name))
        elif child.is_dir() and child.name != "excerpts":
            findings.append(finding("block", "unexpected-directory", f"unexpected directory: {child.name}", child.name))
    required_files = {
        "manifest.json",
        "mission-summary.json",
        "mission-summary.md",
        "selected-event.json",
        "selected-evidence.json",
        "pulse.json",
        "privacy-scan.json",
        "README.md",
    }
    for name in sorted(required_files):
        if not (package_dir / name).is_file():
            findings.append(finding("block", "missing-file", f"missing required file: {name}", name))

    manifest: dict[str, Any] | None = None
    if (package_dir / "manifest.json").is_file():
        value = _validation_json(package_dir / "manifest.json", findings, "manifest.json")
        manifest = value if isinstance(value, dict) else None
        findings.extend(_validate_tplan_manifest(value))
        if manifest and isinstance(manifest.get("case_id"), str):
            expected = f"mindthus-tplan-case-{manifest['case_id']}"
            if package_dir.name != expected:
                findings.append(finding("block", "package-name-mismatch", f"package directory must be named {expected}", package_dir.name))

    summary = _validation_json(package_dir / "mission-summary.json", findings, "mission-summary.json") if (package_dir / "mission-summary.json").is_file() else None
    if not isinstance(summary, dict) or summary.get("schema_version") != TPLAN_CASE_SUMMARY_SCHEMA_VERSION:
        findings.append(finding("block", "invalid-summary", "mission-summary.json schema is invalid", "mission-summary.json"))
    selected = _validation_json(package_dir / "selected-evidence.json", findings, "selected-evidence.json") if (package_dir / "selected-evidence.json").is_file() else None
    if not isinstance(selected, list) or len(selected) > MAX_SELECTED_EVENTS:
        findings.append(finding("block", "invalid-selection", f"selected evidence must contain at most {MAX_SELECTED_EVENTS} events", "selected-evidence.json"))
    elif any(not isinstance(item, dict) or set(item) - {"id", "timestamp", "event_type", "task_id", "summary"} for item in selected):
        findings.append(finding("block", "unbounded-event", "selected evidence contains unsupported event fields", "selected-evidence.json"))
    primary = _validation_json(package_dir / "selected-event.json", findings, "selected-event.json") if (package_dir / "selected-event.json").is_file() else None
    if primary is not None and (not isinstance(primary, dict) or set(primary) - {"id", "timestamp", "event_type", "task_id", "summary"}):
        findings.append(finding("block", "unbounded-event", "selected event contains unsupported fields", "selected-event.json"))
    if manifest and isinstance(manifest.get("selection"), dict) and isinstance(selected, list):
        actual_ids = [item.get("id") for item in selected if isinstance(item, dict)]
        if manifest["selection"].get("selected_evidence_ids") != actual_ids:
            findings.append(finding("block", "selection-index-mismatch", "selected_evidence_ids do not match selected-evidence.json", "manifest.json"))
        primary_id = primary.get("id") if isinstance(primary, dict) else None
        if manifest["selection"].get("selected_event_id") != primary_id:
            findings.append(finding("block", "selection-index-mismatch", "selected_event_id does not match selected-event.json", "manifest.json"))

    trace_path = package_dir / "judgment-trace.json"
    if trace_path.exists():
        if not trace_path.is_file() or trace_path.is_symlink():
            findings.append(finding("block", "invalid-trace", "judgment-trace.json must be a regular file", "judgment-trace.json"))
        else:
            value = _validation_json(trace_path, findings, "judgment-trace.json")
            for item in validate_judgment_trace(value):
                findings.append(finding(item.severity, f"trace-{item.code}", item.message, "judgment-trace.json"))
    if manifest and isinstance(manifest.get("links"), dict):
        declared_trace = manifest["links"].get("judgment_trace")
        actual_trace = "judgment-trace.json" if trace_path.is_file() else None
        if declared_trace != actual_trace:
            findings.append(finding("block", "trace-link-mismatch", "manifest judgment_trace link does not match package contents", "manifest.json"))

    actual_excerpts: set[str] = set()
    excerpt_dir = package_dir / "excerpts"
    if excerpt_dir.exists():
        if not excerpt_dir.is_dir() or excerpt_dir.is_symlink():
            findings.append(finding("block", "invalid-excerpts", "excerpts must be a regular directory", "excerpts"))
        else:
            for path in excerpt_dir.rglob("*"):
                if not path.is_file() or path.is_symlink():
                    findings.append(finding("block", "invalid-excerpt", f"invalid excerpt entry: {path}", "excerpts"))
                    continue
                actual_excerpts.add(path.relative_to(package_dir).as_posix())
                if path.stat().st_size > MAX_EXCERPT_BYTES:
                    findings.append(finding("block", "excerpt-too-large", f"excerpt exceeds size limit: {path.name}", path.name))
    if manifest and isinstance(manifest.get("files"), dict):
        declared = set(str(value) for value in manifest["files"].get("excerpts", []))
        if declared != actual_excerpts:
            findings.append(finding("block", "excerpt-index-mismatch", "manifest excerpt index does not match package files", "manifest.json"))
        privacy = manifest.get("privacy") if isinstance(manifest.get("privacy"), dict) else {}
        if privacy.get("contains_user_selected_excerpts") is not bool(actual_excerpts):
            findings.append(finding("block", "excerpt-privacy-mismatch", "excerpt privacy flag does not match package contents", "manifest.json"))

    content_findings: list[Finding] = []
    for path in package_dir.rglob("*"):
        if not path.is_file() or path.is_symlink() or path.name == "privacy-scan.json":
            continue
        if path.suffix.lower() not in {".json", ".md", ".txt"}:
            findings.append(finding("block", "unsupported-content", f"unsupported content type: {path.name}", path.name))
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(finding("block", "non-utf8-content", f"file must be UTF-8 text: {path.name}", path.name))
            continue
        subject = path.relative_to(package_dir).as_posix()
        content_findings.extend(scan_text(text, subject))
        content_findings.extend(_raw_tplan_content_findings(text, subject))
    findings.extend(content_findings)

    privacy_path = package_dir / "privacy-scan.json"
    if privacy_path.is_file():
        privacy_scan = _validation_json(privacy_path, findings, "privacy-scan.json")
        warning_codes = sorted({item.code for item in content_findings if item.severity == "warn"})
        expected_status = "warnings" if warning_codes else "passed"
        if not isinstance(privacy_scan, dict):
            findings.append(finding("block", "invalid-privacy-scan", "privacy-scan.json must be an object", "privacy-scan.json"))
        else:
            if privacy_scan.get("status") != expected_status:
                findings.append(finding("block", "scan-status-mismatch", f"privacy scan status should be {expected_status}", "privacy-scan.json"))
            if sorted(privacy_scan.get("warning_codes") or []) != warning_codes:
                findings.append(finding("block", "scan-warning-mismatch", "privacy scan warning_codes do not match actual scan", "privacy-scan.json"))
        if manifest and isinstance(manifest.get("privacy"), dict):
            if manifest["privacy"].get("pattern_scan_status") != expected_status:
                findings.append(finding("block", "scan-status-mismatch", "manifest pattern_scan_status does not match actual scan", "manifest.json"))
    return findings


def _case_package_descriptor(package_dir: Path) -> tuple[dict[str, Any], list[Finding]]:
    """Return a bounded collection descriptor after validating one case package."""

    manifest_path = package_dir / "manifest.json"
    if not package_dir.is_dir() or package_dir.is_symlink() or not manifest_path.is_file():
        raise CasePrepError(f"case package must be a regular directory with manifest.json: {package_dir}")
    manifest = _json_load(manifest_path)
    if not isinstance(manifest, dict):
        raise CasePrepError(f"case package manifest must be an object: {manifest_path}")
    schema = manifest.get("schema_version")
    if schema == "mindthus.case-export.v1":
        findings = validate_case_package(package_dir)
        descriptor = {
            "case_id": manifest.get("case_id"),
            "mode": "judgment",
            "case_type": manifest.get("case_type"),
            "focus": None,
            "source_schema": schema,
            "package_name": package_dir.name,
        }
    elif schema == TPLAN_CASE_PACKET_SCHEMA_VERSION:
        findings = validate_tplan_case_packet(package_dir)
        descriptor = {
            "case_id": manifest.get("case_id"),
            "mode": "tplan",
            "case_type": "tplan_case",
            "focus": manifest.get("focus"),
            "source_schema": schema,
            "package_name": package_dir.name,
        }
    else:
        raise CasePrepError(f"unsupported case package schema {schema!r}: {manifest_path}")
    blocks = [item for item in findings if item.severity == "block"]
    if blocks:
        raise CasePrepError(blocks)
    case_id = descriptor.get("case_id")
    if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
        raise CasePrepError(f"case package has invalid case_id: {package_dir}")
    descriptor["path"] = f"cases/{package_dir.name}"
    return descriptor, findings


def _collection_index(title: str, items: list[dict[str, Any]]) -> str:
    lines = [f"# {title}", "", "Every item remains an independently validated case package.", ""]
    for index, item in enumerate(items, 1):
        details = [f"mode={item['mode']}", f"type={item['case_type']}"]
        if item.get("focus"):
            details.append(f"focus={item['focus']}")
        lines.append(f"{index}. `{item['case_id']}` — " + ", ".join(details))
        lines.append(f"   - `{item['path']}`")
    lines.extend(
        [
            "",
            "This index is an inventory, not proof that every candidate is distinct, correct, or ready for benchmark admission.",
        ]
    )
    return "\n".join(lines) + "\n"


def _collection_readme() -> str:
    return """# Mindthus Case Collection

This collection was prepared locally at the user's explicit request. It has not been uploaded.

Before sharing:

1. Read `index.md` and every nested case package.
2. Confirm duplicated or low-value candidates were not included.
3. Review each nested `privacy-scan.json`, manifest, summary, trace, and excerpt.
4. Run the collection validator again after any manual edit.
5. Share the archive only through a separate explicit action.

The collection preserves separate Judgment and TPlan contracts. It does not merge all
cases into one Judgment Trace, and it does not prove anonymity or analytical value.
"""


def _nested_warning_codes(package_dir: Path, findings: list[Finding]) -> list[str]:
    codes = {item.code for item in findings if item.severity == "warn"}
    privacy_path = package_dir / "privacy-scan.json"
    if privacy_path.is_file():
        value = _json_load(privacy_path)
        if isinstance(value, dict) and isinstance(value.get("warning_codes"), list):
            codes.update(str(code) for code in value["warning_codes"] if isinstance(code, str))
    return sorted(codes)


def prepare_case_collection(
    *,
    case_dirs: list[Path],
    output_root: Path,
    collection_id: str | None = None,
    title: str = "Current Mindthus Case Collection",
) -> dict[str, Any]:
    """Package independently validated cases into one review-required collection."""

    if not case_dirs:
        raise CasePrepError("collection requires at least one prepared case directory")
    if len(case_dirs) > MAX_COLLECTION_CASES:
        raise CasePrepError(f"collection supports at most {MAX_COLLECTION_CASES} cases")
    if not isinstance(title, str) or not title.strip():
        raise CasePrepError("collection title must be a non-empty string")

    sources: list[Path] = []
    descriptors: list[dict[str, Any]] = []
    warning_codes: set[str] = set()
    seen_paths: set[Path] = set()
    seen_case_ids: set[str] = set()
    for raw in case_dirs:
        source = raw.expanduser().resolve()
        if source in seen_paths:
            raise CasePrepError(f"duplicate case package path: {source}")
        seen_paths.add(source)
        descriptor, findings = _case_package_descriptor(source)
        if descriptor["case_id"] in seen_case_ids:
            raise CasePrepError(f"duplicate case_id in collection: {descriptor['case_id']}")
        seen_case_ids.add(descriptor["case_id"])
        sources.append(source)
        descriptors.append(descriptor)
        warning_codes.update(_nested_warning_codes(source, findings))

    resolved_id = _safe_case_id(
        collection_id
        or f"collection-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{secrets.token_hex(3)}"
    )
    output_root = output_root.expanduser().resolve()
    package_dir = output_root / f"mindthus-case-collection-{resolved_id}"
    for source in sources:
        if source == package_dir or source in package_dir.parents or package_dir in source.parents:
            raise CasePrepError("collection output must stay outside every source case package")
    if package_dir.exists():
        raise CasePrepError(f"refusing to overwrite existing collection: {package_dir}")

    index_text = _collection_index(title.strip(), descriptors)
    root_findings = scan_text(index_text + _collection_readme(), "collection metadata")
    root_blocks = [item for item in root_findings if item.severity == "block"]
    if root_blocks:
        raise CasePrepError(root_blocks)
    warning_codes.update(item.code for item in root_findings if item.severity == "warn")
    scan_status = "warnings" if warning_codes else "passed"

    output_root.mkdir(parents=True, exist_ok=True)
    package_dir.mkdir()
    try:
        cases_root = package_dir / "cases"
        cases_root.mkdir()
        for source in sources:
            shutil.copytree(source, cases_root / source.name)
        (package_dir / "index.md").write_text(index_text, encoding="utf-8")
        (package_dir / "README.md").write_text(_collection_readme(), encoding="utf-8")
        _write_json(
            package_dir / "privacy-scan.json",
            {
                "schema_version": "mindthus.case-collection-privacy-scan.v1",
                "status": scan_status,
                "warning_codes": sorted(warning_codes),
                "note": "Aggregate of collection metadata and nested case warnings; manual review remains required.",
            },
        )
        manifest = {
            "schema_version": CASE_COLLECTION_SCHEMA_VERSION,
            "collection_id": resolved_id,
            "created_at_utc": now_iso(),
            "mode": "collection",
            "title": title.strip(),
            "consent": {
                "export_requested_by_user": True,
                "review_required_before_share": True,
                "automatic_upload": False,
            },
            "privacy": {
                "contains_raw_conversation": False,
                "contains_full_tplan_runtime": False,
                "redaction_status": "review_required",
                "pattern_scan_status": scan_status,
            },
            "items": descriptors,
            "files": {
                "index": "index.md",
                "privacy_scan": "privacy-scan.json",
                "privacy_notice": "README.md",
                "cases": [item["path"] for item in descriptors],
            },
        }
        _write_json(package_dir / "manifest.json", manifest)
    except Exception:
        shutil.rmtree(package_dir, ignore_errors=True)
        raise

    findings = validate_case_collection(package_dir)
    blocks = [item for item in findings if item.severity == "block"]
    if blocks:
        shutil.rmtree(package_dir, ignore_errors=True)
        raise CasePrepError(blocks)
    archive_path = _archive_directory(package_dir)
    return _judgment_result(
        mode="collection",
        package_dir=package_dir,
        archive_path=archive_path,
        case_type="case_collection",
        warnings=sorted({item.code for item in findings if item.severity == "warn"}),
        item_count=len(descriptors),
    )


def _validate_collection_manifest(manifest: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(manifest, dict):
        return [finding("block", "invalid-manifest", "collection manifest root must be an object")]
    required = {
        "schema_version",
        "collection_id",
        "created_at_utc",
        "mode",
        "title",
        "consent",
        "privacy",
        "items",
        "files",
    }
    for field in sorted(required - set(manifest)):
        findings.append(finding("block", "missing-field", f"missing collection field: {field}", "manifest.json"))
    for field in sorted(set(manifest) - required):
        findings.append(finding("block", "unknown-field", f"unsupported collection field: {field}", "manifest.json"))
    if manifest.get("schema_version") != CASE_COLLECTION_SCHEMA_VERSION:
        findings.append(finding("block", "unsupported-schema", "unsupported case collection schema", "manifest.json"))
    collection_id = manifest.get("collection_id")
    if not isinstance(collection_id, str) or not CASE_ID_RE.fullmatch(collection_id):
        findings.append(finding("block", "invalid-collection-id", "collection_id is invalid", "manifest.json"))
    if manifest.get("mode") != "collection":
        findings.append(finding("block", "invalid-mode", "collection mode must be collection", "manifest.json"))
    if not isinstance(manifest.get("title"), str) or not manifest["title"].strip():
        findings.append(finding("block", "invalid-title", "collection title must be non-empty", "manifest.json"))
    consent = manifest.get("consent")
    if not isinstance(consent, dict) or set(consent) != {
        "export_requested_by_user",
        "review_required_before_share",
        "automatic_upload",
    }:
        findings.append(finding("block", "invalid-consent", "collection consent fields are invalid", "manifest.json"))
    else:
        if consent.get("export_requested_by_user") is not True:
            findings.append(finding("block", "consent-required", "export_requested_by_user must be true", "manifest.json"))
        if consent.get("review_required_before_share") is not True:
            findings.append(finding("block", "review-required", "review_required_before_share must be true", "manifest.json"))
        if consent.get("automatic_upload") is not False:
            findings.append(finding("block", "automatic-upload-forbidden", "automatic_upload must be false", "manifest.json"))
    privacy = manifest.get("privacy")
    if not isinstance(privacy, dict) or set(privacy) != {
        "contains_raw_conversation",
        "contains_full_tplan_runtime",
        "redaction_status",
        "pattern_scan_status",
    }:
        findings.append(finding("block", "invalid-privacy", "collection privacy fields are invalid", "manifest.json"))
    else:
        if privacy.get("contains_raw_conversation") is not False:
            findings.append(finding("block", "raw-conversation-forbidden", "contains_raw_conversation must be false", "manifest.json"))
        if privacy.get("contains_full_tplan_runtime") is not False:
            findings.append(finding("block", "raw-runtime-forbidden", "contains_full_tplan_runtime must be false", "manifest.json"))
        if privacy.get("redaction_status") != "review_required":
            findings.append(finding("block", "review-required", "redaction_status must remain review_required", "manifest.json"))
        if privacy.get("pattern_scan_status") not in {"passed", "warnings"}:
            findings.append(finding("block", "invalid-scan-status", "pattern_scan_status must be passed or warnings", "manifest.json"))
    created_at = manifest.get("created_at_utc")
    if not isinstance(created_at, str):
        findings.append(finding("block", "invalid-created-at", "created_at_utc must be an ISO-8601 string", "manifest.json"))
    else:
        try:
            parsed_created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            findings.append(finding("block", "invalid-created-at", "created_at_utc must be ISO-8601", "manifest.json"))
        else:
            if parsed_created_at.tzinfo is None:
                findings.append(finding("block", "invalid-created-at", "created_at_utc must include a timezone", "manifest.json"))
    items = manifest.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= MAX_COLLECTION_CASES:
        findings.append(finding("block", "invalid-items", f"items must contain 1-{MAX_COLLECTION_CASES} cases", "manifest.json"))
    else:
        expected_item_fields = {
            "case_id",
            "mode",
            "case_type",
            "focus",
            "source_schema",
            "package_name",
            "path",
        }
        case_ids: set[str] = set()
        paths: set[str] = set()
        for index, item in enumerate(items):
            subject = f"manifest.items[{index}]"
            if not isinstance(item, dict) or set(item) != expected_item_fields:
                findings.append(finding("block", "invalid-item", "collection item fields are invalid", subject))
                continue
            case_id = item.get("case_id")
            if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
                findings.append(finding("block", "invalid-case-id", "collection item case_id is invalid", subject))
            elif case_id in case_ids:
                findings.append(finding("block", "duplicate-case-id", f"duplicate case_id: {case_id}", subject))
            else:
                case_ids.add(case_id)
            mode = item.get("mode")
            schema = item.get("source_schema")
            if mode not in {"judgment", "tplan"}:
                findings.append(finding("block", "invalid-item-mode", "collection item mode is invalid", subject))
            if schema not in {"mindthus.case-export.v1", TPLAN_CASE_PACKET_SCHEMA_VERSION}:
                findings.append(finding("block", "invalid-item-schema", "collection item source_schema is invalid", subject))
            if mode == "judgment" and schema != "mindthus.case-export.v1":
                findings.append(finding("block", "item-contract-mismatch", "judgment item must use Case Export v1", subject))
            if mode == "tplan" and schema != TPLAN_CASE_PACKET_SCHEMA_VERSION:
                findings.append(finding("block", "item-contract-mismatch", "TPlan item must use tplan.case-packet.v1", subject))
            if not isinstance(item.get("case_type"), str) or not item["case_type"].strip():
                findings.append(finding("block", "invalid-case-type", "collection item case_type is invalid", subject))
            if item.get("focus") is not None and (not isinstance(item.get("focus"), str) or not item["focus"].strip()):
                findings.append(finding("block", "invalid-focus", "collection item focus must be null or non-empty", subject))
            package_name = item.get("package_name")
            path = item.get("path")
            if not isinstance(package_name, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", package_name):
                findings.append(finding("block", "invalid-package-name", "collection item package_name is invalid", subject))
            expected_path = f"cases/{package_name}" if isinstance(package_name, str) else None
            if path != expected_path or not isinstance(path, str) or not re.fullmatch(r"cases/[A-Za-z0-9._-]+", path):
                findings.append(finding("block", "invalid-case-path", "collection item path is invalid", subject))
            elif path in paths:
                findings.append(finding("block", "duplicate-case-path", f"duplicate case path: {path}", subject))
            else:
                paths.add(path)
    return findings


def validate_case_collection(package_dir: Path) -> list[Finding]:
    """Validate a collection and every independently packaged nested case."""

    findings: list[Finding] = []
    if not package_dir.is_dir() or package_dir.is_symlink():
        return [finding("block", "invalid-package", f"collection must be a regular directory: {package_dir}")]
    for path in package_dir.rglob("*"):
        if path.is_symlink():
            findings.append(finding("block", "symlink-forbidden", f"symlink is not allowed: {path}", str(path)))
    for child in package_dir.iterdir():
        if child.is_file() and child.name not in COLLECTION_ALLOWED_ROOT_FILES:
            findings.append(finding("block", "unexpected-file", f"unexpected collection file: {child.name}", child.name))
        elif child.is_dir() and child.name != "cases":
            findings.append(finding("block", "unexpected-directory", f"unexpected collection directory: {child.name}", child.name))
    for name in COLLECTION_ALLOWED_ROOT_FILES:
        if not (package_dir / name).is_file():
            findings.append(finding("block", "missing-file", f"missing collection file: {name}", name))
    cases_root = package_dir / "cases"
    if not cases_root.is_dir() or cases_root.is_symlink():
        findings.append(finding("block", "missing-cases", "collection cases directory is missing or invalid", "cases"))

    manifest = _validation_json(package_dir / "manifest.json", findings, "manifest.json") if (package_dir / "manifest.json").is_file() else None
    findings.extend(_validate_collection_manifest(manifest))
    if isinstance(manifest, dict) and isinstance(manifest.get("collection_id"), str):
        expected_name = f"mindthus-case-collection-{manifest['collection_id']}"
        if package_dir.name != expected_name:
            findings.append(finding("block", "package-name-mismatch", f"collection directory must be named {expected_name}", package_dir.name))

    actual_descriptors: list[dict[str, Any]] = []
    nested_warning_codes: set[str] = set()
    if cases_root.is_dir():
        for child in sorted(cases_root.iterdir()):
            if not child.is_dir() or child.is_symlink():
                findings.append(finding("block", "invalid-case-entry", f"nested case must be a directory: {child.name}", child.name))
                continue
            try:
                descriptor, nested_findings = _case_package_descriptor(child)
            except CasePrepError as exc:
                findings.extend(
                    finding(item.severity, f"nested-{item.code}", item.message, f"cases/{child.name}")
                    for item in exc.findings
                )
                continue
            actual_descriptors.append(descriptor)
            nested_warning_codes.update(_nested_warning_codes(child, nested_findings))
    actual_descriptors.sort(key=lambda item: item["path"])

    if isinstance(manifest, dict) and isinstance(manifest.get("items"), list):
        declared = sorted(manifest["items"], key=lambda item: str(item.get("path")) if isinstance(item, dict) else "")
        if declared != actual_descriptors:
            findings.append(finding("block", "collection-index-mismatch", "manifest items do not match nested case packages", "manifest.json"))
        files = manifest.get("files")
        expected_files = {
            "index": "index.md",
            "privacy_scan": "privacy-scan.json",
            "privacy_notice": "README.md",
            "cases": [item["path"] for item in manifest["items"]],
        }
        if files != expected_files:
            findings.append(finding("block", "invalid-files-index", "collection files index is invalid", "manifest.json"))

    root_findings: list[Finding] = []
    for name in ("index.md", "README.md"):
        path = package_dir / name
        if path.is_file():
            try:
                root_findings.extend(scan_text(path.read_text(encoding="utf-8"), name))
            except UnicodeDecodeError:
                findings.append(finding("block", "non-utf8-content", f"{name} must be UTF-8", name))
    findings.extend(root_findings)
    expected_warning_codes = sorted(
        nested_warning_codes | {item.code for item in root_findings if item.severity == "warn"}
    )
    expected_scan_status = "warnings" if expected_warning_codes else "passed"
    privacy_scan = _validation_json(package_dir / "privacy-scan.json", findings, "privacy-scan.json") if (package_dir / "privacy-scan.json").is_file() else None
    if not isinstance(privacy_scan, dict):
        findings.append(finding("block", "invalid-privacy-scan", "collection privacy-scan.json must be an object", "privacy-scan.json"))
    else:
        if privacy_scan.get("status") != expected_scan_status:
            findings.append(finding("block", "scan-status-mismatch", f"collection scan status should be {expected_scan_status}", "privacy-scan.json"))
        if sorted(privacy_scan.get("warning_codes") or []) != expected_warning_codes:
            findings.append(finding("block", "scan-warning-mismatch", "collection warning_codes do not match nested cases", "privacy-scan.json"))
    if isinstance(manifest, dict) and isinstance(manifest.get("privacy"), dict):
        if manifest["privacy"].get("pattern_scan_status") != expected_scan_status:
            findings.append(finding("block", "scan-status-mismatch", "manifest pattern_scan_status does not match collection", "manifest.json"))
    return findings

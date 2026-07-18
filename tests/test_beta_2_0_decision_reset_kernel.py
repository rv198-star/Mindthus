from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KERNEL_PATH = ROOT / "beta/2.0.0-beta.2/runtime/decision_reset_kernel.py"
SPEC = importlib.util.spec_from_file_location("decision_reset_kernel", KERNEL_PATH)
assert SPEC and SPEC.loader
KERNEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(KERNEL)


def test_explicit_infrastructure_receipt_dominates_progress() -> None:
    assert KERNEL.classify_attempt({"content": "progress_only", "provider_code": "503"}) == "INFRA_NONCOMPLETION"
    assert KERNEL.classify_attempt({"content": "progress_only"}) == "PRODUCT_NONCOMPLETION"


def test_cut_seals_source_prefix_and_late_event_is_audit_only(tmp_path: Path) -> None:
    runtime = KERNEL.DecisionRuntime(tmp_path)
    runtime.append_source("attempt", {"content": "final_nonempty", "claims": {"C1": "PASS"}}, event_id="a1")
    cut = runtime.seal_cut(reason="test")
    runtime.append_audit("provider_error", {"provider_code": "503"}, event_id="late")
    receipt = runtime.terminal_receipt()
    assert receipt["action"] == "CONTINUE_BETA"
    assert receipt["cut_digest"] == cut["digest"]


def test_pre_cut_unresolved_claim_stops_unproven(tmp_path: Path) -> None:
    runtime = KERNEL.DecisionRuntime(tmp_path)
    runtime.append_source("attempt", {"content": "final_nonempty", "claims": {"C1": "PASS"}}, event_id="a1")
    runtime.append_source("attempt", {"content": "unknown", "claims": {"C1": "UNRESOLVED"}}, event_id="a2")
    runtime.seal_cut(reason="test")
    assert runtime.terminal_receipt()["action"] == "STOP_UNPROVEN"


def test_duplicate_event_is_idempotent(tmp_path: Path) -> None:
    runtime = KERNEL.DecisionRuntime(tmp_path)
    first = runtime.append_source("attempt", {"content": "final_empty"}, event_id="a1")
    second = runtime.append_source("attempt", {"content": "final_empty"}, event_id="a1")
    assert first == second
    assert len(runtime.ledger.records()) == 1


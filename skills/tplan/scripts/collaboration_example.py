#!/usr/bin/env python3
"""Packaged cold-start closed loop for TPlan collaboration (Issue #246 R10).

Self-contained: uses only the packaged init_mission.py and collaboration_runtime.py
next to this script. Runs snapshot.get -> enable -> delegation.prepare ->
dispatch.record -> feedback.record -> feedback.resolve -> snapshot.get -> command.get
against a fresh demo Mission. See ../resources/collaboration-protocol.md.

Usage: python3 collaboration_example.py --work-dir /tmp/tplan-collab-demo
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
PROTOCOL = "tplan.collaboration.command.v1"


def run_script(name, *args):
    result = subprocess.run([sys.executable, "-B", str(SCRIPTS / name), *args],
                            text=True, capture_output=True, timeout=60)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", help="Directory for the demo Mission (default: temp)")
    args = parser.parse_args()
    work = Path(args.work_dir) if args.work_dir else Path(tempfile.mkdtemp(prefix="tplan-collab-demo-"))
    work.mkdir(parents=True, exist_ok=True)
    mission = work / "demo-mission"
    tasks_file = work / "tasks.json"
    tasks_file.write_text(json.dumps([
        {"id": "T1", "title": "Implement demo result", "role": "success-critical",
         "mission_contribution": "Delivers A1", "acceptance_evidence": ["A1"], "status": "active"},
        {"id": "T2", "title": "Supporting mainline", "role": "supporting",
         "mission_contribution": "Supports A1", "acceptance_evidence": []},
    ]))
    init = run_script("init_mission.py", "--dir", str(mission), "--mission-id", "demo-mission",
                      "--title", "Collaboration demo", "--objective", "Demonstrate the packaged collaboration closed loop",
                      "--acceptance-evidence", "A1:Demo result verified", "--task-json", str(tasks_file))
    if init.returncode != 0:
        print("init failed:", init.stderr)
        return 1
    state = json.loads((mission / "mission.json").read_text())
    build = state["runtime_provenance"]["fingerprint"]["build_hash"]
    counter = {"n": 0}

    def collab(action, payload, expected=None, command_id=None):
        counter["n"] += 1
        request = {"protocol": PROTOCOL, "action": action, "mission_id": "demo-mission",
                   "command_id": command_id or f"demo-{counter['n']}", "expected_build_hash": build,
                   "expected_snapshot": expected, "payload": payload}
        req_file = work / f"request-{counter['n']}.json"
        req_file.write_text(json.dumps(request))
        result = run_script("collaboration_runtime.py", "--mission-dir", str(mission),
                            "--principal", "coordinator-a", "--request-file", str(req_file))
        try:
            resp = json.loads(result.stdout)
        except ValueError:
            print("non-JSON response:", result.stdout, result.stderr)
            raise SystemExit(1)
        return resp, result.returncode

    snap, code = collab("snapshot.get", {}, expected=None)
    assert code == 0, snap
    expected = snap["data"]["expected_snapshot"]

    enable_payload = {
        "coordinator": {"thread_ref": "thread-a", "host_ref": "local",
                        "responsibility": "Own the user outcome and acceptance",
                        "communication_authorization_refs": ["user-turn-1"]},
        "participants": [
            {"participant_id": "B", "thread_ref": "thread-b", "host_ref": "local",
             "responsibility": "Implement bounded work", "communication_authorization_refs": ["user-turn-1"]},
            {"participant_id": "C", "thread_ref": "thread-c", "host_ref": "local",
             "responsibility": "Review current artifacts", "communication_authorization_refs": ["user-turn-1"]}],
        "policy": {"max_pending_feedback": 128, "processing_deadline_seconds": 900}}
    resp, code = collab("enable", enable_payload, expected=expected)
    assert code == 0, resp
    expected = resp["data"]["expected_snapshot"]

    delegation = {"coordinator_generation": 1, "delegation_id": "D1", "intent_id": "I1", "task_id": "T1",
                  "round": 1, "assignee_id": "B", "write_scope": "workspace/T1", "contract_version": "contract-r1",
                  "instruction_summary": "Implement the demo result", "input_refs": ["artifact://T1/input"],
                  "dependency_versions": {"design": "v1"},
                  "required_review": {"required": True, "reviewer_id": "C", "scope_refs": ["scope://T1"]}}
    resp, code = collab("delegation.prepare", delegation, expected=expected)
    assert code == 0, resp
    expected = resp["data"]["expected_snapshot"]

    dispatch = {"coordinator_generation": 1, "intent_id": "I1", "send_state": "confirmed",
                "execution_state": "completed", "stop_requested": False,
                "native_refs": ["thread://b/message/I1"], "observed_at": "2026-11-17T00:00:00+00:00",
                "reason": "Demo dispatch observed"}
    resp, code = collab("dispatch.record", dispatch, expected=expected)
    assert code == 0, resp
    expected = resp["data"]["expected_snapshot"]

    digest = "sha256:" + hashlib.sha256(b"demo artifact h1").hexdigest()
    feedback = {"coordinator_generation": 1, "kind": "result", "source_event_ref": "msg-h1",
                "source_thread_ref": "thread-c", "source_host_ref": "local", "source_role_id": "C",
                "delegation_id": "D1", "round": 1, "contract_version": "contract-r1",
                "artifact_ref": "artifact://h1", "artifact_digest": digest,
                "summary": "C reviewed the demo result", "original_ref": "thread://source/msg-h1",
                "attachment_refs": []}
    resp, code = collab("feedback.record", feedback, expected=expected)
    assert code == 0, resp
    feedback_id = resp["data"]["feedback_id"]
    expected = resp["data"]["expected_snapshot"]

    resolve = {"coordinator_generation": 1, "feedback_id": feedback_id, "disposition": "adopted",
               "goal_relation": {"responsibility": "Own acceptance", "acceptance_ids": ["A1"],
                                 "rationale": "Current artifact matches the objective"},
               "evidence_refs": [],
               "artifact_ref": {"ref": "artifact://h1", "digest": digest, "contract_version": "contract-r1", "round": 1},
               "review": {"reviewer_id": "C", "delegation_id": "D1", "round": 1, "contract_version": "contract-r1",
                          "artifact_ref": "artifact://h1", "artifact_digest": digest,
                          "scope_refs": ["scope://T1"], "verdict": "PASS", "rationale": "Demo review PASS"},
               "task_changes": [{"task_id": "T1", "status": "completed"}],
               "new_tasks": [], "next_delegation": None,
               "coordination": {"state": "working", "focus_task_id": "T2",
                                "gap_summary": "Demo acceptance adopted", "next_action": "Continue supporting mainline",
                                "resume_basis": ["T2"], "waiting_on": [], "rationale": "Demo closed loop"}}
    resolve_command = "demo-resolve"
    resp, code = collab("feedback.resolve", resolve, expected=expected, command_id=resolve_command)
    assert code == 0, resp
    expected = resp["data"]["expected_snapshot"]

    snap, code = collab("snapshot.get", {}, expected=None)
    assert code == 0, snap
    assert snap["data"]["expected_snapshot"] == expected, "write response snapshot must match current state"
    assert "D1" in snap["data"]["collaboration"]["adoptions"], "adoption must be present"

    hist, code = collab("command.get", {}, expected=None, command_id=resolve_command)
    assert code == 0, hist
    assert hist["data"]["data"]["feedback_id"] == feedback_id

    print(json.dumps({"closed_loop": "ok", "mission_dir": str(mission),
                      "steps": ["snapshot.get", "enable", "delegation.prepare", "dispatch.record",
                                "feedback.record", "feedback.resolve", "snapshot.get", "command.get"],
                      "adoption": "D1", "task_T1": "completed"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

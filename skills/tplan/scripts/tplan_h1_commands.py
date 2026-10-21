"""Bounded H1 Host protocol over the existing canonical Mission transaction.

Deployment is DISABLED: no isolated Host trust provisioning exists in this package.
There is deliberately no signer, CLI secret/key argument, env trust or public factory.
Tests patch the private disabled seam; that is not a real authentication boundary.
"""
from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import hmac
import os
import shutil
import stat
import time
import uuid
from pathlib import Path
from typing import Any

from tplan_commands import (CommandError, _check_paths, _load, canonical, digest,
                            valid_id, HASH, _existing_evidence, MAX_ARTIFACT, MAX_STORE, MAX_RECORDS, MIN_FREE)
from tplan_h1 import CHOICES, controlled_task_ids

PROTOCOL = "tplan.h1.command.v1"
CAPABILITY = "scoped_owner_execution_core"
MAX_CONTENT = 256 * 1024
MAX_CANDIDATES = 64
ACTIONS = {"candidate.submit", "decision.open", "request.revise", "decision.apply", "adoption.apply",
           "execution.claim", "receipt.record", "execution.get", "command.get"}
OWNER_FIELDS = {"schema_version", "issuer_id", "key_id", "owner_subject_ref", "origin_binding_ref",
                "mission_id", "request_id", "expected_revision", "choice", "candidate_sha256",
                "origin_session_ref", "origin_event_ref", "issued_at", "expires_at", "nonce", "signature"}
HOST_FIELDS = {"issuer_id", "key_id", "issued_at", "expires_at", "nonce", "request_digest", "signature"}


def _trust_config():
    """Fixed disabled root. Only a future isolated Host build may provision trust.

    Never resolve trust from this call's arguments, filesystem, environment, or
    Mission. Same-uid Python monkeypatching cannot establish a security boundary.
    """
    return None


def _fail(code, message):
    raise CommandError(code, message)


def _fields(value, fields):
    if not isinstance(value, dict) or set(value) != set(fields):
        _fail("invalid_request", "Use the exact versioned H1 fields")


def _id(value):
    if not valid_id(value):
        _fail("invalid_request", "Invalid H1 identity")
    return value


def _hash(value):
    if not isinstance(value, str) or not HASH.fullmatch(value):
        _fail("invalid_request", "Invalid H1 digest")
    return value


def _nonce_key(receipt, kind):
    # Key rotation must not make an already consumed issuer nonce usable again.
    return digest({"kind": kind, "issuer": receipt["issuer_id"], "nonce": receipt["nonce"]})


def _verify(receipt, fields, trust):
    _fields(receipt, fields)
    if (receipt["issuer_id"] != trust["issuer_id"] or receipt["key_id"] != trust["key_id"]):
        _fail("unauthorized", "Receipt issuer is not in the fixed Host trust root")
    signature = receipt["signature"]
    body = {k: v for k, v in receipt.items() if k != "signature"}
    expected = hmac.new(trust["key"], canonical(body).encode("utf-8"), hashlib.sha256).hexdigest()
    if not isinstance(signature, str) or len(signature) != 64 or not hmac.compare_digest(signature, expected):
        _fail("unauthorized", "Receipt signature is invalid")
    issued, expires = receipt["issued_at"], receipt["expires_at"]
    now = int(time.time())
    if (type(issued) is not int or type(expires) is not int or not 1 <= expires - issued <= 300
        or issued > now + 30 or expires <= now):
        _fail("unauthorized", "Receipt is expired or outside its bounded time window")
    _id(receipt["nonce"])


def _request(request):
    _fields(request, {"protocol", "action", "mission_id", "command_id", "expected_build_hash",
                      "payload", "host_receipt"})
    if request["protocol"] != PROTOCOL or request["action"] not in ACTIONS:
        _fail("invalid_request", "Unsupported H1 protocol/action")
    _id(request["mission_id"]); _id(request["command_id"]); _hash(request["expected_build_hash"])
    if not isinstance(request["payload"], dict) or len(canonical(request).encode()) > 384 * 1024:
        _fail("invalid_request", "Invalid or oversized H1 request")


def _content_path(directory, sha, *, create=False):
    _hash(sha)
    parent = directory
    for part in ("artifacts", "h1"):
        parent = parent / part
        if create and not parent.exists():
            parent.mkdir(mode=0o700)
            _fsync_dir(parent.parent)
        if parent.is_symlink() or not parent.is_dir():
            _fail("candidate_unavailable", "Candidate store is unavailable")
    return parent / sha.removeprefix("sha256:")


def _fsync_dir(directory):
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _read_content(directory, sha):
    path = _content_path(directory, sha)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as source:
        info = os.fstat(source.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_CONTENT:
            _fail("candidate_unavailable", "Candidate bytes are not a bounded regular file")
        content = source.read(MAX_CONTENT + 1)
    if "sha256:" + hashlib.sha256(content).hexdigest() != sha:
        _fail("candidate_unavailable", "Candidate bytes no longer match their immutable identity")
    return content


def _store_content(directory, sha, content):
    path = _content_path(directory, sha, create=True)
    temporary = path.parent / (".prepare-" + uuid.uuid4().hex)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError:
            pass  # Verify existing bytes; never replace a file with this identity.
        _fsync_dir(path.parent)
        _read_content(directory, sha)
    finally:
        temporary.unlink(missing_ok=True)


def _candidate(hc, candidate_id):
    candidate = hc["candidates"].get(_id(candidate_id))
    if candidate is None:
        _fail("invalid_request", "Candidate is not recorded")
    return candidate


def _eligibility(directory, candidate):
    try:
        _read_content(directory, candidate["content_sha256"])
        return None if candidate["validity"] == "eligible" else "candidate_ineligible"
    except (CommandError, OSError):
        return "candidate_bytes_unavailable_or_changed"


def _decision_ready(directory, hc, request_id):
    req = hc["requests"].get(_id(request_id))
    if req is None:
        _fail("invalid_request", "Request is not recorded")
    decision = hc["decisions"].get(req["current_decision_id"])
    if (req["status"] != "decided" or not decision or decision["adoption_blocked"]
        or decision["choice"] not in {"approve_current", "withdraw_change"}):
        _fail("waiting", "Current Owner decision does not permit adoption or execution")
    candidate = _candidate(hc, decision["candidate_id"])
    if _eligibility(directory, candidate):
        _fail("candidate_unavailable", "Current candidate bytes cannot be adopted")
    return req, decision, candidate


def _dependency_projection(directory, state, req, candidate, task_id, runtime):
    """Conservative native admission for this one-source core; never a scheduler.

    Owner authority cannot replace completed predecessors, qualified versioned
    acceptance, native dependency declarations, or adopted actual input bytes.
    """
    source_id = req["business_task_id"]
    source = runtime.find_task(state, source_id)
    if source["status"] != "completed":
        _fail("waiting", "H1 source must be completed before dependent execution")
    blocks = state.get("work_plan", {}).get("blocks", [])
    matches = [block for block in blocks if block["task_id"] == task_id]
    if len(matches) != 1 or not isinstance(matches[0].get("depends_on"), list):
        _fail("dependency_unverified", "Native planning dependencies are unknown")
    block = matches[0]
    # This slice can prove adopted input only for its named source. Do not turn
    # an unknown/extra native prerequisite into permission using an Owner choice.
    if set(block["depends_on"]) != {source_id} or block.get("parallel_conditions"):
        _fail("dependency_unverified", "Native prerequisites exceed the verified H1 input scope")
    for blocker in state["work_plan"].get("blockers", []):
        if (blocker.get("status", "active") == "active" and
            (not blocker.get("task_ids") or {source_id,task_id}.intersection(blocker["task_ids"]))):
            _fail("waiting", "An active native plan blocker affects this execution")
    required = runtime._acceptance_coverage_for_task(state, source_id)
    if not required:
        _fail("dependency_unverified", "Source has no declared acceptance coverage")
    latest = {}
    events = runtime._read_events_unlocked(directory)
    seen = set()
    for event in events:
        if event.get("id") in seen:
            _fail("invalid_state", "Ambiguous evidence cannot prove a dependency")
        seen.add(event.get("id"))
        if event.get("task_id") != source_id or event.get("event_type") not in {"acceptance_passed", "acceptance_failed"}:
            continue
        if runtime.validate_evidence_event(state, event, compatibility=True, internal=True):
            _fail("invalid_state", "Source acceptance is not a qualified native record")
        payload = event["payload"]
        bound = (payload.get("candidate_sha256") == candidate["content_sha256"]
                 and payload.get("attempt_ref") == candidate["attempt_ref"])
        global_failure = (event["event_type"] == "acceptance_failed"
                          and "candidate_sha256" not in payload and "attempt_ref" not in payload)
        if bound or global_failure:
            for ac in payload["acceptance_ids"]:
                latest[ac] = event
    accepted = {}
    for ac in sorted(required):
        event = latest.get(ac)
        if (event is None or event["event_type"] != "acceptance_passed"
            or event["payload"].get("candidate_sha256") != candidate["content_sha256"]
            or event["payload"].get("attempt_ref") != candidate["attempt_ref"]):
            _fail("dependency_unverified", "Current adopted source lacks qualified version-bound acceptance")
        accepted[ac] = digest(event)
    return {"source":source, "task":runtime.find_task(state,task_id),
            "depends_on":block["depends_on"],"parallel_conditions":block.get("parallel_conditions"),
            "candidate_id":candidate["candidate_id"],"candidate_sha256":candidate["content_sha256"],
            "qualified_acceptance":accepted}


def _apply(directory, state, request, trust, runtime):
    hc = state["human_control"]
    action, payload = request["action"], request["payload"]
    terminal = state["mission"]["status"] in {"completed", "abandoned", "superseded"}
    if terminal and action not in {"candidate.submit", "receipt.record"}:
        _fail("terminal", "Terminal Missions accept late facts without reopening authority")
    if action == "candidate.submit":
        _fields(payload, {"task_id", "attempt_ref", "content_b64"})
        task_id = _id(payload["task_id"]); _id(payload["attempt_ref"])
        runtime.find_task(state, task_id)
        try:
            content = base64.b64decode(payload["content_b64"], validate=True)
        except (ValueError, TypeError, binascii.Error):
            _fail("invalid_request", "Candidate content must be strict base64")
        if not content or len(content) > MAX_CONTENT:
            _fail("capacity_exceeded", "Candidate bytes exceed the bounded content budget")
        sha = "sha256:" + hashlib.sha256(content).hexdigest()
        candidate_id = "CA" + digest({"task":task_id,"attempt":payload["attempt_ref"],"sha":sha})[7:]
        candidate = {"candidate_id":candidate_id,"task_id":task_id,"attempt_ref":payload["attempt_ref"],
                     "content_sha256":sha,"bytes_ref":"artifacts/h1/"+sha[7:],"validity":"eligible"}
        if candidate_id not in hc["candidates"] and len(hc["candidates"]) >= MAX_CANDIDATES:
            _fail("capacity_exceeded", "Candidate retention budget exhausted")
        # One attempt cannot silently replace its byte identity.
        if any(c["task_id"] == task_id and c["attempt_ref"] == payload["attempt_ref"]
               and c != candidate for c in hc["candidates"].values()):
            _fail("command_conflict", "Attempt already has different immutable content")
        _store_content(directory, sha, content)
        hc["candidates"][candidate_id] = candidate
        return candidate
    if action == "decision.open":
        _fields(payload, {"request_id", "business_task_id", "blocked_task_ids", "candidate_id"})
        request_id = _id(payload["request_id"])
        candidate = _candidate(hc, payload["candidate_id"])
        blocked = payload["blocked_task_ids"]
        if (candidate["task_id"] != payload["business_task_id"] or not isinstance(blocked, list)
            or not blocked or not all(valid_id(t) for t in blocked) or len(blocked) != len(set(blocked))
            or candidate["task_id"] in blocked or request_id in hc["requests"]):
            _fail("invalid_request", "Invalid or already recorded local decision scope")
        for task_id in blocked:
            task = runtime.find_task(state, task_id)
            if task["status"] in {"active", "completed"} or task_id in controlled_task_ids(state, include_source=True):
                _fail("invalid_request", "Cannot open overlapping or already executing scope")
        hc["requests"][request_id] = {"business_task_id":candidate["task_id"],"blocked_task_ids":blocked,
            "status":"pending","revision":1,"required_actor":"owner","allowed_choices":sorted(CHOICES),
            "current_candidate_id":candidate["candidate_id"],"fallback_candidate_id":candidate["candidate_id"],
            "current_decision_id":None}
        return {"request_id":request_id, **hc["requests"][request_id]}
    if action == "request.revise":
        _fields(payload, {"request_id", "expected_revision", "candidate_id"})
        req = hc["requests"].get(_id(payload["request_id"]))
        if (req is None or type(payload["expected_revision"]) is not int
            or req["revision"] != payload["expected_revision"]):
            _fail("stale_revision", "Candidate revision must match the current request")
        previous = hc["decisions"].get(req["current_decision_id"], {})
        if req["status"] != "pending" or previous.get("choice") != "request_changes":
            _fail("waiting", "Candidate revision requires a pending request for changes")
        candidate = _candidate(hc, payload["candidate_id"])
        current = _candidate(hc, req["current_candidate_id"])
        if (candidate["task_id"] != req["business_task_id"]
            or candidate["attempt_ref"] == current["attempt_ref"]):
            _fail("invalid_request", "Revised candidate requires a new same-source attempt")
        if _eligibility(directory, candidate):
            _fail("candidate_unavailable", "Revised candidate bytes are unavailable")
        req.update(current_candidate_id=candidate["candidate_id"],revision=req["revision"]+1)
        hc["adoptions"].pop(payload["request_id"], None)
        return {"request_id":payload["request_id"], **req}
    if action == "decision.apply":
        _fields(payload, {"receipt"})
        receipt = payload["receipt"]
        _verify(receipt, OWNER_FIELDS, trust)
        if (receipt["schema_version"] != "tplan.owner_receipt.v0.1" or receipt["mission_id"] != request["mission_id"]
            or any(receipt[k] != trust[k] for k in ("owner_subject_ref", "origin_binding_ref", "origin_session_ref"))):
            _fail("unauthorized", "Owner receipt is outside the fixed authenticated origin")
        _id(receipt["origin_event_ref"])
        req = hc["requests"].get(_id(receipt["request_id"]))
        if req is None or type(receipt["expected_revision"]) is not int or receipt["expected_revision"] != req["revision"]:
            _fail("stale_revision", "Owner decision must match the current request revision")
        selected_id = req["fallback_candidate_id"] if receipt["choice"] == "withdraw_change" else req["current_candidate_id"]
        candidate = _candidate(hc, selected_id)
        if receipt["choice"] not in req["allowed_choices"] or receipt["candidate_sha256"] != candidate["content_sha256"]:
            _fail("unauthorized", "Owner receipt choice/candidate is outside this request")
        nonce = _nonce_key(receipt, "owner")
        if nonce in hc["used_nonces"]:
            _fail("replay", "Owner nonce has already been consumed")
        blocked = "changes_requested" if receipt["choice"] == "request_changes" else _eligibility(directory, candidate)
        decision_id = "HD" + uuid.uuid4().hex
        decision = {k:receipt[k] for k in ("request_id","expected_revision","choice","candidate_sha256",
            "owner_subject_ref","origin_binding_ref","origin_session_ref","origin_event_ref","issuer_id","key_id")}
        decision.update(decision_id=decision_id,candidate_id=candidate["candidate_id"],
                        committed_at=runtime.now_iso(),receipt_digest=digest(receipt),adoption_blocked=blocked)
        hc["decisions"][decision_id] = decision
        if receipt["choice"] == "approve_current":
            req["fallback_candidate_id"] = candidate["candidate_id"]
        if receipt["choice"] == "withdraw_change":
            req["current_candidate_id"] = candidate["candidate_id"]
        hc["used_nonces"][nonce] = request["command_id"]
        req.update(status="pending" if receipt["choice"] == "request_changes" else "decided",
                   revision=req["revision"]+1,current_decision_id=decision_id)
        hc["adoptions"].pop(receipt["request_id"], None)
        # Rounds are kernel facts; observations, Host round IDs and retries cannot advance them.
        for task_id in req["blocked_task_ids"]:
            hc["authorization_rounds"][task_id] = hc["authorization_rounds"].get(task_id,0)+1
        return {"owner_decision_committed":True,"decision_id":decision_id,"request_id":receipt["request_id"],
                "revision":req["revision"],"choice":receipt["choice"],"adoption_blocked":blocked}
    if action == "adoption.apply":
        _fields(payload, {"request_id", "candidate_id"})
        req, decision, candidate = _decision_ready(directory, hc, payload["request_id"])
        if payload["candidate_id"] != candidate["candidate_id"]:
            _fail("unauthorized", "Late candidate is not the currently decided candidate")
        adoption = {"request_id":payload["request_id"],"candidate_id":candidate["candidate_id"],
                    "decision_id":decision["decision_id"],"content_sha256":candidate["content_sha256"]}
        hc["adoptions"][payload["request_id"]] = adoption
        return adoption
    if action == "execution.claim":
        _fields(payload, {"task_id", "request_id", "expected_revision", "input_digest"})
        task_id = _id(payload["task_id"]); _hash(payload["input_digest"])
        req, decision, candidate = _decision_ready(directory, hc, payload["request_id"])
        if (task_id not in req["blocked_task_ids"] or type(payload["expected_revision"]) is not int
            or payload["expected_revision"] != req["revision"]):
            _fail("stale_revision", "Final claim must match the current scoped decision")
        adoption = hc["adoptions"].get(payload["request_id"], {})
        if adoption.get("decision_id") != decision["decision_id"]:
            _fail("waiting", "Current candidate must be adopted before execution")
        if any(slot["task_id"] == task_id for slot in hc["execution_slots"].values()):
            _fail("slot_occupied", "Query the existing slot; this core never releases claimed tasks")
        # All controlling requests must permit this task, including ancestor gates.
        for other_id, other_req in hc["requests"].items():
            if task_id in other_req["blocked_task_ids"]:
                _decision_ready(directory, hc, other_id)
        task = runtime.find_task(state, task_id)
        if state["mission"]["status"] != "active" or task["status"] != "pending":
            _fail("waiting", "Final claim requires an active Mission and an unstarted task")
        projection = _dependency_projection(directory, state, req, candidate, task_id, runtime)
        round_id = hc["authorization_rounds"][task_id]
        slot_id = "HS" + digest({"mission":request["mission_id"],"task":task_id,"round":round_id})[7:]
        slot = {"slot_id":slot_id,"mission_id":request["mission_id"],"task_id":task_id,
                "authorization_round":round_id,"request_id":payload["request_id"],"expected_revision":req["revision"],
                "candidate_id":candidate["candidate_id"],"candidate_sha256":candidate["content_sha256"],
                "decision_id":decision["decision_id"],"dependency_digest":digest(projection),
                "input_digest":payload["input_digest"],"host_ref":trust["issuer_id"],"intent_id":"HI"+uuid.uuid4().hex,
                "session_id":"session-"+str(uuid.uuid4()),"native_request_id":str(uuid.uuid4()),"receipts":[]}
        hc["execution_slots"][slot_id] = slot
        return copy.deepcopy(slot)
    if action == "receipt.record":
        _fields(payload, {"slot_id", "status", "receipt_ref"})
        slot = hc["execution_slots"].get(_id(payload["slot_id"])); _id(payload["receipt_ref"])
        if slot is None or slot["host_ref"] != trust["issuer_id"]:
            _fail("unauthorized", "Dispatch fact must bind the original Host slot")
        if payload["status"] not in {"sent","unknown","accepted","delivered"}:
            _fail("invalid_request", "Receipt cannot release or supersede a claimed slot")
        existing = next((f for f in slot["receipts"] if f["receipt_ref"] == payload["receipt_ref"]),None)
        if existing:
            if existing["status"] != payload["status"]:
                _fail("command_conflict", "A receipt fact cannot be rewritten")
            return {"slot_id":slot["slot_id"], **existing}
        fact = {"status":payload["status"],"receipt_ref":payload["receipt_ref"],"committed_at":runtime.now_iso()}
        slot["receipts"].append(fact)
        return {"slot_id":slot["slot_id"], **fact}
    _fail("invalid_request", "Unsupported H1 mutation")


def execute(directory: Path, request: Any) -> tuple[dict, int]:
    """Future protected Host seam. Caller-supplied keys/principals are never accepted."""
    commit_started = False
    def response(status, code=None, data=None):
        req = request if isinstance(request, dict) else {}
        return {"protocol":PROTOCOL,"mission_id":req.get("mission_id"),"command_id":req.get("command_id"),
                "action":req.get("action"),"ok":code is None,"status":status,"code":code,"data":data}
    try:
        _request(request)
        trust = _trust_config()
        if trust is None:
            _fail("host_disabled", "Isolated Host trust has not been provisioned")
        import tplan_runtime as runtime
        directory = _check_paths(Path(directory))
        with runtime.execution_trace_lock(directory):
            if runtime.mission_paths(directory)["transaction"].exists():
                _fail("recovery_required", "Explicit original-runtime recovery required")
            state = _load(runtime, directory, request)
            if "human_control" not in state or CAPABILITY not in runtime.runtime_fingerprint()["capabilities"]:
                _fail("unsupported_capability", "New opt-in H1 Mission required")
            if runtime._read_interaction_guard_unlocked(directory) is not None:
                _fail("guard_open", "Resolve the existing interaction guard")
            if trust["mission_id"] != state["mission"]["id"]:
                _fail("unauthorized", "Host root is not registered for this Mission")
            events = _existing_evidence(runtime, directory, state)
            hc = state["human_control"]
            request_digest = digest(request)
            prior = hc["commands"].get(request["command_id"])
            if prior:
                if prior["request_digest"] != request_digest:
                    _fail("command_conflict", "Command identity has different content")
                # Exact historical replay is allowed after expiry; it grants no fresh authority.
                return response("replayed",data=copy.deepcopy(prior["result"])),0
            receipt = request["host_receipt"]
            _verify(receipt, HOST_FIELDS, trust)
            if receipt["request_digest"] != digest({k:v for k,v in request.items() if k != "host_receipt"}):
                _fail("unauthorized", "Host receipt is outside this exact command scope")
            nonce_key = _nonce_key(receipt,"host")
            if nonce_key in hc["used_nonces"]:
                _fail("replay", "Host command nonce already consumed")
            if request["action"] in {"command.get", "execution.get"}:
                field, table = ("command_id","commands") if request["action"] == "command.get" else ("slot_id","execution_slots")
                _fields(request["payload"], {field})
                result = hc[table].get(_id(request["payload"][field]))
                if result is None:
                    _fail("not_found", "No canonical fact; absence does not prove non-execution")
                return response("read",data=copy.deepcopy(result)),0
            if len(hc["commands"]) >= MAX_RECORDS or shutil.disk_usage(directory).free < MIN_FREE:
                _fail("capacity_exceeded", "H1 retention/transaction headroom exhausted")
            after = copy.deepcopy(state)
            result = _apply(directory,after,request,trust,runtime)
            updated = after["human_control"]
            updated["used_nonces"][nonce_key] = request["command_id"]
            updated["commands"][request["command_id"]] = {"command_id":request["command_id"],"action":request["action"],
                "request_digest":request_digest,"committed_at":runtime.now_iso(),"result":copy.deepcopy(result)}
            import json
            mission_bytes = len(json.dumps(after, ensure_ascii=False, indent=2).encode()) + 1
            evidence_bytes = sum(len(json.dumps(e, ensure_ascii=False).encode()) + 1 for e in events)
            trace_bytes = runtime.mission_paths(directory)["trace"].stat().st_size
            if (len(canonical(updated).encode()) > MAX_STORE or mission_bytes > MAX_ARTIFACT
                or shutil.disk_usage(directory).free < max(MIN_FREE, 2*(mission_bytes+evidence_bytes+trace_bytes))):
                _fail("capacity_exceeded", "H1 canonical state/headroom budget exhausted; no facts removed")
            # Existing transaction is the only mutable state authority, including nonces/results.
            commit_started = True
            runtime._commit_mission_state_unlocked(directory,state,after,
                source={"kind":"runtime_script","name":"tplan_h1_commands"},
                h1_control_authority=runtime._H1_CONTROL_AUTHORITY)
            return response("committed",data=result),0
    except CommandError as exc:
        return response("rejected",exc.code),4 if exc.code == "recovery_required" else 2
    except Exception:
        # A prepared transaction may already contain the entire result: query/recover original ID.
        return response("outcome_unknown" if commit_started else "rejected",
                        "outcome_unknown" if commit_started else "invalid_state"),14 if commit_started else 7

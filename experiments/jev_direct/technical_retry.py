"""One explicitly authorized A1/native format-repair attempt in the SAME ledger.

No automatic retry, routing, read continuation, new budget, or replacement freeze.
Registration is separate from dispatch so the repaired code is committed first.
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
import time
from experiments.typed_decision.contracts import digest, require, ContractError
from experiments.typed_decision.relationship_runtime import save, _locked
from experiments.typed_decision.session import read_record
from . import pilot as p
from .host_boundary import api_schema, validate_reconciliation
from .serial import SerialRequests


def lineage(root):
    root = Path(root).resolve(); f = p.verify_frozen_inputs(root)
    old = root/'runs/A1/native/host/0'
    receipt = validate_reconciliation(old)
    require(not (root/'runs/A1/native/result.json').exists(), 'retry_original_already_terminal')
    require(f['max_host_calls_per_arm'] == 4 and f['host_model'] == 'gpt-6-sol'
            and f['host_effort'] == 'xhigh' and f.get('serial_policy', {}).get('max_in_flight') == 1,
            'retry_frozen_policy')
    request = read_record(old/'request.json'); schema = json.loads((old/'schema.json').read_text())
    case = next(c for c in f['cases'] if c['id'] == 'A1')
    require(request['original_input'] == case['raw'] and request['route'] is None
            and request['loaded_materials'] == {} and schema == p.answer_schema(request['readable_paths']),
            'retry_original_request_changed')
    require(request['entry_skill'] == p.material(p.REPO, 'skills/using-mindthus/SKILL.md')
            and request['method_catalog'] == p.entry_catalog(p.REPO)
            and request['readable_paths'] == sorted(f['source_hashes']), 'retry_entry_changed')
    return f, old, request, schema, receipt


def register(root):
    root = Path(root).resolve()
    with _locked(root/'.A1.pair-lock'):
        f, old, request, schema, receipt = lineage(root)
        SerialRequests(root/'serial').validate()
        require([x.name for x in sorted(old.parent.iterdir()) if x.is_dir()] == ['0'], 'retry_attempt_already_present')
        # Use the observed shell wall as a conservative debit, not as HTTP time.
        times = [line.split()[1] for line in (root/'operator.stderr.txt').read_text().splitlines()
                 if line.startswith('real ') and len(line.split()) == 2]
        require(len(times) == 1, 'retry_previous_wall_missing')
        debit = float(times[0]); require(debit >= receipt['host_session_seconds'], 'retry_previous_wall_invalid')
        identity = {'schema': 'mindthus.a1-native-format-successor.v1', 'root': str(root),
                    'parent_freeze_sha256': digest(f), 'parent_source_commit': f['source_commit'],
                    'source_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=p.REPO, text=True).strip(),
                    'code_hashes': p.identity(p.REPO), 'case': 'A1', 'arm': 'native',
                    'request_sha256': digest(request), 'local_contract_sha256': digest(schema),
                    'api_schema_sha256': digest(api_schema(schema)), 'old_receipt_sha256': digest(receipt),
                    'previous_attempts': 1, 'remaining_attempts_before': 3, 'max_new_host_calls': 1,
                    'next_host_slot': '1', 'previous_host_session_seconds': receipt['host_session_seconds'],
                    'previous_budget_debit_seconds': debit,
                    'previous_wall_evidence_sha256': p.r.file_hash(root/'operator.stderr.txt'),
                    'automatic_retry': False, 'read_continuation': False}
        save(root/'technical-successor.json', identity)
        save(root/'technical-successor-binding.json', {'successor_sha256': digest(identity)})
        return identity


def run_once(root, *, scheduler=None):
    root = Path(root).resolve(); began = time.monotonic()
    with _locked(root/'.A1.pair-lock'):
        f, old, request, schema, receipt = lineage(root)
        successor = read_record(root/'technical-successor.json')
        require(read_record(root/'technical-successor-binding.json') == {'successor_sha256': digest(successor)}, 'retry_identity_changed')
        require(successor['root'] == str(root) and successor['parent_freeze_sha256'] == digest(f)
                and successor['code_hashes'] == p.identity(p.REPO)
                and successor['old_receipt_sha256'] == digest(receipt)
                and successor['request_sha256'] == digest(request)
                and successor['local_contract_sha256'] == digest(schema)
                and successor['api_schema_sha256'] == digest(api_schema(schema)), 'retry_lineage_changed')
        require((successor['previous_attempts'], successor['remaining_attempts_before'], successor['max_new_host_calls'], successor['next_host_slot']) == (1,3,1,'1'), 'retry_budget_changed')
        require(successor['previous_wall_evidence_sha256'] == p.r.file_hash(root/'operator.stderr.txt'), 'retry_wall_evidence_changed')
        require(successor['previous_budget_debit_seconds'] >= receipt['host_session_seconds'], 'retry_budget_debit_changed')
        scheduler = scheduler or SerialRequests(root/'serial')
        require(scheduler.root == root/'serial' and scheduler.gap == 60, 'retry_serial_root')
        scheduler.validate()
        dest = root/'technical-retry/A1/native'
        if (dest/'result.json').exists():
            result = p.unseal(dest)
            require(result['host_evidence_sha256'] == digest(p.exact_tree(old.parent)), 'retry_host_evidence_changed')
            return result
        require({x.name for x in old.parent.iterdir() if x.is_dir()} <= {'0','1'}, 'retry_unexpected_attempt')
        save(dest/'run-start.json', {'freeze_sha256': digest(f), 'raw_sha256': digest(request['original_input']),
                                  'started_at': datetime.now(timezone.utc).isoformat()})
        loaded_seconds = time.monotonic()-began
        remaining = f['max_host_seconds_per_arm']-successor['previous_budget_debit_seconds']
        require(remaining >= f['host_timeout'], 'retry_time_budget')
        reply, outcome = p.host_call(old.parent, '1', request, schema, f, timeout=f['host_timeout'], scheduler=scheduler)
        result = {'case': 'A1', 'arm': 'native', 'status': 'host_failed', 'text': '',
                  'technical_successor_sha256': digest(successor), 'new_host_calls': 1,
                  'total_host_attempts': 2, 'remaining_host_attempts': 2,
                  'host_evidence_sha256': digest(p.exact_tree(old.parent)),
                  'loading_seconds': loaded_seconds, 'new_host_session_seconds': outcome['elapsed_seconds'],
                  'host_dispatch_wall_seconds': outcome['dispatch_wall_seconds'],
                  'http_seconds': None, 'quality': 'not_scored', 'outcome': outcome,
                  'original_reply_path': str(old.parent/'1/reply.json') if reply is not None else None}
        if outcome['status'] == 'complete':
            try:
                if reply['action'] == 'read':
                    require(reply['text'] == '' and reply['used_methods'] == [] and reply['read_paths'], 'pilot_read_shape')
                    result.update(status='read_requested', requested_reads=reply['read_paths'])
                else:
                    require(not reply['read_paths'] and reply['text'].strip(), 'pilot_answer_required')
                    actual = {m for m in p.ROUTABLE if f'skills/{m}/SKILL.md' in request['loaded_materials']}
                    require(set(reply['used_methods']) <= actual, 'pilot_unread_method_claim')
                    result.update(status='delivered', text=reply['text'], used_methods=reply['used_methods'],
                                  route_objection=reply['route_objection'], quality='requires_independent_content_review')
            except ContractError as exc:
                result.update(status='host_reply_rejected', reason=p.safe_code(exc))
        return p.seal(dest, result)

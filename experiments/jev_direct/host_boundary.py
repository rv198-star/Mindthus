"""API schema projection and request-bound CLI archive failure receipts.

Only a confirmed schema failure can be reconciled here. An exit code, timeout,
unstructured error, or safety refusal never grants another dispatch.
"""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
from experiments.typed_decision.contracts import digest, require
from experiments.typed_decision.relationship_runtime import save, _locked
from experiments.typed_decision.session import read_record
from .router import file_hash


def api_schema(contract):
    """Visit schema nodes, not property names or data inside enum/default values."""
    result = deepcopy(contract)
    def visit(node):
        if not isinstance(node, dict):
            return
        node.pop('uniqueItems', None)  # confirmed invalid_json_schema, 2026-09-27
        for key in ('properties', '$defs', 'definitions', 'patternProperties'):
            for child in node.get(key, {}).values():
                visit(child)
        for key in ('items', 'additionalProperties', 'contains', 'not', 'if', 'then', 'else'):
            visit(node.get(key))
        for key in ('anyOf', 'oneOf', 'allOf', 'prefixItems'):
            for child in node.get(key, []):
                visit(child)
    visit(result)
    return result


def parse_events(text):
    events = []
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def bound_schema_failure(events, directory, thread_id):
    """Use archive event_msg/task_complete, never reinterpret stdout turn.failed.

    session_meta + turn_context + exact UserMessage bind thread, turn, workspace,
    model and prompt to the immutable request. The receipt retains exact request/start/terminal events and projected metadata;
    original event hashes and line numbers bind that projection to the archive.
    """
    directory = Path(directory)
    intent = read_record(directory/'intent.json')
    require(digest(read_record(directory/'request.json')) == intent['request_sha256'], 'host_request_binding')
    require(digest((directory/'prompt.txt').read_text()) == intent['prompt_sha256'], 'host_prompt_binding')
    require(digest(json.loads((directory/'schema.json').read_text())) == intent['schema_sha256'], 'host_schema_binding')
    metas = [e for e in events if e.get('type') == 'session_meta']
    require(len(metas) == 1 and metas[0]['payload'].get('id') == thread_id, 'host_archive_thread')
    workspace = str((directory/'workspace').resolve())
    require(metas[0]['payload'].get('cwd') == workspace, 'host_archive_workspace')
    messages = [e for e in events if e.get('type') == 'event_msg'
                and e.get('payload', {}).get('type') == 'item_completed'
                and e['payload'].get('item', {}).get('type') == 'UserMessage'
                and e['payload'].get('thread_id') == thread_id
                and len(e['payload']['item'].get('content', [])) == 1
                and e['payload']['item']['content'][0].get('type') == 'text'
                and e['payload']['item']['content'][0].get('text') == (directory/'prompt.txt').read_text()]
    require(len(messages) == 1, 'host_archive_prompt')
    message = messages[0]; turn = message['payload'].get('turn_id')
    require(isinstance(turn, str) and turn, 'host_archive_turn')
    contexts = [e for e in events if e.get('type') == 'turn_context' and e['payload'].get('turn_id') == turn]
    starts = [e for e in events if e.get('type') == 'event_msg' and e['payload'].get('type') == 'task_started' and e['payload'].get('turn_id') == turn]
    ends = [e for e in events if e.get('type') == 'event_msg' and e['payload'].get('type') == 'task_complete' and e['payload'].get('turn_id') == turn]
    require(len(contexts) == len(starts) == len(ends) == 1, 'host_archive_terminal_missing')
    context, start, end = contexts[0], starts[0], ends[0]
    require(context['payload'].get('cwd') == workspace and context['payload'].get('model') == intent['model']
            and context['payload'].get('effort') == intent['effort'], 'host_archive_context')
    selected = [metas[0], start, context, message, end]
    require([events.index(e) for e in selected] == sorted(events.index(e) for e in selected), 'host_archive_order')
    payload = end['payload']
    require(payload.get('last_agent_message') is None and isinstance(payload.get('error'), dict), 'host_archive_not_failure')
    try:
        error = json.loads(payload['error']['message'])['error']
    except (KeyError, ValueError, TypeError):
        error = {}
    require((error.get('type'), error.get('code'), error.get('param')) ==
            ('invalid_request_error', 'invalid_json_schema', 'text.format.schema'), 'host_not_schema_failure')
    duration = payload.get('duration_ms')
    require(type(duration) in (int, float) and duration >= 0, 'host_archive_duration')
    end_epoch = datetime.fromisoformat(end['timestamp'].replace('Z', '+00:00')).timestamp()
    start_epoch = datetime.fromisoformat(start['timestamp'].replace('Z', '+00:00')).timestamp()
    require(end_epoch >= start_epoch, 'host_archive_time')
    return {'status': 'confirmed_request_failure', 'failure_kind': 'invalid_json_schema',
            'automatic_retry': False, 'request_sha256': intent['request_sha256'],
            'intent_sha256': digest(intent), 'thread_id': thread_id, 'turn_id': turn,
            'error': error, 'started_at_epoch': start_epoch, 'ended_at_epoch': end_epoch,
            'host_session_seconds': duration/1000, 'http_seconds': None,
            'binding_events': selected}


def binding_events(events):
    result = deepcopy(events)
    fields = {'session_meta': ('id', 'cwd', 'timestamp', 'cli_version', 'model_provider'),
              'turn_context': ('turn_id', 'cwd', 'model', 'effort')}
    for event in result:
        if event.get('type') in fields:
            event['payload'] = {k: event['payload'].get(k) for k in fields[event['type']]}
    return result


def capture_schema_failure(directory, archive, thread_id):
    archive = Path(archive)
    lines = archive.read_text().splitlines()
    originals = [json.loads(line) for line in lines]
    events = binding_events(originals)
    receipt = bound_schema_failure(events, directory, thread_id)
    receipt.update(archive_path=str(archive), archive_sha256=file_hash(archive),
                   archive_line_numbers=[events.index(e)+1 for e in receipt['binding_events']],
                   archive_original_event_sha256=[digest(originals[events.index(e)]) for e in receipt['binding_events']],
                   export_scope='exact start/request/terminal events; session and turn metadata projected')
    save(Path(directory)/'schema-failure-receipt.json', receipt)
    return receipt


def validate_receipt(directory):
    receipt = read_record(Path(directory)/'schema-failure-receipt.json')
    core = bound_schema_failure(receipt['binding_events'], directory, receipt['thread_id'])
    require(all(receipt.get(k) == v for k, v in core.items()), 'host_failure_receipt_changed')
    return receipt


def cli_schema_failure(directory, thread_id):
    """Discover only the archive named by this invocation's thread.started."""
    archives = list((Path.home()/'.codex/sessions').glob('*/*/*/*-'+thread_id+'.jsonl'))
    require(len(archives) == 1, 'host_archive_unavailable')
    return capture_schema_failure(directory, archives[0], thread_id)


def validate_reconciliation(directory):
    directory = Path(directory)
    receipt = validate_receipt(directory)
    record = read_record(directory/'reconciliation.json')
    require(record == {'status': 'confirmed_request_failure', 'receipt_sha256': digest(receipt),
                       'intent_sha256': digest(read_record(directory/'intent.json')),
                       'automatic_retry': False}, 'host_reconciliation_changed')
    return receipt


def reconcile_schema_failure(batch, directory, archive, thread_id):
    """Append evidence; retain the old bare intent and do not invent completion."""
    batch, directory = Path(batch).resolve(), Path(directory).resolve()
    require(directory.is_relative_to(batch/'runs'), 'host_reconcile_outside_batch')
    with _locked(batch/'serial/.lock'):
        slots = [p.parent for p in (batch/'serial').glob('*/intent.json')
                 if read_record(p).get('label') == 'host:'+str(directory)]
        require(len(slots) == 1, 'host_reconcile_serial_binding')
        slot = slots[0]; intent = read_record(slot/'intent.json')
        require(not (slot/'completion.json').exists() and not (directory/'outcome.json').exists(), 'host_reconcile_already_returned')
        anchor = batch/'serial-bindings'/slot.name
        require(read_record(anchor/'intent.json') == {'intent_sha256': digest(intent)}, 'host_reconcile_anchor')
        receipt = capture_schema_failure(directory, archive, thread_id)
        require(receipt['started_at_epoch'] >= intent['started_at_epoch'], 'host_reconcile_time')
        record = {'status': 'confirmed_request_failure', 'receipt_sha256': digest(receipt),
                  'intent_sha256': digest(read_record(directory/'intent.json')), 'automatic_retry': False}
        save(directory/'reconciliation.json', record)
        failure = {'status': 'confirmed_request_failure', 'intent_sha256': digest(intent),
                   'ended_at_epoch': receipt['ended_at_epoch'], 'request_elapsed_seconds': None,
                   'host_session_seconds': receipt['host_session_seconds'],
                   'host_directory': str(directory), 'reconciliation_sha256': digest(record)}
        save(slot/'failure.json', failure)
        save(anchor/'failure.json', {'failure_sha256': digest(failure)})
        return record

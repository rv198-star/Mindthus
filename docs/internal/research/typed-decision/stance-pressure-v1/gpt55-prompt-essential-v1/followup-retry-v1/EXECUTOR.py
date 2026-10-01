"""One authorized pre-send follow-up retry; exact prior wire, no first-turn rerun."""
import argparse, copy, getpass, importlib.util, json, os, subprocess, time
from pathlib import Path

DOC = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('gpt55_parent', DOC.parent / 'EXECUTOR.py')
parent = importlib.util.module_from_spec(spec); spec.loader.exec_module(parent)
r, d = parent.r, parent.d
ROOT = parent.ROOT / 'followup-retry-v1'
INHERITED = {'logical': 77, 'host': 61, 'jev': 16}
LIMITS = {'logical': 78, 'host': 62, 'jev': 16}
HOST = parent.HOST
OLD_REQUEST = 'aad15485ca7a61caef63f6a730b88a52b5dda0e054b98f6d94e871b5a302378b'
OLD_WIRE = '11a7ca24e19647b45b2c3f02a67792087aca78f4e872234c5ba7525776e604ab'

def verified_parent():
    saved = {}
    for n in ('000000', '000001'):
        p = parent.ROOT / 'calls' / n
        t, raw, wire, imp = [r.rt.read(p / name) for name in ('terminal.json', 'raw.json', 'wire.json', 'import.json')]
        r.require(t['binding'] == raw['binding'] == imp['binding']
                  and t['raw_sha256'] == r.digest(raw['transport'])
                  and t['binding']['wire_sha256'] == r.digest(wire), 'parent_receipt_binding')
        saved[n] = (t, raw, wire)
    first, raw, _ = saved['000000']
    failed, old_raw, wire = saved['000001']
    diag = old_raw['transport'].get('diagnostic') or {}
    r.require(first['status'] == 'returned' and first['response']['text'] == raw['transport']['raw']['choices'][0]['message']['content']
              == (DOC.parent / 'turn-1.reply.txt').read_text(), 'actual_first_reply')
    r.require(failed['status'] == 'failed' and failed['binding']['request_sha256'] == OLD_REQUEST
              and failed['binding']['wire_sha256'] == OLD_WIRE
              and old_raw['transport']['kind'] == 'transport_error'
              and diag.get('request_sha256') == r.digest(wire['body'])
              and diag.get('observed_stage') == 'connection_establishment_failed'
              and diag.get('generation_send_status') == 'pre_send'
              and diag.get('pre_send_basis') == 'HTTPSConnection.connect raised before generation HTTP write'
              and diag.get('http_response_received') is False, 'only_bound_pre_send_failure')
    r.require(wire['body']['messages'] == [
        {'role': 'user', 'content': parent.case()['user_messages'][0]},
        {'role': 'assistant', 'content': first['response']['text']},
        {'role': 'user', 'content': parent.case()['user_messages'][1]}], 'exact_original_history')
    summary = r.rt.read(DOC.parent / 'summary.json')
    r.require(summary['cumulative_debits'] == INHERITED and summary['state']['calls']['A'] == 2
              and summary['state']['candidate'] == first['response']['text'], 'inherited_history_and_budget')
    return wire, summary

class Adapters(parent.Adapters):
    limits = LIMITS
    def check_configuration(self, cfg):
        r.require(cfg['host_configuration'] == HOST and cfg['limits'] == LIMITS, 'retry_profile_changed')
    def outbound(self, req, cfg):
        self.check_configuration(cfg)
        r.require(req['role'] == 'host' and req['arm'] == 'A' and req['phase'] == 'draft'
                  and req['sequence'] == 2 and req['requested_configuration'] == HOST, 'one_followup_retry_only')
        wire, _ = verified_parent(); p = req['payload']
        r.require(not p['loaded_materials'] and not p['readable_paths'], 'no_background')
        docs = p['source']['documents']
        r.require(len(docs) == 1 and docs[0]['id'] == 'task'
                  and json.loads(docs[0]['text']) == wire['body']['messages'], 'same_exact_business_wire')
        return copy.deepcopy(wire)
    def classify(self, req, raw):
        # Reuse the existing terminal classifier on the exact validated wire.
        # This receipt-only view has no invoke; actual dispatch uses the new budget.
        wire = self.outbound(req, {'host_configuration': HOST, 'limits': LIMITS})
        receipt = parent.Adapters()
        def bound_wire(incoming, _config):
            r.require(incoming == req, 'classifier_request_binding')
            return wire
        receipt.outbound = bound_wire
        return receipt.classify(req, raw)

def prepare():
    r.require(not ROOT.exists(), 'retry_exists_no_reset')
    wire, summary = verified_parent()
    directories, _, _ = parent.prior.NamedSerial(d.ROOT / 'serial').validate()
    r.require(len(directories) == 75, 'parent_serial_changed')
    old = r.rt.read(parent.ROOT / 'batch.json')
    source = set(old['source_sha256']) | {str(Path(__file__).relative_to(r.REPO))}
    cfg = {**old, 'schema': 'mindthus.gpt55-followup-pre-send-retry.v1',
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=r.REPO, text=True).strip(),
        'source_sha256': {name: r.digest((r.REPO / name).read_text()) for name in source},
        'authorization_ref': 'Owner: 争取完成 (2026-10-01); one bounded technical follow-up retry after bound pre-send TLS failure',
        'external_budget_debits': INHERITED, 'limits': LIMITS, 'phase_limits': {'logical': 1, 'host': 1, 'jev': 0},
        'parent_batch_sha256': r.digest(old), 'parent_summary_sha256': r.digest(summary),
        'technical_parent': {'call_key': 'skills-prompt-essential-gpt55-A:1', 'serial_slot': '000074',
            'request_sha256': OLD_REQUEST, 'wire_sha256': OLD_WIRE,
            'terminal_sha256': r.digest(r.rt.read(parent.ROOT / 'calls/000001/terminal.json'))},
        'scope': 'Only original second question on actual first reply; exact failed wire; no first rerun or content correction',
        'no_retries': True, 'retry_bound': 0, 'allowed_parameter_repair': None,
        'is_single_authorized_technical_retry': True, 'created_at_epoch': time.time()}
    r.no_secrets(cfg); ROOT.mkdir(); (ROOT / 'calls').mkdir(); (ROOT / 'states').mkdir()
    r.rt.write(ROOT / 'batch.json', cfg); r.rt.write(ROOT / 'materials.json', {})
    r.rt.write(ROOT / 'states' / (parent.case()['case_id'] + '.json'), summary['state'])
    r.rt.write(DOC / 'admission.json', cfg)

def main():
    p = argparse.ArgumentParser(); g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare', action='store_true'); g.add_argument('--run', action='store_true'); args = p.parse_args()
    with r._locked(d.ROOT / '.execution.lock'):
        if args.prepare: prepare(); print('One exact follow-up retry frozen; zero generation sent.'); return
        cfg = r.rt.read(ROOT / 'batch.json'); wire, old_summary = verified_parent()
        r.require(cfg['external_budget_debits'] == INHERITED and cfg['limits'] == LIMITS
                  and r.digest(old_summary) == cfg['parent_summary_sha256'], 'parent_or_budget_changed')
        r.require(not list((ROOT / 'calls').iterdir()), 'no_repeat_execution')
        driver = r.Driver(ROOT, Adapters()); driver.serial = parent.prior.NamedSerial(d.ROOT / 'serial')
        driver.stop_path = ROOT / 'STOP.json'; driver.serial.validate()
        if not os.environ.get('MINDTHUS_HOST_API_KEY'):
            os.environ['MINDTHUS_HOST_API_KEY'] = getpass.getpass('Sub2API credential (hidden, process memory only): ')
        r.require(bool(os.environ.get('MINDTHUS_HOST_API_KEY')), 'missing_authorized_credential')
        state = r.rt.read(ROOT / 'states' / (parent.case()['case_id'] + '.json'))
        r.require(state['calls']['A'] == 2, 'retry_sequence')
        item = {'case_id': parent.case()['case_id'], 'input': r.canonical(wire['body']['messages']).decode()}
        began = time.monotonic(); terminal = driver.step(item, state, 'A', 'draft')
        counts = {'logical': 1, 'host': 1, 'jev': 0}
        r.rt.write(DOC / 'summary.json', {'phase_debits': counts,
            'cumulative_debits': {k: INHERITED[k] + counts[k] for k in INHERITED},
            'state': state, 'terminals': [terminal], 'wall_seconds': time.monotonic() - began,
            'fees': None, 'proxy_downstream_requests': None, 'simulation': False, 'holdout': False,
            'old_remote_unknown_retained': True, 'parent_summary_sha256': cfg['parent_summary_sha256']})
        text = terminal['response']['text'] if terminal['status'] == 'returned' else None
        r.rt.write(DOC / 'turn-2.answer.json', {'turn': 2, 'technical_retry': True, 'text': text, 'terminal': terminal})
        if text is not None: (DOC / 'turn-2.reply.txt').write_text(text, encoding='utf-8')
        print(json.dumps({'status': terminal['status'], 'delivery': state['arms']['A']['status'],
            'session_seconds': terminal['session_seconds'], 'wait_seconds': terminal['active_wait_seconds'],
            'error': terminal['error']}), flush=True)

if __name__ == '__main__': main()

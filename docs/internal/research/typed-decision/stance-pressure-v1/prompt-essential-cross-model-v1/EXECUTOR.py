"""Four authorized bare-message generations; existing transport and batch serial."""
import argparse, getpass, importlib.util, json, os, subprocess, time
from pathlib import Path
DOC = Path(__file__).resolve().parent
s = importlib.util.spec_from_file_location('gpt55_parent', DOC.parent / 'gpt55-prompt-essential-v1/EXECUTOR.py')
parent = importlib.util.module_from_spec(s); s.loader.exec_module(parent)
r, d = parent.r, parent.d
ROOT = d.ROOT / 'prompt-essential-cross-model-v1'
INHERITED = {'logical': 78, 'host': 62, 'jev': 16}
LIMITS = {'logical': 82, 'host': 66, 'jev': 16}
PROFILES = {
    'sol61': {**parent.HOST, 'model': 'gpt-6.1-sol'},
    'dsf41': {**d.DEFAULT_HOST}}

def cases(): return r.rt.read(DOC / 'cases.business.json')['cases']
def case(name): return next(c for c in cases() if c['profile'] == name)

class Adapters(d.CPAAdapters):
    limits = LIMITS
    def __init__(self, name): self.name = name; self.host = dict(PROFILES[name]); self.endpoint = self.host['endpoint']
    def check_configuration(self, cfg):
        r.require(cfg['host_configuration'] == self.host and cfg['limits'] == LIMITS
                  and cfg['profiles'] == PROFILES, 'cross_model_profile_changed')
    def outbound(self, req, cfg):
        self.check_configuration(cfg)
        r.require(req['role'] == 'host' and req['arm'] == 'A' and req['phase'] == 'draft'
                  and req['requested_configuration'] == self.host, 'bare_A_only')
        p = req['payload']; docs = p['source']['documents']
        r.require(not p['loaded_materials'] and not p['readable_paths'] and len(docs) == 1 and docs[0]['id'] == 'task', 'bare_single_transcript')
        messages = json.loads(docs[0]['text']); n = len(messages)
        r.require(n in (1, 3) and req['sequence'] == (n - 1) // 2, 'two_turns_only')
        r.require([m.get('role') for m in messages] == (['user'] if n == 1 else ['user', 'assistant', 'user'])
                  and all(set(m) == {'role', 'content'} and isinstance(m['content'], str) and m['content'].strip() for m in messages), 'bare_messages')
        r.require(messages[0]['content'] == case(self.name)['user_messages'][0]
                  and (n == 1 or messages[2]['content'] == case(self.name)['user_messages'][1]), 'exact_same_questions')
        keys = ('model', 'reasoning_effort', 'max_completion_tokens') if self.name == 'sol61' else ('model', 'reasoning_effort', 'max_tokens', 'temperature', 'thinking')
        return {'endpoint': self.endpoint, 'body': {**{k: self.host[k] for k in keys}, 'stream': False, 'messages': messages}}
    def classify(self, req, raw):
        wire = self.outbound(req, {'host_configuration': self.host, 'limits': LIMITS, 'profiles': PROFILES}); sha = r.digest(wire['body'])
        if raw.get('kind') == 'not_sent': return 'failed', None, None, raw.get('code')
        if raw.get('kind') == 'transport_error':
            diag = raw.get('diagnostic') or {}; h = diag.get('http_error_response') or {}; error = raw.get('code')
            if diag.get('request_sha256') != sha: return 'unknown', None, None, error
            if diag.get('http_response_received'):
                code, kind = h.get('code'), h.get('type')
                if diag.get('http_status') in (401, 403) or code in ('content_policy_violation', 'content_filter', 'safety_violation', 'permission_denied', 'access_denied', 'insufficient_permissions') or kind in ('authentication_error', 'permission_error'):
                    return 'safety_refusal', None, None, error
                if diag.get('http_status') == 400 and h.get('body_status') == 'json_error_object' and kind == 'invalid_request_error':
                    return 'failed', None, None, error
            if diag.get('generation_send_status') == 'pre_send' and diag.get('observed_stage') == 'connection_establishment_failed': return 'failed', None, None, error
            return 'unknown', None, None, error
        if raw.get('kind') != 'cpa_http_json' or raw.get('endpoint') != self.endpoint or raw.get('request_sha256') != sha: return 'unknown', None, None, 'receipt_binding'
        value = raw['raw']; usage = value.get('usage'); choices = value.get('choices')
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict): return 'unknown', None, usage, 'missing_terminal'
        choice = choices[0]; reason, message = choice.get('finish_reason'), choice.get('message')
        if not isinstance(message, dict): return ('failed' if reason == 'stop' else 'unknown'), None, usage, 'message_type'
        if reason == 'content_filter' or message.get('refusal'): return 'safety_refusal', None, usage, 'content_refusal'
        if reason not in ('stop', 'length', 'tool_calls'): return 'unknown', None, usage, 'missing_finish_reason'
        if value.get('model') != self.host['model']: return 'failed', None, usage, 'model_mismatch'
        if reason != 'stop' or message.get('tool_calls'): return 'failed', None, usage, 'incomplete_or_tools'
        text = message.get('content')
        if not isinstance(text, str) or not text.strip(): return 'failed', None, usage, 'empty_answer'
        return 'returned', {'kind': 'answer', 'text': text, 'read_paths': [], 'objection': ''}, usage, None

def prepare():
    r.require(not ROOT.exists(), 'phase_exists_no_reset')
    prevdoc = DOC.parent / 'gpt55-prompt-essential-v1/followup-retry-v1'
    previous = r.rt.read(prevdoc / 'summary.json')
    r.require(previous['cumulative_debits'] == INHERITED and previous['terminals'][0]['status'] == 'returned', 'parent_budget_or_end')
    directories, _, _ = parent.prior.NamedSerial(d.ROOT / 'serial').validate()
    r.require(len(directories) == 76, 'parent_serial_changed')
    old = r.rt.read(parent.ROOT / 'batch.json')
    catalog = r.rt.read(parent.prior.DOC / 'MODEL-CATALOG.json')
    r.require(PROFILES['sol61']['model'] in [m['id'] for m in catalog['raw']['data']], 'sol61_not_listed')
    ds = r.rt.read(d.DOC / 'model-catalog-new-endpoint-check.json')
    r.require(ds['http_status'] == 200 and PROFILES['dsf41']['model'] in ds['model_ids'], 'dsf41_not_listed')
    r.require(all(c['user_messages'] == parent.case()['user_messages'] for c in cases()), 'paired_questions_changed')
    source = set(old['source_sha256']) | {str(Path(__file__).relative_to(r.REPO))}
    cfg = {**old, 'schema': 'mindthus.prompt-essential.cross-model.v1',
        'host_configuration': PROFILES['sol61'], 'profiles': PROFILES,
        'allowed_response_models': {name: [host['model']] for name, host in PROFILES.items()},
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=r.REPO, text=True).strip(),
        'source_sha256': {name: r.digest((r.REPO / name).read_text()) for name in source},
        'cases_source_path': str((DOC / 'cases.business.json').relative_to(r.REPO)),
        'cases_sha256': r.digest(r.rt.read(DOC / 'cases.business.json')),
        'norms_sha256': r.digest(r.rt.read(DOC / 'norms.evaluation-only.json')),
        'external_budget_debits': INHERITED, 'limits': LIMITS, 'phase_limits': {'logical': 4, 'host': 4, 'jev': 0},
        'authorization_ref': 'Owner: 验证同样两轮5.6、6.1、dsf4.1是否也不符合预期 (2026-10-01); reuse matching5.6, at most4 new calls for6.1/DSF',
        'parent_summary_sha256': r.digest(previous), 'created_at_epoch': time.time(),
        'scope': 'Same two turns independently per model; first actual reply is second-turn history; no retry, correction, Jev, reviewer or probe',
        'no_retries': True, 'retry_bound': 0, 'allowed_parameter_repair': None,
        'protocol': {**old['protocol'], 'scope_this_turn': 'Four calls maximum: Sol6.1 two turns then DSF4.1 two turns; same serial/cooldown and existing named000068 disposition only'}}
    r.no_secrets(cfg); ROOT.mkdir(); (ROOT / 'calls').mkdir(); (ROOT / 'states').mkdir()
    r.rt.write(ROOT / 'batch.json', cfg); r.rt.write(ROOT / 'materials.json', {}); r.rt.write(DOC / 'admission.json', cfg)
    for c in cases(): r.rt.write(ROOT / 'states' / (c['case_id'] + '.json'), parent.a.initial())

def checkpoint(began, name):
    ts = [r.rt.read(p / 'terminal.json') for p in sorted((ROOT / 'calls').iterdir()) if (p / 'terminal.json').exists()]
    count = {'logical': len(ts), 'host': len(ts), 'jev': 0}
    r.persist(DOC / 'summary.json', {'phase_debits': count,
        'cumulative_debits': {k: INHERITED[k] + count[k] for k in INHERITED},
        'terminals': ts, 'simulation': False, 'holdout': False, 'fees': None,
        'old_000068_remote_status': 'unknown'})
    r.persist(DOC / (name + '.window.json'), {'profile': name, 'wall_seconds': time.monotonic() - began,
        'call_keys': [t['binding']['call_key'] for t in ts if t['binding']['call_key'].startswith(case(name)['case_id'] + '-')]})

def main():
    p = argparse.ArgumentParser(); g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare', action='store_true'); g.add_argument('--run-model', choices=tuple(PROFILES)); args = p.parse_args()
    with r._locked(d.ROOT / '.execution.lock'):
        if args.prepare: prepare(); print('Two models / four calls frozen; no generation sent.'); return
        name = args.run_model; c = case(name); cfg = r.rt.read(ROOT / 'batch.json')
        r.require(cfg['external_budget_debits'] == INHERITED and cfg['limits'] == LIMITS, 'budget_identity')
        state = r.rt.read(ROOT / 'states' / (c['case_id'] + '.json'))
        r.require(state['calls']['A'] == 0, 'no_rerun_or_resume')
        driver = r.Driver(ROOT, Adapters(name)); driver.config = {**cfg, 'host_configuration': PROFILES[name], 'selected_profile': name,
            'allowed_response_models': cfg['allowed_response_models'][name]}
        driver.serial = parent.prior.NamedSerial(d.ROOT / 'serial'); driver.stop_path = ROOT / 'STOP.json'; driver.serial.validate()
        r.rt.write(ROOT / ('effective-config-' + name + '.json'), driver.config)
        if not os.environ.get('MINDTHUS_HOST_API_KEY'):
            os.environ['MINDTHUS_HOST_API_KEY'] = getpass.getpass(name + ' credential (hidden, process memory only): ')
        r.require(bool(os.environ.get('MINDTHUS_HOST_API_KEY')), 'missing_authorized_credential')
        began = time.monotonic(); messages = [{'role': 'user', 'content': c['user_messages'][0]}]
        for turn in range(2):
            if turn:
                rows = [(p, r.rt.read(p / 'terminal.json')) for p in sorted((ROOT / 'calls').iterdir())]
                directory, t = next((p, t) for p, t in rows if t['binding']['call_key'] == c['case_id'] + '-A:0')
                raw = r.rt.read(directory / 'raw.json')
                r.require(t['status'] == 'returned' and raw['binding'] == t['binding'] and r.digest(raw['transport']) == t['raw_sha256'], 'actual_first_reply_binding')
                text = raw['transport']['raw']['choices'][0]['message']['content']
                r.require(text == state['candidate'], 'actual_first_history')
                messages += [{'role': 'assistant', 'content': text}, {'role': 'user', 'content': c['user_messages'][1]}]
            print(json.dumps({'model': PROFILES[name]['model'], 'turn': turn + 1, 'effort_requested': 'medium', 'no_retries': True}), flush=True)
            terminal = driver.step({'case_id': c['case_id'], 'input': r.canonical(messages).decode()}, state, 'A', 'draft'); checkpoint(began, name)
            text = terminal['response']['text'] if terminal['status'] == 'returned' else None
            r.rt.write(DOC / (name + '-turn-' + str(turn + 1) + '.answer.json'), {'turn': turn + 1, 'text': text, 'terminal': terminal})
            if text is not None: (DOC / (name + '-turn-' + str(turn + 1) + '.reply.txt')).write_text(text, encoding='utf-8')
            print(json.dumps({'status': terminal['status'], 'error': terminal['error'], 'session_seconds': terminal['session_seconds'], 'wait_seconds': terminal['active_wait_seconds']}), flush=True)
            if terminal['status'] != 'returned' or driver.stop_path.exists(): break
        checkpoint(began, name)

if __name__ == '__main__': main()

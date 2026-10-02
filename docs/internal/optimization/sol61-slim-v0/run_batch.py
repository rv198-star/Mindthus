#!/usr/bin/env python3
"""One bounded #220 batch; reuse the pinned official adapter and serial ledger.

No credentials, Jev, evaluator, retry loop, or historical unknown exceptions.
The T0 norms are deliberately not loaded by this executable.
"""
import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BASELINE = '1527f32b99c375db9ff73f80812c644686a6576a'
ADAPTER_PIN = 'ed5171bf7b34746027acd730864d9c98ef1dd8d2'
BINARY = '/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'
SKILLS = ('3l5s', 'sra', 'sela', 'mpg', 'edsp', 'wae', 'tvg', 'tplan')


def digest(x):
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def write(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        raise ValueError('refuse_evidence_overwrite:' + p.name)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def git(repo, *args):
    return subprocess.check_output(['git', *args], cwd=repo)


def render(case):
    return case['prompt'] + ('\n\n' + case['condition'] if case.get('condition') else '')


def plan(cases):
    result = []
    for n, case in enumerate(cases):
        for arm in (('current', 'slim') if n % 2 == 0 else ('slim', 'current')):
            result.append(dict(case=case['id'], arm=arm, model='gpt-6.1-sol'))
    for n, key in enumerate(('F01', 'F02', 'V01', 'V02')):
        for arm in (('current', 'slim') if n % 2 == 0 else ('slim', 'current')):
            result.append(dict(case=key, arm=arm, model='gpt-6-astra'))
    result += [dict(case=key, arm='bare', model='gpt-6.1-sol') for key in ('F01', 'F02', 'V01', 'V02')]
    return result


def materials(commit):
    raw = git(REPO, 'archive', commit, 'skills', 'docs/methodologies', 'scripts/primitives')
    result = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for member in archive.getmembers():
            p = Path(member.name)
            if not member.isfile() or p.suffix not in ('.md', '.json', '.yaml', '.py'):
                continue
            if '..' in p.parts or p.is_absolute():
                raise ValueError('archive_path')
            result[member.name] = archive.extractfile(member).read().decode('utf8')
    return result


def adapters(root):
    root = Path(root).resolve()
    if git(root, 'rev-parse', 'HEAD').decode().strip() != ADAPTER_PIN:
        raise ValueError('adapter_pin_changed')
    # Tracked edits could change the invoked adapter despite an unchanged HEAD.
    if git(root, 'diff', '--name-only', 'HEAD', '--', 'experiments', 'docs/internal/research/typed-decision'):
        raise ValueError('adapter_tracked_changes')
    sys.path.insert(0, str(root))
    from experiments.grounded_judgment.dispatch import OfficialAdapters, classify, host_schema
    from experiments.jev_direct.serial import SerialRequests
    from experiments.jev_direct.host_boundary import api_schema
    from experiments.jev_direct.transport_profile import CANDIDATE, PROTOCOL, observe
    from experiments.typed_decision.relationship_runtime import _locked
    from experiments.typed_decision.session import RecoveryRequired, read_record
    return locals()


def prepare(batch, adapter_root, candidate, *, simulation=False, admission=None, parent_batch=None):
    batch = Path(batch).resolve()
    if batch.exists():
        raise ValueError('fresh_batch_required')
    if not simulation:
        if not isinstance(admission, dict) or not parent_batch:
            raise ValueError('explicit_successor_admission_and_parent_required')
        if admission.get('execution_authorized') is not True:
            raise ValueError('successor_not_authorized_no_prepare')
    a = adapters(adapter_root)
    freeze = read(HERE / 'freeze.json')
    for name, sha in freeze['source_files'].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != sha:
            raise ValueError('T0_changed:' + name)
    cases = read(HERE / 'cases.json')['business_cases']
    sources = {arm: materials(sha) for arm, sha in [('current', BASELINE), ('slim', candidate)]}
    profile = read(a['CANDIDATE']); protocol = read(a['PROTOCOL'])
    if digest(profile['candidate_overrides']) != profile['overrides_sha256']:
        raise ValueError('profile_changed')
    version = subprocess.check_output([BINARY, '--version'], text=True).strip()
    config = dict(schema='mindthus.slim-batch.v0', simulation=simulation,
        authorization='Owner approved 64 host logical calls; 44 paths, 3/path; no retry/Jev/evaluator',
        baseline=BASELINE, candidate=candidate, adapter_pin=ADAPTER_PIN,
        adapter_root=str(Path(adapter_root).resolve()), cli_version=version,
        workspace_mode='external_empty_directory_no_project_ancestors',
        binary_sha256=hashlib.sha256(Path(BINARY).read_bytes()).hexdigest(),
        admission=dict(binary=BINARY), host_timeout=300, active_processing_limit_seconds=7200,
        total_calls_max=64, path_calls_max=3, effort='medium',
        transport_overrides=profile['candidate_overrides'], transport_overrides_sha256=profile['overrides_sha256'],
        overrides=profile['candidate_overrides']+['features.skip_host_skill_discovery=true','features.plugins=false'],
        isolation='same call-level skill/plugin isolation in every arm; safety/approval/hooks unchanged',
        protocol=protocol, protocol_sha256=digest(protocol),
        inputs_sha256=digest({c['id']:render(c) for c in cases}),
        source_sha256={arm:digest(value) for arm,value in sources.items()},
        plan=plan(cases), evidence_scope='controlled read exchange; not passive activation qualification')
    if not simulation:
        parent=parent_receipt(parent_batch)
        if admission.get('parent_receipt_sha256')!=digest(parent):
            raise ValueError('successor_parent_binding')
        cap=admission.get('cumulative_call_limit')
        allowance=carry_budget(parent['logical_calls'],cap)
        config.update(successor_admission=admission,parent_receipt=parent,
            total_calls_max=allowance,
            authorization=admission.get('authorization_ref','pending_owner_confirmation'),
            budget_status='authorized_successor' if admission.get('execution_authorized') is True else 'proposal_only_no_dispatch')
    write(batch / 'batch.json', config)
    write(batch / 'batch-binding.json', dict(sha256=digest(config)))
    write(batch / 'inputs.json', {c['id']:render(c) for c in cases})
    for arm, value in sources.items():
        write(batch / 'sources' / (arm+'.json'), value)
    if not simulation:
        bind_successor(batch, config, a['_locked'])
    return config


def successor_record(batch, config):
    return dict(schema='mindthus.slim-successor-binding.v1',
        parent_receipt_sha256=digest(config['parent_receipt']),
        successor_root=str(Path(batch).resolve()), batch_sha256=digest(config))


def driver_lock_path(batch, config):
    if config['simulation']:
        return Path(batch) / '.driver.lock'
    return Path(config['parent_receipt']['root']) / '.slim-successor.lock'


def bind_successor(batch, config, locked):
    # Append one owner at the preserved parent. Failed/duplicate preparations
    # cannot acquire another allowance; no record is deleted to permit a retry.
    parent = Path(config['parent_receipt']['root'])
    with locked(driver_lock_path(batch, config)):
        if parent_receipt(parent) != config['parent_receipt']:
            raise ValueError('successor_parent_changed')
        claim = parent / 'slim-successor-binding.json'
        expected = successor_record(batch, config)
        if claim.exists():
            if read(claim) != expected:
                raise ValueError('parent_successor_already_bound')
        else:
            write(claim, expected)


def validate_successor(batch, config):
    if config.get('post_rc01_regression'):
        import importlib.util
        spec = importlib.util.spec_from_file_location('slim_post_rc01', HERE / 'post_rc01.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module.validate(batch, config)
    if config.get('retry_000049'):
        # One named Owner disposition; never a generic unknown override.
        import importlib.util
        spec=importlib.util.spec_from_file_location('slim_retry_000049',HERE/'retry_000049.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module.validate(batch,config)
    parent = Path(config['parent_receipt']['root'])
    if parent_receipt(parent) != config['parent_receipt']:
        raise ValueError('successor_parent_changed')
    claim = parent / 'slim-successor-binding.json'
    if not claim.exists() or read(claim) != successor_record(batch, config):
        raise ValueError('successor_root_or_configuration_not_bound')


def dispatch_stopped(batch):
    return any((Path(batch) / name).exists() for name in ('STOP.json', 'transport-stop-v2.json'))


def record_stop(batch, reason, binding):
    # Preserve the first stop cause; the terminal and observation retain any
    # additional causes (e.g. unknown plus unclassified internal recovery).
    if not (Path(batch) / 'STOP.json').exists():
        write(Path(batch) / 'STOP.json', dict(reason=reason, binding=binding))


def request(path, business, source, loaded, sequence):
    common = ('完成下面的用户请求。只使用本会话材料；不联网，不调用其他工具，不访问历史答案。'
        '返回合同：kind=answer 时 text 是给用户的完整自然语言答案，read_paths=[]；'
        'kind=read 时 read_paths 列出真正需要的仓库相对路径，text 简述读取目的。'
        'objection 记录执行限制，没有则为空。读取通过下一次受控会话返回；不自行执行脚本。\n\n')
    content = common + '用户请求：\n' + business
    if path['arm'] != 'bare':
        catalog = []
        for name in SKILLS:
            file = f'skills/{name}/SKILL.md'
            match = re.search(r'^description:\s*(.*)$', source[file], re.M)
            catalog.append(dict(path=file, description=match.group(1) if match else ''))
        content += '\n\n可按需读取的 Skill 目录：\n' + json.dumps(catalog, ensure_ascii=False)
        content += '\n\n原入口及已读材料：\n'
        for file in loaded:
            content += '\n--- '+file+' ---\n'+source[file]
    req = dict(role='host', phase='draft', arm='A', sequence=sequence,
        payload=dict(readable_paths=[]), simulation=False)
    req['request_sha256'] = digest(dict(path=path, sequence=sequence, prompt=content))
    return req, content


def drive(batch, *, adapter=None, clock=time.time, monotonic=time.monotonic, sleep=time.sleep):
    batch = Path(batch).resolve(); config = read(batch / 'batch.json')
    if read(batch / 'batch-binding.json') != dict(sha256=digest(config)):
        raise ValueError('batch_binding_changed')
    ceiling = 120 if config.get('post_rc01_regression') else 64
    if not 0<config['total_calls_max']<=ceiling or config['path_calls_max'] != 3:
        raise ValueError('unauthorized_mode_or_caps')
    if config.get('workspace_mode') != 'external_empty_directory_no_project_ancestors':
        raise ValueError('legacy_workspace_not_isolated_no_dispatch')
    if not config['simulation']:
        # Existing 34 attempts remain charged. A new real batch needs an explicit
        # cumulative allowance and parent binding, never a fresh 64-call balance.
        admission=config.get('successor_admission') or {}
        if admission.get('execution_authorized') is not True:
            raise ValueError('successor_not_authorized_no_dispatch')
        if config['total_calls_max']+config['parent_receipt']['logical_calls']>admission['cumulative_call_limit']:
            raise ValueError('successor_budget_reset')
    if hashlib.sha256(Path(BINARY).read_bytes()).hexdigest() != config['binary_sha256']:
        raise ValueError('binary_changed')
    a = adapters(config['adapter_root']); adapter = adapter or a['OfficialAdapters']()
    if adapter.simulation is not config['simulation']:
        raise ValueError('adapter_mode_mismatch')
    inputs = read(batch / 'inputs.json')
    if digest(inputs) != config['inputs_sha256']:
        raise ValueError('inputs_changed')
    sources = {arm:read(batch / 'sources' / (arm+'.json')) for arm in ('current','slim')}
    if any(digest(v) != config['source_sha256'][k] for k,v in sources.items()):
        raise ValueError('sources_changed')
    serial = a['SerialRequests'](batch / 'scheduling' / 'serial',clock=clock,monotonic=monotonic,sleep=sleep)
    with a['_locked'](driver_lock_path(batch, config)):
        if not config['simulation']:
            validate_successor(batch, config)
        if dispatch_stopped(batch):
            raise ValueError('batch_stopped_no_resend')
        serial.validate()
        if not config['simulation'] and not list(serial.root.glob('[0-9]*')):
            # Conservative monotonic cooling across the technical successor.
            start=monotonic()
            while monotonic()-start<60: sleep(min(60,60-(monotonic()-start)))
            write(batch/'parent-cooldown.json',dict(wait_seconds=monotonic()-start,
                basis=config.get('transition_wait_basis','conservative_monotonic_wait_after_known_parent_terminal')))
        for index, path in enumerate(config['plan'],start=config.get('plan_start_index',0)):
            run = batch / 'runs' / f"{index:02d}-{path['case']}-{path['model']}-{path['arm']}"
            if (run / 'result.json').exists():
                continue
            source = sources.get(path['arm'], {})
            loaded = ['skills/using-mindthus/SKILL.md'] if source else []
            for previous in sorted(run.glob('call-*/accepted.json')):
                accepted = read(previous)
                if accepted['kind'] == 'read': loaded += accepted['read_paths']
            existing = list(run.glob('call-*'))
            if any(not (p / 'accepted.json').exists() for p in existing):
                raise ValueError('unimported_call_no_resend')
            path_limit=config['path_calls_max']-config.get('prior_path_calls',{}).get(str(index),0)
            for seq in range(len(existing), path_limit):
                calls = list((batch / 'runs').glob('*/call-*/intent.json'))
                spent = sum(read(p)['session_seconds'] for p in (batch / 'runs').glob('*/call-*/terminal.json'))
                if hashlib.sha256(Path(BINARY).read_bytes()).hexdigest()!=config['binary_sha256']:
                    record_stop(batch,'binary_changed_before_dispatch',dict(calls=len(calls)))
                    return
                if len(calls) >= config['total_calls_max'] or spent >= config['active_processing_limit_seconds']:
                    write(batch / 'STOP.json', dict(reason='authorized_budget_exhausted', calls=len(calls)))
                    return
                req, prompt = request(path, inputs[path['case']], source, loaded, seq)
                req['simulation'] = config['simulation']
                schema = a['host_schema'](req)
                outbound = dict(prompt=prompt, local_schema=schema, api_schema=a['api_schema'](schema),
                    model=path['model'], effort=config['effort'], overrides=config['overrides'])
                directory = run / f'call-{seq:02d}'
                binding = dict(request_sha256=req['request_sha256'], wire_sha256=digest(outbound),
                    batch_sha256=digest(config), path=path, sequence=seq, simulation=config['simulation'])
                if config.get('retry_000049'):
                    binding.update(cumulative_call_ordinal=85+len(calls),
                        retry_of=config['retry_000049']['request_sha256'] if index==31 and seq==0 else None)
                if config.get('post_rc01_regression'):
                    binding.update(cumulative_call_ordinal=99+len(calls), batch_call_ordinal=1+len(calls))
                write(directory / 'request.json', req); write(directory / 'wire.json', outbound)
                transport_dir=external_transport_directory(batch,req,config)
                write(directory / 'workspace-binding.json',dict(**binding,
                    transport_directory=str(transport_dir),cwd=str(transport_dir/'workspace'),
                    preflight_project_AGENTS_ancestors=[]))
                started = time.monotonic(); terminal = None
                def invoke():
                    nonlocal terminal
                    write(directory / 'intent.json', binding)
                    begin = time.monotonic()
                    try:
                        raw = adapter.invoke(req, outbound, transport_dir, config)
                        for name in ('schema.api.json','reply.json'):
                            file=transport_dir/name
                            if file.exists():
                                (directory/name).write_bytes(file.read_bytes())
                    except (OSError, subprocess.TimeoutExpired) as exc:
                        raw = dict(kind='transport_error', code=type(exc).__name__, diagnostic=None)
                    write(directory / 'raw.json', dict(binding=binding, transport=raw))
                    status, response, usage, error = a['classify'](req, raw)
                    context = inspect_bound_context(raw, transport_dir/'workspace') if not config['simulation'] else dict(simulation=True)
                    write(directory/'context-observation.json',context)
                    if context.get('project_AGENTS_message_count',0) or context.get('cwd_matches') is False:
                        record_stop(batch, 'actual_context_not_isolated', binding)
                    observation = None
                    if raw.get('kind') == 'cli':
                        proc = subprocess.CompletedProcess([],raw['returncode'],raw['stdout'],raw['stderr'])
                        observation = a['observe'](batch, directory, proc,
                            dict(request_sha256=req['request_sha256'], transport_successor_sha256=digest(config)))
                    terminal = dict(binding=binding, raw_sha256=digest(raw), status=status,
                        response=response, usage=usage, error=error, session_seconds=time.monotonic()-begin,
                        ended_at_epoch=time.time(), observation=observation, underlying_requests=None, cost=None)
                    write(directory / 'terminal.json', terminal)
                    if status == 'unknown':
                        raise a['RecoveryRequired']('remote_unknown_no_resend')
                    return terminal
                try:
                    serial.call(f'{index}:{seq}', invoke)
                except a['RecoveryRequired']:
                    if terminal is None: raise
                if terminal is None: raise ValueError('missing_terminal')
                slot = sorted(serial.root.glob('[0-9]*'))[-1]
                wait = a['read_record'](slot / 'intent.json')['active_wait_seconds']
                measurement = dict(active_wait_seconds=wait, dispatch_wall_seconds=time.monotonic()-started,
                    session_seconds=terminal['session_seconds'], cli_starts=1,
                    outer_retries=int(bool(binding.get('retry_of'))))
                write(directory / 'measurement.json', measurement)
                if (terminal['observation'] or {}).get('stop_subsequent_dispatch'):
                    record_stop(batch, 'unclassified_internal_recovery', binding)
                response = terminal['response']
                if terminal['status'] != 'returned':
                    write(run / 'result.json', dict(status=terminal['status'], error=terminal['error'], answer=None))
                    if terminal['status'] in ('unknown','safety_refusal'):
                        record_stop(batch, terminal['status'], binding)
                        return
                    write(directory / 'accepted.json', dict(kind='failed'))
                    break
                invalid = (response['kind']=='answer' and bool(response['read_paths'])) or (
                    response['kind']=='read' and (not response['read_paths'] or any(p not in source or p in loaded for p in response['read_paths'])))
                if invalid:
                    write(directory / 'accepted.json', dict(kind='invalid_read_contract'))
                    write(run / 'result.json', dict(status='format_failure', answer=None, error='invalid_read_contract'))
                    break
                if response['kind']=='answer' and not response['text'].strip():
                    write(directory / 'accepted.json', dict(kind='empty_answer'))
                    write(run / 'result.json', dict(status='format_failure', answer=None, error='empty_answer'))
                    break
                write(directory / 'accepted.json', response)
                if response['kind']=='answer':
                    write(run / 'result.json', dict(status='delivered', answer=response['text'], objection=response['objection']))
                    (run / 'answer.txt').write_text(response['text'])
                    print('DELIVERED',run.name,'calls',seq+1,flush=True)
                    break
                loaded += response['read_paths']
                print('READ',run.name,response['read_paths'],flush=True)
                if seq+1==path_limit:
                    write(run / 'result.json', dict(status='read_budget_exhausted', answer=None))
                if dispatch_stopped(batch): return
            if dispatch_stopped(batch): return


def external_transport_directory(batch, req, config):
    """The existing adapter makes cwd beneath its output directory. Keep that
    directory outside every repository, while preserving evidence in the ledger.
    """
    target=Path('/private/tmp')/'mindthus-slim-cli'/digest(config)/digest(str(Path(batch).resolve()))/req['request_sha256']
    target=target.resolve()
    if target.is_relative_to(REPO) or target.is_relative_to(Path(batch).resolve()):
        raise ValueError('workspace_inside_project')
    for parent in (target,*target.parents):
        if (parent/'AGENTS.md').exists() or (parent/'.git').exists():
            raise ValueError('workspace_has_project_ancestor')
    if target.exists():
        raise ValueError('transport_directory_already_exists_no_resend')
    target.mkdir(parents=True)
    return target


def parent_receipt(root):
    root=Path(root).resolve();config=read(root/'batch.json')
    if read(root/'batch-binding.json')!={'sha256':digest(config)}:
        raise ValueError('parent_config_changed')
    if config.get('simulation') is not False:
        raise ValueError('simulated_parent_not_real')
    intents=sorted(root.glob('runs/*/call-*/intent.json'))
    evidence=[]
    for intent in intents:
        terminal=intent.with_name('terminal.json')
        if not terminal.exists() or read(terminal)['status']!='returned':
            raise ValueError('parent_not_all_returned_no_successor')
        evidence.append(dict(intent_sha256=digest(read(intent)),terminal_sha256=digest(read(terminal))))
    if not intents or not (root/'dispatch-pause-context-check.json').exists():
        raise ValueError('parent_not_named_context_failure')
    return dict(root=str(root),batch_sha256=digest(config),logical_calls=len(intents),
        evidence_sha256=digest(evidence),last_terminal_epoch=read(intents[-1].with_name('terminal.json'))['ended_at_epoch'])


def carry_budget(prior_calls, cumulative_limit):
    if type(prior_calls) is not int or type(cumulative_limit) is not int or not 0<=prior_calls<=64 or not prior_calls<cumulative_limit<=98:
        raise ValueError('successor_cumulative_limit')
    return min(64,cumulative_limit-prior_calls)


def inspect_bound_context(raw, expected_cwd):
    """Only this invocation's existing rollout, never auth files or other chats."""
    ids=[e['thread_id'] for e in raw.get('events',[]) if e.get('type')=='thread.started' and e.get('thread_id')]
    if len(ids)!=1:return dict(archive_available=False,reason='missing_bound_thread')
    session_root=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))/'sessions'
    files=list(session_root.glob('**/*'+ids[0]+'*.jsonl'))
    if len(files)!=1:return dict(thread_id=ids[0],archive_available=False,reason='bound_archive_unavailable')
    file=files[0];cwd=None;matches=[]
    for no,line in enumerate(file.read_text().splitlines(),1):
        try:event=json.loads(line)
        except ValueError:continue
        payload=event.get('payload') or {}
        if event.get('type')=='session_meta':cwd=payload.get('cwd')
        if event.get('type')!='response_item' or payload.get('type')!='message' or payload.get('role')!='user':continue
        for part in payload.get('content',[]):
            text=part.get('text','')
            if text.startswith('# AGENTS.md instructions for ') and str(REPO) in text:
                matches.append(dict(line=no,text_sha256=hashlib.sha256(text.encode()).hexdigest()))
    return dict(thread_id=ids[0],archive_available=True,archive=str(file),
        archive_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),actual_cwd=cwd,
        cwd_matches=None if cwd is None else str(Path(cwd).resolve())==str(Path(expected_cwd).resolve()),
        project_AGENTS_message_count=len(matches),project_AGENTS_bindings=matches)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('operation',choices=['prepare','run'])
    parser.add_argument('batch'); parser.add_argument('--adapter-root'); parser.add_argument('--candidate')
    parser.add_argument('--admission'); parser.add_argument('--parent-batch')
    args = parser.parse_args()
    if args.operation=='prepare': prepare(args.batch,args.adapter_root,args.candidate,
        admission=read(args.admission) if args.admission else None,parent_batch=args.parent_batch)
    else: drive(args.batch)

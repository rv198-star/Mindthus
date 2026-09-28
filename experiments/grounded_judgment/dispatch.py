"""Bound dispatch for the grounded prototype; no I/O until explicit step().

Existing transport and serial implementations own transport/recovery. This module
owns request/evidence/import linkage, not judgment or retries.
"""
import json
import hashlib
import os
import subprocess
import time
from pathlib import Path
from . import runtime as rt
from .exchange import jev_payload, jev_results
from .core import agent_contract
from experiments.typed_decision.contracts import DecisionSpec, canonical, digest, require
from experiments.typed_decision.providers import ProviderError, TypeSafeJevProvider
from experiments.typed_decision.session import RecoveryRequired, read_record
from experiments.typed_decision.relationship_runtime import _locked
from experiments.jev_direct.serial import SerialRequests
from experiments.jev_direct.host_boundary import api_schema, parse_events
from experiments.jev_direct.transport_profile import CANDIDATE, PROTOCOL, observe

PROPOSALS = {'A':6, 'B':7, 'C':9}
REPO = Path(__file__).resolve().parents[2]


def obj(properties):
    return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)


def host_schema(req):
    p=req['payload']
    if req['phase'] in ('draft','revision'):
        return obj({'kind':{'type':'string','enum':['answer','read']},'text':{'type':'string'},
          'read_paths':{'type':'array','items':{'type':'string','enum':p['readable_paths']} if p['readable_paths'] else {'type':'string'},'uniqueItems':True},
          'objection':{'type':'string'}})
    if req['arm']=='A':return obj({'needs_revision':{'type':'boolean'},'basis_text':{'type':'string'}})
    properties={}
    for raw in p['questions']:
        q=DecisionSpec(**{k:v for k,v in raw.items() if k!='output_contract'})
        c=agent_contract(q);vs=c['value_enum']+([None] if c['null_value'] else [])
        types=list(dict.fromkeys('null' if v is None else 'integer' if type(v) is int else 'string' for v in vs))
        properties[q.id]=obj({'value':{'type':types if len(types)>1 else types[0],'enum':vs},
          'semantic_state':{'type':'string','enum':c['semantic_states']},
          'unresolved_reason':{'type':['string','null']},
          'basis_refs':{'type':'array','items':{'type':'string'},'uniqueItems':True}})
    return obj(properties)


def prepare(batch, inputs, *, simulation=True, admission=None):
    """inputs is {case-id: prepare-input packet}; norms are never in this mapping."""
    batch=Path(batch);require(not batch.exists(),'batch_exists')
    require(inputs and all(k and k.replace('-','').replace('_','').isalnum() for k in inputs),'case_ids')
    profile=rt.read(CANDIDATE);protocol=rt.read(PROTOCOL)
    require(profile['host_model']=='gpt-6-sol' and profile['host_effort']=='xhigh','host_identity')
    require(digest(profile['candidate_overrides'])==profile['overrides_sha256'],'profile_digest')
    if not simulation:
        require(isinstance(admission,dict) and admission.get('execution_authorized') is True,'batch_not_authorized')
        require(admission.get('authorization_ref') and admission.get('acceptance_seal_sha256'),'missing_authorization_or_seal')
        require(set(admission.get('call_limits',{}))==set(PROPOSALS),'call_limits_required')
        require(all(type(v) is int and 0<v<=PROPOSALS[k] for k,v in admission['call_limits'].items()),'call_limits')
        require(all(type(admission.get(k)) in (int,float) and 0<admission[k]<=3600 for k in ('host_timeout','jev_timeout')),'timeouts_required')
        require(admission.get('binary'),'host_binary_required')
        require(admission['jev_timeout']<=90,'jev_deadline_limit')
        from .materials import verify_materials
        sealed,manifest=verify_materials(admission['materials_root'],admission.get('mode','formal'))
        require(sealed==inputs and digest(manifest)==admission['acceptance_seal_sha256'],'acceptance_material_binding')
        if admission.get('mode')=='exploratory':
            require(admission.get('total_limits')=={'logical':88,'jev':16,'host':72},'exploratory_total_limits')
    batch.mkdir(parents=True);(batch/'calls').mkdir();(batch/'runs').mkdir()
    config={'schema':'mindthus.grounded-dispatch.v1','simulation':simulation,'design_baseline':rt.BASELINE,
      'parent_implementation':'d7da2e4cc4b60fcbb4e90c6176a25e3745feb88b',
      'source_sha256':{str(p.relative_to(REPO)):digest(p.read_text()) for folder in ('grounded_judgment','jev_direct','typed_decision') for p in sorted((REPO/'experiments'/folder).glob('*.py'))},
      'protocol':protocol,'protocol_sha256':digest(protocol),
      'scope':'A/B/C all pre-rounds, reads, draft, check, revision; no old risk exceptions',
      'overrides':profile['candidate_overrides'],'overrides_sha256':digest(profile['candidate_overrides']),
      'call_limits':PROPOSALS if simulation else admission['call_limits'],
      'budget_status':'simulation_caps_only' if simulation else 'explicit_admission',
      'host_binary_sha256':None if simulation else hashlib.sha256(Path(admission['binary']).read_bytes()).hexdigest(),
      'admission':admission,'host_timeout':360 if simulation else admission['host_timeout'],
      'jev_timeout':90 if simulation else admission['jev_timeout'],'inputs_sha256':digest(inputs)}
    config['source_sha256']['docs/internal/research/typed-decision/route-control-v0.2/single-cycle-repair-v1/run.py']=digest((REPO/'docs/internal/research/typed-decision/route-control-v0.2/single-cycle-repair-v1/run.py').read_text())
    rt.write(batch/'batch.json',config);rt.write(batch/'inputs.json',inputs)
    for case,packet in inputs.items():
        require(set(packet)<= {'documents','materials','initial_paths'},'input_packet_keys')
        for arm in PROPOSALS:
            rt.init(batch/'runs'/(case+'-'+arm),packet['documents'],arm,simulation=simulation,
                    materials=packet.get('materials'),initial_paths=packet.get('initial_paths'))
            rt.write(batch/'runs'/(case+'-'+arm)/'dispatch-owner.json',{'batch':str(batch.resolve()),'batch_sha256':digest(config)})
    return config


def wire(req, config):
    body=dict(req);sha=body.pop('request_sha256');require(digest(body)==sha,'request_digest')
    if req['role']=='jev':return {'body':jev_payload(req),'endpoint':TypeSafeJevProvider().serving_identity.endpoint}
    contract=host_schema(req)
    return {'prompt':'根据以下完整请求输出规定JSON；工具关闭，必要材料只用read请求。\n'+canonical(req['payload']).decode(),
      'local_schema':contract,'api_schema':api_schema(contract),'model':'gpt-6-sol','effort':'xhigh',
      'overrides':config['overrides']}


class OfficialAdapters:
    """Lazy existing transports. Construction never reads authentication or starts CLI."""
    simulation=False
    def invoke(self, req, outbound, directory, config):
        if req['role']=='jev':
            from experiments.typed_decision.relationship_live import deadline_post_json
            key=os.environ.get('TYPESAFE_API_KEY')
            if not key:return {'kind':'not_sent','code':'missing_credential'}
            raw=deadline_post_json(outbound['endpoint'],{'Authorization':'Bearer '+key,'Content-Type':'application/json'},
                                   outbound['body'],config['jev_timeout'])
            return {'kind':'http_json','raw':raw}
        from experiments.jev_direct.pilot import wire as existing
        work=directory/'workspace';work.mkdir()
        rt.write(directory/'schema.api.json',outbound['api_schema'])
        cmd=[config['admission']['binary'],'exec','--skip-git-repo-check','-m',outbound['model'],
             '-c','model_reasoning_effort="xhigh"','-c','features.shell_tool=false','--json',
             '--output-schema',str(directory/'schema.api.json'),'-o',str(directory/'reply.json')]
        for option in outbound['overrides']:cmd+=['-c',option]
        cmd+=['--sandbox','read-only','-C',str(work),'-']
        env=os.environ.copy()
        for name in ('TYPESAFE_API_KEY','OPENROUTER_API_KEY','MINDTHUS_HOST_API_KEY'):env.pop(name,None)
        proc=existing._run_cli(cmd,outbound['prompt'],env,config['host_timeout'])
        # Exact decoded stdout events; exit status is diagnostic, never terminal proof.
        return {'kind':'cli','events':parse_events(proc.stdout),'stdout':proc.stdout,'stderr':proc.stderr,
                'returncode':proc.returncode,'reply_text':(directory/'reply.json').read_text() if (directory/'reply.json').exists() else None}


def check_schema(value, spec):
    # Only the schema subset emitted by host_schema; no change to semantic validation.
    kinds=spec['type'] if isinstance(spec['type'],list) else [spec['type']]
    actual='null' if value is None else {dict:'object',list:'array',str:'string',bool:'boolean',int:'integer'}.get(type(value))
    require(actual in kinds,'wire_type')
    if 'enum' in spec:require(value in spec['enum'],'wire_enum')
    if actual=='object':
        require(set(value)==set(spec['required']),'wire_fields')
        for k,v in value.items():check_schema(v,spec['properties'][k])
    elif actual=='array':
        if spec.get('uniqueItems'):require(len({digest(v) for v in value})==len(value),'wire_duplicate')
        for v in value:check_schema(v,spec['items'])


def classify(req, raw):
    """Terminal evidence only from this synchronous invocation, never unrelated archives."""
    kind=raw.get('kind');response=None;usage=None
    if kind=='http_json':
        value=raw['raw'];status='returned'
        if value.get('model')!='jev-1.13.0':return 'failed',None,None,'provider_model_mismatch'
        try:response=jev_results(req,value.get('answers'))
        except (ValueError,TypeError,KeyError):return 'failed',None,value.get('usage'),'provider_format_failure'
        usage=value.get('usage')
    elif kind=='cli':
        events=raw['events'];starts=[e for e in events if e.get('type')=='thread.started' and e.get('thread_id')]
        threads={e['thread_id'] for e in starts}
        terminals=[e for e in events if e.get('type') in ('turn.completed','turn.failed')]
        turns={e['turn_id'] for e in events if e.get('type') in ('turn.started','turn.completed','turn.failed') and e.get('turn_id')}
        if len(starts)!=1 or len(threads)!=1 or len(terminals)!=1 or len(turns)>1:return 'unknown',None,None,'missing_or_ambiguous_cli_terminal'
        terminal=terminals[0]
        if events.index(terminal)<=events.index(starts[0]) or sum(e.get('type')=='turn.started' for e in events)>1:
            return 'unknown',None,None,'cli_event_order_or_turn_count'
        if terminal.get('thread_id',next(iter(threads))) not in threads:return 'unknown',None,None,'terminal_thread_mismatch'
        if terminal['type']=='turn.failed':
            error=terminal.get('error') or {};code=error.get('code') if isinstance(error,dict) else None
            # Only structured terminal codes; arbitrary error strings cannot clear unknown.
            if code in ('permission_denied','access_denied','safety_refusal','policy_violation'):
                return 'safety_refusal',None,None,code
            if code in ('invalid_json_schema','invalid_request_error'):
                return 'failed',None,None,code
            return 'unknown',None,None,'unclassified_cli_failure'
        if any((e.get('item') or {}).get('type') in ('command_execution','mcp_tool_call','web_search','file_change') for e in events):
            return 'failed',None,terminal.get('usage'),'unexpected_tool_use'
        response=raw.get('reply');usage=terminal.get('usage');status='returned'
        if 'reply_text' in raw:
            try:response=json.loads(raw['reply_text'])
            except (ValueError,TypeError):return 'failed',None,usage,'invalid_reply_json_after_terminal'
        if not isinstance(response,dict):return 'failed',None,usage,'missing_reply_after_terminal'
        try:check_schema(response,host_schema(req))
        except (ValueError,KeyError,TypeError):return 'failed',None,usage,'host_format_failure'
    elif kind=='not_sent':return 'failed',None,None,raw['code']
    elif kind=='transport_error':
        d=raw.get('diagnostic') or {};code=raw.get('code')
        if req['role']!='jev' or d.get('request_sha256')!=digest(jev_payload(req)):
            return 'unknown',None,None,code
        if d.get('http_response_received') and d.get('http_status') in (401,403):
            return 'safety_refusal',None,None,code
        if d.get('generation_send_status')=='pre_send' and d.get('observed_stage')=='connection_establishment_failed':return 'failed',None,None,code
        # HTTP receipt alone (e.g. a gateway 5xx) does not prove remote generation ended.
        return 'unknown',None,None,code
    else:return 'unknown',None,None,'unrecognized_transport_record'
    return status,response,usage,None


class Dispatcher:
    def __init__(self,batch,adapter,*,clock=time.time,monotonic=time.monotonic,sleep=time.sleep):
        self.root=Path(batch).resolve();self.config=rt.read(self.root/'batch.json');self.adapter=adapter
        require(adapter.simulation is self.config['simulation'],'adapter_mode_mismatch')
        self.config_sha256=digest(self.config)
        self.clock=clock;self.monotonic=monotonic
        self.serial=SerialRequests(self.root/'serial',clock=clock,monotonic=monotonic,sleep=sleep)
        require(self.serial.batch is None,'historical_batch_not_allowed')

    def step(self,run_name):
        require(run_name in {c+'-'+a for c in rt.read(self.root/'inputs.json') for a in PROPOSALS},'unknown_run')
        with _locked(self.root/'.dispatch.lock'):
            require(digest(self.config)==self.config_sha256==digest(rt.read(self.root/'batch.json')),'batch_configuration_changed')
            require(digest(rt.read(self.root/'inputs.json'))==self.config['inputs_sha256'],'batch_inputs_changed')
            require(not (self.root/'STOP.json').exists(),'batch_stopped')
            self.serial.validate()
            if not self.config['simulation']:
                require(self.config['admission']['execution_authorized'] is True,'batch_not_authorized')
                require(hashlib.sha256(Path(self.config['admission']['binary']).read_bytes()).hexdigest()==self.config['host_binary_sha256'],'host_binary_changed')
                require(all(digest((REPO/p).read_text())==h for p,h in self.config['source_sha256'].items()),'source_changed')
            run=self.root/'runs'/run_name;s=rt.state(run)
            if s['stopped'] or s['phase']=='done':return s
            # No automatic replay after crash between intent/raw/terminal/import writes.
            for previous in sorted((self.root/'calls').iterdir()):
                require((previous/'import.json').exists(),'unimported_dispatch_requires_reconciliation')
            require(s['call_count']<self.config['call_limits'][s['arm']],'call_budget_exhausted')
            req=rt.request(run)
            if req is None:return rt.state(run)
            require(req['simulation'] is self.config['simulation'],'run_mode_mismatch')
            limits=(self.config.get('admission') or {}).get('total_limits')
            if limits:
                prior=[rt.read(p/'request.json') for p in (self.root/'calls').iterdir()]
                require(len(prior)<limits['logical'] and sum(r['role']==req['role'] for r in prior)<limits[req['role']],'batch_call_budget_exhausted')
            began=self.monotonic()
            outbound=wire(req,self.config);directory=self.root/'calls'/f'{len(list((self.root/"calls").iterdir())):06d}'
            directory.mkdir();key=run_name+':'+str(req['sequence'])
            binding={'call_key':key,'request_sha256':req['request_sha256'],'wire_sha256':digest(outbound),
              'batch_sha256':digest(self.config),'simulation':self.config['simulation']}
            rt.write(directory/'request.json',req);rt.write(directory/'wire.json',outbound);rt.write(directory/'binding.json',binding)
            loading=self.monotonic()-began;terminal=None;envelope=None
            def invoke():
                nonlocal terminal,envelope
                start=self.monotonic();rt.write(directory/'intent.json',{**binding,'started_at_epoch':self.clock()})
                try:raw=self.adapter.invoke(req,outbound,directory,self.config)
                except ProviderError as exc:
                    raw={'kind':'transport_error','code':str(exc),'diagnostic':exc.diagnostic}
                except (OSError,subprocess.TimeoutExpired) as exc:
                    raw={'kind':'transport_error','code':type(exc).__name__,'diagnostic':None}
                except Exception as exc:
                    from experiments.typed_decision.transport_diagnostics import exception_type
                    raw={'kind':'transport_error','code':exception_type(exc),'diagnostic':None}
                elapsed=self.monotonic()-start
                rt.write(directory/'raw.json',{'binding':binding,'transport':raw})
                status,response,usage,error=classify(req,raw)
                observation=None
                if raw.get('kind')=='cli':
                    proc=subprocess.CompletedProcess([],raw['returncode'],raw.get('stdout',''),raw.get('stderr',''))
                    observation=observe(self.root,directory,proc,{'request_sha256':req['request_sha256'],'transport_successor_sha256':digest(self.config)})
                terminal={'binding':binding,'raw_sha256':digest(raw),'status':status,'error':error,
                          'ended_at_epoch':self.clock(),'session_seconds':elapsed,'transport_observation':observation}
                rt.write(directory/'terminal.json',terminal)
                slot=read_record(sorted(self.serial.root.glob('[0-9]*'))[-1]/'intent.json')
                envelope={**binding,'status':status,'response':response,'measurement':{
                    'cli_starts':int(req['role']=='host'),'observed_recoveries':observation,
                    'underlying_requests':None,'active_wait_seconds':slot['active_wait_seconds'],
                    'session_seconds':elapsed,'loading_seconds':loading,'usage':usage,'cost':usage.get('cost') if isinstance(usage,dict) else None,
                    'transport_evidence':str(directory/'terminal.json')}}
                if status=='unknown':raise RecoveryRequired('dispatch_remote_unknown')
                return terminal
            try:self.serial.call(key,invoke)
            except RecoveryRequired:
                if terminal is None:raise
            if terminal is None:raise RecoveryRequired('dispatch_missing_terminal')
            # Re-read bindings before accept. Simulated records cannot cross into a real run.
            saved=rt.read(directory/'raw.json')
            require(saved['binding']==binding and digest(saved['transport'])==terminal['raw_sha256'],'raw_binding_mismatch')
            require(rt.state(run)['pending']==req,'pending_changed')
            envelope['dispatch_receipt']=str(directory)
            rt.write(directory/'envelope.json',envelope)
            result=rt.accept(run,envelope)
            rt.write(directory/'import.json',{'binding':binding,'envelope_sha256':digest(envelope),
              'state_event_sha256':rt.verify(run),'phase':result['phase'],'stopped':result['stopped'],
              'dispatch_wall_seconds':self.monotonic()-began,
              'outer_driver_retries':0,'logical_calls':1,'actual_http_count':None,
              'generation_attempt_count':None,'connection_recovery_seconds':None,'authentication_recovery_seconds':None})
            if terminal['status'] in ('unknown','safety_refusal') or (terminal['transport_observation'] or {}).get('stop_subsequent_dispatch'):
                rt.write(self.root/'STOP.json',{'call_key':key,'terminal_sha256':digest(terminal),'reason':terminal['status']})
            return result


def validate_import(run,req,envelope):
    owner=rt.read(Path(run)/'dispatch-owner.json');batch=Path(owner['batch'])
    config=rt.read(batch/'batch.json')
    require(digest(config)==owner['batch_sha256'],'dispatch_owner_changed')
    directory=Path(envelope.get('dispatch_receipt','')).resolve()
    require(directory.parent==batch/'calls','receipt_outside_batch')
    binding=rt.read(directory/'binding.json');terminal=rt.read(directory/'terminal.json');raw=rt.read(directory/'raw.json')
    require(binding==terminal['binding']==raw['binding'],'receipt_binding')
    require(binding['call_key']==Path(run).name+':'+str(req['sequence']),'receipt_call_key')
    require(binding['request_sha256']==req['request_sha256'] and binding['simulation'] is req['simulation']
            and binding['batch_sha256']==owner['batch_sha256'],'receipt_identity')
    require(rt.read(directory/'request.json')==req and digest(rt.read(directory/'wire.json'))==binding['wire_sha256'],'wire_receipt')
    require(digest(raw['transport'])==terminal['raw_sha256'] and envelope==rt.read(directory/'envelope.json'),'receipt_content')
    status,response,usage,error=classify(req,raw['transport'])
    require((status,response,error)==(terminal['status'],envelope['response'],terminal['error'])
            and envelope['status']==status,'receipt_terminal')
